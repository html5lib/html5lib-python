import tokenizer

from utils import utils
from constants import contentModelFlags, spaceCharacters
from constants import scopingElements, formattingElements, specialElements
from constants import headingElements

"""The scope markers are inserted when entering buttons, object
elements, marquees, table cells, and table captions, and are used to
prevent formatting from "leaking" into tables, buttons, object
elements, and marquees."""
Marker = None

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
        if (isinstance(node, TextNode) and self.childNodes and
            isinstance(self.childNodes[-1], TextNode)):
            self.childNodes[-1].value += node.value
        else:
            self.childNodes.append(node)

    def cloneNode(self):
        newNode = type(self)(self.name, self.value)
        for attr, value in self.attributes.iteritems():
            newNode.attributes[attr] = value

class Document(Node):
    def __init__(self):
        Node.__init__(self, None, None)

class DocumentType(Node):
    def __init__(self, name):
        Node.__init__(self, name, None)

class TextNode(Node):
    def __init__(self, value):
        Node.__init__(self, None, value)

class Element(Node):
    def __init__(self, name):
        Node.__init__(self, name, None)

class CommentNode(Node):
    def __init__(self, data):
        Node.__init__(self, None, None, None)
        self.data = data

class HTMLParser(object):
    """Main parser class"""

    def __init__(self, strict = False):
        #Raise an exception on the first error encountered
        self.strict = strict

        self.openElements = []
        self.activeFormattingElements = []
        self.headPointer = None
        self.formPointer = None

        self.phases = {"initial":InitialPhase,
                       "rootElement":RootElementPhase,
                       "main":MainPhase,
                       "trailingEnd":TrailingEndPhase}

    def parse(self, stream, innerHTML=False):
        """Stream should be a stream of unicode bytes. Character encoding
        issues have not yet been dealt with."""

        self.document = Document()

        #We don't actually support inner HTML yet but this should allow
        #assertations
        self.innerHTML = innerHTML

        #The parsing phase we are currently in
        self.phase = InitialPhase(self)

        self.tokenizer = tokenizer.HTMLTokenizer(self)
        self.tokenizer.tokenize(stream)

        return self.document

    def processDoctype(self, name, error):
        self.phase.processDoctype(name, error)

    def processStartTag(self, name, attributes):
        self.phase.processStartTag(name, attributes)

    def processEndTag(self, name):
        self.phase.processEndTag(name)

    def processComment(self, data):
        self.phase.processComment(data)

    def processCharacter(self, data):
        self.phase.processCharacter(data)

    def processEOF(self):
        self.phase.processEOF()

    def parseError(self):
        if self.strict:
            raise ParseError

    def atheistParseError(self):
        """This error is not an error"""
        pass

    def switchInsertionMode(self, name):
        """Switch between different insertion modes in the main phase"""
        #XXX- arguably this should be on the main phase object itself
        self.phase.insertionMode = self.phase.insertionModes[name](self)

    def switchPhase(self, name):
        """Switch between different phases of the parsing
        """
        print name, self.phases["trailingEnd"]
        #Need to hang on to state between trailing end phase and main phase
        if (name == "trailingEnd" and
            isinstance(self.phase, self.phases["main"])):
            self.mainPhaseState = self.phase
            self.phase = self.phases["trailingEnd"](self)
        elif (name == "main" and
              isinstance(self.phase, self.phases["trailingEnd"])):
            self.phase = self.mainPhaseState
        else:
            self.phase = self.phases[name](self)

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

    def elementInActiveFormattingElements(self, name):
        """Check if an element eists between the end of the active
        formatting elements and the last marker. If it does, return it, else
        return false"""

        for item in self.activeFormattingElements[::-1]:
            if item.name == name:
                return item
            elif item == Marker:
                break
        return False

    def createElement(self, name, attributes):
        #Change this if we ever implement different node types for different
        #elements
        element = Element(name)
        element.attributes = attributes
        return element

    def insertElement(self, name, attributes, parent=None):
        element = self.createElement(name, dict(attributes))
        if parent is None:
            if self.openElements:
                self.openElements[-1].appendChild(element)
            self.openElements.append(element)
            print name, self.openElements
        else:
            #Haven't implemented this yet as spec is vaugely unclear
            raise NotImplementedError

    def generateImpliedEndTags(self, exclude):
        while True:
            name = self.openElements[-1].name
            if name in frozenset("dd", "dt", "li", "p", "td", "th",
                                 "tr") and name != exclude:
                self.phase.processEndTag(name)
            else:
                break

    def resetInsertionMode(self):
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
                    "body":"inBody",
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
                self.switchInsertionMode(newModes[node.name])
                break
            elif node.name == "html":
                if self.headPointer is None:
                    self.switchInsertionMode("beforeHead")
                else:
                   self.switchInsertionMode("afterHead")
                break
            elif last:
                self.switchInsertionMode("body")
                break

