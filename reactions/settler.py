from typing import Literal

from attr import define
from reactions.tidyup import TidyUpAction

from rico import Board, TileType, Town, enforce

from .base import Action
from .refuse import RefuseAction


@define
class SettlerAction(Action):
    tile: TileType = None
    down_tile: bool = False
    extra_person: bool = False
    type: Literal["settler"] = "settler"
    priority: int = 5

    def __str__(self):
        return f"{self.name}.settler({self.tile}{' +downtile' if self.down_tile else ''}{' +worker' if self.extra_person else ''})"

    def react(action, board: Board) -> tuple[Board, list[Action]]:
        town: Town = board.towns[action.name]
        
        enforce(
            not action.down_tile or town.privilege("hacienda"),
            "Can't take down tile without occupied hacienda.",
        )
        enforce(
            not action.extra_person or town.privilege("hospice"),
            "Can't take extra person without occupied hospice.",
        )
        enforce(
            action.tile != "quarry"
            or town.role == "settler"
            or town.privilege("construction_hut"),
            "Only the settler can pick a quarry",
        )
        enforce(
            len(town.tiles) < 12,
            "At most 12 tile per player."
        )

        board.give_tile(to=town, type=action.tile)
        if action.extra_person and board.has("people"):
            board.give(1, "people", to=town.tiles[-1])
        if action.down_tile and board.unsettled_tiles:
            board.give_tile(to=town, type="down")
        
        return board, []

    def possibilities(self, board: Board, **kwargs) -> list["SettlerAction"]:
        town = board.towns[self.name]
        actions = []
        if len(town.tiles) < 12:
            tiletypes = set(board.exposed_tiles)
            if board.unsettled_quarries and (town.role == "settler" or town.privilege("construction_hut")):
                tiletypes.add("quarry")
            for tile_type in tiletypes:
                actions.append(SettlerAction(name=town.name, tile=tile_type))
                if town.privilege("hacienda") and town.privilege("hospice"):
                    actions.append(SettlerAction(name=town.name, tile=tile_type, down_tile=True, extra_person=True))
                if town.privilege("hacienda"):
                    actions.append(SettlerAction(name=town.name, tile=tile_type, down_tile=True))
                if town.privilege("hospice"):
                    actions.append(SettlerAction(name=town.name, tile=tile_type, extra_person=True))
            

        return [RefuseAction(name=town.name)] + actions
