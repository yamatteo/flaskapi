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
    def __init__(self, name: str, depth: int = 30, estimator=None):
        self.name = name
        self.depth = depth
        if estimator is None:
            estimator = heuristic_board_estimator
        self.estimator = estimator
    
    @overload
    def decide(self, game: Game) -> Action:
        ...
    
    @overload
    def decide(self, game: Game, wrt: str, depth: int) -> float:
        ...

    def decide(self, game: Game, depth=None, wrt=None):
        expected = game.expected
        board = game.board
        if depth is None and wrt is None:
            main = True
            depth = self.depth
            wrt = self.name
            assert self.name == expected.name
        else:
            main = False

        if isinstance(expected, MayorAction):
            town = board.towns[expected.name]
            choices = [self.decide_mayor(town)]
        else:
            choices = expected.possibilities(board)

        if main:
            if len(choices) == 1:
                return choices[0]
        else:
            if isinstance(expected, TerminateAction):
                return self.delta(board, wrt=wrt, straight=True)
            if depth <= 0 or isinstance(expected, RoleAction):
                return self.delta(board, wrt=wrt)
            
            
        best_action = None
        best_value = None
        best_wrt_value = None
        for action in choices:
            p_game = game.project(action)
            value = self.decide(p_game, wrt=action.name, depth=depth - 1)
            # print(".."*(self.depth - depth), f"{value:+0.1f} (by {action.name})", action)
            if best_value is None or value > best_value:
                best_action = action
                best_value = value
                best_wrt_value = self.delta(p_game.board, wrt=wrt)
        if main:
            return best_action
        else:
            return best_wrt_value
            
            

        return self.minimax(game, choices=choices, depth=self.depth, wrt=self.name, action_only=True)

    def decide_mayor(self, town: Town) -> Action:
        available_workers = town.total_people
        holders = [
            "home",
            *[tile.type for tile in town.tiles],
            *[building.type for building in town.buildings],
        ]
        distribution = WorkPriority().distribute(available_workers, holders)
        return MayorAction(name=town.name, people_distribution=distribution)

    def delta(self, board: Board, wrt: str, straight=False) -> float:
        estimator = straight_board_estimator if straight else self.estimator
        self_value, *other_values = [
            estimator(board, wrt=name) for name in board.round_from(wrt)
        ]
        return self_value - max(other_values)

    def minimax(self, game: Game, *, choices=None, depth: int) -> Evaluated:
        expected = game.expected
        wrt = expected.name
        board = game.board
        if choices is None:
            if isinstance(expected, MayorAction):
                town = board.towns[expected.name]
                choices = [self.decide_mayor(town)]
            else:
                choices = expected.possibilities(board)
            if isinstance(expected, RoleAction):
                depth = 0
        if isinstance(expected, TerminateAction):
            return Evaluated(choices[0], self.delta(board, wrt=wrt, straight=True))
        elif depth <= 0:
            return Evaluated(choices[0], self.delta(board, wrt=wrt))

        if len(choices) > 20:
            choices = sample(choices, 20)

        # choices = [
        #     Evaluated(action, self.minimax(game.project(action), depth=depth - 1).value)
        #     for action in choices
        # ]

        evaluated = []
        for action in choices:
            selected = Evaluated(action, self.minimax(game.project(action), depth=depth - 1).value)
            print(".."*(self.depth - depth), f"{selected.value:+0.1f}", selected.action)
            evaluated.append(selected)

        # for ev in choices:
        #     print(".."*(3 - depth), f"{ev.value:+0.1f}", ev.action)
        selected = max(evaluated, key=lambda tuple: tuple.value)
        projected = game.project(selected.action)
        wrt_value = self.delta(projected.board, wrt=wrt)
        # print(".."*(self.depth - depth), f"{selected.value:+0.1f}", selected.action)
        return Evaluated(selected.action, wrt_value)
        # return max(choices, key=lambda tuple: tuple.value)
