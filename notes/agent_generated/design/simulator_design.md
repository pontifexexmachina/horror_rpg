# Simulator Design

This note treats the simulator as first-class design infrastructure for Dead By Dawn.

The goal is not to build a novelty tool after the game is "done." The goal is to design the game so that simulation is a normal part of rules development, balance work, and monster generation from the start.

This note builds on [book_line_plan.md](C:\\projects\\horror_rpg\\notes\\agent_generated\\design\\book_line_plan.md), especially the idea that the Rules Compendium and the simulator should share a canonical mechanical layer.

## Why The Simulator Comes First

As a solo developer, I cannot rely on large-scale live playtesting to surface every numerical problem, action-economy distortion, or monster outlier.

I can, however:

- run thousands of combat trials
- compare multiple player personas
- test many small rule changes quickly
- pressure-test monster designs before putting them in front of humans
- discover whether a mechanic is stable, swingy, dominant, or dead on arrival

That means the game should be designed to work well with a simulation-first workflow.

This is not a replacement for live testing. It is a force multiplier for a developer who has strong programming skills and limited table bandwidth.

## Research Directions That Inform This

Several existing projects point toward a useful approach.

### RLCard

RLCard is useful less because this project needs reinforcement learning immediately, and more because it demonstrates a clean environment contract.

The important ideas to borrow are:

- a game environment exposes state, legal actions, transitions, payoffs, and reproducible runs
- many different agents can plug into the same environment
- rule-based agents are useful baselines, not just placeholders
- experiments should be easy to run repeatedly across seeds and matchups

Reference:

