from typing import Literal

from attr import define
from game.exceptions import enforce
from game.players import Player
from game.reactions.base import Action
from game.reactions.refuse import RefuseAction
from game.tiles import TileType

@define
class SettlerAction(Action):
    tile: TileType
    down_tile: bool = False
    extra_person: bool = False
    type: Literal["settler"] = "settler"

    def react(action, game):
        enforce(
            game.is_expecting(action),
            f"Now is not the time for {action.player_name} to settle."
        )
        player: Player = game.expected_player
        
        enforce(
            not action.down_tile or player.priviledge("hacienda"),
            "Can't take down tile without occupied hacienda.",
        )
        enforce(
            not action.extra_person or player.priviledge("hospice"),
            "Can't take extra person without occupied hospice.",
        )
        enforce(
            action.tile != "quarry"
            or player.role == "settler"
            or player.priviledge("construction_hut"),
            "Only the settler can pick a quarry",
        )

        game.give_tile(to=player, type=action.tile)
        if action.extra_person and game.has("people"):
            game.give(1, "people", to=player.tiles[-1])
        if action.down_tile and game.unsettled_tiles:
            game.give_tile(to=player, type="down")
        game.actions.pop(0)

        if game.expected_action.type != "settler":
            game.expose_tiles()

    @classmethod
    def possibilities(cls, game) -> list["SettlerAction"]:
        assert game.expected_action.type == "settler", f"Not expecting a SettlerAction."
        player = game.expected_player
        actions = []
        tiletypes = set(game.exposed_tiles)
        if game.unsettled_quarries and (player.role == "settler" or player.priviledge("construction_hut")):
            tiletypes.add("quarry")
        for tile_type in tiletypes:
            actions.append(SettlerAction(player_name=player.name, tile=tile_type))
            if player.priviledge("hacienda") and player.priviledge("hospice"):
                actions.append(SettlerAction(player_name=player.name, tile=tile_type, down_tile=True, extra_person=True))
            if player.priviledge("hacienda"):
                actions.append(SettlerAction(player_name=player.name, tile=tile_type, down_tile=True))
            if player.priviledge("hospice"):
                actions.append(SettlerAction(player_name=player.name, tile=tile_type, extra_person=True))
            

        return [RefuseAction(player_name=player.name)] + actions
