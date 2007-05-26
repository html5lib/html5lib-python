from xml.dom.pulldom import START_ELEMENT, END_ELEMENT, \
    COMMENT, IGNORABLE_WHITESPACE, CHARACTERS

import _base

from constants import voidElements

class TreeWalker(_base.TreeWalker):
    def walk(self, stream):
        previous = None
        for event in stream:
            if previous is not None:
                for token in self.tokens(previous, event):
                    yield token
            previous = event
        for token in self.tokens(previous, None):
            yield token
    
    def tokens(self, event, next):
        type, node = event
        if type == START_ELEMENT:
            name = node.nodeName
            if name in voidElements:
                for token in self.emptyTag(name, \
                  node.attributes.items(), not event or event[1] is not node):
                    yield token
            else:
                yield self.startTag(name, node.attributes.items())
        
        elif type == END_ELEMENT:
            name = node.nodeName
            if name not in voidElements:
                yield self.endTag(name)
        
        elif type == COMMENT:
            yield self.comment(node.nodeValue)
        
        elif type in (IGNORABLE_WHITESPACE, CHARACTERS):
            for token in self.text(node.nodeValue):
                yield token
        
        else:
            yield self.unknown(type)
    
    def walkChildren(self, node):
        raise Exception(_("PullDOM tree walker's walkChildren should never be called"))
