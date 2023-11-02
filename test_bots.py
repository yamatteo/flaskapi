

from attrs import asdict
from bots import Rufus, Quentin
from bots.pablo import Pablo, embed, embed_town
from game import Game
from reactions import GameOver
from rich import print

from reactions.mayor import MayorAction


def test_rufus():
    usernames = ["Ada", "Bert", "Carl", "Dan"]
    game = Game.start(usernames)
    bots = {name: Rufus(name) for name in game.play_order}
    while True:
        try:
            possibilities = game.expected.possibilities(game.board)
            action = bots[game.expected.name].decide(game.board, game.expected)
            game.take_action(action)
        except GameOver as reason:
            print("GAME OVER.", reason)
            print("Final score:")
            scores = {town.name: town.tally() for town in game.board.towns.values()}
            for name, score in scores.items():
                print("  ", name, ">", score, "points")
            break


def test_quentin():
    usernames = ["Ada", "Bert", "Carl", "Dan"]
    game = Game.start(usernames)
    bots = {name: Quentin(name, depth=2) for name in game.play_order}
    while True:
        try:
            possibilities = game.expected.possibilities(game.board)
            action = bots[game.expected.name].decide(board=game.board, actions=game.actions, verbose=True)
            print(action)
            game.take_action(action)
        except GameOver as reason:
            print("GAME OVER.", reason)
            print("Final score:")
            scores = {town.name: town.tally() for town in game.board.towns.values()}
            for name, score in scores.items():
                print("  ", name, ">", score, "points")
            break


def test_pablo():
    usernames = ["Ada", "Bert", "Carl", "Dan"]
    game = Game.start(usernames)
    bots = {name: Pablo(name, depth=2) for name in game.play_order}
    while True:
        try:
            possibilities = game.expected.possibilities(game.board)
            action = bots[game.expected.name].decide(board=game.board, actions=game.actions, verbose=False)

        
            if isinstance(action, MayorAction):
                board_emb = embed(game.board, game.expected.name)
            print(action)
            game.take_action(action)

            if isinstance(action, MayorAction):
                town_emb = embed_town(game.board.towns[game.expected.name])
                x = 0
        except GameOver as reason:
            print("GAME OVER.", reason)
            print("Final score:")
            scores = {town.name: town.tally() for town in game.board.towns.values()}
            for name, score in scores.items():
                print("  ", name, ">", score, "points")
            break


def test_mixed():
    usernames = ["Ada", "Bert", "Carl", "Dan"]
    game = Game.start(usernames)
    bots = {name: (Quentin(name, depth=2) if name=="Ad" else Rufus(name)) for name in game.play_order}
    while True:
        try:
            possibilities = game.expected.possibilities(game.board)
            bot = bots[game.expected.name]
            if isinstance(bot, Rufus):
                action = bot.decide(game.board, game.expected)
            elif isinstance(bot, Quentin):
                action = bot.alt_decide(board=game.board, actions=game.actions, verbose=True)
            print(action)
            game.take_action(action)
        except GameOver as reason:
            print("GAME OVER.", reason)
            print("Final score:")
            scores = {town.name: town.tally() for town in game.board.towns.values()}
            for name, score in scores.items():
                print("  ", name, ">", score, "points")
            break


if __name__=="__main__":
    test_pablo()