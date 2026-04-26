# Simulator Canon Drift Log

This note exists to track places where the simulator and the manuscript intentionally diverge, or may be diverging accidentally.

The book remains the publishable rules text. The simulator is an exploratory design tool.
When the two disagree, we should record the disagreement here rather than silently letting it drift.

## Status Labels

- `intentional divergence`: the simulator changed on purpose to test a design direction
- `accidental divergence`: the simulator and manuscript disagree without an explicit design decision
- `missing in sim`: the manuscript has a rule the simulator does not yet model
- `missing in book`: the simulator has adopted a design direction the book has not caught up to yet
- `resolved`: the manuscript and simulator now agree

## Current Divergences

### Stress thresholds
- Status: `resolved`
- Manuscript: panic at 8 stress, breakdown at 13 stress in `game_rules.qmd`
- Simulator: now matches those thresholds in `data/core_rules/default.yml`.
- Why it matters: this changes every stress, panic, and breakdown result the simulator produces.

### Grit
- Status: `resolved`
- Manuscript: `Grit` heals HP on a successful Brace roll.
- Simulator: now models `Grit` as self-healing again.
- Why it matters: this is a major survivability and resource-economy difference.

### Bleeding and Grit interaction
- Status: `resolved`
- Manuscript: successful `Grit` ends Bleeding.
- Simulator: successful `Grit` now clears `Bleeding`.
- Why it matters: it makes Bleeding materially stronger in the simulator if omitted.

### Stable state behavior
- Status: `resolved`
- Manuscript: a critical success on the critical-condition recovery roll puts you at Stable and 0 HP. If a Stable character takes damage before being healed, they become Critical.
- Simulator: now has an explicit `stable` status at 0 HP that cannot act or continue making death-track checks, and healing moves it back to `normal`.
- Why it matters: the book now states a playable edge rule instead of leaving the Stable state undefined.

### Monster death handling
- Status: `partially resolved`
- Manuscript: now states that ordinary monsters, animals, and human threats usually die, collapse, flee, or are removed from the encounter at 0 HP, while elite monsters, slashers, and supernatural nemeses may have special death rules.
- Simulator: ordinary monsters can use `death_mode: die_at_zero`, while PCs use the full death track.
- Why it matters: this dramatically changes encounter resolution and appears necessary for useful pacing.
- Why the simulator changed: hallway benchmarks showed that universal PC-style death tracks created artificial stalemates.
- Remaining gap: explicit monster durability classes still need to be defined.

### Inventory-gated healing and ammo
- Status: `partially resolved`
- Manuscript: combat text does not yet clearly express ammo consumption, bandage-gated `First Aid`, or medkit-driven between-scene recovery.
- Simulator: ranged attacks consume ammo, `First Aid` consumes bandages, and sessions carry forward ammo/bandages/medkits.
- Why it matters: this is central to the current survival-horror resource model.
- Why the simulator changed: to avoid dissociated per-encounter healing abstractions and move toward a Resident Evil-like loop.
- Current manuscript: `game_rules.qmd` now introduces fiction-first resources, ammo-spending firearm attacks, bandage-gated `First Aid`, and medkit treatment between scenes.
- Remaining gap: inventory slots, scavenging, light, ritual components, time pressure, and detailed safe-room procedures still need rules.

### Monster stress immunity
- Status: `partially resolved`
- Manuscript: current stress rules read as generally applicable and do not yet clearly state whether monsters participate in the stress economy.
- Simulator: ordinary monsters now use `stress_mode: ignore` and do not gain stress, panic, or break down.
- Why it matters: this removes a misleading simulator behavior where fear powers could shut monsters down like PCs.
- Why the simulator changed: fear is now treated as a player-facing horror pressure system rather than a universal morale track.
- Current manuscript: `game_rules.qmd` now says ordinary monsters do not track Stress unless a scenario or monster rule says otherwise.
- Remaining gap: monster exceptions still need explicit design.

### Universal fallback melee attacks
- Status: `resolved`
- Manuscript: some player builds do not currently read as having a clear last-resort attack once they run out of ammo.
- Simulator: all player templates now include a distinct `unarmed_attack` fallback melee option, while real melee specialists keep their weapon-based attacks.
- Why it matters: this removed misleading endgame churn where some PCs had no damaging action left and defaulted into weak support/control loops.
- Why the simulator changed: desperate violence should remain available even when a character is out of ammunition.
- Current manuscript: `game_rules.qmd` now explicitly gives every PC access to `Unarmed Attack`.

### Action-cost economy
- Status: `partially resolved`
- Manuscript: current action text does not yet clearly express any action-cost budget beyond having actions.
- Simulator: action costs are now first-class, and turns spend a real action budget; this matters because `Shriek` now costs 2 actions.
- Why it matters: without a real action-cost loop, action-cost values in the data were decorative and special moves could be spammed unrealistically.
- Current manuscript: `game_rules.qmd` now states that characters normally have two actions and that stronger actions may cost 2.
- Remaining gap: `Shriek` and other monster-only high-impact actions need manuscript-facing definitions.

