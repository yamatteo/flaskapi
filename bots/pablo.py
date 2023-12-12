from collections import namedtuple
from random import sample
from typing import overload

from game import Game
from reactions import Action, MayorAction, TerminateAction
from reactions.role import RoleAction
from rico import Board, Town

from .direct_estimator import heuristic_board_estimator, straight_board_estimator
from .distribution import WorkPriority


Evaluated = namedtuple("Evaluated", ["action", "value"])


class Pablo:
    def __init__(self, name: str, estimator=heuristic_board_estimator):
        self.name = name
        self.estimator = estimator

    def decide(self, game: Game) -> Action:
        action, _ = self.decide_with_value(game)
        return action

    def decide_with_value(self, game: Game) -> tuple[Action, float]:
        expected = game.expected
        board = game.board

        if isinstance(expected, MayorAction):
            town = board.towns[expected.name]
            choices = [self.decide_mayor(town)]
        else:
            choices = expected.possibilities(board)

        if isinstance(expected, TerminateAction):
            return choices[0], straight_board_estimator(game.board, wrt=self.name)

        best_action = None
        best_delta = None
        best_value = None
        for action in choices:
            p_game = game.project(action)
            value = self.estimator(p_game.board, wrt=self.name)
            delta = self.delta(p_game.board, wrt=self.name)
            # print(".."*(self.depth - depth), f"{value:+0.1f} (by {action.name})", action)
            if best_delta is None or delta > best_delta:
                best_action = action
                best_value = value
                best_delta = delta
        return best_action, best_value

    def decide_mayor(self, town: Town) -> Action:
        available_workers = town.total_people
        holders = [
            "home",
            *town.list_tiles(),
            *town.list_buildings(),
        ]
        distribution = WorkPriority().distribute(available_workers, holders)
        return MayorAction(name=town.name, people_distribution=distribution)

    def delta(self, board: Board, wrt: str, straight=False) -> float:
        estimator = straight_board_estimator if straight else self.estimator
        self_value, *other_values = [
            estimator(board, wrt=name) for name in board.round_from(wrt)
        ]
        return self_value - max(other_values)
