import _base
from html5lib.constants import voidElements
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

    def __iter__(self):
        for node in self.childNodes:
            yield node
            for item in node:
                yield item

    def __unicode__(self):
        return self.name

    def toxml(self):
        raise NotImplementedError

    def printTree(self, indent=0):
        tree = '\n|%s%s' % (' '* indent, unicode(self))
        for child in self.childNodes:
            tree += child.printTree(indent + 2)
        return tree

    def appendChild(self, node):
        if (isinstance(node, TextNode) and self.childNodes and
          isinstance(self.childNodes[-1], TextNode)):
            self.childNodes[-1].value += node.value
        else:
            self.childNodes.append(node)
        node.parent = self

    def insertText(self, data, insertBefore=None):
        if insertBefore is None:
            self.appendChild(TextNode(data))
        else:
            self.insertBefore(TextNode(data), insertBefore)

    def insertBefore(self, node, refNode):
        index = self.childNodes.index(refNode)
        if (isinstance(node, TextNode) and index > 0 and
          isinstance(self.childNodes[index - 1], TextNode)):
            self.childNodes[index - 1].value += node.value
        else:
            self.childNodes.insert(index, node)
        node.parent = self

    def removeChild(self, node):
        try:
            self.childNodes.remove(node)
        except:
            # XXX
            raise
        node.parent = None

    def cloneNode(self):
        newNode = type(self)(self.name)
        if hasattr(self, 'attributes'):
            for attr, value in self.attributes.iteritems():
                newNode.attributes[attr] = value
        newNode.value = self.value
        return newNode

    def hasContent(self):
        """Return true if the node has children or text"""
        return bool(self.childNodes)

class Document(Node):
    type = 1
    def __init__(self):
        Node.__init__(self, None)

    def __unicode__(self):
        return "#document"

    def toxml(self, encoding="utf=8"):
        result = ""
        for child in self.childNodes:
            result += child.toxml()
        return result.encode(encoding)

    def hilite(self, encoding="utf-8"):
        result = "<pre>"
        for child in self.childNodes:
            result += child.hilite()
        return result.encode(encoding) + "</pre>"
    
    def printTree(self):
        tree = unicode(self)
        for child in self.childNodes:
            tree += child.printTree(2)
        return tree

class DocumentFragment(Document):
    type = 2
    def __unicode__(self):
        return "#document-fragment"

class DocumentType(Node):
    type = 3
    def __init__(self, name):
        Node.__init__(self, name)
        self.publicId = u""
        self.systemId = u""

    def __unicode__(self):
        return u"<!DOCTYPE %s>" % self.name

    toxml = __unicode__
    
    def hilite(self):
        return '<code class="markup doctype">&lt;!DOCTYPE %s></code>' % self.name

class TextNode(Node):
    type = 4
    def __init__(self, value):
        Node.__init__(self, None)
        self.value = value

    def __unicode__(self):
        return u"\"%s\"" % self.value

    def toxml(self):
        return escape(self.value)
    
    hilite = toxml

class Element(Node):
    type = 5
    def __init__(self, name):
        Node.__init__(self, name)
        self.attributes = {}
        
    def __unicode__(self):
        return u"<%s>" % self.name

    def toxml(self):
        result = '<' + self.name
        if self.attributes:
            for name,value in self.attributes.iteritems():
                result += u' %s="%s"' % (name, escape(value,{'"':'&quot;'}))
        if self.childNodes:
            result += '>'
            for child in self.childNodes:
                result += child.toxml()
            result += u'</%s>' % self.name
        else:
            result += u'/>'
        return result
    
    def hilite(self):
        result = '&lt;<code class="markup element-name">%s</code>' % self.name
        if self.attributes:
            for name, value in self.attributes.iteritems():
                result += ' <code class="markup attribute-name">%s</code>=<code class="markup attribute-value">"%s"</code>' % (name, escape(value, {'"':'&quot;'}))
        if self.childNodes:
            result += ">"
            for child in self.childNodes:
                result += child.hilite()
        elif self.name in voidElements:
            return result + ">"
        return result + '&lt;/<code class="markup element-name">%s</code>>' % self.name

    def printTree(self, indent):
        tree = '\n|%s%s' % (' '*indent, unicode(self))
        indent += 2
        if self.attributes:
            for name, value in self.attributes.iteritems():
                tree += '\n|%s%s="%s"' % (' ' * indent, name, value)
        for child in self.childNodes:
            tree += child.printTree(indent)
        return tree

class CommentNode(Node):
    type = 6
    def __init__(self, data):
        Node.__init__(self, None)
        self.data = data

    def __unicode__(self):
        return "<!-- %s -->" % self.data
    
    def toxml(self):
        return "<!--%s-->" % self.data

    def hilite(self):
        return '<code class="markup comment">&lt;!--%s--></code>' % escape(self.data)

class TreeBuilder(_base.TreeBuilder):
    documentClass = Document
    doctypeClass = DocumentType
    elementClass = Element
    commentClass = CommentNode
    fragmentClass = DocumentFragment
    
    def testSerializer(self, node):
        return node.printTree()
