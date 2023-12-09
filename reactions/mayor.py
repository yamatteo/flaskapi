import random
from typing import Literal, Union

from attr import define

from rico import BUILDINFO, TILES, Board, BuildingType, Tile, enforce
from rico.buildings import Building

from .base import Action

PeopleHolder = Union[Literal["home"], Tile, BuildingType]
PeopleAssignment = tuple[PeopleHolder, int]
PeopleDistribution = list[PeopleAssignment]


@define
class MayorAction(Action):
    people_distribution: PeopleDistribution = None
    type: Literal["mayor"] = "mayor"
    priority: int = 5

    def __str__(self):
        occupations = str(", ").join(
            f"{holder}={amount}" for holder, amount in self.people_distribution
        )
        return f"{self.name}.mayor({occupations})"

    def react(action, board: Board) -> tuple[Board, list[Action]]:
        town = board.towns[action.name]

        updated_town = town.copy()
        (first_holder, people_at_home), *assignments = action.people_distribution
        holders = updated_town.list_tiles() + updated_town.buildings
        enforce(first_holder == "home", "Need to now how many worker stay home.")
        enforce(
            len(assignments) == len(holders),
            f"There should be assignments for every tile/building exactly. Got {assignments} for {holders}",
        )
        updated_town.people = people_at_home
        updated_town.worked_tiles = [0]*8
        for (holder_type, amount), holder in zip(assignments, holders):
            if isinstance(holder, Building):
                enforce(
                    holder_type == holder.type,
                    f"Wrong assignment: {holder_type} to {holder}",
                )
                holder.people = amount
            elif holder in TILES:
                updated_town.worked_tiles[TILES.index(holder)] += 1

        enforce(
            updated_town.total_people == town.total_people, "Wrong total of people."
        )

        board.towns[town.name] = updated_town
        return board, []

    def possibilities(self, board: Board, cap=None, **kwargs) -> list["MayorAction"]:
        town = board.towns[self.name]
        people, space = town.total_people, town.total_space
        holders = [
            "home",
            *town.list_tiles(),
            *[building.type for building in town.buildings],
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
                    name=town.name,
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
            if cap and cap < len(new_distributions):
                distributions = random.sample(new_distributions, cap)
            else:
                distributions = new_distributions

        return [
            MayorAction(name=town.name, people_distribution=list(zip(holders, dist)))
            for dist in distributions
        ]
