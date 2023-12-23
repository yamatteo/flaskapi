import pickle
import random
from typing import Optional

import numpy as np
from tinygrad.nn import Linear
from tinygrad.nn.optim import SGD, Adam, AdamW
from tinygrad.nn.state import (
    get_parameters,
    get_state_dict,
    load_state_dict,
    safe_load,
    safe_save,
)
from tinygrad.tensor import Tensor

from bots import *
from game import Game
from reactions.terminate import GameOver
from rico import *

batch_size = 200
data_size = 2000
num_players = 4
iterations = "auto"


def generate_data_one_game(bot_types="qqqr", delay=1):
    """Generate one game worth of data with time delay.

    Before each action, an embedding of the whole game from the pov of each
    player is stored as input; some time later, the points of each player are
    calculated and used as output."""

    bots = dict()
    for name, type in zip(["Ad", "Be", "Ca", "Da", "Ed"], bot_types):
        if type == "q":
            bots[name] = Quentin(name)
        elif type == "r":
            bots[name] = Rufus(name)
    assert len(bots) == len(bot_types) == num_players

    usernames = list(bots.keys())
    game = Game.start(usernames)

    incomplete_data = list()
    data = set()

    while True:
        try:
            bot = bots[game.expected.name]
            for name in usernames:
                incomplete_data.append((name, game.as_tuple(wrt=name)))

            while len(incomplete_data) > delay * num_players:
                name, embedding = incomplete_data.pop(0)
                data.add((game.board.towns[name].tally(), embedding))

            action = bot.decide(game)
            game.take_action(action)
        except GameOver as reason:
            # print("GAME OVER.", reason)
            scores = {town.name: town.tally() for town in game.board.towns.values()}
            for name, embedding in incomplete_data:
                data.add((scores[name], embedding))
            print(
                "Game over.",
                ", ".join(f"{name}:{score}" for name, score in scores.items()),
            )
            break

    return data

def generate_numpy_data(size=1000, bot_types="qqqr", delay=1):
    data = set()
    while len(data) < size:
        data = data | generate_data_one_game(bot_types, delay)
    data = tuple(data)
    x = np.asarray([ x for (t, x) in data])
    t = np.asarray([ t for (t, x) in data])
    return x, t
class Estimator:
    def __init__(self, path="./last_net.nn"):
        self.path = path
        board_embedding_size = 73
        town_embedding_size = 58
        hidden_size = 60
        steps = 5

        encoding_size = board_embedding_size + num_players * town_embedding_size

        self.steps = [
            Linear(encoding_size + i * hidden_size, hidden_size) for i in range(steps)
        ]

        self.final = Linear(encoding_size + steps * hidden_size, 1, bias=False)

    def __call__(self, x):
        for l in self.steps:
            x = x.cat(l(x).leakyrelu(), dim=-1)
        return self.final(x)

    def load(self):
        state_dict = safe_load(self.path)
        load_state_dict(self, state_dict)

    def save(self):
        state_dict = get_state_dict(self)
        safe_save(state_dict, self.path)


def train_round(input: np.ndarray, target: np.ndarray, net: Estimator, opt):
    round_mean_loss = 0
    if iterations == "auto":
        N = max(1, len(input) // batch_size)
    else:
        N = int(iterations)

    with Tensor.train():
        for _ in range(N):
            indexes = np.random.randint(0, len(input), (batch_size, ))
            x = Tensor(input[indexes], requires_grad=False)
            t = Tensor(target[indexes], requires_grad=False)

            z = net(x)

            loss = ((t - z) ** 2).mean()

            opt.zero_grad()
            loss.backward()
            opt.step()

            round_mean_loss += (t - z).abs().mean().numpy().item()

    round_mean_loss /= N
    print(f"Loss: {round_mean_loss:.3E}")

    return round_mean_loss


def train_cycle(net: Estimator, target_loss, data=None):
    loss = target_loss + 1
    opt = Adam(get_parameters(net))
    if data is None or len(data) < data_size:
        input, target = generate_numpy_data(data_size, delay=20)
    else:
        input, target = data
    while loss > target_loss:
        try:
            loss = train_round(input, target, net, opt)
        except KeyboardInterrupt:
            break
    return (input, target)


def main():
    net = Estimator()

    try:
        1 # net.load()
    except Exception as err:
        print("While loading weights:", err)
    try:
        data = []  # pickle.load(open("training_data.pickle", "rb"))
    except Exception as err:
        print("While loading data:", err)
        data = []

    data = train_cycle(net, data=data, target_loss=0.1)


    net.save()
    pickle.dump(data, open("training_data.pickle", "wb"))


if __name__ == "__main__":
    main()
