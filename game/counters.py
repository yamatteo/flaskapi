from typing import Literal, Union, overload

from pydantic import BaseModel

from .exceptions import enforce

GOODS = ["coffee", "corn", "indigo", "sugar", "tobacco"]
Countable = Literal[
    "coffee", "corn", "indigo", "money", "people", "points", "sugar", "tobacco"
]
Good = Literal["coffee", "corn", "indigo", "sugar", "tobacco"]
alias = {
    "c": "coffee",
    "k": "corn",
    "i": "indigo",
    "m": "money",
    "w": "people",
    "p": "points",
    "s": "sugar",
    "t": "tobacco",
}
rev_alias = {value: key for key, value in alias.items()}


class Holder(BaseModel):
    n: str = ""
    _dict: dict = None

    @classmethod
    def new(cls, **kwargs):
        n = str().join(f"{rev_alias[type]}{amount}" for type, amount in kwargs.items())
        return cls(n=n)

    @property
    def dict(self) -> dict[Countable, int]:
        if self._dict is not None:
            return self._dict
        _dict = {}
        key, value = None, None
        for c in self.n:
            if c in alias:
                if key is not None:
                    _dict[key] = int(value)
                key = alias[c]
                value = ""
            else:
                value += c
        if key is not None:
            _dict[key] = int(value)
        self._dict = _dict
        return _dict

    def count(self, type: Countable):
        return self.dict.get(type, 0)

    @overload
    def has(self, type: Countable) -> bool:
        ...

    @overload
    def has(self, amount: int, type: Countable) -> bool:
        ...

    def has(self, *args):
        if len(args) == 2:
            amount, type = args
        else:
            amount, type = 1, args[0]
        return self.dict.get(type, 0) >= amount

    def give(
        self, amount: Union[int, Literal["all"]], type: str, to: "Holder"
    ):
        if amount == "all":
            amount = self.count(type)
        enforce(isinstance(to, Holder), f"Object {to} can't accept {type}.")
        enforce(self.count(type) >= amount, f"Not enough {type} in {self}.")
        self.set(type, self.count(type) - amount)
        to.set(type, to.count(type) + amount)
    
    def set(self, type: Countable, amount: int):
        _dict = self.dict
        _dict[type] = amount
        self._dict = _dict
        self.n = str().join(f"{rev_alias[type]}{amount}" for type, amount in _dict.items())


def test_holders():
    h = Holder(n="c2m5p10")
    assert h.count("coffee") == 2
    assert h.count("people") == 0
    assert h.count("points") == 10
    assert h.has("coffee")
    assert h.has(6, "money") is False
    k = Holder()
    h.give(2, "money", to=k)
    assert k.has(2, "money")
