from __future__ import absolute_import
import warnings

warnings.warn(u"BeautifulSoup 3.x (as of 3.1) is not fully compatible with html5lib and support will be removed in the future", DeprecationWarning)

from BeautifulSoup import BeautifulSoup, Tag, NavigableString, Comment, Declaration

from . import _base
from html5lib.constants import namespaces, DataLossWarning

class AttrList(object):
    def __init__(self, element):
        self.element = element
        self.attrs = dict(self.element.attrs)
    __init__.func_annotations = {}
    def __iter__(self):
        return list(self.attrs.items()).__iter__()
    __iter__.func_annotations = {}
    def __setitem__(self, name, value):
        u"set attr", name, value
        self.element[name] = value
    __setitem__.func_annotations = {}
    def items(self):
        return list(self.attrs.items())
    items.func_annotations = {}
    def keys(self):
        return list(self.attrs.keys())
    keys.func_annotations = {}
    def __getitem__(self, name):
        return self.attrs[name]
    __getitem__.func_annotations = {}
    def __contains__(self, name):
        return name in list(self.attrs.keys())
    __contains__.func_annotations = {}
    def __eq__(self, other):
        if len(list(self.keys())) != len(list(other.keys())):
            return False
        for item in list(self.keys()):
            if item not in other:
                return False
            if self[item] != other[item]:
                return False
        return True
    __eq__.func_annotations = {}

class Element(_base.Node):
    def __init__(self, element, soup, namespace):
        _base.Node.__init__(self, element.name)
        self.element = element
        self.soup = soup
        self.namespace = namespace
    __init__.func_annotations = {}

    def _nodeIndex(self, node, refNode):
        # Finds a node by identity rather than equality
        for index in xrange(len(self.element.contents)):
            if id(self.element.contents[index]) == id(refNode.element):
                return index
        return None
    _nodeIndex.func_annotations = {}

    def appendChild(self, node):
        if (node.element.__class__ == NavigableString and self.element.contents
            and self.element.contents[-1].__class__ == NavigableString):
            # Concatenate new text onto old text node
            # (TODO: This has O(n^2) performance, for input like "a</a>a</a>a</a>...")
            newStr = NavigableString(self.element.contents[-1]+node.element)

            # Remove the old text node
            # (Can't simply use .extract() by itself, because it fails if
            # an equal text node exists within the parent node)
            oldElement = self.element.contents[-1]
            del self.element.contents[-1]
            oldElement.parent = None
            oldElement.extract()

            self.element.insert(len(self.element.contents), newStr)
        else:
            self.element.insert(len(self.element.contents), node.element)
            node.parent = self
    appendChild.func_annotations = {}

    def getAttributes(self):
        return AttrList(self.element)
    getAttributes.func_annotations = {}

    def setAttributes(self, attributes):
        if attributes:
            for name, value in list(attributes.items()):
                self.element[name] =  value
    setAttributes.func_annotations = {}

    attributes = property(getAttributes, setAttributes)
    
    def insertText(self, data, insertBefore=None):
        text = TextNode(NavigableString(data), self.soup)
        if insertBefore:
            self.insertBefore(text, insertBefore)
        else:
            self.appendChild(text)
    insertText.func_annotations = {}

    def insertBefore(self, node, refNode):
        index = self._nodeIndex(node, refNode)
        if (node.element.__class__ == NavigableString and self.element.contents
            and self.element.contents[index-1].__class__ == NavigableString):
            # (See comments in appendChild)
            newStr = NavigableString(self.element.contents[index-1]+node.element)
            oldNode = self.element.contents[index-1]
            del self.element.contents[index-1]
            oldNode.parent = None
            oldNode.extract()

            self.element.insert(index-1, newStr)
        else:
            self.element.insert(index, node.element)
            node.parent = self
    insertBefore.func_annotations = {}

    def removeChild(self, node):
        index = self._nodeIndex(node.parent, node)
        del node.parent.element.contents[index]
        node.element.parent = None
        node.element.extract()
        node.parent = None
    removeChild.func_annotations = {}

    def reparentChildren(self, newParent):
        while self.element.contents:
            child = self.element.contents[0]
            child.extract()
            if isinstance(child, Tag):
                newParent.appendChild(Element(child, self.soup, namespaces[u"html"]))
            else:
                newParent.appendChild(TextNode(child, self.soup))
    reparentChildren.func_annotations = {}

    def cloneNode(self):
        node = Element(Tag(self.soup, self.element.name), self.soup, self.namespace)
        for key,value in self.attributes:
            node.attributes[key] = value
        return node
    cloneNode.func_annotations = {}

    def hasContent(self):
        return self.element.contents
    hasContent.func_annotations = {}

    def getNameTuple(self):
        if self.namespace == None:
            return namespaces[u"html"], self.name
        else:
            return self.namespace, self.name
    getNameTuple.func_annotations = {}

    nameTuple = property(getNameTuple)

