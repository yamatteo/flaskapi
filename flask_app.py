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
    
    from database import db
    db.init_app(app)

    import kaitor, rico

    with app.app_context():
        app.register_blueprint(kaitor.bp)
        app.register_blueprint(rico.bp)
        kaitor.db.create_all()
        rico.db.create_all()

    return app


app = create_app()

if __name__ == "__main__":
    app.run(debug=True)
