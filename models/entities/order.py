from typing import NamedTuple, Tuple


class Order(NamedTuple):
    ingredients: Tuple[str, ...]
    instant: int
    duration: int
    score: int