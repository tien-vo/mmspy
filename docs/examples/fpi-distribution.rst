Interpolating and integrating FPI distribution functions
========================================================

`mmspy` provides particle-related computations in the
:py:mod:`mmspy.compute.particle` module. Here, we demonstrate how a particle
distribution function may be interpolated onto an N-dimensional regular
grid (in linear or logarithmic spacing) and integrated for plasma moments.
We do this specifically for the electron diffusion region reported in
`Burch et al (2016), Science <burch16_>`_.

First import the package and pre-configure the query:

.. jupyter-execute::
    
    import mmspy as mms

    mms.query.start_time = "2015-10-16T13:06:55"
    mms.query.stop_time = "2015-10-16T13:07:05"
    mms.query.probe = "mms1"
    mms.query.data_rate = "brst"
    mms.query.data_level = "l2"

Event overview
--------------

Let us quickly plot the event using L2 data. We load the magnetic field,
FPI ion, and electron moments:

.. jupyter-execute::
    
    fgm = mms.load(instrument="fgm", data_type="None")
    ion_moments = mms.load(instrument="fpi", data_type="dis-moms")
    elc_moments = mms.load(instrument="fpi", data_type="des-moms")

and plot:

.. jupyter-execute::

    import matplotlib.pyplot as plt
    from matplotlib.colors import LogNorm
    import numpy as np
    
    mms.configure_matplotlib()
    
    fig, axes = plt.subplots(7, 1, figsize=(12, 14), sharex=True)
    
    mms.plot.add_colorbar(ax := axes[0]).remove()
    ax.plot(fgm.time, fgm.b_gse.sel(rank_1="x"), "-b")
    ax.plot(fgm.time, fgm.b_gse.sel(rank_1="y"), "-g")
    ax.plot(fgm.time, fgm.b_gse.sel(rank_1="z"), "-r")
    ax.plot(fgm.time, fgm.b_gse.tensor.magnitude, "-k")
    ax.set_ylabel(f"{fgm.b_gse.pint.units:latex}")
    
    cax = mms.plot.add_colorbar(ax := axes[1])
    im = ax.pcolormesh(
        ion_moments.time.expand_dims(energy_channel=ion_moments.energy_channel, axis=-1),
        ion_moments.energy,
        ion_moments.energyspectr_omni,
        cmap="jet",
        norm=LogNorm(1e2, 1e8),
    )
    cb = fig.colorbar(im, cax=cax)
    cb.set_label(f"{ion_moments.energyspectr_omni.pint.units:latex}")
    ax.set_yscale("log")
    ax.set_ylim(ion_moments.energy.min().values, ion_moments.energy.max().values)
    ax.set_ylabel(f"{ion_moments.energy.pint.units:latex}")
    
    cax = mms.plot.add_colorbar(ax := axes[2])
    im = ax.pcolormesh(
        elc_moments.time.expand_dims(energy_channel=elc_moments.energy_channel, axis=-1),
        elc_moments.energy,
        elc_moments.energyspectr_omni,
        cmap="jet",
        norm=LogNorm(1e3, 1e9),
    )
    cb = fig.colorbar(im, cax=cax)
    cb.set_label(f"{elc_moments.energyspectr_omni.pint.units:latex}")
    ax.set_yscale("log")
    ax.set_ylim(elc_moments.energy.min().values, elc_moments.energy.max().values)
    ax.set_ylabel(f"{elc_moments.energy.pint.units:latex}")
    
    mms.plot.add_colorbar(ax := axes[3]).remove()
    ax.plot(ion_moments.time, ion_moments.numberdensity, "-k")
    ax.set_ylabel(f"{ion_moments.numberdensity.pint.units:latex}")
    
    mms.plot.add_colorbar(ax := axes[4]).remove()
    ax.plot(ion_moments.time, ion_moments.bulkv_gse.sel(rank_1="x"), "-b")
    ax.plot(ion_moments.time, ion_moments.bulkv_gse.sel(rank_1="y"), "-g")
    ax.plot(ion_moments.time, ion_moments.bulkv_gse.sel(rank_1="z"), "-r")
    ax.set_ylabel(f"{ion_moments.bulkv_gse.pint.units:latex}")
    
    mms.plot.add_colorbar(ax := axes[5]).remove()
    ax.plot(elc_moments.time, elc_moments.bulkv_gse.sel(rank_1="x"), "-b")
    ax.plot(elc_moments.time, elc_moments.bulkv_gse.sel(rank_1="y"), "-g")
    ax.plot(elc_moments.time, elc_moments.bulkv_gse.sel(rank_1="z"), "-r")
    ax.set_ylabel(f"{elc_moments.bulkv_gse.pint.units:latex}")
    
    mms.plot.add_colorbar(ax := axes[6]).remove()
    ax.plot(elc_moments.time, elc_moments.temppara, "-b")
    ax.plot(elc_moments.time, elc_moments.tempperp, "-r")
    ax.set_ylabel(f"{elc_moments.temppara.pint.units:latex}")
    
    for i, ax in enumerate(axes):
        ax.axvline(np.datetime64("2015-10-16T13:07"), ls="--")
    
    mms.plot.autoformat(axes)
    fig.align_ylabels(axes)
    plt.show()

