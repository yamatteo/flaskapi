import pytest
from game.bots.rufus import Rufus
# from rich import print
from game import *


def test_rufus():
    names = ["Ada", "Bert", "Carl", "Dan"]
    game = Game.start_new(names)
    game.people = 75  # Shorter game
    bots = {name: Rufus(name=name) for name in game.play_order}
    state, action = game.compress(), None
    while True:
        try:
            prev_state = state
            state, prev_action = game.compress(), action.model_dump() if action else None
            action = bots[game.expected_player.name].decide(game)
            game.take_action(action)
            print(prev_action)
        except GameOver as reason:
            print(reason)
            print("Final score")
            scores = {player.name: player.tally() for player in game.players.values()}
            for name, score in scores.items():
                print("  ", name, ">", score, "points")
            break
        except Exception as err:
            breakpoint()
            raise err


if __name__=="__main__":
    test_rufus()