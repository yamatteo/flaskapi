from game.bots.pluto import Pluto
from game.bots.rufus import Rufus
from game import *


def test_rufus():
    names = ["Ada", "Bert", "Carl", "Dan"]
    game = Game.start_new(names)
    game.people = 75
    bots = {name: Rufus(name=name) for name in game.play_order}
    while True:
        try:
            action = bots[game.expected_player.name].decide(game)
            print(action)
            game.take_action(action)
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


def test_mixed():
    names = ["Ada", "Bert", "Carl", "Dan"]
    game = Game.start_new(names)
    game.people = 75
    bots = {name: Pluto(name=name) if name in ["Ada"] else Rufus(name=name) for name in game.play_order}
    while True:
        try:
            action = bots[game.expected_player.name].decide(game)
            print(action)
            game.take_action(action)
        except GameOver as reason:
            print(reason)
            print("Final score")
            scores = {player.name: player.tally() for player in game.players.values()}
            for name, score in scores.items():
                print("  ", name, ">", score, "points")
            break
        # except Exception as err:
        #     breakpoint()
        #     raise err


if __name__=="__main__":
    test_mixed()