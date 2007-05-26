import gettext
_ = gettext.gettext

import _base

class TreeWalker(_base.TreeWalker):
    def walk(self, node):
        # testing node.type allows us not to import treebuilders.simpletree
        if node.type in (1, 2): # Document or DocumentFragment
            for token in self.serializeChildren(node):
                yield token
        
        elif node.type == 3: # DocumentType
            yield self.doctype(node.name)
        
        elif node.type == 4: # TextNode
            for token in self.text(node.value):
                yield token
        
        elif node.type == 5: # Element
            for token in self.element(node.name, \
              node.attributes.items(), node.childNodes):
                yield token
        
        elif node.type == 6: # CommentNode
            yield self.comment(node.data)
        
        else:
            yield self.unknown(node.type)
    
    def walkChildren(self, node):
        for childNode in node.childNodes:
            for token in self.walk(childNode):
                yield token
