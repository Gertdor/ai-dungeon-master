"""Tests for dice rolling utilities."""

import pytest

from rpg_dm.utilities.dice import DiceRoller, RollResult, parse_dice_notation


class TestDiceNotationParsing:
    """Tests for dice notation parsing."""

    def test_parse_simple_d20(self):
        """Test parsing simple d20."""
        result = parse_dice_notation("d20")
        assert result == (1, 20, 0, None)

    def test_parse_multiple_dice(self):
        """Test parsing multiple dice."""
        result = parse_dice_notation("2d6")
        assert result == (2, 6, 0, None)

    def test_parse_with_positive_modifier(self):
        """Test parsing with positive modifier."""
        result = parse_dice_notation("1d20+5")
        assert result == (1, 20, 5, None)

    def test_parse_with_negative_modifier(self):
        """Test parsing with negative modifier."""
        result = parse_dice_notation("2d8-3")
        assert result == (2, 8, -3, None)

    def test_parse_keep_highest(self):
        """Test parsing keep highest notation."""
        result = parse_dice_notation("4d6kh3")
        assert result == (4, 6, 0, 3)

    def test_parse_keep_highest_with_modifier(self):
        """Test parsing keep highest with modifier."""
        result = parse_dice_notation("4d6kh3+2")
        assert result == (4, 6, 2, 3)

    def test_parse_arbitrary_dice_sizes(self):
        """Test parsing arbitrary dice sizes."""
        assert parse_dice_notation("d3") == (1, 3, 0, None)
        assert parse_dice_notation("d25") == (1, 25, 0, None)
        assert parse_dice_notation("2d100") == (2, 100, 0, None)
        assert parse_dice_notation("3d7") == (3, 7, 0, None)

    def test_parse_case_insensitive(self):
        """Test parsing is case insensitive."""
        result = parse_dice_notation("2D6+3")
        assert result == (2, 6, 3, None)

    def test_parse_with_whitespace(self):
        """Test parsing handles whitespace."""
        result = parse_dice_notation(" 2d6 + 3 ")
        assert result == (2, 6, 3, None)

    def test_parse_invalid_notation(self):
        """Test parsing invalid notation."""
        assert parse_dice_notation("invalid") is None
        assert parse_dice_notation("2x6") is None
        assert parse_dice_notation("d") is None
        assert parse_dice_notation("") is None


