try:
    from sets import ImmutableSet as frozenset
except:
    pass

import tokeniser
from tokeniser import ParseError

def tokenIsType(token, type):
    return isinstance(token, type)

scopingElements = frozenset("button", "caption", "html", "marquee", "object", 
                            "table", "td", "th")

formattingElements = frozenset("a", "b", "big", "em", "font", "i", "nobr", "s", 
                               "small", "strike", "strong", "tt", "u")

specialElements = frozenset("address", "area", "base", "basefont", "bgsound", 
                            "blockquote", "body", "br", "center", "col", 
                            "colgroup", "dd", "dir", "div", "dl", "dt", 
                            "embed", "fieldset", "form", "frame", "frameset",
                            "h1", "h2", "h3", "h4", "h5", "h6", "head", "hr", 
                            "iframe", "image", "img", "input", "isindex", "li",
                            "link", "listing", "menu", "meta", "noembed", 
                            "noframes", "noscript", "ol", "optgroup", "option",
                            "p", "param", "plaintext", "pre", "script", 
                            "select", "spacer", "style", "tbody", "textarea", 
                            "tfoot", "thead", "title", "tr", "ul", "wbr")

spaceCharacters = (u"\t", u"\n", u"\u000B", u"\u000C", u" ")

"""The scope markers are inserted when entering buttons, object
elements, marquees, table cells, and table captions, and are used to
prevent formatting from "leaking" into tables, buttons, object
elements, and marquees."""
Marker = object()

#Really crappy basic implementation of a DOM-core like thing
class Node(object):
    def __init__(self, name, value):
        self.name = name
        self.parent = None
        self.value = value
        self.childNodes = []
        self.attributes = {}
        self._flags = []
    def appendChild(self, node):
        if (isinstance(node, TextNode) and 
            isinstance(self.childNodes[-1}, TextNode))
            self.childNodes[-1].value += node.value
        else:
            self.childNodes.append(node)

    def cloneNode(self):
        newNode = type(self)(self.name, self.value)
        for attr, value in self.attributes.iteritems():
            newNode.attributes[attr] = value

class Document(Node):
    def __init__(self):
        Node.__init__(self, None, None, None)

class DocumentType(Node):
    def __init__(self, name):
        Node.__init__(self, name, None)

class TextNode(Node):
    def __init__(self, value):
        Node.__init__(self, None, value)

class Element(Node):
    def __init__(self, name):
        Node.__init__(self, name, None)

class CommentNode(node):
    def __init__(self, data):
        Node.__init__(self, None, None, None)
        self.data = data


