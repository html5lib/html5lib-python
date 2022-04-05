# SPDX-FileCopyrightText: 2006-2021 html5lib contributors. See AUTHORS.rst
#
# SPDX-License-Identifier: MIT

from __future__ import absolute_import, division, unicode_literals

from html5lib.filters.optionaltags import Filter


def test_empty():
    assert list(Filter([])) == []
