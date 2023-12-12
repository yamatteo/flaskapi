from rico import (BUILDINGS, COUNTABLES, GOODS, ROLES, TILES,
                  Board, GoodsShip, Town)


def embed(board: Board, name: str):
    countables = [board.count(kind) for kind in COUNTABLES]
    tiles = [len(board.unsettled_tiles), board.unsettled_quarries] + [
        board.exposed_tiles.count(tile_type) for tile_type in GOODS
    ]
    roles_money = board.roles
    # roles_money = [-1 for _ in ROLES]
    # for role in board.roles:
    #     roles_money[ROLES.index(role.type)] = role.money
    ships = [board.people_ship.people]
    for ship in board.goods_fleet.values():
        ships.extend(embed_ship(ship))
    market = [board.market.count(kind) for kind in GOODS]
    buildings = [board.unbuilt.count(kind) for kind in BUILDINGS]
    towns = []
    for town in board.town_round_from(name):
        towns.extend(embed_town(town))

    return countables + roles_money + tiles + ships + market + buildings + towns


def embed_town(town: Town):
    data = [town.gov, town.spent_captain, town.spent_wharf] + [
        town.count(kind) for kind in COUNTABLES
    ]
    data.append(town.role_index)
    # for role in ROLES:
    #     data.append(int(town.role == role))
    
    data.extend(town.placed_tiles)
    data.extend(town.worked_tiles)
    # for tile_type in TILES:
    #     those_tiles = [tile for tile in town.tiles if tile.type == tile_type]
    #     data.append(len(those_tiles))
    #     data.append(sum(tile.people for tile in those_tiles))
    data.extend(town.buildings_mixed)
    # workers = {building.type: building.people for building in town.buildings}
    # for building_type in BUILDINGS:
    #     data.append(workers.get(building_type, -1))
    return data


def embed_ship(ship: GoodsShip):
    return [ship.size] + [ship.count(kind) for kind in GOODS]