class Phase(object):
    """Base class for helper object that implements each phase of processing"""
    def __init__(self, parser):
        self.parser = parser

    def processDoctype(self, name, error):
        self.parser.parseError()

    def processStartTag(self, tagname, attributes):
        self.parser.parseError()

    def processEndTag(self, tagname, attributes):
        self.parser.parseError()

    def processComment(self, data):
        self.parser.parseError()

    def processCharacter(self, data):
        self.parser.parseError()

    def processEOF(self):
        self.parser.parseError()

class InitialPhase(Phase):
    # XXX We have to handle also the no doctype/whitespace case here.
    def processDoctype(self, name, error):
        self.parser.document.appendChild(DocumentType(name))
        self.parser.switchPhase("rootElement")


    def processCharacter(self, data):
        if data in spaceCharacters:
            # XXX these should be appended to the Document node as Text node.
            pass
        else:
            self.parser.parseError()

class RootElementPhase(Phase):
    def processDoctype(self, name, error):
        self.parser.parseError()

    def processCharacter(self, data):
        # XXX This doesn't put characters together in a single text node.
        if data in spaceCharacters:
            self.parser.document.appendChild(TextNode(data))
        else:
            self.createHTMLNode()
            self.parser.phase.processCharacter(data)

    def processStartTag(self, tagname, attributes):
        self.createHTMLNode()
        # XXX doesn't this invoke itself?
        self.parser.phase.processStartTag(tagname, attributes)

    def processEndTag(self, name):
        self.createHTMLNode()
        self.parser.phase.processEndTag(name)

    def processComment(self, data):
        self.parser.document.appendChild(CommentNode(data))

    def processEOF(self, data):
        self.createHTMLNode()
        self.parser.phase.processEOF()

    def createHTMLNode(self):
        self.parser.insertElement("html", [])
        #Append the html element to the root node
        self.parser.document.appendChild(self.parser.openElements[-1])
        self.parser.switchPhase("main")


class MainPhase(Phase):
    def __init__(self, parser):
        Phase.__init__(self, parser)
        self.insertionModes = {"beforeHead":BeforeHead,
                               "inHead":InHead,
                               "afterHead":AfterHead,
                               "inBody":InBody,
                               "inTable":InTable,
                               "inCaption":InCaption,
                               "inColumnGroup":InColumnGroup,
                               "inTableBody":InTableBody,
                               "inRow":InRow,
                               "inCell":InCell,
                               "inSelect":InSelect,
                               "afterBody":AfterBody,
                               "inFrameset":InFrameset,
                               "afterFrameset":AfterFrameset}
        self.insertionMode = self.insertionModes['beforeHead'](self.parser)

    def processDoctype(self, name, error):
        self.parser.parseError()

    def processEOF(self):
        self.parser.generateImpliedEndTags()
        if ((self.parser.innerHTML == False or
             len(self.parser.openElements) > 1)
            and self.parser.openElements[-1].name != "body"):
            self.parser.parseError()
        #Stop parsing

    def processStartTag(self, name, attributes):
        if name == "html":
            if self.parser.openElements:
                # XXX Is this check right? Need to be sure there has _never_
                # been a HTML tag open
                self.parser.parseError()
            for attr, value in attributes.iteritems():
                if attr not in self.parser.openElements[0].attributes:
                    selfparser.openElements[0].attributes[attr] = value
        else:
            self.insertionMode.processStartTag(name, attributes)

    def processEndTag(self, name):
        self.insertionMode.processEndTag(name)

    def processComment(self, data):
        self.insertionMode.processComment(data)

    def processCharacter(self, data):
        self.insertionMode.processCharacter(data)

