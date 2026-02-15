## ADDED Requirements

### Requirement: Grid-based Environment
The system SHALL maintain a 2D grid representation of the kitchen environment where agents and stations reside.

#### Scenario: Valid Grid Initialization
- **WHEN** a JSON grid map is provided to the environment
- **THEN** the environment SHALL instantiate a grid with the specified dimensions and static objects (counters, stoves, sinks)

### Requirement: Station Interaction Logic
The environment SHALL allow agents to interact with specific station types (Counter, Stove, Sink, Delivery).

#### Scenario: Ingredient Placement on Counter
- **WHEN** an agent performs a 'PutDown' action on an empty counter tile with an ingredient
- **THEN** the counter SHALL now contain that ingredient and the agent's hands SHALL be empty

### Requirement: ASCII Rendering
The environment SHALL provide a `render()` method that outputs a text-based representation of the current state to the console.

#### Scenario: Visualizing Agent and Stations
- **WHEN** the `render()` method is called
- **THEN** it SHALL display a grid where 'A' represents the agent, 'S' represents a Stove, 'C' a Counter, and 'K' a Sink, along with any held items.
