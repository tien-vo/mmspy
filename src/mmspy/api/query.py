"""Provide dataclass for API query parameters."""

__all__ = ["Query", "query"]

import logging

import pandas as pd
from attrs import asdict, define, field

from mmspy.api.utils.alias import AliasedString, make_aliased_string
from mmspy.api.utils.file import parse_species
from mmspy.configure.config import config
from mmspy.types import Date

log = logging.getLogger(__name__)


#  """
#  Examples: `'2015-10-16'`, `'2015-10-16T08:00:00'`
#  Examples: `'2015-10-17'`, `'2015-10-16T14:00:00'`
#  Examples: `'mms1'`, `'mms2'`, `'mms3'`, `'mms4'`
#  Examples: `'aspoc'`, `'dsp'`, `'edi'`, `'edp'`, `'epd'`,
#      `'epd-eis'`, `'feeps'`, `'fgm'`, `'fpi'`, `'fsm'`, `'hpca'`,
#      `'mec'`, `'scm'`
#  Examples: `'srvy'`, `'brst'`, `'slow'`, `'fast'`
#  Examples: `'epht89d'`, `'epht89q'`, `'ephts04d'` (for MEC),
#      `'dce'`, `'scpot'` (for EDP), `'scsrvy'`, `'scb'`, `'schb'` (for SCM),
#      `'dis-dist'`, `'dis-moms'`, `'dis-partmoms'`, `'des-dist'`,
#      `'des-moms'`, `'des-partmoms'` (for FPI),
#      `'ion'`, `'electron'` (for FEEPS)
#  Examples: `'l2'`, `'l3'`
#  Examples: `'defeph'`, `'defatt'`, `'predatt'`, `'predeph'`,
#      `'radpred'`, `'manplan'`, `'timeline'`
#  """


