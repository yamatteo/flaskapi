from flask import Flask
from werkzeug.middleware.dispatcher import DispatcherMiddleware
from werkzeug.exceptions import NotFound

import rico


application = Flask(__name__)

application.wsgi_app = DispatcherMiddleware(NotFound(), {
    "/rico": rico.app
})

if __name__ == "__main__":
    application.run(debug=True)
