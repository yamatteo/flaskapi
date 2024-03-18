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
    with app.app_context(), app.test_request_context(), app.test_client() as client:

        # Create a new game
        response = client.post(url_for("new_game"))
        assert response.status_code == 302  # Redirect
        assert response.location == "/"  # To homepage

        # Log in as four different players
        player_names = ["Alice", "Bob", "Clara", "David"]
        passwords = ["pass", "pass", "pass", "pass"]
        users = []
        for name, password in zip(player_names, passwords):
            with app.test_client() as client:
                response = client.post(
                    url_for("join_game", game_id=1),
                    data=dict(username=name, password=password),
                    follow_redirects=True,
                )
                assert response.status_code == 200
            user = User.query.filter_by(name=name).first()
            users.append(user)

        # Start the game
        response = client.post(url_for("start_game", game_id=1), follow_redirects=True)
        assert response.status_code == 200
        game = Game.query.first()
        assert game.status == "active"

        # Check login. It should not be necessary, because we already know all tokens.
        # It is used once by a human user to obtain the token.
        response = client.post(
            url_for("login"),
            data={"username": users[1].name, "password": "pass"},
        )
        assert response.location == f"/{users[1].token}"
        assert client.get(url_for("game_page", token=users[0].token)).status_code == 200
        assert client.get(url_for("game_page", token="not_a_token"), follow_redirects=True).status_code == 400

        # Check the play order and make helper variables
        gd = GameData.loads(game.dumped_data)
        rev_pseudos = {pseudo: name for name, pseudo in gd.pseudos.items()}
        play_order = [town.name for town in gd.current_round()]
        name_order = [rev_pseudos[pseudo] for pseudo in play_order]
        users.sort(key=lambda user: name_order.index(user.name))

        # Fail in performing the governor action for the first player
        response = client.post(
            url_for("action_governor", token=users[1].token), follow_redirects=True
        )
        assert response.status_code == 400
        assert f"Assertion Error:".encode() in response.data

        ### First year
        ## Zero take the governor and the builder role and build the construction hut
        assert (
            client.post(
                url_for("action_governor", token=users[0].token), follow_redirects=True
            ).status_code
            == 200
        )

        assert (
            client.post(
                url_for("action_role", token=users[0].token),
                data=dict(role="builder"),
                follow_redirects=True,
            ).status_code
            == 200
        )

        assert (
            client.post(
                url_for("action_builder", token=users[0].token),
                data=dict(building_type="construction_hut", extra_person=""),
                follow_redirects=True,
            ).status_code
            == 200
        )

        # One decides to not build and refuse the action
        assert (
            client.post(
                url_for("action_refuse", token=users[1].token),
                follow_redirects=True,
            ).status_code
            == 200
        )

        # Two builds the hacienda
        assert (
            client.post(
                url_for("action_builder", token=users[2].token),
                data=dict(building_type="hacienda", extra_person=""),
                follow_redirects=True,
            ).status_code
            == 200
        )

        # Three builds the small market
        assert (
            client.post(
                url_for("action_builder", token=users[3].token),
                data=dict(building_type="small_market", extra_person=""),
                follow_redirects=True,
            ).status_code
            == 200
        )

        ## One take the settler role and a quarry
        game = Game.query.first()
        gd = GameData.loads(game.dumped_data)
        exposed_tiles = gd.board.exposed_tiles

        assert client.post(
                url_for("action_role", token=users[1].token),
                data=dict(role="settler"),
                follow_redirects=True,
            ).status_code == 200
        
        assert client.post(
                url_for("action_settler", token=users[1].token),
                data=dict(tile="quarry_tile"),
                follow_redirects=True,
            ).status_code== 200
        
        # Two take a tile
        assert client.post(
                url_for("action_settler", token=users[2].token),
                data=dict(tile=exposed_tiles[0]),
                follow_redirects=True,
            ).status_code == 200
        
        # Three can't take a quarry, then take a tile
        assert client.post(
                url_for("action_settler", token=users[3].token),
                data=dict(tile="quarry_tile"),
                follow_redirects=True,
            ).status_code == 400
        
        assert client.post(
                url_for("action_settler", token=users[3].token),
                data=dict(tile=exposed_tiles[1]),
                follow_redirects=True,
            ).status_code == 200

        # Zero take a tile
        assert client.post(
                url_for("action_settler", token=users[0].token),
                data=dict(tile=exposed_tiles[2]),
                follow_redirects=True,
            ).status_code == 200
        
        # Before changing turn, One have to tidy
        assert client.post(
                url_for("action_tidyup", token=users[1].token),
                follow_redirects=True,
            ).status_code == 200

