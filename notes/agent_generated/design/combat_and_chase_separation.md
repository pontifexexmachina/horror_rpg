# Combat And Chase Separation

This note captures a design correction for Dead By Dawn: combat simulation and fleeing/chase simulation should not be treated as the same subsystem.

The current simulator has experimented with non-deathmatch combat objectives such as `reach_exit`, but this risks producing misleading design signals because players do not usually behave as objective-rational skirmish agents when retreat is on the table.

## Core Thesis

Combat and escape are different phases of play.

The combat simulator should answer:
- What happens if the PCs stand and fight?
- How much damage, stress, and resource loss does that fight impose?
- How lethal or survivable is the monster in direct engagement?
- How do support, positioning, control, and attrition affect a stand-up fight?

A separate flee/chase subsystem should answer:
- When the group decides to break contact, can they get away?
- What does escape cost in wounds, stress, time, separation, supplies, or lost position?
- Does the monster remain a threat afterward?
- How often does escape create a worse later encounter rather than resolving the threat?

## Why Separate Them

### 1. Player behavior is not retreat-optimized

Real players usually do not flee the moment a retreat becomes mathematically correct.

They tend to:
- commit to fights once engaged
- keep trying to turn the fight around
- only retreat after the fight already looks bad
- hesitate because running feels like abandoning progress
- fear that an undefeated monster will remain a future threat

A combat simulator that assumes early, rational retreat will underestimate danger and mis-model actual table behavior.

### 2. Persistent monsters distort retreat incentives

If the game plays fair with the players, then a monster that escapes now can menace them later, usually after they have spent even more resources.

That means players are strongly incentivized to finish a monster once they have started spending:
- bullets
- bandages
- stress
- position
- time

A dead monster is solved. A living monster is deferred danger.

### 3. Escape is not the same as winning the fight

In survival horror, escaping often means:
- you survived this moment
- you lost ground, time, or supplies
- the threat may still exist
- the scenario pressure may now be worse

That is a very different outcome from defeating the enemy, and it should not be flattened into the same victory logic.

## Recommended Design Split

### Combat Layer

Use the combat simulator for situations where the question is primarily about fighting.

Good combat-layer objectives:
- defeat the enemy
- survive a fixed number of rounds while engaged
- prevent an enemy from reaching or destroying something during the fight
- protect an ally or object during a fight

Combat benchmarks should mostly assume:
- the party is trying to win the fight
- retreat is not chosen unless the situation has already gone bad
- monsters killed now do not return later

### Chase / Flee Layer

Create a separate subsystem for breaking contact and escaping pursuit.

Good chase-layer questions:
- can the party disengage successfully?
- who gets left behind or cut off?
- what damage or stress is taken while fleeing?
- what resources are spent to escape?
- does the monster follow immediately, later, or not at all?
- what rooms, exits, barricades, and route choices matter?

The chase layer should care more about:
- routes
- doors
- speed
- obstructions
- noise
- darkness
- separation
- holding actions and sacrifice plays

## Phase Change Model

Instead of treating escape as an always-available combat objective, model it as a phase change.

### Phase 1: Combat
- the party engages or is engaged
- they mostly act as though the fight is winnable
- resources are spent to try to solve the threat directly

### Phase 2: Retreat Decision
- the party recognizes that the fight is no longer worth continuing
- this should usually happen late, not early
- the decision point may depend on casualties, stress, ammo, position, or monster reveals

### Phase 3: Chase / Break Contact
- the goal is no longer to kill the enemy
- the goal is to escape with acceptable losses
- the system should determine whether the group gets away and what it costs

## Simulator Implications

### The combat sim should stop overloading `reach_exit`

`reach_exit` inside the combat engine is a useful experiment, but it should not be treated as the main way Dead By Dawn models retreat.

It is likely better used for narrow edge cases like:
- reaching a panic room while the fight is still active
- crossing a battlefield to get to a lock or switch
- forcing passage during an otherwise combat-forward scene

It is a poor default for modeling full retreat behavior.

### Retreat behavior should be modeled conservatively

The simulator should assume something closer to human behavior:
- players do not flee at the first mathematically bad sign
- they flee after real pressure accumulates
- sunk-cost incentives matter
- unfinished monsters matter

A future retreat policy could trigger only after conditions like:
- one PC is dead, critical, or broken
- multiple PCs are wounded
- party ammo is below a threshold
- monster durability exceeds an expected kill window
- stress has crossed a panic/breakdown danger line

## Design Goals For A Future Chase System

A future chase/flee subsystem should support all of the following:
- break-contact attempts
- pursuit pressure over connected spaces
- route choice and blocked routes
- holding the line so others can escape
- separation risk
- rearguard actions
- temporary safety versus permanent resolution
- monster persistence after escape

It should also integrate with the resource model:
- ammo spent while covering retreat
- bandages spent after escape
- time lost while routing around danger
- additional stress from panic flight
- scenario escalation because the threat survives

## Benchmark Implications

For now, combat benchmarks should mostly return to asking:
- if the players stand and fight, how favorable is the encounter?
- what does winning cost them?
- how much attrition carries forward?

Later, chase benchmarks should ask:
- once the party decides to run, what fraction escape?
- how many escape cleanly versus bloodily?
- how often does the monster survive to become a future threat?
- how much does failed retreat worsen the next encounter?

## Practical Guidance For The Current Simulator

Short term:
1. Keep combat benchmarks focused on direct engagements.
2. Treat `reach_exit` as an experimental or special-case objective, not the default retreat model.
3. Interpret escape benchmark results cautiously because they are still combat-engine outputs, not true chase outputs.

Medium term:
1. Design a dedicated chase/flee rules model.
2. Add a retreat decision policy that assumes late retreat rather than ideal retreat.
3. Add persistent-monster consequences to session simulation.

## Open Questions

1. What makes a monster persistent after escape: all monsters, only some monsters, or scenario-specific tags?
2. How much of retreat is individual versus group-based?
3. Should fleeing always risk separation?
4. What resources can be intentionally spent to improve escape odds?
5. When does a chase fully end rather than pausing the threat temporarily?

## Recommended Next Step

Design a dedicated `chase_and_flee_model.md` note and keep combat balancing focused on fights the players are actually trying to win.
