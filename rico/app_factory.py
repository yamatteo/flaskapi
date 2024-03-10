import random
import uuid
from typing import List

import flask_bootstrap
from flask import Flask, flash, get_flashed_messages, jsonify, redirect, render_template, request, url_for
from flask_login import (
    LoginManager,
    UserMixin,
    current_user,
    login_required,
    login_user,
    logout_user,
)
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import ForeignKey, Integer, String
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

from .engine.actions import *

from .engine.game import Game as GameData


class Base(DeclarativeBase):
    pass


db = SQLAlchemy(model_class=Base)

class Game(db.Model):
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(80), unique=True, nullable=False)
    status: Mapped[str] = mapped_column(String(8), default="open", nullable=False)
    action_counter: Mapped[int] = mapped_column(Integer, default=0)
    expected_user: Mapped[str] = mapped_column(String(80), nullable=True)
    dumped_data: Mapped[str] = mapped_column(String, nullable=True)

    users: Mapped[List["User"]] = relationship()

    def __repr__(self):
        return f"<Game: {self.name}>"

    @staticmethod
    def generate_random_name():
        # List of plausible South American town names
        towns = [
            "Villarrica",
            "Valparaíso",
            "Santa Cruz",
            "Punta Arenas",
            "Potosí",
            "Maracaibo",
            "Guayaquil",
            "Cuenca",
            "Cuzco",
            "Bariloche",
            "Cartagena",
            "Mendoza",
            "Córdoba",
            "Salta",
            "Ushuaia",
            "Iquitos",
            "Arequipa",
            "Trujillo",
            "Chiclayo",
            "Huaraz",
            "Isla Margarita",
            "Puerto La Cruz",
            "Puerto Cabello",
            "Merida",
            "San Cristóbal",
            "Quito",
            "Guayaquil",
            "Cuenca",
            "Loja",
            "Machala",
            "Manta",
            "San José",
            "Antigua",
            "San Salvador",
            "Tegucigalpa",
            "Managua",
            "Ciudad de Panamá",
            "Cancún",
            "Mérida",
        ]

        # List of country names from South America
        countries = [
            "Argentina",
            "Bolivia",
            "Brasil",
            "Chile",
            "Colombia",
            "Ecuador",
            "Guyana",
            "Paraguay",
            "Perú",
            "Uruguay",
            "Venezuela",
            "Costa Rica",
            "El Salvador",
            "Guatemala",
            "Honduras",
            "Nicaragua",
            "Panamá",
            "México",
        ]
        random_year = random.randint(1578, 1624)
        random_town = random.choice(towns)
        random_country = random.choice(countries)

        return f"{random_town}, {random_country}, {random_year} A.D."

    @classmethod
    def browse(cls, name=None, status=None):
        items = db.session.query(cls)
        if name:
            items = items.filter(cls.name == name)
        if status:
            items = items.filter(cls.status == status)
        return items.all()

    @classmethod
    def add(cls) -> "Game":
        name = None
        while name is None:
            name = cls.generate_random_name()
            prev_game = db.session.query(cls).filter(cls.name == name).first()
            if prev_game is not None:
                name = None
        game = cls(name=name)
        db.session.add(game)
        db.session.commit()
        db.session.refresh(game)
        return game
    
    def updated(self, gd: Optional[GameData] = None) -> "Game":
        if gd is None:
            self.dumped_data = None
            self.expected_user = None
        self.dumped_data = gd.dumps()
        self.expected_user = gd.expected.name
        self.action_counter = len(gd.past_actions)
        db.session.commit()
        db.session.refresh(self)
        return self

    def start(self):
        assert self.status == "open"
        assert 3 <= len(self.users) <= 5
        self.status = "active"
        game_data = GameData.start([user.name for user in self.users])
        self.expected_user = game_data.expected.name
        self.dumped_data = game_data.dumps()
        db.session.commit()


