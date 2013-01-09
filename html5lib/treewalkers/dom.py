from __future__ import absolute_import
from xml.dom import Node

import gettext
_ = gettext.gettext

from . import _base
from html5lib.constants import voidElements

class TreeWalker(_base.NonRecursiveTreeWalker):
    def getNodeDetails(self, node):
        if node.nodeType == Node.DOCUMENT_TYPE_NODE:
            return _base.DOCTYPE, node.name, node.publicId, node.systemId

        elif node.nodeType in (Node.TEXT_NODE, Node.CDATA_SECTION_NODE):
            return _base.TEXT, node.nodeValue

        elif node.nodeType == Node.ELEMENT_NODE:
            attrs = {}
            for attr in list(node.attributes.keys()):
                attr = node.getAttributeNode(attr)
                if attr.namespaceURI:
                    attrs[(attr.namespaceURI,attr.localName)] = attr.value
                else:
                    attrs[(None,attr.name)] = attr.value
            return (_base.ELEMENT, node.namespaceURI, node.nodeName, 
                    attrs, node.hasChildNodes())

        elif node.nodeType == Node.COMMENT_NODE:
            return _base.COMMENT, node.nodeValue

        elif node.nodeType in (Node.DOCUMENT_NODE, Node.DOCUMENT_FRAGMENT_NODE):
            return (_base.DOCUMENT,)

        else:
            return _base.UNKNOWN, node.nodeType
    getNodeDetails.func_annotations = {}

    def getFirstChild(self, node):
        return node.firstChild
    getFirstChild.func_annotations = {}

    def getNextSibling(self, node):
        return node.nextSibling
    getNextSibling.func_annotations = {}

    def getParentNode(self, node):
        return node.parentNode
    getParentNode.func_annotations = {}
