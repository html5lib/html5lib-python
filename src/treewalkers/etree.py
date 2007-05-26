import gettext
_ = gettext.gettext

from constants import voidElements, spaceCharacters

spaceCharacters = u''.join(spaceCharacters)

import new
import copy

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

    def _charactersToken(characters):
        return {"type": characters.lstrip(spaceCharacters) and "Characters" or "SpaceCharacters",
                 "data": characters}
    
    class TreeWalker(object):
        def serialize(self, node):
            if type(element) == type(ElementTree.ElementTree):
                element = element.getroot()
            
            if node.tag in ("<DOCUMENT_ROOT>", "<DOCUMENT_FRAGMENT>"):
                if node.text:
                    yield self.charactersToken(node.text)
                for childNode in node.getchildren():
                    for token in self.serialize(childNode):
                        yield token
            
            elif node.tag == "<!DOCTYPE>":
                yield {"type": "Doctype", "name": node.text, "data": False}
            
            elif type(node.tag) == type(ElementTree.Comment):
                yield {"type": "Comment", "data": node.text}
            
            else:
                #This is assumed to be an ordinary element
                if node.name in voidElements:
                    yield {"type": "EmptyTag", "name": node.tag,
                            "data": node.attrib.items()}
                    if node.childNodes or node.text:
                        yield {"type": "SerializeError",
                                "data": _("Void element has children")}
                else:
                    yield {"type": "StartTag", "name": node.name,
                            "data": node.attrib.items()}
                    if node.text:
                        yield self.charactersToken(node.text)
                    for childNode in node.getchildren():
                        for token in self.serialize(childNode):
                            yield token
                    yield {"type": "EndTag", "name": node.tag, "data": []}
            
            if node.tail:
                yield self.charactersToken(node.tail)
    
    return locals()
