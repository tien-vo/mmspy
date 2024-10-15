r"""Set up logging."""

import logging
from os import environ

logging.captureWarnings(True)
logging.basicConfig(
    format="%(asctime)s [%(levelname)s]: %(message)s",
    datefmt="%y-%b-%d %H:%M:%S",
    level="INFO" if not bool(environ.get("DEBUG")) else "DEBUG",
)