class TrailingEndPhase(Phase):

    def processDoctype(self, name, error):
        self.parser.parseError()

    def processEOF(self):
        pass

    def processStartTag(self, name, attributes):
        self.parser.parseError()
        self.parser.switchPhase("main")
        self.parser.processStartTag(name, attributes)

    def processEndTag(self, name):
        self.parser.parseError()
        self.parser.switchPhase("main")
        self.parser.processEndTag(name)

    def processComment(self, data):
        self.parser.document.appendChild(CommentNode(data))

    def processCharacter(self, data):
        self.parser.switchPhase("main")
        self.parser.processCharacter(data)
        #Space characters do not actually cause us to switch phases
        if data in spaceCharacters:
            self.parser.switchPhase("trailingEnd")


class InsertionMode(object):
    def __init__(self, parser):
        self.parser = parser
        self.tokenizer = self.parser.tokenizer

        #Some attributes only used in insertion modes that
        #"collect all character data"
        self.collectingCharacters = False
        self.characterBuffer = []
        self.collectionStartTag = None

    def processComment(self, data):
        self.parser.openElements[-1].appendChild(CommentNode(data))

    def processCharacter(self, data):
        if data in spaceCharacters:
            self.parser.openElements[-1].appendChild(TextNode(data))
        else:
            self.processNonSpaceCharacter(data)

    def finishCollectingCharacters(self, name, endTag=False):
        self.parser.openElements[-1].appendChild(TextNode(
            "".join(self.characterBuffer)))
        self.characterBuffer = []
        self.collectingCharacters == False
        if not self.collectionStartTag == name or not endTag:
            self.parser.parseError()

class BeforeHead(InsertionMode):
    def processNonSpaceCharacter(self, data):
        self.createHeadNode("head", [])
        self.parser.processCharacter(data)

    def processStartTag(self, name, attributes):
        handlers = {"head":self.startTagHead}
        handlers.get(name, self.createHeadNode)(name, attributes)

    def processEndTag(self, name):
        handlers = {"html":self.createHeadNode}
        handlers.get(name, self.endTagOther)(name)

    def startTagHead(self, name, attributes):
        self.parser.insertElement(name, attributes)
        self.parser.headPointer = self.parser.openElements[-1]
        self.parser.switchInsertionMode('inHead')

    def endTagOther(self, name):
        self.parser.parseError()

    def createHeadNode(self, name, attributes):
        self.startTagHead("head", attributes)
        self.parser.headPointer = self.openElements[-1]
        self.parser.switchInsertionMode("inHead")

