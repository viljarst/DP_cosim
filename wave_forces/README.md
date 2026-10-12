# Wave forces (for the vessel block)

Calculates the wave forces on the vessel from the wave components sent out by
the waves block (`../wave_loads/`): **first-order (wave-frequency) loads** and
**mean + slowly varying drift loads** (Newman's approximation).

This code belongs in the **vessel block**. It is kept here until it is moved
there. It is not part of the waves FMU.

## How to use it in the vessel block

```python
from model import build_model

model = build_model(parameters)       # once, at the start (reads the vessel file)

# every time step:
model.set_waves(amplitudes, omegas, phases, directions)   # the outputs of the waves FMU
first_order, drift = model.loads(t, (north, east, heading))
```

- `amplitudes, omegas, phases, directions`: arrays with the `amplitude_i`,
  `omega_i`, `phase_i` and `direction_i` outputs of the waves FMU.
  `direction_i` is where the wave travels **to**, in radians (NED).
- `t`: the simulation time, the same as in the waves FMU.
- `north, east` [m], `heading` [rad]: the vessel position and heading.
- Returns `first_order` and `drift`: `[Fx, Fy, Mz]` in the body frame [N, N, Nm].

`set_waves()` is cheap to call every step: the vessel tables are only looked up
again when the frequencies change.

The formulas assume this wave elevation, which is the one the waves block uses:

```
zeta = sum_i amplitude_i * cos(omega_i * t - k_i * (x cos(direction_i) + y sin(direction_i)) - phase_i)
```

## Files

| File | What it does |
|---|---|
| `model.py` | Calculates the loads. `build_model(p)` builds the model from the parameter list |
| `vessel_data.py` | Reads the vessel file and interpolates RAOs / drift coefficients in frequency and heading |
| `forces_config.py` | Reads `Config/wave_forces_config.py` and returns the parameter list |
| `check_model.py` | Whole chain: waves block -> components -> forces, physics checks |
| `check_vessel_data.py` | Interpolation, physics of the drift table |
| `explore_vessel_data.py` | Prints what is in the vessel data file |
| `run_wave_forces.py` | Runs the whole chain for 3 hours and plots the loads |

Settings are in `Config/wave_forces_config.py` (vessel data file, table rows).

## Check

Run from the repo folder:

```
python wave_forces/check_vessel_data.py
python wave_forces/check_model.py
python wave_forces/run_wave_forces.py
```

## Known limitations

- Zero vessel speed (DP): the tables for zero speed are used, and wave drift
  damping is not included (it belongs in the damping of the vessel model).
- Drift between components uses Newman's approximation, not full QTFs.
- The vessel file must cover 0–360° in heading (no automatic mirroring).
