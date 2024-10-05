mmsws
=====

A Python API for LASP MMS Science Data Center (SDC) web services

About
-----

This is a public mirror of an in-development Python package for
querying and analyzing data from the
[NASA Magnetospheric Multiscale mission.](https://mms.gsfc.nasa.gov/)
At the moment, the public package is extremely barebone with limited
utilities. Future release will be updated alongside publications
with specific use cases and specialized calculations.

Currently, there are a few well-developed alternatives for the above
purposes, such as [PySPEDAS](https://github.com/spedas/pyspedas)
and [CdaWs](https://pypi.org/project/cdasws/). However, there is a
lack of Python utility for direct interactions with the RESTful API
provided by the
[LASP Science Data Center](https://lasp.colorado.edu/mms/sdc/public/).

This package is intended to fill in that gap. In addition, `mmsws` is
developed to fully utilize the power of [xarray](https://xarray.dev/),
[zarr](https://zarr.dev/), and [dask](https://www.dask.org/) for
scalable data analysis. More updates to come in the near future.
