from typing import Literal, Optional

from attr import define

from rico import GOODS, GoodType, enforce
from rico.boards import Board

from .base import Action
from .refuse import RefuseAction


@define
class TraderAction(Action):
    selected_good: Optional[GoodType] = None
    type: Literal["trader"] = "trader"
    priority: int = 5
    
    def __str__(self):
        return f"{self.name}.trade({self.selected_good})"

    def react(action, board: Board) -> tuple[Board, list[Action]]:
        good = action.selected_good
        town = board.towns[action.name]
        enforce(
            sum(board.market.count(g) for g in GOODS) < 4,
            "There is no more space in the market.",
        )
        enforce(
            board.market.count(good) == 0 or town.privilege("office"),
            f"There already is {good} in the market.",
        )
        price = dict(corn=0, indigo=1, sugar=2, tobacco=3, coffee=4)[good]
        price += 1 if town.role == "trader" else 0
        price += 1 if town.privilege("small_market") else 0
        price += 2 if town.privilege("large_market") else 0
        affordable_price = min(price, board.count("money"))
        town.give(1, good, to=board.market)
        board.give(affordable_price, "money", to=town)
        return board, []

    def possibilities(self, board: Board, **kwargs) -> list["TraderAction"]:
        town = board.towns[self.name]
        actions = [RefuseAction(name=town.name)]
        if sum(board.market.count(g) for g in GOODS) >= 4:
            return actions
        for selected_good in [good for good in GOODS if town.has(good)]:
            if board.market.count(selected_good) == 0 or town.privilege("office"):
                actions.append(
                    TraderAction(
                        name=town.name, selected_good=selected_good
                    )
                )
        return actions
