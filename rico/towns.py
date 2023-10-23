from copy import deepcopy
from typing import Literal, Optional

from attr import Factory, define

from . import GOODS, GoodType, TileType, BuildingType
from .buildings import Building
from .holders import AttrHolder
from .roles import Role
from .tiles import Tile


@define
class Town(AttrHolder):
    name: str
    gov: bool = False
    role: Optional[Role] = None
    tiles: list[Tile] = Factory(list)
    buildings: list[Building] = Factory(list)
    spent_captain: bool = False
    spent_wharf: bool = False

    money: int = 0
    people: int = 0
    points: int = 0
    coffee: int = 0
    corn: int = 0
    indigo: int = 0
    sugar: int = 0
    tobacco: int = 0

    @property
    def total_space(self) -> int:
        return len(self.tiles) + sum(building.space for building in self.buildings)

    @property
    def total_people(self) -> int:
        total = self.count("people")
        for tile in self.tiles:
            total += tile.count("people")
        for building in self.buildings:
            total += building.count("people")
        return total

    @property
    def vacant_jobs(self) -> int:
        total = 0
        for building in self.buildings:
            total += max(0, building.space - building.count("people"))
        return total

    @property
    def vacant_places(self) -> int:
        total = 12
        for building in self.buildings:
            total -= 2 if building.tier == 4 else 1
        return total

    def active_quarries(self):
        return len(
            [
                tile
                for tile in self.tiles
                if tile.type == "quarry" and tile.count("people") >= 1
            ]
        )

    def active_tiles(self, type: TileType) -> int:
        return len(
            [
                tile
                for tile in self.tiles
                if tile.type == type and tile.count("people") >= 1
            ]
        )

    def active_workers(
        self, subclass: Literal["coffee", "tobacco", "sugar", "indigo"]
    ) -> int:
        if subclass == "coffee":
            return sum(
                min(building.count("people"), building.space)
                for building in self.buildings
                if building.type == "coffee_roaster"
            )
        if subclass == "indigo":
            return sum(
                min(building.count("people"), building.space)
                for building in self.buildings
                if building.type in ["small_indigo_plant", "indigo_plant"]
            )
        if subclass == "sugar":
            return sum(
                min(building.count("people"), building.space)
                for building in self.buildings
                if building.type in ["sugar_mill", "small_sugar_mill"]
            )
        if subclass == "tobacco":
            return sum(
                min(building.count("people"), building.space)
                for building in self.buildings
                if building.type == "tobacco_storage"
            )
    def copy(self):
        return deepcopy(self)
    
    def priviledge(self, subclass: BuildingType) -> bool:
        for building in self.buildings:
            if building.type == subclass and building.count("people") >= building.space:
                return True
        return False

    def production(self, good: Optional[GoodType] = None):
        if not good:
            return {_good: self.production(_good) for _good in GOODS}
        raw_production = self.active_tiles(good)
        if good == "corn":
            return raw_production
        active_workers = self.active_workers(good)
        return min(raw_production, active_workers)

    def tally(self):
        points = self.count("points")

        # Buildings
        points += sum(building.tier for building in self.buildings)

        # Large buildings
        if self.priviledge("guild_hall"):
            for building in self.buildings:
                if building.type in ["small_indigo_plant", "small_sugar_mill"]:
                    points += 1
                if building.type in [
                    "coffee_roaster",
                    "indigo_plant",
                    "sugar_mill",
                    "tobacco_storage",
                ]:
                    points += 2
        if self.priviledge("residence"):
            occupied_tiles = len(
                [tile for tile in self.tiles if tile.count("people") >= 1]
            )
            points += max(4, occupied_tiles - 5)
        if self.priviledge("fortress"):
            points += self.total_people // 3
        if self.priviledge("custom_house"):
            points += self.count("points") // 4
        if self.priviledge("city_hall"):
            points += len(
                [
                    building
                    for building in self.buildings
                    if building.type
                    not in [
                        "small_indigo_plant",
                        "small_sugar_mill",
                        "coffee_roaster",
                        "indigo_plant",
                        "sugar_mill",
                        "tobacco_storage",
                    ]
                ]
            )

        return points
