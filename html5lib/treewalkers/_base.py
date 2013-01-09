from __future__ import absolute_import
import gettext
_ = gettext.gettext

from html5lib.constants import voidElements, spaceCharacters
spaceCharacters = u"".join(spaceCharacters)

class TreeWalker(object):
    def __init__(self, tree):
        self.tree = tree
    __init__.func_annotations = {}

    def __iter__(self):
        raise NotImplementedError
    __iter__.func_annotations = {}

    def error(self, msg):
        return {u"type": u"SerializeError", u"data": msg}
    error.func_annotations = {}

    def normalizeAttrs(self, attrs):
        newattrs = {}
        if attrs:
            #TODO: treewalkers should always have attrs
            for (namespace,name),value in attrs.items():
                namespace = unicode(namespace) if namespace else None
                name = unicode(name)
                value = unicode(value)
                newattrs[(namespace,name)] = value
        return newattrs
    normalizeAttrs.func_annotations = {}

    def emptyTag(self, namespace, name, attrs, hasChildren=False):
        yield {u"type": u"EmptyTag", u"name": unicode(name), 
               u"namespace":unicode(namespace),
               u"data": self.normalizeAttrs(attrs)}
        if hasChildren:
            yield self.error(_(u"Void element has children"))
    emptyTag.func_annotations = {}

    def startTag(self, namespace, name, attrs):
        return {u"type": u"StartTag", 
                u"name": unicode(name),
                u"namespace":unicode(namespace),
                u"data": self.normalizeAttrs(attrs)}
    startTag.func_annotations = {}

    def endTag(self, namespace, name):
        return {u"type": u"EndTag", 
                u"name": unicode(name),
                u"namespace":unicode(namespace),
                u"data": {}}
    endTag.func_annotations = {}

    def text(self, data):
        data = unicode(data)
        middle = data.lstrip(spaceCharacters)
        left = data[:len(data)-len(middle)]
        if left:
            yield {u"type": u"SpaceCharacters", u"data": left}
        data = middle
        middle = data.rstrip(spaceCharacters)
        right = data[len(middle):]
        if middle:
            yield {u"type": u"Characters", u"data": middle}
        if right:
            yield {u"type": u"SpaceCharacters", u"data": right}
    text.func_annotations = {}

    def comment(self, data):
        return {u"type": u"Comment", u"data": unicode(data)}
    comment.func_annotations = {}

    def doctype(self, name, publicId=None, systemId=None, correct=True):
        return {u"type": u"Doctype",
                u"name": name is not None and unicode(name) or u"",
                u"publicId": publicId,
                u"systemId": systemId,
                u"correct": correct}
    doctype.func_annotations = {}

    def entity(self, name):
        return {u"type": u"Entity", u"name": unicode(name)}
    entity.func_annotations = {}

    def unknown(self, nodeType):
        return self.error(_(u"Unknown node type: ") + nodeType)
    unknown.func_annotations = {}

class RecursiveTreeWalker(TreeWalker):
    def walkChildren(self, node):
        raise NodeImplementedError
    walkChildren.func_annotations = {}

    def element(self, node, namespace, name, attrs, hasChildren):
        if name in voidElements:
            for token in self.emptyTag(namespace, name, attrs, hasChildren):
                yield token
        else:
            yield self.startTag(name, attrs)
            if hasChildren:
                for token in self.walkChildren(node):
                    yield token
            yield self.endTag(name)
    element.func_annotations = {}

from xml.dom import Node

DOCUMENT = Node.DOCUMENT_NODE
DOCTYPE = Node.DOCUMENT_TYPE_NODE
TEXT = Node.TEXT_NODE
ELEMENT = Node.ELEMENT_NODE
COMMENT = Node.COMMENT_NODE
ENTITY = Node.ENTITY_NODE
UNKNOWN = u"<#UNKNOWN#>"

class NonRecursiveTreeWalker(TreeWalker):
    def getNodeDetails(self, node):
        raise NotImplementedError
    getNodeDetails.func_annotations = {}
    
    def getFirstChild(self, node):
        raise NotImplementedError
    getFirstChild.func_annotations = {}
    
    def getNextSibling(self, node):
        raise NotImplementedError
    getNextSibling.func_annotations = {}
    
    def getParentNode(self, node):
        raise NotImplementedError
    getParentNode.func_annotations = {}

    def __iter__(self):
        currentNode = self.tree
        while currentNode is not None:
            details = self.getNodeDetails(currentNode)
            type, details = details[0], details[1:]
            hasChildren = False
            endTag = None

            if type == DOCTYPE:
                yield self.doctype(*details)

            elif type == TEXT:
                for token in self.text(*details):
                    yield token

            elif type == ELEMENT:
                namespace, name, attributes, hasChildren = details
                if name in voidElements:
                    for token in self.emptyTag(namespace, name, attributes, 
                                               hasChildren):
                        yield token
                    hasChildren = False
                else:
                    endTag = name
                    yield self.startTag(namespace, name, attributes)

            elif type == COMMENT:
                yield self.comment(details[0])

            elif type == ENTITY:
                yield self.entity(details[0])

            elif type == DOCUMENT:
                hasChildren = True

            else:
                yield self.unknown(details[0])
            
            if hasChildren:
                firstChild = self.getFirstChild(currentNode)
            else:
                firstChild = None
            
            if firstChild is not None:
                currentNode = firstChild
            else:
                while currentNode is not None:
                    details = self.getNodeDetails(currentNode)
                    type, details = details[0], details[1:]
                    if type == ELEMENT:
                        namespace, name, attributes, hasChildren = details
                        if name not in voidElements:
                            yield self.endTag(namespace, name)
                    if self.tree is currentNode:
                        currentNode = None
                        break
                    nextSibling = self.getNextSibling(currentNode)
                    if nextSibling is not None:
                        currentNode = nextSibling
                        break
                    else:
                        currentNode = self.getParentNode(currentNode)
    __iter__.func_annotations = {}
