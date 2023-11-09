from random import choice
from game import Game

from reactions import Action


class Rufus:
    """A bot that take decisions randomly."""
    def __init__(self, name: str):
        self.name = name

    def decide(self, game: Game) -> Action:
        assert game.expected.name == self.name, "It's not my turn."
        return choice(game.expected.possibilities(game.board, cap=20))