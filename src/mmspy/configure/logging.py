"""Set up logging utilities.

.. todo:: Add docstring.

"""

__all__ = ["enable_log"]

import logging
import sys

import pandas as pd

from mmspy.configure.config import DEFAULT_CONFIG_FILE, config
from mmspy.configure.paths import CACHE_DIR, DATA_DIR, STATE_DIR
from mmspy.configure.units import UNIT_DEFINITIONS


class IgnoreItspDimensionWarningsFilter(logging.Filter):
    """Filter ITSP warnings for dimension issues with L2 CDF files.

    The metadata in FGM, FSM and FEEPS raw CDF files have non-matching
    dimensions. There is nothing we can do except for opening a PR
    for `cdflib` or asking the instrument teams to regenerate files
    with corrected metadata. So for now, this filter is to ignore the
    ISTP warning messages until the issues are fixed.

    """

    def filter(self, record: logging.LogRecord) -> bool:
        """Filter message if patterns are detected."""

        def _is(string: str, instrument: str) -> bool:
            return instrument in string

        def _in_msg(pattern: str) -> bool:
            return (
                _is(record.msg, "fgm")
                or _is(record.msg, "fsm")
                or _is(record.msg, "feeps")
            ) and pattern in record.msg

        different_dimension = _in_msg("but they have different dimension")
        dimension_not_match = _in_msg("but the dimensions do not match")

        return not (different_dimension or dimension_not_match)


def _initialize_logging() -> None:
    logging.captureWarnings(True)

    console_formatter = logging.Formatter(
        fmt="{asctime} [{levelname:.4s}] {message}",
        datefmt="%y-%b-%d %H:%M:%S",
        style="{",
    )
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(console_formatter)

    logging.basicConfig(level=logging.DEBUG, handlers=[console_handler])

    logger = logging.getLogger("urllib3")
    logger.propagate = False

    logger = logging.getLogger("urllib3.connectionpool")
    logger.setLevel(logging.DEBUG)
    for handler in logger.handlers:
        logger.removeHandler(handler)

    logger.addHandler(console_handler)

    logger = logging.getLogger("cdflib.logging")
    logger.addFilter(IgnoreItspDimensionWarningsFilter())


def enable_log(file_name: str | None = None) -> None:
    if file_name is None:
        current_time = pd.Timestamp.today().strftime("%Y-%m-%d-%H-%M-%S")
        file_name = str(CACHE_DIR / f"{current_time}.log")

    file_formatter = logging.Formatter(
        fmt="{asctime} [{levelname:s} | {name:s}] {message}",
        datefmt="%y-%b-%d %H:%M:%S",
        style="{",
    )
    file_handler = logging.FileHandler(file_name, mode="w")
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(file_formatter)

    logger = logging.getLogger("")
    logger.addHandler(file_handler)
    logger.info(f"Log path: {file_name}")
    logger.debug(f"Config path: {config._file_name}")
    logger.debug(f"Default config file: {DEFAULT_CONFIG_FILE}")
    logger.debug(f"Unit definitions: {UNIT_DEFINITIONS}")
    logger.debug(f"Cache directory: {CACHE_DIR}")
    logger.debug(f"State directory: {STATE_DIR}")
    logger.debug(f"Data directory: {DATA_DIR}")

    logger = logging.getLogger("urllib3.connectionpool")
    logger.addHandler(file_handler)


_initialize_logging()
