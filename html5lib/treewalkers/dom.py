# Copyright (c) 2006-2013 James Graham and other contributors
#
# Permission is hereby granted, free of charge, to any person obtaining
# a copy of this software and associated documentation files (the
# "Software"), to deal in the Software without restriction, including
# without limitation the rights to use, copy, modify, merge, publish,
# distribute, sublicense, and/or sell copies of the Software, and to
# permit persons to whom the Software is furnished to do so, subject to
# the following conditions:
#
# The above copyright notice and this permission notice shall be
# included in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
# MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
# NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE
# LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION
# OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION
# WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

from __future__ import absolute_import, division, unicode_literals

from xml.dom import Node

from . import base


class TreeWalker(base.NonRecursiveTreeWalker):
    def getNodeDetails(self, node):
        if node.nodeType == Node.DOCUMENT_TYPE_NODE:
            return base.DOCTYPE, node.name, node.publicId, node.systemId

        elif node.nodeType in (Node.TEXT_NODE, Node.CDATA_SECTION_NODE):
            return base.TEXT, node.nodeValue

        elif node.nodeType == Node.ELEMENT_NODE:
            attrs = {}
            for attr in list(node.attributes.keys()):
                attr = node.getAttributeNode(attr)
                if attr.namespaceURI:
                    attrs[(attr.namespaceURI, attr.localName)] = attr.value
                else:
                    attrs[(None, attr.name)] = attr.value
            return (base.ELEMENT, node.namespaceURI, node.nodeName,
                    attrs, node.hasChildNodes())

        elif node.nodeType == Node.COMMENT_NODE:
            return base.COMMENT, node.nodeValue

        elif node.nodeType in (Node.DOCUMENT_NODE, Node.DOCUMENT_FRAGMENT_NODE):
            return (base.DOCUMENT,)

        else:
            return base.UNKNOWN, node.nodeType

    def getFirstChild(self, node):
        return node.firstChild

    def getNextSibling(self, node):
        return node.nextSibling

    def getParentNode(self, node):
        return node.parentNode
