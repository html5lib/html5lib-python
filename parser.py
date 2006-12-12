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

    def __str__(self):
        return self.name

    def printTree(self, indent=0):
        tree = '\n|%s%s' % (' '*indent, str(self))
        for child in self.childNodes:
            tree += child.printTree(indent+2)
        return tree

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

    def __str__(self):
        return '#document'

    def printTree(self):
        tree = str(self)
        for child in self.childNodes:
            tree += child.printTree(2)
        return tree

class DocumentType(Node):
    def __init__(self, name):
        Node.__init__(self, name, None)

    def __str__(self):
        return '<!DOCTYPE %s>' % self.name

class TextNode(Node):
    def __init__(self, value):
        Node.__init__(self, None, value)

    def __str__(self):
        return '"%s"' % self.value

class Element(Node):
    def __init__(self, name):
        Node.__init__(self, name, None)

    def __str__(self):
        return '<%s>' % self.name

    def printTree(self, indent):
        tree = '\n|%s%s' % (' '*indent, str(self))
        attrs = self.attributes
        indent += 2
        for attr, value in attrs:
            tree += '\n|%s%s="%s"' % (' '*indent, attr, value)
        for child in self.childNodes:
            tree += child.printTree(indent)
        return tree

class CommentNode(Node):
    def __init__(self, data):
        Node.__init__(self, None, None)
        self.data = data

    def __str__(self):
        return '<!-- %s -->' % self.data

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

    def switchPhase(self, name):
        """Switch between different phases of the parsing
        """
        # Need to hang on to state between trailing end phase and main phase
        if (name == "trailingEnd" and
            isinstance(self.phase, self.phases["main"])):
            self.mainPhaseState = self.phase
            self.phase = self.phases["trailingEnd"](self)
        elif (name == "main" and
              isinstance(self.phase, self.phases["trailingEnd"])):
            self.phase = self.mainPhaseState
        else:
            self.phase = self.phases[name](self)

    #XXX - almost everthing after this point should be moved into a
    #seperate treebuilder object

    def switchInsertionMode(self, name):
        """Switch between different insertion modes in the main phase"""
        # XXX AT Arguably this should be on the main phase object itself
        self.phase.insertionMode = self.phase.insertionModes[name](self)

    def elementInScope(self, target, tableVariant=False):
        # AT Use reverse instead of [::-1] when we can rely on Python 2.4
        # AT How about while True and simply set node to [-1] and set it to
        # [-2] at the end...
        for node in self.openElements[::-1]:
            if node.name == target:
                return True
            elif node.name == "table":
                return False
            elif not tableVariant and node.name in scopingElements:
                return False
            elif node.name == "html":
                return False
        assert False # We should never reach this point

    def reconstructActiveFormattingElements(self):
        afe = self.activeFormattingElements
        # If there are no active formatting elements exit early
        if not afe:
            return
        entry = afe[-1]
        if entry == Marker or entry in self.openElements:
            return
        for i, entry in zip(xrange(0, len(afe)-1, -1), afe[:-1:-1]):
            if entry == Marker or entry in self.openElements:
                break
        for j in xrange(i,len(afe)-2):
            entry = afe[j+1]
            # Is this clone strictly necessary?
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
        # XXX AT Change this if we ever implement different node types for
        # different elements
        element = Element(name)
        element.attributes = attributes
        return element

    def insertElement(self, name, attributes, parent=None):
        element = self.createElement(name, attributes)
        if parent is None:
            if self.openElements:
                self.openElements[-1].appendChild(element)
            self.openElements.append(element)
        else:
            # XXX Haven't implemented this yet as spec is vaugely unclear
            raise NotImplementedError

    def generateImpliedEndTags(self, exclude=None):
        name = self.openElements[-1].name
        if name != exclude and name in frozenset(("dd", "dt", "li", "p",
                                                  "td", "th", "tr")):
            self.processEndTag(name)
            # XXX as opposed to the method proposed below, this seems to break
            # when an exclude paramter is passed...
            self.generateImpliedEndTags()

      # XXX AT:
      # name = self.openElements[-1].name
      # while name in frozenset(("dd", "dt", "li", "p", "td", "th", "tr")) and \
      #   name != exclude:
      #     self.phase.processEndTag(name)
      #     name = self.openElements[-1].name

    def resetInsertionMode(self):
        last = False
        newModes = {
            "select":"inSelect",
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
            "frameset":"inFrameset"
        }
        for node in self.openElements[::-1]:
            if node == self.openElements[0]:
                last = True
                if node.name not in ['td', 'th']:
                    # XXX
                    assert self.innerHTML
                    raise NotImplementedError
            # Check for conditions that should only happen in the innerHTML
            # case
            if node.name in ["select", "colgroup", "head", "frameset"]:
                # XXX
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

    def processEndTag(self, tagname):
        self.parser.parseError()

    def processComment(self, data):
        self.parser.parseError()

    def processCharacter(self, data):
        self.parser.parseError()

    def processEOF(self):
        self.parser.parseError()

