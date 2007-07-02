from lxml import etree

from gettext import gettext
_ = gettext

import _base

from html5lib.constants import voidElements

class TreeWalker(_base.NonRecursiveTreeWalker):
    def getNodeDetails(self, node):
        if isinstance(node, tuple): # Text node
            node, key = node
            assert key in ("text", "tail"), _("Text nodes are text or tail, found %s") % key
            return _base.TEXT, getattr(node, key)

        if not(hasattr(node, "tag")):
            node = node.getroot()

        if node.tag in ("<DOCUMENT_ROOT>", "<DOCUMENT_FRAGMENT>"):
            return (_base.DOCUMENT,)

        elif node.tag == "<!DOCTYPE>":
            return _base.DOCTYPE, node.text

        elif node.tag == etree.Comment:
            return _base.COMMENT, node.text

        else:
            #This is assumed to be an ordinary element
            return _base.ELEMENT, node.tag, node.attrib.items(), bool(node) or node.text

    def getFirstChild(self, node):
        assert not isinstance(node, tuple), _("Text nodes have no children")

        assert bool(node) or node.text, "Node has no children"
        if node.text:
            return (node, "text")
        else:
            return node[0]

    def getNextSibling(self, node):
        if isinstance(node, tuple): # Text node
            node, key = node
            assert key in ("text", "tail"), _("Text nodes are text or tail, found %s") % key
            if key == "text":
                # XXX: we cannot use a "bool(node) and node[0] or None" construct here
                # because node[0] might evaluate to False if it has no child element
                if bool(node):
                    return node[0]
                else:
                    return None
            else: # tail
                return node.getnext()

        return node.tail and (node, "tail") or node.getnext()

    def getParentNode(self, node):
        if isinstance(node, tuple): # Text node
            node, key = node
            assert key in ("text", "tail"), _("Text nodes are text or tail, found %s") % key
            if key == "text":
                return node
            # else: fallback to "normal" processing

        return node.getparent()
