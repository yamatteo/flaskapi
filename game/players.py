from .cards import *


class Player(Holder, BaseModel):
    name: str
    pseudo: str = "#?"
    governor_card: Optional[GovernorCard] = None
    role_card: Optional[RoleCard] = None
    tiles: list[Tile] = []
    buildings: list[Building] = []
    _spent_captain: bool = False
    _spent_wharf: bool = False

    @property
    def is_governor(self) -> bool:
        return self.governor_card is not None

    @property
    def role(self) -> Optional[str]:
        try:
            return self.role_card.subclass
        except AttributeError:
            return None

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
            total += max(0, building.max_people - building.count("people"))
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
                if tile.subclass == "quarry" and tile.count("people") >= 1
            ]
        )
    
    def active_tiles(self, subclass: Literal["coffee", "tobacco", "corn", "sugar", "indigo", "quarry"]) -> int:
        return len(
            [
                tile
                for tile in self.tiles
                if tile.subclass == subclass and tile.count("people") >= 1
            ]
        )
    
    def active_workers(self, subclass: Literal["coffee", "tobacco", "sugar", "indigo"]) -> int:
        if subclass == "coffee":
            return sum( min(building.count("people"), building.max_people) for building in self.buildings if building.subclass == "coffee_roaster")
        if subclass == "indigo":
            return sum( min(building.count("people"), building.max_people) for building in self.buildings if building.subclass in ["small_indigo_plant", "indigo_plant" ])
        if subclass == "sugar":
            return sum( min(building.count("people"), building.max_people) for building in self.buildings if building.subclass  in ["sugar_mill", "small_sugar_mill"])
        if subclass == "tobacco":
            return sum( min(building.count("people"), building.max_people) for building in self.buildings if building.subclass == "tobacco_storage")


    def is_equivalent_to(self, other: "Player"):
        try:
            assert self.name == other.name
            assert self.pseudo == other.pseudo
            assert (self.governor_card is None) == (other.governor_card is None)
            assert self.role_card == other.role_card
            assert sorted(self.tiles) == sorted(other.tiles)
            assert sorted(self.buildings) == sorted(other.buildings)
            return True
        except:
            return False

    def priviledge(self, subclass: str):
        for building in self.buildings:
            if building.subclass == subclass and building.count("people") >= building.max_people:
                return True
    
    def production(self, good: Optional[Good] = None):
        if not good:
            return {_good: self.production(_good) for _good in GOODS}
        raw_production = self.active_tiles(good)
        if good == "corn":
            return raw_production
        active_workers = self.active_workers(good)
        return min(raw_production, active_workers)
