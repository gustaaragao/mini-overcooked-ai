import heapq
import time
from aima3.search import Node

def astar_search_with_limit(problem, h, max_expansions=50000, max_time_s=5.0):
    """A* search com limites de expansão e tempo.
    
    Previne que o agente fique preso indefinidamente em sub-objetivos complexos/sem solução.
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

def weighted_astar_search(problem, h, weight=1.5):
    """Busca A* Ponderada (Weighted A*)"""

    node = Node(problem.initial)

    if problem.goal_test(node.state):
        return node

    frontier = []
    push_count = 0

    h_val = h(node)
    f_val = node.path_cost + weight * h_val

    heapq.heappush(frontier, (f_val, h_val, push_count, node))

    explored = {node.state: node.path_cost}

    while frontier:

        f, hv, _, node = heapq.heappop(frontier)

        if problem.goal_test(node.state):
            return node

        for child in node.expand(problem):

            if (child.state not in explored or
                child.path_cost < explored[child.state]):

                explored[child.state] = child.path_cost
                push_count += 1

                ch_val = h(child)
                f_child = child.path_cost + weight * ch_val

                heapq.heappush(
                    frontier,
                    (f_child, ch_val, push_count, child)
                )

    return None

def greedy_best_first_search(problem, h):
    """Greedy Best-First Search (sem limites)."""
    
    node = Node(problem.initial)

    if problem.goal_test(node.state):
        return node

    frontier = []
    push_count = 0

    heapq.heappush(frontier, (h(node), push_count, node))

    explored = set()

    while frontier:
        hv, _, node = heapq.heappop(frontier)

        if problem.goal_test(node.state):
            return node

        if node.state in explored:
            continue

        explored.add(node.state)

        for child in node.expand(problem):
            if child.state not in explored:
                push_count += 1
                heapq.heappush(frontier, (h(child), push_count, child))

    return None
