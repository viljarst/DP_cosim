"""Look inside the vessel data file. Run from the repo folder:  python wave_loads/explore_vessel_data.py

Nothing here is used by the model. It is only for understanding the data.
"""
import json
from pathlib import Path

import numpy as np

# The data file lives in vessels/gunnerus/, one folder up from wave_loads/
data_file = Path(__file__).resolve().parent.parent / "vessels" / "gunnerus" / "gunnerus_vessel.json"

with open(data_file, "r", encoding="utf-8") as f:
    raw = json.load(f)

print("WHAT IS IN THE FILE:")
print(f"  Top-level keys: {list(raw.keys())}")
print(f"  Vessel: {raw['main']['name']},  Lpp = {raw['main']['Lpp']:.1f} m,  B = {raw['main']['B']:.1f} m")

freqs = np.asarray(raw["freqs"])                      # [rad/s]
headings = np.degrees(raw["headings"])                # [deg], relative wave direction
print(f"  Frequencies: {len(freqs)} values from {freqs.min():.2f} to {freqs.max():.2f} rad/s")
print(f"  Headings:    {len(headings)} values, {headings[0]:.0f} to {headings[-1]:.0f} deg in steps of {headings[1] - headings[0]:.0f}")
print("  Speeds:      the last index of each table is vessel speed. Index 0 = zero speed, which is what DP uses")

rao_amp = np.asarray(raw["forceRAO"]["amp"])          # first-order force per metre wave amplitude
drift = np.asarray(raw["driftfrc"]["amp"])            # mean drift force per (metre wave amplitude)^2
print(f"  Force RAO table shape:   {rao_amp.shape}  = (DOF, frequency, heading, speed)")
print(f"  Drift table shape:       {drift.shape}  = (DOF, frequency, heading, speed)")

print("LOOK UP A FEW VALUES (zero speed, frequency closest to 0.7 rad/s):")
i_f = np.argmin(np.abs(freqs - 0.7))                  # index of the frequency closest to 0.7
i_head = np.argmin(np.abs(headings - 180.0))          # 180 deg = head sea
i_beam = np.argmin(np.abs(headings - 90.0))           # 90 deg = beam sea
print(f"  Frequency used: {freqs[i_f]:.3f} rad/s")
print(f"  Head sea (180 deg): surge drift = {drift[0, i_f, i_head, 0]:9.0f} N/m^2,  sway drift = {drift[1, i_f, i_head, 0]:9.0f} N/m^2")
print(f"  Beam sea ( 90 deg): surge drift = {drift[0, i_f, i_beam, 0]:9.0f} N/m^2,  sway drift = {drift[1, i_f, i_beam, 0]:9.0f} N/m^2")
print(f"  Head sea (180 deg): surge force RAO amplitude = {abs(rao_amp[0, i_f, i_head, 0]):9.0f} N/m")