import random
from typing import Annotated, Optional

from annotated_types import Le, Lt
from pydantic import BaseModel, model_validator

from .counters import *
from .exceptions import *

ALWAYS_ROLES = ["builder", "captain", "craftsman", "mayor", "settler", "trader"]
ROLES = ["builder", "captain", "craftsman", "mayor", "prospector", "settler", "trader"]
TILE_TYPES = ["coffee", "corn", "indigo", "quarry", "sugar", "tobacco"]
Role = Literal["builder", "captain", "craftsman", "mayor", "prospector", "settler", "trader"]
TileType = Literal["coffee", "corn", "indigo", "quarry", "sugar", "tobacco"]
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


class Card(BaseModel):
    cls: str


class RoleCard(Holder, BaseModel):
    role: Role

    def __eq__(self, other):
        return self.role == getattr(other, "role", None)


class Tile(Holder, BaseModel):
    type: TileType

    def __eq__(self, other):
        return self.type == getattr(other, "type", None)

    def __lt__(self, other):
        if not isinstance(other, Tile):
            raise TypeError(
                f"'<' not supported between instances of 'Tile' and '{type(other).__name__}'"
            )
        return self.type < other.type


class Building(Holder, BaseModel):
    cls: BuildingType

    @property
    def tier(self) -> int:
        return building_info[self.cls][0]

    @property
    def cost(self) -> int:
        return building_info[self.cls][1]

    @property
    def max_people(self) -> int:
        return building_info[self.cls][2]

    def __eq__(self, other):
        try:
            assert self.cls == other.cls
            return True
        except:
            return False


building_info = {
    # cls:          (tier,   cost, people, number)
    "indigo_plant": (2, 3, 3, 3),
    "small_indigo_plant": (1, 1, 1, 4),
    "sugar_mill": (2, 4, 3, 3),
    "small_sugar_mill": (1, 2, 1, 4),
    "tobacco_storage": (3, 5, 3, 3),
    "coffee_roaster": (3, 6, 2, 3),
    "small_market": (1, 1, 1, 2),
    "hacienda": (1, 2, 1, 2),
    "construction_hut": (1, 2, 1, 2),
    "small_warehouse": (1, 3, 1, 2),
    "hospice": (2, 4, 1, 2),
    "office": (2, 5, 1, 2),
    "large_market": (2, 5, 1, 2),
    "large_warehouse": (2, 6, 1, 2),
    "factory": (3, 7, 1, 2),
    "university": (3, 8, 1, 2),
    "harbor": (3, 8, 1, 2),
    "wharf": (3, 9, 1, 2),
    "guild_hall": (4, 10, 1, 1),
    "residence": (4, 10, 1, 1),
    "fortress": (4, 10, 1, 1),
    "city_hall": (4, 10, 1, 1),
    "custom_house": (4, 10, 1, 1),
}
