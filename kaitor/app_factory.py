from flask import Flask, render_template, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timedelta
import random
import flask_bootstrap
from models import db, Group, User


def create_app(db_uri="sqlite:///:memory:"):
    app = Flask(__name__)
    app.config["SQLALCHEMY_DATABASE_URI"] = db_uri
    db.init_app(app)
    flask_bootstrap.Bootstrap5(app)
    S = db.session 

    # Create tables
    with app.app_context():
        db.create_all()
    
    import blueprints.group 
    import blueprints.user

    app.register_blueprint(blueprints.group.bp)
    app.register_blueprint(blueprints.user.bp)


    @app.route("/", methods=["GET"])
    def main():
        groups = S.query(Group).all()

        return render_template("select_group.html", groups=groups)


    # Middleware to check user credentials in each request
    def authenticate_user(username, password):
        user = User.query.filter_by(name=username).first()

        # If the user doesn't exist or has a password and it doesn't match, authentication fails
        if user is None or (user.password is not None and user.password != password):
            return None

        return user


    # Endpoint to set a new password for a user with no password
    @app.route("/set_password", methods=["POST"])
    def set_password():
        data = request.get_json()
        username = data.get("username")
        new_password = data.get("new_password")
        token = data.get("token")

        user = User.query.filter_by(name=username, token=token, password=None).first()

        if user:
            user.password = new_password
            db.session.commit()
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


    # Endpoint to trigger the comparison after the due date
    @app.route("/compare_solutions", methods=["POST"])
    def compare_solutions():
        data = request.get_json()
        username = data.get("username")
        password = data.get("password")
        better_solution_id = data.get("better_solution_id")
        worse_solution_id = data.get("worse_solution_id")
        motivation = data.get("motivation")

        user = authenticate_user(username, password)
        if not user:
            return jsonify({"error": "Invalid credentials"}), 401

        due_comparison = (
            db.session.query(DueComparison)
            .filter_by(user_id=user.id, first_solution_id=better_solution_id)
            .first()
        )
        if not due_comparison:
            due_comparison = (
                db.session.query(DueComparison)
                .filter_by(user_id=user.id, second_solution_id=better_solution_id)
                .first()
            )
        if not due_comparison:
            return jsonify({"error": "No due comparison"}), 410

        if not (
            (
                (due_comparison.first_solution_id, due_comparison.second_solution_id)
                == (worse_solution_id, better_solution_id)
            )
            or (
                (due_comparison.first_solution_id, due_comparison.second_solution_id)
                == (better_solution_id, worse_solution_id)
            )
        ):
            return jsonify({"error": "Not the right due comparison"}), 420

        comparison = (
            db.session.query(Comparison)
            .filter_by(
                user_id=user.id,
                better_solution_id=better_solution_id,
                worse_solution_id=worse_solution_id,
            )
            .first()
        )

        if comparison:
            return jsonify({"error": "Already compared"}), 430

        comparison = Comparison(
            user_id=user.id,
            better_solution_id=better_solution_id,
            worse_solution_id=worse_solution_id,
            motivation=motivation,
        )

        db.session.add(comparison)
        db.session.delete(due_comparison)

        return jsonify(
            {
                "message": "Comparison stored.",
            }
        )


    @app.route("/authenticate", methods=["POST"])
    def authenticate():
        data = request.get_json()
        username = data.get("username")
        password = data.get("password", None)

        u = authenticate_user(username, password)

        return jsonify({"token": u.token})


    @app.route("/<token>", methods=["GET"])
    def user_main(token):
        user = S.query(User).filter_by(token=token).first()
        groups = [m.group for m in S.query(Membership).filter_by(user_id=user.id)]
        problems = set()

        past_due_problems = [
            dp
            for dp in S.query(DueProblem).filter(
                DueProblem.group_id.in_([g.id for g in groups]),
                DueProblem.due_date < datetime.now(),
            )
        ]

        solved_due_problems = [
            dp
            for dp in S.query(DueProblem).filter(
                DueProblem.group_id.in_([g.id for g in groups]),
                DueProblem.due_date > datetime.now(),
            )
            if (
                S.query(Solution)
                .filter_by(user_id=user.id, problem_id=dp.problem_id)
                .first()
                is not None
            )
        ]

        unsolved_due_problems = [
            dp
            for dp in S.query(DueProblem).filter(
                DueProblem.group_id.in_([g.id for g in groups]),
                DueProblem.due_date > datetime.now(),
            )
            if (
                S.query(Solution)
                .filter_by(user_id=user.id, problem_id=dp.problem_id)
                .first()
                is None
            )
        ]

        for g in groups:
            for dp in S.query(DueProblem).filter_by(group_id=g.id):
                problems.add((dp.due_date, dp.problem))

        problems = [
            {"text": dp.problem.text, "due_date": dp.due_date, "id": dp.problem_id}
            for g in groups
            for dp in S.query(DueProblem)
            .filter_by(group_id=g.id)
            .filter(DueProblem.due_date > datetime.now())
        ]
        return render_template(
            "user_main.html",
            user=user,
            past_due_problems=past_due_problems,
            solved_due_problems=solved_due_problems,
            unsolved_due_problems=unsolved_due_problems,
        )


    @app.route("/<token>/solve/<problem_id>", methods=["GET"])
    def user_solve(token, problem_id):
        user = S.query(User).filter_by(token=token).first()
        group_ids = [m.group.id for m in S.query(Membership).filter_by(user_id=user.id)]
        due_problem = (
            S.query(DueProblem)
            .filter(DueProblem.group_id.in_(group_ids), DueProblem.problem_id == problem_id)
            .first()
        )
        too_old = due_problem.due_date < datetime.now()
        problem = S.get(Problem, problem_id)

        solution = (
            S.query(Solution).filter_by(user_id=user.id, problem_id=problem.id).first()
        )

        return render_template(
            "user_solve.html", user=user, problem=problem, solution=solution, too_old=too_old
        )


    @app.route("/<token>/submit_solution/<problem_id>", methods=["POST"])
    def user_submit(token, problem_id):
        data = request.get_json()
        user = S.query(User).filter_by(token=token).first()
        problem = S.get(Problem, problem_id)
        solution_text = data.get("solution_text")

        if not user:
            return jsonify({"error": "Invalid credentials"}), 401
        if not problem:
            return jsonify({"error": "Problem not found"}), 404

        # Check if the submission is before the due date
        groups = [m.group for m in user.memberships]
        for g in groups:
            due_problem = (
                S.query(DueProblem).filter_by(group_id=g.id, problem_id=problem.id).first()
            )
            if due_problem and datetime.now() < due_problem.due_date:
                break
        else:
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



    return app
