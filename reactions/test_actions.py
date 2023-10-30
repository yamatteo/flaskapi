import pytest
from .builder import BuilderAction
from rico import Board


def test_unique_buildings():
    names = ["Ad", "Be", "Ca", "Da"]
    board = Board.start_new(names)
    town = board.towns["Ad"]

    assert BuilderAction(name="Ad", building_type="small_indigo_plant") in BuilderAction(name="Ad").possibilities(board)
    board, action = BuilderAction(name="Ad", building_type="small_indigo_plant").react(board)

    assert BuilderAction(name="Ad", building_type="small_indigo_plant") not in BuilderAction(name="Ad").possibilities(board)