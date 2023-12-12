import pytest
from . import *


def test_give_role():
    names = ["Ad", "Be", "Ca", "Da"]
    board = Board.start_new(names)
    role = ROLES[0]
    assert role == "builder"
    board.roles[0] = 2
    town = board.towns["Ad"]
    assert town.money == 3
    board.give_role("builder", to="Ad")
    assert (
        isinstance(board.towns["Ad"].role, Role) and board.towns["Ad"].role == "builder"
    )
    assert town.money == 5
    assert town.role.money == 0


def test_is_end_of_round():
    names = ["Ad", "Be", "Ca", "Da"]
    board = Board.start_new(names)
    assert not board.is_end_of_round()

    for name in names:
        board.give_role(board.roles[0], to=name)

    assert board.is_end_of_round()


def test_new_board():
    board = Board.start_new(["Ad", "Be", "Ca", "Da"])
    assert isinstance(board, Board)


def test_next_to():
    board = Board.start_new(["Be", "Ca", "Ad", "Da"])
    assert board.next_to("Be") == "Ca"
    assert board.next_to("Ca") == "Ad"
    assert board.next_to("Ad") == "Da"
    assert board.next_to("Da") == "Be"


def test_set_governor():
    names = ["Ad", "Be", "Ca", "Da"]
    board = Board.start_new(names)
    board.set_governor("Be")
    for name in names:
        assert board.towns[name].gov == int(name == "Be")

def test_unique_building():
    names = ["Ad", "Be", "Ca", "Da"]
    board = Board.start_new(names)
    town = board.towns["Ad"]
    town.money = 8
    board.give_building("indigo_plant", to=town)
    with pytest.raises(RuleError):
        board.give_building("indigo_plant", to=town)



def nottest():
    first, second, third, fourth = [game.towns[name] for name in game.play_order]

    assert first.gov
    with pytest.raises(RuleError):
        game.take_action(RoleAction(player_name=second.name, role="settler"))

    # First player take the settler role
    game.take_action(RoleAction(player_name=first.name, role="settler"))
    game.take_action(SettlerAction(player_name=first.name, tile="quarry"))
    with pytest.raises(RuleError):
        # Taking a quarry is a priviledge of the settler
        game.take_action(SettlerAction(player_name=second.name, tile="quarry"))
    tiles = game.exposed_tiles
    game.take_action(SettlerAction(player_name=second.name, tile=tiles[0]))
    game.take_action(SettlerAction(player_name=third.name, tile=tiles[1]))
    game.take_action(SettlerAction(player_name=fourth.name, tile=tiles[2]))

    # Second player take the mayor role
    game.take_action(RoleAction(type="role", player_name=second.name, role="mayor"))
    assert second.count("people") == 2  # Mayor's priviledge
    assert all(
        player.count("people") == 1 for player in [first, third, fourth]
    )  # Others get 1 person
    game.take_action(
        MayorAction(
            player_name=second.name,
            people_distribution=[
                ["home", 0],
                [second.tiles[0].type, 1],
                [second.tiles[1].type, 1],
            ],
        )
    )

    with pytest.raises(RuleError):  # Check correct amount of people
        game.take_action(
            MayorAction(
                player_name=third.name,
                people_distribution=[
                    ["home", 0],
                    [third.tiles[0].type, 1],
                    [third.tiles[1].type, 1],
                ],
            )
        )

    game.take_action(
        MayorAction(
            player_name=third.name,
            people_distribution=[
                ["home", 0],
                [third.tiles[0].type, 1],
                [third.tiles[1].type, 0],
            ],
        )
    )

    game.take_action(
        MayorAction(
            player_name=fourth.name,
            people_distribution=[
                ["home", 0],
                [fourth.tiles[0].type, 1],
                [fourth.tiles[1].type, 0],
            ],
        )
    )

    game.take_action(
        MayorAction(
            player_name=first.name,
            people_distribution=[
                ["home", 0],
                [first.tiles[0].type, 0],
                [first.tiles[1].type, 1],
            ],
        )
    )

    # Third player take the builder role
    game.take_action(RoleAction(player_name=third.name, role="builder"))
    # He can build the sugar mill because he has three money and the mill cost four, but he has builder's priviledge
    game.take_action(BuilderAction(player_name=third.name, building_type="sugar_mill"))

    # Integers are not referenced, but this is WEIRD!!!
    # TODO: understand why this happens
    first, second, third, fourth = [game.towns[name] for name in game.play_order]
    assert not third.has("money")
    with pytest.raises(RuleError):
        # Fourth can't, because he don't have the money
        game.take_action(
            BuilderAction(player_name=fourth.name, building_type="sugar_mill")
        )
    game.take_action(
        BuilderAction(player_name=fourth.name, building_type="construction_hut")
    )
    # First can build hospice (cost: 4) because he has a quarry
    game.take_action(BuilderAction(player_name=first.name, building_type="hospice"))
    game.take_action(
        BuilderAction(player_name=second.name, building_type="indigo_plant")
    )

    # Fourth player take the craftsman role
    game.take_action(RoleAction(player_name=fourth.name, role="craftsman"))

    # Integers are not referenced, but this is WEIRD!!!
    # TODO: understand why this happens
    first, second, third, fourth = [game.towns[name] for name in game.play_order]
    assert third.count("corn") == 1 and fourth.count("corn") == 1
    game.take_action(CraftsmanAction(player_name=fourth.name, selected_good="corn"))
    assert fourth.count("corn") == 2

    # Second round: second is governor
    assert second.gov
    game.take_action(RoleAction(player_name=second.name, role="prospector"))
    assert second.count("money") == 2

    # Third take trader
    game.take_action(RoleAction(player_name=third.name, role="trader"))
    game.take_action(TraderAction(player_name=third.name, selected_good="corn"))
    game.take_action(RefuseAction(player_name=fourth.name))
    game.take_action(RefuseAction(player_name=first.name))
    game.take_action(RefuseAction(player_name=second.name))
    assert (
        third.count("money") == 2
    )  # One from selling (corn = 0 + trader's prviledge = 1) and one from the card bonus.
    assert game.market.count("corn") == 1

    # Fourth take the captain role
    game.take_action(RoleAction(player_name=fourth.name, role="captain"))
    game.take_action(
        CaptainAction(player_name=fourth.name, selected_ship=7, selected_good="corn")
    )
    game.take_action(RefuseAction(player_name=first.name))
    game.take_action(RefuseAction(player_name=second.name))
    game.take_action(RefuseAction(player_name=third.name))


