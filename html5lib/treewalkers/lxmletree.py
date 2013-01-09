from __future__ import absolute_import
from lxml import etree
from html5lib.treebuilders.etree import tag_regexp

from gettext import gettext
import sys
_ = gettext

from . import _base

from html5lib.constants import voidElements
from html5lib import ihatexml

class Root(object):
    def __init__(self, et):
        self.elementtree = et
        self.children = []
        if et.docinfo.internalDTD:
            self.children.append(Doctype(self, et.docinfo.root_name, 
                                         et.docinfo.public_id, 
                                         et.docinfo.system_url))
        root = et.getroot()
        node = root

        while node.getprevious() is not None:
            node = node.getprevious()
        while node is not None:
            self.children.append(node)
            node = node.getnext()

        self.text = None
        self.tail = None
    __init__.func_annotations = {}
    
    def __getitem__(self, key):
        return self.children[key]
    __getitem__.func_annotations = {}

    def getnext(self):
        return None
    getnext.func_annotations = {}

    def __len__(self):
        return 1
    __len__.func_annotations = {}

class Doctype(object):
    def __init__(self, root_node, name, public_id, system_id):
        self.root_node = root_node
        self.name = name
        self.public_id = public_id
        self.system_id = system_id
        
        self.text = None
        self.tail = None
    __init__.func_annotations = {}

    def getnext(self):
        return self.root_node.children[1]
    getnext.func_annotations = {}

class FragmentRoot(Root):
    def __init__(self, children):
        self.children = [FragmentWrapper(self, child) for child in children]
        self.text = self.tail = None
    __init__.func_annotations = {}

    def getnext(self):
        return None
    getnext.func_annotations = {}

class FragmentWrapper(object):
    def __init__(self, fragment_root, obj):
        self.root_node = fragment_root
        self.obj = obj
        if hasattr(self.obj, u'text'):
            self.text = self.obj.text
        else:
            self.text = None
        if hasattr(self.obj, u'tail'):
            self.tail = self.obj.tail
        else:
            self.tail = None
        self.isstring = isinstance(obj, unicode) or isinstance(obj, str)
        assert not self.isstring or isinstance(obj, unicode) or sys.version_info.major == 2
    __init__.func_annotations = {}
        
    def __getattr__(self, name):
        return getattr(self.obj, name)
    __getattr__.func_annotations = {}
    
    def getnext(self):
        siblings = self.root_node.children
        idx = siblings.index(self)
        if idx < len(siblings) - 1:
            return siblings[idx + 1]
        else:
            return None
    getnext.func_annotations = {}

    def __getitem__(self, key):
        return self.obj[key]
    __getitem__.func_annotations = {}

    def __nonzero__(self):
        return bool(self.obj)
    __nonzero__.func_annotations = {}

    def getparent(self):
        return None
    getparent.func_annotations = {}

    def __unicode__(self):
        return unicode(self.obj)
    __unicode__.func_annotations = {}

    def __unicode__(self):
        return unicode(self.obj)
    __unicode__.func_annotations = {}

    def __len__(self):
        return len(self.obj)
    __len__.func_annotations = {}

        
class TreeWalker(_base.NonRecursiveTreeWalker):
    def __init__(self, tree):
        if hasattr(tree, u"getroot"):
            tree = Root(tree)
        elif isinstance(tree, list):
            tree = FragmentRoot(tree)
        _base.NonRecursiveTreeWalker.__init__(self, tree)
        self.filter = ihatexml.InfosetFilter()
    __init__.func_annotations = {}
    def getNodeDetails(self, node):
        if isinstance(node, tuple): # Text node
            node, key = node
            assert key in (u"text", u"tail"), _(u"Text nodes are text or tail, found %s") % key
            return _base.TEXT, getattr(node, key)

        elif isinstance(node, Root):
            return (_base.DOCUMENT,)

        elif isinstance(node, Doctype):
            return _base.DOCTYPE, node.name, node.public_id, node.system_id

        elif isinstance(node, FragmentWrapper) and node.isstring:
            return _base.TEXT, node

        elif node.tag == etree.Comment:
            return _base.COMMENT, node.text

        elif node.tag == etree.Entity:
            return _base.ENTITY, node.text[1:-1] # strip &;

        else:
            #This is assumed to be an ordinary element
            match = tag_regexp.match(node.tag)
            if match:
                namespace, tag = match.groups()
            else:
                namespace = None
                tag = node.tag
            attrs = {}
            for name, value in list(node.attrib.items()):
                match = tag_regexp.match(name)
                if match:
                    attrs[(match.group(1),match.group(2))] = value
                else:
                    attrs[(None,name)] = value
            return (_base.ELEMENT, namespace, self.filter.fromXmlName(tag), 
                    attrs, len(node) > 0 or node.text)
    getNodeDetails.func_annotations = {}

    def getFirstChild(self, node):
        assert not isinstance(node, tuple), _(u"Text nodes have no children")

        assert len(node) or node.text, u"Node has no children"
        if node.text:
            return (node, u"text")
        else:
            return node[0]
    getFirstChild.func_annotations = {}

    def getNextSibling(self, node):
        if isinstance(node, tuple): # Text node
            node, key = node
            assert key in (u"text", u"tail"), _(u"Text nodes are text or tail, found %s") % key
            if key == u"text":
                # XXX: we cannot use a "bool(node) and node[0] or None" construct here
                # because node[0] might evaluate to False if it has no child element
                if len(node):
                    return node[0]
                else:
                    return None
            else: # tail
                return node.getnext()

        return node.tail and (node, u"tail") or node.getnext()
    getNextSibling.func_annotations = {}

    def getParentNode(self, node):
        if isinstance(node, tuple): # Text node
            node, key = node
            assert key in (u"text", u"tail"), _(u"Text nodes are text or tail, found %s") % key
            if key == u"text":
                return node
            # else: fallback to "normal" processing

        return node.getparent()
    getParentNode.func_annotations = {}
