from attrs import asdict
from bots import Oliver, Pablo, Quentin, Rufus
from game import Game
from reactions import GameOver
from rich import print


def test_rufus():
    usernames = ["Ada", "Bert", "Carl", "Dan", "Earl"]
    game = Game.start(usernames)
    bots = {name: Rufus(name) for name in game.play_order}
    while True:
        try:
            bot = bots[game.expected.name]
            action = bot.decide(game)
            print(action)
            game.take_action(action)
        except GameOver as reason:
            print("GAME OVER.", reason)
            print("Final score:")
            scores = {town.name: town.tally() for town in game.board.towns.values()}
            for name, score in scores.items():
                print("  ", name, ">", score, "points")
            break


def test_quentin():
    test_mixed(
        {
            "Ad": Quentin("Ad"),
            "Be": Quentin("Be"),
            "Ca": Quentin("Ca"),
            "Da": Quentin("Da"),
            "Ea": Quentin("Ea"),
        }
    )


def test_pablo():
    usernames = ["Ada", "Bert", "Carl", "Dan"]
    game = Game.start(usernames)
    bots = {name: Pablo(name, depth=2) for name in game.play_order}
    while True:
        try:
            possibilities = game.expected.possibilities(game.board)
            action = bots[game.expected.name].decide(
                board=game.board, actions=game.actions, verbose=False
            )

            print(action)
            game.take_action(action)
        except GameOver as reason:
            print("GAME OVER.", reason)
            print("Final score:")
            scores = {town.name: town.tally() for town in game.board.towns.values()}
            for name, score in scores.items():
                print("  ", name, ">", score, "points")
            break


def test_oliver():
    usernames = ["Ada", "Bert", "Carl", "Dan"]
    game = Game.start(usernames)
    bots = {
        "Ad": Oliver("Ad"),
        "Be": Oliver("Be"),
        "Ca": Oliver(
            "Ca",
        ),
        "Da": Oliver("Da"),
    }
    while True:
        try:
            training_data, action = bots[game.expected.name].train_decide(
                board=game.board, actions=game.actions
            )

            print(action)
            game.take_action(action)
        except GameOver as reason:
            print("GAME OVER.", reason)
            print("Final score:")
            scores = {town.name: town.tally() for town in game.board.towns.values()}
            for name, score in scores.items():
                print("  ", name, ">", score, "points")
            break


def test_mixed(bots):
    usernames = list(bots.keys())
    game = Game.start(usernames)
    while True:
        try:
            bot = bots[game.expected.name]
            action = bot.decide(game)
            print(action)
            game.take_action(action)
        except GameOver as reason:
            print("GAME OVER.", reason)
            print("Final score:")
            scores = {town.name: town.tally() for town in game.board.towns.values()}
            for name, score in scores.items():
                print("  ", name, ">", score, "points")
            break


if __name__ == "__main__":
    test_quentin()

