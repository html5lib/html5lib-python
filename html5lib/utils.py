from __future__ import absolute_import
try:
    frozenset
except NameError:
    #Import from the sets module for python 2.3
    from sets import Set as set
    from sets import ImmutableSet as frozenset

from types import ModuleType


class MethodDispatcher(dict):
    u"""Dict with 2 special properties:

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
        for name,value in items:
            if type(name) in (list, tuple, frozenset, set):
                for item in name:
                    _dictEntries.append((item, value))
            else:
                _dictEntries.append((name, value))
        dict.__init__(self, _dictEntries)
        self.default = None
    __init__.func_annotations = {}

    def __getitem__(self, key):
        return dict.get(self, key, self.default)
    __getitem__.func_annotations = {}

#Pure python implementation of deque taken from the ASPN Python Cookbook
#Original code by Raymond Hettinger

class deque(object):

    def __init__(self, iterable=(), maxsize=-1):
        if not hasattr(self, u'data'):
            self.left = self.right = 0
            self.data = {}
        self.maxsize = maxsize
        self.extend(iterable)
    __init__.func_annotations = {}

    def append(self, x):
        self.data[self.right] = x
        self.right += 1
        if self.maxsize != -1 and len(self) > self.maxsize:
            self.popleft()
    append.func_annotations = {}
        
    def appendleft(self, x):
        self.left -= 1        
        self.data[self.left] = x
        if self.maxsize != -1 and len(self) > self.maxsize:
            self.pop()      
    appendleft.func_annotations = {}
        
    def pop(self):
        if self.left == self.right:
            raise IndexError(u'cannot pop from empty deque')
        self.right -= 1
        elem = self.data[self.right]
        del self.data[self.right]         
        return elem
    pop.func_annotations = {}
    
    def popleft(self):
        if self.left == self.right:
            raise IndexError(u'cannot pop from empty deque')
        elem = self.data[self.left]
        del self.data[self.left]
        self.left += 1
        return elem
    popleft.func_annotations = {}

    def clear(self):
        self.data.clear()
        self.left = self.right = 0
    clear.func_annotations = {}

    def extend(self, iterable):
        for elem in iterable:
            self.append(elem)
    extend.func_annotations = {}

    def extendleft(self, iterable):
        for elem in iterable:
            self.appendleft(elem)
    extendleft.func_annotations = {}

    def rotate(self, n=1):
        if self:
            n %= len(self)
            for i in xrange(n):
                self.appendleft(self.pop())
    rotate.func_annotations = {}

    def __getitem__(self, i):
        if i < 0:
            i += len(self)
        try:
            return self.data[i + self.left]
        except KeyError:
            raise IndexError
    __getitem__.func_annotations = {}

    def __setitem__(self, i, value):
        if i < 0:
            i += len(self)        
        try:
            self.data[i + self.left] = value
        except KeyError:
            raise IndexError
    __setitem__.func_annotations = {}

    def __delitem__(self, i):
        size = len(self)
        if not (-size <= i < size):
            raise IndexError
        data = self.data
        if i < 0:
            i += size
        for j in xrange(self.left+i, self.right-1):
            data[j] = data[j+1]
        self.pop()
    __delitem__.func_annotations = {}
    
    def __len__(self):
        return self.right - self.left
    __len__.func_annotations = {}

    def __cmp__(self, other):
        if type(self) != type(other):
            return cmp(type(self), type(other))
        return cmp(list(self), list(other))
    __cmp__.func_annotations = {}
            
    def __repr__(self, _track=[]):
        if id(self) in _track:
            return u'...'
        _track.append(id(self))
        r = u'deque(%r)' % (list(self),)
        _track.remove(id(self))
        return r
    __repr__.func_annotations = {}
    
    def __getstate__(self):
        return (tuple(self),)
    __getstate__.func_annotations = {}
    
    def __setstate__(self, s):
        self.__init__(s[0])
    __setstate__.func_annotations = {}
        
    def __hash__(self):
        raise TypeError
    __hash__.func_annotations = {}
    
    def __copy__(self):
        return self.__class__(self)
    __copy__.func_annotations = {}
    
    def __deepcopy__(self, memo={}):
        from copy import deepcopy
        result = self.__class__()
        memo[id(self)] = result
        result.__init__(deepcopy(tuple(self), memo))
        return result
    __deepcopy__.func_annotations = {}

#Some utility functions to dal with weirdness around UCS2 vs UCS4
#python builds

def encodingType():
    if len() == 2:
        return u"UCS2"
    else:
        return u"UCS4"
encodingType.func_annotations = {}

def isSurrogatePair(data):   
    return (len(data) == 2 and
            ord(data[0]) >= 0xD800 and ord(data[0]) <= 0xDBFF and
            ord(data[1]) >= 0xDC00 and ord(data[1]) <= 0xDFFF)
isSurrogatePair.func_annotations = {}

def surrogatePairToCodepoint(data):
    char_val = (0x10000 + (ord(data[0]) - 0xD800) * 0x400 + 
                (ord(data[1]) - 0xDC00))
    return char_val
surrogatePairToCodepoint.func_annotations = {}

# Module Factory Factory (no, this isn't Java, I know)
# Here to stop this being duplicated all over the place.

def moduleFactoryFactory(factory):
    moduleCache = {}
    def moduleFactory(baseModule, *args, **kwargs):
        if type(ModuleType.__name__) is unicode:
            name = u"_%s_factory" % baseModule.__name__
        else:
            name = "_%s_factory" % baseModule.__name__

        if name in moduleCache:
            return moduleCache[name]
        else:
            mod = ModuleType(name)
            objs = factory(baseModule, *args, **kwargs)
            mod.__dict__.update(objs)
            moduleCache[name] = mod    
            return mod
    moduleFactory.func_annotations = {}

    return moduleFactory
moduleFactoryFactory.func_annotations = {}
