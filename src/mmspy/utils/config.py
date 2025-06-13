"""Provide config object for the package."""

__all__ = ["Config", "config", "default_config_file"]

import json
from importlib.resources import files
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import IO, Any, Union

from benedict import benedict

from mmspy.utils.paths import STATE_DIR


class Config(benedict):
    _file: IO[Any] | None = None
    _file_name: str = ""

    def __init__(
        self,
        file_name: str | None = None,
        load_default: bool = False,
        format="toml",
        keypath_separator="/",
        **kwargs,
    ):
        if file_name is None:
            file_name = self.get_temporary_file()

        self._file_name = file_name
        super().__init__(
            file_name,
            format=format,
            keypath_separator=keypath_separator,
            **kwargs,
        )

        if load_default:
            self.update(default_config_file)

    def write_content(self):
        with open(self._file_name, "w") as file:
            file.write(self.to_toml())

    def update(
        self,
        config: Union[None, str, dict, "Config"] = None,
        **kwargs,
    ):
        if config is not None:
            if isinstance(config, str):
                config = Config(config)

            self.merge(config)

        self.merge(kwargs)
        self.write_content()

    def get_temporary_file(self):
        self._file = NamedTemporaryFile(delete=False, mode="a", dir=STATE_DIR)
        return self._file.name

    def get(self, key, default=None):
        if default is None:
            default = {}

        value = super(Config, self).get(key, default=default)
        if value == default == "raise":
            msg = (
                f"{key!r} is not available in the configuration file. "
                "This is breaking, please check your configuration."
            )
            raise ValueError(msg)

        return value

    def __del__(self) -> None:
        r"""Close request session."""
        if self._file is not None:
            Path(self._file.name).unlink(missing_ok=True)

    def __repr__(self) -> str:
        return json.dumps(self, sort_keys=True, indent=2, default=str)


default_config_file = str(files("mmspy.data") / "default-config.toml")
config = Config(load_default=True)
