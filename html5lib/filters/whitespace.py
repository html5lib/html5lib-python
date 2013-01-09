from __future__ import absolute_import
try:
    frozenset
except NameError:
    # Import from the sets module for python 2.3
    from sets import ImmutableSet as frozenset

import re

from . import _base
from html5lib.constants import rcdataElements, spaceCharacters
spaceCharacters = u"".join(spaceCharacters)

SPACES_REGEX = re.compile(u"[%s]+" % spaceCharacters)

class Filter(_base.Filter):

    spacePreserveElements = frozenset([u"pre", u"textarea"] + list(rcdataElements))

    def __iter__(self):
        preserve = 0
        for token in _base.Filter.__iter__(self):
            type = token[u"type"]
            if type == u"StartTag" \
              and (preserve or token[u"name"] in self.spacePreserveElements):
                preserve += 1

            elif type == u"EndTag" and preserve:
                preserve -= 1

            elif not preserve and type == u"SpaceCharacters" and token[u"data"]:
                # Test on token["data"] above to not introduce spaces where there were not
                token[u"data"] = u" "

            elif not preserve and type == u"Characters":
                token[u"data"] = collapse_spaces(token[u"data"])

            yield token
    __iter__.func_annotations = {}

def collapse_spaces(text):
    return SPACES_REGEX.sub(u' ', text)
collapse_spaces.func_annotations = {}

