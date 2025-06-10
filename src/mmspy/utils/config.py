__all__ = ["config"]

import collections.abc
import tomllib
from importlib.resources import files
from pathlib import Path

import zarr


def create_table(dictionary):
    def create_node(parent, children):
        if isinstance(children, str):
            parent.attrs.update(value=children)
            return
        for key, value in children.items():
            child = parent.require_group(key)
            create_node(child, value)

    root = zarr.group()
    create_node(root, dictionary)
    return root


def nested_update(d, u):
    for k, v in u.items():
        if isinstance(v, collections.abc.Mapping):
            d[k] = nested_update(d.get(k, {}), v)
        else:
            d[k] = v

    return d


default_config = files("mmspy.data") / "default-config.toml"


class Config:
    def __init__(self, config_file: Path = Path(str(default_config))):
        with open(config_file, "rb") as f:
            self.data = tomllib.load(f)

    def update(self, data: Path | dict):
        if not isinstance(data, dict):
            with open(data, "rb") as f:
                data = tomllib.load(f)

        self.data = nested_update(self.data, data)

    @property
    def table(self) -> zarr.Group:
        return create_table(self.data)


config = Config()
