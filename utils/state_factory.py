from typing import List, Tuple

from models.entities import Ingredient, Order, Plate, Extinguisher
from models.states import KitchenState, StationState


def create_initial_state(layout: List[str], orders: List[Order]) -> KitchenState:
    agent_pos: Tuple[int, int] = (0, 0)
    clean_layout: List[str] = []
    stations_state_list = []
    grid_objects_list = []

    for y, row in enumerate(layout):
        row_list = list(row)
        for x, char in enumerate(row_list):
            if char == "A":
                agent_pos = (x, y)
                row_list[x] = "."  # Agent starts on floor
            elif char in ("S", "T", "B", "W", "R", "N"):  # Stove, Cutting Board (T/B), Sink (W), Counter (R)
                stations_state_list.append(((x, y), StationState()))
            elif char == "P":  # Initial Clean Plate on Counter
                grid_objects_list.append(
                    ((x, y), Plate(state="CLEAN"))
                )
                row_list[x] = "C"  # Plates start on a counter
            elif char == "E":  # Extinguisher on Counter
                grid_objects_list.append(((x, y), Extinguisher()))
                row_list[x] = "C"  # Extinguishers start on a counter
        clean_layout.append("".join(row_list))

    return KitchenState(
        agent_pos=agent_pos,
        held_item=None,
        layout=tuple(clean_layout),
        grid_objects=tuple(sorted(grid_objects_list, key=lambda x: x[0])),
        active_orders=tuple(orders),
        delivered_orders=(),
        stations_state=tuple(sorted(stations_state_list, key=lambda x: x[0])),
        time=0,
    )