class User(UserMixin, db.Model):
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(80), nullable=False)
    password: Mapped[str] = mapped_column(String(80), nullable=False)
    token: Mapped[str] = mapped_column(String(16), nullable=False)

    game_id: Mapped[int] = mapped_column(ForeignKey("game.id"))

    @property
    def game(self):
        return db.session.get(Game, self.game_id)

    def __repr__(self):
        return f"User[{self.id}]({self.name}, ***, ***, {self.game_id})"

    @classmethod
    def add(cls, name: str, password: str, game_id: int) -> "User":

        user = cls(
            name=name,
            password=password,
            token=uuid.uuid4().hex.upper()[:16],
            game_id=game_id,
        )
        db.session.add(user)
        db.session.commit()
        db.session.refresh(user)
        return user

    def get_id(self):
        return str(self.id)


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

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    @app.get("/")
    def main():
        if current_user.is_authenticated:
            return redirect(url_for("game_page", user_id=current_user.id))
        games = Game.browse()
        return render_template("home.html", games=games)

    @app.get("/<int:user_id>")
    @login_required
    def game_page(user_id):
        user = db.session.get(User, user_id)
        game = user.game
        status = 400 if any( category=="danger" for category, message in get_flashed_messages(with_categories=True)) else 200
        if game.status == "active":
            gd = GameData.loads(game.dumped_data)
            turn_info = [
                {
                    "pseudo": town.name,
                    "role": town.role,
                    "expected": town.name == gd.expected.name,
                    "is_you": gd.pseudos.get(user.name, None) == town.name,
                }
                for town in gd.current_round()
            ]
        else:
            turn_info = []
            gd=None
        return render_template(
            "game_page.html", user=user, game=game, gd=gd, turn_info=turn_info
        ), status

    @app.get("/status/<int:game_id>")
    @login_required
    def game_status(game_id):
        game = Game.query.get(game_id)
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
                return redirect(url_for("game_page", user_id=user.id))
            else:
                flash("Invalid username or password", "warning")
        return render_template("login.html")

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
            return redirect(url_for("game_page", user_id=user.id))

        flash(f"Error joining game.", "danger")
        return redirect(url_for("main"))

    @app.post("/start_game/<int:game_id>")
    def start_game(game_id):
        game = db.session.get(Game, game_id)
        if game and game.status == "open" and 3 <= len(game.users) <= 5:
            game.start()
            return redirect(url_for("main"))
        return "Error starting game", 400

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
    @login_required
    def logout():
        logout_user()
        return redirect(url_for("main"))

    @app.post("/action/governor/<name>")
    @login_required
    def action_governor(name):
        game = current_user.game
        gd = GameData.loads(game.dumped_data)
        if name != gd.pseudos.get(current_user.name):
            flash(f"Mismatch {name} != {gd.pseudos.get(current_user.name)}", "danger")
        else:
            try:
                gd.take_action(GovernorAction(name))
                game.updated(gd)
            except AssertionError as err:
                flash(f"Assertion Error: {err}", "danger")
        return redirect(url_for("game_page", user_id=current_user.id))
    
    @app.post("/action/role/<name>")
    @login_required
    def action_role(name):
        game = current_user.game
        gd = GameData.loads(game.dumped_data)
        if name != gd.pseudos.get(current_user.name):
            flash(f"Mismatch {name} != {gd.pseudos.get(current_user.name)}", "danger")
            return redirect(url_for("game_page", user_id=current_user.id))

        selected_role = request.form.get("role")
        if selected_role:
            gd.take_action(RoleAction(name, role=selected_role))
            game.updated(gd)  
        else:
            flash("Please select a role.", "warning")

        return redirect(url_for("game_page", user_id=current_user.id))
    
    @app.post("/action/builder/<name>")
    @login_required
    def action_builder(name):
        game = current_user.game
        gd = GameData.loads(game.dumped_data)
        if name != gd.pseudos.get(current_user.name):
            flash(f"Mismatch {name} != {gd.pseudos.get(current_user.name)}", "danger")
            return redirect(url_for("game_page", user_id=current_user.id))

        building_type = request.form.get("building_type")
        extra_person = request.form.get("extra_person", False)

        if building_type:
            gd.take_action(BuilderAction(name, building_type=building_type, extra_person=extra_person))
            game.updated(gd) 
        else:
            flash("Please select a building to construct.", "warning")

        return redirect(url_for("game_page", user_id=current_user.id))

    return app
