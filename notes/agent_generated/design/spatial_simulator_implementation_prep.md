# Spatial Simulator Implementation Prep

## Purpose

This note translates the spatial rules architecture into a concrete implementation target for the simulator.

The goal is not to build the full spatial engine in one pass. The goal is to define the first useful slice cleanly enough that we can implement it with contract-first TDD.

The first slice should:

- replace white-room range bands with area-based positioning
- preserve most existing combat resolution logic
- support at least one cramped-space scenario and one open-space scenario
- establish the schema and state model that later visibility, cover, chokepoints, and objectives will use

## Current Model and Its Limits

Right now the simulator uses:

- `ActorTemplate.starting_band`
- `ActorState.range_band`
- action ranges expressed as `engaged`, `near`, `far`, `self`, `ally`, `enemy`

That is enough for early combat math, but it cannot honestly represent:

- who is in which room
- who controls a doorway
- whether a hallway is cramped
- whether a ballroom is open and exposed
- how exits, routes, and local terrain shape outcomes

So the first migration target is straightforward:

- stop modeling personal position as a single range band
- start modeling position as area occupancy plus local engagement

## First Spatial Slice

The first slice should add exactly four new spatial ideas:

1. areas
2. connections
3. actor area location
4. scenario objectives

The first slice should *not* yet fully implement:

- dynamic line-of-sight tracing across multiple hops
- exact cover math
- split-area local sub-positioning
- pathfinding
- loot or exploration procedures

Those can come later once the base contract exists.

## Proposed Scenario Schema

### AreaDefinition

Each scenario should be able to define named areas.

Proposed shape:

```yaml
areas:
  - id: foyer
    name: Foyer
    tags: [open, lit]
    occupancy_limit: null
  - id: hall
    name: Front Hall
    tags: [cramped, dark]
    occupancy_limit: 2
```

Recommended fields for v1:

- `id`: stable identifier
- `name`: human-readable label
- `tags`: scenario-facing spatial traits
- `occupancy_limit`: optional coarse cap for later crowding rules

### ConnectionDefinition

Areas should connect through explicit routes.

Proposed shape:

```yaml
connections:
  - id: foyer_to_hall
    from_area: foyer
    to_area: hall
    tags: [open]
    bidirectional: true
```

Recommended fields for v1:

- `id`: stable identifier
- `from_area`
- `to_area`
- `tags`: `open`, `narrow`, `blocked`, `locked`, `hazardous`, etc.
- `bidirectional`: whether reverse travel is allowed automatically

### ObjectiveDefinition

Scenarios should stop being pure deathmatches.

Proposed shape:

```yaml
objective:
  type: defeat_enemies
```

Early objective types could be:

- `defeat_enemies`
- `reach_exit`
- `hold_out`

For v1, one scenario can still default to `defeat_enemies`, but the schema should be ready for the others.

### Spawn Placement

Actors need a starting area.

Proposed addition to scenario side entries:

```yaml
team_a:
  - template_id: survivor
    persona_id: power_gamer
    count: 1
    start_area: foyer
```

If a side entry expands to multiple actors, they all initially spawn in that area unless a future schema says otherwise.

## Proposed Rules Models

The current `ScenarioDefinition` should grow from:

- `id`
- `name`
- `description`
- `team_a`
- `team_b`

into something closer to:

```python
class AreaDefinition(BaseModel):
    id: str
    name: str
    tags: list[str] = Field(default_factory=list)
    occupancy_limit: int | None = None


class ConnectionDefinition(BaseModel):
    id: str
    from_area: str
    to_area: str
    tags: list[str] = Field(default_factory=list)
    bidirectional: bool = True


class ObjectiveDefinition(BaseModel):
    type: Literal["defeat_enemies", "reach_exit", "hold_out"]
    area_id: str | None = None
    rounds: int | None = None


class ScenarioSideEntry(BaseModel):
    template_id: str
    persona_id: str | None = None
    count: int = 1
    start_area: str


class ScenarioDefinition(BaseModel):
    id: str
    name: str
    description: str
    areas: list[AreaDefinition]
    connections: list[ConnectionDefinition]
    objective: ObjectiveDefinition
    team_a: list[ScenarioSideEntry]
    team_b: list[ScenarioSideEntry]
```

Validation should ensure:

- area ids are unique within the scenario
- all `start_area` values exist
- all connection endpoints exist
- objective area references exist when present

## Proposed State Model

The current `ActorState.range_band` should be replaced by:

- `area_id: str`
- `engaged_with: frozenset[str]`

That gives us a much better foundation.

### Why `engaged_with`

