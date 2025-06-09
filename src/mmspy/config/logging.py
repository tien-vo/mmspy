r"""Set up `logging`."""

__all__ = ["configure_logger"]

import logging
import sys


def configure_logger(cache_directory):
    logging.captureWarnings(True)

    file_handler = logging.FileHandler(cache_directory / "log", mode="a")
    file_handler.setLevel(logging.DEBUG)

    stream_handler = logging.StreamHandler(sys.stdout)
    stream_handler.setLevel(logging.INFO)

    logging.basicConfig(
        format="%(asctime)s [%(levelname)s]: %(message)s",
        datefmt="%y-%b-%d %H:%M:%S",
        level=logging.DEBUG,
        handlers=[file_handler, stream_handler],
    )
