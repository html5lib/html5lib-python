import gettext
_ = gettext.gettext

import new
import copy

import _base
from constants import voidElements

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

    class TreeWalker(_base.TreeWalker):
        def walk(self, node):
            if not(hasattr(node, "tag")):
                node = node.getroot()

            if node.tag in ("<DOCUMENT_ROOT>", "<DOCUMENT_FRAGMENT>"):
                for token in self.walkChildren(node):
                    yield token

            elif node.tag == "<!DOCTYPE>":
                yield self.doctype(node.text)

            elif type(node.tag) == type(ElementTree.Comment):
                yield self.comment(node.text)

            else:
                #This is assumed to be an ordinary element
                if node.tag in voidElements:
                    for token in self.emptyTag(node.tag, \
                      node.attrib.items(), len(node) or node.text):
                        yield token
                else:
                    yield self.startTag(node.tag, node.attrib.items())
                    for token in self.walkChildren(node):
                        yield token
                    yield self.endTag(node.tag)

            if node.tail:
                for token in self.text(node.tail):
                    yield token

        def walkChildren(self, node):
            if node.text:
                for token in self.text(node.text):
                    yield token
            for childNode in node.getchildren():
                for token in self.walk(childNode):
                    yield token

    return locals()
