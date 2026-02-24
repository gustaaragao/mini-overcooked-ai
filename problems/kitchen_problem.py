import re
from aima3.search import Problem
from models.entities import Ingredient, Order, Plate, Extinguisher
from models.states import KitchenState, StationState
from typing import List, Tuple, Optional, Union

CHOP_DURATION = 3
COOK_DURATION = 5   # boil on S (Pasta, Onion)
FRY_DURATION  = 4   # fry on N (Meat)
BURN_LIMIT    = 10
WASH_DURATION = 2

# Ingredient categories
BOILABLE = {"Pasta", "Onion"}  # Go RAW → COOKED directly on S (stove)
FRYABLE  = {"Meat"}            # Go RAW → FRIED on N (frying pan)
CHOPPABLE = set()              # Future use

def _ingredient_needed_states(ing_name: str) -> tuple:
    """Return the ready-states an ingredient can be placed on a plate."""
    if ing_name in FRYABLE:
        return ('FRIED',)
    if ing_name in BOILABLE:
        return ('COOKED', 'CHOPPED')
    return ('COOKED', 'CHOPPED')


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

            held = state.held_item

            # ── HOLDING NOTHING ──────────────────────────────────────────────
            if held is None:
                if tile == 'R':
                    # Check if there are ANY dirty plates at R
                    dirty_at_r = any(
                        p == (sx, sy) and isinstance(obj, Plate) and obj.state == 'DIRTY'
                        for p, obj in state.grid_objects
                    )
                    if dirty_at_r:
                        possible_actions.append(f"PickUp(Plate, DIRTY, {sx}, {sy})")

                elif obj_on_tile is not None:
                    if isinstance(obj_on_tile, Plate):
                        possible_actions.append(f"PickUp(Plate, {obj_on_tile.state}, {sx}, {sy})")
                    elif isinstance(obj_on_tile, Extinguisher):
                        possible_actions.append(f"PickUp(Extinguisher, READY, {sx}, {sy})")
                    else:
                        possible_actions.append(f"PickUp({obj_on_tile.name}, {obj_on_tile.state}, {sx}, {sy})")

                elif tile == 'O':
                    possible_actions.append(f"PickUp(Onion, RAW, {sx}, {sy})")
                elif tile == 'M':
                    possible_actions.append(f"PickUp(Meat, RAW, {sx}, {sy})")
                elif tile == 'K':
                    possible_actions.append(f"PickUp(Pasta, RAW, {sx}, {sy})")

                elif tile in ('S', 'T', 'B', 'W', 'N'):
                    if station_state and station_state.content:
                        content = station_state.content
                        if isinstance(content, Plate):
                            possible_actions.append(f"PickUp(Plate, {content.state}, {sx}, {sy})")
                        else:
                            possible_actions.append(f"PickUp({content.name}, {content.state}, {sx}, {sy})")

            # ── HOLDING SOMETHING ────────────────────────────────────────────
            else:
                # Trash
                if tile == 'G':
                    item_name = getattr(held, 'name', 'Item') if not isinstance(held, Plate) else 'Plate'
                    possible_actions.append(f"PutDown({item_name}, trash, {sx}, {sy})")

                # Counter / empty plate spots
                if tile in ('C', 'E', 'P') and obj_on_tile is None:
                    if isinstance(held, Plate):
                        possible_actions.append(f"PutDown(Plate, {held.state}, {sx}, {sy})")
                    elif isinstance(held, Extinguisher):
                        possible_actions.append(f"PutDown(Extinguisher, READY, {sx}, {sy})")
                    else:
                        possible_actions.append(f"PutDown({held.name}, {held.state}, {sx}, {sy})")

                # Plate assembly on counter (CLEAN plate → add ingredient)
                elif tile == 'C' and isinstance(obj_on_tile, Plate) and obj_on_tile.state in ("CLEAN", "WITH_FOOD"):
                    if isinstance(held, Ingredient):
                        ready_states = _ingredient_needed_states(held.name)
                        if held.state in ready_states:
                            possible_actions.append(f"PutDown({held.name}, {held.state}, {sx}, {sy})")

                # Station: Cutting board (T/B) — RAW ingredient
                elif tile in ('T', 'B') and station_state and station_state.content is None:
                    if isinstance(held, Ingredient) and held.state == 'RAW':
                        possible_actions.append(f"PutDown({held.name}, {held.state}, {sx}, {sy})")

                # Station: Stove (S) — RAW Boilable ingredient directly
                elif tile == 'S' and station_state and station_state.content is None:
                    if isinstance(held, Ingredient):
                        if held.name in BOILABLE and held.state == 'RAW':
                            possible_actions.append(f"PutDown({held.name}, {held.state}, {sx}, {sy})")
                        elif held.state == 'CHOPPED':
                            possible_actions.append(f"PutDown({held.name}, {held.state}, {sx}, {sy})")

                # Station: Frying pan (N) — CHOPPED Fryable ingredient only (must be chopped first)
                elif tile == 'N' and station_state and station_state.content is None:
                    if isinstance(held, Ingredient) and held.name in FRYABLE and held.state == 'CHOPPED':
                        possible_actions.append(f"PutDown({held.name}, {held.state}, {sx}, {sy})")

                # Station: Sink (W) — DIRTY plate
                elif tile == 'W' and station_state and station_state.content is None:
                    if isinstance(held, Plate) and held.state == "DIRTY":
                        possible_actions.append(f"PutDown(Plate, DIRTY, {sx}, {sy})")

                # Delivery
                if tile == 'D' and isinstance(held, Plate) and held.state == "WITH_FOOD":
                    possible_actions.append(f"Deliver({sx}, {sy})")

                # Pick up cooked/fried/chopped food directly onto held CLEAN plate
                if isinstance(held, Plate) and held.state in ("CLEAN", "WITH_FOOD"):
                    if tile in ('S', 'T', 'B', 'N') and station_state and station_state.content:
                        content = station_state.content
                        if isinstance(content, Ingredient):
                            ready_states = _ingredient_needed_states(content.name)
                            if content.state in ready_states:
                                possible_actions.append(f"PickUp({content.name}, {content.state}, {sx}, {sy})")

            # ── STATION ACTIONS (Chop, Fry, Wait) ───────────────────────────

            # Chop on cutting board
            if tile in ('T', 'B') and station_state and station_state.content:
                if isinstance(station_state.content, Ingredient) and station_state.content.state == 'RAW':
                    possible_actions.append(f"Chop({sx}, {sy})")

            # Fry on frying pan (N) — only CHOPPED Fryable
            if tile == 'N' and station_state and station_state.content:
                if isinstance(station_state.content, Ingredient) and station_state.content.state == 'CHOPPED' \
                        and station_state.content.name in FRYABLE:
                    possible_actions.append(f"Fry({sx}, {sy})")

            # Wait on stove (cooking progress): RAW Boilable OR CHOPPED anything
            if tile == 'S' and station_state and station_state.content:
                content = station_state.content
                if isinstance(content, Ingredient) and (
                    (content.state == 'RAW' and content.name in BOILABLE) or
                    content.state == 'CHOPPED'
                ):
                    possible_actions.append(f"Wait({sx}, {sy})")

            # Wait on frying pan (frying progress) — only CHOPPED Fryable
            if tile == 'N' and station_state and station_state.content:
                content = station_state.content
                if isinstance(content, Ingredient) and content.state == 'CHOPPED' and content.name in FRYABLE:
                    possible_actions.append(f"Wait({sx}, {sy})")

            # Wait on sink (washing progress)
            if tile == 'W' and station_state and station_state.content:
                if isinstance(station_state.content, Plate) and station_state.content.state == "DIRTY":
                    possible_actions.append(f"Wait({sx}, {sy})")

        return possible_actions

    def result(self, state: KitchenState, action: str) -> KitchenState:
        match = re.match(r"(\w+)\((.*)\)", action)
        if not match:
            return state._replace(time=state.time + 1)

        act_name, params_str = match.groups()
        params = [p.strip() for p in params_str.split(",")]

        new_agent_pos    = state.agent_pos
        new_held_item    = state.held_item
        new_grid_objects = list(state.grid_objects)
        new_delivered_orders = list(state.delivered_orders)
        new_active_orders    = list(state.active_orders)
        new_stations_state   = {pos: s_state for pos, s_state in state.stations_state}

        # ── MOVE ─────────────────────────────────────────────────────────────
        if act_name == "Move":
            new_agent_pos = (int(params[0]), int(params[1]))

        # ── PICKUP ───────────────────────────────────────────────────────────
        elif act_name == "PickUp":
            pos = (int(params[2]), int(params[3]))
            tile_at_pos = state.get_layout_at(pos[0], pos[1])

            if tile_at_pos == 'R':
                # Pick up ALL dirty plates from the stack
                total_count = 0
                remaining_objects = []
                for p, obj in new_grid_objects:
                    if p == pos and isinstance(obj, Plate) and obj.state == 'DIRTY':
                        total_count += getattr(obj, 'count', 1)
                    else:
                        remaining_objects.append((p, obj))
                
                if total_count > 0:
                    picked_item = Plate(state="DIRTY", count=total_count)
                    new_grid_objects = remaining_objects
            else:
                # Try grid object, then station content, then infinite source
                picked_item = state.get_object_at(pos)
                if picked_item is None:
                    if pos in new_stations_state and new_stations_state[pos].content:
                        picked_item = new_stations_state[pos].content
                        new_stations_state[pos] = StationState(progress=0, content=None)
                    elif tile_at_pos == 'O':
                        picked_item = Ingredient(name="Onion", state="RAW")
                    elif tile_at_pos == 'M':
                        picked_item = Ingredient(name="Meat", state="RAW")
                    elif tile_at_pos == 'K':
                        picked_item = Ingredient(name="Pasta", state="RAW")

            # Picking food onto a held plate
            if isinstance(state.held_item, Plate) and state.held_item.state in ("CLEAN", "WITH_FOOD"):
                if isinstance(picked_item, Ingredient):
                    new_contents = list(state.held_item.contents)
                    new_contents.append(picked_item.name)
                    new_held_item = state.held_item._replace(
                        contents=tuple(new_contents),
                        state="WITH_FOOD"
                    )
                    if tile_at_pos != 'R':
                        new_grid_objects = [obj for obj in new_grid_objects if obj[0] != pos]
            elif tile_at_pos != 'R':
                new_held_item = picked_item
                new_grid_objects = [obj for obj in new_grid_objects if obj[0] != pos]
            else:
                new_held_item = picked_item

        # ── PUTDOWN ──────────────────────────────────────────────────────────
        elif act_name == "PutDown":
            pos = (int(params[2]), int(params[3]))
            tile = state.get_layout_at(pos[0], pos[1])
            obj_at_pos = state.get_object_at(pos)

            if tile == 'G':
                # Trash: discard item
                new_held_item = None

            elif isinstance(obj_at_pos, Plate) and obj_at_pos.state in ("CLEAN", "WITH_FOOD") and \
                 isinstance(new_held_item, Ingredient):
                # Assembly: place ingredient onto plate on counter
                new_contents = list(obj_at_pos.contents)
                new_contents.append(new_held_item.name)
                updated_plate = obj_at_pos._replace(
                    contents=tuple(new_contents),
                    state="WITH_FOOD"
                )
                new_grid_objects = [obj for obj in new_grid_objects if obj[0] != pos]
                new_grid_objects.append((pos, updated_plate))
                new_held_item = None

            elif tile in ('C', 'E', 'P'):
                new_grid_objects.append((pos, new_held_item))
                new_held_item = None

            elif tile in ('S', 'T', 'B', 'W', 'N'):
                # Stations (usually) only hold one plate/item at a time.
                # If holding a stack, put down one and keep the rest.
                if isinstance(new_held_item, Plate) and new_held_item.count > 1:
                    new_stations_state[pos] = StationState(progress=0, content=new_held_item._replace(count=1))
                    new_held_item = new_held_item._replace(count=new_held_item.count - 1)
                else:
                    new_stations_state[pos] = StationState(progress=0, content=new_held_item)
                    new_held_item = None

        # ── DELIVER ──────────────────────────────────────────────────────────
        elif act_name == "Deliver":
            if new_active_orders:
                delivered_plate = state.held_item
                plate_contents = tuple(sorted(delivered_plate.contents)) if delivered_plate else ()
                matched_idx = 0
                for i, order in enumerate(new_active_orders):
                    if tuple(sorted(order.ingredients)) == plate_contents:
                        matched_idx = i
                        break
                delivered_order = new_active_orders.pop(matched_idx)
                new_delivered_orders.append(delivered_order)
                new_held_item = None

                # Spawn dirty plate at R tile (stacking allowed)
                return_pos = None
                for y_idx, row in enumerate(state.layout):
                    for x_idx, char in enumerate(row):
                        if char == 'R':
                            return_pos = (x_idx, y_idx)
                            break
                    if return_pos:
                        break

                if not return_pos:  # Fallback: first empty P counter
                    for y_idx, row in enumerate(state.layout):
                        for x_idx, char in enumerate(row):
                            if char == 'P' and state.get_object_at((x_idx, y_idx)) is None:
                                return_pos = (x_idx, y_idx)
                                break
                        if return_pos:
                            break

                if return_pos:
                    new_grid_objects.append((return_pos, Plate(state="DIRTY")))

        # ── CHOP ─────────────────────────────────────────────────────────────
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

        # ── FRY ──────────────────────────────────────────────────────────────
        elif act_name == "Fry":
            pos = (int(params[0]), int(params[1]))
            s_state = new_stations_state[pos]
            new_progress = s_state.progress + 1
            new_content = s_state.content
            if new_progress >= FRY_DURATION:
                if isinstance(new_content, Ingredient):
                    new_content = new_content._replace(state='FRIED')
                new_progress = 0
            new_stations_state[pos] = StationState(progress=new_progress, content=new_content)

        # ── EXTINGUISH ───────────────────────────────────────────────────────
        elif act_name == "Extinguish":
            pos = (int(params[0]), int(params[1]))
            new_stations_state[pos] = StationState(progress=0, is_on_fire=False, content=None)

        # ── GLOBAL TICK PROGRESS ─────────────────────────────────────────────
        for pos, s_state in new_stations_state.items():
            tile = state.get_layout_at(pos[0], pos[1])

            # Stove S: cook CHOPPED ingredient OR boil RAW Boilable
            if tile == 'S' and isinstance(s_state.content, Ingredient):
                content = s_state.content
                if (content.state == 'CHOPPED') or \
                   (content.state == 'RAW' and content.name in BOILABLE):
                    new_progress = s_state.progress + 1
                    new_content  = content
                    new_fire     = s_state.is_on_fire
                    if new_progress >= COOK_DURATION:
                        new_content = new_content._replace(state='COOKED')
                    if new_progress >= BURN_LIMIT:
                        new_content = new_content._replace(state='BURNT')
                        new_fire = True
                    new_stations_state[pos] = StationState(
                        progress=new_progress,
                        content=new_content,
                        is_on_fire=new_fire
                    )

            # Frying pan N: fry CHOPPED Fryable (must be chopped before frying)
            elif tile == 'N' and isinstance(s_state.content, Ingredient):
                content = s_state.content
                if content.state == 'CHOPPED' and content.name in FRYABLE:
                    new_progress = s_state.progress + 1
                    new_content  = content
                    new_fire     = s_state.is_on_fire
                    if new_progress >= FRY_DURATION:
                        new_content = new_content._replace(state='FRIED')
                    if new_progress >= BURN_LIMIT:
                        new_content = new_content._replace(state='BURNT')
                        new_fire = True
                    new_stations_state[pos] = StationState(
                        progress=new_progress,
                        content=new_content,
                        is_on_fire=new_fire
                    )

            # Sink W: wash DIRTY plate
            elif tile == 'W' and isinstance(s_state.content, Plate) and s_state.content.state == "DIRTY":
                new_progress = s_state.progress + 1
                new_content  = s_state.content
                if new_progress >= WASH_DURATION:
                    new_content  = Plate(state="CLEAN")
                    new_progress = 0
                new_stations_state[pos] = StationState(progress=new_progress, content=new_content)

        return KitchenState(
            agent_pos=new_agent_pos,
            held_item=new_held_item,
            layout=state.layout,
            grid_objects=tuple(sorted(new_grid_objects, key=lambda x: x[0])),
            active_orders=tuple(new_active_orders),
            delivered_orders=tuple(new_delivered_orders),
            stations_state=tuple(sorted(new_stations_state.items(), key=lambda x: x[0])),
            time=state.time + 1
        )

    def path_cost(self, c, state1, action, state2):
        if "Wait" in action:
            return c + 1.1
        return c + 1

    def h(self, node):
        state = node.state
        if not state.active_orders:
            return 0

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
                            if char == 'E':
                                targets.append((x, y))
                            elif state.get_object_at((x, y)) and isinstance(state.get_object_at((x, y)), Extinguisher):
                                targets.append((x, y))
                if targets:
                    return min(abs(ax - tx) + abs(ay - ty) for tx, ty in targets)

        held = state.held_item

        if held is not None:
            if isinstance(held, Extinguisher):
                for y, row in enumerate(state.layout):
                    for x, char in enumerate(row):
                        if char == 'E':
                            targets.append((x, y))

            elif isinstance(held, Plate):
                progress_bonus = 10
                if held.state == "DIRTY":
                    for y, row in enumerate(state.layout):
                        for x, char in enumerate(row):
                            if char == 'W':
                                targets.append((x, y))
                    extra_cost = WASH_DURATION * getattr(held, 'count', 1)
                elif held.state in ("CLEAN", "WITH_FOOD"):
                    # Check if all ingredients are satisfied
                    order_ingredients = sorted(state.active_orders[0].ingredients) if state.active_orders else []
                    plate_contents = sorted(held.contents)
                    remaining = list(order_ingredients)
                    for item in plate_contents:
                        if item in remaining:
                            remaining.remove(item)

                    if not remaining or held.state == "WITH_FOOD" and not remaining:
                        # Ready to deliver
                        progress_bonus = 40
                        for y, row in enumerate(state.layout):
                            for x, char in enumerate(row):
                                if char == 'D':
                                    targets.append((x, y))
                    else:
                        # Still needs more ingredients — target a cooked/fried station
                        progress_bonus = 20
                        for pos, s_st in state.stations_state:
                            if s_st.content and isinstance(s_st.content, Ingredient):
                                tile = state.get_layout_at(pos[0], pos[1])
                                ready_states = _ingredient_needed_states(s_st.content.name)
                                if s_st.content.state in ready_states:
                                    targets.append(pos)
                        
                        if not targets:
                            # NO READY INGREDIENTS -> target empty counters to put plate down
                            for y, row in enumerate(state.layout):
                                for x, char in enumerate(row):
                                    if char == 'C' and state.get_object_at((x, y)) is None:
                                        targets.append((x, y))
                            extra_cost = 5 # Add small extra cost to prefer stations if they were available

            elif isinstance(held, Ingredient):
                if held.state in ('COOKED', 'FRIED'):
                    progress_bonus = 25
                    for pos, obj in state.grid_objects:
                        if isinstance(obj, Plate) and obj.state in ("CLEAN", "WITH_FOOD"):
                            targets.append(pos)
                    if not targets:
                        for pos, s_st in state.stations_state:
                            if isinstance(s_st.content, Plate) and s_st.content.state in ("CLEAN", "WITH_FOOD"):
                                targets.append(pos)
                elif held.state == 'RAW':
                    progress_bonus = 5
                    if held.name in FRYABLE:
                        # Must chop first before frying
                        for y, row in enumerate(state.layout):
                            for x, char in enumerate(row):
                                if char in ('T', 'B'):
                                    targets.append((x, y))
                        extra_cost = CHOP_DURATION + FRY_DURATION
                    elif held.name in BOILABLE:
                        for y, row in enumerate(state.layout):
                            for x, char in enumerate(row):
                                if char == 'S':
                                    targets.append((x, y))
                        extra_cost = COOK_DURATION
                    else:
                        for y, row in enumerate(state.layout):
                            for x, char in enumerate(row):
                                if char in ('T', 'B'):
                                    targets.append((x, y))
                        extra_cost = CHOP_DURATION
                elif held.state == 'CHOPPED':
                    progress_bonus = 15
                    if held.name in FRYABLE:
                        # Chopped Fryable goes to frying pan
                        for y, row in enumerate(state.layout):
                            for x, char in enumerate(row):
                                if char == 'N':
                                    targets.append((x, y))
                        extra_cost = FRY_DURATION
                    else:
                        for y, row in enumerate(state.layout):
                            for x, char in enumerate(row):
                                if char == 'S':
                                    targets.append((x, y))
                        extra_cost = COOK_DURATION
        else:
            # Holding nothing
            cooked_exists = any(
                s.content and isinstance(s.content, Ingredient) and s.content.state in ('COOKED', 'FRIED')
                for _, s in state.stations_state
            )
            if cooked_exists:
                clean_plate = any(isinstance(obj, Plate) and obj.state in ("CLEAN", "WITH_FOOD") for _, obj in state.grid_objects)
                if clean_plate:
                    for pos, obj in state.grid_objects:
                        if isinstance(obj, Plate) and obj.state in ("CLEAN", "WITH_FOOD"):
                            targets.append(pos)
                else:
                    # Need a plate — look for dirty at R to wash
                    dirty_at_r = any(
                        isinstance(obj, Plate) and obj.state == 'DIRTY'
                        and state.get_layout_at(pos[0], pos[1]) == 'R'
                        for pos, obj in state.grid_objects
                    )
                    if dirty_at_r:
                        for pos, obj in state.grid_objects:
                            if isinstance(obj, Plate) and obj.state == 'DIRTY' and state.get_layout_at(pos[0], pos[1]) == 'R':
                                targets.append(pos)
                        extra_cost = WASH_DURATION

            if not targets:
                # Get next ingredient for active order
                if state.active_orders:
                    needed = list(state.active_orders[0].ingredients)
                    # Simple heuristic: what's already on stations?
                    on_stations = set()
                    for _, s in state.stations_state:
                        if s.content and isinstance(s.content, Ingredient):
                            on_stations.add(s.content.name)
                    
                    for ing_name in needed:
                        if ing_name in on_stations: continue # already working on it
                        
                        target_char = None
                        if ing_name == 'Meat': target_char = 'M'
                        elif ing_name == 'Onion': target_char = 'O'
                        elif ing_name == 'Pasta': target_char = 'K'
                        
                        if target_char:
                            for y, row in enumerate(state.layout):
                                for x, char in enumerate(row):
                                    if char == target_char:
                                        targets.append((x, y))
                            break  # focus on one ingredient at a time

        if not targets:
            return 100

        dist = min(abs(ax - tx) + abs(ay - ty) for tx, ty in targets)
        return dist + extra_cost + (60 - progress_bonus)
