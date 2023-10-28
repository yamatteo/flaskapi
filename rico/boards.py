import itertools
import random
from copy import deepcopy
from typing import Iterator, Union

from attr import asdict, define

from .constants import BUILDINFO, GOODS, ROLES, BuildingType, RoleType, TileType
from .buildings import Building
from .exceptions import RuleError, enforce
from .holders import AttrHolder
from .markets import Market
from .towns import Town
from .roles import Role
from .ships import GoodsShip, PeopleShip, GoodsFleet
from .tiles import Tile


@define
class Board(AttrHolder):
    exposed_tiles: list[TileType]
    goods_fleet: GoodsFleet
    market: Market
    people_ship: PeopleShip
    towns: dict[str, Town]
    roles: list[Role]
    unbuilt: list[BuildingType]
    unsettled_quarries: int
    unsettled_tiles: list[TileType]

    money: int = 0
    people: int = 0
    points: int = 0
    coffee: int = 0
    corn: int = 0
    indigo: int = 0
    sugar: int = 0
    tobacco: int = 0

    @classmethod
    def start_new(cls, names: list[str]):
        enforce(3 <= len(names) <= 5, "Players must be between 3 and 5.")
        # if intelligences is None:
        #     intelligences = ["human" for _ in users]
        # assert len(users) == len(intelligences)
        game_data = {}
        game_data["towns"] = {name: Town(name=name) for name in names}

        # Generate countables
        game_data["money"] = 54
        game_data["points"] = 122
        game_data["people"] = 20 * len(names) - 5
        game_data["coffee"] = 9
        game_data["corn"] = 10
        game_data["indigo"] = 11
        game_data["sugar"] = 11
        game_data["tobacco"] = 9

        game_data["people_ship"] = PeopleShip(people=len(names))
        game_data["market"] = Market()
        game_data["goods_fleet"] = GoodsFleet(
            {n: GoodsShip(size=n) for n in range(len(names) + 1, len(names) + 4)}
        )

        # Generate role cards
        game_data["roles"] = [Role(type=r) for r in ROLES if r != "prospector"] + [
            Role(type="prospector") for _ in range(len(names) - 3)
        ]

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

    def give_tile(self, to: Town, type: TileType):
        if type == "quarry":
            enforce(self.unsettled_quarries, "No more quarry to give.")
            self.unsettled_quarries -= 1
            to.tiles.append(Tile(type="quarry"))
            return
        if type == "down":
            enforce(self.unsettled_tiles, "No more covert tiles.")
            tile_type = Tile(type=self.unsettled_tiles.pop(0))
            to.tiles.append(tile_type)
            return
        i, tile_type = next(
            (i, tile_type)
            for i, tile_type in enumerate(self.exposed_tiles)
            if tile_type == type
        )
        self.exposed_tiles.pop(i)
        to.tiles.append(Tile(type=tile_type))

    def give_role(self, role: Union[RoleType, Role], *, to: Union[str, Town]):
        if isinstance(to, str):
            town = self.towns[to]
        else:
            town = to
        enforce(town.role is None, f"Player {to} already as role {town.role}.")
        available_roles = [role.type for role in self.roles]
        role_type = role.type if isinstance(role, Role) else role
        enforce(role_type in available_roles, f"Role {role_type} is not available.")
        i = available_roles.index(role_type)
        town.role = self.roles.pop(i)
        town.role.give("all", "money", to=town)

    def is_end_of_round(self):
        return all(town.role is not None for town in self.towns.values())

    def next_to(self, name: str) -> str:
        cycle = itertools.cycle(self.towns)
        for owner in cycle:
            if name == owner:
                break
        return next(cycle)

    def pay_roles(self):
        for card in self.roles:
            self.give(1, "money", to=card)

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

    # def project_action(self, action: Action):
    #     projection = deepcopy(self)
    #     projection.take_action(action)
    #     return projection

    def set_governor(self, name: str):
        for owner, town in self.towns.items():
            town.gov = owner == name
