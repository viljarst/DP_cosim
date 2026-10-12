# Waves

The waves block for the DP simulator. It describes a **long-crested or
short-crested irregular sea** as a set of regular wave components, and sends
them to the vessel block. Packaged as an FMU (`WaveLoads.fmu`) for OSP.

The block does **not** calculate any forces. The forces on the vessel are
calculated in the vessel block from the wave components, see `../wave_forces/`.

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

### Outputs

Four numbers per wave component, for `i = 0, 1, ..., N_WAVES - 1`
(`N_WAVES` from `Config/wave_config.py`, now 100, so 400 outputs).
Component 0 has the most energy.

| Name | Unit | Description |
|---|---|---|
| `amplitude_i` | m | Wave amplitude (half the wave height) |
| `omega_i` | rad/s | Wave frequency |
| `phase_i` | rad | Phase |
| `direction_i` | **rad** | Direction the wave travels **to**, NED, 0 = north, clockwise |
| `kept_energy_fraction` | – | Share of the total wave energy in the components sent out (for logging) |

**The vessel block must use exactly this wave elevation** (same sign, cos and
time `t` as the simulation time):

```
zeta(x, y, t) = sum_i amplitude_i * cos(omega_i * t - k_i * (x cos(direction_i) + y sin(direction_i)) - phase_i)
k_i = omega_i^2 / g      (deep water)
```

where `x` is north and `y` is east. The components only change when `hs` or
`tp` changes (then the sea is built again) or when `wave_direction_deg`
changes (then all directions turn).

### Parameters (set once, before the simulation starts)

15 parameters, set by the cosimulation master from
`waveloads_config.get_waveloads_parameters()`. The FMU does **not** read the
config files itself, and refuses to run unless `configuration_loaded = 1`.

| Type | Parameters |
|---|---|
| Real | `configuration_loaded`, `gamma`, `spreading_s`, `direction_limit_deg`, `omega_min_factor`, `omega_max_factor` |
| Integer | `n_directions`, `n_frequencies`, `seed`, `n_waves` |
| Boolean | `direction_is_from`, `random_frequencies`, `random_directions` |
| String | `spectrum_type`, `spreading_type` |

> **Important for the master script:** each parameter must be set with the
> function for its FMI type (`real_initial_value`, `integer_initial_value`,
> `boolean_initial_value`, `string_initial_value` in libcosimpy). A value set
> with the wrong type is silently ignored by OSP.

### `N_WAVES` is special

An FMU has a fixed number of outputs, decided when it is **built**. So the
FMU reads `N_WAVES` from `Config/wave_config.py` when it is built (the file is
copied into the FMU). After changing `N_WAVES`:

1. rebuild the FMU,
2. redo the connections in `OspSystemStructure.xml` (4 per wave component).

If the config and the FMU do not agree, the FMU stops at the start of the
simulation with a message saying so.

---

## How it works

```
Hs, Tp
   ↓  spectra.py + sea_state.py: realize()
N_FREQUENCIES x N_DIRECTIONS wave components
   ↓  sea_state.py: keep_strongest()
the N_WAVES components with the most energy (Sørensen 6.2.1, method 1)
   ↓  sea_state.py: directions_to()   (+ mean wave direction)
amplitude, omega, phase, direction  ->  outputs
```

The amplitudes are **not** scaled up after the weakest components are
removed, so Hs of the components sent out is a little lower than the input
Hs. `kept_energy_fraction` says how much of the energy is kept.

## Files

| File | What it does |
|---|---|
| `spectra.py` | Wave spectra (Pierson–Moskowitz, JONSWAP) and the cos-2s spreading function |
| `sea_state.py` | Splits the spectrum into wave components, keeps the strongest, adds the mean direction |
| `waveloads_fmu.py` | The FMU shell: inputs, parameters, outputs, `do_step` |
| `waveloads_config.py` | Reads `Config/wave_config.py` and returns the parameter list for the FMU |
| `check_*.py` | Check scripts, one per file |

Settings are in `Config/wave_config.py` (spectrum, spreading, discretization,
`N_WAVES`). Hs, Tp and direction are in `Config/enviroment_config.py`.

---

## Build the FMU

From the repo folder, with the `dpcosim` environment active:

```
python -m pythonfmu build -f wave_loads/waveloads_fmu.py -d wave_loads/build wave_loads/sea_state.py wave_loads/spectra.py Config/wave_config.py
```

The FMU is written to `wave_loads/build/WaveLoads.fmu` (not in git). Rebuild
after every change to the `.py` files, and after changing `N_WAVES`.

**Requirements to run the FMU:**
- Windows or Linux. pythonfmu only includes `win64` and `linux64` binaries,
  so the FMU can be **built** on Mac but not **run** there.
- Python 3.11+ with `numpy` installed on the machine that runs the simulation.

## Check

Run from the repo folder. All of these work on Mac.

```
python wave_loads/check_spectra.py          # Hs from spectrum area, peak position
python wave_loads/check_sea_state.py        # Hs, spreading, repetition, strongest components, directions
python wave_loads/check_waveloads_config.py # parameters from config build the sea
python wave_loads/check_waveloads_fmu.py    # FMU outputs, new direction, calm sea, wrong N_WAVES
```

---

## Known limitations

- Deep water (k = ω²/g).
- The spreading function depends only on direction, not on frequency.
- A change in Tp during the simulation moves all frequencies, which gives a jump in the wave elevation.
- Keeping only the strongest components removes the short waves first. For a
  small vessel like Gunnerus these give much of the drift, so the drift is
  underestimated (see `wave_forces/check_model.py`).

## Open points

- [ ] How to handle the energy that is removed (scale the amplitudes up, or not) – asked Dong.
- [ ] Agree with the vessel block: `direction_i` is where the wave goes **to**, in **radians**.
- [ ] Move the settings in `Config/wave_config.py` into the shared config structure.
