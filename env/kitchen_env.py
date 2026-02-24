from aima3.agents import Environment
from models.states import KitchenState


class KitchenEnvironment(Environment):
    def __init__(self, initial_state: KitchenState):
        super().__init__()
        self.state = initial_state
        self.height = len(initial_state.layout)
        self.width = len(initial_state.layout[0])
        self.history = []  # Lista de tuplas (state, action)

    def thing_classes(self):
        return []

    def percept(self, agent):
        return self.state

    def execute_action(self, agent, action):
        from problems.kitchen_problem import KitchenProblem
        prev_state = self.state
        if action:
            problem = KitchenProblem(self.state)
            self.state = problem.result(self.state, action)
        else:
            # Incrementa o tempo mesmo sem ação
            self.state = self.state._replace(time=self.state.time + 1)

        self.history.append((prev_state, action))

    def render(self, out=None, quiet: bool = False) -> str:
        from models.entities import Ingredient, Plate, Extinguisher, Pot

        render_grid = [list(row) for row in self.state.layout]

        # Estações e seus estados
        for (x, y), s_state in self.state.stations_state:
            if s_state.is_on_fire:
                render_grid[y][x] = 'F'
            elif s_state.content:
                obj = s_state.content
                if isinstance(obj, Plate):
                    render_grid[y][x] = 'p'
                elif isinstance(obj, Extinguisher):
                    render_grid[y][x] = 'e'
                elif isinstance(obj, Pot):
                    state_char = {'EMPTY': 'k', 'FILLING': 'f', 'COOKING': 'c', 'READY': 'R'}
                    render_grid[y][x] = state_char.get(obj.state, 'k')
                else:
                    render_grid[y][x] = obj.name[0].lower()

        # Objetos dinâmicos sobre balcões
        for (x, y), obj in self.state.grid_objects:
            if isinstance(obj, Plate):
                render_grid[y][x] = 'P'
            elif isinstance(obj, Extinguisher):
                render_grid[y][x] = 'E'
            else:
                render_grid[y][x] = obj.name[0]

        # Agente
        ax, ay = self.state.agent_pos
        render_grid[ay][ax] = 'A'

        # Legenda do que o agente segura
        held = self.state.held_item
        if held is None:
            holding_str = 'Nada'
        elif isinstance(held, Plate):
            if held.contents:
                holding_str = f"Prato({held.state}, [{', '.join(held.contents)}])"
            else:
                holding_str = f"Prato({held.state})"
        elif isinstance(held, Extinguisher):
            holding_str = "Extintor"
        else:
            holding_str = f"{held.name}({held.state})"

        lines = []
        lines.append(f"\nTempo: {self.state.time} | Segurando: {holding_str}")
        lines.append("+" + "---" * self.width + "+")
        for row in render_grid:
            lines.append("| " + "  ".join(row) + " |")
        lines.append("+" + "---" * self.width + "+")

        # Pedidos ativos
        if self.state.active_orders:
            order_strs = []
            for o in self.state.active_orders:
                name = o.recipe.name if o.recipe else "/".join(o.ingredients)
                order_strs.append(name)
            lines.append("Pedidos ativos: " + ", ".join(order_strs))

        # Detalhes das estações
        for pos, s_state in self.state.stations_state:
            if s_state.content or s_state.is_on_fire:
                obj = s_state.content
                if isinstance(obj, Plate):
                    content_str = f"Prato({obj.state})"
                elif isinstance(obj, Extinguisher):
                    content_str = "Extintor"
                elif isinstance(obj, Pot):
                    content_str = f"Panela({obj.state}, [{', '.join(obj.ingredients)}], prog={obj.progress})"
                elif obj:
                    content_str = f"{obj.name}({obj.state})"
                else:
                    content_str = "VAZIO"
                fire_str = "  !!! EM CHAMAS !!!" if s_state.is_on_fire else ""
                lines.append(f"  Estação em {pos}: {content_str} | Progresso: {s_state.progress}{fire_str}")

        # Legenda rápida
        lines.append("\nLegenda: A=Agente, K=Panela(vazia), f=Panela(enchendo), c=Panela(cozinhando), R=Panela(pronta)")
        lines.append("         O=Fonte Cebola, V=Fonte Tomate, T/B=Tábua, S=Fogão, W=Pia, D=Entrega, G=Lixo")

        rendered = "\n".join(lines) + "\n"
        if out is not None:
            out.write(rendered)
        if not quiet:
            print(rendered, end="")
        return rendered
