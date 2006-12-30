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

    def appendChild(self, node):
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
                self.text += data

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
    pass

class Document(Element):
    def __init__(self):
        Element.__init__(self, "")

class TreeBuilder(base.TreeBuilder):
    documentClass = Document
    doctypeClass = DocumentType
    elementClass = Element
    commentClass = Comment

    def testSerializer(self, element):
        ElementTree.tostring(element)

    def getDocument(self):
        return self.document.getchildren()[0]._element
