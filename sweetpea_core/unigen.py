from contextlib import contextmanager
from enum import Enum
from pathlib import Path
from shlex import split as shell_split
from subprocess import CompletedProcess, run
from typing import Iterator, List, NamedTuple, Optional
from uuid import uuid4 as generateUUID

from .data_structures import CNF
from .generate_cnf import GenerationRequest, build_CNF
from .haskell.data.list import drop, intercalate, take, unwords


@contextmanager
def temporary_CNF_file(base_path: Path = Path('.')) -> Iterator[Path]:
    cnf_file = base_path / Path(str(generateUUID())).with_suffix('.cnf')
    try:
        yield cnf_file
    finally:
        if cnf_file.exists():
            cnf_file.unlink()


class DockerRunReturnCode(Enum):
    """
    Invocation of the `docker run` command can result in one of the following
    special return codes. Any other return code is the result of invoking the
    indicated command in the container.

    Reference:
        https://docs.docker.com/engine/reference/run/#exit-status
    """
    DockerDaemonError                    = 125
    ContainedCommandCannotBeInvokedError = 126
    ContainedCommandCannotBeFoundError   = 127

    @classmethod
    def has_value(cls, value: int) -> bool:
        return value in (e.value for e in cls)


class DockerRunError(Exception):
    def __init__(self, returncode: DockerRunReturnCode, stderr: str):
        super().__init__(f"Error running Docker: {returncode.name}\n    stderr output captured below:\n\n{stderr}")


class UnigenError(Exception):
    def __init__(self, returncode: int, stdout: str, stderr: str):
        message_lines = [str(returncode)]
        if stdout:
            message_lines.append("\n    stdout output captured below:\n" + stdout)
        if stderr:
            message_lines.append("\n    stderr output captured below:\n" + stderr)
        super().__init__(''.join(message_lines))


class SolutionSpec(NamedTuple):
    assignment: List[int]
    frequency: int


def docker_run(container: str,
               args: Optional[List[str]] = None,
               input_bytes: Optional[bytes] = None) -> CompletedProcess:
    if args is None:
        args = []
    command = ['docker', 'run', *args, container]
    result = run(command, capture_output=True, input=input_bytes)
    if DockerRunReturnCode.has_value(result.returncode):
        code = DockerRunReturnCode(result.returncode)
        raise DockerRunError(code, result.stderr.decode())
    return result


def call_unigen_docker(input_file: Path) -> CompletedProcess:
    unigen_container = 'msoos/unigen'
    input_bytes = input_file.read_bytes()
    args = shell_split("--rm -i -a stdin -a stdout")
    result = docker_run(unigen_container, args, input_bytes)
    return result


def call_unigen_cli(input_file: Path) -> CompletedProcess:
    command = ["unigen", str(input_file)]
    result = run(command, capture_output=True)
    return result


def call_unigen(input_file: Path, docker_mode: bool = True) -> str:
    if docker_mode:
        result = call_unigen_docker(input_file)
    else:
        result = call_unigen_cli(input_file)
    if result.returncode == 0:
        # Success!
        # (Comments in the earlier Haskell version of SweetPea's core indicate
        # that Unigen used to use 0 as an error indicator.)
        return result.stdout
    else:
        # Failure.
        stdout = result.stdout.decode()
        stderr = result.stderr.decode()
        raise UnigenError(result.returncode, stdout, stderr)


def generate(initial_CNF: CNF,
             fresh: int,
             support: int,
             generation_requests: List[GenerationRequest],
             use_docker: bool = True
             ) -> List[SolutionSpec]:
    with temporary_CNF_file() as cnf_file:
        save_CNF(cnf_file, initial_CNF, fresh, support, generation_requests)
        output = call_unigen(cnf_file, docker_mode=use_docker)
        return extract_solutions(output)


def generate_non_uniform(support: int, count: int) -> List[List[int]]:
    raise NotImplementedError()  # NOTE: Deprecated in Haskell code.
    with temporary_CNF_file() as cnf_file:
        solutions = compute_solutions(cnf_file, support, count)
        return solutions


def compute_solutions(filename: Path, support: int, count: int, solutions: Optional[List[List[int]]] = None) -> List[List[int]]:
    if solutions is None:
        solutions = []
    if count == 0:
        return solutions
    command = shell_split(f"cryptominisat5 --verb=0 {filename}")
    result = run(command, capture_output=True)
    raw_solution = parse_CMSat_solution(result.stdout.decode())
    if not raw_solution:
        return solutions
    solution = take(support, raw_solution)
    update_file(filename, solution)
    return compute_solutions(filename, support, count - 1, solutions + [solution])


def update_file(filename: Path, solution: List[int]):
    lines = filename.read_text().strip().splitlines()
    updated_header = add_clause_to_header(lines[0])
    negated_solution = [-1 * val for val in solution]
    negated_solution_str = unwords([str(val) for val in negated_solution + [0]])
    updated_lines = [updated_header] + drop(1, lines) + [negated_solution_str]
    updated_contents = intercalate('\n', updated_lines)
    filename.write_text(updated_contents)


def add_clause_to_header(s: str) -> str:
    return update_header(1, s)


def update_header(additional_clause_count: int, header: str) -> str:
    segments = header.strip().split()
    new_clause_count = int(segments[3]) + additional_clause_count
    return ' '.join(take(3, segments) + [str(new_clause_count)])


def parse_CMSat_solution(output: str):
    if "s UNSATISFIABLE" in output:
        return []
    parts = ''.join(line for line in map(str.strip, output.strip().splitlines())
                    if line.startswith('v')).replace('v', '').split()
    return [int(s) for s in parts]


def new_CNF_path(base_path: Path = Path('.')) -> Path:
    return base_path / Path(str(generateUUID())).with_suffix('.cnf')


def sample_non_uniform(count: int,
                       initial_CNF: CNF,
                       fresh: int,
                       support: int,
                       generation_requests: List[GenerationRequest]
                       ) -> List[SolutionSpec]:
    with temporary_CNF_file() as cnf_file:
        save_CNF(cnf_file, initial_CNF, fresh, support, generation_requests)
        solutions = compute_solutions(cnf_file, support, count)
        return [SolutionSpec(solution, 1) for solution in solutions]


# TODO: I'm not sure we need this, since we aren't using a job system anymore.
def determine_SAT():
    raise NotImplementedError()


def save_CNF(filename: Path,
             initial_CNF: CNF,
             fresh: int,
             support: int,
             generation_requests: List[GenerationRequest]):
    cnf_str = build_CNF(initial_CNF, fresh, support, generation_requests)
    filename.write_text(cnf_str)


def read_solution_file(filename: Path) -> str:
    return filename.read_text()


def extract_solutions(solution_str: str) -> List[SolutionSpec]:
    return [build_solution(line) for line in solution_str.strip().splitlines()]


def build_solution(line: str) -> SolutionSpec:
    parts = line.replace('v', '').strip().split()
    assignment = [int(s) for s in parts[:-1]]
    frequency = int(parts[-1].split(':')[-1])
    return SolutionSpec(assignment, frequency)
