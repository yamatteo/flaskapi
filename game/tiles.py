from typing import  Literal
from pydantic import BaseModel

from .holders import Holder
from .exceptions import enforce, RuleError

REGULAR_TILES = ["coffee", "corn", "indigo", "sugar", "tobacco"]
TILES = ["coffee", "corn", "indigo", "quarry", "sugar", "tobacco"]
TileType = Literal["coffee", "corn", "indigo", "quarry", "sugar", "tobacco"]


class Tile(Holder, BaseModel):
    type: TileType

    @classmethod
    def from_compressed(cls, data: str):
        type, people = data.split(":")
        return Tile(type=type, people=people)

    def __eq__(self, other):
        return isinstance(other, Tile) and self.type == other.type

    def __lt__(self, other):
        if not isinstance(other, Tile):
            raise TypeError(
                f"'<' not supported between instances of 'Tile' and '{type(other).__name__}'"
            )
        return self.type < other.type
    
    def compress(self):
        return f"{self.type}:{self.people}"

