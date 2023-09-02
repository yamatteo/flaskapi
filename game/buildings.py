from pydantic import BaseModel

from .exceptions import *
from .holders import *

SMALL_PRODUCTION_BUILDINGS = ["small_indigo_plant", "small_sugar_mill"]
LARGE_PRODUCTION_BUILDINGS = [
    "indigo_plant",
    "sugar_mill",
    "tobacco_storage",
    "coffee_roaster",
]
SMALL_BUILDINGS = [
    "small_market",
    "hacienda",
    "construction_hut",
    "small_warehouse",
    "hospice",
    "office",
    "large_market",
    "large_warehouse",
    "factory",
    "university",
    "harbor",
    "wharf",
]
LARGE_BUILDINGS = ["guild_hall", "residence", "fortress", "city_hall", "custom_house"]
BUILDINGS = (
    SMALL_PRODUCTION_BUILDINGS
    + LARGE_PRODUCTION_BUILDINGS
    + SMALL_BUILDINGS
    + LARGE_BUILDINGS
)
BuildingType = Literal[
    "indigo_plant",
    "small_indigo_plant",
    "sugar_mill",
    "small_sugar_mill",
    "tobacco_storage",
    "coffee_roaster",
    "small_market",
    "hacienda",
    "construction_hut",
    "small_warehouse",
    "hospice",
    "office",
    "large_market",
    "large_warehouse",
    "factory",
    "university",
    "harbor",
    "wharf",
    "guild_hall",
    "residence",
    "fortress",
    "city_hall",
    "custom_house",
]


class Building(Holder, BaseModel):
    type: BuildingType

    @property
    def tier(self) -> int:
        return BUILDINFO[self.type]["tier"]

    @property
    def cost(self) -> int:
        return BUILDINFO[self.type]["cost"]

    @property
    def space(self) -> int:
        return BUILDINFO[self.type]["space"]
    
    @classmethod
    def from_compressed(self, data):
        type, people = data.split(":")
        return Building(type=type, people=int(people))

    def __eq__(self, other):
        return isinstance(other, Building) and self.type == other.type
    
    def compress(self):
        return f"{self.type}:{self.people}"


BUILDINFO = {
    "indigo_plant": {"tier": 2, "cost": 3, "space": 3, "number": 3},
    "small_indigo_plant": {"tier": 1, "cost": 1, "space": 1, "number": 4},
    "sugar_mill": {"tier": 2, "cost": 4, "space": 3, "number": 3},
    "small_sugar_mill": {"tier": 1, "cost": 2, "space": 1, "number": 4},
    "tobacco_storage": {"tier": 3, "cost": 5, "space": 3, "number": 3},
    "coffee_roaster": {"tier": 3, "cost": 6, "space": 2, "number": 3},
    "small_market": {"tier": 1, "cost": 1, "space": 1, "number": 2},
    "hacienda": {"tier": 1, "cost": 2, "space": 1, "number": 2},
    "construction_hut": {"tier": 1, "cost": 2, "space": 1, "number": 2},
    "small_warehouse": {"tier": 1, "cost": 3, "space": 1, "number": 2},
    "hospice": {"tier": 2, "cost": 4, "space": 1, "number": 2},
    "office": {"tier": 2, "cost": 5, "space": 1, "number": 2},
    "large_market": {"tier": 2, "cost": 5, "space": 1, "number": 2},
    "large_warehouse": {"tier": 2, "cost": 6, "space": 1, "number": 2},
    "factory": {"tier": 3, "cost": 7, "space": 1, "number": 2},
    "university": {"tier": 3, "cost": 8, "space": 1, "number": 2},
    "harbor": {"tier": 3, "cost": 8, "space": 1, "number": 2},
    "wharf": {"tier": 3, "cost": 9, "space": 1, "number": 2},
    "guild_hall": {"tier": 4, "cost": 10, "space": 1, "number": 1},
    "residence": {"tier": 4, "cost": 10, "space": 1, "number": 1},
    "fortress": {"tier": 4, "cost": 10, "space": 1, "number": 1},
    "city_hall": {"tier": 4, "cost": 10, "space": 1, "number": 1},
    "custom_house": {"tier": 4, "cost": 10, "space": 1, "number": 1},
}
