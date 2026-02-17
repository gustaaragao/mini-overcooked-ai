import sys
import argparse
import os
from utils import load_kitchen_data, create_initial_state
from env.kitchen_env import KitchenEnvironment
from agents.kitchen_agent import KitchenAgent
from problems.kitchen_problem import KitchenProblem

def run():
    parser = argparse.ArgumentParser(description="Mini-Overcooked Simulation")
    parser.add_argument("layout", nargs="?", default="layouts/overcooked1.json", help="Path to layout file")
    parser.add_argument("--debug", action="store_true", help="Interactive step-by-step mode")
    parser.add_argument("--batch", action="store_true", help="Non-interactive mode with silent logging")
    
    args = parser.parse_args()
    layout_path = args.layout

    # Output: save only the environment render
    out_dir = "out"
    os.makedirs(out_dir, exist_ok=True)
    render_path = os.path.join(out_dir, "render.txt")
    
    # 1. Carrega dados
    layout, orders, max_steps = load_kitchen_data(layout_path)
    initial_state = create_initial_state(layout, orders)
    
    # 2. Inicializa Ambiente
    env = KitchenEnvironment(initial_state)
    
    # 3. Inicializa o Agente com sua Heurística
    problem = KitchenProblem(initial_state)
    agent = KitchenAgent(heuristic=problem.h)
    
    # Adicionamos o agente ao ambiente
    env.add_thing(agent)

    render_f = open(render_path, "w", encoding="utf-8")
    try:
        render_f.write(f"--- Render Log ({layout_path}) ---\n")
        render_f.write("\n--- Initial State ---\n")
        env.render(out=render_f, quiet=args.batch)
    
        if not args.batch:
            print(f"--- Initial State ({layout_path}) ---")
            env.render()

        # 4. Simulação: Avança o ambiente até o objetivo ou limite
        for step in range(max_steps):
            if not args.batch:
                print(f"\n--- Step {step + 1} / {max_steps} ---")

            # O ambiente obtém a percepção, passa para o agente,
            # e executa a ação retornada pelo programa do agente.
            env.step()

            render_f.write(f"\n--- Step {step + 1} ---\n")
            env.render(out=render_f, quiet=args.batch)

            if not args.batch:
                env.render()

            if args.debug:
                input("\n[DEBUG] Press ENTER to continue to the next step...")

            if len(env.state.active_orders) == 0:
                print("\n[Simulation] All orders delivered! Goal reached.")
                break
        else:
            print("\n[Simulation] Max steps reached.")

    finally:
        render_f.close()

    print(f"\n[Simulation] Finished. Render saved to {render_path}.")

if __name__ == "__main__":
    run()
