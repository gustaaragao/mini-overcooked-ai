import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from aima3.agents import Agent
from aima3.search import astar_search
from problems.kitchen_problem import KitchenProblem

class KitchenAgent(Agent):
    def __init__(self, heuristic):
        super().__init__(program=self)
        self.heuristic = heuristic
        self.plan = []

    def __call__(self, percept):
        """O programa do agente que decide a próxima ação baseada na percepção."""
        state = percept
        
        # Se não temos um plano, ou o plano acabou, buscamos um novo
        if not self.plan:
            print("[Agent] Formulating problem and searching for plan...")
            problem = KitchenProblem(state)
            solution_node = astar_search(problem, h=self.heuristic)
            
            if solution_node:
                # O path() do AIMA inclui o nó raiz (estado inicial), 
                # então pegamos as ações do caminho.
                self.plan = solution_node.solution()
                print(f"[Agent] Plan found with {len(self.plan)} actions.")
            else:
                print("[Agent] No solution found!")
                return None

        if self.plan:
            return self.plan.pop(0) # Retorna a primeira ação do plano
        
        return None
