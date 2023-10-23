from random import choice
from rico.reactions import possibilities


class Rufus:
    def __init__(self, name: str = "Bot Rufus"):
        self.name = name

    def decide(self, game):
        assert game.expected_player.name == self.name, "It's not my turn."
        return choice(possibilities(game))