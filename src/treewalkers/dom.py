from xml.dom import Node

import gettext
_ = gettext.gettext

from constants import voidElements, spaceCharacters

spaceCharacters = u''.join(spaceCharacters)

class TreeWalker(object):
    def serialize(self, node):
        if node.nodeType in (Node.DOCUMENT_NODE, Node.DOCUMENT_FRAGMENT_NODE):
            for childNode in node.childNodes:
                for token in self.serialize(childNode):
                    yield token
        
        elif node.nodeType == Node.DOCUMENT_TYPE_NODE:
            yield {"type": "Doctype", "name": node.nodeName, "data": False}
        
        elif node.nodeType in (Node.TEXT_NODE, Node.CDATA_SECTION_NODE):
            yield {"type": node.nodeValue.lstrip(spaceCharacters) and "Characters" or "SpaceCharacters",
                    "data": node.nodeValue}
        
        elif node.nodeType == Node.ELEMENT_NODE:
            if node.nodeName in voidElements:
                yield {"type": "EmptyTag", "name": node.nodeName,
                        "data": node.attributes.items()}
                if node.childNodes:
                    yield {"type": "SerializeError",
                            "data": _("Void element has children")}
            else:
                yield {"type": "StartTag", "name": node.name,
                        "data": node.attributes.items()}
                for childNode in node.childNodes:
                    for token in self.serialize(childNode):
                        yield token
                yield {"type": "EndTag", "name": node.nodeName, "data": []}
        
        elif node.nodeType == Node.COMMENT_NODE:
            yield {"type": "Comment", "data": node.nodeValue}
        
        else:
            yield {"type": "SerializeError",
                    "data": _("Unknown node type: " + node.nodeType)}