class TextNode(Element):
    def __init__(self, element, soup):
        _base.Node.__init__(self, None)
        self.element = element
        self.soup = soup
    __init__.func_annotations = {}
    
    def cloneNode(self):
        raise NotImplementedError
    cloneNode.func_annotations = {}

class TreeBuilder(_base.TreeBuilder):
    def __init__(self, namespaceHTMLElements):
        if namespaceHTMLElements:
            warnings.warn(u"BeautifulSoup cannot represent elements in any namespace", DataLossWarning)
        _base.TreeBuilder.__init__(self, namespaceHTMLElements)
    __init__.func_annotations = {}
        
    def documentClass(self):
        self.soup = BeautifulSoup(u"")
        return Element(self.soup, self.soup, None)
    documentClass.func_annotations = {}
    
    def insertDoctype(self, token):
        name = token[u"name"]
        publicId = token[u"publicId"]
        systemId = token[u"systemId"]

        if publicId:
            self.soup.insert(0, Declaration(u"DOCTYPE %s PUBLIC \"%s\" \"%s\""%(name, publicId, systemId or u"")))
        elif systemId:
            self.soup.insert(0, Declaration(u"DOCTYPE %s SYSTEM \"%s\""%
                                            (name, systemId)))
        else:
            self.soup.insert(0, Declaration(u"DOCTYPE %s"%name))
    insertDoctype.func_annotations = {}
    
    def elementClass(self, name, namespace):
        if namespace is not None:
            warnings.warn(u"BeautifulSoup cannot represent elements in any namespace", DataLossWarning)
        return Element(Tag(self.soup, name), self.soup, namespace)
    elementClass.func_annotations = {}
        
    def commentClass(self, data):
        return TextNode(Comment(data), self.soup)
    commentClass.func_annotations = {}
    
    def fragmentClass(self):
        self.soup = BeautifulSoup(u"")
        self.soup.name = u"[document_fragment]"
        return Element(self.soup, self.soup, None) 
    fragmentClass.func_annotations = {}

    def appendChild(self, node):
        self.soup.insert(len(self.soup.contents), node.element)
    appendChild.func_annotations = {}

    def testSerializer(self, element):
        return testSerializer(element)
    testSerializer.func_annotations = {}

    def getDocument(self):
        return self.soup
    getDocument.func_annotations = {}
    
    def getFragment(self):
        return _base.TreeBuilder.getFragment(self).element
    getFragment.func_annotations = {}
    
def testSerializer(element):
    import re
    rv = []
    def serializeElement(element, indent=0):
        if isinstance(element, Declaration):
            doctype_regexp = ur'DOCTYPE\s+(?P<name>[^\s]*)( PUBLIC "(?P<publicId>.*)" "(?P<systemId1>.*)"| SYSTEM "(?P<systemId2>.*)")?'
            m = re.compile(doctype_regexp).match(element.string)
            assert m is not None, u"DOCTYPE did not match expected format"
            name = m.group(u'name')
            publicId = m.group(u'publicId')
            if publicId is not None:
                systemId = m.group(u'systemId1') or u""
            else:
                systemId = m.group(u'systemId2')

            if publicId is not None or systemId is not None:
                rv.append(u"""|%s<!DOCTYPE %s "%s" "%s">"""%
                          (u' '*indent, name, publicId or u"", systemId or u""))
            else:
                rv.append(u"|%s<!DOCTYPE %s>"%(u' '*indent, name))
            
        elif isinstance(element, BeautifulSoup):
            if element.name == u"[document_fragment]":
                rv.append(u"#document-fragment")                
            else:
                rv.append(u"#document")

        elif isinstance(element, Comment):
            rv.append(u"|%s<!-- %s -->"%(u' '*indent, element.string))
        elif isinstance(element, unicode):
            rv.append(u"|%s\"%s\"" %(u' '*indent, element))
        else:
            rv.append(u"|%s<%s>"%(u' '*indent, element.name))
            if element.attrs:
                for name, value in sorted(element.attrs):
                    rv.append(u'|%s%s="%s"' % (u' '*(indent+2), name, value))
        indent += 2
        if hasattr(element, u"contents"):
            for child in element.contents:
                serializeElement(child, indent)
    serializeElement.func_annotations = {}
    serializeElement(element, 0)

    return u"\n".join(rv)
testSerializer.func_annotations = {}