class InHead(InsertionMode):

    # XXX Are we sure to only recieve start and end tag tokens once we start
    # colleting characters?

    def finishCollectingCharacters(self, name, endTag=False):
        InsertionMode.finishCollectingCharacters(self,name)
        if self.parser.openElements[-1].name == "script":
            if not endTag or not name == "script":
                self.parser.openElements[-1].append("already excecuted")
            if self.parser.innerHTML:
                self.parser.openElements[-1].append("already excecuted")
        # Ignore the rest of the script element handling

    def processNonWhitespaceCharacter(self, data):
        if self.collectingCharacters:
           self.characterBuffer += data
        else:
            self.anythingElse()
            self.parser.processCharacter(data)

    def processStartTag(self, name, attributes):
        if self.collectingCharacters:
            self.finishCollectingCharacters(name)

        handlers = utils.MethodDispatcher([
                ("title",self.startTagTitleStyle),
                ("style",self.startTagTitleStyle),
                ("script",self.startTagScript),
                (("base", "link", "meta"),self.startTagBaseLinkMeta),
                ("head",self.startTagHead)])
        handlers.setDefaultValue(self.startTagOther)
        handlers[name](name, attributes)

    def processEndTag(self, name):
        if self.collectingCharacters:
            self.finishCollectingCharacters(name, True)
        handlers = {"head":self.endTagHead,
                    "html":self.endTagHTML}
        handlers.get(name, self.endTagOther)(name)

    def appendToHead(element):
        if self.headPointer is not None:
            self.parser.headPointer.appendChild(element)
        else:
            assert self.innerHTML
            self.parser.openElements[-1].append(element)

    def startTagTitleStyle(self, name, attributes):
        stateFlags = {"title":"RCDATA", "style":"CDATA"}
        element = self.parser.createElement(name, attributes)
        self.appendToHead(element)
        self.parser.tokenizer.state = self.parser.tokenizer.states[stateFlags[name]]
        # We have to start collecting characters
        self.collectingCharacters = True
        self.collectionStartTag = name

    def startTagScript(self, name, attributes):
        element = self.parser.createElement(name, attributes)
        element._flags.append("parser-inserted")
        # XXX Should this be moved to after we finish collecting characters
        self.appendToHead(element)
        self.parser.tokenizer.state = self.parser.tokenizer.states["CDATA"]

    def startTagBaseLinkMeta(self, name, attributes):
        element = self.createElement(name, attributes)
        self.appendToHead(element)

    def endTagHead(self, name):
        if self.parser.openElements[-1].name == "head":
            self.parser.openElements.pop()
        else:
            self.parser.parseError()
        self.parser.switchInsertionMode("afterHead")

    def endTagHTML(self, name):
        self.anythingElse()
        self.parser.processEndTag(name)

    def startTagOther(self, name, attributes):
        self.anythingElse()
        self.parser.processStartTag(name, attributes)

    def endTagOther(self, name):
        self.parser.parseError()

    def anythingElse(self):
        if self.parser.openElements[-1].name == "head":
            self.endTagHead("head")
        else:
            self.parser.switchInsertionMode("afterHead")

class AfterHead(InsertionMode):
    def processNonSpaceCharacter(self, data):
        self.anythingElse()
        self.parser.processCharacter(data)

    def processStartTag(self, name, attributes):
        handlers = utils.MethodDispatcher([
                ("body",self.startTagBody),
                ("frameset",self.startTagFrameset),
                (("base", "link", "meta", "script", "style", "title"),
                 self.startTagFromHead)
                ])
        handlers.setDefaultValue(self.startTagOther)

    def startTagBody(self, name, attributes):
        self.parser.insertElement(name, attributes)
        self.parser.switchInsertionMode("inBody")

    def startTagFrameset(self, name, attributes):
        self.parser.insertElement(name, attributes)
        self.parser.switchInsertionMode("inFrameset")

    def startTagFromHead(self, name, attributes):
        self.parser.parseError()
        self.parser.switchInsertionMode("inHead")
        self.parser.processStartTag(name, attributes)

    def startTagOther(self, name, attributes):
        self.anytingElse()
        self.parser.processStartTag(name, attributes)

    def processEndTag(self, name):
        self.anythingElse()
        self.parser.processEndTag(name)

    def anythingElse(self):
        self.parser.insertElement("body", [])
        self.parser.switchInsertionMode("inBody")


