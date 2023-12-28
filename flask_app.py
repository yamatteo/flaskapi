from flask import Flask, abort, request
from flask_cors import CORS

def create_app():
    app = Flask(__name__)
    CORS(app)

    @app.route("/")
    def main():
        return "The app is running, but for API requests only."
    return app

app = create_app()

if __name__ == "__main__":
    app.run(debug=True)