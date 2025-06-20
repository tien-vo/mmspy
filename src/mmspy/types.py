"""Define common types"""

from collections.abc import Callable, Hashable, Iterable, Sequence
from datetime import date
from numbers import Number
from pathlib import Path
from typing import TYPE_CHECKING, Any, Hashable, TypeVar, Union

import numpy as np
import pint
from numpy.typing import ArrayLike, NDArray
from xarray.core.types import Dims, T_DataArray, T_Dataset, T_Xarray

if TYPE_CHECKING:
    from mmspy.api.utils.file import CdfFile

FractionComponent = Iterable[tuple[str, Number]]

Date = float | str | date | np.datetime64

Unit = pint.util.UnitsContainer
Quantity = pint.Quantity
Registry = pint.UnitRegistry

T_File = TypeVar("T_File", bound=Union["CdfFile", Path])
