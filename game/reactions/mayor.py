from copy import copy, deepcopy
from typing import Literal, Union
from game.buildings import BUILDINFO, BUILDINGS, BuildingType
from game.exceptions import enforce
from game.players import Player
from game.reactions.base import Action
from game.reactions.refuse import RefuseAction
from game.tiles import TILES, TileType

PeopleHolder = Union[Literal["home"], TileType, BuildingType]
PeopleAssignment = tuple[PeopleHolder, int]
PeopleDistribution = list[PeopleAssignment]


class MayorAction(Action):
    type: Literal["mayor"] = "mayor"
    people_disttribution: PeopleDistribution

    def react(action, game):
        enforce(
            game.is_expecting(action),
            f"Now is not the time for {action.player_name} to distribute people.",
        )
        player = game.expected_player
        updated_player = Player(**player.model_dump())
        (first_holder, people_at_home), *assignments = action.people_disttribution
        holders = updated_player.tiles+updated_player.buildings
        enforce(first_holder == "home", "Need to now how many worker stay home.")
        enforce(
            len(assignments) == len(holders),
            f"There should be assignments for every tile/building exactly. Got {assignments} for {holders}"
        )
        updated_player.people = people_at_home
        for (holder_type, amount), holder in zip(assignments, holders):
            enforce(holder_type == holder.type, f"Wrong assignment: {holder_type} to {holder}")
            holder.people = amount
        
        enforce(
            updated_player.total_people == player.total_people, "Wrong total of people."
        )
        
        game.players[player.name] = updated_player
        game.actions.pop(0)


    @classmethod
    def possibilities(cls, game) -> list["MayorAction"]:
        assert (
            game.expected_action.type == "mayor"
        ), f"Not expecting a MayorAction."
        player = game.expected_player
        holders = ["home", *[ tile.type for tile in player.tiles], *[ building.type for building in player.buildings]]
        distributions: set[PeopleDistribution] = {tuple( (key, 0) for key in holders )}
        remaining_total = player.total_people
        while remaining_total > 0:
            new_distributions = set()
            for dist in distributions:
                for i, (key, value) in enumerate(dist):
                    if key == "home" or (key in TILES and value < 1) or (key in BUILDINGS and value < BUILDINFO[key]["space"]):
                        next_dist = list(dist)
                        next_dist[i] = (key, value+1)
                        new_distributions.add(tuple(next_dist))
            remaining_total -= 1
            distributions = new_distributions

        return [RefuseAction(player_name=player.name)] + [ MayorAction(player_name=player.name, people_disttribution=dist) for dist in distributions ]