from copy import deepcopy
from typing import Literal, Optional, overload

from attr import Factory, define

from rico.constants import BUILDINFO, BUILDINGS, PROD_BUILDINGS, ROLES, TILES, Role

from . import GOODS, GoodType, Tile, Building
from .buildings import ActualBuilding
from .holders import AttrHolder


@define
class Town(AttrHolder):
    name: str
    gov: bool = False
    role_index: int = -1
    placed_tiles: list[int] = Factory(lambda: [0]*8)
    worked_tiles: list[int] = Factory(lambda: [0]*8)
    # buildings: list[ActualBuilding] = Factory(list)
    buildings_mixed: list[int] = Factory(lambda: [-1]*len(BUILDINGS))
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
        return sum(self.placed_tiles) + sum(self.list_buildings("space"))

    @property
    def total_people(self) -> int:
        total = self.count("people")
        total += sum(self.worked_tiles)
        # for tile in self.tiles:
        #     total += tile.count("people")
        total += sum(self.list_buildings("people"))
        # for building in self.buildings:
        #     total += building.count("people")
        return total

    @property
    def vacant_jobs(self) -> int:
        total = 0
        for space, people in zip(self.list_buildings("space"), self.list_buildings("people")):
            total += max(0, space - people)
        return total

    @property
    def vacant_places(self) -> int:
        total = 12
        for tier in self.list_buildings("tier"):
            total -= 2 if tier == 4 else 1
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
            i = BUILDINGS.index("coffee_roaster")
            space = BUILDINFO["coffee_roaster"]["space"]
            workers = max(0, self.buildings_mixed[i])
            return min(space, workers)
            # return sum(
            #     min(building.count("people"), building.space)
            #     for building in self.buildings
            #     if building.type == "coffee_roaster"
            # )
        if subclass == "indigo":
            i = BUILDINGS.index("small_indigo_plant")
            space_i = BUILDINFO["small_indigo_plant"]["space"]
            workers_i = max(0, self.buildings_mixed[i])
            j = BUILDINGS.index("indigo_plant")
            space_j = BUILDINFO["indigo_plant"]["space"]
            workers_j = max(0, self.buildings_mixed[j])
            return min(space_i, workers_i) + min(space_j, workers_j)
            # return sum(
            #     min(building.count("people"), building.space)
            #     for building in self.buildings
            #     if building.type in ["small_indigo_plant", "indigo_plant"]
            # )
        if subclass == "sugar":
            i = BUILDINGS.index("sugar_mill")
            space_i = BUILDINFO["sugar_mill"]["space"]
            workers_i = max(0, self.buildings_mixed[i])
            j = BUILDINGS.index("small_sugar_mill")
            space_j = BUILDINFO["small_sugar_mill"]["space"]
            workers_j = max(0, self.buildings_mixed[j])
            return min(space_i, workers_i) + min(space_j, workers_j)
            # return sum(
            #     min(building.count("people"), building.space)
            #     for building in self.buildings
            #     if building.type in ["sugar_mill", "small_sugar_mill"]
            # )
        if subclass == "tobacco":
            i = BUILDINGS.index("tobacco_storage")
            space = BUILDINFO["tobacco_storage"]["space"]
            workers = max(0, self.buildings_mixed[i])
            return min(space, workers)
            # return sum(
            #     min(building.count("people"), building.space)
            #     for building in self.buildings
            #     if building.type == "tobacco_storage"
            # )
    
    # @property
    # def buildings(self) -> list[ActualBuilding]:
    #     l = []
    #     for building, info in zip(BUILDINGS, self.buildings_mixed):
    #         if info == -1:
    #             continue
    #         l.append(ActualBuilding(building, people=info))
    #     return l
    
    def count_farmers(self, tile_type: Tile) -> int:
        return self.worked_tiles[TILES.index(tile_type)]
        # return sum(tile.people for tile in self.tiles if tile.type == tile_type)
    
    def count_workers(self, build_type: Building) -> int:
        i = BUILDINGS.index(build_type)
        return max(0, self.buildings_mixed[i])
        # for built in self.buildings:
        #     if built.type == build_type:
        #         return built.count("people")
        # return 0
        
    def copy(self):
        return deepcopy(self)
    
    def privilege(self, subclass: Building) -> bool:
        space = BUILDINFO[subclass]["space"]
        workers = self.count_workers(subclass)
        return workers >= space
        # for building in self.buildings:
        #     if building.type == subclass and building.count("people") >= building.space:
        #         return True
        # return False

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

    @overload
    def list_buildings(self) -> list[Building]:
        ...

    @overload
    def list_buildings(self, attr: str) -> list[int]:
        ...
    
    def list_buildings(self, attr="types") -> list[Building]:
        if attr == "people":
            return [ info for info in self.buildings_mixed if info > -1]
        types = [ b for b, info in zip(BUILDINGS, self.buildings_mixed) if info > -1]
        if attr == "types":
            return types
        elif attr == "space":
            return [ BUILDINFO[t]["space"] for t in types ]
        elif attr == "tier":
            return [ BUILDINFO[t]["tier"] for t in types ]

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
        points += sum(self.list_buildings("tier"))

        # Large buildings
        if self.privilege("guild_hall"):
            for building in self.list_buildings():
                if building in ["small_indigo_plant", "small_sugar_mill"]:
                    points += 1
                if building in [
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
                    for building in self.list_buildings()
                    if building
                    not in PROD_BUILDINGS
                ]
            )

        return points
