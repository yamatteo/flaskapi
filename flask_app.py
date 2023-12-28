from flask import Flask, abort, request
from flask_cors import CORS


def create_app():
    app = Flask(__name__)
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///flaskapi.db"
    app.config["SQLALCHEMY_BINDS"] = {
        "kaitor": "sqlite:///kaitor.db",
    }
    CORS(app)

    @app.route("/")
    def main():
        return "The app is running, but for API requests only."

    from kaitor import bp as kaitor_bp, db as kaitor_db

    kaitor_db.init_app(app)
    with app.app_context():
        app.register_blueprint(kaitor_bp)
        kaitor_db.create_all()

    return app


app = create_app()

if __name__ == "__main__":
    app.run(debug=True)
