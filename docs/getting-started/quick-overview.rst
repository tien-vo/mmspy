Quick overview
==============

As an overview, `mmspy` utilizes `zarr` as the data format to convert
from CDF files and store on disk. In memory, the data are openned
and wrapped, in order, with `dask.array.Array` for automatic
chunking and lazily evaluated parallel operations, `pint.Quantity`
for unit handling and conversion, and `xarray.DataArray` for
dimensions and coordinates labeling, with all metadata preserved
from CDF files.

In the following, we show how MMS datasets are loaded with `mmspy` and
the basics of each of the feature. Users are encouraged to familiarize
at least with `xarray`'s basic `data structures <xarray_structures_>`_.
While knowledge of `pint`_ and `dask`_ internals are good to know,
there is generally no need to dig too deep into it, since all the
main features can be accessed via `xarray`.

Query parameters and data stores
--------------------------------

The two main components of `mmspy` are `mmspy.query` and `mmspy.store`.
The former is an interface for setting the query parameters for the
`LASP SDC web services <sdc_>`_. The latter is an interface for managing
both local (on machine) and remote (on the SDC) storages
(aka data 'stores'). By default, `mmspy.store` is set to the system's
data path:

.. jupyter-execute::

    import mmspy as mms

    mms.store.show()

The path can be changed, for example, by setting:

.. jupyter-execute::

    mms.store.path = "./data.zarr"
    mms.store.show()

.. note::
    By default, a ``'local'`` store is always initialized under the
    root directory.

`mmspy.store` handles the synchronization from the `remote store
<remote_>`_ to the ``'local'`` store, wherein CDF files from the
`remote <remote_>`_ are converted to `zarr` storages locally.
`mmspy.store` also manages the reading and writing of MMS datasets from
*any data store* under the root path.

By default, `mmspy.query` is empty:

.. jupyter-execute::

    mms.query.show()

It is a good idea to browse the `remote store in the SDC <remote_>`_ 
(and the documentation for `~mmspy.api.query.Query`) to
get an idea of what values for query parameters are allowed. Typically,
the CDF files are organized as
``probe/instrument/data_rate/data_level/data_type/**/*.cdf``
on the SDC, which will be converted to
``probe/instrument/data_type/data_rate/data_level/zarr_*`` locally.

.. note::
    The order of the local path is inverted to put ``data_type``
    after ``instrument``, because typically ``data_rate`` and ``data_level``
    do not vary much in the same project.

Loading MMS datasets
--------------------

`mmspy` provides a high-level `mmspy.load()` method that handles `mmspy.query`
and `mmspy.store` under the hood. `mmspy.load()` takes
`~mmspy.api.query.Query` parameters as arguments and returns a
(`pint quantified <xarray_pint_blog>`_) `xarray.Dataset`.

To get the Fluxgate Magnetometers (FGM) dataset, run:

.. jupyter-execute::

    fgm = mms.load(
        store="remote",
        start_time="2015-10-16T08:00:00",
        stop_time="2015-10-16T14:00:00",
        probe="mms1",
        instrument="fgm",
        data_rate="srvy",
        data_level="l2",
    )

`mmspy.store` should now show the `zarr` files on the local storage:

.. jupyter-execute::

    mms.store.show("*")

Unpacking Xarray components
~~~~~~~~~~~~~~~~~~~~~~~~~~~

Exploring the ``fgm`` dataset:

.. jupyter-execute::

    fgm

we see that it is described by ``Dimensions``, ``Coordinates``,
``Data variables``, and ``Attributes``. `Dimensions <dimension_>`_ describe
the shape (degrees of freedom) of arrays.
`Coordinates <coordinate_>`_ label the `dimensions <dimension_>`_, and
there can be many `coordinates <coordinate_>`_ along each
`dimension <dimension_>`_. `Data variables <variable_>`_ are described
by both `dimensions <dimension_>`_ and `coordinates <coordinate_>`_, as
well as their :py:attr:`~xarray.DataArray.data`. Attributes contain the
metadata describing a `~xarray.Dataset` or `~xarray.DataArray`.