class HTML5Parser(object):
    """Main parser class.
    """

    def __init__(self, strict = False):
        #Raise an exception on the first error encountered
        self.strict = strict

        self.openElements = []
        self.activeFormattingElements = []
        self.headPointer = None
        self.formPointer = None
        self.insertionMode = insertionModes["beforeHead"]
        self.document = Document()

    def parse(self, stream, innerHTML=False):
        """Stream should be a stream of unicode bytes. Character encoding
        issues have not yet been dealt with."""

        #We don't support document.write at the moment
        #If we do want to support it, we need to pass more state inc. 
        #the tokeniser around
        self.tokeniser = tokeniser.Tokeniser(stream)

        
        self.phases = {"initial":self.initialPhase,
                       "rootElement":self.rootElementPhase,
                       "main":self.mainPhase}

        self.insertionModes = {"beforeHead":BeforeHead, 
                               "inHead",:InHead,
                               "afterHead"self.afterHead,
                               "inBody", 
                               "inTable", 
                               "inCaption", 
                               "inColumnGroup", 
                               "inTableBody", 
                               "inRow", 
                               "inCell", 
                               "inSelect", 
                               "afterBody", 
                               "inFrameset", 
                               "afterFrameset"} 

        #We don't actually support inner HTML yet but this should allow 
        #assertations
        self.innerHTML = innerHTML

        #The parsing phase we are currently in
        self.phase = self.phases['initialPhase']
        
        #We pull a token from the tokeniser to get us started
        token = self.tokeniser.getToken()
        #With each token we pass the token to the method representing the 
        #current phase. The method must return the next token to be processed
        #or None if we are grabbing a new token from the tokeniser
        while not(tokenIsType(token, tokeniser.EOFToken)):
            token = self.phase(token)
            if token is None:
                token = self.tokeniser.getToken()

    def elementInScope(self, target, tableVariant=False):
        for node in self.openElements[::-1]:
            if node == target:
                return True
            elif node.name == "table":
                return False
            elif not tableVariant and node.name in scopingElements:
                return False
            elif node.name == "html":
                return False
        assert False #We should never reach this point

    def reconstructActiveFormattingElements(self):
        afe = self.activeFormattingElements
        entry = afe[-1]
        if entry == Marker or entry in self.openElements:
            return
        for i, entry in zip(xrange(0, len(afe)-1, -1), afe[:-1:-1]):
            if entry == Marker or entry in self.openElements:
                break
        for j in xrange(i,len(afe)-2):
            entry = afe[j+1]
            #Is this clone strictly necessary?
            clone = entry.cloneNode()
            self.openElements[-1].appendChild(clone)
            self.openElements.append(clone)
            afe[i] = clone

    def clearActiveFormattingElements(self):
        entry = self.activeFormattingElements.pop()
        while self.activeFormattingElements and not entry == Marker:
            entry = self.activeFormattingElements.pop()

    def createElementFromToken(token):
        #Change this if we ever implement different node types for different
        #elements
        element = Element(token.name)
        element.attributes = token.attributes
        return element

    def insertElementFromToken(token, parent=None):
        element = self.createElementFromToken(token)
        if parent is None:
            self.openElements[-1].appendChild(element)
            self.openElements.append(element)
        else:
            #Haven't implemented this yet as spec is vaugely unclear
            raise NotImplementedError

    def generateImpliedEndTags(self, exclude):
        while True:
            name = self.openElements[-1].name
            if name in ["dd", "dt", "li", "p", "td", "th",
                        "tr"] and name != exclude:
                token = tokeniser.EndTagToken()
                token.name = name
                nextToken = self.phase(token)
                #Not sure if the spec ensures this but we don't support it
                assert nextToken is None 
            else:
                break

    def resetInsertationMode(self):
        last = False
        newModes = {"select":"inSelect",
                    "td":"inCell",
                    "th":"inCell",
                    "tr":"inRow",
                    "tbody":"inTableBody",
                    "thead":"inTableBody",
                    "tfoot":"inTableBody",
                    "caption":"inCaption",
                    "colgroup":"inColumnGroup",
                    "table":"inTable",
                    "head":"inBody",
                    "body":"inBody"
                    "frameset":"inFrameset"}
        for node in self.openElements[::-1]:
            if node == self.openElements[0]:
                last = True
                if node.name not in ['td', 'th']:
                    assert self.innerHTML
                    raise NotImplementedError
            #Check for conditions that should only happen in the innerHTML case
            if node.name in ["select", "colgroup", "head", "frameset"]:
                assert self.innerHTML
            if node.name in newModes:
                self.insertationMode = self.insertationModes[
                    newModes[node.name]]
                break
            elif node.name == "html":
                if self.headPointer is None:
                    self.insertationMode = self.insertationModes["beforeHead"]
                else:
                   self.insertationMode = self.insertationModes["afterHead"] 
                break
            elif last:
                self.insertationMode = self.insertationModes["body"]
                break

    def insertCharacterTokens(self, element):
        """Insert all character tokens after the current token into the element 
        and return the next token""" 
        characterTokens = []
        while True:
            token = self.tokeniser.getToken()
            if tokenIsType(token, tokeniser.CharacterToken):
                characterTokens.append(token)
            else:
                break
        element.appendChild(TextNode("".join([t.value for t in
                                              characterTokens])))
        return token
        
    def initialPhase(self, token):
        if (tokenIsType(token, tokeniser.CharacterToken) and 
            token.data in spaceCharacters):
            #Ignore these whitespace tokens
            pass
        elif (tokenIsType(token, tokeniser.DoctypeToken) 
              and not token.error):
            #When we find a Doctype, append it to the tree and move on to
            #the next phase
            self.document.appendChild(DocumentType(token.name, None))
            self.phase = self.phases['rootElement']
        else:
            raise ParseError
                   
    def rootElementPhase(self, token):
        nextToken = None
        if tokenIsType(token, tokeniser.DoctypeToken):
            if self.strict:
                raise ParseError
        elif (tokenIsType(token, tokeniser.CharacterToken) and 
              token.data in spaceCharacters):
            self.document.appendChild(TextNode(token.data))
        else:
            self.document.append(Element("html"))
            self.phase = self.phases['main']
            nextToken = token
        return nextToken

    def mainPhase(self, token):
        nextToken = None
        if tokenIsType(token, tokeniser.DoctypeToken):
            if self.strict:
                raise ParseError
        elif (tokenIsType(token, tokeniser.StartTagToken) and 
              token.name == "html"):
            #XXX Should raise an error here if this is not the first start
            #tag token
            for attr, value in token.attributes.iteritems():
                if not attr in self.openElements[0].attributes:
                    self.openElements[0].attributes[attr] = value
        elif tokenIsType(token, tokeniser.EOFToken):
            self.generateImpliedEndTags()
            if (not self.innerHTML and not len(self.openElements) > 1 and
                self.openElements[1].name != "body" and self.strict):
                raise ParseError
        else:
            nextToken = self.insertionModes[self.insertionMode].parseToken(token)
        return nextToken

    
    def afterHead(self, token):
        nextToken = None
        if (tokenIsType(token, tokeniser.CharacterToken) 
            and token.data not in spaceCharacters):
            self.openElements[-1].appendChild(TextNode(token.data))
        elif (tokenIsType(token, tokeniser.CommentToken)):
            self.openElements[-1].appendChild(CommentNode(token.data))
        elif (tokenIsType(token, tokeniser.StartTag) and token.name == "body"):
            self.insertElementFromToken(token)
            self.insertionMode = self.insertionModes["inBody"]
        elif (tokenIsType(token, tokeniser.StartTag) and 
              token.name == "frameset"):
            self.insertElementFromToken(token)
            self.insertionMode = self.insertionModes["inFrameset"]
        elif (tokenIsType(token, tokeniser.StartTag) and 
              token.name in ["base", "link", "meta", "script", 
                             "style", "title"]):
            if self.strict:
                raise ParseError
            self.insertionMode = self.insertionModes["inHead"]
            nextToken = token
        else:
            self.insertElementFromToken(tokeniser.StartTag("body"))
            self.insertionMode = self.insertionModes["inBody"]
            nextToken = token
        return nextToken
    
    def inBody(self, token):
        def handlePEndTag():
            self.generateImpliedEndTags("p")
            if self.openElements[-1].name != "p":
                if self.strict:
                    raise ParseError
            while self.elementInScope("p"):
                self.openElements.pop()

        nextToken = None
        if tokenIsType(token, tokeniser.CharacterToken):
            self.reconstructActiveFormattingElements()
            self.openElements[-1].appendChild(TextNode(token.data))
        elif (tokenIsType(token, tokeniser.CommentToken)):
            self.openElements[-1].appendChild(CommentNode(token.data))
        elif (tokenIsType(token, tokeniser.StartTag) and 
              token.name == "script"):
            nextToken = self.insertionModes["inHead"](token)
        elif (tokenIsType(token, tokeniser.StartTag) and 
              token.name in ["base", "link", "meta", "style", "title"]):
            if self.strict:
                raise ParseError
            nextToken = self.insertionModes["inHead"](token)
        elif (tokenIsType(token, tokeniser.StartTag) and 
              token.name ==  "body"):
            if self.strict:
                raise ParseError
            if len(self.openElements)==1 or self.openElements[1].name != "body":
                assert self.innerHtml
            else:
                for attr, value in self.token.attrs.iteritems():
                    if attr not in self.openElements[1].attributes:
                        self.openElements[1].attributes[attr] = value
        elif (tokenIsType(token, tokeniser.EndTag) and 
              token.name ==  "body"):
            if self.openElements[1].name != "body":
                assert self.innerHtml
                if self.strict:
                    raise ParseError
            self.insertionMode = self.insertionModes["afterBody"]
        elif (tokenIsType(token, tokeniser.EndTag) and 
              token.name ==  "html"):
            #Lots of nasty code copying here
            if self.openElements[-1] != "body":
                assert self.innerHtml
                if self.strict:
                    raise ParseError
            else:
                nextToken = token
            self.insertionMode = self.insertionModes["afterBody"]

        elif (tokenIsType(token, tokeniser.StartTag) and 
              token.name in  ("address", "blockquote", "center", "dir", "div", 
                              "dl", "fieldset", "listing", "menu", "ol", "p", 
                              "pre", "ul")):
            if self.elementInScope("p"):
                handlePEndTag()
            self.insertElementFromToken(token)
        elif (tokenIsType(token, tokeniser.StartTag) and 
              token.name == "form"):
            if self.formPointer is not None:
                if self.strict:
                    raise ParseError
            else:
                if self.elementInScope("p"):
                    handlePEndTag()  
                self.insertElementFromToken(token)
                self.formPointer = self.openElements[-1]
        elif (tokenIsType(token, tokeniser.StartTag) and 
              token.name == in ("li", "dd", "dt")):
            if self.elementInScope("p"):
                    handlePEndTag()
            stopNames = {"li":("li"), "dd":("dd", "dt"), "dt",("dd", "dt")}
            stopName = stopNames[token.name]
            for i, node in enumerate(self.openElements[::-1]):
                if node.name in stopName:
                    for j in range(i+1):
                        self.openElements.pop()
                        break
                #Phrasing elements are all non special, non scoping, 
                #non formatting elements
                elif (node.name in (formattingElements | specialElements | 
                                    scopingElements)
                      and node.name not in formattingElements and 
                      node.name not in ("address", "div")):
                    break
            self.insertElementFromToken(token)
        elif (tokenIsType(token, tokeniser.StartTag) and 
              token.name == "plaintext"):
            if self.elementInScope("p"):
                handlePEndTag()
            self.insertElementFromToken(token)
            self.tokeniser.contentModelFlag = self.tokeniser.contentModelFlags["PLAINTEXT"]
        elif (tokenIsType(token, tokeniser.EndTag) and token.name in
              ("address", "blockquote", "centre", "div", "dl", "fieldset",
               "listing", "menu", "ol", "pre", "ul")):
            if self.elementInScope(token.name)):
                self.generateImpliedEndTags()
            if self.openElements[-1].name != token.name:
                if self.strict:
                    raise ParseError
                if self.elementInScope(token.name):
                    node = self.openElements.pop()
                    while node.name != token.name:
                        node = self.openElements.pop()
        elif tokenIsType(token, tokeniser.EndTag) and token.name == "form":

