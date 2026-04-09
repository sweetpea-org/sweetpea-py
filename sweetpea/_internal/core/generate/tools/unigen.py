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
from typing import Tuple
import warnings

from .docker_utility import DEFAULT_DOCKER_MODE_ON, docker_run
from .executables import DEFAULT_DOWNLOAD_IF_MISSING, UNIGEN_EXE, CMSGEN_EXE, ensure_executable_available
from .tool_error import ToolError
from ..utility import temporary_cnf_file


__all__ = ['DEFAULT_DOCKER_MODE_ON', 'UnigenError', 'call_unigen']


try:
    import pyunigen
    HAS_PYUNIGEN = True
except ImportError:
    HAS_PYUNIGEN = False

try:
    import pycmsgen
    HAS_PYCMSGEN = True
except ImportError:
    HAS_PYCMSGEN = False


class UnigenError(ToolError):
    """An error raised when Unigen fails."""
    pass


def parse_cnf_file(input_file: Path) -> Tuple[list, list, int]:
    """Parse a DIMACS CNF file to extract clauses, sampling set, and variable count.

    :param input_file:
        Path to a DIMACS CNF file.

    :returns:
        A :class:`tuple` of ``(clauses, sampling_set, num_vars)``.
    """
    clauses = []
    sampling_set = []
    num_vars = 0
    
    try:
        with open(input_file, 'r') as f:
            for line in f:
                line = line.strip()
                
                if not line:
                    continue
                
                # Parse sampling set (c ind lines)
                if line.startswith('c ind'):
                    parts = line.split()[2:]
                    vars_in_line = [int(x) for x in parts if x != '0']
                    sampling_set.extend(vars_in_line)
                    continue
                
                # Skip other comments
                if line.startswith('c'):
                    continue
                
                # Parse problem line (p cnf variables clauses)
                if line.startswith('p cnf'):
                    parts = line.split()
                    if len(parts) >= 3:
                        num_vars = int(parts[2])
                    continue
                
                # Parse clause
                if line and not line.startswith('c') and not line.startswith('p'):
                    clause = [int(x) for x in line.split() if x != '0']
                    if clause:
                        clauses.append(clause)
    except (IOError, ValueError) as e:
        raise UnigenError(-1, "", f"Failed to parse CNF file: {e}")
    
    # Remove duplicates and sort
    if sampling_set:
        sampling_set = sorted(set(sampling_set))
    
    return clauses, sampling_set, num_vars


def call_unigen_python(input_file: Path, sample_count: int) -> str:
    """Calls the ``pyunigen`` library for uniform sampling.

    :param input_file:
        Path to a CNF file to sample from.

    :param sample_count:
        Number of samples requested. ``pyunigen`` may return a different
        number based on its internal algorithm.

    :returns:
        Formatted sample output :class:`str` matching UniGen binary format.
    """
    if not HAS_PYUNIGEN:
        raise ImportError("pyunigen not available")
    
    clauses, sampling_set, num_vars = parse_cnf_file(input_file)
    
    if not clauses:
        return ""
    
    if not sampling_set:
        sampling_set = list(range(1, num_vars + 1))
    
    sampler = pyunigen.Sampler()
    for clause in clauses:
        sampler.add_clause(clause)
    
    try:
        # pyunigen may return more or fewer samples based on its internal algorithm
        cells, hashes, samples = sampler.sample(
            num=sample_count,
            sampling_set=sampling_set
        )
        
        if not samples or cells == 0:
            return ""
        
        # Format output to match UniGen's expected format
        output_lines = []
        for sample in samples:
            sample_str = "v " + " ".join(str(lit) for lit in sample) + " 0:1"
            output_lines.append(sample_str)
        
        return "\n".join(output_lines) + "\n"
        
    except Exception as e:
        raise UnigenError(-1, str(e), f"pyunigen sampling failed: {e}")


def call_cmsgen_python(input_file: Path, sample_count: int) -> str:
    """Calls the ``pycmsgen`` library for near-uniform sampling.

    Unlike ``pyunigen`` which returns multiple samples in one call, ``pycmsgen``
    returns one sample per ``solve()`` call. To collect multiple samples, a new
    ``Solver`` is created with a different random seed for each sample.

    :param input_file:
        Path to a CNF file to sample from.

    :param sample_count:
        Number of samples requested.

    :returns:
        Formatted sample output :class:`str` matching CMSGen binary format.
    """
    if not HAS_PYCMSGEN:
        raise ImportError("pycmsgen not available")

    clauses, sampling_set, num_vars = parse_cnf_file(input_file)

    if not clauses:
        return ""

    if not sampling_set:
        sampling_set = list(range(1, num_vars + 1))

    try:
        output_lines = []
        for i in range(sample_count):
            seed = random.randint(999999999)
            solver = pycmsgen.Solver(seed=int(seed))
            for clause in clauses:
                solver.add_clause(clause)

            sat, solution = solver.solve()

            if not sat:
                return ""

            sample_lits = []
            for var in sampling_set:
                if var < len(solution) and solution[var]:
                    sample_lits.append(str(var))
                else:
                    sample_lits.append(str(-var))

            sample_str = "v " + " ".join(sample_lits) + " 0"
            output_lines.append(sample_str)

        return "\n".join(output_lines) + "\n"

    except Exception as e:
        raise UnigenError(-1, str(e), f"pycmsgen sampling failed: {e}")


