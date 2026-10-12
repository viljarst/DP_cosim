"""Quick check of model.py. Run from the repo folder:  python wave_forces/check_model.py

The wave components are made the same way the waves FMU makes them
(sea_from_parameters in wave_loads/sea_state.py), so this checks the whole
chain: waves block -> wave components -> forces in the vessel block.
"""
import forces_config  # noqa: F401  (must be first: makes Config/ and wave_loads/ importable)

import numpy as np

from forces_config import get_wave_forces_parameters
from model import build_model
from sea_state import directions_to, sea_from_parameters
from waveloads_config import get_waveloads_parameters

wave_parameters = get_waveloads_parameters()
model = build_model(get_wave_forces_parameters())

hs, tp = 3.0, 9.0                    # sea state [m], [s]
eta = np.array([0.0, 0.0, 0.0])      # vessel at the origin, heading north (psi = 0)


def send_waves(hs, tp, from_deg):
    """Do what the waves FMU does, and give the wave components to the force model."""
    sea, kept = sea_from_parameters(hs, tp, wave_parameters)
    directions = directions_to(sea, from_deg, wave_parameters["direction_is_from"])
    model.set_waves(sea.amplitudes, sea.frequencies, sea.phases, directions)
    return kept


print("CHECK CALM SEA:")
send_waves(0.0, tp, 0.0)
print(f"  Hs = 0 gives first order = {model.first_order(10.0, eta)},  drift = {model.drift(10.0, eta)}")

print("CHECK HEAD SEA (waves from north, vessel heading north):")
kept = send_waves(hs, tp, 0.0)
print(f"  {len(model.amplitudes)} wave components, {kept:.1%} of the wave energy")
fx, fy, mz = model.mean_drift(psi=0.0)
print(f"  Mean drift:  Fx = {fx:8.0f} N,  Fy = {fy:6.0f} N,  Mz = {mz:7.0f} Nm")
print("  (Fx < 0: pushed backwards. Fy and Mz small: spreading is symmetric)")

print("CHECK TIME SERIES (3 hours, head sea):")
t = np.arange(0.0, 3 * 3600.0, 1.0)
tau1 = np.array([model.first_order(ti, eta) for ti in t])
tau2 = np.array([model.drift(ti, eta) for ti in t])
print(f"  Drift Fx:        time average = {tau2[:, 0].mean():8.0f} N   (should be close to mean drift {fx:8.0f} N)")
print(f"  First order Fx:  time average = {tau1[:, 0].mean():8.0f} N,  std = {tau1[:, 0].std():8.0f} N")
print("  (first order: large, but averages to zero. drift: small, but always pushes the same way)")

print("CHECK DRIFT POINTS DOWNWAVE (for 8 wave directions):")
for deg in range(0, 360, 45):
    send_waves(hs, tp, deg)
    fx, fy, mz = model.mean_drift(psi=0.0)
    going_to = np.radians(deg) + np.pi             # waves come FROM deg, so they go TO deg + 180
    # with psi = 0, body x = north and body y = east
    along = fx * np.cos(going_to) + fy * np.sin(going_to)
    print(f"  Waves from {deg:3d} deg:  Fx = {fx:7.0f},  Fy = {fy:7.0f},  force along wave direction = {along:7.0f}  "
          f"{'OK' if along > 0 else 'WRONG'}")

print("CHECK MIRRORED SEA (waves from 60 deg vs 300 deg):")
send_waves(hs, tp, 60.0)
a = model.mean_drift(0.0)
send_waves(hs, tp, 300.0)
b = model.mean_drift(0.0)
print(f"  from  60: Fx = {a[0]:7.0f},  Fy = {a[1]:7.0f},  Mz = {a[2]:8.0f}")
print(f"  from 300: Fx = {b[0]:7.0f},  Fy = {b[1]:7.0f},  Mz = {b[2]:8.0f}")
print("  (Fx should be about the same, Fy and Mz should change sign.")
print("   Not exact, because the random directions inside each bin are not mirrored.)")

print("CHECK HOW MUCH THE DRIFT CHANGES WHEN ONLY THE STRONGEST WAVES ARE KEPT:")
n_grid = wave_parameters["n_frequencies"] * wave_parameters["n_directions"]
for n_waves in (wave_parameters["n_waves"], n_grid):
    sea, kept = sea_from_parameters(hs, tp, dict(wave_parameters, n_waves=n_waves))
    model.set_waves(sea.amplitudes, sea.frequencies, sea.phases, directions_to(sea, 45.0, True))
    fx, fy, mz = model.mean_drift(0.0)
    print(f"  {n_waves:4d} components ({kept:6.1%} of the energy):  mean drift Fx = {fx:7.0f},  Fy = {fy:7.0f},  Mz = {mz:8.0f}")
print("  (Gunnerus is small, so much of the drift comes from short waves with little energy.")
print("   Those are the first to be removed when only the strongest waves are kept.)")
