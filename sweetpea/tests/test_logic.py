from sweetpea.logic import Iff, And, Or, Not, to_cnf_naive, to_cnf_switching, to_cnf_tseitin, cnf_to_json


def test_to_cnf_naive():
    assert to_cnf_naive(1, 2) == (And([1]), 2)
    assert to_cnf_naive(And([1]), 2) == (And([1]), 2)
    assert to_cnf_naive(And([1, 2]), 3) == (And([1, 2]), 3)

    assert to_cnf_naive(Or([1, 2]), 3) == (And([Or([1, 2])]), 3)
    assert to_cnf_naive(Or([1, And([2, 3])]), 4) == (And([Or([1, 2]), Or([1, 3])]), 4)

    formula = And([
        Iff(1, And([2, 3])),
        Iff(4, And([5, 6]))
    ])
    expected_cnf = And([
        Or([1, Not(2), Not(3)]),
        Or([Not(1), 2]),
        Or([Not(1), 3]),
        Or([4, Not(5), Not(6)]),
        Or([Not(4), 5]),
        Or([Not(4), 6])
    ])
    assert to_cnf_switching(formula, 7) == (expected_cnf, 7)


def test_to_cnf_switching():
    formula = Or([
        And([3, 4]),
        And([Not(2), Or([1, 5])])
    ])
    expected_cnf = And([
        Or([3, Not(6)]),
        Or([4, Not(6)]),
        Or([1, 5, 6]),
        Or([Not(2), 6])
    ])
    assert to_cnf_switching(formula, 6) == (expected_cnf, 7)

    formula = And([
        Iff(1, And([2, 3])),
        Iff(4, And([5, 6]))
    ])
    expected_cnf = And([
        Or([1, Not(2), Not(3)]),
        Or([Not(1), 2]),
        Or([Not(1), 3]),
        Or([4, Not(5), Not(6)]),
        Or([Not(4), 5]),
        Or([Not(4), 6])
    ])
    assert to_cnf_switching(formula, 7) == (expected_cnf, 7)


def test_to_cnf_tseitin():
    assert to_cnf_tseitin(Or([1, And([2, 3])]), 4) == (And([
        # 4 <=> (2 ^ 3)
        Or([Not(2), Not(3), 4]),
        Or([2, Not(4)]),
        Or([3, Not(4)]),

        # 5 <=> (1 v 4)
        Or([1, 4, Not(5)]),
        Or([Not(1), 5]),
        Or([Not(4), 5]),

        # Final clause
        5
    ]), 6)


def test_cnf_to_json():
    assert cnf_to_json([And([1])]) == [[1]]

    assert cnf_to_json([And([Or([1])])]) == [[1]]
    assert cnf_to_json([And([Or([Not(5)])])]) == [[-5]]
    assert cnf_to_json([And([Or([1, 2, Not(4)])])]) == [[1, 2, -4]]

    assert cnf_to_json([And([Or([1, 4]), Or([5, -4, 2]), Or([-1, -5])])]) == [
        [1, 4],
        [5, -4, 2],
        [-1, -5]]

    assert cnf_to_json([And([
        Or([1, 3, Not(2)]),
        Or([1, 3, 5]),
        Or([1, 4, Not(2)]),
        Or([1, 4, 5]),
        Or([2, 3, 1, 5]),
        Or([2, 4, 1, 5])])]) == [
            [1, 3, -2],
            [1, 3, 5],
            [1, 4, -2],
            [1, 4, 5],
            [2, 3, 1, 5],
            [2, 4, 1, 5]]


def test_eliminate_iff():
    from sweetpea.logic import __eliminate_iff

    # P <-> Q ==> (P v ~Q) ^ (~P v Q)
    assert __eliminate_iff(Iff(1, 2)) == And([Or([1, Not(2)]), Or([Not(1), 2])])

    assert __eliminate_iff(Iff(1, And([2, 3]))) == And([
        Or([1, Not(And([2, 3]))]),
        Or([Not(1), And([2, 3])])
    ])


def test_apply_demorgan():
    from sweetpea.logic import __apply_demorgan

    # P ==> P, ~P ==> ~P
    assert __apply_demorgan(4) == 4
    assert __apply_demorgan(Not(4)) == Not(4)

    # ~~P ==> P
    assert __apply_demorgan(Not(Not(4))) == 4

    # ~(P v Q) ==> ~P ^ ~Q
    assert __apply_demorgan(Not(Or([1, 2]))) == And([Not(1), Not(2)])

    # ~(P ^ Q) ==> ~P v ~Q
    assert __apply_demorgan(Not(And([1, 2]))) == Or([Not(1), Not(2)])

    assert __apply_demorgan(Or([1, Not(And([2, 3]))])) == Or([1, Not(2), Not(3)])


def test_distribute_ors_naive():
    from sweetpea.logic import __distribute_ors_naive

    # When f is int or Not, return it. (Not can only contain int, as we've
    # already applied DeMorgan's laws)
    assert __distribute_ors_naive(1) == 1
    assert __distribute_ors_naive(Not(1)) == Not(1)

    # When f in an Or, distribute the Or over the contained clauses.
    assert __distribute_ors_naive(Or([1, 2])) == And([Or([1, 2])])
    assert __distribute_ors_naive(Or([1, And([2, 3])])) == And([Or([1, 2]), Or([1, 3])])
    assert __distribute_ors_naive(Or([And([1, 2]), And([3, 4])])) == And([
        Or([1, 3]), Or([1, 4]), Or([2, 3]), Or([2, 4])
    ])

    # When f is an And, disitribute Ors over the contained clauses.
    assert __distribute_ors_naive(And([1, Not(2)])) == And([1, Not(2)])
    assert __distribute_ors_naive(And([1, Or([2, And([3, 4])])])) == And([
        Or([2, 3]), Or([2, 4]), 1
    ])


