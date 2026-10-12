"""Wave forces on the vessel, calculated from the wave components.

This code belongs to the VESSEL block. The waves block (wave_loads/) sends
out the wave components (amplitude, frequency, phase and direction of each
wave), and this code turns them into forces on the vessel at time t.

1. First-order (wave-frequency) loads, Sørensen eq. 6.67:
       tau1 = sum_j a_j |H(w_j, b_j)| cos(w_j t - k_j (x cos a_j + y sin a_j) - eps_j - <H>)
   where a_j is the direction wave j travels to, and b_j = a_j - psi is its
   direction relative to the vessel.

2. Slowly varying drift loads with Newman's approximation, Sørensen eq. 6.96-6.97:
       tau2 = sum_j sum_k a_j a_k T_jk cos(phi_j - phi_k),   T_jk = (T_j + T_k) / 2
   Each component uses its own drift coefficient T_j = T(w_j, b_j).
   The double sum is rewritten as
       tau2 = Re[ (sum_j a_j T_j e^{i phi_j}) * conj(sum_k a_k e^{i phi_k}) ]
   which gives exactly the same answer but costs N instead of N^2 operations.

The wave elevation behind these formulas must be the same as in the waves block:
    zeta = sum_j amplitude_j * cos(omega_j * t - k_j * (x cos(direction_j) + y sin(direction_j)) - phase_j)

Coordinates: eta = (north, east, heading psi) in NED, directions in radians.
Output: forces in the body frame [Fx (N), Fy (N), Mz (Nm)].
"""
import numpy as np

from vessel_data import VesselData


class WaveLoadModel:
    """Wave forces on one vessel. One instance per vessel and simulation."""

    def __init__(self, vessel, gravity):
        """
        vessel:  a VesselData object (vessel_data.py)
        gravity: [m/s^2]
        """
        self.vessel = vessel
        self.gravity = gravity
        self.frequencies = None
        self.set_waves([], [], [], [])                       # no waves until set_waves() is called

    # -- wave components from the waves block -------------------------------------

    def set_waves(self, amplitudes, frequencies, phases, directions):
        """Store the wave components from the waves block.

        amplitudes [m], frequencies [rad/s], phases [rad],
        directions [rad]: the direction each wave travels TO, NED.

        The vessel tables are only looked up again when the frequencies change
        (that is, when the waves block has built a new sea).
        """
        frequencies = np.asarray(frequencies, dtype=float)
        if self.frequencies is None or not np.array_equal(frequencies, self.frequencies):
            self.frequencies = frequencies
            self._rao, self._drift = self.vessel.tables_at(frequencies)
            self._k = frequencies**2 / self.gravity          # wave number, deep water
            self._idx = np.arange(len(frequencies))          # 0, 1, 2, ... one per component
        self.amplitudes = np.asarray(amplitudes, dtype=float)
        self.phases = np.asarray(phases, dtype=float)
        self.directions = np.asarray(directions, dtype=float)

    # -- loads --------------------------------------------------------------------

    def _interpolate_heading(self, table, beta):
        """Pick each component's value from table (3, n, nh) at its relative direction beta."""
        lo, hi, w = self.vessel.heading_weights(beta)
        j = self._idx
        return table[:, j, lo] * (1.0 - w) + table[:, j, hi] * w      # (3, n)

    def first_order(self, t, eta):
        """First-order (wave-frequency) loads [Fx, Fy, Mz] at time t."""
        if len(self.amplitudes) == 0:
            return np.zeros(3)
        north, east, psi = eta
        H = self._interpolate_heading(self._rao, self.directions - psi)      # relative direction
        arg = (self.frequencies * t
               - self._k * (north * np.cos(self.directions) + east * np.sin(self.directions))
               - self.phases)
        return (np.conj(H) * np.exp(1j * arg)).real @ self.amplitudes

    def drift(self, t, eta):
        """Mean + slowly varying drift loads [Fx, Fy, Mz] at time t (Newman)."""
        if len(self.amplitudes) == 0:
            return np.zeros(3)
        psi = eta[2]
        T = self._interpolate_heading(self._drift, self.directions - psi)
        e = self.amplitudes * np.exp(1j * (self.frequencies * t - self.phases))
        return ((T * e).sum(axis=1) * np.conj(e.sum())).real

    def mean_drift(self, psi):
        """The mean value of the drift load for heading psi (no time series)."""
        if len(self.amplitudes) == 0:
            return np.zeros(3)
        T = self._interpolate_heading(self._drift, self.directions - psi)
        return T @ self.amplitudes**2

    def loads(self, t, eta):
        """Returns (first_order, drift) at time t for vessel position eta."""
        return self.first_order(t, eta), self.drift(t, eta)


def build_model(p):
    """Build a WaveLoadModel from a flat parameter list (dict).

    p has the same names as get_wave_forces_parameters() in forces_config.py.
    """
    vessel = VesselData(
        p["vessel_data_file"], int(p["speed_index"]),
        force_rao_rows={"surge": int(p["force_rao_row_surge"]),
                        "sway": int(p["force_rao_row_sway"]),
                        "yaw": int(p["force_rao_row_yaw"])},
        drift_rows={"surge": int(p["drift_row_surge"]),
                    "sway": int(p["drift_row_sway"]),
                    "yaw": int(p["drift_row_yaw"])},
        rao_amplitude=p["rao_amplitude"],
    )
    return WaveLoadModel(vessel, float(p["gravity"]))
