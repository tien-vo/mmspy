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

``mmspy`` is distributed on the `Python package Index <https://pypi.org/>`_.
To install, run

.. code-block:: console

   pip install mmspy
