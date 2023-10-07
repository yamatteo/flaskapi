import itertools
import random
from typing import Callable, Iterator

from attr import Factory, evolve, define

from .bots.rufus import Rufus
from .buildings import BUILDINFO, Building, BuildingType
from .exceptions import RuleError, enforce
from .holders import GOODS, AttrHolder, Holder
from .players import Player
from .pseudos import generate_pseudos
from .reactions import *
from .reactions.base import Action
from .roles import REGULAR_ROLES, Role, RoleType
from .tiles import Tile, TileType


class GameOver(Exception):
    pass

@define
class Game(AttrHolder):
    actions: list[Action]
    exposed_tiles: list[TileType]
    goods_ships: dict[int, Holder]
    market: Holder
    people_ship: Holder
    play_order: list[str]
    players: dict[str, Player]
    roles: list[Role] = Factory(list)
    unbuilt: list[BuildingType] = Factory(list)
    unsettled_quarries: int = 0
    unsettled_tiles: list[TileType] = Factory(list)
    _broadcast: Callable = lambda *_: None

    money: int = 0
    people: int = 0
    points: int = 0
    coffee: int = 0
    corn: int = 0
    indigo: int = 0
    sugar: int = 0
    tobacco: int = 0

    @property
    def expected_player(self) -> Player:
        name = self.actions[0].player_name
        return self.players[name]

    @property
    def expected_action(self) -> Action:
        return self.actions[0]

    @classmethod
    def start_new(cls, users: list[str], intelligences: list[str] = None):
        enforce(3 <= len(users) <= 5, "Players must be between 3 and 5.")
        if intelligences is None:
            intelligences = ["human" for _ in users]
        assert len(users) == len(intelligences)
        game_data = {}
        pseudos = generate_pseudos(users)
        game_data["players"] = {
            name: Player(name=name, pseudo=pseudos[name], intelligence=intelligence)
            for name, intelligence in zip(users, intelligences)
        }

        # Assign playing order
        game_data["play_order"] = list(
            random.sample(list(game_data["players"].keys()), k=len(users))
        )
        game_data["actions"] = [
            GovernorAction(player_name=name) for name in game_data["play_order"]
        ]

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

        game_data["people_ship"] = Holder(people=len(users))
        game_data["market"] = Holder()
        game_data["goods_ships"] = {
            n: Holder() for n in range(len(users) + 1, len(users) + 4)
        }

        # Generate role cards
        game_data["roles"] = [Role(type=r) for r in REGULAR_ROLES] + [
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
        for player in self.players.values():
            self.money -= len(users) - 1
            player.money += len(users) - 1

        # Distribute tiles
        num_indigo = 2 if len(users) < 5 else 3
        for i, player_name in enumerate(self.play_order):
            player = self.players[player_name]
            self.give_tile(to=player, type="indigo" if i < num_indigo else "corn")
        self.expose_tiles()

        # Take first action (governor assignment)
        self.take_action()
        return self
    
    def empty_ships_and_market(self):
        for size, ship in self.goods_ships.items():
            what, amount = next(ship.what_and_amount(), (None, 0))
            if amount >= size:
                ship.give(amount, what, to=self)
        market_total = sum( amount for type, amount in self.market.what_and_amount() )
        if market_total >= 4:
            for type, amount in self.market.what_and_amount():
                self.market.give(amount, type, to=self)

    def expose_tiles(self):
        all_tiles = self.unsettled_tiles + self.exposed_tiles
        self.exposed_tiles, self.unsettled_tiles = (
            all_tiles[: len(self.players) + 1],
            all_tiles[len(self.players) + 1 :],
        )

    def give_tile(self, to: Player, type: TileType):
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

    def is_expecting(self, action: Action) -> bool:
        return (
            self.expected_action.type == action.type
            and self.expected_action.player_name == action.player_name
        )

    def name_round_from(self, player_name: str) -> Iterator[str]:
        cycle = itertools.cycle(self.play_order)
        curr_player_name = next(cycle)
        while curr_player_name != player_name:
            curr_player_name = next(cycle)
        for _ in range(len(self.players)):
            yield curr_player_name
            curr_player_name = next(cycle)

    def player_round_from(self, player_name: str) -> Iterator[Player]:
        cycle = itertools.cycle(self.play_order)
        curr_player_name = next(cycle)
        while curr_player_name != player_name:
            curr_player_name = next(cycle)
        for _ in range(len(self.players)):
            yield self.players[curr_player_name]
            curr_player_name = next(cycle)

    def pop_role(self, role: RoleType) -> Role:
        i = next(i for i, card in enumerate(self.roles) if card.type == role)
        return self.roles.pop(i)

    def take_action(self, action: Action = None):
        # Next governor is assigned automatically
        if action is None:
            if self.expected_action.type == "governor":
                self.expected_action.react(self)
                self.take_action()
            elif self.expected_player.intelligence == "rufus":
                action = Rufus(self.expected_player.name).decide(self)
                self.take_action(action)

        else:
            action.react(self)
            # print("TOOK", action)
            self._broadcast(action.model_dump(), "action")
            self.take_action()

    def terminate(self, reason: str = None):
        if reason:
            raise GameOver(reason)
        else:
            raise GameOver("Game over for no reason.")
