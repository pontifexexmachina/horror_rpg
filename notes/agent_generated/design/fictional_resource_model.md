# Fictional Resource Model

This note defines the kind of resource economy Dead By Dawn should use if it wants to support survival horror pressure without sliding into dissociated mechanics or opaque metacurrency budgeting.

It is a design note for both the game text and the simulator.

## Core Principle

Whenever possible, Dead By Dawn should prefer resources that are visible, carryable, lootable, exhaustible, and fictionally legible.

A good Dead By Dawn resource is something the characters can understand and make decisions about inside the fiction.

Examples:

- bullets
- shells
- batteries
- fuel
- bandages
- medkits
- ritual components
- salt
- holy water
- keys
- lockpicks
- time
- noise
- safe shelter

A weaker Dead By Dawn resource is something the player must budget but the character cannot meaningfully perceive.

Examples:

- once per encounter powers with no in-world explanation
- spendable clue points
- generic effort pools with hidden scenario-length assumptions
- recovery that happens because a scene ended rather than because anything changed in the fiction

## What We Are Trying To Avoid

Two Alexandrian ideas matter here.

### 1. Dissociated Mechanics

A mechanic becomes dissociated when the player's decision cannot be directly equated to the character's decision in the world.

That does not mean all abstraction is bad. It does mean the game should be suspicious of limits or expenditures that have no clear fictional referent.

### 2. Hidden Hard Limits

A game becomes frustrating when the players are forced to ration a limited resource without knowing:

- how long the scenario is
- what the future demands will be
- whether the game expects them to spend now or hoard
- what they are even really buying

That is the GUMSHOE failure mode this project should avoid.

Dead By Dawn should create pressure through visible costs, not through secret budgeting games.

## Resident Evil As A Structural Model

The intended loop should look more like survival horror video games than like pool-management investigation games.

A rough loop:

1. Enter a dangerous place.
2. Spend resources to survive, progress, or learn.
3. Scavenge and explore to refill some of those resources.
4. Decide whether to push deeper, detour, or retreat.
5. Reach a climax in a degraded but not hopeless state.

The point is not that the party should usually lose fights.

The point is that the party should usually survive while becoming thinner, shakier, louder, bloodier, and more desperate.

## Encounter Success Model

The party should win the vast majority of encounters.

That is not a contradiction with survival horror.

If the party loses encounters too often, session-level compounding will drown the game in failure states and make the larger resource model irrelevant.

The intended pattern is:

- most encounters are survived
- many encounters cost meaningful resources
- some encounters create acute spikes of danger
- the climax cashes out prior attrition
- catastrophe is possible, but not routine

So Dead By Dawn should optimize for costly success, not for evenly matched one-fight fairness.

## Resource Taxonomy

Dead By Dawn should think in terms of fictional resource classes.

### 1. Survival Resources

These are the resources that most directly determine whether the party can keep moving.

Suggested category:

- HP or wounds
- stress
- shrouds or equivalent death-track burden
- ammunition
- medical supplies
- light or power

These should be central to the session simulator.

### 2. Utility Resources

These let the party solve problems more cleanly or safely.

Suggested category:

- keys
- lockpicks
- ritual tools
- fuel
- barricade materials
- throwable weapons
- maps
- radios
- cameras or recorders

These are not always life-or-death in the moment, but they strongly affect route quality, safety, and scenario shape.

### 3. Positional Resources

These are not inventory items, but they are still fictionally real and strategically important.

Suggested category:

- time before a threat escalates
- secrecy or noise discipline
- control of exits
- knowledge of routes
- access to safe rooms
- control of chokepoints

These are excellent survival horror resources because they are associated and scenario-relevant without becoming pure abstractions.

### 4. Recovery Resources

These are what allow the party to turn attrition into survivable pacing instead of a slow death march.

Suggested category:

- found supplies
- secure rooms
- uninterrupted time
- helpful NPC shelter
- vehicles
- infirmaries, chapels, workshops, or supply caches

These should be embedded in scenario design rather than handed out as invisible resets.

## Hard Limits vs Soft Limits

The game should distinguish between hard limits and soft limits deliberately.

### Good Hard Limits

Hard limits are acceptable when they are visible and fictionally grounded.

Examples:

- the shotgun has 4 shells left
- the medkit has 2 charges left
- the flashlight battery is dying
- the ritual circle needs one more candle to work
- dawn arrives in 20 minutes

These are not hidden. They are part of play.

### Dangerous Hard Limits

Hard limits become a problem when they are hidden or structurally opaque.

Examples:

- you only get 3 great heals per scenario
- this pool does not refresh until the GM decides the chapter is over
- the game secretly assumes 5 checks of this type per adventure

Dead By Dawn should avoid these unless the fiction makes them obvious and the scenario design supports informed choice.

### Preferred Soft Limits

Soft limits are often better for the game because they support pressure without dictating a single scenario shape.

Examples:

- HP can be restored, but only with scarce supplies
- stress can come down, but only in actual moments of safety
- ammo can be replenished, but only if the party takes risks to scavenge
- healing is possible, but every bandage spent now is a bandage not available later

This is probably the best general pattern for the game.

## Preferred Resource Expressions

When a mechanic needs rationing, the first design question should be:

What is the character actually spending?

Good answers:

- ammo
- charge
- dose
- battery
- fuel
- bandage
- herb
- time
- secrecy
- stamina expressed through stress, breath, exhaustion, or pain

Bad answers:

- encounter use
- scene use
- pool point
- generic metacurrency

That does not mean scene structure can never matter. It means scene structure should not be the primary explanation for why a resource exists.

## Healing Model Guidance