class InBody(InsertionMode):

    def processCharacter(self, data):
        self.parser.reconstructActiveFormattingElements()
        self.parser.openElements[-1].appendChild(TextNode(data))

    def processStartTag(self, name, attributes):
        # XXX Should this handle unknown elements as well?
        handlers=utils.MethodDispatcher([
                ("script",self.startTagScript),
                (("base", "link", "meta", "style", "title"), startTagFromHead),
                ("body", self.startTagBody),
                (("address", "blockquote", "center", "dir", "div",
                  "dl", "fieldset", "listing", "menu", "ol", "p",
                  "pre", "ul"), self.startTagCloseP),
                ("form", self.startTagForm),
                (("li", "dd", "dt"), self.startTagListItem),
                ("plaintext",self.startTagPlaintext),
                (headingElements, self.startTagHeading),
                ("a",self.startTagA),
                (("b", "big", "em", "font", "i", "nobr", "s", "small",
                  "strike", "strong", "tt", "u"),self.startTagFormatting),
                ])
        handlers[name](name, attributes)

    def processEndTag(self, name):
        # XXX Should this handle unknown elements?
        handlers = utils.MethodDispatcher([
                ("p",self.endTagP),
                ("body",self.endTagBody),
                ("html",self.endTagHtml),
                (("address", "blockquote", "centre", "div", "dl", "fieldset",
                  "listing", "menu", "ol", "pre", "ul"), self.endTagBlock),
                ("form", self.endTagForm),
                (("dd", "dt", "li"), self.endTagListItem),
                (headingElements, self.endTagHeading)
                ])
        handlers[name](name)

    def endTagP(self, name):
        self.parser.generateImpliedEndTags("p")
        if self.parser.openElements[-1].name != "p":
           self.parser.parseError()
        while self.parser.elementInScope("p"):
            self.parser.openElements.pop()

    def startTagScript(self, name, attributes):
        self.insertionModes["inHead"](self.parser).processStartTag(name,
                                                                   attributes)

    def startTagFromHead(self, name, attributes):
        self.parser.parseError()
        self.insertionModes["inHead"](self.parser).processStartTag(name,
                                                                   attributes)
    def startTagBody(self, name, attributes):
        self.parser.parseError()
        if len(self.parser.openElements)==1 or self.parser.openElements[1].name != "body":
            assert self.parser.innerHtml
        else:
            for attr, value in attributes.iteritems():
                if attr not in self.parser.openElements[1].attributes:
                    self.parser.openElements[1].attributes[attr] = value

    def endTagBody(self, name):
        if self.parser.openElements[1].name != "body":
            assert self.innerHtml
            self.parser.parseError()
        else:
            if self.parser.openElements[-1].name != "body":
                assert self.innerHtml
            self.parser.switchInsertionMode("afterBody")

    def endTagHtml(self, name, attributes):
        self.bodyEndTag(name)
        if not self.parser.innerHtml:
            self.endTagHtml(name)

    def startTagCloseP(self, name, attributes):
        if self.parser.elementInScope("p"):
            self.endTagP(name)
        self.parser.insertElement(name, attributes)

    def startTagForm(self, name, attributes):
        if self.parser.formPointer is not None:
            self.parser.parseError()
        else:
            if self.parser.elementInScope("p"):
                self.handlePEndTag("p")
            self.parser.insertElement(name, attributes)
            self.parser.formPointer = self.parser.openElements[-1]

    def startTagListItem(self, name, attributes):
        if self.parser.elementInScope("p"):
            self.handlePEndTag("p")
        stopNames = {"li":("li"), "dd":("dd", "dt"), "dt":("dd", "dt")}
        stopName = stopNames[name]
        for i, node in enumerate(self.parser.openElements[::-1]):
            if node.name in stopName:
                for j in range(i+1):
                    self.parser.openElements.pop()
                    break
            # Phrasing elements are all non special, non scoping, non
            # formatting elements
            elif (node.name in (specialElements | scopingElements)
                  and node.name not in ("address", "div")):
                break
            self.parser.insertElement(name, attributes)

    def startTagPlaintext(self, name, attributes):
        if self.parser.elementInScope("p"):
            self.endTagP("p")
        self.parser.insertElement(name, attributes)
        self.tokenizer.contentModelFlag = contentModelFlags["PLAINTEXT"]

    def endTagBlock(self, name):
        if self.parser.elementInScope(name):
            self.parser.generateImpliedEndTags()
            if self.parser.openElements[-1].name != name:
                self.parser.parseError()

        if self.parser.elementInScope(name):
            node = self.parser.openElements.pop()
            while node.name != name:
                node = self.parser.openElements.pop()

    def endTagForm(self, name):
        self.endTagBlock(name)
        self.parser.formPointer = None

    def endTagListItem(self, name):
        # AT Could merge this with the Block case
        if self.parser.elementInScope(name):
            self.parser.generateImpliedEndTags(name)
            if self.parser.openElements[-1].name != name:
                self.parser.parseError()

        if self.parser.elementInScope(name):
            node = self.parser.openElements.pop()
            while node.name != name:
                node = self.parser.openElements.pop()

    def startTagHeading(self, name, attributes):
        if self.parser.elementInScope("p"):
            self.endTagP("p")
        for item in headingElements:
            if self.parser.elementInScope(item):
                self.parser.parseError()
                item = self.parser.openElements.pop()
                while item.name not in headingElements:
                    item = self.parser.openElements.pop()
                break
        self.parser.insertElement(name, attributes)

    def endTagHeading(self, name):
        for item in headingElements:
            if self.parser.elementInScope(item):
                self.parser.generateImpliedEndTags()
                break
        if self.parser.openElements[-1].name != name:
            self.parser.parseError()

        for item in headingElements:
            if self.parser.elementInScope(item):
                item = self.parser.openElements.pop()
                while item.name not in headingElements:
                    item = self.parser.openElements.pop()
                break

    def addFormattingElement(self, name, attributes):
        self.parser.insertElement(name, attributes)
        self.parser.activeFormattingElements.append(
            self.parser.openElements[-1])

    def startTagA(self, name, attributes):
        afeAElement = self.parser.elementInActiveFormattingElements("a")
        if afeAElement:
            self.parser.parseError()
            self.endTagA("a")
            if afeAElement in self.parser.openElements:
                self.parser.openElements.remove(afeAElement)
            if afeAElement in self.parser.activeFormattingElements:
                self.parser.activeFormattingElements.remove(afeAElement)
        self.parser.reconstructActiveFormattingElements()
        self.addFormattingElement(self, name, attributes)

    def startTagFormatting(self, name, attributes):
        self.parser.reconstructActiveFormattingElements()
        self.addFormattingElement(self, name, attributes)

    def endTagFormatting(self, name):
        """The much-feared adoption agency algorithm"""
        afeElement = self.parser.elementInActiveFormattingElements(name)
        if not afeElement or (afeElement in self.parser.openElements and
                              not self.parser.elementInScope(afeElement)):
            self.parser.parseError()
            return
        elif afeElement not in self.parser.activeFormattingElements:
            self.parser.parseError()
            self.parser.activeFormattingElements.remove(afeElement)
            return

        if afeElement != self.parser.openElements[-1]:
            self.parser.parseError()

        # XXX Start of the adoption agency algorithm proper
        afeIndex = self.parser.openElements.index(afeElement)
        furthestBlock = None
        for element in self.parser.openElements[afeIndex:]:
            if element.name in (specialElements | scopingElements):
                furthestBlock = element
                break
        if furthestBlock is None:
            element = self.parser.openElements.pop()
            while element != afeElement:
                element = self.parser.openElements.pop()
            self.parser.activeFormattingElements.remove(element)
            return
        commonAncestor = self.parser.openElements[afeIndex-1]

        if furthestBlock.parent:
            furthestBlock.childNodes.remove(furthestBlock)
        # XXX Need to finish this
        raise NotImplementedError

    def startTagButton(self, name, attributes):
        if self.parser.elementInScope("button"):
            self.parser.parseError()
            self.processEndTag("button")
            self.parser.processStartTag(name, attributes)
        else:
            self.parser.reconstructActiveFormattingElements()
            self.parser.insertElement(name, attributes)
            self.parser.activeFormattingElements.append(Marker)

    def startTagMarqueeObject(self, name, attributes):
        self.parser.reconstructActiveFormattingElements()
        self.parser.insertElement(name, attributes)
        self.parser.activeFormattingElements.append(Marker)

    def endTagButtonMarqueeObject(self, name):
        if self.parser.elementInScope(name):
            self.parser.generateImpliedEndTags()
        if self.parser.openElements[-1].name != name:
            self.parser.parseError()

        if self.parser.elementInScope(name):
            element = self.parser.openElements.pop()
            while element.name != name:
                element = self.parser.openElements.pop()
            self.parser.clearActiveFormattingElements()

    def startTagXMP(self, name, attributes):
        self.parser.reconstructActiveFormattingElements()
        self.parser.insertElement(name, attributes)
        self.tokenizer.contentModelFlag = contentModelFlags["CDATA"]

    def startTagTable(self, name, attributes):
        if self.parser.elementInScope(p):
            self.processEndTag("p")
        self.parser.insertElement(name, attributes)
        self.parser.switchInsertionMode("inTable")

    def startTagVoidFormatting(self, name, attributes):
        self.parser.reconstructActiveFormattingElements()
        self.parser.insertElement(name, attributes)
        self.parser.openElements.pop()

    def startTagHR(self, name, attributes):
        self.endTagP("p")
        self.parser.insertElement(name, attributes)
        self.parser.openElements.pop()

    def startTagImage(self, name, attributes):
        # No really...
        self.parser.parseError()
        self.processStartTag("img", attributes)

    def startTagInput(self, name, attributes):
        self.parser.reconstructActiveFormattingElements()
        self.parser.insertElement(name, attributes)
        if self.parser.formPointer is not None:
            # XXX Not exactly sure what to do here
            self.parser.openElements[-1].form = self.parser.formPointer
        self.parser.openElements.pop()

    def startTagIsIndex(self, name, attributes):
        self.parser.parseError()
        if self.parser.formPointer is not None:
            return
        self.parser.processStartTag("form", [])
        self.parser.processStartTag("hr", [])
        self.parser.processStartTag("p", [])
        self.parser.processStartTag("label", [])
        self.parser.processCharacter(
            "This is a searchable index. Insert your search keywords here:")
        attributes["name"] = "isindex"
        attrs = [[key,value] for key,value in attributes.iteritems()]
        self.parser.processStartTag("input", attrs)
        self.parser.processEndTag("label")
        self.parser.processEndTag("p")
        self.parser.processStartTag("hr")
        self.parser.processEndTag("form")

class InTable(InsertionMode): pass
class InCaption(InsertionMode): pass
class InColumnGroup(InsertionMode): pass
class InTableBody(InsertionMode): pass
class InRow(InsertionMode): pass
class InCell(InsertionMode): pass
class InSelect(InsertionMode): pass

class AfterBody(InsertionMode):
    def processComment(self, data):
        self.parser.openElements[-1].appendChild(CommentNode(data))

    def processStartTag(self, name, attributes):
        self.parser.parseError()
        self.parser.switchInsertionMode("inBody")
        self.parser.processStartTag(name, attributes)

    def processEndTag(self, name):
        handlers = utils.MethodDispatcher([('html',self.endTagHtml)])
        handlers.setDefaultValue(self.endTagOther)
        handlers[name](name)

    def endTagHtml(self,name):
        if self.parser.innerHTML:
            self.parser.parseError()
        else:
            self.parser.switchPhase("trailingEnd")

    def endTagOther(self, name):
        self.parser.parseError()
        self.parser.switchInsertionMode("inBody")
        self.parser.processEndTag(name)

class InFrameset(InsertionMode): pass
class AfterFrameset(InsertionMode): pass

class ParseError(Exception):
    """Error in parsed document"""
    pass
