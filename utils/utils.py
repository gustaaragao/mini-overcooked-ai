import json
from typing import Tuple, List, Dict
from models.models import Order, KitchenState

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
    
    for y, row in enumerate(layout):
        if 'A' in row:
            agent_pos = (row.find('A'), y)
            # Substitui 'A' por '.' no layout estático para o agente poder se mover
            clean_layout.append(row.replace('A', '.'))
        else:
            clean_layout.append(row)
    
    return KitchenState(
        agent_pos=agent_pos,
        held_item="",
        layout=tuple(clean_layout),
        grid_objects=(), # Itens dinâmicos começam vazios
        active_orders=tuple(orders),
        delivered_orders=(),
        time=0
    )
