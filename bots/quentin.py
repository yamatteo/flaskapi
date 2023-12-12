from random import sample
import random
from bots.direct_estimator import heuristic_board_estimator

from game import Game
from reactions import Action, MayorAction, TerminateAction
from rico import GOODS, SMALL_BUILDINGS, Board, Town

from .distribution import WorkPriority


class Quentin:
    def __init__(self, name: str):
        self.name = name

    def decide(self, game: Game) -> Action:
        expected = game.expected
        board = game.board
        assert self.name == expected.name

        if isinstance(expected, MayorAction):
            return self.decide_mayor(board.towns[self.name])

        choices = expected.possibilities(board)
        if len(choices) == 1:
            return choices[0]

        good_choices = None
        best_value = None
        for action in choices:
            self_value, *other_values = [
                    heuristic_board_estimator(board, wrt=wrt)
                    for wrt in board.round_from(self.name)
                ]
            value = self_value - max(other_values)
            if best_value is None or value > best_value:
                best_value = value
                good_choices = [action]
            elif value == best_value:
                good_choices.append(action)
        return random.choice(good_choices)

    def decide_mayor(self, town: Town) -> Action:
        available_workers = town.total_people
        holders = [
            "home",
            *town.list_tiles(),
            *town.list_buildings(),
        ]
        distribution = WorkPriority().distribute(available_workers, holders)
        return MayorAction(name=town.name, people_distribution=distribution)
