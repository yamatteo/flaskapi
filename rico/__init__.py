
from .app_factory import *

app = create_app(db_uri="sqlite:///rico.db")