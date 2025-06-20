__all__ = ["get_processor", "process_cdf_epoch", "process_cdf_metadata"]

from collections.abc import Callable

import xarray as xr

from mmspy.api.processors.edp_dce import process_edp_dce
from mmspy.api.processors.edp_scpot import process_edp_scpot
from mmspy.api.processors.feeps import process_feeps
from mmspy.api.processors.fgm import process_fgm
from mmspy.api.processors.fpi_dist import process_fpi_dist
from mmspy.api.processors.fpi_moms import process_fpi_moms
from mmspy.api.processors.fpi_partmoms import process_fpi_partmoms
from mmspy.api.processors.fsm import process_fsm
from mmspy.api.processors.hpca_moments import process_hpca_moments
from mmspy.api.processors.mec import process_mec
from mmspy.api.processors.scm import process_scm


def get_processor(
    metadata: dict[str, str],
) -> Callable[[str, dict], list[tuple[bool, str, xr.Dataset]]]:
    instrument = metadata["instrument"]
    data_type = metadata["data_type"]
    match instrument:
        case "mec":
            return process_mec
        case "fgm":
            return process_fgm
        case "scm":
            return process_scm
        case "fsm":
            return process_fsm
        case "edp":
            match data_type:
                case "dce":
                    return process_edp_dce
                case "scpot":
                    return process_edp_scpot
        case "feeps":
            return process_feeps
        case "fpi":
            match data_type[4:]:
                case "dist":
                    return process_fpi_dist
                case "moms":
                    return process_fpi_moms
                case "partmoms":
                    return process_fpi_partmoms
        case "hpca":
            match data_type:
                case "moments":
                    return process_hpca_moments

    raise NotImplementedError
