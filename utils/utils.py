import json
from typing import Tuple, List, Dict, Optional
from models.models import Order, KitchenState, Ingredient, StationState

def load_kitchen_data(file_path: str) -> Tuple[List[str], List[Order], int]:
    with open(file_path, 'r') as f:
        data = json.load(f)
    
    layout = data.get("layout", [])
    orders_data = data.get("orders", [])
    max_steps = data.get("max_steps", 20)
    
    orders = []
    for o in orders_data:
        orders.append(Order(
            ingredients=tuple(o["ingredients"]),
            instant=o["instant"],
            duration=o["duration"],
            score=o["score"]
        ))
    
    return layout, orders, max_steps

def create_initial_state(layout: List[str], orders: List[Order]) -> KitchenState:
    agent_pos = (0, 0)
    clean_layout = []
    stations_state_list = []
    grid_objects_list = []
    
    for y, row in enumerate(layout):
        row_list = list(row)
        for x, char in enumerate(row_list):
            if char == 'A':
                agent_pos = (x, y)
                row_list[x] = '.' # Agent starts on floor
            elif char in ('S', 'B', 'K'): # Stove, Cutting Board, Sink
                stations_state_list.append(((x, y), StationState()))
            elif char == 'P': # Initial Clean Plate
                grid_objects_list.append(((x, y), Ingredient(name="Plate", state="clean")))
                row_list[x] = 'C' # Plates start on a counter
        clean_layout.append("".join(row_list))
    
    return KitchenState(
        agent_pos=agent_pos,
        held_item=None,
        layout=tuple(clean_layout),
        grid_objects=tuple(grid_objects_list),
        active_orders=tuple(orders),
        delivered_orders=(),
        stations_state=tuple(stations_state_list),
        time=0
    )
