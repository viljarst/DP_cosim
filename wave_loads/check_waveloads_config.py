"""Quick check of waveloads_config.py. Run from the repo folder:  python wave_loads/check_waveloads_config.py

Builds the sea ONLY from the parameter list, the same way the FMU does it.
"""
import numpy as np

from sea_state import sea_from_parameters
from waveloads_config import get_waveloads_parameters

from enviroment_config import WAVE    # found because waveloads_config added Config/ to the path

p = get_waveloads_parameters()

print("PARAMETERS FROM CONFIG:")
for name, value in p.items():
    print(f"  {name:22s} = {value}")

print(f"SEA STATE FROM enviroment_config.py: Hs = {WAVE.hs} m, Tp = {WAVE.tp} s, from {WAVE.direction_deg} deg")
sea, kept = sea_from_parameters(WAVE.hs, WAVE.tp, p)
n_grid = p["n_frequencies"] * (p["n_directions"] if p["spreading_type"] != "none" else 1)
hs_kept = 4 * np.sqrt(np.sum(0.5 * sea.amplitudes**2))
print(f"  Grid: {n_grid} components. Sent out: the {len(sea.amplitudes)} strongest")
print(f"  Kept energy: {kept:.1%}  ->  Hs of the components sent out = {hs_kept:.2f} m (full sea: {WAVE.hs} m)")
print(f"  Frequencies sent out: {sea.frequencies.min():.2f} to {sea.frequencies.max():.2f} rad/s "
      f"(peak frequency {2 * np.pi / WAVE.tp:.2f} rad/s)")
