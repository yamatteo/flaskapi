from typing import Literal

from attr import define
from reactions.builder import BuilderAction
from reactions.craftsman import CraftsmanAction
from reactions.settler import SettlerAction
from reactions.storage import StorageAction
from reactions.trader import TraderAction

from rico import Board, Role, RuleError, enforce
from rico.constants import ROLES

from .base import Action
from .captain import CaptainAction
from .mayor import MayorAction
from .terminate import TerminateAction
from .tidyup import TidyUpAction


@define
class RoleAction(Action):
    role: Role = None
    type: Literal["role"] = "role"
    priority: int = 2

    def __str__(self):
        return f"{self.name}.take_role({self.role})"

    def react(action, board: Board):
        town = board.towns[action.name]
        role = action.role

        enforce(
            town.role is None,
            f"Player {town.name} already has role ({town.role}).",
        )

        board.give_role(role, to=town)

        if role == "settler":
            extra = [SettlerAction(name=name) for name in board.round_from(town.name)] + [TidyUpAction(name=action.name)]
        if role == "mayor":
            if board.has("people"):
                board.give(1, "people", to=town)
            while board.people_ship.count("people"):
                for some_town in board.town_round_from(town.name):
                    try:
                        board.people_ship.give(1, "people", to=some_town)
                    except RuleError:
                        break

            extra = [MayorAction(name=name) for name in board.round_from(town.name)]
            extra.append(TidyUpAction(name=action.name))

        if role == "builder":
            extra = [BuilderAction(name=name) for name in board.round_from(town.name)]
        if role == "craftsman":
            for some_town in board.town_round_from(town.name):
                for good, amount in some_town.production().items():
                    possible_amount = min(amount, board.count(good))
                    board.give(possible_amount, good, to=some_town)
            extra = [CraftsmanAction(name=town.name)]
        if role == "trader":
            extra = [TraderAction(name=name) for name in board.round_from(town.name)] + [TidyUpAction(name=action.name)]
        if role == "captain":
            extra = (
                [CaptainAction(name=name) for name in board.round_from(town.name)]
                + [StorageAction(name=name) for name in board.round_from(town.name)]
                + [TidyUpAction(name=action.name)]
            )
        if role in ["prospector1", "prospector2"]:
            if board.has("money"):
                board.give(1, "money", to=town)
                extra = []
            if board.count("money") <= 0:
                extra = [TerminateAction(name=action.name, reason="No more money.")]

        return board, extra

    def possibilities(self, board: Board, **kwargs) -> list["RoleAction"]:
        return [RoleAction(name=self.name, role=role) for role, money in zip(ROLES, board.roles) if money > -1]