Let us print a variable from the ``fgm`` dataset, say the GSE magnetic
field:

.. jupyter-execute::

    fgm.b_gse

``b_gse`` has its own `dimensions <dimension_>`_ (``time`` and ``rank_1``,
i.e., the spatial components), `coordinates <coordinate_>`_
(time stamps and ``x,y,z`` labels), and has its own
:py:attr:`~xarray.DataArray.attrs` attached.

Let us examine its :py:attr:`~xarray.DataArray.data`:

.. jupyter-execute::

    fgm.b_gse.data

This is a `pint.Quantity` which, somewhat similar to
`astropy.units.Quantity`, is an array with :py:attr:`~pint.Quantity.units`
and :py:attr:`~pint.Quantity.magnitude` properties. Peeling further:

.. jupyter-execute::

    fgm.b_gse.data.magnitude

is a `dask.array.Array`, which gives a `numpy.ndarray` when calling
:py:func:`~dask.compute()`:

.. jupyter-execute::
    
    fgm.b_gse.data.magnitude.compute()

To see what steps :py:func:`~dask.compute()` take to produce this
`numpy.ndarray`, examine the
`dask task graph <https://docs.dask.org/en/stable/graphs.html>`_:

.. jupyter-execute::
    
    fgm.b_gse.data.magnitude.dask

Instead of evaluating operations for numerical results, `dask`_ calculates
`task graphs <https://docs.dask.org/en/stable/graphs.html>`_
that plan out the calculations for each data chunk (and how to merge them).
Task graphs are automatically optimized and are evaluated when
:py:func:`~dask.compute()` is called. In the
`dask integration <dask_integration_>`_ section below, we provide
an example of calculating a complicated graph.

Note that in regular usage, a user does not need to perform the
above decomposition steps, since both `pint.Quantity` and `dask.array.Array`
are exposed in `xarray` API. :py:func:`~dask.compute()` can be called on
`xarray.Dataset` and `xarray.DataArray`:

.. jupyter-execute::
    
    fgm.b_gse.compute()

The :py:attr:`~pint.Quantity.units` and :py:attr:`~pint.Quantity.magnitude`
properties can be accessed via the `pint` `accessor <accessors_>`_:

.. jupyter-execute::

    fgm.b_gse.pint.units

.. jupyter-execute::

    fgm.b_gse.pint.magnitude

as well as unit conversion:

.. jupyter-execute::

    fgm.b_gse.pint.to("T")


Switching data store
~~~~~~~~~~~~~~~~~~~~

One can now load ``fgm`` directly from ``'local'`` instead of having to
synchronize with ``'remote'``:

.. jupyter-execute::

    fgm = mms.load(
        store="local",
        start_time="2015-10-16T08:00:00",
        stop_time="2015-10-16T14:00:00",
        probe="mms1",
        instrument="fgm",
        data_rate="srvy",
        data_level="l2",
    )
    fgm

.. note::
    By default, when `mmspy.load(store="remote")` is called a second
    time, `mmspy` checks if the local `zarr` files are updated with
    the remote, and calls `mmspy.load(store="local")` if they are to
    avoid downloading the same file twice.

Note that this makes it very convenient to switch between ``'remote'``
and ``'local'``, and any secondary (or tertiary, and so on and so forth)
data stores. This allows a research project to mutate and combine
different MMS datasets through many stages to obtain
publication-worthy results! More on this later.

Persistent query
~~~~~~~~~~~~~~~~

When provided as arguments for `mmspy.load()`, the query parameters are
not remembered. Thus, after the `~mmspy.load()` call is finished,
`mmspy.query` is still empty:

.. jupyter-execute::

    mms.query.show()

To make the query persistent, assign the parameters directly into
`mmspy.query`:

.. jupyter-execute::

    mms.query.start_time = "2015-10-16T08:00:00"
    mms.query.stop_time = "2015-10-16T14:00:00"
    mms.query.probe = "mms1"
    mms.query.data_rate = "fast"
    mms.query.data_level = "l2"
    mms.query.show()

This shortens the necessary parameters to specify for later
`~mmspy.load()` calls. For example, the Electric Double Probes
(EDP) dataset can be loaded with:

