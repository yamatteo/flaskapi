from typing import Literal
from attr import define


from .holders import AttrHolder

REGULAR_ROLES = ["builder", "captain", "craftsman", "mayor", "settler", "trader"]
ROLES = ["builder", "captain", "craftsman", "mayor", "prospector", "settler", "trader"]
RoleType = Literal[
    "builder", "captain", "craftsman", "mayor", "prospector", "settler", "trader"
]


@define
class Role(AttrHolder):
    type: RoleType
    money: int = 0

    def __eq__(self, other):
        if isinstance(other, Role):
            return self.type == other.type
        else:
            return self.type == other