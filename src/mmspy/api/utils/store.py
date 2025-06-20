import atexit
import shutil
from pathlib import Path
from typing import TYPE_CHECKING

import zarr
from attrs import Attribute

from mmspy.config.config import config

if TYPE_CHECKING:
    from mmspy.api.store import Store


def setup_zarr_store(store: "Store", attribute: Attribute, path: Path) -> None:
    """Function for store initialization.

    .. todo:: Add remote capability.

    """
    # Create root node
    root = zarr.open(zarr.DirectoryStore(path), mode="a")
    setattr(store, "zarr", root)

    # Make local sync store
    root.require_group(config.get("store/sync_store", "raise"))

    #  # Make remote store
    #  remote_store = zarr.TempStore(dir=path)
    #  temporary_path = Path(remote_store.path)
    #  new_path = temporary_path.parent / "remote"
    #  if new_path.exists():
    #      shutil.rmtree(new_path)
    #  remote_store.path = str(new_path)
    #  temporary_path.rename(new_path)

    #  # Make sure remote store is wiped when the object is deleted
    #  atexit.register(zarr.storage.atexit_rmtree, new_path)
