import heapq
import time

from aima3.agents import Agent
from aima3.search import Node

from problems.kitchen_problem import KitchenProblem
from utils.recipe_utils import pot_required_ingredients
from models.entities import Ingredient, Plate, Extinguisher, Pot


def astar_search_with_limit(problem, h, max_expansions=50000, max_time_s=5.0):
    """A* com limites de expansão e tempo.

    Justificativa: o espaço de estados cresce muito com receitas multi-ingrediente.
    A versão padrão do aima3 não tem proteção contra timeout, o que causaria
    travamentos durante a busca de sub-objetivos complexos como encher uma panela.
    Esta implementação é idêntica ao A* clássico, porém com salvaguardas.
    """
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
        if time.monotonic() - start_t > max_time_s:
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
        """Identifica um sub-objetivo alcançável com base no estado atual."""

        # 1. Incêndio — prioridade máxima
        if any(s.is_on_fire for _, s in state.stations_state):
            if isinstance(state.held_item, Extinguisher):
                return lambda s: not any(st.is_on_fire for _, st in s.stations_state)
            else:
                return lambda s: isinstance(s.held_item, Extinguisher)

        # 2. Estações com progresso (Chop, Cook, Wash)
        for pos, s_state in state.stations_state:
            if s_state.content:
                tile = state.get_layout_at(pos[0], pos[1])

                # RAW na tábua --> CHOPPED
                if tile in ('T', 'B') and isinstance(s_state.content, Ingredient) and s_state.content.state == 'RAW':
                    return lambda s: any(
                        st_pos == pos and st.content and st.content.state == 'CHOPPED'
                        for st_pos, st in s.stations_state
                    )

                # CHOPPED no fogão --> COOKED
                if tile == 'S' and isinstance(s_state.content, Ingredient) and s_state.content.state == 'CHOPPED':
                    return lambda s: any(
                        st_pos == pos and st.content and st.content.state == 'COOKED'
                        for st_pos, st in s.stations_state
                    )

                # DIRTY plate na pia --> CLEAN
                if tile == 'W' and isinstance(s_state.content, Plate) and s_state.content.state == 'DIRTY':
                    return lambda s: any(
                        st_pos == pos and st.content and isinstance(st.content, Plate) and st.content.state == 'CLEAN'
                        for st_pos, st in s.stations_state
                    )

                # Panela cozinhando --> READY
                if tile == 'K' and isinstance(s_state.content, Pot) and s_state.content.state == 'COOKING':
                    return lambda s: any(
                        st_pos == pos and isinstance(st.content, Pot) and st.content.state == 'READY'
                        for st_pos, st in s.stations_state
                    )

        # 3. Verificar se há panela que precisa de ingredientes
        if state.active_orders:
            order = state.active_orders[0]
            for pos, s_state in state.stations_state:
                tile = state.get_layout_at(pos[0], pos[1])
                if tile == 'K' and isinstance(s_state.content, Pot):
                    pot = s_state.content
                    if pot.state in ('EMPTY', 'FILLING'):
                        needed = list(pot_required_ingredients(order))
                        for ing in pot.ingredients:
                            if ing in needed:
                                needed.remove(ing)

                        if needed:
                            first_needed = needed[0]

                            # Se já está segurando esse ingrediente (chopped)
                            if (isinstance(state.held_item, Ingredient)
                                    and state.held_item.state == 'CHOPPED'
                                    and state.held_item.name == first_needed):
                                return lambda s, p=captured_pos, tc=target_count: any(
                                    st_pos == p and isinstance(st.content, Pot)
                                    and len(st.content.ingredients) >= tc
                                    for st_pos, st in s.stations_state
                                )

                            # Se está segurando RAW do ingrediente certo
                            if (isinstance(state.held_item, Ingredient)
                                    and state.held_item.state == 'RAW'
                                    and state.held_item.name == first_needed):
                                return lambda s: any(
                                    isinstance(st.content, Ingredient) and st.content.state == 'CHOPPED'
                                    and st.content.name == first_needed
                                    for _, st in s.stations_state
                                ) or (
                                    isinstance(s.held_item, Ingredient)
                                    and s.held_item.state == 'CHOPPED'
                                    and s.held_item.name == first_needed
                                )

                            # Nada na mão: buscar ingrediente
                            if state.held_item is None:
                                return lambda s, ing=first_needed: (
                                    isinstance(s.held_item, Ingredient)
                                    and s.held_item.name == ing
                                )

                    # Panela pronta --> precisa de prato para servir
                    if pot.state == 'READY':
                        if isinstance(state.held_item, Plate) and state.held_item.state == 'CLEAN':
                            return lambda s: isinstance(s.held_item, Plate) and s.held_item.state == 'WITH_FOOD'
                        if state.held_item is None:
                            return lambda s: isinstance(s.held_item, Plate) and s.held_item.state == 'CLEAN'

        # 4. Se segurando RAW --> levar para tábua de corte
        if isinstance(state.held_item, Ingredient) and state.held_item.state == 'RAW':
            return lambda s: any(
                st.content == state.held_item for _, st in s.stations_state
            )

        # 5. Se segurando CHOPPED --> levar para fogão (ou panela coberta acima)
        if isinstance(state.held_item, Ingredient) and state.held_item.state == 'CHOPPED':
            return lambda s: any(
                st.content == state.held_item for _, st in s.stations_state
            )

        # 6. Prato limpo na mão + comida pronta --> pegar comida
        if isinstance(state.held_item, Plate) and state.held_item.state == 'CLEAN':
            if any(
                s.content and isinstance(s.content, Ingredient) and s.content.state == 'COOKED'
                for _, s in state.stations_state
            ):
                return lambda s: isinstance(s.held_item, Plate) and s.held_item.state == 'WITH_FOOD'

        # 7. Prato WITH_FOOD --> entregar
        if isinstance(state.held_item, Plate) and state.held_item.state == 'WITH_FOOD':
            return lambda s: len(s.active_orders) < len(state.active_orders)

        # 8. Sem nada na mão
        if state.held_item is None:
            # Comida pronta no mapa --> pegar prato
            cooked_exists = any(
                s.content and isinstance(s.content, Ingredient) and s.content.state == 'COOKED'
                for _, s in state.stations_state
            )
            if cooked_exists:
                plate_exists = any(
                    isinstance(obj, Plate) and obj.state == 'CLEAN' for _, obj in state.grid_objects
                )
                if plate_exists:
                    return lambda s: isinstance(s.held_item, Plate) and s.held_item.state == 'CLEAN'

            # Nada em processamento --> pegar primeiro ingrediente da receita
            nothing_in_progress = not any(
                s.content for pos, s in state.stations_state
                if state.get_layout_at(pos[0], pos[1]) not in ('K',)
            )
            if nothing_in_progress and state.active_orders:
                order = state.active_orders[0]
                needed = pot_required_ingredients(order)
                if needed:
                    first_ing = needed[0]
                    return lambda s, ing=first_ing: (
                        isinstance(s.held_item, Ingredient) and s.held_item.name == ing
                    )

        return None

    def __call__(self, percept):
        """Decide a próxima ação com base na percepção (estado atual)."""
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
