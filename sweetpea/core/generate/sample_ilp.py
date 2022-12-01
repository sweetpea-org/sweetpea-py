from io import TextIOWrapper
from typing import List, Optional
from pathlib import Path

from ..cnf import CNF
from .utility import GenerationRequest, Solution, combine_and_save_opb, temporary_cnf_file


__all__ = ['sample_ilp']


def sample_ilp_iterate(count: int,
                    initial_cnf: CNF,
                    support: int,
                    generation_requests: List[GenerationRequest],
                    ) -> List[Solution]:
    with temporary_cnf_file(Path('.'), '.opb') as opb_file:
        combine_and_save_opb(opb_file, initial_cnf, support, generation_requests)
        print("Running Gurobi...")
        solutions = compute_solutions(opb_file, support, count)
        return [Solution(solution, 1) for solution in solutions]

def compute_solutions(filename: Path,
                      support: int,
                      count: int,
                      solutions: Optional[List[List[int]]] = None) -> List[List[int]]:
    try:
        import gurobipy
    except ImportError as e:
        raise Exception("To use a Gurobi-backed solver, please install the gurobipy package: pip install gurobipy\n")
    
    import gurobipy as gp
    from gurobipy import GRB

    with gp.Env(empty=True) as env:
        env.setParam('OutputFlag', 0)
        env.setParam('LogFile', '')
        env.start()
        while True:
            if solutions is None:
                solutions = []
            if count == 0:
                return solutions
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
            count -= 1
            solutions += [solution]

def update_file(filename: Path, solution: List[int]):
    with open(filename, 'a') as opb_file:
        false_count = len(list(v for v in solution if v < 0))
        opb_file.write('\n' + ' '.join(map(lambda x :  '-1 v' + str(abs(x)) \
                                                    if str(x)[0] == '-' \
                                                    else '+1 v' + str(x), solution)) \
                                + ' <= ' + str(len(solution) - 1 - false_count) + ' ;\n')
