from rico import GOODS, SMALL_BUILDINGS, Board, Town


def straight_town_estimator(town: Town) -> int:
    return town.tally()

def heuristic_town_estimator(town: Town) -> float:
    # Base points, already secured
    value = town.tally()

    # There is value in money
    value += town.count("money") / 5

    # There is value in having functioning buildings
    value += (
        sum(town.privilege(building_type) for building_type in SMALL_BUILDINGS)
        / 5
    )

    # There is value in stored goods
    value += sum(town.count(g) for g in GOODS) / 10

    # There is value in having tiles
    value += sum(town.placed_tiles) / 10

    # There is value having people
    value += town.total_people / 20

    # There is value in production
    value += sum(town.production().values()) / 20
    return value


def heuristic_board_estimator(board: Board, wrt: str) -> float:
    return heuristic_town_estimator(board.towns[wrt])


def straight_board_estimator(board: Board, wrt: str) -> float:
    return straight_town_estimator(board.towns[wrt])