A single `engaged` boolean is too weak once multiple actors can share an area.

We need to know whether an actor is currently tied up with:

- one enemy
- several enemies
- nobody in the same area

That matters for movement, melee targeting, fallback, and chokepoints.

Proposed shape:

```python
@dataclass(frozen=True)
class ActorState:
    ...
    area_id: str
    engaged_with: frozenset[str]
```

We do not need local x/y coordinates inside the area yet.

## Movement Model for v1

In the first area-based slice:

- an actor may move only along scenario connections
- a move action changes `area_id`
- movement through a `blocked` connection is illegal
- movement through a `narrow` connection is still legal for now, but the tag is stored for later rules
- leaving engagement should remain restricted just as falling back is restricted now

That means the first move generation rules become:

- if there is a connected destination area, `advance` can become `move`
- melee actions require at least one hostile target in the same area
- ranged actions can initially target hostiles in the same area or in directly connected areas

That last point is intentionally conservative. It gives us useful local space before we implement deeper LOS rules.

## Range Translation Strategy

Current action definitions still use `engaged`, `near`, and `far` ranges.

We should not solve the entire action-schema rewrite in the same step as the spatial migration.

Instead, the first translation should be:

- `engaged` means a hostile target in the same area and in `engaged_with`
- `near` means target in the same area
- `far` means target in the same area or a directly connected visible area
- `ally` means ally in the same area
- `enemy` means enemy in the same area or directly connected area, depending on effect

This keeps existing action data usable while we migrate the positional model.

## Initial Scenario Fixtures

We should create two new scenarios specifically to exercise the new model.

### Hallway Ambush

Purpose:

- verify cramped spaces feel different from open spaces
- verify movement between areas matters
- verify narrow routes are representable

Suggested structure:

- `entry`
- `hallway`
- `parlor`

Tags:

- hallway is `cramped`, `dark`
- connections are `narrow`

Initial pressure:

- team A starts in `entry`
- monster starts in `hallway`
- support or second monster starts in `parlor`

### Ballroom Escape

Purpose:

- verify open spaces and exits are representable
- verify objective schema is real, not decorative

Suggested structure:

- `gallery`
- `ballroom`
- `stage`
- `side_exit`

Tags:

- ballroom is `open`, `lit`
- stage is `elevated`
- side exit is tagged as an escape area

Objective:

- `reach_exit`

This lets us test a non-deathmatch encounter immediately.

## Test Plan

We should add tests in layers.

### Schema Tests

- valid scenario with areas and connections loads successfully
- scenario fails if `start_area` is unknown
- scenario fails if connection endpoint is unknown
- scenario fails if objective area is unknown

### State Construction Tests

- actor state is initialized in the correct area
- actor state starts with empty `engaged_with`

### Legal Action Tests

- melee attacks only appear for hostiles in the same area and engaged
- move actions only appear for connected destination areas
- blocked connections do not generate move actions
- ranged attacks can initially reach directly connected areas but not two hops away
- ally-targeted healing only works on allies in the same area for v1

### Engine Tests

- moving changes `area_id`
- entering an occupied hostile area can create engagement
- leaving engagement requires the correct action path or restriction
- defeat-enemies objective still ends the encounter correctly
- reach-exit objective ends the encounter when enough PCs reach the exit area

### Scenario Behavior Tests

- hallway ambush produces more constrained legal movement than ballroom escape
- ballroom escape exposes more ranged options than hallway ambush

## Migration Strategy

We should do this in a way that does not require rewriting the whole simulator at once.

### Phase 1

Add the schema and validation while leaving old scenarios untouched until migrated.

Possible compatibility bridge:

- allow legacy scenarios with no `areas`
- synthesize a single default area for them temporarily

### Phase 2

Replace `range_band` in `ActorState` with `area_id` plus `engaged_with`.

At that point, action generation and engine logic migrate to area-based reasoning.

### Phase 3

Add explicit objective handling and at least one non-deathmatch scenario.

### Phase 4

Only then add visibility, cover, and chokepoint rules on top of the new model.

## Recommended First Coding Slice

The smallest honest coding slice after this note is:

1. add `AreaDefinition`, `ConnectionDefinition`, and `ObjectiveDefinition` to `rules.py`
2. extend scenario YAML with `areas`, `connections`, `objective`, and `start_area`
3. replace `range_band` with `area_id` and `engaged_with` in `state.py`
4. update legal action generation so movement uses area connections
5. add `hallway_ambush.yml` and `ballroom_escape.yml`
6. add schema and action-generation tests before implementation details

That slice is big enough to matter and still small enough to finish cleanly.
