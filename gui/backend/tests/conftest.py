import sys
from pathlib import Path

# CI runs pytest from outside the repository without installing anything, so the tests
# import sweetpea_gui from gui/backend and sweetpea from the repository root.
HERE = Path(__file__).resolve()
for path in (HERE.parents[1], HERE.parents[3]):
    sys.path.insert(0, str(path))
