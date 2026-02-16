import re
from aima3.search import Problem
from models.entities import Ingredient, Order, Plate, Extinguisher
from models.states import KitchenState, StationState
from typing import List, Tuple, Optional, Union

CHOP_DURATION = 3
COOK_DURATION = 5
BURN_LIMIT = 10
WASH_DURATION = 2

class KitchenProblem(Problem):
    def __init__(self, initial: KitchenState, goal_orders: List[Order] = None):
        super().__init__(initial)
        self.goal_orders = goal_orders

    def goal_test(self, state: KitchenState) -> bool:
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
            
            # C=Counter, S=Stove, T/B=Cutting Board, D=Delivery, W=Sink, G=Trash, E=Extinguisher, P=Plate, O=Source
            if tile in ('C', 'S', 'T', 'B', 'D', 'W', 'G', 'E', 'P', 'O'):
                obj_on_tile = state.get_object_at((sx, sy))
                station_state = state.get_station_state_at((sx, sy))
                
                # Fire suppression check
                if station_state and station_state.is_on_fire:
                    if isinstance(state.held_item, Extinguisher):
                        possible_actions.append(f"Extinguish({sx}, {sy})")
                    continue

                if state.held_item is None:
                    # PickUp logic when holding nothing
                    if obj_on_tile:
                        if isinstance(obj_on_tile, Plate):
                            possible_actions.append(f"PickUp(Plate, {obj_on_tile.state}, {sx}, {sy})")
                        elif isinstance(obj_on_tile, Extinguisher):
                            possible_actions.append(f"PickUp(Extinguisher, READY, {sx}, {sy})")
                        else: # Ingredient
                            possible_actions.append(f"PickUp({obj_on_tile.name}, {obj_on_tile.state}, {sx}, {sy})")
                    elif tile == 'O': # Infinite Onion Source
                        possible_actions.append(f"PickUp(Onion, RAW, {sx}, {sy})")
                    elif tile in ('S', 'T', 'B', 'W'):
                        if station_state and station_state.content:
                            content = station_state.content
                            if isinstance(content, Plate):
                                possible_actions.append(f"PickUp(Plate, {content.state}, {sx}, {sy})")
                            else:
                                possible_actions.append(f"PickUp({content.name}, {content.state}, {sx}, {sy})")
                else:
                    # PutDown/Interact logic when holding something
                    held = state.held_item
                    
                    # Trash interaction
                    if tile == 'G':
                        possible_actions.append(f"PutDown({getattr(held, 'name', 'Item')}, trash, {sx}, {sy})")
                    
                    # Counter/Empty Space interaction
                    if (tile in ('C', 'E', 'P')) and obj_on_tile is None:
                        if isinstance(held, Plate):
                            possible_actions.append(f"PutDown(Plate, {held.state}, {sx}, {sy})")
                        elif isinstance(held, Extinguisher):
                            possible_actions.append(f"PutDown(Extinguisher, READY, {sx}, {sy})")
                        else:
                            possible_actions.append(f"PutDown({held.name}, {held.state}, {sx}, {sy})")
                    
                    # Plate assembly on counter
                    elif tile == 'C' and isinstance(obj_on_tile, Plate) and obj_on_tile.state == "CLEAN":
                        if isinstance(held, Ingredient) and held.state in ('CHOPPED', 'COOKED'):
                            possible_actions.append(f"PutDown({held.name}, {held.state}, {sx}, {sy})")
                    
                    # Station interaction
                    elif (tile in ('S', 'T', 'B', 'W')) and station_state and station_state.content is None:
                        if tile in ('T', 'B') and isinstance(held, Ingredient) and held.state == 'RAW':
                            possible_actions.append(f"PutDown({held.name}, {held.state}, {sx}, {sy})")
                        elif tile == 'S' and isinstance(held, Ingredient) and held.state == 'CHOPPED':
                            possible_actions.append(f"PutDown({held.name}, {held.state}, {sx}, {sy})")
                        elif tile == 'W' and isinstance(held, Plate) and held.state == "DIRTY":
                            possible_actions.append(f"PutDown(Plate, DIRTY, {sx}, {sy})")
                    
                    # Delivery
                    if tile == 'D' and isinstance(held, Plate) and held.state == "WITH_FOOD":
                        possible_actions.append(f"Deliver({sx}, {sy})")
                    
                    # Special interaction: Pick up from stove/table directly onto a held plate
                    if isinstance(held, Plate) and held.state == "CLEAN":
                        if tile in ('S', 'T', 'B') and station_state and station_state.content:
                             content = station_state.content
                             if (tile == 'S' and content.state == 'COOKED') or \
                                (tile in ('T', 'B') and content.state == 'CHOPPED'):
                                 possible_actions.append(f"PickUp({content.name}, {content.state}, {sx}, {sy})")

                # Station specific actions (Wait, Chop)
                if tile in ('T', 'B') and station_state and station_state.content:
                    if isinstance(station_state.content, Ingredient) and station_state.content.state == 'RAW':
                        possible_actions.append(f"Chop({sx}, {sy})")
                
                if tile == 'S' and station_state and station_state.content:
                    if isinstance(station_state.content, Ingredient) and station_state.content.state == 'CHOPPED':
                        possible_actions.append(f"Wait({sx}, {sy})")
                
                if tile == 'W' and station_state and station_state.content:
                    if isinstance(station_state.content, Plate) and station_state.content.state == "DIRTY":
                        possible_actions.append(f"Wait({sx}, {sy})")

        return possible_actions

    def result(self, state: KitchenState, action: str) -> KitchenState:
        match = re.match(r"(\w+)\((.*)\)", action)
        if not match: return state._replace(time=state.time + 1)
        
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
            picked_item = state.get_object_at(pos)
            if picked_item is None:
                if pos in new_stations_state:
                    picked_item = new_stations_state[pos].content
                    new_stations_state[pos] = StationState(progress=0, content=None)
                elif state.get_layout_at(pos[0], pos[1]) == 'O':
                    picked_item = Ingredient(name="Onion", state="RAW")
            
            # Special case: Picking up food onto a held plate
            if isinstance(state.held_item, Plate) and state.held_item.state == "CLEAN":
                if isinstance(picked_item, Ingredient):
                    new_contents = list(state.held_item.contents)
                    new_contents.append(picked_item.name)
                    new_held_item = state.held_item._replace(contents=tuple(new_contents), state="WITH_FOOD")
                    new_grid_objects = [obj for obj in new_grid_objects if obj[0] != pos]
            else:
                new_held_item = picked_item
                new_grid_objects = [obj for obj in new_grid_objects if obj[0] != pos]
                
        elif act_name == "PutDown":
            pos = (int(params[1]), int(params[2])) if act_name == "Wait" else (int(params[2]), int(params[3]))
            tile = state.get_layout_at(pos[0], pos[1])
            obj_at_pos = state.get_object_at(pos)
            
            if tile == 'G': # Trash
                new_held_item = None
            elif isinstance(obj_at_pos, Plate) and obj_at_pos.state == "CLEAN" and isinstance(new_held_item, Ingredient):
                # Assembly logic: Put ingredient onto plate
                new_contents = list(obj_at_pos.contents)
                new_contents.append(new_held_item.name)
                updated_plate = obj_at_pos._replace(contents=tuple(new_contents), state="WITH_FOOD")
                new_grid_objects = [obj for obj in new_grid_objects if obj[0] != pos]
                new_grid_objects.append((pos, updated_plate))
                new_held_item = None
            elif tile in ('C', 'E', 'P'):
                new_grid_objects.append((pos, new_held_item))
                new_held_item = None
            elif tile in ('S', 'T', 'B', 'W'):
                new_stations_state[pos] = StationState(progress=0, content=new_held_item)
                new_held_item = None

        elif act_name == "Deliver":
            if new_active_orders:
                new_active_orders.pop(0)
                new_delivered_orders.append(state.active_orders[0])
                new_held_item = None
                
                # Spawn dirty plate at Return station or designated counter
                return_pos = None
                for y_idx, row in enumerate(state.layout):
                    for x_idx, char in enumerate(row):
                        if char == 'P': # Prefer designated Plate counter
                            if state.get_object_at((x_idx, y_idx)) is None:
                                return_pos = (x_idx, y_idx)
                                break
                    if return_pos: break
                
                if not return_pos: # Fallback to any empty counter
                    for y_idx, row in enumerate(state.layout):
                        for x_idx, char in enumerate(row):
                            if char == 'C':
                                if state.get_object_at((x_idx, y_idx)) is None:
                                    return_pos = (x_idx, y_idx)
                                    break
                        if return_pos: break

                if return_pos:
                    new_grid_objects.append((return_pos, Plate(state="DIRTY")))

        elif act_name == "Chop":
            pos = (int(params[0]), int(params[1]))
            s_state = new_stations_state[pos]
            new_progress = s_state.progress + 1
            new_content = s_state.content
            if new_progress >= CHOP_DURATION:
                if isinstance(new_content, Ingredient):
                    new_content = new_content._replace(state='CHOPPED')
                new_progress = 0
            new_stations_state[pos] = StationState(progress=new_progress, content=new_content)
        elif act_name == "Extinguish":
            pos = (int(params[0]), int(params[1]))
            new_stations_state[pos] = StationState(progress=0, is_on_fire=False, content=None)

        # Global progress
        for pos, s_state in new_stations_state.items():
            tile = state.get_layout_at(pos[0], pos[1])
            if tile == 'S' and isinstance(s_state.content, Ingredient) and s_state.content.state == 'CHOPPED':
                new_progress = s_state.progress + 1
                new_content = s_state.content
                new_fire = s_state.is_on_fire
                if new_progress >= COOK_DURATION:
                    new_content = new_content._replace(state='COOKED')
                if new_progress >= BURN_LIMIT:
                    new_content = new_content._replace(state='BURNT')
                    new_fire = True
                new_stations_state[pos] = StationState(progress=new_progress, content=new_content, is_on_fire=new_fire)
            elif tile == 'W' and isinstance(s_state.content, Plate) and s_state.content.state == "DIRTY":
                 new_progress = s_state.progress + 1
                 new_content = s_state.content
                 if new_progress >= WASH_DURATION:
                     new_content = Plate(state="CLEAN")
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
        
        # Fire Priority
        for pos, s_state in state.stations_state:
            if s_state.is_on_fire:
                if isinstance(state.held_item, Extinguisher):
                    targets.append(pos)
                else:
                    for y, row in enumerate(state.layout):
                        for x, char in enumerate(row):
                            if char == 'E': targets.append((x, y))
                            elif state.get_object_at((x, y)) and isinstance(state.get_object_at((x, y)), Extinguisher):
                                targets.append((x, y))
                if targets: 
                    return min(abs(ax - tx) + abs(ay - ty) for tx, ty in targets)

        if state.held_item:
            held = state.held_item
            if isinstance(held, Extinguisher):
                # Return it if no fire? For now just go to an E counter
                for y, row in enumerate(state.layout):
                    for x, char in enumerate(row):
                        if char == 'E': targets.append((x, y))
            elif isinstance(held, Plate):
                progress_bonus = 10
                if held.state == "DIRTY":
                    for y, row in enumerate(state.layout):
                        for x, char in enumerate(row):
                            if char == 'W': targets.append((x, y))
                    extra_cost = WASH_DURATION
                elif held.state == "CLEAN":
                    if held.contents:
                        progress_bonus = 30
                        for y, row in enumerate(state.layout):
                            for x, char in enumerate(row):
                                if char == 'D': targets.append((x, y))
                    else:
                        for pos, s_state in state.stations_state:
                            if s_state.content and isinstance(s_state.content, Ingredient) and s_state.content.state in ('COOKED', 'CHOPPED'):
                                targets.append(pos)
                        if not targets:
                            for y, row in enumerate(state.layout):
                                for x, char in enumerate(row):
                                    if char == 'C' and state.get_object_at((x, y)) is None:
                                        targets.append((x, y))
                elif held.state == "WITH_FOOD":
                    progress_bonus = 40
                    for y, row in enumerate(state.layout):
                        for x, char in enumerate(row):
                            if char == 'D': targets.append((x, y))
            elif isinstance(held, Ingredient):
                if held.state == 'COOKED':
                    progress_bonus = 25
                    for pos, obj in state.grid_objects:
                        if isinstance(obj, Plate) and obj.state == "CLEAN": targets.append(pos)
                    if not targets:
                        for pos, s_state in state.stations_state:
                            if isinstance(s_state.content, Plate) and s_state.content.state == "CLEAN":
                                targets.append(pos)
                elif held.state == 'RAW':
                    progress_bonus = 5
                    for y, row in enumerate(state.layout):
                        for x, char in enumerate(row):
                            if char in ('T', 'B'): targets.append((x, y))
                    extra_cost = CHOP_DURATION
                elif held.state == 'CHOPPED':
                    progress_bonus = 15
                    for y, row in enumerate(state.layout):
                        for x, char in enumerate(row):
                            if char == 'S': targets.append((x, y))
                    extra_cost = COOK_DURATION
        else:
            # Holding nothing
            cooked_exists = any(s.content and isinstance(s.content, Ingredient) and s.content.state == 'COOKED' for _, s in state.stations_state)
            if cooked_exists:
                for pos, obj in state.grid_objects:
                    if isinstance(obj, Plate) and obj.state == "CLEAN": targets.append(pos)
            
            if not targets:
                for y, row in enumerate(state.layout):
                    for x, char in enumerate(row):
                        if char == 'O': targets.append((x, y))
        
        if not targets: return 100
        
        dist = min(abs(ax - tx) + abs(ay - ty) for tx, ty in targets)
        return dist + extra_cost + (60 - progress_bonus)
