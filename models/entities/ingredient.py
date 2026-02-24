from typing import NamedTuple, Tuple


class Ingredient(NamedTuple):
    name: str
    state: str = "RAW" # RAW, CHOPPED, COOKED, BURNT
    contents: Tuple[str, ...] = ()