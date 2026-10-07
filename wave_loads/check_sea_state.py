"""Quick check of sea_state.py. Run from the repo folder:  python wave_loads/check_sea_state.py"""
import numpy as np

from sea_state import elevation, realize
from spectra import cos2s

hs = 3.0     # significant wave height [m]
tp = 9.0     # peak period [s]
t = np.arange(0.0, 3 * 3600.0, 0.5)          # three hours, 0.5 s steps


def make_sea(spreading_type, random_frequencies=True, seed=123):
    """Short helper so each check only shows what it changes."""
    return realize(hs, tp, "jonswap", 3.3,
                   spreading_type=spreading_type, s=2, n_directions=11, direction_limit_deg=90,
                   n_frequencies=30, omega_min_factor=0.25, omega_max_factor=3.0,
                   random_frequencies=random_frequencies, random_directions=True, seed=seed)


print("CHECK SPREADING FUNCTION:")
theta = np.linspace(-np.pi / 2, np.pi / 2, 2001)
for s in (1, 2, 10):
    area = np.trapezoid(cos2s(theta, s), theta)
    print(f"  s = {s:2d}: area under D = {area:.4f} (should be 1),  D at mean direction = {cos2s(0.0, s):.3f}")

print("CHECK HS:")
for spreading_type in ("none", "cos2s"):
    sea = make_sea(spreading_type)
    m0 = np.sum(sea.amplitudes**2 / 2)       # energy in the components
    zeta = elevation(t, sea)                 # wave elevation time series
    print(f"  {spreading_type:5s}: {len(sea.amplitudes):3d} components,  "
          f"Hs from components = {4 * np.sqrt(m0):.3f} m,  from time series = {4 * np.std(zeta):.3f} m")

print("CHECK DIRECTIONS (cos2s):")
sea = make_sea("cos2s")
energy = sea.amplitudes**2 / 2
mean_offset = np.degrees(np.sum(energy * sea.direction_offsets) / np.sum(energy))
within_30 = np.sum(energy[np.abs(sea.direction_offsets) <= np.radians(30)]) / np.sum(energy)
print(f"  Energy-weighted mean direction offset: {mean_offset:+.1f} deg  (should be close to 0)")
print(f"  Share of energy within +-30 deg:        {within_30:.0%}")
print(f"  Widest direction used:                  {np.degrees(np.abs(sea.direction_offsets).max()):.1f} deg")


def envelope(t, sea):
    """Height of the wave groups (the slowly varying envelope of the waves)."""
    t = t[:, None]
    return np.abs(np.sum(sea.amplitudes * np.exp(1j * (sea.frequencies * t - sea.phases)), axis=1))


print("CHECK REPETITION OF WAVE GROUPS:")
d_omega = (3.0 - 0.25) * (2 * np.pi / tp) / (30 - 1)
t_repeat = 2 * np.pi / d_omega               # repeat period of an evenly spaced grid
t_short = np.arange(0.0, 200.0, 0.5)
for random_frequencies in (False, True):
    sea = make_sea("none", random_frequencies)
    same = np.allclose(envelope(t_short, sea), envelope(t_short + t_repeat, sea))
    print(f"  random_frequencies = {random_frequencies}:  groups repeat after {t_repeat:.1f} s? {same}")

print("CHECK WRONG NAME:")
try:
    realize(hs, tp, "jonswap", 3.3, "cos-2s", 2, 11, 90, 30, 0.25, 3.0, True, True, seed=123)
except ValueError as error:
    print(f"  {error}")