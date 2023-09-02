from typing import Literal, Union, overload

from pydantic import BaseModel

from .exceptions import enforce

CountableType = Literal[
    "coffee", "corn", "indigo", "money", "people", "points", "sugar", "tobacco"
]
COUNTABLES: list[CountableType] = [
    "coffee",
    "corn",
    "indigo",
    "money",
    "people",
    "points",
    "sugar",
    "tobacco",
]
GoodType = Literal[
    "coffee",
    "corn",
    "indigo",
    "sugar",
    "tobacco",
]
GOODS: list[GoodType] = [
    "coffee",
    "corn",
    "indigo",
    "sugar",
    "tobacco",
]
ALIASES = {
    "c": "coffee",
    "k": "corn",
    "i": "indigo",
    "m": "money",
    "w": "people",
    "p": "points",
    "s": "sugar",
    "t": "tobacco",
}

class Holder(BaseModel):
    money: int = 0
    people: int = 0
    points: int = 0
    coffee: int = 0
    corn: int = 0
    indigo: int = 0
    sugar: int = 0
    tobacco: int = 0

    @classmethod
    def from_compressed(cls, data: str):
        holdings = {}
        key = None
        value = ''
        
        for c in data:
            if c in ALIASES:
                if key is not None:
                    holdings[key] = int(value)
                key = ALIASES[c]
                value = ''
            else:
                value += c
                
        if key is not None:
            holdings[key] = int(value)
            
        for key in ALIASES.values():
            if key not in holdings:
                holdings[key] = 0
                
        return cls(**holdings)
    
    def compress(self) -> str:
        return str().join(
            f"{alias}{self.count(countable)}"
            for alias, countable in ALIASES.items()
            if self.count(countable) > 0
        )
    
    def count(self, kind: CountableType):
        return getattr(self, kind, 0)

    @overload
    def has(self, type: CountableType) -> bool:
        ...

    @overload
    def has(self, amount: int, type: CountableType) -> bool:
        ...

    def has(self, *args):
        if len(args) == 2:
            amount, type = args
        else:
            amount, type = 1, args[0]
        return getattr(self, type, 0) >= amount

    def give(self, amount: Union[int, Literal["all"]], kind: str, *, to: "Holder"):
        if amount == "all":
            amount = self.count(kind)
        enforce(isinstance(to, Holder), f"Object {to} can't accept {kind}.")
        enforce(self.count(kind) >= amount, f"Not enough {kind} in {self}.")
        self.set(kind, self.count(kind) - amount)
        to.set(kind, to.count(kind) + amount)

    def give_or_make(self, amount: Union[int, Literal["all"]], kind: str, *, to: "Holder"):
        if amount == "all":
            amount = self.count(kind)
        enforce(isinstance(to, Holder), f"Object {to} can't accept {kind}.")
        self.set(kind, max(0, self.count(kind) - amount))
        to.set(kind, to.count(kind) + amount)

    def set(self, kind: CountableType, amount: int):
        setattr(self, kind, amount)
