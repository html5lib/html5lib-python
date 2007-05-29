import gettext
_ = gettext.gettext

from BeautifulSoup import BeautifulSoup, Declaration, Comment

import _base

class TreeWalker(_base.NonRecursiveTreeWalker):
    def getNodeDetails(self, node):
        if isinstance(node, BeautifulSoup): # Document or DocumentFragment
            return (_base.DOCUMENT,)

        elif isinstance(node, Declaration): # DocumentType
            return _base.DOCTYPE, node.string

        elif isinstance(node, Comment):
            return _base.COMMENT, node.data

        elif isinstance(node, unicode): # TextNode
            return _base.TEXT, node

        elif isinstance(node, Tag): # Element
            return _base.ELEMENT, node.name, \
              node.attrs.items(), node.contents

        else:
            return _base.UNKNOWN, node.__class__.__name__

    def getFirstChild(self, node):
        return node.contents[0]

    def getNextSibling(self, node):
        return node.nextSibling

    def getParentNode(self, node):
        return node.parent
