"""
Settings for the wave force calculation (wave_forces/).

TEMPORARY FILE. The wave forces will be calculated in the vessel block, so
these settings move to vessel_config.py when the code is moved there.
They used to be in wave_config.py.
"""

# -- Vessel hydrodynamic data -------------------------------------------------------
VESSEL_DATA_FILE = "vessels/gunnerus/gunnerus_vessel.json"  # relative to the repo folder
SPEED_INDEX = 0                                    # column in the speed table, 0 = zero speed (DP)
# Which table row is which DOF. Check this for every new vessel file!
FORCE_RAO_ROWS = {"surge": 0, "sway": 1, "yaw": 5}
DRIFT_ROWS = {"surge": 0, "sway": 1, "yaw": 2}     # Gunnerus: yaw drift is in row 2 (MSS layout)
RAO_AMPLITUDE = "absolute"                         # "absolute" (as mcsimpy) or "signed"
