__all__ = ["validate_dataset"]

import xarray as xr


def validate_dataset(
    dataset: xr.Dataset,
    instrument: str,
    expected_descriptor: list[str],
) -> None:
    r"""Validate that a dataset has the expected descriptor."""
    descriptor = dataset.attrs.get("Descriptor")
    if descriptor is None:
        msg = "Cannot validate the instrument."
        raise ValueError(msg)

    if not any(pattern in descriptor for pattern in expected_descriptor):
        msg = f"Dataset does not come from {instrument} instrument"
        raise ValueError(msg)
