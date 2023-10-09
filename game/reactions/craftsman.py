from typing import Literal

from attr import define
from game.exceptions import enforce
# from game.games import Game
from game.holders import GOODS, GoodType
from game.reactions.base import Action
from game.reactions.refuse import RefuseAction

@define
class CraftsmanAction(Action):
    selected_good: GoodType
    type: Literal["craftsman"] = "craftsman"

    def react(action, game):
        enforce(
            game.is_expecting(action),
            f"Now is not the time for {action.player_name} to get extra goods.",
        )
        good = action.selected_good
        player = game.expected_player
        enforce(
            player.production(good) > 0,
            f"Craftsman get one extra good of something he produces, not {good}.",
        )
        enforce(game.has(good), f"There is no {good} left in the game.")
        game.give(1, good, to=player)
        game.actions.pop(0)

    @classmethod
    def possibilities(cls, game) -> list["CraftsmanAction"]:
        assert (
            game.expected_action.type == "craftsman"
        ), f"Not expecting a CraftsmanAction."
        player = game.expected_player
        actions = []
        for selected_good in GOODS:
            if player.production(selected_good) > 0 and game.has(selected_good):
                actions.append(
                    CraftsmanAction(
                        player_name=player.name, selected_good=selected_good
                    )
                )
        return [RefuseAction(player_name=player.name)] + actions
