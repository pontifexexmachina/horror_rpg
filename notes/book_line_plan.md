# Book Line Plan

This note turns the current "one book with everything in it" draft into a planned product line with clearer jobs for each book.

The goals are:

1. Separate audience needs instead of making one text teach, explain, inspire, and reference all at once.
2. Keep the rules teachable without losing exactness.
3. Make room for simulation and rules reference to share a single source of truth.
4. Use an intro scenario as a design target so the rest of the line has something concrete to support.

## Why Split The Line

The current manuscript is doing too many jobs at once. A player does not need the same text a GM needs. A GM learning how to run the game does not need the same kind of text as someone checking the exact effects of Prone or Panic in the middle of play.

Diataxis is a useful lens here even if it does not map perfectly onto RPG books.

- Tutorial: show someone how to start playing.
- How-to: show someone how to perform a task.
- Reference: provide exact rules and lookup material.
- Explanation: explain intent, principles, and design logic.

Most RPG books blend all four badly. This line should try to give each mode a home.

## Proposed Line

### 1. Player's Guide

Primary job: teach players how to make characters, understand the core procedures, and survive their first session.

Main Diataxis modes:

- Tutorial
- Reference
- A small amount of explanation

What belongs here:

- What this game is about
- What player characters do
- The tone and promises of play
- Character creation
- Player-facing core rules
- Stress, injury, combat, gear, and talents
- Examples of play from the player side
- A short "your first session" onboarding section
- Character sheet guidance

What does not belong here:

- Deep GM procedure
- Monster building
- Scenario construction
- Large bestiary content
- Edge-case-heavy rules wording if it harms readability

Success condition:

Someone can read this book, make a character, sit down at a table, and understand what choices they are expected to make.

### 2. GM's Guide

Primary job: teach the GM how to produce good Dead By Dawn sessions on purpose.

Main Diataxis modes:

- How-to
- Explanation
- Some reference

What belongs here:

- How horror works in this game
- How to run investigation and discovery
- How to pace danger, relief, and escalation
- How to use Stress as pressure instead of just punishment
- How to build locations, clues, threats, and fronts
- How to improvise within the game's intended boundaries
- How to run chases, ambushes, sieges, and downtime
- Campaign structure if the game supports campaign play
- Advice on tone, content boundaries, and table safety if desired

What does not belong here:

- Exhaustive stat blocks
- Player character options in detail
- Rules reference phrased as a legal document

Success condition:

A GM can run the intended style of horror without having to invent the game's procedures from scratch.

### 3. Bestiary

Primary job: provide ready-to-run threats and show what kinds of horror the system supports.

Main Diataxis modes:

- Reference
- How-to
- A little explanation

What belongs here:

- Monster and human antagonist stat blocks
- Special abilities
- Behavioral guidance
- Scenario hooks
- Variants and templates
- Threat categories such as slashers, infected, cultists, ghosts, cryptids, and warped humans
- Guidance on encounter use, not just raw stats

Success condition:

The GM can lift threats directly into play and understand how each one changes the texture of the scenario.

### 4. Rules Compendium

Primary job: be the exact, stable, searchable rules reference that the rest of the line points at.

Main Diataxis mode:

- Reference

What belongs here:

- Core terms
- Timing rules
- Conditions
- Action definitions
- Combat sequence
- Difficulty rules
- Skill and save definitions
- Weapon properties
- Talent wording
- Healing and death states
- Movement, adjacency, and reactions
- Cross references to related rules

Style rules:

- Short sections
- Low flavor density
- Exact wording
- Strong indexing and cross-linking
- Tables where they clarify, prose where they must

Success condition:

During play, someone can answer "what exactly happens?" in under a minute.

### 5. Intro Scenario Book

Primary job: prove the rest of the line works.

Main Diataxis modes:

- Tutorial
- How-to

What belongs here:

- One introductory scenario written for the intended experience
- GM notes on why each section exists
- Sample clues, clocks, locations, and enemy use
- Sample starting characters if helpful
- Guidance on where players are likely to get stuck
- Post-scenario notes on tuning and follow-up play

Why this matters:

The intro scenario gives the line a practical target. Instead of asking whether a rule is elegant in the abstract, we can ask whether it helps this sort of scenario sing.

Success condition:

The scenario can teach the game while also pressure-testing the system.

## Recommended Release Order

The line does not need to be built all at once.

Recommended order:

1. Player's Guide v0
2. GM's Guide v0
3. Rules Compendium v0
4. Intro Scenario v0
5. Bestiary v0

Reasoning:

- The Player's Guide and GM's Guide establish what play is.
- The Rules Compendium stabilizes the language once the core loop is clearer.
- The Intro Scenario proves the first three books are aiming at the same experience.
- The Bestiary should grow from proven scenario needs instead of being a pile of disconnected stat blocks.

An alternative order is to move the Intro Scenario ahead of the Compendium if the scenario becomes the fastest way to discover what rules actually matter. That is a valid path as long as the scenario is treated as a systems test, not just fiction.

## Diataxis Map Across The Line

This is not a rigid doctrine. It is a way to keep sections from trying to do too much.

