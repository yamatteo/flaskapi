from random import choice
from rico import BUILDINGS, COUNTABLES, GOODS, ROLES, SHIPABLES, TILES
from rico.towns import Town
from rico.reactions import possibilities
from rico.ships import GoodsShip

def project_ship(ship: GoodsShip):
    return [ ship.size or 0 ] + [ ship.count(kind) for kind in SHIPABLES ]

def project_player(p: Town):
    data = [int(p.gov), int(p.spent_captain), int(p.spent_wharf)] + [ p.count(kind) for kind in COUNTABLES]
    for role in ROLES:
        data.append(int(p.role == role))
    for tile_type in TILES:
        data.append( sum(tile.people for tile in p.tiles if tile.type == tile_type) )
        data.append( len([tile for tile in p.tiles if tile.type == tile_type]))
    workers = { b.type: b.people for b in p.buildings }
    for b_type in BUILDINGS:
        data.append(workers.get(b_type, -1))
    return data

class Pluto:
    def __init__(self, name: str = "Bot Pluto"):
        self.name = name

    def decide(self, game):
        assert game.expected_player.name == self.name, "It's not my turn."
        projection = self.project(game, self.name)
        return max(
            possibilities(game),
            key=lambda action: self.evaluate(game.project_action(action)),
        )

    def evaluate(self, player):
        value = (
            player.count("points")
            + (
                player.count("money")
                + player.count("corn")
                + player.count("indigo")
                + player.count("sugar")
                + player.count("tobacco")
                + player.count("coffee")
            )
            / 3
            + player.count("people") / 6
        )

        # Buildings
        value += sum(building.tier for building in player.buildings)

        # Active buildings
        value += sum(
            int(player.priviledge(building_type))
            for building_type in [
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
            ]
        )

        # Production
        good_value = dict(corn=0.5, indigo=0.6, sugar=0.7, tobacco=0.8, coffee=0.9)
        value += sum(
            good_value[good] * amount for (good, amount) in player.production().items()
        )

        # Large buildings
        if player.priviledge("guild_hall"):
            for building in player.buildings:
                if building.type in ["small_indigo_plant", "small_sugar_mill"]:
                    value += 1
                if building.type in [
                    "coffee_roaster",
                    "indigo_plant",
                    "sugar_mill",
                    "tobacco_storage",
                ]:
                    value += 2
        if player.priviledge("residence"):
            occupied_tiles = len(
                [tile for tile in player.tiles if tile.count("people") >= 1]
            )
            value += max(4, occupied_tiles - 5)
        if player.priviledge("fortress"):
            value += player.total_people // 3
        if player.priviledge("custom_house"):
            value += player.count("points") // 4
        if player.priviledge("city_hall"):
            value += len(
                [
                    building
                    for building in player.buildings
                    if building.type
                    not in [
                        "small_indigo_plant",
                        "small_sugar_mill",
                        "coffee_roaster",
                        "indigo_plant",
                        "sugar_mill",
                        "tobacco_storage",
                    ]
                ]
            )

        return value
    
    def project(self, game, player_name):
        countables = [ game.count(kind) for kind in COUNTABLES ]
        tiles = [ len(game.unsettled_tiles), game.unsettled_quarries ] + [ game.exposed_tiles.count(tile_type) for tile_type in TILES if tile_type != "quarry" ]
        ships = [ game.people_ship.people ] + [ n for ship in game.goods_ships.values() for n in project_ship(ship) ]
        market = [ game.market.count(kind) for kind in GOODS ]
        buildings = [ game.unbuilt.count(kind) for kind in BUILDINGS]
        players = [ n for _player in game.player_round_from(player_name) for n in project_player(_player)]
        return countables + tiles + ships + market + buildings + players