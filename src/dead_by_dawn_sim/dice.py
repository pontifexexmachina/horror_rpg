from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from random import Random


class DiceRoller:
    def roll_d6(self, count: int = 1) -> list[int]:
        raise NotImplementedError


@dataclass
class RandomDiceRoller(DiceRoller):
    rng: Random

    def roll_d6(self, count: int = 1) -> list[int]:
        return [self.rng.randint(1, 6) for _ in range(count)]


@dataclass
class FixedDiceRoller(DiceRoller):
    values: list[int]

    def roll_d6(self, count: int = 1) -> list[int]:
        if len(self.values) < count:
            msg = f"Requested {count} d6 rolls but only {len(self.values)} fixed values remain."
            raise ValueError(msg)
        result = self.values[:count]
        self.values = self.values[count:]
        return result
