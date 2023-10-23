from typing import Literal


CountableType = Literal[
    "coffee", "corn", "indigo", "money", "people", "points", "sugar", "tobacco"
]

COUNTABLES: list[CountableType] = [
    "coffee",
    "corn",
    "indigo",
    "money",
    "people",
    "points",
    "sugar",
    "tobacco",
]

ShipableType = Literal["coffee", "corn", "indigo", "people", "sugar", "tobacco"]

SHIPABLES: list[ShipableType] = [
    "coffee",
    "corn",
    "indigo",
    "people",
    "sugar",
    "tobacco",
]

GoodType = Literal[
    "coffee",
    "corn",
    "indigo",
    "sugar",
    "tobacco",
]

GOODS: list[GoodType] = [
    "coffee",
    "corn",
    "indigo",
    "sugar",
    "tobacco",
]

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

BUILDINGS = [
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

ROLES = ["builder", "captain", "craftsman", "mayor", "prospector", "settler", "trader"]

RoleType = Literal[
    "builder", "captain", "craftsman", "mayor", "prospector", "settler", "trader"
]



TILES = ["coffee", "corn", "indigo", "quarry", "sugar", "tobacco"]
TileType = Literal["coffee", "corn", "indigo", "quarry", "sugar", "tobacco"]
TILE_INFO = {
    "coffee":8, "corn":10, "indigo":12, "quarry":8, "sugar":11, "tobacco":9
}

from .boards import Board
from .buildings import Building
from .exceptions import enforce, RuleError
from .holders import AttrHolder
from .markets import Market
from .roles import Role
from .ships import GoodsShip, GoodsFleet
from .tiles import Tile
from .towns import Town