class InsertationMode(object):
    
    def __init__(self, parser):
        self.tokenDispatch = {
        tokeniser.StartTag:self.handleStartTag, 
        tokeniser.EndTag:self.handleEndTag, 
        tokeniser.CommentToken:self.handleComment,
        tokeniser.CharacterToken:self.handleCharacter
        }
        self.parser = parser
        self.tokeniser = self.parser.tokeniser

    def parseToken(token):
        self.nextToken = None
        self.tokenDispatch(type(token))
        return self.nextToken

    def handleComment(self, token):
        self.parser.openElements[-1].appendChild(CommentNode(token.data))

    def handleCharacter(self, token):
        if token.data in spaceCharacters:
            self.parser.openElements[-1].appendChild(TextNode(token.data))
        else:
            self.handleNonWhitespaceCharacter(token) 

    
class BeforeHead(InsertationMode):
    def handleNonWhilespaceCharacter(self, token):
        self.createHeadNode(token)

    def handleStartTag(self, token):
        handlers = {"base":self.createHeadNode,
        "link":self.createHeadNode,
        "meta":self.createHeadNode,
        "script":self.createHeadNode, 
        "style":self.createHeadNode,
        "title":self.createHeadNode,
        }
        handlers.get(token.name, self.startTagOther)(token)

    def handleEndTag(self, token):
        handlers = {"html":self.createHeadNode
        }
        handlers.get(token.name, self.endTagOther)(token)

    def startTagHead(self, headToken):
        self.parser.insertElementFromToken(headToken)
        self.parser.headPointer = self.openElements[-1]
        self.parser.insertionMode = self.parser.insertionModes['inHead']

    def endTagOther(self, token):
        self.parser.parseError()

    def createHeadNode(self, token):
        headToken = self.tokeniser.StartTagToken()
        headToken.name = "head"
        self.startTagHead(headToken)
        self.nextToken = token

