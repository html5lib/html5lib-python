from __future__ import absolute_import
from itertools import chain

from datrie import Trie as DATrie

from ._base import Trie as ABCTrie

class Trie(ABCTrie):
    def __init__(self, data):
        chars = set()
        for key in data.keys():
            if not isinstance(key, unicode):
                raise TypeError(u"All keys must be strings")
            for char in key:
                chars.add(char)

        self._data = DATrie(u"".join(chars))
        for key, value in data.items():
            self._data[key] = value
    __init__.func_annotations = {}

    def __contains__(self, key):
        return key in self._data
    __contains__.func_annotations = {}

    def __len__(self):
        return len(self._data)
    __len__.func_annotations = {}

    def __iter__(self):
        raise NotImplementedError()
    __iter__.func_annotations = {}

    def __getitem__(self, key):
        return self._data[key]
    __getitem__.func_annotations = {}

    def keys(self, prefix=None):
        return self._data.keys(prefix)
    keys.func_annotations = {}

    def has_keys_with_prefix(self, prefix):
        return self._data.has_keys_with_prefix(prefix)
    has_keys_with_prefix.func_annotations = {}

    def longest_prefix(self, prefix):
        return self._data.longest_prefix(prefix)
    longest_prefix.func_annotations = {}

    def longest_prefix_item(self, prefix):
        return self._data.longest_prefix_item(prefix)
    longest_prefix_item.func_annotations = {}
