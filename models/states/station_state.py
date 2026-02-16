from typing import NamedTuple, Optional

from models.entities.ingredient import Ingredient



class StationState(NamedTuple):
    progress: int = 0
    is_on_fire: bool = False
    content: Optional[Ingredient] = None