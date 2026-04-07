# Simulator / Rules / Inventory Design Pass

This note turns the current direction into a concrete next-pass design target.

The goal is not to finish the entire economy now. The goal is to define a coherent first working model that:

- supports the intended survival horror loop
- avoids dissociated resource play
- gives the simulator the right unit of analysis
- tells us which current mechanics should be rewritten instead of merely tuned

This note assumes the principles in [fictional_resource_model.md](C:\\projects\\horror_rpg\\notes\\agent_generated\\design\\fictional_resource_model.md).

## Current Problem Statement

The current simulator is still mostly testing a combat engine with abstract or semi-abstract sustain.

That has produced useful information, but it is no longer the right center of gravity.

The major current problems are:

- encounter math is being asked to carry too much of the horror burden by itself
- healing is too easy to express as a self-contained combat move instead of a supply decision
- stress pressure exists, but is not yet connected strongly enough to scenario-scale consequences
- inventory does not yet exist as a real balancing layer
- the simulator is optimizing around fresh-fight benchmarks when the intended game is about costly progress through a location

So the next pass should stop asking, "How do we make fights fair?" and start asking, "What does the party spend to survive a night?"

## High-Level Direction

Dead By Dawn should move toward a model with these properties:

- PCs win most encounters
- the party degrades across the session
- recovery depends on found supplies, time, and safety
- combat options are partly constrained by inventory state
- noncombat exploration matters because it is how the party regains options
- different builds contribute differently without relying on abstract metacurrency

That means the simulator should grow from a combat lab into a session attrition lab.

## The First Working Resource Model

The first working resource model should stay intentionally small.

Recommended tracked resources for v1:

- HP
- stress
- shrouds
- ammo by weapon family
- bandages
- medkit charges
- light charge
- ritual components
- time pressure

This is enough to create real scarcity, exploration incentives, and associated decision-making without exploding complexity.

## Resource Definitions

### HP

What it means:

- physical injury and immediate fighting capacity

How it is spent:

- incoming damage

How it recovers:

- immediate first aid with supplies
- field treatment with better supplies and time
- deep recovery only in true safety

Desired role in the design:

- moment-to-moment survivability
- one of several pressures, not the only one

### Stress

What it means:

- fear, shock, loss of composure, mounting terror

How it is spent:

- frightening encounters
- pushing too hard
- monster abilities
- prolonged exposure

How it recovers:

- real calm
- shelter
- reassurance
- drugs or ritual comfort if the setting supports them
- not because a combat ended

Desired role in the design:

- tactical pressure in fights
- session-level decision pressure between fights
- distinct from HP attrition

### Shrouds

What it means:

- proximity to death, trauma, or accumulated grave harm

How it is spent:

- dying progression

How it recovers:

- rarely during the same session
- likely only with significant treatment, safety, or supernatural intervention

Desired role in the design:

- hardening consequence track
- forces respect for injury escalation

### Ammo

What it means:

- immediately obvious offensive capability

How it is spent:

- firearm attacks and special shots

How it recovers:

- scavenging
- caches
- enemy drops only if fictionally appropriate

Desired role in the design:

- weapon identity
- route and scavenging pressure
- prevents firearms from being "just melee but better"

Recommended v1 simplification:

- do not track every caliber yet
- track `sidearm_ammo`, `longarm_ammo`, and `special_ammo` or a similarly coarse structure

### Bandages

What they mean:

- quick, limited trauma response

How they are spent:

- immediate first aid
- bleeding control
- possibly stabilizing Wounded characters

How they recover:

- scavenging
- infirmaries
- supply caches

Desired role in the design:

- make in-combat healing a visible spend
- keep healing associated and loot-driven

### Medkit Charges

What they mean:

- better medical treatment, not just improvised wrapping

How they are spent:

- field recovery during a lull
- stronger treatment than a bandage

How they recover:

