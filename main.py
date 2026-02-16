import sys
from utils import load_kitchen_data, create_initial_state
from env.kitchen_env import KitchenEnvironment
from agents.kitchen_agent import KitchenAgent
from problems.kitchen_problem import KitchenProblem

def run():
    layout_path = sys.argv[1] if len(sys.argv) > 1 else "layouts/overcooked1.json"
    # 1. Carrega dados
    layout, orders, max_steps = load_kitchen_data(layout_path)
    initial_state = create_initial_state(layout, orders)
    
    # 2. Inicializa Ambiente
    env = KitchenEnvironment(initial_state)
    
    # 3. Inicializa o Agente com sua Heurística
    temp_problem = KitchenProblem(initial_state)
    agent = KitchenAgent(heuristic=temp_problem.h)
    
    # Adicionamos o agente ao ambiente
    env.add_thing(agent)
    
    print(f"--- Initial State ({layout_path}) ---")
    env.render()
    
    # 4. Simulação: Avança o ambiente até o objetivo ou limite
    for step in range(max_steps):
        print(f"\n--- Step {step + 1} / {max_steps} ---")
        
        # O ambiente obtém a percepção, passa para o agente, 
        # e executa a ação retornada pelo programa do agente.
        env.step()
        env.render()
        
        if len(env.state.active_orders) == 0:
            print("\n[Simulation] All orders delivered! Goal reached.")
            break
    else:
        print("\n[Simulation] Max steps reached.")

if __name__ == "__main__":
    run()
