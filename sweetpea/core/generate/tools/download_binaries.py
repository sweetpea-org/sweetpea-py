"""This script makes it easy to set up Unigen as needed by Sweetpea."""


import platform

from json import loads as load_json
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import Any, Dict, Iterator, List, Optional, Tuple
from urllib.request import Request, urlopen
from zipfile import ZipFile, ZipInfo


__all__ = ['guided_download']


JSONDict = Dict[str, Any]


UNIGEN_EXE_LATEST_RELEASE_URL = "https://api.github.com/repos/sweetpea-org/unigen-exe/releases/latest"
UNIGEN_EXE_SPECIFIC_TAG_URL = "https://api.github.com/repos/sweetpea-org/unigen-exe/releases/tags/{tag}"

DEFAULT_EXE_BIN_LOCATION = Path('~').expanduser() / '.sweetpea' / 'bin'

_ASSET_NAMES = {
    ('Darwin', 'arm64'): 'mac-apple-silicon',
    ('Darwin', 'x86_64'): 'mac-intel',
    ('Linux', 'x86_64'): 'linux-x86_64',
    ('Windows', 'x86_64'): 'win-x64',
}


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
        write_buffer: List[ZipInfo, Path] = []
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


def download(to_bin_dir: Path, system: str, machine: str, tag: Optional[str]):
    """Perform the download and extraction!"""
    print("Downloading and extracting files...")
    for extracted_path in download_and_extract_asset_zip_for_release(to_bin_dir, system, machine, tag):
        print(f"    {extracted_path}")
    print("Done. You may want to adjust your PATH in your shell's configuration:")
    print(f"    PATH=\"{to_bin_dir}:$PATH\"")


def guided_download():
    """Performs the download, prompting the user for each input."""

    def prompt(query: str, default: Any, choices: Optional[List[Any]] = None) -> str:
        print(query)
        print(f"    Default: {default}")
        if choices is not None:
            print(f"    Choices: {choices}")
        result = input(" > ")
        if result:
            return result
        return str(default)

    print("Attempting automated download of SweetPea dependency binaries.")
    print("For each prompt, either select the default by pressing RETURN or input a new value followed by RETURN.")
    to_bin_dir = prompt("Where would you like to place the binaries?", DEFAULT_EXE_BIN_LOCATION)
    system = prompt("What system do you use?", platform.system(), list({system for system, _ in _ASSET_NAMES.keys()}))
    machine = prompt("What machine type do you use?", platform.machine(), list({machine for _, machine in _ASSET_NAMES.keys()}))
    tag = prompt("What release tag would you like to use?", 'latest')
    if tag == 'latest':
        tag = None
    download(to_bin_dir, system, machine, tag)


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--to-bin_dir', type=Path, default=DEFAULT_EXE_BIN_LOCATION,
                        help=f"the directory to extract files to; default: {DEFAULT_EXE_BIN_LOCATION}")
    parser.add_argument('--system', choices=list({system for system, _ in _ASSET_NAMES.keys()}),
                        help=f"the system type, default: {platform.system()}")
    parser.add_argument('--machine', choices=list({machine for _, machine in _ASSET_NAMES.keys()}),
                        help=f"the machine type; default: {platform.machine()}")
    parser.add_argument('--tag',
                        help="the release tag to use; defaults to the latest release available")
    args = parser.parse_args()

    download(args.to_bin_dir, args.sytem, args.machine, args.tag)
