from random import sample
from typing import Optional, Sequence
from attr import define

import numpy as np
from bots.distribution import WORKLABELS, WorkPriority
from reactions import Action
from reactions.mayor import MayorAction
from reactions.terminate import TerminateAction
from rico import Board
from rico.constants import (
    BUILDINFO,
    BUILDINGS,
    COUNTABLES,
    GOODS,
    NONPRODUCTION_BUILDINGS,
    REGULAR_TILES,
    ROLES,
    STANDARD_BUILDINGS,
    TILES,
)
from rico.ships import GoodsShip
from rico.towns import Town


@define
class Evaluation:
    action: Optional[Action]
    board: Board
    # actions: list[Action]
    prime_value: float
    author_value: float

    @classmethod
    def many_from(cls, board, actions, wrt, depth, breadth=3) -> list["Evaluation"]:
        expected_action = actions[0]

        if depth <= 0 or isinstance(expected_action, TerminateAction):
            return [
                Evaluation(
                    None,
                    board,
                    # actions,
                    evaluate_board(board, wrt=wrt),
                    evaluate_board(board, wrt=expected_action.name),
                )
            ]

        if isinstance(expected_action, MayorAction):
            choices = [decide_mayor(board, actions)]
        else:
            choices = expected_action.possibilities(board)

        # depth = depth-1  # if len(choices) > 1 else depth

        evaluations = []
        for choice in choices:
            next_board, next_actions = project(board, choice, actions)
            evaluations.append(
                Evaluation(
                    choice,
                    next_board,
                    # next_actions,
                    cls.single_eval(
                        next_board, next_actions, depth=depth - 1, wrt=wrt
                    ),
                    cls.single_eval(
                        next_board,
                        next_actions,
                        depth=depth - 1,
                        wrt=expected_action.name,
                    ),
                )
            )
        return evaluations

    @classmethod
    def single_eval(cls, board, actions, depth=None, breadth=3, wrt=None) -> float:
        """An in-depth evaluation of the given game state.

        To evaluate rivals' choices, we assume that they are driven by their best interest rather than our demise. So
        they will probably take an action that maximize their value. But we minimax with the worst (for self) of k
        best (for them) options.
        """
        expected_action = actions[0]

        # Evaluate all possible future scenarios (according to who's going to take the next action)
        evaluations = cls.many_from(board, actions, depth=depth, wrt=wrt)

        if expected_action.name == wrt:
            # Wrt is taking the next action, so he takes the best value available
            return max(ev.prime_value for ev in evaluations)
        else:
            # Someone else is making the next choice, so values are according to them
            # Take k=self.breadth of most valuable scenarios, according to the rival
            evaluations = sorted(evaluations, key=lambda ev: ev.author_value)
            evaluations = evaluations[-breadth :]

            # To wrt, the value is the lowest of those possible
            return min(ev.prime_value for ev in evaluations)



