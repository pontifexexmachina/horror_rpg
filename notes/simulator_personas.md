# Simulator Personas

This note defines player and monster personas for Dead By Dawn's simulator.

The goal is not to sort real humans into rigid personality boxes. The goal is to create useful, distinct decision models that can pressure-test the game from multiple angles.

These personas build on broader player-type frameworks, especially:

- Bartle's Taxonomy
- Robin Laws' player types
- Matt Colville's discussion of different kinds of players

But the simulator should not adopt any of those taxonomies wholesale. Those frameworks describe why people enjoy play. The simulator needs models for how actors make decisions under pressure.

So the simulator should translate "player type" into a three-layer model:

1. motivation
2. preference profile
3. tactical policy

## Why A Three-Layer Model

Most player-type frameworks mix together different things:

- what a player enjoys
- what kind of spotlight they want
- how they act in tactical situations

Those are related, but they are not the same.

For simulation, we need to distinguish:

- why a player comes to the table
- what kind of scenes they prefer
- what they are likely to do in a fight

Two people may both love story, but one fights cautiously while the other makes reckless dramatic plays. Two people may both love tactics, but one values survival while the other values control and setup.

That is why the simulator should not use one-label personas alone.

## Source Frameworks

### Bartle

Bartle is useful for broad motivations:

- achievers
- explorers
- socializers
- killers

For a TTRPG, this helps describe what players are trying to get out of play, but it is too coarse to serve directly as a combat policy model.

### Robin Laws

Robin Laws is more useful for tabletop simulation because the types are closer to the rhythms of RPG play:

- power gamer
- butt-kicker
- tactician
- specialist
- method actor
- storyteller
- casual gamer

These are still not yet simulation-ready, but they are a better starting point because they imply more distinct decision tendencies.

### Matt Colville

Matt Colville's discussion is useful because it highlights that not all engaged players value the same things:

- some want to act
- some want to optimize
- some want to watch things pop off
- some want spotlight for character expression

That is useful when deciding whether the game survives contact with less optimization-heavy play.

## Translation Strategy

The simulator should convert these source frameworks into Dead By Dawn-specific personas.

Each persona should define:

- what it values
- what it fears
- what it tends to prioritize
- what thresholds it uses for risk
- what kinds of actions it favors

That makes personas usable for actual decision policies instead of just descriptive labels.

## Player Persona Model

Each player persona should eventually be represented as a policy object with at least these dimensions:

- aggression level
- survival priority
- support priority
- push willingness
- condition/control preference
- target-focus discipline
- risk tolerance at low HP
- risk tolerance at high Stress
- retreat willingness if retreat exists
- preference for dramatic or character-consistent actions over efficient ones

Not every persona needs a unique value on every axis, but this gives the simulator a stable vocabulary.

## Recommended Core Personas

These are the first player personas the simulator should support.

### 1. Power Gamer

Main roots:

- Robin Laws: Power Gamer
- Bartle: Achiever

What this persona values:

- efficient victory
- strong combos
- high leverage abilities
- numerical advantage

What this persona fears:

- wasted actions
- weak builds
- low-impact turns

Likely tactical behavior:

- uses the strongest known attack pattern
- pushes when expected value is positive
- focuses fire if it improves elimination tempo
- exploits best talents and weapons aggressively
- heals only when healing has strong expected value

Use in simulation:

- detects obvious balance outliers
- reveals dominant options quickly
- stress-tests whether one strategy crowds out others

### 2. Butt-Kicker

Main roots:

- Robin Laws: Butt-Kicker
- Bartle: Killer

What this persona values:

- hitting things
- decisive action
- visible momentum

What this persona fears:

- slow setup
- passive turns
- overcomplicated support loops

Likely tactical behavior:

- prioritizes attacks over setup or support
- pushes for damage more often than a cautious player
- prefers direct elimination to control effects
- tolerates risk if it means ending the fight sooner

Use in simulation:

- shows whether straightforward violent play is viable
- reveals whether offensive loops are too dominant or too weak
- helps tune the game's pulp-horror action floor

### 3. Tactician

Main roots:

- Robin Laws: Tactician
- DMG and Colville style "strategy-first" player

What this persona values:

- smart sequencing
- control
- focus fire
- action economy

What this persona fears:

- sloppy target choice
- unnecessary exposure
- low-discipline play

Likely tactical behavior:

- prioritizes targets that change the encounter state most
- values status effects and setup actions
- heals or supports when it preserves future efficiency
- pushes selectively, not impulsively
- makes disciplined use of reactions if modeled

Use in simulation:

- establishes a strong but explainable baseline
- shows whether control and support options actually matter
- highlights whether sequencing choices are meaningful

### 4. Method Actor

Main roots:

- Robin Laws: Method Actor
- Colville's character-expression-oriented player

What this persona values:

- acting in character
- emotional consistency
- identity-driven choices

What this persona fears:

- choices that feel out of character
- flattening the PC into pure efficiency

Likely tactical behavior:

- follows character tags or temperament rules
- may attack, retreat, or push based on persona fiction rather than expected value
- may avoid optimal actions that violate the character concept

Examples:

- a cowardly PC avoids risky pushes
- a hotheaded PC overcommits
- a caretaker PC over-heals allies

Use in simulation:

- tests whether the game remains legible under non-optimized play
- reveals whether certain builds collapse when not piloted efficiently
- helps tune the "it still works when people roleplay hard" factor

