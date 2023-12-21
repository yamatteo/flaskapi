import pickle
from typing import Optional

import numpy as np
from tinygrad.nn import Linear
from tinygrad.nn.optim import SGD, Adam, AdamW
from tinygrad.nn.state import (get_parameters, get_state_dict, load_state_dict,
                               safe_load, safe_save)
from tinygrad.tensor import Tensor

from bots import *
from game import Game
from reactions.terminate import GameOver
from rico import *

batch_size = 200
num_players = 4

def one_game_worth_of_data():
    """Play one game and returns a list of (x, y) tuples.

    Each x is a tuple of ints representing a town mid-game, without loss of information.
    Each y is a tuple of int, y[1:8] is a breakdown of the way we count points,
    i.e. physical points, normal buildings and the five large buildings separately,
    and y[0] is the total.
    """
    bots = {
        "Ad": Quentin("Ad"),  # Heuristic player
        "Be": Quentin("Be"),
        "Ca": Quentin("Ca"),
        "Da": Rufus("Da"),  # Random silly player
    }
    usernames = list(bots.keys())
    game = Game.start(usernames)
    data = []

    while True:
        try:
            bot = bots[game.expected.name]
            town = game.board.towns[game.expected.name]
            inputs = town.as_tuple()
            outputs = town.tally_details()
            # Some sanity checks
            assert outputs[0] == town.tally()
            assert outputs[1] == inputs[8]

            data.append((inputs, outputs))
            action = bot.decide(game)
            game.take_action(action)
        except GameOver as reason:
            # print("GAME OVER.", reason)
            scores = {town.name: town.tally() for town in game.board.towns.values()}
            print(
                "Game over.",
                ", ".join(f"{name}:{score}" for name, score in scores.items()),
            )
            break

    return data


def ogwod_long_range(bots = None, delta = 1):
    if bots is None:
        bots = {
            "Ad": Quentin("Ad"),  # Heuristic player
            "Be": Quentin("Be"),
            "Ca": Quentin("Ca"),
            "Da": Rufus("Da"),  # Random silly player
        }
    elif isinstance(bots, str):
        raise NotImplementedError
    
    usernames = list(bots.keys())
    assert len(usernames) == num_players
    game = Game.start(usernames)

    incomplete_data = dict()
    data = set()

    t = 0
    while True:
        incomplete_data[t] = list()
        try:
            bot = bots[game.expected.name]
            for name in usernames:
                incomplete_data[t].append( (name, sum(game.board.as_tuples(wrt=name), start=tuple()) ) )
            
            for name, embedding in incomplete_data.pop(t - delta, []):
                data.add((game.board.towns[name].tally(), embedding))

            action = bot.decide(game)
            game.take_action(action)
            t += 1
        except GameOver as reason:
            # print("GAME OVER.", reason)
            scores = {town.name: town.tally() for town in game.board.towns.values()}
            for prev_embeddings_list in incomplete_data.values():
                for name, embedding in prev_embeddings_list:
                    data.add((scores[name], embedding))
            print(
                "Game over.",
                ", ".join(f"{name}:{score}" for name, score in scores.items()),
            )
            break

    return data
    


class Estimator:
    def __init__(self, path="./last_net.nn"):
        self.path = path
        board_size = 73
        in_size = 58
        h_size = 60
        steps = 5

        encoding_size = board_size + 4*in_size
        
        self.steps = [Linear(encoding_size + i * h_size, h_size) for i in range(steps)]

        self.final = Linear(encoding_size + steps*h_size, 1, bias=False)

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


def train_round(data, net: Estimator, opt):
    cumulative_loss = 0
    # per_channel_losses = np.zeros(7)
    # per_row_losses = []
    batch_num = -(-len(data) // batch_size)
    with Tensor.train():
        for i in range(0, batch_num):
            start = i*batch_size
            x = Tensor([x for (_, x) in data[start : start + batch_size]], requires_grad=False)
            t = Tensor([t for (t, _) in data[start : start + batch_size]], requires_grad=False)

            # data is sorted in descending order; this way we train more on hard data
            # If we do this step only once, it's a regular training pattern (without shuffle)
            # for _ in range(batch_num - i):
            z = net(x)
            
            loss = ((t - z) ** 2).mean()

            opt.zero_grad()
            loss.backward()
            opt.step()

            # per_channel_losses += difference.sum(axis=0).numpy()
            cumulative_loss += (t - z).abs().sum().item()

            # per_row_losses.extend(difference.sum(axis=1).numpy())


    # per_channel_losses /= len(data)
    cumulative_loss  /= len(data)
    # per_channel_losses = [f"{l:.3f}" for l in per_channel_losses]
    print(f"Loss: {cumulative_loss:.3f}")
    # print(f"Loss: {cumulative_loss:.3f}", "|", " ".join(per_channel_losses))

    # data = [ (x, y) for (_, (x, y)) in sorted(zip(per_row_losses, data), reverse = True)]

    return data, cumulative_loss


def train_cycle(net: Estimator, data, size, target_loss):
    loss = target_loss + 1
    opt = Adam(get_parameters(net))
    while loss > target_loss:
        try:
            if len(data) < size:
                data = list(set(data) | ogwod_long_range(delta=5))

            data, loss = train_round(data, net, opt)
            # data = data[:-10]  # Throw away some data, easier cases because data is sorted

        except (NameError, IndexError):
            print(f" * Delete training data")
            data = []
        except KeyboardInterrupt:
            break
    return data


def main():
    net = Estimator()
    size = 10000

    try:
        net.load()
    except Exception as err:
        print("While loading weights:", err)
    try:
        data = []  # pickle.load(open("training_data.pickle", "rb"))
    except Exception as err:
        print("While loading data:", err)
        data = []

    data = train_cycle(net, data=data, size=size, target_loss=0.1)

    net.save()
    pickle.dump(data, open("training_data.pickle", "wb"))


if __name__ == "__main__":
    main()
