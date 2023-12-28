from datetime import datetime
import functools

from flask import (
    Blueprint, flash, g, jsonify, redirect, render_template, request, session, url_for
)

from ..models import *

bp = Blueprint('user', __name__, url_prefix='/u/<token>/')
from . import problem

bp.register_blueprint(problem.bp)

@bp.route("/set_password/", methods=["POST"])
def set_password(token):
    data = request.get_json()
    username = data.get("username")
    new_password = data.get("new_password")

    user = S.query(User).filter_by(name=username, token=token, password=None).first()

    if user:
        user.password = new_password
        S.commit()
        return jsonify({"message": "Password set successfully"})
    else:
        return (
            jsonify(
                {
                    "error": "Invalid username, reset_token, or user already has a password"
                }
            ),
            400,
        )

@bp.route("/", methods=["GET"])
def main(token):
    user = S.query(User).filter_by(token=token).first()


    past_problems = [
        vars(read_problem(ds.problem_id)) | {
            "due_comparison": S.query(DueComparison).filter(
            DueComparison.user_id == user.id,
            DueComparison.problem_id == ds.problem_id,
            DueComparison.date > datetime.now()
        ).first(),
            "comparison": S.query(Comparison).filter(
            Comparison.user_id == user.id,
            Comparison.problem_id == ds.problem_id).first()
        }
        for ds in S.query(DueSolution).filter(
            DueSolution.user_id == user.id,
            DueSolution.date < datetime.now()
        )
    ]

    solved_problems = [
        read_problem(ds.problem_id)
        for ds in S.query(DueSolution).filter(
            DueSolution.user_id == user.id,
            DueSolution.date > datetime.now()
        )
        if (
            S.query(Solution)
            .filter_by(user_id=user.id, problem_id=ds.problem_id)
            .first()
        )
    ]

    unsolved_problems = [
        vars(read_problem(ds.problem_id)) | {"date": ds.date}
        for ds in S.query(DueSolution).filter(
            DueSolution.user_id == user.id,
            DueSolution.date > datetime.now()
        )
        if not (
            S.query(Solution)
            .filter_by(user_id=user.id, problem_id=ds.problem_id)
            .first()
        )
    ]
    
    print("COMPARISON", S.query(Comparison).all())

    return render_template(
        "user_main.html",
        user=user,
        past_problems=past_problems,
        solved_problems=solved_problems,
        unsolved_problems=unsolved_problems,
    )

