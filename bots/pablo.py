from random import sample
from typing import Sequence

import numpy as np
from bots.distribution import WORK_LABELS, WorkPriority
from reactions import Action
from reactions.mayor import MayorAction
from reactions.terminate import TerminateAction
from rico import Board
from rico.constants import (
    BUILDINFO,
    BUILDINGS,
    COUNTABLES,
    GOODS,
    NONPRODUCTION_BUILDINGS,
    REGULAR_TILES,
    ROLES,
    STANDARD_BUILDINGS,
    TILES,
)
from rico.ships import GoodsShip
from rico.towns import Town


class Pablo:
    def __init__(self, name: str, depth: int = 1):
        self.name = name
        self.depth = depth

    def decide(self, board: Board, actions: list[Action], verbose=False) -> Action:
        if isinstance(actions[0], MayorAction):
            return self.decide_mayor(board, actions)
        
        choices = actions[0].possibilities(board)
        if len(choices) == 1:
            return choices[0]

        selected_action, _ = minimax(
            name=self.name, board=board, actions=actions, depth=self.depth, choices=choices, verbose=verbose
        )
        return selected_action
    
    def decide_mayor(self, board: Board, actions: list[Action]) -> Action:
        expected = actions[0]
        assert isinstance(expected, MayorAction)
        assert expected.name == self.name
        town = board.towns[self.name]
        available_workers = town.total_people
        holders = [
            "home",
            *[tile.type for tile in town.tiles],
            *[building.type for building in town.buildings],
        ]
        distribution = WorkPriority(range(len(WORK_LABELS))).distribute(available_workers, holders)
        return MayorAction(name=self.name, people_distribution=distribution)




def embed(board: Board, name: str):
    countables = [board.count(kind) for kind in COUNTABLES]
    tiles = [len(board.unsettled_tiles), board.unsettled_quarries] + [
        board.exposed_tiles.count(tile_type) for tile_type in REGULAR_TILES
    ]
    ships = [board.people_ship.people]
    for ship in board.goods_fleet.values():
        ships.extend(embed_ship(ship))
    market = [board.market.count(kind) for kind in GOODS]
    buildings = [board.unbuilt.count(kind) for kind in BUILDINGS]
    towns = []
    for town in board.town_round_from(name):
        towns.extend(embed_town(town))

    return countables + tiles + ships + market + buildings + towns


def embed_town(town: Town):
    data = [int(town.gov), int(town.spent_captain), int(town.spent_wharf)] + [
        town.count(kind) for kind in COUNTABLES
    ]
    for role in ROLES:
        data.append(int(town.role == role))
    for tile_type in TILES:
        those_tiles = [tile for tile in town.tiles if tile.type == tile_type]
        data.append(len(those_tiles))
        data.append(sum(tile.people for tile in those_tiles))
    workers = {building.type: building.people for building in town.buildings}
    for building_type in BUILDINGS:
        data.append(workers.get(building_type, -1))
    return data


def embed_ship(ship: GoodsShip):
    return [ship.size] + [ship.count(kind) for kind in GOODS]

def embed_mayor(town: Town):
    data = []
    # 6 x 4
    for tile_type in TILES:
        for amount in range(4):
            data.append(int(town.count_farmers(tile_type) > amount))
    # 
    for build_type in BUILDINGS:
        space = BUILDINFO[build_type]["space"]
        for num_workers in range(space):
            data.append(int(town.count_workers(build_type) > num_workers))
    return data
