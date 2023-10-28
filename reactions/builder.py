from itertools import product
from typing import Literal, Optional

from attr import define

from rico import BUILDINFO, Board, Building, BuildingType, enforce

from .base import Action
from .refuse import RefuseAction
from .terminate import TerminateAction


@define
class BuilderAction(Action):
    building_type: Optional[BuildingType] = None
    extra_person: bool = False
    type: Literal["builder"] = "builder"
    priority: int = 5

    def react(action, board: Board):
        town = board.towns[action.name]
        buildinfo = BUILDINFO[action.building_type]
        tier = buildinfo["tier"]
        cost = buildinfo["cost"]
        quarries_discount = min(tier, town.active_quarries())
        builder_discount = 1 if town.role == "builder" else 0
        price = max(0, cost - quarries_discount - builder_discount)
        enforce(town.has(price, "money"), f"Player does not have enough money.")
        enforce(
            [kind for kind in board.unbuilt if kind == action.building_type],
            f"There are no more {action.building_type} to sell.",
        )
        enforce(
            town.vacant_places >= (2 if tier == 4 else 1),
            f"Player {town.name} does not have space for {action.building_type}",
        )

        i, type = next(
            (i, type)
            for i, type in enumerate(board.unbuilt)
            if type == action.building_type
        )
        board.unbuilt.pop(i)
        new_building = Building(type=type)
        town.buildings.append(new_building)
        if action.extra_person and town.priviledge("hospice") and board.has("people"):
            board.give(1, "people", to=new_building)
        town.give(price, "money", to=board)

        extra = []
        # Stop for building space
        if town.vacant_places == 0:
            extra.append(
                TerminateAction(
                    name=action.name, reason="Game over: no more real estate."
                )
            )

        return board, extra

    def possibilities(self, board: Board) -> list["BuilderAction"]:
        town = board.towns[self.name]

        extra_person_possibilities = (
            [False, True]
            if town.priviledge("hospice") and board.has("people")
            else [False]
        )

        type_possibilities: list[BuildingType] = []
        for type in set(board.unbuilt):
            tier = BUILDINFO[type]["tier"]
            cost = BUILDINFO[type]["cost"]
            quarries_discount = min(tier, town.active_quarries())
            builder_discount = 1 if town.role == "builder" else 0
            price = max(0, cost - quarries_discount - builder_discount)
            if town.has(price, "money") and town.vacant_places >= (
                2 if tier == 4 else 1
            ):
                type_possibilities.append(type)

        return [RefuseAction(name=town.name)] + [
            BuilderAction(name=town.name, building_type=type, extra_person=extra)
            for (type, extra) in product(type_possibilities, extra_person_possibilities)
        ]
