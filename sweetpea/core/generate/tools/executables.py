"""This module makes it easy to set up the Unigen and CryptoMiniSAT executables
as needed by Sweetpea. It can also be run as a script.

.. note::

    SweetPea Core only makes use of the automated download of the current
    system and machine-type's executables from the latest release. The rest of
    the code accommodates other use cases and is not strictly necessary, but it
    took a bit of reading to suss out GitHub's API so I figured I'd leave it in
    place for future use if necessary. But perhaps it should be removed at some
    point.

Using This Module As a Script
=============================

To use this module as a script, do ``python executables.py`` (specifying the
full path as needed). A number of options are supported:

-h, --help
    Show a help message and exit.

-d BIN_DIR, --bin-dir BIN_DIR
    The directory into which to install the executables.

    The default is determined by :func:`appdirs.user_data_dir` +
    ``SweetPea/Executables``.

-s SYSTEM, --system SYSTEM
    The target system. Valid options are ``None``, ``Darwin``, ``Linux``, and
    ``Windows``. When ``None`` is given, the system will be automatically
    deduced by :func:`platform.system`.

    The default is ``None``.

-m MACHINE, --machine MACHINE
    The target machine type. Valid options are ``None``, ``arm64``, ``x86_64``,
    and ``AMD64``. When ``None`` is given, the machine type will be
    automatically deduced by :func:`platform.machine`.

    The default is ``None``.

-t TAG, --tag TAG
    The `sweetpea-org/unigen-exe <https://github.com/sweetpea-org/unigen-exe>`_
    release tag to target for downloading.

    The default is to use the latest available release tag.

--asset-string
    Prints out the asset string for the indicated system+machine combination.
    This is provided mostly for debugging.
"""


import platform
import stat

from appdirs import user_data_dir
from itertools import groupby
from json import loads as load_json
from os import chmod, environ
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import Any, Dict, Iterator, List, Optional, Tuple
from urllib.request import Request, urlopen
from zipfile import ZipFile, ZipInfo


__all__ = [
    # We export the environment variable names so they will be documented.
    'DOWNLOAD_UNIGEN_ENV_VAR', 'UNIGEN_EXE_ENV_VAR',
    # The rest of the exports are for use in other modules.
    'CRYPTOMINISAT_EXE', 'DEFAULT_DOWNLOAD_IF_MISSING', 'UNIGEN_EXE', 'CMSGEN_EXE',
    'ensure_executable_available'
]


JSONDict = Dict[str, Any]

#: The name of the environment variable that can be used to specify whether the
#: bundled executables should be downloaded. The default value is ``True``.
#: Valid options are:
#:
#: ===============================  ================================================================
#: Download executables if missing  ``True``, ``true``, ``T``, ``t``, ``Yes``, ``yes``, ``Y``, ``y``
#: Do not download executables      ``False``, ``false``, ``F``, ``f``, ``No``, ``no``, ``N``, ``n``
#: ===============================  ================================================================
DOWNLOAD_UNIGEN_ENV_VAR = 'UNIGEN_DOWNLOAD_IF_MISSING'
if DOWNLOAD_UNIGEN_ENV_VAR in environ:
    download_if_missing = environ[DOWNLOAD_UNIGEN_ENV_VAR]
    if download_if_missing in ('True', 'true', 'T', 't', 'Yes', 'yes', 'Y', 'y'):
        DEFAULT_DOWNLOAD_IF_MISSING = True
    elif download_if_missing in ('False', 'false', 'F', 'f', 'No', 'no', 'N', 'n'):
        DEFAULT_DOWNLOAD_IF_MISSING = False
    else:
        raise RuntimeError(f"Invalid {DOWNLOAD_UNIGEN_ENV_VAR} value: {download_if_missing}. Please use 'True' or 'False'.")
else:
    DEFAULT_DOWNLOAD_IF_MISSING = True

UNIGEN_EXE_LATEST_RELEASE_URL = "https://api.github.com/repos/sweetpea-org/unigen-exe/releases/latest"
UNIGEN_EXE_SPECIFIC_TAG_URL = "https://api.github.com/repos/sweetpea-org/unigen-exe/releases/tags/{tag}"

_ASSET_NAMES = {
    ('Darwin',  'arm64'):  'mac-apple-silicon',
    ('Darwin',  'x86_64'): 'mac-intel',
    ('Linux',   'x86_64'): 'linux-x86_64',
    ('Windows', 'x86_64'): 'win-x64',  # TODO: Verify that this is needed.
    ('Windows', 'AMD64'):  'win-x64',
}

_VALID_ASSETS = {k: list(p[1] for p in v) for k, v in groupby(_ASSET_NAMES.keys(), lambda p: p[0])}

