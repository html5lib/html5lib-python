import gettext
_ = gettext.gettext

import new
import copy

import _base

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
            if type(element) == type(ElementTree.ElementTree):
                element = element.getroot()
            
            if node.tag in ("<DOCUMENT_ROOT>", "<DOCUMENT_FRAGMENT>"):
                for token in self.walkChildren(node):
                    yield token
            
            elif node.tag == "<!DOCTYPE>":
                yield self.doctype(node.text)
                if node.tail:
                    for token in self.text(node.tail):
                        yield token
            
            elif type(node.tag) == type(ElementTree.Comment):
                yield self.comment(node.text)
                if node.tail:
                    for token in self.text(node.tail):
                        yield token
            
            else:
                #This is assumed to be an ordinary element
                for token in self.element(node):
                    yield token
        
        def walkChildren(self, node):
            if node.text:
                for token in self.text(node.text):
                    yield token
            for childNode in node.getchildren():
                for token in self.walk(childNode):
                    yield token
            if node.tail:
                for token in self.text(node.tail):
                    yield token
    
    return locals()
