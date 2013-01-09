
from __future__ import absolute_import
from xml.dom import minidom, Node, XML_NAMESPACE, XMLNS_NAMESPACE
import re
import weakref

from . import _base
from html5lib import constants, ihatexml
from html5lib.constants import namespaces
from html5lib.utils import moduleFactoryFactory

def getDomBuilder(DomImplementation):
    Dom = DomImplementation
    class AttrList(object):
        def __init__(self, element):
            self.element = element
        __init__.func_annotations = {}
        def __iter__(self):
            return list(self.element.attributes.items()).__iter__()
        __iter__.func_annotations = {}
        def __setitem__(self, name, value):
            self.element.setAttribute(name, value)
        __setitem__.func_annotations = {}
        def __len__(self):
            return len(list(self.element.attributes.items()))
        __len__.func_annotations = {}
        def items(self):
            return [(item[0], item[1]) for item in
                     list(self.element.attributes.items())]
        items.func_annotations = {}
        def keys(self):
            return list(self.element.attributes.keys())
        keys.func_annotations = {}
        def __getitem__(self, name):
            return self.element.getAttribute(name)
        __getitem__.func_annotations = {}

        def __contains__(self, name):
            if isinstance(name, tuple):
                raise NotImplementedError
            else:
                return self.element.hasAttribute(name)
        __contains__.func_annotations = {}
    
    class NodeBuilder(_base.Node):
        def __init__(self, element):
            _base.Node.__init__(self, element.nodeName)
            self.element = element
        __init__.func_annotations = {}

        namespace = property(lambda self:hasattr(self.element, u"namespaceURI")
                             and self.element.namespaceURI or None)

        def appendChild(self, node):
            node.parent = self
            self.element.appendChild(node.element)
        appendChild.func_annotations = {}
    
        def insertText(self, data, insertBefore=None):
            text = self.element.ownerDocument.createTextNode(data)
            if insertBefore:
                self.element.insertBefore(text, insertBefore.element)
            else:
                self.element.appendChild(text)
        insertText.func_annotations = {}
    
        def insertBefore(self, node, refNode):
            self.element.insertBefore(node.element, refNode.element)
            node.parent = self
        insertBefore.func_annotations = {}
    
        def removeChild(self, node):
            if node.element.parentNode == self.element:
                self.element.removeChild(node.element)
            node.parent = None
        removeChild.func_annotations = {}
    
        def reparentChildren(self, newParent):
            while self.element.hasChildNodes():
                child = self.element.firstChild
                self.element.removeChild(child)
                newParent.element.appendChild(child)
            self.childNodes = []
        reparentChildren.func_annotations = {}
    
        def getAttributes(self):
            return AttrList(self.element)
        getAttributes.func_annotations = {}
    
        def setAttributes(self, attributes):
            if attributes:
                for name, value in list(attributes.items()):
                    if isinstance(name, tuple):
                        if name[0] is not None:
                            qualifiedName = (name[0] + u":" + name[1])
                        else:
                            qualifiedName = name[1]
                        self.element.setAttributeNS(name[2], qualifiedName, 
                                                    value)
                    else:
                        self.element.setAttribute(
                            name, value)
        setAttributes.func_annotations = {}
        attributes = property(getAttributes, setAttributes)
    
        def cloneNode(self):
            return NodeBuilder(self.element.cloneNode(False))
        cloneNode.func_annotations = {}
    
        def hasContent(self):
            return self.element.hasChildNodes()
        hasContent.func_annotations = {}

        def getNameTuple(self):
            if self.namespace == None:
                return namespaces[u"html"], self.name
            else:
                return self.namespace, self.name
        getNameTuple.func_annotations = {}

        nameTuple = property(getNameTuple)

    class TreeBuilder(_base.TreeBuilder):
        def documentClass(self):
            self.dom = Dom.getDOMImplementation().createDocument(None,None,None)
            return weakref.proxy(self)
        documentClass.func_annotations = {}
    
        def insertDoctype(self, token):
            name = token[u"name"]
            publicId = token[u"publicId"]
            systemId = token[u"systemId"]

            domimpl = Dom.getDOMImplementation()
            doctype = domimpl.createDocumentType(name, publicId, systemId)
            self.document.appendChild(NodeBuilder(doctype))
            if Dom == minidom:
                doctype.ownerDocument = self.dom
        insertDoctype.func_annotations = {}
    
        def elementClass(self, name, namespace=None):
            if namespace is None and self.defaultNamespace is None:
                node = self.dom.createElement(name)
            else:
                node = self.dom.createElementNS(namespace, name)

            return NodeBuilder(node)
        elementClass.func_annotations = {}
            
        def commentClass(self, data):
            return NodeBuilder(self.dom.createComment(data))
        commentClass.func_annotations = {}
        
        def fragmentClass(self):
            return NodeBuilder(self.dom.createDocumentFragment())
        fragmentClass.func_annotations = {}
    
        def appendChild(self, node):
            self.dom.appendChild(node.element)
        appendChild.func_annotations = {}
    
        def testSerializer(self, element):
            return testSerializer(element)
        testSerializer.func_annotations = {}
    
        def getDocument(self):
            return self.dom
        getDocument.func_annotations = {}
        
        def getFragment(self):
            return _base.TreeBuilder.getFragment(self).element
        getFragment.func_annotations = {}
    
        def insertText(self, data, parent=None):
            data=data
            if parent != self:
                _base.TreeBuilder.insertText(self, data, parent)
            else:
                # HACK: allow text nodes as children of the document node
                if hasattr(self.dom, u'_child_node_types'):
                    if not Node.TEXT_NODE in self.dom._child_node_types:
                        self.dom._child_node_types=list(self.dom._child_node_types)
                        self.dom._child_node_types.append(Node.TEXT_NODE)
                self.dom.appendChild(self.dom.createTextNode(data))
        insertText.func_annotations = {}
    
        name = None
    
    def testSerializer(element):
        element.normalize()
        rv = []
        def serializeElement(element, indent=0):
            if element.nodeType == Node.DOCUMENT_TYPE_NODE:
                if element.name:
                    if element.publicId or element.systemId:
                        publicId = element.publicId or u""
                        systemId = element.systemId or u""
                        rv.append( u"""|%s<!DOCTYPE %s "%s" "%s">"""%(
                                u' '*indent, element.name, publicId, systemId))
                    else:
                        rv.append(u"|%s<!DOCTYPE %s>"%(u' '*indent, element.name))
                else:
                    rv.append(u"|%s<!DOCTYPE >"%(u' '*indent,))
            elif element.nodeType == Node.DOCUMENT_NODE:
                rv.append(u"#document")
            elif element.nodeType == Node.DOCUMENT_FRAGMENT_NODE:
                rv.append(u"#document-fragment")
            elif element.nodeType == Node.COMMENT_NODE:
                rv.append(u"|%s<!-- %s -->"%(u' '*indent, element.nodeValue))
            elif element.nodeType == Node.TEXT_NODE:
                rv.append(u"|%s\"%s\"" %(u' '*indent, element.nodeValue))
            else:
                if (hasattr(element, u"namespaceURI") and
                    element.namespaceURI != None):
                    name = u"%s %s"%(constants.prefixes[element.namespaceURI],
                                    element.nodeName)
                else:
                    name = element.nodeName
                rv.append(u"|%s<%s>"%(u' '*indent, name))
                if element.hasAttributes():
                    attributes = []
                    for i in xrange(len(element.attributes)):
                        attr = element.attributes.item(i)
                        name = attr.nodeName
                        value = attr.value
                        ns = attr.namespaceURI
                        if ns:
                            name = u"%s %s"%(constants.prefixes[ns], attr.localName)
                        else:
                            name = attr.nodeName
                        attributes.append((name, value))

                    for name, value in sorted(attributes):
                        rv.append(u'|%s%s="%s"' % (u' '*(indent+2), name, value))
            indent += 2
            for child in element.childNodes:
                serializeElement(child, indent)
        serializeElement.func_annotations = {}
        serializeElement(element, 0)
    
        return u"\n".join(rv)
    testSerializer.func_annotations = {}
    
    def dom2sax(node, handler, nsmap={u'xml':XML_NAMESPACE}):
      if node.nodeType == Node.ELEMENT_NODE:
        if not nsmap:
          handler.startElement(node.nodeName, node.attributes)
          for child in node.childNodes: dom2sax(child, handler, nsmap)
          handler.endElement(node.nodeName)
        else:
          attributes = dict(node.attributes.itemsNS()) 
    
          # gather namespace declarations
          prefixes = []
          for attrname in list(node.attributes.keys()):
            attr = node.getAttributeNode(attrname)
            if (attr.namespaceURI == XMLNS_NAMESPACE or
               (attr.namespaceURI == None and attr.nodeName.startswith(u'xmlns'))):
              prefix = (attr.nodeName != u'xmlns' and attr.nodeName or None)
              handler.startPrefixMapping(prefix, attr.nodeValue)
              prefixes.append(prefix)
              nsmap = nsmap.copy()
              nsmap[prefix] = attr.nodeValue
              del attributes[(attr.namespaceURI, attr.nodeName)]
    
          # apply namespace declarations
          for attrname in list(node.attributes.keys()):
            attr = node.getAttributeNode(attrname)
            if attr.namespaceURI == None and u':' in attr.nodeName:
              prefix = attr.nodeName.split(u':')[0]
              if prefix in nsmap:
                del attributes[(attr.namespaceURI, attr.nodeName)]
                attributes[(nsmap[prefix],attr.nodeName)]=attr.nodeValue
    
          # SAX events
          ns = node.namespaceURI or nsmap.get(None,None)
          handler.startElementNS((ns,node.nodeName), node.nodeName, attributes)
          for child in node.childNodes: dom2sax(child, handler, nsmap)
          handler.endElementNS((ns, node.nodeName), node.nodeName)
          for prefix in prefixes: handler.endPrefixMapping(prefix)
    
      elif node.nodeType in [Node.TEXT_NODE, Node.CDATA_SECTION_NODE]:
        handler.characters(node.nodeValue)
    
      elif node.nodeType == Node.DOCUMENT_NODE:
        handler.startDocument()
        for child in node.childNodes: dom2sax(child, handler, nsmap)
        handler.endDocument()
    
      elif node.nodeType == Node.DOCUMENT_FRAGMENT_NODE:
        for child in node.childNodes: dom2sax(child, handler, nsmap)
    
      else:
        # ATTRIBUTE_NODE
        # ENTITY_NODE
        # PROCESSING_INSTRUCTION_NODE
        # COMMENT_NODE
        # DOCUMENT_TYPE_NODE
        # NOTATION_NODE
        pass
    dom2sax.func_annotations = {}
        
    return locals()
getDomBuilder.func_annotations = {}


# The actual means to get a module!
getDomModule = moduleFactoryFactory(getDomBuilder)


# Keep backwards compatibility with things that directly load 
# classes/functions from this module
for key, value in list(getDomModule(minidom).__dict__.items()):
	globals()[key] = value
