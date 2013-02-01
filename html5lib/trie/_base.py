from __future__ import absolute_import
from collections import Mapping

class Trie(Mapping):
    u"""Abstract base class for tries"""

    def keys(self, prefix=None):
        keys = super(Trie, self).keys()

        if prefix is None:
            return set(keys)

        return set(x for x in keys if x.startswith(prefix))
    keys.func_annotations = {}

    def has_keys_with_prefix(self, prefix):
        for key in self.keys():
            if key.startswith(prefix):
                return True

        return False
    has_keys_with_prefix.func_annotations = {}

    def longest_prefix(self, prefix):
        if prefix in self:
            return prefix

        for i in xrange(1, len(prefix) + 1):
            if prefix[:-i] in self:
                return prefix[:-i]

        raise KeyError(prefix)
    longest_prefix.func_annotations = {}

    def longest_prefix_item(self, prefix):
        lprefix = self.longest_prefix(prefix)
        return (lprefix, self[lprefix])
    longest_prefix_item.func_annotations = {}
