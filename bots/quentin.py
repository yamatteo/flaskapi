from random import sample
from reactions import Action
from reactions.mayor import MayorAction
from reactions.terminate import TerminateAction
from rico import Board
from rico.constants import GOODS, STANDARD_BUILDINGS
from rico.towns import Town


class Quentin:
    def __init__(self, name: str, depth: int = 1):
        self.name = name
        self.depth = depth

    def alt_decide(self, board: Board, actions: list[Action], verbose=False) -> Action:
        choices = actions[0].possibilities(board)
        if len(choices) == 1:
            return choices[0]

        selected_action, _ = alt_minimax(
            name=self.name, board=board, actions=actions, depth=self.depth, verbose=True
        )
        return selected_action

    def decide(self, board: Board, actions: list[Action], verbose=False) -> Action:
        expected_action = actions[0]

        choices = expected_action.possibilities(board)
        if len(choices) == 1:
            return choices[0]

        selected = None
        best_value = -1000
        for action in choices:
            future_board, future_actions = project(board, action, actions)
            future_value = minimax(
                self.name,
                future_board,
                future_actions,
                self.depth - 1,
                early_stop=isinstance(expected_action, MayorAction),
            )
            if verbose:
                print(f"  {future_value:4.1f} << {action}")
            if future_value > best_value:
                selected = action
                best_value = future_value
        return selected


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
    name: str, board: Board, actions: list[Action], depth: int, early_stop=False
) -> float:
    expected_action = actions[0]
    if depth <= 0 or isinstance(expected_action, TerminateAction) or early_stop:
        return evaluate_board(name, board)
    maximize = bool(expected_action.name == name)
    choices = expected_action.possibilities(board)
    if len(choices) == 1:
        future_board, future_actions = project(board, choices[0], actions)
        return minimax(name, future_board, future_actions, depth)
    values = list()
    for action in choices:
        future_board, future_actions = project(board, action, actions)
        future_value = minimax(
            name,
            future_board,
            future_actions,
            depth - 1,
            early_stop=isinstance(action, MayorAction),
        )
        values.append(future_value)
    if maximize:
        return max(values)
    else:
        return min(values)


def alt_minimax(
    name: str, board: Board, actions: list[Action], depth: int, verbose=False
) -> tuple[Action, float]:
    expected_action = actions[0]
    choices = expected_action.possibilities(board)
    if depth <= 0 or isinstance(expected_action, TerminateAction):
        return choices[0], evaluate_board(name, board)
    maximize = bool(expected_action.name == name)
    if len(choices) == 1:
        future_board, future_actions = project(board, choices[0], actions)
        _, future_value = alt_minimax(name, future_board, future_actions, depth)
        return choices[0], future_value
    elif len(choices) > 20:
        choices = sample(choices, 20)
    if isinstance(expected_action, MayorAction):
        depth = 0
    best_action, best_value = None, (-1000 if maximize else 1000)

    for future_action in choices:
        future_board, future_actions = project(board, future_action, actions)
        _, future_value = alt_minimax(
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
