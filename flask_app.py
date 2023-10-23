import hashlib
import os
import secrets
from collections.abc import Mapping, Sequence
from dataclasses import asdict, is_dataclass
from typing import Iterable

import pusher
import requests
from flask import Flask, abort, request
from flask_cors import CORS
from rico import *

def create_app(with_pusher=None):
    app = Flask(__name__)
    CORS(app)
    game = None
    users = {}
    use_pusher = with_pusher or not os.environ.get("NO_PUSHER", False)

    if use_pusher:
        print(" * USING PUSHER")
        pusher_client = pusher.Pusher(
            app_id="1639585",
            key="b0b9c080f9c8ac2e5089",
            secret="cb90bc74caedcf1f7303",
            cluster="eu",
            ssl=True,
        )

        def broadcast(obj, event: str = "game", channel: str = "rico"):
            try:
                obj = serialize(obj)
                pusher_client.trigger(channel, event, obj)
                # print(f"PUSHING (to {channel}/{event} - len {len(str(obj))}):\n", str(obj)[:80])
            except requests.exceptions.ReadTimeout as err:
                print("requests.exceptions.ReadTimeout:", err)
    else:
        print(" * NOT USING PUSHER")
        def broadcast(obj, event: str = "game", channel: str = "rico"):
            try:
                obj = serialize(obj)
                # print(f"WOULD PUSH (to {channel}/{event} - len {len(str(obj))}):\n", str(obj)[:80])
            except requests.exceptions.ReadTimeout as err:
                print("requests.exceptions.ReadTimeout:", err)


    def auth(req):
        access_token = req.headers.get("Authorization", "")
        try:
            _, token = access_token.split()
            name, hex = token.split("~")
            assert users[name]["hex"] == hex
            return users[name]
        except Exception as err:
            return None


    @app.route("/login", methods=["POST"])
    def login():
        nonlocal game, users
        data = request.json
        username = data.get("username")
        password = data.get("password", "pass")
        hash = hashlib.sha256(password.encode("utf-8")).hexdigest()

        if username in users and users[username]["hash"] == hash:
            payload, status = {"access_token": f"{username}~{users[username]['hex']}"}, 200
        elif username in users:
            payload, status = {"error": "Wrong password"}, 401
        else:
            users[username] = {
                "username": username,
                "hash": hash,
                "hex": secrets.token_hex(16),
            }
            payload, status = {"access_token": f"{username}~{users[username]['hex']}"}, 200

        broadcast(game.compress() if game else None if game else None, "game")
        broadcast(users.keys(), "users")
        return payload, status


    @app.route("/start", methods=["POST"])
    def start():
        nonlocal game, users
        players: list[tuple[str, str]] = request.json["players"]
        if game is None:
            game = Game.start_new(users=[ name_type[0] for name_type in players ], intelligences=[ name_type[1] for name_type in players ])
            game._broadcast = broadcast
            broadcast(game.compress() if game else None, "game")
            return {"message": "Game created. Please wait for pusher event.", "game": serialize(game.compress() if game else None)}, 201
        else:
            return {"error": "There is a game going on."}, 400


    @app.route("/action", methods=["POST"])
    def action():
        nonlocal game, users
        try:
            action = specific(**dict(request.json, player_name=auth(request)["username"]))
            game.take_action(action)
            broadcast(game.compress() if game else None, "game")
            return {"message": "Action accepted. Please wait for pusher event.", "game": serialize(game.compress() if game else None)}, 200
        except GameOver as err:
            broadcast(game.compress() if game else None, "game")
            broadcast(err, "game_over")
            return {"message": f"Game over: {err}"}, 200
        except Exception as err:
            # print("ERROR", err)
            return {"error": str(err)}, 400
    
    @app.route("/info", methods=["GET"])
    def info():
        nonlocal game, users
        return {"game": serialize(game.compress() if game else None), "users": serialize(users.keys())}

    @app.route("/erase", methods=["POST"])
    def erase():
        nonlocal game, users
        game = None
        users = {}
        broadcast(game, "game")
        broadcast(users.keys(), "users")
        return {"message": "Everything is erased."}, 200

    return app

app = create_app()

if __name__ == "__main__":
    app.run(debug=True)