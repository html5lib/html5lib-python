import gettext
_ = gettext.gettext

from constants import voidElements, spaceCharacters

spaceCharacters = u''.join(spaceCharacters)

class TreeWalker(object):
    def serialize(self, node):
        # testing node.type allows us not to import treebuilders.simpletree
        if node.type in (1, 2): # Document or DocumentFragment
            for childNode in node.childNodes:
                for token in self.serialize(childNode):
                    yield token
        
        elif node.type == 3: # DocumentType
            yield {"type": "Doctype", "name": node.name, "data": False}
        
        elif node.type == 4: # TextNode
            yield {"type": node.value.lstrip(spaceCharacters) and "Characters" or "SpaceCharacters",
                    "data": node.value}
        
        elif node.type == 5: # Element
            if node.name in voidElements:
                yield {"type": "EmptyTag", "name": node.name,
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
                yield {"type": "EndTag", "name": node.name, "data": []}
        
        elif node.type == 6: # CommentNode
            yield {"type": "Comment", "data": node.data}
        
        else:
            yield {"type": "SerializeError",
                    "data": _("Unknown node type: " + node.type)}
