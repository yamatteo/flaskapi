from attr import define

from . import BUILDINFO, Building
from .holders import AttrHolder


@define
class ActualBuilding(AttrHolder):
    type: Building
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



