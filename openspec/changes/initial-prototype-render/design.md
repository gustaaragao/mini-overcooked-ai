## Context
This project implements a simplified version of "Overcooked" for an Artificial Intelligence course. The environment must support search agents that plan a sequence of actions to fulfill culinary orders. It relies on the `aima-python` library for search algorithms and environment base classes.

## Goals / Non-Goals

**Goals:**
- Provide a hashable state representation suitable for `A*` and other search algorithms.
- Implement a transition model (`result` function) that handles movement and station interactions.
- Create an ASCII-based `render()` method for visualizing the simulation steps.
- Support JSON-based initialization of map and orders.

**Non-Goals:**
- Real-time physics or fluid movement (only discrete grid steps).
- Multi-agent coordination in this initial prototype (focus on single-agent).
- Complex UI/Graphics (terminal output only).

## Decisions

### 1. State Representation
- **Decision**: Use a `NamedTuple` or `frozen dataclass` to represent the kitchen state.
- **Rationale**: Search algorithms in `aima-python` require states to be hashable to keep track of visited nodes.
- **Alternatives**: Mutable dictionaries (would require manual hashing logic).

### 2. Heuristics Logic
- **Decision**: Primary heuristic will be Manhattan distance to the next logical goal (e.g., nearest station for the current task).
- **Rationale**: Admissible and easy to compute in a grid world.
- **Refinement**: Weights will be applied based on task priority (e.g., "washing a plate" might have higher weight if no clean plates are available).

### 3. Action Filtering (Pruning)
- **Decision**: The `actions(state)` method will perform "pre-search" pruning by only returning actions that are physically and logically possible (e.g., cannot chop without a knife or ingredient).
- **Rationale**: Dramatically reduces the branching factor.

## Risks / Trade-offs

- **[Risk] State Space Explosion** → [Mitigation] Keep the grid small (max 10x10) and limit the active order queue size.
- **[Risk] AIMA Package Differences** → [Mitigation] Use standard `search.Problem` and `agents.Environment` interfaces which are stable across versions.
