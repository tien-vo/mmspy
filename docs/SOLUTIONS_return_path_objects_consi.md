from pathlib import Path
from typing import List, Dict, Any, Union, cast

# --- Mocking Setup ---
# In a real scenario, Store would handle file system operations and network requests.
# We use mocks here to isolate the logic change for testing purposes.

class Store:
    """
    Mocked Store class representing the core functionality under scrutiny.
    The fix is applied within sync().
    """
    def __init__(self, root_dir: Union[str, Path]):
        self.root = Path(root_dir)
        # Mock internal state simulating metadata storage: 
        # {"file_name": {"full_path": str_path, "size": int}}
        self._mock_metadata: Dict[str, Any] = {}

    def set_metadata(self, file_data: Dict[str, Any]):
        """Helper for setting up initial state."""
        self._mock_metadata.update(file_data)

    @property
    def metadata(self) -> Dict[str, Any]:
        return self._mock_metadata

    # -----------------------------------------------------
    # THE FIX IS APPLIED HERE:
    # The return type must strictly be list[Path].
    # -----------------------------------------------------
    def sync(self) -> List[Path]:
        """
        Synchronizes local and remote files. Ensures all returned paths are Path objects.

        Returns:
            list[Path]: A list of pathlib.Path objects representing the synchronized or up-to-date files.
        """
        synchronized_paths: List[Path] = []
        
        # Simulate iterating through file metadata (e.g., from a remote manifest)
        for key, metadata in self.metadata.items():
            full_path_str = metadata["full_path"]
            is_up_to_date = metadata.get("synced", False)

            if is_up_to_date:
                # --- FIX APPLIED HERE ---
                # Original bug: Returning full_path_str (a string).
                # Fix: Convert the stored path string to a Path object immediately.
                path_obj = Path(full_path_str)
                synchronized_paths.append(path_obj)
            else:
                # Simulate successful download/sync for new files. 
                # This branch already correctly handles returning Paths.
                new_path = Path(f"{self.root}/downloaded/{key}")
                synchronized_paths.append(new_path)

        return synchronized_paths
