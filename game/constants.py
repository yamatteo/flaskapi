from typing import Iterator, Literal, Union, overload

from attr import define

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

ShipableType = Literal[
    "coffee", "corn", "indigo", "people", "sugar", "tobacco"
]
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