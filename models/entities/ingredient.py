from typing import NamedTuple, Tuple


class Ingredient(NamedTuple):
    name: str
    state: str = "raw" # raw, chopped, cooked, burnt
    # final_state: str # TODO: Adicionar o estado final desse ingrediente
    contents: Tuple[str, ...] = ()