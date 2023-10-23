from typing import Literal

from attr import define
from rico.exceptions import enforce
# from game.games import Game
from .. import GOODS, GoodType
from rico.reactions.base import Action
from rico.reactions.refuse import RefuseAction

@define
class TraderAction(Action):
    selected_good: GoodType
    type: Literal["trader"] = "trader"

    def react(action, game):
        enforce(
            game.is_expecting(action),
            f"Now is not the time for {action.player_name} to sell its stuff.",
        )
        good = action.selected_good
        player = game.expected_player
        enforce(
            sum(game.market.count(g) for g in GOODS) < 4,
            "There is no more space in the market.",
        )
        enforce(
            game.market.count(good) == 0 or player.priviledge("office"),
            f"There already is {good} in the market.",
        )
        price = dict(corn=0, indigo=1, sugar=2, tobacco=3, coffee=4)[good]
        price += 1 if player.role == "trader" else 0
        price += 1 if player.priviledge("small_market") else 0
        price += 2 if player.priviledge("large_market") else 0
        affordable_price = min(price, game.count("money"))
        player.give(1, good, to=game.market)
        game.give(affordable_price, "money", to=player)
        game.actions.pop(0)

    @classmethod
    def possibilities(cls, game) -> list["TraderAction"]:
        assert (
            game.expected_action.type == "trader"
        ), f"Not expecting a TraderAction."
        player = game.expected_player
        actions = [RefuseAction(player_name=player.name)]
        if sum(game.market.count(g) for g in GOODS) >= 4:
            return actions
        for selected_good in [good for good in GOODS if player.has(good)]:
            if game.market.count(selected_good) == 0 or player.priviledge("office"):
                actions.append(
                    TraderAction(
                        player_name=player.name, selected_good=selected_good
                    )
                )
        return actions
