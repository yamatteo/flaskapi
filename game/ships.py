from typing import Literal, Optional
from attr import define


from .holders import AttrHolder, CountableType


@define
class Ship(AttrHolder):
    people: int = 0
    coffee: int = 0
    corn: int = 0
    indigo: int = 0
    sugar: int = 0
    tobacco: int = 0

    size: Optional[int] = None