### 5. Storyteller

Main roots:

- Robin Laws: Storyteller

What this persona values:

- dramatic momentum
- tension
- meaningful reversals
- scenes that feel like horror fiction

What this persona fears:

- flat, repetitive turns
- choices that kill drama for marginal efficiency

Likely tactical behavior:

- sometimes favors escalation over safety
- may pick actions that create more tension or spotlight
- may conserve a dramatic once-per-day ability for a key moment
- may not always choose the mathematically best line

Use in simulation:

- tests whether "dramatic but not stupid" play is survivable
- reveals whether certain mechanics only work under highly optimized play
- helps judge whether the rules support horror fiction beats

### 6. Casual

Main roots:

- Robin Laws: Casual Gamer

What this persona values:

- ease
- readability
- participation without heavy optimization load

What this persona fears:

- overwhelming decision spaces
- punishing mistakes too harshly
- hidden traps in build or play

Likely tactical behavior:

- uses simple heuristics
- favors obvious attacks and obvious heals
- pushes less often unless the benefit is very visible
- underuses advanced sequencing and synergy

Use in simulation:

- tests whether the game is too punishing for low-optimization play
- reveals whether simple turns remain functional
- helps tune the floor of player competence the game assumes

## Optional Additional Personas

These may be worth adding after the core set.

### Specialist

Main roots:

- Robin Laws: Specialist

This persona repeatedly gravitates toward a preferred style or build identity. In simulation terms, this is best represented as a modifier layered on another persona.

Examples:

- melee-only specialist
- healer specialist
- control specialist
- shotgun specialist

This is probably a build-bias wrapper, not a base persona.

### Explorer

Main roots:

- Bartle: Explorer

This is probably more relevant to scenario and exploration simulation than to tactical combat. It may matter later for investigation procedures, clue networks, or risk-taking in unknown spaces.

### Socializer

Main roots:

- Bartle: Socializer

This is also likely more relevant to scenario-level simulation than combat. It may later inform negotiation or party-cohesion assumptions, but is not a strong tactical-combat identity on its own.

## Recommended Core Monster Personas

Monsters also need policies, not just stats.

The first wave of monster personas should be role-oriented rather than psychology-oriented.

### Brute

Values:

- direct damage
- nearest vulnerable target
- staying engaged

Likely behavior:

- closes distance
- attacks directly
- rarely uses subtle setup

### Stalker

Values:

- isolation
- wounded prey
- pressure through threat and positioning

Likely behavior:

- prefers separated or weakened targets
- may disengage and re-engage if the rules support that
- punishes panic or exposure

### Harrier

Values:

- mobility
- attrition
- forcing wasted actions

Likely behavior:

- avoids slugging matches
- applies pressure over time
- prefers vulnerable backline or support targets

### Controller

Values:

- conditions
- disruption
- restricting player options

Likely behavior:

- uses status effects early
- tries to reduce party efficiency rather than maximize raw damage

### Panic Engine

Values:

- stress generation
- fear effects
- collapsing player action economy

Likely behavior:

- prioritizes actions that raise Stress or trigger panic consequences
- may finish less often if escalating panic is more effective

### Finisher

Values:

- downed or weakened targets
- conversions from Wounded to Critical or death

Likely behavior:

- focuses low-HP characters
- prioritizes secure eliminations over spreading damage

## Persona Composition

Not every simulated actor needs a single monolithic persona.

A cleaner approach is:

- base persona
- optional modifiers

Possible modifiers:

- `Cowardly`
- `Hotheaded`
- `Caretaker`
- `Showoff`
- `BloodiedPanic`
- `LowStressConfidence`
- `WeaponSpecialist`

This lets the simulator represent "Tactician + Cowardly" or "Butt-Kicker + Hotheaded" without multiplying the number of core personas too quickly.

## How Personas Should Interact With Data

Personas should not hardcode every game concept by name if that can be avoided.

Better:

- actions expose tags such as `attack`, `heal`, `control`, `stress`, `aoe`, `setup`, `finisher`
- personas score legal actions partly by these tags
- rules data defines the action tags

That keeps personas reusable even when the action list changes.

For example:

- the Butt-Kicker heavily prefers `attack` and `finisher`
- the Tactician values `control`, `setup`, and high expected damage
- the Panic Engine values `stress`
- the Casual persona prefers simple high-clarity actions

## What Personas Should Help Us Learn

The persona suite should help answer questions such as:

- does the game only work when piloted by a Power Gamer?
- are support actions only attractive to the Tactician?
- does the Casual player collapse too easily?
- can the Method Actor still contribute meaningfully?
- do Panic-focused monsters only prey on weak personas, or do they change everyone's behavior?
- are some talents only strong for one persona and dead for others?

These are better balance questions for a TTRPG than "what is the single strongest policy?"

## Recommended Initial Persona Set For v0

If we want a small but high-value first set, use:

- Power Gamer
- Butt-Kicker
- Tactician
- Method Actor
- Casual

And monster roles:

- Brute
- Controller
- Panic Engine
- Finisher

That is enough variety to surface a surprising amount of design information without exploding implementation cost.

## Working Heuristic

When adding a persona, ask:

- does it reveal a new kind of design failure?
- does it make meaningfully different choices from existing personas?
- can its logic be explained in plain language?
- would a real player plausibly behave this way?

If the answer is no, it probably does not need to be a separate persona yet.
