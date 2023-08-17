from typing import Literal, Union
from pydantic import BaseModel

from .exceptions import enforce

class MoneyHolder(BaseModel):
    money: int = 0

    def give_money(self, to: 'MoneyHolder', amount: Union[int, Literal["all"]]="all"):
        if amount == "all":
            amount = self.money
        enforce(isinstance(to, MoneyHolder), f"Object {to} can't accept money.")
        enforce(self.money >= amount, f"Not enough money in {self}.")
        self.money, to.money = self.money - amount, to.money + amount
