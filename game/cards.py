import random
from typing import Annotated, Optional

from annotated_types import Le, Lt
from pydantic import BaseModel, model_validator

from .counters import *
from .exceptions import *


class Card(BaseModel):
    cls: str


class RoleCard(Holder, Card):
    cls: str = "role"
    subclass: Literal[
        "settler", "mayor", "builder", "craftsman", "trader", "captain", "prospector"
    ]

    def __eq__(self, other):
        try:
            assert self.cls == other.cls
            assert self.subclass == other.subclass
            return True
        except:
            return False


class Tile(Holder, Card):
    cls: str = "tile"
    subclass: Literal["coffee", "tobacco", "corn", "sugar", "indigo", "quarry"]

    def __eq__(self, other):
        try:
            assert self.cls == other.cls
            assert self.subclass == other.subclass
            return True
        except:
            return False
    
    def __lt__(self, other):
        if not isinstance(other, Tile):
            raise TypeError(f"'<' not supported between instances of 'Tile' and '{type(other).__name__}'")
        return self.subclass < other.subclass


class Building(Holder, Card):
    cls: str = "building"
    subclass: Literal[
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
    tier: int
    cost: int
    max_people: int

    # def __init__(self, **kwargs):
    #     super().__init__(**kwargs)
    #     tier, cost, max_people, _ = building_info[self.subclass]
    #     self.tier = tier
    #     self.cost = cost
    #     self.max_people = max_people


    def __eq__(self, other):
        try:
            assert self.cls == other.cls
            assert self.subclass == other.subclass
            return True
        except:
            return False
        
building_info = {
    # subclass:          (tier,   cost, people, number)
    "indigo_plant":       (2,      3,      3,      3),
    "small_indigo_plant": (1,      1,      1,      4),
    "sugar_mill":         (2,      4,      3,      3),
    "small_sugar_mill":   (1,      2,      1,      4),
    "tobacco_storage":    (3,      5,      3,      3),
    "coffee_roaster":     (3,      6,      2,      3),
    "small_market":       (1,      1,      1,      2),
    "hacienda":           (1,      2,      1,      2),
    "construction_hut":   (1,      2,      1,      2),
    "small_warehouse":    (1,      3,      1,      2),
    "hospice":            (2,      4,      1,      2),
    "office":             (2,      5,      1,      2),
    "large_market":       (2,      5,      1,      2),
    "large_warehouse":    (2,      6,      1,      2),
    "factory":            (3,      7,      1,      2),
    "university":         (3,      8,      1,      2),
    "harbor":             (3,      8,      1,      2),
    "wharf":              (3,      9,      1,      2),
    "guild_hall":         (4,     10,      1,      1),
    "residence":          (4,     10,      1,      1),
    "fortress":           (4,     10,      1,      1),
    "city_hall":          (4,     10,      1,      1),
    "custom_house":       (4,     10,      1,      1),
}
