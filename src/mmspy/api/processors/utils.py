__all__ = [
    "center_timestamps",
    "shorten_variable_names",
    "alias_variable_names",
    "filter_variables",
]

import logging

import pandas as pd
import xarray as xr

from mmspy.configure.config import config
from mmspy.configure.units import units as u

log = logging.getLogger(__name__)


def center_timestamps(
    dataset: xr.Dataset,
    time_variable: str = "Epoch",
    plus_variable: str = "Epoch_PLUS",
    minus_variable: str = "Epoch_MINUS",
) -> xr.Dataset:
    """Center dataset timestamps.

    .. todo:: Add docstring.

    References
    ----------
    .. [1] :pytplot_center_time:`cdf_to_tplot.py#L195-L231`

    """

    def _in_dataset(variable: str) -> bool:
        if variable not in dataset:
            msg = f"{variable!r} not in dataset."
            log.warning(msg)
            return False

        return True

    if not (
        _in_dataset(time_variable)
        and _in_dataset(plus_variable)
        and _in_dataset(minus_variable)
    ):
        return dataset

    dataset = dataset.copy()

    plus = dataset[plus_variable].pint.quantify()
    minus = dataset[minus_variable].pint.quantify()
    dt = 0.5 * (plus - minus).data
    dt = dt.to("ns").magnitude.astype(int).astype("timedelta64[ns]")

    dataset[time_variable] = dataset[time_variable] + dt
    dataset[time_variable].attrs.update(CATDESC="Centered timestamps")

    return dataset


def shorten_variable_names(
    dataset: xr.Dataset,
    prefix: str | None = None,
    suffix: str | None = None,
) -> xr.Dataset:
    """Shorten variable names from {prefix}_{name}_{suffix} to {name}.

    .. todo:: Add docstring.

    """
    for name in dataset.data_vars:
        short = str(name)
        if bool(prefix):
            short = short.replace(f"{prefix}_", "")
        if bool(suffix):
            short = short.replace(f"_{suffix}", "")

        dataset = dataset.rename({name: short})

    return dataset


def alias_variable_names(dataset: xr.Dataset, instrument: str) -> xr.Dataset:
    """Look up config and alias variable names if their rule exist.

    .. todo:: Add docstring.

    """
    if not config.get("query/use_alias", default=False):
        return dataset

    aliases = config.get(f"{instrument}/aliases/variable").items()
    for value, alias in aliases:
        if value in dataset:
            dataset = dataset.rename({value: alias})
            dataset[alias].attrs.update(original_name=value)

    return dataset


def filter_variables(dataset: xr.Dataset, instrument: str) -> xr.Dataset:
    """Look up config and filter variables from the dataset.

    .. todo:: Add docstring.

    """
    variables = config.get(f"{instrument}/variables", default=None)
    if variables is None or variables == "all":
        return dataset

    return dataset[[variable for variable in variables if variable in dataset]]
