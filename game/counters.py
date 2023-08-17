
from typing import Literal, Union
from pydantic import BaseModel

from .exceptions import enforce

class Holder(BaseModel):
    def give(self, to: 'Holder', subclass: str, amount: Union[int, Literal["all"]]="all"):
        if amount == "all":
            amount = getattr(self, subclass)
        enforce(hasattr(to, subclass), f"Object {to} can't accept {subclass}.")
        enforce(getattr(self, subclass) >= amount, f"Not enough {subclass} in {self}.")
        setattr(self, subclass, getattr(self, subclass) - amount)
        setattr(to,   subclass, getattr(to,   subclass) + amount)

class GoodsHolder(Holder):
    _goods = ["coffee", "corn", "indigo", "sugar", "tobacco"]
    coffee: int = 0
    corn: int = 0
    indigo: int = 0
    sugar: int = 0
    tobacco: int = 0

    def give(self, to: 'Holder', subclass: str = "all", amount: Union[int, Literal["all"]]="all"):
        if subclass != "all":
            super().give(to, subclass, amount)
            return
        for subclass in self._goods:
            super().give(to, subclass, amount)

class MoneyHolder(Holder):
    money: int = 0

    def give_money(self, to: 'MoneyHolder', amount: Union[int, Literal["all"]]="all"):
        self.give(to, "money", amount)

class PeopleHolder(Holder):
    people: int = 0

    def give_people(self, to: 'PeopleHolder', amount: Union[int, Literal["all"]]="all"):
        self.give(to, "people", amount)

class PointHolder(Holder):
    points: int = 0

    def give_points(self, to: 'PointHolder', amount: Union[int, Literal["all"]]="all"):
        self.give(to, "points", amount)
