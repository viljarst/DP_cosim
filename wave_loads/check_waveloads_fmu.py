"""Check the FMU code WITHOUT building an FMU and without OSP.
Run from the repo folder:  python wave_loads/check_waveloads_fmu.py

It creates the WaveLoads class directly in Python and calls it the same way
OSP would: set parameters -> exit_initialization_mode() -> do_step() again and again.
This works on any computer, also where OSP is not available (Mac).
"""
import numpy as np

from model import build_model
from waveloads_config import get_waveloads_parameters
from waveloads_fmu import WaveLoads

from enviroment_config import WAVE    # found because waveloads_config added Config/ to the path

DT = 0.5                               # time step [s]

# 1. Create the FMU object, as OSP does when it loads the FMU
fmu = WaveLoads(instance_name="wave_loads")

# 2. Set the parameters from config, as the cosimulation master will do
for name, value in get_waveloads_parameters().items():
    setattr(fmu, name, value)

# 3. Set the inputs. Later these come from the environment and vessel FMUs
fmu.hs, fmu.tp, fmu.wave_direction_deg = WAVE.hs, WAVE.tp, WAVE.direction_deg
fmu.north, fmu.east, fmu.heading = 0.0, 0.0, 0.0

# 4. Start, and run 10 minutes of time steps
fmu.exit_initialization_mode()
t = 0.0
x_drift = []
while t < 600.0:
    fmu.do_step(t, DT)
    t += DT
    x_drift.append(fmu.X_drift)

print("OUTPUTS AFTER 10 MINUTES:")
print(f"  First order: X = {fmu.X_first / 1000:8.1f} kN,  Y = {fmu.Y_first / 1000:8.1f} kN,  N = {fmu.N_first / 1000:8.1f} kNm")
print(f"  Drift:       X = {fmu.X_drift / 1000:8.1f} kN,  Y = {fmu.Y_drift / 1000:8.1f} kN,  N = {fmu.N_drift / 1000:8.1f} kNm")
print(f"  Total:       X = {fmu.X / 1000:8.1f} kN,  Y = {fmu.Y / 1000:8.1f} kN,  N = {fmu.N / 1000:8.1f} kNm")

print("COMPARE WITH THE MODEL CALLED DIRECTLY:")
model = build_model(get_waveloads_parameters())
model.set_sea_state(WAVE.hs, WAVE.tp, np.radians(WAVE.direction_deg))
first, drift = model.loads(t, (0.0, 0.0, 0.0))
same = np.allclose([fmu.X_first, fmu.Y_first, fmu.N_first, fmu.X_drift, fmu.Y_drift, fmu.N_drift],
                   np.concatenate([first, drift]))
print(f"  FMU gives the same loads as the model: {same}")

print("CHECK THAT A MISSING CONFIG IS CAUGHT:")
fmu2 = WaveLoads(instance_name="no_config")
try:
    fmu2.exit_initialization_mode()
except RuntimeError as error:
    print(f"  {error}")
    