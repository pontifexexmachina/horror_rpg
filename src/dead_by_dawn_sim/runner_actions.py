from __future__ import annotations

from dead_by_dawn_sim.actions import ActionChoice
from dead_by_dawn_sim.rules import Ruleset, attack_step_for_action


def choice_action_cost(choice: ActionChoice, ruleset: Ruleset) -> int:
    return ruleset.actions[choice.action_id].action_cost


def affordable_actions(
    legal_actions: list[ActionChoice], ruleset: Ruleset, remaining_actions: int
) -> list[ActionChoice]:
    return [
        choice
        for choice in legal_actions
        if choice_action_cost(choice, ruleset) <= remaining_actions
    ]


def is_attack_choice(choice: ActionChoice, ruleset: Ruleset) -> bool:
    return attack_step_for_action(ruleset.actions[choice.action_id]) is not None
