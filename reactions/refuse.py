from typing import Literal

from attr import define

from rico import GOODS, Board, enforce

from . import ActionType
from .base import Action


@define
class RefuseAction(Action):
    type: Literal["refuse"] = "refuse"
    priority: int = 4

    def __str__(self):
        return f"{self.name}.refuse()"

    def possibilities(self, board: Board, **kwargs):
        return [self]

    def react(action, board: Board) -> tuple[Board, list[Action]]:
        return board, []
