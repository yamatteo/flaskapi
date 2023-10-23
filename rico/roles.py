from attr import define

from . import RoleType
from .holders import AttrHolder


@define
class Role(AttrHolder):
    type: RoleType
    money: int = 0

    def __eq__(self, other):
        if isinstance(other, Role):
            return self.type == other.type
        else:
            return self.type == other
