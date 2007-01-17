try:
    from xml.etree import ElementTree
except ImportError:
    from elementtree import ElementTree

import _base

class Element(_base.Node):
    def __init__(self, name):
        self._element = ElementTree.Element(name)
        self.name = name
        self.parent = None
        self._childNodes = []
        self._flags = []

    def _setName(self, name):
        self._element.tag = name
    
    def _getName(self):
        return self._element.tag

    name = property(_getName, _setName)

    def _getAttributes(self):
        return self._element.attrib

    def _setAttributes(self, attributes):
        #Delete existing attributes first
        #XXX - there may be a better way to do this...
        for key in self._element.attrib.keys():
            del self._element.attrib[key]
        for key, value in attributes.iteritems():
            self._element.set(key, value)

    attributes = property(_getAttributes, _setAttributes)

    def _getChildNodes(self):
        return self._childNodes

    def _setChildNodes(self, value):
        del self._element[:]
        self._childNodes = []
        for element in value:
            self.insertChild(element)

    childNodes = property(_getChildNodes, _setChildNodes)

    def hasContent(self):
        """Return true if the node has children or text"""
        return bool(self._element.text or self._element.getchildren())

    def appendChild(self, node):
        self._childNodes.append(node)
        self._element.append(node._element)
        node.parent = self

    def insertBefore(self, node, refNode):
        index = self._element.getchildren().index(refNode._element)
        self._element.insert(index, node._element)
        node.parent = self

    def removeChild(self, node):
        self._element.remove(node._element)
        node.parent=None

    def insertText(self, data, insertBefore=None):
        if not(len(self._element)):
            if not self._element.text:
                self._element.text = ""
            self._element.text += data
        elif insertBefore is None:
            #Insert the text as the tail of the last child element
            if not self._element[-1].tail:
                self._element[-1].tail = ""
            self._element[-1].tail += data
        else:
            #Insert the text before the specified node
            children = self._element.getchildren()
            index = children.index(insertBefore._element)
            if index > 0:
                if not self._element[index-1].tail:
                    self._element[index-1].tail = ""
                self._element[index-1].tail += data
            else:
                if not self._element.text:
                    self._element.text = ""
                self._element.text += data

    def cloneNode(self):
        element = Element(self.name)
        element.attributes = self.attributes
        return element

    def reparentChildren(self, newParent):
        if newParent.childNodes:
            newParent.childNodes[-1]._element.tail += self._element.text
        else:
            if not newParent._element.text:
                newParent._element.text = ""
            if self._element.text is not None:
                newParent._element.text += self._element.text
        self._element.text = ""
        _base.Node.reparentChildren(self, newParent)

class Comment(Element):
    def __init__(self, data):
        #Use the superclass constructor to set all properties on the 
        #wrapper element
        Element.__init__(self, None)
        self._element = ElementTree.Comment(data)

    def _getData(self):
        return self._element.text

    def _setData(self, value):
        self._element.text = value

    data = property(_getData, _setData)

class DocumentType(Element):
    def __init__(self, name):
        Element.__init__(self, DocumentType) 
        self._element.text = name

class Document(Element):
    def __init__(self):
        Element.__init__(self, Document) 

def testSerializer(element):
    rv = []
    finalText = None
    def serializeElement(element, indent=0):
        if element.tag is DocumentType:
            rv.append("|%s<!DOCTYPE %s>"%(' '*indent, element.text))
        elif element.tag is Document:
            rv.append("#document")
            if element.text:
                rv.append("|%s\"%s\""%(' '*(indent+2), element.text))
            if element.tail:
                finalText = element.tail
        elif element.tag is ElementTree.Comment:
            rv.append("|%s<!-- %s -->"%(' '*indent, element.text))
        else:
            rv.append("|%s<%s>"%(' '*indent, element.tag))
            if hasattr(element, "attrib"):
                for name, value in element.attrib.iteritems():
                    rv.append('|%s%s="%s"' % (' '*(indent+2), name, value))
            if element.text:
                rv.append("|%s\"%s\"" %(' '*(indent+2), element.text))
        indent += 2
        for child in element.getchildren():
            serializeElement(child, indent)
        if element.tail:
            rv.append("|%s\"%s\"" %(' '*(indent-2), element.tail))
    serializeElement(element, 0)

    if finalText is not None:
        rv.append("|%s\"%s\""%(' '*2, finalText))

    return "\n".join(rv)

def tostring(element):
    """Serialize an element and its child nodes to a string"""
    rv = []
    finalText = None
    def serializeElement(element):
        if element.tag is DocumentType:
            rv.append("<!DOCTYPE %s>"%(element.text,))
        elif element.tag is Document:
            if element.text:
                rv.append(element.text)
            if element.tail:
                finalText = element.tail

            for child in element.getchildren():
                serializeElement(child)

        elif element.tag is ElementTree.Comment:
            rv.append("<!--%s-->"%(element.text,))
        else:
            #This is assumed to be an ordinary element
            if not element.attrib:
                rv.append("<%s>"%(element.tag,))
            else:
                attr = " ".join(["%s=\"%s\""%(name, value) 
                                 for name, value in element.attrib.iteritems()])
                rv.append("<%s %s>"%(element.tag, attr))
            if element.text:
                rv.append(element.text)

            for child in element.getchildren():
                serializeElement(child)

            rv.append("</%s>"%(element.tag,))

        if element.tail:
            rv.append(element.tail)

    serializeElement(element)

    if finalText is not None:
        rv.append("%s\""%(' '*2, finalText))

    return "".join(rv)

class TreeBuilderFull(_base.TreeBuilder):
    documentClass = Document
    doctypeClass = DocumentType
    elementClass = Element
    commentClass = Comment

    def testSerializer(self, element):
        return testSerializer(element)

    def getDocument(self):
        return self.document._element

class TreeBuilder(TreeBuilderFull):
    def getDocument(self):
        return self.document._element.find("html")
