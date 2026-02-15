import re
from aima3.search import Problem
from models.models import KitchenState, Order
from typing import List, Tuple, Optional

class KitchenProblem(Problem):
    def __init__(self, initial: KitchenState, goal_orders: List[Order] = None):
        super().__init__(initial)
        self.goal_orders = goal_orders

    def actions(self, state: KitchenState) -> List[str]:
        possible_actions = []
        x, y = state.agent_pos
        
        # 1. Movimentação (Apenas para o chão '.')
        for dx, dy in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
            nx, ny = x + dx, y + dy
            if state.get_layout_at(nx, ny) == '.':
                possible_actions.append(f"Move({nx}, {ny})")
            
        # 2. Interações com Estações Adjacentes
        # Checa as 4 direções adjacentes para ver se há uma estação
        for dx, dy in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
            sx, sy = x + dx, y + dy
            tile = state.get_layout_at(sx, sy)
            
            if tile in ('C', 'S', 'D', 'K'): # Counter, Stove, Delivery, Sink
                # Lógica simplificada de interação
                if state.held_item == "":
                    # Se o balcão tiver algo (grid_objects), pode pegar
                    obj_on_tile = state.get_object_at((sx, sy))
                    if obj_on_tile:
                        possible_actions.append(f"PickUp({obj_on_tile}, {sx}, {sy})")
                    elif tile == 'C': # Se for balcão vazio, talvez tenha ingredientes infinitos (exemplo)
                        possible_actions.append(f"PickUp(Onion, {sx}, {sy})")
                else:
                    possible_actions.append(f"PutDown({state.held_item}, {sx}, {sy})")
                
                if tile == 'D' and state.held_item != "":
                    possible_actions.append(f"Deliver({sx}, {sy})")

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
        
        if act_name == "Move":
            new_agent_pos = (int(params[0]), int(params[1]))
            
        elif act_name == "PickUp":
            new_held_item = params[0]
            # Remove do grid se estava lá
            pos = (int(params[1]), int(params[2]))
            new_grid_objects = [obj for obj in new_grid_objects if obj[0] != pos]
            
        elif act_name == "PutDown":
            pos = (int(params[1]), int(params[2]))
            new_grid_objects.append((pos, new_held_item))
            new_held_item = ""
            
        elif act_name == "Deliver":
            if new_active_orders:
                order_delivered = new_active_orders.pop(0)
                new_delivered_orders.append(order_delivered)
                new_held_item = ""

        return KitchenState(
            agent_pos=new_agent_pos,
            held_item=new_held_item,
            layout=state.layout,
            grid_objects=tuple(new_grid_objects),
            active_orders=tuple(new_active_orders),
            delivered_orders=tuple(new_delivered_orders),
            time=state.time + 1
        )

    def goal_test(self, state: KitchenState) -> bool:
        return len(state.active_orders) == 0

    def h(self, node):
        """
        Heurística: Manhattan Distance.
        Se não segura nada: vai até o ingrediente mais próximo (Counter 'C').
        Se segura algo: vai até a entrega ('D').
        """
        state = node.state
        if not state.active_orders: return 0
        
        ax, ay = state.agent_pos
        targets = []
        
        if state.held_item:
            # Procura estações de entrega 'D'
            for y, row in enumerate(state.layout):
                for x, char in enumerate(row):
                    if char == 'D': targets.append((x, y))
        else:
            # Procura balcões 'C'
            for y, row in enumerate(state.layout):
                for x, char in enumerate(row):
                    if char == 'C': targets.append((x, y))
        
        if not targets: return 10
        
        # Retorna a menor distância de Manhattan até um alvo
        return min(abs(ax - tx) + abs(ay - ty) for tx, ty in targets)
