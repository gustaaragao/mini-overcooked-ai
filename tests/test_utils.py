from models.entities import Order
from models.states import KitchenState
from utils.kitchen_data import load_kitchen_data
from utils.state_factory import create_initial_state

def test_load_kitchen_data_basic(tmp_path):
    # Cria um JSON temporário para os testes
    layout_data = """{
        "layout": [
            "WWWWW",
            "W P W",
            "W A W",
            "WWWWW"
        ],
        "orders": [
            {
                "ingredients": ["Onion", "Onion", "Onion"],
                "instant": 0,
                "duration": 50,
                "score": 20
            }
        ],
        "max_steps": 100
    }"""
    test_file = tmp_path / "test_layout.json"
    test_file.write_text(layout_data)

    layout, orders, max_steps = load_kitchen_data(str(test_file))

    assert len(layout) == 4
    assert len(orders) == 1
    assert max_steps == 100
    assert orders[0].duration == 50
    assert orders[0].score == 20
    assert orders[0].ingredients == ("Onion", "Onion", "Onion")

def test_create_initial_state():
    layout = [
        "WWWWW",
        "W P W",
        "W A W",
        "WWWWW"
    ]
    orders = [
        Order(ingredients=("Onion",), instant=0, duration=50, score=20, recipe=None)
    ]
    
    state = create_initial_state(layout, orders)
    
    assert isinstance(state, KitchenState)
    assert state.agent_pos == (2, 2)
    assert state.layout[1] == "W C W"
    assert len(state.grid_objects) == 1
    assert state.grid_objects[0][0] == (2, 1)
    assert state.grid_objects[0][1].state == "CLEAN"
