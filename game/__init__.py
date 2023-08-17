from dataclasses import asdict, is_dataclass
from typing import Iterable, Mapping
from pydantic import ValidationError

from .actions import *
from .cards import *
from .counters import *
from .exceptions import *
from .games import *
from .players import *


def serialize(obj):
    if isinstance(obj, (bool, int, float, str, type(None))):
        return obj
    elif is_dataclass(obj):
        return serialize(asdict(obj))
    elif hasattr(obj, "model_dump"):
        return serialize(vars(obj))
    elif isinstance(obj, Mapping):
        return {key: serialize(value) for key, value in obj.items()}
    elif isinstance(obj, Iterable):
        return [serialize(item) for item in obj]
    else:
        raise NotImplementedError(f"Object of type {type(obj)} are not serializable.")
