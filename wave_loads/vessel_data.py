"""Hydrodynamic data for the vessel: force RAOs and wave drift coefficients.

Reads a vessel file in the same JSON format as mcsimpy / TMR4240 (exported
from ShipX) and answers the question: what is the RAO and the drift
coefficient for THIS frequency and THIS relative wave direction?

The table only has values at 36 frequencies and 36 headings, so values in
between are found by linear interpolation.

Heading convention in the table (as ShipX and Sørensen app. D):
beta = 0 is following sea, beta = 180 deg is head sea, measured from the
vessel's x-axis.

Which row in the table is surge, sway and yaw is given from outside (config),
because the files are not consistent: in the corrected Gunnerus file the yaw
drift is in row 2 (MSS layout), while the yaw RAO is in row 5.

The RAOs are stored and interpolated in complex form, H = amp * exp(i * phase).
Then it does not matter if the phase jumps between -180 and +180 degrees.
"""
import json

import numpy as np

DOFS = ("surge", "sway", "yaw")


def interpolate_frequency(x_table, table, x_new, left, right):
    """Linear interpolation along the frequency axis (axis 1) of table (3, nf, nh).

    left / right: what to use below / above the table range,
    either "hold" (keep the edge value) or "zero".
    """
    x_new = np.asarray(x_new, dtype=float)
    nf = len(x_table)
    # index of the table point just below each new frequency
    i = np.clip(np.searchsorted(x_table, x_new) - 1, 0, nf - 2)
    # how far between point i and point i+1 (0 = at i, 1 = at i+1)
    w = (x_new - x_table[i]) / (x_table[i + 1] - x_table[i])
    out = table[:, i, :] * (1.0 - w)[None, :, None] + table[:, i + 1, :] * w[None, :, None]

    below = x_new < x_table[0]
    above = x_new > x_table[-1]
    for mask, rule, edge in ((below, left, 0), (above, right, -1)):
        if mask.any():
            out[:, mask, :] = 0.0 if rule == "zero" else table[:, [edge], :]
    return out


class VesselData:
    """Force RAOs and drift coefficients for surge, sway and yaw."""

    def __init__(self, data_file, speed_index, force_rao_rows, drift_rows, rao_amplitude):
        """Read the tables from the vessel file.

        speed_index:    which speed column to use. 0 = zero speed (DP).
        force_rao_rows: which table row is each DOF, e.g. {"surge": 0, "sway": 1, "yaw": 5}
        drift_rows:     the same for the drift table
        rao_amplitude:  "absolute" uses |amp| (as mcsimpy/TMR4240),
                        "signed" uses the amplitude with the sign in the file.
                        (The Gunnerus file has negative amplitudes for surge, heave and yaw.)
        """
        if rao_amplitude not in ("absolute", "signed"):
            raise ValueError(f"rao_amplitude must be 'absolute' or 'signed', got '{rao_amplitude}'")
        with open(data_file, "r", encoding="utf-8") as f:
            raw = json.load(f)

        freqs = np.asarray(raw["freqs"], dtype=float)
        headings = np.asarray(raw["headings"], dtype=float) % (2.0 * np.pi)
        order = np.argsort(headings)                          # sort headings from 0 to 2*pi
        if np.any(np.diff(freqs) <= 0):
            raise ValueError(f"{data_file}: the frequencies must be increasing")

        # Pick out surge, sway and yaw at the chosen speed
        rao_rows = [force_rao_rows[dof] for dof in DOFS]
        drift_row_list = [drift_rows[dof] for dof in DOFS]
        amp = np.asarray(raw["forceRAO"]["amp"], dtype=float)[rao_rows, :, :, speed_index]
        phase = np.deg2rad(np.asarray(raw["forceRAO"]["phase"], dtype=float))[rao_rows, :, :, speed_index]
        drift = np.asarray(raw["driftfrc"]["amp"], dtype=float)[drift_row_list, :, :, speed_index]
        if rao_amplitude == "absolute":
            amp = np.abs(amp)

        self.freqs = freqs                                     # (nf,)  [rad/s]
        self.headings = headings[order]                        # (nh,)  [rad]
        self.rao = (amp * np.exp(1j * phase))[:, :, order]     # (3, nf, nh) [N/m, Nm/m]
        self.drift = drift[:, :, order]                        # (3, nf, nh) [N/m^2, Nm/m^2]

    # -- frequency --------------------------------------------------------------

    def tables_at(self, frequencies):
        """RAO and drift tables interpolated to the frequencies of the wave components.

        Returns (rao, drift), each with shape (3, n_components, n_headings).
        This is done once when the sea is built, not in every time step.

        Outside the table (same choice as mcsimpy):
        - RAO:   edge value below the lowest frequency, zero above the highest.
        - Drift: goes linearly to zero at omega = 0, edge value above the highest.
        """
        rao = interpolate_frequency(self.freqs, self.rao, frequencies, left="hold", right="zero")
        # add a zero-drift point at omega = 0, so the drift goes to zero for very long waves
        f0 = np.concatenate(([0.0], self.freqs))
        d0 = np.concatenate((np.zeros_like(self.drift[:, :1, :]), self.drift), axis=1)
        drift = interpolate_frequency(f0, d0, frequencies, left="hold", right="hold")
        return rao, drift

    # -- heading ----------------------------------------------------------------

    def heading_weights(self, beta):
        """Interpolation indices and weights for relative wave directions beta [rad].

        Returns (lo, hi, w) so that value = (1 - w) * table[lo] + w * table[hi].
        Works for any heading grid and wraps around from 360 back to 0 degrees.
        """
        h = self.headings
        nh = len(h)
        beta = (np.asarray(beta, dtype=float) - h[0]) % (2.0 * np.pi) + h[0]   # into [h0, h0 + 2*pi)
        h_ext = np.append(h, h[0] + 2.0 * np.pi)                               # add 360 deg = 0 deg at the end
        lo = np.clip(np.searchsorted(h_ext, beta, side="right") - 1, 0, nh - 1)
        w = (beta - h_ext[lo]) / (h_ext[lo + 1] - h_ext[lo])
        hi = (lo + 1) % nh                                                     # index after the last is the first
        return lo, hi, w