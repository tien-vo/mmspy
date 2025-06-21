import logging
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import TYPE_CHECKING

import numpy as np
import pandas as pd
import requests
from pathos.threading import ThreadPool
from tqdm.contrib.logging import tqdm_logging_redirect as tqdm

from mmspy.api.processors import get_processor
from mmspy.api.utils.file import (
    CdfFile,
    truncate_file_list_using_name,
)
from mmspy.api.utils.progress_bar import bar_config
from mmspy.configure.config import config
from mmspy.configure.units import units as u

if TYPE_CHECKING:
    from mmspy.api.query import Query
    from mmspy.api.store import Store

log = logging.getLogger(__name__)


def get_remote_files(
    request: requests.Session,
    query: "Query",
) -> list[CdfFile]:
    try:
        response = request.get(
            url=query.get_url(command="file_info", data="science"),
            params=query.get_payload(),
            stream=True,
        )
    except requests.exceptions.ConnectionError as e:
        log.warning(e)
        return []

    if not response.ok:
        msg = f"Bad query with HTTP code {response.status_code}."
        log.warning(msg)
        return []

    # Sort the files
    files = sorted(
        response.json()["files"],
        key=lambda file: pd.to_datetime(file["timetag"]),
    )

    # Parse the files
    files = [
        CdfFile(
            cdf_file_name=file["file_name"],
            modified_date=file["modified_date"],
            size=str(u.Quantity(file["file_size"], "B").to("MB")),
        )
        for file in files
    ]

    if len(files) == 0:
        msg = "No file found from remote."
        log.warning(msg)
        return files

    log.debug(
        f"Found {len(files)} files from "
        f"{files[0].timestamp} to {files[-1].timestamp}."
    )

    # Truncate the list based on query
    files = truncate_file_list_using_name(files, query)
    log.debug(
        f"Truncated list to {len(files)} files from "
        f"{files[0].timestamp} to {files[-1].timestamp} based on query."
    )

    # Consolidate files with query
    for file in files:
        file.consolidate(query)

    log.debug(
        "Validated CDF file list with query metadata! "
        "Starting the download now."
    )
    return files


def download_cdf_file(
    cdf_file_name: str,
    request: requests.Session,
    query: "Query",
) -> str | None:
    temporary_file = NamedTemporaryFile(delete=False, mode="wb")
    chunk_size = int(
        u(config.get("store/download_chunk_size", default="0.5 MB"))
        .to("B")
        .magnitude
    )

    try:
        response = request.get(
            url=query.get_url(command="download", data="science"),
            params=query.get_payload(cdf_file_name),
            stream=True,
        )
        remote_size = int(response.headers.get("content-length", "0"))

        with tqdm(
            **bar_config(
                desc=f"Downloading {cdf_file_name}.",
                total=remote_size,
                unit="B",
                unit_scale=True,
            ),
        ) as bar:
            for data in response.iter_content(chunk_size):
                temporary_file.write(data)
                temporary_file.flush()
                bar.update(len(data))
    except (
        requests.ConnectionError,
        requests.HTTPError,
        requests.Timeout,
    ):
        msg = "Download failed! Giving up..."
        log.warning(msg)
        return None

    local_size = Path(temporary_file.name).stat().st_size
    if local_size != remote_size:
        Path(temporary_file.name).unlink(missing_ok=True)
        msg = (
            "Download failed! "
            f"File size mismatch ({local_size!r} != {remote_size!r}). "
        )
        log.warning(msg)
        return None

    return temporary_file.name
