import pytest

from sweetpea.primitives import Factor


def test_factor_validation():
	Factor("factor name", ["level 1", "level 2"])

	# Non-string name
	with pytest.raises(ValueError):
		Factor(56, ["level "])

	# Non-list levels
	with pytest.raises(ValueError):
		Factor("name", 42)

	# Empty list
	with pytest.raises(ValueError):
		Factor("name", [])