from __future__ import annotations

from typing import TYPE_CHECKING, Literal, NamedTuple

if TYPE_CHECKING:
    from dead_by_dawn_sim.dice import DiceRoller
    from dead_by_dawn_sim.rules import Ruleset


class RollResult(NamedTuple):
    kept: list[int]
    total: int
    is_success: bool
    is_critical: bool


class ContestResult(NamedTuple):
    attacker: RollResult
    defender: RollResult
    is_success: bool
    is_critical: bool


RollMode = Literal["normal", "advantage", "disadvantage"]


def resolve_roll(
    *, raw_rolls: list[int], keep: int, modifier: int, difficulty: int, highest: bool = True
) -> RollResult:
    kept = sorted(raw_rolls, reverse=highest)[:keep]
    total = sum(kept) + modifier
    is_success = total >= difficulty
    is_critical = is_success and len(kept) >= 2 and kept[0] == kept[1]
    return RollResult(kept=kept, total=total, is_success=is_success, is_critical=is_critical)


def difficulty_value(ruleset: Ruleset, difficulty_name: str) -> int:
    return getattr(ruleset.core.difficulties, difficulty_name)


def roll_mode_params(ruleset: Ruleset, roll_mode: RollMode, push: bool) -> tuple[int, int, bool]:
    if roll_mode == "advantage":
        return (ruleset.core.check_dice + 1 + int(push), ruleset.core.keep_dice, True)
    if roll_mode == "disadvantage":
        if push:
            return (ruleset.core.check_dice + 1, ruleset.core.keep_dice, True)
        return (ruleset.core.check_dice + 1, ruleset.core.keep_dice, False)
    return (
        ruleset.core.check_dice + (ruleset.core.push.extra_die if push else 0),
        ruleset.core.push.keep if push else ruleset.core.keep_dice,
        True,
    )


def roll_check(
    *,
    roller: DiceRoller,
    ruleset: Ruleset,
    modifier: int,
    difficulty: int,
    push: bool,
    roll_mode: RollMode = "normal",
) -> RollResult:
    num_dice, keep, highest = roll_mode_params(ruleset, roll_mode, push)
    raw_rolls = roller.roll_d6(num_dice)
    return resolve_roll(
        raw_rolls=raw_rolls,
        keep=keep,
        modifier=modifier,
        difficulty=difficulty,
        highest=highest,
    )


def roll_contest(
    *,
    roller: DiceRoller,
    ruleset: Ruleset,
    attacker_modifier: int,
    defender_modifier: int,
    push: bool,
    roll_mode: RollMode,
) -> ContestResult:
    attacker = roll_check(
        roller=roller,
        ruleset=ruleset,
        modifier=attacker_modifier,
        difficulty=-999,
        push=push,
        roll_mode=roll_mode,
    )
    defender = roll_check(
        roller=roller,
        ruleset=ruleset,
        modifier=defender_modifier,
        difficulty=-999,
        push=False,
        roll_mode="normal",
    )
    is_success = attacker.total > defender.total
    return ContestResult(
        attacker=attacker,
        defender=defender,
        is_success=is_success,
        is_critical=is_success and attacker.is_critical,
    )
