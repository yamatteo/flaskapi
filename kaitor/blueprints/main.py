import functools

from flask import (Blueprint, flash, g, jsonify, redirect, render_template, request,
                   session, url_for)

from ..models import *


bp = Blueprint('kaitor', __name__, url_prefix='/kaitor/', template_folder="../templates/", static_folder="../static/")
S = db.session 

from . import group 
from . import user

bp.register_blueprint(group.bp)
bp.register_blueprint(user.bp)


@bp.route("/", methods=["GET"])
def main():
    groups = S.query(Group).all()

    return render_template("select_group.html", groups=groups)