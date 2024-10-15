r"""Miscellaneous utilities.

.. todo:: Add docstring.
"""


def bar_config(**kwargs) -> dict:
    r""".. todo:: Add docstring."""
    return {
        "bar_format": (
            "[{bar:16}] [{n_fmt}/{total_fmt} | {rate_fmt}]: "
            "{desc:50}"
        ),
        "dynamic_ncols": True,
        "leave": True,
        "ascii": "-#",
        **kwargs,
    }
