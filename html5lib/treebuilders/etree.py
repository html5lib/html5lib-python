from __future__ import absolute_import
import re

from . import _base
from html5lib import ihatexml
from html5lib import constants
from html5lib.constants import namespaces
from html5lib.utils import moduleFactoryFactory
from itertools import ifilter

tag_regexp = re.compile(u"{([^}]*)}(.*)")

def getETreeBuilder(ElementTreeImplementation, fullTree=False):
    ElementTree = ElementTreeImplementation
    class Element(_base.Node):
        def __init__(self, name, namespace=None):
            self._name = name
            self._namespace = namespace
            self._element = ElementTree.Element(self._getETreeTag(name,
                                                                  namespace))
            if namespace is None:
                self.nameTuple = namespaces[u"html"], self._name
            else:
                self.nameTuple = self._namespace, self._name
            self.parent = None
            self._childNodes = []
            self._flags = []
        __init__.func_annotations = {}

        def _getETreeTag(self, name, namespace):
            if namespace is None:
                etree_tag = name
            else:
                etree_tag = u"{%s}%s"%(namespace, name)
            return etree_tag
        _getETreeTag.func_annotations = {}
    
        def _setName(self, name):
            self._name = name
            self._element.tag = self._getETreeTag(self._name, self._namespace)
        _setName.func_annotations = {}
        
        def _getName(self):
            return self._name
        _getName.func_annotations = {}
        
        name = property(_getName, _setName)

        def _setNamespace(self, namespace):
            self._namespace = namespace
            self._element.tag = self._getETreeTag(self._name, self._namespace)
        _setNamespace.func_annotations = {}

        def _getNamespace(self):
            return self._namespace
        _getNamespace.func_annotations = {}

        namespace = property(_getNamespace, _setNamespace)
    
        def _getAttributes(self):
            return self._element.attrib
        _getAttributes.func_annotations = {}
    
        def _setAttributes(self, attributes):
            #Delete existing attributes first
            #XXX - there may be a better way to do this...
            for key in list(self._element.attrib.keys()):
                del self._element.attrib[key]
            for key, value in attributes.items():
                if isinstance(key, tuple):
                    name = u"{%s}%s"%(key[2], key[1])
                else:
                    name = key
                self._element.set(name, value)
        _setAttributes.func_annotations = {}
    
        attributes = property(_getAttributes, _setAttributes)
    
        def _getChildNodes(self):
            return self._childNodes    
        _getChildNodes.func_annotations = {}
        def _setChildNodes(self, value):
            del self._element[:]
            self._childNodes = []
            for element in value:
                self.insertChild(element)
        _setChildNodes.func_annotations = {}
    
        childNodes = property(_getChildNodes, _setChildNodes)
    
        def hasContent(self):
            u"""Return true if the node has children or text"""
            return bool(self._element.text or len(self._element))
        hasContent.func_annotations = {}
    
        def appendChild(self, node):
            self._childNodes.append(node)
            self._element.append(node._element)
            node.parent = self
        appendChild.func_annotations = {}
    
        def insertBefore(self, node, refNode):
            index = list(self._element).index(refNode._element)
            self._element.insert(index, node._element)
            node.parent = self
        insertBefore.func_annotations = {}
    
        def removeChild(self, node):
            self._element.remove(node._element)
            node.parent=None
        removeChild.func_annotations = {}
    
        def insertText(self, data, insertBefore=None):
            if not(len(self._element)):
                if not self._element.text:
                    self._element.text = u""
                self._element.text += data
            elif insertBefore is None:
                #Insert the text as the tail of the last child element
                if not self._element[-1].tail:
                    self._element[-1].tail = u""
                self._element[-1].tail += data
            else:
                #Insert the text before the specified node
                children = list(self._element)
                index = children.index(insertBefore._element)
                if index > 0:
                    if not self._element[index-1].tail:
                        self._element[index-1].tail = u""
                    self._element[index-1].tail += data
                else:
                    if not self._element.text:
                        self._element.text = u""
                    self._element.text += data
        insertText.func_annotations = {}
    
        def cloneNode(self):
            element = type(self)(self.name, self.namespace)
            for name, value in self.attributes.items():
                element.attributes[name] = value
            return element
        cloneNode.func_annotations = {}
    
        def reparentChildren(self, newParent):
            if newParent.childNodes:
                newParent.childNodes[-1]._element.tail += self._element.text
            else:
                if not newParent._element.text:
                    newParent._element.text = u""
                if self._element.text is not None:
                    newParent._element.text += self._element.text
            self._element.text = u""
            _base.Node.reparentChildren(self, newParent)
        reparentChildren.func_annotations = {}
    
    class Comment(Element):
        def __init__(self, data):
            #Use the superclass constructor to set all properties on the 
            #wrapper element
            self._element = ElementTree.Comment(data)
            self.parent = None
            self._childNodes = []
            self._flags = []
        __init__.func_annotations = {}
            
        def _getData(self):
            return self._element.text
        _getData.func_annotations = {}
    
        def _setData(self, value):
            self._element.text = value
        _setData.func_annotations = {}
    
        data = property(_getData, _setData)
    
    class DocumentType(Element):
        def __init__(self, name, publicId, systemId):
            Element.__init__(self, u"<!DOCTYPE>") 
            self._element.text = name
            self.publicId = publicId
            self.systemId = systemId
        __init__.func_annotations = {}

        def _getPublicId(self):
            return self._element.get(u"publicId", u"")
        _getPublicId.func_annotations = {}

        def _setPublicId(self, value):
            if value is not None:
                self._element.set(u"publicId", value)
        _setPublicId.func_annotations = {}

        publicId = property(_getPublicId, _setPublicId)
    
        def _getSystemId(self):
            return self._element.get(u"systemId", u"")
        _getSystemId.func_annotations = {}

        def _setSystemId(self, value):
            if value is not None:
                self._element.set(u"systemId", value)
        _setSystemId.func_annotations = {}

        systemId = property(_getSystemId, _setSystemId)
    
    class Document(Element):
        def __init__(self):
            Element.__init__(self, u"DOCUMENT_ROOT")
        __init__.func_annotations = {}
    
    class DocumentFragment(Element):
        def __init__(self):
            Element.__init__(self, u"DOCUMENT_FRAGMENT")
        __init__.func_annotations = {}
    
    def testSerializer(element):
        rv = []
        finalText = None
        def serializeElement(element, indent=0):
            if not(hasattr(element, u"tag")):
                element = element.getroot()
            if element.tag == u"<!DOCTYPE>":
                if element.get(u"publicId") or element.get(u"systemId"):
                    publicId = element.get(u"publicId") or u""
                    systemId = element.get(u"systemId") or u""
                    rv.append( u"""<!DOCTYPE %s "%s" "%s">"""%(
                            element.text, publicId, systemId))
                else:     
                    rv.append(u"<!DOCTYPE %s>"%(element.text,))
            elif element.tag == u"DOCUMENT_ROOT":
                rv.append(u"#document")
                if element.text:
                    rv.append(u"|%s\"%s\""%(u' '*(indent+2), element.text))
                if element.tail:
                    finalText = element.tail
            elif element.tag == ElementTree.Comment:
                rv.append(u"|%s<!-- %s -->"%(u' '*indent, element.text))
            else:
                assert type(element.tag) is unicode, u"Expected unicode, got %s, %s"%(type(element.tag), element.tag)
                nsmatch = tag_regexp.match(element.tag)

                if nsmatch is None:
                    name = element.tag
                else:
                    ns, name = nsmatch.groups()
                    prefix = constants.prefixes[ns]
                    name = u"%s %s"%(prefix, name)
                rv.append(u"|%s<%s>"%(u' '*indent, name))

                if hasattr(element, u"attrib"):
                    attributes = []
                    for name, value in element.attrib.items():
                        nsmatch = tag_regexp.match(name)
                        if nsmatch is not None:
                            ns, name = nsmatch.groups()
                            prefix = constants.prefixes[ns]
                            attr_string = u"%s %s"%(prefix, name)
                        else:
                            attr_string = name
                        attributes.append((attr_string, value))

                    for name, value in sorted(attributes):
                        rv.append(u'|%s%s="%s"' % (u' '*(indent+2), name, value))
                if element.text:
                    rv.append(u"|%s\"%s\"" %(u' '*(indent+2), element.text))
            indent += 2
            for child in element:
                serializeElement(child, indent)
            if element.tail:
                rv.append(u"|%s\"%s\"" %(u' '*(indent-2), element.tail))
        serializeElement.func_annotations = {}
        serializeElement(element, 0)
    
        if finalText is not None:
            rv.append(u"|%s\"%s\""%(u' '*2, finalText))
    
        return u"\n".join(rv)
    testSerializer.func_annotations = {}
    
    def tostring(element):
        u"""Serialize an element and its child nodes to a string"""
        rv = []
        finalText = None
        filter = ihatexml.InfosetFilter()
        def serializeElement(element):
            if type(element) == type(ElementTree.ElementTree):
                element = element.getroot()
            
            if element.tag == u"<!DOCTYPE>":
                if element.get(u"publicId") or element.get(u"systemId"):
                    publicId = element.get(u"publicId") or u""
                    systemId = element.get(u"systemId") or u""
                    rv.append( u"""<!DOCTYPE %s PUBLIC "%s" "%s">"""%(
                            element.text, publicId, systemId))
                else:     
                    rv.append(u"<!DOCTYPE %s>"%(element.text,))
            elif element.tag == u"DOCUMENT_ROOT":
                if element.text:
                    rv.append(element.text)
                if element.tail:
                    finalText = element.tail
    
                for child in element:
                    serializeElement(child)
    
            elif type(element.tag) == type(ElementTree.Comment):
                rv.append(u"<!--%s-->"%(element.text,))
            else:
                #This is assumed to be an ordinary element
                if not element.attrib:
                    rv.append(u"<%s>"%(ifilter.fromXmlName(element.tag),))
                else:
                    attr = u" ".join([u"%s=\"%s\""%(
                                ifilter.fromXmlName(name), value) 
                                     for name, value in element.attrib.items()])
                    rv.append(u"<%s %s>"%(element.tag, attr))
                if element.text:
                    rv.append(element.text)
    
                for child in element:
                    serializeElement(child)
    
                rv.append(u"</%s>"%(element.tag,))
    
            if element.tail:
                rv.append(element.tail)
        serializeElement.func_annotations = {}
    
        serializeElement(element)
    
        if finalText is not None:
            rv.append(u"%s\""%(u' '*2, finalText))
    
        return u"".join(rv)
    tostring.func_annotations = {}
    
    class TreeBuilder(_base.TreeBuilder):
        documentClass = Document
        doctypeClass = DocumentType
        elementClass = Element
        commentClass = Comment
        fragmentClass = DocumentFragment
    
        def testSerializer(self, element):
            return testSerializer(element)
        testSerializer.func_annotations = {}
    
        def getDocument(self):
            if fullTree:
                return self.document._element
            else:
                if self.defaultNamespace is not None:
                    return self.document._element.find(
                        u"{%s}html"%self.defaultNamespace)
                else:
                    return self.document._element.find(u"html")
        getDocument.func_annotations = {}
        
        def getFragment(self):
            return _base.TreeBuilder.getFragment(self)._element
        getFragment.func_annotations = {}
        
    return locals()
getETreeBuilder.func_annotations = {}


getETreeModule = moduleFactoryFactory(getETreeBuilder)
