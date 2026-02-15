## 1. Project Infrastructure

- [x] 1.1 Create directory structure (`env/`, `agents/`, `problems/`).
- [x] 1.2 Verify `aima` package availability in the virtual environment.

## 2. Core Data Models

- [x] 2.1 Implement `Order` class (Ingredients, Instant, Duration, Score).
- [x] 2.2 Define `KitchenState` as a hashable `NamedTuple` or frozen dataclass.
- [x] 2.3 Implement JSON loader for map grid and initial orders.

## 3. Environment and Visualization

- [x] 3.1 Implement `KitchenEnvironment` subclassing `aima.agents.Environment`.
- [x] 3.2 Implement `KitchenEnvironment.render()` with ASCII grid output.
- [x] 3.3 Implement station interaction logic (Counter, Stove, Sink, Delivery).

## 4. Search Problem and Mechanics

- [x] 4.1 Implement `KitchenProblem` subclassing `aima.search.Problem`.
- [x] 4.2 Implement `actions(state)` with validity checks (pruning).
- [x] 4.3 Implement `result(state, action)` transition model.

## 5. Heuristics and Explanation

- [x] 5.1 Implement Manhattan distance heuristic with task-based weights.
- [x] 5.2 Implement look-ahead logic (depth k) for action filtering.
- [x] 5.3 Prepare explanation of the heuristic logic and choices.
