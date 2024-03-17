from typing import List

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
from flask_login import (
    LoginManager,
    current_user,
    login_required,
    login_user,
    logout_user,
)

from .engine.actions import *
from .engine.game import Game as GameData
from .models import Game, User, db


def create_app(db_uri="sqlite:///:memory:", url_prefix=""):
    app = Flask(__name__)
    app.jinja_env.auto_reload = True
    app.config["TEMPLATES_AUTO_RELOAD"] = True
    app.config["SQLALCHEMY_DATABASE_URI"] = db_uri
    app.config["SECRET_KEY"] = "your_secret_key"  # Replace with your own secret key
    db.init_app(app)
    flask_bootstrap.Bootstrap5(app)
    login_manager = LoginManager()
    login_manager.init_app(app)

    # Create tables
    with app.app_context():
        db.create_all()

    # @login_manager.user_loader
    # def load_user(user_id):
    #     return User.query.get(int(user_id))

    @login_manager.request_loader
    def load_user_from_request(request: Request):

        paths = request.path.split("/")
        token = paths[1] if paths else None
        user = db.session.query(User).filter_by(token=token).first()

        # print("LOGIN", paths, token, user)

        if user:
            return user

        # finally, return None if both methods did not login the user
        return None

    @app.get("/")
    def main():
        if current_user.is_authenticated:
            return redirect(url_for("game_page", token=current_user.token))
        games = Game.browse()
        return render_template("home.html", games=games)

    @app.get("/<token>")
    def game_page(token):
        current_user = db.session.query(User).filter_by(token=token).first()
        if not current_user:
            flash(f"Authentication Error: your token is not valid.", "danger")
            return redirect(url_for("main"))
        game = current_user.game
        status = (
            400
            if any(
                category == "danger"
                for category, message in get_flashed_messages(with_categories=True)
            )
            else 200
        )
        if game.status == "active":
            gd = GameData.loads(game.dumped_data)
            rev_pseudos = {pseudo: name for name, pseudo in gd.pseudos.items()}
            turn_info = [
                {
                    "name": rev_pseudos[town.name],
                    "pseudo": town.name,
                    "role": town.role,
                    "expected": town.name == gd.expected.name,
                    "is_you": gd.pseudos.get(current_user.name, None) == town.name,
                }
                for town in gd.current_round()
            ]
        else:
            turn_info = []
            gd = None
        return (
            render_template(
                "game_page.html",
                user=current_user,
                game=game,
                gd=gd,
                turn_info=turn_info,
                translation=translation,
                explanation=explanation,
                BUILD_INFO=BUILD_INFO,
            ),
            status,
        )

    @app.get("/<token>/status")
    def game_status(token):
        current_user=db.session.query(User).filter_by(token=token).first()
        game = current_user.game
        # game = Game.query.get(game_id)
        return jsonify(
            {
                "status": game.status,
                "num_players": len(game.users),
                "action_counter": game.action_counter,
                "expected_user": game.expected_user,
            }
        )

    @app.route("/login", methods=["GET", "POST"])
    def login():
        if request.method == "POST":
            username = request.form.get("username")
            password = request.form.get("password")
            user = User.query.filter_by(name=username, password=password).first()
            if user:
                login_user(user)
                return redirect(url_for("game_page", token=user.token))
            else:
                flash("Invalid username or password", "warning")
        user_id = request.args.get("user_id", None)
        user_id = int(user_id) if user_id else None
        user = db.session.get(User, user_id)
        
        return render_template("login.html", name=user.name if user else None)

    @app.get("/fastlogin/<name>")
    def fastlogin(name):
        user = db.session.query(User).filter_by(name=name).first()
        login_user(user)
        return redirect(url_for("game_page", token=user.token))

    @app.post("/new_game")
    def new_game():
        game = Game.add()
        return redirect(url_for("main"))

    @app.post("/join_game/<int:game_id>")
    def join_game(game_id):
        game = db.session.get(Game, game_id)
        if game and game.status == "open":
            username = request.form.get("username")
            password = request.form.get("password")

            # Check if the username is already taken in the game
            if any(user.name == username for user in game.users):
                flash(
                    f"Username '{username}' is already taken in this game. Please choose a different name.",
                    "warning",
                )
                return redirect(url_for("main"))

            user = User.add(username, password, game_id)
            login_user(user)
            return redirect(url_for("game_page", token=user.token))

        flash(f"Error joining game.", "danger")
        return redirect(url_for("main"))

    @app.post("/start_game/<int:game_id>")
    def start_game(game_id):
        game = db.session.get(Game, game_id)
        if game and game.status == "open" and 3 <= len(game.users) <= 5:
            game.start()
            return redirect(url_for("main"))
        return f"Error starting game: {game}", 400

    @app.post("/stop_game/<int:game_id>")
    def stop_game(game_id):
        game = Game.query.get(game_id)
        if game and game.status == "active":
            game.status = "closed"
            db.session.commit()
            return redirect(url_for("main"))
        return "Error stopping game", 400

    @app.post("/delete_game/<int:game_id>")
    def delete_game(game_id):
        game = Game.query.get(game_id)
        if game and game.status == "closed":
            for user in game.users:
                db.session.delete(user)
            db.session.delete(game)
            db.session.commit()
            return redirect(url_for("main"))
        return "Error deleting game", 400

    @app.post("/delete_user/<int:user_id>")
    def delete_user(user_id):
        user = User.query.get(user_id)
        if user:
            db.session.delete(user)
            db.session.commit()
            return redirect(url_for("main"))
        return "Error deleting user", 400

    @app.post("/logout")
    def logout():
        logout_user()
        return redirect(url_for("main"))

    @app.post("/<token>/action/governor")
    def action_governor(token):
        current_user = db.session.query(User).filter_by(token=token).first()
        if not current_user:
            flash(f"Authentication Error: your token is not valid.", "danger")
            return redirect(url_for("main"))
        game = current_user.game
        gd = GameData.loads(game.dumped_data)
        name = gd.pseudos.get(current_user.name)

        try:
            gd.take_action(GovernorAction(name))
            game.updated(gd)
        except AssertionError as err:
            flash(f"Assertion Error: {err}", "danger")
        return redirect(url_for("game_page", token=current_user.token))

    @app.post("/<token>/action/role")
    def action_role(token):
        current_user = db.session.query(User).filter_by(token=token).first()
        if not current_user:
            flash(f"Authentication Error: your token is not valid.", "danger")
            return redirect(url_for("main"))
        game = current_user.game
        gd = GameData.loads(game.dumped_data)
        name = gd.pseudos.get(current_user.name)

        selected_role = request.form.get("role")
        if not selected_role:
            flash("Please select a role.", "danger")
            return redirect(url_for("game_page", token=current_user.token))
        try:
            gd.take_action(RoleAction(name, role=selected_role))
            game.updated(gd)
        except AssertionError as err:
            flash(f"Assertion Error: {err}", "danger")

        return redirect(url_for("game_page", token=current_user.token))

    @app.post("/<token>/action/refuse")
    def action_refuse(token):
        current_user = db.session.query(User).filter_by(token=token).first()
        if not current_user:
            flash(f"Authentication Error: your token is not valid.", "danger")
            return redirect(url_for("main"))
        game = current_user.game
        gd = GameData.loads(game.dumped_data)
        name = gd.pseudos.get(current_user.name)

        try:
            gd.take_action(RefuseAction(name))
            game.updated(gd)
        except AssertionError as err:
            flash(f"Assertion Error: {err}", "danger")
        return redirect(url_for("game_page", token=current_user.token))

    @app.post("/<token>/action/tidyup")
    def action_tidyup(token):
        current_user = db.session.query(User).filter_by(token=token).first()
        if not current_user:
            flash(f"Authentication Error: your token is not valid.", "danger")
            return redirect(url_for("main"))
        game = current_user.game
        gd = GameData.loads(game.dumped_data)
        name = gd.pseudos.get(current_user.name)

        try:
            gd.take_action(TidyUpAction(name))
            game.updated(gd)
        except AssertionError as err:
            flash(f"Assertion Error: {err}", "danger")
        return redirect(url_for("game_page", token=current_user.token))

    @app.post("/<token>/action/builder")
    def action_builder(token):
        current_user = db.session.query(User).filter_by(token=token).first()
        if not current_user:
            flash(f"Authentication Error: your token is not valid.", "danger")
            return redirect(url_for("main"))
        game = current_user.game
        gd = GameData.loads(game.dumped_data)
        name = gd.pseudos.get(current_user.name)

        building_type = request.form.get("building_type")
        extra_person = request.form.get("extra_person", False)

        if not building_type:
            flash("Please select a building to construct.", "warning")
            return redirect(url_for("game_page", token=current_user.token))

        try:
            gd.take_action(
                BuilderAction(
                    name, building_type=building_type, extra_person=extra_person
                )
            )
            game.updated(gd)
        except AssertionError as err:
            flash(f"Assertion Error: {err}", "danger")
        return redirect(url_for("game_page", token=current_user.token))

    @app.route("/<token>/action/captain", methods=["POST"])
    def action_captain(token):
        current_user = db.session.query(User).filter_by(token=token).first()
        if not current_user:
            flash(f"Authentication Error: your token is not valid.", "danger")
            return redirect(url_for("main"))
        game = current_user.game
        gd = GameData.loads(game.dumped_data)
        name = gd.pseudos.get(current_user.name)

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

        return redirect(url_for("game_page", token=current_user.token))

    @app.route("/<token>/action/settler", methods=["POST"])
    def action_settler(token):
        current_user = db.session.query(User).filter_by(token=token).first()
        if not current_user:
            flash(f"Authentication Error: your token is not valid.", "danger")
            return redirect(url_for("main"))
        game = current_user.game
        gd = GameData.loads(game.dumped_data)
        name = gd.pseudos.get(current_user.name)

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

        return redirect(url_for("game_page", token=current_user.token))

    @app.route("/<token>/action/mayor", methods=["POST"])
    def action_mayor(token):
        current_user = db.session.query(User).filter_by(token=token).first()
        if not current_user:
            flash(f"Authentication Error: your token is not valid.", "danger")
            return redirect(url_for("main"))
        game = current_user.game
        gd = GameData.loads(game.dumped_data)
        name = gd.pseudos.get(current_user.name)

        people_distribution = [
            (place, int(workers)) for place, workers in request.form.items()
        ]
        people_distribution.sort(key=lambda place_number: place_number[0] != "home")
        print(people_distribution)

        try:
            gd.take_action(
                MayorAction(name=name, people_distribution=people_distribution)
            )
            game.updated(gd)
        except AssertionError as err:
            flash(f"Assertion Error: {err}", "danger")

        return redirect(url_for("game_page", token=current_user.token))

    @app.post("/<token>/action/craftsman")
    def action_craftsman(token):
        current_user = db.session.query(User).filter_by(token=token).first()
        if not current_user:
            flash(f"Authentication Error: your token is not valid.", "danger")
            return redirect(url_for("main"))
        game = current_user.game
        gd = GameData.loads(game.dumped_data)
        name = gd.pseudos.get(current_user.name)

        selected_good = request.form.get("selected_good")
        if not selected_good:
            flash("Please select a good to produce.", "warning")
            return redirect(url_for("game_page", token=current_user.token))

        try:
            gd.take_action(CraftsmanAction(name, selected_good=selected_good))
            game.updated(gd)
        except AssertionError as err:
            flash(f"Assertion Error: {err}", "danger")

        return redirect(url_for("game_page", token=current_user.token))

    @app.post("/<token>/action/trader")
    def action_trader(token):
        current_user = db.session.query(User).filter_by(token=token).first()
        if not current_user:
            flash(f"Authentication Error: your token is not valid.", "danger")
            return redirect(url_for("main"))
        game = current_user.game
        gd = GameData.loads(game.dumped_data)
        name = gd.pseudos.get(current_user.name)

        selected_good = request.form.get("selected_good")
        if not selected_good:
            flash("Please select a good to sell.", "warning")
            return redirect(url_for("game_page", token=current_user.token))

        try:
            gd.take_action(TraderAction(name, selected_good=selected_good))
            game.updated(gd)
        except AssertionError as err:
            flash(f"Assertion Error: {err}", "danger")

        return redirect(url_for("game_page", token=current_user.token))

    @app.post("/<token>/action/storage")
    def action_storage(token):
        current_user = db.session.query(User).filter_by(token=token).first()
        if not current_user:
            flash(f"Authentication Error: your token is not valid.", "danger")
            return redirect(url_for("main"))
        game = current_user.game
        gd = GameData.loads(game.dumped_data)
        name = gd.pseudos.get(current_user.name)

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

        return redirect(url_for("game_page", token=current_user.token))

    return app


