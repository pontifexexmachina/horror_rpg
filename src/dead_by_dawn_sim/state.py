from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field, replace
from enum import Enum
from typing import TYPE_CHECKING, Literal

if TYPE_CHECKING:
    from dead_by_dawn_sim.rules import (
        ActorTemplate,
        AreaDefinition,
        ConnectionDefinition,
        DeathMode,
        ObjectiveDefinition,
        Ruleset,
        StressMode,
    )
    from dead_by_dawn_sim.rules_content_models import ResourceId

CONSUMABLE_RESOURCE_IDS: frozenset[ResourceId] = frozenset({"bandages", "medkits"})


class ActorStatus(str, Enum):
    NORMAL = "normal"
    WOUNDED = "wounded"
    CRITICAL = "critical"
    STABLE = "stable"
    DEAD = "dead"
    BROKEN = "broken"


_NONACTIVE_STATUSES = frozenset(
    {ActorStatus.CRITICAL, ActorStatus.STABLE, ActorStatus.DEAD, ActorStatus.BROKEN}
)


@dataclass(frozen=True)
class ConditionState:
    id: str
    rounds_remaining: int
    source_actor_id: str | None = None


@dataclass(frozen=True)
class TalentState:
    used: frozenset[str] = field(default_factory=frozenset)


@dataclass(frozen=True)
class AttackModifierState:
    amount: int
    rounds_remaining: int
    source_actor_id: str | None = None


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
    resources: dict[str, int]
    action_ids: tuple[str, ...]
    talent_ids: tuple[str, ...]
    talent_state: TalentState
    conditions: tuple[ConditionState, ...]
    attack_modifiers: tuple[AttackModifierState, ...]
    death_mode: DeathMode
    stress_mode: StressMode
    area_id: str
    engaged_with: frozenset[str]

    @property
    def can_act(self) -> bool:
        return self.status in {ActorStatus.NORMAL, ActorStatus.WOUNDED}

    @property
    def ammo(self) -> dict[str, int]:
        return {
            resource_id: amount
            for resource_id, amount in self.resources.items()
            if resource_id not in CONSUMABLE_RESOURCE_IDS
        }

    @property
    def bandages(self) -> int:
        return self.resources.get("bandages", 0)

    @property
    def medkits(self) -> int:
        return self.resources.get("medkits", 0)

    def resource_amount(self, resource_id: str) -> int:
        return self.resources.get(resource_id, 0)


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
    used_reactions: frozenset[str] = field(default_factory=frozenset)
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
    return occupancy_limit is None or actor_count_in_area(state, area_id) < occupancy_limit


def connection_between(
    state: EncounterState, from_area: str, to_area: str
) -> ConnectionDefinition | None:
    for connection in state.connections:
        if connection.from_area == from_area and connection.to_area == to_area:
            return connection
        if connection.bidirectional and connection.from_area == to_area and connection.to_area == from_area:
            return connection
    return None


def _connection_allows(state: EncounterState, from_area: str, to_area: str, blocked_tag: str) -> bool:
    if from_area == to_area:
        return True
    connection = connection_between(state, from_area, to_area)
    return connection is not None and blocked_tag not in connection.tags


def has_line_of_effect(state: EncounterState, from_area: str, to_area: str) -> bool:
    return _connection_allows(state, from_area, to_area, "blocked")


def has_line_of_sight(state: EncounterState, from_area: str, to_area: str) -> bool:
    return _connection_allows(state, from_area, to_area, "blocked_sight") and has_line_of_effect(
        state, from_area, to_area
    )


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
    return ActorState(
        actor_id=actor_id,
        name=name,
        team=team,
        template_id=template.id,
        stats=dict(template.stats),
        skills=dict(template.skills),
        hp=max_hp,
        max_hp=max_hp,
        defense=ruleset.core.defense_base + template.stats["speed"],
        stress=ruleset.core.stress.starting if template.stress_mode == "track" else 0,
        shrouds=0,
        status=ActorStatus.NORMAL,
        weapon_id=template.weapon_id,
        resources={str(resource_id): amount for resource_id, amount in template.starting_resources.items()},
        action_ids=tuple(template.actions),
        talent_ids=tuple(template.talents),
        talent_state=TalentState(),
        conditions=(),
        attack_modifiers=(),
        death_mode=template.death_mode,
        stress_mode=template.stress_mode,
        area_id=start_area,
        engaged_with=frozenset(),
    )


def update_actor(state: EncounterState, actor: ActorState) -> EncounterState:
    return replace(state, actors={**state.actors, actor.actor_id: actor})


def append_event(state: EncounterState, message: str) -> EncounterState:
    return replace(state, events=(*state.events, message))


def snapshot_actor(actor: ActorState) -> dict[str, int | str | dict[str, int]]:
    return {
        "hp": actor.hp,
        "status": actor.status.value,
        "stress": actor.stress,
        "shrouds": actor.shrouds,
        "area_id": actor.area_id,
        "resources": dict(actor.resources),
        "ammo": actor.ammo,
        "bandages": actor.bandages,
        "medkits": actor.medkits,
    }


def synchronize_engagements(state: EncounterState) -> EncounterState:
    return replace(
        state,
        actors={
            actor_id: replace(
                actor,
                engaged_with=frozenset(
                    other.actor_id
                    for other in state.actors.values()
                    if other.actor_id != actor_id
                    and other.team != actor.team
                    and other.area_id == actor.area_id
                    and other.status not in _NONACTIVE_STATUSES
                ),
            )
            for actor_id, actor in state.actors.items()
        },
    )
