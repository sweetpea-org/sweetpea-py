"""This module provides functionality for calling the third-party CryptoMiniSAT
tool.

`CryptoMiniSAT <https://github.com/msoos/cryptominisat>`_ is a an advanced
incremental SAT solver. SweetPea uses CryptoMiniSAT for a few processes,
including solving some CNF formulas or checking whether a CNF formula is
satisfiable to begin with.
"""


from pathlib import Path
from shlex import split as shell_split
from subprocess import CompletedProcess, run
from typing import List, Optional, Tuple

from .docker_utility import DEFAULT_DOCKER_MODE_ON, docker_run
from .executables import CRYPTOMINISAT_EXE, DEFAULT_DOWNLOAD_IF_MISSING, ensure_executable_available
from .return_code import ReturnCodeEnum
from .tool_error import ToolError


__all__ = ['DEFAULT_DOCKER_MODE_ON', 'cryptominisat_solve', 'cryptominisat_is_satisfiable']


class CryptoMiniSATReturnCode(ReturnCodeEnum):
    """CryptoMiniSAT uses some unconventional return codes to indicate the
    result of various computations.
    """

    #: CryptoMiniSAT judged the CNF formula to be satisfiable.
    Satisfiable   = 10
    #: CryptoMiniSAT can make no judgment about the CNF formula.
    Unknown       = 15
    #: CryptoMiniSAT judged the CNF formula to be unsatisfiable.
    Unsatisfiable = 20


class CryptoMiniSATError(ToolError):
    """An error raised when CryptoMiniSAT fails."""
    pass


def call_cryptominisat_docker(input_file: Path) -> CompletedProcess:
    """Calls CryptoMiniSAT in a Docker container, reading a given file as the
    input problem.
    """
    cms_container = 'msoos/cryptominisat'
    input_bytes = input_file.read_bytes()
    args = shell_split("--rm -i -a stdin -a stdout")
    result = docker_run(cms_container, args, input_bytes)
    return result


def call_cryptominisat_cli(input_file: Path, download_if_missing: bool) -> CompletedProcess:
    """Calls CryptoMiniSAT from the command line, reading a given file as the
    input problem.

    If ``download_if_missing`` is ``True``, SweetPea will automatically
    download the CryptoMiniSAT executable (and other executables SweetPea
    depends on) to a local directory from the `sweetpea-org/unigen-exe
    repository <https://github.com/sweetpea-org/unigen-exe>`_.
    """
    ensure_executable_available(CRYPTOMINISAT_EXE, download_if_missing)
    command = [str(CRYPTOMINISAT_EXE), "--verb=0", str(input_file)]
    result = run(command, capture_output=True)
    return result


def call_cryptominisat(input_file: Path,
                       docker_mode: bool = DEFAULT_DOCKER_MODE_ON,
                       download_if_missing: bool = DEFAULT_DOWNLOAD_IF_MISSING
                       ) -> Tuple[str, CryptoMiniSATReturnCode]:
    """Calls CryptoMiniSAT with the given file as input.

    If ``docker_mode`` is ``True``, this will use a Docker container to run
    CryptoMiniSAT. If it's ``False``, a command-line executable will be used.

    If ``docker_mode`` is ``False`` *and* no local CryptoMiniSAT executable can
    be found, and if ``download_if_missing`` is ``True``, the needed executable
    will be automatically downloaded if it's missing.
    """
    if docker_mode:
        result = call_cryptominisat_docker(input_file)
    else:
        result = call_cryptominisat_cli(input_file, download_if_missing)
    if CryptoMiniSATReturnCode.has_value(result.returncode):
        return (result.stdout.decode(), CryptoMiniSATReturnCode(result.returncode))
    else:
        stdout = result.stdout.decode()
        stderr = result.stderr.decode()
        raise CryptoMiniSATError(result.returncode, stdout, stderr)


def cryptominisat_solve(input_file: Path, docker_mode: bool = DEFAULT_DOCKER_MODE_ON) -> Optional[List[int]]:
    """Attempts to solve a CNF formula with CryptoMiniSAT and returns the
    result as a list of integers.

    Returns an empty list if the result was unsatisfiable, and returns ``None``
    if CryptoMiniSAT encounters some unknown issue.
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


def cryptominisat_is_satisfiable(input_file: Path, docker_mode: bool = DEFAULT_DOCKER_MODE_ON) -> Optional[bool]:
    """Determines whether the CNF formula encoded in the input file is
    satisfiable, according to CryptoMiniSAT.

    Returns ``None`` if CryptoMiniSAT encounters an unknown issue.
    """
    (_, code) = call_cryptominisat(input_file, docker_mode)
    if code is CryptoMiniSATReturnCode.Satisfiable:
        return True
    elif code is CryptoMiniSATReturnCode.Unsatisfiable:
        return False
    else:
        return None
