from pathlib import Path

import pandas as pd
import xarray as xr

import mmspy

# ---- MMS API
store = (
    Path("/")
    / "media"
    / "data"
    / "mms"
    / "processing"
    / "distribution_function"
)
mms = mmspy.api.MMS()
mms.query.probe = "mms1"
mms.query.data_rate = "brst"
mms.query.data_level = "l2"
mms.sync.store = store / "00" / "raw"

# ---- Resources
periods = xr.Dataset.from_dataframe(
    pd.read_csv(
        store / "00" / "resources" / "periods.csv",
        parse_dates=["start_date", "end_date"],
    )
).rename(index="period")

fpi_grid = mmspy.computation.particle.grid.ParticleGrid(
    minimum_energy=1e0,
    maximum_energy=5e4,
    energy_resolution=39,   # log spacing ~ 0.1515
    zenith_resolution=19,   # spacing = 11.25 deg
    azimuth_resolution=33,  # spacing = 11.25 deg
)
