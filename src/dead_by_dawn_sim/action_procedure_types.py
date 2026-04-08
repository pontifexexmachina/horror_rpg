from __future__ import annotations

from dataclasses import dataclass, replace
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from dead_by_dawn_sim.dice import DiceRoller
    from dead_by_dawn_sim.engine_rolls import ContestResult, RollMode, RollResult
    from dead_by_dawn_sim.rules import ActionDefinition, Ruleset
    from dead_by_dawn_sim.state import ActorState, EncounterState


@dataclass(frozen=True)
class ActionResolutionContext:
    state: EncounterState
    actor: ActorState
    target: ActorState
    action: ActionDefinition
    roller: DiceRoller
    ruleset: Ruleset
    push: bool
    destination_area: str | None
    roll_mode: RollMode

    def with_state(self, state: EncounterState) -> ActionResolutionContext:
        actor = state.actor(self.actor.actor_id)
        target = state.actor(self.target.actor_id)
        return replace(self, state=state, actor=actor, target=target)


@dataclass(frozen=True)
class ProcedureResolution:
    state: EncounterState
    actor: ActorState
    target: ActorState
    last_roll: RollResult | ContestResult | None = None

    @classmethod
    def build(cls, ctx: ActionResolutionContext) -> ProcedureResolution:
        return cls(state=ctx.state, actor=ctx.actor, target=ctx.target)

    def with_state(
        self,
        state: EncounterState,
        *,
        actor_id: str,
        target_id: str,
        last_roll: RollResult | ContestResult | None = None,
    ) -> ProcedureResolution:
        return ProcedureResolution(
            state=state,
            actor=state.actor(actor_id),
            target=state.actor(target_id),
            last_roll=self.last_roll if last_roll is None else last_roll,
        )
