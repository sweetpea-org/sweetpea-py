"""This module provides functionality for calling Unigen."""


from pathlib import Path
from shlex import split as shell_split
from subprocess import CompletedProcess, run

from .docker_utility import DEFAULT_DOCKER_MODE_ON, docker_run
from .executables import DEFAULT_DOWNLOAD_IF_MISSING, UNIGEN_EXE, ensure_executable_available
from .tool_error import ToolError


__all__ = ['DEFAULT_DOCKER_MODE_ON', 'UnigenError', 'call_unigen']


class UnigenError(ToolError):
    """An error raised when Unigen fails."""
    pass


def call_unigen_docker(input_file: Path) -> CompletedProcess:
    # TODO DOC
    unigen_container = 'msoos/unigen'
    input_bytes = input_file.read_bytes()
    args = shell_split("--rm -i -a stdin -a stdout")
    result = docker_run(unigen_container, args, input_bytes)
    return result


def call_unigen_cli(input_file: Path, download_if_missing: bool) -> CompletedProcess:
    # TODO DOC
    ensure_executable_available(UNIGEN_EXE, download_if_missing)
    command = [str(UNIGEN_EXE), str(input_file)]
    # NOTE: flake8 doesn't seem to handle the calls to `run` correctly, but
    #       mypy reports everything is fine here so we `noqa` to prevent flake8
    #       complaining about what it doesn't understand.
    result = run(command, capture_output=True)  # noqa
    return result


def call_unigen(input_file: Path,
                docker_mode: bool = DEFAULT_DOCKER_MODE_ON,
                download_if_missing: bool = DEFAULT_DOWNLOAD_IF_MISSING
                ) -> str:
    # TODO DOC
    if docker_mode:
        result = call_unigen_docker(input_file)
    else:
        result = call_unigen_cli(input_file, download_if_missing)
    if result.returncode == 0:
        # Success!
        # (Comments in the earlier Haskell version of SweetPea's core indicate
        # that Unigen used to use 0 as an error indicator.)
        return result.stdout.decode()
    else:
        # Failure.
        stdout = result.stdout.decode()
        stderr = result.stderr.decode()
        raise UnigenError(result.returncode, stdout, stderr)
