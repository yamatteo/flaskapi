from typing import Literal, Optional
from attr import define

from .constants import GOODS, GoodType, CountableType


from .holders import AttrHolder


@define
class Ship(AttrHolder):
    people: int = 0
    coffee: int = 0
    corn: int = 0
    indigo: int = 0
    sugar: int = 0
    tobacco: int = 0

    size: Optional[int] = None

    def accepts(self, good: GoodType, others: list["Ship"]):
        for g in GOODS:
            if self.has(g) and g != good:
                return False
        if len([ship for ship in others if ship.has(good)]) == int(self.has(good)):
            return self.count(good) < getattr(self, "size", 100)
        else:
            return False
