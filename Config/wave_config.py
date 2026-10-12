"""
Settings for the waves block (wave_loads/).

TEMPORARY FILE: kept separate for now. When we align the config with the
rest of the group, each section below moves to the file named in its header.

Hs, Tp and wave direction are NOT here: they change during the simulation
and come from the environment (see enviroment_config.py).

The waves block only describes the sea. It does not know anything about the
vessel. The settings for calculating the forces on the vessel are in
wave_forces_config.py.
"""

# -- Direction convention  (later -> not needed) ------------------------------------
# classes.py already says Wave.direction_deg is "where the waves come from",
# so this is always True for our group.
DIRECTION_IS_FROM = True

# -- Sea description  (later -> extra fields in Wave, enviroment_config.py) ---------
SPECTRUM_TYPE = "jonswap"                          # "jonswap" or "pierson_moskowitz"
GAMMA = 3.3                                        # peak factor, only used for "jonswap"
SPREADING_TYPE = "cos2s"                           # "none" = long-crested, "cos2s" = short-crested
SPREADING_S = 1                                    # 1 = cos^2 (as DNV-ST-0111), 2 = ISSC. Higher = narrower

# -- Numerical settings  (later -> simulation_config.py) ----------------------------
N_DIRECTIONS = 11                                  # number of direction bins
DIRECTION_LIMIT_DEG = 90.0                         # use directions within +- this angle of the mean
N_FREQUENCIES = 30                                 # number of frequency bins (total = N_FREQUENCIES x N_DIRECTIONS)
OMEGA_MIN_FACTOR = 0.25                            # lowest frequency  = factor * peak frequency
OMEGA_MAX_FACTOR = 3.0                             # highest frequency = factor * peak frequency
RANDOM_FREQUENCIES = True                          # random frequency inside each bin (no repetition)
RANDOM_DIRECTIONS = True                           # random direction inside each bin
SEED = 123                                         # same seed = same sea

# Number of wave components the waves block sends out: the N_WAVES components
# with the most energy (Sørensen section 6.2.1, method 1). If the grid has fewer
# components (N_FREQUENCIES x N_DIRECTIONS), the rest are sent with amplitude 0.
#
# NB: N_WAVES decides how many outputs the FMU has (4 per wave). After changing
# it you must REBUILD the FMU and redo the connections in OspSystemStructure.xml.
# The FMU stops with an error message if it was built with another N_WAVES.
N_WAVES = 100
