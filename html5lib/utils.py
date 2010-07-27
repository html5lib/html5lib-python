from __future__ import absolute_import, division, unicode_literals

from types import ModuleType

from .constants import invisibleChars


class MethodDispatcher(dict):
    """Dict with 2 special properties:

    On initiation, keys that are lists, sets or tuples are converted to
    multiple keys so accessing any one of the items in the original
    list-like object returns the matching value

    md = MethodDispatcher({("foo", "bar"):"baz"})
    md["foo"] == "baz"

    A default value which can be set through the default attribute.
    """

    def __init__(self, items=()):
        # Using _dictEntries instead of directly assigning to self is about
        # twice as fast. Please do careful performance testing before changing
        # anything here.
        _dictEntries = []
        for name, value in items:
            if type(name) in (list, tuple, frozenset, set):
                for item in name:
                    _dictEntries.append((item, value))
            else:
                _dictEntries.append((name, value))
        dict.__init__(self, _dictEntries)
        self.default = None

    def __getitem__(self, key):
        return dict.get(self, key, self.default)


# Some utility functions to dal with weirdness around UCS2 vs UCS4
# python builds

def isSurrogatePair(data):
    return (len(data) == 2 and
            ord(data[0]) >= 0xD800 and ord(data[0]) <= 0xDBFF and
            ord(data[1]) >= 0xDC00 and ord(data[1]) <= 0xDFFF)


def surrogatePairToCodepoint(data):
    char_val = (0x10000 + (ord(data[0]) - 0xD800) * 0x400 +
                (ord(data[1]) - 0xDC00))
    return char_val

# Module Factory Factory (no, this isn't Java, I know)
# Here to stop this being duplicated all over the place.


def moduleFactoryFactory(factory):
    moduleCache = {}

    def moduleFactory(baseModule, *args, **kwargs):
        if isinstance(ModuleType.__name__, type("")):
            name = "_%s_factory" % baseModule.__name__
        else:
            name = b"_%s_factory" % baseModule.__name__

        if name in moduleCache:
            return moduleCache[name]
        else:
            mod = ModuleType(name)
            objs = factory(baseModule, *args, **kwargs)
            mod.__dict__.update(objs)
            moduleCache[name] = mod
            return mod

    return moduleFactory


def escapeInvisible(text, useNamedEntities=False):
    """Escape invisible characters other than Tab, LF, CR, and ASCII space
    """
    assert type(text) == text_type
    # This algorithm is O(MN) for M len(text) and N num escapable
    # But it doesn't modify the text when N is zero (common case) and
    # N is expected to be small (usually 1 or 2) in most other cases.
    escapable = set()
    for c in text:
        if ord(c) in invisibleChars:
            escapable.add(c)
    if useNamedEntities:
        raise NotImplementedError("This doesn't work on Python 3")
        for c in escapable:
            name = codepoint2name.get(ord(c))
            escape = "&%s;" % name if name else "&#x%X;" % ord(c)
            text = text.replace(c, escape)
    else:
        for c in escapable:
            text = text.replace(c, "&#x%X;" % ord(c))

    return text
