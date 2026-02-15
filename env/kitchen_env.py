from aima3.agents import Environment
from models.models import KitchenState

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
        # Cria cópia do layout para renderização
        render_grid = [list(row) for row in self.state.layout]
        
        # Insere objetos dinâmicos
        for (x, y), obj_name in self.state.grid_objects:
            # Pega primeira letra ou símbolo
            render_grid[y][x] = obj_name[0]
            
        # Insere o agente
        ax, ay = self.state.agent_pos
        render_grid[ay][ax] = 'A'
        
        print(f"\nTime: {self.state.time} | Holding: {self.state.held_item or 'Nothing'}")
        print("+" + "---" * self.width + "+")
        for row in render_grid:
            print("| " + "  ".join(row) + " |")
        print("+" + "---" * self.width + "+")
        
        if self.state.active_orders:
            print("Active Orders:", [", ".join(o.ingredients) for o in self.state.active_orders])
