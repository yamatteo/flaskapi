from itertools import combinations
from typing import Literal
from game.exceptions import enforce
from game.holders import GOODS, GoodType
from game.reactions.base import Action
from game.reactions.refuse import RefuseAction


class StorageAction(Action):
    type: Literal["storage"] = "storage"
    selected_good: GoodType = None
    small_warehouse_good: GoodType = None
    large_warehouse_first_good: GoodType = None
    large_warehouse_second_good: GoodType = None

    def react(action, game):
        enforce(
            game.is_expecting(action),
            f"Now is not the time for {action.player_name} to store its goods.",
        )
        player = game.expected_player
        for good in GOODS:
            if good in [
                action.small_warehouse_good,
                action.large_warehouse_first_good,
                action.large_warehouse_second_good,
            ]:
                continue
            elif good == action.selected_good:
                player.give(max(0, player.count(good) - 1), good, to=game)
            else:
                player.give("all", good, to=game)
        game.actions.pop(0)

    @classmethod
    def possibilities_with_three_warehouses(cls, game) -> list["StorageAction"]:
        assert game.expected_action.type == "storage", f"Not expecting a StorageAction."
        player = game.expected_player
        actions = []
        excess_goods = [good for good in GOODS if player.has(good)]
        if len(excess_goods) > 3:
            for stored_goods in combinations(excess_goods, 3):
                for selected_good in [
                    good for good in excess_goods if good not in stored_goods
                ]:
                    actions.append(
                        StorageAction(
                            player_name=player.name,
                            selected_good=selected_good,
                            small_warehouse_good=stored_goods[0],
                            large_warehouse_first_good=stored_goods[1],
                            large_warehouse_second_good=stored_goods[2],
                        )
                    )
        elif len(excess_goods) == 3:
            actions = [StorageAction(
                            player_name=player.name,
                            selected_good=excess_goods[0],
                            small_warehouse_good=excess_goods[0],
                            large_warehouse_first_good=excess_goods[1],
                            large_warehouse_second_good=excess_goods[2],
                        )]
        elif len(excess_goods) == 2:
            actions = [StorageAction(
                            player_name=player.name,
                            selected_good=excess_goods[0],
                            large_warehouse_first_good=excess_goods[0],
                            large_warehouse_second_good=excess_goods[1],
                        )]
        elif len(excess_goods) == 1:
            actions = [StorageAction(
                            player_name=player.name,
                            selected_good=excess_goods[0],
                            small_warehouse_good=excess_goods[0],
                        )]
        return actions
    

    @classmethod
    def possibilities_with_two_warehouses(cls, game) -> list["StorageAction"]:
        assert game.expected_action.type == "storage", f"Not expecting a StorageAction."
        player = game.expected_player
        actions = []
        excess_goods = [good for good in GOODS if player.has(good)]
        if len(excess_goods) > 2:
            for stored_goods in combinations(excess_goods, 2):
                for selected_good in [
                    good for good in excess_goods if good not in stored_goods
                ]:
                    actions.append(
                        StorageAction(
                            player_name=player.name,
                            selected_good=selected_good,
                            large_warehouse_first_good=stored_goods[0],
                            large_warehouse_second_good=stored_goods[1],
                        )
                    )
        elif len(excess_goods) == 2:
            actions = [StorageAction(
                            player_name=player.name,
                            selected_good=excess_goods[0],
                            large_warehouse_first_good=excess_goods[0],
                            large_warehouse_second_good=excess_goods[1],
                        )]
        elif len(excess_goods) == 1:
            actions = [StorageAction(
                            player_name=player.name,
                            selected_good=excess_goods[0],
                            large_warehouse_first_good=excess_goods[0],
                        )]
        return actions

    @classmethod
    def possibilities_with_one_warehouses(cls, game) -> list["StorageAction"]:
        assert game.expected_action.type == "storage", f"Not expecting a StorageAction."
        player = game.expected_player
        actions = []
        excess_goods = [good for good in GOODS if player.has(good)]
        if len(excess_goods) > 1:
            for stored_goods in combinations(excess_goods, 1):
                for selected_good in [
                    good for good in excess_goods if good not in stored_goods
                ]:
                    actions.append(
                        StorageAction(
                            player_name=player.name,
                            selected_good=selected_good,
                            small_warehouse_good=stored_goods[0],
                        )
                    )
        elif len(excess_goods) == 1:
            actions = [StorageAction(
                            player_name=player.name,
                            selected_good=excess_goods[0],
                            small_warehouse_good=excess_goods[0],
                        )]
        return actions

    @classmethod
    def possibilities_with_no_warehouse(cls, game) -> list["StorageAction"]:
        assert game.expected_action.type == "storage", f"Not expecting a StorageAction."
        player = game.expected_player
        actions = []
        excess_goods = [good for good in GOODS if player.has(good)]
        for selected_good in excess_goods:
            actions.append(
                StorageAction(
                    player_name=player.name,
                    selected_good=selected_good,
                )
            )
        return actions

    @classmethod
    def possibilities(cls, game) -> list["StorageAction"]:
        assert game.expected_action.type == "storage", f"Not expecting a StorageAction."
        player = game.expected_player
        if player.priviledge("large_warehouse") and player.priviledge("small_warehouse"):
            actions = cls.possibilities_with_three_warehouses(game)
        elif player.priviledge("large_warehouse"):
            actions = cls.possibilities_with_two_warehouses(game)
        elif player.priviledge("small_warehouse"):
            actions = cls.possibilities_with_one_warehouses(game)
        else:
            actions = cls.possibilities_with_no_warehouse(game)
        return [RefuseAction(player_name=player.name)] + actions
