r"""Configure logging functionality."""

__all__ = [
    "IgnoreFeepsIstpWarningsFilter",
    "LOGGING_CONFIG",
]

import logging
import logging.config
from os import environ


class IgnoreFeepsIstpWarningsFilter(logging.Filter):
    r"""Filter ITSP warnings for FEEPS.

    The metadata in FEEPS raw CDF files seem to be buggy right now.
    There is nothing we can do except for opening a PR for `cdflib`.
    So for now, this filter is to ignore the ISTP warning messages
    until the issues are fixed.

    """

    def filter(self, record: logging.LogRecord) -> bool:
        r"""Filter message if FEEPS patterns are detected."""

        def _in_msg(pattern: str) -> bool:
            return "feeps" in record.msg and pattern in record.msg

        different_dimension = _in_msg("but they have different dimension")
        dimension_not_match = _in_msg("but the dimensions do not match")

        return not (different_dimension or dimension_not_match)


LOGGING_CONFIG = {
    "version": 1,
    "disable_existing_loggers": True,
    "formatters": {
        "default": {
            "format": "%(asctime)s [%(levelname)s - %(name)s]: %(message)s",
            "datefmt": "%Y-%m-%d %H:%M:%S",
        },
    },
    "filters": {
        "ignore_feeps_warnings": {
            "()": IgnoreFeepsIstpWarningsFilter,
        },
    },
    "handlers": {
        "stderr": {
            "class": "logging.StreamHandler",
            "level": "INFO" if environ.get("DEBUG") is None else "DEBUG",
            "formatter": "default",
            "stream": "ext://sys.stderr",
            "filters": [
                "ignore_feeps_warnings",
            ],
        },
    },
    "loggers": {
        "root": {
            "level": "INFO" if environ.get("DEBUG") is None else "DEBUG",
            "handlers": [
                "stderr",
            ],
            "filters": [
                "ignore_feeps_warnings",
            ],
        },
        "cdflib.logging": {
            "level": "INFO" if environ.get("DEBUG") is None else "DEBUG",
            "handlers": [
                "stderr",
            ],
            "filters": [
                "ignore_feeps_warnings",
            ],
        },
    },
}