class InitialPhase(Phase):
    def processDoctype(self, name, error):
        self.parser.document.appendChild(DocumentType(name))
        self.parser.switchPhase("rootElement")

    def processCharacter(self, data):
        if data in spaceCharacters:
            # XXX these should be appended to the Document node as Text node.
            pass
        else:
            # XXX
            self.parser.parseError()

    # This is strictly not per-spec but in the case of missing doctype we
    # choose to switch to the root element phase and reprocess the current
    # token
    def processStartTag(self, tagname, attributes):
        self.parser.switchPhase("rootElement")
        self.parser.processStartTag(tagname, attributes)

    def processEndTag(self, tagname):
        self.parser.switchPhase("rootElement")
        self.parser.processEndTag(tagname)

    def processComment(self, data):
        # XXX WRONG!
        self.parser.switchPhase("rootElement")
        self.parser.processComment(data)

    def processEOF(self):
        self.parser.switchPhase("rootElement")
        self.parser.processEOF()

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
        self.parser.phase.processStartTag(tagname, attributes)

    def processEndTag(self, name):
        self.createHTMLNode()
        self.parser.phase.processEndTag(name)

    def processComment(self, data):
        self.parser.document.appendChild(CommentNode(data))

    def processEOF(self):
        self.createHTMLNode()
        self.parser.phase.processEOF()

    def createHTMLNode(self):
        self.parser.insertElement("html", {})
        # Append the html element to the root node
        self.parser.document.appendChild(self.parser.openElements[-1])
        self.parser.switchPhase("main")


class MainPhase(Phase):
    def __init__(self, parser):
        Phase.__init__(self, parser)
        self.insertionModes = {
            "beforeHead":BeforeHead,
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
            "afterFrameset":AfterFrameset
        }
        self.insertionMode = self.insertionModes['beforeHead'](self.parser)

    def processDoctype(self, name, error):
        self.parser.parseError()

    def processEOF(self):
        self.parser.generateImpliedEndTags()
        if (self.parser.innerHTML == False \
          or len(self.parser.openElements) > 1) \
          and self.parser.openElements[-1].name != "body":
            self.parser.parseError()
        # Stop parsing
        # XXX Does stop parsing happen here or not?!

    def processStartTag(self, name, attributes):
        if name == "html":
            if self.parser.openElements:
                # XXX Is this check right? Need to be sure there has _never_
                # been a HTML tag open
                self.parser.parseError()
            for attr, value in attributes.iteritems():
                if attr not in self.parser.openElements[0].attributes:
                    self.parser.openElements[0].attributes[attr] = value
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
        # XXX Space characters do not actually cause us to switch phases
        if data in spaceCharacters:
            self.parser.switchPhase("trailingEnd")


class InsertionMode(object):
    def __init__(self, parser):
        self.parser = parser
        self.tokenizer = self.parser.tokenizer

        # Some attributes only used in insertion modes that
        # "collect all character data"
        self.collectingCharacters = False
        self.characterBuffer = []
        self.collectionStartTag = None

    # XXX we should ensure that classes don't overwrite this when they don't
    # need to.
    def processComment(self, data):
        self.parser.openElements[-1].appendChild(CommentNode(data))

    # XXX we should ensure that classes don't overwrite this when they don't
    # need to.
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
        self.startTagHead("head")
        self.parser.processCharacter(data)

    def processStartTag(self, name, attributes):
        handlers = utils.MethodDispatcher([
            ("head", self.startTagHead),
            (("base", "link", "meta", "script", "style", "title"), self.startTagOther)
        ])
        handlers.setDefaultValue(self.startTagOther)
        handlers[name](name, attributes)
    
    def startTagHead(self, name="head", attributes={}):
        self.parser.insertElement(name, attributes)
        self.parser.headPointer = self.parser.openElements[-1]
        self.parser.switchInsertionMode("inHead")

    def startTagOther(self, name, attributes):
        self.startTagHead()
        self.parser.processStartTag(name, attributes)

    def processEndTag(self, name):
        handlers = utils.MethodDispatcher([
            ("html", self.endTagHtml)
        ])
        handlers.setDefaultValue(self.endTagOther)
        handlers[name](name)

    def endTagHtml(self, name):
        self.startTagHead()
        self.parser.processEndTag(name)

    def endTagOther(self, name):
        self.parser.parseError()

