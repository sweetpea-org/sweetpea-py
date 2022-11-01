import os
import numpy as np

from functools import reduce
from itertools import product, chain
from time import time
from typing import List, cast

from sweetpea.blocks import Block
from sweetpea.core import CNF, cnf_is_satisfiable
from sweetpea.logic import And, cnf_to_json
from sweetpea.sampling_strategies.base import SamplingStrategy, SamplingResult
from sweetpea.server import build_cnf


"""
This strategy gradually constructs samples in memory, with the aid of a SAT solver to
guide the choices it makes.

While sufficient in some cases, this strategy isn't guaranteed to produce uniform results
because trial selections early on can prune the remaining search space unevenly.
"""
class GuidedSamplingStrategy(SamplingStrategy):

    @staticmethod
    def class_name():
        return 'Guided Sampling Strategy'

    @staticmethod
    def sample(block: Block, sample_count: int) -> SamplingResult:

        samples = cast(List[dict], [])
        metrics = cast(dict, {
            'sample_metrics': []
        })

        overall_start = time()

        # Build the full CNF for this block
        cnf = build_cnf(block)

        metrics['solver_call_count'] = 0
        for _ in range(sample_count):
            sample_metrics = cast(dict, {})
            t_start = time()
            samples.append(GuidedSamplingStrategy.__generate_sample(block, cnf, sample_metrics))
            sample_metrics['time'] = time() - t_start
            metrics['sample_metrics'].append(sample_metrics)
            metrics['solver_call_count'] += sample_metrics['solver_call_count']

        metrics['time'] = time() - overall_start
        GuidedSamplingStrategy.__compute_additional_metrics(metrics)

        return SamplingResult(samples, metrics)


    @staticmethod
    def __generate_sample(block: Block, cnf: CNF, sample_metrics: dict) -> dict:
        sample_metrics['trials'] = []

        # Start a 'committed' list of CNFs
        committed = cast(List[And], [])

        for trial_number in range(block.trials_per_sample()):
            trial_start_time = time()

            trial_metrics = {
                't': trial_number + 1,
                'solver_calls': []
            }
            solver_calls = cast(List[dict], trial_metrics['solver_calls'])

            #  Get the variable list for this trial.
            variables = block.variable_list_for_trial(trial_number + 1)
            variables = list(filter(lambda i: i != [], variables))
            potential_trials = list(map(list, product(*variables)))

            trial_metrics['potential_trials'] = len(potential_trials)

            # Use env var to switch between filtering and not
            if GuidedSamplingStrategy.__prefilter_enabled():
                # Flatten the list
                flat_vars = list(chain(*variables))

                # Check SAT for each one
                unsat = []
                for v in flat_vars:
                    t_start = time()
                    full_cnf = cnf + CNF(cnf_to_json(committed)) + CNF(cnf_to_json([And([v])]))
                    allowed = cnf_is_satisfiable(full_cnf)
                    duration_seconds = time() - t_start
                    solver_calls.append({'time': duration_seconds, 'SAT': allowed})
                    if not allowed:
                        unsat.append(v)

                # TODO: Count filtering SAT calls separately?

                # Filter out any potential trials with those vars set
                filtered_pts = []
                for pt in potential_trials:
                    if any(uv in pt for uv in unsat):
                        continue
                    else:
                        filtered_pts.append(pt)

                # Record the number filterd out for metrics
                trial_metrics['prefiltered_out'] = len(potential_trials) - len(filtered_pts)
                potential_trials = filtered_pts

            allowed_trials = []
            for potential_trial in potential_trials:
                start_time = time()
                full_cnf = cnf + CNF(cnf_to_json(committed)) + CNF(cnf_to_json([And(potential_trial)]))
                allowed = cnf_is_satisfiable(full_cnf)
                duration_seconds = time() - start_time

                solver_calls.append({'time': duration_seconds, 'SAT': allowed})

                if allowed:
                    allowed_trials.append(potential_trial)

            trial_metrics['allowed_trials'] = len(allowed_trials)
            trial_metrics['solver_call_count'] = len(solver_calls)
            sample_metrics['trials'].append(trial_metrics)

            # Randomly sample a single trial from the uniform distribution of the allowed trials,
            # and commit that trial to the committed sequence.
            trial_idx = np.random.randint(0, len(allowed_trials))
            committed.append(And(allowed_trials[trial_idx]))

            trial_metrics['time'] = time() - trial_start_time

        # Aggregate the total solver calls
        sample_metrics['solver_call_count'] = 0
        for tm in sample_metrics['trials']:
            sample_metrics['solver_call_count'] += tm['solver_call_count']

        # Flatten the committed trials into a list of integers and decode it.
        solution = GuidedSamplingStrategy.__committed_to_solution(committed)
        return SamplingStrategy.decode(block, solution)

    @staticmethod
    def __committed_to_solution(committed: List[And]) -> List[int]:
        return reduce(lambda sol, clause: sol + clause.input_list, committed, [])

    @staticmethod
    def __prefilter_enabled():
        return os.environ.get('SWEETPEA_GUIDED_PREFILTER_TRIALS') is not None

    @staticmethod
    def print_summary(result: SamplingResult) -> None:
        metrics = result.metrics
        print("Total Time: {} seconds".format(metrics['time']))
        print("Total SAT Solver Calls: {}".format(metrics['solver_call_count']))
        print("Mean SAT Time: {}".format(metrics['mean_sat_time']))
        print("Mean UNSAT Time: {}".format(metrics['mean_unsat_time']))

        if 'total_prefiltered_out' in metrics:
            print("Total Prefiltered Out: {}".format(metrics['total_prefiltered_out']))

    @staticmethod
    def __compute_additional_metrics(metrics: dict) -> None:
        total_sat = 0
        total_sat_time = 0
        total_unsat = 0
        total_unsat_time = 0

        for sample in metrics['sample_metrics']:
            for trial in sample['trials']:
                for sc in trial['solver_calls']:
                    if sc['SAT'] == True:
                        total_sat += 1
                        total_sat_time += sc['time']
                    elif sc['SAT'] == False:
                        total_unsat += 1
                        total_unsat_time += sc['time']

        metrics['mean_sat_time'] = total_sat_time / total_sat
        metrics['mean_unsat_time'] = total_unsat_time / total_unsat

        if GuidedSamplingStrategy.__prefilter_enabled():
            total_prefiltered_out = 0
            for sample in metrics['sample_metrics']:
                for trial in sample['trials']:
                    total_prefiltered_out += trial['prefiltered_out']
            metrics['total_prefiltered_out'] = total_prefiltered_out


