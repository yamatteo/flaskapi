from typing import List, Mapping

import flask_bootstrap
from flask import (
    Flask,
    Request,
    flash,
    get_flashed_messages,
    jsonify,
    redirect,
    render_template,
    request,
    url_for,
)
import pusher
import requests

from .engine.actions import *
from .engine.game import Game as GameData, game_converter
from .models import DbGame, DbUser, ActiveGame, db
from .constants import translation_dict, explanation_dict


def create_app(db_uri="sqlite:///:memory:", url_prefix=""):
    app = Flask(__name__)
    app.jinja_env.auto_reload = True
    app.config["TEMPLATES_AUTO_RELOAD"] = True
    app.config["SQLALCHEMY_DATABASE_URI"] = db_uri
    app.config["SECRET_KEY"] = "your_secret_key"  # Replace with real secret key, maybe
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

    @app.get("/<token>")
    def game_page(token):
        user = db.session.query(DbUser).filter_by(token=token).first()
        if not user:
            flash(f"Authentication Error: your token is not valid.", "danger")
            return redirect(url_for("main"))

        dbgame = user.dbgame
        if dbgame.status == "open":
            return (
                render_template(
                    "open_game.html",
                    user=user,
                ),
                get_status_from_messages(),
            )
        elif dbgame.status == "active":
            gd = GameData.loads(dbgame.data)
            rev_pseudos = {pseudo: name for name, pseudo in gd.pseudos.items()}
            turn_info = [
                {
                    "name": rev_pseudos[town.name],
                    "pseudo": town.name,
                    "role": town.role,
                    "expected": town.name == gd.expected.name,
                    "is_you": gd.pseudos.get(user.name, None) == town.name,
                }
                for town in gd.current_round()
            ]
        else:
            turn_info = []
            gd = None
        return (
            render_template(
                "game_page.html",
                user=user,
                game=dbgame,
                gd=gd,
                turn_info=turn_info,
                translation=translation_dict,
                explanation=explanation_dict,
                BUILD_INFO=BUILD_INFO,
            ),
            get_status_from_messages(),
        )

    @app.get("/<token>/status")
    def game_status(token):
        user = db.session.query(DbUser).filter_by(token=token).first()
        game = user.dbgame
        return jsonify(
            {
                "status": game.status,
                "players": str(", ").join(user.name for user in game.users),
                "action_counter": game.action_counter,
            }
        )

    @app.route("/login", methods=["GET", "POST"])
    def login():
        if request.method == "POST":
            username = request.form.get("username")
            password = request.form.get("password")
            user = DbUser.query.filter_by(name=username, password=password).first()
            if user:
                # login_user(user)
                return redirect(url_for("game_page", token=user.token))
            else:
                flash("Invalid username or password", "danger")
        user_id = request.args.get("user_id", None)
        user_id = int(user_id) if user_id else None
        user = db.session.get(DbUser, user_id)

        return render_template("login.html", name=user.name if user else None)

    @app.get("/fastlogin/<name>")
    def fastlogin(name):
        user = db.session.query(DbUser).filter_by(name=name).first()
        # login_user(user)
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

    @app.post("/<token>/begin")
    def begin(token):
        user = db.session.query(DbUser).filter_by(token=token).first()
        if not user:
            flash(f"Authentication Error: your token is not valid.", "danger")
            return redirect(url_for("main"))
        game = user.dbgame
        if game and game.status == "open" and 3 <= len(game.users) <= 5:
            game.start()
            return redirect(url_for("game_page", token=user.token))

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

    @app.post("/logout")
    def logout():
        return redirect(url_for("main"))

    @app.post("/<token>/post_action")
    def post_action(token):
        user = db.session.query(DbUser).filter_by(token=token).first()
        if not user:
            flash(f"Authentication Error: your token is not valid.", "danger")
            return redirect(url_for("main"))
        game = user.dbgame
        print("TODO sync with active game")
        active_game = GameData.loads(game.data)
        print("pre PA", active_game)
        posted_action = game_converter.loads(request.data, Action)
        print("PA", posted_action)
        try:
            active_game.take_action(posted_action)
            game.update(active_game)  # TODO postpone?
        except AssertionError as err:
            flash(f"Assertion Error: {err}", "danger")
        print("post PA", active_game)
        return redirect(url_for("game_page", token=user.token))

    @app.post("/<token>/action/governor")
    def action_governor(token):
        user = db.session.query(User).filter_by(token=token).first()
        if not user:
            flash(f"Authentication Error: your token is not valid.", "danger")
            return redirect(url_for("main"))
        game = user.game
        gd = GameData.loads(game.dumped_data)
        name = gd.pseudos.get(user.name)

        try:
            gd.take_action(GovernorAction(name))
            game.updated(gd)
        except AssertionError as err:
            flash(f"Assertion Error: {err}", "danger")
        return redirect(url_for("game_page", token=user.token))

    @app.post("/<token>/action/role")
    def action_role(token):
        user = db.session.query(User).filter_by(token=token).first()
        if not user:
            flash(f"Authentication Error: your token is not valid.", "danger")
            return redirect(url_for("main"))
        game = user.game
        gd = GameData.loads(game.dumped_data)
        name = gd.pseudos.get(user.name)

        selected_role = request.form.get("role")
        if not selected_role:
            flash("Please select a role.", "danger")
            return redirect(url_for("game_page", token=user.token))
        try:
            gd.take_action(RoleAction(name, role=selected_role))
            game.updated(gd)
        except AssertionError as err:
            flash(f"Assertion Error: {err}", "danger")

        return redirect(url_for("game_page", token=user.token))

    @app.post("/<token>/action/refuse")
    def action_refuse(token):
        user = db.session.query(User).filter_by(token=token).first()
        if not user:
            flash(f"Authentication Error: your token is not valid.", "danger")
            return redirect(url_for("main"))
        game = user.game
        gd = GameData.loads(game.dumped_data)
        name = gd.pseudos.get(user.name)

        try:
            gd.take_action(RefuseAction(name))
            game.updated(gd)
        except AssertionError as err:
            flash(f"Assertion Error: {err}", "danger")
        return redirect(url_for("game_page", token=user.token))

    @app.post("/<token>/action/tidyup")
    def action_tidyup(token):
        user = db.session.query(User).filter_by(token=token).first()
        if not user:
            flash(f"Authentication Error: your token is not valid.", "danger")
            return redirect(url_for("main"))
        game = user.game
        gd = GameData.loads(game.dumped_data)
        name = gd.pseudos.get(user.name)

        try:
            gd.take_action(TidyUpAction(name))
            game.updated(gd)
        except AssertionError as err:
            flash(f"Assertion Error: {err}", "danger")
        return redirect(url_for("game_page", token=user.token))

    @app.post("/<token>/action/builder")
    def action_builder(token):
        user = db.session.query(User).filter_by(token=token).first()
        if not user:
            flash(f"Authentication Error: your token is not valid.", "danger")
            return redirect(url_for("main"))
        game = user.game
        gd = GameData.loads(game.dumped_data)
        name = gd.pseudos.get(user.name)

        building_type = request.form.get("building_type")
        extra_person = request.form.get("extra_person", False)

        if not building_type:
            flash("Please select a building to construct.", "warning")
            return redirect(url_for("game_page", token=user.token))

        try:
            gd.take_action(
                BuilderAction(
                    name, building_type=building_type, extra_person=extra_person
                )
            )
            game.updated(gd)
        except AssertionError as err:
            flash(f"Assertion Error: {err}", "danger")
        return redirect(url_for("game_page", token=user.token))

    @app.route("/<token>/action/captain", methods=["POST"])
    def action_captain(token):
        user = db.session.query(User).filter_by(token=token).first()
        if not user:
            flash(f"Authentication Error: your token is not valid.", "danger")
            return redirect(url_for("main"))
        game = user.game
        gd = GameData.loads(game.dumped_data)
        name = gd.pseudos.get(user.name)

        selected_ship = int(request.form.get("selected_ship"))
        selected_good = request.form.get("selected_good")

        try:
            gd.take_action(
                CaptainAction(
                    name, selected_ship=selected_ship, selected_good=selected_good
                )
            )
            game.updated(gd)
        except AssertionError as err:
            flash(f"Assertion Error: {err}", "danger")

        return redirect(url_for("game_page", token=user.token))

    @app.route("/<token>/action/settler", methods=["POST"])
    def action_settler(token):
        user = db.session.query(User).filter_by(token=token).first()
        if not user:
            flash(f"Authentication Error: your token is not valid.", "danger")
            return redirect(url_for("main"))
        game = user.game
        gd = GameData.loads(game.dumped_data)
        name = gd.pseudos.get(user.name)

        tile = request.form.get("tile")
        down_tile = request.form.get("down_tile", False)
        extra_person = request.form.get("extra_person", False)

        try:
            gd.take_action(
                SettlerAction(
                    name, tile=tile, down_tile=down_tile, extra_person=extra_person
                )
            )
            game.updated(gd)
        except AssertionError as err:
            flash(f"Assertion Error: {err}", "danger")

        return redirect(url_for("game_page", token=user.token))

    @app.route("/<token>/action/mayor", methods=["POST"])
    def action_mayor(token):
        user = db.session.query(User).filter_by(token=token).first()
        if not user:
            flash(f"Authentication Error: your token is not valid.", "danger")
            return redirect(url_for("main"))
        game = user.game
        gd = GameData.loads(game.dumped_data)
        name = gd.pseudos.get(user.name)
        town = gd.board.towns[name]

        form_data = {
            place: dict(requested=int(requested), placed=0)
            for place, requested in request.form.items()
        }

        distribution = [("home", int(form_data["home"]["requested"]))]

        for tile in town.list_tiles():
            if form_data[tile]["placed"] < form_data[tile]["requested"]:
                distribution.append((tile, 1))
                form_data[tile]["placed"] += 1
            else:
                distribution.append((tile, 0))

        for building in town.list_buildings():
            distribution.append((building, form_data[building]["requested"]))

        print(distribution)

        try:
            gd.take_action(MayorAction(name=name, people_distribution=distribution))
            game.updated(gd)
        except AssertionError as err:
            flash(f"Assertion Error: {err}", "danger")

        return redirect(url_for("game_page", token=user.token))

    @app.post("/<token>/action/craftsman")
    def action_craftsman(token):
        user = db.session.query(User).filter_by(token=token).first()
        if not user:
            flash(f"Authentication Error: your token is not valid.", "danger")
            return redirect(url_for("main"))
        game = user.game
        gd = GameData.loads(game.dumped_data)
        name = gd.pseudos.get(user.name)

        selected_good = request.form.get("selected_good")
        if not selected_good:
            flash("Please select a good to produce.", "warning")
            return redirect(url_for("game_page", token=user.token))

        try:
            gd.take_action(CraftsmanAction(name, selected_good=selected_good))
            game.updated(gd)
        except AssertionError as err:
            flash(f"Assertion Error: {err}", "danger")

        return redirect(url_for("game_page", token=user.token))

    @app.post("/<token>/action/trader")
    def action_trader(token):
        user = db.session.query(User).filter_by(token=token).first()
        if not user:
            flash(f"Authentication Error: your token is not valid.", "danger")
            return redirect(url_for("main"))
        game = user.game
        gd = GameData.loads(game.dumped_data)
        name = gd.pseudos.get(user.name)

        selected_good = request.form.get("selected_good")
        if not selected_good:
            flash("Please select a good to sell.", "warning")
            return redirect(url_for("game_page", token=user.token))

        try:
            gd.take_action(TraderAction(name, selected_good=selected_good))
            game.updated(gd)
        except AssertionError as err:
            flash(f"Assertion Error: {err}", "danger")

        return redirect(url_for("game_page", token=user.token))

    @app.post("/<token>/action/storage")
    def action_storage(token):
        user = db.session.query(User).filter_by(token=token).first()
        if not user:
            flash(f"Authentication Error: your token is not valid.", "danger")
            return redirect(url_for("main"))
        game = user.game
        gd = GameData.loads(game.dumped_data)
        name = gd.pseudos.get(user.name)

        selected_good = request.form.get("selected_good", None)
        small_warehouse_good = request.form.get("small_warehouse_good", None)
        large_warehouse_first_good = request.form.get(
            "large_warehouse_first_good", None
        )
        large_warehouse_second_good = request.form.get(
            "large_warehouse_second_good", None
        )

        try:
            gd.take_action(
                StorageAction(
                    name,
                    selected_good=selected_good,
                    small_warehouse_good=small_warehouse_good,
                    large_warehouse_first_good=large_warehouse_first_good,
                    large_warehouse_second_good=large_warehouse_second_good,
                )
            )
            game.updated(gd)
        except AssertionError as err:
            flash(f"Assertion Error: {err}", "danger")

        return redirect(url_for("game_page", token=user.token))

    @app.template_filter()
    def translate(string):
        try:
            return translation_dict[string]
        except (KeyError, TypeError):
            return string

    return app


def get_status_from_messages():
    if any(
        category == "danger"
        for category, _ in get_flashed_messages(with_categories=True)
    ):
        return 400
    else:
        return 200
