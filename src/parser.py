try:
    frozenset
except NameError:
    #Import from the sets module for python 2.3
    from sets import Set as set
    from sets import ImmutableSet as frozenset

import tokenizer

import utils
from constants import contentModelFlags, spaceCharacters
from constants import scopingElements, formattingElements, specialElements
from constants import headingElements, tableInsertModeElements

# The scope markers are inserted when entering buttons, object elements,
# marquees, table cells, and table captions, and are used to prevent formatting
# from "leaking" into tables, buttons, object elements, and marquees.
Marker = None

# Really crappy basic implementation of a DOM-core like thing
class Node(object):
    def __init__(self, name):
        self.name = name
        self.parent = None
        self.value = None
        self.childNodes = []
        self.attributes = {}
        self._flags = []

    def __str__(self):
        return self.name

    def __repr__(self):
        return "<%s %s>" % (self.__class__, self.name)

    def printTree(self, indent=0):
        tree = '\n|%s%s' % (' '* indent, str(self))
        for child in self.childNodes:
            tree += child.printTree(indent + 2)
        return tree

    def appendChild(self, node, index=None):
        if (isinstance(node, TextNode) and self.childNodes and
          isinstance(self.childNodes[-1], TextNode)):
            self.childNodes[-1].value += node.value
        else:
            self.childNodes.append(node)
        node.parent = self

    def insertBefore(self, node, refNode):
        index = self.childNodes.index(refNode)
        if (isinstance(node, TextNode) and index > 0 and
          isinstance(self.childNodes[index - 1], TextNode)):
            self.childNodes[index - 1].value += node.value
        else:
            self.childNodes.insert(index, node)
        node.parent = self

    def removeChild(self, node):
        try:
            self.childNodes.remove(node)
        except:
            # XXX
            raise
        node.parent = None

    def cloneNode(self):
        newNode = type(self)(self.name)
        for attr, value in self.attributes.iteritems():
            newNode.attributes[attr] = value
        newNode.value = self.value
        return newNode

class Document(Node):
    def __init__(self):
        Node.__init__(self, None)

    def __str__(self):
        return "#document"

    def printTree(self):
        tree = str(self)
        for child in self.childNodes:
            tree += child.printTree(2)
        return tree

class DocumentType(Node):
    def __init__(self, name):
        Node.__init__(self, name)

    def __str__(self):
        return "<!DOCTYPE %s>" % self.name

class TextNode(Node):
    def __init__(self, value):
        Node.__init__(self, None)
        self.value = value

    def __str__(self):
        return "\"%s\"" % self.value

class Element(Node):
    def __init__(self, name):
        Node.__init__(self, name)

    def __str__(self):
        return "<%s>" % self.name

    def printTree(self, indent):
        tree = '\n|%s%s' % (' '*indent, str(self))
        indent += 2
        if self.attributes:
            for name, value in self.attributes.iteritems():
                tree += '\n|%s%s="%s"' % (' ' * indent, name, value)
        for child in self.childNodes:
            tree += child.printTree(indent)
        return tree

class CommentNode(Node):
    def __init__(self, data):
        Node.__init__(self, None)
        self.data = data

    def __str__(self):
        return "<!-- %s -->" % self.data

