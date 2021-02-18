"""This script makes it easy to set up the Unigen and CryptoMiniSAT executables
as needed by Sweetpea.

NOTE: SweetPea Core only makes use of the automated download of the current
      system and machine-type's executables from the latest release. The rest
      of the code accommodates other use cases and is not strictly necessary,
      but it took a bit of reading to suss out GitHub's API so I figured I'd
      leave it in place for future use if necessary. But perhaps it should be
      removed at some point.
"""


import platform
import stat

from appdirs import user_data_dir
from json import loads as load_json
from os import chmod
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import Any, Dict, Iterator, List, Optional, Tuple
from urllib.request import Request, urlopen
from zipfile import ZipFile, ZipInfo


__all__ = ['CRYPTOMINISAT_EXE', 'DEFAULT_DOWNLOAD_IF_MISSING', 'UNIGEN_EXE', 'ensure_executable_available']


JSONDict = Dict[str, Any]

DEFAULT_DOWNLOAD_IF_MISSING = True

UNIGEN_EXE_LATEST_RELEASE_URL = "https://api.github.com/repos/sweetpea-org/unigen-exe/releases/latest"
UNIGEN_EXE_SPECIFIC_TAG_URL = "https://api.github.com/repos/sweetpea-org/unigen-exe/releases/tags/{tag}"

_ASSET_NAMES = {
    ('Darwin', 'arm64'): 'mac-apple-silicon',
    ('Darwin', 'x86_64'): 'mac-intel',
    ('Linux', 'x86_64'): 'linux-x86_64',
    ('Windows', 'x86_64'): 'win-x64',
}

# The folder in which executables will be stored.
EXE_BIN_LOCATION = Path(user_data_dir('SweetPea', 'SweetPea-Org')) / 'Executables'


def _build_exe_name(base_name: str) -> Path:
    path = EXE_BIN_LOCATION / base_name
    if platform.system() == 'Windows':
        path = path.with_suffix('.exe')


# The various executables we provide.
APPROXMC_EXE = _build_exe_name('approxmc')
CRYPTOMINISAT_EXE = _build_exe_name('cryptominisat5')
UNIGEN_EXE = _build_exe_name('unigen')

# An easy-to-use collection of the paths.
EXECUTABLE_PATHS = [
    APPROXMC_EXE,
    CRYPTOMINISAT_EXE,
    UNIGEN_EXE,
]


def _select_asset_for_host_platform() -> Tuple[str, str]:
    """Select the correct asset for the host platform."""
    system = platform.system()
    machine = platform.machine()
    bad_machine = False
    if system == 'Darwin':
        bad_machine = machine not in ('arm64', 'x86_64')
    elif system == 'Linux':
        bad_machine = machine != 'x86_64'
    elif system == 'Windows':
        bad_machine = machine != 'x86_64'
    else:
        raise RuntimeError(f"Unsupported system: {system}")
    if bad_machine:
        raise RuntimeError(f"Unsupported {system} machine type: {machine}")
    return system, machine


def _get_asset_path(system: Optional[str], machine: Optional[str]) -> str:
    """Retrieves the name of the appropriate release asset."""
    if system is None and machine is None:
        system, machine = _select_asset_for_host_platform()
    elif system is not None or machine is not None:
        # We don't allow one or the other --- it must be both or neither.
        raise RuntimeError(f"Must specify (a) both system and machine or (b) neither. Got system: {system}, machine: {machine}")
    return _ASSET_NAMES[(system, machine)]


def _get_asset_zip(system: Optional[str], machine: Optional[str]) -> str:
    """Retrieves the .zip name of the appropriate release asset."""
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
    the latest release of the sweetpea-org/unigen-exe repository.
    """
    return _get_release_from_url(UNIGEN_EXE_LATEST_RELEASE_URL)


def get_specific_release(tag: str) -> List[JSONDict]:
    """Returns a list of JSON dictionaries, each corresponding to an asset in
    the indicated release of the sweetpea-org/unigen-exe repository.
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
    appropriate release. If `system` and `machine` are unspecified, they will
    be deduced automatically from the host platform's self-report information.
    If the `tag` is unspecified, the latest release will be used.
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
    """Fetches the .zip archive corresponding to the indicated system and
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
                    raise RuntimeError(f"File exists; no contents extracted from zip: {new_path}")
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
    """Perform the download and extraction!"""
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
