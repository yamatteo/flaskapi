from typing import Literal

from attr import define
from rico.exceptions import enforce
from .. import GOODS, GoodType
from rico.reactions.base import Action
from rico.reactions.refuse import RefuseAction

@define
class CaptainAction(Action):
    selected_ship: int
    selected_good: GoodType
    type: Literal["captain"] = "captain"

    def react(action, game):
        enforce(
            game.is_expecting(action),
            f"Now is not the time for {action.player_name} to ships good to the old world.",
        )
        player = game.players[action.player_name]
        ship_size = action.selected_ship
        good = action.selected_good

        # Want to use wharf
        if ship_size == 11:
            enforce(
                player.priviledge("wharf") and not player.spent_wharf,
                "Player does not have a free wharf.",
            )
            player.spent_wharf = True
            amount = player.count(good)
            player.give(amount, good, to=game)
            points = amount
            if player.priviledge("harbor"):
                points += 1
            if player.role == "captain" and not player.spent_captain:
                points += 1
                player.spent_captain = True
            game.give_or_make(points, "points", to=player)

        else:
            # ship_contains = 0
            # ship_contains_class = None
            # for _good in ["coffee", "tobacco", "corn", "sugar", "indigo"]:
            #     if game.goods_ships[ship_size].has(_good):
            #         ship_contains = game.goods_ships[ship_size].count(_good)
            #         ship_contains_class = _good
            # if ship_contains > 0:
            #     enforce(ship_contains < ship_size, "The ship is full.")
            #     enforce(
            #         ship_contains_class == good,
            #         f"The ship contains {ship_contains_class}",
            #     )
            ship = game.goods_ships[ship_size]

            enforce(ship.accepts(good,game.goods_ships.values()), f"Ship {ship_size} cannot accept {good}.")

            amount = min(ship.size - ship.count(good), player.count(good))
            player.give(amount, good, to=game.goods_ships[ship_size])
            points = amount
            if player.priviledge("harbor"):
                points += 1
            if player.role == "captain" and not player.spent_captain:
                points += 1
                player.spent_captain = True
            game.give_or_make(points, "points", to=player)

        if sum(player.count(g) for g in GOODS) > 0:
            game.actions = (
                [action for action in game.actions[1:] if action.type == "captain"]
                + [game.actions[0]]
                + [
                    action
                    for action in game.actions[1:]
                    if action.type != "captain"
                ]
            )
        else:
            game.actions.pop(0)

    @classmethod
    def possibilities(cls, game) -> list["CaptainAction"]:
        assert game.expected_action.type == "captain", f"Not expecting a CaptainAction."
        player = game.expected_player
        actions = []
        for selected_good in GOODS:
            if not player.has(selected_good):
                continue
            if player.priviledge("wharf") and not player.spent_wharf:
                actions.append(CaptainAction(player_name=player.name, selected_good=selected_good, selected_ship=11))
            for ship_size, ship in game.goods_ships.items():
                if ship.accepts(selected_good, game.goods_ships.values()):
                    actions.append(CaptainAction(player_name=player.name, selected_good=selected_good, selected_ship=ship_size))
            

        return [RefuseAction(player_name=player.name)] + actions