- less frequently than bandages
- clinics, ambulances, locked supply rooms

Desired role in the design:

- stronger recovery with real opportunity cost
- supports the Medic without giving unlimited abstract healing

### Light Charge

What it means:

- batteries, lamp fuel, generator power, or similar visibility resource

How it is spent:

- exploration in darkness
- possibly resisting certain environmental or supernatural penalties

How it recovers:

- batteries, fuel, generators, safe rooms, supply caches

Desired role in the design:

- ties exploration and combat together
- creates route pressure without requiring combat to do everything

### Ritual Components

What they mean:

- salt, candles, iron nails, sigils, charms, incense, blessed water, etc.

How they are spent:

- occult actions
- warding
- banishment
- anti-supernatural preparation

How they recover:

- occult sites
- caches
- chapels, shrines, hidden cupboards, cult stores

Desired role in the design:

- lets occult characters feel different without abstract spell slots or point pools
- creates scenario-specific preparation decisions

### Time Pressure

What it means:

- dawn, a ritual countdown, pursuit, worsening infestation, hostage danger, weather collapse

How it is spent:

- searching
- detours
- treatment
- retreat and regrouping

How it recovers:

- usually it does not

Desired role in the design:

- prevents infinite scavenging and perfect reset play
- turns exploration into a meaningful tradeoff instead of a free refill loop

## Inventory Model

The game should probably avoid full simulationist loadouts at first.

A good first-pass inventory model is:

- a small number of item slots
- stackable consumables in coarse bundles
- a weapon slot model
- a few tagged special items

Recommended v1 structure:

- primary weapon
- secondary weapon
- 4 to 6 item slots
- consumables can stack up to a small cap per slot

Examples:

- `bandages x2`
- `sidearm_ammo x6`
- `salt packet x1`
- `battery x1`
- `medkit x1`

This is enough to create hard choices without making the game into spreadsheet inventory management.

## Recovery Model

Recovery should be split explicitly.

### In Combat

Allowed:

- bandage-based first aid
- grit-style self-stabilization if it has a strong fictional and mechanical cost

Not allowed:

- full reset healing
- free scene-based refresh

### Between Fights In Unsafe Territory

Allowed:

- medkit treatment
- limited stress reduction if the party actually secures a calm pocket
- reloads and item transfers

Costs:

- time
- supplies
- noise or exposure if relevant

### In Safe Rooms

Allowed:

- more reliable stress reduction
- broader inventory management
- stronger field treatment
- save/checkpoint style procedural reset if desired

Still not allowed:

- full overnight healing unless the fiction supports it

### Between Sessions Or After Full Rest

Allowed:

- deep HP recovery
- major stress reduction
- possible shroud removal if the design wants a longer campaign loop

## Action Redesign Implications

Several current actions should probably change shape.

### Attack

Current problem:

- attacks do not consume visible resources for firearms

Recommended direction:

- ranged attacks spend ammo
- some weapon tags may spend extra ammo for stronger effects
- quiet weapons and loud weapons should differ in scenario consequences later

### First Aid

Current problem:

- abstract healing roll with no fictional cost beyond action economy

Recommended direction:

- consumes `bandage` on use
- stabilizes or heals modestly
- better when performed by someone with Cure and proper supplies
- may be impossible without supplies

This keeps the Medic good, but in a way the world can support.

### Grit

Current problem:

- reads like a free personal healing button

Recommended direction:

Choose one:

1. make it self-stabilization instead of healing
2. make it trade stress for temporary function
3. make it reduce penalties rather than restore HP

My recommendation:

- Grit should primarily be a pain-management or self-stabilization move, not a reliable self-heal
- example: ignore Wounded penalties until end of scene, then gain 1 Stress

That is much more survival-horror and much less "I press my healing verb again."

### Shriek / Occult Pressure

Current problem:

- occult or panic actions currently risk feeling like just another combat rider

Recommended direction:

- let some occult actions consume ritual components
- let stronger anti-supernatural actions require preparation or expendables
- keep minor fear pressure as an at-will monster-side tool if desired

### Taunt / Control

Current problem:

- control exists, but its scenario-level meaning is still thin

Recommended direction:

- keep simple combat control, but avoid building whole character roles around abstract control spam
- some control may later come from environment use, traps, barricades, or route manipulation instead

## Actor And Build Implications

Different builds should express different relationships to resources.

### Survivor

Should feel like:

- efficient generalist
- good with ammo use
- solid at staying alive under pressure

Possible identity:

- turns ammo into reliable damage
- good panic resistance
- decent at carrying the run when things go wrong

### Medic

Should feel like:

- the best at converting medical supplies into party longevity
- not a fountain of abstract healing

Possible identity:

- better yield from bandages and medkits
- safer treatment under pressure
- stronger stabilization and field recovery

### Bruiser

Should feel like:

- less dependent on supplies for moment-to-moment offense
- good at protecting others in close quarters

Possible identity:

- strong when ammo is scarce
- better at shoving, holding space, or finishing wounded enemies
- uses Grit to stay in the fight, not to erase injuries for free

### Occultist

Should feel like:

- a specialist in supernatural pressure and defense
- dependent on strange, scenario-specific tools

Possible identity:

- strong against supernatural enemies when prepared
- can convert ritual components into safety, warding, or panic pressure
- weak when deprived of preparation or tools

## Simulator Data Model Implications

The simulator schema should add explicit inventory and session fields.

### Actor Template Additions

Each actor template should eventually declare:

- starting inventory bundles
- carrying capacity
- recovery efficiencies
- ammo profile if armed
- special item affinities

### Encounter State Additions

The encounter layer should eventually track:

- current ammo counts
- current consumable counts
- weapon readiness if relevant
- noise or exposure later if needed

### Session State Additions

The session layer should track:

- party shared inventory if the game allows pooling
- actor personal inventory if the game keeps it separate
- current time clock
- safe-room availability or usage
- remaining unexplored replenishment nodes

### Scenario Data Additions

Scenarios should eventually define:

- loot nodes
- replenishment probabilities or fixed finds
- safe rooms
- optional detours
- time costs for travel, search, and treatment

## Suggested First Simulator Expansion

Do not try to add the whole economy at once.

Recommended order:

1. Add ammo to ranged attacks.
2. Add bandages as a requirement for First Aid.
3. Redesign Grit into self-stabilization rather than free healing.
4. Add medkit charges for stronger between-scene recovery.
5. Add a session runner with carry-forward HP, stress, ammo, and supplies.
6. Add time costs and loot nodes.

That sequence gets the game out of abstract sustain land quickly.

## Suggested First Rules Rewrites

If the manuscript were being rewritten to match this direction, the first concrete rewrites would be:

- firearms list ammo and reload handling
- First Aid consumes a bandage or medkit use
- Grit becomes a pain-management or stabilization rule
- stress recovery requires real calm, shelter, or specific aids
- safe rooms are introduced as a procedural element
- exploration/search procedures determine how resources are found

## What Good Results Should Look Like

Once this model is in place, simulator success should look more like this:

- team A wins most encounters
- average ammo and supply loss is meaningful
- parties sometimes choose detours to replenish
- medics increase the effective value of limited supplies rather than printing healing
- bruisers become more valuable when ammo is low or space control matters
- occultists matter most in supernatural scenarios and when components are available
- climax encounters are won with depleted resources rather than with fresh sheets

## Working Recommendation

The current simulator should stop being treated as a combat balancer with a few extra dials.

It should become the first layer of a fiction-first attrition model.

That means the next serious implementation milestone should be:

- inventory-aware actions
- supply-gated healing
- session carry-forward
- exploration-driven replenishment

That is the point where the simulator will actually be testing the game Dead By Dawn seems to want to be.
