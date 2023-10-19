from random import choice
from game.reactions import possibilities


class Quentin:
    def __init__(self, name: str = "Bot Quentin"):
        self.name = name

    def decide(self, game):
        assert game.expected_player.name == self.name, "It's not my turn."
        choices = possibilities(game)
        
        values = { i:self.evaluate(game.project_action(action)) for i, action in enumerate(choices) }
        best = max(values, key=values.get)
        return choices[best]
    
    def evaluate(self, game):
        player = game.players[self.name]

        value = (
            player.count("points")
            + (player.count("money") ** 0.5
            + 0.5*player.count("corn")
            + 0.6*player.count("indigo")
            + 0.7*player.count("sugar")
            + 0.8*player.count("tobacco")
            + 0.9*player.count("coffee")
            + player.count("people") / 2)/3
        )

        # Buildings
        value += sum(building.tier for building in player.buildings)

        value += len(player.tiles) / 4

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
        good_value = dict(
            corn=0.5,
            indigo=0.6,
            sugar=0.7,
            tobacco=0.8,
            coffee=0.9
        )
        value += sum( good_value[good] * amount for (good, amount) in player.production().items())

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
