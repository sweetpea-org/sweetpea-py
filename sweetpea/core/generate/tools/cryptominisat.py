"""This module provides functionality for calling CryptoMiniSAT."""


from pathlib import Path
from shlex import split as shell_split
from subprocess import CompletedProcess, run
from typing import List, Optional

from .docker_utility import docker_run
from .tool_error import ToolError


__all__ = ['call_and_parse_cryptominisat']


class CryptoMinisatError(ToolError):
    """An error raised when CryptoMiniSAT fails."""
    pass


def call_cryptominisat_docker(input_file: Path) -> CompletedProcess:
    # TODO DOC
    cms_container = 'msoos/cryptominisat'
    input_bytes = input_file.read_bytes()
    args = shell_split("--rm -i -a stdin -a stdout")
    result = docker_run(cms_container, args, input_bytes)
    return result


def call_cryptominisat_cli(input_file: Path) -> CompletedProcess:
    # TODO DOC
    command = ["cryptominisat5", "--verb=0", str(input_file)]
    result = run(command, capture_output=True)
    return result


def call_cryptominisat(input_file: Path, docker_mode: bool = True) -> str:
    # TODO DOC
    if docker_mode:
        result = call_cryptominisat_docker(input_file)
    else:
        result = call_cryptominisat_cli(input_file)
    if result.returncode == 0:
        return result.stdout.decode()
    else:
        stdout = result.stdout.decode()
        stderr = result.stderr.decode()
        raise CryptoMinisatError(result.returncode, stdout, stderr)


def parse_cryptominisat_result(result: str) -> Optional[List[int]]:
    # TODO DOC
    if not result:
        return None
    if "s UNSATISFIABLE" in result:
        return []
    parts = ''.join(line for line in map(str.strip, result.strip().splitlines())
                    if line.startswith('v')).replace('v', '').split()
    return [int(p) for p in parts]


def call_and_parse_cryptominisat(input_file: Path, docker_mode: bool = True) -> Optional[List[int]]:
    # TODO DOC
    result = call_cryptominisat(input_file, docker_mode)
    parsed_result = parse_cryptominisat_result(result)
    return parsed_result
