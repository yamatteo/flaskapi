from random import sample

from attr import define

from pseudos import BiDict, generate_pseudos
from reactions import Action, GovernorAction
from rico import Board


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

    def take_action(self, action: Action):
        assert action.responds_to(self.expected)
        board, extra = action.react(self.board)
        self.board = board
        self.actions = merge(self.actions[1:], extra)
