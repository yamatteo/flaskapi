# from .models import db
# from .blueprints import bp

from .app_factory import create_app
from pathlib import Path

app = create_app(db_uri="sqlite:///rico.db")