from __future__ import annotations

from dataclasses import dataclass, field, replace
from enum import Enum
from typing import Literal

from dead_by_dawn_sim.rules import ActorTemplate, Ruleset


class RangeBand(str, Enum):
    ENGAGED = "engaged"
    NEAR = "near"
    FAR = "far"


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
    action_ids: tuple[str, ...]
    talent_ids: tuple[str, ...]
    talent_state: TalentState
    conditions: tuple[ConditionState, ...]
    range_band: RangeBand

    @property
    def can_act(self) -> bool:
        return self.status in {ActorStatus.NORMAL, ActorStatus.WOUNDED}


@dataclass(frozen=True)
class EncounterState:
    actors: dict[str, ActorState]
    round_number: int
    initiative_order: tuple[str, ...]
    active_actor_id: str | None
    winner: str | None = None
    events: tuple[str, ...] = field(default_factory=tuple)

    def actor(self, actor_id: str) -> ActorState:
        return self.actors[actor_id]


def build_actor_state(
    actor_id: str,
    team: str,
    template: ActorTemplate,
    ruleset: Ruleset,
    name: str,
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
        action_ids=tuple(template.actions),
        talent_ids=tuple(template.talents),
        talent_state=TalentState(),
        conditions=tuple(),
        range_band=RangeBand(template.starting_band),
    )


def update_actor(state: EncounterState, actor: ActorState) -> EncounterState:
    updated = dict(state.actors)
    updated[actor.actor_id] = actor
    return replace(state, actors=updated)


def append_event(state: EncounterState, message: str) -> EncounterState:
    return replace(state, events=(*state.events, message))
