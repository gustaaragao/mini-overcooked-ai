import re
from aima3.search import Problem
from models.models import KitchenState, Order, Ingredient, StationState
from typing import List, Tuple, Optional

CHOP_DURATION = 3
COOK_DURATION = 5
BURN_LIMIT = 10
WASH_DURATION = 2

class KitchenProblem(Problem):
    def __init__(self, initial: KitchenState, goal_orders: List[Order] = None):
        super().__init__(initial)
        self.goal_orders = goal_orders

    def goal_test(self, state: KitchenState) -> bool:
        """Goal: all active orders delivered.

        We treat the problem as solved once there are no remaining active
        orders. This is the natural objective for the simulator and makes A*
        terminate (the default AIMA goal_test would compare to self.goal=None).
        """
        return len(state.active_orders) == 0

    def actions(self, state: KitchenState) -> List[str]:
        possible_actions = []
        x, y = state.agent_pos
        
        # 1. Movimentação
        for dx, dy in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
            nx, ny = x + dx, y + dy
            if not state.is_impassable(nx, ny):
                possible_actions.append(f"Move({nx}, {ny})")
            
        # 2. Interações com Estações Adjacentes
        for dx, dy in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
            sx, sy = x + dx, y + dy
            tile = state.get_layout_at(sx, sy)
            
            if tile in ('C', 'S', 'B', 'D', 'K', 'E', 'R', 'O'): # B for Cutting Board, O for Onion Source
                obj_on_tile = state.get_object_at((sx, sy))
                station_state = state.get_station_state_at((sx, sy))
                
                if station_state and station_state.is_on_fire:
                    if state.held_item and state.held_item.name == "Extinguisher":
                        possible_actions.append(f"Extinguish({sx}, {sy})")
                    continue

                if state.held_item is None:
                    if obj_on_tile:
                        possible_actions.append(f"PickUp({obj_on_tile.name}, {obj_on_tile.state}, {sx}, {sy})")
                    elif tile == 'O': # Infinite Onion Source
                        possible_actions.append(f"PickUp(Onion, raw, {sx}, {sy})")
                    elif tile == 'E':
                        possible_actions.append(f"PickUp(Extinguisher, tool, {sx}, {sy})")
                    elif tile in ('S', 'B', 'K'):
                        if station_state and station_state.content:
                            possible_actions.append(f"PickUp({station_state.content.name}, {station_state.content.state}, {sx}, {sy})")
                else:
                    # PutDown logic
                    if (tile == 'C' or tile == 'R' or tile == 'E') and obj_on_tile is None:
                        # Allow putting anything on empty counter, return station, or extinguisher station
                        possible_actions.append(f"PutDown({state.held_item.name}, {state.held_item.state}, {sx}, {sy})")
                    elif tile == 'C' and obj_on_tile and obj_on_tile.name == "Plate" and obj_on_tile.state == "clean":
                        # Assembly: Put processed ingredient on a clean plate
                        if state.held_item.state in ('chopped', 'cooked'):
                            possible_actions.append(f"PutDown({state.held_item.name}, {state.held_item.state}, {sx}, {sy})")
                    elif (tile in ('S', 'B', 'K')) and station_state and station_state.content is None:
                        if tile == 'B' and state.held_item.state == 'raw':
                            possible_actions.append(f"PutDown({state.held_item.name}, {state.held_item.state}, {sx}, {sy})")
                        elif tile == 'S' and state.held_item.state == 'chopped':
                            possible_actions.append(f"PutDown({state.held_item.name}, {state.held_item.state}, {sx}, {sy})")
                        elif tile == 'K' and state.held_item.name == "Plate" and state.held_item.state == "dirty":
                            possible_actions.append(f"PutDown({state.held_item.name}, {state.held_item.state}, {sx}, {sy})")
                    elif tile == 'E' and state.held_item.name == "Extinguisher":
                        possible_actions.append(f"PutDown(Extinguisher, tool, {sx}, {sy})")

                    if tile == 'D' and state.held_item.name == "Plate" and state.held_item.contents:
                        # Deliver only if it's a plate with something on it
                        possible_actions.append(f"Deliver({sx}, {sy})")
                    
                    # Special interaction: Pick up from stove/table directly onto a plate
                    if state.held_item.name == "Plate" and state.held_item.state == "clean":
                        if tile in ('S', 'B') and station_state and station_state.content:
                             if (tile == 'S' and station_state.content.state == 'cooked') or \
                                (tile == 'B' and station_state.content.state == 'chopped'):
                                 possible_actions.append(f"PickUp({station_state.content.name}, {station_state.content.state}, {sx}, {sy})")

                if tile == 'B' and station_state and station_state.content and station_state.content.state == 'raw':
                    possible_actions.append(f"Chop({sx}, {sy})")
                
                if tile == 'S' and station_state and station_state.content and station_state.content.state == 'chopped':
                    possible_actions.append(f"Wait({sx}, {sy})")
                
                if tile == 'K' and station_state and station_state.content and station_state.content.name == "Plate" and station_state.content.state == "dirty":
                    possible_actions.append(f"Wait({sx}, {sy})")

        return possible_actions

    def result(self, state: KitchenState, action: str) -> KitchenState:
        match = re.match(r"(\w+)\((.*)\)", action)
        if not match: return state
        
        act_name, params_str = match.groups()
        params = [p.strip() for p in params_str.split(",")]
        
        new_agent_pos = state.agent_pos
        new_held_item = state.held_item
        new_grid_objects = list(state.grid_objects)
        new_delivered_orders = list(state.delivered_orders)
        new_active_orders = list(state.active_orders)
        new_stations_state = {pos: s_state for pos, s_state in state.stations_state}
        
        if act_name == "Move":
            new_agent_pos = (int(params[0]), int(params[1]))
        elif act_name == "PickUp":
            pos = (int(params[2]), int(params[3]))
            # Special case: Picking up food onto a held plate
            if state.held_item and state.held_item.name == "Plate":
                picked_ingredient = Ingredient(name=params[0], state=params[1])
                new_contents = list(state.held_item.contents)
                new_contents.append(picked_ingredient.name)
                new_held_item = state.held_item._replace(contents=tuple(new_contents))
                
                if pos in new_stations_state:
                    new_stations_state[pos] = StationState(progress=0, content=None)
                new_grid_objects = [obj for obj in new_grid_objects if obj[0] != pos]
            else:
                new_held_item = Ingredient(name=params[0], state=params[1])
                new_grid_objects = [obj for obj in new_grid_objects if obj[0] != pos]
                if pos in new_stations_state:
                    new_stations_state[pos] = StationState(progress=0, content=None)
        elif act_name == "PutDown":
            pos = (int(params[2]), int(params[3]))
            tile = state.get_layout_at(pos[0], pos[1])
            obj_at_pos = state.get_object_at(pos)
            
            if obj_at_pos and obj_at_pos.name == "Plate":
                # Assembly logic: Put ingredient onto plate
                new_contents = list(obj_at_pos.contents)
                new_contents.append(new_held_item.name)
                updated_plate = obj_at_pos._replace(contents=tuple(new_contents))
                new_grid_objects = [obj for obj in new_grid_objects if obj[0] != pos]
                new_grid_objects.append((pos, updated_plate))
            elif tile in ('C', 'E', 'R'):
                new_grid_objects.append((pos, new_held_item))
            elif tile in ('S', 'B', 'K'):
                new_stations_state[pos] = StationState(progress=0, content=new_held_item)
            new_held_item = None
        elif act_name == "Deliver":
            if new_active_orders:
                order_delivered = new_active_orders.pop(0)
                new_delivered_orders.append(order_delivered)
                new_held_item = None
                
                # Spawn dirty plate at Return station
                return_pos = None
                for y_idx, row in enumerate(state.layout):
                    for x_idx, char in enumerate(row):
                        if char == 'R':
                            if state.get_object_at((x_idx, y_idx)) is None:
                                return_pos = (x_idx, y_idx)
                                break
                    if return_pos: break
                
                if return_pos:
                    new_grid_objects.append((return_pos, Ingredient(name="Plate", state="dirty")))
        elif act_name == "Chop":
            pos = (int(params[0]), int(params[1]))
            s_state = new_stations_state[pos]
            new_progress = s_state.progress + 1
            new_content = s_state.content
            if new_progress >= CHOP_DURATION:
                new_content = Ingredient(name=s_state.content.name, state='chopped')
                new_progress = 0
            new_stations_state[pos] = StationState(progress=new_progress, content=new_content)
        elif act_name == "Extinguish":
            pos = (int(params[0]), int(params[1]))
            new_stations_state[pos] = StationState(progress=0, is_on_fire=False, content=None)

        # Global progress
        for pos, s_state in new_stations_state.items():
            tile = state.get_layout_at(pos[0], pos[1])
            if tile == 'S' and s_state.content and s_state.content.state == 'chopped':
                new_progress = s_state.progress + 1
                new_content = s_state.content
                new_fire = s_state.is_on_fire
                if new_progress >= COOK_DURATION:
                    new_content = Ingredient(name=s_state.content.name, state='cooked')
                if new_progress >= BURN_LIMIT:
                    new_content = Ingredient(name=s_state.content.name, state='burnt')
                    new_fire = True
                new_stations_state[pos] = StationState(progress=new_progress, content=new_content, is_on_fire=new_fire)
            elif tile == 'K' and s_state.content and s_state.content.name == "Plate" and s_state.content.state == "dirty":
                 # Washing logic
                 new_progress = s_state.progress + 1
                 new_content = s_state.content
                 if new_progress >= WASH_DURATION:
                     new_content = Ingredient(name="Plate", state="clean")
                     new_progress = 0
                 new_stations_state[pos] = StationState(progress=new_progress, content=new_content)

        return KitchenState(
            agent_pos=new_agent_pos,
            held_item=new_held_item,
            layout=state.layout,
            grid_objects=tuple(new_grid_objects),
            active_orders=tuple(new_active_orders),
            delivered_orders=tuple(new_delivered_orders),
            stations_state=tuple(new_stations_state.items()),
            time=state.time + 1
        )

    def path_cost(self, c, state1, action, state2):
        # Penaliza o 'Wait' levemente para incentivar outras ações se possível
        if "Wait" in action:
            return c + 1.1
        return c + 1

    def h(self, node):
        state = node.state
        if not state.active_orders: return 0
        
        ax, ay = state.agent_pos
        targets = []
        extra_cost = 0
        progress_bonus = 0
        
        # 1. Fire Priority
        for pos, s_state in state.stations_state:
            if s_state.is_on_fire:
                if state.held_item and state.held_item.name == "Extinguisher":
                    targets.append(pos)
                else:
                    for y, row in enumerate(state.layout):
                        for x, char in enumerate(row):
                            if char == 'E': targets.append((x, y))
                if targets: 
                    return min(abs(ax - tx) + abs(ay - ty) for tx, ty in targets)

        if state.held_item:
            item = state.held_item
            if item.name == "Extinguisher":
                for y, row in enumerate(state.layout):
                    for x, char in enumerate(row):
                        if char == 'E': targets.append((x, y))
            elif item.name == "Plate":
                progress_bonus = 10
                if item.state == "dirty":
                    for y, row in enumerate(state.layout):
                        for x, char in enumerate(row):
                            if char == 'K': targets.append((x, y))
                    extra_cost = WASH_DURATION
                elif item.state == "clean":
                    if item.contents:
                        progress_bonus = 30
                        for y, row in enumerate(state.layout):
                            for x, char in enumerate(row):
                                if char == 'D': targets.append((x, y))
                    else:
                        # Empty plate: MUST find processed food at S or B
                        for pos, s_state in state.stations_state:
                            if s_state.content and s_state.content.state in ('cooked', 'chopped'):
                                targets.append(pos)
                        if not targets:
                            # Go to empty counter to drop it or wait
                            for y, row in enumerate(state.layout):
                                for x, char in enumerate(row):
                                    if char == 'C' and state.get_object_at((x, y)) is None:
                                        targets.append((x, y))
            else:
                # Holding ingredient
                if item.state == 'cooked':
                    progress_bonus = 25
                    for pos, obj in state.grid_objects:
                        if obj.name == "Plate" and obj.state == "clean": targets.append(pos)
                    if not targets:
                        for pos, s_state in state.stations_state:
                            if s_state.content and s_state.content.name == "Plate" and s_state.content.state == "clean":
                                targets.append(pos)
                elif item.state == 'raw':
                    progress_bonus = 5
                    for y, row in enumerate(state.layout):
                        for x, char in enumerate(row):
                            if char == 'B': targets.append((x, y))
                    extra_cost = CHOP_DURATION
                elif item.state == 'chopped':
                    progress_bonus = 15
                    for y, row in enumerate(state.layout):
                        for x, char in enumerate(row):
                            if char == 'S': targets.append((x, y))
                    extra_cost = COOK_DURATION
        else:
            # Holding nothing
            # 1. Clean plate if cooked food exists
            cooked_exists = any(s.content and s.content.state == 'cooked' for _, s in state.stations_state)
            if cooked_exists:
                for pos, obj in state.grid_objects:
                    if obj.name == "Plate" and obj.state == "clean": targets.append(pos)
            
            # 2. Food source (Onion Source 'O')
            if not targets:
                for y, row in enumerate(state.layout):
                    for x, char in enumerate(row):
                        if char == 'O': targets.append((x, y))
        
        if not targets: return 100
        
        dist = min(abs(ax - tx) + abs(ay - ty) for tx, ty in targets)
        return dist + extra_cost + (50 - progress_bonus)
