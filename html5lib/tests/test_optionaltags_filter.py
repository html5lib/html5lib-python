
from html5lib.filters.optionaltags import Filter


def test_empty():
    assert list(Filter([])) == []
