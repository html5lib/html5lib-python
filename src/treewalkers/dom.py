from xml.dom import Node

import gettext
_ = gettext.gettext

import _base

class TreeWalker(_base.TreeWalker):
    def walk(self, node):
        if node.nodeType in (Node.DOCUMENT_NODE, Node.DOCUMENT_FRAGMENT_NODE):
            for token in self.walkChildren(node):
                yield token
        
        elif node.nodeType == Node.DOCUMENT_TYPE_NODE:
            yield self.doctype(node.nodeName)
        
        elif node.nodeType in (Node.TEXT_NODE, Node.CDATA_SECTION_NODE):
            for token in self.text(node.nodeValue):
                yield token
        
        elif node.nodeType == Node.ELEMENT_NODE:
            for token in self.element(node.nodeName, \
              node.attributes.items(), node.childNodes):
                yield token
        
        elif node.nodeType == Node.COMMENT_NODE:
            yield self.comment(node.nodeValue)
        
        else:
            yield self.unknown(node.nodeType)
    
    def walkChildren(self, node):
        for childNode in node.childNodes:
            for token in self.walk(node):
                yield token
