import itertools
import random
from copy import deepcopy
from typing import Iterator

from attr import asdict, define

from . import BUILDINFO, GOODS, ROLES, BuildingType, RoleType, TileType
from .buildings import Building
from .exceptions import RuleError, enforce
from .holders import AttrHolder
from .markets import Market
from .towns import Town
from .roles import Role
from .ships import GoodsShip, PeopleShip, GoodsFleet
from .tiles import Tile


class GameOver(Exception):
    pass


@define
class Board(AttrHolder):
    # actions: list # TODO
    exposed_tiles: list[TileType]
    goods_fleet: GoodsFleet
    market: Market
    people_ship: PeopleShip
    # play_order: list[str]
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

    # @property
    # def expected_player(self) -> Town:
    #     name = self.actions[0].player_name
    #     return self.towns[name]

    # @property
    # def expected_action(self) -> Action:
    #     return self.actions[0]

    @classmethod
    def start_new(cls, users: list[str]):
        enforce(3 <= len(users) <= 5, "Players must be between 3 and 5.")
        # if intelligences is None:
        #     intelligences = ["human" for _ in users]
        # assert len(users) == len(intelligences)
        game_data = {}
        game_data["towns"] = {
            name: Town(name=name)
            for name in users
        }
        # game_data["players"] = {
        #     name: Town(name=name, intelligence=intelligence)
        #     for name, intelligence in zip(users, intelligences)
        # }

        # Assign playing order
        # game_data["play_order"] = list(
        #     random.sample(list(game_data["players"].keys()), k=len(users))
        # )
        # game_data["actions"] = [
        #     GovernorAction(player_name=name) for name in game_data["play_order"]
        # ]

        # Generate countables
        # game_data["n"] = f"m54p122w{20 * len(users) - 5}c9k10i11s11t9"
        game_data["money"] = 54
        game_data["points"] = 122
        game_data["people"] = 20 * len(users) - 5
        game_data["coffee"] = 9
        game_data["corn"] = 10
        game_data["indigo"] = 11
        game_data["sugar"] = 11
        game_data["tobacco"] = 9

        game_data["people_ship"] = PeopleShip(people=len(users))
        game_data["market"] = Market()
        game_data["goods_fleet"] = {
            n: GoodsShip(size=n) for n in range(len(users) + 1, len(users) + 4)
        }

        # Generate role cards
        game_data["roles"] = [Role(type=r) for r in ROLES if r != "prospector"] + [
            Role(type="prospector") for _ in range(len(users) - 3)
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
            self.money -= len(users) - 1
            player.money += len(users) - 1

        # Distribute tiles
        num_indigo = 2 if len(users) < 5 else 3
        for i, player_name in enumerate(users):
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

    # def is_expecting(self, action: Action) -> bool:
    #     return (
    #         self.expected_action.type == action.type
    #         and self.expected_action.player_name == action.player_name
    #     )

    def name_round_from(self, player_name: str) -> Iterator[str]:
        cycle = itertools.cycle(self.play_order)
        curr_player_name = next(cycle)
        while curr_player_name != player_name:
            curr_player_name = next(cycle)
        for _ in range(len(self.towns)):
            yield curr_player_name
            curr_player_name = next(cycle)

    def player_round_from(self, player_name: str) -> Iterator[Town]:
        cycle = itertools.cycle(self.play_order)
        curr_player_name = next(cycle)
        while curr_player_name != player_name:
            curr_player_name = next(cycle)
        for _ in range(len(self.towns)):
            yield self.towns[curr_player_name]
            curr_player_name = next(cycle)

    def pop_role(self, role: RoleType) -> Role:
        i = next(i for i, card in enumerate(self.roles) if card.type == role)
        return self.roles.pop(i)
    
    # def project_action(self, action: Action):
    #     projection = deepcopy(self)
    #     projection.take_action(action)
    #     return projection

    # def take_action(self, action: Action = None):
    #     # Next governor is assigned automatically
    #     if action is None:
    #         if self.expected_action.type == "governor":
    #             self.expected_action.react(self)
    #             self.take_action()
    #         # elif self.expected_player.intelligence == "rufus":
    #         #     action = Rufus(self.expected_player.name).decide(self)
    #         #     self.take_action(action)
    #         elif self.expected_player.intelligence == "quentin":
    #             action = Quentin(self.expected_player.name).decide(self)
    #             self.take_action(action)

    #     else:
    #         action.react(self)
    #         # print("TOOK", action)
    #         self._broadcast(asdict(action), "action")
    #         self.take_action()

    def terminate(self, reason: str = None):
        if reason:
            raise GameOver(reason)
        else:
            raise GameOver("Game over for no reason.")
