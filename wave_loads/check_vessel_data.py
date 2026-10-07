"""Quick check of vessel_data.py. Run from the repo folder:  python wave_loads/check_vessel_data.py"""
from pathlib import Path

import numpy as np

from vessel_data import VesselData

data_file = Path(__file__).resolve().parent.parent / "vessels" / "gunnerus" / "gunnerus_vessel.json"
vessel = VesselData(data_file, speed_index=0,
                    force_rao_rows={"surge": 0, "sway": 1, "yaw": 5},
                    drift_rows={"surge": 0, "sway": 1, "yaw": 2},
                    rao_amplitude="absolute")

SURGE, SWAY, YAW = 0, 1, 2                    # row numbers in vessel.rao and vessel.drift
f = vessel.freqs
i = np.argmin(np.abs(f - 0.7))                # a table frequency close to 0.7 rad/s

print("CHECK WHAT WAS READ:")
print(f"  RAO table:   {vessel.rao.shape}  (surge/sway/yaw, frequency, heading)")
print(f"  Drift table: {vessel.drift.shape}")

print("CHECK FREQUENCY INTERPOLATION (head sea, surge drift):")
_, drift = vessel.tables_at([f[i], f[i + 1], 0.5 * (f[i] + f[i + 1])])
i_head = np.argmin(np.abs(np.degrees(vessel.headings) - 180.0))
a, b, mid = drift[SURGE, :, i_head]
print(f"  At table point {f[i]:.3f}:  {a:8.1f}   (table: {vessel.drift[SURGE, i, i_head]:8.1f})")
print(f"  At table point {f[i + 1]:.3f}:  {b:8.1f}   (table: {vessel.drift[SURGE, i + 1, i_head]:8.1f})")
print(f"  Halfway between:       {mid:8.1f}   (should be the average {0.5 * (a + b):8.1f})")

print("CHECK OUTSIDE THE TABLE:")
rao, drift = vessel.tables_at([0.0, 10.0])
print(f"  Drift at omega = 0:  {np.abs(drift[:, 0, :]).max():.1f}  (should be 0: very long waves give no drift)")
print(f"  RAO at omega = 10:   {np.abs(rao[:, 1, :]).max():.1f}  (should be 0: above the table)")

print("CHECK HEADING INTERPOLATION:")
for deg in (180.0, 185.0, 355.0):
    lo, hi, w = vessel.heading_weights(np.radians(deg))
    print(f"  {deg:5.1f} deg: between {np.degrees(vessel.headings[lo]):5.1f} and "
          f"{np.degrees(vessel.headings[hi]):5.1f} deg, weight w = {w:.2f}")

print("CHECK PHYSICS (mean drift direction at 0.7 rad/s):")
_, drift = vessel.tables_at([0.7])
for deg, name in ((180.0, "head sea"), (90.0, "beam sea"), (0.0, "following sea")):
    lo, hi, w = vessel.heading_weights(np.radians(deg))
    d = drift[:, 0, lo] * (1 - w) + drift[:, 0, hi] * w
    print(f"  {name:13s} ({deg:5.1f} deg): surge = {d[SURGE]:7.1f},  sway = {d[SWAY]:7.1f},  yaw = {d[YAW]:9.1f}")