def notest_captain_autorefuse():
    """After a CaptainAction, if there is no more good to ship, no need to refuse."""
    game = Game(
        # n='m48p122w66c9k7i11s11t9',
        points=122,
        players={
            "Ada": Player(
                name="Ada",
                pseudo="Ad",
                corn=2,
                gov=False,
                role=None,
            ),
            "Bert": Player(
                name="Bert",
                pseudo="Be",
                gov=False,
                role=Role(type="trader"),
            ),
            "Carl": Player(
                name="Carl",
                pseudo="Ca",
                gov=False,
                role=None,
            ),
            "Dan": Player(
                name="Dan",
                pseudo="Da",
                gov=True,
                role=Role(type="prospector"),
            ),
        },
        actions=[
            Action(type="role", player_name="Ada"),
            Action(type="role", player_name="Carl"),
            GovernorAction(type="governor", player_name="Bert"),
            GovernorAction(type="governor", player_name="Ada"),
            GovernorAction(type="governor", player_name="Carl"),
            GovernorAction(type="governor", player_name="Dan"),
        ],
        play_order=["Carl", "Dan", "Bert", "Ada"],
        people_ship=Ship(people=8),
        goods_ships={5: Ship(), 6: Ship(), 7: Ship()},
        market=Market(),
        roles=[
            Role(money=1, type="captain"),
            Role(type="craftsman"),
            Role(type="builder"),
            Role(type="settler"),
            Role(type="mayor"),
        ],
        exposed_tiles=[],
    )
    game.take_action(RoleAction(player_name="Ada", role="captain"))
    game.take_action(
        CaptainAction(player_name="Ada", selected_ship=7, selected_good="corn")
    )
    game.take_action(RefuseAction(player_name="Carl"))
    game.take_action(RefuseAction(player_name="Dan"))
    game.take_action(RefuseAction(player_name="Bert"))
    with pytest.raises(RuleError):
        game.take_action(RefuseAction(player_name="Ada"))
    assert game.expected_player.name == "Carl"
    assert game.expected_action.type == "role"
