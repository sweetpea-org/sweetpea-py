"""This module checks whether binaries are installed and, if not, offers to
download them for the user.
"""


from subprocess import run

from .download_binaries import guided_download


__all__ = ['check_binary_available']


def binary_is_available(name: str) -> bool:
    """Tests whether a given binary command is available on the user's PATH."""
    result = run(["command", "-v", name], capture_output=True)
    if result.returncode == 0:
        return True
    elif result.returncode == 1:
        return False
    else:
        raise RuntimeError(f"Unknown error encountered while checking binary availability:\n{result.stderr}")


def check_binary_available(name: str, download_if_unavailable: bool = True):
    # TODO DOC
    if not binary_is_available(name):
        if download_if_unavailable:
            guided_download()
        else:
            raise RuntimeError(f"Could not find executable on $PATH: {name}")
