import json
from pathlib import Path
from typing import List, Mapping

import flask_bootstrap
import pusher
import requests
from flask import (
    Flask,
    Request,
    flash,
    get_flashed_messages,
    jsonify,
    redirect,
    render_template,
    request,
    send_from_directory,
    url_for,
)

from .constants import brief_explanation_dict, explanation_dict, translation_dict
from .engine.actions import *
from .engine.game import Game as GameData
from .engine.game import game_converter
from .models import ActiveGame, DbGame, DbUser, db

active_game: Optional[ActiveGame] = None


def create_app(db_uri="sqlite:///:memory:", url_prefix=""):
    app = Flask(__name__)
    app.jinja_env.auto_reload = True
    app.config["TEMPLATES_AUTO_RELOAD"] = True
    app.config["SQLALCHEMY_DATABASE_URI"] = db_uri
    app.config["SECRET_KEY"] = "your_secret_key"  # Replace with real secret key, maybe
    app.config["ENGINE_FOLDER"] = str(Path(__file__).parent / "dist")
    app.config["TEMPLATES_FOLDER"] = str(Path(__file__).parent / "templates")
    db.init_app(app)
    flask_bootstrap.Bootstrap5(app)

    # Create tables
    with app.app_context():
        db.create_all()

    # Initialize pusher
    pusher_client = pusher.Pusher(
        app_id="1639585",
        key="b0b9c080f9c8ac2e5089",
        secret="cb90bc74caedcf1f7303",
        cluster="eu",
        ssl=True,
    )

    def broadcast(mapping: Mapping, event: str = "game", channel: str = "rico"):
        try:
            pusher_client.trigger(channel, event, mapping)
            print(
                f"PUSHING (to {channel}/{event} - len {len(str(mapping))}):\n",
                str(mapping)[:80],
            )
        except requests.exceptions.ReadTimeout as err:
            print("requests.exceptions.ReadTimeout:", err)

    @app.get("/")
    def main():
        games = db.session.query(DbGame).all()
        return render_template("home.html", games=games), get_status_from_messages()

    # @app.get("/<token>/render")
    # def active_game_render(token):
    #     global active_game
    #     user = db.session.query(DbUser).filter_by(token=token).first()
    #     if not user:
    #         return "ERROR", 400
    #     dbgame = user.dbgame
    #     active_game = dbgame.sync_active_game(active_game)

    #     rev_pseudos = {pseudo: name for name, pseudo in active_game.pseudos.items()}
    #     turn_info = [
    #         {
    #             "name": rev_pseudos[town.name],
    #             "pseudo": town.name,
    #             "role": town.role,
    #             "expected": town.name == active_game.expected.name,
    #             "is_you": active_game.pseudos.get(user.name, None) == town.name,
    #         }
    #         for town in active_game.current_round()
    #     ]

    #     return render_template(
    #             "active_game_subpart.html",
    #             user=user,
    #             # game=dbgame,
    #             # gd=active_game,
    #             active_game = active_game,
    #             # turn_info=turn_info,
    #             # translation=translation_dict,
    #             # explanation=explanation_dict,
    #             # BUILD_INFO=BUILD_INFO,
    #         )

    # @app.post("/<token>/trigger")
    # def trigger(token):
    #     global active_game
    #     user = db.session.query(DbUser).filter_by(token=token).first()
    #     dbgame = user.dbgame
    #     active_game = dbgame.sync_active_game(active_game)
    #     broadcast(asdict(active_game))
    #     return "OK", 200

    # @app.get("/<token>/status")
    # def game_status(token):
    #     user = db.session.query(DbUser).filter_by(token=token).first()
    #     game = user.dbgame
    #     return jsonify(
    #         {
    #             "status": game.status,
    #             "players": str(", ").join(user.name for user in game.users),
    #             "action_counter": game.action_counter,
    #         }
    #     )

    @app.route("/login", methods=["GET", "POST"])
    def login():
        if request.method == "POST":
            username = request.form.get("username")
            password = request.form.get("password")
            user = DbUser.query.filter_by(name=username, password=password).first()
            if user:
                return redirect(url_for("game_page", token=user.token))
            else:
                flash("Invalid username or password", "danger")
        user_id = request.args.get("user_id", None)
        user_id = int(user_id) if user_id else None
        user = db.session.get(DbUser, user_id)

        return render_template("login.html", name=user.name if user else None)

    @app.get("/fastlogin/<pseudo>")
    def fastlogin(pseudo):
        user = db.session.query(DbUser).filter_by(pseudo=pseudo).first()
        return redirect(url_for("game_page", token=user.token))

    @app.post("/new_game")
    def new_game():
        DbGame.new()
        return redirect(url_for("main"))

    @app.post("/join_game/<int:game_id>")
    def join_game(game_id):
        game = db.session.get(DbGame, game_id)
        if game and game.status == "open":
            username = request.form.get("username")
            password = request.form.get("password")

            # Check if the username is already taken in the game
            if any(user.name == username for user in game.users):
                flash(
                    f"Username '{username}' is already taken in this game. Please choose a different name.",
                    "danger",
                )
                return redirect(url_for("main"))

            user = DbUser.new(username, password, game_id)
            return redirect(url_for("game_page", token=user.token))

        flash(f"Error joining game.", "danger")
        return redirect(url_for("main"))

    @app.post("/stop_game/<int:game_id>")
    def stop_game(game_id):
        game = DbGame.query.get(game_id)
        if game and game.status == "active":
            game.status = "closed"
            db.session.commit()
            return redirect(url_for("main"))
        return "Error stopping game", 400

    @app.post("/delete_game/<int:game_id>")
    def delete_game(game_id):
        game = DbGame.query.get(game_id)
        if game and game.status == "closed":
            for user in game.users:
                db.session.delete(user)
            db.session.delete(game)
            db.session.commit()
            return redirect(url_for("main"))
        return "Error deleting game", 400

    @app.post("/delete_user/<int:user_id>")
    def delete_user(user_id):
        user = DbUser.query.get(user_id)
        if user:
            db.session.delete(user)
            db.session.commit()
        else:
            flash("Error deleting user", "danger")
        return redirect(url_for("main"))

    @app.get("/<token>/game_page")
    def game_page(token):
        global active_game
        user = db.session.query(DbUser).filter_by(token=token).first()
        if not user:
            flash(f"Authentication Error: your token is not valid.", "danger")
            return redirect(url_for("main"))
        dbgame = user.dbgame
        active_game = dbgame.sync_active_game(active_game)

        if dbgame.status == "open":
            return (
                render_template(
                    "open_game.html",
                    user=user,
                ),
                get_status_from_messages(),
            )
        elif dbgame.status == "active":
            return (
                render_template(
                    "active_game.html",
                    user=user,
                    active_game=active_game,
                ),
                get_status_from_messages(),
            )
        elif dbgame.status == "closed":
            return (
                render_template(
                    "closed_game.html",
                    user=user,
                ),
                get_status_from_messages(),
            )
        else:
            flash(
                f"Database Error: game status {dbgame.status} is unexpected.", "danger"
            )
            return redirect(url_for("main"))

    @app.get("/<token>/game_data")
    def game_data(token):
        global active_game
        user = db.session.query(DbUser).filter_by(token=token).first()
        if not user:
            flash(f"Authentication Error: your token is not valid.", "danger")
            return redirect(url_for("main"))
        dbgame = user.dbgame
        active_game = dbgame.sync_active_game(active_game)
        return jsonify(
            {
                "active_game": active_game.dumps(),
                "active_game_content": app.jinja_env.get_template(
                    "active_game_content.html"
                ).render(active_game=active_game, user=user, BUILD_INFO=BUILD_INFO),
            }
        )

    @app.post("/<token>/begin")
    def begin(token):
        user = db.session.query(DbUser).filter_by(token=token).first()
        if not user:
            flash(f"Authentication Error: your token is not valid.", "danger")
            return redirect(url_for("main"))
        game = user.dbgame
        if game and game.status == "open" and 3 <= len(game.users) <= 5:
            game.start()
            broadcast({"game_id": user.dbgame.id}, event="action")
            return redirect(url_for("game_page", token=user.token))

    @app.post("/<token>/post_action")
    def post_action(token):
        global active_game
        user = db.session.query(DbUser).filter_by(token=token).first()
        if not user:
            return (
                jsonify({"error": "Authentication Error: your token is not valid."}),
                400,
            )
        dbgame = user.dbgame
        active_game = dbgame.sync_active_game(active_game)
        # print("Received request.data =", request.data)
        posted_action = game_converter.loads(request.data, Action)
        # print("Loaded action is", posted_action)
        try:
            active_game.take_action(posted_action)
            dbgame.update(active_game)  # TODO postpone?
            broadcast({"game_id": dbgame.id}, event="action")
        except AssertionError as err:
            return jsonify({"error": f"Assertion Error: {err}"}), 400
        except GameOver as reason:
            print("GAME OVER.", reason)
            dbgame.set_scores(active_game)
            broadcast({"game_id": dbgame.id}, event="gameover")
        return jsonify({"message": "OK"}), 200

    @app.route("/engine/<filename>")
    def engine_folder(filename):
        return send_from_directory(
            app.config["ENGINE_FOLDER"], filename, as_attachment=False
        )

    @app.route("/templates/<path:filename>")
    def templates_folder(filename):
        return send_from_directory(
            app.config["TEMPLATES_FOLDER"], filename, as_attachment=True
        )

    @app.template_filter()
    def translate(s: str):
        try:
            return translation_dict[s]
        except (KeyError, TypeError):
            return s

    @app.template_filter()
    def parse(s: str):
        try:
            return json.loads(s)
        except:
            print("Parsing error:", s)
            return {}

    @app.template_filter()
    def briefly_explain(s: str):
        try:
            return brief_explanation_dict[s]
        except (KeyError, TypeError):
            return s

    return app


def get_status_from_messages():
    if any(
        category == "danger"
        for category, _ in get_flashed_messages(with_categories=True)
    ):
        return 400
    else:
        return 200
