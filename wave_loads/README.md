# Wave loads

Wave loads on the vessel for the DP simulator: **first-order (wave-frequency)
loads** and **mean + slowly varying drift loads**, in long-crested or
short-crested irregular sea. Packaged as an FMU (`WaveLoads.fmu`) for OSP.

Based on the TMR4240 / `mcsimpy` wave model, extended with directional
spreading (Sørensen, *Marine Control Systems*, section 6.2.1).

---

## FMU interface

### Inputs (change during the simulation)

| Name | Unit | From | Description |
|---|---|---|---|
| `hs` | m | environment | Significant wave height |
| `tp` | s | environment | Peak period |
| `wave_direction_deg` | deg | environment | Mean wave direction, where the waves come **from**, 0 = north, clockwise |
| `north` | m | vessel model | Vessel position north (NED) |
| `east` | m | vessel model | Vessel position east (NED) |
| `heading` | **rad** | vessel model | Vessel heading ψ, 0 = north, clockwise |

### Outputs (body frame)

| Name | Unit | Description |
|---|---|---|
| `X`, `Y`, `N` | N, N, Nm | **Total** wave load = first order + drift |
| `X_first`, `Y_first`, `N_first` | N, N, Nm | First-order (wave-frequency) part only |
| `X_drift`, `Y_drift`, `N_drift` | N, N, Nm | Drift (mean + slowly varying) part only |

Body frame: x forward, y to starboard, N positive bow to starboard.

### Parameters (set once, before the simulation starts)

24 parameters, set by the cosimulation master from
`waveloads_config.get_waveloads_parameters()`. The FMU does **not** read the
config files itself, and refuses to run unless `configuration_loaded = 1`.

| Type | Parameters |
|---|---|
| Real | `configuration_loaded`, `gravity`, `gamma`, `spreading_s`, `direction_limit_deg`, `omega_min_factor`, `omega_max_factor` |
| Integer | `speed_index`, `force_rao_row_surge/sway/yaw`, `drift_row_surge/sway/yaw`, `n_directions`, `n_frequencies`, `seed` |
| Boolean | `direction_is_from`, `random_frequencies`, `random_directions` |
| String | `vessel_data_file`, `rao_amplitude`, `spectrum_type`, `spreading_type` |

> **Important for the master script:** each parameter must be set with the
> function for its FMI type (`real_initial_value`, `integer_initial_value`,
> `boolean_initial_value`, `string_initial_value` in libcosimpy). A value set
> with the wrong type is silently ignored by OSP.

---

## How it works

```
Hs, Tp, direction
      ↓  spectra.py + sea_state.py
N x M regular wave components (amplitude, frequency, direction, phase)
      ↓  vessel_data.py
force RAO and drift coefficient for each component (from the ShipX table)
      ↓  model.py
first-order loads + drift loads (Newman's approximation)
      ↓
X, Y, N
```

The hydrodynamic table only describes the response to **one regular wave**
(per metre amplitude). The block splits the irregular sea into many regular
waves, looks each one up in the table and adds the contributions together.

## Files

| File | What it does |
|---|---|
| `spectra.py` | Wave spectra (Pierson–Moskowitz, JONSWAP) and the cos-2s spreading function |
| `sea_state.py` | Splits the spectrum into wave components |
| `vessel_data.py` | Reads the vessel file and interpolates RAOs / drift coefficients in frequency and heading |
| `model.py` | Calculates the loads. `build_model(p)` builds the model from the parameter list |
| `waveloads_fmu.py` | The FMU shell: inputs, parameters, outputs, `do_step` |
| `waveloads_config.py` | Reads `Config/` and returns the parameter list for the FMU |
| `check_*.py` | Test scripts, one per file |
| `explore_vessel_data.py` | Prints what is in the vessel data file |
| `run_waveloads.py` | Runs the whole model for 3 hours and plots the loads |

Settings are in `Config/wave_config.py` (spectrum, spreading, discretization,
vessel data file). Hs, Tp and direction are in `Config/enviroment_config.py`.
Vessel data is in `vessels/<vessel>/`.

---

## Build the FMU

From the repo folder, with the `dpcosim` environment active:

```
python -m pythonfmu build -f wave_loads/waveloads_fmu.py -d wave_loads/build wave_loads/model.py wave_loads/sea_state.py wave_loads/spectra.py wave_loads/vessel_data.py
```

The FMU is written to `wave_loads/build/WaveLoads.fmu` (not in git). Rebuild
after every change to the `.py` files.

**Requirements to run the FMU:**
- Windows or Linux. pythonfmu only includes `win64` and `linux64` binaries,
  so the FMU can be **built** on Mac but not **run** there.
- Python 3.11+ with `numpy` installed on the machine that runs the simulation.

## Test

Run from the repo folder. All of these work on Mac.

```
python wave_loads/check_spectra.py          # Hs from spectrum area, peak position
python wave_loads/check_sea_state.py        # Hs, spreading, no repetition of wave groups
python wave_loads/check_vessel_data.py      # interpolation, physics of the drift table
python wave_loads/check_model.py            # drift points downwave, mirror symmetry
python wave_loads/check_waveloads_config.py # parameters from config build a model
python wave_loads/check_waveloads_fmu.py    # FMU code gives the same loads as the model
python wave_loads/run_waveloads.py          # 3-hour run with plots
```


## Recommended time step

The first-order loads vary with the wave period (5–10 s), so use a time step
of **0.5 s or less**.

---

## Known limitations

- Deep water (k = ω²/g).
- Zero vessel speed (DP).
- Drift between components uses Newman's approximation, not full QTFs.
- The spreading function depends only on direction, not on frequency.
- The vessel file must cover 0–360° in heading (no automatic mirroring).
- No interaction between waves and current.

## Open points

- [ ] Agree units with the vessel model: `heading` is in **radians**, `wave_direction_deg` in **degrees**.
- [ ] Agree which output the vessel model uses: total (`X, Y, N`) or drift only.
- [ ] Use the same vessel for all blocks. Now: wind uses the 88 m OSV in `vessel_config.py`, waves use Gunnerus.
- [ ] Ulstein data: write a converter to the JSON format in `vessels/`, and keep the data out of git (`vessels/ulstein/` in `.gitignore`).
- [ ] Move the settings in `Config/wave_config.py` into the shared config structure.


