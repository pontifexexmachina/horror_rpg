from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field, replace
from enum import Enum
from typing import Literal

from dead_by_dawn_sim.rules import (
    ActorTemplate,
    AreaDefinition,
    ConnectionDefinition,
    DeathMode,
    ObjectiveDefinition,
    Ruleset,
)


class ActorStatus(str, Enum):
    NORMAL = "normal"
    WOUNDED = "wounded"
    CRITICAL = "critical"
    DEAD = "dead"
    BROKEN = "broken"


@dataclass(frozen=True)
class ConditionState:
    id: str
    rounds_remaining: int


@dataclass(frozen=True)
class TalentState:
    used: frozenset[str] = field(default_factory=frozenset)


StatKey = Literal["might", "speed", "wits"]


@dataclass(frozen=True)
class ActorState:
    actor_id: str
    name: str
    team: str
    template_id: str
    stats: dict[StatKey, int]
    skills: dict[str, int]
    hp: int
    max_hp: int
    defense: int
    stress: int
    shrouds: int
    status: ActorStatus
    weapon_id: str | None
    ammo: dict[str, int]
    bandages: int
    medkits: int
    action_ids: tuple[str, ...]
    talent_ids: tuple[str, ...]
    talent_state: TalentState
    conditions: tuple[ConditionState, ...]
    death_mode: DeathMode
    area_id: str
    engaged_with: frozenset[str]

    @property
    def can_act(self) -> bool:
        return self.status in {ActorStatus.NORMAL, ActorStatus.WOUNDED}


@dataclass(frozen=True)
class EncounterState:
    scenario_id: str
    objective: ObjectiveDefinition
    areas: dict[str, AreaDefinition]
    connections: tuple[ConnectionDefinition, ...]
    actors: dict[str, ActorState]
    round_number: int
    initiative_order: tuple[str, ...]
    active_actor_id: str | None
    winner: str | None = None
    events: tuple[str, ...] = field(default_factory=tuple)

    def actor(self, actor_id: str) -> ActorState:
        return self.actors[actor_id]


def area_has_tag(state: EncounterState, area_id: str, tag: str) -> bool:
    return tag in state.areas[area_id].tags


def actor_count_in_area(state: EncounterState, area_id: str) -> int:
    return sum(
        1
        for actor in state.actors.values()
        if actor.area_id == area_id and actor.status is not ActorStatus.DEAD
    )


def can_enter_area(state: EncounterState, area_id: str) -> bool:
    occupancy_limit = state.areas[area_id].occupancy_limit
    if occupancy_limit is None:
        return True
    return actor_count_in_area(state, area_id) < occupancy_limit


def connection_between(
    state: EncounterState, from_area: str, to_area: str
) -> ConnectionDefinition | None:
    for connection in state.connections:
        if connection.from_area == from_area and connection.to_area == to_area:
            return connection
        if (
            connection.bidirectional
            and connection.from_area == to_area
            and connection.to_area == from_area
        ):
            return connection
    return None


def has_line_of_effect(state: EncounterState, from_area: str, to_area: str) -> bool:
    if from_area == to_area:
        return True
    connection = connection_between(state, from_area, to_area)
    if connection is None:
        return False
    return "blocked" not in connection.tags


def has_line_of_sight(state: EncounterState, from_area: str, to_area: str) -> bool:
    if not has_line_of_effect(state, from_area, to_area):
        return False
    if from_area == to_area:
        return True
    connection = connection_between(state, from_area, to_area)
    if connection is None:
        return False
    return "blocked_sight" not in connection.tags


def connected_area_ids(state: EncounterState, area_id: str) -> tuple[str, ...]:
    connected: list[str] = []
    for connection in state.connections:
        if "blocked" in connection.tags:
            continue
        if connection.from_area == area_id:
            connected.append(connection.to_area)
        elif connection.bidirectional and connection.to_area == area_id:
            connected.append(connection.from_area)
    return tuple(dict.fromkeys(connected))


def shortest_path_distance(state: EncounterState, start_area: str, goal_area: str) -> int | None:
    if start_area == goal_area:
        return 0
    frontier: deque[tuple[str, int]] = deque([(start_area, 0)])
    seen = {start_area}
    while frontier:
        current, distance = frontier.popleft()
        for neighbor in connected_area_ids(state, current):
            if neighbor in seen:
                continue
            if neighbor == goal_area:
                return distance + 1
            seen.add(neighbor)
            frontier.append((neighbor, distance + 1))
    return None


def build_actor_state(
    actor_id: str,
    team: str,
    template: ActorTemplate,
    ruleset: Ruleset,
    name: str,
    start_area: str,
) -> ActorState:
    max_hp = ruleset.core.hp_base + template.stats["might"]
    defense = ruleset.core.defense_base + template.stats["speed"]
    return ActorState(
        actor_id=actor_id,
        name=name,
        team=team,
        template_id=template.id,
        stats=dict(template.stats),
        skills=dict(template.skills),
        hp=max_hp,
        max_hp=max_hp,
        defense=defense,
        stress=ruleset.core.stress.starting,
        shrouds=0,
        status=ActorStatus.NORMAL,
        weapon_id=template.weapon_id,
        ammo=dict(template.starting_ammo),
        bandages=template.starting_bandages,
        medkits=template.starting_medkits,
        action_ids=tuple(template.actions),
        talent_ids=tuple(template.talents),
        talent_state=TalentState(),
        conditions=tuple(),
        death_mode=template.death_mode,
        area_id=start_area,
        engaged_with=frozenset(),
    )


def update_actor(state: EncounterState, actor: ActorState) -> EncounterState:
    updated = dict(state.actors)
    updated[actor.actor_id] = actor
    return replace(state, actors=updated)


def append_event(state: EncounterState, message: str) -> EncounterState:
    return replace(state, events=(*state.events, message))


def synchronize_engagements(state: EncounterState) -> EncounterState:
    updated: dict[str, ActorState] = {}
    for actor_id, actor in state.actors.items():
        engaged = frozenset(
            other.actor_id
            for other in state.actors.values()
            if other.actor_id != actor_id
            and other.team != actor.team
            and other.area_id == actor.area_id
            and other.status not in {ActorStatus.DEAD, ActorStatus.BROKEN}
        )
        updated[actor_id] = replace(actor, engaged_with=engaged)
    return replace(state, actors=updated)