class InHead(InsertationMode):
    def handleNonWhilespaceCharacter(self, token):
        self.parser.openElements[-1].appendChild(TextNode(token.data))

    def handleStartTag(self, token):
        handlers = {"title":self.startTagTitle,
        "style":self.startTagStyle,
        "script":self.startTagScript,
        "base":
        "link":
        "meta"
        "head":self.startTagHead


    def appendToHead(element):
        if self.headPointer is not None:
            self.parser.headPointer.appendChild(element)
        else:
            assert self.innerHTML
            self.parser.openElements[-1].append(element)
        

        elif (tokenIsType(token, tokeniser.StartTag) and token.name == "title"):
            element = self.createElementFromToken(token)
            appendToHead(element)
            self.tokeniser.state = self.tokeniser.states["RCDATA"]
            #Insert characters and get the next token
            nextToken = self.insertCharacterTokens(element)
            if (tokenIsType(token, tokeniser.EndTag) and 
                token.name == "title"):
                #Ignore a title end tag
                nextToken = None
            elif self.strict:
                raise ParseError
        elif tokenIsType(token, tokeniser.StartTag) and token.name =="style":
            element = self.createElementFromToken(token)
            appendToHead(element)
            self.tokeniser.state = self.tokeniser.states["PCDATA"]
            #Insert characters and get the next token
            nextToken = self.insertCharacterTokens(element)
            if (tokenIsType(token, tokeniser.EndTag) and 
                nextToken.name == "style"):
                #Ignore a title end tag
                nextToken = None
            elif self.strict:
                raise ParseError
        elif tokenIsType(token, tokeniser.StartTag) and token.name =="script":
            element = self.createElementFromToken(token)
            element._flags.append("parser-inserted")
            self.tokeniser.state = self.tokeniser.states["CDATA"]
            nextToken = self.insertCharacterTokens(element)
            if (tokenIsType(token, tokeniser.EndTag) and 
                nextToken.name == "script"):
                #Ignore a title end tag
                nextToken = None
            else:
                element._flags.append("already excecuted")
                if self.strict:
                    raise ParseError
            #Lots of complexity here to do with document.write; 
            #this is unimplemented
            appendToHead(element)
        elif (tokenIsType(token, tokeniser.StartTag) and 
              token.name in ["base", "link", "meta"]):
            element = self.createElementFromToken(token)
            appendToHead(element)
        elif tokenIsType(token, tokeniser.EndTag) and token.name == "head":
            if self.openElements[-1].name == "head":
                self.openElements.pop()
            elif self.strict:
                raise ParseError
            self.insertionMode = self.insertionModes["afterHead"]
        elif (tokenIsType(token, tokeniser.EndTag) and token.name != "html" or
              tokenIsType(token, tokeniser.StartTag) and token.name == "head"):
            if self.strict:
                raise ParseError
        else:
            if self.openElements[-1].name == "head":
                self.openElements.pop()
            self.insertionMode = self.insertionModes["afterHead"]
            nextToken = token
        return nextToken
