from aima3.agents import Environment
from models.states import KitchenState

class KitchenEnvironment(Environment):
    def __init__(self, initial_state: KitchenState):
        super().__init__()
        self.state = initial_state
        self.height = len(initial_state.layout)
        self.width = len(initial_state.layout[0])

    def thing_classes(self):
        return []

    def percept(self, agent):
        return self.state

    def execute_action(self, agent, action):
        from problems.kitchen_problem import KitchenProblem
        if action:
            problem = KitchenProblem(self.state)
            self.state = problem.result(self.state, action)
        else:
            # Incrementa o tempo mesmo sem ação para evitar loops infinitos
            self.state = self.state._replace(time=self.state.time + 1)

    def render(self):
        from models.entities import Ingredient, Plate, Extinguisher
        # Cria cópia do layout para renderização
        render_grid = [list(row) for row in self.state.layout]
        
        # Estações e seus estados
        for (x, y), s_state in self.state.stations_state:
            if s_state.is_on_fire:
                render_grid[y][x] = 'F' # Fire
            elif s_state.content:
                if isinstance(s_state.content, Plate):
                    render_grid[y][x] = 'p'
                elif isinstance(s_state.content, Extinguisher):
                    render_grid[y][x] = 'e'
                else:
                    render_grid[y][x] = s_state.content.name[0].lower()

        # Insere objetos dinâmicos
        for (x, y), obj in self.state.grid_objects:
            if isinstance(obj, Plate):
                render_grid[y][x] = 'P'
            elif isinstance(obj, Extinguisher):
                render_grid[y][x] = 'E'
            else:
                render_grid[y][x] = obj.name[0]
            
        # Insere o agente
        ax, ay = self.state.agent_pos
        render_grid[ay][ax] = 'A'
        
        held = self.state.held_item
        if held:
            if isinstance(held, Plate):
                holding_str = f"Plate({held.state})"
            elif isinstance(held, Extinguisher):
                holding_str = "Extinguisher"
            else:
                holding_str = f"{held.name}({held.state})"
        else:
            holding_str = 'Nothing'

        print(f"\nTime: {self.state.time} | Holding: {holding_str}")
        print("+" + "---" * self.width + "+")
        for row in render_grid:
            print("| " + "  ".join(row) + " |")
        print("+" + "---" * self.width + "+")
        
        if self.state.active_orders:
            print("Active Orders:", [", ".join(o.ingredients) for o in self.state.active_orders])
        
        # Mostra detalhes das estações
        for pos, s_state in self.state.stations_state:
            if s_state.content or s_state.is_on_fire:
                content = s_state.content
                if isinstance(content, Plate):
                    content_str = f"Plate({content.state})"
                elif isinstance(content, Extinguisher):
                    content_str = "Extinguisher"
                elif content:
                    content_str = f"{content.name}({content.state})"
                else:
                    content_str = "EMPTY"
                fire_str = "!!! ON FIRE !!!" if s_state.is_on_fire else ""
                print(f"  Station at {pos}: {content_str} | Progress: {s_state.progress} {fire_str}")
