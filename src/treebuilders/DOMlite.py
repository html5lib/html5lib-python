import base

# Really crappy basic implementation of a DOM-core like thing
class Node(object):
    def __init__(self, name):
        self.name = name
        self.parent = None
        self.value = None
        self.childNodes = []
        self._flags = []

    def __str__(self):
        return self.name

    def __repr__(self):
        return "<%s %s>" % (self.__class__, self.name)

    def printTree(self, indent=0):
        tree = '\n|%s%s' % (' '* indent, str(self))
        for child in self.childNodes:
            tree += child.printTree(indent + 2)
        return tree

    def appendChild(self, node, index=None):
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
        for attr, value in self.attributes.iteritems():
            newNode.attributes[attr] = value
        newNode.value = self.value
        return newNode

    def hasContent(self):
        """Return true if the node has children or text"""
        return bool(self.childNodes)

class Document(Node):
    def __init__(self):
        Node.__init__(self, None)

    def __str__(self):
        return "#document"

    def printTree(self):
        tree = str(self)
        for child in self.childNodes:
            tree += child.printTree(2)
        return tree

class DocumentType(Node):
    def __init__(self, name):
        Node.__init__(self, name)

    def __str__(self):
        return "<!DOCTYPE %s>" % self.name

class TextNode(Node):
    def __init__(self, value):
        Node.__init__(self, None)
        self.value = value

    def __str__(self):
        return "\"%s\"" % self.value

class Element(Node):
    def __init__(self, name):
        Node.__init__(self, name)
        self.attributes = {}
        
    def __str__(self):
        return "<%s>" % self.name

    def printTree(self, indent):
        tree = '\n|%s%s' % (' '*indent, str(self))
        indent += 2
        if self.attributes:
            for name, value in self.attributes.iteritems():
                tree += '\n|%s%s="%s"' % (' ' * indent, name, value)
        for child in self.childNodes:
            tree += child.printTree(indent)
        return tree

class CommentNode(Node):
    def __init__(self, data):
        Node.__init__(self, None)
        self.data = data

    def __str__(self):
        return "<!-- %s -->" % self.data

class TreeBuilder(base.TreeBuilder):
    documentClass = Document
    doctypeClass = DocumentType
    elementClass = Element
    commentClass = CommentNode
    
    def testSerializer(self, node):
        return node.printTree()
