from datetime import datetime, timedelta
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
import pytest
from app_factory import create_app
from models import *


def app_in_memory():
    app = create_app()
    app.config.update(
        {
            "TESTING": True,
        }
    )

    S = db.session

    with app.app_context():
        g1 = add_group(name="Group 1")
        g2 = add_group(name="Group 2")

        u1 = add_user(name="User 1")
        u2 = add_user(name="User 2")
        u3 = add_user(name="User 3", password="pass3")

        set_membership("User 1", "Group 1")
        set_membership("User 2", "Group 1")
        set_membership(u3, g1)

        p1 = add_problem(
            short="Prob1", text="# Some problem about sum \n $$3 + 7 = x$$"
        )
        p2 = add_problem(
            short="Prob2", text="# Some problem about division\n $$ 4 / x = 3 $$"
        )

        set_due_solution(g1, p1, datetime.now() - timedelta(days=1))
        set_due_solution(g1, p2, datetime.now() + timedelta(days=1))

        for u in [u1, u2, u3]:
            add_solution(u, p1, f"Solution by {u.name}. $$ x = {hash(u.name) % 10}^3$$")

        set_due_comparison(g1, p1, date=datetime.now() - timedelta(days=1))

        for u, b, w in [(u1, u2, u3), (u2, u3, u1), (u3, u2, u1)]:
            add_comparison(u, p1, b.id, w.id, f"Solution by {b.name} is better than $$ x^{'{'}{w.name}{'}'}$$")
        
        # set_due_comparison(g1, p1, date=datetime.now() - timedelta(days=1))

    return app


@pytest.fixture()
def app():
    # other setup can go here

    yield app_in_memory()

    # clean up / reset resources here


@pytest.fixture()
def client(app):
    return app.test_client()


@pytest.fixture()
def runner(app):
    return app.test_cli_runner()


def test_set_membership(app):
    with app.app_context():
        set_membership("User 1", "Group 2")
        g = read_group("Group 2")
        u = read_user("User 1")
        assert u in g.users

        set_membership("User 1", "Group 2", False)
        g = read_group("Group 2")
        u = read_user("User 1")
        assert u not in g.users


def test_request_example(app, client):
    response = client.get("/")
    assert b"Quale classe?" in response.data
    assert b'<option value="/g/1/">Group 1</option>' in response.data

    response = client.get("/g/1/")
    assert b"Quale studente?" in response.data
    assert b'<option value="User 1">User 1</option>' in response.data

    with app.app_context():
        u1 = read_user("User 1")

    response = client.post(
        f"/g/1/authenticate/", json={"username": u1.name, "password": ""}
    )
    assert response.status_code == 200

    response = client.get(f"/u/{u1.token}/")
    assert b'<h5 class="my-1">Attenzione</h5>' in response.data

    response = client.post(
        f"/u/{u1.token}/set_password/",
        json={"username": u1.name, "new_password": "pass", "token": u1.token},
    )
    assert "message" in response.get_json()

    response = client.get(f"/u/{u1.token}/")
    assert b'<h5 class="my-1">Attenzione</h5>' not in response.data
    assert f'<a href="/u/{u1.token}/p/2/">'.encode() in response.data


if __name__ == "__main__":
    app_in_memory().run(debug=True)
