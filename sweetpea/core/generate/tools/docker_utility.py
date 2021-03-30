"""This module provides simple Docker command-line functionality. It is
generally discouraged to use this functionality, as we prefer using the bundled
executables from `sweetpea-org/unigen-exe
<https://github.com/sweetpea-org/unigen-exe>`_. However, these executables may
lag behind their respective repositories, so we provide the Docker
functionality to stay on the cutting edge.
"""


from subprocess import CompletedProcess, run
from typing import List, Optional

from .return_code import ReturnCodeEnum


#: Whether Docker should be used by default.
DEFAULT_DOCKER_MODE_ON = False


class DockerRunReturnCode(ReturnCodeEnum):
    """Invocation of the ``docker run`` command can result in one of the
    following special return codes. Any other return code is the result of
    invoking the indicated command in the container.

    Based on `this reference information
    <https://docs.docker.com/engine/reference/run/#exit-status>`_.
    """

    #: There was an error executing the Docker daemon itself.
    DockerDaemonError                    = 125
    #: The command produced an error in the container.
    ContainedCommandCannotBeInvokedError = 126
    #: The command specified could not be found in the container.
    ContainedCommandCannotBeFoundError   = 127


class DockerRunError(Exception):
    """An error raised when something fails while invoking Docker."""

    def __init__(self, returncode: DockerRunReturnCode, stderr: str):
        super().__init__(f"Error running Docker: {returncode.name}\n    stderr output captured below:\n\n{stderr}")


def docker_run(container: str,
               args: Optional[List[str]] = None,
               input_bytes: Optional[bytes] = None) -> CompletedProcess:
    """Runs a Docker container, with the optional arguments and input if
    provided.

    If the execution produces an error, a :class:`DockerRunError` will be
    raised.
    """
    if args is None:
        args = []
    command = ['docker', 'run', *args, container]
    # NOTE: flake8 doesn't seem to handle the calls to `run` correctly, but
    #       mypy reports everything is fine here so we `noqa` to prevent flake8
    #       complaining about what it doesn't understand.
    result = run(command, capture_output=True, input=input_bytes)  # noqa
    if DockerRunReturnCode.has_value(result.returncode):
        code = DockerRunReturnCode(result.returncode)
        raise DockerRunError(code, result.stderr.decode())
    return result