class InHead(InsertionMode):

    # XXX Are we sure to only recieve start and end tag tokens once we start
    # colleting characters?

    # helper
    def finishCollectingCharacters(self, name, endTag=False):
        InsertionMode.finishCollectingCharacters(self,name)
        if self.parser.openElements[-1].name == "script":
            if not endTag or not name == "script":
                self.parser.openElements[-1].append("already excecuted")
            if self.parser.innerHTML:
                self.parser.openElements[-1].append("already excecuted")
        # Ignore the rest of the script element handling

    def appendToHead(self, element):
        if self.parser.headPointer is not None:
            self.parser.headPointer.appendChild(element)
        else:
            assert self.parser.innerHTML
            self.parser.openElements[-1].append(element)

    # the real thing
    def processNonSpaceCharacter(self, data):
        if self.collectingCharacters:
           self.characterBuffer += data
        else:
            self.anythingElse()
            self.parser.processCharacter(data)

    def processStartTag(self, name, attributes):
        if self.collectingCharacters:
            self.finishCollectingCharacters(name)

        handlers = utils.MethodDispatcher([
            ("title", self.startTagTitleStyle),
            ("style", self.startTagTitleStyle),
            ("script", self.startTagScript),
            (("base", "link", "meta"), self.startTagBaseLinkMeta),
            ("head", self.startTagHead)
        ])
        handlers.setDefaultValue(self.startTagOther)
        handlers[name](name, attributes)

    def startTagHead(self, name, attributes):
        self.parser.insertElement(name, attributes)
        self.parser.headPointer = self.parser.openElements[-1]
        self.parser.switchInsertionMode("inHead")

    def startTagTitleStyle(self, name, attributes):
        cmFlags = {"title":"RCDATA", "style":"CDATA"}
        element = self.parser.createElement(name, attributes)
        self.appendToHead(element)
        self.parser.tokenizer.contentModelFlag = contentModelFlags[cmFlags[name]]
        # We have to start collecting characters
        self.collectingCharacters = True
        self.collectionStartTag = name

    def startTagScript(self, name, attributes):
        element = self.parser.createElement(name, attributes)
        element._flags.append("parser-inserted")
        # XXX Should this be moved to after we finish collecting characters
        self.appendToHead(element)
        self.parser.tokenizer.contentModelFlag = contentModelFlags["CDATA"]

    def startTagBaseLinkMeta(self, name, attributes):
        element = self.createElement(name, attributes)
        self.appendToHead(element)

    def startTagOther(self, name, attributes):
        self.anythingElse()
        self.parser.processStartTag(name, attributes)

    def processEndTag(self, name):
        if self.collectingCharacters:
            self.finishCollectingCharacters(name, True)
        handlers = utils.MethodDispatcher([
            ("head", self.endTagHead),
            ("html", self.endTagHtml)
        ])
        handlers.setDefaultValue(self.endTagOther)
        handlers[name](name)

    def endTagHead(self, name):
        if self.parser.openElements[-1].name == "head":
            self.parser.openElements.pop()
        else:
            self.parser.parseError()
        self.parser.switchInsertionMode("afterHead")

    def endTagHtml(self, name):
        self.anythingElse()
        self.parser.processEndTag(name)

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
        handlers[name](name, attributes)

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
        self.anythingElse()
        self.parser.processStartTag(name, attributes)

    def processEndTag(self, name):
        self.anythingElse()
        self.parser.processEndTag(name)

    def anythingElse(self):
        self.parser.insertElement("body", {})
        self.parser.switchInsertionMode("inBody")


