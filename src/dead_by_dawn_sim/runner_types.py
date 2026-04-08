from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ActorMetadata:
    actor_id: str
    team: str
    name: str
    template_id: str
    policy_id: str


@dataclass(frozen=True)
class ContributionStats:
    actions_taken: int = 0
    pushes_used: int = 0
    damage_dealt: int = 0
    healing_done: int = 0
    stress_inflicted: int = 0
    control_applied: int = 0
    enemy_wounded: int = 0
    enemy_critical: int = 0
    enemy_dead: int = 0
    enemy_broken: int = 0


@dataclass(frozen=True)
class EncounterResult:
    scenario_id: str
    seed: int
    winner: str
    rounds: int
    actor_metadata: dict[str, ActorMetadata]
    actor_snapshots: dict[str, dict[str, int | str | dict[str, int]]]
    actor_contributions: dict[str, ContributionStats]
    action_counts: dict[str, int]
    push_count: int
    events: tuple[str, ...]