Process FPI distributions
-------------------------

Load the spacecraft potential, ion, and electron distribution functions:

.. jupyter-execute::
    
    edp = mms.load(instrument="edp", data_type="scpot")
    ion_distribution = mms.load(instrument="fpi", data_type="dis-dist")
    elc_distribution = mms.load(instrument="fpi", data_type="des-dist")

Preprocessing
~~~~~~~~~~~~~

A common preprocessing step suggested for FPI distributions 
`(CMAD) <https://hpde.io/NASA/Document/MMS/CMAD.html>`_
is to subtract the spacecraft potential. This can be done quickly via
the `fpi` `accessor <accessors_>`_:

.. jupyter-execute::

    V_sc = edp.scpot
    ion_distribution = ion_distribution.fpi.correct_for_spacecraft_potential(V_sc, average=True)
    elc_distribution = elc_distribution.fpi.correct_for_spacecraft_potential(V_sc, average=True)

.. note::
    `V_sc` is automatically resampled to the resolution of `ion_distribution`
    and `elc_distribution`. The ``average=True`` option also tells the
    function to perform a rolling average on the scale of `V_sc`'s resolution.

By default, the units of phase space density in the CDF files are
``'s3 cm-6'``, which can be as low as ``1e-25-1e-30``. Arithmetic operations
at these values are not recommended. Thus, it is in general good to
convert the distribution functions to some other units that are far from
machine precision, or to normalize the distributions with their minimum
values before interpolation. Here, we do the former (also converting
the data type to double precision in the process):

.. jupyter-execute::

    ion_distribution["dist"] = ion_distribution.dist.astype("f8").pint.to("s3 km-6")
    elc_distribution["dist"] = elc_distribution.dist.astype("f8").pint.to("s3 km-6")

Particle grid
~~~~~~~~~~~~~

To define a new grid of a given coordinate:

.. jupyter-execute::

    from mmspy.compute.particle import ParticleGrid
    from mmspy import units as u
    
    energy_range = u.Quantity(np.logspace(0.0, np.log10(4e4), 32), "eV")
    zenith_range = u.Quantity(np.arange(0.0, 180.01, 12.0), "deg")
    azimuth_range = u.Quantity(np.arange(0.0, 360.01, 12.0), "deg")
    grid = {
        "W": ParticleGrid(name="energy", center=energy_range, log_scale=True),
        "theta": ParticleGrid(name="zenith", center=zenith_range),
        "phi": ParticleGrid(name="azimuth", center=azimuth_range),
    }

.. note::
    The keys in the ``grid`` are the coordinates of the `~xarray.DataArray`
    you want to regrid. The values of the ``grid`` are the new
    `~mmspy.compute.particle.grid.ParticleGrid` you wish to regrid the
    `~xarray.DataArray` on.

.. note::
    The ``name`` argument for `~mmspy.compute.particle.grid.ParticleGrid`
    defines a new dimension name corresponding to the new coordinates.

.. note::
    The ``grid`` above is 3-dimensional. If you only wish to regrid
    along one specific coordinate, say ``'energy'``, remove the other
    keys. This allows the routine to perform interpolation in arbitrary
    dimensions.

The (unaliased) energy coordinate in L2 distribution functions have
two dimensions, ``time`` and ``energy_channel``:

.. jupyter-execute::

    ion_distribution

However, we prefer to have the regridded dimension to be named ``'energy'``,
so we rename the energy coordinate to ``'W'``:

.. jupyter-execute::

    ion_distribution = ion_distribution.rename(energy="W")
    elc_distribution = elc_distribution.rename(energy="W")
    ion_distribution

Interpolation
~~~~~~~~~~~~~

We can now regrid the distributions.
`~mmspy.compute.particle.interpolate.interpolate_distribution` does not
care how many dimensions a coordinate has. So as long as they are listed
in the ``grid``, they will be resampled:

