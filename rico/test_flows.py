import pytest
from flask import url_for
from flask_login import FlaskLoginClient
from . import create_app, db, User, Game, GameData

# @pytest.fixture
# def client():
#     app = create_app("sqlite:///:memory:")

#     with app.app_context():
#         db.create_all()
#         yield app.test_client()
#         db.drop_all()

@pytest.fixture
def app():
    app = create_app("sqlite:///:memory:")

    with app.app_context():
        db.create_all()
        app.test_client_class = FlaskLoginClient
        yield app
        db.drop_all()

def test_game_flow(app):
    client = app.test_client()
    
    # Create a new game
    response = client.post("/new_game")
    assert response.status_code == 302  # Redirect
    assert response.location == "/"  # To homepage

    # Log in as four different players
    player_names = ["Alice", "Bob", "Clara", "David"]
    passwords = ["pass", "pass", "pass", "pass"]
    users = []
    for name, password in zip(player_names, passwords):
        with app.test_client() as client:
            response = client.post(
                "/join_game/1", data=dict(username=name, password=password), follow_redirects=True
            )
            assert response.status_code == 200
        user = User.query.filter_by(name=name).first()
        users.append(user)

    # Start the game
    with app.test_client() as client:
        response = client.post("/start_game/1", follow_redirects=True)
        assert response.status_code == 200
        game = Game.query.first()
        assert game.status == "active"

    # Check the play order and make helper variables
    gd = GameData.loads(game.dumped_data)
    rev_pseudos = {pseudo: name for name, pseudo in gd.pseudos.items()}
    play_order = [town.name for town in gd.current_round()]
    name_order = [rev_pseudos[pseudo] for pseudo in play_order]
    users.sort(key=lambda user: name_order.index(user.name))
    id_order = [ { user.name:user.id for user in users }[name] for name in name_order ]
    zeroth, first, second, third = play_order

    # Fail in performing the governor action for the first player
    with app.test_client(user=users[1]) as client:
        response = client.post(f"/login", data={"username":users[1].name, "password":"pass"}, follow_redirects=True)
        response = client.post(f"/action/governor/{first}", follow_redirects=True)
        assert response.status_code == 400
        assert f"Assertion Error:".encode() in response.data

    # Perform the governor action for the zeroth player
    with app.test_client() as client:
        response = client.post(f"/login", data={"username":users[0].name, "password":"pass"}, follow_redirects=True)
        response = client.post(f"/action/governor/{zeroth}", follow_redirects=True)
        assert response.status_code == 200

    # Perform the role action for the zeroth player, taking the builder role
    response = client.post(
        f"/action/role/{zeroth}", data=dict(role="builder"), follow_redirects=True
    )
    assert response.status_code == 200

    # Perform the builder action for the zeroth player building the construction hut
    response = client.post(
        f"/action/builder/{zeroth}",
        data=dict(building_type="construction_hut", extra_person=""),
        follow_redirects=True,
    )
    assert response.status_code == 200

    # First player decides to not build and refuse the action
    client.post(f"/login", data={"username":users[1].name, "password":"pass"}, follow_redirects=True)
    response = client.post(
        f"/action/refuse/{first}",
        follow_redirects=True,
    )
    assert response.status_code == 200

    # Second player decides to not build and refuse the action
    client.post(f"/login", data={"username":users[2].name, "password":"pass"}, follow_redirects=True)
    response = client.post(
        f"/action/refuse/{second}",
        follow_redirects=True,
    )
    assert response.status_code == 200

    # Third player decides to not build and refuse the action
    client.post(f"/login", data={"username":users[3].name, "password":"pass"}, follow_redirects=True)
    response = client.post(
        f"/action/refuse/{third}",
        follow_redirects=True,
    )
    assert response.status_code == 200

    # First player take the captain role
    client.post(f"/login", data={"username":users[1].name, "password":"pass"}, follow_redirects=True)
    response = client.post(
        f"/action/role/{first}", data=dict(role="captain"), follow_redirects=True
    )
    assert response.status_code == 200

    # Each player refuse 
    client.post(f"/login", data={"username":users[1].name, "password":"pass"}, follow_redirects=True)
    response = client.post(
        f"/action/refuse/{first}",
        follow_redirects=True,
    )

    client.post(f"/login", data={"username":users[2].name, "password":"pass"}, follow_redirects=True)
    response = client.post(
        f"/action/refuse/{second}",
        follow_redirects=True,
    )

    client.post(f"/login", data={"username":users[3].name, "password":"pass"}, follow_redirects=True)
    response = client.post(
        f"/action/refuse/{third}",
        follow_redirects=True,
    )

    client.post(f"/login", data={"username":users[0].name, "password":"pass"}, follow_redirects=True)
    response = client.post(
        f"/action/refuse/{zeroth}",
        follow_redirects=True,
    )
