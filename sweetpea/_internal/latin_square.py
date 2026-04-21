"""Latin Square diagonal computation and validation for SweetPea.

Provides utilities for partitioning outer factor combinations into
Latin Square diagonals, where each diagonal is assigned to a different
participant for counterbalanced experimental designs.

Diagonal assignment uses: diagonal = (i1 + i2 + ...) % D
where i1, i2, ... are level indices and D = max(level counts).
"""

from itertools import product as iter_product
from typing import List, Dict, Tuple, Optional

from sweetpea._internal.base_constraint import Constraint


def latin_square_diagonals(outer_factors, num_diagonals=None):
    """Compute Latin Square diagonal assignments for outer factor combinations.

    For factors with level counts N1, N2, ..., assigns each combination an
    index tuple (i1, i2, ...) and computes::

        diagonal = (i1 + i2 + ...) % D

    where D = ``num_diagonals`` or ``max(N1, N2, ...)``.

    :param outer_factors:
        :class:`list` of :class:`.Factor` objects forming the outer grid.

    :param num_diagonals:
        Number of diagonals to create. Defaults to ``max`` of all factor
        level counts.

    :returns:
        A :class:`dict` mapping diagonal ID (:class:`int`) to a :class:`list`
        of combo :class:`tuples <tuple>`. Each combo tuple contains
        ``(level_name_1, level_name_2, ...)``.

    Example::

        >>> diags = latin_square_diagonals([font, color])
        {0: [('S', 'R'), ('B', 'G')],
         1: [('S', 'G'), ('B', 'R')]}
    """
    if not outer_factors:
        raise ValueError("outer_factors must not be empty")

    level_counts = [len(f.levels) for f in outer_factors]

    if any(n < 1 for n in level_counts):
        raise ValueError("All outer factors must have at least one level")

    D = num_diagonals if num_diagonals is not None else max(level_counts)

    if D < 1:
        raise ValueError("num_diagonals must be at least 1")

    # Build index ranges for each factor
    index_ranges = [range(n) for n in level_counts]

    # Compute diagonal assignment for each combo
    diagonals = {d: [] for d in range(D)}

    for indices in iter_product(*index_ranges):
        diagonal = sum(indices) % D
        combo = tuple(outer_factors[f_idx].levels[i].name
                      for f_idx, i in enumerate(indices))
        diagonals[diagonal].append(combo)

    return diagonals


def validate_latin_square_balance(diagonals, outer_factors):
    """Check if diagonals have balanced coverage of all factor levels.

    For a square grid (all factors have the same number of levels), each
    diagonal contains exactly one level of each factor. For rectangular
    grids, some levels may be missing from some diagonals.

    :param diagonals:
        A :class:`dict` returned by :func:`latin_square_diagonals`.

    :param outer_factors:
        :class:`list` of :class:`.Factor` objects.

    :returns:
        A :class:`list` of warning strings (empty if perfectly balanced).
    """
    warnings_list = []

    for d_id, combos in sorted(diagonals.items()):
        for f_idx, factor in enumerate(outer_factors):
            all_levels = {level.name for level in factor.levels}
            present_levels = {combo[f_idx] for combo in combos}
            missing = all_levels - present_levels
            if missing:
                warnings_list.append(
                    f"Diagonal {d_id}: factor '{factor.name}' is missing "
                    f"levels {missing}"
                )

    return warnings_list


