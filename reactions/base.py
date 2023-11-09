from attr import define, asdict

from rico import Board

from . import ActionType


@define
class Action:
    type: ActionType
    name: str
    priority: int

    def possibilities(self, board: Board, **kwargs) -> list["Action"]:
        # When not otherwise defined, this is a forced action with no choice for the player
        raise NotImplementedError
        return [self]

    def react(self, board: Board) -> tuple[Board, list["Action"]]:
        raise NotImplementedError

    def responds_to(self, other: "Action") -> bool:
        exact_type = self.type == other.type
        refusal = self.type == "refuse" and other.type in [
            "builder",
            "captain",
            "craftsman",
            "settler",
            "storage",
            "trader",
        ]
        exact_name = self.name == other.name
        correct_payload = all(
            value is not None
            for value in asdict(
                self, filter=lambda k, v: k.name not in ["type", "name", "priority"]
            ).values()
        )
        return (exact_type or refusal) and exact_name and correct_payload