"""
Generates a static HTML file that will render a flamegraph showing the time breakdown for a given sampling.
"""
class Flamegraph():
    GRAPH_FILE_TEMPLATE = '''
<head>
  <link rel="stylesheet" type="text/css" href="https://cdn.jsdelivr.net/gh/spiermar/d3-flame-graph@2.0.6/dist/d3-flamegraph.css">
</head>
<body>
  <div id="chart"></div>
  <script type="text/javascript" src="https://d3js.org/d3.v4.min.js"></script>
  <script type="text/javascript" src="https://cdnjs.cloudflare.com/ajax/libs/d3-tip/0.9.1/d3-tip.min.js"></script>
  <script type="text/javascript" src="https://cdn.jsdelivr.net/gh/spiermar/d3-flame-graph@2.0.6/dist/d3-flamegraph.min.js"></script>
  <script type="text/javascript">
  graph_data = {}
  var flamegraph = d3.flamegraph().width(960);
  d3.select("#chart").datum(graph_data).call(flamegraph);
  <!-- TODO: Render SAT/UNSAT calls as Green/Red -->
  <!-- TODO: Replace 'samples' with 'seconds' in tooltip -->
  </script>
</body>
'''

    @staticmethod
    def generate(filename: str, sampling_result: SamplingResult) -> None:
        graph_data = Flamegraph.__convert_metrics_to_graph_data(sampling_result.metrics)
        with open(filename, 'w') as f:
            f.write(Flamegraph.GRAPH_FILE_TEMPLATE.format(graph_data))

    @staticmethod
    def __convert_metrics_to_graph_data(metrics: dict) -> dict:
        children = []
        for sample_number in range(len(metrics['sample_metrics'])):
            children.append(Flamegraph.__convert_sample_to_graph_data(sample_number, metrics['sample_metrics'][sample_number]))

        return {
            'name': 'All Samples',
            'value': metrics['time'],
            'children': children
        }

    @staticmethod
    def __convert_sample_to_graph_data(sample_number: int, sample_metrics: dict) -> dict:
        children = []
        for trial_number in range(len(sample_metrics['trials'])):
            children.append(Flamegraph.__convert_trial_to_graph_data(trial_number, sample_metrics['trials'][trial_number]))

        return {
            'name': 'Sample #{}'.format(sample_number + 1),
            'value': sample_metrics['time'],
            'children': children
        }

    @staticmethod
    def __convert_trial_to_graph_data(trial_number: int, trial_metrics: dict) -> dict:
        children = []
        for solver_number in range(len(trial_metrics['solver_calls'])):
            solver_call = trial_metrics['solver_calls'][solver_number]
            children.append({
                'name': 'Solver Call #{}'.format(solver_number + 1),
                'value': solver_call['time'],
                'SAT': str(solver_call['SAT']).lower()
            })

        return {
            'name': 'Trial #{}'.format(trial_number + 1),
            'value': trial_metrics['time'],
            'children': children
        }
