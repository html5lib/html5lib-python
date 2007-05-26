import gettext
_ = gettext.gettext

from BeautifulSoup import BeautifulSoup, Declaration, Comment

import _base

class TreeWalker(_base.TreeWalker):
    def walk(self, node):
        if isinstance(node, BeautifulSoup): # Document or DocumentFragment
            for token in self.walkChildren(childNode):
                yield token

        elif isinstance(node, Declaration): # DocumentType
            yield self.doctype(node.string)

        elif isinstance(node, Comment):
            yield self.comment(node.data)

        elif isinstance(node, unicode): # TextNode
            for token in self.text(node):
                yield token

        elif isinstance(node, Tag): # Element
            for token in self.element(node, node.name, \
              node.attrs.items(), node.contents):
                yield token

        else:
            yield self.unknown(node.__class__.__name__)

    def walkChildren(self, node):
        for childNode in node.contents:
            for token in self.walk(childNode):
                yield token
