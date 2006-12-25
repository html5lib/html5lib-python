try:
    type(frozenset)
except NameError:
    #Import from the sets module for python 2.3
    from sets import Set as set
    from sets import ImmutableSet as frozenset

class MethodDispatcher(dict):
    """Dict with 2 special properties:

    On initiation, keys that are lists, sets or tuples are converted to
    multiple keys so accessing any one of the items in the original
    list-like object returns the matching value

    md = MethodDispatcher({["foo", "bar"]:"baz"})
    md["foo"] == "baz"

    A default value which can be set through the default attribute.
    """

    def __init__(self, items=()):
        _dictEntries = []
        for name,value in items:
            if type(name) in (list, tuple, frozenset, set):
                for item in name:
                    _dictEntries.append((item, value))
            else:
                _dictEntries.append((name, value))
        dict.__init__(self, _dictEntries)
        self.default = None

    def __getitem__(self, key):
        try:
            return dict.__getitem__(self, key)
        except KeyError:
            if self.default:
                return self.default
            else:
                raise
