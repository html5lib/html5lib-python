# Copyright (c) 2006-2013 James Graham and other contributors
#
# Permission is hereby granted, free of charge, to any person obtaining
# a copy of this software and associated documentation files (the
# "Software"), to deal in the Software without restriction, including
# without limitation the rights to use, copy, modify, merge, publish,
# distribute, sublicense, and/or sell copies of the Software, and to
# permit persons to whom the Software is furnished to do so, subject to
# the following conditions:
#
# The above copyright notice and this permission notice shall be
# included in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
# MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
# NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE
# LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION
# OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION
# WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

from __future__ import absolute_import, division, unicode_literals

from datrie import Trie as DATrie
from six import text_type

from ._base import Trie as ABCTrie


class Trie(ABCTrie):
    def __init__(self, data):
        chars = set()
        for key in data.keys():
            if not isinstance(key, text_type):
                raise TypeError("All keys must be strings")
            for char in key:
                chars.add(char)

        self._data = DATrie("".join(chars))
        for key, value in data.items():
            self._data[key] = value

    def __contains__(self, key):
        return key in self._data

    def __len__(self):
        return len(self._data)

    def __iter__(self):
        raise NotImplementedError()

    def __getitem__(self, key):
        return self._data[key]

    def keys(self, prefix=None):
        return self._data.keys(prefix)

    def has_keys_with_prefix(self, prefix):
        return self._data.has_keys_with_prefix(prefix)

    def longest_prefix(self, prefix):
        return self._data.longest_prefix(prefix)

    def longest_prefix_item(self, prefix):
        return self._data.longest_prefix_item(prefix)