class InBody(InsertionMode):

    def processCharacter(self, data):
        self.parser.reconstructActiveFormattingElements()
        self.parser.openElements[-1].appendChild(TextNode(data))

    def processStartTag(self, name, attributes):
        # XXX Should this handle unknown elements as well?
        handlers=utils.MethodDispatcher([
            ("script",self.startTagScript),
            (("base", "link", "meta", "style", "title"), self.startTagFromHead),
            ("body", self.startTagBody),
            (("address", "blockquote", "center", "dir", "div", "dl",
              "fieldset", "listing", "menu", "ol", "p", "pre", "ul"),
              self.startTagCloseP),
            ("form", self.startTagForm),
            (("li", "dd", "dt"), self.startTagListItem),
            ("plaintext",self.startTagPlaintext),
            (headingElements, self.startTagHeading),
            ("a",self.startTagA),
            (("b", "big", "em", "font", "i", "nobr", "s", "small",
              "strike", "strong", "tt", "u"),self.startTagFormatting),
            ("button", self.startTagButton),
            (("marquee", "object"), self.startTagMarqueeObject),
            ("xmp", self.startTagXMP),
            ("table", self.startTagTable),
            (("area", "basefont", "bgsound", "br", "embed", "img",
              "param", "spacer", "wbr"), self.startTagVoidFormatting),
            ("hr", self.startTagHR),
            ("image", self.startTagImage),
            ("isindex", self.startTagIsIndex),
            ("textarea", self.startTagTextarea),
            (("iframe", "noembed", "noframes", "noscript"), self.startTagCDATA),
            ("select", self.startTagSelect),
            (("caption", "col", "colgroup", "frame", "frameset", "head",
              "option", "optgroup", "tbody", "td", "tfoot", "th", "thead",
              "tr"), self.startTagMisplaced),
            (("event-source", "section", "nav", "article", "aside", "header",
              "footer", "datagrid", "command"), self.startTagNew)
        ])
        handlers.setDefaultValue(self.startTagOther)
        handlers[name](name, attributes)

    def processEndTag(self, name):
        handlers = utils.MethodDispatcher([
            ("p",self.endTagP),
            ("body",self.endTagBody),
            ("html",self.endTagHtml),
            (("address", "blockquote", "centre", "div", "dl", "fieldset",
              "listing", "menu", "ol", "pre", "ul"), self.endTagBlock),
            ("form", self.endTagForm),
            (("dd", "dt", "li"), self.endTagListItem),
            (headingElements, self.endTagHeading),
            (("a", "b", "big", "em", "font", "i", "nobr", "s", "small",
              "strike", "strong", "tt", "u"), self.endTagFormatting),
            (("marquee", "object", "button"), self.endTagButtonMarqueeObject),
            (("caption", "col", "colgroup", "frame", "frameset", "head",
              "option", "optgroup", "tbody", "td", "tfoot", "th", "thead",
              "tr", "area", "basefont", "bgsound", "br", "embed", "hr",
              "iframe", "image", "img", "input", "isindex", "noembed",
              "noframes", "param", "select", "spacer", "table", "textarea",
              "wbr", "noscript"),self.endTagMisplacedNone),
            (("event-source", "section", "nav", "article", "aside", "header",
              "footer", "datagrid", "command"), self.endTagNew)
            ])
        handlers.setDefaultValue(self.endTagOther)
        handlers[name](name)

    def endTagP(self, name):
        self.parser.generateImpliedEndTags("p")
        if self.parser.openElements[-1].name != "p":
           self.parser.parseError()
        while self.parser.elementInScope("p"):
            self.parser.openElements.pop()

    def startTagScript(self, name, attributes):
        self.parser.phase.insertionModes["inHead"](self.parser).processStartTag(name,
                                                                   attributes)

    def startTagFromHead(self, name, attributes):
        self.parser.parseError()
        self.parser.phase.insertionModes["inHead"](self.parser).processStartTag(name,
                                                                          attributes)
    def startTagBody(self, name, attributes):
        self.parser.parseError()
        if len(self.parser.openElements)==1 or self.parser.openElements[1].name != "body":
            assert self.parser.innerHTML
        else:
            for attr, value in attributes.iteritems():
                if attr not in self.parser.openElements[1].attributes:
                    self.parser.openElements[1].attributes[attr] = value

    def endTagBody(self, name):
        if self.parser.openElements[1].name != "body":
            assert self.parser.innerHTML
            self.parser.parseError()
        else:
            if self.parser.openElements[-1].name != "body":
                assert self.parser.innerHTML
            self.parser.switchInsertionMode("afterBody")

    def endTagHtml(self, name):
        self.endTagBody(name)
        if not self.parser.innerHTML:
            self.parser.processEndTag(name)

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
        self.addFormattingElement(name, attributes)

    def startTagFormatting(self, name, attributes):
        self.parser.reconstructActiveFormattingElements()
        self.addFormattingElement(name, attributes)

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
        # XXX startTagXMP -> startTagXmp
        self.parser.reconstructActiveFormattingElements()
        self.parser.insertElement(name, attributes)
        self.tokenizer.contentModelFlag = contentModelFlags["CDATA"]

    def startTagTable(self, name, attributes):
        if self.parser.elementInScope("p"):
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

    def startTagTextarea(self, name, attributes):
        raise NotImplementedError

    def startTagCDATA(self, name, attributes):
        """iframe, noembed noframes, noscript(if scripting enabled)"""
        raise NotImplementedError

    def startTagSelect(self, name, attributes):
        self.parser.reconstructActiveFormattingElements()
        self.parser.insertElement(name, attributes)
        self.parser.switchInsertionMode("inSelect")

    def startTagMisplaced(self, name, attributes):
        """ Elements that should be children of other elements that have a
        different insertion mode; here they are ignored
        "caption", "col", "colgroup", "frame", "frameset", "head",
        "option", "optgroup", "tbody", "td", "tfoot", "th", "thead",
        "tr", "noscript"
        """
        self.parser.parseError()

    def endTagMisplacedNone(self, name):
        """ Elements that should be children of other elements that have a
        different insertion mode or elements that have no end tag;
        here they are ignored
        "caption", "col", "colgroup", "frame", "frameset", "head",
        "option", "optgroup", "tbody", "td", "tfoot", "th", "thead",
        "tr", "noscript, "area", "basefont", "bgsound", "br", "embed",
        "hr", "iframe", "image", "img", "input", "isindex", "noembed",
        "noframes", "param", "select", "spacer", "table", "textarea", "wbr""
        """
        self.parser.parseError()

    def startTagNew(self, name, other):
        """New HTML5 elements, "event-source", "section", "nav",
        "article", "aside", "header", "footer", "datagrid", "command"
        """
        raise NotImplementedError

    def endTagNew(self, name):
        """New HTML5 elements, "event-source", "section", "nav",
        "article", "aside", "header", "footer", "datagrid", "command"
        """
        raise NotImplementedError

    def startTagOther(self, name, attributes):
        self.parser.reconstructActiveFormattingElements()
        self.parser.insertElement(name, attributes)

    def endTagOther(self, name):
        # XXX This logic should be moved into the treebuilder
        # AT should use reversed instead of [::-1] when Python 2.4 == True.
        for node in self.parser.openElements[::-1]:
            if node.name == name:
                self.parser.generateImpliedEndTags()
                if self.parser.openElements[-1].name != name:
                    self.parser.parseError()
                while self.parser.openElements.pop() != node:
                    pass
                break
            else:
                if (node not in formattingElements and
                    node in specialElements | scopingElements):
                    self.parser.parseError()

