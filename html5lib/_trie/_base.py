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

from collections import Mapping


class Trie(Mapping):
    """Abstract base class for tries"""

    def keys(self, prefix=None):
        # pylint:disable=arguments-differ
        keys = super(Trie, self).keys()

        if prefix is None:
            return set(keys)

        # Python 2.6: no set comprehensions
        return set([x for x in keys if x.startswith(prefix)])

    def has_keys_with_prefix(self, prefix):
        for key in self.keys():
            if key.startswith(prefix):
                return True

        return False

    def longest_prefix(self, prefix):
        if prefix in self:
            return prefix

        for i in range(1, len(prefix) + 1):
            if prefix[:-i] in self:
                return prefix[:-i]

        raise KeyError(prefix)

    def longest_prefix_item(self, prefix):
        lprefix = self.longest_prefix(prefix)
        return (lprefix, self[lprefix])
