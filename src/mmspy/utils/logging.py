"""Set up `logging`."""

__all__ = ["log"]

import logging
import sys

import pandas as pd

from mmspy.utils.config import config, default_config_file
from mmspy.utils.paths import CACHE_DIR, DATA_DIR, STATE_DIR
from mmspy.utils.pint import unit_definitions


def _initialize_logging():
    logging.captureWarnings(True)

    stream_formatter = logging.Formatter(
        fmt="{asctime} [{levelname:^10s}]: {message}",
        datefmt="%y-%b-%d %H:%M:%S",
        style="{",
    )
    stream_handler = logging.StreamHandler(sys.stdout)
    stream_handler.setLevel(logging.INFO)
    stream_handler.setFormatter(stream_formatter)

    logging.basicConfig(level=logging.DEBUG, handlers=[stream_handler])


def log(file_name: str | None = None):
    if file_name is None:
        current_time = pd.Timestamp.today().strftime("%Y-%m-%d-%H-%M-%S")
        file_name = CACHE_DIR / f"{current_time}.log"

    file_formatter = logging.Formatter(
        fmt="{asctime} [{levelname:^10s}]: {message}",
        datefmt="%y-%b-%d %H:%M:%S",
        style="{",
    )
    file_handler = logging.FileHandler(file_name, mode="w")
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(file_formatter)

    root_logger = logging.getLogger("mmspy")
    root_logger.addHandler(file_handler)
    root_logger.info(f"Log path: {file_name}")
    root_logger.debug(f"Config path: {config._file_name}")
    root_logger.debug(f"Default config file: {default_config_file}")
    root_logger.debug(f"Unit definitions: {unit_definitions}")
    root_logger.debug(f"Cache directory: {CACHE_DIR}")
    root_logger.debug(f"State directory: {STATE_DIR}")
    root_logger.debug(f"Data directory: {DATA_DIR}")


_initialize_logging()