class InTable(InsertionMode):
    # http://www.whatwg.org/specs/web-apps/current-work/#in-table

    # helper methods
    def clearStackToTableContext(self):
        # "clear the stack back to a table context"
        while self.parser.openElements[-1].name not in ("table", "html"):
            self.parser.openElements.pop()
            self.parser.parseError()
        # When the current node is <html> it's an innerHTML case


    # processing methods
    # processComment is handled by InsertionMode
    def processCharacter(self, data):
        if character in spaceCharacters:
            self.parser.openElements[-1].appendChild(TextNode(character))
        else:
            # XXX
            raise NotImplementedError()

    def processStartTag(self, name, attributes):
        handlers = utils.MethodDispatcher([
            ("caption", self.startTagCaption),
            ("colgroup", self.startTagColgroup),
            ("col", self.startTagCol),
            (("tbody", "tfoot", "thead"), self.startTagRowGroup),
            (("td", "th", "tr"), self.startTagImplyTbody),
            ("table", self.startTagTable)
        ])
        handlers.setDefaultValue(self.startTagOther)
        handlers[name](name, attributes)

    def startTagCaption(self, name, attributes):
        self.clearStackToTableContext()
        self.parser.activeFormattingElements.append(Marker)
        self.parser.insertElement(name, attributes)
        self.parser.switchInsertionMode("inCaption")

    def startTagColgroup(self, name="colgroup", attributes={}):
        self.clearStackToTableContext()
        self.parser.insertElement(name, attributes)
        self.parser.switchInsertionMode("inColgroup")

    def startTagCol(self, name, attributes):
        self.startTagColgroup()
        self.parser.processStartTag(name, attributes)

    def startTagRowGroup(self, name, attributes={}):
        self.clearStackToTableContext()
        self.parser.insertElement(name, attributes)
        self.parser.switchInsertionMode("inTableBody")

    def startTagImplyTbody(self, name, attributes):
        self.startTagRowGroup("tbody")
        self.parser.processStartTag(name, attributes)

    def startTagTable(self, name, attributes):
        self.parser.parseError()
        # XXX innerHTML how to check if the token wasn't ignored?
        assert False

    def startTagOther(self, name, attributes):
        # XXX
        assert False

    def processEndTag(self, name):
        handlers = utils.MethodDispatcher([
            ("table", self.endTagTable),
            (("body", "caption", "col", "colgroup", "html", "tbody", "td",
              "tfoot", "th", "thead", "tr"), self.endTagOther)
        ])
        # XXX Can we handle this through the anything else case??
        handlers.setDefaultValue(self.processAnythingElse)
        handlers[name](name)

    def endTagTable(self, name):
        if self.parser.elementInScope("table", True):
            self.generateImpliedEndTags()
            if self.parser.openElements[-1].name == "table":
                self.parser.parseError()
            while self.parser.openElements[-1].name != "table":
                self.parser.openElements.pop()
            self.parser.resetInsertionMode()
        else:
            self.parser.parseError()
            # innerHTML case

    def endTagOther(self, name):
        self.parser.parseError()

    def processAnythingElse(self, name, attributes={}):
        assert False


class InCaption(InsertionMode):
    # http://www.whatwg.org/specs/web-apps/current-work/#in-caption
    # XXX ...

    def processCharacter(data):
        self.switchInsertionMode("inBody")
        self.parser.processCharacter(data)
        # XXX switch back to this insertion mode afterwards?!

    def processStartTag(self, name, attributes):
        handlers = utils.MethodDispatcher([
            (("caption", "col", "colgroup", "tbody", "td", "tfoot", "th",
              "thead", "tr"), self.startTagTableElement)
        ])
        handlers.setDefaultValue(self.startTagOther)
        handlers[name](name, attributes)

    def startTagTableElement(self, name, attributes):
        self.parser.parseError()
        self.parser.processEndTag("caption")
        # XXX innerHTML case ... token ignored and such
        assert False

    def startTagOther(self, name, attributes):
        # Parse error is thrown later on.
        self.parser.switchInsertionMode("inBody")
        self.parser.processStartTag(name, attributes)

    def processEndTag(self, name):
        handlers = utils.MethodDispatcher([
            ("caption", self.endTagCaption),
            ("table", self.endTagTable),
            (("body", "col", "colgroup", "html", "tbody", "td", "tfoot", "th",
              "thead", "tr"), self.endTagIgnore)
        ])
        handlers.setDefaultValue(self.endTagOther)
        handlers[name](name)

    def endTagCaption(self, name):
        if self.parser.elementInScope(name, True):
            # XXX this code is quite similar to endTagTable in "InTable"
            self.generateImpliedEndTags()
            if self.parser.openElements[-1].name == "caption":
                self.parser.parseError()
            while self.parser.openElements[-1].name != "caption":
                self.parser.openElements.pop()
            self.parser.clearActiveFormattingElements()
            self.parser.switchInsertionMode("inTable")
        else:
            # innerHTML case
            self.parser.parseError()

    def endTagTable(self, name):
        self.parser.parseError()
        self.parser.processEndTag("caption")
        # XXX check if the token wasn't ignored... innerHTML case
        assert False

    def endTagIgnore(self, name):
        self.parser.parseError()

    def endTagOther(self, name):
        self.parser.switchInsertionMode("inBody")
        self.parser.processEndTag(name)


