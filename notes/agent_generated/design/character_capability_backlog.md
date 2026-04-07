# Character Capability Backlog

This note captures the current assessment of what the simulator can and cannot express about player characters, plus a prioritized backlog of capabilities that would unlock richer character support later.

The framing here is deliberate:

- first, identify which character fantasies are already supported, partially supported, or unsupported
- second, identify the simulator and rules capabilities that would unlock the most new character types
- third, postpone chargen procedures and presentation until the underlying game can actually express the kinds of characters we want

## Current Read

The simulator currently supports combat roles much better than horror character archetypes.

Its strongest current space is:

- melee bruisers
- ranged survivors
- medics
- panic or fear specialists

Its weakest current space is:

- exploration identities
- preparation-driven identities
- protection or bodyguard identities
- stealth identities
- resource-management identities
- true occult specialization

In other words: it is already pretty good at "what do you do on your turn in a fight?" and much weaker at "what kind of horror protagonist are you over the course of a night?"

## Character Type Matrix

### Supported Now

#### Bruiser / melee heavy

Why this works now:

- strong Might / Brawl / Brawn templates already exist
- melee weapon support exists
- shove and trip already create some space-control identity
- basic survivability hooks already exist

Current supporting pieces:

- `bruiser`
- `brawl_attack`
- `shove`
- `trip`

#### Ranged survivor / action hero generalist

Why this works now:

- pistols and ranged attacks are modeled
- ammo is tracked
- speed-based defense and mobility matter
- panic and death-track pressure already create a "stay alive and keep shooting" loop

Current supporting pieces:

- `survivor`
- `attack`
- `pistol`

#### Combat medic

Why this works now:

- first aid exists
- bandage consumption is modeled
- medkits exist as a tracked resource
- rally provides a lightweight support identity
- `healing_hands` gives a clear talent-based upgrade

Current supporting pieces:

- `medic`
- `first_aid`
- `rally`
- `healing_hands`

#### Panic / fear specialist

Why this works now:

- stress attacks exist
- panic and breakdown thresholds exist
- the simulator can already model fear-based pressure changing action economy

Current supporting pieces:

- `shriek`
- stress thresholds in core rules
- `panic_engine` persona

### Partially Supported

#### Tactician / battlefield controller

What exists:

- taunt
- trip
- shove
- some position and setup play

What is missing:

- chokepoint control
- guard or intercept mechanics
- trap or barricade play
- richer terrain exploitation
- more varied control effects

#### Occultist

What exists:

- a template named `occultist`
- `shriek`
- some Wits-heavy identity

What is missing:

- ritual components
- warding
- banishment
- supernatural countermeasures
- preparation-dependent occult play
- scenario-specific anti-monster tools

Right now this is mostly "person with pistol plus panic move," not a real occult subsystem.

#### Leader / morale anchor

What exists:

- `rally`

What is missing:

- stronger ally coordination
- panic recovery support
- command identity
- teamwide synergy hooks

#### Final girl / last-stand survivor

What exists:

- `final_girl`

What is missing:

- mechanics that reward being isolated, bloodied, hunted, or near collapse
- broader last-stand identity beyond a single rescue passive

#### Resource-thrifty scavenger

What exists:

- ammo
- bandages
- medkits

What is missing:

- scavenging procedures
- inventory slot pressure
- loot economy
- carrying or caching choices
- supply-efficiency traits

#### Weapon specialist

What exists:

- melee versus pistol distinction

What is missing:

- enough weapon diversity for multiple specialist identities
- quiet versus loud tradeoffs
- range identity beyond "bat" or "pistol"

### Unsupported

#### Stealth / infiltration specialist

Missing:

- hidden state
- stealth actions
- noise model
- ambush procedures

#### Scout / explorer

Missing:

- search
- clue or route utility
- exploration-facing actions
- map-pressure advantages for perceptive or mobile characters

#### Engineer / barricade / trap maker

Missing:

- deployables
- environmental control
- barricade actions
- trap creation or trap use

#### Protector / tank / bodyguard

Missing:

- intercept attacks
- guard ally
- damage redirection
- dragging or shielding wounded allies

#### Coward / evasive survivor

Missing:

- retreat-specialist mechanics
- hiding or evasion tools
- a build identity focused on survival rather than throughput

#### Doomed but functional flawed character

Missing:

- explicit trait or flaw layer
- controllable drawbacks that create identity without producing trap characters

#### Prepared anti-supernatural specialist

Missing:

- ritual inventory
- warding tools
- banes and counters
- enemy-type interaction hooks

#### Light-bearing / darkness-management specialist

Missing:

- light as a player resource
- carried-light decisions
- darkness-mitigation tools

#### Social manipulator / face

Missing:

- broader social procedures
- calming, deception, extraction, distraction, negotiation

`Chat` currently matters mostly as a combat-facing support or control stat.

## Major Capability Gaps

These are the broad missing capabilities revealed by the matrix.

### 1. No composable PC build layer

Right now a character is mostly a fixed template.

Missing:

- modular assembly
- selectable packages
- configurable stat or skill allocation
- build-level tradeoffs

### 2. Talents are too thin

Only a very small number of simple passives exist.

Missing:

- enough perks to create expressive or optimizer-facing build identity
- talents tied to survival, preparation, leadership, stealth, protection, scavenging, and occult play

### 3. The action vocabulary is still mostly combat-turn verbs

The simulator is much better at:

- attack
- heal
- buff
- control
- move

Than it is at:

- search
- hide
- ward
- barricade
- guard
- rescue
- scavenge
- calm

### 4. Resource identity is incomplete

The current model has:

- HP
- stress
- shrouds
- ammo
- bandages
- medkits

But is still missing several important identity-bearing resources:

- light
- ritual components
- inventory slots
- time pressure
- replenishment nodes
- safe-room interaction

### 5. There is no character-data layer for controlled flaws or temperament

The persona design notes already point toward modifiers such as:

- Cowardly
- Hotheaded
- Caretaker
- Showoff
- Weapon Specialist

But these live as policy ideas, not as character build elements.

That means the game cannot yet support "deliberately below curve but still functional" in a structured way.

### 6. Weapons and tools are too narrow

There is not enough gear diversity for equipment to define multiple archetypes.

Missing:

- more firearm families
- quiet versus loud choices
- improvised tools
- light tools
- ritual tools
- barricade or survival gear

## Capability Backlog

This backlog is ordered by the amount of character space each capability unlocks versus likely implementation cost.

## Tier 1

### 1. Modular character build schema

Add a layer between actor templates and final actor state so PCs can be assembled from components rather than taken wholesale from fixed classes.

Target additions:

- base stat package or stat array choice
- skill package or spendable skill budget
- selectable starting talent
- selectable loadout package
- optional trait or flaw modifier

Why this comes first:

- almost every later improvement is bottlenecked on it
- without this, new mechanics mostly become more premade classes

### 2. Expanded talent / perk system

Grow talents from a tiny passive list into a real build axis.

High-value early talent families:

- melee control
- ranged efficiency
- panic resistance
- rescue and stabilization
- leadership and support
- scavenging and preparation
- occult affinity

Why this comes second:

- once modular build support exists, talents are the fastest way to create expressive differentiation

### 3. Inventory and resource model expansion

Add the missing resource families that make survival-horror characters feel different from one another.

Priority resources:

- light
- ritual components
- inventory slots or carrying capacity
- personal versus shared inventory
- time pressure

Why this comes early:

- it unlocks scavenger, prepared occultist, light-bearer, survivalist, and gear-specialist character types

## Tier 2

### 4. Non-combat and survival action families

Add actions that matter because of the night's survival loop, not just because they fit inside initiative.

High-value early actions:

- `search`
- `reload`
- `transfer_item`
- `stabilize`
- `calm`
- `guard`
- `hide`
- `barricade`
- `ward`
- `scavenge`

Why this matters:

- this is one of the major shifts from combat-role simulator to horror-protagonist simulator

### 5. Trait / flaw / temperament modifiers as character data

Turn identity modifiers into buildable character components rather than keeping them only as persona-policy ideas.

Candidate modifiers:

- `Cowardly`
- `Hotheaded`
- `Caretaker`
- `Showoff`
- `Weapon Specialist`
- `Superstitious`
- `Bad Knee`

Why this matters:

- it supports identity-driven characters
- it supports deliberate but bounded suboptimality
- it reduces the gap between character fantasy and simulator representation

### 6. Weapon and tool ecosystem expansion

Add enough equipment variety that gear can define a character identity.

High-value additions:

- shotgun
- rifle or hunting gun
- improvised quiet weapon
- heavy noisy melee weapon
- flashlight or lantern
- medkit as item
- ritual kit
- salt, charms, wards
- barricade tools

Why this matters:

- specialist fantasies need real tool distinctions, not just stat differences

## Tier 3

### 7. Scenario interaction layer

Let characters matter through the map and the scenario, not only through enemy attrition.

Add:

- loot nodes
- safe rooms
- searchable areas
- blocked or unlockable paths
- environmental hazards
- sanctified or cursed spaces
- time costs outside direct combat

Why this matters:

- this is what unlocks scout, explorer, engineer, and preparation-heavy character types

### 8. Protection and interception mechanics

Support characters whose identity is keeping other people alive rather than maximizing their own output.

Add:

- guard ally
- intercept attack
- body-block route
- cover retreat
- drag or carry wounded ally

Why this matters:

- the current bruiser can control space, but cannot really be a bodyguard

### 9. Occult subsystem proper

Once ritual resources exist, give them real verbs and scenario hooks.

Add:

- ward area
- banish
- reveal hidden threat
- suppress fear effect
- exploit monster weakness
- risky ritual with time or exposure cost

Why this matters:

- this is what turns the occultist into a true supernatural specialist instead of just a fear attacker

## Tier 4

### 10. Stealth / noise / exposure system

Add:

- hidden state
- noise generation
- enemy attention or pursuit
- ambush bonuses
- interaction between concealment and carried light

Why it is later:

- it depends on earlier work in scenario interaction and non-combat actions

### 11. Social and NPC-facing procedures

Add:

- calm civilian
- deceive or distract
- extract information
- coordinate or command NPCs
- protect or escort noncombatants

Why it is later:

- the immediate foundation problem is survival-horror identity more than social gameplay

## Recommended Order

If implementation starts soon, the highest-momentum sequence is:

1. modular build schema
2. expanded talent system
3. inventory and resource expansion
4. non-combat action families
5. weapon and tool expansion
6. trait and flaw modifiers
7. scenario interaction layer
8. protection mechanics
9. occult subsystem
10. stealth / noise system
11. social procedures

## Why This Order

This sequence produces:

- build expression first
- survival-horror identity second
- scenario-facing specialization third

That means new character types become possible early, without waiting for the entire exploration game to be fully built out.

## What This Backlog Unlocks Fastest

If work stops after the first four items, the game should already be much closer to supporting:

- scavenger
- leader
- coward-survivor
- caretaker
- prepared occultist
- survivalist
- bodyguard-lite
- flawed but playable characters

## Working Conclusion

The simulator is already a decent combat-role lab.

It is not yet a strong character-expression lab.

The main work before chargen procedures is therefore:

- make characters composable
- widen the resource and action vocabulary
- add identity-bearing traits, tools, and scenario hooks

Only after that foundation exists will chargen support, guided procedures, and Session 0 hooks have enough real material to work with.