# Translation dictionary (English to Italian)
translation = {
    "ActionType": "Tipo di Azione",
    "Good": "Merce",
    "LargeBuilding": "Palazzo Grande",
    "ProdBuilding": "Impianto di Produzione",
    "Role": "Ruolo",
    "SmallBuilding": "Piccolo Palazzo",
    "Tile": "Segnalino",
    "Building": "Palazzo",
    "builder": "Costruttore",
    "captain": "Capitano",
    "craftsman": "Sovrintendente",
    "governor": "Governatore",
    "mayor": "Sindaco",
    "prospector": "Cercatore d'oro",
    "second_prospector": "Cercatore d'oro",
    "refuse": "rifiutare",
    "role": "ruolo",
    "settler": "Colono",
    "storage": "stoccaggio",
    "terminate": "terminare",
    "tidyup": "riordinare",
    "trader": "Mercante",
    "coffee": "caffè",
    "corn": "granturco",
    "indigo": "indaco",
    "sugar": "zucchero",
    "tobacco": "tabacco",
    "quarry": "cava",
    "city_hall": "municipio",
    "custom_house": "dogana",
    "fortress": "fortezza",
    "guild_hall": "sede della corporazione",
    "residence": "residenza",
    "coffee_roaster": "torrefazione del caffè",
    "indigo_plant": "fabbrica di indaco",
    "small_indigo_plant": "piccola fabbrica di indaco",
    "small_sugar_mill": "piccolo mulino dello zucchero",
    "sugar_mill": "mulino dello zucchero",
    "tobacco_storage": "conservazione del tabacco",
    "construction_hut": "capanna della costruzione",
    "factory": "fabbrica",
    "hacienda": "hacienda",
    "harbor": "porto",
    "hospice": "ospizio",
    "large_market": "grande mercato",
    "large_warehouse": "grande magazzino",
    "office": "ufficio",
    "small_market": "piccolo mercato",
    "small_warehouse": "piccolo magazzino",
    "university": "università",
    "wharf": "molo",
    "coffee_tile": "segnalino del caffè",
    "corn_tile": "segnalino del granturco",
    "indigo_tile": "segnalino dell'indaco",
    "quarry_tile": "segnalino della cava",
    "sugar_tile": "segnalino dello zucchero",
    "tobacco_tile": "segnalino del tabacco",
}

