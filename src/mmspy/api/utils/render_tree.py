__all__ = ["render_tree"]

import fnmatch
import glob
import re
from pathlib import Path
from typing import TYPE_CHECKING

import zarr
from bigtree import Node, list_to_tree, yield_tree

if TYPE_CHECKING:
    from mmspy.api.store import Store


def is_glob(pattern: str) -> bool:
    if not bool(pattern):
        return False

    string = glob.escape(pattern)
    return any(map(lambda x: string.find(x) != -1, ("[?]", "[*]")))


def find_glob_pattern(
    pattern: str,
    store: zarr.DirectoryStore,
    store_prefix: str,
) -> list[str]:
    paths: list[str] = [str(store_prefix / Path(path)) for path in store]
    regex = re.compile(fnmatch.translate(pattern))

    def findall(path):
        path = Path(path)
        if regex.search(str(path)) or regex.search(str(path.parent)):
            if path.parent.name[:4] != "zarr":
                paths.append(str(store_prefix / path))

    store.visit(findall)
    return paths


def find_literal_pattern(
    pattern: str,
    store: zarr.DirectoryStore,
    store_prefix: str,
):
    paths: list[str] = [str(store_prefix / Path(path)) for path in store]
    if pattern not in store:
        return paths

    paths.append(str(store_prefix / Path(pattern)))
    for _, node in store[pattern].groups():
        paths.append(str(store_prefix / Path(node.path)))

    return paths


def render_tree(store: "Store", pattern: str = "") -> None:
    if bool(pattern) and pattern[0] == "/":
        pattern = pattern[1:]

    find = find_glob_pattern if is_glob(pattern) else find_literal_pattern
    paths = find(pattern, store.zarr, store_prefix="/store")
    tree: Node = list_to_tree(paths)
    for branch, stem, node in yield_tree(tree):
        if node.node_name != "store":
            print(f"{branch}{stem}{node.node_name}")
        else:
            print(f"/ (system path: {store.path})")