class HTMLParser(object):
    """Main parser class"""

    def __init__(self, strict = False):
        # Raise an exception on the first error encountered
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

        #Flag indicationg special insertion mode from elements misnested inside
        #a table
        self.insertFromTable = False

        self.tokenizer = tokenizer.HTMLTokenizer(stream)

        # XXX This is temporary for the moment so there isn't any other
        # changes needed for the parser to work with the iterable tokenizer
        for token in self.tokenizer:
            tokenClass = token.__class__.__name__
            method = getattr(self.phase, 'process%s' % tokenClass, None)
            if tokenClass in ('Characters', 'Comment'):
                method(token.data)
            elif tokenClass in ('Doctype', 'StartTag'):
                method(token.name, token.data)
            elif tokenClass == 'EndTag':
                method(token.name)
            elif tokenClass == 'ParseError':
                self.parseError()
            else:
                self.atheistParseError()

        # When the loop finishes it's EOF
        self.processEOF()

        return self.document

    def processDoctype(self, name, error):
        self.phase.processDoctype(name, error)

    def processStartTag(self, name, attributes):
        self.phase.processStartTag(name, attributes)

    def processEndTag(self, name):
        self.phase.processEndTag(name)

    def processComment(self, data):
        self.phase.processComment(data)

    def processCharacters(self, data):
        self.phase.processCharacters(data)

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
        self.phase.mode = self.phase.modes[name](self)

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
        # Within this algorithm the order of steps described in the
        # specification is not quite the same as the order of steps in the
        # code. It should still do the same though.

        # Step 1: stop the algorithm when there's nothing to do.
        if not self.activeFormattingElements:
            return

        # Step 2 and step 3: we start with the last element. So i is -1.
        i = -1
        entry = self.activeFormattingElements[i]
        if entry == Marker or entry in self.openElements:
            return

        # Step 6
        while entry != Marker and entry not in self.openElements:
            # Step 5: let entry be one earlier in the list.
            i -= 1
            try:
                entry = self.activeFormattingElements[i]
            except:
                # Step 4: at this point we need to jump to step 8. By not doing
                # i += 1 which is also done in step 7 we achieve that.
                break
        while True:
            # Step 7
            i += 1

            # Step 8
            clone = self.activeFormattingElements[i].cloneNode()

            # Step 9
            element = self.insertElement(clone.name, clone.attributes)

            # Step 10
            self.activeFormattingElements[i] = element

            # Step 11
            if element == self.activeFormattingElements[-1]:
                break

    def clearActiveFormattingElements(self):
        entry = self.activeFormattingElements.pop()
        while self.activeFormattingElements and entry != Marker:
            entry = self.activeFormattingElements.pop()

    def elementInActiveFormattingElements(self, name):
        """Check if an element exists between the end of the active
        formatting elements and the last marker. If it does, return it, else
        return false"""

        for item in self.activeFormattingElements[::-1]:
            # Check for Marker first because if it's a Marker it doesn't have a
            # name attribute.
            if item == Marker:
                break
            elif item.name == name:
                return item
        return False

    def createElement(self, name, attributes):
        # XXX AT Change this if we ever implement different node types for
        # different elements
        element = Element(name)
        element.attributes = attributes
        return element

    def insertElement(self, name, attributes):
        element = self.createElement(name, attributes)
        if (not(self.insertFromTable) or (self.insertFromTable and
          self.openElements[-1].name not in tableInsertModeElements)):
            self.openElements[-1].appendChild(element)
            self.openElements.append(element)
        else:
            #We should be in the InTable mode. This means we want to do
            #special magic element rearranging
            self.insertMisnestedNodeFromTable(element)
            self.openElements.append(element)
        return element

    def insertText(self, data, parent=None):
        node = TextNode(data)
        if parent is None:
            parent = self.openElements[-1]
        if (not(self.insertFromTable) or (self.insertFromTable and
                                          self.openElements[-1].name not in
                                          tableInsertModeElements)):
            parent.appendChild(node)
        else:
            #We should be in the InTable mode. This means we want to do
            #special magic element rearranging
            self.insertMisnestedNodeFromTable(node)

    def insertMisnestedNodeFromTable(self, element):
        #The foster parent element is the one which comes before the most
        #recently opened table element
        #XXX - this is really inelegant
        lastTable=None
        for elm in self.openElements[::-1]:
            if elm.name == u"table":
                lastTable = elm
                break
        if lastTable:
            #XXX - we should really check that this parent is actually a
            #node here
            if lastTable.parent:
                fosterParent = lastTable.parent
                fosterParent.insertBefore(element, lastTable)
            else:
                fosterParent = self.openElements[
                    self.openElements.index(lastTable) - 1]
                fosterParent.appendChild(element)
        else:
            assert self.innerHTML
            fosterParent = self.openElements[0]
            fosterParent.appendChild(element)

    def generateImpliedEndTags(self, exclude=None):
        name = self.openElements[-1].name
        if (name in frozenset(("dd", "dt", "li", "p", "td", "th", "tr"))
          and name != exclude):
            self.processEndTag(name)
            self.generateImpliedEndTags(exclude)

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
            if node.name in ("select", "colgroup", "head", "frameset"):
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

    def processStartTag(self, name, attributes):
        self.parser.parseError()

    def processEndTag(self, name):
        self.parser.parseError()

    def processComment(self, data):
        self.parser.document.appendChild(CommentNode(data))

    def processCharacters(self, data):
        # XXX This method is never invoked...
        self.parser.parseError()

    def processEOF(self):
        self.parser.parseError()

class InitialPhase(Phase):
    # XXX This phase deals with error handling as well which is currently not
    # in the specification.

    def processDoctype(self, name, error):
        self.parser.document.appendChild(DocumentType(name))
        self.parser.switchPhase("rootElement")

    def processCharacters(self, data):
        if data in spaceCharacters:
            # This check works because space characters (when needed) are
            # emitted as a single character.
            self.parser.insertText(data, self.parser.document)
        else:
            self.parser.parseError()
            self.parser.switchPhase("rootElement")
            self.parser.phase.processCharacters(data)

    def processStartTag(self, name, attributes):
        self.parser.switchPhase("rootElement")
        self.parser.phase.processStartTag(name, attributes)

    def processEndTag(self, name):
        self.parser.switchPhase("rootElement")
        self.parser.phase.processEndTag(name)

    def processEOF(self):
        self.parser.switchPhase("rootElement")
        self.parser.phase.processEOF()

class RootElementPhase(Phase):
    # helper methods
    def insertHtmlElement(self):
        element = self.parser.createElement("html", {})
        self.parser.openElements.append(element)
        self.parser.document.appendChild(element)
        self.parser.switchPhase("main")

    # other
    def processCharacters(self, data):
        if data in spaceCharacters:
            # This check works because space characters (when needed) are
            # emitted as a single character.
            self.parser.insertText(data, self.parser.document)
        else:
            self.insertHtmlElement()
            self.parser.phase.processCharacters(data)

    def processStartTag(self, name, attributes):
        self.insertHtmlElement()
        self.parser.phase.processStartTag(name, attributes)

    def processEndTag(self, name):
        self.insertHtmlElement()
        self.parser.phase.processEndTag(name)

    def processEOF(self):
        self.insertHtmlElement()
        self.parser.phase.processEOF()

