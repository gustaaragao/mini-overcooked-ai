from typing import Tuple, Optional, NamedTuple

class Order(NamedTuple):
    ingredients: Tuple[str, ...]
    instant: int
    duration: int
    score: int

class KitchenState(NamedTuple):
    agent_pos: Tuple[int, int]
    held_item: str # e.g., "", "Onion", "Plate"
    layout: Tuple[str, ...] # Armazena o grid estático (W, ., C, D, etc)
    # Representado como ((x, y), "Objeto") para itens dinâmicos sobre bancadas
    grid_objects: Tuple[Tuple[Tuple[int, int], str], ...]
    active_orders: Tuple[Order, ...]
    delivered_orders: Tuple[Order, ...]
    time: int = 0

    def get_layout_at(self, x: int, y: int) -> str:
        if 0 <= y < len(self.layout) and 0 <= x < len(self.layout[0]):
            return self.layout[y][x]
        return 'W' # Fora dos limites é parede

    def get_object_at(self, pos: Tuple[int, int]) -> Optional[str]:
        for obj_pos, obj_name in self.grid_objects:
            if obj_pos == pos:
                return obj_name
        return None
