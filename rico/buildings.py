from attr import define

from . import BUILDINFO, BuildingType
from .holders import AttrHolder


@define
class Building(AttrHolder):
    type: BuildingType
    people: int = 0

    @property
    def tier(self) -> int:
        return BUILDINFO[self.type]["tier"]

    @property
    def cost(self) -> int:
        return BUILDINFO[self.type]["cost"]

    @property
    def space(self) -> int:
        return BUILDINFO[self.type]["space"]



