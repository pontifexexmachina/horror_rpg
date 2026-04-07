# Spatial Rules Architecture

## Why This Exists

Dead By Dawn wants space to matter. A cramped hallway, a blocked stairwell, a ruined chapel, and a wide-open ballroom should not merely look different. They should play differently.

At the same time, the game should not require a full tactical miniatures engine in order for those differences to matter. The core rules need to be easy to adjudicate at the table, easy to explain in the book, and tractable for the simulator.

This note proposes a two-layer spatial model:

- a canonical area-based tactical model as the core rules
- an optional grid mode as a presentation and precision layer over the same underlying concepts

The goal is not to choose between theater of the mind and grid play. The goal is to make both work from the same mechanical foundation.

## Design Goals

The spatial rules should:

- make horror spaces feel materially different from one another
- support room-to-room pursuit, chokepoints, exits, ambushes, and retreats
- distinguish open spaces from constrained ones
- make line of sight, cover, and concealment matter
- remain adjudicable without counting exact squares
- support optional grid play without creating a second incompatible rules engine
- be simulable without a full physics or pathfinding model

## Core Position

The default rules should not be pure range bands.

Pure range bands are useful for early simulator work, but they flatten too much. They do not naturally express:

- who controls the doorway
- whether the monster is between you and the exit
- whether a corridor can only support one or two bodies abreast
- whether a ballroom gives the shooter too much room to dominate
- whether the darkness in the next room matters before you step into it

The default rules should also not require full-time grid tactics.

A grid is often the fastest way to communicate space, but it creates overhead if every encounter assumes exact square-counting, exact movement budgets, and exact geometry. That overhead is not always desirable in a horror RPG where pacing, dread, and procedure matter as much as tactical precision.

The likely best core is a hybrid:

- area-based tactical rules as the canonical mechanics
- optional grid-based presentation and precision rules built on top of those mechanics

## Canonical Tactical Concepts

These are the concepts the rules and simulator should care about. They are the stable layer beneath both area play and grid play.

### Areas

An area is a tactically meaningful chunk of space.

Examples:

- a narrow hallway
- a foyer
- a stair landing
- the stage in a ballroom
- the balcony above the ballroom
- a kitchen
- the far side of a graveyard

An area is not defined by exact square footage. It is defined by whether movement and interaction inside it can reasonably be treated as local for the current scene.

### Connections

Areas connect to one another through doors, halls, stairs, windows, broken walls, catwalks, and similar routes.

Connections may have properties such as:

- open
- blocked
- locked
- narrow
- hazardous
- noisy
- one-way
- climb

### Engagement

Engagement is local immediate danger.

If two hostile actors are engaged, they are close enough that melee pressure, interference, and escape risk all matter right now.

In area play, engagement usually means sharing an area and being actively tied up with one another.

In grid play, engagement is derived from map position, but it should still map back to the same core concept rather than creating a separate melee engine.

### Line of Sight

Line of sight answers whether a target can be seen well enough to target effectively.

This should be kept distinct from line of effect.

A target may be visible but hard to hit because of concealment, smoke, darkness, or movement.

### Line of Effect

Line of effect answers whether something can physically travel to the target.

A target behind a sealed wall has no line of effect. A target behind a railing may have line of sight and line of effect, but also cover.

### Cover

Cover is physical protection that blocks or interferes with attacks.

Examples:

- doorframes
- overturned tables
- pillars
- stone crypts
- wrecked machinery

### Concealment

Concealment makes a target hard to perceive clearly, but does not necessarily stop attacks from reaching them.

Examples:

- darkness
- fog
- smoke
- hanging sheets
- dense brush

Cover and concealment should not be the same rule, even if they often stack.

### Chokepoints

Some areas or connections limit how many actors can effectively contest them at once.

Examples:

- a narrow corridor
- a staircase
- a doorway
- a bathroom stall entrance

This matters enormously to horror pacing. A cramped hallway and a ballroom are different because the hallway compresses threat while the ballroom diffuses it.

### Objectives

An encounter should not always be won by killing everything.

Objectives should attach to areas and connections as much as to enemies.

Examples:

- reach the exit
- hold the stairwell for 3 rounds
- get the generator running in the basement
- retrieve supplies from the infirmary
- keep the creature out of the chapel

## Area Mode: Default Table Rules

The default table rules should use areas rather than exact squares.

