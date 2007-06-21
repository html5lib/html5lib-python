try:
    frozenset
except NameError:
    # Import from the sets module for python 2.3
    from sets import ImmutableSet as frozenset

import re

import _base
from constants import rcdataElements

from constants import spaceCharacters
spaceCharacters = u"".join(spaceCharacters)

class Filter(_base.Filter):
    
    spacePreserveElements = frozenset(["pre", "textarea"] + list(rcdataElements))
    
    def __iter__(self):
        preserve = 0
        for token in _base.Filter.__iter__(self):
            type = token["type"]
            if type == "StartTag" \
              and (preserve or token["name"] in self.spacePreserveElements):
                preserve += 1

            elif type == "EndTag" and preserve:
                preserve -= 1

            elif not preserve and type == "SpaceCharacters":
                continue

            elif not preserve and type == "Characters":
                token["data"] = collapse_spaces(token["data"])

            yield token

def collapse_spaces(text):
    return re.compile(u"[%s]+" % spaceCharacters).sub(' ', text)

