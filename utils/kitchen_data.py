import json
from typing import List, Tuple

from models.entities import Order


def load_kitchen_data(file_path: str) -> Tuple[List[str], List[Order], int]:
    with open(file_path, "r") as f:
        data = json.load(f)

    layout = data.get("layout", [])
    orders_data = data.get("orders", [])
    max_steps = data.get("max_steps", 20)

    orders: List[Order] = []
    for o in orders_data:
        orders.append(
            Order(
                ingredients=tuple(o["ingredients"]),
                instant=o["instant"],
                duration=o["duration"],
                score=o["score"],
            )
        )

    return layout, orders, max_steps