@define
class Query:
    """Query parameters for the MMS SDC.

    .. todo:: Add examples.

    This class is not supposed to be initialized directly. Rather, it
    should be used through the package-level `mmspy.query` instance.

    For detailed descriptions of the web services and the query parameters,
    see the `SDC website`_. For usage examples, see the ``Attributes`` and
    ``Examples`` sections below.

    .. _`SDC website`: https://lasp.colorado.edu/mms/sdc/public/about/how-to/

    Parameters
    ----------
    start_time : date-like, optional
        API equivalence: ``start_date``.
    stop_time : date-like, optional
        API equivalence: ``stop_date``.
    probe : str, optional
        API equivalence: ``sc_id``.
    instrument : str, optional
        API equivalence: ``instrument_id``.
    data_rate : str, optional
        API equivalence: ``data_rate_mode``.
    data_type : str, optional
        API equivalence: ``descriptor``.
    data_level : str, optional
        API equivalence: ``data_level``.
    ancillary_product : str, optional
        API equivalence: ``product``.

    """

    start_time: Date = field(default=None, converter=pd.Timestamp)
    """: Query start time in acceptable format for `~pandas.Timestamp`,
    e.g., YYYY-MM-DD, YYYY-MM-DD/hh:mm:ss, or YYYY-MM-DDThh:mm:ss.ssssss.
    """

    stop_time: Date = field(default=None, converter=pd.Timestamp)
    """: Query stop time in acceptable format for `~pandas.Timestamp`,
    e.g., YYYY-MM-DD, YYYY-MM-DD/hh:mm:ss, or YYYY-MM-DDThh:mm:ss.ssssss.
    """

    probe: str = field(default=None, converter=str)
    """: Probe name."""

    instrument: str = field(default=None, converter=str)
    """: Instrument name."""

    data_rate: str = field(default=None, converter=str)
    """: Data rate mode."""

    data_type: str = field(default=None, converter=str)
    """: Data descriptor."""

    data_level: str = field(default=None, converter=str)
    """: Data level."""

    ancillary_product: str = field(default=None, converter=str)
    """: Ancillary product (unsupported)."""

    _state: dict = field(default={}, init=False, repr=False)

    @property
    def _start_time(self) -> pd.Timestamp:
        """`start_time` adjusted for query."""
        return pd.Timestamp(self.start_time) - pd.Timedelta(1, "d")

    @property
    def _stop_time(self) -> pd.Timestamp:
        """`stop_time` adjusted for query."""
        return pd.Timestamp(self.stop_time) + pd.Timedelta(1, "d")

    @property
    def _probe(self) -> AliasedString:
        return make_aliased_string(self.probe, "aliases/probe")

    @property
    def _instrument(self) -> AliasedString:
        return make_aliased_string(self.instrument, "aliases/instrument")

    @property
    def _data_rate(self) -> AliasedString:
        path = f"{self._instrument.true_value}/aliases/data_rate"
        return make_aliased_string(self.data_rate, path)

    @property
    def _data_type(self) -> AliasedString:
        path = f"{self._instrument.true_value}/aliases/data_type"
        return make_aliased_string(self.data_type, path)

    @property
    def _data_level(self) -> AliasedString:
        return make_aliased_string(self.data_level, "aliases/data_level")

    @property
    def _ancillary_product(self) -> AliasedString:
        return make_aliased_string(
            self.ancillary_product,
            "aliases.ancillary_product",
        )

    @property
    def remote_path(self) -> str:
        """Path to the remote store."""
        path = [
            self._probe.true_value,
            self._instrument.true_value,
            self._data_rate.true_value,
            self._data_level.true_value,
        ]
        additional = (
            [] if not bool(self._data_type) else [self._data_type.true_value]
        )
        return "/".join(path + additional)

    @property
    def local_path(self) -> str:
        """Path to the local store."""
        alias = (
            "alias"
            if config.get("query/use_alias", default=False)
            else "true_value"
        )
        probe = getattr(self._probe, alias)
        instrument = getattr(self._instrument, alias)
        data_rate = getattr(self._data_rate, alias)
        data_type = getattr(self._data_type, alias)
        data_level = getattr(self._data_level, alias)

        # This will only apply for FGM
        if config.get(
            f"{self._instrument.true_value}/alias_local_data_type",
            default=False,
        ) and not bool(self._data_type):
            data_type = config.get(
                f"{self._instrument.true_value}/aliases/data_type/None",
                default=self.data_type,
            )

        return "/".join([probe, instrument, data_type, data_rate, data_level])

    @property
    def metadata(self) -> dict[str, str]:
        """Return the query's metadata."""
        probe = self._probe.true_value
        instrument = self._instrument.true_value
        data_rate = self._data_rate.true_value
        data_type = self._data_type.true_value
        data_level = self._data_level.true_value

        extras: dict[str, str] = {}
        if instrument in ["feeps", "fpi"]:
            extras["species"] = parse_species(instrument, data_type)

        return {
            "probe": probe,
            "instrument": instrument,
            "data_rate": data_rate,
            "data_type": data_type,
            "data_level": data_level,
            "local_path": self.local_path,
            **extras,
        }

    def get_url(self, command: str, data: str = "science") -> str:
        """Get the url for a HTTP request.

        Parameters
        ----------
        command : str
            {'file_names', 'file_info', 'version_info', 'download'}
        data : str
            {'science', 'ancillary', 'hk'}

        Returns
        -------
        url : str
            Base url to provide for an HTTP request.

        """
        base_api_url = config.get("query/base_api_url", "raise")
        return f"{base_api_url}/{command}/{data}"

    def get_payload(
        self,
        cdf_file_name: str | None = None,
    ) -> dict[str, str | None]:
        """Get the HTTP payload constructed from query parameters.

        Parameters
        ----------
        cdf_file_name : str, optional
            Query parameters will be ignored if a specific
            ``cdf_file_name`` is provided.

        Returns
        -------
        payload : dict
            Payload to provide for an HTTP request.

        """

        def wrap_none_string(value: str) -> str | None:
            return None if value == "None" else value

        def wrap_none_time(value: pd.Timestamp) -> str | None:
            return (
                value.strftime("%Y-%m-%d-%H-%M-%S")
                if not pd.isnull(value)
                else None
            )

        if cdf_file_name is not None:
            return {"file": cdf_file_name}

        if pd.isnull(self._start_time) and pd.isnull(self._stop_time):
            msg = (
                "Both 'start_time' and 'stop_time' are not set! "
                "This is unsafe because it will query a lot of CDF files. "
                "Please set a time range."
            )
            log.warning(msg)

        return {
            "start_date": wrap_none_time(self._start_time),
            "end_date": wrap_none_time(self._stop_time),
            "sc_id": wrap_none_string(self._probe.true_value),
            "instrument_id": wrap_none_string(self._instrument.true_value),
            "data_rate_mode": wrap_none_string(self._data_rate.true_value),
            "descriptor": wrap_none_string(self._data_type.true_value),
            "data_level": wrap_none_string(self._data_level.true_value),
            "product": wrap_none_string(self._ancillary_product.true_value),
        }

    def summary(self) -> str:
        return (
            f"  * start_time        : {self.start_time}\n"
            f"  * stop_time         : {self.stop_time}\n"
            f"  * probe             : {self._probe}\n"
            f"  * instrument        : {self._instrument}\n"
            f"  * data_rate         : {self._data_rate}\n"
            f"  * data_type         : {self._data_type}\n"
            f"  * data_level        : {self._data_level}\n"
            f"  * ancillary_product : {self._ancillary_product}"
        )

    def show(self) -> None:
        print(self.summary())

    def update(self, **kwargs) -> None:
        """Update the query with init parameters."""
        for variable, value in kwargs.items():
            if value is not None:
                setattr(self, variable, value)

    def reset(self) -> None:
        """Reset the query."""
        for variable in [
            "start_time",
            "stop_time",
            "probe",
            "instrument",
            "data_rate",
            "data_type",
            "data_level",
            "ancillary_product",
        ]:
            setattr(self, variable, None)

    def save_state(self) -> None:
        """Save the current query."""
        self._state = asdict(self)

    def restore_state(self) -> None:
        self.update(**self._state)


query = Query()
