from typing import Tuple, Optional, NamedTuple, Dict

class Order(NamedTuple):
    ingredients: Tuple[str, ...]
    instant: int
    duration: int
    score: int

class Ingredient(NamedTuple):
    name: str
    state: str = "raw" # raw, chopped, cooked, burnt

class StationState(NamedTuple):
    progress: int = 0
    is_on_fire: bool = False
    content: Optional[Ingredient] = None

class KitchenState(NamedTuple):
    agent_pos: Tuple[int, int]
    held_item: Optional[Ingredient] # can be None
    layout: Tuple[str, ...] # Armazena o grid estático (W, ., C, D, etc)
    # Representado como ((x, y), Ingredient) para itens dinâmicos sobre bancadas
    grid_objects: Tuple[Tuple[Tuple[int, int], Ingredient], ...]
    active_orders: Tuple[Order, ...]
    delivered_orders: Tuple[Order, ...]
    # Mapeamento de (x, y) para estado da estação (fogão, tábua de corte)
    stations_state: Tuple[Tuple[Tuple[int, int], StationState], ...]
    time: int = 0

    def get_layout_at(self, x: int, y: int) -> str:
        if 0 <= y < len(self.layout) and 0 <= x < len(self.layout[0]):
            return self.layout[y][x]
        return 'W' # Fora dos limites é parede

    def get_object_at(self, pos: Tuple[int, int]) -> Optional[Ingredient]:
        for obj_pos, obj in self.grid_objects:
            if obj_pos == pos:
                return obj
        return None

    def get_station_state_at(self, pos: Tuple[int, int]) -> Optional[StationState]:
        for s_pos, s_state in self.stations_state:
            if s_pos == pos:
                return s_state
        return None
