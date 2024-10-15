import pytest
from attr import define

from mmspy.api.process.parse_metadata import parse_metadata


@define
class Case:
    name: str
    instrument: str
    result: dict[str, str]


mec_brst = Case(
    "mms1_mec_brst_l2_epht89q_20170508000225_v2.2.0.cdf",
    "mec",
    {
        "file_name": "mms1_mec_brst_l2_epht89q_20170508000225_v2.2.0.cdf",
        "probe": "mms1",
        "instrument": "mec",
        "data_rate": "brst",
        "data_level": "l2",
        "version": "2.2.0",
        "group": "/mms1/mec_epht89q/brst/l2/2017-05-08-00-02-25-000000",
    },
)

mec_srvy = Case(
    "mms1_mec_srvy_l2_epht89q_20210506_v2.2.1.cdf",
    "mec",
    {
        "file_name": "mms1_mec_srvy_l2_epht89q_20210506_v2.2.1.cdf",
        "probe": "mms1",
        "instrument": "mec",
        "data_rate": "srvy",
        "data_level": "l2",
        "version": "2.2.1",
        "group": "/mms1/mec_epht89q/srvy/l2/2021-05-06-00-00-00-000000",
    },
)

fgm_brst = Case(
    "mms1_fgm_brst_l2_20180410062213_v5.134.0.cdf",
    "fgm",
    {
        "file_name": "mms1_fgm_brst_l2_20180410062213_v5.134.0.cdf",
        "probe": "mms1",
        "instrument": "fgm",
        "data_rate": "brst",
        "data_level": "l2",
        "version": "5.134.0",
        "group": "/mms1/fgm_bfield/brst/l2/2018-04-10-06-22-13-000000",
        "eph_group": "/mms1/fgm_ephemeris/brst/l2/2018-04-10-06-22-13-000000",
    },
)
fgm_srvy = Case(
    "mms1_fgm_srvy_l2_20180801_v5.149.0.cdf",
    "fgm",
    {
        "file_name": "mms1_fgm_srvy_l2_20180801_v5.149.0.cdf",
        "probe": "mms1",
        "instrument": "fgm",
        "data_rate": "srvy",
        "data_level": "l2",
        "version": "5.149.0",
        "group": "/mms1/fgm_bfield/srvy/l2/2018-08-01-00-00-00-000000",
        "eph_group": "/mms1/fgm_ephemeris/srvy/l2/2018-08-01-00-00-00-000000",
    },
)

edp_scpot_brst = Case(
    "mms2_edp_brst_l2_scpot_20180513002823_v2.5.0.cdf",
    "edp",
    {
        "file_name": "mms2_edp_brst_l2_scpot_20180513002823_v2.5.0.cdf",
        "probe": "mms2",
        "instrument": "edp",
        "data_rate": "brst",
        "data_level": "l2",
        "version": "2.5.0",
        "group": "/mms2/edp_potential/brst/l2/2018-05-13-00-28-23-000000",
    },
)

edp_dce_brst = Case(
    "mms2_edp_brst_l2_dce_20190410033613_v3.0.3.cdf",
    "edp",
    {
        "file_name": "mms2_edp_brst_l2_dce_20190410033613_v3.0.3.cdf",
        "probe": "mms2",
        "instrument": "edp",
        "data_rate": "brst",
        "data_level": "l2",
        "version": "3.0.3",
        "group": "/mms2/edp_efield/brst/l2/2019-04-10-03-36-13-000000",
    },
)

edp_scpot_fast = Case(
    "mms2_edp_fast_l2_scpot_20170603000000_v2.4.3.cdf",
    "edp",
    {
        "file_name": "mms2_edp_fast_l2_scpot_20170603000000_v2.4.3.cdf",
        "probe": "mms2",
        "instrument": "edp",
        "data_rate": "fast",
        "data_level": "l2",
        "version": "2.4.3",
        "group": "/mms2/edp_potential/fast/l2/2017-06-03-00-00-00-000000",
    },
)

edp_dce_fast = Case(
    "mms2_edp_fast_l2_dce_20170603_v3.0.0.cdf",
    "edp",
    {
        "file_name": "mms2_edp_fast_l2_dce_20170603_v3.0.0.cdf",
        "probe": "mms2",
        "instrument": "edp",
        "data_rate": "fast",
        "data_level": "l2",
        "version": "3.0.0",
        "group": "/mms2/edp_efield/fast/l2/2017-06-03-00-00-00-000000",
    },
)