class InColumnGroup(InsertionMode):
    # http://www.whatwg.org/specs/web-apps/current-work/#in-column

    def processStartTag(self, name, attributes):
        handlers = utils.MethodDispatcher([
            ("col", self.startTagCol)
        ])
        # XXX Can we handle this through the anything else case??
        handlers.setDefaultValue(self.startTagOther)
        handlers[name](name, attributes)

    def startTagCol(self, name ,attributes):
        self.parser.insertElement(name, attributes)
        self.parser.openElements.pop()

    def startTagOther(self, name, attributes):
        # XXX
        assert False

    def processEndTag(self, name):
        handlers = utils.MethodDispatcher([
            ("colgroup", self.endTagColgroup),
            ("col", self.endTagCol)
        ])
        # XXX Can we handle this through the anything else case??
        handlers.setDefaultValue(self.endTagOther)
        handlers[name](name)

    def endTagColGroup(self, name):
        if self.parser.openElements[-1].name == "html":
            # innerHTML case
            self.parser.parseError()
        else:
            self.parser.openElements.pop()
            self.parser.switchInsertionMode("inTable")

    def endTagCol(self, name):
        self.parser.parseError()

    def endTagOther(self, name):
        # XXX
        assert False


class InTableBody(InsertionMode):
    # http://www.whatwg.org/specs/web-apps/current-work/#in-table0

    # helper methods
    def clearStackToTableBodyContext(self):
        while self.parser.openElements[-1].name in ("tbody", "tfoot", "thead",
          "html"):
            self.parser.openElements.pop()
            self.parser.parseError()

    # the rest
    # XXX character tokens and all that ...

    def processStartTag(self, name, attributes):
        handlers = utils.MethodDispatcher([
            ("tr", self.startTagTr),
            (("td", "th"), self.startTagTableCell),
            (("caption", "col", "colgroup", "tbody", "tfoot", "thead"), self.startTagTableOther)
        ])
        handlers.setDefaultValue(self.startTagOther)
        handlers[name](name, attributes)

    def startTagTr(self, name="tr", attributes={}):
        self.clearStackToTableBodyContext()
        self.parser.insertElement(name, attributes)
        self.parser.switchInsertionMode("inRow")

    def startTagTableCell(self, name, attributes):
        self.parser.parseError()
        self.startTagTr()
        self.parser.processStartTag(name, attributes)

    def startTagTableOther(self, name, attributes):
        # XXX AT Any ideas on how to share this with endTagTable?
        if self.elementInScope("tbody", True) or \
          self.elementInScope("thead", True) or \
          self.elementInScope("tfoot", True):
            self.clearStackToTableBodyContext()
            self.endTagTableRowGroup(self.parser.openElements[-1])
        else:
            # innerHTML case
            self.parser.parseError()

    def startTagOther(self, name, attributes):
        self.parser.switchInsertionMode("inTable")
        self.parser.processStartTag(name, attributes)

    def processEndTag(self, name):
        handlers = utils.MethodDispatcher([
            (("tbody", "tfoot", "thead"), self.endTagTableRowGroup),
            ("table", self.endTagTable),
            (("body", "caption", "col", "colgroup", "html", "td", "th",
              "tr"), self.endTagIgnore)
        ])
        handlers.setDefaultValue(self.endTagOther)
        handlers[name](name)

    def endTagTableRowGroup(self, name):
        if self.parser.elementInScope(name, True):
            self.clearStackToTableBodyContext()
            self.parser.openElements.pop()
            self.parser.switchInsertionMode("inTable")
        else:
            self.parser.parseError()

    def endTagTable(self, name):
        # XXX AT Any ideas on how to share this with startTagTableOther?
        if self.elementInScope("tbody", True) or \
          self.elementInScope("thead", True) or \
          self.elementInScope("tfoot", True):
            self.clearStackToTableBodyContext()
            self.endTagTableRowGroup(self.parser.openElements[-1])
        else:
            # innerHTML case
            self.parser.parseError()

    def endTagIgnore(self, name):
        self.parser.parseError()

    def endTagOther(self, name):
        self.parser.switchInsertionMode("inTable")
        self.parser.processEndTag(name)


