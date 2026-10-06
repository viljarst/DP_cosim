from pythonfmu import Fmi2Causality, Fmi2Slave, Real


class WaveLoads(Fmi2Slave):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.hs = 0.0  # inngang: bølgehøyde [m]
        self.X = 0.0   # utgang: kraft [N]

        self.register_variable(Real("hs", causality=Fmi2Causality.input))
        self.register_variable(Real("X", causality=Fmi2Causality.output))

    def do_step(self, current_time, step_size):
        self.X = 1000.0 * self.hs  # midlertidig: bare for å se at noe skjer
        return True