class MainPhase(Phase):
    def __init__(self, parser):
        Phase.__init__(self, parser)
        self.modes = {
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
        self.mode = self.modes["beforeHead"](self.parser)

    def processEOF(self):
        self.mode.processEOF()

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
            self.mode.processStartTag(name, attributes)

    def processEndTag(self, name):
        self.mode.processEndTag(name)

    def processComment(self, data):
        self.mode.processComment(data)

    def processCharacters(self, data):
        self.mode.processCharacters(data)

class TrailingEndPhase(Phase):
    def processEOF(self):
        pass

    def processStartTag(self, name, attributes):
        self.parser.parseError()
        self.parser.switchPhase("main")
        self.parser.phase.processStartTag(name, attributes)

    def processEndTag(self, name):
        self.parser.parseError()
        self.parser.switchPhase("main")
        self.parser.phase.processEndTag(name)

    def processCharacters(self, data):
        if data not in spaceCharacters:
            # This check works because space characters (when needed) are
            # emitted as a single character. Same below.
            self.parser.parseError()
        self.parser.switchPhase("main")
        self.parser.phase.processCharacters(data)
        # If it's a space character we want to stay in this phase.
        if data in spaceCharacters:
            self.parser.switchPhase("trailingEnd")


class InsertionMode(object):
    def __init__(self, parser):
        self.parser = parser

    def processEOF(self):
        self.parser.generateImpliedEndTags()
        if (self.parser.innerHTML == False \
          or len(self.parser.openElements) > 1) \
          and self.parser.openElements[-1].name != "body":
            self.parser.parseError()
        # Stop parsing

    def processComment(self, data):
        self.parser.openElements[-1].appendChild(CommentNode(data))

    def processCharacters(self, data):
        if data in spaceCharacters:
            # This check works because space characters (when needed) are
            # emitted as a single character.
            self.parser.insertText(data)
        else:
            self.processNonSpaceCharacters(data)

class BeforeHead(InsertionMode):
    def processEOF(self):
        self.startTagHead()
        self.parser.processEOF()

    def processNonSpaceCharacters(self, data):
        self.startTagHead()
        self.parser.processCharacters(data)

    def processStartTag(self, name, attributes):
        handlers = utils.MethodDispatcher([
            ("head", self.startTagHead),
            (("base", "link", "meta", "script", "style", "title"),
              self.startTagOther)
        ])
        handlers.default = self.startTagOther
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
        handlers.default = self.endTagOther
        handlers[name](name)

    def endTagHtml(self, name):
        self.startTagHead()
        self.parser.processEndTag(name)

    def endTagOther(self, name):
        self.parser.parseError()

class InHead(InsertionMode):
    # helper
    def appendToHead(self, element):
        if self.parser.headPointer is not None:
            self.parser.headPointer.appendChild(element)
        else:
            assert self.parser.innerHTML
            self.parser.openElements[-1].appendChild(element)

    # the real thing
    def processEOF(self):
        if self.parser.openElements[-1].name in ("title", "style", "script"):
            self.parser.openElements.pop()
        self.anythingElse()
        self.parser.processEOF()

    def processNonSpaceCharacters(self, data):
        if self.parser.openElements[-1].name in ("title", "style", "script"):
            self.parser.insertText(data)
        else:
            self.anythingElse()
            self.parser.processCharacters(data)

    def processStartTag(self, name, attributes):
        handlers = utils.MethodDispatcher([
            (("title", "style"), self.startTagTitleStyle),
            ("script", self.startTagScript),
            (("base", "link", "meta"), self.startTagBaseLinkMeta),
            ("head", self.startTagHead)
        ])
        handlers.default = self.startTagOther
        handlers[name](name, attributes)

    def startTagHead(self, name, attributes):
        self.parser.insertElement(name, attributes)
        self.parser.headPointer = self.parser.openElements[-1]
        self.parser.switchInsertionMode("inHead")

    def startTagTitleStyle(self, name, attributes):
        cmFlags = {"title":"RCDATA", "style":"CDATA"}
        element = self.parser.createElement(name, attributes)
        self.appendToHead(element)
        self.parser.openElements.append(element)
        self.parser.tokenizer.contentModelFlag =\
          contentModelFlags[cmFlags[name]]

    def startTagScript(self, name, attributes):
        element = self.parser.createElement(name, attributes)
        element._flags.append("parser-inserted")

        # XXX in theory we should check if we're actually in the InHead state
        # here and if the headElementPointer is not zero but it seems to work
        # without that being the case.
        self.parser.openElements[-1].appendChild(element)
        self.parser.openElements.append(element)

        # XXX AT we could use self.parser.insertElement(name, attributes) ...
        self.parser.tokenizer.contentModelFlag = contentModelFlags["CDATA"]

    def startTagBaseLinkMeta(self, name, attributes):
        element = self.parser.createElement(name, attributes)
        self.appendToHead(element)

    def startTagOther(self, name, attributes):
        self.anythingElse()
        self.parser.processStartTag(name, attributes)

    def processEndTag(self, name):
        handlers = utils.MethodDispatcher([
            ("head", self.endTagHead),
            ("html", self.endTagHtml),
            (("title", "style", "script"), self.endTagTitleStyleScript)
        ])
        handlers.default = self.endTagOther
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

    def endTagTitleStyleScript(self, name):
        if self.parser.openElements[-1].name == name:
            self.parser.openElements.pop()
        else:
            self.parser.parseError()

    def endTagOther(self, name):
        self.parser.parseError()

    def anythingElse(self):
        if self.parser.openElements[-1].name == "head":
            self.endTagHead("head")
        else:
            self.parser.switchInsertionMode("afterHead")

class AfterHead(InsertionMode):
    def processEOF(self):
        self.anythingElse()
        self.parser.processEOF()

    def processNonSpaceCharacters(self, data):
        self.anythingElse()
        self.parser.processCharacters(data)

    def processStartTag(self, name, attributes):
        handlers = utils.MethodDispatcher([
            ("body",self.startTagBody),
            ("frameset",self.startTagFrameset),
            (("base", "link", "meta", "script", "style", "title"),
              self.startTagFromHead)
        ])
        handlers.default = self.startTagOther
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
    # http://www.whatwg.org/specs/web-apps/current-work/#in-body
    # the crazy mode
    def __init__(self, parser):
        InsertionMode.__init__(self, parser)
        self.processStartTagHandler = utils.MethodDispatcher([
            ("script", self.startTagScript),
            (("base", "link", "meta", "style", "title"),
              self.startTagFromHead),
            ("body", self.startTagBody),
            (("address", "blockquote", "center", "dir", "div", "dl",
              "fieldset", "listing", "menu", "ol", "p", "pre", "ul"),
              self.startTagCloseP),
            ("form", self.startTagForm),
            (("li", "dd", "dt"), self.startTagListItem),
            ("plaintext",self.startTagPlaintext),
            (headingElements, self.startTagHeading),
            ("a", self.startTagA),
            (("b", "big", "em", "font", "i", "nobr", "s", "small", "strike",
              "strong", "tt", "u"),self.startTagFormatting),
            ("button", self.startTagButton),
            (("marquee", "object"), self.startTagMarqueeObject),
            ("xmp", self.startTagXmp),
            ("table", self.startTagTable),
            (("area", "basefont", "bgsound", "br", "embed", "img", "param",
              "spacer", "wbr"), self.startTagVoidFormatting),
            ("hr", self.startTagHr),
            ("image", self.startTagImage),
            ("input", self.startTagInput),
            ("isindex", self.startTagIsIndex),
            ("textarea", self.startTagTextarea),
            (("iframe", "noembed", "noframes", "noscript"), self.startTagCdata),
            ("select", self.startTagSelect),
            (("caption", "col", "colgroup", "frame", "frameset", "head",
              "option", "optgroup", "tbody", "td", "tfoot", "th", "thead",
              "tr"), self.startTagMisplaced),
            (("event-source", "section", "nav", "article", "aside", "header",
              "footer", "datagrid", "command"), self.startTagNew)
        ])
        self.processStartTagHandler.default = self.startTagOther

        self.processEndTagHandler = utils.MethodDispatcher([
            ("p",self.endTagP),
            ("body",self.endTagBody),
            ("html",self.endTagHtml),
            (("address", "blockquote", "center", "div", "dl", "fieldset",
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
              "image", "img", "input", "isindex", "param", "select", "spacer",
              "table",  "wbr"),self.endTagMisplacedNone),
            (("noframes", "noscript", "noembed", "textarea", "xmp", "iframe"),
              self.endTagCdataTextAreaXmp),
            (("event-source", "section", "nav", "article", "aside", "header",
              "footer", "datagrid", "command"), self.endTagNew)
            ])
        self.processEndTagHandler.default = self.endTagOther

    # helper
    def addFormattingElement(self, name, attributes):
        self.parser.insertElement(name, attributes)
        self.parser.activeFormattingElements.append(
            self.parser.openElements[-1])

    # the real deal
    def processNonSpaceCharacters(self, data):
        # XXX The specification says to do this for every character at the
        # moment, but apparently that doesn't match the real world...
        self.parser.reconstructActiveFormattingElements()
        self.parser.insertText(data)

    def processStartTag(self, name, attributes):
        self.processStartTagHandler[name](name, attributes)

    def startTagScript(self, name, attributes):
        self.parser.phase.modes["inHead"](self.parser).processStartTag(name,
          attributes)

    def startTagFromHead(self, name, attributes):
        self.parser.parseError()
        self.parser.phase.modes["inHead"](self.parser).processStartTag(name,
          attributes)

    def startTagBody(self, name, attributes):
        self.parser.parseError()
        if len(self.parser.openElements) == 1 \
          or self.parser.openElements[1].name != "body":
            assert self.parser.innerHTML
        else:
            for attr, value in attributes.iteritems():
                if attr not in self.parser.openElements[1].attributes:
                    self.parser.openElements[1].attributes[attr] = value

    def startTagCloseP(self, name, attributes):
        if self.parser.elementInScope("p"):
            self.endTagP("p")
        self.parser.insertElement(name, attributes)

    def startTagForm(self, name, attributes):
        if self.parser.formPointer:
            self.parser.parseError()
        else:
            if self.parser.elementInScope("p"):
                self.endTagP("p")
            self.parser.insertElement(name, attributes)
            self.parser.formPointer = self.parser.openElements[-1]

    def startTagListItem(self, name, attributes):
        if self.parser.elementInScope("p"):
            self.endTagP("p")
        stopNames = {"li":("li"), "dd":("dd", "dt"), "dt":("dd", "dt")}
        stopName = stopNames[name]
        # AT Use reversed in Python 2.4...
        for i, node in enumerate(self.parser.openElements[::-1]):
            if node.name in stopName:
                for j in range(i+1):
                    self.parser.openElements.pop()
                break

            # Phrasing elements are all non special, non scoping, non
            # formatting elements
            if (node.name in (specialElements | scopingElements)
              and node.name not in ("address", "div")):
                break
        # Always insert an <li> element.
        self.parser.insertElement(name, attributes)

    def startTagPlaintext(self, name, attributes):
        if self.parser.elementInScope("p"):
            self.endTagP("p")
        self.parser.insertElement(name, attributes)
        self.parser.tokenizer.contentModelFlag = contentModelFlags["PLAINTEXT"]

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

    def startTagA(self, name, attributes):
        afeAElement = self.parser.elementInActiveFormattingElements("a")
        if afeAElement:
            self.parser.parseError()
            self.endTagFormatting("a")
            if afeAElement in self.parser.openElements:
                self.parser.openElements.remove(afeAElement)
            if afeAElement in self.parser.activeFormattingElements:
                self.parser.activeFormattingElements.remove(afeAElement)
        self.parser.reconstructActiveFormattingElements()
        self.addFormattingElement(name, attributes)

    def startTagFormatting(self, name, attributes):
        self.parser.reconstructActiveFormattingElements()
        self.addFormattingElement(name, attributes)

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

    def startTagXmp(self, name, attributes):
        self.parser.reconstructActiveFormattingElements()
        self.parser.insertElement(name, attributes)
        self.parser.tokenizer.contentModelFlag = contentModelFlags["CDATA"]

    def startTagTable(self, name, attributes):
        if self.parser.elementInScope("p"):
            self.processEndTag("p")
        self.parser.insertElement(name, attributes)
        self.parser.switchInsertionMode("inTable")

    def startTagVoidFormatting(self, name, attributes):
        self.parser.reconstructActiveFormattingElements()
        self.parser.insertElement(name, attributes)
        self.parser.openElements.pop()

    def startTagHr(self, name, attributes):
        if self.parser.elementInScope("p"):
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
        if self.parser.formPointer:
            # XXX Not exactly sure what to do here
            self.parser.openElements[-1].form = self.parser.formPointer
        self.parser.openElements.pop()

    def startTagIsIndex(self, name, attributes):
        self.parser.parseError()
        if self.parser.formPointer:
            return
        self.processStartTag("form", {})
        self.processStartTag("hr", {})
        self.processStartTag("p", {})
        self.processStartTag("label", {})
        # XXX Localization ...
        self.processCharacters(
            "This is a searchable index. Insert your search keywords here:")
        attributes["name"] = "isindex"
        attrs = [[key,value] for key,value in attributes.iteritems()]
        self.processStartTag("input", dict(attrs))
        self.processEndTag("label")
        self.processEndTag("p")
        self.processStartTag("hr", {})
        self.processEndTag("form")

    def startTagTextarea(self, name, attributes):
        # XXX Form element pointer checking here as well...
        self.parser.insertElement(name, attributes)
        self.parser.tokenizer.contentModelFlag = contentModelFlags["RCDATA"]

    def startTagCdata(self, name, attributes):
        """iframe, noembed noframes, noscript(if scripting enabled)"""
        self.parser.insertElement(name, attributes)
        self.parser.tokenizer.contentModelFlag = contentModelFlags["CDATA"]

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

    def startTagNew(self, name, other):
        """New HTML5 elements, "event-source", "section", "nav",
        "article", "aside", "header", "footer", "datagrid", "command"
        """
        raise NotImplementedError

    def startTagOther(self, name, attributes):
        self.parser.reconstructActiveFormattingElements()
        self.parser.insertElement(name, attributes)


    def processEndTag(self, name):
        self.processEndTagHandler[name](name)

    def endTagP(self, name):
        self.parser.generateImpliedEndTags("p")
        if self.parser.openElements[-1].name != "p":
            self.parser.parseError()
        while self.parser.elementInScope("p"):
            self.parser.openElements.pop()

    def endTagBody(self, name):
        if self.parser.openElements[1].name != "body":
            # innerHTML case
            self.parser.parseError()
            return
        if self.parser.openElements[-1].name != "body":
            self.parser.parseError()
        self.parser.switchInsertionMode("afterBody")

    def endTagHtml(self, name):
        self.endTagBody(name)
        if not self.parser.innerHTML:
            self.parser.processEndTag(name)

    def endTagBlock(self, name):
        inScope = self.parser.elementInScope(name)
        if inScope:
            self.parser.generateImpliedEndTags()
        if self.parser.openElements[-1].name != name:
             self.parser.parseError()
        if inScope:
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

    def endTagFormatting(self, name):
        """The much-feared adoption agency algorithm
        """
        while True:
            # Step 1 paragraph 1
            afeElement = self.parser.elementInActiveFormattingElements(name)
            if not afeElement or (afeElement in self.parser.openElements and
              not self.parser.elementInScope(afeElement.name)):
                self.parser.parseError()
                return

            # Step 1 paragraph 2
            elif afeElement not in self.parser.openElements:
                self.parser.parseError()
                self.parser.activeFormattingElements.remove(afeElement)
                return

            # Step 1 paragraph 3
            if afeElement != self.parser.openElements[-1]:
                self.parser.parseError()

            # Step 2
            # Start of the adoption agency algorithm proper
            afeIndex = self.parser.openElements.index(afeElement)
            furthestBlock = None
            for element in self.parser.openElements[afeIndex:]:
                if element.name in specialElements | scopingElements:
                    furthestBlock = element
                    break

            # Step 3
            if furthestBlock is None:
                element = self.parser.openElements.pop()
                while element != afeElement:
                    element = self.parser.openElements.pop()
                self.parser.activeFormattingElements.remove(element)
                return
            commonAncestor = self.parser.openElements[afeIndex-1]

            # Step 5
            if furthestBlock.parent:
                furthestBlock.parent.removeChild(furthestBlock)

            # Step 6
            # The bookmark is supposed to help us identify where to reinsert
            # nodes in step 12. We have to ensure that we reinsert nodes after
            # the node before the active formatting element. Note the bookmark
            # can move in step 7.4
            bookmark = self.parser.activeFormattingElements.index(afeElement)

            # Step 7
            lastNode = node = furthestBlock
            while True:
                # AT replace this with a function and recursion?
                # Node is element before node in open elements
                node = self.parser.openElements[
                    self.parser.openElements.index(node)-1]
                while node not in self.parser.activeFormattingElements:
                    tmpNode = node
                    node = self.parser.openElements[
                        self.parser.openElements.index(node)-1]
                    self.parser.openElements.remove(tmpNode)
                # Step 7.3
                if node == afeElement:
                    break
                # Step 7.4
                if lastNode == furthestBlock:
                    # XXX should this be index(node) or index(node)+1
                    # Anne: I think +1 is ok. Given x = [2,3,4,5]
                    # x.index(3) gives 1 and then x[1 +1] gives 4...
                    bookmark = self.parser.activeFormattingElements.\
                      index(node) + 1
                # Step 7.5
                if node.childNodes:
                    clone = node.cloneNode()
                    # Replace node with clone
                    self.parser.activeFormattingElements[
                      self.parser.activeFormattingElements.index(node)] = clone
                    self.parser.openElements[
                      self.parser.openElements.index(node)] = clone
                    node = clone
                # Step 7.6
                # Remove lastNode from its parents, if any
                if lastNode.parent:
                    lastNode.parent.removeChild(lastNode)
                node.appendChild(lastNode)
                # Step 7.7
                lastNode = node
                # End of inner loop

            # Step 8
            if lastNode.parent:
                lastNode.parent.removeChild(lastNode)
            commonAncestor.appendChild(lastNode)

            # Step 9
            clone = afeElement.cloneNode()

            # Step 10
            clone.childNodes.extend(furthestBlock.childNodes)
            furthestBlock.childNodes = []

            # Step 11
            furthestBlock.childNodes.append(clone)

            # Step 12
            self.parser.activeFormattingElements.remove(afeElement)
            self.parser.activeFormattingElements.insert(bookmark, clone)

            # Step 13
            self.parser.openElements.remove(afeElement)
            self.parser.openElements.insert(
              self.parser.openElements.index(furthestBlock) + 1, clone)

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

    def endTagCdataTextAreaXmp(self, name):
        if self.parser.openElements[-1].name == name:
            self.parser.openElements.pop()
        else:
            self.parser.parseError()

    def endTagNew(self, name):
        """New HTML5 elements, "event-source", "section", "nav",
        "article", "aside", "header", "footer", "datagrid", "command"
        """
        raise NotImplementedError

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
                if node.name in specialElements | scopingElements:
                    self.parser.parseError()
                    break

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
    def processNonSpaceCharacters(self, data):
        self.parser.parseError()
        # Make all the special element rearranging voodoo kick in
        self.parser.insertFromTable = True
        # Process the character in the "in body" mode
        InBody(self.parser).processCharacters(data)
        self.parser.insertFromTable = False

    def processStartTag(self, name, attributes):
        handlers = utils.MethodDispatcher([
            ("caption", self.startTagCaption),
            ("colgroup", self.startTagColgroup),
            ("col", self.startTagCol),
            (("tbody", "tfoot", "thead"), self.startTagRowGroup),
            (("td", "th", "tr"), self.startTagImplyTbody),
            ("table", self.startTagTable)
        ])
        handlers.default = self.startTagOther
        handlers[name](name, attributes)

    def startTagCaption(self, name, attributes):
        self.clearStackToTableContext()
        self.parser.activeFormattingElements.append(Marker)
        self.parser.insertElement(name, attributes)
        self.parser.switchInsertionMode("inCaption")

    def startTagColgroup(self, name="colgroup", attributes={}):
        self.clearStackToTableContext()
        self.parser.insertElement(name, attributes)
        self.parser.switchInsertionMode("inColumnGroup")

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
        self.parser.processEndTag("table")
        if not self.parser.innerHTML:
            self.parser.processStartTag(name, attributes)

    def startTagOther(self, name, attributes):
        self.parser.parseError()
        # Make all the special element rearranging voodoo kick in
        self.parser.insertFromTable = True
        # Process the start tag in the "in body" mode
        InBody(self.parser).processStartTag(name, attributes)
        self.parser.insertFromTable = False

    def processEndTag(self, name):
        handlers = utils.MethodDispatcher([
            ("table", self.endTagTable),
            (("body", "caption", "col", "colgroup", "html", "tbody", "td",
              "tfoot", "th", "thead", "tr"), self.endTagIgnore)
        ])
        handlers.default = self.endTagOther
        handlers[name](name)

    def endTagTable(self, name):
        if self.parser.elementInScope("table", True):
            self.parser.generateImpliedEndTags()
            if self.parser.openElements[-1].name == "table":
                self.parser.parseError()
            while self.parser.openElements[-1].name != "table":
                self.parser.openElements.pop()
            self.parser.openElements.pop()
            self.parser.resetInsertionMode()
        else:
            self.parser.parseError()
            # innerHTML case

    def endTagIgnore(self, name):
        self.parser.parseError()

    def endTagOther(self, name, attributes={}):
        # Make all the special element rearranging voodoo kick in
        self.parser.insertFromTable = True
        # Process the end tag in the "in body" mode
        InBody(self.parser).processEndTag(name)
        self.parser.insertFromTable = False


class InCaption(InsertionMode):
    # http://www.whatwg.org/specs/web-apps/current-work/#in-caption
    # XXX ...

    def processCharacters(self, data):
        InBody(self.parser).processCharacters(data)

    def processStartTag(self, name, attributes):
        handlers = utils.MethodDispatcher([
            (("caption", "col", "colgroup", "tbody", "td", "tfoot", "th",
              "thead", "tr"), self.startTagTableElement)
        ])
        handlers.default = self.startTagOther
        handlers[name](name, attributes)

    def startTagTableElement(self, name, attributes):
        self.parser.parseError()
        self.parser.processEndTag("caption")
        # XXX how do we know the tag is _always_ ignored in the innerHTML
        # case and therefore shouldn't be processed again? I'm not sure this
        # strategy makes sense...
        if not self.parser.innerHTML:
            self.parser.processStartTag(name, attributes)

    def startTagOther(self, name, attributes):
        InBody(self.parser).processStartTag(name, attributes)

    def processEndTag(self, name):
        handlers = utils.MethodDispatcher([
            ("caption", self.endTagCaption),
            ("table", self.endTagTable),
            (("body", "col", "colgroup", "html", "tbody", "td", "tfoot", "th",
              "thead", "tr"), self.endTagIgnore)
        ])
        handlers.default = self.endTagOther
        handlers[name](name)

    def endTagCaption(self, name):
        if self.parser.elementInScope(name, True):
            # AT this code is quite similar to endTagTable in "InTable"
            self.parser.generateImpliedEndTags()
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
        # XXX ...
        if not self.parser.innerHTML:
            self.parser.processStartTag(name, attributes)

    def endTagIgnore(self, name):
        self.parser.parseError()

    def endTagOther(self, name):
        InBody(self.parser).processEndTag(name)


class InColumnGroup(InsertionMode):
    # http://www.whatwg.org/specs/web-apps/current-work/#in-column

    def processNonSpaceCharacters(self, data):
        self.endTagColgroup()
        # XXX
        if not self.parser.innerHTML:
            self.parser.processCharacters(data)

    def processStartTag(self, name, attributes):
        handlers = utils.MethodDispatcher([
            ("col", self.startTagCol)
        ])
        handlers.default = self.startTagOther
        handlers[name](name, attributes)

    def startTagCol(self, name ,attributes):
        self.parser.insertElement(name, attributes)
        self.parser.openElements.pop()

    def startTagOther(self, name, attributes):
        self.endTagColgroup()
        # XXX how can be sure it's always ignored?
        if not self.parser.innerHTML:
            self.parser.processStartTag(name, attributes)

    def processEndTag(self, name):
        handlers = utils.MethodDispatcher([
            ("colgroup", self.endTagColgroup),
            ("col", self.endTagCol)
        ])
        handlers.default = self.endTagOther
        handlers[name](name)

    def endTagColgroup(self, name="colgroup"):
        if self.parser.openElements[-1].name == "html":
            # innerHTML case
            self.parser.parseError()
        else:
            self.parser.openElements.pop()
            self.parser.switchInsertionMode("inTable")

    def endTagCol(self, name):
        self.parser.parseError()

    def endTagOther(self, name):
        self.endTagColgroup()
        # XXX how can be sure it's always ignored?
        if not self.parser.innerHTML:
            self.parser.processEndTag(name)


class InTableBody(InsertionMode):
    # http://www.whatwg.org/specs/web-apps/current-work/#in-table0

    # helper methods
    def clearStackToTableBodyContext(self):
        while self.parser.openElements[-1].name not in ("tbody", "tfoot",
          "thead", "html"):
            self.parser.openElements.pop()
            self.parser.parseError()

    # the rest
    def processCharacters(self,data):
        InTable(self.parser).processCharacters(data)

    def processStartTag(self, name, attributes):
        handlers = utils.MethodDispatcher([
            ("tr", self.startTagTr),
            (("td", "th"), self.startTagTableCell),
            (("caption", "col", "colgroup", "tbody", "tfoot", "thead"), self.startTagTableOther)
        ])
        handlers.default = self.startTagOther
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
        if self.parser.elementInScope("tbody", True) or \
          self.parser.elementInScope("thead", True) or \
          self.parser.elementInScope("tfoot", True):
            self.clearStackToTableBodyContext()
            self.endTagTableRowGroup(self.parser.openElements[-1].name)
            self.parser.processStartTag(name, attributes)
        else:
            # innerHTML case
            self.parser.parseError()

    def startTagOther(self, name, attributes):
        InTable(self.parser).processStartTag(name, attributes)

    def processEndTag(self, name):
        handlers = utils.MethodDispatcher([
            (("tbody", "tfoot", "thead"), self.endTagTableRowGroup),
            ("table", self.endTagTable),
            (("body", "caption", "col", "colgroup", "html", "td", "th",
              "tr"), self.endTagIgnore)
        ])
        handlers.default = self.endTagOther
        handlers[name](name)

    def endTagTableRowGroup(self, name):
        if self.parser.elementInScope(name, True):
            self.clearStackToTableBodyContext()
            self.parser.openElements.pop()
            self.parser.switchInsertionMode("inTable")
        else:
            self.parser.parseError()

    def endTagTable(self, name):
        if self.parser.elementInScope("tbody", True) or \
          self.parser.elementInScope("thead", True) or \
          self.parser.elementInScope("tfoot", True):
            self.clearStackToTableBodyContext()
            self.endTagTableRowGroup(self.parser.openElements[-1].name)
            self.parser.processEndTag(name)
        else:
            # innerHTML case
            self.parser.parseError()

    def endTagIgnore(self, name):
        self.parser.parseError()

    def endTagOther(self, name):
        InTable(self.parser).processEndTag(name)


class InRow(InsertionMode):
    # http://www.whatwg.org/specs/web-apps/current-work/#in-row

    # helper methods (XXX unify this with other table helper methods)
    def clearStackToTableRowContext(self):
        while self.parser.openElements[-1].name not in ("tr", "html"):
            self.parser.openElements.pop()
            self.parser.parseError()

    # the rest
    def processCharacters(self, data):
        InTable(self.parser).processNonSpaceCharacters(data)

    def processStartTag(self, name, attributes):
        handlers = utils.MethodDispatcher([
            (("td", "th"), self.startTagTableCell),
            (("caption", "col", "colgroup", "tbody", "tfoot", "thead",
              "tr"), self.startTagTableOther)
        ])
        handlers.default = self.startTagOther
        handlers[name](name, attributes)

    def startTagTableCell(self, name, attributes):
        self.clearStackToTableRowContext()
        self.parser.insertElement(name, attributes)
        self.parser.switchInsertionMode("inCell")
        self.parser.activeFormattingElements.append(Marker)

    def startTagTableOther(self, name, attributes):
        self.endTagTr()
        # XXX how are we sure it's always ignored in the innerHTML case?
        if not self.parser.innerHTML:
            self.parser.processStartTag(name, attributes)

    def startTagOther(self, name, attributes):
        InTable(self.parser).processStartTag(name, attributes)

    def processEndTag(self, name):
        handlers = utils.MethodDispatcher([
            ("tr", self.endTagTr),
            ("table", self.endTagTable),
            (("tbody", "tfoot", "thead"), self.endTagTableRowGroup),
            (("body", "caption", "col", "colgroup", "html", "td", "th"),
              self.endTagIgnore)
        ])
        handlers.default = self.endTagOther
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
        self.endTagTr("tr")
        # Reprocess the current tag if the tr end tag was not ignored
        # XXX how are we sure it's always ignored in the innerHTML case?
        if not self.parser.innerHTML:
            self.parser.processEndTag(name)

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
        InTable(self.parser).processEndTag(name)

class InCell(InsertionMode):
    # http://www.whatwg.org/specs/web-apps/current-work/#in-cell

    # helper
    def closeCell(self):
        if self.parser.elementInScope("td", True):
            self.endTagTableCell("td")
        elif self.parser.elementInScope("th", True):
            self.endTagTableCell("th")

    # the rest
    def processCharacters(self, data):
        InBody(self.parser).processCharacters(data)

    def processStartTag(self, name, attributes):
        handlers = utils.MethodDispatcher([
            (("caption", "col", "colgroup", "tbody", "td", "tfoot", "th",
              "thead", "tr"), self.startTagTableOther)
        ])
        handlers.default = self.startTagOther
        handlers[name](name, attributes)

    def startTagTableOther(self, name, attributes):
        if self.parser.elementInScope("td", True) or \
          self.parser.elementInScope("th", True):
            self.closeCell()
            self.parser.processStartTag(name, attributes)
        else:
            # innerHTML case
            self.parser.parseError()

    def startTagOther(self, name, attributes):
        InBody(self.parser).processStartTag(name, attributes)

    def processEndTag(self, name):
        handlers = utils.MethodDispatcher([
            (("td", "th"), self.endTagTableCell),
            (("body", "caption", "col", "colgroup", "html"), self.endTagIgnore),
            (("table", "tbody", "tfoot", "thead", "tr"), self.endTagImply)
        ])
        handlers.default = self.endTagOther
        handlers[name](name)

    def endTagTableCell(self, name):
        if self.parser.elementInScope(name, True):
            self.parser.generateImpliedEndTags(name)
            if self.parser.openElements[-1].name != name:
                self.parser.parseError()
                while True:
                    node = self.parser.openElements.pop()
                    if node.name == name:
                        break
            else:
                self.parser.openElements.pop()
            self.parser.clearActiveFormattingElements()
            self.parser.switchInsertionMode("inRow")
        else:
            self.parser.parseError()

    def endTagIgnore(self, name):
        self.parser.parseError()

    def endTagImply(self, name):
        if self.parser.elementInScope(name, True):
            self.closeCell()
            self.parser.processEndTag(name)
        else:
            # sometimes innerHTML case
            self.parser.parseError()

    def endTagOther(self, name):
        InBody(self.parser).processEndTag(name)


class InSelect(InsertionMode):
    # http://www.whatwg.org/specs/web-apps/current-work/#in-select
    def processCharacters(self, data):
        self.parser.insertText(data)

    def processStartTag(self, name, attributes):
        handlers = utils.MethodDispatcher([
            ("option", self.startTagOption),
            ("optgroup", self.startTagOptgroup),
            ("select", self.startTagSelect)
        ])
        handlers.default = self.processAnythingElse
        handlers[name](name, attributes)

    def startTagOption(self, name, attributes):
        # We need to imply </option> if <option> is the current node.
        if self.parser.openElements[-1].name == "option":
            self.parser.openElements.pop()
        self.parser.insertElement(name, attributes)

    def startTagOptgroup(self, name, attributes):
        if self.parser.openElements[-1].name == "option":
            self.parser.openElements.pop()
        if self.parser.openElements[-1].name == "optgroup":
            self.parser.openElements.pop()
        self.parser.insertElement(name, attributes)

    def startTagSelect(self, name, attributes):
        self.parser.parseError()
        self.endTagSelect("select")

    def processEndTag(self, name):
        handlers = utils.MethodDispatcher([
            ("option", self.endTagOption),
            ("optgroup", self.endTagOptgroup),
            ("select", self.endTagSelect),
            (("caption", "table", "tbody", "tfoot", "thead", "tr", "td",
              "th"), self.endTagTableElements)
        ])
        handlers.default = self.processAnythingElse
        handlers[name](name)

    def endTagOption(self, name):
        if self.parser.openElements[-1].name == "option":
            self.parser.openElements.pop()
        else:
            self.parser.parseError()

    def endTagOptgroup(self, name):
        # </optgroup> implicitly closes <option>
        if self.parser.openElements[-1].name == "option" and \
          self.parser.openElements[-2].name == "optgroup":
            self.parser.openElements.pop()
        # It also closes </optgroup>
        if self.parser.openElements[-1].name == "optgroup":
            self.parser.openElements.pop()
        # But nothing else
        else:
            self.parser.parseError()

    def endTagSelect(self, name):
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
    def processComment(self, data):
        # This is needed because data is to be appended to the <html> element
        # here and not to whatever is currently open.
        self.parser.openElements[0].appendChild(CommentNode(data))

    def processNonSpaceCharacters(self, data):
        self.parser.parseError()
        self.parser.switchInsertionMode("inBody")
        self.parser.processCharacters(data)

    def processStartTag(self, name, attributes):
        self.parser.parseError()
        self.parser.switchInsertionMode("inBody")
        self.parser.processStartTag(name, attributes)

    def processEndTag(self, name):
        handlers = utils.MethodDispatcher([("html", self.endTagHtml)])
        handlers.default = self.endTagOther
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

    def processNonSpaceCharacters(self, data):
        self.parser.parseError()

    def processStartTag(self, name, attributes):
        handlers = utils.MethodDispatcher([
            ("frameset", self.startTagFrameset),
            ("frame", self.startTagFrame),
            ("noframes", self.startTagNoframes)
        ])
        handlers.default = self.tagOther
        handlers[name](name, attributes)

    def startTagFrameset(self, name, attributes):
        self.parser.insertElement(name, attributes)

    def startTagFrame(self, name, attributes):
        self.parser.insertElement(name, attributes)
        self.parser.openElements.pop()

    def startTagNoframes(self, name, attributes):
        InBody(self.parser).processStartTag(name, attributes)

    def processEndTag(self, name):
        handlers = utils.MethodDispatcher([("frameset", self.endTagFrameset)])
        handlers.default = self.tagOther
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
    def processNonSpaceCharacters(self, data):
        self.parser.parseError()

    def processStartTag(self, name, attributes):
        handlers = utils.MethodDispatcher([("noframes", self.startTagNoframes)])
        handlers.default = self.tagOther
        handlers[name](name, attributes)

    def startTagNoframes(self, name, attributes):
        InBody(self.parser).processStartTag(name, attributes)

    def processEndTag(self, name):
        handlers = utils.MethodDispatcher([("html", self.endTagHtml)])
        handlers.default = self.tagOther
        handlers[name](name)

    def endTagHtml(self, name):
        self.parser.switchPhase("trailingEnd")

    def tagOther(self, name, attributes={}):
        self.parser.parseError()


class ParseError(Exception):
    """Error in parsed document"""
    pass
