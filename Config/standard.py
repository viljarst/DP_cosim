"""
Standard values used in simulation.
"""

import numpy as np

RHO_AIR = 1.226  # kg/m^3, DNV-ST-0111 [3.5]
RHO_WATER = 1026.0  # kg/m^3, DNV-ST-0111 [3.6]
# m/s^2, used in the wave drift formulas [3.7]. The standard does not fix a
# value for g; this is our choice (HANDOVER.md, open decisions).
G = 9.81
TZ_FROM_TP = 1.4049  # Tp = 1.4049 * Tz for Pierson-Moskowitz with cos^2 spreading, [3.3.3]
DYNAMIC_FACTOR_LEVEL1 = 1.25  # applied to wind, current and wave loads, [3.2.2]
