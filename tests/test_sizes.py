from __future__ import annotations

import pytest

from notion_bg_gen.errors import UsageError
from notion_bg_gen.sizes import NAMED_SIZES, parse_size


@pytest.mark.parametrize("name", list(NAMED_SIZES))
def test_named_sizes_resolve(name):
    assert parse_size(name) == NAMED_SIZES[name]


def test_named_sizes_are_case_insensitive():
    assert parse_size("COVER@2X") == NAMED_SIZES["cover@2x"]


@pytest.mark.parametrize("raw", ["1500x600", "1500X600", " 1500 x 600 ", "1500×600"])
def test_custom_sizes(raw):
    assert parse_size(raw) == (1500, 600)


@pytest.mark.parametrize("raw", ["nope", "0x0", "10x10", "99999x100", "1500", "x600", "-5x5"])
def test_rejects_bad_sizes(raw):
    with pytest.raises(UsageError):
        parse_size(raw)
