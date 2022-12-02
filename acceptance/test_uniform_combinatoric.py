import glob
import os
import pytest

from sweetpea._internal.logic import And, cnf_to_json
from sweetpea._internal.server import build_cnf
from sweetpea._internal.core import cnf_is_satisfiable, CNF
from sweetpea._internal.sampling_strategy.random import UCSolutionEnumerator


path_to_test_files = os.path.dirname(os.path.abspath(__file__)) + "/../sweetpea/tests/sampling_strategies/uc-counting-tests/*.py"

@pytest.mark.slow
@pytest.mark.parametrize('filename', glob.glob(path_to_test_files))
def test_uniform_combinatoric_is_always_valid(filename):

    failures = []
    contents = None
    with open(filename, 'r') as f:
        contents = f.read()
        exec(contents, globals(), locals())

    if 'block' not in vars():
        pytest.fail("File did not produce a variable named 'block', aborting. file={}".format(filename))


    # Build the CNF for this block
    build_cnf_result = build_cnf(vars()['block'])

    # Build the sampler
    enumerator = UCSolutionEnumerator(vars()['block'])

    # Generate some samples, make sure they're all SAT.
    sample_count = min(enumerator.solution_count(), 200)
    print("Checking that UC samples are SAT for {}, sample count={}".format(filename, sample_count))
    for s in range(sample_count):
        sample = enumerator.generate_solution_variables()
        if not cnf_is_satisfiable(build_cnf_result + CNF(cnf_to_json([And(sample)]))):
            failures.append("Found UNSAT solution! Solution={} File={}".format(sample, filename))

    if failures:
        pytest.fail('{} failures occurred in SAT checks for UC sampler: {}'.format(len(failures), failures))
