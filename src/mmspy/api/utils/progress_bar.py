"""Configure the progress bar."""

__all__ = ["bar_config"]


def bar_config(**kwargs) -> dict:
    """Config for progress bar."""
    return {
        "bar_format": (
            "[{bar:16}] [{n_fmt}/{total_fmt} | {rate_fmt}]: " "{desc:50}"
        ),
        "dynamic_ncols": True,
        "leave": False,
        "ascii": "-#",
        **kwargs,
    }
