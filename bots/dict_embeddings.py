from rico import (
    BUILDINGS,
    COUNTABLES,
    GOODS,
    REGULAR_TILES,
    ROLES,
    TILES,
    NONPRODUCTION_BUILDINGS,
    Board,
    Building,
    GoodsShip,
    Role,
    Tile,
    Town,
)


def embed_role(town: Town) -> int:
    # Ten possibilities, from -1 (No role) to 7 (prospector2)
    return town.role_index
    # for i, role in enumerate(ROLES):
    #     if town.role == role:
    #         return i + 1
    # return 0


def embed_tiles(town: Town) -> dict[Tile, tuple[int, int]]:
    # Values like (0..12, 0..12)
    return { tile: (placed, worked) for tile, placed, worked in zip(TILES, town.placed_tiles, town.worked_tiles)}
    # data = {type: (0, 0) for type in TILES}
    # those_tiles = [tile for tile in town.tiles if tile.type == type]
    # for tile in town.tiles:
    #     built, worked = data[tile.type]
    #     data[tile.type] = built + 1, worked + tile.people
    # return data


def embed_buildings(town: Town) -> dict[Building, tuple[int, int]]:
    # Values like (0..1, 0..3)
    return { (int(info>-1), max(0, info)) for building, info in zip(BUILDINGS, town.buildings_mixed)}
    # data = {type: (0, 0) for type in BUILDINGS}
    # for building in town.buildings:
    #     data[building.type] = (1, building.people)
    # return data


def embed_town(town: Town):
    building_data = embed_buildings(town)
    tiles_data = embed_tiles(town)
    return (
        dict(
            gov=int(town.gov),
            spent_captain=int(town.spent_captain),
            spent_wharf=int(town.spent_wharf),
            role=embed_role(town),
        )
        | {f"{type}_stored": town.count(type) for type in COUNTABLES}
        | {f"{good}_produced": value for good, value in town.production().items()}
        | {f"{type}_built": built for (type, (built, worked)) in building_data.items()}
        | {f"{type}_worked": worked for (type, (built, worked)) in building_data.items()}
        | {f"{type}_built": built for (type, (built, worked)) in tiles_data.items()}
        | {f"{type}_worked": worked for (type, (built, worked)) in tiles_data.items()}
    )

def embed_ship(ship: GoodsShip) -> int:  # Between 0 and 269
    size = ship.size  # Between 4 and 8 included
    what = str(ship.contains())
    type = ({"None": 0}|{type:i+1 for i, type in enumerate(GOODS)})[what] # Between 0 and 5
    amount = ship.count(what)  # Between 0 and 8

    return (size - 4)*54 + type*9 + amount

def embed_board(board: Board, name: str):
    countables = {f"{type}_stored": board.count(type) for type in COUNTABLES}
    tiles = {"unsettled_tiles": len(board.unsettled_tiles), "unsettled_quarries": board.unsettled_quarries} | {
        f"{tile_type}_exposed": board.exposed_tiles.count(tile_type) for tile_type in REGULAR_TILES
    }
    roles = { role: board.roles[i] for i, role in enumerate(ROLES)}
    # roles = { role: (0, 0) for role in ROLES}
    # for role in board.roles:
    #     roles[role.type] = (1, role.money)
    ships = {"people_ship": board.people_ship.people}
    for size, ship in zip(["small", "medium", "large"], board.goods_fleet.values()):
        ships[f"{size}_ship"] = embed_ship(ship)
    market = { f"{type}_sold": board.market.count(type) for type in GOODS }
    buildings = { type: board.unbuilt.count(type) for type in BUILDINGS }

    return countables | roles | tiles | ships | market | buildings