from BeautifulSoup import BeautifulSoup, Tag, NavigableString, Comment, Declaration

import _base

class AttrList(object):
    def __init__(self, element):
        self.element = element
        self.attrs = dict(self.element.attrs)
    def __iter__(self):
        return self.attrs.items().__iter__()
    def __setitem__(self, name, value):
        "set attr", name, value
        self.element[name] = value
    def items(self):
        return self.attrs.items()
    def keys(self):
        return self.attrs.keys()
    def __getitem__(self, name):
        return self.attrs[name]
    def __contains__(self, name):
        return name in self.attrs.keys()


class Element(_base.Node):
    def __init__(self, element, soup):
        _base.Node.__init__(self, element.name)
        self.element = element
        self.soup=soup

    def appendChild(self, node):
        if (node.element.__class__ == NavigableString and self.element.contents
            and self.element.contents[-1].__class__ == NavigableString):
            newNode = TextNode(NavigableString(
                self.element.contents[-1]+node.element), self.soup)
            self.element.contents[-1].extract()
            self.appendChild(newNode)
        else:
            self.element.insert(len(self.element.contents), node.element)
            node.parent = self
    
    def getAttributes(self):
        return AttrList(self.element)

    def setAttributes(self, attributes):
        if attributes:
            for name, value in attributes.items():
                self.element[name] =  value

    attributes = property(getAttributes, setAttributes)
    
    def insertText(self, data, insertBefore=None):
        text = TextNode(NavigableString(data), self.soup)
        if insertBefore:
            self.insertBefore(text, insertBefore)
        else:
            self.appendChild(text)

    def insertBefore(self, node, refNode):
        index = self.element.contents.index(refNode.element)
        if (node.element.__class__ == NavigableString and self.element.contents
            and self.element.contents[index-1].__class__ == NavigableString):
            newNode = TextNode(NavigableString(
                self.element.contents[index-1]+node.element), self.soup)
            self.element.contents[index-1].extract()
            self.insertBefore(newNode, refNode)
        else:
            self.element.insert(index, node.element)
            node.parent = self

    def removeChild(self, node):
        node.element.extract()
        node.parent = None

    def reparentChildren(self, newParent):
        while self.element.contents:
            child = self.element.contents[0]
            child.extract()
            if isinstance(child, Tag):
                newParent.appendChild(Element(child, self.soup))
            else:
                newParent.appendChild(TextNode(child, self.soup))

    def cloneNode(self):
        node = Element(Tag(self.soup, self.element.name), self.soup)
        for key,value in self.attributes:
            node.attributes[key] = value
        return node

    def hasContent(self):
        return self.element.contents

class TextNode(Element):
    def __init__(self, element, soup):
        _base.Node.__init__(self, None)
        self.element = element
        self.soup=soup
    
    def cloneNode(self):
        raise NotImplementedError

class TreeBuilder(_base.TreeBuilder):
    def documentClass(self):
        self.soup = BeautifulSoup("")
        return Element(self.soup, self.soup)
    
    def insertDoctype(self, name, publicId, systemId):
        self.soup.insert(0, Declaration(name))
    
    def elementClass(self, name):
        return Element(Tag(self.soup, name), self.soup)
        
    def commentClass(self, data):
        return TextNode(Comment(data), self.soup)
    
    def fragmentClass(self):
        self.soup = BeautifulSoup("")
        self.soup.name = "[document_fragment]"
        return Element(self.soup, self.soup) 

    def appendChild(self, node):
        self.soup.insert(len(self.soup.contents), node.element)

    def testSerializer(self, element):
        return testSerializer(element)

    def getDocument(self):
        return self.soup
    
    def getFragment(self):
        return _base.TreeBuilder.getFragment(self).element
    
def testSerializer(element):
    rv = []
    def serializeElement(element, indent=0):
        if isinstance(element, Declaration):
            rv.append("|%s<!DOCTYPE %s>"%(' '*indent, element.string))
        elif isinstance(element, BeautifulSoup):
            if element.name == "[document_fragment]":
                rv.append("#document-fragment")                
            else:
                rv.append("#document")

        elif isinstance(element, Comment):
            rv.append("|%s<!-- %s -->"%(' '*indent, element.string))
        elif isinstance(element, unicode):
            rv.append("|%s\"%s\"" %(' '*indent, element))
        else:
            rv.append("|%s<%s>"%(' '*indent, element.name))
            if element.attrs:
                for name, value in element.attrs:
                    rv.append('|%s%s="%s"' % (' '*(indent+2), name, value))
        indent += 2
        if hasattr(element, "contents"):
            for child in element.contents:
                serializeElement(child, indent)
    serializeElement(element, 0)

    return "\n".join(rv)
