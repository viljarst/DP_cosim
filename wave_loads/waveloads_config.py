"""Build the FMI parameter values for the WaveLoads FMU from the project config.

Same idea as Olve's windloads_config.py: the FMU does not read the config
files itself. This file reads them and returns a list of names and values
that the cosimulation master sets on the FMU before the simulation starts.
"""
import sys
from pathlib import Path

REPO_DIR = Path(__file__).resolve().parent.parent      # the DP_cosim folder
sys.path.insert(0, str(REPO_DIR / "Config"))           # so Python can find the files in Config/

import standard      # noqa: E402  (must come after the line above)
import wave_config   # noqa: E402


def get_waveloads_parameters() -> dict:
    """Return names and values to set on the WaveLoads FMU before initialization."""
    c = wave_config
    return {
        "configuration_loaded": 1.0,
        # vessel data
        "vessel_data_file": str(REPO_DIR / c.VESSEL_DATA_FILE),   # full path, so the FMU can find it
        "speed_index": c.SPEED_INDEX,
        "force_rao_row_surge": c.FORCE_RAO_ROWS["surge"],
        "force_rao_row_sway": c.FORCE_RAO_ROWS["sway"],
        "force_rao_row_yaw": c.FORCE_RAO_ROWS["yaw"],
        "drift_row_surge": c.DRIFT_ROWS["surge"],
        "drift_row_sway": c.DRIFT_ROWS["sway"],
        "drift_row_yaw": c.DRIFT_ROWS["yaw"],
        "rao_amplitude": c.RAO_AMPLITUDE,
        # physics and conventions
        "gravity": standard.G,
        "direction_is_from": c.DIRECTION_IS_FROM,
        # spectrum and spreading
        "spectrum_type": c.SPECTRUM_TYPE,
        "gamma": c.GAMMA,
        "spreading_type": c.SPREADING_TYPE,
        "spreading_s": c.SPREADING_S,
        "n_directions": c.N_DIRECTIONS,
        "direction_limit_deg": c.DIRECTION_LIMIT_DEG,
        # discretization
        "n_frequencies": c.N_FREQUENCIES,
        "omega_min_factor": c.OMEGA_MIN_FACTOR,
        "omega_max_factor": c.OMEGA_MAX_FACTOR,
        "random_frequencies": c.RANDOM_FREQUENCIES,
        "random_directions": c.RANDOM_DIRECTIONS,
        "seed": c.SEED,
    }