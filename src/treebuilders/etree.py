try:
    from xml.etree import ElementTree
except ImportError:
    from elementtree import ElementTree

import base

class Element(object):
    def __init__(self, name):
        self._element = ElementTree.Element(name)
        self.name = name
        self.parent = None
        self._childNodes = []
        self._flags = []

        #Set the element text and tail to the empty string rather than None
        #XXX - is this desirable or should we do it on a case by case basis?
        self._element.text = ""
        self._element.tail = ""

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
            self._element.text += data
        elif insertBefore is None:
            #Insert the text as the tail of the last child element
            self._element[-1].tail += data
        else:
            #Insert the text before the specified node
            children = self._element.getchildren()
            index = children.index(insertBefore._element)
            if index > 0:
                self._element[index-1].tail += data
            else:
                self._element.text += data

    def cloneNode(self):
        element = Element(self.name)
        element.attributes = self.attributes
        return element

class Comment(Element):
    def __init__(self, data):
        self._element = ElementTree.Comment(data)
        self.name = None
        self.parent = None

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
    def serializeElement(element, indent=0):
        if element.tag is DocumentType:
            rv.append("|%s<!DOCTYPE %s>"%(' '*indent, element.text))
        elif element.tag is Document:
            rv.append("#document")
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
    return "\n".join(rv)

class TreeBuilder(base.TreeBuilder):
    documentClass = Document
    doctypeClass = DocumentType
    elementClass = Element
    commentClass = Comment

    def testSerializer(self, element):
        return testSerializer(element)

    def getDocument(self):
        return self.document._element