def call_unigen_docker(input_file: Path, sample_count: int) -> Tuple[CompletedProcess, str]:
    """Calls Unigen in a Docker container, reading a given file as the input problem."""
    unigen_container = 'msoos/unigen'
    input_bytes = input_file.read_bytes()
    args = shell_split("--rm -i -a stdin -a stdout")
    result = docker_run(unigen_container, args, input_bytes)
    return (result, "")


def call_unigen_cli(input_file: Path,
                    download_if_missing: bool,
                    sample_count: int,
                    use_cmsgen: bool) -> Tuple[CompletedProcess, str]:
    """Calls Unigen or CMSGen from the command line, reading a given file as the input problem.

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
        with temporary_cnf_file(suffix=".out") as output_file:
            command.append("--samplefile="+output_file.name)
            result = run(command, capture_output=True)
            with open(output_file, 'r') as output:
                samples = output.read()
                return (result, samples)
    else:
        result = run(command, capture_output=True)
        return (result, "")


def call_unigen(sample_count: int,
                input_file: Path,
                docker_mode: bool = DEFAULT_DOCKER_MODE_ON,
                download_if_missing: bool = DEFAULT_DOWNLOAD_IF_MISSING,
                use_cmsgen: bool = False,
                use_python: bool = True
                ) -> str:
    """Calls Unigen or CMSGen with the given file as input.

    If ``use_python`` is ``True`` and the appropriate Python library is installed
    (pyunigen for UniGen, pycmsgen for CMSGen), this will use the Python-based
    library (recommended for Windows).

    If ``use_cmsgen`` is ``True``, CMSGen sampler is used instead of UniGen.

    If ``docker_mode`` is ``True``, this will use a Docker container to run
    Unigen/CMSGen. If it's ``False``, a command-line executable will be used.

    If ``docker_mode`` is ``False`` and no local Unigen executable can be
    found, and if ``download_if_missing`` is ``True``, the needed executable
    will be automatically downloaded if it's missing.
    """
    # Priority for UniGen: Python → Docker → Binary
    # Priority for CMSGen: Python → Docker → Binary

    if use_python and not docker_mode:
        if use_cmsgen:
            if HAS_PYCMSGEN:
                try:
                    return call_cmsgen_python(input_file, sample_count)
                except ImportError:
                    pass
                except Exception as e:
                    warnings.warn(
                        f"pycmsgen failed ({e}), falling back to binary",
                        UserWarning,
                        stacklevel=2
                    )
        else:
            if HAS_PYUNIGEN:
                try:
                    return call_unigen_python(input_file, sample_count)
                except ImportError:
                    pass
                except Exception as e:
                    warnings.warn(
                        f"pyunigen failed ({e}), falling back to binary",
                        UserWarning,
                        stacklevel=2
                    )
    
    # Fall back to Docker or binary
    if docker_mode:
        (result, samples) = call_unigen_docker(input_file, sample_count)
    else:
        (result, samples) = call_unigen_cli(input_file, download_if_missing, 
                                            sample_count, use_cmsgen)
    
    if result.returncode == (10 if use_cmsgen else 0):
        return result.stdout.decode() + samples
    else:
        stdout = result.stdout.decode()
        stderr = result.stderr.decode()
        
        # Check for Windows DLL error
        if result.returncode == 3221225595:
            solver_name = "CMSGen" if use_cmsgen else "UniGen"
            friendly_message = f"""
Windows DLL Error: {solver_name} binary is missing Visual C++ dependencies.

SOLUTIONS:
"""
            if not use_cmsgen:
                friendly_message += """1. Use Python mode (recommended): pip install pyunigen
2. Use Docker mode: Set docker_mode=True
3. Install Visual C++ Redistributable 2015-2022:
   - x64: https://aka.ms/vs/17/release/vc_redist.x64.exe
   - x86: https://aka.ms/vs/17/release/vc_redist.x86.exe
"""
            else:
                friendly_message += """1. Use Python mode (recommended): pip install pycmsgen
2. Use Docker mode: Set docker_mode=True
3. Install Visual C++ Redistributable 2015-2022:
   - x64: https://aka.ms/vs/17/release/vc_redist.x64.exe
   - x86: https://aka.ms/vs/17/release/vc_redist.x86.exe
"""
            raise UnigenError(result.returncode, stdout, friendly_message)
        
        if "The input formula is unsatisfiable" in stdout:
            return ""
        
        raise UnigenError(result.returncode, stdout, stderr)