In area mode:

- a scene is divided into a small number of tactically meaningful areas
- actors occupy an area
- movement shifts an actor from one area to a connected area
- melee generally requires sharing an area or actively engaging across a narrow connection
- ranged attacks require line of sight and line of effect across areas
- cover, concealment, hazards, and chokepoints are properties of areas and connections

This gives the GM enough structure to answer meaningful tactical questions without measuring every step.

## Grid Mode: Optional Precision Layer

Grid play should be presented as an option, not as the hidden real game.

In grid mode:

- the map provides a more detailed visual representation of areas and connections
- exact positions on the map help answer line of sight, cover, and lane control faster
- the grid is used to resolve local uncertainty, not to replace the canonical tactical concepts

The key rule architecture principle is:

The area model is canonical. The grid is a more detailed way to observe and adjudicate the same battlefield.

That means:

- areas still exist, even on a grid map
- engagement still matters as a rules concept
- chokepoints still matter as a rules concept
- cover and concealment still resolve through the same mechanics
- the simulator can continue to model the canonical layer without simulating every square

## Ballroom vs Hallway

This design exists to make spaces like these matter immediately.

### Cramped Hallway

A cramped hallway should usually imply:

- narrow connection or narrow area
- limited engagement width
- limited ability to get around enemies
- short lines of sight
- high ambush potential
- strong defender advantage if someone is holding the line

### Wide-Open Ballroom

A wide-open ballroom should usually imply:

- open area
- long lines of sight
- weak natural cover unless furnished or ruined
- easier repositioning
- less ability to lock the whole field down with one body
- more exposure to ranged attack and pursuit

These should not just be descriptive tags. They should have direct tactical consequences.

## Rules Writing Approach

The published rules should likely be split into:

- Core tactical rules using areas and connections
- Environmental traits such as cover, concealment, darkness, hazards, and chokepoints
- Optional grid conversion guidance

The optional grid guidance should answer:

- how to read areas from a map
- when exact placement matters
- how to adjudicate engagement on a grid
- how to handle cover and line of sight on a map without turning play into geometry homework

## Simulator Implications

The simulator should evolve in layers.

### Current State

Right now the simulator uses personal range bands and no real environment model.

That is good enough for early balance work, but it is still a white-room abstraction.

### Next Spatial Layer

The next simulator layer should not jump straight to square-by-square maps.

It should instead add:

- areas or zones
- connections between them
- area tags such as open, dark, cramped, hazardous, or cover-rich
- connection tags such as blocked, narrow, locked, or noisy
- objectives attached to areas

### Later Optional Layer

If needed later, the simulator could support more exact local positioning inside areas. But that should be a later extension, not the first move.

## Proposed Canonical Schema Concepts

The simulator and future compendium data should probably grow toward concepts like:

- `areas`
- `connections`
- `area_tags`
- `connection_tags`
- `occupancy_limits`
- `visibility_rules`
- `cover_rules`
- `objectives`
- `entry_points`
- `escape_points`
- `loot_nodes`

That lets scenarios express spaces as theaters of operations rather than featureless white rooms.

## Recommended Implementation Sequence

### Step 1: Environment-Aware Scenarios

Add scenario-level:

- areas
- connections
- area tags
- connection tags
- objective types

Keep current combat resolution mostly intact.

### Step 2: Actor Location

Replace single personal range bands with:

- current area
- local engagement state

### Step 3: Visibility and Cover

Add area- and connection-based checks for:

- line of sight
- line of effect
- cover
- concealment

### Step 4: Chokepoints and Access Control

Add support for:

- limited frontage
- blocked passage
- holding a doorway
- forced retreat routes

### Step 5: Exploration and Session Integration

Tie the spatial model into:

- scavenging
- detours
- time costs
- route choice
- safe rooms and recovery windows

## Guardrails

We should avoid:

- making the grid the only complete version of the rules
- requiring exact square-counting for ordinary play
- inventing a second incompatible tactical engine for mapped encounters
- jumping to a full physics sim before the area model is working

## Working Decision

For now, the working decision should be:

- build Dead By Dawn's core tactical rules around areas, connections, and theater-of-operations play
- support grid maps as an optional, strongly supported presentation mode
- evolve the simulator toward area-based scenarios first

This gives us a path that is tactically meaningful, horror-friendly, and implementable.
