from typing import NamedTuple, Optional, Tuple


class Order(NamedTuple):
    ingredients: Tuple[str, ...]
    instant: int
    duration: int
    score: int
    recipe: Optional["Recipe"] = None