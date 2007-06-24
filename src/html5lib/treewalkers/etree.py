import gettext
_ = gettext.gettext

import new
import copy

import _base
from html5lib.constants import voidElements

moduleCache = {}

def getETreeModule(ElementTreeImplementation):
    name = "_" + ElementTreeImplementation.__name__+"builder"
    if name in moduleCache:
        return moduleCache[name]
    else:
        mod = new.module("_" + ElementTreeImplementation.__name__+"builder")
        objs = getETreeBuilder(ElementTreeImplementation)
        mod.__dict__.update(objs)
        moduleCache[name] = mod
        return mod

def getETreeBuilder(ElementTreeImplementation):
    ElementTree = ElementTreeImplementation

    class TreeWalker(_base.NonRecursiveTreeWalker):
        """Given the particular ElementTree representation, this implementation,
        to avoid using recursion, returns "nodes" as tuples with the following
        content:

        1. An Element node serving as *context* (it cannot be called the parent
           node due to the particular ``tail`` text nodes.

        2. Either the string literals ``"text"`` or ``"tail"`` or a child index

        3. A list used as a stack of all ancestor *context nodes*. It is a
           pair tuple whose first item is an Element and second item is a child
           index.
        """

        def getNodeDetails(self, node):
            if isinstance(node, tuple): # It might be the root Element
                elt, key, parents = node
                if key in ("text", "tail"):
                    return _base.TEXT, getattr(elt, key)
                else:
                    node = elt[int(key)]

            if not(hasattr(node, "tag")):
                node = node.getroot()

            if node.tag in ("<DOCUMENT_ROOT>", "<DOCUMENT_FRAGMENT>"):
                return (_base.DOCUMENT,)

            elif node.tag == "<!DOCTYPE>":
                return _base.DOCTYPE, node.text

            elif type(node.tag) == type(ElementTree.Comment):
                return _base.COMMENT, node.text

            else:
                #This is assumed to be an ordinary element
                return _base.ELEMENT, node.tag, node.attrib.items(), len(node) or node.text

        def getFirstChild(self, node):
            if isinstance(node, tuple): # It might be the root Element
                elt, key, parents = node
                assert key not in ("text", "tail"), "Text nodes have no children"
                parents.append((elt, int(key)))
                node = elt[int(key)]
            else:
                parents = []
            
            assert len(node) or node.text, "Node has no children"
            if node.text:
                return (node, "text", parents)
            else:
                return (node, 0, parents)

        def getNextSibling(self, node):
            assert isinstance(node, tuple), "Node is not a tuple: " + str(node)

            elt, key, parents = node
            if key == "text":
                key = -1
            elif key == "tail":
                elt, key = parents.pop()
            else:
                # Look for "tail" of the "revisited" node
                child = elt[key]
                if child.tail:
                    parents.append((elt, key))
                    return (child, "tail", parents)

            # case where key were "text" or "tail" or elt[key] had a tail
            key += 1
            if len(elt) > key:
                return (elt, key, parents)
            else:
                return None

        def getParentNode(self, node):
            assert isinstance(node, tuple)
            elt, key, parents = node
            if parents:
                elt, key = parents.pop()
                return elt, key, parents
            else:
                # HACK: We could return ``elt`` but None will stop the algorithm the same way
                return None

    return locals()
