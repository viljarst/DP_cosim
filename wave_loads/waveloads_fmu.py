"""Waves FMU: describes the sea as a set of regular wave components.

The FMU only describes the sea. It does NOT calculate any forces on the
vessel: that is done in the vessel block, from the wave components this FMU
sends out (see wave_forces/ for the code).

All the physics is in sea_state.py and spectra.py. This file only:
  1. declares the inputs, parameters and outputs of the FMU,
  2. builds the sea when Hs or Tp changes,
  3. writes the wave components to the outputs in every time step.

Build (from the repo folder). All the .py files the FMU needs must be listed,
including Config/wave_config.py, which decides how many outputs the FMU gets:
  python -m pythonfmu build -f wave_loads/waveloads_fmu.py -d wave_loads/build wave_loads/sea_state.py wave_loads/spectra.py Config/wave_config.py

The FMU does not read the config files. The cosimulation master must set the
parameters from waveloads_config.get_waveloads_parameters() before the
simulation starts, and set configuration_loaded = 1.
"""
import sys
from pathlib import Path

from pythonfmu import Boolean, Fmi2Causality, Fmi2Slave, Fmi2Variability, Integer, Real, String

from sea_state import directions_to, sea_from_parameters

# The number of wave components decides how many outputs the FMU has, and that
# must be fixed when the FMU is built. It is read from Config/wave_config.py:
#   - when building:        from the Config folder
#   - when running in OSP:  from the copy of wave_config.py inside the FMU
try:
    import wave_config
except ModuleNotFoundError:
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "Config"))
    import wave_config
N_WAVES_BUILT = wave_config.N_WAVES

# Parameter names and types. Must match get_waveloads_parameters() in waveloads_config.py.
REAL_PARAMETERS = ("configuration_loaded", "gamma", "spreading_s", "direction_limit_deg",
                   "omega_min_factor", "omega_max_factor")
INTEGER_PARAMETERS = ("n_directions", "n_frequencies", "seed", "n_waves")
BOOLEAN_PARAMETERS = ("direction_is_from", "random_frequencies", "random_directions")
STRING_PARAMETERS = ("spectrum_type", "spreading_type")

INPUTS = ("hs", "tp", "wave_direction_deg")

# Outputs: four numbers per wave component, numbered 0, 1, ..., N_WAVES_BUILT - 1.
# Component 0 has the most energy.
COMPONENT_OUTPUTS = ("amplitude",    # wave amplitude [m] (half the wave height)
                     "omega",        # frequency [rad/s]
                     "phase",        # phase [rad]
                     "direction")    # direction the wave travels TO [rad], NED, 0 = north, clockwise


class WaveLoads(Fmi2Slave):

    author = "Viljar Simonnes Tveit"
    description = "Short-crested irregular sea as a set of regular wave components"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.sea = None                          # the current wave components
        self.kept_energy_fraction = 1.0          # share of the energy in the components sent out
        self._built_for = None                   # (hs, tp) the sea was built for

        # -- Inputs: change during the simulation ------------------------------------
        self.hs = 0.0                  # significant wave height [m]
        self.tp = 0.0                  # peak period [s]
        self.wave_direction_deg = 0.0  # mean wave direction [deg], where the waves come from, 0 = north
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

        # -- Outputs: the wave components ----------------------------------------------
        # amplitude_0, omega_0, phase_0, direction_0, amplitude_1, ...
        for i in range(N_WAVES_BUILT):
            for quantity in COMPONENT_OUTPUTS:
                name = f"{quantity}_{i}"
                setattr(self, name, 0.0)
                self.register_variable(Real(name, causality=Fmi2Causality.output))
        # Share of the total wave energy in the components sent out (for logging)
        self.register_variable(Real("kept_energy_fraction", causality=Fmi2Causality.output))

    def _parameters(self):
        """All parameters as a dict, with the same names as in waveloads_config.py."""
        names = REAL_PARAMETERS + INTEGER_PARAMETERS + BOOLEAN_PARAMETERS + STRING_PARAMETERS
        return {name: getattr(self, name) for name in names}

    def exit_initialization_mode(self):
        """Called once, after the parameters are set and before the first step."""
        if self.configuration_loaded != 1.0:
            raise RuntimeError(
                "The cosimulation host must set configuration_loaded=1 after "
                "applying all WaveLoads parameters from the config."
            )
        if self.n_waves != N_WAVES_BUILT:
            raise RuntimeError(
                f"The config says n_waves = {self.n_waves}, but this FMU was built for "
                f"{N_WAVES_BUILT} wave components. Rebuild the FMU after changing N_WAVES, "
                f"and redo the connections in OspSystemStructure.xml."
            )

    def do_step(self, current_time, step_size):
        """Called once per time step.

        The wave components do not depend on time: the vessel block uses them to
        calculate zeta = amplitude * cos(omega * t - k * (x cos(direction) + y sin(direction)) - phase).
        So the sea is only built again when Hs or Tp changes.
        """
        if (self.hs, self.tp) != self._built_for:
            self.sea, self.kept_energy_fraction = sea_from_parameters(self.hs, self.tp, self._parameters())
            self._built_for = (self.hs, self.tp)

        directions = directions_to(self.sea, self.wave_direction_deg, self.direction_is_from)
        for i in range(N_WAVES_BUILT):
            setattr(self, f"amplitude_{i}", float(self.sea.amplitudes[i]))
            setattr(self, f"omega_{i}", float(self.sea.frequencies[i]))
            setattr(self, f"phase_{i}", float(self.sea.phases[i]))
            setattr(self, f"direction_{i}", float(directions[i]))
        return True
