"""Quick check of waveloads_config.py. Run from the repo folder:  python wave_loads/check_waveloads_config.py

Builds the wave load model ONLY from the parameter list, the same way the
FMU will do it in the next step.
"""
import numpy as np

from model import WaveLoadModel
from vessel_data import VesselData
from waveloads_config import get_waveloads_parameters

from enviroment_config import WAVE    # found because waveloads_config added Config/ to the path

p = get_waveloads_parameters()

print("PARAMETERS FROM CONFIG:")
for name, value in p.items():
    print(f"  {name:22s} = {value}")

print("BUILD THE MODEL FROM THE PARAMETERS:")
vessel = VesselData(
    p["vessel_data_file"], p["speed_index"],
    force_rao_rows={"surge": p["force_rao_row_surge"], "sway": p["force_rao_row_sway"], "yaw": p["force_rao_row_yaw"]},
    drift_rows={"surge": p["drift_row_surge"], "sway": p["drift_row_sway"], "yaw": p["drift_row_yaw"]},
    rao_amplitude=p["rao_amplitude"],
)
sea_settings = {
    "spectrum_type": p["spectrum_type"], "gamma": p["gamma"],
    "spreading_type": p["spreading_type"], "s": p["spreading_s"],
    "n_directions": p["n_directions"], "direction_limit_deg": p["direction_limit_deg"],
    "n_frequencies": p["n_frequencies"],
    "omega_min_factor": p["omega_min_factor"], "omega_max_factor": p["omega_max_factor"],
    "random_frequencies": p["random_frequencies"], "random_directions": p["random_directions"],
    "seed": p["seed"],
}
model = WaveLoadModel(vessel, sea_settings, p["gravity"], p["direction_is_from"])
print("  OK")

print(f"SEA STATE FROM enviroment_config.py: Hs = {WAVE.hs} m, Tp = {WAVE.tp} s, from {WAVE.direction_deg} deg")
model.set_sea_state(WAVE.hs, WAVE.tp, np.radians(WAVE.direction_deg))
fx, fy, mz = model.mean_drift(psi=0.0)
print(f"  {len(model.sea.amplitudes)} wave components")
print(f"  Mean drift with vessel heading north:  Fx = {fx:7.0f} N,  Fy = {fy:7.0f} N,  Mz = {mz:8.0f} Nm")