def test_distribute_ors_switching():
    from sweetpea.logic import __distribute_ors_switching

    # When lhs or rhs is a single variable, just distribute it.
    assert __distribute_ors_switching(Or([1, And([2, 3])]), 4) == (
        And([Or([1, 2]), Or([1, 3])]),
        4
    )

    assert __distribute_ors_switching(Or([And([1, 2]), 3]), 4) == (
        And([Or([1, 3]), Or([2, 3])]),
        4
    )

    # Should distribute over multiple individual variables
    assert __distribute_ors_switching(Or([
        1, 2, And([3, 4])
    ]), 5) == (
        And([
            Or([1, 2, 3]),
            Or([1, 2, 4])
        ]),
        5
    )

    # When both the lhs and rhs are more than just a single variable,
    # then introduce a switching variable to limit the formula growth.
    assert __distribute_ors_switching(Or([And([1, 2]), And([3, 4])]), 5) == (
        And([
            Or([1, Not(5)]),
            Or([2, Not(5)]),
            Or([3, 5]),
            Or([4, 5])
        ]),
        6
    )


def test_tseitin_rep_variables():
    from sweetpea.logic import __tseitin_rep, _Cache

    clauses = []
    cache = _Cache(2)
    assert __tseitin_rep(1, clauses, cache) == 1
    assert clauses == []
    assert cache.get_next_variable() == 2


def test_tseitin_rep_not():
    from sweetpea.logic import __tseitin_rep, _Cache

    # Should replace Not(var) with another variable
    clauses = []
    cache = _Cache(2)
    assert __tseitin_rep(Not(1), clauses, cache) == 2

    # Make sure that Not(1) was cached.
    assert cache.get(str(Not(1))) == 2

    # Make sure that the correct implication clauses were added.
    assert Or([    1,      2 ]) in clauses
    assert Or([Not(1), Not(2)]) in clauses

    # No clauses should be added if the value was already cached.
    clauses = []
    cache = _Cache(2)
    assert cache.get(str(Not(1))) == 2 # Prewarm the cache.
    assert __tseitin_rep(Not(1), clauses, cache) == 2
    assert clauses == []


def test_tseitin_rep_iff():
    from sweetpea.logic import __tseitin_rep, _Cache

    clauses = []
    cache = _Cache(3)

    # Make sure return is correct and value was cached.
    assert __tseitin_rep(Iff(1, 2), clauses, cache) == 3
    assert cache.get(str(Iff(1, 2))) == 3

    # Make sure equivalence clauses were added.
    assert Or([    1,      2,      3 ]) in clauses
    assert Or([Not(1), Not(2),     3 ]) in clauses
    assert Or([    1,  Not(2), Not(3)]) in clauses
    assert Or([Not(1),     2,  Not(3)]) in clauses

    # Don't duplicate clauses when the cache was already populated.
    clauses = []
    cache = _Cache(3)

    # Prewarm the cache.
    assert cache.get(str(Iff(1, 2))) == 3
    assert __tseitin_rep(Iff(1, 2), clauses, cache) == 3

    # Make sure no clauses were added.
    assert clauses == []


def test_tseitin_rep_and():
    from sweetpea.logic import __tseitin_rep, _Cache

    clauses = []
    cache = _Cache(4)

    # Make sure return is correct, and value was cached.
    assert __tseitin_rep(And([1, 2, 3]), clauses, cache) == 4
    assert cache.get(str(And([1, 2, 3]))) == 4

    # Make sure equivalence clauses were added.
    assert Or([1, Not(4)]) in clauses
    assert Or([2, Not(4)]) in clauses
    assert Or([3, Not(4)]) in clauses
    assert Or([Not(1), Not(2), Not(3), 4]) in clauses

    # Don't duplicate clauses when the cache was already populated
    clauses = []
    cache = _Cache(4)

    # Prewarm the cache
    assert cache.get(str(And([1, 2, 3]))) == 4
    assert __tseitin_rep(And([1, 2, 3]), clauses, cache) == 4

    # Make sure no clauses were added
    assert clauses == []


def test_tseitin_rep_or():
    from sweetpea.logic import __tseitin_rep, _Cache

    clauses = []
    cache = _Cache(4)

    # Make sure return is correct, and value was cached.
    assert __tseitin_rep(Or([1, 2, 3]), clauses, cache) == 4
    assert cache.get(str(Or([1, 2, 3]))) == 4

    # Make sure equivalence clauses were added.
    assert Or([Not(1), 4]) in clauses
    assert Or([Not(2), 4]) in clauses
    assert Or([Not(3), 4]) in clauses
    assert Or([1, 2, 3, Not(4)]) in clauses

    # Don't duplicate clauses when the cache was already populated
    clauses = []
    cache = _Cache(4)

    # Prewarm the cache
    assert cache.get(str(Or([1, 2, 3]))) == 4
    assert __tseitin_rep(Or([1, 2, 3]), clauses, cache) == 4

    # Make sure no clauses were added
    assert clauses == []


def test_tseitin_cache():
    from sweetpea.logic import _Cache

    c = _Cache(5)

    assert c.get('x') == 5
    assert c.get('x') == 5
    assert c.get('y') == 6
    assert c.get('z') == 7
    assert c.get('x') == 5

    assert c.get_next_variable() == 8