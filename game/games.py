from copy import copy
import itertools
from typing import Iterator


from .actions import *
from .counters import *
from .cards import *
from .players import *
from .pseudos import generate_pseudos


class Game(Holder, BaseModel):
    players: dict[str, Player]
    actions: list[Union[Action, ExpectedAction]]
    play_order: list[str]
    people_ship: Holder
    goods_ships: dict[int, Holder]
    market: Holder
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
        
        # Generate countables
        game_data["n"] = f"m54p122w{20 * len(users) - 5}c9k10i11s11t9"
        # game_data["money"] = 54
        # game_data["points"] = 122
        # game_data["people"] = 20 * len(users) - 5
        # game_data["coffee"] = 9
        # game_data["corn"] = 10
        # game_data["indigo"] = 11
        # game_data["sugar"] = 11
        # game_data["tobacco"] = 9

        game_data["people_ship"] = Holder.new(people=len(users))
        game_data["market"] = Holder()
        game_data["goods_ships"] = {n: Holder() for n in range(len(users)+1, len(users)+4)}

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
            self.give(len(users)-1, "money", to=player)

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

        if last_governor.gov:
            # Increase money bonus
            if self.has(len(self.role_cards), "money"):
                for card in self.role_cards:
                    self.give(1, "money", to=card)
            else:
                self.terminate()
        new_governor.gov, last_governor.gov = True, False

        # Eventually refill people_ship
        if self.people_ship.count("people") == 0:
            total = sum(player.vacant_jobs for player in self.players.values())
            total = max(total, len(self.players))
            if self.count("people") >= total:
                self.give(total, "people", to=self.people_ship)
            else:
                self.terminate()

        # Stop for building space
        for player in self.players.values():
            if player.vacant_places == 0:
                self.terminate()

        # Stop for victory points
        if self.count("points") <= 0:
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
        player.role_card.give("all", "money", to=player)

        self.actions.pop(0)

        if role_name == "settler":
            self.actions = [
                ExpectedTileAction(player_name=name)
                for name in self.name_round_from(player.name)
            ] + self.actions
        if role_name == "mayor":
            self.give(1, "people", to=player)
            while self.people_ship.count("people"):
                for _player in self.player_round_from(player.name):
                    try:
                        self.people_ship.give(1, "people", to=_player)
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
                    possible_amount = min(amount, self.count(good))
                    self.give(possible_amount, good, to=_player)
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
            if self.has("money"):
                self.give(1, "money", to=player)


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
            if refused.subclass == "Captain" and sum(player.count(_good) for _good in GOODS) > 0:
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
            enforce(player.has(price, "money"), f"Player does not have enough money.")
            enforce( [building.subclass for building in self.buildings if building.subclass == action.building_subclass], f"There are no more {action.building_subclass} to sell.")
            enforce( player.vacant_places >= (2 if tier==4 else 1), f"Player {player.name} does not have space for {action.building_subclass}")
            i, building = next(
                (i, building)
                for i, building in enumerate(self.buildings)
                if building.subclass == action.building_subclass
            )
            if player.priviledge("hospice") and self.has("people"):
                self.give(1, "people", to=building)
            self.actions.pop(0)
            self.buildings.pop(i)
            player.buildings.append(building)
            player.give(price, "money", to=self)

            
        elif isinstance(action, CraftsmanAction):
            good = action.selected_good
            enforce(player.production(good) > 0, f"Craftsman get one extra good of something he produces, not {good}.")
            enforce(self.has(good), f"There is no {good} left in the game.")
            self.give(1, good, to=player)
            self.actions.pop(0)
        elif isinstance(action, TraderAction):
            good = action.selected_good
            enforce(sum( self.market.count(_good) for _good in GOODS) < 4, "There is no more space in the market.")
            enforce( self.market.count(good)==0 or player.priviledge("office"), f"There already is {good} in the market.")
            price = dict(corn=0, indigo=1, sugar=2, tobacco=3, coffee=4)[good]
            price += (1 if player.role == "trader" else 0)
            price += (1 if player.priviledge("small_market") else 0)
            price += (2 if player.priviledge("large_market") else 0)
            affordable_price = min(price, self.count("money"))
            player.give(1, good, to=self.market)
            self.give(affordable_price, "money", to=player)
            self.actions.pop(0)
        elif isinstance(action, CaptainAction):
            ship, good = action.selected_ship, action.selected_good

            if ship == 11:
                enforce( player.priviledge("wharf") and not player._spent_wharf, "Player does not have a free wharf.")
                player._spent_wharf = True
                amount = player.count(good)
                player.give(amount, good, to=self)
                points = amount
                if player.priviledge("harbor"):
                    points += 1
                if player.role == "captain" and not player._spent_captain:
                    points += 1
                    player._spent_captain = True
                self.give(points, "points", to=player)

            else:
                ship_contains = 0
                ship_contains_class = None
                for _good in ["coffee", "tobacco", "corn", "sugar", "indigo"]:
                    if self.goods_ships[ship].has(_good):
                        ship_contains = self.goods_ships[ship].count(_good)
                        ship_contains_class = _good
                if ship_contains > 0:
                    enforce( ship_contains < ship, "The ship is full.")
                    enforce( ship_contains_class == good, f"The ship contains {ship_contains_class}")
                amount = min(ship-ship_contains, player.count(good))
                player.give(amount, good, to=self.goods_ships[ship])
                points = amount
                if player.priviledge("harbor"):
                    points += 1
                if player.role == "captain" and not player._spent_captain:
                    points += 1
                    player._spent_captain = True
                self.give(points, "points", to=player)

            if sum(player.count(_good) for _good in GOODS) > 0:
                self.actions = [ action for action in self.actions[1:] if action.subclass == "Captain"] + [self.actions[0]] + [ action for action in self.actions[1:] if action.subclass != "Captain"]
        elif isinstance(action, PreserveGoodsAction):
            for _good in GOODS:
                if _good in [ action.small_warehouse_good, action.large_warehouse_first_good, action.large_warehouse_second_good]:
                    continue
                elif _good == action.selected_good:
                    player.give(max(0, player.count(_good)-1), _good, to=self)
                else: 
                    player.give("all", _good, to=self)
            self.actions.pop(0)
        else:
            raise NotImplementedError
        self.take_action()

    def take_role(self, to: Player):
        if to.role_card:
            self.role_cards.append(to.role_card)
            to.role_card = None
