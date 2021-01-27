from enum import Enum
from pathlib import Path
from shlex import split as shell_split
from subprocess import CompletedProcess, run
from typing import List, NamedTuple, Optional


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
