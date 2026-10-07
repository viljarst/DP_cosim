"""Wave loads on the vessel in short-crested (or long-crested) sea.

Puts together the sea (sea_state.py) and the vessel data (vessel_data.py)
and calculates the forces on the vessel at time t:

1. First-order (wave-frequency) loads, Sørensen eq. 6.67:
       tau1 = sum_j a_j |H(w_j, b_j)| cos(w_j t - k_j (x cos a_j + y sin a_j) - eps_j - <H>)
   where b_j is the relative direction of EACH component.

2. Slowly varying drift loads with Newman's approximation, Sørensen eq. 6.96-6.97:
       tau2 = sum_j sum_k a_j a_k T_jk cos(phi_j - phi_k),   T_jk = (T_j + T_k) / 2
   Each component uses its own drift coefficient T_j = T(w_j, b_j).
   The double sum is rewritten as
       tau2 = Re[ (sum_j a_j T_j e^{i phi_j}) * conj(sum_k a_k e^{i phi_k}) ]
   which gives exactly the same answer but costs N instead of N^2 operations.

Coordinates: eta = (north, east, heading psi) in NED, directions in radians.
Output: forces in the body frame [Fx (N), Fy (N), Mz (Nm)].
"""
import numpy as np

from sea_state import SeaState, realize
from vessel_data import VesselData


def calm_sea():
    """A sea with no wave components. Gives zero loads."""
    empty = np.zeros(0)
    return SeaState(empty, empty, empty, empty)


class WaveLoadModel:
    """The wave load model. One instance per vessel and simulation."""

    def __init__(self, vessel, sea_settings, gravity, direction_is_from):
        """
        vessel:            a VesselData object (vessel_data.py)
        sea_settings:      dict with every argument of realize() except hs and tp,
                           e.g. {"spectrum_type": "jonswap", "gamma": 3.3, ...}
        gravity:           [m/s^2]
        direction_is_from: True  = the wave direction is where the waves come FROM
                           False = the wave direction is where the waves go TO
        """
        self.vessel = vessel
        self.sea_settings = sea_settings
        self.gravity = gravity
        self.direction_is_from = direction_is_from
        self._hs = None
        self._tp = None
        self._mean_to = 0.0                       # mean direction the waves travel TO [rad, NED]
        self._set_sea(calm_sea())

    # -- sea state ----------------------------------------------------------------

    def _set_sea(self, sea):
        """Store a new sea and look up the vessel tables for its frequencies (done once)."""
        self.sea = sea
        self._rao, self._drift = self.vessel.tables_at(sea.frequencies)
        self._k = sea.frequencies**2 / self.gravity          # wave number, deep water
        self._idx = np.arange(len(sea.amplitudes))           # 0, 1, 2, ... one per component

    def set_sea_state(self, hs, tp, direction):
        """Update the sea state from the environment block.

        hs [m], tp [s], direction [rad, NED] in the convention given by direction_is_from.
        The sea is only rebuilt when Hs or Tp changes. A new direction only
        turns all the components, so the sea is not rebuilt.
        """
        hs, tp = float(hs), float(tp)
        if hs != self._hs or tp != self._tp:
            if hs <= 0.0 or tp <= 0.0:
                self._set_sea(calm_sea())
            else:
                self._set_sea(realize(hs, tp, **self.sea_settings))
            self._hs, self._tp = hs, tp
        d = float(direction)
        # store the direction the waves go TO, which is what the formulas use
        self._mean_to = (d + np.pi if self.direction_is_from else d) % (2.0 * np.pi)

    def component_directions(self):
        """The direction each component travels TO [rad, NED]."""
        return self._mean_to + self.sea.direction_offsets

    # -- loads --------------------------------------------------------------------

    def _interpolate_heading(self, table, beta):
        """Pick each component's value from table (3, n, nh) at its relative direction beta."""
        lo, hi, w = self.vessel.heading_weights(beta)
        j = self._idx
        return table[:, j, lo] * (1.0 - w) + table[:, j, hi] * w      # (3, n)

    def first_order(self, t, eta):
        """First-order (wave-frequency) loads [Fx, Fy, Mz] at time t."""
        if len(self.sea.amplitudes) == 0:
            return np.zeros(3)
        north, east, psi = eta
        directions = self.component_directions()
        H = self._interpolate_heading(self._rao, directions - psi)      # relative direction
        arg = (self.sea.frequencies * t
               - self._k * (north * np.cos(directions) + east * np.sin(directions))
               - self.sea.phases)
        return (np.conj(H) * np.exp(1j * arg)).real @ self.sea.amplitudes

    def drift(self, t, eta):
        """Mean + slowly varying drift loads [Fx, Fy, Mz] at time t (Newman)."""
        if len(self.sea.amplitudes) == 0:
            return np.zeros(3)
        psi = eta[2]
        T = self._interpolate_heading(self._drift, self.component_directions() - psi)
        e = self.sea.amplitudes * np.exp(1j * (self.sea.frequencies * t - self.sea.phases))
        return ((T * e).sum(axis=1) * np.conj(e.sum())).real

    def mean_drift(self, psi):
        """The mean value of the drift load for heading psi (no time series)."""
        if len(self.sea.amplitudes) == 0:
            return np.zeros(3)
        T = self._interpolate_heading(self._drift, self.component_directions() - psi)
        return T @ self.sea.amplitudes**2

    def loads(self, t, eta):
        """Returns (first_order, drift) at time t for vessel position eta."""
        return self.first_order(t, eta), self.drift(t, eta)

    

def build_model(p):
    """Build a WaveLoadModel from a flat parameter list (dict).

    p has the same names as get_waveloads_parameters() in waveloads_config.py.
    Used by the FMU and by the test scripts, so the model is always built the same way.
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
    sea_settings = {
        "spectrum_type": p["spectrum_type"], "gamma": float(p["gamma"]),
        "spreading_type": p["spreading_type"], "s": float(p["spreading_s"]),
        "n_directions": int(p["n_directions"]), "direction_limit_deg": float(p["direction_limit_deg"]),
        "n_frequencies": int(p["n_frequencies"]),
        "omega_min_factor": float(p["omega_min_factor"]), "omega_max_factor": float(p["omega_max_factor"]),
        "random_frequencies": bool(p["random_frequencies"]), "random_directions": bool(p["random_directions"]),
        "seed": int(p["seed"]),
    }
    return WaveLoadModel(vessel, sea_settings, float(p["gravity"]), bool(p["direction_is_from"]))

