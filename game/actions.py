from typing import Literal
from pydantic import BaseModel, ConfigDict

from .exceptions import enforce
from .cards import Role

from .players import Player



class Action(BaseModel):
    model_config = ConfigDict(extra='allow')
    cls: Literal["Action"] = "Action"
    subclass: str
    player_name: str

# Transfer governor card
class GovernorAction(Action):
    subclass: Literal["Governor"] = "Governor"

# Take a role card
class RoleAction(Action):
    subclass: Literal["Role"] = "Role"
    role: Role

# Take a tile
class TileAction(Action):
    subclass: Literal["Tile"] = "Tile"
    tile: Literal["coffee", "tobacco", "corn", "sugar", "indigo", "quarry"]
    down_tile: bool = False
    extra_person: bool = False

# Inform on people distribution
class PeopleAction(Action):
    subclass: Literal["People"] = "People"
    whole_player: Player

# Take building
class BuildingAction(Action):
    subclass: Literal["Building"] = "Building"
    building_subclass: Literal[
        "indigo_plant",
        "small_indigo_plant",
        "sugar_mill",
        "small_sugar_mill",
        "tobacco_storage",
        "coffee_roaster",
        "small_market",
        "hacienda",
        "construction_hut",
        "small_warehouse",
        "hospice",
        "office",
        "large_market",
        "large_warehouse",
        "factory",
        "university",
        "harbor",
        "wharf",
        "guild_hall",
        "residence",
        "fortress",
        "city_hall",
        "custom_house",
    ]
    extra_person: bool = False

# Craftsman priviledge
class CraftsmanAction(Action):
    subclass: Literal["Craftsman"] = "Craftsman"
    selected_good: Literal["coffee", "tobacco", "corn", "sugar", "indigo"]

# Trader action
class TraderAction(Action):
    subclass: Literal["Trader"] = "Trader"
    selected_good: Literal["coffee", "tobacco", "corn", "sugar", "indigo"]

# Captain action
class CaptainAction(Action):
    subclass: Literal["Captain"] = "Captain"
    selected_ship: int
    selected_good: Literal["coffee", "tobacco", "corn", "sugar", "indigo"]

# PreserveGoods action
class PreserveGoodsAction(Action):
    subclass: Literal["PreserveGoods"] = "PreserveGoods"
    selected_good: Literal["coffee", "tobacco", "corn", "sugar", "indigo"]
    small_warehouse_good: Literal["coffee", "tobacco", "corn", "sugar", "indigo"] = None
    large_warehouse_first_good: Literal["coffee", "tobacco", "corn", "sugar", "indigo"] = None
    large_warehouse_second_good: Literal["coffee", "tobacco", "corn", "sugar", "indigo"] = None

# Refuse action
class RefuseAction(Action):
    subclass: Literal["Refuse"] = "Refuse"

def specify(action: Action):
    enforce(hasattr(action, "subclass"), f"Given {action} is not an action.")
    subclass = eval(f"{action.subclass}Action")
    return subclass(**action.model_dump())




