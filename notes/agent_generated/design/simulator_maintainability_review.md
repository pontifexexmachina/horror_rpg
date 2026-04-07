# Simulator Maintainability Review

## Current hotspots

- `src/dead_by_dawn_sim/engine.py` is the main orchestration bottleneck at 758 lines. `_apply_action_effect()` is carrying too many branches and game-rule variants in one place.
- `src/dead_by_dawn_sim/personas.py` centralizes most AI scoring logic in a few long functions, which makes adding new behaviors risky.
- `src/dead_by_dawn_sim/runner.py` mixes encounter orchestration, result aggregation, and reporting concerns.
- Small but meaningful duplication already exists:
  - `_attack_weapon()` in both `actions.py` and `engine.py`
  - `_has_condition()` in both `actions.py` and `engine.py`
  - actor snapshot dictionaries in both `runner.py` and `session.py`
  - manual `EncounterState(...)` reconstruction in both `runner.py` and `session.py`

## Tooling baseline

- Ruff now covers complexity-focused rules with a pragmatic baseline:
  - `C90` for cyclomatic complexity
  - `PLR` for return/branch/statement pressure
  - `SIM` for simplification opportunities
- Existing hot modules are temporarily grandfathered with per-file ignores so new code is held to the standard without immediately breaking the current branch.
- `tools/check_module_sizes.py` adds a file-length ratchet because Ruff does not provide a native module-length rule.
- `.pre-commit-config.yaml` is set up for `prek`, with:
  - `ruff check`
  - `ruff format --check`
  - `basedpyright`
  - module-size guard
  - `pytest` on `pre-push`
  - `vulture` on `pre-push`
  - `jscpd` on `pre-push`

## Library recommendations

- Replace the homegrown `dice.py` roller with [d20](https://github.com/avrae/d20) when we do the next dice refactor.
  - That removes custom dice parsing/rolling pressure before it grows.
  - It also gives us a standard expression language if the simulator starts needing richer roll notation.
- Prefer standard-library helpers before adding bespoke glue:
  - `dataclasses.asdict()` instead of custom dataclass serialization
  - shared snapshot/state helpers instead of repeated dict-building
- Avoid adding more runtime libraries unless they remove a real maintenance burden. Right now the strongest win is `d20`; the rest of the codebase mostly wants better boundaries more than more dependencies.

## Refactor order

1. Split `engine.py` by effect family:
   - attack resolution
   - healing/support resolution
   - movement/reaction resolution
2. Pull shared state helpers into one place:
   - `has_condition`
   - `attack_weapon`
   - actor snapshot serialization
   - safe `EncounterState` copy/update helpers
3. Break persona scoring into composable scorers:
   - base action scoring
   - tactical context
   - objective pressure
   - closeout logic
4. Keep `runner.py` focused on encounter flow and push reporting/aggregation logic into a reporting module.

## Suggested command cadence

- `prek run ruff-check ruff-format basedpyright --all-files`
- `prek run module-size --all-files`
- `prek run pytest vulture jscpd --all-files`