class Oliver:
    def __init__(self, name: str, depth: int = 3, breadth: int = 3):
        self.name = name
        self.depth = depth
        self.breadth = breadth

    def many_eval(self, board, actions, depth=None, wrt=None) -> list[Evaluation]:
        expected_action = actions[0]
        if depth is None:
            depth = self.depth
        if wrt is None:
            wrt = self.name

        if depth <= 0 or isinstance(expected_action, TerminateAction):
            return [
                Evaluation(
                    None,
                    board,
                    actions,
                    evaluate_board(board, wrt=wrt),
                    evaluate_board(board, wrt=expected_action.name),
                )
            ]

        if isinstance(expected_action, MayorAction):
            choices = [decide_mayor(board, actions)]
        else:
            choices = expected_action.possibilities(board)

        # depth = depth-1  # if len(choices) > 1 else depth

        evaluations = []
        for choice in choices:
            next_board, next_actions = project(board, choice, actions)
            evaluations.append(
                Evaluation(
                    choice,
                    next_board,
                    next_actions,
                    self.single_eval(
                        next_board, next_actions, depth=depth - 1, wrt=wrt
                    ),
                    self.single_eval(
                        next_board,
                        next_actions,
                        depth=depth - 1,
                        wrt=expected_action.name,
                    ),
                )
            )
        return evaluations

    def single_eval(self, board, actions, depth=None, wrt=None) -> float:
        """An in-depth evaluation of the given game state.

        To evaluate rivals' choices, we assume that they are driven by their best interest rather than our demise. So
        they will probably take an action that maximize their value. But we minimax with the worst (for self) of k
        best (for them) options.
        """
        expected_action = actions[0]

        # Evaluate all possible future scenarios (according to who's going to take the next action)
        evaluations = self.many_eval(board, actions, depth=depth, wrt=wrt)

        if expected_action.name == wrt:
            # Wrt is taking the next action, so he takes the best value available
            return max(ev.prime_value for ev in evaluations)
        else:
            # Someone else is making the next choice, so values are according to them
            # Take k=self.breadth of most valuable scenarios, according to the rival
            evaluations = sorted(evaluations, key=lambda ev: ev.author_value)
            evaluations = evaluations[-self.breadth :]

            # To wrt, the value is the lowest of those possible
            return min(ev.prime_value for ev in evaluations)

    def decide(self, board: Board, actions: list[Action]) -> Action:
        # evaluations = self.many_eval(board, actions, depth=self.depth)
        # best, _ = max(evaluations, key=lambda action_value: action_value[1])
        # if best is None:
        #     best = (actions[0].possibilities(board))[0]
        return best

    def train_decide(self, board: Board, actions: list[Action]):
        # evaluations = self.many_eval(board, actions, depth=self.depth)
        evaluations = Evaluation.many_from(board, actions, depth=self.depth, wrt=self.name)

        data = []
        for ev in evaluations:
            data.append((embed(ev.board, wrt=self.name), ev.prime_value))
        best = max(evaluations, key=lambda ev: ev.prime_value).action
        if best is None:
            best = (actions[0].possibilities(board))[0]
        return data, best


def decide_mayor(board: Board, actions: list[Action]) -> Action:
    expected = actions[0]
    assert isinstance(expected, MayorAction)
    town = board.towns[expected.name]
    available_workers = town.total_people
    holders = [
        "home",
        *[tile.type for tile in town.tiles],
        *[building.type for building in town.buildings],
    ]
    distribution = WorkPriority(range(len(WORKLABELS))).distribute(
        available_workers, holders
    )
    return MayorAction(name=expected.name, people_distribution=distribution)


def unpack_worker_priority(worker_priority: Sequence[float]) -> list[tuple[float, str]]:
    keys = (
        [f"prod.{good}.{amount}" for good in GOODS for amount in range(1, 5)]
        + [f"quarry.{amount}" for amount in range(1, 5)]
        + [f"build.{build_type}" for build_type in NONPRODUCTION_BUILDINGS]
        + ["vacant"]
    )
    priorities = sorted([(worker_priority[i], keys[i]) for i in range(42)])
    return priorities


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


def evaluate_board(board: Board, wrt: str) -> float:
    return evaluate_town(board.towns[wrt]) - max(
        evaluate_town(town) for _name, town in board.towns.items() if _name != wrt
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
    name: str,
    board: Board,
    actions: list[Action],
    depth: int,
    choices=None,
    verbose=False,
) -> tuple[Action, float]:
    expected_action = actions[0]
    if choices is None:
        if isinstance(actions[0], MayorAction):
            choices = [
                Pablo(name=actions[0].name, depth=depth).decide_mayor(board, actions)
            ]
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


def embed(board: Board, wrt: str):
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
    for town in board.town_round_from(wrt):
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


def embed_mayor(town: Town):
    data = []
    # 6 x 4
    for tile_type in TILES:
        for amount in range(4):
            data.append(int(town.count_farmers(tile_type) > amount))
    #
    for build_type in BUILDINGS:
        space = BUILDINFO[build_type]["space"]
        for num_workers in range(space):
            data.append(int(town.count_workers(build_type) > num_workers))
    return data