.. jupyter-execute::

    edp = mms.load(instrument="edp", data_type="dce")
    edp

Similarly, ion moments from the Fast Plasma Investigation (FPI):

.. jupyter-execute::

    ion_fpi = mms.load(instrument="fpi", data_type="dis-moms")
    ion_fpi

FEEPS dataset
~~~~~~~~~~~~~

FGM, EDP, and FPI datasets are mostly simple in terms of metadata.
However, FEEPS is one of more complicated cases where the variables and
metadata in the CDF files can be overwhelming. `mmspy` provides an
automatic autoformatting that turns the FEEPS dataset into a more
readable form (without altering the data):

.. jupyter-execute::

    ion_feeps = mms.load(instrument="feeps", data_rate="srvy", data_type="ion")
    ion_feeps


Masking flagged data
~~~~~~~~~~~~~~~~~~~~

Data from the level-2 CDF files are not fault-free, and many 
instruments have caveats that one should read about in the `product
guides <product_guide_>`_ before using the data. `mmspy` provides
instrument-specific `xarray accessors <accessors_>`_ (`fgm`, `edp`, `fpi`,
`feeps`) that allows for automatic data masking in accordance with the
`Calibration and Measurement Algorithms document (CMAD)
<https://hpde.io/NASA/Document/MMS/CMAD.html>`_ and in consistency with
`PySPEDAS <pyspedas_>`_. The FEEPS masking is the most complicated,
which uses multiple time-dependent and time-independent energy tables.
Simply call the following and bad eyes will be set to ``NaN``:

.. jupyter-execute::

    ion_feeps = ion_feeps.feeps.mask_data()
    ion_feeps

.. _units:

Unit handling and conversions
-----------------------------

`astropy.units <astropy_units_>`_ is the more common library for units
handling. However, `xarray` currently cannot wrap astropy quantities
until `Quantity 2.0 <quantity_2_>`_ is implemented. Thus, `mmspy`
resorts to utilizing `pint`_ and `pint-xarray <pint_xarray_>`_ for units
handling and conversions. One setback is that `pint`_ does not accept
`FITS-compliant <fits_>`_ strings. Thus, users familiar with
`astropy.units <astropy_units_>`_ may find it difficult to migrate to
`pint`_. As a resolution, `mmspy` implements a custom `pint`_ formatter
that makes the `pint`_ experience as close to that of
`astropy.units <astropy_units_>`_ as much as possible. This formatter is
initialized when `mmspy` is imported.

Below is an example of using the custom `mmspy.units` registry
for calculating the ion cyclotron frequency:

.. jupyter-execute::

    from mmspy import units as u

    background_field = u.Quantity(50.0, "nT")
    proton_gyrofrequency = (u.e * background_field / u.m_p).to("Hz")
    proton_gyrofrequency

.. tip::
    The pint unit registry can also be imported
    with `from pint import application_registry as u`, which is the
    same registry as `mmspy.units`.


`pint-xarray <pint_xarray_>`_ also provides an `accessor <accessors_>`_
called `pint` that allows similar unit conversions with
`quantified <xarray_pint_blog>`_ `xarray`. `xarray.Dataset` loaded with
`mmspy.load()` are quantified by default. For example, to convert magnetic
field amplitude to gyrofrequency, similar to above calculations:

.. jupyter-execute::

    background_field = fgm.b_gse.tensor.magnitude
    fci = (u.e * background_field / u.m_p).pint.to("Hz")
    fci.data.compute()

.. tip::
    Dequantify an `~xarray.Dataset` or `~xarray.DataArray` with
    :py:meth:`pint.dequantify`. For example, `fgm.b_gse.pint.dequantify()`
    will return a `~xarray.DataArray` with the `pint` wrapping layer removed,
    where the units will be saved in its ``attrs``. In opposite,
    `fgm.b_gse.pint.quantify()` will rewrap the array with `pint.Quantity`.

Above, :py:attr:`tensor` is an `accessor <accessors_>`_
provided by `mmspy` to conveniently calculate the magnitude of
``rank_1`` and ``rank_2`` tensors.

