import json
from typing import List, Tuple

from models.entities import Order, Recipe, RecipeStep


def load_kitchen_data(file_path: str) -> Tuple[List[str], List[Order], int]:
    with open(file_path, "r") as f:
        data = json.load(f)

    layout = data.get("layout", [])
    orders_data = data.get("orders", [])
    max_steps = data.get("max_steps", 20)

    orders: List[Order] = []
    for o in orders_data:
        # Build recipe if defined in JSON
        recipe = None
        if "recipe" in o:
            steps = tuple(
                RecipeStep(
                    ingredient=s["ingredient"],
                    required_state=s["required_state"],
                    quantity=s.get("quantity", 1),
                )
                for s in o["recipe"]["steps"]
            )
            recipe = Recipe(name=o["recipe"]["name"], steps=steps)

        orders.append(
            Order(
                ingredients=tuple(o["ingredients"]),
                instant=o["instant"],
                duration=o["duration"],
                score=o["score"],
                recipe=recipe,
            )
        )

    return layout, orders, max_steps