.. jupyter-execute:: 

    from mmspy.compute.particle import interpolate_distribution

    f_ion = interpolate_distribution(ion_distribution, variable="dist", grid=grid)
    f_elc = interpolate_distribution(elc_distribution, variable="dist", grid=grid)
    f_ion.attrs.update(species=ion_distribution.species.name)
    f_elc.attrs.update(species=elc_distribution.species.name)
    f_ion

Integration
~~~~~~~~~~~

Now, we integrate the regridded distributions.
`~mmspy.compute.particle.integrate.integrate_distribution` calculates
the density, the velocity, and the pressure tensor from a given distribution.
The name of the spherical coordinates must be specified:

.. jupyter-execute:: 

    from mmspy.compute.particle import integrate_distribution

    ion_int_moments = integrate_distribution(f_ion, energy="W", zenith="theta", azimuth="phi")
    elc_int_moments = integrate_distribution(f_elc, energy="W", zenith="theta", azimuth="phi")
    ion_int_moments

All this is planned out by `dask`_. Let us examine the `task graph
<task_graph_>`_ for the pressure tensor (which will be the most complicated
since it depends on the density and the velocity):

.. jupyter-execute:: 

    ion_int_moments.P.data.dask

Call compute to get final data. This is efficient if we plan to make
multiple plots, since it avoids multiple evaluations of the `task graph
<task_graph_>`_:

.. jupyter-execute:: 

    ion_int_moments = ion_int_moments.compute()
    elc_int_moments = elc_int_moments.compute()

Validating the results
======================

Density
~~~~~~~

Let us first compare the L2 and integrated density:

.. jupyter-execute:: 

    fig, axes = plt.subplots(2, 1, figsize=(12, 8), sharex=True)
    
    axes[0].plot(ion_moments.time, ion_moments.numberdensity, "-k", label="L2 density")
    axes[0].plot(ion_int_moments.time, ion_int_moments.N, "-r", label="Integrated density")
    
    axes[1].plot(elc_moments.time, elc_moments.numberdensity, "-k")
    axes[1].plot(elc_int_moments.time, elc_int_moments.N, "-r")

    mms.plot.add_panel_label(axes[0], x=0.02, y=0.95, text="Ion", va="top")
    mms.plot.add_panel_label(axes[1], x=0.02, y=0.95, text="Electron", va="top")
    axes[0].legend(frameon=False, loc="upper right")
    for i, ax in enumerate(axes):
        ax.set_ylabel(f"{ion_moments.numberdensity.pint.units:latex}")
    
    mms.plot.autoformat(axes)
    plt.show()

.. note::
    The discrepancies are because the ``grid`` is different from what
    the FPI team uses to integrate for L2 moments. But also, the integration
    method is different. `xarray.DataArray.integrate` uses trapezoidal
    integration. However, this is quite good agreement!

Velocity
~~~~~~~~

.. jupyter-execute:: 

    fig, axes = plt.subplots(6, 1, figsize=(12, 10), sharex=True)

    axes[0].plot(ion_moments.time, ion_moments.bulkv_dbcs.sel(rank_1="x"), "-k", label="L2")
    axes[1].plot(ion_moments.time, ion_moments.bulkv_dbcs.sel(rank_1="y"), "-k")
    axes[2].plot(ion_moments.time, ion_moments.bulkv_dbcs.sel(rank_1="z"), "-k")
    axes[3].plot(elc_moments.time, elc_moments.bulkv_dbcs.sel(rank_1="x"), "-k")
    axes[4].plot(elc_moments.time, elc_moments.bulkv_dbcs.sel(rank_1="y"), "-k")
    axes[5].plot(elc_moments.time, elc_moments.bulkv_dbcs.sel(rank_1="z"), "-k")

    axes[0].plot(ion_int_moments.time, ion_int_moments.V.sel(rank_1="x"), "-r", label="Integrated")
    axes[1].plot(ion_int_moments.time, ion_int_moments.V.sel(rank_1="y"), "-r")
    axes[2].plot(ion_int_moments.time, ion_int_moments.V.sel(rank_1="z"), "-r")
    axes[3].plot(elc_int_moments.time, elc_int_moments.V.sel(rank_1="x"), "-r")
    axes[4].plot(elc_int_moments.time, elc_int_moments.V.sel(rank_1="y"), "-r")
    axes[5].plot(elc_int_moments.time, elc_int_moments.V.sel(rank_1="z"), "-r")

    labels = ["$V_{ix}$", "$V_{iy}$", "$V_{iz}$", "$V_{ex}$", "$V_{ey}$", "$V_{ez}$"]
    axes[0].legend(frameon=False, loc="upper right")
    for i, ax in enumerate(axes):
        mms.plot.add_panel_label(axes[i], x=0.02, y=0.93, text=labels[i], va="top")

    mms.plot.autoformat(axes)
    plt.show()