Healing is the biggest pressure-release valve in the current simulator, so it deserves explicit guidance.

Dead By Dawn should probably split healing into three modes.

### 1. Immediate First Aid

This is in-the-moment stabilization.

It should:

- require supplies
- be usable under pressure
- help keep someone moving
- not fully erase the consequences of getting hurt

Possible fiction:

- bandages
- tourniquets
- painkillers
- improvised splints

### 2. Field Recovery

This is slightly slower recovery during a lull.

It should:

- require time and relative safety
- likely consume better supplies
- improve short-term survivability
- still leave meaningful injury hanging around

Possible fiction:

- medkit treatment
- stitching
- setting a limb
- antiseptic and rest

### 3. Deep Recovery

This is what takes a badly hurt character back toward normal.

It should:

- require real shelter
- require hours or days, not a quick action
- usually sit outside the core session loop

This prevents every wound from becoming an easily erased tempo tax.

## Stress Model Guidance

Stress is already a good candidate for an associated resource because characters understand fear, panic, and cracking under pressure.

Stress should remain fictionally grounded.

That means:

- stress should be caused by recognizable events
- reducing stress should require recognizable relief, comfort, ritual, reassurance, drugs, rest, or regained control
- panic should change what the character can actually do in the fiction
- breakdown should feel like collapse, not just a silent numerical threshold

The simulator should eventually treat stress as a carry-forward session resource, not just an encounter decoration.

## Ammo And Consumables

Ammunition and consumables are likely the cleanest balancing tools for this game.

Why they work:

- players understand them immediately
- characters understand them immediately
- they fit survival horror fiction perfectly
- they support exploration and scavenging loops naturally
- they can be replenished in scenario-specific ways

The game should strongly consider making offensive consistency depend on ammunition quality and quantity rather than only on abstract action economy.

That gives the designer many good knobs:

- scarcity
- weapon identity
- stash placement
- risk-reward detours
- noisy but efficient options versus quiet but weak options

## Exploration As Replenishment

Replenishment should come from the world whenever possible.

That means the scenario should include things like:

- medicine cabinets
- police lockers
- hunting sheds
- gas cans
- ritual supply closets
- hidden caches
- survivor stashes
- locked rooms with useful inventory inside

This is important because it keeps the resource game associated.

The party is not refreshing because an encounter ended.

The party is refreshing because they found a place, a tool, or a moment of safety.

## Inventory Pressure

Inventory should probably matter, because inventory creates real choices without becoming a metacurrency puzzle.

Good inventory pressure asks:

- do we carry extra ammo or extra healing?
- do we bring ritual tools or barricade tools?
- do we keep the key item or discard it after use?
- do we carry the heavy weapon or move faster?

That is a more satisfying survival horror economy than invisible pool management.

The simulator does not need full inventory Tetris at first, but it should eventually model:

- quantity-limited consumables
- coarse carry capacity
- stash locations or safe storage if the game wants that loop

## Safe Rooms And Recovery Windows

The game should strongly consider explicit safe rooms or equivalent shelters.

These are useful because they create associated recovery windows.

A safe room can justify:

- stress reduction
- limited field treatment
- inventory swaps
- weapon reload or maintenance
- planning
- save/checkpoint structure if desired in tone

The key is that recovery happens because the characters found refuge, not because the designer wanted a pacing reset.

## Design Rules For Abilities

When writing talents, class features, or special moves, prefer these questions in order:

1. Does it change what the character can do in the fiction?
2. If it is limited, what fictional thing limits it?
3. Can the player understand the limit the same way the character does?
4. Can the simulator model that limit as an actual resource or state change?

Good examples:

- expend one shell to use a stopping-power shot
- consume a stimulant to ignore panic penalties briefly
- spend a warding charm to negate one supernatural effect
- use a bandage to stabilize a Wounded ally

Weak examples:

- once per encounter, do something dramatic
- spend 2 tension points to gain advantage
- after every scene, regain your nerve move

## Simulator Implications

The simulator should grow toward this resource model.

### Encounter Layer

The encounter simulator should still answer tactical questions.

But it should no longer be the main balancing target by itself.

### Session Layer

The session simulator should eventually carry forward:

- HP
- stress
- shrouds
- ammo
- medical supplies
- light or power
- key consumables
- safe-room usage
- time pressure

### Scenario Layer

Longer term, scenario models should include replenishment nodes and optional detours.

The important question becomes:

How much can the party recover if they take the risk to search for help?

That is much closer to the intended game than a fresh-party benchmark loop.

## Initial Resource Proposal For Dead By Dawn

If the game needed a first working resource model right now, a good candidate would be:

- HP
- stress
- shrouds
- ammo by weapon type
- bandages or medkit charges
- light source charge
- ritual components for occult tools
- time pressure clock

That is enough to create meaningful survival horror economics without exploding complexity on day one.

## Resource Design Heuristic

Before adding any new limited mechanic, ask:

- what is being spent?
- can the character perceive that expenditure?
- can the world replenish it?
- can the GM place it in the environment?
- does it create exploration decisions?
- does it create meaningful pressure without becoming a hidden hard limit?

If the answer to most of those is no, the mechanic is probably drifting toward the wrong kind of game.

## Working Conclusion

Dead By Dawn should create pressure through fiction-first attrition.

The party should usually survive encounters.
The session should still feel dangerous because survival costs something real.
That cost should usually be expressed through inventory, injury, stress, time, exposure, and access to safety.

This supports:

- a survival horror loop
- associated decision-making
- exploration-driven replenishment
- scenario flexibility
- simulator-friendly resource modeling

It also helps avoid the metacurrency and hidden-hard-limit problems that make some investigation-forward games feel frustrating rather than tense.
