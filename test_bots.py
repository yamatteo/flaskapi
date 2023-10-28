

from bots import Rufus
from game import Game
from reactions import GameOver


def test_rufus():
    usernames = ["Ada", "Bert", "Carl", "Dan"]
    game = Game.start(usernames)
    bots = {name: Rufus(name) for name in game.play_order}
    while True:
        try:
            action = bots[game.expected.name].decide(game.board, game.expected)
            print(action)
            game.take_action(action)
        except GameOver as reason:
            print("GAME OVER.", reason)
            print("Final score:")
            scores = {town.name: town.tally() for town in game.board.towns.values()}
            for name, score in scores.items():
                print("  ", name, ">", score, "points")
            break


def nottest_mixed():
    names = ["Ada", "Bert", "Carl", "Dan"]
    game = Board.start_new(names)
    game.people = 75
    bots = {name: Quentin(name=name) if name in ["Ada", "Bert", "Carl", "Dan"] else Rufus(name=name) for name in game.play_order}
    while True:
        try:
            name = game.expected_player.name

            state = Pluto(game.expected_player.name).project(game, game.expected_player.name)[:28]
            print(f"\nSTATE {state}")

            action = Quentin(name).decide(game)
            print(action)

            game.take_action(action)
        except GameOver as reason:
            print(reason)
            print("Final score")
            scores = {player.name: player.tally() for player in game.towns.values()}
            for name, score in scores.items():
                print("  ", name, ">", score, "points")
            break
        # except Exception as err:
        #     breakpoint()
        #     raise err


if __name__=="__main__":
    test_rufus()
    test_rufus()
    test_rufus()
    test_rufus()
    test_rufus()