#: The folder in which executables will be stored if they are going to be
#: downloaded. The default is an automatically generated directory in the
#: user's data directory as determined by :func:`appdirs.user_data_dir`.
UNIGEN_EXE_ENV_VAR = 'UNIGEN_EXE_DIR'
if UNIGEN_EXE_ENV_VAR in environ:
    EXE_BIN_LOCATION = Path(environ[UNIGEN_EXE_ENV_VAR])
else:
    EXE_BIN_LOCATION = Path(user_data_dir('SweetPea', 'SweetPea-Org')) / 'Executables'


def _build_exe_name(base_name: str) -> Path:
    path = EXE_BIN_LOCATION / base_name
    if platform.system() == 'Windows':
        path = path.with_suffix('.exe')
    return path


# The various executables we provide.
APPROXMC_EXE = _build_exe_name('approxmc')
CRYPTOMINISAT_EXE = _build_exe_name('cryptominisat5')
UNIGEN_EXE = _build_exe_name('unigen')
CMSGEN_EXE = _build_exe_name('cmsgen')

# An easy-to-use collection of the paths.
EXECUTABLE_PATHS = [
    APPROXMC_EXE,
    CRYPTOMINISAT_EXE,
    UNIGEN_EXE,
    CMSGEN_EXE,
]


def _select_asset_for_host_platform() -> Tuple[str, str]:
    """Select the correct asset for the host platform."""
    system = platform.system()
    machine = platform.machine()
    if system not in _VALID_ASSETS:
        raise RuntimeError(f"Unsupported system: {system}")
    if machine not in _VALID_ASSETS[system]:
        raise RuntimeError(f"Unsupported {system} machine type: {machine}")
    return system, machine


def _get_asset_path(system: Optional[str], machine: Optional[str]) -> str:
    """Retrieves the name of the appropriate release asset."""
    if system is None and machine is None:
        return _ASSET_NAMES[_select_asset_for_host_platform()]
    elif system is not None and machine is not None:
        return _ASSET_NAMES[(system, machine)]
    else:
        # We don't allow one or the other --- it must be both or neither.
        raise RuntimeError(f"Must specify (a) both system and machine or (b) neither. Got system: {system}, machine: {machine}")


def _get_asset_zip(system: Optional[str], machine: Optional[str]) -> str:
    """Retrieves the ``.zip`` name of the appropriate release asset."""
    return _get_asset_path(system, machine) + '.zip'


def _get_release_from_url(url: str) -> List[JSONDict]:
    """Queries the GitHub API to get the assets corresponding to a release
    specified by the given URL.
    """
    response = urlopen(url)
    response_bytes = response.read()
    response_text = response_bytes.decode()
    response_json = load_json(response_text)
    return [asset for asset in response_json['assets']]


def get_latest_release_assets() -> List[JSONDict]:
    """Returns a list of JSON dictionaries, each corresponding to an asset in
    the latest release of the `sweetpea-org/unigen-exe repository
    <https://github.com/sweetpea-org/unigen-exe>`_.
    """
    return _get_release_from_url(UNIGEN_EXE_LATEST_RELEASE_URL)


def get_specific_release(tag: str) -> List[JSONDict]:
    """Returns a list of JSON dictionaries, each corresponding to an asset in
    the indicated release of the `sweetpea-org/unigen-exe repository
    <https://github.com/sweetpea-org/unigen-exe>`_..
    """
    url = UNIGEN_EXE_SPECIFIC_TAG_URL.format(tag=tag)
    return _get_release_from_url(url)


def ensure_dir_path_exists(path: Path):
    """Make sure the specified path is a directory and that it and all its
    parents exist.
    """
    path.mkdir(parents=True, exist_ok=True)


def get_asset_url_for_release(system: Optional[str] = None,
                              machine: Optional[str] = None,
                              tag: Optional[str] = None
                              ) -> str:
    """Produces the URL corresponding to the indicated asset for the
    appropriate release. If ``system`` and ``machine`` are unspecified, they
    will be deduced automatically from the host platform's self-report
    information. If the ``tag`` is unspecified, the latest release will be
    used.
    """
    # First resolve the needed asset name.
    asset_zip_name = _get_asset_zip(system, machine)
    # Then we obtain the appropriate list of assets for the correct release.
    if tag is None:
        release_assets = get_latest_release_assets()
    else:
        release_assets = get_specific_release(tag)
    # Now we search the assets for our desired asset.
    matches = [asset for asset in release_assets if asset['name'] == asset_zip_name]
    if len(matches) != 1:
        raise RuntimeError(f"Did not find exactly one asset named {asset_zip_name} for "
                           f"{'release on tag ' + tag if tag is not None else 'latest release'}.")
    asset = matches[0]
    asset_url = asset['url']
    return asset_url


