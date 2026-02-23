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
    def __init__(self, initial: KitchenState, goal_orders: List[Order] = None, on_transition=None, goal_test_fn=None):
        super().__init__(initial)
        self.goal_orders = goal_orders
        self.on_transition = on_transition
        self.goal_test_fn = goal_test_fn

    def goal_test(self, state: KitchenState) -> bool:
        if self.goal_test_fn:
            return self.goal_test_fn(state)
        return len(state.active_orders) == 0

    def actions(self, state: KitchenState) -> List[str]:
        # ... (no changes in actions)
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
        held = state.held_item
        cost = 0
        
        #varredura de pontos de interesse pra agilizar
        
        chop_stations = [] 
        stoves = [] 
        deliveries = [] 
        sinks = [] 
        extinguishers = [] 
        plates_clean = [] 
        plates_dirty = [] 
        cooked_food = [] 
        chopped_food = [] 
        raw_sources = [] 
        
        for y, row in enumerate(state.layout): 
            for x, char in enumerate(row): 
                pos = (x, y) 
                if char == 'T': 
                    chop_stations.append(pos) 
                elif char == 'S': 
                    stoves.append(pos) 
                elif char == 'D': 
                    deliveries.append(pos) 
                elif char == 'W': 
                    sinks.append(pos) 
                elif char == 'E': 
                    extinguishers.append(pos) 
                elif char == 'O': 
                    raw_sources.append(pos) 
                
        for pos, obj in state.grid_objects: 
            if isinstance(obj, Plate) and obj.state == "CLEAN": 
                plates_clean.append(pos)
            if isinstance(obj, Plate) and obj.state == "DIRTY": 
                plates_dirty.append(pos) 
            if isinstance(obj, Ingredient): 
                if obj.state == "COOKED": 
                    cooked_food.append(pos) 
                elif obj.state == "CHOPPED": 
                    chopped_food.append(pos)  
        
        for pos, st in state.stations_state: 
            if st.content: 
                obj = st.content 
                if isinstance(obj, Plate) and obj.state == "CLEAN": 
                    plates_clean.append(pos)
                if isinstance(obj, Plate) and obj.state == "DIRTY": 
                    plates_dirty.append(pos)
                if isinstance(obj, Ingredient): 
                    if obj.state == "COOKED": 
                        cooked_food.append(pos)
                    elif obj.state == "CHOPPED": 
                        chopped_food.append(pos)
        
        #incendio: pegar extintor (se nao tiver) -> apagar
        
        fire_positions = [pos for pos, st in state.stations_state if st.is_on_fire] 
        
        if fire_positions: 
            if isinstance(held, Extinguisher): 
                return min(abs(ax - tx) + abs(ay - ty) for tx, ty in fire_positions) 
            else: 
                best = float("inf")

                for (ex, ey) in extinguishers:
                    for (fx, fy) in fire_positions:
                        cost = (
                            abs(ax - ex) + abs(ay - ey) +  
                            abs(ex - fx) + abs(ey - fy)  
                        )
                        best = min(best, cost)

                return best
            
        #devolver extintor: andar ate onde devolver
        
        if isinstance(held, Extinguisher) and held is not None:
            return min(abs(ax - tx) + abs(ay - ty) for tx, ty in extinguishers) 

        #ORGANIZANDO
        
        #caso 1 prato sujo na mao: limpa 

        if isinstance(held, Plate) and held.state == "DIRTY":
            best = float("inf")

            for (sx, sy) in sinks:
                cost = (
                    abs(ax - sx) + abs(ay - sy) +
                    WASH_DURATION
                )
                best = min(best, cost)

            return best
        
        
        #caso 2 comida pronta na mao: entregar 
        
        if isinstance(held, Plate) and held.state == "WITH_FOOD":
            return min(abs(ax - tx) + abs(ay - ty) for tx, ty in deliveries) 
        
        #caso 3 prato limpo na mao: se tiver comida pronta -> pega, se não, coloca em balcao 
        
        if isinstance(held, Plate) and not held.contents:
            if chopped_food or cooked_food:
                best = float("inf")
                
                for (chx, chy) in chopped_food:
                    for (dx, dy) in deliveries:
                        cost = (
                        abs(ax - chx) + abs(ay - chy) +     
                        abs(chx - dx) + abs(chy - dy)   
                    )
                    best = min(best, cost)
                        
                for (chx, chy) in cooked_food:
                    for (dx, dy) in deliveries:
                        cost = (
                        abs(ax - chx) + abs(ay - chy) +     
                        abs(chx - dx) + abs(chy - dy)   
                    )
                    best = min(best, cost)
                    
                return best
            
            else:
                targets = []
                for y, row in enumerate(state.layout):
                    for x, char in enumerate(row):
                        if char == 'C' and state.get_object_at((x, y)) is None:
                            targets.append((x, y))
                
                return min(abs(ax - tx) + abs(ay - ty) for tx, ty in targets)
                        
        #caso 4 segurando comida cozida 
        if isinstance(held, Ingredient) and held.state == "COOKED":
            best = float("inf")
            
            for (pcx, pcy) in plates_clean:
                for (dx, dy) in deliveries:
                    cost = (
                        abs(ax - pcx) + abs(ay - pcy) +     
                        abs(pcx - dx) + abs(pcy - dy)   
                    )
                    best = min(best, cost)
            
            return best
        
        #caso 5 segurando comida crua 
        
        if isinstance(held, Ingredient) and held.state == "RAW":
            best = float("inf")
            
            for (csx, csy) in chop_stations:
                for (sx, sy) in stoves:
                    for (pcx, pcy) in plates_clean:
                        for (dx, dy) in plates_clean:
                            cost = (
                                abs(ax - csx) + abs(ay - csy) +     
                                abs(csx - sx) + abs(csy - sy) +
                                abs(sx - pcx) + abs(sy - pcy) +     
                                abs(pcx - dx) + abs(pcy - dy) +
                                CHOP_DURATION +
                                COOK_DURATION
                            )
                            best = min(best, cost)
                            
        #caso 6 segurando comida cortada
        if isinstance(held, Ingredient) and held.state == "CHOPPED":
            best = float("inf")
            
            for (sx, sy) in stoves:
                    for (pcx, pcy) in plates_clean:
                        for (dx, dy) in plates_clean:
                            cost = (
                                abs(ax - sx) + abs(ay - sy) +     
                                abs(sx - pcx) + abs(sy - pcy) +     
                                abs(pcx - dx) + abs(pcy - dy) +
                                COOK_DURATION
                            )
                            best = min(best, cost)
                            
        #caso 7 comida pronta no mapa 
        
        if cooked_food:
            best = float("inf")

            for (cfx, cfy) in cooked_food:
                for (pcx, pcy) in plates_clean:
                    for (dx, dy) in deliveries:
                        cost = (
                            abs(ax - cfx) + abs(ay - cfy) +     
                            abs(cfx - pcx) + abs(cfy - pcy) +   
                            abs(pcx - dx) + abs(pcy - dy)       
                        )
                        best = min(best, cost)

            return best
        
        #caso 8 comida cortada no mapa
        
        if chopped_food:
            best = float("inf")

            for (cfx, cfy) in chopped_food:
                for (sx, sy) in stoves:
                    for (pcx, pcy) in plates_clean:
                        for (dx, dy) in deliveries:
                            cost = (
                                abs(ax - cfx) + abs(ay - cfy) +     
                                abs(cfx - sx) + abs(cfy - sy) +   
                                abs(sx - pcx) + abs(sy - pcy) +
                                abs(pcx - dx) + abs(pcy - dy) +
                                COOK_DURATION      
                            )
                            best = min(best, cost)

                return best
        
        #caso 9 nada feito
        best = float("inf")

        for (rsx, rsy) in raw_sources:
            for (csx, csy) in chop_stations:
                for (sx, sy) in stoves:
                    for (pcx, pcy) in plates_clean:
                        for (dx, dy) in deliveries:
                            cost = (
                                abs(ax - rsx) + abs(ay - rsy) +     
                                abs(rsx - csx) + abs(rsy - csy) +   
                                abs(csx - sx) + abs(csy - sy) +
                                abs(sx - pcx) + abs(sy - pcy) +
                                abs(pcx - dx) + abs(pcy - dy) +  
                                COOK_DURATION + 
                                CHOP_DURATION     
                            )
                            best = min(best, cost)

        return best
        