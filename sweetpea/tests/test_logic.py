from sweetpea.logic import Iff, And, Or, Not, to_cnf, cnf_to_json


def test_to_cnf():
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
    assert to_cnf(formula, 6) == (expected_cnf, 7)

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
    assert to_cnf(formula, 7) == (expected_cnf, 7)



def test_cnf_to_json():
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


def test_distribute_ors():
    from sweetpea.logic import __distribute_ors

    # When lhs or rhs is a single variable, just distribute it.
    assert __distribute_ors(Or([1, And([2, 3])]), 4) == (
        And([Or([1, 2]), Or([1, 3])]),
        4
    )

    assert __distribute_ors(Or([And([1, 2]), 3]), 4) == (
        And([Or([1, 3]), Or([2, 3])]),
        4
    )

    # Should distribute over multiple individual variables
    assert __distribute_ors(Or([
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
    assert __distribute_ors(Or([And([1, 2]), And([3, 4])]), 5) == (
        And([
            Or([1, Not(5)]),
            Or([2, Not(5)]),
            Or([3, 5]),
            Or([4, 5])
        ]),
        6
    )

