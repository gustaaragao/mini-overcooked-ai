from typing import NamedTuple, Tuple


class Ingredient(NamedTuple):
    name: str
    state: str = "RAW" # RAW, CHOPPED, COOKED, BURNT
    # final_state: str # TODO: Adicionar o estado final desse ingrediente
    contents: Tuple[str, ...] = ()