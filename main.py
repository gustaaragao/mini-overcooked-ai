import os
import sys
import argparse

from utils import load_kitchen_data, create_initial_state
from env.kitchen_env import KitchenEnvironment
from agents.kitchen_agent import KitchenAgent
from problems.kitchen_problem import KitchenProblem

def _wait_for_key(prompt: str = "\n[Pressione qualquer tecla para avançar...]") -> None:  # aguarda tecla sem Enter
    print(prompt, end="", flush=True)
    if sys.platform == "win32":
        import msvcrt
        msvcrt.getch()
    else:
        import tty, termios
        fd = sys.stdin.fileno()
        old = termios.tcgetattr(fd)
        try:
            tty.setraw(fd)
            sys.stdin.read(1)
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old)
    print()  # nova linha após a tecla


def _clear_screen() -> None:
    os.system("cls" if sys.platform == "win32" else "clear")

# Simulação principal
def run():
    parser = argparse.ArgumentParser(description="Simulação Mini-Overcooked")
    parser.add_argument(
        "layout",
        nargs="?",
        default="layouts/overcooked1.json",
        help="Caminho para o arquivo de layout (padrão: layouts/overcooked1.json)",
    )
    parser.add_argument(
        "--auto",
        action="store_true",
        help="Modo automático: executa sem interação, gera apenas out/render.txt",
    )

    args = parser.parse_args()
    layout_path = args.layout
    interactive = not args.auto

    # Diretório de saída dos renders
    out_dir = "out"
    os.makedirs(out_dir, exist_ok=True)
    render_path = os.path.join(out_dir, "render.txt")

    # 1. Lê o layout JSON e constrói os pedidos
    layout, orders, max_steps = load_kitchen_data(layout_path)
    initial_state = create_initial_state(layout, orders)

    # 2. Inicializa o ambiente, o agente com sua heurística e registra o agente
    env = KitchenEnvironment(initial_state)
    problem = KitchenProblem(initial_state)
    agent = KitchenAgent(heuristic=problem.h)
    env.add_thing(agent)

    # 3. Renderiza e registra o estado inicial
    render_lines = [f"--- Render Log ({layout_path}) ---\n", "\n--- Estado Inicial ---\n"]
    initial_render = env.render(quiet=True)
    render_lines.append(initial_render)

    if interactive:
        _clear_screen()  # limpa o terminal antes de exibir
        print(f"=== Mini-Overcooked | Nível: {layout_path} ===")
        print("\n--- Estado Inicial ---")
        print(initial_render)
        # Salva o estado inicial como step 000
        step_path = os.path.join(out_dir, "step_000.txt")
        with open(step_path, "w", encoding="utf-8") as sf:
            sf.write("--- Estado Inicial ---\n")
            sf.write(initial_render)
        _wait_for_key()

    # 4. Loop principal da simulação
    for step in range(1, max_steps + 1):
        env.step()

        step_render = env.render(quiet=True)
        step_header = f"\n--- Passo {step} / {max_steps} ---\n"
        render_lines.append(step_header)
        render_lines.append(step_render)

        if interactive:
            _clear_screen()
            print(f"=== Mini-Overcooked | Nível: {layout_path} ===")
            print(f"--- Passo {step} / {max_steps} ---")
            print(step_render)
            # Salva o estado atual em arquivo individual
            step_path = os.path.join(out_dir, f"step_{step:03d}.txt")
            with open(step_path, "w", encoding="utf-8") as sf:
                sf.write(f"--- Passo {step} ---\n")
                sf.write(step_render)

        # Verifica se o objetivo foi alcançado
        if len(env.state.active_orders) == 0:
            msg = "\n[Simulação] Todos os pedidos entregues! Objetivo alcançado."
            print(msg)
            render_lines.append(msg + "\n")
            break

        if interactive:
            _wait_for_key()
    else:
        msg = "\n[Simulação] Limite de passos atingido."
        print(msg)
        render_lines.append(msg + "\n")

    # 5. Salva o log completo em render.txt
    with open(render_path, "w", encoding="utf-8") as rf:
        rf.write("".join(render_lines))

    print(f"\n[Simulação] Finalizada. Render salvo em {render_path}.")


if __name__ == "__main__":
    run()
