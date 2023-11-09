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

    def __str__(self):
        return f"{self.name}.build({self.building_type}{' with worker' if self.extra_person else ''})"

    def react(action, board: Board):
        town = board.towns[action.name]
        board.give_building(action.building_type, to=town)
        if action.extra_person:
            enforce(town.privilege("hospice") and board.has("people"), "Can't ask for extra worker")
            board.give(1, "people", to=town.buildings[-1])

        extra = []
        # Stop for building space
        if town.vacant_places == 0:
            extra.append(
                TerminateAction(
                    name=action.name, reason="Game over: no more real estate."
                )
            )

        return board, extra

    def possibilities(self, board: Board, **kwargs) -> list["BuilderAction"]:
        town = board.towns[self.name]

        extra_person_possibilities = (
            [False, True]
            if town.privilege("hospice") and board.has("people")
            else [False]
        )

        type_possibilities: list[BuildingType] = []
        for type in set(board.unbuilt).difference({ building.type for building in town.buildings }):
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
