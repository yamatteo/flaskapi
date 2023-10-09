from copy import copy, deepcopy
from typing import Literal, Union

from attr import define
from game.buildings import BUILDINFO, BUILDINGS, BuildingType
from game.exceptions import enforce
from game.players import Player
from game.reactions.base import Action
from game.reactions.refuse import RefuseAction
from game.tiles import TILES, TileType

PeopleHolder = Union[Literal["home"], TileType, BuildingType]
PeopleAssignment = tuple[PeopleHolder, int]
PeopleDistribution = list[PeopleAssignment]


@define
class MayorAction(Action):
    people_distribution: PeopleDistribution
    type: Literal["mayor"] = "mayor"

    def react(action, game):
        enforce(
            game.is_expecting(action),
            f"Now is not the time for {action.player_name} to distribute people.",
        )
        player = game.expected_player
        updated_player = player.copy()
        (first_holder, people_at_home), *assignments = action.people_distribution
        holders = updated_player.tiles + updated_player.buildings
        enforce(first_holder == "home", "Need to now how many worker stay home.")
        enforce(
            len(assignments) == len(holders),
            f"There should be assignments for every tile/building exactly. Got {assignments} for {holders}",
        )
        updated_player.people = people_at_home
        for (holder_type, amount), holder in zip(assignments, holders):
            enforce(
                holder_type == holder.type,
                f"Wrong assignment: {holder_type} to {holder}",
            )
            holder.people = amount

        enforce(
            updated_player.total_people == player.total_people, "Wrong total of people."
        )

        game.players[player.name] = updated_player
        game.actions.pop(0)

    @classmethod
    def possibilities(cls, game) -> list["MayorAction"]:
        assert game.expected_action.type == "mayor", f"Not expecting a MayorAction."
        player = game.expected_player
        people, space = player.total_people, player.total_space
        holders = [
            "home",
            *[tile.type for tile in player.tiles],
            *[building.type for building in player.buildings],
        ]

        if people >= space:
            dist = tuple(
                people - space
                if key == "home"
                else (1 if key in TILES else BUILDINFO[key]["space"])
                for key in holders
            )
            return [
                MayorAction(
                    player_name=player.name,
                    people_distribution=list(zip(holders, dist)),
                )
            ]
        else:
            dist = tuple(
                0 if key == "home" else (1 if key in TILES else BUILDINFO[key]["space"])
                for key in holders
            )
            distributions = {dist}
            total_people_in_new_dist = sum(dist)
        while total_people_in_new_dist > people:
            new_distributions = set()
            for dist in distributions:
                for i, value in enumerate(dist):
                    if value > 0:
                        next_dist = list(dist)
                        next_dist[i] = value - 1
                        new_distributions.add(tuple(next_dist))
            total_people_in_new_dist -= 1
            distributions = new_distributions

        return [
            MayorAction(
                player_name=player.name, people_distribution=list(zip(holders, dist))
            )
            for dist in distributions
        ]
