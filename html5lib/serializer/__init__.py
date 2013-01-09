
from __future__ import absolute_import
from html5lib import treewalkers

from .htmlserializer import HTMLSerializer
from .xhtmlserializer import XHTMLSerializer

def serialize(input, tree=u"simpletree", format=u"html", encoding=None,
              **serializer_opts):
    # XXX: Should we cache this?
    walker = treewalkers.getTreeWalker(tree) 
    if format == u"html":
        s = HTMLSerializer(**serializer_opts)
    elif format == u"xhtml":
        s = XHTMLSerializer(**serializer_opts)
    else:
        raise ValueError(u"type must be either html or xhtml")
    return s.render(walker(input), encoding)
serialize.func_annotations = {}
