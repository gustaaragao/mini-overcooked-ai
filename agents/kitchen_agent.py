import heapq
import time
from math import inf

from aima3.agents import Agent
from aima3.search import Node

from problems.kitchen_problem import KitchenProblem


def limited_astar_search(problem, h, *, max_expansions: int = 20_000, max_time_s: float = 1.0):
    """A* com limites para evitar travar a simulação.

    Retorna (solution_node, stats). solution_node pode ser None se estourar limite.
    """
    start_t = time.monotonic()

    root = Node(problem.initial)
    root_f = root.path_cost + h(root)

    frontier = []
    push_count = 0
    heapq.heappush(frontier, (root_f, push_count, root))

    best_g = {root.state: 0}
    expansions = 0

    while frontier:
        if (time.monotonic() - start_t) > max_time_s:
            return None, {"reason": "timeout", "expansions": expansions, "frontier": len(frontier)}

        _, _, node = heapq.heappop(frontier)

        if problem.goal_test(node.state):
            return node, {"reason": "goal", "expansions": expansions, "frontier": len(frontier)}

        expansions += 1
        if expansions > max_expansions:
            return None, {"reason": "max_expansions", "expansions": expansions, "frontier": len(frontier)}

        for child in node.expand(problem):
            child_g = child.path_cost
            prev_g = best_g.get(child.state, inf)
            if child_g < prev_g:
                best_g[child.state] = child_g
                push_count += 1
                heapq.heappush(frontier, (child_g + h(child), push_count, child))

    return None, {"reason": "no_solution", "expansions": expansions, "frontier": 0}

class KitchenAgent(Agent):
    def __init__(self, heuristic):
        super().__init__(program=self)
        self.heuristic = heuristic
        self.plan = []
        self._cooldown_until_time = 0
        self._planning_time_s = 0.2
        self._planning_max_expansions = 8_000
        self._planning_cooldown_steps = 5

    def __call__(self, percept):
        """O programa do agente que decide a próxima ação baseada na percepção."""
        state = percept

        if state.time < self._cooldown_until_time:
            return None
        
        # Se já temos um plano longo, seguimos ele. 
        # Mas para Overcooked, recalcular frequentemente pode ser melhor devido ao fogo.
        if not self.plan:
            print("[Agent] Searching for plan...")
            problem = KitchenProblem(state)
            
            solution_node, stats = limited_astar_search(
                problem,
                self.heuristic,
                max_expansions=self._planning_max_expansions,
                max_time_s=self._planning_time_s,
            )
            
            if solution_node:
                self.plan = solution_node.solution()
                print(f"[Agent] Plan found with {len(self.plan)} actions.")
            else:
                print(f"[Agent] Planning aborted: {stats['reason']} (expanded={stats['expansions']}, frontier={stats['frontier']}).")
                # Evita tentar planejar de novo em todo tick quando está difícil.
                self._cooldown_until_time = state.time + self._planning_cooldown_steps

        if self.plan:
            return self.plan.pop(0)
        
        return None
