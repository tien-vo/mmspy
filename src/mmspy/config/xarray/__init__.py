"""Configure `xarray` and provide accessors to datasets."""

import xarray as xr

xr.set_options(keep_attrs=True)

from mmspy.config.xarray.edp import EdpAccessor
from mmspy.config.xarray.fgm import FgmAccessor
from mmspy.config.xarray.fpi import FpiAccessor
from mmspy.config.xarray.feeps import FeepsAccessor
from mmspy.config.xarray.species import SpeciesAccessor
from mmspy.config.xarray.tensors import TensorAccessor