class InRow(InsertionMode):
    # http://www.whatwg.org/specs/web-apps/current-work/#in-row

    # helper methods (XXX unify this with other table helper methods)
    def clearStackToTableRowContext(self):
        while self.parser.openElements[-1].name in ("tr", "html"):
            self.parser.openElements.pop()
            self.parser.parseError()

    # the rest
    def processStartTag(self, name, attributes):
        handlers = utils.MethodDispatcher([
            (("td", "th"), self.startTagTableCell),
            (("caption", "col", "colgroup", "tbody", "tfoot", "thead",
              "tr"), self.startTagTableOther)
        ])
        handlers.setDefaultValue(self.startTagOther)
        handlers[name](name, attributes)

    def startTagTableCell(self, name, attributes):
        self.clearStackToTableRowContext()
        self.parser.insertElement(name, attributes)
        self.parser.switchInsertionMode("inCell")
        self.parser.activeFormattingElements.append(Marker)

    def startTagTableOther(self, name, attributes):
        self.endTagTr()
        # XXX check if it wasn't ignored... innerHTML case ... reprocess
        # current. see also endTagTable

    def startTagOther(self, name, attributes):
        self.parser.switchInsertionMode("inTable")
        self.parser.processStartTag(name, attributes)

    def processEndTag(self, name):
        handlers = utils.MethodDispatcher([
            ("tr", self.endTagTr),
            ("table", self.endTagTable),
            (("tbody", "tfoot", "thead"), self.endTagTableRowGroup),
            (("body", "caption", "col", "colgroup", "html", "td", "th"), \
              self.endTagIgnore)
        ])
        handlers.setDefaultValue(self.endTagOther)
        handlers[name](name)

    def endTagTr(self, name="tr"):
        if self.parser.elementInScope("tr", True):
            self.clearStackToTableRowContext()
            self.parser.openElements.pop()
            self.parser.switchInsertionMode("inTableBody")
        else:
            # innerHTML case
            self.parser.parseError()

    def endTagTable(self, name):
        self.endTagTr()
        # XXX check if it wasn't ignored... innerHTML case ... reprocess
        # current. see also startTagTableOther...

    def endTagTableRowGroup(self, name):
        if self.parser.elementInScope(name, True):
            self.endTagTr()
            self.parser.processEndTag(name)
        else:
            # innerHTML case
            self.parser.parseError()

    def endTagIgnore(self, name):
        self.parser.parseError()

    def endTagOther(self, name):
        self.parser.switchInsertionMode("inTable")
        self.parser.processEndTag(name)

class InCell(InsertionMode):
    # http://www.whatwg.org/specs/web-apps/current-work/#in-cell

    # helper
    def closeCell(self, type="td"):
        if self.parser.elementInScope(type, True):
            self.endTagTableCell(type)
            return
        self.closeCell("th")
        # AT We could use elif...

    # the rest
    # XXX look into characters and comments

    def processStartTag(self, name, attributes):
        handlers = utils.MethodDispatcher([
            (("caption", "col", "colgroup", "tbody", "td", "tfoot", "th",
              "thead", "tr"), self.startTagTableOther)
        ])
        handlers.setDefaultValue(self.startTagOther)
        handlers[name](name, attributes)

    def startTagTableOther(self, name, attributes):
        if self.parser.elementInScope("td") or \
          self.parser.elementInScope("th"):
            self.closeCell()
            self.parser.processStartTag(name, attributes)
        else:
            # innerHTML case
            self.parser.parseError()

    def startTagOther(self, name, attributes):
        self.parser.switchInsertionMode("inBody")
        self.parser.processStartTag(name, attributes)

    def processEndTag(self, name):
        handlers = utils.MethodDispatcher([
            (("td", "th"), self.endTagTableCell),
            (("body", "caption", "col", "colgroup", "html"), self.endTagIgnore),
            (("table", "tbody", "tfoot", "thead", "tr"), self.endTagImply)
        ])
        handlers.setDefaultValue(self.endTagOther)
        handlers[name](name)

    def endTagTableCell(self, name):
        if self.parser.elementInScope(name):
            self.parser.generateImpliedEndTags()
            node = self.parser.openElements[-1].name
            if node != name:
                self.parser.parseError()
                node = self.parser.openElements.pop()
                while node.name != name:
                    node = self.parser.openElements.pop()
            self.parser.clearActiveFormattingElements()
            self.parser.switchInsertionMode("inRow")
        else:
            self.parser.parseError()

    def endTagIgnore(self, name):
        self.parser.parseError()

    def endTagImply(self, name):
        if self.parser.elementInScope(name):
            self.closeCell()
            self.parser.processEndTag(name)
        else:
            # sometimes innerHTML case
            self.parser.parseError()

    def endTagOther(self, name):
        self.parser.switchInsertionMode("inBody")
        self.parser.processEndTag(name)


