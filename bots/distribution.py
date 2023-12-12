from copy import deepcopy
import random
from typing import Literal, Sequence, Union

from attr import define

from rico import BUILDINFO, TILES, Board, Building, Tile, enforce
from rico.constants import NONPRODUCTION_BUILDINGS

PeopleHolder = Union[Literal["home"], Tile, Building]
PeopleAssignment = tuple[PeopleHolder, int]
PeopleDistribution = list[PeopleAssignment]

WORK_LABELS = [
    "quarry.1",
    "corn.1",
    "indigo.1",
    "sugar.1",
    "coffee.1",
    "tobacco.1",
    "quarry.2",
    "quarry.3",
    "quarry.4",
    "small_market",
    "hacienda",
    "construction_hut",
    "small_warehouse",
    "hospice",
    "office",
    "large_market",
    "large_warehouse",
    "factory",
    "university",
    "harbor",
    "wharf",
    "guild_hall",
    "residence",
    "fortress",
    "city_hall",
    "custom_house",
    "corn.2",
    "corn.3",
    "corn.4",
    "all_corn",
    "indigo.2",
    "indigo.3",
    "indigo.4",
    "sugar.2",
    "sugar.3",
    "sugar.4",
    "tobacco.2",
    "tobacco.3",
    "coffee.2",
    "from_bottom",
    "all_tiles",
]
STANDARD_WEIGHTS = list(range(len(WORK_LABELS)))

@define
class WorkPriority:
    weights: Sequence[float] = STANDARD_WEIGHTS

    def distribute(self, n: int, holders: Sequence[PeopleHolder]):
        distribution = [(holder, n if holder == "home" else 0) for holder in holders]
        priorities = self.sorted_priorities()
        for priority in priorities:
            distribution = self.safe_move(distribution, priority)
        return distribution

    def safe_move(
        self, distribution: PeopleDistribution, priority: str
    ) -> PeopleDistribution:
        try:
            return unsafe_move(distribution, priority)
        except AssertionError:
            return distribution

    def sorted_priorities(self):
        weights_and_labels = zip(self.weights, WORK_LABELS)
        weights_and_labels = sorted(weights_and_labels)
        return [label for (_, label) in weights_and_labels]


def move_allcorn(distribution: PeopleDistribution):
    length = len(distribution)
    for i in range(1, length):
        _, home = distribution[0]
        type, amount = distribution[i]
        correct_type = type == "corn"
        worker_available = home > 0
        worker_needed = amount < 1
        if correct_type and worker_available and worker_needed:
            distribution[0] = ("home", home - 1)
            distribution[i] = (type, amount + 1)
    return distribution


def move_alltile(distribution: PeopleDistribution):
    length = len(distribution)
    for i in range(1, length):
        _, home = distribution[0]
        type, amount = distribution[i]
        correct_type = type in TILES
        worker_available = home > 0
        worker_needed = amount < 1
        if correct_type and worker_available and worker_needed:
            distribution[0] = ("home", home - 1)
            distribution[i] = (type, amount + 1)
    return distribution


def move_simple_production(
    distribution: PeopleDistribution, required_type, required_amount
):
    distribution = deepcopy(distribution)
    length = len(distribution)
    occupied_tiles = 0
    for i in range(1, length):
        if occupied_tiles >= required_amount:
            break
        # More productio is required

        _, home = distribution[0]
        type, amount = distribution[i]
        
        if type != required_type:
            continue
        # We are looking at a correct tile

        if amount == 1:  # Is the tile worked?
            occupied_tiles += 1
            continue
        # The tile is not worked

        if home > 0:  # Do we have free workers?
            distribution[0] = ("home", home - 1)
            distribution[i] = (type, amount + 1)
            occupied_tiles += 1
    assert occupied_tiles >= required_amount
    return distribution


def move_complex_production(
    distribution: PeopleDistribution, required_type, required_amount
):
    distribution = deepcopy(distribution)
    length = len(distribution)
    occupied_tiles = 0
    occupied_workplace = 0
    acceptable_factories = dict(
        indigo=[
            "indigo_plant",
            "small_indigo_plant",
        ],
        sugar=[
            "sugar_mill",
            "small_sugar_mill",
        ],
        coffee=[
            "coffee_roaster",
        ],
        tobacco=[
            "tobacco_storage",
        ],
    )[required_type]
    for i in range(1, length):
        _, home = distribution[0]
        type, amount = distribution[i]
        
        # Correct tile, needed
        if (type == required_type) and (occupied_tiles < required_amount):
            worker_needed = (amount < 1)
            worker_available = (home > 0)
            if worker_needed and worker_available:
                distribution[0] = ("home", home - 1)
                distribution[i] = (type, amount + 1)
                occupied_tiles += 1
            elif not worker_needed:
                occupied_tiles += 1
        
        # Correct building
        if (type in acceptable_factories):
            space = BUILDINFO[type]["space"]
            occupied_workplace += amount
            while (occupied_workplace < required_amount) and (amount < space) and (home > 0):
                distribution[0] = ("home", home - 1)
                home -= 1
                distribution[i] = (type, amount + 1)
                amount += 1
                occupied_workplace += 1
    production = min(occupied_tiles, occupied_workplace)
    assert production >= required_amount
    return distribution


def move_white(distribution: PeopleDistribution, building_type):
    length = len(distribution)
    for i in range(1, length):
        _, home = distribution[0]
        type, amount = distribution[i]
        if (type != building_type):
            continue
        worker_available = home > 0
        worker_needed = amount < 1
        if worker_available and worker_needed:
            distribution[0] = ("home", home - 1)
            distribution[i] = (type, amount + 1)
    return distribution

def move_final(distribution):
    length = len(distribution)
    for i in reversed(range(1, length)):
        _, home = distribution[0]
        type, amount = distribution[i]
        if type in TILES:
            space = 1
        else:
            space = BUILDINFO[type]["space"]
        while home > 0 and amount < space:
            distribution[0] = ("home", home - 1)
            distribution[i] = (type, amount + 1)
            home -= 1
            amount += 1



    return distribution
        


def unsafe_move(distribution: PeopleDistribution, priority: str) -> PeopleDistribution:
    assert priority in WORK_LABELS
    if priority == "all_tiles":
        return move_alltile(distribution)
    elif priority == "all_corn":
        return move_allcorn(distribution)
    elif priority == "from_bottom":
        return move_final(distribution)
    elif priority in NONPRODUCTION_BUILDINGS:
        return move_white(distribution, priority)
    type, amount = priority.split(".")
    if type in ["corn", "quarry"]:
        return move_simple_production(distribution, type, int(amount))
    else:
        return move_complex_production(distribution, type, int(amount))
