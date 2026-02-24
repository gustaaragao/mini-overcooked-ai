from models.entities import Order,Ingredient
from problems.kitchen_problem import KitchenProblem
from utils.state_factory import create_initial_state

def create_simple_state():
    layout = [
        "WWWWW",
        "W.P.W",
        "W.A.W",
        "W.O.W",
        "WWWWW"
    ]
    orders = [
        Order(ingredients=("Onion",), instant=0, duration=50, score=20, recipe=None)
    ]
    return create_initial_state(layout, orders)

def test_kitchen_problem_actions_movement():
    state = create_simple_state()
    problem = KitchenProblem(state)
    
    actions = problem.actions(state)
    
    assert "Move(1, 2)" in actions
    assert "Move(3, 2)" in actions
    assert "Move(2, 1)" not in actions
    assert "Move(2, 3)" not in actions

def test_kitchen_problem_actions_interaction():
    state = create_simple_state()
    problem = KitchenProblem(state)
    actions = problem.actions(state)
    
    # Verifica se gera ações
    assert "PickUp(Onion, RAW, 2, 3)" in actions
    assert "PickUp(Plate, CLEAN, 2, 1)" in actions
    
def test_kitchen_problem_result_pickup():
    state = create_simple_state()
    problem = KitchenProblem(state)
    
    # Executa pickup
    new_state = problem.result(state, "PickUp(Onion, RAW, 2, 3)")
    
    assert isinstance(new_state.held_item, Ingredient)
    assert new_state.held_item.name == "Onion"
    assert new_state.held_item.state == "RAW"
    
    # Testa se o tempo está sendo incrementado
    assert new_state.time == state.time + 1
