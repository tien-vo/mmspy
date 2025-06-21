"""Set up base directories."""

__all__ = ["CACHE_DIR", "STATE_DIR", "DATA_DIR"]

from pathlib import Path

from platformdirs import user_cache_dir, user_data_dir, user_state_dir

CACHE_DIR = Path(user_cache_dir("mmspy", ensure_exists=True))
STATE_DIR = Path(user_state_dir("mmspy", ensure_exists=True))
DATA_DIR = Path(user_data_dir("mmspy", ensure_exists=True))
