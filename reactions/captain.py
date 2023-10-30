from typing import Literal

from attr import define

from rico import GOODS, GoodType, enforce
from rico.boards import Board

from .base import Action
from .refuse import RefuseAction


@define
class CaptainAction(Action):
    selected_ship: int = None
    selected_good: GoodType = None
    type: Literal["captain"] = "captain"
    priority: int = 5

    def __str__(self):
        return f"{self.name}.captain({self.selected_good} in {self.selected_ship})"

    def react(action, board: Board) -> tuple[Board, list[Action]]:
        town = board.towns[action.name]
        ship_size = action.selected_ship
        good = action.selected_good

        # Want to use wharf
        if ship_size == 11:
            enforce(
                town.priviledge("wharf") and not town.spent_wharf,
                "Player does not have a free wharf.",
            )
            town.spent_wharf = True
            amount = town.count(good)
            town.give(amount, good, to=board)
            points = amount
            if town.priviledge("harbor"):
                points += 1
            if town.role == "captain" and not town.spent_captain:
                points += 1
                town.spent_captain = True
            board.give_or_make(points, "points", to=town)

        else:
            enforce(
                board.goods_fleet.accepts(ship_size=ship_size, good=good),
                f"Ship {ship_size} cannot accept {good}.",
            )
            ship = board.goods_fleet[ship_size]
            amount = min(ship.size - ship.count(good), town.count(good))
            town.give(amount, good, to=ship)
            points = amount
            if town.priviledge("harbor"):
                points += 1
            if town.role == "captain" and not town.spent_captain:
                points += 1
                town.spent_captain = True
            board.give_or_make(points, "points", to=town)

        extra = []
        if sum(town.count(g) for g in GOODS) > 0:
            extra = [CaptainAction(name=action.name)]

        return board, extra

    def possibilities(self, board: Board) -> list["CaptainAction"]:
        town = board.towns[self.name]
        actions = [RefuseAction(name=town.name)]
        for selected_good in GOODS:
            if not town.has(selected_good):
                continue
            if town.priviledge("wharf") and not town.spent_wharf:
                actions.append(
                    CaptainAction(
                        name=town.name, selected_good=selected_good, selected_ship=11
                    )
                )
            for ship_size in board.goods_fleet:
                if board.goods_fleet.accepts(ship_size=ship_size, good=selected_good):
                    actions.append(
                        CaptainAction(
                            name=town.name,
                            selected_good=selected_good,
                            selected_ship=ship_size,
                        )
                    )

        return actions
