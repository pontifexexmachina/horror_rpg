# Session Simulation Goals

This note defines what the simulator should optimize for once Dead By Dawn moves beyond isolated encounter testing.

The current simulator is an encounter lab. That is still useful, but it is not yet testing the unit of play that matters most for a horror RPG.

A real session or "adventuring day" should involve multiple scenes, multiple threats, pacing variation, and resource carryover. The simulator therefore needs a larger frame for judging whether the game is doing what it is supposed to do.

## Why Encounter-Level Balance Is Not Enough

A fight can be individually fair and still produce bad horror play.

Examples:

- fights reset too cleanly, so attrition never matters
- stress spikes in one scene but vanishes from relevance because nothing follows it
- one monster type loses often but still softens the party correctly for later scenes
- a build looks weak in one fight but is extremely valuable across a session

That means isolated encounter results are necessary but not sufficient.

The simulator should treat encounter balance as one layer inside a larger session-pressure model.

## Primary Design Question

The main question should become:

How does a 3-5 PC party perform across a full horror session with varying encounter intensity, imperfect information, and persistent consequences?

That is a better target than "does a fresh party beat one monster from full resources?"

## Assumed Party Size

The simulator should treat 3-5 PCs as the honest baseline range.

Recommended baseline party models:

- 3 PCs: stressed, fragile, low redundancy
- 4 PCs: core baseline
- 5 PCs: high redundancy, more tactical coverage

The existing 1-2 PC scenarios remain useful for micro-analysis, but they should not be treated as the primary balancing target.

## Session Model

A session model should be a sequence of encounters or pressure scenes, not one fight.

At minimum, a session simulation should support:

- ordered scenes
- persistent party state across scenes
- encounter classes with different expected intensity
- explicit recovery windows
- session end conditions

The session simulator does not need to model every conversation or clue. It does need to model the mechanical cost structure of what happens between the start and end of a night of play.

## Encounter Classes

Not every encounter should hit the party with the same force.

The simulator should eventually classify encounters into a few pacing buckets.

Suggested initial classes:

- ambient pressure scene
- light encounter
- standard threat
- spike threat
- climax encounter

### Ambient Pressure Scene

Purpose:

- raise tension
- tax stress or positioning lightly
- threaten future danger without demanding a full fight

Expected result:

- low HP loss
- low to moderate stress gain
- little or no death risk by itself

### Light Encounter

Purpose:

- keep pressure on
- reward clean play
- create attrition without dominating the whole session

Expected result:

- modest HP/stress cost
- low but nonzero chance of Wounded
- should not usually consume all major resources

### Standard Threat

Purpose:

- represent the most common serious conflict
- test whether the party is handling the night's pressure well

Expected result:

- meaningful injury and/or stress
- real chance of Wounded or Critical
- should matter to later scenes

### Spike Threat

Purpose:

- create a moment of acute danger before the climax
- punish prior attrition
- force hard choices

Expected result:

- high resource cost
- real chance of collapse if the party is already strained

### Climax Encounter

Purpose:

- cash out the session's pressure
- turn prior mistakes and successes into consequences

Expected result:

- high injury/stress burden
- real chance of death or failure
- success should often look costly, not clean

## Persistent Resources And State

The simulator should carry forward any state that matters across scenes.

At minimum:

- current HP
- current Stress
- current Shrouds
- once-per-day talent usage
- conditions that can plausibly persist into the next scene

Potential later additions:

- ammo or charges
- consumable gear
- temporary buffs/debuffs
- narrative clocks converted into mechanical pressure

## Recovery Model

Recovery cadence needs to be explicit or the simulator cannot tell whether attrition works.

The game should define, and the simulator should model:

- what can recover between scenes
- what can recover after a calm period
- what only recovers at end of session or after full rest
- what never recovers without specific intervention

For the current rule skeleton, obvious recovery questions include:

- how often can Stress reduction realistically happen during a session?
- can HP be meaningfully recovered during a scene, between scenes, or only through specific actions?
- do Shrouds ever clear during the same night?

If those rules are undefined, the simulator should mark them as missing design dependencies rather than guess silently.

## Resource Consumption Goals

The simulator should help answer not just whether the party survives, but what survival costs.

Key session-level questions:

- How many standard threats can a baseline 4-PC party survive before collapse?
- How much HP is typically lost per encounter class?
- How much Stress is typically gained per encounter class?
- How often do once-per-day effects get consumed before the climax?
- How often does a party enter the climax already carrying Wounded, Critical, or high Stress?
- Are some encounter classes too cheap or too punishing relative to their intended pacing role?

## What Good Session Results Look Like

The simulator needs target bands, not just raw output.

These bands can evolve, but the game should have a working theory.

### Baseline Session Success

For a baseline 4-PC party across a standard session mix:

- success should be common but not easy
- the party should usually reach the climax degraded
- clean, unscarred victories should be uncommon
- total-party collapse should be possible but not the default

### Stress Success

Stress should:

- rise often enough to matter before the session ends
- alter decisions, not just decorate the sheet
- meaningfully change action economy or risk tolerance in a noticeable share of sessions

A bad result is average Stress staying near its starting value across most realistic session mixes.

### Injury Success

Injury should:

- accumulate often enough that healing/support matter
- create fear of escalation from Wounded to Critical
- remain survivable often enough that the game does not become random slaughter

A bad result is either:

- almost no injury until sudden death spikes, or
- constant grind that forces repetitive heal loops

### Climax Success

By the climax, a baseline session should often produce at least one of:

- elevated Stress
- reduced HP across the party
- once-per-day talent expenditure
- lingering death-track burden

If the climax is usually entered at full strength, earlier scenes are too cheap.

## Contribution Balance Goals

The simulator should also test whether PCs are balanced against each other while still feeling different.

This means pursuing two goals at once:

- parity of contribution
- differentiation of contribution

### Parity Of Contribution

No build should be consistently useless.

No build should be so dominant that it invalidates alternatives across most scenarios and session mixes.

Parity does not mean equal damage or equal actions. It means that each build brings meaningful value often enough to justify its existence.

### Differentiation Of Contribution

Different builds should produce meaningfully different play patterns and value profiles.

Good differentiation means:

- different action frequencies
- different pressure profiles
- different survival curves
- different preferred targets or timing windows
- different ways of helping the party succeed

A bad result is multiple builds having nearly identical contribution shapes once the numbers settle.

## Contribution Metrics

The simulator should move toward a contribution vector per PC rather than a single score.

Suggested contribution dimensions:

- damage dealt
- finishing pressure or elimination conversion
- healing delivered
- stress inflicted
- control/debuff uptime created
- damage prevented indirectly
- survival persistence
- actions spent productively
- once-per-day resource leverage

Not all of these need to be implemented immediately, but they define the right direction.

## What Good PC Balance Looks Like

For a healthy roster:

- a support or control PC should not need top damage to justify itself
- a bruiser should not out-heal the healer and out-control the controller while also leading damage
- a medic should alter attrition curves in a way visible at session scale
- a panic/control build should change enemy behavior or party survival enough to matter
- a casual-friendly build should still contribute even when piloted simply

## Missing Metrics In The Current Simulator

The current simulator tracks useful encounter data, but it is still missing several session- and contribution-level metrics.

High-value additions include:

- per-team status breakdown already added, but extend toward per-PC breakdowns
- first Wounded timing
- first Critical timing
- first death timing
- panic-threshold crossing rate
- breakdown-threshold crossing rate
- per-round HP/stress deltas
- contribution metrics per actor across an encounter
- contribution totals per actor across a session
- stall detection metrics such as repeated low-progress rounds

## Recommended Next Simulator Layers

The simulator should grow in this order:

### 1. Honest Party Benchmarks

Expand benchmark scenarios so the primary test parties are 3-5 PCs instead of 1-2 PCs.

### 2. Contribution Reporting

Add per-actor contribution metrics within the current encounter model.

### 3. Session Runner

Add a higher-level runner that chains encounters while carrying forward persistent state.

### 4. Recovery Rules

Encode explicit between-scene and between-session recovery rules once the design decides them.

### 5. Session Target Bands

Convert the design goals in this note into measurable expected ranges for specific party and session models.

## Working Heuristic

When evaluating a mechanic, ask:

- does it matter in one encounter?
- does it matter across a whole session?
- does it change party resource curves?
- does it support a distinct PC contribution profile?

If the answer is only yes at the single-fight level, it may still be failing the real design target.
