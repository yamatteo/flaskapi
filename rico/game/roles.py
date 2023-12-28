from typing import  Literal

from pydantic import BaseModel

from .holders import Holder

REGULAR_ROLES = ["builder", "captain", "craftsman", "mayor", "settler", "trader"]
ROLES = ["builder", "captain", "craftsman", "mayor", "prospector", "settler", "trader"]
RoleType = Literal["builder", "captain", "craftsman", "mayor", "prospector", "settler", "trader"]

class Role(Holder, BaseModel):
    type: RoleType

    @classmethod
    def from_compressed(cls, data: str):
        type, money = data.split(":")
        return Role(type=type, money=money)

    def __eq__(self, other):
        if isinstance(other, Role):
            return self.type == other.type
        elif isinstance(other, str):
            return self.type == other
        else:
            return False
    
    def compress(self):
        return f"{self.type}:{self.money}"