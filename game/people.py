from typing import Literal, Union
from pydantic import BaseModel

from .exceptions import enforce

class PeopleHolder(BaseModel):
    people: int = 0

    def give_people(self, to: 'PeopleHolder', amount: Union[int, Literal["all"]]="all"):
        if amount == "all":
            amount = self.people
        enforce(isinstance(to, PeopleHolder), f"Object {to} can't accept people.")
        enforce(self.people >= amount, f"Not enough people in {self}.")
        self.people, to.people = self.people - amount, to.people + amount