class LatinSquare(Constraint):
    """Latin Square counterbalancing constraint for :class:`.NestedBlock` designs.

    Computes Latin Square diagonals from outer factors and stores the
    diagonal-to-participant mapping. When used with :func:`.synthesize_trials`
    and a ``participants`` list, builds per-participant
    :class:`NestedBlocks <.NestedBlock>` with only that participant's diagonal
    combos, saving computation by not solving for all outer combos.

    :param outer_factors:
        :class:`list` of :class:`.Factor` objects forming the outer grid.

    :param num_diagonals:
        Number of diagonals (participants). Defaults to ``max`` of all factor
        level counts.

    Example::

        >>> ls = LatinSquare(outer_factors=[font, color])
        >>> nb = NestedBlock(
        ...     design=[font, color, inner],
        ...     crossing=[font, color],
        ...     constraints=[ls]
        ... )
        >>> results = synthesize_trials(nb, 1, participants=[0, 1])
        >>> print_experiments(nb, results)
    """

    def __init__(self, outer_factors, num_diagonals=None):
        self.outer_factors = outer_factors
        self._diagonals = latin_square_diagonals(outer_factors, num_diagonals)
        # Print balance warnings at construction
        for w in validate_latin_square_balance(self._diagonals, outer_factors):
            print("WARNING: {}".format(w))

    @property
    def num_participants(self):
        """Number of participants (diagonals)."""
        return len(self._diagonals)

    @property
    def diagonals(self):
        """Dict mapping diagonal_id to list of combo tuples."""
        return dict(self._diagonals)

    def diagonal_combos(self, participant):
        """Returns the outer factor combos for a participant's diagonal.

        :param participant:
            Participant ID (:class:`int`). IDs >= ``num_participants``
            wrap cyclically via ``participant % num_participants``.

        :returns:
            A :class:`list` of combo :class:`tuples <tuple>` for this
            participant's diagonal.
        """
        d = participant % len(self._diagonals)
        return self._diagonals[d]

    def participant_for_trial(self, experiment, trial_index):
        """Returns the participant ID for a given trial based on its outer combo.

        :param experiment:
            A single experiment :class:`dict` from :func:`.synthesize_trials`
            output.

        :param trial_index:
            Index of the trial within the experiment.

        :returns:
            Participant ID (:class:`int`), or ``None`` if the combo doesn't
            match any diagonal.
        """
        outer_names = [str(f.name) for f in self.outer_factors]
        combo = tuple(experiment[name][trial_index] for name in outer_names)
        for d_id, combos in self._diagonals.items():
            if combo in combos:
                return d_id
        return None

    def build_participant_block(self, block, participant):
        """Build a reduced :class:`.NestedBlock` for a specific participant.

        Uses a synthetic condition factor whose levels are only this
        participant's diagonal combos, yielding fewer windows than the
        original :class:`.NestedBlock` (which has windows for all outer combos).

        :param block:
            The original :class:`.NestedBlock` (used to extract inner block
            info).

        :param participant:
            Participant ID (:class:`int`). Wraps cyclically.

        :returns:
            A :class:`tuple` of ``(reduced_nb, outer_factor_names, separator)``
            where ``reduced_nb`` is the per-participant :class:`.NestedBlock`,
            ``outer_factor_names`` is a :class:`list` of :class:`str`, and
            ``separator`` is the :class:`str` used to encode combo levels.
        """
        from sweetpea._internal.cross_block import (
            MultiCrossBlockRepeat, CrossBlock, NestedBlock
        )
        from sweetpea._internal.primitive import Factor

        combos = self.diagonal_combos(participant)
        separator = "|"
        outer_factor_names = [str(f.name) for f in self.outer_factors]

        for f in self.outer_factors:
            for level in f.levels:
                if separator in str(level.name):
                    raise ValueError(
                        "Level name '{}' in factor '{}' contains the separator "
                        "'{}'. This conflicts with the internal condition factor "
                        "encoding.".format(level.name, f.name, separator)
                    )

        condition_levels = [separator.join(str(v) for v in combo)
                           for combo in combos]
        condition_factor = Factor("_ls_condition", condition_levels)

        if not hasattr(block, '_inner_block'):
            raise ValueError(
                "LatinSquare.build_participant_block requires a NestedBlock "
                "with an inner CrossBlock in its design."
            )
        orig_inner = block._inner_block

        # Fresh CrossBlock avoids state pollution from the original
        fresh_inner = CrossBlock(
            orig_inner.orig_design,
            orig_inner.orig_crossings[0],
            list(orig_inner.orig_constraints)
        )

        # Use _user_constraints to avoid carrying over MinimumTrials
        # sized for ALL outer combos
        user_constraints = getattr(block, '_user_constraints', [])
        non_ls_constraints = [c for c in user_constraints
                              if not isinstance(c, LatinSquare)]
        reduced_nb = NestedBlock(
            design=[condition_factor, fresh_inner],
            crossing=[condition_factor],
            constraints=non_ls_constraints
        )

        return reduced_nb, outer_factor_names, separator

    # --- Constraint ABC methods (all no-ops) ---
    # LatinSquare does not add CNF clauses; per-participant filtering is handled
    # by build_participant_block() and synthesize_trials().

    def validate(self, block):
        """Validates that :class:`.LatinSquare` is applied to a :class:`.NestedBlock`
        and that ``outer_factors`` are external factors of that block.

        Skips validation on non-NestedBlocks and on constraints inherited
        from inner blocks (NestedBlock merges inner constraints into its
        own list)."""
        from sweetpea._internal.cross_block import NestedBlock
        if not isinstance(block, NestedBlock):
            return
        if self not in getattr(block, '_user_constraints', []):
            return
        # External = all design factors minus inner block factors
        inner_factor_names = {str(f.name) for f in block._inner_block.design
                              if hasattr(f, 'name')}
        external_names = {str(f.name) for f in block.design} - inner_factor_names
        for f in self.outer_factors:
            if str(f.name) not in external_names:
                raise ValueError(
                    "LatinSquare outer_factor '{}' is not an external factor "
                    "of the NestedBlock. outer_factors must be the external "
                    "factors listed in the NestedBlock design, not factors "
                    "from the inner block.".format(f.name)
                )

    def apply(self, block, backend_request):
        """No-op. Latin Square does not add CNF clauses to the SAT formula."""
        pass

    def potential_sample_conforms(self, sample, block):
        """Always returns ``True``. Latin Square does not constrain individual samples."""
        return True

    def desugar(self, replacements):
        """Returns ``[self]``. No desugaring needed for Latin Square."""
        return [self]

    def uses_factor(self, f):
        """Reports whether the given factor is one of the outer factors."""
        return f in self.outer_factors
