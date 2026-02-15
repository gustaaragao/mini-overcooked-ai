## ADDED Requirements

### Requirement: Search-Based Action Selection
The agent SHALL use a search algorithm to determine the optimal sequence of actions to fulfill active orders.

#### Scenario: Action Generation
- **WHEN** the agent's `actions(state)` method is called
- **THEN** it SHALL return only valid actions (e.g., cannot 'Chop' if not at a counter with an unchopped ingredient)

### Requirement: Transition Model Accuracy
The `result(state, action)` method SHALL accurately reflect the state change in the kitchen environment.

#### Scenario: Picking Up Ingredient
- **WHEN** the action 'PickUp(Onion)' is applied to a state where the agent is next to an Onion on a counter
- **THEN** the resulting state SHALL show the agent holding the Onion and the counter being empty

### Requirement: Goal Test Definition
The `goal_test(state)` SHALL evaluate to true when all required orders for a specific scenario have been delivered.

#### Scenario: Fulfillment Goal
- **WHEN** the delivered orders list matches the target orders for the problem instance
- **THEN** `goal_test` SHALL return True
