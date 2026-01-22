"""Dice rolling utilities with standard notation support."""

import random
import re
from dataclasses import dataclass
from typing import Optional


@dataclass
class RollResult:
    """Result of a dice roll."""

    notation: str  # Original notation (e.g., "2d6+3")
    rolls: list[int]  # Individual die results
    modifier: int  # Modifier applied
    total: int  # Final total
    details: str  # Human-readable breakdown


class DiceRoller:
    """Handles dice rolling with standard notation."""

    def __init__(self, seed: Optional[int] = None):
        """Initialize dice roller.

        Args:
            seed: Optional seed for reproducible rolls (useful for testing)
        """
        if seed is not None:
            random.seed(seed)

    def roll(self, notation: str) -> RollResult:
        """Roll dice using standard notation.

        Supported formats:
        - "d20" - Roll single d20
        - "2d6" - Roll 2 six-sided dice
        - "3d8+5" - Roll 3d8 and add 5
        - "1d20-2" - Roll d20 and subtract 2
        - "4d6kh3" - Roll 4d6, keep highest 3 (for ability scores)

        Args:
            notation: Dice notation string

        Returns:
            RollResult with rolls and total

        Raises:
            ValueError: If notation is invalid
        """
        parsed = parse_dice_notation(notation)
        if not parsed:
            raise ValueError(f"Invalid dice notation: {notation}")

        num_dice, die_size, modifier, keep_highest = parsed

        # Roll all dice
        rolls = [random.randint(1, die_size) for _ in range(num_dice)]

        # Handle keep highest
        kept_rolls = rolls
        if keep_highest is not None and keep_highest < num_dice:
            sorted_rolls = sorted(rolls, reverse=True)
            kept_rolls = sorted_rolls[:keep_highest]

        # Calculate total
        total = sum(kept_rolls) + modifier

        # Build details string
        if keep_highest is not None and keep_highest < num_dice:
            details = (
                f"Rolled {num_dice}d{die_size}: [{', '.join(map(str, rolls))}], "
                f"kept highest {keep_highest}: [{', '.join(map(str, kept_rolls))}]"
            )
        else:
            details = f"Rolled {num_dice}d{die_size}: [{', '.join(map(str, rolls))}]"

        if modifier != 0:
            details += f" {'+' if modifier > 0 else ''}{modifier}"

        details += f" = {total}"

        return RollResult(
            notation=notation,
            rolls=rolls,
            modifier=modifier,
            total=total,
            details=details,
        )

    def roll_multiple(self, notation: str, count: int) -> list[RollResult]:
        """Roll the same dice notation multiple times.

        Args:
            notation: Dice notation string
            count: Number of times to roll

        Returns:
            List of RollResults
        """
        return [self.roll(notation) for _ in range(count)]

    def advantage(self, notation: str = "d20") -> RollResult:
        """Roll with advantage (roll twice, keep higher).

        Args:
            notation: Dice notation (default d20)

        Returns:
            RollResult with advantage
        """
        roll1 = self.roll(notation)
        roll2 = self.roll(notation)

        better_roll = roll1 if roll1.total >= roll2.total else roll2
        worse_roll = roll2 if better_roll == roll1 else roll1

        # Create new result with combined details
        details = (
            f"Advantage: {better_roll.total} (kept) vs {worse_roll.total} (discarded)\n"
            f"Kept: {better_roll.details}"
        )

        return RollResult(
            notation=f"{notation} (advantage)",
            rolls=better_roll.rolls,
            modifier=better_roll.modifier,
            total=better_roll.total,
            details=details,
        )

    def disadvantage(self, notation: str = "d20") -> RollResult:
        """Roll with disadvantage (roll twice, keep lower).

        Args:
            notation: Dice notation (default d20)

        Returns:
            RollResult with disadvantage
        """
        roll1 = self.roll(notation)
        roll2 = self.roll(notation)

        worse_roll = roll1 if roll1.total <= roll2.total else roll2
        better_roll = roll2 if worse_roll == roll1 else roll1

        # Create new result with combined details
        details = (
            f"Disadvantage: {worse_roll.total} (kept) vs {better_roll.total} (discarded)\n"
            f"Kept: {worse_roll.details}"
        )

        return RollResult(
            notation=f"{notation} (disadvantage)",
            rolls=worse_roll.rolls,
            modifier=worse_roll.modifier,
            total=worse_roll.total,
            details=details,
        )


def parse_dice_notation(notation: str) -> Optional[tuple[int, int, int, Optional[int]]]:
    """Parse dice notation string into components.

    Args:
        notation: Dice notation (e.g., "2d6+3", "1d20", "4d6kh3")

    Returns:
        Tuple of (num_dice, die_size, modifier, keep_highest) or None if invalid
    """
    notation = notation.strip().lower().replace(" ", "")

    # Handle keep highest (e.g., "4d6kh3")
    keep_highest = None
    if "kh" in notation:
        match = re.match(r"(\d*)d(\d+)kh(\d+)([+-]\d+)?", notation)
        if match:
            num_dice = int(match.group(1) or "1")
            die_size = int(match.group(2))
            keep_highest = int(match.group(3))
            modifier = int(match.group(4) or "0")
            return (num_dice, die_size, modifier, keep_highest)
        return None

    # Standard notation (e.g., "2d6+3", "d20-1")
    match = re.match(r"(\d*)d(\d+)([+-]\d+)?", notation)
    if not match:
        return None

    num_dice = int(match.group(1) or "1")
    die_size = int(match.group(2))
    modifier = int(match.group(3) or "0")

    return (num_dice, die_size, modifier, keep_highest)
