from typing import Literal

from attr import define

from rico import Board

from .base import Action


class GameOver(Exception):
    pass


@define
class TerminateAction(Action):
    reason: str
    type: Literal["terminate"] = "terminate"
    priority: int = 1

    def react(action, board: Board):
        raise GameOver(action.reason)
    
    def possibilities(self, board: Board, **kwargs) -> list[Action]:
        return [self]
