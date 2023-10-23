from itertools import product
from typing import Literal

from attr import define

from rico.buildings import BUILDINFO, Building, BuildingType
from rico.reactions.refuse import RefuseAction
from rico.roles import RoleType
from rico.exceptions import enforce
# from game.games import Game
from rico.reactions.base import Action

@define
class BuilderAction(Action):
    building_type: BuildingType
    extra_person: bool = False
    type: Literal["builder"] = "builder"

    def react(action, game):
        enforce(
            game.is_expecting(action),
            f"Now is not the time for {action.player_name} to build new stuff.",
        )
        player = game.expected_player
        buildinfo = BUILDINFO[action.building_type]
        tier = buildinfo["tier"]
        cost = buildinfo["cost"]
        quarries_discount = min(tier, player.active_quarries())
        builder_discount = 1 if player.role == "builder" else 0
        price = max(0, cost - quarries_discount - builder_discount)
        enforce(player.has(price, "money"), f"Player does not have enough money.")
        enforce(
            [kind for kind in game.unbuilt if kind == action.building_type],
            f"There are no more {action.building_type} to sell.",
        )
        enforce(
            player.vacant_places >= (2 if tier == 4 else 1),
            f"Player {player.name} does not have space for {action.building_type}",
        )
        game.actions.pop(0)
        i, type = next(
            (i, type)
            for i, type in enumerate(game.unbuilt)
            if type == action.building_type
        )
        game.unbuilt.pop(i)
        new_building = Building(type=type)
        player.buildings.append(new_building)
        if action.extra_person and player.priviledge("hospice") and game.has("people"):
            game.give(1, "people", to=new_building)
        player.give(price, "money", to=game)

    @classmethod
    def possibilities(cls, game) -> list["BuilderAction"]:
        assert game.expected_action.type == "builder", f"Not expecting a BuilderAction."
        player = game.expected_player
        
        extra_person_possibilities = [False, True] if player.priviledge("hospice") and game.has("people") else [False]
        type_possibilities: list[BuildingType] = []
        for type in set(game.unbuilt):
            tier = BUILDINFO[type]["tier"]
            cost = BUILDINFO[type]["cost"]
            quarries_discount = min(tier, player.active_quarries())
            builder_discount = 1 if player.role == "builder" else 0
            price = max(0, cost - quarries_discount - builder_discount)
            if (player.has(price, "money") and player.vacant_places >= (2 if tier == 4 else 1)):
                type_possibilities.append(type)
        
        return [RefuseAction(player_name=player.name)] + [ BuilderAction(player_name=player.name, building_type=type, extra_person=extra) for (type, extra) in product(type_possibilities, extra_person_possibilities) ]