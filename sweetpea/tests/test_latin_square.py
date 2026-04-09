"""Tests for Latin Square diagonal counterbalancing."""

import pytest
from sweetpea._internal.primitive import Factor, SimpleLevel
from sweetpea._internal.latin_square import (
    latin_square_diagonals,
    validate_latin_square_balance,
    LatinSquare
)
from sweetpea._internal.main import synthesize_trials, print_experiments
from sweetpea._internal.cross_block import CrossBlock, NestedBlock
from sweetpea._internal.sampling_strategy.iterate import IterateGen


# ---------- helpers

def levels(names):
    return [SimpleLevel(n) for n in names]


# ==========================================================================
# Unit tests: latin_square_diagonals
# ==========================================================================

class TestLatinSquareDiagonals:

    def test_2x2_grid(self):
        """Font={S,B} x Color={R,G} -> 2 diagonals of 2 combos each."""
        font = Factor("Font", levels(["S", "B"]))
        color = Factor("Color", levels(["R", "G"]))

        diags = latin_square_diagonals([font, color])

        assert len(diags) == 2
        # Diagonal 0: (0+0)%2=0, (1+1)%2=0 -> (S,R), (B,G)
        assert set(diags[0]) == {("S", "R"), ("B", "G")}
        # Diagonal 1: (0+1)%2=1, (1+0)%2=1 -> (S,G), (B,R)
        assert set(diags[1]) == {("S", "G"), ("B", "R")}

    def test_3x3_grid(self):
        """Font={S,M,B} x Color={R,G,Bu} -> 3 diagonals of 3 combos each."""
        font = Factor("Font", levels(["S", "M", "B"]))
        color = Factor("Color", levels(["R", "G", "Bu"]))

        diags = latin_square_diagonals([font, color])

        assert len(diags) == 3

        # Each diagonal should have exactly 3 combos
        for d in range(3):
            assert len(diags[d]) == 3

        # Diagonal 0: (0+0)%3=0, (1+2)%3=0, (2+1)%3=0 -> (S,R), (M,Bu), (B,G)
        assert set(diags[0]) == {("S", "R"), ("M", "Bu"), ("B", "G")}
        # Diagonal 1: (0+1)%3=1, (1+0)%3=1, (2+2)%3=1 -> (S,G), (M,R), (B,Bu)
        assert set(diags[1]) == {("S", "G"), ("M", "R"), ("B", "Bu")}
        # Diagonal 2: (0+2)%3=2, (1+1)%3=2, (2+0)%3=2 -> (S,Bu), (M,G), (B,R)
        assert set(diags[2]) == {("S", "Bu"), ("M", "G"), ("B", "R")}

    def test_rectangular_2x3(self):
        """Font={S,B} x Color={R,G,Bu} -> 3 diagonals (D=max(2,3)=3)."""
        font = Factor("Font", levels(["S", "B"]))
        color = Factor("Color", levels(["R", "G", "Bu"]))

        diags = latin_square_diagonals([font, color])

        # D = max(2, 3) = 3 diagonals
        assert len(diags) == 3

        # Total combos = 2*3 = 6, split across 3 diagonals = 2 each
        total = sum(len(v) for v in diags.values())
        assert total == 6
        for d in range(3):
            assert len(diags[d]) == 2

    def test_single_factor(self):
        """Single factor: each level is its own diagonal."""
        task = Factor("Task", levels(["Rd", "Wr", "Sp"]))

        diags = latin_square_diagonals([task])

        # D = max(3) = 3, each level is index i, diagonal = i%3
        assert len(diags) == 3
        assert diags[0] == [("Rd",)]
        assert diags[1] == [("Wr",)]
        assert diags[2] == [("Sp",)]

    def test_three_factors(self):
        """Three outer factors: A(2) x B(2) x C(2) -> D=2, 4 combos each."""
        A = Factor("A", levels(["a1", "a2"]))
        B = Factor("B", levels(["b1", "b2"]))
        C = Factor("C", levels(["c1", "c2"]))

        diags = latin_square_diagonals([A, B, C])

        assert len(diags) == 2
        # 2*2*2 = 8 combos total, 4 per diagonal
        assert len(diags[0]) == 4
        assert len(diags[1]) == 4

        # Diagonal 0: sum of indices is even
        # (0,0,0)=0, (0,1,1)=2, (1,0,1)=2, (1,1,0)=2 -> all %2=0
        assert set(diags[0]) == {
            ("a1", "b1", "c1"),  # 0+0+0=0
            ("a1", "b2", "c2"),  # 0+1+1=2
            ("a2", "b1", "c2"),  # 1+0+1=2
            ("a2", "b2", "c1"),  # 1+1+0=2
        }

    def test_custom_num_diagonals(self):
        """Override default D with custom num_diagonals."""
        font = Factor("Font", levels(["S", "B"]))
        color = Factor("Color", levels(["R", "G"]))

        # Use D=4 instead of default D=2
        diags = latin_square_diagonals([font, color], num_diagonals=4)

        assert len(diags) == 4
        # Some diagonals may be empty since 2*2=4 combos across 4 diags
        total = sum(len(v) for v in diags.values())
        assert total == 4

    def test_empty_factors_raises(self):
        """Empty outer_factors list should raise ValueError."""
        with pytest.raises(ValueError, match="outer_factors must not be empty"):
            latin_square_diagonals([])

    def test_invalid_num_diagonals_raises(self):
        """num_diagonals < 1 should raise ValueError."""
        font = Factor("Font", levels(["S", "B"]))
        with pytest.raises(ValueError, match="num_diagonals must be at least 1"):
            latin_square_diagonals([font], num_diagonals=0)


