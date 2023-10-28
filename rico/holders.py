from typing import Iterator, Literal, Union, overload

from attr import define

from . import COUNTABLES, CountableType
from .exceptions import enforce


@define
class AttrHolder:
    def count(self, kind: CountableType) -> int:
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

    def give(self, amount: Union[int, Literal["all"]], type: CountableType, *, to: "AttrHolder"):
        if amount == "all":
            amount = self.count(type)
        enforce(hasattr(to, type), f"Object {to} can't accept {type}.")
        enforce(self.count(type) >= amount, f"Not enough {type} in {self}.")
        self.set(type, self.count(type) - amount)
        to.set(type, to.count(type) + amount)

    def give_or_make(self, amount: Union[int, Literal["all"]], type: CountableType, *, to: "AttrHolder"):
        if amount == "all":
            amount = self.count(type)
        enforce(hasattr(to, type), f"Object {to} can't accept {type}.")
        self.set(type, max(0, self.count(type) - amount))
        to.set(type, to.count(type) + amount)

    def set(self, kind: CountableType, amount: int):
        setattr(self, kind, amount)
    
    def items(self) -> Iterator[tuple[CountableType, int]]:
        for type in COUNTABLES:
            if self.has(type):
                yield type, self.count(type)
