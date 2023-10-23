from typing import Literal

from attr import define
from rico.exceptions import enforce
# from game.games import Game
from .. import GOODS

from rico.reactions.base import Action

@define
class RefuseAction(Action):
    type: Literal["refuse"] = "refuse"

    def react(action, game):

        enforce(
            game.expected_player.name == action.player_name,
            f"Now is not the time for {action.player_name} to take action.",
        )
        enforce(
            game.expected_action.type
            in [
                "settler",
                "mayor",
                "builder",
                "craftsman",
                "trader",
                "captain",
                "storage",
            ],
            f"Can't refuse {game.expected_action}.",
        )
        player = game.players[action.player_name]
        refused = game.actions.pop(0)
        if (
            refused.type == "captain"
            and sum(player.count(_good) for _good in GOODS) > 0
        ):
            game.actions = (
                [action for action in game.actions if action.type == "captain"]
                + [Action(player_name=player.name, type="storage")]
                + [action for action in game.actions if action.type != "captain"]
            )