# ==========================================================================
# Unit tests: validate_latin_square_balance
# ==========================================================================

class TestValidateBalance:

    def test_square_grid_balanced(self):
        """2x2 grid is perfectly balanced — no warnings."""
        font = Factor("Font", levels(["S", "B"]))
        color = Factor("Color", levels(["R", "G"]))

        diags = latin_square_diagonals([font, color])
        warnings = validate_latin_square_balance(diags, [font, color])

        assert warnings == []

    def test_3x3_grid_balanced(self):
        """3x3 grid is perfectly balanced — no warnings."""
        font = Factor("Font", levels(["S", "M", "B"]))
        color = Factor("Color", levels(["R", "G", "Bu"]))

        diags = latin_square_diagonals([font, color])
        warnings = validate_latin_square_balance(diags, [font, color])

        assert warnings == []

    def test_rectangular_grid_warns(self):
        """2x3 grid has imbalanced diagonals — should produce warnings."""
        font = Factor("Font", levels(["S", "B"]))
        color = Factor("Color", levels(["R", "G", "Bu"]))

        diags = latin_square_diagonals([font, color])
        warnings = validate_latin_square_balance(diags, [font, color])

        # Some diagonals will be missing Color levels
        assert len(warnings) > 0


# ==========================================================================
# Unit tests: LatinSquare constraint class
# ==========================================================================

