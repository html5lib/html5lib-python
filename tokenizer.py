
import string

contentModelFlags = {
    "PCDATA":0,
    "RCDATA":1,
    "CDATA":2,
    "PLAINTEXT":3
}

spaceCharacters = (
    u"\t",
    u"\n",
    u"\u000B",
    u"\u000C",
    u" "
)

entities = {
    "AElig": u"\u00C6",
    "Aacute": u"\u00C1",
    "Acirc": u"\u00C2",
    "Agrave": u"\u00C0",
    "Alpha": u"\u0391",
    "Aring": u"\u00C5",
    "Atilde": u"\u00C3",
    "Auml": u"\u00C4",
    "Beta": u"\u0392",
    "Ccedil": u"\u00C7",
    "Chi": u"\u03A7",
    "Dagger": u"\u2021",
    "Delta": u"\u0394",
    "ETH": u"\u00D0",
    "Eacute": u"\u00C9",
    "Ecirc": u"\u00CA",
    "Egrave": u"\u00C8",
    "Epsilon": u"\u0395",
    "Eta": u"\u0397",
    "Euml": u"\u00CB",
    "Gamma": u"\u0393",
    "Iacute": u"\u00CD",
    "Icirc": u"\u00CE",
    "Igrave": u"\u00CC",
    "Iota": u"\u0399",
    "Iuml": u"\u00CF",
    "Kappa": u"\u039A",
    "Lambda": u"\u039B",
    "Mu": u"\u039C",
    "Ntilde": u"\u00D1",
    "Nu": u"\u039D",
    "OElig": u"\u0152",
    "Oacute": u"\u00D3",
    "Ocirc": u"\u00D4",
    "Ograve": u"\u00D2",
    "Omega": u"\u03A9",
    "Omicron": u"\u039F",
    "Oslash": u"\u00D8",
    "Otilde": u"\u00D5",
    "Ouml": u"\u00D6",
    "Phi": u"\u03A6",
    "Pi": u"\u03A0",
    "Prime": u"\u2033",
    "Psi": u"\u03A8",
    "Rho": u"\u03A1",
    "Scaron": u"\u0160",
    "Sigma": u"\u03A3",
    "THORN": u"\u00DE",
    "Tau": u"\u03A4",
    "Theta": u"\u0398",
    "Uacute": u"\u00DA",
    "Ucirc": u"\u00DB",
    "Ugrave": u"\u00D9",
    "Upsilon": u"\u03A5",
    "Uuml": u"\u00DC",
    "Xi": u"\u039E",
    "Yacute": u"\u00DD",
    "Yuml": u"\u0178",
    "Zeta": u"\u0396",
    "aacute": u"\u00E1",
    "acirc": u"\u00E2",
    "acute": u"\u00B4",
    "aelig": u"\u00E6",
    "agrave": u"\u00E0",
    "alefsym": u"\u2135",
    "alpha": u"\u03B1",
    "amp": u"\u0026",
    "AMP": u"\u0026",
    "and": u"\u2227",
    "ang": u"\u2220",
    "apos": u"\u0027",
    "aring": u"\u00E5",
    "asymp": u"\u2248",
    "atilde": u"\u00E3",
    "auml": u"\u00E4",
    "bdquo": u"\u201E",
    "beta": u"\u03B2",
    "brvbar": u"\u00A6",
    "bull": u"\u2022",
    "cap": u"\u2229",
    "ccedil": u"\u00E7",
    "cedil": u"\u00B8",
    "cent": u"\u00A2",
    "chi": u"\u03C7",
    "circ": u"\u02C6",
    "clubs": u"\u2663",
    "cong": u"\u2245",
    "copy": u"\u00A9",
    "COPY": u"\u00A9",
    "crarr": u"\u21B5",
    "cup": u"\u222A",
    "curren": u"\u00A4",
    "dArr": u"\u21D3",
    "dagger": u"\u2020",
    "darr": u"\u2193",
    "deg": u"\u00B0",
    "delta": u"\u03B4",
    "diams": u"\u2666",
    "divide": u"\u00F7",
    "eacute": u"\u00E9",
    "ecirc": u"\u00EA",
    "egrave": u"\u00E8",
    "empty": u"\u2205",
    "emsp": u"\u2003",
    "ensp": u"\u2002",
    "epsilon": u"\u03B5",
    "equiv": u"\u2261",
    "eta": u"\u03B7",
    "eth": u"\u00F0",
    "euml": u"\u00EB",
    "euro": u"\u20AC",
    "exist": u"\u2203",
    "fnof": u"\u0192",
    "forall": u"\u2200",
    "frac12": u"\u00BD",
    "frac14": u"\u00BC",
    "frac34": u"\u00BE",
    "frasl": u"\u2044",
    "gamma": u"\u03B3",
    "ge": u"\u2265",
    "gt": u"\u003E",
    "GT": u"\u003E",
    "hArr": u"\u21D4",
    "harr": u"\u2194",
    "hearts": u"\u2665",
    "hellip": u"\u2026",
    "iacute": u"\u00ED",
    "icirc": u"\u00EE",
    "iexcl": u"\u00A1",
    "igrave": u"\u00EC",
    "image": u"\u2111",
    "infin": u"\u221E",
    "int": u"\u222B",
    "iota": u"\u03B9",
    "iquest": u"\u00BF",
    "isin": u"\u2208",
    "iuml": u"\u00EF",
    "kappa": u"\u03BA",
    "lArr": u"\u21D0",
    "lambda": u"\u03BB",
    "lang": u"\u2329",
    "laquo": u"\u00AB",
    "larr": u"\u2190",
    "lceil": u"\u2308",
    "ldquo": u"\u201C",
    "le": u"\u2264",
    "lfloor": u"\u230A",
    "lowast": u"\u2217",
    "loz": u"\u25CA",
    "lrm": u"\u200E",
    "lsaquo": u"\u2039",
    "lsquo": u"\u2018",
    "lt": u"\u003C",
    "LT": u"\u003C",
    "macr": u"\u00AF",
    "mdash": u"\u2014",
    "micro": u"\u00B5",
    "middot": u"\u00B7",
    "minus": u"\u2212",
    "mu": u"\u03BC",
    "nabla": u"\u2207",
    "nbsp": u"\u00A0",
    "ndash": u"\u2013",
    "ne": u"\u2260",
    "ni": u"\u220B",
    "not": u"\u00AC",
    "notin": u"\u2209",
    "nsub": u"\u2284",
    "ntilde": u"\u00F1",
    "nu": u"\u03BD",
    "oacute": u"\u00F3",
    "ocirc": u"\u00F4",
    "oelig": u"\u0153",
    "ograve": u"\u00F2",
    "oline": u"\u203E",
    "omega": u"\u03C9",
    "omicron": u"\u03BF",
    "oplus": u"\u2295",
    "or": u"\u2228",
    "ordf": u"\u00AA",
    "ordm": u"\u00BA",
    "oslash": u"\u00F8",
    "otilde": u"\u00F5",
    "otimes": u"\u2297",
    "ouml": u"\u00F6",
    "para": u"\u00B6",
    "part": u"\u2202",
    "permil": u"\u2030",
    "perp": u"\u22A5",
    "phi": u"\u03C6",
    "pi": u"\u03C0",
    "piv": u"\u03D6",
    "plusmn": u"\u00B1",
    "pound": u"\u00A3",
    "prime": u"\u2032",
    "prod": u"\u220F",
    "prop": u"\u221D",
    "psi": u"\u03C8",
    "quot": u"\u0022",
    "QUOT": u"\u0022",
    "rArr": u"\u21D2",
    "radic": u"\u221A",
    "rang": u"\u232A",
    "raquo": u"\u00BB",
    "rarr": u"\u2192",
    "rceil": u"\u2309",
    "rdquo": u"\u201D",
    "real": u"\u211C",
    "reg": u"\u00AE",
    "REG": u"\u00AE",
    "rfloor": u"\u230B",
    "rho": u"\u03C1",
    "rlm": u"\u200F",
    "rsaquo": u"\u203A",
    "rsquo": u"\u2019",
    "sbquo": u"\u201A",
    "scaron": u"\u0161",
    "sdot": u"\u22C5",
    "sect": u"\u00A7",
    "shy": u"\u00AD",
    "sigma": u"\u03C3",
    "sigmaf": u"\u03C2",
    "sim": u"\u223C",
    "spades": u"\u2660",
    "sub": u"\u2282",
    "sube": u"\u2286",
    "sum": u"\u2211",
    "sup": u"\u2283",
    "sup1": u"\u00B9",
    "sup2": u"\u00B2",
    "sup3": u"\u00B3",
    "supe": u"\u2287",
    "szlig": u"\u00DF",
    "tau": u"\u03C4",
    "there4": u"\u2234",
    "theta": u"\u03B8",
    "thetasym": u"\u03D1",
    "thinsp": u"\u2009",
    "thorn": u"\u00FE",
    "tilde": u"\u02DC",
    "times": u"\u00D7",
    "trade": u"\u2122",
    "uArr": u"\u21D1",
    "uacute": u"\u00FA",
    "uarr": u"\u2191",
    "ucirc": u"\u00FB",
    "ugrave": u"\u00F9",
    "uml": u"\u00A8",
    "upsih": u"\u03D2",
    "upsilon": u"\u03C5",
    "uuml": u"\u00FC",
    "weierp": u"\u2118",
    "xi": u"\u03BE",
    "yacute": u"\u00FD",
    "yen": u"\u00A5",
    "yuml": u"\u00FF",
    "zeta": u"\u03B6",
    "zwj": u"\u200D",
    "zwnj": u"\u200C"
}

