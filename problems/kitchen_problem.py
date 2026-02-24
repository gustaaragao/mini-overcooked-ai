import re
from aima3.search import Problem
from models.entities import Ingredient, Order, Plate, Extinguisher, Pot
from models.states import KitchenState, StationState
from typing import List
from utils.recipe_utils import (
    order_satisfied_by_plate,
    pot_required_ingredients,
    pot_needed_ingredients,
    pot_needed_count_for_order,
)

CHOP_DURATION = 3       # passos para cortar um ingrediente
COOK_DURATION = 5       # passos para cozinhar no fogão simples
BURN_LIMIT = 10         # passos até queimar (e pegar fogo)
WASH_DURATION = 2       # passos para lavar um prato sujo
POT_COOK_DURATION = 7   # passos para a panela concluir o cozimento

class KitchenProblem(Problem):
    def __init__(self, initial: KitchenState, goal_orders: List[Order] = None,
                 on_transition=None, goal_test_fn=None):
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
        # for dx, dy in [(0, 1), (0, -1), (1, 0), (-1, 0)]: # vizinhança-4
        for dx, dy in [(0, 1), (0, -1), (1, 0), (-1, 0), (1, 1), (-1, 1), (1, -1), (-1, -1)]: # vizinhança-8
            nx, ny = x + dx, y + dy
            if not state.is_impassable(nx, ny):
                possible_actions.append(f"Move({nx}, {ny})")

        # 2. Interações com Estações Adjacentes
        # for dx, dy in [(0, 1), (0, -1), (1, 0), (-1, 0), (1, 1), (-1, 1), (1, -1), (-1, -1)]: # vizinhança-8
        for dx, dy in [(0, 1), (0, -1), (1, 0), (-1, 0)]: # vizinhança-4
            sx, sy = x + dx, y + dy
            tile = state.get_layout_at(sx, sy)

            # C=Balcão, S=Fogão, T/B=Tábua de Corte, D=Entrega, W=Pia,
            # G=Lixeira, E=Extintor, P=Prato, O=Fonte Cebola,
            # V=Fonte Tomate, K=Panela
            if tile not in ('C', 'S', 'T', 'B', 'D', 'W', 'G', 'E', 'P', 'O', 'V', 'K'):
                continue

            obj_on_tile = state.get_object_at((sx, sy))
            station_state = state.get_station_state_at((sx, sy))

            # Apagar fogo
            if station_state and station_state.is_on_fire:
                if isinstance(state.held_item, Extinguisher):
                    possible_actions.append(f"Extinguish({sx}, {sy})")
                continue

            held = state.held_item

            # Panela (K)
            if tile == 'K':
                pot = station_state.content if station_state else None
                if isinstance(pot, Pot):
                    if held is None:
                        # Nenhuma ação possível sem segurar algo
                        pass
                    elif isinstance(held, Ingredient) and held.state == 'CHOPPED':
                        if pot.state in ('EMPTY', 'FILLING'):
                            # Verifica se ainda precisamos desse ingrediente
                            needed = pot_needed_ingredients(pot, state)
                            if needed:
                                possible_actions.append(
                                    f"PutInPot({held.name}, {sx}, {sy})"
                                )
                    elif isinstance(held, Plate) and held.state == 'CLEAN':
                        if pot.state == 'READY':
                            possible_actions.append(f"ServeFromPot({sx}, {sy})")
                    # Espera enquanto cozinha
                    if pot.state == 'COOKING':
                        possible_actions.append(f"Wait({sx}, {sy})")
                continue

            if held is None:
                # Pegar item quando sem nada na mão
                if obj_on_tile:
                    if isinstance(obj_on_tile, Plate):
                        possible_actions.append(f"PickUp(Plate, {obj_on_tile.state}, {sx}, {sy})")
                    elif isinstance(obj_on_tile, Extinguisher):
                        possible_actions.append(f"PickUp(Extinguisher, READY, {sx}, {sy})")
                    else:
                        possible_actions.append(f"PickUp({obj_on_tile.name}, {obj_on_tile.state}, {sx}, {sy})")
                elif tile == 'O':   # Fonte infinita de cebola
                    possible_actions.append(f"PickUp(Onion, RAW, {sx}, {sy})")
                elif tile == 'V':   # Fonte infinita de tomate
                    possible_actions.append(f"PickUp(Tomato, RAW, {sx}, {sy})")
                elif tile == 'M':   # Fonte infinita de carne
                    possible_actions.append(f"PickUp(Meat, RAW, {sx}, {sy})")
                elif tile == 'B':   # Fonte infinita de pão
                    possible_actions.append(f"PickUp(Bread, RAW, {sx}, {sy})")
                elif tile == 'L':   # Fonte infinita de alface
                    possible_actions.append(f"PickUp(Lettuce, RAW, {sx}, {sy})")
                elif tile in ('S', 'T', 'B', 'W'):
                    if station_state and station_state.content:
                        content = station_state.content
                        if isinstance(content, Plate):
                            possible_actions.append(f"PickUp(Plate, {content.state}, {sx}, {sy})")
                        else:
                            possible_actions.append(f"PickUp({content.name}, {content.state}, {sx}, {sy})")
            else:
                # Colocar/interagir quando segurando algo

                # Lixeira
                if tile == 'G':
                    possible_actions.append(f"PutDown({getattr(held, 'name', 'Item')}, trash, {sx}, {sy})")

                # Balcão ou espaço vazio
                if tile in ('C', 'E', 'P') and obj_on_tile is None:
                    if isinstance(held, Plate):
                        possible_actions.append(f"PutDown(Plate, {held.state}, {sx}, {sy})")
                    elif isinstance(held, Extinguisher):
                        possible_actions.append(f"PutDown(Extinguisher, READY, {sx}, {sy})")
                    else:
                        possible_actions.append(f"PutDown({held.name}, {held.state}, {sx}, {sy})")

                # Montar prato sobre balcão (colocar ingrediente em prato limpo)
                elif tile == 'C' and isinstance(obj_on_tile, Plate) and obj_on_tile.state == 'CLEAN':
                    if isinstance(held, Ingredient) and held.state in ('CHOPPED', 'COOKED'):
                        possible_actions.append(f"PutDown({held.name}, {held.state}, {sx}, {sy})")

                # Colocar em estação (tábua, fogão, pia)
                elif tile in ('S', 'T', 'B', 'W') and station_state and station_state.content is None:
                    if tile in ('T', 'B') and isinstance(held, Ingredient) and held.state == 'RAW':
                        possible_actions.append(f"PutDown({held.name}, {held.state}, {sx}, {sy})")
                    elif tile == 'S' and isinstance(held, Ingredient) and held.state == 'CHOPPED':
                        possible_actions.append(f"PutDown({held.name}, {held.state}, {sx}, {sy})")
                    elif tile == 'W' and isinstance(held, Plate) and held.state == 'DIRTY':
                        possible_actions.append(f"PutDown(Plate, DIRTY, {sx}, {sy})")

                # Entrega (somente se o prato satisfaz o pedido ativo)
                if tile == 'D' and isinstance(held, Plate) and held.state == 'WITH_FOOD':
                    if state.active_orders:
                        order = state.active_orders[0]
                        if order_satisfied_by_plate(held, order):
                            possible_actions.append(f"Deliver({sx}, {sy})")

                # Pegar comida diretamente do fogão/tábua para o prato limpo
                if isinstance(held, Plate) and held.state == 'CLEAN':
                    if tile in ('S', 'T', 'B') and station_state and station_state.content:
                        content = station_state.content
                        if (tile == 'S' and content.state == 'COOKED') or \
                           (tile in ('T', 'B') and content.state == 'CHOPPED'):
                            possible_actions.append(f"PickUp({content.name}, {content.state}, {sx}, {sy})")

            # Ações específicas de estação (Cortar, Aguardar)
            if tile in ('T', 'B') and station_state and station_state.content:
                if isinstance(station_state.content, Ingredient) and station_state.content.state == 'RAW':
                    possible_actions.append(f"Chop({sx}, {sy})")

            if tile == 'S' and station_state and station_state.content:
                if isinstance(station_state.content, Ingredient) and station_state.content.state == 'CHOPPED':
                    possible_actions.append(f"Wait({sx}, {sy})")

            if tile == 'W' and station_state and station_state.content:
                if isinstance(station_state.content, Plate) and station_state.content.state == 'DIRTY':
                    possible_actions.append(f"Wait({sx}, {sy})")

        return possible_actions

    def result(self, state: KitchenState, action: str) -> KitchenState:
        match = re.match(r"(\w+)\((.*)\)", action)
        if not match:
            return state._replace(time=state.time + 1)

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
                elif state.get_layout_at(pos[0], pos[1]) == 'O':  # fonte de cebola
                    picked_item = Ingredient(name="Onion", state="RAW")
                elif state.get_layout_at(pos[0], pos[1]) == 'V':  # fonte de tomate
                    picked_item = Ingredient(name="Tomato", state="RAW")

            # Caso especial: pegar ingrediente diretamente em prato limpo que o agente segura
            if isinstance(state.held_item, Plate) and state.held_item.state == 'CLEAN':
                if isinstance(picked_item, Ingredient):
                    new_contents = list(state.held_item.contents)
                    new_contents.append(picked_item.name)
                    new_held_item = state.held_item._replace(
                        contents=tuple(new_contents), state="WITH_FOOD"
                    )
                    new_grid_objects = [obj for obj in new_grid_objects if obj[0] != pos]
            else:
                new_held_item = picked_item
                new_grid_objects = [obj for obj in new_grid_objects if obj[0] != pos]

        elif act_name == "PutDown":
            pos = (int(params[2]), int(params[3]))
            tile = state.get_layout_at(pos[0], pos[1])
            obj_at_pos = state.get_object_at(pos)

            if tile == 'G':  # Lixeira: descarta o item
                new_held_item = None
            elif isinstance(obj_at_pos, Plate) and obj_at_pos.state == 'CLEAN' and isinstance(new_held_item, Ingredient):
                # Montagem: colocar ingrediente no prato sobre o balcão
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

        elif act_name == "PutInPot":
            # Coloca ingrediente CHOPPED na panela
            pos = (int(params[1]), int(params[2]))
            pot = new_stations_state[pos].content
            if isinstance(pot, Pot) and isinstance(new_held_item, Ingredient):
                new_ingredients = pot.ingredients + (new_held_item.name,)
                needed = pot_needed_count_for_order(new_active_orders, new_ingredients)
                if needed == 0:  # todos os ingredientes colocados → começa a cozinhar
                    new_pot_state = "COOKING"
                else:            # ainda faltam ingredientes
                    new_pot_state = "FILLING"
                new_pot = Pot(ingredients=new_ingredients, state=new_pot_state, progress=0)
                new_stations_state[pos] = StationState(progress=0, content=new_pot)
                new_held_item = None

        elif act_name == "ServeFromPot":
            # Agente tem prato limpo e serve a sopa pronta nele
            pos = (int(params[0]), int(params[1]))
            pot = new_stations_state[pos].content
            if isinstance(pot, Pot) and pot.state == 'READY' and isinstance(new_held_item, Plate):
                new_held_item = new_held_item._replace(
                    contents=pot.ingredients, state="WITH_FOOD"
                )
                # Reseta a panela para vazia
                new_stations_state[pos] = StationState(progress=0, content=Pot())

        elif act_name == "Deliver":
            if new_active_orders:
                delivered_order = new_active_orders.pop(0)
                new_delivered_orders.append(delivered_order)
                new_held_item = None

                # Gera prato sujo no balcão de retorno (P) ou em qualquer balcão vazio (C)
                return_pos = None
                for y_idx, row in enumerate(state.layout):
                    for x_idx, char in enumerate(row):
                        if char == 'P':
                            if state.get_object_at((x_idx, y_idx)) is None:
                                return_pos = (x_idx, y_idx)
                                break
                    if return_pos:
                        break

                if not return_pos:
                    for y_idx, row in enumerate(state.layout):
                        for x_idx, char in enumerate(row):
                            if char == 'C':
                                if state.get_object_at((x_idx, y_idx)) is None:
                                    return_pos = (x_idx, y_idx)
                                    break
                        if return_pos:
                            break

                if return_pos:
                    new_grid_objects.append((return_pos, Plate(state="DIRTY")))

        elif act_name == "Chop":
            pos = (int(params[0]), int(params[1]))
            s_state = new_stations_state[pos]
            new_progress = s_state.progress + 1
            new_content = s_state.content
            if new_progress >= CHOP_DURATION:  # corte concluído
                if isinstance(new_content, Ingredient):
                    new_content = new_content._replace(state='CHOPPED')
                new_progress = 0
            new_stations_state[pos] = StationState(progress=new_progress, content=new_content)

        elif act_name == "Extinguish":
            pos = (int(params[0]), int(params[1]))
            new_stations_state[pos] = StationState(progress=0, is_on_fire=False, content=None)

        # Progresso global por tick: fogões (S), pias (W), panelas (K)
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
                new_stations_state[pos] = StationState(
                    progress=new_progress, content=new_content, is_on_fire=new_fire
                )

            elif tile == 'W' and isinstance(s_state.content, Plate) and s_state.content.state == 'DIRTY':
                new_progress = s_state.progress + 1
                new_content = s_state.content
                if new_progress >= WASH_DURATION:
                    new_content = Plate(state="CLEAN")
                    new_progress = 0
                new_stations_state[pos] = StationState(progress=new_progress, content=new_content)

            elif tile == 'K' and isinstance(s_state.content, Pot) and s_state.content.state == 'COOKING':
                new_progress = s_state.progress + 1
                new_pot = s_state.content
                if new_progress >= POT_COOK_DURATION:
                    new_pot = new_pot._replace(state='READY', progress=new_progress)
                else:
                    new_pot = new_pot._replace(progress=new_progress)
                new_stations_state[pos] = StationState(progress=new_progress, content=new_pot)

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

    # 
    def h(self, node):
        state = node.state
        if not state.active_orders:
            return 0

        ax, ay = state.agent_pos
        held = state.held_item

        # Varredura de pontos de interesse
        chop_stations = []
        stoves = []
        deliveries = []
        sinks = []
        extinguishers = []
        plates_clean = []
        plates_dirty = []
        cooked_food = []
        chopped_food = []
        raw_sources_onion = []
        raw_sources_tomato = []
        pot_stations = []

        for y, row in enumerate(state.layout):
            for x, char in enumerate(row):
                pos = (x, y)
                if char == 'T' or char == 'B':
                    chop_stations.append(pos)
                elif char == 'S':
                    stoves.append(pos)
                elif char == 'D':
                    deliveries.append(pos)
                elif char == 'W':
                    sinks.append(pos)
                elif char == 'O':
                    raw_sources_onion.append(pos)
                elif char == 'V':
                    raw_sources_tomato.append(pos)
                elif char == 'K':
                    pot_stations.append(pos)

        for pos, obj in state.grid_objects:
            if isinstance(obj, Plate):
                if obj.state == 'CLEAN':
                    plates_clean.append(pos)
                elif obj.state == 'DIRTY':
                    plates_dirty.append(pos)
            if isinstance(obj, Ingredient):
                if obj.state == 'COOKED':
                    cooked_food.append(pos)
                elif obj.state == 'CHOPPED':
                    chopped_food.append(pos)

        for pos, st in state.stations_state:
            if st.content:
                obj = st.content
                if isinstance(obj, Plate):
                    if obj.state == 'CLEAN':
                        plates_clean.append(pos)
                    elif obj.state == 'DIRTY':
                        plates_dirty.append(pos)
                if isinstance(obj, Ingredient):
                    if obj.state == 'COOKED':
                        cooked_food.append(pos)
                    elif obj.state == 'CHOPPED':
                        chopped_food.append(pos)

        # Ordem ativa e sua receita
        order = state.active_orders[0]
        needed_ingredients = pot_required_ingredients(order)

        def md(a, b):
            return abs(a[0] - b[0]) + abs(a[1] - b[1])

        def best_dist(pos, targets):
            if not targets:
                return 0
            return min(md(pos, t) for t in targets)

        agent = (ax, ay)

        # --- Incêndio
        fire_positions = [pos for pos, st in state.stations_state if st.is_on_fire]
        if fire_positions:
            if isinstance(held, Extinguisher):
                return best_dist(agent, fire_positions)
            else:
                return best_dist(agent, extinguishers) + best_dist(extinguishers[0] if extinguishers else agent, fire_positions)

        if isinstance(held, Extinguisher):
            return best_dist(agent, extinguishers)

        # --- Prato sujo na mão
        if isinstance(held, Plate) and held.state == 'DIRTY':
            return best_dist(agent, sinks) + WASH_DURATION

        # --- Prato com comida: entregar
        if isinstance(held, Plate) and held.state == 'WITH_FOOD':
            return best_dist(agent, deliveries)

        # --- Receita usa panela (K)?
        uses_pot = bool(pot_stations) and bool(needed_ingredients)

        if uses_pot:
            # Verificar estado da panela
            for pot_pos in pot_stations:
                ss = state.get_station_state_at(pot_pos)
                if ss and isinstance(ss.content, Pot):
                    pot = ss.content
                    if pot.state == 'READY':
                        # Só precisamos de prato limpo → servir → entregar
                        if isinstance(held, Plate) and held.state == 'CLEAN':
                            return md(agent, pot_pos) + best_dist(pot_pos, deliveries)
                        return best_dist(agent, plates_clean) + best_dist(
                            plates_clean[0] if plates_clean else agent, pot_pos
                        ) + best_dist(pot_pos, deliveries)

                    if pot.state == 'COOKING':
                        remaining_cook = max(0, POT_COOK_DURATION - ss.progress)
                        return remaining_cook + best_dist(pot_pos, deliveries)

                    # EMPTY or FILLING: still need more ingredients
                    already_in = list(pot.ingredients)
                    still_needed = list(needed_ingredients)
                    for ing in already_in:
                        if ing in still_needed:
                            still_needed.remove(ing)

                    # Estimate: for each missing ingredient
                    # agent → source → chop → pot
                    if still_needed:
                        if isinstance(held, Ingredient) and held.state == 'CHOPPED' and held.name in still_needed:
                            still_needed.remove(held.name)
                            cost = md(agent, pot_pos)
                        elif isinstance(held, Ingredient) and held.state == 'RAW':
                            cost = best_dist(agent, chop_stations) + CHOP_DURATION + best_dist(
                                chop_stations[0] if chop_stations else agent, pot_pos)
                        else:
                            # Walk to source for first needed ingredient
                            first_ing = still_needed[0]
                            sources = raw_sources_onion if first_ing == 'Onion' else raw_sources_tomato
                            cost = best_dist(agent, sources) + best_dist(
                                sources[0] if sources else agent, chop_stations
                            ) + CHOP_DURATION + best_dist(
                                chop_stations[0] if chop_stations else agent, pot_pos
                            )
                        # Each extra ingredient
                        for ing in still_needed[1:]:
                            sources = raw_sources_onion if ing == 'Onion' else raw_sources_tomato
                            cost += best_dist(agent, sources) + best_dist(
                                sources[0] if sources else agent, chop_stations
                            ) + CHOP_DURATION + best_dist(
                                chop_stations[0] if chop_stations else agent, pot_pos
                            )
                        # After filling: cook + serve + deliver
                        cost += POT_COOK_DURATION + best_dist(pot_pos, deliveries)
                        return cost

                    # All ingredients in pot but not yet COOKING (shouldn't happen)
                    return POT_COOK_DURATION + best_dist(pot_pos, deliveries)

        # --- Receita simples (sem panela, ou fallback)

        if isinstance(held, Plate) and not held.contents:
            if chopped_food or cooked_food:
                best = float("inf")
                for pos in chopped_food + cooked_food:
                    for d in deliveries:
                        best = min(best, md(agent, pos) + md(pos, d))
                return best
            targets = [
                (x, y)
                for y, row in enumerate(state.layout)
                for x, char in enumerate(row)
                if char == 'C' and state.get_object_at((x, y)) is None
            ]
            return best_dist(agent, targets) if targets else 0

        if isinstance(held, Ingredient) and held.state == 'COOKED':
            best = float("inf")
            for pc in plates_clean:
                for d in deliveries:
                    best = min(best, md(agent, pc) + md(pc, d))
            return best

        if isinstance(held, Ingredient) and held.state == 'RAW':
            best = float("inf")
            for cs in chop_stations:
                for s in stoves:
                    for d in deliveries:
                        best = min(best, md(agent, cs) + CHOP_DURATION + md(cs, s) + COOK_DURATION + md(s, d))
            return best

        if isinstance(held, Ingredient) and held.state == 'CHOPPED':
            best = float("inf")
            for s in stoves:
                for d in deliveries:
                    best = min(best, md(agent, s) + COOK_DURATION + md(s, d))
            return best

        if cooked_food:
            best = float("inf")
            for cf in cooked_food:
                for pc in plates_clean:
                    for d in deliveries:
                        best = min(best, md(agent, cf) + md(cf, pc) + md(pc, d))
            return best

        if chopped_food:
            best = float("inf")
            for cf in chopped_food:
                for s in stoves:
                    for d in deliveries:
                        best = min(best, md(agent, cf) + md(cf, s) + COOK_DURATION + md(s, d))
            return best

        # Nada feito
        raw_sources = raw_sources_onion + raw_sources_tomato
        best = float("inf")
        for rs in raw_sources:
            for cs in chop_stations:
                for s in stoves:
                    for d in deliveries:
                        best = min(best,
                                   md(agent, rs) + md(rs, cs) + CHOP_DURATION +
                                   md(cs, s) + COOK_DURATION + md(s, d))
        return best