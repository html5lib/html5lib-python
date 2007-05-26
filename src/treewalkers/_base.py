from constants import voidElements, spaceCharacters
spaceCharacters = u"".join(spaceCharacters)

class TreeWalker(object):
    def walk(self, node):
        raise NotImplementedError
    
    def walkChildren(self, node):
        raise NodeImplementedError
    
    def error(self, msg):
        yield {"type": "SerializeError", "data": msg}
    
    def normalizeAttrs(self, attrs):
        if not attrs:
            attrs = []
        elif hasattr(attrs, 'items'):
            attrs = attrs.items()
        return attrs
    
    def element(self, name, attrs, hasChildren):
        if name in voidElements:
            for token in self.emptyTag(name, attrs, hasChildren):
                yield token
        else:
            yield self.startTag(name, attrs)
            if hasChildren:
                for token in self.serializeChildren(node):
                    yield token
            yield self.endTag(name)

    def emptyTag(self, name, attrs, hasChildren=False):
        yield {"type": "EmptyTag", "name": name, \
                "data": self.normalizeAttrs(attrs)}
        if hasChildren:
            yield self.error(_("Void element has children"))
    
    def startTag(self, name, attrs):
        return {"type": "StartTag", "name": name, \
                 "data": self.normalizeAttrs(attrs)}
    
    def endTag(self, name):
        return {"type": "EndTag", "name": name, "data": []}
    
    def text(self, data):
        middle = data.lstrip(spaceCharacters)
        left = data[:len(data)-len(middle)]
        if left:
            yield {"type": "SpaceCharacters", "data": left}
        if middle:
            data = middle
            middle = data.rstrip(spaceCharacters)
            right = data[len(data)-len(middle):]
            if middle:
                yield {"type": "Characters", "data": middle}
            if right:
                yield {"type": "SpaceCharacters", "data": right}
    
    def comment(self, data):
        return {"type": "Comment", "data": data}
    
    def doctype(self, name):
        return {"type": "Doctype", "name": name, "data": name.upper() == "HTML"}
    
    def unknown(self, nodeType):
        return self.error(_("Unknown node type: ") + nodeType)
    