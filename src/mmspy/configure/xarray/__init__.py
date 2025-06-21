"""Configure `xarray` and provide accessors to datasets."""

import xarray as xr

xr.set_options(keep_attrs=True)

from mmspy.configure.xarray.edp import EdpAccessor
from mmspy.configure.xarray.fgm import FgmAccessor
from mmspy.configure.xarray.fpi import FpiAccessor
from mmspy.configure.xarray.feeps import FeepsAccessor
from mmspy.configure.xarray.species import SpeciesAccessor
from mmspy.configure.xarray.tensors import TensorAccessor