class TestLatinSquareConstraint:

    def test_properties(self):
        """LatinSquare exposes num_participants and diagonals."""
        font = Factor("Font", levels(["S", "B"]))
        color = Factor("Color", levels(["R", "G"]))

        ls = LatinSquare(outer_factors=[font, color])

        assert ls.num_participants == 2
        assert len(ls.diagonals) == 2
        assert set(ls.diagonals[0]) == {("S", "R"), ("B", "G")}
        assert set(ls.diagonals[1]) == {("S", "G"), ("B", "R")}

    def test_diagonal_combos(self):
        """diagonal_combos returns correct combos for each participant."""
        font = Factor("Font", levels(["S", "B"]))
        color = Factor("Color", levels(["R", "G"]))

        ls = LatinSquare(outer_factors=[font, color])

        assert set(map(tuple, ls.diagonal_combos(0))) == {("S", "R"), ("B", "G")}
        assert set(map(tuple, ls.diagonal_combos(1))) == {("S", "G"), ("B", "R")}

    def test_diagonal_combos_wraps(self):
        """Participant IDs >= num_participants wrap cyclically."""
        font = Factor("Font", levels(["S", "B"]))
        color = Factor("Color", levels(["R", "G"]))

        ls = LatinSquare(outer_factors=[font, color])

        # ID 2 should wrap to diagonal 0
        assert ls.diagonal_combos(2) == ls.diagonal_combos(0)
        assert ls.diagonal_combos(3) == ls.diagonal_combos(1)

    def test_participant_for_trial(self):
        """participant_for_trial maps trial combos to correct participant IDs."""
        font = Factor("Font", levels(["S", "B"]))
        color = Factor("Color", levels(["R", "G"]))

        ls = LatinSquare(outer_factors=[font, color])

        # Mock experiment dict
        exp = {
            "Font": ["S", "B", "S", "B"],
            "Color": ["R", "G", "G", "R"],
            "Task": ["Rd", "Wr", "Rd", "Wr"],
        }

        # SR and BG are diagonal 0; SG and BR are diagonal 1
        assert ls.participant_for_trial(exp, 0) == 0  # S,R
        assert ls.participant_for_trial(exp, 1) == 0  # B,G
        assert ls.participant_for_trial(exp, 2) == 1  # S,G
        assert ls.participant_for_trial(exp, 3) == 1  # B,R

    def test_constraint_noop(self):
        """Constraint ABC methods are no-ops."""
        font = Factor("Font", levels(["S", "B"]))
        ls = LatinSquare(outer_factors=[font])

        # These should not raise
        ls.validate(None)
        ls.apply(None, None)
        assert ls.potential_sample_conforms(None, None) is True
        assert ls.desugar({}) == [ls]


# ==========================================================================
# Integration tests: synthesize_trials with participants parameter
# ==========================================================================

