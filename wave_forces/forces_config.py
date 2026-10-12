"""Parameters for the wave force calculation, read from the project config.

Also makes the files in Config/ and wave_loads/ importable, so the check
scripts in this folder can build wave components the same way the waves
FMU does. Import this file FIRST in every script in wave_forces/.
"""
import sys
from pathlib import Path

REPO_DIR = Path(__file__).resolve().parent.parent      # the DP_cosim folder
sys.path.insert(0, str(REPO_DIR / "Config"))           # standard.py, wave_forces_config.py, ...
sys.path.insert(0, str(REPO_DIR / "wave_loads"))       # sea_state.py, waveloads_config.py

import standard             # noqa: E402  (must come after the lines above)
import wave_forces_config   # noqa: E402


def get_wave_forces_parameters() -> dict:
    """Return the parameters needed by build_model() in model.py."""
    c = wave_forces_config
    return {
        "vessel_data_file": str(REPO_DIR / c.VESSEL_DATA_FILE),   # full path
        "speed_index": c.SPEED_INDEX,
        "force_rao_row_surge": c.FORCE_RAO_ROWS["surge"],
        "force_rao_row_sway": c.FORCE_RAO_ROWS["sway"],
        "force_rao_row_yaw": c.FORCE_RAO_ROWS["yaw"],
        "drift_row_surge": c.DRIFT_ROWS["surge"],
        "drift_row_sway": c.DRIFT_ROWS["sway"],
        "drift_row_yaw": c.DRIFT_ROWS["yaw"],
        "rao_amplitude": c.RAO_AMPLITUDE,
        "gravity": standard.G,
    }
