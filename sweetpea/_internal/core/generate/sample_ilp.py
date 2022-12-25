from typing import List, Union
from pathlib import Path

from ..cnf import CNF
from .utility import GenerationRequest, Solution, combine_and_save_opb, temporary_cnf_file


__all__ = ['sample_ilp']


def sample_ilp(count: int,
                    initial_cnf: CNF,
                    support: int,
                    generation_requests: List[GenerationRequest],
                    use_uniform: bool = False,
                    support_factors: List[List[int]] = [],
                    sample_dimensions: Union[int, int] = (-1, -1)
                    ) -> List[Solution]:
    with temporary_cnf_file(Path('.'), '.opb') as opb_file:
        combine_and_save_opb(opb_file, initial_cnf, generation_requests)
        print("Running Gurobi...")
        solutions = compute_solutions(opb_file, support, count,
                                        use_uniform,
                                        support_factors,
                                        sample_dimensions)
        return [Solution(solution, 1) for solution in solutions]

def compute_solutions(filename: Path,
                      support: int,
                      count: int,
                      use_uniform: bool,
                      support_factors: List[List[int]],
                      sample_dimensions: Union[int, int]) -> List[List[int]]:
    try:
        import gurobipy
    except ImportError as e:
        raise Exception("To use a Gurobi-backed solver, please install the gurobipy package: pip install gurobipy\n")

    if not use_uniform:
        return compute_solutions_iterate(filename, support, count)
    else:
        try:
            import numpy
        except ImportError as e:
            raise Exception("To use Gurobi as a uniform solver, please install the numpy package: pip install numpy\n")

        return compute_solutions_uniform(filename, support, count,
                                            support_factors,
                                            sample_dimensions)


def compute_solutions_iterate(filename: Path,
                                support: int,
                                count: int) -> List[List[int]]:
    import gurobipy as gp
    solutions = []
    with gp.Env(empty=True) as env:
        env.setParam('OutputFlag', 0)
        env.setParam('LogFile', '')
        env.start()
        for i in range(count):
            model = gp.read(filename.name, env)
            model.optimize()
            
            # TODO: Look into more error codes?
            # https://www.gurobi.com/documentation/9.5/refman/optimization_status_codes.html
            if model.Status != 2:
                return solutions

            solution = [int(v.varName.replace('v','')) \
                        if v.x == 1 \
                        else -int(v.varName.replace('v','')) \
                        for v in model.getVars()]
            solution = sorted(solution, key=abs)[:support]
            update_file(filename, solution)
            solutions.append(solution)
        return solutions

def update_file(filename: Path, solution: List[int]):
    with open(filename, 'a') as opb_file:
        false_count = len(list(v for v in solution if v < 0))
        opb_file.write('\n' + ' '.join(map(lambda x :  '-1 v' + str(abs(x)) \
                                                    if str(x)[0] == '-' \
                                                    else '+1 v' + str(x), solution)) \
                                + ' <= ' + str(len(solution) - 1 - false_count) + ' ;\n')

def compute_solutions_uniform(filename: Path,
                                support: int,
                                count: int,
                                support_factors: List[List[int]],
                                sample_dimensions: Union[int, int]) -> List[List[int]]:
    import gurobipy as gp
    import numpy as np
    from gurobipy import GRB

    solutions = []

    support_levels      = sum([len(f) for f in support_factors])
    levels_per_trial    = sample_dimensions[0]
    num_trials          = sample_dimensions[1]

    with gp.Env(empty=True) as env:
        env.setParam('OutputFlag', 0)
        env.setParam('LogFile', '')
        env.start()

        model = gp.read(filename.name, env)
        model.ModelSense = GRB.MAXIMIZE
        
        for i in range(count):
            weights         = np.array([[1]*support_levels]*num_trials)
            rnd             = np.random.gumbel(0, 1, size=(num_trials, support_levels))
            weighted_rnd    = rnd + np.log(weights)

            for j in range(num_trials):
                index = 0
                offset = levels_per_trial * j
                for f in support_factors:
                    next = index + len(f)
                    var_list = np.array([model.getVarByName('v' + str(l + offset)) for l in f])
                    model.setObjectiveN(np.dot(weighted_rnd[j][index:next], var_list), index + offset)
                    index = next

            model.optimize()
            
            # TODO: Look into more error codes?
            # https://www.gurobi.com/documentation/9.5/refman/optimization_status_codes.html
            if model.Status != 2:
                return solutions

            solution = [int(v.varName.replace('v','')) \
                        if v.x == 1 \
                        else -int(v.varName.replace('v','')) \
                        for v in model.getVars()]
            solution = sorted(solution, key=abs)[:support]
            solutions.append(solution)
        return solutions