Furthermore, `mmspy` provides convienient conversion species-dependent
parameters, so that one can directly convert by specifying what species
the conversion involves:

.. jupyter-execute::

    fce = background_field.data.to("Hz", "electron")
    fce.compute()

Unfortunately, this conversion is not implemented within the pint
accessor. So one would have to detach the data from the `xarray` manually
(via :py:attr:`~xarray.DataArray.data`), convert it to desired units, and
then put the data back into the `xarray`. For example:

.. jupyter-execute::
    
    fce = background_field.copy()
    fce.data = fce.data.to("Hz", "electron")
    fce.compute()

We can also add the converted array as coordinates as follows:

.. jupyter-execute::

    fgm = fgm.assign_coords(
        fce=(background_field.dims, background_field.data.to("Hz", "electron")),
        fci=(background_field.dims, background_field.data.to("Hz", "ion")),
    )
    fgm

Similarly, number density can be converted to plasma frequencies, which
are added as extra coordinates of the ``ion_fpi`` dataset:

.. jupyter-execute::

    ion_fpi = ion_fpi.assign_coords(
        fpi=(ion_fpi.numberdensity.dims, ion_fpi.numberdensity.data.to("Hz", "ion")),
    )
    ion_fpi

Energy can be converted (relativistically correctly) to speed

.. jupyter-execute::

    ion_fpi = ion_fpi.assign_coords(
        V=(ion_fpi.energy.dims, ion_fpi.energy.data.to("km/s", "ion")),
    )
    ion_fpi

Energy flux can be converted (relativistically correctly) to phase space
density (a bit more involved, since the conversion involves energy) as follows:

.. jupyter-execute::

    ion_fpi = ion_fpi.assign_coords(
        f_omni=(
            ion_fpi.energyspectr_omni.dims,
            ion_fpi.energyspectr_omni.data.to(
                "s3 km-6",
                "ion",
                energy=ion_fpi.energy.broadcast_like(ion_fpi.energyspectr_omni).data,
            ),
        ),
    )
    ion_fpi

.. _dask_integration:

Dask in action
--------------

Every calculation that we have laid out thus far (frequency, speed,
and phase space density conversions) are not evaluated immediately. Let us
examine the `task graph <https://docs.dask.org/en/stable/graphs.html>`_ of
one of the variables from the previous section:

.. jupyter-execute::

    ion_fpi.V.data.dask

These layers show all of the necessary steps to get from data on-disk
to the final computational results in-memory, which is the ion speed
quantified in ``'km/s'``. The benefit of using `dask` adds up quickly for
more complicated operations, which could easily result in a graph of
hundreds of layers.

As a demonstration, let us further complicate the calculations by trying
to integrate for the number density using the omni-directional phase
space density ``ion_fpi.f_omni``. Usually, there are important
preprocessing steps to obtain the correct plasma moments. But let us
ignore them for now. Perform a regrid in the ion speed
(see more detail in the Gallery):

.. jupyter-execute::

    from mmspy.compute.particle import ParticleGrid, interpolate_distribution
    import numpy as np

    grid = {
        "V": ParticleGrid(
            name="speed",
            center=u.Quantity(np.linspace(0, 5000, 30), "km s-1")
        ),
    }
    f_interpolated = interpolate_distribution(ion_fpi, grid, variable="f_omni")
    f_interpolated

And finally integrate along the speed coordinate, convert to number
density, and add a factor of 2pi (because ``f_omni`` is solid-angle averaged):

.. jupyter-execute::

    V = f_interpolated.V
    n = 2 * np.pi * (V**2 * f_interpolated).integrate("V").pint.to("cm-3")
    n.data.dask

This gets us up to 75 layers! To debug, we set up a
`dask dashboard <https://docs.dask.org/en/latest/dashboard.html>`_:

.. jupyter-execute::
    
    mms.enable_diagnostics()

and finally call :py:meth:`~xarray.DataArray.compute()` for the final
results while monitoring the dashboard:

.. jupyter-execute::

    n_integrated = n.compute()
    n_integrated