- Player's Guide: tutorial first, reference second
- GM's Guide: how-to first, explanation second
- Bestiary: reference first, how-to second
- Rules Compendium: pure reference
- Intro Scenario Book: tutorial plus how-to

The same rule may appear in more than one place, but with different jobs.

Example:

- The Player's Guide teaches how attacking works.
- The Rules Compendium defines attack timing and exact wording.
- The GM's Guide explains what combat is for in a horror scenario.
- The Intro Scenario demonstrates how often combat should happen and under what pressure.

## Canonical Mechanics Strategy

The simulation and the Rules Compendium should not be maintained as separate truths.

The project should have three layers:

1. Structured mechanics data
2. Human-readable rules text
3. Simulation and analysis tooling

### Layer 1: Structured Mechanics Data

Put numerical and strongly procedural content in data files that are easy to diff and audit.

Suggested future directories:

- `data/core_rules.yml`
- `data/skills.yml`
- `data/actions.yml`
- `data/conditions.yml`
- `data/weapons.yml`
- `data/talents.yml`
- `data/enemies.yml`

Good candidates for structured data:

- Difficulty thresholds
- Starting HP and Defense formulas
- Stress thresholds
- Action costs
- Weapon damage and tags
- Condition names and effects
- Talent modifiers
- Enemy stat blocks

Some rules will always need prose. That is fine. The goal is not to force everything into YAML. The goal is to make the parts most likely to drift machine-readable.

### Layer 2: Human-Readable Rules Text

The Rules Compendium should be treated as canonical for exact wording.

That means:

- If a mechanic has edge-case wording, the Compendium is the source to quote.
- If a mechanic has numbers or tags, those should come from the structured data when possible.
- Player- and GM-facing books can summarize and teach the rule, but the Compendium should define it.

### Layer 3: Simulation And Analysis Tooling

The simulator should consume the same structured mechanics data used to build the Compendium tables.

That means a future workflow like this:

1. Edit data
2. Regenerate or update compendium tables/snippets
3. Run simulation
4. Review output
5. Adjust prose if behavior or wording changed

If a rule changes, the change should be visible in both the human-facing compendium and the simulator without manual copy-paste.

## Minimum Viable Data Model

This is the smallest useful mechanical schema for an early pass.

### Core Rules

- Stat names
- Check formula
- Save formula
- Difficulty values
- Advantage and Disadvantage behavior
- Critical success trigger
- Starting HP formula
- Starting Defense formula
- Starting Stress
- Panic threshold
- Breakdown threshold

### Skills

For each skill:

- Name
- Parent stat
- Short description

### Actions

For each action:

- Name
- Action cost
- Skill or save used
- Target rule
- Success effect
- Critical effect
- Range or positioning requirement

### Conditions

For each condition:

- Name
- Trigger
- Mechanical effect
- Recovery method

### Weapons

For each weapon:

- Name
- Category
- Damage die
- Tags
- Starting availability

### Talents

For each talent:

- Name
- Usage limit
- Mechanical effect
- Trigger or scope

### Enemies

For each enemy:

- Name
- HP
- Defense
- Attack bonus or skill
- Damage
- Special rules
- Threat category

## What To Simulate First

The first simulation pass should stay small and answer only the most decision-shaping questions.

Questions worth answering early:

- How often does a starting PC hit a typical enemy?
- How often does a typical enemy hit a starting PC?
- How many rounds does a 1-on-1 fight usually last?
- How deadly is a 2-on-1 fight?
- How much does Advantage change outcomes?
- How often is Push worth it?
- How quickly does Stress climb under repeated pushing?
- How strong are healing actions relative to incoming damage?
- Are some starting Talents obvious outliers?

Questions not worth overfitting too early:

- Perfect realism
- Exact long-campaign advancement curves
- Monster ecosystem balance before the first real scenario exists

## Guardrails For Simulation

Simulation is a design aid, not an oracle.

Use simulation for:

- spotting numerical outliers
- checking survival windows
- comparing action efficiency
- validating the feel of risk curves

Do not use simulation alone for:

- judging fear
- judging pacing
- judging clarity at the table
- judging whether noncombat play is satisfying

Those need scenario testing and live play.

## Anti-Drift Rules

If we build the compendium and simulator, they should obey a few hard rules.

1. No hand-copying numerical values from prose into the simulator.
2. No hand-copying mechanical tables from the simulator into the compendium.
3. If a rule is both numerical and player-facing, it should live in structured data first or be clearly marked as prose-only.
4. The Rules Compendium defines wording. Structured data defines numbers and tags.
5. Any balance discussion should cite the version of the mechanical data it used.

## Immediate Next Artifacts

The next planning and writing steps should probably be:

1. Draft a table of contents for each planned book.
2. Identify which current text belongs in which future book.
3. Define a first-pass structured data schema for core mechanics.
4. Write the intro scenario premise early so the rest of the line has a target.
5. Clean and stabilize the current one-page rules skeleton before encoding it.

## Working Heuristic

When deciding where something belongs:

- Put teaching in the Player's Guide or Intro Scenario.
- Put procedures in the GM's Guide.
- Put exact rule wording in the Rules Compendium.
- Put ready threats in the Bestiary.
- Put balance-sensitive numbers in structured data.

If a section is trying to do all of those things at once, it probably needs to be split.
