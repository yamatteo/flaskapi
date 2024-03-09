from flask import Flask, flash, render_template, request, redirect, url_for
import flask_bootstrap
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from .models import db, Game, User

def create_app(db_uri="sqlite:///:memory:", url_prefix=""):
    app = Flask(__name__)
    app.jinja_env.auto_reload = True
    app.config['TEMPLATES_AUTO_RELOAD'] = True
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
        user = User.query.get(user_id)
        game = user.game
        return render_template("game_page.html", user=user, game=game)

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
        game = Game.query.get(game_id)
        if game and game.status == "open":
            username = request.form.get("username")
            password = request.form.get("password")
            user = User.add(username, password, game_id)
            login_user(user)
            return redirect(url_for("game_page", user_id=user.id))
        return "Error joining game", 400

    @app.post("/start_game/<int:game_id>")
    def start_game(game_id):
        game = Game.query.get(game_id)
        if game and game.status == "open" and 3 <= len(game.users) <= 5:
            game.status = "active"
            db.session.commit()
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

    return app