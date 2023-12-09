from typing import Literal

from attr import define

from rico import Board, RuleError, enforce

from .base import Action
from .role import RoleAction
from .terminate import TerminateAction


@define
class GovernorAction(Action):
    type: Literal["governor"] = "governor"
    priority: int = 0

    def __str__(self):
        return f"{self.name}.governor()"

    def possibilities(self, board: Board, **kwargs):
        return [self]

    def react(action, board: Board) -> tuple[Board, list[Action]]:
        board.set_governor(action.name)
        extra = [RoleAction(name=name) for name in board.round_from(action.name)]
        extra += [GovernorAction(name=board.next_to(action.name))]
        
        if not board.is_end_of_round():
            # Game just started, nothing else to do
            return board, extra

        # Increase money bonus of unchosen roles
        try:
            board.pay_roles()
        except RuleError:
            return board, [ TerminateAction(name=action.name, reason="Not enough money for roles.")]

        # Take back all role cards and reset flags
        for town in board.towns.values():
            # board.roles.append(town.role)
            town.role = None
            town.spent_wharf = False
            town.spent_captain = False

        return board, extra
