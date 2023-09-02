from .base import Action, ActionType
from .builder import BuilderAction
from .captain import CaptainAction
from .craftsman import CraftsmanAction
from .governor import GovernorAction
from .mayor import MayorAction
from .refuse import RefuseAction
from .role import RoleAction
from .settler import SettlerAction
from .storage import StorageAction
from .trader import TraderAction

def possibilities(game) -> list[Action]:
    type: ActionType = game.expected_action.type
    if type == "builder":
        return BuilderAction.possibilities(game)
    elif type == "captain":
        return CaptainAction.possibilities(game)
    elif type == "craftsman":
        return CraftsmanAction.possibilities(game)
    elif type == "governor":
        return GovernorAction.possibilities(game)
    elif type == "mayor":
        return MayorAction.possibilities(game)
    elif type == "refuse":
        return RefuseAction.possibilities(game)
    elif type == "role":
        return RoleAction.possibilities(game)
    elif type == "settler":
        return SettlerAction.possibilities(game)
    elif type == "storage":
        return StorageAction.possibilities(game)
    elif type == "trader":
        return TraderAction.possibilities(game)
    else:
        raise NotImplementedError(f"Unknown action type {type}.")