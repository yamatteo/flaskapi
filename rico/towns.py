from copy import deepcopy
from typing import Literal, Optional, overload

from attr import Factory, define

from rico.constants import ROLES, TILES, Role

from . import GOODS, GoodType, Tile, BuildingType
from .buildings import Building
from .holders import AttrHolder


@define
class Town(AttrHolder):
    name: str
    gov: bool = False
    role_index: int = -1
    placed_tiles: list[int] = Factory(lambda: [0]*8)
    worked_tiles: list[int] = Factory(lambda: [0]*8)
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
        return sum(self.placed_tiles) + sum(building.space for building in self.buildings)

    @property
    def total_people(self) -> int:
        total = self.count("people")
        total += sum(self.worked_tiles)
        # for tile in self.tiles:
        #     total += tile.count("people")
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
        return self.worked_tiles[TILES.index("quarry")]
        # return len(
        #     [
        #         tile
        #         for tile in self.tiles
        #         if tile.type == "quarry" and tile.count("people") >= 1
        #     ]
        # )

    def active_tiles(self, type: Tile) -> int:
        return self.worked_tiles[TILES.index(type)]
        # return len(
        #     [
        #         tile
        #         for tile in self.tiles
        #         if tile.type == type and tile.count("people") >= 1
        #     ]
        # )

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
    
    def count_farmers(self, tile_type: Tile) -> int:
        return self.worked_tiles[TILES.index(tile_type)]
        # return sum(tile.people for tile in self.tiles if tile.type == tile_type)
    
    def count_workers(self, build_type: BuildingType) -> int:
        for built in self.buildings:
            if built.type == build_type:
                return built.count("people")
        return 0
        
    def copy(self):
        return deepcopy(self)
    
    def privilege(self, subclass: BuildingType) -> bool:
        for building in self.buildings:
            if building.type == subclass and building.count("people") >= building.space:
                return True
        return False

    @overload
    def production(self) -> dict[GoodType, int]:
        ...

    @overload
    def production(self, good: GoodType) -> int:
        ...

    def production(self, good: Optional[GoodType] = None):
        if not good:
            return {_good: self.production(_good) for _good in GOODS}
        raw_production = self.active_tiles(good)
        if good == "corn":
            return raw_production
        active_workers = self.active_workers(good)
        return min(raw_production, active_workers)

    def list_tiles(self) -> list[Tile]:
        l = []
        for tile, placed in zip(TILES, self.placed_tiles):
            l.extend( [tile]*placed )
        return l
    
    @property
    def role(self) -> Optional[Role]:
        if self.role_index == -1:
            return None
        return ROLES[self.role_index]
    
    @role.setter
    def role(self, role: Optional[Role]):
        if role is None:
            i = -1
        else:
            i = ROLES.index(role)
        self.role_index = i

    def tally(self):
        points = self.count("points")

        # Buildings
        points += sum(building.tier for building in self.buildings)

        # Large buildings
        if self.privilege("guild_hall"):
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
        if self.privilege("residence"):
            occupied_tiles = sum(self.worked_tiles)
            # occupied_tiles = len(
            #     [tile for tile in self.tiles if tile.count("people") >= 1]
            # )
            points += max(4, occupied_tiles - 5)
        if self.privilege("fortress"):
            points += self.total_people // 3
        if self.privilege("custom_house"):
            points += self.count("points") // 4
        if self.privilege("city_hall"):
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
