from __future__ import absolute_import
from . import _base
from html5lib.constants import voidElements, namespaces, prefixes
from xml.sax.saxutils import escape

# Really crappy basic implementation of a DOM-core like thing
class Node(_base.Node):
    type = -1
    def __init__(self, name):
        self.name = name
        self.parent = None
        self.value = None
        self.childNodes = []
        self._flags = []
    __init__.func_annotations = {}

    def __iter__(self):
        for node in self.childNodes:
            yield node
            for item in node:
                yield item
    __iter__.func_annotations = {}

    def __unicode__(self):
        return self.name
    __unicode__.func_annotations = {}

    def toxml(self):
        raise NotImplementedError
    toxml.func_annotations = {}

    def printTree(self, indent=0):
        tree = u'\n|%s%s' % (u' '* indent, unicode(self))
        for child in self.childNodes:
            tree += child.printTree(indent + 2)
        return tree
    printTree.func_annotations = {}

    def appendChild(self, node):
        assert isinstance(node, Node)
        if (isinstance(node, TextNode) and self.childNodes and
          isinstance(self.childNodes[-1], TextNode)):
            self.childNodes[-1].value += node.value
        else:
            self.childNodes.append(node)
        node.parent = self
    appendChild.func_annotations = {}

    def insertText(self, data, insertBefore=None):
        assert isinstance(data, unicode), u"data %s is of type %s expected unicode"%(repr(data), type(data))
        if insertBefore is None:
            self.appendChild(TextNode(data))
        else:
            self.insertBefore(TextNode(data), insertBefore)
    insertText.func_annotations = {}

    def insertBefore(self, node, refNode):
        index = self.childNodes.index(refNode)
        if (isinstance(node, TextNode) and index > 0 and
          isinstance(self.childNodes[index - 1], TextNode)):
            self.childNodes[index - 1].value += node.value
        else:
            self.childNodes.insert(index, node)
        node.parent = self
    insertBefore.func_annotations = {}

    def removeChild(self, node):
        try:
            self.childNodes.remove(node)
        except:
            # XXX
            raise
        node.parent = None
    removeChild.func_annotations = {}

    def cloneNode(self):
        raise NotImplementedError
    cloneNode.func_annotations = {}

    def hasContent(self):
        u"""Return true if the node has children or text"""
        return bool(self.childNodes)
    hasContent.func_annotations = {}

    def getNameTuple(self):
        if self.namespace == None:
            return namespaces[u"html"], self.name
        else:
            return self.namespace, self.name
    getNameTuple.func_annotations = {}

    nameTuple = property(getNameTuple)

class Document(Node):
    type = 1
    def __init__(self):
        Node.__init__(self, None)
    __init__.func_annotations = {}

    def __unicode__(self):
        return u"#document"
    __unicode__.func_annotations = {}

    def appendChild(self, child):
        Node.appendChild(self, child)
    appendChild.func_annotations = {}

    def toxml(self, encoding=u"utf=8"):
        result = u""
        for child in self.childNodes:
            result += child.toxml()
        return result.encode(encoding)
    toxml.func_annotations = {}

    def hilite(self, encoding=u"utf-8"):
        result = u"<pre>"
        for child in self.childNodes:
            result += child.hilite()
        return result.encode(encoding) + u"</pre>"
    hilite.func_annotations = {}
    
    def printTree(self):
        tree = unicode(self)
        for child in self.childNodes:
            tree += child.printTree(2)
        return tree
    printTree.func_annotations = {}

    def cloneNode(self):
        return Document()
    cloneNode.func_annotations = {}

class DocumentFragment(Document):
    type = 2
    def __unicode__(self):
        return u"#document-fragment"
    __unicode__.func_annotations = {}

    def cloneNode(self):
        return DocumentFragment()
    cloneNode.func_annotations = {}

