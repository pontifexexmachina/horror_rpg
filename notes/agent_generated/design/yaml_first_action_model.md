# YAML-First Action Model

## Problem

The simulator currently treats YAML action files as labels over Python behavior. An action chooses an effect union such as `buff` or `contest_move`, but the real semantics still live in long handler branches. That makes the data descriptive instead of authoritative.

## Direction

Actions should move toward an explicit `procedure` field that describes execution as a sequence of supported primitives. Python should own the interpreter and state transitions. YAML should own the action plan.

## Current Procedure Vocabulary

- `attack`: perform an attack roll using the declared stat, skill, and optional weapon override
- `check`: perform a difficulty-based check
- `contest`: perform an opposed roll
- `apply_condition`: add a condition to `self` or `target`
- `heal`: restore hit points to `self` or `target`
- `stress`: apply stress to `target`
- `apply_attack_modifier`: apply a temporary attack modifier condition-like payload
- `clear_condition`: remove a condition from `self` or `target`
- `move_target`: move the target using a destination supplied by the action choice

Each non-roll step can declare `when: always|success|critical` so the data carries the success table instead of Python branches.

## Migration Strategy

1. Keep the legacy `effect` field as a compatibility shim while we migrate runtime execution.
2. Add `procedure` to every existing action YAML so the declarative source of truth starts taking shape immediately.
3. Teach the engine to execute `procedure` for migrated actions, falling back to `effect` only for unmigrated actions.
4. Once all actions execute from `procedure`, remove the legacy effect union and collapse the remaining bespoke handlers into interpreter primitives.

## What This Buys Us

- Action YAML becomes the primary semantic source of truth.
- New actions become composition of primitives instead of new Python branches.
- Validation can happen at load time against a closed vocabulary.
- Engine complexity shifts from many effect families to a small interpreter plus domain transitions.

## Immediate Next Step

Implement a procedure interpreter for the existing vocabulary and route a handful of actions such as `rally`, `trip`, `shove`, and `stand_up` through it first.
