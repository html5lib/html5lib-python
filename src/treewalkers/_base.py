import gettext
_ = gettext.gettext

from constants import voidElements, spaceCharacters
spaceCharacters = u"".join(spaceCharacters)

class TreeWalker(object):
    def __init__(self, tree):
        self.tree = tree

    def __iter__(self):
        raise NotImplementedError

    walk = __iter__

    def error(self, msg):
        return {"type": "SerializeError", "data": msg}

    def normalizeAttrs(self, attrs):
        if not attrs:
            attrs = []
        elif hasattr(attrs, 'items'):
            attrs = attrs.items()
        return attrs

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
        data = middle
        middle = data.rstrip(spaceCharacters)
        right = data[len(middle):]
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

class RecursiveTreeWalker(TreeWalker):
    def walkChildren(self, node):
        raise NodeImplementedError

    def element(self, node, name, attrs, hasChildren):
        if name in voidElements:
            for token in self.emptyTag(name, attrs, hasChildren):
                yield token
        else:
            yield self.startTag(name, attrs)
            if hasChildren:
                for token in self.walkChildren(node):
                    yield token
            yield self.endTag(name)

from xml.dom import Node

DOCUMENT = Node.DOCUMENT_NODE
DOCTYPE = Node.DOCUMENT_TYPE_NODE
TEXT = Node.TEXT_NODE
ELEMENT = Node.ELEMENT_NODE
COMMENT = Node.COMMENT_NODE
UNKNOWN = "<#UNKNOWN#>"

class NonRecursiveTreeWalker(TreeWalker):
    def getNodeDetails(self, node):
        raise NotImplementedError
    
    def getFirstChild(self, node):
        raise NotImplementedError
    
    def getNextSibling(self, node):
        raise NotImplementedError
    
    def getParentNode(self, node):
        raise NotImplementedError

    def walk(self):
        currentNode = self.tree
        while currentNode is not None:
            details = self.getNodeDetails(currentNode)
            type, details = details[0], details[1:]
            hasChildren = False

            if type == DOCTYPE:
                yield self.doctype(*details)

            elif type == TEXT:
                for token in self.text(*details):
                    yield token

            elif type == ELEMENT:
                name, attributes, hasChildren = details
                if name in voidElements:
                    for token in self.emptyTag(name, attributes, hasChildren):
                        yield token
                    hasChildren = False
                else:
                    yield self.startTag(name, attributes)

            elif type == COMMENT:
                yield self.comment(details[0])

            elif type == DOCUMENT:
                hasChildren = True

            else:
                yield self.unknown(details[0])
            
            firstChild = hasChildren and self.getFirstChild(currentNode) or None
            if firstChild is not None:
                currentNode = firstChild
            else:
                while currentNode is not None:
                    details = self.getNodeDetails(currentNode)
                    type, details = details[0], details[1:]
                    if type == ELEMENT:
                        name, attributes, hasChildren = details
                        if name not in voidElements:
                            yield self.endTag(name)
                    nextSibling = self.getNextSibling(currentNode)
                    if nextSibling is not None:
                        currentNode = nextSibling
                        break
                    if self.tree is currentNode:
                        currentNode = None
                    else:
                        currentNode = self.getParentNode(currentNode)
