__all__ = ["AliasedString"]


from attrs import define, field

from mmspy.configure.config import config


@define
class AliasedString:
    """Aliased string.

    .. todo:: Add docstring

    """

    true_value: str = field(default=None, converter=str)
    alias: str = field(default=None, converter=str)

    def __repr__(self) -> str:
        return f"{self.true_value} (Alias: {self.alias})"

    def __bool__(self) -> bool:
        return self.true_value != "None"


def make_aliased_string(alias: str, path: str | list[str]) -> AliasedString:
    """Make aliased string within query paramters.

    .. todo:: Add docstring

    """
    if not config.get("query/use_alias", default=False):
        return AliasedString(alias, alias=alias)

    for true_value, _alias in config.get(path).items():
        if alias == _alias:
            return AliasedString(true_value, alias=_alias)

    return AliasedString(alias, alias=alias)
