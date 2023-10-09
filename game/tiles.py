from typing import  Literal
from attr import define

from .holders import AttrHolder
from .exceptions import enforce, RuleError

TILES = ["coffee", "corn", "indigo", "quarry", "sugar", "tobacco"]
TileType = Literal["coffee", "corn", "indigo", "quarry", "sugar", "tobacco"]
TILE_INFO = {
    "coffee":8, "corn":10, "indigo":12, "quarry":8, "sugar":11, "tobacco":9
}

@define
class Tile(AttrHolder):
    type: TileType
    people: int = 0

    def __eq__(self, other):
        return isinstance(other, Tile) and self.type == other.type

