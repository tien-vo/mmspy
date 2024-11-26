import config as c

kw: dict = {"parallel": 4}
for period in c.periods.period:
    c.mms.query.start_date = c.periods.start_date[period].values
    c.mms.query.end_date = c.periods.end_date[period].values

    c.mms.query.instrument = "fgm"
    c.mms.query.data_type = "bfield"
    c.mms.sync.sync(**kw)

    c.mms.query.instrument = "edp"
    c.mms.query.data_type = "potential"
    c.mms.sync.sync(**kw)

    c.mms.query.instrument = "fpi"
    for data_type in [
        "ion_distribution",
        "elc_distribution",
        "ion_moments",
        "elc_moments",
    ]:
        c.mms.query.data_type = data_type
        c.mms.sync.sync(**kw)

    c.mms.query.instrument = "feeps"
    for data_type in ["ion_distribution", "elc_distribution"]:
        c.mms.query.data_type = data_type
        c.mms.sync.sync(**kw)
