from typing import NamedTuple, Tuple


class Plate(NamedTuple):
    state: str = "CLEAN"  # CLEAN, DIRTY, WITH_FOOD
    contents: Tuple[str, ...] = ()
