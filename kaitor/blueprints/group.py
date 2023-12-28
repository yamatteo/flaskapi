import functools

from flask import (Blueprint, flash, g, jsonify, redirect, render_template, request,
                   session, url_for)

from ..models import *

bp = Blueprint('group', __name__, url_prefix='/g/<group_id>/')

@bp.route("/")
def select_users(group_id):
    g = S.get(Group, group_id)
    return render_template("select_user.html", group=g, users=g.users)

# Middleware to check user credentials in each request
def authenticate_user(username, password):
    user = User.query.filter_by(name=username).first()

    # If the user doesn't exist or has a password and it doesn't match, authentication fails
    if user is None or (user.password is not None and user.password != password):
        return None

    return user

@bp.route("/authenticate/", methods=["POST"])
def authenticate(group_id):
    data = request.get_json()
    username = data.get("username")
    password = data.get("password", None)

    u = authenticate_user(username, password)

    if u:
        return jsonify({"token": u.token})
    else:
        return jsonify({"error": "Something wrong with authentication"})