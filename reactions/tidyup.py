from typing import Literal

from attr import define
from .terminate import TerminateAction

from rico import Board

from .base import Action

@define
class TidyUpAction(Action):
    type: Literal["tidyup"] = "tidyup"
    priority: int = 3

    def __str__(self):
        return f"{self.name}.tidyup()"

    def react(action, board: Board) -> tuple[Board, list[Action]]:
        extra = []

        # Check if enough tiles are revealed
        if len(board.exposed_tiles) <= len(board.towns):
            board.expose_tiles()
        
        # Check ships and market
        board.empty_ships_and_market()
        
        # Eventually refill people_ship
        if board.people_ship.people <= 0:
            total_jobs = sum(town.vacant_jobs for town in board.towns.values())
            total_jobs = max(total_jobs, len(board.towns))
            if board.count("people") >= total_jobs:
                board.give(total_jobs, "people", to=board.people_ship)
            else:
                extra.append(TerminateAction(name=action.name, reason="No more people."))
        
        # Check that there are points left
        if board.points <= 0:
            extra.append(TerminateAction(name=action.name, reason="No more points."))

        return board, extra
    
    def possibilities(self, board: Board, **kwargs) -> list["TidyUpAction"]:
        return [self]
