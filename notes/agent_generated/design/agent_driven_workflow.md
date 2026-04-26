# Agent-Driven Workflow

This note defines how Dead By Dawn should operate now that agents are allowed to drive more of the project, with the author acting as creative director.

The goal is not to remove authorial taste. The goal is to let agents do the heavy drafting, mechanical reconciliation, simulation, and book-production work while the author spends attention on direction, vetoes, and high-value design calls.

## Working Roles

### Author

The author owns:

- taste
- tone
- final canon decisions
- major premise and setting direction
- veto power over rules, prose, and product structure
- deciding when something feels like the intended game

The author should mostly be asked for decisions when a change affects the identity of the game, not every time a paragraph needs cleaning up.

### Agent

Agents own:

- turning notes into draft-ready rules text
- reconciling manuscript text with simulator behavior
- maintaining design notes under `notes/agent_generated/`
- extending structured mechanics data
- running tests, validation, and benchmarks
- surfacing contradictions and open decisions
- keeping the Quarto book renderable

Agents should act like a lead designer/developer: proactive, conservative with canon, and explicit when making a provisional choice.

## Canon Layers

Dead By Dawn should use four layers of truth.

### 1. Structured Mechanics Data

Location: `data/`

Use this for numbers, tags, action costs, actor templates, weapon stats, conditions, talents, resources, scenarios, benchmark suites, and session plans.

If a rule is numerical, repeated, or simulator-relevant, prefer encoding it here before hand-copying it into prose.

### 2. Simulator

Location: `src/dead_by_dawn_sim/`

Use this to test tactical combat, resource attrition, session carry-forward, monster roles, party roles, and contribution patterns.

The simulator is a design instrument, not an oracle. A result can reveal a problem without dictating the solution.

### 3. Manuscript

Primary files:

- `index.qmd`
- `game_rules.qmd`
- `appendix_n.qmd`

Use this for human-facing rules, teaching order, play procedures, examples, tone, and book structure.

The manuscript should not drift far from the data and simulator unless the divergence is intentional and logged.

### 4. Design Notes

Location: `notes/agent_generated/`

Use this for research summaries, design arguments, migration plans, benchmark interpretations, and unresolved decisions.

Root `notes/` remains author-owned except for `README.md` and `AGENTS.md`.

## Default Production Loop

For any meaningful rules change, agents should prefer this loop:

1. Identify the design target.
2. Check current manuscript, data, simulator behavior, and drift notes.
3. Make the smallest coherent canon choice, or mark the choice as provisional.
4. Update structured data if the rule has mechanical content.
5. Update simulator behavior if needed.
6. Update manuscript prose.
7. Run validation and tests.
8. Run a relevant benchmark when balance or pacing might change.
9. Record unresolved drift or decision points.

## Provisional Decisions

Agents may make provisional decisions when:

- the existing notes strongly imply a direction
- the choice is reversible
- the change keeps the project moving
- the decision is clearly marked for author review

Agents should not silently settle identity-level questions such as:

- whether the core game is grid-first or area-first
- whether the game is one book or a product line
- whether a major resource becomes central or optional
- whether the default tone becomes supernatural, mundane slasher, cosmic, or mixed

## Current Working Direction

The current working direction is:

- survival horror rather than balanced tactical skirmish
- costly success rather than frequent encounter loss
- fiction-first resources rather than abstract metacurrency
- area-based horror spaces, with possible optional grid translation later
- simulator-backed combat and session attrition
- structured mechanics data as the source for numbers and repeated mechanical definitions
- manuscript prose that teaches play first and refines exact reference wording over time

## First Milestone

The first agent-driven milestone is:

**Dead By Dawn v0.2: Playable Survival-Horror Core**

Targets:

- rewrite the current rules skeleton into a clearer playable draft
- reconcile the book with simulator-backed resources such as ammo and bandages
- name unresolved simulator/manuscript drift instead of hiding it
- keep tests passing
- use benchmark results to choose the next design pass

## Working Heuristic

When in doubt, agents should ask:

- Does this make the game easier to play?
- Does this make the horror loop sharper?
- Does this reduce drift between data, simulator, and book?
- Does this preserve room for the author to make taste calls?

If the answer is yes, move the project forward and record what still needs judgment.
