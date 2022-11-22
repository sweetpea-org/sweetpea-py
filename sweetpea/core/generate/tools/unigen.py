"""This module provides functionality for calling the third-party Unigen tool.

`Unigen <https://github.com/meelgroup/unigen>`_ is a state-of-the-art,
almost-uniform SAT sampler that uses `CryptoMiniSAT
<https://github.com/msoos/cryptominisat>`_ to solve SAT problems. SweetPea uses
Unigen for a few processes.
"""


from pathlib import Path
from shlex import split as shell_split
from subprocess import CompletedProcess, run
from numpy import random
from tempfile import NamedTemporaryFile

from typing import Tuple

from .docker_utility import DEFAULT_DOCKER_MODE_ON, docker_run
from .executables import DEFAULT_DOWNLOAD_IF_MISSING, UNIGEN_EXE, CMSGEN_EXE, ensure_executable_available
from .tool_error import ToolError
from ..utility import temporary_cnf_file


__all__ = ['DEFAULT_DOCKER_MODE_ON', 'UnigenError', 'call_unigen']


class UnigenError(ToolError):
    """An error raised when Unigen fails."""
    pass


def call_unigen_docker(input_file: Path, sample_count: int) -> Tuple[CompletedProcess, str]:
    """Calls Unigen in a Docker container, reading a given file as the input
    problem.
    """
    unigen_container = 'msoos/unigen'
    input_bytes = input_file.read_bytes()
    # args = shell_split("--rm -i -a stdin -a stdout --samples="+str(sample_count))
    args = shell_split("--rm -i -a stdin -a stdout")
    result = docker_run(unigen_container, args, input_bytes)
    return (result, "")


def call_unigen_cli(input_file: Path,
                    download_if_missing: bool,
                    sample_count: int,
                    use_cmsgen: bool) -> Tuple[CompletedProcess, str]:
    """Calls Unigen from the command line, reading a given file as the input
    problem.

    If ``download_if_missing`` is ``True``, SweetPea will automatically
    download the Unigen executable (and other executables SweetPea depends on)
    to a local directory from the `sweetpea-org/unigen-exe repository
    <https://github.com/sweetpea-org/unigen-exe>`_.
    """
    unigen_exe = CMSGEN_EXE if use_cmsgen else UNIGEN_EXE
    ensure_executable_available(unigen_exe, download_if_missing)
    seed = random.randint(999999999)
    command = [str(unigen_exe), str(input_file), "--samples="+str(sample_count), "--seed="+str(seed)]
    if use_cmsgen:
        with temporary_cnf_file(suffix = ".out") as output_file:
            command.append("--samplefile="+output_file.name)
            result = run(command, capture_output=True)  # noqa
            with open(output_file, 'r') as output:
                samples = output.read()
                return (result, samples)
    else:
        # NOTE: flake8 doesn't seem to handle the calls to `run` correctly, but
        #       mypy reports everything is fine here so we `noqa` to prevent flake8
        #       complaining about what it doesn't understand.
        result = run(command, capture_output=True)  # noqa
        return (result, "")


def call_unigen(sample_count: int,
                input_file: Path,
                docker_mode: bool = DEFAULT_DOCKER_MODE_ON,
                download_if_missing: bool = DEFAULT_DOWNLOAD_IF_MISSING,
                use_cmsgen: bool = False
                ) -> str:
    """Calls Unigen with the given file as input.

    If ``docker_mode`` is ``True``, this will use a Docker container to run
    Unigen. If it's ``False``, a command-line executable will be used.

    If ``docker_mode`` is ``False`` and no local Unigen executable can be
    found, and if ``download_if_missing`` is ``True``, the needed executable
    will be automatically downloaded if it's missing.
    """
    if docker_mode:
        (result, samples) = call_unigen_docker(input_file, sample_count)
    else:
        (result, samples) = call_unigen_cli(input_file, download_if_missing, sample_count, use_cmsgen)
    if result.returncode == (10 if use_cmsgen else 0):
        # Success!
        # (Comments in the earlier Haskell version of SweetPea's core indicate
        # that Unigen used to use 0 as an error indicator.)
        return result.stdout.decode()+samples
    else:
        # Failure.
        stdout = result.stdout.decode()
        stderr = result.stderr.decode()
        if "The input formula is unsatisfiable" in stdout:
            return ""
        raise UnigenError(result.returncode, stdout, stderr)
