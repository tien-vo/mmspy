"""Set up `logging`."""

import logging
import sys

import pandas as pd

from mmspy.utils.paths import CACHE_DIR

log = logging.getLogger(__name__)


def _configure_logging(current_time):
    logging.captureWarnings(True)

    file_formatter = logging.Formatter(
        fmt="%(asctime)s [%(levelname)s] (%(name)s): %(message)s",
        datefmt="%y-%b-%d %H:%M:%S",
    )
    file_name = CACHE_DIR / f"{current_time.strftime('%Y-%m-%d-%H-%M-%S')}.log"
    file_handler = logging.FileHandler(file_name, mode="w")
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(file_formatter)

    stream_formatter = logging.Formatter(
        fmt="%(asctime)s [%(levelname)s] (mmspy): %(message)s",
        datefmt="%y-%b-%d %H:%M:%S",
    )
    stream_handler = logging.StreamHandler(sys.stdout)
    stream_handler.setLevel(logging.INFO)
    stream_handler.setFormatter(stream_formatter)

    logging.basicConfig(
        level=logging.DEBUG,
        handlers=[file_handler, stream_handler],
    )

    log.info(f"Log path: {file_name}")
    return file_name


_configure_logging(pd.Timestamp.today())
