## ADDED Requirements

### Requirement: Order Queue Management
The system SHALL maintain a queue of orders, each with a specific arrival time (Instant) and duration (Duration).

#### Scenario: Order Activation
- **WHEN** the current simulation time reaches an order's 'Instant'
- **THEN** the order SHALL become active and available for fulfillment

### Requirement: Recipe and Ingredient Tracking
Each order SHALL define a list of required ingredients and their required state (e.g., Chopped, Cooked).

#### Scenario: Successful Dish Delivery
- **WHEN** an agent delivers a dish that matches all required ingredients and states for an active order
- **THEN** the order SHALL be marked as fulfilled and removed from the active queue

### Requirement: Scoring System
The system SHALL award points upon successful delivery of an order based on its predefined 'Score'.

#### Scenario: Points Awarded
- **WHEN** an order is fulfilled before its 'Duration' expires
- **THEN** the total score SHALL increase by the order's score value
