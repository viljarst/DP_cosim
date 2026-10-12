"""Check the FMU code WITHOUT building an FMU and without OSP.
Run from the repo folder:  python wave_loads/check_waveloads_fmu.py

It creates the WaveLoads class directly in Python and calls it the same way
OSP would: set parameters -> exit_initialization_mode() -> do_step() again and again.
This works on any computer, also where OSP is not available (Mac).
"""
import numpy as np

from sea_state import directions_to, sea_from_parameters
from waveloads_config import get_waveloads_parameters
from waveloads_fmu import COMPONENT_OUTPUTS, N_WAVES_BUILT, WaveLoads

from enviroment_config import WAVE    # found because waveloads_config added Config/ to the path

DT = 0.5                               # time step [s]


def make_fmu(parameters):
    """Create the FMU object and set the parameters, as the cosimulation master will do."""
    fmu = WaveLoads(instance_name="waves")
    for name, value in parameters.items():
        setattr(fmu, name, value)
    return fmu


def read_outputs(fmu):
    """Read the wave component outputs back into four arrays."""
    return [np.array([getattr(fmu, f"{quantity}_{i}") for i in range(N_WAVES_BUILT)])
            for quantity in COMPONENT_OUTPUTS]


p = get_waveloads_parameters()

print("CHECK THE OUTPUTS:")
fmu = make_fmu(p)
n_outputs = sum(1 for v in fmu.vars.values() if v.causality.name == "output")
print(f"  Built for {N_WAVES_BUILT} wave components: {n_outputs} outputs "
      f"(4 per component + kept_energy_fraction)")

# Set the inputs. Later these come from the environment FMU
fmu.hs, fmu.tp, fmu.wave_direction_deg = WAVE.hs, WAVE.tp, WAVE.direction_deg

# Start, and run 1 minute of time steps
fmu.exit_initialization_mode()
t = 0.0
while t < 60.0:
    fmu.do_step(t, DT)
    t += DT

amplitude, omega, phase, direction = read_outputs(fmu)
print(f"  Component 0 (strongest): amplitude = {amplitude[0]:.3f} m,  omega = {omega[0]:.3f} rad/s,  "
      f"phase = {phase[0]:.3f} rad,  direction = {np.degrees(direction[0]):.1f} deg")
print(f"  kept_energy_fraction = {fmu.kept_energy_fraction:.3f}")

print("COMPARE WITH sea_state.py CALLED DIRECTLY:")
sea, kept = sea_from_parameters(WAVE.hs, WAVE.tp, p)
same = (np.allclose(amplitude, sea.amplitudes) and np.allclose(omega, sea.frequencies)
        and np.allclose(phase, sea.phases)
        and np.allclose(direction, directions_to(sea, WAVE.direction_deg, p["direction_is_from"])))
print(f"  FMU gives the same wave components: {same}")

print("CHECK THAT A NEW DIRECTION ONLY TURNS THE WAVES:")
fmu.wave_direction_deg = WAVE.direction_deg + 90.0
fmu.do_step(t, DT)
amplitude2, omega2, phase2, direction2 = read_outputs(fmu)
turned = np.degrees((direction2 - direction) % (2 * np.pi))
print(f"  Amplitudes, frequencies and phases unchanged: "
      f"{np.array_equal(amplitude, amplitude2) and np.array_equal(omega, omega2) and np.array_equal(phase, phase2)}")
print(f"  All directions turned by 90 deg: {np.allclose(turned, 90.0)}")

print("CHECK CALM SEA (Hs = 0):")
fmu.hs = 0.0
fmu.do_step(t, DT)
amplitude, *_ = read_outputs(fmu)
print(f"  All amplitudes zero: {np.all(amplitude == 0.0)}")

print("CHECK THAT A MISSING CONFIG IS CAUGHT:")
try:
    WaveLoads(instance_name="no_config").exit_initialization_mode()
except RuntimeError as error:
    print(f"  {error}")

print("CHECK THAT A WRONG N_WAVES IS CAUGHT:")
wrong = dict(p, n_waves=N_WAVES_BUILT + 50)
try:
    make_fmu(wrong).exit_initialization_mode()
except RuntimeError as error:
    print(f"  {error}")
