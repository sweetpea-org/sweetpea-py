import json
import pytest

from sweetpea._internal.logic import And, Or
from sweetpea._internal.backend import LowLevelRequest, BackendRequest


def test_low_level_request_validation():
    # Acceptable requests
    LowLevelRequest('EQ', 1, [1, 2, 3])
    LowLevelRequest('LT', 1, [1, 2, 3])
    LowLevelRequest('GT', 1, [1, 2, 3])

    # Invalid comparison
    with pytest.raises(ValueError):
        LowLevelRequest('bad', 1, [1, 2, 3])

    # Non-numeric k
    with pytest.raises(ValueError):
        LowLevelRequest('EQ', '5', [1, 2, 3])