class TestDiceRoller:
    """Tests for dice roller."""

    def test_roll_d20(self):
        """Test rolling a d20."""
        roller = DiceRoller(seed=42)
        result = roller.roll("d20")

        assert result.notation == "d20"
        assert len(result.rolls) == 1
        assert 1 <= result.rolls[0] <= 20
        assert result.modifier == 0
        assert result.total == result.rolls[0]
        assert "d20" in result.details

    def test_roll_multiple_dice(self):
        """Test rolling multiple dice."""
        roller = DiceRoller(seed=42)
        result = roller.roll("3d6")

        assert result.notation == "3d6"
        assert len(result.rolls) == 3
        assert all(1 <= r <= 6 for r in result.rolls)
        assert result.modifier == 0
        assert result.total == sum(result.rolls)

    def test_roll_with_positive_modifier(self):
        """Test rolling with positive modifier."""
        roller = DiceRoller(seed=42)
        result = roller.roll("1d20+5")

        assert result.modifier == 5
        assert result.total == result.rolls[0] + 5
        assert "+5" in result.details

    def test_roll_with_negative_modifier(self):
        """Test rolling with negative modifier."""
        roller = DiceRoller(seed=42)
        result = roller.roll("2d6-2")

        assert result.modifier == -2
        assert result.total == sum(result.rolls) - 2
        assert "-2" in result.details

    def test_roll_keep_highest(self):
        """Test rolling with keep highest."""
        roller = DiceRoller(seed=42)
        result = roller.roll("4d6kh3")

        assert len(result.rolls) == 4
        assert all(1 <= r <= 6 for r in result.rolls)
        # Total should be sum of 3 highest
        expected_total = sum(sorted(result.rolls, reverse=True)[:3])
        assert result.total == expected_total
        assert "kept highest 3" in result.details

    def test_roll_arbitrary_dice_d3(self):
        """Test rolling arbitrary dice size d3."""
        roller = DiceRoller(seed=42)
        # Roll multiple times to check range
        for _ in range(20):
            result = roller.roll("d3")
            assert len(result.rolls) == 1
            assert 1 <= result.rolls[0] <= 3
            assert result.total == result.rolls[0]

    def test_roll_arbitrary_dice_d25(self):
        """Test rolling arbitrary dice size d25."""
        roller = DiceRoller(seed=42)
        result = roller.roll("d25")

        assert len(result.rolls) == 1
        assert 1 <= result.rolls[0] <= 25
        assert result.total == result.rolls[0]

    def test_roll_arbitrary_dice_d100(self):
        """Test rolling d100 (percentile)."""
        roller = DiceRoller(seed=42)
        result = roller.roll("d100")

        assert len(result.rolls) == 1
        assert 1 <= result.rolls[0] <= 100
        assert result.total == result.rolls[0]

    def test_roll_arbitrary_dice_d7(self):
        """Test rolling unusual dice size d7."""
        roller = DiceRoller(seed=42)
        result = roller.roll("2d7+3")

        assert len(result.rolls) == 2
        assert all(1 <= r <= 7 for r in result.rolls)
        assert result.modifier == 3
        assert result.total == sum(result.rolls) + 3

    def test_roll_invalid_notation(self):
        """Test rolling with invalid notation."""
        roller = DiceRoller()
        with pytest.raises(ValueError, match="Invalid dice notation"):
            roller.roll("invalid")

    def test_roll_multiple(self):
        """Test rolling multiple times."""
        roller = DiceRoller(seed=42)
        results = roller.roll_multiple("d20", 3)

        assert len(results) == 3
        assert all(isinstance(r, RollResult) for r in results)
        assert all(r.notation == "d20" for r in results)

    def test_advantage(self):
        """Test rolling with advantage."""
        roller = DiceRoller(seed=42)
        result = roller.advantage("d20")

        assert "(advantage)" in result.notation
        assert len(result.rolls) == 1
        assert 1 <= result.total <= 20
        assert "Advantage:" in result.details
        assert "kept" in result.details
        assert "discarded" in result.details

    def test_advantage_with_arbitrary_dice(self):
        """Test advantage works with arbitrary dice."""
        roller = DiceRoller(seed=42)
        result = roller.advantage("d25")

        assert "(advantage)" in result.notation
        assert 1 <= result.total <= 25

    def test_disadvantage(self):
        """Test rolling with disadvantage."""
        roller = DiceRoller(seed=42)
        result = roller.disadvantage("d20")

        assert "(disadvantage)" in result.notation
        assert len(result.rolls) == 1
        assert 1 <= result.total <= 20
        assert "Disadvantage:" in result.details
        assert "kept" in result.details
        assert "discarded" in result.details

    def test_disadvantage_with_arbitrary_dice(self):
        """Test disadvantage works with arbitrary dice."""
        roller = DiceRoller(seed=42)
        result = roller.disadvantage("d12")

        assert "(disadvantage)" in result.notation
        assert 1 <= result.total <= 12

    def test_seeded_rolls_are_reproducible(self):
        """Test that seeded rolls are reproducible."""
        roller1 = DiceRoller(seed=12345)
        result1 = roller1.roll("3d6+2")

        roller2 = DiceRoller(seed=12345)
        result2 = roller2.roll("3d6+2")

        assert result1.rolls == result2.rolls
        assert result1.total == result2.total


class TestRollResult:
    """Tests for RollResult dataclass."""

    def test_roll_result_creation(self):
        """Test creating a RollResult."""
        result = RollResult(
            notation="2d6+3",
            rolls=[4, 5],
            modifier=3,
            total=12,
            details="Rolled 2d6: [4, 5] +3 = 12",
        )

        assert result.notation == "2d6+3"
        assert result.rolls == [4, 5]
        assert result.modifier == 3
        assert result.total == 12
        assert result.details == "Rolled 2d6: [4, 5] +3 = 12"


class TestEdgeCases:
    """Tests for edge cases."""

    def test_roll_single_d1(self):
        """Test rolling a d1 (always returns 1)."""
        roller = DiceRoller()
        result = roller.roll("d1")

        assert result.rolls == [1]
        assert result.total == 1

    def test_roll_many_dice(self):
        """Test rolling many dice at once."""
        roller = DiceRoller(seed=42)
        result = roller.roll("10d10")

        assert len(result.rolls) == 10
        assert all(1 <= r <= 10 for r in result.rolls)
        assert result.total == sum(result.rolls)

    def test_roll_with_large_modifier(self):
        """Test rolling with large modifier."""
        roller = DiceRoller(seed=42)
        result = roller.roll("d20+100")

        assert result.modifier == 100
        assert result.total == result.rolls[0] + 100

    def test_keep_highest_keeps_all(self):
        """Test keep highest when keeping all dice."""
        roller = DiceRoller(seed=42)
        result = roller.roll("3d6kh3")

        assert len(result.rolls) == 3
        assert result.total == sum(result.rolls)

    def test_keep_highest_keeps_one(self):
        """Test keep highest keeping only one die."""
        roller = DiceRoller(seed=42)
        result = roller.roll("4d6kh1")

        assert len(result.rolls) == 4
        assert result.total == max(result.rolls)
        assert "kept highest 1" in result.details
