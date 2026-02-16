from aima3.agents import Agent
from aima3.search import astar_search, Node
from problems.kitchen_problem import KitchenProblem

class KitchenAgent(Agent):
    def __init__(self, heuristic):
        super().__init__(program=self)
        self.heuristic = heuristic
        self.plan = []

    def __call__(self, percept):
        """O programa do agente que decide a próxima ação baseada na percepção."""
        state = percept
        
        # Se já temos um plano longo, seguimos ele. 
        # Mas para Overcooked, recalcular frequentemente pode ser melhor devido ao fogo.
        if not self.plan:
            print("[Agent] Searching for plan...")
            problem = KitchenProblem(state)
            
            # Tentamos A* normal
            solution_node = astar_search(problem, h=self.heuristic)
            
            if solution_node:
                self.plan = solution_node.solution()
                print(f"[Agent] Plan found with {len(self.plan)} actions.")
            else:
                print("[Agent] No solution found.")

        if self.plan:
            return self.plan.pop(0)
        
        return None
