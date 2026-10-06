from pythonfmu import Fmi2Causality, Fmi2Slave, Real


def wave_force(hs):
    """Physics goes here. Plain Python, no FMU code."""
    return 1000.0 * hs

class WaveLoads(Fmi2Slave):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.hs = 0.0  # inngang: bølgehøyde [m]
        self.X = 0.0   # utgang: kraft [N]

        self.register_variable(Real("hs", causality=Fmi2Causality.input))
        self.register_variable(Real("X", causality=Fmi2Causality.output))

    
    def do_step(self, current_time, step_size):
        self.X = wave_force(self.hs)
        return True