- [RLCard](https://rlcard.org/)

### AlphaZero-General

AlphaZero-General is useful mainly as an architectural example.

The ideas worth borrowing are:

- separate game rules from search or agent logic
- separate self-play or experiment orchestration from the core engine
- keep evaluation harnesses distinct from the rules layer
- make it possible to swap in better decision-making later without rewriting the game model

The key thing not to borrow too early is the assumption that the project needs neural network training from the start.

Reference:

- [alpha-zero-general](https://github.com/suragnair/alpha-zero-general)

### OpenSpiel

OpenSpiel is the strongest conceptual fit for the simulator architecture.

The useful idea is to model play as an extensive-form game with:

- explicit states
- legal actions
- chance events
- state transitions
- rewards or outcomes

That model fits turn-based combat well and can later grow into broader encounter and scenario simulation if the rules are designed cleanly enough.

References:

- [OpenSpiel introduction](https://openspiel.readthedocs.io/en/stable/intro.html)
- [OpenSpiel repository](https://github.com/google-deepmind/open_spiel)

### Monte Carlo And Automated Playtesting Work

The broader automated playtesting and Monte Carlo literature reinforces two points:

1. simulation is useful for evaluating distributions, not just averages
2. simulated agents should represent multiple playstyles, not a single notion of "correct" play

That strongly suggests that this simulator should model personas such as cautious, reckless, support-oriented, and pressure-sensitive players rather than only optimizing for a perfect agent.

References:

- [A Monte Carlo Approach to Skill-Based Automated Playtesting](https://pmc.ncbi.nlm.nih.gov/articles/PMC6319931/)
- [A visual probability analysis tool for board game designers](https://www.sciencedirect.com/science/article/pii/S2666389921000805)

## Design Principle: Simulable By Construction

The game should be designed so that important mechanics can be simulated directly, not reconstructed by interpretive glue code.

That means Dead By Dawn should prefer:

- finite legal actions over open-ended action menus in the parts of the game we want to simulate
- explicit timing windows
- explicit condition effects
- explicit stochastic procedures
- explicit resource changes
- explicit target selection rules
- explicit end conditions

This does not mean the entire RPG must be reduced to formal machine logic. It means the mechanically important parts should be.

## Scope Of Simulator v0

Simulator v0 should focus on the smallest slice that pays immediate design dividends.

That slice is:

- tactical combat
- stress accumulation during combat
- healing and attrition inside combat
- monster lethality and durability
- action efficiency
- talent outliers

Simulator v0 should not try to model:

- investigation scenes
- clue interpretation
- social improvisation
- full scenario structure
- campaign progression
- horror pacing in the dramatic sense

Those belong to later layers, scenario analysis, or live testing.

## Core Questions Simulator v0 Must Answer

The simulator should make it easy to ask and answer questions like these:

- How often does a starting PC hit a typical enemy?
- How often does a typical enemy hit a starting PC?
- How many rounds does a typical fight last?
- How often do PCs go Wounded, Critical, or die?
- How much does Advantage move outcomes?
- How much value does Push create?
- How quickly does Stress rise in different fight lengths?
- How often does Panic matter in a typical combat?
- Is First Aid stronger than offense at key points?
- Is Grit too efficient or too weak?
- Which starting Talents are obvious power outliers?
- Which monster roles are too oppressive or too soft?

If the simulator architecture does not make these questions easy to ask, it is the wrong architecture.

## What The Simulator Should Optimize For

The simulator is a design laboratory, not a game client.

It should optimize for:

- clarity
- reproducibility
- fast iteration
- explainability
- low-friction batch experiments
- versioned outputs

It should not optimize first for:

- beautiful UI
- real-time visualization
- generic AI benchmarking prestige
- machine learning novelty

## Recommended Architecture

The simulator should be built as an environment plus pluggable agents plus an experiment harness.

### 1. Rules Layer

This is the deterministic mechanical core plus controlled randomness.

Responsibilities:

- define the sequence of play
- validate legal actions
- resolve dice and modifiers
- apply damage, healing, movement, and conditions
- apply stress changes and panic state
- check death and encounter end conditions

Suggested conceptual modules:

- `rules/engine`
- `rules/actions`
- `rules/conditions`
- `rules/dice`
- `rules/end_conditions`

### 2. State Layer

This is the authoritative model of the encounter at a point in time.

Responsibilities:

- actor stats
- HP and Stress
- conditions
- initiative or turn order
- positioning abstraction
- action economy state
- reaction availability
- weapon/equipment state if relevant
- team membership
- encounter metadata

Suggested conceptual modules:

- `sim/state`
- `sim/actor_state`
- `sim/encounter_state`

### 3. Action Generation Layer

This layer turns the current state into a finite list of legal actions for the acting unit.

Responsibilities:

- enumerate legal actions
- attach targets and action parameters
- hide impossible options
- expose information agents can use to choose

This is important because it forces the game to be explicit about what an actor can actually do at a given moment.

Suggested conceptual modules:

- `sim/legal_actions`

### 4. Agent Policy Layer

This layer decides what an actor tries to do.

Responsibilities:

- choose from legal actions
- embody a playstyle or monster behavior
- work with transparent heuristics in v0

Initial agent types should include:

- `RandomAgent`
- `AggressiveAgent`
- `CautiousAgent`
- `SupportAgent`
- `PusherAgent`
- `MonsterRoleAgent`

These should be hand-authored policies first, not learned models.

Suggested conceptual modules:

- `agents/base`
- `agents/player_personas`
- `agents/monster_personas`

### 5. Encounter Runner

This layer runs one full encounter from setup to resolution.

Responsibilities:

- initialize state from a scenario spec
- step turns and rounds
- collect event logs
- stop when an end condition is met
- return outcome summaries

Suggested conceptual modules:

- `sim/runner`

### 6. Experiment Harness

This layer runs many encounters and summarizes results.

Responsibilities:

- run batches across seeds
- compare rules versions or matchup sets
- aggregate metrics
- write reproducible reports

Suggested conceptual modules:

- `experiments/batch_runner`
- `experiments/reporting`

## Borrowed Architectural Pattern

The right pattern to borrow from RLCard and AlphaZero-style systems is:

- an environment-like rules model
- pluggable agents
- a repeatable experiment harness
- optional future search and learning layers

The wrong pattern to borrow for v0 is:

- training-heavy pipelines
- neural network dependence
- a requirement for perfect-information optimization
- giant compute assumptions

In other words: borrow the shape, not the hype.

## Why Rule-Based Agents First

The first simulator should not start with reinforcement learning or AlphaZero-style self-play.

Reasons:

- the rules are still changing rapidly
- the action space is still immature
- learned agents can hide design problems behind policy artifacts
- rule-based agents are easier to debug
- rule-based agents are easier to explain
- personas are more useful than superhuman play at this stage

The first simulator should help answer "what happens if a frightened but competent player does this?" not "what is the optimal policy in a frozen game?"

## Personas Instead Of Perfect Play

The simulator should be able to run the same encounter under multiple player personas.

Example personas:

- cautious survivor
- reckless attacker
- opportunistic pusher
- support specialist
- conservative healer
- panic-averse character

These matter because balance in an RPG is not just about optimal play. A horror game especially should remain legible under imperfect choices, desperation, and stress.

That means each persona should be represented as a policy over legal actions and thresholds such as:

- when to Push
- when to heal
- when to focus fire
- when to risk a status action
- when to avoid reactions
- when to retreat if the rules later support it

## Monster Simulation And Generation

The simulator should eventually support monster generation as a structured design problem.

The best way to make that possible is to define monsters as combinations of:

- core stat profile
- durability profile
- attack profile
- tags
- special abilities
- behavior policy
- role

Possible roles might include:

- brute
- stalker
- harrier
- controller
- attrition threat
- panic engine
- finisher

The simulator can then test whether monsters in a role actually behave like that role claims.

Over time, monster generation could become:

1. choose a role
2. choose a budget or threat tier
3. assemble stats and abilities within constraints
4. simulate against benchmark parties
5. reject or revise outliers

That is much more promising than trying to balance monsters only by intuition.

## Required Game Design Constraints

If the game is meant to be simulation-friendly, some design habits should be encouraged and others discouraged.

Encourage:

- explicit action costs
- explicit targeting rules
- explicit success and critical effects
- standardized condition format
- explicit turn and reaction timing
- keyworded weapon tags
- keyworded monster abilities
- finite and inspectable resource changes

Discourage:

- vague "the GM decides the mechanical effect" rules in combat-critical procedures
- effects that depend on undefined fictional weighting
- action options that cannot be enumerated
- hidden balance assumptions not represented in data

This does not outlaw GM judgment. It just means balance-critical procedures should not depend on unstructured judgment if we want them to simulate well.

## Data Model Implications

The simulator architecture implies a specific style of mechanical data.

The data model should support:

- core resolution rules
- actor templates
- skills and stats
- actions as structured objects
- conditions as structured objects
- weapons with tags
- talents with triggers and modifications
- monsters with role and policy metadata
- encounter setup definitions

This suggests the schema should be derived from:

1. what the rules engine must resolve
2. what legal action generation must enumerate
3. what policies must inspect
4. what experiments must report

Not from "what seems tidy in YAML."

## Positioning Model For v0

Full grid tactics are probably unnecessary for the first simulator unless the game depends heavily on exact geometry.

The recommended first abstraction is a coarse tactical model with concepts such as:

- engaged
- near
- far
- adjacent-enemy count
- threatened or not threatened

If grid detail later matters, the model can grow. But a coarse model will be faster to implement, easier to analyze, and more robust during early rule churn.

## Logging And Explainability

The simulator should produce outputs that help design decisions, not just win rates.

Useful outputs include:

- win/loss rate
- average rounds to resolution
- KO, Wounded, Critical, and death rates
- average stress gained
- push frequency
- damage dealt per action
- healing per action
- condition uptime
- action-choice frequency by persona

Useful drill-down outputs include:

- representative encounter logs
- percentile distributions, not just means
- side-by-side comparisons between rules versions
- reasons a policy preferred one action over another

The simulator should help answer "why did this happen?" not only "what happened?"

## Versioning And Reproducibility

Each experiment should be tied to:

- a rules data version
- a simulator code version
- the scenario spec used
- the agent set used
- the random seed policy used

This matters because balancing discussions become much less useful if the underlying mechanical assumptions are not pinned.

## What Not To Build Yet

Simulator v0 should not include:

- reinforcement learning training loops
- neural network evaluation
- full scenario simulation
- freeform fiction parsing
- GM improvisation models
- exhaustive content generation systems
- generalized dungeon exploration AI

Those may become useful later. They are not the highest-leverage first move.

## Future Growth Path

If the architecture stays clean, later versions could add:

- search-based agents such as MCTS
- learned policies trained against benchmark scenarios
- scenario-level simulation beyond combat
- map-aware tactical models
- procedural monster generation with automated rejection tests
- campaign-level attrition simulation

The important thing is that none of those should require rewriting the core environment contract.

## Immediate Next Design Tasks

Now that the simulator is treated as primary infrastructure, the next tasks should be:

1. Define the environment contract for a single encounter.
2. Define the benchmark questions Simulator v0 must answer.
3. Define the first set of player and monster personas.
4. Define the structured action model the engine will resolve.
5. Define the first-pass data schema from those needs.

## Working Heuristic

When designing a mechanic, ask:

- can the engine represent this state?
- can legal actions enumerate this choice?
- can a persona make a meaningful decision about it?
- can the simulator report whether it is strong, weak, or swingy?

If the answer is no, either the simulator model is missing something important or the mechanic is too vague to support the simulation-first workflow this project wants.
