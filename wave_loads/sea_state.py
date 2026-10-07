"""Sea state: turns a wave spectrum into a set of regular wave components.

Each component is a cosine wave with its own amplitude, frequency, phase and
direction. Adding all the components together gives an irregular sea.

Long-crested sea:  all waves travel in the mean direction (spreading "none").
Short-crested sea: the energy is spread over several directions around the
                   mean direction (spreading "cos2s").

The directions are stored RELATIVE to the mean direction (direction_offsets).
The mean direction itself is added later, when the loads are calculated, so
the environment block can change it without building a new sea.

References:
- Sørensen, Marine Control Systems, section 6.2.1 (eq. 6.1, 6.6, 6.22)
"""
from dataclasses import dataclass

import numpy as np

from spectra import cos2s, jonswap, pierson_moskowitz


@dataclass
class SeaState:
    """One realisation of the sea. All arrays have length n_components."""
    amplitudes: np.ndarray          # [m]
    frequencies: np.ndarray         # [rad/s]
    phases: np.ndarray              # [rad]
    direction_offsets: np.ndarray   # [rad], relative to the mean wave direction


def frequency_spectrum(omega, hs, tp, spectrum_type, gamma):
    """Pick the wave spectrum by name.

    spectrum_type: "pierson_moskowitz" or "jonswap".
    gamma is only used for "jonswap".
    """
    if spectrum_type == "pierson_moskowitz":
        return pierson_moskowitz(omega, hs, tp)
    if spectrum_type == "jonswap":
        return jonswap(omega, hs, tp, gamma)
    raise ValueError(
        f"Unknown spectrum type '{spectrum_type}'. Valid: pierson_moskowitz, jonswap"
    )


def direction_bins(spreading_type, s, n_directions, direction_limit_deg):
    """Split the directions around the mean direction into bins.

    Returns (offsets, weights, d_theta):
      offsets: centre of each direction bin, relative to the mean direction [rad]
      weights: share of the energy in each bin (they add up to 1)
      d_theta: width of each bin [rad]

    spreading_type "none" gives one bin straight along the mean direction.
    """
    if spreading_type == "none":
        return np.zeros(1), np.ones(1), 0.0
    if spreading_type != "cos2s":
        raise ValueError(f"Unknown spreading type '{spreading_type}'. Valid: none, cos2s")

    limit = np.deg2rad(direction_limit_deg)                  # +- limit around the mean
    d_theta = 2.0 * limit / n_directions
    offsets = -limit + (np.arange(n_directions) + 0.5) * d_theta
    weights = cos2s(offsets, s) * d_theta                    # energy share = D * d_theta
    return offsets, weights / weights.sum(), d_theta         # normalise so the sum is exactly 1


def realize(hs, tp, spectrum_type, gamma,
            spreading_type, s, n_directions, direction_limit_deg,
            n_frequencies, omega_min_factor, omega_max_factor,
            random_frequencies, random_directions, seed):
    """Split a wave spectrum into n_frequencies x n_directions wave components.

    random_frequencies / random_directions = True moves each component to a
    random point inside its bin, so the sea does not repeat itself.
    The same seed always gives the same sea.
    """
    # 1. Frequency bins
    wp = 2.0 * np.pi / tp                                   # peak frequency [rad/s]
    omega = np.linspace(omega_min_factor * wp, omega_max_factor * wp, n_frequencies)
    d_omega = omega[1] - omega[0]                           # width of each frequency bin
    S = frequency_spectrum(omega, hs, tp, spectrum_type, gamma)   # energy density per bin

    # 2. Direction bins
    offsets, dir_weights, d_theta = direction_bins(
        spreading_type, s, n_directions, direction_limit_deg)
    m = len(offsets)                                        # number of directions actually used

    # 3. Every combination of frequency and direction becomes one component
    #    (frequency in the outer loop, direction in the inner loop)
    freqs = np.repeat(omega, m)                             # f1 f1 f1 f2 f2 f2 ...
    dirs = np.tile(offsets, n_frequencies)                  # d1 d2 d3 d1 d2 d3 ...
    energy_share = np.repeat(S * d_omega, m) * np.tile(dir_weights, n_frequencies)
    amplitudes = np.sqrt(2.0 * energy_share)                # Sørensen eq. 6.6

    # 4. Random numbers: phases first, then frequencies, then directions
    n_total = n_frequencies * m
    rng = np.random.default_rng(seed)                       # random number generator
    phases = rng.uniform(0.0, 2.0 * np.pi, n_total)         # random phase per component
    if random_frequencies:
        # move each frequency randomly within its own bin: +- half a bin width
        freqs = freqs + rng.uniform(-0.5 * d_omega, 0.5 * d_omega, n_total)
    if random_directions and m > 1:
        # move each direction randomly within its own bin: +- half a bin width
        dirs = dirs + rng.uniform(-0.5 * d_theta, 0.5 * d_theta, n_total)

    return SeaState(amplitudes, freqs, phases, dirs)


def elevation(t, sea):
    """Wave elevation zeta [m] at the origin at time(s) t.

    zeta(t) = sum_j a_j * cos(omega_j * t - eps_j)
    (At the origin the direction of each wave does not matter.)
    """
    t = np.atleast_1d(np.asarray(t, dtype=float))[:, None]  # column, so each row is one time
    return np.sum(sea.amplitudes * np.cos(sea.frequencies * t - sea.phases), axis=1)