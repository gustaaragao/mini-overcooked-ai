import heapq
import time
from math import inf

from aima3.agents import Agent
from aima3.search import Node, astar_search

from problems.kitchen_problem import KitchenProblem
from models.entities import Ingredient, Plate, Extinguisher


def astar_search_with_limit(problem, h, max_expansions=50000, max_time_s=5.0):
    """A* search with expansion and time limits."""
    start_t = time.monotonic()
    node = Node(problem.initial)
    if problem.goal_test(node.state):
        return node
    
    frontier = []
    push_count = 0
    h_val = h(node)
    heapq.heappush(frontier, (node.path_cost + h_val, h_val, push_count, node))
    
    explored = {node.state: node.path_cost}
    expansions = 0
    
    while frontier:
        elapsed = time.monotonic() - start_t
        if elapsed > max_time_s:
            return None

        f, hv, pc, node = heapq.heappop(frontier)
        
        if problem.goal_test(node.state):
            return node
        
        expansions += 1
        if expansions > max_expansions:
            return None
            
        for child in node.expand(problem):
            if child.state not in explored or child.path_cost < explored[child.state]:
                explored[child.state] = child.path_cost
                push_count += 1
                ch_val = h(child)
                heapq.heappush(frontier, (child.path_cost + ch_val, ch_val, push_count, child))
                
    return None


class KitchenAgent(Agent):
    def __init__(self, heuristic):
        super().__init__(program=self)
        self.heuristic = heuristic
        self.plan = []
        self.debug_info = {}

    def get_subgoal_test(self, state):
        """Identifies a reachable sub-goal based on the current state."""
        # 1. Fire Priority
        if any(s.is_on_fire for _, s in state.stations_state):
            if isinstance(state.held_item, Extinguisher):
                return lambda s: any(st.is_on_fire for _, st in s.stations_state) == False
            else:
                return lambda s: isinstance(s.held_item, Extinguisher)

        # 2. Station progress sub-goals (Chop, Cook, Wash)
        for pos, s_state in state.stations_state:
            if s_state.content:
                # If RAW ingredient on Cutting Board -> Goal: CHOPPED
                if state.get_layout_at(pos[0], pos[1]) in ('T', 'B') and s_state.content.state == 'RAW':
                    return lambda s: any(st_pos == pos and st.content and st.content.state == 'CHOPPED' for st_pos, st in s.stations_state)
                # If CHOPPED ingredient on Stove -> Goal: COOKED
                if state.get_layout_at(pos[0], pos[1]) == 'S' and s_state.content.state == 'CHOPPED':
                    return lambda s: any(st_pos == pos and st.content and st.content.state == 'COOKED' for st_pos, st in s.stations_state)
                # If DIRTY plate on Sink -> Goal: CLEAN
                if state.get_layout_at(pos[0], pos[1]) == 'W' and isinstance(s_state.content, Plate) and s_state.content.state == 'DIRTY':
                    return lambda s: any(st_pos == pos and st.content and st.content.state == 'CLEAN' for st_pos, st in s.stations_state)

        # 3. If holding RAW ingredient: Go to Station (Cutting Board)
        if isinstance(state.held_item, Ingredient) and state.held_item.state == 'RAW':
            return lambda s: any(st.content == state.held_item for _, st in s.stations_state)

        # 4. If holding CHOPPED ingredient: Go to Station (Stove)
        if isinstance(state.held_item, Ingredient) and state.held_item.state == 'CHOPPED':
            return lambda s: any(st.content == state.held_item for _, st in s.stations_state)

        # 5. If holding CLEAN Plate: Pick up COOKED food
        if isinstance(state.held_item, Plate) and state.held_item.state == 'CLEAN':
            if any(s.content and isinstance(s.content, Ingredient) and s.content.state == 'COOKED' for _, s in state.stations_state):
                return lambda s: isinstance(s.held_item, Plate) and s.held_item.state == "WITH_FOOD"

        # 6. If holding Plate WITH_FOOD: Go to Delivery
        if isinstance(state.held_item, Plate) and state.held_item.state == 'WITH_FOOD':
            return lambda s: len(s.active_orders) < len(state.active_orders)

        # 7. If holding nothing
        if state.held_item is None:
            # If something is cooked, get a plate
            cooked_exists = any(s.content and isinstance(s.content, Ingredient) and s.content.state == 'COOKED' for _, s in state.stations_state)
            if cooked_exists:
                plate_exists = any(isinstance(obj, Plate) and obj.state == "CLEAN" for _, obj in state.grid_objects)
                if plate_exists:
                    return lambda s: isinstance(s.held_item, Plate) and s.held_item.state == "CLEAN"
            
            # If nothing is on cutting board or stove, get an onion
            if not any(s.content for _, s in state.stations_state):
                return lambda s: isinstance(s.held_item, Ingredient) and s.held_item.name == "Onion"

        return None

    def __call__(self, percept):
        """O programa do agente que decide a próxima ação baseada na percepção."""
        state = percept
        self.debug_info = {"step": state.time, "plan_found": False}

        if not self.plan:
            subgoal_fn = self.get_subgoal_test(state)
            
            if subgoal_fn:
                print(f"[Agent] Searching for sub-goal plan (step={state.time})...")
                problem = KitchenProblem(state, goal_test_fn=subgoal_fn)
                solution_node = astar_search_with_limit(problem, lambda n: 0, max_expansions=100000)
            else:
                print(f"[Agent] Searching for full goal plan (step={state.time})...")
                problem = KitchenProblem(state)
                solution_node = astar_search_with_limit(problem, self.heuristic, max_expansions=200000)
            
            if solution_node:
                self.plan = solution_node.solution()
                self.debug_info["plan_found"] = True
                self.debug_info["plan_length"] = len(self.plan)
                print(f"[Agent] Plan found with {len(self.plan)} actions.")
            else:
                self.debug_info["plan_found"] = False
                print(f"[Agent] No plan found.")
                return None

        if self.plan:
            action = self.plan.pop(0)
            self.debug_info["action"] = action
            return action
        
        return None