class TestLatinSquareIntegration:

    def test_2x2_basic(self):
        """2x2 Latin Square: 2 participants, each gets 8 trials (2 blocks x 4 inner)."""
        font = Factor("Font", levels(["S", "B"]))
        color = Factor("Color", levels(["R", "G"]))
        task = Factor("Task", levels(["Rd", "Wr"]))
        speed = Factor("Speed", levels(["F", "Sl"]))

        ls = LatinSquare(outer_factors=[font, color])
        inner = CrossBlock([task, speed], [task, speed], [])

        nb = NestedBlock(
            design=[font, color, inner],
            crossing=[font, color],
            constraints=[ls]
        )

        results = synthesize_trials(nb, 1, sampling_strategy=IterateGen,
                                    participants=[0, 1])

        # Should return a dict with 2 participants
        assert isinstance(results, dict)
        assert len(results) == 2
        assert 0 in results
        assert 1 in results

        for pid in [0, 1]:
            assert len(results[pid]) == 1  # 1 sample
            exp = results[pid][0]

            # Should have all 4 factor columns
            assert "Font" in exp
            assert "Color" in exp
            assert "Task" in exp
            assert "Speed" in exp
            # Should NOT have the internal condition factor
            assert "_ls_condition" not in exp

            # 2 blocks x 4 inner trials = 8 trials total
            assert len(exp["Font"]) == 8

        # Collect outer combos per participant
        p0_combos = set()
        exp0 = results[0][0]
        for i in range(len(exp0["Font"])):
            p0_combos.add((exp0["Font"][i], exp0["Color"][i]))

        p1_combos = set()
        exp1 = results[1][0]
        for i in range(len(exp1["Font"])):
            p1_combos.add((exp1["Font"][i], exp1["Color"][i]))

        # Each participant has exactly 2 unique outer combos
        assert len(p0_combos) == 2
        assert len(p1_combos) == 2

        # No overlap between participants
        assert p0_combos.isdisjoint(p1_combos)

        # Together they cover all 4 combos
        assert p0_combos | p1_combos == {
            ("S", "R"), ("S", "G"), ("B", "R"), ("B", "G")
        }

    def test_2x2_inner_crossing_complete(self):
        """Verify inner factors are fully crossed within each block."""
        font = Factor("Font", levels(["S", "B"]))
        color = Factor("Color", levels(["R", "G"]))
        task = Factor("Task", levels(["Rd", "Wr"]))
        speed = Factor("Speed", levels(["F", "Sl"]))

        ls = LatinSquare(outer_factors=[font, color])
        inner = CrossBlock([task, speed], [task, speed], [])

        nb = NestedBlock(
            design=[font, color, inner],
            crossing=[font, color],
            constraints=[ls]
        )

        results = synthesize_trials(nb, 1, sampling_strategy=IterateGen,
                                    participants=[0, 1])

        for pid in [0, 1]:
            exp = results[pid][0]

            # Get the unique outer combos for this participant
            outer_combos = set()
            for i in range(len(exp["Font"])):
                outer_combos.add((exp["Font"][i], exp["Color"][i]))

            # For each outer combo (block), check inner crossing is complete
            for oc in outer_combos:
                block_trials = []
                for i in range(len(exp["Font"])):
                    if (exp["Font"][i], exp["Color"][i]) == oc:
                        block_trials.append((exp["Task"][i], exp["Speed"][i]))

                # Should have 4 inner trials (2x2 crossing)
                assert len(block_trials) == 4

                # All 4 inner combos should be present
                inner_combos = set(block_trials)
                assert inner_combos == {
                    ("Rd", "F"), ("Rd", "Sl"), ("Wr", "F"), ("Wr", "Sl")
                }

    def test_3x3_structure(self):
        """3x3 Latin Square: 3 participants, 3 blocks each, 12 trials each."""
        font = Factor("Font", levels(["S", "M", "B"]))
        color = Factor("Color", levels(["R", "G", "Bu"]))
        task = Factor("Task", levels(["Rd", "Wr"]))
        speed = Factor("Speed", levels(["F", "Sl"]))

        ls = LatinSquare(outer_factors=[font, color])
        inner = CrossBlock([task, speed], [task, speed], [])

        nb = NestedBlock(
            design=[font, color, inner],
            crossing=[font, color],
            constraints=[ls]
        )

        results = synthesize_trials(nb, 1, sampling_strategy=IterateGen,
                                    participants=[0, 1, 2])

        assert len(results) == 3

        all_combos = set()
        for pid in range(3):
            exp = results[pid][0]

            # 3 blocks x 4 inner trials = 12 trials
            assert len(exp["Font"]) == 12

            # Collect outer combos
            p_combos = set()
            for i in range(len(exp["Font"])):
                p_combos.add((exp["Font"][i], exp["Color"][i]))

            # Each participant should see exactly 3 outer combos
            assert len(p_combos) == 3

            # Each combo has all Font levels and all Color levels
            fonts_seen = {c[0] for c in p_combos}
            colors_seen = {c[1] for c in p_combos}
            assert fonts_seen == {"S", "M", "B"}
            assert colors_seen == {"R", "G", "Bu"}

            all_combos |= p_combos

        # All 9 combos covered across participants
        assert len(all_combos) == 9

    def test_without_participants_defaults_to_all(self):
        """Without participants param, LatinSquare defaults to all participants."""
        font = Factor("Font", levels(["S", "B"]))
        color = Factor("Color", levels(["R", "G"]))
        task = Factor("Task", levels(["Rd", "Wr"]))
        speed = Factor("Speed", levels(["F", "Sl"]))

        ls = LatinSquare(outer_factors=[font, color])
        inner = CrossBlock([task, speed], [task, speed], [])

        nb = NestedBlock(
            design=[font, color, inner],
            crossing=[font, color],
            constraints=[ls]
        )

        # Call without participants — should default to all participants
        results = synthesize_trials(nb, 1, sampling_strategy=IterateGen)

        # Should return Dict[int, List[dict]] with all participants
        assert isinstance(results, dict)
        assert len(results) == 2
        assert 0 in results
        assert 1 in results

        # Each participant gets 8 trials (2 blocks x 4 inner)
        for pid in [0, 1]:
            assert len(results[pid][0]["Font"]) == 8

    def test_single_participant(self):
        """Request only one participant — only that participant's block is solved."""
        font = Factor("Font", levels(["S", "B"]))
        color = Factor("Color", levels(["R", "G"]))
        task = Factor("Task", levels(["Rd", "Wr"]))
        speed = Factor("Speed", levels(["F", "Sl"]))

        ls = LatinSquare(outer_factors=[font, color])
        inner = CrossBlock([task, speed], [task, speed], [])

        nb = NestedBlock(
            design=[font, color, inner],
            crossing=[font, color],
            constraints=[ls]
        )

        results = synthesize_trials(nb, 1, sampling_strategy=IterateGen,
                                    participants=[0])

        assert isinstance(results, dict)
        assert list(results.keys()) == [0]
        assert len(results[0][0]["Font"]) == 8

    def test_cyclical_participant_wrapping(self):
        """Participant ID 2 in a 2x2 grid wraps to diagonal 0."""
        font = Factor("Font", levels(["S", "B"]))
        color = Factor("Color", levels(["R", "G"]))
        task = Factor("Task", levels(["Rd", "Wr"]))
        speed = Factor("Speed", levels(["F", "Sl"]))

        ls = LatinSquare(outer_factors=[font, color])
        inner = CrossBlock([task, speed], [task, speed], [])

        nb = NestedBlock(
            design=[font, color, inner],
            crossing=[font, color],
            constraints=[ls]
        )

        results = synthesize_trials(nb, 1, sampling_strategy=IterateGen,
                                    participants=[2])

        # Participant 2 wraps to diagonal 0 (same combos as participant 0)
        exp = results[2][0]
        combos = set()
        for i in range(len(exp["Font"])):
            combos.add((exp["Font"][i], exp["Color"][i]))

        # Diagonal 0 combos: SR, BG
        assert combos == {("S", "R"), ("B", "G")}

    def test_print_experiments_dict_input(self, capsys):
        """print_experiments auto-detects Dict input and labels by participant."""
        font = Factor("Font", levels(["S", "B"]))
        color = Factor("Color", levels(["R", "G"]))
        task = Factor("Task", levels(["Rd", "Wr"]))
        speed = Factor("Speed", levels(["F", "Sl"]))

        ls = LatinSquare(outer_factors=[font, color])
        inner = CrossBlock([task, speed], [task, speed], [])

        nb = NestedBlock(
            design=[font, color, inner],
            crossing=[font, color],
            constraints=[ls]
        )

        results = synthesize_trials(nb, 1, sampling_strategy=IterateGen,
                                    participants=[0, 1])

        print_experiments(nb, results)
        output = capsys.readouterr().out

        assert "Participant 0" in output
        assert "Participant 1" in output

    def test_no_latin_square_raises(self):
        """Using participants without LatinSquare constraint raises ValueError."""
        font = Factor("Font", levels(["S", "B"]))
        color = Factor("Color", levels(["R", "G"]))
        task = Factor("Task", levels(["Rd", "Wr"]))
        speed = Factor("Speed", levels(["F", "Sl"]))

        inner = CrossBlock([task, speed], [task, speed], [])

        nb = NestedBlock(
            design=[font, color, inner],
            crossing=[font, color],
            constraints=[]
        )

        with pytest.raises(ValueError, match="LatinSquare constraint"):
            synthesize_trials(nb, 1, sampling_strategy=IterateGen,
                              participants=[0])
