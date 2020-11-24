from pathlib import Path

from ..parser import JSONSpec, process_requests


DEFAULT_LL_CONSTRAINTS_FILE = Path("ll_constraints.json")


def process_constraints_file(constraints_file: Path) -> str:
    contents = constraints_file.read_text()
    spec = JSONSpec.decode(contents)
    if spec is None:
        raise ValueError(f"Improperly formatted requests file: {constraints_file.absolute()}")
    else:
        return process_requests(spec)


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--constraints', type=Path, default=DEFAULT_LL_CONSTRAINTS_FILE,
                        help="The JSON constraints file to load data from.")
    args = parser.parse_args()
    print(process_constraints_file(args.constraints))
