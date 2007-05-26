import gettext
_ = gettext.gettext

from BeautifulSoup import BeautifulSoup, Declaration, Comment

from constants import voidElements, spaceCharacters

spaceCharacters = u''.join(spaceCharacters)

class TreeWalker(object):
    def serialize(self, node):
        if isinstance(node, BeautifulSoup): # Document or DocumentFragment
            for childNode in node.contents:
                for token in self.serialize(childNode):
                    yield token
        
        elif isinstance(node, Declaration): # DocumentType
            yield {"type": "Doctype", "name": node.string, "data": False}
        
        elif isinstance(node, Comment):
            yield {"type": "Comment", "data": node.data}
        
        elif isinstance(node, unicode): # TextNode
            yield {"type": node.value.lstrip(spaceCharacters) and "Characters" or "SpaceCharacters",
                    "data": node.value}
        
        elif isinstance(node, Tag): # Element
            if node.name in voidElements:
                yield {"type": "EmptyTag", "name": node.name,
                        "data": node.attrs.items()}
                if node.childNodes:
                    yield {"type": "SerializeError",
                            "data": _("Void element has children")}
            else:
                yield {"type": "StartTag", "name": node.name,
                        "data": node.attrs.items()}
                for childNode in node.contents:
                    for token in self.serialize(childNode):
                        yield token
                yield {"type": "EndTag", "name": node.name, "data": []}
        
        else:
            yield {"type": "SerializeError",
                    "data": _("Unknown node type: " + node.__class__.__name__)}
