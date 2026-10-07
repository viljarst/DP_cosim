"""Quick check of model.py. Run from the repo folder:  python wave_loads/check_model.py"""
from pathlib import Path

import numpy as np

from model import WaveLoadModel
from vessel_data import VesselData

data_file = Path(__file__).resolve().parent.parent / "vessels" / "gunnerus" / "gunnerus_vessel.json"
vessel = VesselData(data_file, speed_index=0,
                    force_rao_rows={"surge": 0, "sway": 1, "yaw": 5},
                    drift_rows={"surge": 0, "sway": 1, "yaw": 2},
                    rao_amplitude="absolute")

sea_settings = {
    "spectrum_type": "jonswap", "gamma": 3.3,
    "spreading_type": "cos2s", "s": 2, "n_directions": 11, "direction_limit_deg": 90,
    "n_frequencies": 30, "omega_min_factor": 0.25, "omega_max_factor": 3.0,
    "random_frequencies": True, "random_directions": True, "seed": 123,
}
model = WaveLoadModel(vessel, sea_settings, gravity=9.81, direction_is_from=True)

hs, tp = 3.0, 9.0                    # sea state [m], [s]
eta = np.array([0.0, 0.0, 0.0])      # vessel at the origin, heading north (psi = 0)

print("CHECK CALM SEA:")
model.set_sea_state(0.0, tp, 0.0)
print(f"  Hs = 0 gives first order = {model.first_order(10.0, eta)},  drift = {model.drift(10.0, eta)}")

print("CHECK HEAD SEA (waves from north, vessel heading north):")
model.set_sea_state(hs, tp, np.radians(0.0))
print(f"  Number of wave components: {len(model.sea.amplitudes)}")
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
    model.set_sea_state(hs, tp, np.radians(deg))
    fx, fy, mz = model.mean_drift(psi=0.0)
    going_to = np.radians(deg) + np.pi             # waves come FROM deg, so they go TO deg + 180
    # with psi = 0, body x = north and body y = east
    along = fx * np.cos(going_to) + fy * np.sin(going_to)
    print(f"  Waves from {deg:3d} deg:  Fx = {fx:7.0f},  Fy = {fy:7.0f},  force along wave direction = {along:7.0f}  "
          f"{'OK' if along > 0 else 'WRONG'}")

print("CHECK MIRRORED SEA (waves from 60 deg vs 300 deg):")
model.set_sea_state(hs, tp, np.radians(60.0))
a = model.mean_drift(0.0)
model.set_sea_state(hs, tp, np.radians(300.0))
b = model.mean_drift(0.0)
print(f"  from  60: Fx = {a[0]:7.0f},  Fy = {a[1]:7.0f},  Mz = {a[2]:8.0f}")
print(f"  from 300: Fx = {b[0]:7.0f},  Fy = {b[1]:7.0f},  Mz = {b[2]:8.0f}")
print("  (Fx should be about the same, Fy and Mz should change sign.")
print("   Not exact, because the random directions inside each bin are not mirrored.)")