### Shriek cadence
- Status: `intentional divergence`
- Manuscript: the move is not yet explicitly constrained in cadence.
- Simulator: `Shriek` now costs 2 actions, which effectively limits it to once per turn for most monsters.
- Why it matters: this solved a simulator pathology where panic monsters spammed a strong fear move twice every round.
- Why the simulator changed: a fear power should feel like a significant event, not a rote double-tap.
- Recommended direction: manuscript should decide whether `Shriek` is expensive, once-per-turn, target-limited, or otherwise cadence-limited.

### Spatial model
- Status: `resolved`
- Previous manuscript: combat text was square/grid-based and assumed direct movement and adjacency.
- Simulator: uses an area-and-connections model with line of sight, cover, darkness, and occupancy limits.
- Why it matters: the simulator is now testing a more abstract canonical model with optional future grid support.
- Why the simulator changed: to model chokepoints, exits, and room-to-room horror spaces without a full tactical grid sim.
- Current manuscript: `game_rules.qmd` now presents area-based positioning as the core combat model.

## Missing In Simulator

### Rally
- Status: `resolved`
- Manuscript currently includes `Rally`.
- Simulator now includes `Rally` as advantage on the target's next weapon attack plus critical healing.
- Design note: this now uses the simulator's real advantage/disadvantage path rather than a flat attack modifier.

### Shove / Trip
- Status: `resolved`
- Manuscript includes both.
- Simulator now models `Shove` as a one-area forced move with crit-to-prone, and `Trip` as a contested prone application.
- Design note: this is expressed in the simulator's area model rather than square-by-square movement.

### Prone
- Status: `resolved`
- Manuscript includes `Prone`.
- Simulator now has a persistent `prone` condition, grants attackers advantage against prone targets, and requires a separate `stand_up` action to recover.

### Feint
- Status: `resolved`
- Manuscript includes `Feint`.
- Simulator now models it as an opposed setup action that grants advantage on the next attack against the feinted target.

### Reaction attacks
- Status: `resolved`
- Manuscript includes reaction attacks from movement and standing.
- Simulator now models reaction attacks when leaving engagement and when standing up from prone while engaged.

### Taunt targeting penalty
- Status: `resolved`
- Manuscript gives the taunted target disadvantage on actions against combatants other than the taunter on its next turn.
- Simulator now models that behavior with condition source tracking plus real disadvantage.

### Taunt opposed roll
- Status: `resolved`
- Manuscript resolves `Taunt` against the target's Wits.
- Simulator now models `Taunt` as an opposed test instead of a flat difficulty check.

### One weapon attack per turn
- Status: `resolved`
- Manuscript limits each combat turn to a single weapon attack.
- Simulator now enforces that limit in the turn loop instead of allowing multiple attack actions in the same turn.

### Several talents
- Status: `resolved`
- Manuscript now lists only `Final Girl` and `Healing Hands`.
- Simulator currently models `Final Girl` and `Healing Hands`.

## Author Checklist For The Book

These are manuscript changes for the author to decide and apply.

1. Choose the canonical stress thresholds and update `game_rules.qmd` to match the chosen simulator/book values.
2. Decide whether `Grit` is still HP healing or has become self-stabilization / pain management.
3. If `Grit` changes, update the `Bleeding` rule to match its final interaction.
4. Add an explicit rule for ordinary monsters vs. elite/nemesis enemies at 0 HP.
5. Decide whether monsters use the stress system at all, and if not, say so explicitly.
6. Add a real resource/inventory section covering ammo, bandages, medkits, and between-scene recovery if those remain core.
7. Give every PC a fallback melee/basic attack for out-of-ammo situations, ideally as a distinct unarmed/basic attack rather than reusing stronger melee weapon attacks.
8. Decide whether the game's core spatial model is squares or areas, and make that explicit.
9. If areas are primary, frame grid play as an optional precision module.
10. Decide whether action costs are part of the real combat procedure, and if so, explain the action budget clearly.
11. Decide how `Shriek` cadence is limited if it remains a major fear move.
12. Define explicit monster durability classes beyond the ordinary-threat rule.

## Simulator Fix Plan

These are implementation tasks for the simulator, independent of manuscript edits.

### Must reconcile with the manuscript or an explicit design decision now
1. Decide whether monsters ignore stress by default and keep simulator behavior aligned to that choice.
2. Decide whether every PC should keep the universal fallback melee/basic attack now present in the simulator.
3. Decide whether action costs are part of the real combat procedure, especially for high-impact moves like `Shriek`.
4. Decide what cadence limit `Shriek` should ultimately use: high action cost, once-per-turn, target lockout, or something else.

### Next fidelity work once canon is chosen
5. Clarify the manuscript's remaining ambiguity around what further harm does to a `Stable` character before healing.
6. Add the remaining first-pass talents that materially affect combat math.
7. Add player-side stress-focused reporting so benchmark stress metrics are not diluted by monster-side zeros.

### Session and horror quality work after core rules match
8. Add longer-arc stress recovery testing between encounters or sessions.
9. Add scavenging/replenishment nodes instead of only between-scene medkit spending.
10. Add more horror-specific experiment outputs such as per-session PC death frequency, breakdown incidence, and end-of-session shroud burden.
11. Add monster-specific behavior rules beyond generic persona weighting where needed.

## Working Rule

Until a divergence is either resolved or explicitly blessed, simulator output touching that rule should be treated as provisional.
