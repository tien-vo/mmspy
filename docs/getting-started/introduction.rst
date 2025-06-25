Introduction
============

Why another space physics software?
-----------------------------------

At the moment, there are already a couple of well-developed Python
libraries for loading space physics data, such as
`PySPEDAS <pyspedas_>`_,
`Speasy <https://speasy.readthedocs.io/en/latest/>`_, and 
`SciQLop <https://sciqlop.github.io/>`_. However, there is
a lack of Python utility for direct interactions with the RESTful API
provided by the `MMS Science Data Center (SDC)
<https://lasp.colorado.edu/mms/sdc/public/>`_. Inspired by
the Python package for CDAS web services,
`cdasws`_, this package
intends to provide access to the MMS SDC web services at LASP and fills
in that gap.

While the core functionality of `mmspy` does not differ much from that
of `PySPEDAS <pyspedas_>`_, which is to provide data from a repository to
space physics researchers, it puts focus on the broader
`Xarray ecosystem <https://xarray.dev/#ecosystem>`_ for
distributed and parallel computing with
`Dask <dask_>`_, performant I/O with
`Zarr <zarr_>`_, and automatic
unit handling with `Pint <pint_>`_. These
features aim to make the most out of metadata provided in CDF files
and make analysis of MMS data more intuitive, efficient, and scalable.

.. _pyspedas: https://pyspedas.readthedocs.io/en/latest/
.. _dask: https://docs.dask.org/en/stable/
.. _zarr: https://zarr.readthedocs.io/en/stable/
.. _pint: https://pint.readthedocs.io/en/stable/
.. _cdasws: https://cdaweb.gsfc.nasa.gov/WebServices/REST/

Installation
------------

Required dependencies
~~~~~~~~~~~~~~~~~~~~~

- `python <https://www.python.org/>`__ (>=3.11)
- `numpy <https://www.numpy.org/>`__ (>=2.2.6)
- `scipy <https://scipython.com/>`__ (>=1.15.3)
- `xarray <https://xarray.dev/>`__ (>=2025.4.0,<2026.0.0)
- `dask[distributed] <https://www.dask.org/>`__ (>=2025.5.1,<2026.0.0)
- `zarr <https://zarr.readthedocs.io/en/stable/>`__ (2.18.5)
- `cdflib <https://cdflib.readthedocs.io/en/latest/>`__ (>=1.3.4,<2.0.0))
- `attrs <https://www.attrs.org/en/stable/>`__ (>=25.3.0,<26.0.0)
- `pint-xarray <https://pint-xarray.readthedocs.io/en/stable/>`__ (>=0.4,<0.5)
- `tqdm <https://tqdm.github.io/>`__ (>=4.67.1,<5.0.0)
- `matplotlib <https://matplotlib.org/>`__ (>=3.10.3)
- `requests <https://requests.readthedocs.io/en/latest/>`__ (>=2.32.3)
- `pathos <https://pathos.readthedocs.io/en/latest/pathos.html>`__ (>=0.3.4)
- `bigtree <https://bigtree.readthedocs.io/stable/>`__ (>=0.29.2)
- `bs4 <https://www.crummy.com/software/BeautifulSoup/>`__ (>=0.0.2)
- `python-benedict[toml] <https://github.com/fabiocaccamo/python-benedict>`__ (>=0.34.1)
- `numcodecs <https://github.com/zarr-developers/numcodecs>`__ (0.15.1)
- `rocket-fft <https://github.com/styfenschaer/rocket-fft>`__ (>=0.2.5)
- `astropy <https://www.astropy.org/>`__ (>=7.1.0)


Instructions
~~~~~~~~~~~~

`mmspy` is distributed on the `Python package Index (PyPI)
<https://pypi.org/>`_. To install, run:

.. code-block:: console

   pip install mmspy
