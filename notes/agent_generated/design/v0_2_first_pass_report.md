# v0.2 First Pass Report

Date: 2026-04-26

This report summarizes the first agent-driven manuscript pass after adopting the author-as-creative-director workflow.

## Files Changed

- `game_rules.qmd`
- `notes/README.md`
- `notes/agent_generated/design/agent_driven_workflow.md`
- generated Quarto output in `docs/` after render verification

## What Changed

The rules manuscript was rewritten from a loose skeleton into a clearer playable core.

Major additions:

- survival-horror play loop
- Stats, Skills, derived values, and core resolution
- Push, Stress, Panic, and Breakdown
- fiction-first resources and inventory pressure
- PC death states and ordinary monster removal at 0 HP
- action economy and area-based positioning
- current core actions aligned with simulator behavior
- conditions and compact weapon/talent lists
- between-scene recovery sketch
- open design calls for the next pass

The new workflow note establishes:

- author as creative director
- agents as production leads
- structured data, simulator, manuscript, and generated notes as separate canon layers
- a default production loop for rules changes

## Verification

Commands run:

- `uv run ddb-sim validate`
- `uv run --extra dev pytest -q`
- `quarto render`
- `uv run ddb-sim benchmark --suite core --runs 50 --seed 20260426`
- `uv run ddb-sim session-benchmark --plan core_night --runs 50 --seed 20260426`

Results:

- simulator validation passed
- test suite passed: 88 tests
- Quarto rendered successfully
- core benchmark completed
- core session benchmark completed

## Benchmark Snapshot

Core benchmark, 50 runs per scenario:

- team A win rate: `0.96`
- average rounds: `3.80`
- p50 rounds: `4`
- p90 rounds: `7`
- average pushes per encounter: `23.99`
- team A final status rates:
  - normal: `0.9675`
  - wounded: `0.0175`
  - critical: `0.0108`
  - broken: `0.0017`
  - dead: `0`

Core night session benchmark, 50 runs:

- average completed scenarios: `3`
- average final HP: `4.345`
- average final Stress: `6.05`
- average remaining bandages: `0.515`
- average remaining medkits: `0`
- average remaining sidearm ammo: `1.65`
- final team status rates:
  - normal: `0.67`
  - wounded: `0.115`
  - critical: `0.155`
  - dead: `0.005`
  - broken: `0`

## Interpretation

The current simulator shape supports the intended high-level horror pattern:

- individual encounters are usually survived
- the session leaves the party visibly degraded
- stress rises near the panic threshold without constantly breaking characters
- medkits are fully consumed in the core night plan
- death is rare but not impossible

The strongest caution is that Push frequency is extremely high in several benchmark personas. That may be acceptable for desperate horror play, but it should be checked once Stress recovery, safe rooms, and time pressure are more explicit.

## Next Design Targets

Recommended next pass:

1. Decide and encode the new Grit direction.
2. Add safe rooms and short recovery procedures.
3. Add scavenging nodes to session play.
4. Draft player archetypes as manuscript-facing character options.
5. Begin the intro scenario as the first full play target.

The immediate mechanical priority is Grit. It currently works, but it still points toward free self-healing rather than fiction-first attrition.
