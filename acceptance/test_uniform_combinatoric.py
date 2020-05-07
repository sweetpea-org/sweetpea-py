import glob
import os
import pytest

from sweetpea.docker import start_docker_container, stop_docker_container
from sweetpea.logic import And
from sweetpea.server import build_cnf, is_cnf_still_sat
from sweetpea.sampling_strategies.uniform_combinatoric import UCSolutionEnumerator


path_to_test_files = os.path.dirname(os.path.abspath(__file__)) + "/../sweetpea/tests/sampling_strategies/uc-counting-tests/*.py"

@pytest.mark.parametrize('filename', glob.glob(path_to_test_files))
def test_uniform_combinatoric_is_always_valid(filename):
    container = start_docker_container("sweetpea/server", 8080)

    try:
        failures = []
        contents = None
        with open(filename, 'r') as f:
            contents = f.read()
            exec(contents, globals(), locals())

        if 'block' not in vars():
            pytest.fail("File did not produce a variable named 'block', aborting. file={}".format(filename))


        # Build the CNF for this block
        build_cnf_result = build_cnf(vars()['block'])
        cnf_id = build_cnf_result['id']
        
        # Build the sampler
        enumerator = UCSolutionEnumerator(vars()['block'])
        
        # Generate some samples, make sure they're all SAT.
        sample_count = min(enumerator.solution_count(), 200)
        print("Checking that UC samples are SAT for {}, sample count={}".format(filename, sample_count))
        for s in range(sample_count):
            sample = enumerator.generate_solution_variables()
            if not is_cnf_still_sat(cnf_id, [And(sample)]):
                failures.append("Found UNSAT solution! Solution={} File={}".format(sample, filename))

        if failures:
            pytest.fail('{} failures occurred in SAT checks for UC sampler: {}'.format(len(failures), failures))

    finally:
        stop_docker_container(container)
