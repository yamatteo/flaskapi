import itertools
import random
from copy import deepcopy
from typing import Iterator, Union

from attr import Factory, define

from .constants import BUILDINFO, BUILDINGS, ROLES, TILES, Building, Role, Tile
from .exceptions import enforce
from .holders import AttrHolder
from .markets import Market
from .towns import Town
from .ships import GoodsShip, PeopleShip, GoodsFleet


@define
class Board(AttrHolder):
    exposed_tiles: list[Tile]
    goods_fleet: GoodsFleet
    market: Market
    people_ship: PeopleShip
    towns: dict[str, Town]
    unbuilt: list[Building]
    unsettled_quarries: int
    unsettled_tiles: list[Tile]

    roles: list[int] = Factory(list)

    money: int = 54
    people: int = 0
    points: int = 122
    coffee: int = 9
    corn: int = 10
    indigo: int = 11
    sugar: int = 11
    tobacco: int = 9

    @classmethod
    def start_new(cls, names: list[str]):
        enforce(3 <= len(names) <= 5, "Players must be between 3 and 5.")
        # if intelligences is None:
        #     intelligences = ["human" for _ in users]
        # assert len(users) == len(intelligences)
        game_data = {}
        game_data["towns"] = {name: Town(name=name) for name in names}

        game_data["people_ship"] = PeopleShip(people=len(names))
        game_data["market"] = Market()
        game_data["goods_fleet"] = GoodsFleet(
            {n: GoodsShip(size=n) for n in range(len(names) + 1, len(names) + 4)}
        )

        # Generate role cards
        game_data["roles"] = [ 0 if i < len(names)+3 else -1 for i in range(8) ]

        # Generate tiles
        game_data["unsettled_quarries"] = 8
        game_data["exposed_tiles"] = (
            ["coffee" for _ in range(8)]
            + ["tobacco" for _ in range(9)]
            + ["corn" for _ in range(10)]
            + ["sugar" for _ in range(11)]
            + ["indigo" for _ in range(12)]
        )
        game_data["unsettled_tiles"] = []
        random.shuffle(game_data["exposed_tiles"])

        # Generate buildings
        game_data["unbuilt"] = [
            kind
            for kind, buildinfo in BUILDINFO.items()
            for _ in range(buildinfo["number"])
        ]

        self = cls(**game_data)

        # Set available people
        self.people = 20 * len(names) - 5

        # Distribute money
        for player in self.towns.values():
            self.money -= len(names) - 1
            player.money += len(names) - 1

        # Distribute tiles
        num_indigo = 2 if len(names) < 5 else 3
        for i, player_name in enumerate(names):
            player = self.towns[player_name]
            self.give_tile(to=player, type="indigo" if i < num_indigo else "corn")
        self.expose_tiles()

        # # Take first action (governor assignment)
        # self.take_action()
        return self
    
    def copy(self):
        return deepcopy(self)

    def empty_ships_and_market(self):
        for size, ship in self.goods_fleet.items():
            what, amount = next(ship.items(), (None, 0))
            if amount >= size:
                ship.give(amount, what, to=self)
        market_total = sum(amount for type, amount in self.market.items())
        if market_total >= 4:
            for type, amount in self.market.items():
                self.market.give(amount, type, to=self)

    def expose_tiles(self):
        all_tiles = self.unsettled_tiles + self.exposed_tiles
        self.exposed_tiles, self.unsettled_tiles = (
            all_tiles[: len(self.towns) + 1],
            all_tiles[len(self.towns) + 1 :],
        )
    
    def give_building(self, building_type: Building, *, to: Town):
        if isinstance(to, str):
            town = self.towns[to]
        else:
            town = to

        buildinfo = BUILDINFO[building_type]
        tier = buildinfo["tier"]
        cost = buildinfo["cost"]
        quarries_discount = min(tier, town.active_quarries())
        builder_discount = 1 if town.role == "builder" else 0
        price = max(0, cost - quarries_discount - builder_discount)
        enforce(town.has(price, "money"), f"Player does not have enough money.")
        enforce(
            [type for type in self.unbuilt if type == building_type],
            f"There are no more {building_type} to sell.",
        )
        enforce(
            town.count_free_build_space() >= (2 if tier == 4 else 1),
            f"Town of {town.name} does not have space for {building_type}",
        )
        enforce(
            building_type not in town.list_buildings(),
            f"Town of {town.name} already has a {building_type}"
        )

        i, type = next(
            (i, type)
            for i, type in enumerate(self.unbuilt)
            if type == building_type
        )
        self.unbuilt.pop(i)
        town.buildings_mixed[BUILDINGS.index(type)] = 0
        town.give(price, "money", to=self)

    def give_tile(self, to: Town, type: Tile):
        if type == "quarry":
            enforce(self.unsettled_quarries, "No more quarry to give.")
            self.unsettled_quarries -= 1
            index = TILES.index(type)
            to.placed_tiles[index] += 1
            # to.tiles.append(Tile(type="quarry"))
            return
        if type == "down":
            enforce(self.unsettled_tiles, "No more covert tiles.")
            tile_type = self.unsettled_tiles.pop(0)
            index = TILES.index(tile_type)
            to.placed_tiles[index] += 1
            # to.tiles.append(tile_type)
            return
        i, tile_type = next(
            (i, tile_type)
            for i, tile_type in enumerate(self.exposed_tiles)
            if tile_type == type
        )
        self.exposed_tiles.pop(i)
        index = TILES.index(tile_type)
        to.placed_tiles[index] += 1
        # to.tiles.append(Tile(type=tile_type))

    def give_role(self, role: Role, *, to: Union[str, Town]):
        if isinstance(to, str):
            town = self.towns[to]
        else:
            town = to
        enforce(town.role is None, f"Player {to} already as role {town.role}.")

        enforce(role in ROLES, f"Role {role} is not available.")
        i = ROLES.index(role)
        enforce(self.roles[i] > -1, f"Role {role} is not available.")
        # available_roles = [role for role, amount in zip(ROLES, self.roles) if amount > -1]
        # role_type = role.type if isinstance(role, Role) else role
        # enforce(role_type in available_roles, f"Role {role_type} is not available.")
        # i = available_roles.index(role_type)

        town.add("money", self.roles[i])
        self.roles[i] = -1
        town.role = role
        # self.roles[i].give("all", "money", to=town)
        # town.role = self.roles.pop(i)

    def is_end_of_round(self):
        return all( (town.role_index != -1) for town in self.towns.values())

    def next_to(self, name: str) -> str:
        cycle = itertools.cycle(self.towns)
        for owner in cycle:
            if name == owner:
                break
        return next(cycle)

    def pay_roles(self):
        # assert It's a bug!
        for i in range(len(self.towns)+3):
            if self.roles[i] == -1:
                self.roles[i] = 0
            else:
               self.roles[i] += self.pop("money", 1)
        # for card in self.roles:
        #     self.give(1, "money", to=card)

    def round_from(self, name: str) -> Iterator[str]:
        cycle = itertools.cycle(self.towns)

        curr_player_name = next(cycle)
        while curr_player_name != name:
            curr_player_name = next(cycle)

        for _ in range(len(self.towns)):
            yield curr_player_name
            curr_player_name = next(cycle)

    def town_round_from(self, name: str) -> Iterator[Town]:
        for town_name in self.round_from(name):
            yield self.towns[town_name]

    def set_governor(self, name: str):
        for owner, town in self.towns.items():
            town.gov = int(owner == name)
