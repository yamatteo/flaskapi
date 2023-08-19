import pytest
from rich import print

from . import *

def test_a_game():
    game = Game.start_new(["Ada", "Bert", "Carl", "Dan"])
    first, second, third, fourth = [game.players[name] for name in game.play_order]

    assert first.gov
    with pytest.raises(RuleError):
        game.take_action(RoleAction(player_name=second.name, role="settler"))

    # First player take the settler role
    game.take_action(RoleAction(player_name=first.name, role="settler"))
    game.take_action(TileAction(player_name=first.name, tile_subclass="quarry"))
    with pytest.raises(RuleError):
        # Taking a quarry is a priviledge of the settler
        game.take_action(TileAction(player_name=second.name, tile_subclass="quarry"))
    tiles = [ tile.subclass for tile in game.exposed_tiles]
    game.take_action(TileAction(player_name=second.name, tile_subclass=tiles[0]))
    game.take_action(TileAction(player_name=third.name, tile_subclass=tiles[1]))
    game.take_action(TileAction(player_name=fourth.name, tile_subclass=tiles[2]))

    # Second player take the mayor role
    game.take_action(Action(subclass="Role", player_name=second.name, role="mayor"))
    assert second.count("people") == 2  # Mayor's priviledge
    assert all(player.count("people") == 1 for player in [first, third, fourth])  # Others get 1 person
    second.give(1, "people", to=second.tiles[0])
    second.give(1, "people", to=second.tiles[1])
    game.take_action(PeopleAction(player_name=second.name, whole_player=second))
 
    third.give(1, "people", to=third.tiles[0])
    game.take_action(PeopleAction(player_name=third.name, whole_player=third))
 
    fourth.give(1, "people", to=fourth.tiles[0])
    with pytest.raises(RuleError):
        # Check safeguards: fourth can't became third
        game.take_action(PeopleAction(player_name=fourth.name, whole_player=third))
    game.take_action(PeopleAction(player_name=fourth.name, whole_player=fourth))

    first.give(1, "people", to=first.tiles[1])  # Put the person in the quarry
    game.take_action(PeopleAction(player_name=first.name, whole_player=first))

    # Third player take the builder role
    game.take_action(RoleAction(player_name=third.name, role="builder"))
    # He can build the sugar mill because he has three money and the mill cost four, but he has builder's priviledge
    game.take_action(BuildingAction(player_name=third.name, building_subclass="sugar_mill"))

    # Integers are not referenced, but this is WEIRD!!!
    # TODO: understand why this happens
    first, second, third, fourth = [game.players[name] for name in game.play_order]
    assert not third.has("money")
    with pytest.raises(RuleError):
        # Fourth can't, because he don't have the money
        game.take_action(BuildingAction(player_name=fourth.name, building_subclass="sugar_mill"))
    game.take_action(BuildingAction(player_name=fourth.name, building_subclass="construction_hut"))
    # First can build hospice (cost: 4) because he has a quarry
    game.take_action(BuildingAction(player_name=first.name, building_subclass="hospice"))
    game.take_action(BuildingAction(player_name=second.name, building_subclass="indigo_plant"))

    # Fourth player take the craftsman role
    game.take_action(RoleAction(player_name=fourth.name, role="craftsman"))

    # Integers are not referenced, but this is WEIRD!!!
    # TODO: understand why this happens
    first, second, third, fourth = [game.players[name] for name in game.play_order]
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
    assert third.count("money") == 2  # One from selling (corn = 0 + trader's prviledge = 1) and one from the card bonus.
    assert game.market.count("corn") == 1

    # Fourth take the captain role
    game.take_action(RoleAction(player_name=fourth.name, role="captain"))
    game.take_action(CaptainAction(player_name=fourth.name, selected_ship=7, selected_good="corn"))
    game.take_action(RefuseAction(player_name=first.name))
    game.take_action(RefuseAction(player_name=second.name))
    game.take_action(RefuseAction(player_name=third.name))
    game.take_action(RefuseAction(player_name=fourth.name))