Pressure
~~~~~~~~

For ions:

.. jupyter-execute:: 

    fig, axes = plt.subplots(6, 1, figsize=(12, 12), sharex=True)

    axes[0].plot(ion_moments.time, ion_moments.prestensor_dbcs.sel(rank_2="xx"), "-k", label="L2")
    axes[1].plot(ion_moments.time, ion_moments.prestensor_dbcs.sel(rank_2="yy"), "-k")
    axes[2].plot(ion_moments.time, ion_moments.prestensor_dbcs.sel(rank_2="zz"), "-k")
    axes[3].plot(ion_moments.time, ion_moments.prestensor_dbcs.sel(rank_2="xy"), "-k")
    axes[4].plot(ion_moments.time, ion_moments.prestensor_dbcs.sel(rank_2="xz"), "-k")
    axes[5].plot(ion_moments.time, ion_moments.prestensor_dbcs.sel(rank_2="yz"), "-k")

    axes[0].plot(ion_int_moments.time, ion_int_moments.P.sel(rank_2="xx"), "-r", label="Integrated")
    axes[1].plot(ion_int_moments.time, ion_int_moments.P.sel(rank_2="yy"), "-r")
    axes[2].plot(ion_int_moments.time, ion_int_moments.P.sel(rank_2="zz"), "-r")
    axes[3].plot(ion_int_moments.time, ion_int_moments.P.sel(rank_2="xy"), "-r")
    axes[4].plot(ion_int_moments.time, ion_int_moments.P.sel(rank_2="xz"), "-r")
    axes[5].plot(ion_int_moments.time, ion_int_moments.P.sel(rank_2="yz"), "-r")

    labels = ["$P_{xx}$", "$P_{yy}$", "$P_{zz}$", "$P_{xy}$", "$P_{xz}$", "$P_{yz}$"]
    axes[0].legend(frameon=False, loc="upper right")
    for i, ax in enumerate(axes):
        mms.plot.add_panel_label(axes[i], x=0.02, y=0.93, text=labels[i], va="top")

    mms.plot.autoformat(axes)
    plt.show()

For electrons:

.. jupyter-execute:: 

    fig, axes = plt.subplots(6, 1, figsize=(12, 10), sharex=True)

    axes[0].plot(elc_moments.time, elc_moments.prestensor_dbcs.sel(rank_2="xx"), "-k", label="L2")
    axes[1].plot(elc_moments.time, elc_moments.prestensor_dbcs.sel(rank_2="yy"), "-k")
    axes[2].plot(elc_moments.time, elc_moments.prestensor_dbcs.sel(rank_2="zz"), "-k")
    axes[3].plot(elc_moments.time, elc_moments.prestensor_dbcs.sel(rank_2="xy"), "-k")
    axes[4].plot(elc_moments.time, elc_moments.prestensor_dbcs.sel(rank_2="xz"), "-k")
    axes[5].plot(elc_moments.time, elc_moments.prestensor_dbcs.sel(rank_2="yz"), "-k")

    axes[0].plot(elc_int_moments.time, elc_int_moments.P.sel(rank_2="xx"), "-r", label="Integrated")
    axes[1].plot(elc_int_moments.time, elc_int_moments.P.sel(rank_2="yy"), "-r")
    axes[2].plot(elc_int_moments.time, elc_int_moments.P.sel(rank_2="zz"), "-r")
    axes[3].plot(elc_int_moments.time, elc_int_moments.P.sel(rank_2="xy"), "-r")
    axes[4].plot(elc_int_moments.time, elc_int_moments.P.sel(rank_2="xz"), "-r")
    axes[5].plot(elc_int_moments.time, elc_int_moments.P.sel(rank_2="yz"), "-r")

    labels = ["$P_{xx}$", "$P_{yy}$", "$P_{zz}$", "$P_{xy}$", "$P_{xz}$", "$P_{yz}$"]
    axes[0].legend(frameon=False, loc="upper right")
    for i, ax in enumerate(axes):
        mms.plot.add_panel_label(axes[i], x=0.02, y=0.93, text=labels[i], va="top")

    mms.plot.autoformat(axes)
    plt.show()

.. _burch16: 10.1126/science.aaf2939
.. _accessor: https://docs.xarray.dev/en/stable/internals/extending-xarray.html
.. _dask: https://docs.dask.org/en/stable/
.. _task_graph: https://docs.dask.org/en/stable/graphs.html
