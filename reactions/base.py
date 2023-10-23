from typing import Literal
from attr import define

ActionType = Literal[
    "builder",
    "captain",
    "craftsman",
    "governor",
    "mayor",
    "refuse",
    "role",
    "settler",
    "storage",
    "trader",
]

@define
class Action:
    type: ActionType
    player_name: str

    @classmethod
    def from_compressed(cls, data: str):
        from rico.reactions.governor import GovernorAction  # Avoid circular imports

        type, name = data.split(":")
        if type == "governor":
            return GovernorAction(player_name=name)
        else:
            return Action(type=type, player_name=name)

    def compress(self):
        return f"{self.type}:{self.player_name}"

    @classmethod
    def possibilities(cls, game):
        raise NotImplementedError("This actions should not ask for possibilities.")  


    def react(self, game):
        raise NotImplementedError