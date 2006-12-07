class MethodDispatcher(dict):
    """Dict with 2 special properties:

    On initiation, keys that are lists, sets or tuples are converted to 
    multiple keys so accessing any one of the items in the original 
    list-like object returns the matching value
    
    md = MethodDispatcher({["foo", "bar"]:"baz"})
    md["foo"] == "baz"

    A default value which can be set through the setDefaultValue method
    """

    def __init__(self, items=()):
        _dictEntries = []
        for name,value in items:
            print _dictEntries
            if type(name) in (list, tuple, frozenset, set):
                for item in name:
                    _dictEntries.append((item, value))
            else:
                _dictEntries.append((name, value))
        dict.__init__(self, _dictEntries)
    
    def setDefaultValue(self, value):
        self.defaultValue = value

    def __getitem__(self, key):
        try:
            return dict.__getitem__(self, key)
        except KeyError:
            if hasattr(self, "defaultValue"):
                return self.defaultValue
            else:
                raise

def openSource(source):
    """ Opens source first trying to open a local file, if that fails 
    try to open as a URL and finally treating source as a string.

    Returns a file-like object.
    """
    # Already a file-like object?
    if hasattr(source, 'tell'):
        return source

    # Try opening source normally
    try:
        return open(source)
    except: pass

    # Try opening source as a URL and storing the bytes returned so
    # they can be turned into a file-like object below
    try:
        import urllib
        source = urllib.urlopen(source).read(-1)
    except: pass

    # Treat source as a string and make it into a file-like object
    import cStringIO as StringIO
    return StringIO.StringIO(str(source))