# Explanation dictionary (English to Italian explanation)
explanation = {
    "builder": "Permette di costruire un palazzo, pagando un doblone in meno.",
    "captain": "Bisogna caricare le merci sulle navi per ottenere punti vittoria. Il capitano ottiene 1 PV extra.",
    "craftsman": "Permette di produrre merci in base alle piantagioni occupate. L'artigiano ottiene 1 merce in più.",
    "governor": "Inizia il round scegliendo un ruolo.",
    "mayor": "Permette di prendere coloni e piazzarli sui cerchietti vuoti dei segnalini. Il sindaco ottiene 1 colono extra.",
    "settler": "Permette di piazzare un nuovo segnalino piantagione o cava sull'isola. Il colonizzatore può prendere una cava invece di una piantagione.",
    "trader": "Permette di vendere una merce all'emporio. Il commerciante ottiene 1 doblone extra.",
    "prospector": "Prende un doblone dalla banca.",
    "second_prospector": "Prende un doblone dalla banca.",
    "city_hall": "Palazzo grande. Vale 4 PV più 1 per ogni palazzo viola occupato nella città, incluso se stesso.",
    "custom_house": "Palazzo grande. Vale 4 PV più 1 PV ogni 4 PV ottenuti (dai gettoni, non dai palazzi).",
    "fortress": "Palazzo grande. Vale 4 PV più 1 PV ogni 3 coloni sulla scheda del giocatore.",
    "guild_hall": "Palazzo grande. Vale 4 PV più 1 PV per ogni impianto di produzione piccolo e 2 PV per ogni impianto grande nella città.",
    "residence": "Palazzo grande. Vale 4 PV più bonus in base al numero di segnalini sull'isola: 9 = +4 PV, 10 = +5 PV, 11 = +6 PV, 12 = +7 PV.",
    "coffee_roaster": "Impianto di produzione. Serve per produrre caffè dalle piantagioni di caffè.",
    "indigo_plant": "Impianto di produzione. Serve per produrre indaco dalle piantagioni di indaco.",
    "small_indigo_plant": "Impianto di produzione piccolo. Serve per produrre indaco dalle piantagioni di indaco.",
    "small_sugar_mill": "Impianto di produzione piccolo. Serve per produrre zucchero dalle piantagioni di zucchero.",
    "sugar_mill": "Impianto di produzione. Serve per produrre zucchero dalle piantagioni di zucchero.",
    "tobacco_storage": "Impianto di produzione. Serve per produrre tabacco dalle piantagioni di tabacco.",
    "construction_hut": "Piccolo palazzo. Permette di prendere una cava invece di una piantagione nella fase del colonizzatore.",
    "factory": "Piccolo palazzo. Il proprietario ottiene dobloni in base al numero di tipi di merce prodotti.",
    "hacienda": "Piccolo palazzo. Permette di prendere una piantagione extra dalla pila coperta nella fase del colonizzatore.",
    "harbor": "Piccolo palazzo. Il proprietario ottiene 1 PV extra ogni volta che carica merci sulle navi.",
    "hospice": "Piccolo palazzo. Permette di prendere un colono dalla riserva quando si piazza una nuova piantagione o cava.",
    "large_market": "Piccolo palazzo. Il proprietario ottiene 2 dobloni extra quando vende una merce all'emporio.",
    "large_warehouse": "Piccolo palazzo. Permette di conservare due tipi di merce extra dopo la fase del capitano.",
    "office": "Piccolo palazzo. Permette di vendere una merce già presente nell'emporio. Costa 5 dobloni, occupa 1 lavoratore, vale 2 punti.",
    "small_market": "Piccolo palazzo. Il proprietario ottiene 1 doblone extra quando vende una merce all'emporio.",
    "small_warehouse": "Piccolo palazzo. Permette di conservare un tipo di merce extra dopo la fase del capitano.",
    "university": "Piccolo palazzo. Permette di prendere un colono dalla riserva quando si costruisce un palazzo.",
    "wharf": "Piccolo palazzo. Permette di 'caricare' tutte le merci di un tipo nella riserva come se fossero su una nave, guadagnando i relativi PV.",
}

