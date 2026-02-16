from aima3.agents import Agent
from aima3.search import astar_search, Node
from problems.kitchen_problem import KitchenProblem

class KitchenAgent(Agent):
    def __init__(self, heuristic, lookahead_k=5):
        super().__init__(program=self)
        self.heuristic = heuristic
        self.lookahead_k = lookahead_k
        self.plan = []

    def __call__(self, percept):
        """O programa do agente que decide a próxima ação baseada na percepção."""
        state = percept
        
        # Se já temos um plano longo, seguimos ele. 
        # Mas para Overcooked, recalcular frequentemente pode ser melhor devido ao fogo.
        if not self.plan:
            print(f"[Agent] Searching for plan (lookahead k={self.lookahead_k})...")
            problem = KitchenProblem(state)
            
            # Tentamos A* normal primeiro
            solution_node = astar_search(problem, h=self.heuristic)
            
            if solution_node:
                self.plan = solution_node.solution()
                print(f"[Agent] Plan found with {len(self.plan)} actions.")
            else:
                # Se falhar (espaço muito grande), poderíamos fazer busca limitada
                print("[Agent] No full solution found, attempting greedy lookahead...")
                self.plan = self.greedy_lookahead(state, k=self.lookahead_k)

        if self.plan:
            return self.plan.pop(0)
        
        return None

    def greedy_lookahead(self, state, k):
        """Busca a melhor sequência de k ações usando a heurística."""
        problem = KitchenProblem(state)
        # Simplificação: Explora k níveis e pega o nó com menor h
        best_node = None
        min_h = float('inf')
        
        queue = [Node(state)]
        for _ in range(k):
            next_queue = []
            for node in queue:
                for action in problem.actions(node.state):
                    child = node.child_node(problem, action)
                    h_val = self.heuristic(child)
                    if h_val < min_h:
                        min_h = h_val
                        best_node = child
                    next_queue.append(child)
            if not next_queue: break
            queue = next_queue
            
        if best_node:
            return best_node.solution()
        return []
