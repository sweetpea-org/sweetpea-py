"""This module provides functionality for calling CryptoMiniSAT."""


from pathlib import Path
from shlex import split as shell_split
from subprocess import CompletedProcess, run
from typing import List, Optional, Tuple

from .docker_utility import docker_run
from .return_code import ReturnCodeEnum
from .tool_error import ToolError


__all__ = ['cryptominisat_solve', 'cryptominisat_is_satisfiable']


class CryptoMiniSATReturnCode(ReturnCodeEnum):
    """CryptoMiniSAT uses some unconventional return codes to indicate the
    result of various computations.
    """

    Satisfiable   = 10
    Unknown       = 15
    Unsatisfiable = 20


class CryptoMiniSATError(ToolError):
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


def call_cryptominisat(input_file: Path, docker_mode: bool = True) -> Tuple[str, CryptoMiniSATReturnCode]:
    # TODO DOC
    if docker_mode:
        result = call_cryptominisat_docker(input_file)
    else:
        result = call_cryptominisat_cli(input_file)
    if CryptoMiniSATReturnCode.has_value(result.returncode):
        return (result.stdout.decode(), CryptoMiniSATReturnCode(result.returncode))
    else:
        stdout = result.stdout.decode()
        stderr = result.stderr.decode()
        raise CryptoMiniSATError(result.returncode, stdout, stderr)


def cryptominisat_solve(input_file: Path, docker_mode: bool = True) -> Optional[List[int]]:
    """Attempts to solve a CNF formula with CryptoMiniSAT and return the result
    as a list of integers.

    Returns an empty list if the result was unsatisfiable, and returns None if
    CryptoMiniSAT encounters some unknown issue.
    """
    (result, code) = call_cryptominisat(input_file, docker_mode)
    if code is CryptoMiniSATReturnCode.Unsatisfiable:
        return []
    elif code is CryptoMiniSATReturnCode.Satisfiable:
        parts = ''.join(line for line in map(str.strip, result.strip().splitlines())
                        if line.startswith('v')).replace('v', '').split()
        return [int(p) for p in parts]
    else:
        return None


def cryptominisat_is_satisfiable(input_file: Path, docker_mode: bool = True) -> Optional[bool]:
    """Determines whether the CNF formula encoded in the input file is
    satisfiable, according to CryptoMiniSAT.

    Returns None if CryptoMiniSAT encounters an unknown issue.
    """
    (_, code) = call_cryptominisat(input_file, docker_mode)
    if code is CryptoMiniSATReturnCode.Satisfiable:
        return True
    elif code is CryptoMiniSATReturnCode.Unsatisfiable:
        return False
    else:
        return None
