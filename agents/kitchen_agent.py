import heapq
import time
from math import inf

from aima3.agents import Agent
from aima3.search import Node, astar_search

from problems.kitchen_problem import KitchenProblem, FRYABLE, BOILABLE
from models.entities import Ingredient, Plate, Extinguisher


def astar_search_with_limit(problem, h, max_expansions=500000, max_time_s=5.0):
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
                targets = [pos for pos, s in state.stations_state if s.is_on_fire]
                return lambda s: not any(st.is_on_fire for _, st in s.stations_state), targets
            else:
                ext_pos = []
                for y, row in enumerate(state.layout):
                    for x, char in enumerate(row):
                        if char == 'E': ext_pos.append((x, y))
                for pos, obj in state.grid_objects:
                    if isinstance(obj, Extinguisher): ext_pos.append(pos)
                return lambda s: isinstance(s.held_item, Extinguisher), ext_pos

        # 2. Station progress sub-goals (Chop on T/B, Cook/Boil on S, Fry on N, Wash on W)
        for pos, s_state in state.stations_state:
            tile = state.get_layout_at(pos[0], pos[1])
            content = s_state.content
            if not content:
                continue

            # Cutting board: RAW → CHOPPED
            if tile in ('T', 'B') and isinstance(content, Ingredient) and content.state == 'RAW':
                return lambda s, _pos=pos: any(
                    st_pos == _pos and st.content and st.content.state == 'CHOPPED'
                    for st_pos, st in s.stations_state
                ), [pos]

            # Stove: RAW Boilable or CHOPPED → COOKED
            if tile == 'S' and isinstance(content, Ingredient) and content.state in ('RAW', 'CHOPPED'):
                return lambda s, _pos=pos: any(
                    st_pos == _pos and st.content and st.content.state == 'COOKED'
                    for st_pos, st in s.stations_state
                ), [pos]

            # Frying pan: CHOPPED Fryable → FRIED
            if tile == 'N' and isinstance(content, Ingredient) and content.state == 'CHOPPED' \
                    and content.name in FRYABLE:
                return lambda s, _pos=pos: any(
                    st_pos == _pos and st.content and st.content.state == 'FRIED'
                    for st_pos, st in s.stations_state
                ), [pos]

            # Sink: DIRTY plate → CLEAN
            if tile == 'W' and isinstance(content, Plate) and content.state == 'DIRTY':
                return lambda s, _pos=pos: any(
                    st_pos == _pos and st.content and st.content.state == 'CLEAN'
                    for st_pos, st in s.stations_state
                ), [pos]

        # 3. Holding RAW Meat → goal: meat is placed on a cutting board (T/B)
        if isinstance(state.held_item, Ingredient) and state.held_item.state == 'RAW' \
                and state.held_item.name in FRYABLE:
            targets = []
            for y, row in enumerate(state.layout):
                for x, char in enumerate(row):
                    if char in ('T', 'B'): targets.append((x,y))
            return lambda s: any(
                st.content and isinstance(st.content, Ingredient) 
                and st.content.name in FRYABLE and st.content.state == 'RAW'
                and s.get_layout_at(pos[0], pos[1]) in ('T', 'B')
                for pos, st in s.stations_state
            ), targets

        # 4. Holding CHOPPED Meat → goal: meat is placed on a frying pan (N)
        if isinstance(state.held_item, Ingredient) and state.held_item.state == 'CHOPPED' \
                and state.held_item.name in FRYABLE:
            targets = []
            for y, row in enumerate(state.layout):
                for x, char in enumerate(row):
                    if char == 'N': targets.append((x,y))
            return lambda s: any(
                st.content and isinstance(st.content, Ingredient)
                and st.content.name in FRYABLE and st.content.state == 'CHOPPED'
                and s.get_layout_at(pos[0], pos[1]) == 'N'
                for pos, st in s.stations_state
            ), targets

        # 5. Holding RAW Boilable → place on stove S
        if isinstance(state.held_item, Ingredient) and state.held_item.state == 'RAW' \
                and state.held_item.name in BOILABLE:
            targets = []
            for y, row in enumerate(state.layout):
                for x, char in enumerate(row):
                    if char == 'S': targets.append((x,y))
            return lambda s: any(
                st.content and isinstance(st.content, Ingredient) and st.content.name in BOILABLE
                for _, st in s.stations_state
            ), targets

        # 6. Holding RAW other (generic choppable) → place on cutting board
        if isinstance(state.held_item, Ingredient) and state.held_item.state == 'RAW':
            targets = []
            for y, row in enumerate(state.layout):
                for x, char in enumerate(row):
                    if char in ('T', 'B'): targets.append((x,y))
            return lambda s: any(st.content == state.held_item for _, st in s.stations_state), targets

        # 7. Holding CHOPPED non-Fryable → place on stove
        if isinstance(state.held_item, Ingredient) and state.held_item.state == 'CHOPPED':
            targets = []
            for y, row in enumerate(state.layout):
                for x, char in enumerate(row):
                    if char == 'S': targets.append((x,y))
            return lambda s: any(st.content == state.held_item for _, st in s.stations_state), targets

        # 7.5 Holding DIRTY Plate → place on sink W
        if isinstance(state.held_item, Plate) and state.held_item.state == 'DIRTY':
            targets = []
            for y, row in enumerate(state.layout):
                for x, char in enumerate(row):
                    if char == 'W': targets.append((x,y))
            # Subgoal: plate is placed on sink or being washed
            return lambda s: any(
                st.content and isinstance(st.content, Plate) and st.content.state == 'DIRTY'
                and s.get_layout_at(pos[0], pos[1]) == 'W'
                for pos, st in s.stations_state
            ) or (s.held_item is not None and isinstance(s.held_item, Plate) and s.held_item.state == 'DIRTY' and s.held_item.count < state.held_item.count), targets

        # 8. Holding CLEAN or WITH_FOOD Plate → pick up ready ingredient
        if isinstance(state.held_item, Plate) and state.held_item.state in ("CLEAN", "WITH_FOOD"):
            ready_targets = [pos for pos, s in state.stations_state 
                            if s.content and isinstance(s.content, Ingredient) 
                            and s.content.state in ('COOKED', 'FRIED', 'CHOPPED')]
            if ready_targets:
                # Determine remaining ingredients needed
                if state.active_orders:
                    needed = list(state.active_orders[0].ingredients)
                    plate_contents = list(state.held_item.contents)
                    for item in plate_contents:
                        if item in needed:
                            needed.remove(item)
                    if needed:
                        if ready_targets:
                            return lambda s: isinstance(s.held_item, Plate) and \
                                len(s.held_item.contents) > len(state.held_item.contents), ready_targets
                        else:
                            # HOLDING PLATE NO READY INGREDIENTS -> Put plate down on empty counter
                            counter_targets = []
                            for y, row in enumerate(state.layout):
                                for x, char in enumerate(row):
                                    if char == 'C' and state.get_object_at((x, y)) is None:
                                        counter_targets.append((x, y))
                            if counter_targets:
                                return lambda s: s.held_item is None and any(
                                    isinstance(obj, Plate) and obj.contents == state.held_item.contents
                                    for _, obj in s.grid_objects), counter_targets

        # 9. Holding Plate WITH_FOOD and all ingredients present → Deliver
        if isinstance(state.held_item, Plate) and state.held_item.state == 'WITH_FOOD':
            if state.active_orders:
                needed = sorted(state.active_orders[0].ingredients)
                plate = sorted(state.held_item.contents)
                if plate == needed:
                    del_targets = []
                    for y, row in enumerate(state.layout):
                        for x, char in enumerate(row):
                            if char == 'D': del_targets.append((x,y))
                    return lambda s: len(s.active_orders) < len(state.active_orders), del_targets

        # 10. Holding nothing
        if state.held_item is None:
            # Something is cooked/fried — need a clean plate
            ready_targets = [pos for pos, s in state.stations_state 
                            if s.content and isinstance(s.content, Ingredient) and s.content.state in ('COOKED', 'FRIED')]
            
            if ready_targets:
                plate_targets = [pos for pos, obj in state.grid_objects if isinstance(obj, Plate) and obj.state in ("CLEAN", "WITH_FOOD")]
                if plate_targets:
                    return lambda s: isinstance(s.held_item, Plate) and s.held_item.state in ("CLEAN", "WITH_FOOD"), plate_targets

                # Need to wash a dirty plate first
                dirty_targets = [pos for pos, obj in state.grid_objects if isinstance(obj, Plate) and obj.state == 'DIRTY']
                if dirty_targets:
                    return lambda s: isinstance(s.held_item, Plate) and s.held_item.state == 'DIRTY', dirty_targets

            # Pick up a ready-on-board ingredient
            for pos, s_state in state.stations_state:
                tile = state.get_layout_at(pos[0], pos[1])
                content = s_state.content
                if not content or not isinstance(content, Ingredient):
                    continue
                if tile in ('T', 'B') and content.state == 'CHOPPED':
                    return lambda s: isinstance(s.held_item, Ingredient) and s.held_item.state == 'CHOPPED', [pos]
                if tile == 'S' and content.state == 'COOKED':
                    return lambda s: isinstance(s.held_item, Ingredient) and s.held_item.state == 'COOKED', [pos]
                if tile == 'N' and content.state == 'FRIED':
                    return lambda s: isinstance(s.held_item, Ingredient) and s.held_item.state == 'FRIED', [pos]

            # Nothing cookin — fetch next ingredient for first order
            stations_busy = any(
                s.content
                for pos, s in state.stations_state
                if state.get_layout_at(pos[0], pos[1]) in ('S', 'T', 'B', 'N')
            )
            if not stations_busy and state.active_orders:
                # Pick the first needed ingredient
                needed = list(state.active_orders[0].ingredients)
                if needed:
                    first_needed = needed[0]
                    src_targets = []
                    char_map = {'Onion': 'O', 'Meat': 'M', 'Pasta': 'K'}
                    target_char = char_map.get(first_needed)
                    if target_char:
                        for y, row in enumerate(state.layout):
                            for x, char in enumerate(row):
                                if char == target_char: src_targets.append((x,y))
                        return lambda s, f=first_needed: isinstance(s.held_item, Ingredient) and s.held_item.name == f, src_targets

        return None, []

    def __call__(self, percept):
        """O programa do agente que decide a próxima ação baseada na percepção."""
        state = percept
        self.debug_info = {"step": state.time, "plan_found": False}

        if not self.plan:
            subgoal_fn, targets = self.get_subgoal_test(state)

            if subgoal_fn:
                print(f"[Agent] Searching for sub-goal plan (step={state.time})... with {len(targets)} targets")
                
                # Heuristic for sub-goal: Manhattan distance to nearest target
                def subgoal_h(node):
                    if not targets: return 0
                    ax, ay = node.state.agent_pos
                    return min(abs(ax - tx) + abs(ay - ty) for tx, ty in targets)

                problem = KitchenProblem(state, goal_test_fn=subgoal_fn)
                solution_node = astar_search_with_limit(problem, subgoal_h, max_expansions=100000)
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
