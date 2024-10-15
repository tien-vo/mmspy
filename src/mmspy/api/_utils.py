r"""Miscellaneous utilities.

.. todo:: Add docstring.
"""


def bar_config(**kwargs) -> dict:
    r""".. todo:: Add docstring."""
    return {
        "bar_format": (
            "[{bar:20}] | {desc:70} "
            "[{n_fmt}/{total_fmt} | {percentage:.0f}% | {rate_fmt}]"
        ),
        "dynamic_ncols": True,
        "leave": True,
        "ascii": "-#",
        **kwargs,
    }
