from attr import define

from . import TileType
from .holders import AttrHolder

@define
class Tile(AttrHolder):
    type: TileType
    people: int = 0

    def __eq__(self, other):
        return isinstance(other, Tile) and self.type == other.type