Plotting
--------

`mmspy` does not provide any interactive component. Plotting is deferred
to `matplotlib`, which is the most common scientific visualization library
in Python. However, `mmspy` does provide a custom `matplotlib stylesheet
<https://matplotlib.org/stable/gallery/style_sheets/style_sheets_reference.html>`_
and some convenient formatting methods for time series and spectrograms.

To use the stylesheet:

.. jupyter-execute::

    mms.configure_matplotlib()

Nothing else is required. Let us now compare the integrated moment in the
previous section with the L2 density using `matplotlib`:

.. jupyter-execute::

    import matplotlib.pyplot as plt

    fig, ax = plt.subplots(1, 1, figsize=(12, 6))
    
    ax.plot(ion_fpi.time, ion_fpi.numberdensity, "-k", label="L2 density")
    ax.plot(n_integrated.time, n_integrated, "-r", label="Integrated density")
    ax.legend(frameon=False, loc="upper right")
    ax.set_ylabel(f"{n_integrated.pint.units:latex}")

    mms.plot.autoformat(ax)
    plt.show()

Not too bad! There are some expected discrepancy, mainly due to the usage
of a linear grid. A more detailed example on how to use functions in the
`mmspy.compute.particle` module is given in the Gallery.

Alias query parameters and variables
------------------------------------

You might have noticed prior that `mmspy.query` shows aliases for the
parameters. This option is available if you wish to customize different names
for datasets and variables. There is actually another important component
of `mmspy`, called :py:attr:`mmspy.config`, which configures the behaviors of
`mmspy.query` and `mmspy.store`. To enable aliasing, set:

.. jupyter-execute::

    mms.config.query.use_alias = True

    mms.query.data_rate = "survey"
    mms.query.data_level = "level_2"
    mms.query.show()

By default, ``'survey'`` is aliased to ``'srvy'`` for
``fgm,scm,fsm,hpca,feeps``, and ``'fast'`` for ``edp,fpi``. And
the data variables are renamed to be more verbose. However,
this can be customized by changing `mmspy.config`.

.. note::
    The code still works if the actual values are provided in place of
    the aliases.

.. tip::
    Print out `mmspy.config` to examine the default aliases.

.. jupyter-execute::

    fgm = mms.load(instrument="fgm")
    fgm

.. jupyter-execute::

    edp = mms.load(instrument="edp", data_type="efield")
    edp

.. jupyter-execute::

    fpi = mms.load(instrument="fpi", data_type="ion_moments")
    fpi

.. jupyter-execute::

    feeps = mms.load(instrument="feeps", data_type="ion_distribution")
    feeps

More on this later...


.. _sdc: https://lasp.colorado.edu/mms/sdc/public/about/how-to/
.. _remote: https://lasp.colorado.edu/mms/sdc/public/about/browse-wrapper/
.. _Query: mmspy.api.query.Query
.. _product_guide: https://lasp.colorado.edu/mms/sdc/public/datasets/
.. _pyspedas: https://pyspedas.readthedocs.io/en/latest/
.. _astropy_units: https://docs.astropy.org/en/stable/units/
.. _quantity_2: https://github.com/nstarman/astropy-APEs/blob/units-quantity-2.0/APE25/report.pdf
.. _pint_xarray: https://pint-xarray.readthedocs.io/en/stable/
.. _fits: https://fits.gsfc.nasa.gov/fits_standard.html
.. _xarray_structures: https://docs.xarray.dev/en/stable/user-guide/data-structures.html
.. _accessors: https://docs.xarray.dev/en/stable/internals/extending-xarray.html
.. _dask: https://docs.dask.org/en/stable/
.. _pint: https://pint.readthedocs.io/en/stable/
.. _dimension: https://docs.xarray.dev/en/stable/user-guide/terminology.html#term-Dimension
.. _coordinate: https://docs.xarray.dev/en/stable/user-guide/terminology.html#term-Coordinate
.. _variable: https://docs.xarray.dev/en/stable/user-guide/terminology.html#term-Variable
.. _xarray_pint_blog: https://xarray.dev/blog/introducing-pint-xarray
