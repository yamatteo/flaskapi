from typing import Optional

from attr import define

from . import GOODS, CountableType, GoodType
from .holders import AttrHolder

@define
class PeopleShip(AttrHolder):
    people: int = 0


@define
class GoodsShip(AttrHolder):
    coffee: int = 0
    corn: int = 0
    indigo: int = 0
    sugar: int = 0
    tobacco: int = 0

    size: Optional[int] = None

    def contains(self) -> Optional[GoodType]:
        return next((g for g in GOODS if self.has(g)), None)

    def has_space(self) -> bool:
        return max(self.count(g) for g in GOODS) < self.size


class GoodsFleet(dict[int, GoodsShip]):
    def accepts(self, ship_size: int, good: GoodType):
        in_transit = any(ship.has(good) for ship in self.values())
        ship = self[ship_size]
        contained = ship.contains()
        free = (not in_transit) and (contained is None)
        bounded = in_transit and contained == good and ship.has_space()
        return free or bounded
