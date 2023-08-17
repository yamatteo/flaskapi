from copy import copy
import itertools
from types import SimpleNamespace
from typing import Iterator

from pydantic import ConfigDict

from .actions import *
from .counters import *
from .cards import *
from .players import *
from .pseudos import generate_pseudos


class Game(MoneyHolder, PeopleHolder, PointHolder, GoodsHolder, BaseModel):
    players: dict[str, Player]
    actions: list[Union[Action, ExpectedAction]]
    play_order: list[str]
    # ref_governor_cycle: list[str]
    # ref_role_cycle: list[str]
    # ref_tile_cycle: list[str]
    # ref_people_cycle: list[str]
    people_ship: PeopleHolder
    goods_ships: dict[int, GoodsHolder]
    market: GoodsHolder
    role_cards: list[RoleCard]
    quarries: list[Tile]
    tiles: list[Tile]
    exposed_tiles: list[Tile]
    buildings: list[Building]
    marked_for_completion: bool = False

    @property
    def expected_player(self) -> Player:
        name = self.actions[0].player_name
        return self.players[name]

    @property
    def expected_action(self) -> Union[GovernorAction, ExpectedAction]:
        return self.actions[0]

    @classmethod
    def start_new(cls, users: list[str]):
        enforce(3 <= len(users) <= 5, "Players must be between 3 and 5.")
        game_data = {}
        pseudos = generate_pseudos(users)
        game_data["players"] = {
            name: Player(name=name, pseudo=pseudos[name]) for name in users
        }

        # Assign playing order
        game_data["play_order"] = list(
            random.sample(list(game_data["players"].keys()), k=len(users))
        )
        game_data["actions"] = [
            GovernorAction(player_name=name) for name in game_data["play_order"]
        ]
        # game_data["ref_governor_cycle"] = list(
        #     random.sample(list(game_data["players"].keys()), k=len(users))
        # )
        # game_data["ref_role_cycle"] = copy(game_data["ref_governor_cycle"])
        # game_data["ref_tile_cycle"] = []
        # game_data["ref_people_cycle"] = []

        # Generate money
        game_data["money"] = 54

        # Generate points
        game_data["points"] = 122

        # Generate people
        game_data["people"] = 20 * len(users) - 5
        game_data["people_ship"] = PeopleHolder(people=len(users))

        # Generate goods
        game_data["coffee"] = 9
        game_data["corn"] = 10
        game_data["indigo"] = 11
        game_data["sugar"] = 11
        game_data["tobacco"] = 9
        game_data["market"] = GoodsHolder()
        game_data["goods_ships"] = {n: GoodsHolder() for n in range(len(users)+1, len(users)+4)}

        # Generate role cards
        game_data["role_cards"] = [
            RoleCard(subclass=name)
            for name in [
                "settler",
                "mayor",
                "builder",
                "craftsman",
                "trader",
                "captain",
            ]
        ] + [RoleCard(subclass="prospector") for _ in range(len(users) - 3)]

        # Generate tiles
        game_data["quarries"] = [Tile(subclass="quarry") for _ in range(8)]
        game_data["exposed_tiles"] = (
            [Tile(subclass="coffee") for _ in range(8)]
            + [Tile(subclass="tobacco") for _ in range(9)]
            + [Tile(subclass="corn") for _ in range(10)]
            + [Tile(subclass="sugar") for _ in range(11)]
            + [Tile(subclass="indigo") for _ in range(12)]
        )
        game_data["tiles"] = []
        random.shuffle(game_data["exposed_tiles"])

        # Generate buildings
        game_data["buildings"] = []
        for subclass, (tier, cost, max_people, number) in building_info.items():
            for _ in range(number):
                game_data["buildings"].append(
                    Building(subclass=subclass, tier=tier, cost=cost, max_people=max_people)
                )

        self = cls(**game_data)

        # Distribute money
        for player in self.players.values():
            self.give_money(player, len(users) - 1)

        # Distribute tiles
        num_indigo = 2 if len(users) < 5 else 3
        for i, player_name in enumerate(self.play_order):
            player = self.players[player_name]
            self.give_tile(to=player, subclass="indigo" if i < num_indigo else "corn")
        self.expose_tiles()

        # Take first action
        self.take_action()
        return self
    
    def assign_governor(self):
        enforce(
            isinstance(self.expected_action, GovernorAction),
            "Not time to asign new governor.",
        )

        new_governor = self.players[self.actions[0].player_name]
        last_governor = self.players[self.actions[-1].player_name]

        if last_governor.is_governor:
            new_governor.governor_card, last_governor.governor_card = last_governor.governor_card, None

            # Increase money bonus
            if self.money >= len(self.role_cards):
                for card in self.role_cards:
                    self.give_money(card, 1)
            else:
                self.terminate()
        else:
            new_governor.governor_card, last_governor.governor_card = GovernorCard(), None

        # Eventually refill people_ship
        if self.people_ship.people == 0:
            total = sum(player.vacant_jobs for player in self.players.values())
            total = max(total, len(self.players))
            if self.people >= total:
                self.give_people(self.people_ship, total)
            else:
                self.terminate()

        # Stop for building space
        for player in self.players.values():
            if player.vacant_places == 0:
                self.terminate()

        # Stop for victory points
        if self.points <= 0:
            self.terminate()

        # Take back all role cards and reset flags
        for player in self.players.values():
            self.take_role(player)
            player._spent_wharf = False
            player._spent_captain = False

        self.actions.append(self.actions.pop(0))
        self.actions = [
            ExpectedRoleAction(player_name=name)
            for name in self.name_round_from(new_governor.name)
        ] + self.actions

    def assign_role(self, player_name: str, role_name: str):
        player: Player = self.expected_player
        enforce(
            player.name == player_name,
            f"It's not {player_name} time to select a role.",
        )
        enforce(
            player.role is None,
            f"Player {player_name} already has role.",
        )
        enforce(
            self.actions[0].subclass == "Role", "Not expecting to give out roles."
        )

        self.give_role(to=player, subclass=role_name)
        player.role_card.give_money(to=player)

        self.actions.pop(0)

        if role_name == "settler":
            self.actions = [
                ExpectedTileAction(player_name=name)
                for name in self.name_round_from(player.name)
            ] + self.actions
        if role_name == "mayor":
            self.give_people(player, 1)
            while self.people_ship.people:
                for _player in self.player_round_from(player.name):
                    try:
                        self.people_ship.give_people(_player, 1)
                    except RuleError:
                        break
            self.actions = [
                ExpectedPeopleAction(player_name=name)
                for name in self.name_round_from(player.name)
            ] + self.actions
        if role_name == "builder":
            self.actions = [
                ExpectedBuildingAction(player_name=name)
                for name in self.name_round_from(player.name)
            ] + self.actions
        if role_name == "craftsman":
            for _player in self.player_round_from(player.name):
                for good, amount in _player.production().items():
                    possible_amount = min(amount, getattr(self, good))
                    self.give(to=_player, subclass=good, amount=possible_amount)
                    if possible_amount:
                        print("CRAFTSMAN", _player.name, good, amount, getattr(self, good))
                        print(_player)
            self.actions = [
                ExpectedCraftsmanAction(player_name=player.name)
            ] + self.actions
        if role_name == "trader":
            self.actions = [
                ExpectedTraderAction(player_name=name)
                for name in self.name_round_from(player.name)
            ] + self.actions
        if role_name == "captain":
            self.actions = [
                ExpectedCaptainAction(player_name=name)
                for name in self.name_round_from(player.name)
            ] + self.actions
        if role_name == "prospector":
            if self.money:
                self.give_money(player, 1)


        self.take_action()

    def assign_tile(self, player_name: str, tile_type: str, down_tile: bool = False):
        enforce(self.expected_action.subclass == "Tile", "Not tiles' time.")
        player: Player = self.expected_player
        enforce(
            player.name == player_name,
            f"It's not {player_name} time to select a tile.",
        )
        enforce(not down_tile or player.priviledge("hacienda"), "Can't take down tile without occupied hacienda.")
        enforce(
            tile_type != "quarry" or player.role == "settler" or player.priviledge("construction_hut"),
            "Only the settler can pick a quarry",
        )

        self.give_tile(to=player, subclass=tile_type)
        self.actions.pop(0)


    def assign_people(self, new_player: Player):
        # breakpoint()
        player = self.expected_player
        enforce(self.expected_action.subclass == "People", "Not the time to redistribute people.")
        enforce(player.name == new_player.name, "Not your turn to redistribute people.")
        enforce(
            new_player.total_people == player.total_people, "Wrong total of people."
        )
        enforce(
            new_player.is_equivalent_to(player),
            "There are differences other than people distribution.",
        )
        self.players[player.name] = new_player
        self.actions.pop(0)
        self.take_action()

    def expose_tiles(self):
        all_tiles = self.tiles + self.exposed_tiles
        self.exposed_tiles, self.tiles = (
            all_tiles[: len(self.players) + 1],
            all_tiles[len(self.players) + 1 :],
        )

    def give_role(self, to: Player, subclass: str):
        i, card = next(
            (i, card) for i, card in enumerate(self.role_cards) if card.subclass == subclass
        )
        self.role_cards.pop(i)
        to.role_card = card

    def give_tile(self, to: Player, subclass: str):
        if subclass=="quarry" :
            enforce(self.quarries, "No more quarry to give.")
            tile = self.quarries.pop(0)
            to.tiles.append(tile)
            return
        i, tile = next(
            (i, tile)
            for i, tile in enumerate(self.exposed_tiles)
            if tile.subclass == subclass
        )
        self.exposed_tiles.pop(i)
        to.tiles.append(tile)

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

    def take_action(self, action: Action = None):
        # Next governor is assigned automatically
        if action is None:
            try:
                self.assign_governor()
            except:
                pass
            return
        action = specify(action)
        expected = self.expected_action
        player = self.expected_player

        # Some expected action can be refused (like, not taking a tile or not selling to market)
        if isinstance(action, RefuseAction):
            enforce(
                expected.subclass
                in [
                    "Tile",
                    "People",
                    "Building",
                    "Craftsman",
                    "Trader",
                    "Captain",
                    "PreserveGoods",
                ],
                f"Can't refuse {expected}.",
            )

            refused = self.actions.pop(0)
            if refused.subclass == "Captain" and sum(getattr(player, _good) for _good in ["coffee", "tobacco", "corn", "sugar", "indigo"]) > 0:
                self.actions = [ action for action in self.actions if action.subclass == "Captain"] + [ExpectedPreserveGoodsAction(player_name=player.name)] + [ action for action in self.actions if action.subclass != "Captain"]

            self.take_action()
            return
        
        # At this point, only expected action can be taken
        enforce(action.subclass == expected.subclass and action.player_name == expected.player_name, f"Unexpected action {action} instead of {expected}")
        if isinstance(action, RoleAction):
            self.assign_role(action.player_name, role_name=action.role_subclass)
        elif isinstance(action, TileAction):
            self.assign_tile(player_name=action.player_name, tile_type=action.tile_subclass, down_tile=action.down_tile)
            if self.expected_action.subclass != "Tile":
                self.expose_tiles()
        elif isinstance(action, PeopleAction):
            self.assign_people(action.whole_player)
        elif isinstance(action, BuildingAction):
            tier, cost, _, _ = building_info[action.building_subclass]
            quarries_discount = min(tier, player.active_quarries())
            builder_discount = 1 if player.role == "builder" else 0
            price = max(0, cost - quarries_discount - builder_discount)
            enforce(player.money >= price, f"Player does not have enough money.")
            enforce( [building.subclass for building in self.buildings if building.subclass == action.building_subclass], f"There are no more {action.building_subclass} to sell.")
            enforce( player.vacant_places >= (2 if tier==4 else 1), f"Player {player.name} does not have space for {action.building_subclass}")
            i, building = next(
                (i, building)
                for i, building in enumerate(self.buildings)
                if building.subclass == action.building_subclass
            )
            if player.priviledge("hospice") and self.people:
                self.give_people(to=building, amount=1)
            self.actions.pop(0)
            self.buildings.pop(i)
            player.buildings.append(building)
            player.give_money(self, price)

            
        elif isinstance(action, CraftsmanAction):
            good = action.selected_good
            enforce(player.production(good) > 0, f"Craftsman get one extra good of something he produces, not {good}.")
            enforce(getattr(self, good) > 0, f"There is no {good} left in the game.")
            self.give(player, good, 1)
            self.actions.pop(0)
        elif isinstance(action, TraderAction):
            good = action.selected_good
            enforce(sum( getattr(self.market, _good) for _good in ["coffee", "tobacco", "corn", "sugar", "indigo"]) < 4, "There is no more space in the market.")
            enforce( getattr(self.market, good)==0 or player.priviledge("office"), f"There already is {good} in the market.")
            price = dict(corn=0, indigo=1, sugar=2, tobacco=3, coffee=4)[good]
            price += (1 if player.role == "trader" else 0)
            price += (1 if player.priviledge("small_market") else 0)
            price += (2 if player.priviledge("large_market") else 0)
            affordable_price = min(price, self.money)
            player.give(self.market, good, 1)
            self.give_money(player, affordable_price)
            self.actions.pop(0)
        elif isinstance(action, CaptainAction):
            ship, good = action.selected_ship, action.selected_good

            if ship == 11:
                enforce( player.priviledge("wharf") and not player._spent_wharf, "Player does not have a free wharf.")
                player._spent_wharf = True
                amount = getattr(player, good)
                player.give(self, good, amount)
                points = amount
                if player.priviledge("harbor"):
                    points += 1
                if player.role == "captain" and not player._spent_captain:
                    points += 1
                    player._spent_captain = True
                self.give(player, "points", points)

            else:
                ship_contains = 0
                ship_contains_class = None
                for _good in ["coffee", "tobacco", "corn", "sugar", "indigo"]:
                    if getattr(self.goods_ships[ship], _good) > 0:
                        ship_contains = getattr(self.goods_ships[ship], _good)
                        ship_contains_class = _good
                if ship_contains > 0:
                    enforce( ship_contains < ship, "The ship is full.")
                    enforce( ship_contains_class == good, f"The ship contains {ship_contains_class}")
                amount = min(ship-ship_contains, getattr(player, good))
                player.give(self.goods_ships[ship], good, amount)
                points = amount
                if player.priviledge("harbor"):
                    points += 1
                if player.role == "captain" and not player._spent_captain:
                    points += 1
                    player._spent_captain = True
                self.give(player, "points", points)

            if sum(getattr(player, _good) for _good in ["coffee", "tobacco", "corn", "sugar", "indigo"]) > 0:
                self.actions = [ action for action in self.actions[1:] if action.subclass == "Captain"] + [self.actions[0]] + [ action for action in self.actions[1:] if action.subclass != "Captain"]
        elif isinstance(action, PreserveGoodsAction):
            for _good in ["coffee", "tobacco", "corn", "sugar", "indigo"]:
                if _good in [ action.small_warehouse_good, action.large_warehouse_first_good, action.large_warehouse_second_good]:
                    continue
                elif _good == action.selected_good:
                    player.give(self, _good, max(0, getattr(player, _good)-1))
                else: 
                    player.give(self, _good)
            self.actions.pop(0)
        else:
            raise NotImplementedError
        self.take_action()

    def take_role(self, to: Player):
        if to.role_card:
            self.role_cards.append(to.role_card)
            to.role_card = None
