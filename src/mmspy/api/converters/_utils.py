__all__ = ["wrap_converter"]

from collections.abc import Callable
from typing import TypeAlias, cast

from attr import Converter


def wrap_converter(signature: TypeAlias, **kwargs) -> Callable:
    r"""Cast a converter into the correct signature.

    Since `~attr.Converter` does not have a compatible signature for
    `~attr.Attribute`, we need to force type casting the
    `~attr.Converter` instance.

    Parameters
    ----------
    signature : ~typing.TypeAlias
        Signature of converter.
    **kwargs : dict, optional
        Extra arguments for `~attr.Converter`.

    Returns
    -------
    wrapped_converter : Callable
        Wrapped converter

    """

    def _wrapped(converter: Callable) -> Callable:
        return cast(signature, Converter(converter=converter, **kwargs))

    return _wrapped
