from typing import Literal

from attr import define

from rico.exceptions import enforce
# from game.games import Game
from .base import Action
from .role import RoleAction


@define
class GovernorAction(Action):
    type: Literal["governor"] = "governor"

    @classmethod
    def possibilities(cls, game) -> list["GovernorAction"]:
        assert (
            game.expected_action.type == "governor"
        ), f"Not expecting a GovernorAction."
        player = game.expected_player
        return [GovernorAction(player_name=player.name)]

    def react(self, game):
        enforce(
            game.is_expecting(self),
            f"Now is not the time for {self.player_name} to be the governor.",
        )

        last_governor = next((player for player in game.players.values() if player.gov), None)  # Find last governor, if any

        if last_governor:
            # Increase money bonus of unchosen roles
            if game.has(len(game.roles), "money"):
                for card in game.roles:
                    game.give(1, "money", to=card)
            else:
                game.terminate("Game over: no more money.")
            last_governor.gov = False
        
        # Take back all role cards and reset flags
        for player in game.players.values():
            if player.role:
                game.roles.append(player.role)
                player.role = None
            player.spent_wharf = False
            player.spent_captain = False

        # Eventually refill people_ship
        if game.people_ship.count("people") == 0:
            total = sum(player.vacant_jobs for player in game.players.values())
            total = max(total, len(game.players))
            if game.count("people") >= total:
                game.give(total, "people", to=game.people_ship)
            else:
                game.terminate("Game over: no more people.")

        # Stop for building space
        for player in game.players.values():
            if player.vacant_places == 0:
                game.terminate("Game over: no more real estate.")

        # Stop for victory points
        if game.count("points") <= 0:
            game.terminate("Game over: no more points.")

        new_governor = game.players[self.player_name]
        new_governor.gov = True

        game.actions.append(game.actions.pop(0))
        game.actions = [
            Action(player_name=name, type="role")
            for name in game.name_round_from(new_governor.name)
        ] + game.actions