# Data representing the end of the input stream
EOF = object()

# Token objects used to hold token data when tokens are in the
# process of being constructed
class Token(object):
    """Abstract base class from which all tokens derive
    """
    def __init__(self):
        raise NotImplementedError

class DoctypeToken(Token):
    """Token representing a DOCTYPE
    Attributes - name:  The name of the doctype
                 error: The Error status of the doctype)
    """
    def __init__(self, name=None):
        self.name = None
        self.error = True

class TagToken(Token):
    """Token representing a tag.
    Attributes - name:       The tag name
                 attributes: A list of (attribute-name,value) lists
    """
    def __init__(self, name=""):
        self.name = name
        self.attributes = []

class StartTagToken(TagToken):
    """Token representing a start tag
    """
    pass

class EndTagToken(TagToken):
    """Token representing an end tag
    """
    pass

class CommentToken(Token):
    """Token representing a comment
    Attributes - data:   The comment data"""
    def __init__(self, data=None):
        self.data = data

class HTMLTokenizer(object):
    """This class has various attributes:

    * self.parser
      Points to the parser object that implements the following methods:

      - processDoctype(name, error)
      - processStartTag(tagname, attributes[])
      - processEndTag(tagname, attributes[])
      - processComment(data)
      - processCharacter(data)
      - processEOF()

    * self.currentToken
      Holds the token that is currently being processed.

    * self.state
      Holds a reference to the method to be invoked... XXX

    * self.states
      Holds a mapping between states and methods that implement the state.
    """

    # XXX does processEndTag really need that second argument?

    def __init__(self, parser):
        self.parser = parser

        self.states = {
            "data":self.dataState,
            "entityData":self.entityDataState,
            "tagOpen":self.tagOpenState,
            "closeTagOpen":self.closeTagOpenState,
            "tagName":self.tagNameState,
            "beforeAttributeName":self.beforeAttributeNameState,
            "attributeName":self.attributeNameState,
            "afterAttributeName":self.afterAttributeNameState,
            "beforeAttributeValue":self.beforeAttributeValueState,
            "attributeValueDoubleQuoted":self.attributeValueDoubleQuotedState,
            "attributeValueSingleQuoted":self.attributeValueSingleQuotedState,
            "attributeValueUnQuoted":self.attributeValueUnQuotedState,
            "bogusComment":self.bogusCommentState,
            "markupDeclerationOpen":self.markupDeclerationOpenState,
            "comment":self.commentState,
            "commentDash":self.commentDashState,
            "commentEnd":self.commentEndState,
            "doctype":self.doctypeState,
            "beforeDoctypeName":self.beforeDoctypeNameState,
            "doctypeName":self.doctypeNameState,
            "afterDoctypeName":self.afterDoctypeNameState,
            "bogusDoctype":self.bogusDoctypeState
        }

        self.voidElements = (
            # XXX This list doesn't include <event-source> and <command> yet.
            # AT Make this a "global" variable?
            "base",
            "link",
            "meta",
            "hr",
            "br",
            "img",
            "embed",
            "param",
            "area",
            "col",
            "input"
        )

        # Setup the initial tokenizer state
        self.contentModelFlag = contentModelFlags['PCDATA']
        self.state = self.states['data']

        # The current token being created
        self.currentToken = None

        self.characterQueue = []

    def tokenize(self, dataStream):
        # For simplicity we assume here that the input to the tokenizer is
        # already decoded to unicode
        self.dataStream = dataStream

        # Start processing. When EOF is reached self.state will return False
        # instead of True and the loop will terminate.
        while self.state():
            pass

    def changeState(self, state):
        self.state = self.states[state]

    def consumeChar(self):
        """Get the next character to be consumed

        If the characterQueue has characters they must be processed before any
        character is added to the stream. This is to allow e.g. lookahead
        """

        # XXX this is quite wrong ... the input stream has some normalization
        # applied that doesn't happen here...
        if self.characterQueue:
            return self.characterQueue.pop(0)
        else:
            return self.dataStream.read(1) or EOF


    # Below are various helper functions the tokenizer states use worked out.

    def processSolidusInTag(self):
        """When a solidus (/) is encountered within a tag name what happens
        depends on whether the current tag name matches that of a void element.
        If it matches a void element atheists did the wrong thing and if it
        doesn't it's wrong for everyone.
        """

        # We need to consume another character to make sure it's a ">" before
        # throwing an atheist parse error.
        data = self.consumeChar()

        if self.currentToken.name in self.voidElements and data == u">":
            self.parser.atheistParseError()
        else:
            self.parser.parseError()

        # The character we just consumed need to be put back on the stack so it
        # doesn't get lost...
        self.characterQueue.append(data)

    def consumeNumberEntity(isHex):
        """This function returns either U+FFFD or the character based on the
        decimal or hexadecimal representation. It also discards ";" if present.
        If not present self.parser.parseError() is invoked.
        """

        range = string.digits
        radix = 10
        if isHex:
            range = string.hexdigits
            radix = 16

        char = u"\uFFFD"
        charStack = []

        # Consume all the characters that are in range.
        while c is self.consumeChar() and c in range: # XXX does this work!?
            charStack.append(c)

        # Convert the set of characters consumed to an int.
        charAsInt = int("".join(charStack), radix)

        try:
            # XXX This is wrong. This doesn't take "windows-1252 entities" into
            # account.

            # XXX We should have a separate function that does "int" to
            # "unicodestring" conversion since this doesn't always work
            # according to hsivonen. Also, unichr has a limitation of 65535
            char = unichr(charAsInt)
        except:
            pass

        # Discard the ; if present. Otherwise, put it back on the queue and
        # invoke parseError on parser.
        data = self.consumeChar()
        if data != u";":
            self.parser.parseError()
            self.characterQueue.append(data)

        return char

    def consumeEntity():
        char = None
        charStack = []
        charStack.append(self.consumeChar())
        if charStack[0] == u"#":
            charStack.append(self.consumeChar())
            charStack.append(self.consumeChar())
            if charStack[1].lower() == u"x" \
              and charStack[2] in string.hexdigits:
                # Hexadecimal entity detected.
                self.characterQueue.append(charStack[2]) # XXX does this work!?
                char = consumeNumberEntity(True)
            elif charStack[1] in string.digits:
                # Decimal entity detected.
                charStack.pop(0)
                self.characterQueue.append(charStack[1]) # XXX does this work!?
                self.characterQueue.append(charStack[2]) # XXX does this work!?
                char = consumeNumberEntity(False)
            else:
                # No number entity detected.
                self.characterQueue.extend(charStack) # XXX does this work!?
                self.parser.parseError()
        else:
            # At this point in the process might have named entity. Entities
            # are stored in the global variable "entities".

            # Consume characters and compare to these to a substring of the
            # entity names in the list until the substring no longer returns
            # something.
            while filter(lambda name: \
              name.startswith("".join(charStack)), entities):
                charStack.append(self.consumeChar())

            # At this point we have the name of the named entity or nothing.
            possibleEntityName = "".join(charStack)[:-1]
            if possibleEntityName in entities:
                char = entities[possibleEntityName]

                # Check whether or not the last character returned can be
                # discarded or needs to be put back.
                if not charStack[-1] == ";":
                    self.parser.parseError()
                    self.characterQueue.append(charStack[-1])
            else:
                self.parser.parseError()
                self.characterQueue.extend(charStack)
        return char

    def processEntityInAttribute(self):
        """This method replaces the need for "entityInAttributeValueState".
        """
        entity = self.consumeEntity()
        if entity:
            self.currentToken.attributes[-1][1] += entity
        else:
            self.currentToken.attributes[-1][1] += u"&"

    def emitCurrentToken(self):
        """This method is a generic handler for emitting the StartTagToken,
        EndTagToken, CommentToken and DoctypeToken. It also sets the state to
        "data" because that's what's needed after a token has been emitted.
        """

        # Although isinstance() is http://www.canonical.org/~kragen/isinstance/
        # considered harmful it should be ok here given that the classes are for
        # internal usage.

        if isinstance(self.currentToken, StartTagToken):
            # XXX set last emitted tag name...
            self.parser.processStartTag(self.currentToken.name, self.currentToken.attributes)
        elif isinstance(self.currentToken, EndTagToken):
            self.parser.processEndTag(self.currentToken.name, self.currentToken.attributes)
        elif isinstance(self.currentToken, CommentToken):
            self.parser.processComment(self.currentToken.data)
        elif isinstance(self.currentToken, DoctypeToken):
            self.parser.processDoctype(self.currentToken.name, self.currentToken.error)
        else:
            assert False
        self.changeState("data")

    def emitCurrentTokenWithParseError(self, data=None):
        """This method is equivalent to emitCurrentToken (well, it invokes it)
        except that it also puts "data" back on the characters queue if a data
        argument is provided and it throws a parse error."""
        if data:
            self.characterQueue.append(data)
        self.emitCurrentToken()
        self.parser.parseError()

    def attributeValueQuotedStateHandler(self, quoteType):
        data = self.consumeChar()
        if data == quoteType:
            self.changeState("beforeAttributeName")
        elif data == u"&":
            self.processEntityInAttribute()
        elif data == EOF:
            self.emitCurrentTokenWithParseError(data)
        else:
            self.currentToken.attributes[-1][1] += data

    # Below are the various tokenizer states worked out.

    # XXX AT Perhaps we should have Hixie run some evaluation on billions of
    # documents to figure out what the order of the various if and elif
    # statements should be.

    def dataState(self):
        data = self.consumeChar()
        if (data == u"&" and
          (self.contentModelFlag in
          (contentModelFlags["PCDATA"], contentModelFlags["RCDATA"]))):
            self.changeState("entity")
        elif (data == u"<" and
          self.contentModelFlag != contentModelFlags['PLAINTEXT']):
            self.changeState("tagOpen")
        elif data == EOF:
            self.parser.processEOF()
            return False
        else:
            self.parser.processCharacter(data)
        return True

    def entityDataState(self):
        assert self.contentModelFlag != contentModelFlags["CDATA"]

        entity = self.consumeEntity()
        if entity:
            self.parser.processCharacter(entity)
        else:
            self.parser.processCharacter(u"&")
        self.changeState("data")
        return True

    def tagOpenState(self):
        data = self.consumeChar()
        if (self.contentModelFlag in
          (contentModelFlags["RCDATA"], contentModelFlags["CDATA"])):
            if data == u"/":
                self.changeState("closeTagOpen")
            else:
                self.parser.processCharacter(u"<")
                self.characterQueue.append(data)
                self.changeState("data")
        elif self.contentModelFlag == contentModelFlags['PCDATA']:
            if data == u"!":
                self.changeState("markupDeclerationOpen")
            elif data == u"/":
                self.changeState("closeTagOpen")
            elif data in string.ascii_letters:
                self.currentToken = StartTagToken(data.lower())
                self.changeState("tagName")
            elif data == u">":
                self.parser.parseError()
                self.parser.processCharacter(u"<")
                self.parser.processCharacter(u">")
                self.changeState("dataState")
            elif data == u"?":
                self.parser.parseError()
                self.characterQueue.append(data)
                self.changeState("bogusComment")
            else:
                self.parser.parseError()
                self.parser.processCharacter(u"<")
                self.characterQueue.append(data)
                self.changeState("data")
        else:
            assert False
        return True

    def closeTagOpenState(self):
        if (self.contentModelFlag in
          (contentModelFlags["RCDATA"], contentModelFlags["CDATA"])):
            charStack = []

            # So far we know that "</" has been consumed. We now need to know
            # whether the next few characters match the name of last emitted
            # start tag which also happens to be the currentToken. We also need
            # to have the character directly after the characters that could
            # match the start tag name.
            for x in xrange(len(self.currentToken.name)+1):
                charStack.append(self.consumeChar())

            # Since this is just for checking. We put the characters back on
            # the stack.
            self.characterQueue.append(charStack)

            if not self.currentToken.name == "".join(charStack[:-1]).lower() \
              and charStack[-1] in spaceCharacters + [u">", u"/", u"<", EOF]:
                self.parser.parseError()
                self.parser.processCharacter(u"<")
                self.parser.processCharacter(u"/")
                self.changeState("data")

                # Need to return here since we don't want the rest of the
                # method to be walked through.
                return True

        if self.contentModelFlag != contentModelFlags["PLAINTEXT"]:
            data = self.consumeChar()
            if data in string.ascii_letters:
                self.currentToken = EndTagToken(data)
                self.changeState("tagName")
            elif data == u">":
                self.parser.parseError()
                self.changeState("data")
            elif data == EOF:
                self.parser.parseError()
                self.parser.processCharacter(u"<")
                self.parser.processCharacter(u"/")
                self.characterQueue.append(data)
                self.changeState("data")
            else:
                self.parser.parseError()
                self.characterQueue.append(data)
                self.changeState("bogusComment")
        return True

    def tagNameState(self):
        data = self.consumeChar()
        if data in spaceCharacters:
            self.changeState("beforeAttributeName")
        elif data == u">":
            self.emitCurrentToken()
        elif data in string.ascii_uppercase:
            self.currentToken.name += data.lower()
        elif data == u"<" or data == EOF:
            self.emitCurrentTokenWithParseError(data)
        elif data == u"/":
            self.processSolidusInTag()
            self.changeState("beforeAttributeName")
        else:
            self.currentToken.name += data
        return True

    def beforeAttributeNameState(self):
        data = self.consumeChar()
        if data in spaceCharacters:
            pass
        elif data == u">":
            self.emitCurrentToken()
        elif data in string.ascii_uppercase:
            self.currentToken.attributes.append([data.lower(), ""])
        elif data == u"/":
            self.processSolidusInTag()
        elif data == u"<" or data == EOF:
            self.emitCurrentTokenWithParseError(data)
        else:
            self.currentToken.attributes.append([data, ""])
        return True

    def attributeNameState(self):
        # XXX Doesn't handle leaving the attribute name state very well.
        # Specifically dropping of duplicate attributes and reporting a parse
        # error for them...
        data = self.consumeChar()
        if data in spaceCharacters:
            self.changeState("afterAttributeName")
        elif data == u"=":
            self.changeState("beforeAttributeValue")
        elif data == u">":
            self.emitCurrentToken()
        elif data in string.ascii_uppercase:
            self.currentToken.attributes[-1][0] += data.lower()
        elif data == u"/":
            self.processSolidusInTag()
            self.changeState("beforeAttributeName")
        elif data == u"<" or data == EOF:
            self.emitCurrentTokenWithParseError(data)
        else:
            self.currentToken.attributes[-1][0] += data
        return True

    def afterAttributeNameState(self):
        data = self.consumeChar()
        if data in spaceCharacters:
            pass
        elif data == u"=":
            self.changeState("beforeAttributeValue")
        elif data == u">":
            self.emitCurrentToken()
        elif data in string.ascii_uppercase:
            self.currentToken.attributes.append(data.lower(), "")
            self.changeState("attributeName")
        elif data == u"/":
            self.processSolidusInTag()
            self.changeState("beforeAttributeName")
        elif data == u"<" or data == EOF:
            self.emitCurrentTokenWithParseError(data)
        else:
            self.currentToken.attributes.append(data, "")
            self.changeState("attributeName")
        return True

    def beforeAttributeValueState(self):
        data = consumeChar()
        if data in spaceCharacters:
            pass
        elif data == u"\"":
            self.changeState("attributeValueDoubleQuoted")
        elif data == u"&":
            self.changeState("attributeValueUnQuoted")
            self.characterQueue.append(data);
        elif data == u"'":
            self.changeState("attributeValueSingleQuoted")
        elif data == u">":
            self.emitCurrentToken()
        elif data == u"<" or data == EOF:
            self.emitCurrentTokenWithParseError(data)
        else:
            self.currentToken[-1][1] += data
            self.changeState("attributeValueUnQuoted")
        return True

    def attributeValueDoubleQuotedState(self):
        # AT We could also let self.attributeValueQuotedStateHandler always
        # return true and then return that directly here. Not sure what is
        # faster or better...
        self.attributeValueQuotedStateHandler(u"\"")
        return True

    def attributeValueSingleQuotedState(self):
        self.attributeValueQuotedStateHandler(u"'")
        return True

    def attributeValueUnQuotedState(self):
        data = self.consumeChar()
        if data in spaceCharacters:
            self.changeState("beforeAttributeName")
        elif data == u"&":
            self.processEntityInAttribute()
        elif data == u">":
            self.emitCurrentToken()
        elif data == u"<" or data == EOF:
            self.emitCurrentTokenWithParseError(data)
        else:
            self.currentToken.attributes[-1][1] += data
        return True

    def bogusCommentState(self):
        assert self.contentModelFlag != contentModelFlags['PCDATA']

        charStack = [self.ConsumeChar()]
        while charStack[-1] not in [u">", EOF]:
            charStack.append(self.consumeChar())

        if charStack[-1] == EOF:
            self.characterQueue.append(EOF)

        # Make a new comment token and give it as value the characters the loop
        # consumed. The last character is either > or EOF and should not be
        # part of the comment data.
        self.currentToken = CommentToken("".charStack[:-1])
        self.emitCurrentToken()

    def markupDeclerationOpenState(self):
        assert self.contentModelFlag != contentModelFlags['PCDATA']

        charStack = []
        for x in xrange(2):
            charStack.append(self.consumeChar())
        if charStack == [u"-", u"-"]:
            self.currentToken = CommentToken()
            self.changeState("comment")
        else:
            for x in xrange(5):
                charStack.append(self.consumeChar())
            if "".join(charStack).upper() == u"DOCTYPE":
                self.changeState("doctype")
            else:
                self.parser.parseError()
                self.characterQueue.extend(charStack)
                self.changeState("bogusComment")
        return True

    def commentState(self):
        data = self.consumeChar()
        if data == u"-":
            self.changeState("commentDash")
        elif data == EOF:
            self.emitCurrentTokenWithParseError(data)
        else:
            self.currentToken.data += data
        return True

    def commentDashState(self):
        data = self.consumeChar()
        if data == u"-":
            self.changeState("commentEnd")
        elif data == EOF:
            self.emitCurrentTokenWithParseError(data)
        else:
            self.currentToken.data += u"-" + data
        return True

    def commentEndState(self):
        data = self.consumeChar()
        if data == u">":
            self.emitCurrentToken()
        elif data == u"-":
            self.parser.parseError()
            self.currentToken.data += data
        elif data == EOF:
            self.emitCurrentTokenWithParseError(data)
        else:
            self.parser.parseError()
            self.currentToken.data += u"--" + data
            self.changeState("comment")
        return True

    def doctypeState(self):
        data = self.consumeChar()
        if data in spaceCharacters:
            self.changeState("beforeDoctypeName")
        else:
            self.parser.parseError()
            self.characterQueue.append(data)
            self.changeState("beforeDoctypeName")
        return True

    def beforeDoctypeNameState(self):
        data = self.consumeChar()
        if data in spaceCharacters:
            pass
        elif data in string.ascii_lowercase:
            self.currentToken = DoctypeToken(data.upper())
        elif data == u">":
            # Character needs to be consumed per the specification so don't
            # invoke with "data" as argument.
            self.emitCurrentTokenWithParseError()
        elif data == EOF:
            self.emitCurrentTokenWithParseError(data)
        else:
            self.currentToken = DoctypeToken(data)
        return True

    def doctypeNameState(self):
        data = self.consumeChar()
        if data in spaceCharacters:
            self.changeState("afterDoctypeName")
        elif data == u">":
            self.emitCurrentToken()
        elif data == EOF:
            self.emitCurrentTokenWithParseError(data)
        else:
            # We can't just uppercase everything that arrives here. For
            # instance, non-ASCII characters.
            if data in string.ascii_lowercase:
                data = data.upper()
            self.currentToken.name += data

            # After some iterations through this state it should eventually say
            # "HTML". Otherwise there's an error.
            if self.currentToken.name == u"HTML":
                self.currentToken.error = False
        return True

    def afterDoctypeNameState(self):
        data = self.consumeChar()
        if data in spaceCharacters:
            pass
        elif data == u">":
            self.emitCurrentToken()
        elif data == EOF:
            self.currentToken.error = True
            self.emitCurrentTokenWithParseError(data)
        else:
            self.parser.parseError()
            self.currentToken.error = True
            self.changeState("bogusDoctype")
        return True

    def bogusDoctypeState(self):
        data = self.consumeChar()
        if data == u">":
            self.emitCurrentToken()
        elif data == EOF:
            self.emitCurrentTokenWithParseError(data)
        else:
            pass
        return True
