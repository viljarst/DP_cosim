"""WaveLoads FMU: the wave load model wrapped as an FMU for OSP.

All the physics is in model.py (and sea_state.py, spectra.py, vessel_data.py).
This file only:
  1. declares the inputs, parameters and outputs of the FMU,
  2. builds the model once, when the simulation starts,
  3. calls the model in every time step.

Build (from the repo folder). All the .py files the model needs must be listed:
  python -m pythonfmu build -f wave_loads/waveloads_fmu.py -d wave_loads/build wave_loads/model.py wave_loads/sea_state.py wave_loads/spectra.py wave_loads/vessel_data.py

The FMU does not read the config files. The cosimulation master must set the
parameters from waveloads_config.get_waveloads_parameters() before the
simulation starts, and set configuration_loaded = 1.
"""
import math

from pythonfmu import Boolean, Fmi2Causality, Fmi2Slave, Fmi2Variability, Integer, Real, String

from model import build_model

# Parameter names and types. Must match get_waveloads_parameters() in waveloads_config.py.
REAL_PARAMETERS = ("configuration_loaded", "gravity", "gamma", "spreading_s", "direction_limit_deg",
                   "omega_min_factor", "omega_max_factor")
INTEGER_PARAMETERS = ("speed_index", "force_rao_row_surge", "force_rao_row_sway", "force_rao_row_yaw",
                      "drift_row_surge", "drift_row_sway", "drift_row_yaw",
                      "n_directions", "n_frequencies", "seed")
BOOLEAN_PARAMETERS = ("direction_is_from", "random_frequencies", "random_directions")
STRING_PARAMETERS = ("vessel_data_file", "rao_amplitude", "spectrum_type", "spreading_type")

INPUTS = ("hs", "tp", "wave_direction_deg", "north", "east", "heading")
OUTPUTS = ("X", "Y", "N",                       # total wave load = first order + drift
           "X_first", "Y_first", "N_first",     # first-order (wave-frequency) part
           "X_drift", "Y_drift", "N_drift")     # drift (mean + slowly varying) part


class WaveLoads(Fmi2Slave):

    author = "Viljar Simonnes Tveit"
    description = "Wave loads (first order + drift) on a vessel in short-crested sea"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.model = None                        # built in exit_initialization_mode()

        # -- Inputs: change during the simulation ------------------------------------
        self.hs = 0.0                  # significant wave height [m]
        self.tp = 0.0                  # peak period [s]
        self.wave_direction_deg = 0.0  # mean wave direction [deg], where the waves come from, 0 = north
        self.north = 0.0               # vessel position north [m]
        self.east = 0.0                # vessel position east [m]
        self.heading = 0.0             # vessel heading psi [rad], 0 = north
        for name in INPUTS:
            self.register_variable(Real(name, causality=Fmi2Causality.input))

        # -- Parameters: set once, before the simulation starts ----------------------
        # The start values are only placeholders. The real values come from the config.
        for name in REAL_PARAMETERS:
            setattr(self, name, 0.0)
            self.register_variable(Real(name, causality=Fmi2Causality.parameter,
                                        variability=Fmi2Variability.fixed))
        for name in INTEGER_PARAMETERS:
            setattr(self, name, 0)
            self.register_variable(Integer(name, causality=Fmi2Causality.parameter,
                                           variability=Fmi2Variability.fixed))
        for name in BOOLEAN_PARAMETERS:
            setattr(self, name, False)
            self.register_variable(Boolean(name, causality=Fmi2Causality.parameter,
                                           variability=Fmi2Variability.fixed))
        for name in STRING_PARAMETERS:
            setattr(self, name, "")
            self.register_variable(String(name, causality=Fmi2Causality.parameter,
                                          variability=Fmi2Variability.fixed))

        # -- Outputs: the loads in the body frame [N, N, Nm] -------------------------
        for name in OUTPUTS:
            setattr(self, name, 0.0)
            self.register_variable(Real(name, causality=Fmi2Causality.output))

    def exit_initialization_mode(self):
        """Called once, after the parameters are set and before the first step."""
        if self.configuration_loaded != 1.0:
            raise RuntimeError(
                "The cosimulation host must set configuration_loaded=1 after "
                "applying all WaveLoads parameters from the config."
            )
        parameters = {name: getattr(self, name)
                      for name in REAL_PARAMETERS + INTEGER_PARAMETERS + BOOLEAN_PARAMETERS + STRING_PARAMETERS}
        self.model = build_model(parameters)

    def do_step(self, current_time, step_size):
        """Called once per time step."""
        t = current_time + step_size             # the outputs are for the end of the step
        self.model.set_sea_state(self.hs, self.tp, math.radians(self.wave_direction_deg))
        eta = (self.north, self.east, self.heading)
        first, drift = self.model.loads(t, eta)

        self.X_first, self.Y_first, self.N_first = first
        self.X_drift, self.Y_drift, self.N_drift = drift
        self.X = self.X_first + self.X_drift
        self.Y = self.Y_first + self.Y_drift
        self.N = self.N_first + self.N_drift
        return True