def download_and_extract_asset_zip_for_release(to_bin_dir: Path,
                                               system: Optional[str] = None,
                                               machine: Optional[str] = None,
                                               tag: Optional[str] = None
                                               ) -> Iterator[Path]:
    """Fetches the ``.zip`` archive corresponding to the indicated system and
    machine from the indicated tag, or else use the automatically deduced
    system and machine from the latest release.
    """
    asset_url = get_asset_url_for_release(system, machine, tag)
    ensure_dir_path_exists(to_bin_dir)
    request = Request(asset_url)
    request.add_header('Accept', 'application/octet-stream')
    # We first have to download the .zip archive to a temporary file.
    # NOTE: I did try to implement this without the intermediate save-to-a-
    #       temp-file step, but the ZipFile initializer seems to not like
    #       accepting the url_file as an argument (even though I think the
    #       latter is a "file-like object" and ZipFile claims it accepts
    #       those).
    with NamedTemporaryFile(suffix='.zip') as temp_file:
        temp_file.close()
        temp_file_path = Path(temp_file.name)
        with urlopen(request) as url_file:
            temp_file_path.write_bytes(url_file.read())
        # With the file downloaded, we can extract its contents.
        zf = ZipFile(temp_file_path)
        internal_base_asset_path = _get_asset_path(system, machine) + '/'
        write_buffer: List[Tuple[ZipInfo, Path]] = []
        for zipinfo in zf.infolist():
            if zipinfo.filename == internal_base_asset_path:
                # We don't do anything with the base path.
                continue
            if zipinfo.filename.startswith(internal_base_asset_path):
                # We do a reprocessing pass to ensure none of the paths we
                # want to write to are already occupied. If they are, we refuse
                # to extract anything.
                sub_path = Path(zipinfo.filename).relative_to(internal_base_asset_path)
                new_path = to_bin_dir / sub_path
                if new_path.is_file():
                    # We'll need to do something different here one day when we
                    # want to update existng executables...
                    print(f"File exists; no contents extracted from zip: {new_path}")
                else:
                    write_buffer.append((zipinfo, new_path))
            else:
                # We only extract the needed contents.
                continue
        # Now we go through and actually perform the extractions.
        for zipinfo, new_path in write_buffer:
            new_path.write_bytes(zf.read(zipinfo))
            yield new_path


def ensure_executable_permissions(executable_path: Path):
    """Set permissions on the indicated executable such that the file owner can
    read, write, or execute it, and the owner's group and other users can read
    and execute it.
    """
    # chmod 755 executable_path
    chmod(executable_path,
          stat.S_IRWXU | stat.S_IRGRP | stat.S_IXGRP | stat.S_IROTH | stat.S_IXOTH)


def download_executables(to_bin_dir: Optional[Path] = None,
                         system: Optional[str] = None,
                         machine: Optional[str] = None,
                         tag: Optional[str] = None):
    """Performs the download and extraction of the bundled executables."""
    if to_bin_dir is None:
        to_bin_dir = EXE_BIN_LOCATION
    print(f"Downloading and extracting SweetPea executables to {to_bin_dir}...")
    for extracted_path in download_and_extract_asset_zip_for_release(to_bin_dir, system, machine, tag):
        print(f"    {extracted_path}")
    for executable_path in EXECUTABLE_PATHS:
        ensure_executable_permissions(executable_path)
    print("Done.")


def ensure_executable_available(executable_path: Path, download_if_missing: bool = DEFAULT_DOWNLOAD_IF_MISSING):
    """Checks whether a given necessary executable is available and, if not,
    downloads it (and its companions) automatically.
    """
    if executable_path in EXECUTABLE_PATHS and not executable_path.is_file():
        if download_if_missing:
            download_executables()
        else:
            raise RuntimeError(f"Could not find binary: {executable_path}")


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('-d', '--bin-dir', type=Path, default=EXE_BIN_LOCATION,
                        help=f"the directory to install executables to; default is: {EXE_BIN_LOCATION}")
    parser.add_argument('-s', '--system', choices=['None'] + [p[0] for p in _ASSET_NAMES.keys()], default='None',
                        help="the target system; default is determined platform.system()")
    parser.add_argument('-m', '--machine', choices=['None'] + [p[1] for p in _ASSET_NAMES.keys()], default='None',
                        help="the target machine type; default is determined by platform.machine()")
    parser.add_argument('-t', '--tag', default=None,
                        help="the unigen-exe tag to target; default is the latest tag available")
    parser.add_argument('--asset-string', action='store_true',
                        help="only print out the asset string for the indicated system+machine combination")
    args = parser.parse_args()

    if args.system == 'None':
        args.system = None
    if args.machine == 'None':
        args.machine = None

    if args.asset_string:
        print(_get_asset_path(system=args.system, machine=args.machine))
    else:
        download_executables(
            to_bin_dir=args.bin_dir,
            system=args.system,
            machine=args.machine,
            tag=args.tag)