class InSelect(InsertionMode):
    # http://www.whatwg.org/specs/web-apps/current-work/#in-select

    # No need for processComment.
    # XXX character token ... always appended to the current node

    def processStartTag(self, name, attributes):
        handlers = utils.MethodDispatcher([
            ("option", self.startTagOption),
            ("optgroup", self.startTagOptgroup),
            ("select", self.startTagSelect)
        ])
        handlers.setDefaultValue(self.processAnythingElse)
        handlers[name](name, attributes)

    def startTagOption(self, name, attributes):
        # We need to imply </option> if <option> is the current node.
        if self.parser.openElements[-1].name == "option":
            # AT We could also pop the node from the stack...
            self.endTagOption()
        self.parser.insertElement(name, attributes)

    def startTagOptgroup(self, name, attributes):
        if self.parser.openElements[-1].name == "option":
            # AT see above
            self.endTagOption()
        if self.parser.openElements[-1].name == "optgroup":
            self.endTagOptgroup()
        self.parser.insertElement(name, attributes)

    def startTagSelect(self, name, attributes):
        self.parser.parseError()
        self.endTagSelect()

    def processEndTag(self, name):
        handlers = utils.MethodDispatcher([
            ("option", self.endTagOption),
            ("optgroup", self.endTagOptgroup)
            ("select", self.endTagSelect),
            (("caption", "table", "tbody", "tfoot", "thead", "tr", "td",
              "th"), self.endTagTableElements)
        ])
        handlers.setDefaultValue(self.processAnythingElse)
        handlers[name](name)

    def endTagOption(self, name="option"):
        if self.parser.openElements[-1].name == "option":
            self.parser.openElements.pop()
        else:
            self.parser.parseError()

    def endTagOptgroup(self, name="optgroup"):
        # </optgroup> implicitly closes <option>
        if self.parser.openElements[-1].name == "option" and \
          self.parser.openElements[-2].name == "optgroup":
            self.endTagOption()
        # It also closes </optgroup>
        if self.parser.openElements[-1].name == "optgroup":
            self.parser.openElements.pop()
        # But nothing else
        else:
            self.parser.parseError()

    def endTagSelect(self, name="select"):
        if self.parser.elementInScope(name, True):
            if self.parser.openElements[-1].name != "select":
                node = self.parser.openElements.pop()
                while node.name != "select":
                    node = self.parser.openElements.pop()
            self.parser.resetInsertionMode()
        else:
            # innerHTML case
            self.parser.parseError()

    def endTagTableElements(self, name):
        self.parser.parseError()
        if self.parser.elementInScope(name, True):
            self.endTagSelect()
            self.parser.processEndTag(name)

    def processAnythingElse(self, name, attributes={}):
        self.parser.parseError()


class AfterBody(InsertionMode):
    # No need for processComment

    def processStartTag(self, name, attributes):
        self.parser.parseError()
        self.parser.switchInsertionMode("inBody")
        self.parser.processStartTag(name, attributes)

    def processEndTag(self, name):
        handlers = utils.MethodDispatcher([("html", self.endTagHtml)])
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

class InFrameset(InsertionMode):
    # http://www.whatwg.org/specs/web-apps/current-work/#in-frameset

    # XXX
    # No need for processComment or processCharacter.
    # XXX we do need processNonSpaceCharacter ...

    def processStartTag(self, name, attributes):
        handlers = utils.MethodDispatcher([
            ("frameset", self.startTagFrameset),
            ("frame", self.startTagFrame),
            ("noframes", self.startTagNoframes)
        ])
        handlers.setDefaultValue(self.tagOther)
        handlers[name](name, attributes)

    def startTagFrameset(self, name, attributes):
        self.parser.insertElement(name, attributes)

    def startTagFrame(self, name, attributes):
        self.parser.insertElement(name, attributes)
        self.parser.openElements.pop()

    def startTagNoframes(self, name, attributes):
        self.parser.switchInsertionMode("inBody")
        self.parser.processStartTag(name, attributes)

    def processEndTag(self, name):
        handlers = utils.MethodDispatcher([("frameset", self.endTagFrameset)])
        handlers.setDefaultValue(self.tagOther)
        handlers[name](name)

    def endTagFrameset(self, name):
        if self.parser.openElements[-1].name == "html":
            # innerHTML case
            self.parser.parseError()
        else:
            self.parser.openElements.pop()
        if not self.parser.innerHTML and \
          self.parser.openElements[-1].name == "frameset":
            self.parser.switchInsertionMode("afterFrameset")

    def tagOther(self, name, attributes={}):
        self.parser.parseError()


class AfterFrameset(InsertionMode):
    # http://www.whatwg.org/specs/web-apps/current-work/#after3
    # XXX

    # No need for processComment or processCharacter.
    # XXX we do need processNonSpaceCharacter ...

    def processStartTag(self, name, attributes):
        handlers = utils.MethodDispatcher([("noframes", self.startTagNoframes)])
        handlers.setDefaultValue(self.tagOther)
        handlers[name](name, attributes)

    def startTagNoframes(self, name, attributes):
        self.parser.switchInsertionMode("inBody")
        self.processStartTag(self, name, attributes)

    def processEndTag(self, name):
        handlers = utils.MethodDispatcher([("html", self.endTagHtml)])
        handlers.setDefaultValue(self.tagOther)
        handlers[name](name)

    def endTagHtml(self, name):
        self.parser.switchPhase("trailingEnd")

    def tagOther(self, name, attributes={}):
        self.parser.parseError()


class ParseError(Exception):
    """Error in parsed document"""
    pass
