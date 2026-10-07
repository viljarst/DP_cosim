"""
Settings for the wave load block (wave_loads/).

TEMPORARY FILE: kept separate for now. When we align the config with the
rest of the group, each section below moves to the file named in its header.

Hs, Tp and wave direction are NOT here: they change during the simulation
and come from the environment (see enviroment_config.py).
"""

# -- Vessel hydrodynamic data  (later -> vessel_config.py) ------------------------
VESSEL_DATA_FILE = "vessels/gunnerus/gunnerus_vessel.json"  # relative to the repo folder
SPEED_INDEX = 0                                    # column in the speed table, 0 = zero speed (DP)
# Which table row is which DOF. Check this for every new vessel file!
FORCE_RAO_ROWS = {"surge": 0, "sway": 1, "yaw": 5}
DRIFT_ROWS = {"surge": 0, "sway": 1, "yaw": 2}     # Gunnerus: yaw drift is in row 2 (MSS layout)
RAO_AMPLITUDE = "absolute"                         # "absolute" (as mcsimpy) or "signed"

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

