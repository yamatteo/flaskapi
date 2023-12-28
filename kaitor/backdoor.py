from app_factory import create_app

app = create_app(db_uri="sqlite:///site.db")

from models import *

app.app_context().__enter__()