class DocumentType(Node):
    type = 3
    def __init__(self, name, publicId, systemId):
        Node.__init__(self, name)
        self.publicId = publicId
        self.systemId = systemId
    __init__.func_annotations = {}

    def __unicode__(self):
        if self.publicId or self.systemId:
            publicId = self.publicId or u""
            systemId = self.systemId or u""
            return u"""<!DOCTYPE %s "%s" "%s">"""%(
                self.name, publicId, systemId)
                            
        else:
            return u"<!DOCTYPE %s>" % self.name
    __unicode__.func_annotations = {}
    

    toxml = __unicode__
    
    def hilite(self):
        return u'<code class="markup doctype">&lt;!DOCTYPE %s></code>' % self.name
    hilite.func_annotations = {}

    def cloneNode(self):
        return DocumentType(self.name, self.publicId, self.systemId)
    cloneNode.func_annotations = {}

class TextNode(Node):
    type = 4
    def __init__(self, value):
        Node.__init__(self, None)
        self.value = value
    __init__.func_annotations = {}

    def __unicode__(self):
        return u"\"%s\"" % self.value
    __unicode__.func_annotations = {}

    def toxml(self):
        return escape(self.value)
    toxml.func_annotations = {}
    
    hilite = toxml

    def cloneNode(self):
        assert isinstance(self.value, unicode)
        return TextNode(self.value)
    cloneNode.func_annotations = {}

class Element(Node):
    type = 5
    def __init__(self, name, namespace=None):
        Node.__init__(self, name)
        self.namespace = namespace
        self.attributes = {}
    __init__.func_annotations = {}

    def __unicode__(self):
        if self.namespace == None:
            return u"<%s>" % self.name
        else:
            return u"<%s %s>"%(prefixes[self.namespace], self.name)
    __unicode__.func_annotations = {}

    def toxml(self):
        result = u'<' + self.name
        if self.attributes:
            for name,value in self.attributes.items():
                result += u' %s="%s"' % (name, escape(value,{u'"':u'&quot;'}))
        if self.childNodes:
            result += u'>'
            for child in self.childNodes:
                result += child.toxml()
            result += u'</%s>' % self.name
        else:
            result += u'/>'
        return result
    toxml.func_annotations = {}
    
    def hilite(self):
        result = u'&lt;<code class="markup element-name">%s</code>' % self.name
        if self.attributes:
            for name, value in self.attributes.items():
                result += u' <code class="markup attribute-name">%s</code>=<code class="markup attribute-value">"%s"</code>' % (name, escape(value, {u'"':u'&quot;'}))
        if self.childNodes:
            result += u">"
            for child in self.childNodes:
                result += child.hilite()
        elif self.name in voidElements:
            return result + u">"
        return result + u'&lt;/<code class="markup element-name">%s</code>>' % self.name
    hilite.func_annotations = {}

    def printTree(self, indent):
        tree = u'\n|%s%s' % (u' '*indent, unicode(self))
        indent += 2
        if self.attributes:
            for name, value in sorted(self.attributes.items()):
                if isinstance(name, tuple):
                    name = u"%s %s"%(name[0], name[1])
                tree += u'\n|%s%s="%s"' % (u' ' * indent, name, value)
        for child in self.childNodes:
            tree += child.printTree(indent)
        return tree
    printTree.func_annotations = {}

    def cloneNode(self):
        newNode = Element(self.name, self.namespace)
        for attr, value in self.attributes.items():
            newNode.attributes[attr] = value
        return newNode
    cloneNode.func_annotations = {}

class CommentNode(Node):
    type = 6
    def __init__(self, data):
        Node.__init__(self, None)
        self.data = data
    __init__.func_annotations = {}

    def __unicode__(self):
        return u"<!-- %s -->" % self.data
    __unicode__.func_annotations = {}
    
    def toxml(self):
        return u"<!--%s-->" % self.data
    toxml.func_annotations = {}

    def hilite(self):
        return u'<code class="markup comment">&lt;!--%s--></code>' % escape(self.data)
    hilite.func_annotations = {}

    def cloneNode(self):
        return CommentNode(self.data)
    cloneNode.func_annotations = {}

class TreeBuilder(_base.TreeBuilder):
    documentClass = Document
    doctypeClass = DocumentType
    elementClass = Element
    commentClass = CommentNode
    fragmentClass = DocumentFragment
    
    def testSerializer(self, node):
        return node.printTree()
    testSerializer.func_annotations = {}
