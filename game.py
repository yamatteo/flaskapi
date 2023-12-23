from copy import deepcopy
from random import sample

from attr import define

from pseudos import BiDict, generate_pseudos
from reactions import Action, GovernorAction
from rico import Board, GOODS, BUILDINGS


def merge(actions: list[Action], extra: list[Action]) -> list[Action]:
    merged = []
    i, j = 0, 0
    while i < len(actions):
        if j < len(extra) and extra[j].priority > actions[i].priority:
            merged.append(extra[j])
            j += 1
        else:
            merged.append(actions[i])
            i += 1
    while j < len(extra):
        merged.append(extra[j])
        j += 1
    return merged


@define
class Game:
    play_order: list[str]
    actions: list[Action]
    board: Board
    pseudos: BiDict[str, str]

    @property
    def expected(self) -> Action:
        return self.actions[0]

    @classmethod
    def start(cls, usernames: list[str]):
        assert 3 <= len(usernames) <= 5, "Games are for three to five players."
        pseudos = generate_pseudos(usernames)
        play_order = sample(list(pseudos.values()), len(usernames))
        board = Board.start_new(play_order)
        actions = [GovernorAction(name=play_order[0])]
        return cls(play_order=play_order, actions=actions, board=board, pseudos=pseudos)

    def as_tuple(self, wrt: str) -> tuple[tuple[int, ...], ...]:
        board = self.board
        direct = tuple(
            board.count(kind)
            for kind in (
                "gov",
                "spent_captain",
                "spent_wharf",
                "coffee",
                "corn",
                "indigo",
                "money",
                "people",
                "points",
                "sugar",
                "tobacco",
            )
        )
        tiles = (len(board.unsettled_tiles), board.unsettled_quarries) + tuple(
            board.exposed_tiles.count(tile_type) for tile_type in GOODS
        )
        roles_money = tuple(board.roles)
        ships = [board.people_ship.people]
        for ship in board.goods_fleet.values():
            ships.extend([ship.size] + [ship.count(kind) for kind in GOODS])
        ships = tuple(ships)
        market = tuple(board.market.count(kind) for kind in GOODS)
        buildings = tuple(board.unbuilt.count(kind) for kind in BUILDINGS)
        
        board_embedding = direct + roles_money + tiles + ships + market + buildings
        towns = tuple(town.as_tuple() for town in board.town_round_from(wrt))

        return sum([board_embedding, *towns], start=tuple())

    def copy(self) -> "Game":
        return Game(
            play_order=self.play_order,
            actions=deepcopy(self.actions),
            board=deepcopy(self.board),
            pseudos=self.pseudos,
        )

    def project(self, action: Action) -> "Game":
        game = self.copy()
        game.take_action(action)
        return game

    def take_action(self, action: Action):
        assert action.responds_to(self.expected)
        board, extra = action.react(self.board)
        self.board = board
        self.actions = merge(self.actions[1:], extra)
