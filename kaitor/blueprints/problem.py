import functools
from datetime import datetime

from flask import Blueprint, jsonify, redirect, render_template, request, url_for

from ..models import *

bp = Blueprint("problem", __name__, url_prefix="/p/<problem_id>/")


@bp.route("/", methods=["GET"])
def main(token, problem_id):
    user = S.query(User).filter_by(token=token).first()
    problem = S.get(Problem, problem_id)
    due_solution = (
        S.query(DueSolution)
        .filter(DueSolution.user_id == user.id, DueSolution.problem_id == problem.id)
        .first()
    )
    solution_open = due_solution and due_solution.date > datetime.now()

    if user is None or problem is None or due_solution is None:
        return redirect(url_for("kaitor.user.main", token=token))

    solution = (
        S.query(Solution).filter_by(user_id=user.id, problem_id=problem.id).first()
    )

    due_comparison = (
        S.query(DueComparison)
        .filter(
            DueComparison.user_id == user.id,
            DueComparison.problem_id == problem.id,
        )
        .first()
    )
    comparison_open = due_comparison and due_comparison.date > datetime.now()
    comparison = (
        S.query(Comparison).filter_by(user_id=user.id, problem_id=problem.id).first()
    )
    if comparison_open:
        left_id, right_id = due_comparison.others.split(";")
        comparison_open = dict(
            left_id=int(left_id),
            right_id=int(right_id),
            left_solution=S.query(Solution)
            .filter_by(user_id=left_id, problem_id=problem.id)
            .first(),
            right_solution=S.query(Solution)
            .filter_by(user_id=right_id, problem_id=problem.id)
            .first(),
            better_solution=comparison.better if comparison else None,
            worse_solution=comparison.worse if comparison else None,
            motivation=comparison.motivation if comparison else "",
            left_better=(comparison.better == int(left_id)) if comparison else False,
            right_better=(comparison.better == int(right_id)) if comparison else False,
        )

    positive_inbound_comparisons = S.query(Comparison).filter_by(problem_id=problem.id, better=user.id).all()
    negative_inbound_comparisons = S.query(Comparison).filter_by(problem_id=problem.id, worse=user.id).all()

    return render_template(
        "user_solve.html",
        user=user,
        problem=problem,
        solution=solution,
        solution_open=solution_open,
        comparison=comparison,
        comparison_open=comparison_open,
        positive_inbound_comparisons=positive_inbound_comparisons,
        negative_inbound_comparisons=negative_inbound_comparisons,
    )


@bp.route("/submit/", methods=["POST"])
def submit(token, problem_id):
    data = request.get_json()
    user = S.query(User).filter_by(token=token).first()
    problem = S.get(Problem, problem_id)
    solution_text = data.get("solution_text")

    if not user:
        return jsonify({"error": "Invalid credentials"}), 401
    if not problem:
        return jsonify({"error": "Problem not found"}), 404

    # Check if the submission is before the due date
    due_solution = (
        S.query(DueSolution)
        .filter(DueSolution.user_id == user.id, DueSolution.problem_id == problem.id)
        .first()
    )

    if due_solution.date < datetime.now():
        return jsonify({"error": "Submission past due date"}), 400

    solution = (
        S.query(Solution).filter_by(user_id=user.id, problem_id=problem.id).first()
    )

    if solution and not solution_text:
        S.delete(solution)

    elif not solution and not solution_text:
        return jsonify({"error": "Solution should contains something"}), 400

    elif solution_text and solution is None:
        solution = Solution(
            user_id=user.id, problem_id=problem.id, solution_text=solution_text
        )
        S.add(solution)
    else:
        solution.solution_text = solution_text
    S.commit()

    return jsonify({"message": "Solution updated"})


@bp.route("/compare/", methods=["POST"])
def compare(token, problem_id):
    user = S.query(User).filter_by(token=token).first()
    problem = S.get(Problem, problem_id)
    data = request.get_json()
    left_is_better = bool(data.get("left_is_better", False))
    right_is_better = bool(data.get("right_is_better", False))
    motivation = data.get("motivation")
    if not user:
        return jsonify({"error": "Invalid credentials"}), 401
    if not problem:
        return jsonify({"error": "Problem not found"}), 404

    due_comparison = (
        S.query(DueComparison).filter_by(user_id=user.id, problem_id=problem.id).first()
    )
    comparison_open = due_comparison and due_comparison.date > datetime.now()
    left_id, right_id = due_comparison.others.split(";")
    if not comparison_open:
        return (
            jsonify(
                {"error": f"Comparison of {problem.short} is not open for {user.name}."}
            ),
            400,
        )

    if not (motivation and (left_is_better or right_is_better)):
        return (
            jsonify({"error": f"A comparison needs a winner and a motivation."}),
            400,
        )

    comparison = (
        S.query(Comparison).filter_by(user_id=user.id, problem_id=problem.id).first()
    )
    better = left_id if left_is_better else right_id
    worse = right_id if left_is_better else left_id
    if not comparison:
        comparison = Comparison(
            user_id=user.id,
            problem_id=problem.id,
            better=better,
            worse=worse,
            motivation=motivation,
        )
        S.add(comparison)
    else:
        comparison.better = better
        comparison.worse = worse
        comparison.motivation = motivation
    S.commit()
    print(S.query(Comparison).all())
    return jsonify({"message": "Comparison updated"})
