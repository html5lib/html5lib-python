# cython: language_level=3
from __future__ import absolute_import, division, unicode_literals

import cython

from six import unichr as chr

from collections import deque, OrderedDict
from sys import version_info

from ._ascii import ascii_lower

from .constants import spaceCharacters
from .constants import entities
from .constants import asciiLetters
from .constants import digits, hexDigits, EOF
from .constants import tokenTypes, tagTokenTypes
from .constants import replacementCharacters

from ._inputstream import HTMLInputStream

from ._trie import Trie

entitiesTrie = Trie(entities)

if cython.compiled:
    @cython.cfunc
    @cython.inline
    def attributeMap():
        if version.PY_VERSION_HEX >= 0x03070000:
            return {}
        else:
            return OrderedDict()
elif version_info >= (3, 7):
    attributeMap = dict
else:
    attributeMap = OrderedDict


class HTMLTokenizer(object):
    """ This class takes care of tokenizing HTML.

    * self.currentToken
      Holds the token that is currently being processed.

    * self._state
      Holds a reference to the method to be invoked... XXX

    * self.stream
      Points to HTMLInputStream object.
    """

    def __init__(self, stream, parser=None, **kwargs):

        self.stream = HTMLInputStream(stream, **kwargs)
        self.parser = parser

        # Setup the initial tokenizer state
        self._state = self.dataState

        # The current token being created
        self.currentToken = None
        self.currentAttribute = None
        super(HTMLTokenizer, self).__init__()

    def __iter__(self):
        """ This is where the magic happens.

        We do our usually processing through the states and when we have a token
        to return we yield the token which pauses processing until the next token
        is requested.
        """
        self.tokenQueue = deque([])
        # Start processing. When EOF is reached self._state will return False
        # instead of True and the loop will terminate.
        if cython.compiled:
            with cython.binding(False):
                while self._state(self):
                    while self.stream.errors:
                        yield {"type": tokenTypes["ParseError"], "data": self.stream.errors.pop(0)}
                    while self.tokenQueue:
                        yield self.tokenQueue.popleft()
        else:
            while self._state():
                while self.stream.errors:
                    yield {"type": tokenTypes["ParseError"], "data": self.stream.errors.pop(0)}
                while self.tokenQueue:
                    yield self.tokenQueue.popleft()

    @property
    def state(self):
        if cython.compiled:
            if self._state == self.dataState:
                return "dataState"
            elif self._state == self.entityDataState:
                return "entityDataState"
            elif self._state == self.rcdataState:
                return "rcdataState"
            elif self._state == self.characterReferenceInRcdata:
                return "characterReferenceInRcdata"
            elif self._state == self.rawtextState:
                return "rawtextState"
            elif self._state == self.scriptDataState:
                return "scriptDataState"
            elif self._state == self.plaintextState:
                return "plaintextState"
            elif self._state == self.tagOpenState:
                return "tagOpenState"
            elif self._state == self.closeTagOpenState:
                return "closeTagOpenState"
            elif self._state == self.tagNameState:
                return "tagNameState"
            elif self._state == self.rcdataLessThanSignState:
                return "rcdataLessThanSignState"
            elif self._state == self.rcdataEndTagOpenState:
                return "rcdataEndTagOpenState"
            elif self._state == self.rcdataEndTagNameState:
                return "rcdataEndTagNameState"
            elif self._state == self.rawtextLessThanSignState:
                return "rawtextLessThanSignState"
            elif self._state == self.rawtextEndTagOpenState:
                return "rawtextEndTagOpenState"
            elif self._state == self.rawtextEndTagNameState:
                return "rawtextEndTagNameState"
            elif self._state == self.scriptDataLessThanSignState:
                return "scriptDataLessThanSignState"
            elif self._state == self.scriptDataEndTagOpenState:
                return "scriptDataEndTagOpenState"
            elif self._state == self.scriptDataEndTagNameState:
                return "scriptDataEndTagNameState"
            elif self._state == self.scriptDataEscapeStartState:
                return "scriptDataEscapeStartState"
            elif self._state == self.scriptDataEscapeStartDashState:
                return "scriptDataEscapeStartDashState"
            elif self._state == self.scriptDataEscapedState:
                return "scriptDataEscapedState"
            elif self._state == self.scriptDataEscapedDashState:
                return "scriptDataEscapedDashState"
            elif self._state == self.scriptDataEscapedDashDashState:
                return "scriptDataEscapedDashDashState"
            elif self._state == self.scriptDataEscapedLessThanSignState:
                return "scriptDataEscapedLessThanSignState"
            elif self._state == self.scriptDataEscapedEndTagOpenState:
                return "scriptDataEscapedEndTagOpenState"
            elif self._state == self.scriptDataEscapedEndTagNameState:
                return "scriptDataEscapedEndTagNameState"
            elif self._state == self.scriptDataDoubleEscapeStartState:
                return "scriptDataDoubleEscapeStartState"
            elif self._state == self.scriptDataDoubleEscapedState:
                return "scriptDataDoubleEscapedState"
            elif self._state == self.scriptDataDoubleEscapedDashState:
                return "scriptDataDoubleEscapedDashState"
            elif self._state == self.scriptDataDoubleEscapedDashDashState:
                return "scriptDataDoubleEscapedDashDashState"
            elif self._state == self.scriptDataDoubleEscapedLessThanSignState:
                return "scriptDataDoubleEscapedLessThanSignState"
            elif self._state == self.scriptDataDoubleEscapeEndState:
                return "scriptDataDoubleEscapeEndState"
            elif self._state == self.beforeAttributeNameState:
                return "beforeAttributeNameState"
            elif self._state == self.attributeNameState:
                return "attributeNameState"
            elif self._state == self.afterAttributeNameState:
                return "afterAttributeNameState"
            elif self._state == self.beforeAttributeValueState:
                return "beforeAttributeValueState"
            elif self._state == self.attributeValueDoubleQuotedState:
                return "attributeValueDoubleQuotedState"
            elif self._state == self.attributeValueSingleQuotedState:
                return "attributeValueSingleQuotedState"
            elif self._state == self.attributeValueUnQuotedState:
                return "attributeValueUnQuotedState"
            elif self._state == self.afterAttributeValueState:
                return "afterAttributeValueState"
            elif self._state == self.selfClosingStartTagState:
                return "selfClosingStartTagState"
            elif self._state == self.bogusCommentState:
                return "bogusCommentState"
            elif self._state == self.markupDeclarationOpenState:
                return "markupDeclarationOpenState"
            elif self._state == self.commentStartState:
                return "commentStartState"
            elif self._state == self.commentStartDashState:
                return "commentStartDashState"
            elif self._state == self.commentState:
                return "commentState"
            elif self._state == self.commentEndDashState:
                return "commentEndDashState"
            elif self._state == self.commentEndState:
                return "commentEndState"
            elif self._state == self.commentEndBangState:
                return "commentEndBangState"
            elif self._state == self.doctypeState:
                return "doctypeState"
            elif self._state == self.beforeDoctypeNameState:
                return "beforeDoctypeNameState"
            elif self._state == self.doctypeNameState:
                return "doctypeNameState"
            elif self._state == self.afterDoctypeNameState:
                return "afterDoctypeNameState"
            elif self._state == self.afterDoctypePublicKeywordState:
                return "afterDoctypePublicKeywordState"
            elif self._state == self.beforeDoctypePublicIdentifierState:
                return "beforeDoctypePublicIdentifierState"
            elif self._state == self.doctypePublicIdentifierDoubleQuotedState:
                return "doctypePublicIdentifierDoubleQuotedState"
            elif self._state == self.doctypePublicIdentifierSingleQuotedState:
                return "doctypePublicIdentifierSingleQuotedState"
            elif self._state == self.afterDoctypePublicIdentifierState:
                return "afterDoctypePublicIdentifierState"
            elif self._state == self.betweenDoctypePublicAndSystemIdentifiersState:
                return "betweenDoctypePublicAndSystemIdentifiersState"
            elif self._state == self.afterDoctypeSystemKeywordState:
                return "afterDoctypeSystemKeywordState"
            elif self._state == self.beforeDoctypeSystemIdentifierState:
                return "beforeDoctypeSystemIdentifierState"
            elif self._state == self.doctypeSystemIdentifierDoubleQuotedState:
                return "doctypeSystemIdentifierDoubleQuotedState"
            elif self._state == self.doctypeSystemIdentifierSingleQuotedState:
                return "doctypeSystemIdentifierSingleQuotedState"
            elif self._state == self.afterDoctypeSystemIdentifierState:
                return "afterDoctypeSystemIdentifierState"
            elif self._state == self.bogusDoctypeState:
                return "bogusDoctypeState"
            elif self._state == self.cdataSectionState:
                return "cdataSectionState"
            else:
                raise ValueError("unreachable")
        else:
            return self._state.__name__

    @state.setter
    def state(self, newState):
        if newState == "dataState":
            self._state = self.dataState
        elif newState == "cdataSectionState":
            self._state = self.cdataSectionState
        elif newState == "rawtextState":
            self._state = self.rawtextState
        elif newState == "rcdataState":
            self._state = self.rcdataState
        elif newState == "plaintextState":
            self._state = self.plaintextState
        elif newState == "scriptDataState":
            self._state = self.scriptDataState
        else:
            raise ValueError(newState)

    def consumeNumberEntity(self, isHex):
        """This function returns either U+FFFD or the character based on the
        decimal or hexadecimal representation. It also discards ";" if present.
        If not present self.tokenQueue.append({"type": tokenTypes["ParseError"]}) is invoked.
        """

        allowed = digits
        radix = 10
        if isHex:
            allowed = hexDigits
            radix = 16

        charStack = []

        # Consume all the characters that are in range while making sure we
        # don't hit an EOF.
        c = self.stream.char()
        while c in allowed and c is not EOF:
            charStack.append(c)
            c = self.stream.char()

        # Convert the set of characters consumed to an int.
        if cython.compiled:
            with cython.overflowcheck(True):
                try:
                    charAsInt = int("".join(charStack), radix)
                except OverflowError:
                    charAsInt = 0x7FFFFFFF
        else:
            charAsInt = int("".join(charStack), radix)

        # Certain characters get replaced with others
        if charAsInt in replacementCharacters:
            char = replacementCharacters[charAsInt]
            self.tokenQueue.append({"type": tokenTypes["ParseError"], "data":
                                    "illegal-codepoint-for-numeric-entity",
                                    "datavars": {"charAsInt": charAsInt}})
        elif ((0xD800 <= charAsInt <= 0xDFFF) or
              (charAsInt > 0x10FFFF)):
            char = "\uFFFD"
            self.tokenQueue.append({"type": tokenTypes["ParseError"], "data":
                                    "illegal-codepoint-for-numeric-entity",
                                    "datavars": {"charAsInt": charAsInt}})
        else:
            if (
                (0x0001 <= charAsInt <= 0x0008) or
                (0x000E <= charAsInt <= 0x001F) or
                (0x007F <= charAsInt <= 0x009F) or
                (0xFDD0 <= charAsInt <= 0xFDEF) or
                charAsInt == 0x000B or
                (charAsInt & 0xFFFE) == 0xFFFE
            ):
                self.tokenQueue.append({"type": tokenTypes["ParseError"],
                                        "data":
                                        "illegal-codepoint-for-numeric-entity",
                                        "datavars": {"charAsInt": charAsInt}})
            try:
                # Try/except needed as UCS-2 Python builds' unichar only works
                # within the BMP.
                char = chr(charAsInt)
            except ValueError:
                v = charAsInt - 0x10000
                char = chr(0xD800 | (v >> 10)) + chr(0xDC00 | (v & 0x3FF))

        # Discard the ; if present. Otherwise, put it back on the queue and
        # invoke parseError on parser.
        if c != ";":
            self.tokenQueue.append({"type": tokenTypes["ParseError"], "data":
                                    "numeric-entity-without-semicolon"})
            self.stream.unget(c)

        return char

    def consumeEntity(self, allowedChar=None, fromAttribute=False):
        # Initialise to the default output for when no entity is matched
        output = "&"

        charStack = [self.stream.char()]
        if (charStack[0] in spaceCharacters or charStack[0] in (EOF, "<", "&") or
                (allowedChar is not None and allowedChar == charStack[0])):
            self.stream.unget(charStack[0])

        elif charStack[0] == "#":
            # Read the next character to see if it's hex or decimal
            hex = False
            charStack.append(self.stream.char())
            if charStack[-1] in ("x", "X"):
                hex = True
                charStack.append(self.stream.char())

            # charStack[-1] should be the first digit
            if (hex and charStack[-1] in hexDigits) \
                    or (not hex and charStack[-1] in digits):
                # At least one digit found, so consume the whole number
                self.stream.unget(charStack[-1])
                output = self.consumeNumberEntity(hex)
            else:
                # No digits found
                self.tokenQueue.append({"type": tokenTypes["ParseError"],
                                        "data": "expected-numeric-entity"})
                self.stream.unget(charStack.pop())
                output = "&" + "".join(charStack)

        else:
            # At this point in the process might have named entity. Entities
            # are stored in the global variable "entities".
            #
            # Consume characters and compare to these to a substring of the
            # entity names in the list until the substring no longer matches.
            while (charStack[-1] is not EOF):
                if not entitiesTrie.has_keys_with_prefix("".join(charStack)):
                    break
                charStack.append(self.stream.char())

            # At this point we have a string that starts with some characters
            # that may match an entity
            # Try to find the longest entity the string will match to take care
            # of &noti for instance.
            try:
                entityName = entitiesTrie.longest_prefix("".join(charStack[:-1]))
                entityLength = len(entityName)
            except KeyError:
                entityName = None

            if entityName is not None:
                if entityName[-1] != ";":
                    self.tokenQueue.append({"type": tokenTypes["ParseError"], "data":
                                            "named-entity-without-semicolon"})
                if (entityName[-1] != ";" and fromAttribute and
                    (charStack[entityLength] in asciiLetters or
                     charStack[entityLength] in digits or
                     charStack[entityLength] == "=")):
                    self.stream.unget(charStack.pop())
                    output = "&" + "".join(charStack)
                else:
                    output = entities[entityName]
                    self.stream.unget(charStack.pop())
                    output += "".join(charStack[entityLength:])
            else:
                self.tokenQueue.append({"type": tokenTypes["ParseError"], "data":
                                        "expected-named-entity"})
                self.stream.unget(charStack.pop())
                output = "&" + "".join(charStack)

        if fromAttribute:
            self.currentToken["data"][self.currentAttribute][-1] += output
        else:
            if output in spaceCharacters:
                tokenType = "SpaceCharacters"
            else:
                tokenType = "Characters"
            self.tokenQueue.append({"type": tokenTypes[tokenType], "data": output})

    def processEntityInAttribute(self, allowedChar):
        """This method replaces the need for "entityInAttributeValueState".
        """
        self.consumeEntity(allowedChar=allowedChar, fromAttribute=True)

    def emitCurrentToken(self):
        """This method is a generic handler for emitting the tags. It also sets
        the state to "data" because that's what's needed after a token has been
        emitted.
        """
        token = self.currentToken
        # Add token to the queue to be yielded
        if (token["type"] in tagTokenTypes):
            token["name"] = ascii_lower(token["name"])
            if token["type"] == tokenTypes["StartTag"]:
                data = token["data"]
                for k, v in data.items():
                    data[k] = v[0]

            if token["type"] == tokenTypes["EndTag"]:
                if token["data"]:
                    self.tokenQueue.append({"type": tokenTypes["ParseError"],
                                            "data": "attributes-in-end-tag"})
                if token["selfClosing"]:
                    self.tokenQueue.append({"type": tokenTypes["ParseError"],
                                            "data": "self-closing-flag-on-end-tag"})
        self.tokenQueue.append(token)
        self._state = self.dataState

    # Below are the various tokenizer states worked out.
    def dataState(self):
        data = self.stream.char()
        if data == "&":
            self._state = self.entityDataState
        elif data == "<":
            self._state = self.tagOpenState
        elif data == "\u0000":
            self.tokenQueue.append({"type": tokenTypes["ParseError"],
                                    "data": "invalid-codepoint"})
            self.tokenQueue.append({"type": tokenTypes["Characters"],
                                    "data": "\u0000"})
        elif data is EOF:
            # Tokenization ends.
            return False
        elif data in spaceCharacters:
            # Directly after emitting a token you switch back to the "data
            # state". At that point spaceCharacters are important so they are
            # emitted separately.
            self.tokenQueue.append({"type": tokenTypes["SpaceCharacters"], "data":
                                    data + self.stream.charsUntil(spaceCharacters, True)})
            # No need to update lastFourChars here, since the first space will
            # have already been appended to lastFourChars and will have broken
            # any <!-- or --> sequences
        else:
            chars = self.stream.charsUntil(("&", "<", "\u0000"))
            self.tokenQueue.append({"type": tokenTypes["Characters"], "data":
                                    data + chars})
        return True

    def entityDataState(self):
        self.consumeEntity()
        self._state = self.dataState
        return True

    def rcdataState(self):
        data = self.stream.char()
        if data == "&":
            self._state = self.characterReferenceInRcdata
        elif data == "<":
            self._state = self.rcdataLessThanSignState
        elif data == EOF:
            # Tokenization ends.
            return False
        elif data == "\u0000":
            self.tokenQueue.append({"type": tokenTypes["ParseError"],
                                    "data": "invalid-codepoint"})
            self.tokenQueue.append({"type": tokenTypes["Characters"],
                                    "data": "\uFFFD"})
        elif data in spaceCharacters:
            # Directly after emitting a token you switch back to the "data
            # state". At that point spaceCharacters are important so they are
            # emitted separately.
            self.tokenQueue.append({"type": tokenTypes["SpaceCharacters"], "data":
                                    data + self.stream.charsUntil(spaceCharacters, True)})
            # No need to update lastFourChars here, since the first space will
            # have already been appended to lastFourChars and will have broken
            # any <!-- or --> sequences
        else:
            chars = self.stream.charsUntil(("&", "<", "\u0000"))
            self.tokenQueue.append({"type": tokenTypes["Characters"], "data":
                                    data + chars})
        return True

    def characterReferenceInRcdata(self):
        self.consumeEntity()
        self._state = self.rcdataState
        return True

    def rawtextState(self):
        data = self.stream.char()
        if data == "<":
            self._state = self.rawtextLessThanSignState
        elif data == "\u0000":
            self.tokenQueue.append({"type": tokenTypes["ParseError"],
                                    "data": "invalid-codepoint"})
            self.tokenQueue.append({"type": tokenTypes["Characters"],
                                    "data": "\uFFFD"})
        elif data == EOF:
            # Tokenization ends.
            return False
        else:
            chars = self.stream.charsUntil(("<", "\u0000"))
            self.tokenQueue.append({"type": tokenTypes["Characters"], "data":
                                    data + chars})
        return True

    def scriptDataState(self):
        data = self.stream.char()
        if data == "<":
            self._state = self.scriptDataLessThanSignState
        elif data == "\u0000":
            self.tokenQueue.append({"type": tokenTypes["ParseError"],
                                    "data": "invalid-codepoint"})
            self.tokenQueue.append({"type": tokenTypes["Characters"],
                                    "data": "\uFFFD"})
        elif data == EOF:
            # Tokenization ends.
            return False
        else:
            chars = self.stream.charsUntil(("<", "\u0000"))
            self.tokenQueue.append({"type": tokenTypes["Characters"], "data":
                                    data + chars})
        return True

    def plaintextState(self):
        data = self.stream.char()
        if data == EOF:
            # Tokenization ends.
            return False
        elif data == "\u0000":
            self.tokenQueue.append({"type": tokenTypes["ParseError"],
                                    "data": "invalid-codepoint"})
            self.tokenQueue.append({"type": tokenTypes["Characters"],
                                    "data": "\uFFFD"})
        else:
            self.tokenQueue.append({"type": tokenTypes["Characters"], "data":
                                    data + self.stream.charsUntil("\u0000")})
        return True

    def tagOpenState(self):
        data = self.stream.char()
        if data == "!":
            self._state = self.markupDeclarationOpenState
        elif data == "/":
            self._state = self.closeTagOpenState
        elif data in asciiLetters:
            self.currentToken = {"type": tokenTypes["StartTag"],
                                 "name": data, "data": attributeMap(),
                                 "selfClosing": False,
                                 "selfClosingAcknowledged": False}
            self._state = self.tagNameState
        elif data == ">":
            # XXX In theory it could be something besides a tag name. But
            # do we really care?
            self.tokenQueue.append({"type": tokenTypes["ParseError"], "data":
                                    "expected-tag-name-but-got-right-bracket"})
            self.tokenQueue.append({"type": tokenTypes["Characters"], "data": "<>"})
            self._state = self.dataState
        elif data == "?":
            # XXX In theory it could be something besides a tag name. But
            # do we really care?
            self.tokenQueue.append({"type": tokenTypes["ParseError"], "data":
                                    "expected-tag-name-but-got-question-mark"})
            self.stream.unget(data)
            self._state = self.bogusCommentState
        else:
            # XXX
            self.tokenQueue.append({"type": tokenTypes["ParseError"], "data":
                                    "expected-tag-name"})
            self.tokenQueue.append({"type": tokenTypes["Characters"], "data": "<"})
            self.stream.unget(data)
            self._state = self.dataState
        return True

    def closeTagOpenState(self):
        data = self.stream.char()
        if data in asciiLetters:
            self.currentToken = {"type": tokenTypes["EndTag"], "name": data,
                                 "data": attributeMap(), "selfClosing": False}
            self._state = self.tagNameState
        elif data == ">":
            self.tokenQueue.append({"type": tokenTypes["ParseError"], "data":
                                    "expected-closing-tag-but-got-right-bracket"})
            self._state = self.dataState
        elif data is EOF:
            self.tokenQueue.append({"type": tokenTypes["ParseError"], "data":
                                    "expected-closing-tag-but-got-eof"})
            self.tokenQueue.append({"type": tokenTypes["Characters"], "data": "</"})
            self._state = self.dataState
        else:
            # XXX data can be _'_...
            self.tokenQueue.append({"type": tokenTypes["ParseError"], "data":
                                    "expected-closing-tag-but-got-char",
                                    "datavars": {"data": data}})
            self.stream.unget(data)
            self._state = self.bogusCommentState
        return True

    def tagNameState(self):
        data = self.stream.char()
        if data in spaceCharacters:
            self._state = self.beforeAttributeNameState
        elif data == ">":
            self.emitCurrentToken()
        elif data is EOF:
            self.tokenQueue.append({"type": tokenTypes["ParseError"], "data":
                                    "eof-in-tag-name"})
            self._state = self.dataState
        elif data == "/":
            self._state = self.selfClosingStartTagState
        elif data == "\u0000":
            self.tokenQueue.append({"type": tokenTypes["ParseError"],
                                    "data": "invalid-codepoint"})
            self.currentToken["name"] += "\uFFFD"
        else:
            self.currentToken["name"] += data
            # (Don't use charsUntil here, because tag names are
            # very short and it's faster to not do anything fancy)
        return True

    def rcdataLessThanSignState(self):
        data = self.stream.char()
        if data == "/":
            self.temporaryBuffer = ""
            self._state = self.rcdataEndTagOpenState
        else:
            self.tokenQueue.append({"type": tokenTypes["Characters"], "data": "<"})
            self.stream.unget(data)
            self._state = self.rcdataState
        return True

    def rcdataEndTagOpenState(self):
        data = self.stream.char()
        if data in asciiLetters:
            self.temporaryBuffer += data
            self._state = self.rcdataEndTagNameState
        else:
            self.tokenQueue.append({"type": tokenTypes["Characters"], "data": "</"})
            self.stream.unget(data)
            self._state = self.rcdataState
        return True

    def rcdataEndTagNameState(self):
        appropriate = self.currentToken and self.currentToken["name"].lower() == self.temporaryBuffer.lower()
        data = self.stream.char()
        if data in spaceCharacters and appropriate:
            self.currentToken = {"type": tokenTypes["EndTag"],
                                 "name": self.temporaryBuffer,
                                 "data": attributeMap(), "selfClosing": False}
            self._state = self.beforeAttributeNameState
        elif data == "/" and appropriate:
            self.currentToken = {"type": tokenTypes["EndTag"],
                                 "name": self.temporaryBuffer,
                                 "data": attributeMap(), "selfClosing": False}
            self._state = self.selfClosingStartTagState
        elif data == ">" and appropriate:
            self.currentToken = {"type": tokenTypes["EndTag"],
                                 "name": self.temporaryBuffer,
                                 "data": attributeMap(), "selfClosing": False}
            self.emitCurrentToken()
            self._state = self.dataState
        elif data in asciiLetters:
            self.temporaryBuffer += data
        else:
            self.tokenQueue.append({"type": tokenTypes["Characters"],
                                    "data": "</" + self.temporaryBuffer})
            self.stream.unget(data)
            self._state = self.rcdataState
        return True

    def rawtextLessThanSignState(self):
        data = self.stream.char()
        if data == "/":
            self.temporaryBuffer = ""
            self._state = self.rawtextEndTagOpenState
        else:
            self.tokenQueue.append({"type": tokenTypes["Characters"], "data": "<"})
            self.stream.unget(data)
            self._state = self.rawtextState
        return True

    def rawtextEndTagOpenState(self):
        data = self.stream.char()
        if data in asciiLetters:
            self.temporaryBuffer += data
            self._state = self.rawtextEndTagNameState
        else:
            self.tokenQueue.append({"type": tokenTypes["Characters"], "data": "</"})
            self.stream.unget(data)
            self._state = self.rawtextState
        return True

    def rawtextEndTagNameState(self):
        appropriate = self.currentToken and self.currentToken["name"].lower() == self.temporaryBuffer.lower()
        data = self.stream.char()
        if data in spaceCharacters and appropriate:
            self.currentToken = {"type": tokenTypes["EndTag"],
                                 "name": self.temporaryBuffer,
                                 "data": attributeMap(), "selfClosing": False}
            self._state = self.beforeAttributeNameState
        elif data == "/" and appropriate:
            self.currentToken = {"type": tokenTypes["EndTag"],
                                 "name": self.temporaryBuffer,
                                 "data": attributeMap(), "selfClosing": False}
            self._state = self.selfClosingStartTagState
        elif data == ">" and appropriate:
            self.currentToken = {"type": tokenTypes["EndTag"],
                                 "name": self.temporaryBuffer,
                                 "data": attributeMap(), "selfClosing": False}
            self.emitCurrentToken()
            self._state = self.dataState
        elif data in asciiLetters:
            self.temporaryBuffer += data
        else:
            self.tokenQueue.append({"type": tokenTypes["Characters"],
                                    "data": "</" + self.temporaryBuffer})
            self.stream.unget(data)
            self._state = self.rawtextState
        return True

    def scriptDataLessThanSignState(self):
        data = self.stream.char()
        if data == "/":
            self.temporaryBuffer = ""
            self._state = self.scriptDataEndTagOpenState
        elif data == "!":
            self.tokenQueue.append({"type": tokenTypes["Characters"], "data": "<!"})
            self._state = self.scriptDataEscapeStartState
        else:
            self.tokenQueue.append({"type": tokenTypes["Characters"], "data": "<"})
            self.stream.unget(data)
            self._state = self.scriptDataState
        return True

    def scriptDataEndTagOpenState(self):
        data = self.stream.char()
        if data in asciiLetters:
            self.temporaryBuffer += data
            self._state = self.scriptDataEndTagNameState
        else:
            self.tokenQueue.append({"type": tokenTypes["Characters"], "data": "</"})
            self.stream.unget(data)
            self._state = self.scriptDataState
        return True

    def scriptDataEndTagNameState(self):
        appropriate = self.currentToken and self.currentToken["name"].lower() == self.temporaryBuffer.lower()
        data = self.stream.char()
        if data in spaceCharacters and appropriate:
            self.currentToken = {"type": tokenTypes["EndTag"],
                                 "name": self.temporaryBuffer,
                                 "data": attributeMap(), "selfClosing": False}
            self._state = self.beforeAttributeNameState
        elif data == "/" and appropriate:
            self.currentToken = {"type": tokenTypes["EndTag"],
                                 "name": self.temporaryBuffer,
                                 "data": attributeMap(), "selfClosing": False}
            self._state = self.selfClosingStartTagState
        elif data == ">" and appropriate:
            self.currentToken = {"type": tokenTypes["EndTag"],
                                 "name": self.temporaryBuffer,
                                 "data": attributeMap(), "selfClosing": False}
            self.emitCurrentToken()
            self._state = self.dataState
        elif data in asciiLetters:
            self.temporaryBuffer += data
        else:
            self.tokenQueue.append({"type": tokenTypes["Characters"],
                                    "data": "</" + self.temporaryBuffer})
            self.stream.unget(data)
            self._state = self.scriptDataState
        return True

    def scriptDataEscapeStartState(self):
        data = self.stream.char()
        if data == "-":
            self.tokenQueue.append({"type": tokenTypes["Characters"], "data": "-"})
            self._state = self.scriptDataEscapeStartDashState
        else:
            self.stream.unget(data)
            self._state = self.scriptDataState
        return True

    def scriptDataEscapeStartDashState(self):
        data = self.stream.char()
        if data == "-":
            self.tokenQueue.append({"type": tokenTypes["Characters"], "data": "-"})
            self._state = self.scriptDataEscapedDashDashState
        else:
            self.stream.unget(data)
            self._state = self.scriptDataState
        return True

    def scriptDataEscapedState(self):
        data = self.stream.char()
        if data == "-":
            self.tokenQueue.append({"type": tokenTypes["Characters"], "data": "-"})
            self._state = self.scriptDataEscapedDashState
        elif data == "<":
            self._state = self.scriptDataEscapedLessThanSignState
        elif data == "\u0000":
            self.tokenQueue.append({"type": tokenTypes["ParseError"],
                                    "data": "invalid-codepoint"})
            self.tokenQueue.append({"type": tokenTypes["Characters"],
                                    "data": "\uFFFD"})
        elif data == EOF:
            self._state = self.dataState
        else:
            chars = self.stream.charsUntil(("<", "-", "\u0000"))
            self.tokenQueue.append({"type": tokenTypes["Characters"], "data":
                                    data + chars})
        return True

    def scriptDataEscapedDashState(self):
        data = self.stream.char()
        if data == "-":
            self.tokenQueue.append({"type": tokenTypes["Characters"], "data": "-"})
            self._state = self.scriptDataEscapedDashDashState
        elif data == "<":
            self._state = self.scriptDataEscapedLessThanSignState
        elif data == "\u0000":
            self.tokenQueue.append({"type": tokenTypes["ParseError"],
                                    "data": "invalid-codepoint"})
            self.tokenQueue.append({"type": tokenTypes["Characters"],
                                    "data": "\uFFFD"})
            self._state = self.scriptDataEscapedState
        elif data == EOF:
            self._state = self.dataState
        else:
            self.tokenQueue.append({"type": tokenTypes["Characters"], "data": data})
            self._state = self.scriptDataEscapedState
        return True

    def scriptDataEscapedDashDashState(self):
        data = self.stream.char()
        if data == "-":
            self.tokenQueue.append({"type": tokenTypes["Characters"], "data": "-"})
        elif data == "<":
            self._state = self.scriptDataEscapedLessThanSignState
        elif data == ">":
            self.tokenQueue.append({"type": tokenTypes["Characters"], "data": ">"})
            self._state = self.scriptDataState
        elif data == "\u0000":
            self.tokenQueue.append({"type": tokenTypes["ParseError"],
                                    "data": "invalid-codepoint"})
            self.tokenQueue.append({"type": tokenTypes["Characters"],
                                    "data": "\uFFFD"})
            self._state = self.scriptDataEscapedState
        elif data == EOF:
            self._state = self.dataState
        else:
            self.tokenQueue.append({"type": tokenTypes["Characters"], "data": data})
            self._state = self.scriptDataEscapedState
        return True

    def scriptDataEscapedLessThanSignState(self):
        data = self.stream.char()
        if data == "/":
            self.temporaryBuffer = ""
            self._state = self.scriptDataEscapedEndTagOpenState
        elif data in asciiLetters:
            self.tokenQueue.append({"type": tokenTypes["Characters"], "data": "<" + data})
            self.temporaryBuffer = data
            self._state = self.scriptDataDoubleEscapeStartState
        else:
            self.tokenQueue.append({"type": tokenTypes["Characters"], "data": "<"})
            self.stream.unget(data)
            self._state = self.scriptDataEscapedState
        return True

    def scriptDataEscapedEndTagOpenState(self):
        data = self.stream.char()
        if data in asciiLetters:
            self.temporaryBuffer = data
            self._state = self.scriptDataEscapedEndTagNameState
        else:
            self.tokenQueue.append({"type": tokenTypes["Characters"], "data": "</"})
            self.stream.unget(data)
            self._state = self.scriptDataEscapedState
        return True

    def scriptDataEscapedEndTagNameState(self):
        appropriate = self.currentToken and self.currentToken["name"].lower() == self.temporaryBuffer.lower()
        data = self.stream.char()
        if data in spaceCharacters and appropriate:
            self.currentToken = {"type": tokenTypes["EndTag"],
                                 "name": self.temporaryBuffer,
                                 "data": attributeMap(), "selfClosing": False}
            self._state = self.beforeAttributeNameState
        elif data == "/" and appropriate:
            self.currentToken = {"type": tokenTypes["EndTag"],
                                 "name": self.temporaryBuffer,
                                 "data": attributeMap(), "selfClosing": False}
            self._state = self.selfClosingStartTagState
        elif data == ">" and appropriate:
            self.currentToken = {"type": tokenTypes["EndTag"],
                                 "name": self.temporaryBuffer,
                                 "data": attributeMap(), "selfClosing": False}
            self.emitCurrentToken()
            self._state = self.dataState
        elif data in asciiLetters:
            self.temporaryBuffer += data
        else:
            self.tokenQueue.append({"type": tokenTypes["Characters"],
                                    "data": "</" + self.temporaryBuffer})
            self.stream.unget(data)
            self._state = self.scriptDataEscapedState
        return True

    def scriptDataDoubleEscapeStartState(self):
        data = self.stream.char()
        if data in (spaceCharacters | frozenset(("/", ">"))):
            self.tokenQueue.append({"type": tokenTypes["Characters"], "data": data})
            if self.temporaryBuffer.lower() == "script":
                self._state = self.scriptDataDoubleEscapedState
            else:
                self._state = self.scriptDataEscapedState
        elif data in asciiLetters:
            self.tokenQueue.append({"type": tokenTypes["Characters"], "data": data})
            self.temporaryBuffer += data
        else:
            self.stream.unget(data)
            self._state = self.scriptDataEscapedState
        return True

    def scriptDataDoubleEscapedState(self):
        data = self.stream.char()
        if data == "-":
            self.tokenQueue.append({"type": tokenTypes["Characters"], "data": "-"})
            self._state = self.scriptDataDoubleEscapedDashState
        elif data == "<":
            self.tokenQueue.append({"type": tokenTypes["Characters"], "data": "<"})
            self._state = self.scriptDataDoubleEscapedLessThanSignState
        elif data == "\u0000":
            self.tokenQueue.append({"type": tokenTypes["ParseError"],
                                    "data": "invalid-codepoint"})
            self.tokenQueue.append({"type": tokenTypes["Characters"],
                                    "data": "\uFFFD"})
        elif data == EOF:
            self.tokenQueue.append({"type": tokenTypes["ParseError"], "data":
                                    "eof-in-script-in-script"})
            self._state = self.dataState
        else:
            self.tokenQueue.append({"type": tokenTypes["Characters"], "data": data})
        return True

    def scriptDataDoubleEscapedDashState(self):
        data = self.stream.char()
        if data == "-":
            self.tokenQueue.append({"type": tokenTypes["Characters"], "data": "-"})
            self._state = self.scriptDataDoubleEscapedDashDashState
        elif data == "<":
            self.tokenQueue.append({"type": tokenTypes["Characters"], "data": "<"})
            self._state = self.scriptDataDoubleEscapedLessThanSignState
        elif data == "\u0000":
            self.tokenQueue.append({"type": tokenTypes["ParseError"],
                                    "data": "invalid-codepoint"})
            self.tokenQueue.append({"type": tokenTypes["Characters"],
                                    "data": "\uFFFD"})
            self._state = self.scriptDataDoubleEscapedState
        elif data == EOF:
            self.tokenQueue.append({"type": tokenTypes["ParseError"], "data":
                                    "eof-in-script-in-script"})
            self._state = self.dataState
        else:
            self.tokenQueue.append({"type": tokenTypes["Characters"], "data": data})
            self._state = self.scriptDataDoubleEscapedState
        return True

    def scriptDataDoubleEscapedDashDashState(self):
        data = self.stream.char()
        if data == "-":
            self.tokenQueue.append({"type": tokenTypes["Characters"], "data": "-"})
        elif data == "<":
            self.tokenQueue.append({"type": tokenTypes["Characters"], "data": "<"})
            self._state = self.scriptDataDoubleEscapedLessThanSignState
        elif data == ">":
            self.tokenQueue.append({"type": tokenTypes["Characters"], "data": ">"})
            self._state = self.scriptDataState
        elif data == "\u0000":
            self.tokenQueue.append({"type": tokenTypes["ParseError"],
                                    "data": "invalid-codepoint"})
            self.tokenQueue.append({"type": tokenTypes["Characters"],
                                    "data": "\uFFFD"})
            self._state = self.scriptDataDoubleEscapedState
        elif data == EOF:
            self.tokenQueue.append({"type": tokenTypes["ParseError"], "data":
                                    "eof-in-script-in-script"})
            self._state = self.dataState
        else:
            self.tokenQueue.append({"type": tokenTypes["Characters"], "data": data})
            self._state = self.scriptDataDoubleEscapedState
        return True

    def scriptDataDoubleEscapedLessThanSignState(self):
        data = self.stream.char()
        if data == "/":
            self.tokenQueue.append({"type": tokenTypes["Characters"], "data": "/"})
            self.temporaryBuffer = ""
            self._state = self.scriptDataDoubleEscapeEndState
        else:
            self.stream.unget(data)
            self._state = self.scriptDataDoubleEscapedState
        return True

    def scriptDataDoubleEscapeEndState(self):
        data = self.stream.char()
        if data in (spaceCharacters | frozenset(("/", ">"))):
            self.tokenQueue.append({"type": tokenTypes["Characters"], "data": data})
            if self.temporaryBuffer.lower() == "script":
                self._state = self.scriptDataEscapedState
            else:
                self._state = self.scriptDataDoubleEscapedState
        elif data in asciiLetters:
            self.tokenQueue.append({"type": tokenTypes["Characters"], "data": data})
            self.temporaryBuffer += data
        else:
            self.stream.unget(data)
            self._state = self.scriptDataDoubleEscapedState
        return True

    def beforeAttributeNameState(self):
        data = self.stream.char()
        if data in spaceCharacters:
            self.stream.charsUntil(spaceCharacters, True)
        elif data in asciiLetters:
            self.currentAttribute = data
            self._state = self.attributeNameState
        elif data == ">":
            self.emitCurrentToken()
        elif data == "/":
            self._state = self.selfClosingStartTagState
        elif data in ("'", '"', "=", "<"):
            self.tokenQueue.append({"type": tokenTypes["ParseError"], "data":
                                    "invalid-character-in-attribute-name"})
            self.currentAttribute = data
            self._state = self.attributeNameState
        elif data == "\u0000":
            self.tokenQueue.append({"type": tokenTypes["ParseError"],
                                    "data": "invalid-codepoint"})
            self.currentAttribute = "\uFFFD"
            self._state = self.attributeNameState
        elif data is EOF:
            self.tokenQueue.append({"type": tokenTypes["ParseError"], "data":
                                    "expected-attribute-name-but-got-eof"})
            self._state = self.dataState
        else:
            self.currentAttribute = data
            self._state = self.attributeNameState
        return True

    def attributeNameState(self):
        data = self.stream.char()
        leavingThisState = True
        emitToken = False
        if data == "=":
            self._state = self.beforeAttributeValueState
        elif data in asciiLetters:
            self.currentAttribute += data +\
                self.stream.charsUntil(asciiLetters, True)
            leavingThisState = False
        elif data == ">":
            # XXX If we emit here the attributes are converted to a dict
            # without being checked and when the code below runs we error
            # because data is a dict not a list
            emitToken = True
        elif data in spaceCharacters:
            self._state = self.afterAttributeNameState
        elif data == "/":
            self._state = self.selfClosingStartTagState
        elif data == "\u0000":
            self.tokenQueue.append({"type": tokenTypes["ParseError"],
                                    "data": "invalid-codepoint"})
            self.currentAttribute += "\uFFFD"
            leavingThisState = False
        elif data in ("'", '"', "<"):
            self.tokenQueue.append({"type": tokenTypes["ParseError"],
                                    "data":
                                    "invalid-character-in-attribute-name"})
            self.currentAttribute += data
            leavingThisState = False
        elif data is EOF:
            self.tokenQueue.append({"type": tokenTypes["ParseError"],
                                    "data": "eof-in-attribute-name"})
            self._state = self.dataState
        else:
            self.currentAttribute += data
            leavingThisState = False

        assert leavingThisState == ((self._state != self.attributeNameState) or emitToken)
        if leavingThisState:
            # Attributes are not dropped at this stage. That happens when the
            # start tag token is emitted so values can still be safely appended
            # to attributes, but we do want to report the parse error in time.
            self.currentAttribute = ascii_lower(self.currentAttribute)
            if self.currentAttribute in self.currentToken["data"]:
                self.tokenQueue.append({"type": tokenTypes["ParseError"],
                                        "data": "duplicate-attribute"})
                self.currentToken["data"][self.currentAttribute].append("")
            else:
                self.currentToken["data"][self.currentAttribute] = [""]
            # XXX Fix for above XXX
            if emitToken:
                self.emitCurrentToken()
        return True

    def afterAttributeNameState(self):
        data = self.stream.char()
        if data in spaceCharacters:
            self.stream.charsUntil(spaceCharacters, True)
        elif data == "=":
            self._state = self.beforeAttributeValueState
        elif data == ">":
            self.emitCurrentToken()
        elif data in asciiLetters:
            self.currentAttribute = data
            self._state = self.attributeNameState
        elif data == "/":
            self._state = self.selfClosingStartTagState
        elif data == "\u0000":
            self.tokenQueue.append({"type": tokenTypes["ParseError"],
                                    "data": "invalid-codepoint"})
            self.currentAttribute = "\uFFFD"
            self._state = self.attributeNameState
        elif data in ("'", '"', "<"):
            self.tokenQueue.append({"type": tokenTypes["ParseError"], "data":
                                    "invalid-character-after-attribute-name"})
            self.currentAttribute = data
            self._state = self.attributeNameState
        elif data is EOF:
            self.tokenQueue.append({"type": tokenTypes["ParseError"], "data":
                                    "expected-end-of-tag-but-got-eof"})
            self._state = self.dataState
        else:
            self.currentAttribute = data
            self._state = self.attributeNameState
        return True

    def beforeAttributeValueState(self):
        data = self.stream.char()
        if data in spaceCharacters:
            self.stream.charsUntil(spaceCharacters, True)
        elif data == "\"":
            self._state = self.attributeValueDoubleQuotedState
        elif data == "&":
            self._state = self.attributeValueUnQuotedState
            self.stream.unget(data)
        elif data == "'":
            self._state = self.attributeValueSingleQuotedState
        elif data == ">":
            self.tokenQueue.append({"type": tokenTypes["ParseError"], "data":
                                    "expected-attribute-value-but-got-right-bracket"})
            self.emitCurrentToken()
        elif data == "\u0000":
            self.tokenQueue.append({"type": tokenTypes["ParseError"],
                                    "data": "invalid-codepoint"})
            self.currentToken["data"][self.currentAttribute][-1] += "\uFFFD"
            self._state = self.attributeValueUnQuotedState
        elif data in ("=", "<", "`"):
            self.tokenQueue.append({"type": tokenTypes["ParseError"], "data":
                                    "equals-in-unquoted-attribute-value"})
            self.currentToken["data"][self.currentAttribute][-1] += data
            self._state = self.attributeValueUnQuotedState
        elif data is EOF:
            self.tokenQueue.append({"type": tokenTypes["ParseError"], "data":
                                    "expected-attribute-value-but-got-eof"})
            self._state = self.dataState
        else:
            self.currentToken["data"][self.currentAttribute][-1] += data
            self._state = self.attributeValueUnQuotedState
        return True

    def attributeValueDoubleQuotedState(self):
        data = self.stream.char()
        if data == "\"":
            self._state = self.afterAttributeValueState
        elif data == "&":
            self.processEntityInAttribute('"')
        elif data == "\u0000":
            self.tokenQueue.append({"type": tokenTypes["ParseError"],
                                    "data": "invalid-codepoint"})
            self.currentToken["data"][self.currentAttribute][-1] += "\uFFFD"
        elif data is EOF:
            self.tokenQueue.append({"type": tokenTypes["ParseError"], "data":
                                    "eof-in-attribute-value-double-quote"})
            self._state = self.dataState
        else:
            self.currentToken["data"][self.currentAttribute][-1] += data +\
                self.stream.charsUntil(("\"", "&", "\u0000"))
        return True

    def attributeValueSingleQuotedState(self):
        data = self.stream.char()
        if data == "'":
            self._state = self.afterAttributeValueState
        elif data == "&":
            self.processEntityInAttribute("'")
        elif data == "\u0000":
            self.tokenQueue.append({"type": tokenTypes["ParseError"],
                                    "data": "invalid-codepoint"})
            self.currentToken["data"][self.currentAttribute][-1] += "\uFFFD"
        elif data is EOF:
            self.tokenQueue.append({"type": tokenTypes["ParseError"], "data":
                                    "eof-in-attribute-value-single-quote"})
            self._state = self.dataState
        else:
            self.currentToken["data"][self.currentAttribute][-1] += data +\
                self.stream.charsUntil(("'", "&", "\u0000"))
        return True

    def attributeValueUnQuotedState(self):
        data = self.stream.char()
        if data in spaceCharacters:
            self._state = self.beforeAttributeNameState
        elif data == "&":
            self.processEntityInAttribute(">")
        elif data == ">":
            self.emitCurrentToken()
        elif data in ('"', "'", "=", "<", "`"):
            self.tokenQueue.append({"type": tokenTypes["ParseError"], "data":
                                    "unexpected-character-in-unquoted-attribute-value"})
            self.currentToken["data"][self.currentAttribute][-1] += data
        elif data == "\u0000":
            self.tokenQueue.append({"type": tokenTypes["ParseError"],
                                    "data": "invalid-codepoint"})
            self.currentToken["data"][self.currentAttribute][-1] += "\uFFFD"
        elif data is EOF:
            self.tokenQueue.append({"type": tokenTypes["ParseError"], "data":
                                    "eof-in-attribute-value-no-quotes"})
            self._state = self.dataState
        else:
            self.currentToken["data"][self.currentAttribute][-1] += data + self.stream.charsUntil(
                frozenset(("&", ">", '"', "'", "=", "<", "`", "\u0000")) | spaceCharacters)
        return True

    def afterAttributeValueState(self):
        data = self.stream.char()
        if data in spaceCharacters:
            self._state = self.beforeAttributeNameState
        elif data == ">":
            self.emitCurrentToken()
        elif data == "/":
            self._state = self.selfClosingStartTagState
        elif data is EOF:
            self.tokenQueue.append({"type": tokenTypes["ParseError"], "data":
                                    "unexpected-EOF-after-attribute-value"})
            self.stream.unget(data)
            self._state = self.dataState
        else:
            self.tokenQueue.append({"type": tokenTypes["ParseError"], "data":
                                    "unexpected-character-after-attribute-value"})
            self.stream.unget(data)
            self._state = self.beforeAttributeNameState
        return True

    def selfClosingStartTagState(self):
        data = self.stream.char()
        if data == ">":
            self.currentToken["selfClosing"] = True
            self.emitCurrentToken()
        elif data is EOF:
            self.tokenQueue.append({"type": tokenTypes["ParseError"],
                                    "data":
                                    "unexpected-EOF-after-solidus-in-tag"})
            self.stream.unget(data)
            self._state = self.dataState
        else:
            self.tokenQueue.append({"type": tokenTypes["ParseError"], "data":
                                    "unexpected-character-after-solidus-in-tag"})
            self.stream.unget(data)
            self._state = self.beforeAttributeNameState
        return True

    def bogusCommentState(self):
        # Make a new comment token and give it as value all the characters
        # until the first > or EOF (charsUntil checks for EOF automatically)
        # and emit it.
        data = self.stream.charsUntil(">")
        data = data.replace("\u0000", "\uFFFD")
        self.tokenQueue.append(
            {"type": tokenTypes["Comment"], "data": data})

        # Eat the character directly after the bogus comment which is either a
        # ">" or an EOF.
        self.stream.char()
        self._state = self.dataState
        return True

    def markupDeclarationOpenState(self):
        charStack = [self.stream.char()]
        if charStack[-1] == "-":
            charStack.append(self.stream.char())
            if charStack[-1] == "-":
                self.currentToken = {"type": tokenTypes["Comment"], "data": ""}
                self._state = self.commentStartState
                return True
        elif charStack[-1] in ('d', 'D'):
            matched = True
            for expected in (('o', 'O'), ('c', 'C'), ('t', 'T'),
                             ('y', 'Y'), ('p', 'P'), ('e', 'E')):
                charStack.append(self.stream.char())
                if charStack[-1] not in expected:
                    matched = False
                    break
            if matched:
                self.currentToken = {"type": tokenTypes["Doctype"],
                                     "name": "",
                                     "publicId": None, "systemId": None,
                                     "correct": True}
                self._state = self.doctypeState
                return True
        elif (charStack[-1] == "[" and
              self.parser is not None and
              self.parser.tree.openElements and
              self.parser.tree.openElements[-1].namespace != self.parser.tree.defaultNamespace):
            matched = True
            for expected in ["C", "D", "A", "T", "A", "["]:
                charStack.append(self.stream.char())
                if charStack[-1] != expected:
                    matched = False
                    break
            if matched:
                self._state = self.cdataSectionState
                return True

        self.tokenQueue.append({"type": tokenTypes["ParseError"], "data":
                                "expected-dashes-or-doctype"})

        while charStack:
            self.stream.unget(charStack.pop())
        self._state = self.bogusCommentState
        return True

    def commentStartState(self):
        data = self.stream.char()
        if data == "-":
            self._state = self.commentStartDashState
        elif data == "\u0000":
            self.tokenQueue.append({"type": tokenTypes["ParseError"],
                                    "data": "invalid-codepoint"})
            self.currentToken["data"] += "\uFFFD"
        elif data == ">":
            self.tokenQueue.append({"type": tokenTypes["ParseError"], "data":
                                    "incorrect-comment"})
            self.tokenQueue.append(self.currentToken)
            self._state = self.dataState
        elif data is EOF:
            self.tokenQueue.append({"type": tokenTypes["ParseError"], "data":
                                    "eof-in-comment"})
            self.tokenQueue.append(self.currentToken)
            self._state = self.dataState
        else:
            self.currentToken["data"] += data
            self._state = self.commentState
        return True

    def commentStartDashState(self):
        data = self.stream.char()
        if data == "-":
            self._state = self.commentEndState
        elif data == "\u0000":
            self.tokenQueue.append({"type": tokenTypes["ParseError"],
                                    "data": "invalid-codepoint"})
            self.currentToken["data"] += "-\uFFFD"
        elif data == ">":
            self.tokenQueue.append({"type": tokenTypes["ParseError"], "data":
                                    "incorrect-comment"})
            self.tokenQueue.append(self.currentToken)
            self._state = self.dataState
        elif data is EOF:
            self.tokenQueue.append({"type": tokenTypes["ParseError"], "data":
                                    "eof-in-comment"})
            self.tokenQueue.append(self.currentToken)
            self._state = self.dataState
        else:
            self.currentToken["data"] += "-" + data
            self._state = self.commentState
        return True

    def commentState(self):
        data = self.stream.char()
        if data == "-":
            self._state = self.commentEndDashState
        elif data == "\u0000":
            self.tokenQueue.append({"type": tokenTypes["ParseError"],
                                    "data": "invalid-codepoint"})
            self.currentToken["data"] += "\uFFFD"
        elif data is EOF:
            self.tokenQueue.append({"type": tokenTypes["ParseError"],
                                    "data": "eof-in-comment"})
            self.tokenQueue.append(self.currentToken)
            self._state = self.dataState
        else:
            self.currentToken["data"] += data + \
                self.stream.charsUntil(("-", "\u0000"))
        return True

    def commentEndDashState(self):
        data = self.stream.char()
        if data == "-":
            self._state = self.commentEndState
        elif data == "\u0000":
            self.tokenQueue.append({"type": tokenTypes["ParseError"],
                                    "data": "invalid-codepoint"})
            self.currentToken["data"] += "-\uFFFD"
            self._state = self.commentState
        elif data is EOF:
            self.tokenQueue.append({"type": tokenTypes["ParseError"], "data":
                                    "eof-in-comment-end-dash"})
            self.tokenQueue.append(self.currentToken)
            self._state = self.dataState
        else:
            self.currentToken["data"] += "-" + data
            self._state = self.commentState
        return True

    def commentEndState(self):
        data = self.stream.char()
        if data == ">":
            self.tokenQueue.append(self.currentToken)
            self._state = self.dataState
        elif data == "\u0000":
            self.tokenQueue.append({"type": tokenTypes["ParseError"],
                                    "data": "invalid-codepoint"})
            self.currentToken["data"] += "--\uFFFD"
            self._state = self.commentState
        elif data == "!":
            self.tokenQueue.append({"type": tokenTypes["ParseError"], "data":
                                    "unexpected-bang-after-double-dash-in-comment"})
            self._state = self.commentEndBangState
        elif data == "-":
            self.tokenQueue.append({"type": tokenTypes["ParseError"], "data":
                                    "unexpected-dash-after-double-dash-in-comment"})
            self.currentToken["data"] += data
        elif data is EOF:
            self.tokenQueue.append({"type": tokenTypes["ParseError"], "data":
                                    "eof-in-comment-double-dash"})
            self.tokenQueue.append(self.currentToken)
            self._state = self.dataState
        else:
            # XXX
            self.tokenQueue.append({"type": tokenTypes["ParseError"], "data":
                                    "unexpected-char-in-comment"})
            self.currentToken["data"] += "--" + data
            self._state = self.commentState
        return True

    def commentEndBangState(self):
        data = self.stream.char()
        if data == ">":
            self.tokenQueue.append(self.currentToken)
            self._state = self.dataState
        elif data == "-":
            self.currentToken["data"] += "--!"
            self._state = self.commentEndDashState
        elif data == "\u0000":
            self.tokenQueue.append({"type": tokenTypes["ParseError"],
                                    "data": "invalid-codepoint"})
            self.currentToken["data"] += "--!\uFFFD"
            self._state = self.commentState
        elif data is EOF:
            self.tokenQueue.append({"type": tokenTypes["ParseError"], "data":
                                    "eof-in-comment-end-bang-state"})
            self.tokenQueue.append(self.currentToken)
            self._state = self.dataState
        else:
            self.currentToken["data"] += "--!" + data
            self._state = self.commentState
        return True

    def doctypeState(self):
        data = self.stream.char()
        if data in spaceCharacters:
            self._state = self.beforeDoctypeNameState
        elif data is EOF:
            self.tokenQueue.append({"type": tokenTypes["ParseError"], "data":
                                    "expected-doctype-name-but-got-eof"})
            self.currentToken["correct"] = False
            self.tokenQueue.append(self.currentToken)
            self._state = self.dataState
        else:
            self.tokenQueue.append({"type": tokenTypes["ParseError"], "data":
                                    "need-space-after-doctype"})
            self.stream.unget(data)
            self._state = self.beforeDoctypeNameState
        return True

    def beforeDoctypeNameState(self):
        data = self.stream.char()
        if data in spaceCharacters:
            pass
        elif data == ">":
            self.tokenQueue.append({"type": tokenTypes["ParseError"], "data":
                                    "expected-doctype-name-but-got-right-bracket"})
            self.currentToken["correct"] = False
            self.tokenQueue.append(self.currentToken)
            self._state = self.dataState
        elif data == "\u0000":
            self.tokenQueue.append({"type": tokenTypes["ParseError"],
                                    "data": "invalid-codepoint"})
            self.currentToken["name"] = "\uFFFD"
            self._state = self.doctypeNameState
        elif data is EOF:
            self.tokenQueue.append({"type": tokenTypes["ParseError"], "data":
                                    "expected-doctype-name-but-got-eof"})
            self.currentToken["correct"] = False
            self.tokenQueue.append(self.currentToken)
            self._state = self.dataState
        else:
            self.currentToken["name"] = data
            self._state = self.doctypeNameState
        return True

    def doctypeNameState(self):
        data = self.stream.char()
        if data in spaceCharacters:
            self.currentToken["name"] = ascii_lower(self.currentToken["name"])
            self._state = self.afterDoctypeNameState
        elif data == ">":
            self.currentToken["name"] = ascii_lower(self.currentToken["name"])
            self.tokenQueue.append(self.currentToken)
            self._state = self.dataState
        elif data == "\u0000":
            self.tokenQueue.append({"type": tokenTypes["ParseError"],
                                    "data": "invalid-codepoint"})
            self.currentToken["name"] += "\uFFFD"
            self._state = self.doctypeNameState
        elif data is EOF:
            self.tokenQueue.append({"type": tokenTypes["ParseError"], "data":
                                    "eof-in-doctype-name"})
            self.currentToken["correct"] = False
            self.currentToken["name"] = ascii_lower(self.currentToken["name"])
            self.tokenQueue.append(self.currentToken)
            self._state = self.dataState
        else:
            self.currentToken["name"] += data
        return True

    def afterDoctypeNameState(self):
        data = self.stream.char()
        if data in spaceCharacters:
            pass
        elif data == ">":
            self.tokenQueue.append(self.currentToken)
            self._state = self.dataState
        elif data is EOF:
            self.currentToken["correct"] = False
            self.stream.unget(data)
            self.tokenQueue.append({"type": tokenTypes["ParseError"], "data":
                                    "eof-in-doctype"})
            self.tokenQueue.append(self.currentToken)
            self._state = self.dataState
        else:
            if data in ("p", "P"):
                matched = True
                for expected in (("u", "U"), ("b", "B"), ("l", "L"),
                                 ("i", "I"), ("c", "C")):
                    data = self.stream.char()
                    if data not in expected:
                        matched = False
                        break
                if matched:
                    self._state = self.afterDoctypePublicKeywordState
                    return True
            elif data in ("s", "S"):
                matched = True
                for expected in (("y", "Y"), ("s", "S"), ("t", "T"),
                                 ("e", "E"), ("m", "M")):
                    data = self.stream.char()
                    if data not in expected:
                        matched = False
                        break
                if matched:
                    self._state = self.afterDoctypeSystemKeywordState
                    return True

            # All the characters read before the current 'data' will be
            # [a-zA-Z], so they're garbage in the bogus doctype and can be
            # discarded; only the latest character might be '>' or EOF
            # and needs to be ungetted
            self.stream.unget(data)
            self.tokenQueue.append({"type": tokenTypes["ParseError"], "data":
                                    "expected-space-or-right-bracket-in-doctype", "datavars":
                                    {"data": data}})
            self.currentToken["correct"] = False
            self._state = self.bogusDoctypeState

        return True

    def afterDoctypePublicKeywordState(self):
        data = self.stream.char()
        if data in spaceCharacters:
            self._state = self.beforeDoctypePublicIdentifierState
        elif data in ("'", '"'):
            self.tokenQueue.append({"type": tokenTypes["ParseError"], "data":
                                    "unexpected-char-in-doctype"})
            self.stream.unget(data)
            self._state = self.beforeDoctypePublicIdentifierState
        elif data is EOF:
            self.tokenQueue.append({"type": tokenTypes["ParseError"], "data":
                                    "eof-in-doctype"})
            self.currentToken["correct"] = False
            self.tokenQueue.append(self.currentToken)
            self._state = self.dataState
        else:
            self.stream.unget(data)
            self._state = self.beforeDoctypePublicIdentifierState
        return True

    def beforeDoctypePublicIdentifierState(self):
        data = self.stream.char()
        if data in spaceCharacters:
            pass
        elif data == "\"":
            self.currentToken["publicId"] = ""
            self._state = self.doctypePublicIdentifierDoubleQuotedState
        elif data == "'":
            self.currentToken["publicId"] = ""
            self._state = self.doctypePublicIdentifierSingleQuotedState
        elif data == ">":
            self.tokenQueue.append({"type": tokenTypes["ParseError"], "data":
                                    "unexpected-end-of-doctype"})
            self.currentToken["correct"] = False
            self.tokenQueue.append(self.currentToken)
            self._state = self.dataState
        elif data is EOF:
            self.tokenQueue.append({"type": tokenTypes["ParseError"], "data":
                                    "eof-in-doctype"})
            self.currentToken["correct"] = False
            self.tokenQueue.append(self.currentToken)
            self._state = self.dataState
        else:
            self.tokenQueue.append({"type": tokenTypes["ParseError"], "data":
                                    "unexpected-char-in-doctype"})
            self.currentToken["correct"] = False
            self._state = self.bogusDoctypeState
        return True

    def doctypePublicIdentifierDoubleQuotedState(self):
        data = self.stream.char()
        if data == "\"":
            self._state = self.afterDoctypePublicIdentifierState
        elif data == "\u0000":
            self.tokenQueue.append({"type": tokenTypes["ParseError"],
                                    "data": "invalid-codepoint"})
            self.currentToken["publicId"] += "\uFFFD"
        elif data == ">":
            self.tokenQueue.append({"type": tokenTypes["ParseError"], "data":
                                    "unexpected-end-of-doctype"})
            self.currentToken["correct"] = False
            self.tokenQueue.append(self.currentToken)
            self._state = self.dataState
        elif data is EOF:
            self.tokenQueue.append({"type": tokenTypes["ParseError"], "data":
                                    "eof-in-doctype"})
            self.currentToken["correct"] = False
            self.tokenQueue.append(self.currentToken)
            self._state = self.dataState
        else:
            self.currentToken["publicId"] += data
        return True

    def doctypePublicIdentifierSingleQuotedState(self):
        data = self.stream.char()
        if data == "'":
            self._state = self.afterDoctypePublicIdentifierState
        elif data == "\u0000":
            self.tokenQueue.append({"type": tokenTypes["ParseError"],
                                    "data": "invalid-codepoint"})
            self.currentToken["publicId"] += "\uFFFD"
        elif data == ">":
            self.tokenQueue.append({"type": tokenTypes["ParseError"], "data":
                                    "unexpected-end-of-doctype"})
            self.currentToken["correct"] = False
            self.tokenQueue.append(self.currentToken)
            self._state = self.dataState
        elif data is EOF:
            self.tokenQueue.append({"type": tokenTypes["ParseError"], "data":
                                    "eof-in-doctype"})
            self.currentToken["correct"] = False
            self.tokenQueue.append(self.currentToken)
            self._state = self.dataState
        else:
            self.currentToken["publicId"] += data
        return True

    def afterDoctypePublicIdentifierState(self):
        data = self.stream.char()
        if data in spaceCharacters:
            self._state = self.betweenDoctypePublicAndSystemIdentifiersState
        elif data == ">":
            self.tokenQueue.append(self.currentToken)
            self._state = self.dataState
        elif data == '"':
            self.tokenQueue.append({"type": tokenTypes["ParseError"], "data":
                                    "unexpected-char-in-doctype"})
            self.currentToken["systemId"] = ""
            self._state = self.doctypeSystemIdentifierDoubleQuotedState
        elif data == "'":
            self.tokenQueue.append({"type": tokenTypes["ParseError"], "data":
                                    "unexpected-char-in-doctype"})
            self.currentToken["systemId"] = ""
            self._state = self.doctypeSystemIdentifierSingleQuotedState
        elif data is EOF:
            self.tokenQueue.append({"type": tokenTypes["ParseError"], "data":
                                    "eof-in-doctype"})
            self.currentToken["correct"] = False
            self.tokenQueue.append(self.currentToken)
            self._state = self.dataState
        else:
            self.tokenQueue.append({"type": tokenTypes["ParseError"], "data":
                                    "unexpected-char-in-doctype"})
            self.currentToken["correct"] = False
            self._state = self.bogusDoctypeState
        return True

    def betweenDoctypePublicAndSystemIdentifiersState(self):
        data = self.stream.char()
        if data in spaceCharacters:
            pass
        elif data == ">":
            self.tokenQueue.append(self.currentToken)
            self._state = self.dataState
        elif data == '"':
            self.currentToken["systemId"] = ""
            self._state = self.doctypeSystemIdentifierDoubleQuotedState
        elif data == "'":
            self.currentToken["systemId"] = ""
            self._state = self.doctypeSystemIdentifierSingleQuotedState
        elif data == EOF:
            self.tokenQueue.append({"type": tokenTypes["ParseError"], "data":
                                    "eof-in-doctype"})
            self.currentToken["correct"] = False
            self.tokenQueue.append(self.currentToken)
            self._state = self.dataState
        else:
            self.tokenQueue.append({"type": tokenTypes["ParseError"], "data":
                                    "unexpected-char-in-doctype"})
            self.currentToken["correct"] = False
            self._state = self.bogusDoctypeState
        return True

    def afterDoctypeSystemKeywordState(self):
        data = self.stream.char()
        if data in spaceCharacters:
            self._state = self.beforeDoctypeSystemIdentifierState
        elif data in ("'", '"'):
            self.tokenQueue.append({"type": tokenTypes["ParseError"], "data":
                                    "unexpected-char-in-doctype"})
            self.stream.unget(data)
            self._state = self.beforeDoctypeSystemIdentifierState
        elif data is EOF:
            self.tokenQueue.append({"type": tokenTypes["ParseError"], "data":
                                    "eof-in-doctype"})
            self.currentToken["correct"] = False
            self.tokenQueue.append(self.currentToken)
            self._state = self.dataState
        else:
            self.stream.unget(data)
            self._state = self.beforeDoctypeSystemIdentifierState
        return True

    def beforeDoctypeSystemIdentifierState(self):
        data = self.stream.char()
        if data in spaceCharacters:
            pass
        elif data == "\"":
            self.currentToken["systemId"] = ""
            self._state = self.doctypeSystemIdentifierDoubleQuotedState
        elif data == "'":
            self.currentToken["systemId"] = ""
            self._state = self.doctypeSystemIdentifierSingleQuotedState
        elif data == ">":
            self.tokenQueue.append({"type": tokenTypes["ParseError"], "data":
                                    "unexpected-char-in-doctype"})
            self.currentToken["correct"] = False
            self.tokenQueue.append(self.currentToken)
            self._state = self.dataState
        elif data is EOF:
            self.tokenQueue.append({"type": tokenTypes["ParseError"], "data":
                                    "eof-in-doctype"})
            self.currentToken["correct"] = False
            self.tokenQueue.append(self.currentToken)
            self._state = self.dataState
        else:
            self.tokenQueue.append({"type": tokenTypes["ParseError"], "data":
                                    "unexpected-char-in-doctype"})
            self.currentToken["correct"] = False
            self._state = self.bogusDoctypeState
        return True

    def doctypeSystemIdentifierDoubleQuotedState(self):
        data = self.stream.char()
        if data == "\"":
            self._state = self.afterDoctypeSystemIdentifierState
        elif data == "\u0000":
            self.tokenQueue.append({"type": tokenTypes["ParseError"],
                                    "data": "invalid-codepoint"})
            self.currentToken["systemId"] += "\uFFFD"
        elif data == ">":
            self.tokenQueue.append({"type": tokenTypes["ParseError"], "data":
                                    "unexpected-end-of-doctype"})
            self.currentToken["correct"] = False
            self.tokenQueue.append(self.currentToken)
            self._state = self.dataState
        elif data is EOF:
            self.tokenQueue.append({"type": tokenTypes["ParseError"], "data":
                                    "eof-in-doctype"})
            self.currentToken["correct"] = False
            self.tokenQueue.append(self.currentToken)
            self._state = self.dataState
        else:
            self.currentToken["systemId"] += data
        return True

    def doctypeSystemIdentifierSingleQuotedState(self):
        data = self.stream.char()
        if data == "'":
            self._state = self.afterDoctypeSystemIdentifierState
        elif data == "\u0000":
            self.tokenQueue.append({"type": tokenTypes["ParseError"],
                                    "data": "invalid-codepoint"})
            self.currentToken["systemId"] += "\uFFFD"
        elif data == ">":
            self.tokenQueue.append({"type": tokenTypes["ParseError"], "data":
                                    "unexpected-end-of-doctype"})
            self.currentToken["correct"] = False
            self.tokenQueue.append(self.currentToken)
            self._state = self.dataState
        elif data is EOF:
            self.tokenQueue.append({"type": tokenTypes["ParseError"], "data":
                                    "eof-in-doctype"})
            self.currentToken["correct"] = False
            self.tokenQueue.append(self.currentToken)
            self._state = self.dataState
        else:
            self.currentToken["systemId"] += data
        return True

    def afterDoctypeSystemIdentifierState(self):
        data = self.stream.char()
        if data in spaceCharacters:
            pass
        elif data == ">":
            self.tokenQueue.append(self.currentToken)
            self._state = self.dataState
        elif data is EOF:
            self.tokenQueue.append({"type": tokenTypes["ParseError"], "data":
                                    "eof-in-doctype"})
            self.currentToken["correct"] = False
            self.tokenQueue.append(self.currentToken)
            self._state = self.dataState
        else:
            self.tokenQueue.append({"type": tokenTypes["ParseError"], "data":
                                    "unexpected-char-in-doctype"})
            self._state = self.bogusDoctypeState
        return True

    def bogusDoctypeState(self):
        data = self.stream.char()
        if data == ">":
            self.tokenQueue.append(self.currentToken)
            self._state = self.dataState
        elif data is EOF:
            # XXX EMIT
            self.stream.unget(data)
            self.tokenQueue.append(self.currentToken)
            self._state = self.dataState
        else:
            pass
        return True

    def cdataSectionState(self):
        data = []
        while True:
            data.append(self.stream.charsUntil("]"))
            data.append(self.stream.charsUntil(">"))
            char = self.stream.char()
            if char == EOF:
                break
            else:
                assert char == ">"
                if data[-1][-2:] == "]]":
                    data[-1] = data[-1][:-2]
                    break
                else:
                    data.append(char)

        data = "".join(data)  # pylint:disable=redefined-variable-type
        # Deal with null here rather than in the parser
        nullCount = data.count("\u0000")
        if nullCount > 0:
            for _ in range(nullCount):
                self.tokenQueue.append({"type": tokenTypes["ParseError"],
                                        "data": "invalid-codepoint"})
            data = data.replace("\u0000", "\uFFFD")
        if data:
            self.tokenQueue.append({"type": tokenTypes["Characters"],
                                    "data": data})
        self._state = self.dataState
        return True
