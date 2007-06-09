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
        preserve = False
        for token in _base.Filter.__iter__(self):
            type = token["type"]
            if not preserve and type == "StartTag" \
              and token["name"] in self.spacePreserveElements:
                preserve = True

            elif type == "EndTag":
                preserve = False

            elif not preserve and type == "SpaceCharacters":
                continue

            elif not preserve and type == "Characters":
                token["data"] = collapse_spaces(token["data"])

            yield token

def collapse_spaces(text):
    return re.compile(u"[%s]+" % spaceCharacters).sub(' ', text)

