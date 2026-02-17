from typing import NamedTuple, Optional, Tuple, Union

from models.entities import Order, Ingredient, Plate, Extinguisher
from models.states.station_state import StationState

KitchenItem = Union[Ingredient, Plate, Extinguisher]


class KitchenState(NamedTuple):
    agent_pos: Tuple[int, int]
    held_item: Optional[KitchenItem] # can be None
    layout: Tuple[str, ...] # Armazena o grid estático (W, ., C, D, etc)
    # Representado como ((x, y), KitchenItem) para itens dinâmicos sobre bancadas
    grid_objects: Tuple[Tuple[Tuple[int, int], KitchenItem], ...]
    active_orders: Tuple[Order, ...]
    delivered_orders: Tuple[Order, ...]
    # Mapeamento de (x, y) para estado da estação (fogão, tábua de corte)
    stations_state: Tuple[Tuple[Tuple[int, int], StationState], ...]
    time: int = 0

    def _search_key(self):
        """Key used for hashing/equality in search.

        The simulator uses `time` for rendering and logs, but including it in
        the state identity makes every step unique and prevents cycle
        detection in graph search (A*, UCS, etc.). For planning we want the
        state identity to depend on the physical configuration, not the tick
        counter.
        """
        # Sort objects by position to ensure canonical representation
        # grid_objects is ((pos, item), ...)
        sorted_objects = tuple(sorted(self.grid_objects, key=lambda x: x[0]))
        # stations_state is ((pos, s_state), ...)
        sorted_stations = tuple(sorted(self.stations_state, key=lambda x: x[0]))

        return (
            self.agent_pos,
            self.held_item,
            self.layout,
            sorted_objects,
            self.active_orders,
            self.delivered_orders,
            sorted_stations,
        )

    def __hash__(self):
        return hash(self._search_key())

    def __eq__(self, other):
        if not isinstance(other, KitchenState):
            return False
        return self._search_key() == other._search_key()

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

    def is_impassable(self, x: int, y: int) -> bool:
        """Returns True if the cell is impassable for movement (anything not floor '.')."""
        return self.get_layout_at(x, y) != '.'

    def __lt__(self, other):
        return self.time < other.time
