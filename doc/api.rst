.. currentmodule:: mmspy

.. _api:

#############
API reference
#############

This page provides an auto-generated summary of mmspy's API. For more details
and examples, refer to the relevant chapters in the main part of the
documentation.

====================
Top-level components
====================

.. autosummary::
   :toctree: generated/

   load
   query
   store
   units
   config


Setting query parameters
========================
.. autosummary::
   :toctree: generated/

   api.query.Query
   api.query.Query.start_time
   api.query.Query.stop_time
   api.query.Query.probe
   api.query.Query.instrument
   api.query.Query.data_rate
   api.query.Query.data_type
   api.query.Query.data_level
   api.query.Query.ancillary_product

Managing data stores
====================
.. autosummary::
   :toctree: generated/

   api.store.Store
   api.store.Store.path
   api.store.Store.zarr
   api.store.Store.show
   api.store.Store.sync
   api.store.Store.write_dataset
   api.store.Store.get_local_files
   api.store.Store.get_time_slices
   api.store.Store.files
   api.store.Store.time_slices

Computation
===========

Particle distribution processing
--------------------------------
.. autosummary::
   :toctree: generated/

   compute.particle.grid.ParticleGrid
   compute.particle.interpolate.interpolate_distribution
   compute.particle.integrate.integrate_distribution
   compute.particle.integrate.reduce_distribution
   compute.particle.smooth.smooth_distribution
