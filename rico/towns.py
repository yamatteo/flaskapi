from copy import deepcopy
from typing import Literal, Optional, overload

from attr import Factory, define, asdict

from .constants import (BUILDINFO, BUILDINGS, GOODS, PROD_BUILDINGS, ROLES,
                        TILES, Building, GoodType, Role, Tile)
from .holders import AttrHolder


@define
class Town(AttrHolder):
    name: str

    # Booleans; 0 is False, 1 is True
    gov: int = 0
    spent_captain: int = 0
    spent_wharf: int = 0

    # Optional index. -1 means role is None, otherwise its ROLES[n]
    role_index: int = -1

    # List of counters.
    # placed_tiles[i] = n means the town has n tiles of type TILES[i]
    # worked_tiles[i] = n means the town has n *active* tiles of type TILES[i]
    # buildings_mixed[i] = -1 means the town doesn't have building BUILDINGS[i]
    # buildings_mixed[i] = n means the town has building BUILDINGS[i] with n workers
    placed_tiles: list[int] = Factory(lambda: [0] * 8)
    worked_tiles: list[int] = Factory(lambda: [0] * 8)
    buildings_mixed: list[int] = Factory(lambda: [-1] * len(BUILDINGS))

    # Simple counters. People refers to people in the pool, not counting workers of tiles and buildings.
    money: int = 0
    people: int = 0
    points: int = 0
    coffee: int = 0
    corn: int = 0
    indigo: int = 0
    sugar: int = 0
    tobacco: int = 0

    def active_quarries(self):
        return self.worked_tiles[TILES.index("quarry")]

    def active_tiles(self, type: Tile) -> int:
        return self.worked_tiles[TILES.index(type)]

    def active_workers(
        self, subclass: Literal["coffee", "tobacco", "sugar", "indigo"]
    ) -> int:
        if subclass == "coffee":
            i = BUILDINGS.index("coffee_roaster")
            space = BUILDINFO["coffee_roaster"]["space"]
            workers = max(0, self.buildings_mixed[i])
            return min(space, workers)
        if subclass == "indigo":
            i = BUILDINGS.index("small_indigo_plant")
            space_i = BUILDINFO["small_indigo_plant"]["space"]
            workers_i = max(0, self.buildings_mixed[i])
            j = BUILDINGS.index("indigo_plant")
            space_j = BUILDINFO["indigo_plant"]["space"]
            workers_j = max(0, self.buildings_mixed[j])
            return min(space_i, workers_i) + min(space_j, workers_j)
        if subclass == "sugar":
            i = BUILDINGS.index("sugar_mill")
            space_i = BUILDINFO["sugar_mill"]["space"]
            workers_i = max(0, self.buildings_mixed[i])
            j = BUILDINGS.index("small_sugar_mill")
            space_j = BUILDINFO["small_sugar_mill"]["space"]
            workers_j = max(0, self.buildings_mixed[j])
            return min(space_i, workers_i) + min(space_j, workers_j)
        if subclass == "tobacco":
            i = BUILDINGS.index("tobacco_storage")
            space = BUILDINFO["tobacco_storage"]["space"]
            workers = max(0, self.buildings_mixed[i])
            return min(space, workers)
    
    def asdict(self) -> dict:
        return asdict(self)

    def count_farmers(self, tile_type: Tile) -> int:
        return self.worked_tiles[TILES.index(tile_type)]

    def count_free_build_space(self) -> int:
        total = 12
        for tier in self.list_buildings("tier"):
            total -= 2 if tier == 4 else 1
        return total

    def count_total_jobs(self) -> int:
        return sum(self.placed_tiles) + sum(self.list_buildings("space"))

    def count_total_people(self) -> int:
        return (
            self.count("people")
            + sum(self.worked_tiles)
            + sum(self.list_buildings("people"))
        )

    def count_vacant_building_jobs(self) -> int:
        total = 0
        for space, people in zip(
            self.list_buildings("space"), self.list_buildings("people")
        ):
            total += max(0, space - people)
        return total

    def count_workers(self, build_type: Building) -> int:
        i = BUILDINGS.index(build_type)
        return max(0, self.buildings_mixed[i])

    def copy(self):
        return deepcopy(self)

    def privilege(self, subclass: Building) -> bool:
        space = BUILDINFO[subclass]["space"]
        workers = self.count_workers(subclass)
        return workers >= space

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
            return [info for info in self.buildings_mixed if info > -1]
        types = [b for b, info in zip(BUILDINGS, self.buildings_mixed) if info > -1]
        if attr == "types":
            return types
        elif attr == "space":
            return [BUILDINFO[t]["space"] for t in types]
        elif attr == "tier":
            return [BUILDINFO[t]["tier"] for t in types]

    def list_tiles(self) -> list[Tile]:
        l = []
        for tile, placed in zip(TILES, self.placed_tiles):
            l.extend([tile] * placed)
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
            points += max(4, occupied_tiles - 5)
        if self.privilege("fortress"):
            points += self.count_total_people() // 3
        if self.privilege("custom_house"):
            points += self.count("points") // 4
        if self.privilege("city_hall"):
            points += len(
                [
                    building
                    for building in self.list_buildings()
                    if building not in PROD_BUILDINGS
                ]
            )

        return points
