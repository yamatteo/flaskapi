import json
import unittest
from datetime import datetime, timedelta
from functools import partial
from flask_sqlalchemy import SQLAlchemy

import requests

from app import DueComparison, Problem, Solution, User, app, db
from utils import *


class TestYourApp(unittest.TestCase):
    base_url = "http://127.0.0.1:5500"

    @classmethod
    def setUpClass(cls):
        g1 = add_group("Group 1")
        add_group("Group 2")

        # Create test users
        add_user("User 0")
        u1 = add_user("User 1")
        u2 = add_user("User 2")
        u3 = add_user("User 3")
        edit_user("User 0", password=None)
        edit_user("User 1", password="pass1")
        edit_user("User 2", password="pass2")
        edit_user("User 3", password="pass3")

        add_membership("Group 1", "User 1")
        add_membership("Group 1", "User 2")
        add_membership("Group 1", "User 3")

        p1 = add_problem("### Problem 1.\n\n Find $\\frac{3}{4} + \\frac{2}{3}$.")
        p2 = add_problem("Problem 2")
        p3 = add_problem("### Problem 3.\nVery very old.")

        add_due_problem(datetime.now() + timedelta(days=1), p1.id, g1.id)
        add_due_problem(datetime.now() + timedelta(days=1), p2.id, g1.id)
        add_due_problem(datetime.now() - timedelta(days=2), p3.id, g1.id)

        add_solution(u1.id, p3.id, "My good solution.")
        add_solution(u2.id, p3.id, "A middle solution.")
        add_solution(u3.id, p3.id, "Some bad solution.")

        settle()

    def ensure_solution(self, username, problem_text, solution_text):
        with app.app_context():
            user = db.session.query(User).filter_by(name=username).first()
            problem = db.session.query(Problem).filter_by(text=problem_text).first()
            solution = (
                db.session.query(Solution)
                .filter_by(
                    user_id=user.id, problem_id=problem.id, solution_text=solution_text
                )
                .first()
            )

            if not solution:
                solution = Solution(
                    user_id=user.id, problem_id=problem.id, solution_text=solution_text
                )
                db.session.add(solution)
                db.session.commit()

    def ensure_due_comparison(
        self, username, problem_text, solution_1_text, solution_2_text
    ):
        with app.app_context():
            user = db.session.query(User).filter_by(name=username).first()
            problem = db.session.query(Problem).filter_by(text=problem_text).first()
            solution_1 = (
                db.session.query(Solution)
                .filter_by(
                    problem_id=problem.id,
                    solution_text=solution_1_text,
                )
                .first()
            )
            solution_2 = (
                db.session.query(Solution)
                .filter_by(
                    problem_id=problem.id,
                    solution_text=solution_2_text,
                )
                .first()
            )

            due_comparison = (
                db.session.query(DueComparison)
                .filter_by(
                    user_id=user.id,
                    first_solution_id=solution_1.id,
                    second_solution_id=solution_2.id,
                )
                .first()
            )

            if not due_comparison:
                due_comparison = DueComparison(
                    user_id=user.id,
                    first_solution_id=solution_1.id,
                    second_solution_id=solution_2.id,
                )
                db.session.add(due_comparison)
                db.session.commit()

    def test_root_endpoint(self):
        response = requests.get(f"{self.base_url}/", json={})
        self.assertEqual(response.status_code, 200)
    
    def test_group_endpoint(self):
        g = browse_group().pop()
        response = requests.get(f"{self.base_url}/get_users/{g.id}", json={})
        self.assertEqual(response.status_code, 200)
    
    def test_user_endpoint(self):
        u = browse_user().pop()
        response = requests.get(f"{self.base_url}/{u.token}", json={})
        self.assertEqual(response.status_code, 200)

    def test_create_user(self):
        name = uuid.uuid4().hex.upper()
        self.assertIsNone(read_user(name))
        add_user(name)
        self.assertIsNotNone(read_user(name))
        delete_user(name)
        self.assertIsNone(read_user(name))

    def test_submit_solution(self):
        with app.app_context():
            u = read_user("User 1")
            p = read_problem(text="Problem 2")
            delete_solution(user_id=u.id, problem_id=p.id)

        payload = {
            "problem_id": p.id,
            "solution_text": "Sample solution",
        }
        response = requests.post(f"{self.base_url}/{u.token}/submit_solution/{p.id}", json=payload)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["message"], "Solution updated")

    def test_compare_solutions(self):
        with app.app_context():
            sol1 = (
                db.session.query(Solution)
                .filter_by(solution_text="First solution")
                .first()
            )
            sol2 = (
                db.session.query(Solution)
                .filter_by(solution_text="Second solution")
                .first()
            )

        payload = {
            "username": "User 1",
            "password": "pass1",
            "better_solution_id": sol1.id,
            "worse_solution_id": sol2.id,
            "motivation": "The first is better.",
        }

        response = requests.post(f"{self.base_url}/compare_solutions", json=payload)
        self.assertEqual(response.status_code, 200)
        self.assertIn("message", response.json())

    def test_set_password(self):
        # Assuming you have a user with no password and reset_token
        with app.app_context():
            token = db.session.query(User).filter_by(name="User 0").first().token
        payload = {"username": "User 0", "new_password": "pass0", "token": token}
        response = requests.post(f"{self.base_url}/set_password", json=payload)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["message"], "Password set successfully")


if __name__ == "__main__":
    # Ensure your Flask app is running before executing the tests
    unittest.main()
