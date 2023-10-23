from attr import define

from .holders import AttrHolder


@define
class Market(AttrHolder):
    coffee: int = 0
    corn: int = 0
    indigo: int = 0
    sugar: int = 0
    tobacco: int = 0