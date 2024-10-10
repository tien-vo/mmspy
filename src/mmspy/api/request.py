r"""Provide interface for HTTPS data request."""

import logging
from pathlib import Path
from tempfile import NamedTemporaryFile

import astropy.units as u
import requests
from attr import define, field
from tqdm.contrib.logging import tqdm_logging_redirect as tqdm

from .query import Query

log = logging.getLogger(__name__)


@define
class Request:
    r"""Interface for making HTTP requests.

    .. todo:: Write docstring
    """

    query: Query

    session = requests.Session()

    api: str = field(
        repr=False,
        default="https://lasp.colorado.edu/mms/sdc/public/files/api/v1",
        converter=str,
    )

    timeout: float = field(default=60.0, converter=float)

    number_of_attempts: int = field(default=3, converter=int)

    request_chunk_size: u.Quantity = field(
        default=0.5 * u.MB,
        converter=lambda x: int(x.to("B").value),
    )

    verbose: bool = True

    bar_format = (
        "[{bar:40}] | {desc} "
        "[{n_fmt}/{total_fmt}/{rate_fmt} ({percentage:.0f}%)]"
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
        if self.verbose:
            msg = f"Query {response.url.split('?')[1]}"
            log.info(msg)
        response.raise_for_status()

        cdf_info = response.json()["files"]
        cdf_list = [item["file_name"] for item in cdf_info]
        cdf_size = 1e-9 * sum([item["file_size"] for item in cdf_info])  # GB

        if self.verbose:
            msg = f"Found {len(cdf_list)} files from query ({cdf_size:.4f} GB)"
            log.info(msg)

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
            response = self.session.get(
                url=f"{self.api}/download/{self.query.data}",
                params={"file": cdf_file_name},
                timeout=self.timeout,
                stream=True,
                allow_redirects=True,
            )
            response.raise_for_status()
            remote_size = int(response.headers.get("content-length", "0"))

            temporary_file = NamedTemporaryFile(delete=False, mode="wb")
            with tqdm(
                desc=f"Downloading {cdf_file_name}",
                total=remote_size,
                unit="B",
                dynamic_ncols=True,
                unit_scale=True,
                bar_format=self.bar_format,
                ascii="-#",
                position=0,
            ) as bar:
                for data in response.iter_content(self.request_chunk_size):
                    bar.update(len(data))
                    temporary_file.write(data)

            local_size = Path(temporary_file.name).stat().st_size
            return remote_size == local_size, temporary_file

        for _ in range(self.number_of_attempts):
            try:
                success, temporary_file = _helper()
                if success:
                    break
            except (
                requests.HTTPError,
                requests.ConnectionError,
                requests.Timeout,
            ):
                ...

        if not success:
            msg = f"Giving up downloading {cdf_file_name}."
            log.warning(msg)
            Path(temporary_file.name).unlink(missing_ok=True)
            return None

        return temporary_file.name

    def __del__(self) -> None:
        r"""Close request session."""
        self.session.close()
