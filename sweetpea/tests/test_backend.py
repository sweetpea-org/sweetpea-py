import json
import pytest

from sweetpea.logic import And, Or
from sweetpea.backend import LowLevelRequest, BackendRequest


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


def test_backend_request_to_request_data():
    fresh = 34
    cnfs = [And([Or([1, 2, 3])]),
            And([Or([-4, 5, -6])])]
    requests = [
        LowLevelRequest("EQ", 1, [5, 10, 15, 20]),
        LowLevelRequest("LT", 3, [1, 2, 3, 4])]

    backend_request = BackendRequest(fresh, cnfs, requests)
    result = backend_request.to_request_data(24, 100, 24)

    # The backend assumes fresh was the last allocated variable, not the next available variable,
    # so we need to subtract 1 before handing it off.
    assert result['fresh'] == 33
    assert result['unigen']['support'] == 24
    assert len(result['unigen']['arguments']) > 0
    assert "--samples=100" in result['unigen']['arguments']

    assert result['cnfs'] == [[1, 2, 3], [-4, 5, -6]]
    assert result['requests'] == [
        {"equalityType": "EQ", "k": 1, "booleanValues": [5, 10, 15, 20]},
        {"equalityType": "LT", "k": 3, "booleanValues": [1, 2, 3, 4]}
    ]
