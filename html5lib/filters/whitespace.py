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

import re

from . import base
from ..constants import rcdataElements, spaceCharacters
spaceCharacters = "".join(spaceCharacters)

SPACES_REGEX = re.compile("[%s]+" % spaceCharacters)


class Filter(base.Filter):

    spacePreserveElements = frozenset(["pre", "textarea"] + list(rcdataElements))

    def __iter__(self):
        preserve = 0
        for token in base.Filter.__iter__(self):
            type = token["type"]
            if type == "StartTag" \
                    and (preserve or token["name"] in self.spacePreserveElements):
                preserve += 1

            elif type == "EndTag" and preserve:
                preserve -= 1

            elif not preserve and type == "SpaceCharacters" and token["data"]:
                # Test on token["data"] above to not introduce spaces where there were not
                token["data"] = " "

            elif not preserve and type == "Characters":
                token["data"] = collapse_spaces(token["data"])

            yield token


def collapse_spaces(text):
    return SPACES_REGEX.sub(' ', text)
