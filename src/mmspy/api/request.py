r"""Provide interface for HTTPS data request."""

__all__ = ["Request"]

import logging
from bisect import bisect_left
from pathlib import Path
from tempfile import NamedTemporaryFile

import pandas as pd
import requests
from attr import define, field
from pint import application_registry as u
from tqdm.contrib.logging import tqdm_logging_redirect as tqdm

from mmspy.api._utils import bar_config
from mmspy.api.query import Query

LOG = logging.getLogger(__name__)


@define
class Request:
    r"""Interface for making HTTP requests.

    .. todo:: Write docstring
    """

    query: Query = field(repr=False)

    session = requests.Session()

    api: str = field(
        repr=False,
        default="https://lasp.colorado.edu/mms/sdc/public/files/api/v1",
        converter=str,
    )

    timeout: float = field(default=60.0, converter=float)

    number_of_attempts: int = field(default=3, converter=int)

    request_chunk_size: int = field(
        default=u("0.5 MB"),
        converter=lambda x: int(x.to("B").magnitude),
    )

    @property
    def cdf_file_list(self) -> list[str]:
        r"""Get list of CDF file names relevant to payload information.

        Returns
        -------
        cdf_file_list: list[str]
            List of file names

        """
        response = self.session.get(
            url=f"{self.api}/file_info/{self.query.data}",
            params=self.query.payload,
            timeout=self.timeout,
            stream=True,
        )
        response.raise_for_status()

        cdf_info = sorted(
            response.json()["files"],
            key=lambda file: pd.to_datetime(file["timetag"]),
        )

        # Find truncated list based on query.start_date
        idx = max(
            0,
            bisect_left(
                [pd.to_datetime(file["timetag"]) for file in cdf_info],
                self.query.start_date,
            )
            - 1,
        )
        cdf_info = cdf_info[idx:]

        # Extract info
        cdf_list = [item["file_name"] for item in cdf_info]
        cdf_size = 1e-9 * sum([item["file_size"] for item in cdf_info])  # GB

        msg = (
            f"Found {len(cdf_list)} file(s) from query "
            f"({cdf_size:.4f} GB)."
        )
        LOG.debug(msg)

        return cdf_list

    def download_file(self, cdf_file_name: str) -> str | None:
        r"""Download content of CDF file into a temporary file.

        Parameters
        ----------
        cdf_file_name: str
            Name of CDF file.

        Returns
        -------
        temporary_file_name: str | None
            Name of temporary file (None if download failed)

        """

        def _helper() -> tuple:
            temporary_file = NamedTemporaryFile(delete=False, mode="wb")

            with self.session.get(
                url=f"{self.api}/download/{self.query.data}",
                params={"file": cdf_file_name},
                timeout=self.timeout,
                stream=True,
            ) as response:
                response.raise_for_status()
                remote_size = int(response.headers.get("content-length", "0"))

                with tqdm(
                    **bar_config(
                        desc=f"Downloading {cdf_file_name}.",
                        total=remote_size,
                        unit="B",
                        unit_scale=True,
                        position=1,
                    ),
                ) as bar:
                    for data in response.iter_content(self.request_chunk_size):
                        temporary_file.write(data)
                        temporary_file.flush()
                        bar.update(len(data))

            local_size = Path(temporary_file.name).stat().st_size
            return local_size, remote_size, temporary_file

        for _ in range(self.number_of_attempts):
            try:
                local_size, remote_size, temporary_file = _helper()
                if success := (local_size == remote_size):
                    break

                Path(temporary_file.name).unlink(missing_ok=True)
                msg = (
                    f"File size mismatch ({local_size!r} != {remote_size!r}). "
                    f"Trying again..."
                )
                LOG.warning(msg)
            except (
                requests.HTTPError,
                requests.ConnectionError,
                requests.Timeout,
            ):
                ...

        if not success:
            msg = f"Giving up downloading {cdf_file_name}."
            LOG.warning(msg)
            return None

        return temporary_file.name

    def __del__(self) -> None:
        r"""Close request session."""
        self.session.close()
