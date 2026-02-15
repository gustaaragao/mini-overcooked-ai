## Why
Establish the foundational architecture for the Mini-Overcooked AI project. This change implements the core environment, state representation, and visualization necessary to simulate kitchen operations and order fulfillment using search-based agents.

## What Changes
- **KitchenEnvironment**: A class managing the grid-based world, agent positions, and station states (counters, stoves, sinks).
- **State Representation**: Support for JSON-based initialization of the map grid and order queue.
- **Order Management**: `Order` class with attributes for ingredients, timing (instant/duration), and scoring.
- **Game Mechanics**: Logic for picking up ingredients, chopping, cooking, and handling dirty dishes.
- **Rendering**: ASCII-based visualization of the environment state.
- **AIMA Integration**: Subclassing `Environment` and `Problem` from the `aima` package.

## Capabilities

### New Capabilities
- `kitchen-core`: Grid management, station logic, and ASCII `render()`.
- `order-logic`: Order queue handling , ingredients tracking, and scoring. Maybe a priority queue.
- `search-problem`: Mapping of kitchen mechanics to the AIMA `Problem` structure (actions, result, goal_test).

### Modified Capabilities
- None (Initial implementation).

## Impact
This serves as the backbone for all future agent implementations. It defines the "world rules" and the perception/action interface for the AI.
