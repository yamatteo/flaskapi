from typing import Literal

from game.roles import RoleType
from game.exceptions import RuleError, enforce
# from game.games import Game
from .base import Action


class RoleAction(Action):
    type: Literal["role"] = "role"
    role: RoleType = None

    def react(self, game):
        enforce(
            game.is_expecting(self),
            f"Now is not the time for {self.player_name} to take a role.",
        )

        player = game.expected_player
        role = self.role
        
        enforce(
            player.role is None,
            f"Player {player.name} already has role ({player.role}).",
        )

        player.role = game.pop_role(self.role)
        player.role.give("all", "money", to=player)

        game.actions.pop(0)

        if role == "settler":
            game.actions = [
                Action(player_name=name, type="settler")
                for name in game.name_round_from(player.name)
            ] + game.actions
        if role == "mayor":
            game.give(1, "people", to=player)
            while game.people_ship.count("people"):
                for _player in game.player_round_from(player.name):
                    try:
                        game.people_ship.give(1, "people", to=_player)
                    except RuleError:
                        break
            game.actions = [
                Action(player_name=name, type="mayor")
                for name in game.name_round_from(player.name)
            ] + game.actions
        if role == "builder":
            game.actions = [
                Action(player_name=name, type="builder")
                for name in game.name_round_from(player.name)
            ] + game.actions
        if role == "craftsman":
            for _player in game.player_round_from(player.name):
                for good, amount in _player.production().items():
                    possible_amount = min(amount, game.count(good))
                    game.give(possible_amount, good, to=_player)
            game.actions = [
                Action(player_name=player.name, type="craftsman")
            ] + game.actions
        if role == "trader":
            game.actions = [
                Action(player_name=name, type="trader")
                for name in game.name_round_from(player.name)
            ] + game.actions
        if role == "captain":
            game.actions = [
                Action(player_name=name, type="captain")
                for name in game.name_round_from(player.name)
            ] + game.actions
        if role == "prospector":
            if game.has("money"):
                game.give(1, "money", to=player)

        game.take_action()
    
    @classmethod
    def possibilities(cls, game) -> list["RoleAction"]:
        assert game.expected_action.type == "role", f"Not expecting a RoleAction."
        player = game.expected_player
        return [ RoleAction(player_name=player.name, role=role.type) for role in game.roles ]