fpi_ion_brst = [
    Case(
        f"mms2_fpi_brst_l2_dis-{old}_20190412095653_v3.4.0.cdf",
        "fpi",
        {
            "file_name": f"mms2_fpi_brst_l2_dis-{old}_20190412095653_v3.4.0.cdf",
            "probe": "mms2",
            "instrument": "fpi",
            "data_rate": "brst",
            "data_level": "l2",
            "version": "3.4.0",
            "species": "ion",
            "group": f"/mms2/fpi_ion_{new}/brst/l2/2019-04-12-09-56-53-000000",
        },
    )
    for (old, new) in [
        ("dist", "distribution"),
        ("moms", "moments"),
        ("partmoms", "partial_moments"),
    ]
]

fpi_elc_brst = [
    Case(
        f"mms2_fpi_brst_l2_des-{old}_20190412095653_v3.4.0.cdf",
        "fpi",
        {
            "file_name": f"mms2_fpi_brst_l2_des-{old}_20190412095653_v3.4.0.cdf",
            "probe": "mms2",
            "instrument": "fpi",
            "data_rate": "brst",
            "data_level": "l2",
            "version": "3.4.0",
            "species": "elc",
            "group": f"/mms2/fpi_elc_{new}/brst/l2/2019-04-12-09-56-53-000000",
        },
    )
    for (old, new) in [
        ("dist", "distribution"),
        ("moms", "moments"),
        ("partmoms", "partial_moments"),
    ]
]

fpi_ion_fast = [
    Case(
        f"mms2_fpi_fast_l2_dis-{old}_20200601000000_v3.4.0.cdf",
        "fpi",
        {
            "file_name": f"mms2_fpi_fast_l2_dis-{old}_20200601000000_v3.4.0.cdf",
            "probe": "mms2",
            "instrument": "fpi",
            "data_rate": "fast",
            "data_level": "l2",
            "version": "3.4.0",
            "species": "ion",
            "group": f"/mms2/fpi_ion_{new}/fast/l2/2020-06-01-00-00-00-000000",
        },
    )
    for (old, new) in [
        ("dist", "distribution"),
        ("moms", "moments"),
        ("partmoms", "partial_moments"),
    ]
]

fpi_elc_fast = [
    Case(
        f"mms2_fpi_fast_l2_des-{old}_20200601000000_v3.4.0.cdf",
        "fpi",
        {
            "file_name": f"mms2_fpi_fast_l2_des-{old}_20200601000000_v3.4.0.cdf",
            "probe": "mms2",
            "instrument": "fpi",
            "data_rate": "fast",
            "data_level": "l2",
            "version": "3.4.0",
            "species": "elc",
            "group": f"/mms2/fpi_elc_{new}/fast/l2/2020-06-01-00-00-00-000000",
        },
    )
    for (old, new) in [
        ("dist", "distribution"),
        ("moms", "moments"),
        ("partmoms", "partial_moments"),
    ]
]

feeps_brst = [
    Case(
        f"mms2_feeps_brst_l2_{old}_20180511104403_v7.1.1.cdf",
        "feeps",
        {
            "file_name": f"mms2_feeps_brst_l2_{old}_20180511104403_v7.1.1.cdf",
            "probe": "mms2",
            "instrument": "feeps",
            "data_rate": "brst",
            "data_level": "l2",
            "version": "7.1.1",
            "species": new[:3],
            "group": f"/mms2/feeps_{new}/brst/l2/2018-05-11-10-44-03-000000",
        },
    )
    for (old, new) in [
        ("ion", "ion_distribution"),
        ("electron", "elc_distribution"),
    ]
]

feeps_srvy = [
    Case(
        f"mms2_feeps_srvy_l2_{old}_20190622000000_v7.1.1.cdf",
        "feeps",
        {
            "file_name": f"mms2_feeps_srvy_l2_{old}_20190622000000_v7.1.1.cdf",
            "probe": "mms2",
            "instrument": "feeps",
            "data_rate": "srvy",
            "data_level": "l2",
            "version": "7.1.1",
            "species": new[:3],
            "group": f"/mms2/feeps_{new}/srvy/l2/2019-06-22-00-00-00-000000",
        },
    )
    for (old, new) in [
        ("ion", "ion_distribution"),
        ("electron", "elc_distribution"),
    ]
]


@pytest.mark.parametrize(
    "case",
    [
        mec_brst,
        mec_srvy,
        fgm_brst,
        fgm_srvy,
        edp_dce_fast,
        edp_scpot_fast,
        edp_dce_brst,
        edp_scpot_brst,
        *fpi_ion_brst,
        *fpi_elc_brst,
        *fpi_ion_fast,
        *fpi_elc_fast,
        *feeps_brst,
        *feeps_srvy,
    ],
)
def test_parser(case):
    assert case.result == parse_metadata(case.name, case.instrument)
