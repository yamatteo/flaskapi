from random import sample
from reactions import Action
from reactions.mayor import MayorAction
from reactions.terminate import TerminateAction
from rico import Board
from rico.constants import (
    BUILDINGS,
    COUNTABLES,
    GOODS,
    REGULAR_TILES,
    ROLES,
    STANDARD_BUILDINGS,
    TILES,
)
from rico.ships import GoodsShip
from rico.towns import Town


class Pablo:
    def __init__(self, name: str, depth: int = 1):
        self.name = name
        self.depth = depth

    def decide(self, board: Board, actions: list[Action], verbose=False) -> Action:
        if isinstance(actions[0], MayorAction):
            choices = actions[0].possibilities(board, cap=20)
        else:
            choices = actions[0].possibilities(board)
        if len(choices) == 1:
            return choices[0]

        selected_action, _ = minimax(
            name=self.name, board=board, actions=actions, depth=self.depth, choices=choices, verbose=verbose
        )
        return selected_action


def evaluate_town(town: Town) -> float:
    value = town.count("points")

    # Buildings
    value += sum(building.tier for building in town.buildings)

    # Large buildings
    if town.priviledge("guild_hall"):
        for building in town.buildings:
            if building.type in ["small_indigo_plant", "small_sugar_mill"]:
                value += 1
            if building.type in [
                "coffee_roaster",
                "indigo_plant",
                "sugar_mill",
                "tobacco_storage",
            ]:
                value += 2
    if town.priviledge("residence"):
        occupied_tiles = len([tile for tile in town.tiles if tile.count("people") >= 1])
        value += max(4, occupied_tiles - 5)
    if town.priviledge("fortress"):
        value += town.total_people // 3
    if town.priviledge("custom_house"):
        value += town.count("points") // 4
    if town.priviledge("city_hall"):
        value += len(
            [
                building
                for building in town.buildings
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

    # There is value in money
    value += town.count("money") / 5

    # There is value in clerks
    value += (
        sum(int(town.priviledge(building_type)) for building_type in STANDARD_BUILDINGS)
        / 5
    )

    # There is value in stored goods
    value += sum(town.count(g) for g in GOODS) / 10

    # There is value in the land
    value += len(town.tiles) / 10

    # There is value in numbers
    value += town.total_people / 20

    # There is value in production
    value += sum(town.production().values()) / 20
    return value


def evaluate_board(name: str, board: Board) -> float:
    return evaluate_town(board.towns[name]) - max(
        evaluate_town(town) for _name, town in board.towns.items() if _name != name
    )


def merge(actions: list[Action], extra: list[Action]) -> list[Action]:
    merged = []
    i, j = 0, 0
    while i < len(actions):
        if j < len(extra) and extra[j].priority > actions[i].priority:
            merged.append(extra[j])
            j += 1
        else:
            merged.append(actions[i])
            i += 1
    while j < len(extra):
        merged.append(extra[j])
        j += 1
    return merged


def minimax(
    name: str, board: Board, actions: list[Action], depth: int, choices=None, verbose=False
) -> tuple[Action, float]:
    expected_action = actions[0]
    if choices is None:
        if isinstance(actions[0], MayorAction):
            choices = actions[0].possibilities(board, cap=20)
        else:
            choices = actions[0].possibilities(board)
    if depth <= 0 or isinstance(expected_action, TerminateAction):
        return choices[0], evaluate_board(name, board)
    maximize = bool(expected_action.name == name)
    if len(choices) == 1:
        future_board, future_actions = project(board, choices[0], actions)
        _, future_value = minimax(name, future_board, future_actions, depth)
        return choices[0], future_value
    elif len(choices) > 20:
        choices = sample(choices, 20)
    if isinstance(expected_action, MayorAction):
        depth = 0
    best_action, best_value = None, (-1000 if maximize else 1000)

    for future_action in choices:
        future_board, future_actions = project(board, future_action, actions)
        _, future_value = minimax(
            name,
            future_board,
            future_actions,
            depth - 1,
        )
        if verbose:
            print(f"{future_value:>5.1f} >> {future_action}")
        if (maximize and future_value > best_value) or (
            not maximize and future_value < best_value
        ):
            best_action, best_value = future_action, future_value

    return best_action, best_value


def project(
    board: Board, action: Action, actions: list[Action]
) -> tuple[Board, list[Action]]:
    board = board.copy()
    board, extra = action.react(board)
    actions = merge(actions[1:], extra)
    return board, actions


def embed(board: Board, name: str):
    countables = [board.count(kind) for kind in COUNTABLES]
    tiles = [len(board.unsettled_tiles), board.unsettled_quarries] + [
        board.exposed_tiles.count(tile_type) for tile_type in REGULAR_TILES
    ]
    ships = [board.people_ship.people]
    for ship in board.goods_fleet.values():
        ships.extend(embed_ship(ship))
    market = [board.market.count(kind) for kind in GOODS]
    buildings = [board.unbuilt.count(kind) for kind in BUILDINGS]
    towns = []
    for town in board.town_round_from(name):
        towns.extend(embed_town(town))

    return countables + tiles + ships + market + buildings + towns


def embed_town(town: Town):
    data = [int(town.gov), int(town.spent_captain), int(town.spent_wharf)] + [
        town.count(kind) for kind in COUNTABLES
    ]
    for role in ROLES:
        data.append(int(town.role == role))
    for tile_type in TILES:
        those_tiles = [tile for tile in town.tiles if tile.type == tile_type]
        data.append(len(those_tiles))
        data.append(sum(tile.people for tile in those_tiles))
    workers = {building.type: building.people for building in town.buildings}
    for building_type in BUILDINGS:
        data.append(workers.get(building_type, -1))
    return data


def embed_ship(ship: GoodsShip):
    return [ship.size] + [ship.count(kind) for kind in GOODS]
