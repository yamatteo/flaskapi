from rico import (BUILDINGS, COUNTABLES, GOODS, REGULAR_TILES, ROLES, TILES, NONPRODUCTION_BUILDINGS, Board, BuildingType, GoodsShip, Role, TileType, Town)

def embed_role(town: Town) -> int:
    # Ten possibilities, from 0 (No role) to 9 (prospector2)
    for i, role in enumerate(ROLES):
        if town.role == role:
            return i+1
    return 0

def embed_tiles(town: Town, type: TileType, full: bool=False) -> int:
    # Between 0 and 12 included
    those_tiles = [tile for tile in town.tiles if tile.type == type]
    if full:
        return sum(tile.people for tile in those_tiles)
    else:
        return len(those_tiles)

def embed_buildings(town: Town, type: BuildingType, full = False) -> int:
    # Between 0 and 3 included
    for building in town.buildings:
        if type==building.type:
            return building.people if full else 1
    return 0

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
    return dict(
        gov=int(town.gov),
        spent_captain = int(town.spent_captain),
        spent_wharf = int(town.spent_wharf),
        role = embed_role(town),
        tiles = { type: embed_tiles(town, type) for type in TILES },
        active_tiles = { type: embed_tiles(town, type, full=True) for type in TILES },
        production = town.production(),

    )