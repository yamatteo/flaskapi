import json

import pytest

from game.games import Game
from game.players import Player

players = ["Ada", "Bert", "Carl", "Dan"]
tokens = {}


@pytest.fixture()
def app():
    from flask_app import create_app

    app = create_app(with_pusher=True)

    app.config.update(
        {
            "TESTING": True,
        }
    )

    # other setup can go here

    yield app

    # clean up / reset resources here


@pytest.fixture()
def client(app):
    return app.test_client()


def test_api(client):
    for name in players:
        response = client.post("/login", json={"username": name, "password": "pass"})
        tokens[name] = (response.json).get("access_token")
    # Login players

    # Start game
    resp = client.post("/start")
    assert resp.status_code == 201
    game = (resp.json).get("game")
    names = [first, second, third, fourth] = game["play_order"]

    def post(i, obj):
        if isinstance(i, str):
            name = i
        else:
            name = names[i-1]
        token = tokens[name]
        return client.post("/action", json=obj, headers={"Authorization": f"Bearer: {token}"})

    # First player take settler role
    resp = post(1, {"subclass": "Role", "role": "settler"})
    assert resp.status_code == 200

    # First player take quarry tile
    resp = post(1, {"subclass": "Tile", "tile_subclass": "quarry"})
    assert resp.status_code == 200

    # Second player take exposed tile
    assert post(2, {"subclass": "Tile", "tile_subclass": game["exposed_tiles"][0]["type"]}).status_code == 200

    # Third player take exposed tile
    assert post(3, {"subclass": "Tile", "tile_subclass": game["exposed_tiles"][1]["type"]}).status_code == 200

    # Fourth player take exposed tile
    assert post(4, {"subclass": "Tile", "tile_subclass": game["exposed_tiles"][2]["type"]}).status_code == 200

    # Second player take mayor role
    resp = post(2, {"subclass": "Role", "role": "mayor"})
    assert resp.status_code == 200
    game = Game(**(resp.json).get("game"))

    # Second player place people
    second_player = game.players[second]
    second_player.give(1, "people", to=second_player.tiles[0])
    second_player.give(1, "people", to=second_player.tiles[1])
    assert post(2, {"subclass": "People", "whole_player": second_player.model_dump()}).status_code == 200

    # # Third player place person
    # resp = client.post(
    #     "/action",
    #     json={
    #         "player_name": "Carl",
    #         "whole_player": {
    #             "name": "Carl",
    #             "people": 1,
    #             "goods": {},
    #             "tiles": [{"subclass": "field", "people": 1}],
    #         },
    #     },
    # )
    # assert resp.status_code == 200

    # # Fourth player place person
    # resp = client.post(
    #     "/action",
    #     json={
    #         "player_name": "Dan",
    #         "whole_player": {
    #             "name": "Dan",
    #             "people": 1,
    #             "goods": {},
    #             "tiles": [{"subclass": "pasture", "people": 1}],
    #         },
    #     },
    # )
    # assert resp.status_code == 200

    # # Third player take builder role
    # resp = client.post(
    #     "/action", json={"player_name": "Carl", "role_subclass": "builder"}
    # )
    # assert resp.status_code == 200

    # # Third player build sugar mill
    # resp = client.post(
    #     "/action", json={"player_name": "Carl", "building_subclass": "sugar_mill"}
    # )
    # assert resp.status_code == 200

    # # Fourth player build construction hut
    # resp = client.post(
    #     "/action", json={"player_name": "Dan", "building_subclass": "construction_hut"}
    # )
    # assert resp.status_code == 200

    # # First player build hospice
    # resp = client.post(
    #     "/action", json={"player_name": "Ada", "building_subclass": "hospice"}
    # )
    # assert resp.status_code == 200

    # # Second player build indigo plant
    # resp = client.post(
    #     "/action", json={"player_name": "Bert", "building_subclass": "indigo_plant"}
    # )
    # assert resp.status_code == 200

    # # Fourth player take craftsman role
    # resp = client.post(
    #     "/action", json={"player_name": "Dan", "role_subclass": "craftsman"}
    # )
    # assert resp.status_code == 200

    # # Fourth player produce good
    # resp = client.post("/action", json={"player_name": "Dan", "selected_good": "corn"})
    # assert resp.status_code == 200

    # # Second player take prospector role
    # resp = client.post(
    #     "/action", json={"player_name": "Bert", "role_subclass": "prospector"}
    # )
    # assert resp.status_code == 200

    # # Third player take trader role
    # resp = client.post(
    #     "/action", json={"player_name": "Carl", "role_subclass": "trader"}
    # )
    # assert resp.status_code == 200

    # # Third player trade good
    # resp = client.post("/action", json={"player_name": "Carl", "selected_good": "corn"})
    # assert resp.status_code == 200

    # # Players refuse trade
    # resp = client.post(
    #     "/action", json={"player_name": "Ada", "action_subclass": "refuse"}
    # )
    # assert resp.status_code == 200
    # resp = client.post(
    #     "/action", json={"player_name": "Bert", "action_subclass": "refuse"}
    # )
    # assert resp.status_code == 200
    # resp = client.post(
    #     "/action", json={"player_name": "Dan", "action_subclass": "refuse"}
    # )
    # assert resp.status_code == 200

    # # Fourth player take captain role
    # resp = client.post(
    #     "/action", json={"player_name": "Dan", "role_subclass": "captain"}
    # )
    # assert resp.status_code == 200

    # # Fourth player ship good
    # resp = client.post(
    #     "/action",
    #     json={"player_name": "Dan", "selected_ship": 7, "selected_good": "corn"},
    # )
    # assert resp.status_code == 200

    # # Players refuse shipping
    # resp = client.post(
    #     "/action", json={"player_name": "Ada", "action_subclass": "refuse"}
    # )
    # assert resp.status_code == 200
    # resp = client.post(
    #     "/action", json={"player_name": "Bert", "action_subclass": "refuse"}
    # )
    # assert resp.status_code == 200
    # resp = client.post(
    #     "/action", json={"player_name": "Carl", "action_subclass": "refuse"}
    # )
    # assert resp.status_code == 200
    # resp = client.post(
    #     "/action", json={"player_name": "Dan", "action_subclass": "refuse"}
    # )
    # assert resp.status_code == 200
    assert False
