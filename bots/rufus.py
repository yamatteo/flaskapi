from random import choice

from reactions import Action
from rico import Board


class Rufus:
    def __init__(self, name: str):
        self.name = name

    def decide(self, board: Board, expected_action: Action):
        assert expected_action.name == self.name, "It's not my turn."
        return choice(expected_action.possibilities(board))