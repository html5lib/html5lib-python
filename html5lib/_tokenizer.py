from __future__ import absolute_import, division, unicode_literals

from six import unichr as chr

from collections import deque, OrderedDict
from sys import version_info

from .constants import spaceCharacters
from .constants import entities
from .constants import asciiLetters, asciiUpper2Lower
from .constants import digits, hexDigits, EOF
from .constants import replacementCharacters

from ._inputstream import HTMLInputStream

from ._trie import Trie

entitiesTrie = Trie(entities)

if version_info >= (3, 7):
    attributeMap = dict
else:
    attributeMap = OrderedDict


class Token(object):
    def __init__(self, data=None):
        self.data = data


class Doctype(Token):
    def __init__(self, name, public_id, system_id, correct):
        self.name = name
        self.public_id = public_id
        self.system_id = system_id
        self.correct = correct

class Characters(Token):
    pass

class SpaceCharacters(Token):
    pass


class Tag(Token):
    def __init__(self, name, attributes):
        self.name = name
        self.attributes = attributeMap(attributes or {})
        self.self_closing = False
        self.attribute_name = ""
        self.attribute_value = ""

    def clearAttribute(self):
        if self.attribute_name and self.attribute_name not in self.attributes:
            self.attributes[self.attribute_name] = self.attribute_value
        self.attribute_name = ""
        self.attribute_value = ""

    def accumulateAttributeName(self, text):
        self.attribute_name += text.translate(asciiUpper2Lower)

    def accumulateAttributeValue(self, text):
        self.attribute_value += text

class StartTag(Tag):
    def __init__(self, name, data=None):
        super(StartTag, self).__init__(name, data)
        self.self_closing_acknowledged = False

class EndTag(Tag):
    def __init__(self, name, data=None):
        super(EndTag, self).__init__(name, data)

class EmptyTag(Tag):
    def __init__(self, name, data=None):
        super(EmptyTag, self).__init__(name, data)
        self.self_closing = True

class Comment(Token):
    pass

class ParseError(Token):
    def __init__(self, data, datavars=None):
        self.data = data
        self.datavars = datavars or {}


class HTMLTokenizer(object):
    """ This class takes care of tokenizing HTML.

    * self.currentToken
      Holds the token that is currently being processed.

    * self.state
      Holds a reference to the method to be invoked... XXX

    * self.stream
      Points to HTMLInputStream object.
    """

    def __init__(self, stream, parser=None, **kwargs):

        self.stream = HTMLInputStream(stream, **kwargs)
        self.parser = parser

        # Setup the initial tokenizer state
        self.escapeFlag = False
        self.lastFourChars = []
        self.state = self.dataState
        self.escape = False

        # The current token being created
        self.currentToken = None
        super(HTMLTokenizer, self).__init__()

    def __iter__(self):
        """ This is where the magic happens.

        We do our usually processing through the states and when we have a token
        to return we yield the token which pauses processing until the next token
        is requested.
        """
        self.tokenQueue = deque([])
        # Start processing. When EOF is reached self.state will return False
        # instead of True and the loop will terminate.
        while self.state():
            while self.stream.errors:
                yield ParseError(data=self.stream.errors.pop(0))
            while self.tokenQueue:
                yield self.tokenQueue.popleft()

    def consumeNumberEntity(self, isHex):
        """This function returns either U+FFFD or the character based on the
        decimal or hexadecimal representation. It also discards ";" if present.
        If not present self.tokenQueue.append(ParseError) is invoked.
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
        charAsInt = int("".join(charStack), radix)

        # Certain characters get replaced with others
        if charAsInt in replacementCharacters:
            char = replacementCharacters[charAsInt]
            self.tokenQueue.append(ParseError("illegal-codepoint-for-numeric-entity", {"charAsInt": charAsInt}))
        elif ((0xD800 <= charAsInt <= 0xDFFF) or
              (charAsInt > 0x10FFFF)):
            char = "\uFFFD"
            self.tokenQueue.append(ParseError("illegal-codepoint-for-numeric-entity", {"charAsInt": charAsInt}))
        else:
            # Should speed up this check somehow (e.g. move the set to a constant)
            if ((0x0001 <= charAsInt <= 0x0008) or
                (0x000E <= charAsInt <= 0x001F) or
                (0x007F <= charAsInt <= 0x009F) or
                (0xFDD0 <= charAsInt <= 0xFDEF) or
                charAsInt in frozenset([0x000B, 0xFFFE, 0xFFFF, 0x1FFFE,
                                        0x1FFFF, 0x2FFFE, 0x2FFFF, 0x3FFFE,
                                        0x3FFFF, 0x4FFFE, 0x4FFFF, 0x5FFFE,
                                        0x5FFFF, 0x6FFFE, 0x6FFFF, 0x7FFFE,
                                        0x7FFFF, 0x8FFFE, 0x8FFFF, 0x9FFFE,
                                        0x9FFFF, 0xAFFFE, 0xAFFFF, 0xBFFFE,
                                        0xBFFFF, 0xCFFFE, 0xCFFFF, 0xDFFFE,
                                        0xDFFFF, 0xEFFFE, 0xEFFFF, 0xFFFFE,
                                        0xFFFFF, 0x10FFFE, 0x10FFFF])):
                self.tokenQueue.append(ParseError("illegal-codepoint-for-numeric-entity", {"charAsInt": charAsInt}))
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
            self.tokenQueue.append(ParseError("numeric-entity-without-semicolon"))
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
                self.tokenQueue.append(ParseError("expected-numeric-entity"))
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
                    self.tokenQueue.append(ParseError("named-entity-without-semicolon"))
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
                self.tokenQueue.append(ParseError("expected-named-entity"))
                self.stream.unget(charStack.pop())
                output = "&" + "".join(charStack)

        if fromAttribute:
            self.currentToken.accumulateAttributeValue(output)
        else:
            if output in spaceCharacters:
                token = SpaceCharacters(output)
            else:
                token = Characters(output)
            self.tokenQueue.append(token)

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
        if isinstance(token, Tag):
            token.name = token.name.translate(asciiUpper2Lower)
            token.clearAttribute()
            if isinstance(token, EndTag):
                if token.attributes:
                    self.tokenQueue.append(ParseError("attributes-in-end-tag"))
                if token.self_closing:
                    self.tokenQueue.append(ParseError("self-closing-flag-on-end-tag"))
        self.tokenQueue.append(token)
        self.state = self.dataState

    # Below are the various tokenizer states worked out.
    def dataState(self):
        data = self.stream.char()
        if data == "&":
            self.state = self.entityDataState
        elif data == "<":
            self.state = self.tagOpenState
        elif data == "\u0000":
            self.tokenQueue.append(ParseError("invalid-codepoint"))
            self.tokenQueue.append(Characters("\u0000"))
        elif data is EOF:
            # Tokenization ends.
            return False
        elif data in spaceCharacters:
            # Directly after emitting a token you switch back to the "data
            # state". At that point spaceCharacters are important so they are
            # emitted separately.
            self.tokenQueue.append(SpaceCharacters(data + self.stream.charsUntil(spaceCharacters, True)))
            # No need to update lastFourChars here, since the first space will
            # have already been appended to lastFourChars and will have broken
            # any <!-- or --> sequences
        else:
            chars = self.stream.charsUntil(("&", "<", "\u0000"))
            self.tokenQueue.append(Characters(data + chars))
        return True

    def entityDataState(self):
        self.consumeEntity()
        self.state = self.dataState
        return True

    def rcdataState(self):
        data = self.stream.char()
        if data == "&":
            self.state = self.characterReferenceInRcdata
        elif data == "<":
            self.state = self.rcdataLessThanSignState
        elif data == EOF:
            # Tokenization ends.
            return False
        elif data == "\u0000":
            self.tokenQueue.append(ParseError("invalid-codepoint"))
            self.tokenQueue.append(Characters("\uFFFD"))
        elif data in spaceCharacters:
            # Directly after emitting a token you switch back to the "data
            # state". At that point spaceCharacters are important so they are
            # emitted separately.
            self.tokenQueue.append(SpaceCharacters(data + self.stream.charsUntil(spaceCharacters, True)))
            # No need to update lastFourChars here, since the first space will
            # have already been appended to lastFourChars and will have broken
            # any <!-- or --> sequences
        else:
            chars = self.stream.charsUntil(("&", "<", "\u0000"))
            self.tokenQueue.append(Characters(data + chars))
        return True

    def characterReferenceInRcdata(self):
        self.consumeEntity()
        self.state = self.rcdataState
        return True

    def rawtextState(self):
        data = self.stream.char()
        if data == "<":
            self.state = self.rawtextLessThanSignState
        elif data == "\u0000":
            self.tokenQueue.append(ParseError("invalid-codepoint"))
            self.tokenQueue.append(Characters("\uFFFD"))
        elif data == EOF:
            # Tokenization ends.
            return False
        else:
            chars = self.stream.charsUntil(("<", "\u0000"))
            self.tokenQueue.append(Characters(data + chars))
        return True

    def scriptDataState(self):
        data = self.stream.char()
        if data == "<":
            self.state = self.scriptDataLessThanSignState
        elif data == "\u0000":
            self.tokenQueue.append(ParseError("invalid-codepoint"))
            self.tokenQueue.append(Characters("\uFFFD"))
        elif data == EOF:
            # Tokenization ends.
            return False
        else:
            chars = self.stream.charsUntil(("<", "\u0000"))
            self.tokenQueue.append(Characters(data + chars))
        return True

    def plaintextState(self):
        data = self.stream.char()
        if data == EOF:
            # Tokenization ends.
            return False
        elif data == "\u0000":
            self.tokenQueue.append(ParseError("invalid-codepoint"))
            self.tokenQueue.append(Characters("\uFFFD"))
        else:
            self.tokenQueue.append(Characters(data + self.stream.charsUntil("\u0000")))
        return True

    def tagOpenState(self):
        data = self.stream.char()
        if data == "!":
            self.state = self.markupDeclarationOpenState
        elif data == "/":
            self.state = self.closeTagOpenState
        elif data in asciiLetters:
            self.currentToken = StartTag(name=data)
            self.state = self.tagNameState
        elif data == ">":
            # XXX In theory it could be something besides a tag name. But
            # do we really care?
            self.tokenQueue.append(ParseError("expected-tag-name-but-got-right-bracket"))
            self.tokenQueue.append(Characters("<>"))
            self.state = self.dataState
        elif data == "?":
            # XXX In theory it could be something besides a tag name. But
            # do we really care?
            self.tokenQueue.append(ParseError("expected-tag-name-but-got-question-mark"))
            self.stream.unget(data)
            self.state = self.bogusCommentState
        else:
            # XXX
            self.tokenQueue.append(ParseError("expected-tag-name"))
            self.tokenQueue.append(Characters("<"))
            self.stream.unget(data)
            self.state = self.dataState
        return True

    def closeTagOpenState(self):
        data = self.stream.char()
        if data in asciiLetters:
            self.currentToken = EndTag(name=data)
            self.state = self.tagNameState
        elif data == ">":
            self.tokenQueue.append(ParseError("expected-closing-tag-but-got-right-bracket"))
            self.state = self.dataState
        elif data is EOF:
            self.tokenQueue.append(ParseError("expected-closing-tag-but-got-eof"))
            self.tokenQueue.append(Characters("</"))
            self.state = self.dataState
        else:
            # XXX data can be _'_...
            self.tokenQueue.append(ParseError("expected-closing-tag-but-got-char", datavars={"data": data}))
            self.stream.unget(data)
            self.state = self.bogusCommentState
        return True

    def tagNameState(self):
        data = self.stream.char()
        if data in spaceCharacters:
            self.state = self.beforeAttributeNameState
        elif data == ">":
            self.emitCurrentToken()
        elif data is EOF:
            self.tokenQueue.append(ParseError("eof-in-tag-name"))
            self.state = self.dataState
        elif data == "/":
            self.state = self.selfClosingStartTagState
        elif data == "\u0000":
            self.tokenQueue.append(ParseError("invalid-codepoint"))
            self.currentToken.name += "\uFFFD"
        else:
            self.currentToken.name += data
            # (Don't use charsUntil here, because tag names are
            # very short and it's faster to not do anything fancy)
        return True

    def rcdataLessThanSignState(self):
        data = self.stream.char()
        if data == "/":
            self.temporaryBuffer = ""
            self.state = self.rcdataEndTagOpenState
        else:
            self.tokenQueue.append(Characters("<"))
            self.stream.unget(data)
            self.state = self.rcdataState
        return True

    def rcdataEndTagOpenState(self):
        data = self.stream.char()
        if data in asciiLetters:
            self.temporaryBuffer += data
            self.state = self.rcdataEndTagNameState
        else:
            self.tokenQueue.append(Characters("</"))
            self.stream.unget(data)
            self.state = self.rcdataState
        return True

    def rcdataEndTagNameState(self):
        appropriate = self.currentToken and self.currentToken.name.lower() == self.temporaryBuffer.lower()
        data = self.stream.char()
        if data in spaceCharacters and appropriate:
            self.currentToken = EndTag(name=self.temporaryBuffer)
            self.state = self.beforeAttributeNameState
        elif data == "/" and appropriate:
            self.currentToken = EndTag(name=self.temporaryBuffer)
            self.state = self.selfClosingStartTagState
        elif data == ">" and appropriate:
            self.currentToken = EndTag(name=self.temporaryBuffer)
            self.emitCurrentToken()
            self.state = self.dataState
        elif data in asciiLetters:
            self.temporaryBuffer += data
        else:
            self.tokenQueue.append(Characters("</" + self.temporaryBuffer))
            self.stream.unget(data)
            self.state = self.rcdataState
        return True

    def rawtextLessThanSignState(self):
        data = self.stream.char()
        if data == "/":
            self.temporaryBuffer = ""
            self.state = self.rawtextEndTagOpenState
        else:
            self.tokenQueue.append(Characters("<"))
            self.stream.unget(data)
            self.state = self.rawtextState
        return True

    def rawtextEndTagOpenState(self):
        data = self.stream.char()
        if data in asciiLetters:
            self.temporaryBuffer += data
            self.state = self.rawtextEndTagNameState
        else:
            self.tokenQueue.append(Characters("</"))
            self.stream.unget(data)
            self.state = self.rawtextState
        return True

    def rawtextEndTagNameState(self):
        appropriate = self.currentToken and self.currentToken.name.lower() == self.temporaryBuffer.lower()
        data = self.stream.char()
        if data in spaceCharacters and appropriate:
            self.currentToken = EndTag(name=self.temporaryBuffer)
            self.state = self.beforeAttributeNameState
        elif data == "/" and appropriate:
            self.currentToken = EndTag(name=self.temporaryBuffer)
            self.state = self.selfClosingStartTagState
        elif data == ">" and appropriate:
            self.currentToken = EndTag(name=self.temporaryBuffer)
            self.emitCurrentToken()
            self.state = self.dataState
        elif data in asciiLetters:
            self.temporaryBuffer += data
        else:
            self.tokenQueue.append(Characters("</" + self.temporaryBuffer))
            self.stream.unget(data)
            self.state = self.rawtextState
        return True

    def scriptDataLessThanSignState(self):
        data = self.stream.char()
        if data == "/":
            self.temporaryBuffer = ""
            self.state = self.scriptDataEndTagOpenState
        elif data == "!":
            self.tokenQueue.append(Characters("<!"))
            self.state = self.scriptDataEscapeStartState
        else:
            self.tokenQueue.append(Characters("<"))
            self.stream.unget(data)
            self.state = self.scriptDataState
        return True

    def scriptDataEndTagOpenState(self):
        data = self.stream.char()
        if data in asciiLetters:
            self.temporaryBuffer += data
            self.state = self.scriptDataEndTagNameState
        else:
            self.tokenQueue.append(Characters("</"))
            self.stream.unget(data)
            self.state = self.scriptDataState
        return True

    def scriptDataEndTagNameState(self):
        appropriate = self.currentToken and self.currentToken.name.lower() == self.temporaryBuffer.lower()
        data = self.stream.char()
        if data in spaceCharacters and appropriate:
            self.currentToken = EndTag(name=self.temporaryBuffer)
            self.state = self.beforeAttributeNameState
        elif data == "/" and appropriate:
            self.currentToken = EndTag(name=self.temporaryBuffer)
            self.state = self.selfClosingStartTagState
        elif data == ">" and appropriate:
            self.currentToken = EndTag(name=self.temporaryBuffer)
            self.emitCurrentToken()
            self.state = self.dataState
        elif data in asciiLetters:
            self.temporaryBuffer += data
        else:
            self.tokenQueue.append(Characters("</" + self.temporaryBuffer))
            self.stream.unget(data)
            self.state = self.scriptDataState
        return True

    def scriptDataEscapeStartState(self):
        data = self.stream.char()
        if data == "-":
            self.tokenQueue.append(Characters("-"))
            self.state = self.scriptDataEscapeStartDashState
        else:
            self.stream.unget(data)
            self.state = self.scriptDataState
        return True

    def scriptDataEscapeStartDashState(self):
        data = self.stream.char()
        if data == "-":
            self.tokenQueue.append(Characters("-"))
            self.state = self.scriptDataEscapedDashDashState
        else:
            self.stream.unget(data)
            self.state = self.scriptDataState
        return True

    def scriptDataEscapedState(self):
        data = self.stream.char()
        if data == "-":
            self.tokenQueue.append(Characters("-"))
            self.state = self.scriptDataEscapedDashState
        elif data == "<":
            self.state = self.scriptDataEscapedLessThanSignState
        elif data == "\u0000":
            self.tokenQueue.append(ParseError("invalid-codepoint"))
            self.tokenQueue.append(Characters("\uFFFD"))
        elif data == EOF:
            self.state = self.dataState
        else:
            chars = self.stream.charsUntil(("<", "-", "\u0000"))
            self.tokenQueue.append(Characters(data + chars))
        return True

    def scriptDataEscapedDashState(self):
        data = self.stream.char()
        if data == "-":
            self.tokenQueue.append(Characters("-"))
            self.state = self.scriptDataEscapedDashDashState
        elif data == "<":
            self.state = self.scriptDataEscapedLessThanSignState
        elif data == "\u0000":
            self.tokenQueue.append(ParseError("invalid-codepoint"))
            self.tokenQueue.append(Characters("\uFFFD"))
            self.state = self.scriptDataEscapedState
        elif data == EOF:
            self.state = self.dataState
        else:
            self.tokenQueue.append(Characters(data))
            self.state = self.scriptDataEscapedState
        return True

    def scriptDataEscapedDashDashState(self):
        data = self.stream.char()
        if data == "-":
            self.tokenQueue.append(Characters("-"))
        elif data == "<":
            self.state = self.scriptDataEscapedLessThanSignState
        elif data == ">":
            self.tokenQueue.append(Characters(">"))
            self.state = self.scriptDataState
        elif data == "\u0000":
            self.tokenQueue.append(ParseError("invalid-codepoint"))
            self.tokenQueue.append(Characters("\uFFFD"))
            self.state = self.scriptDataEscapedState
        elif data == EOF:
            self.state = self.dataState
        else:
            self.tokenQueue.append(Characters(data))
            self.state = self.scriptDataEscapedState
        return True

    def scriptDataEscapedLessThanSignState(self):
        data = self.stream.char()
        if data == "/":
            self.temporaryBuffer = ""
            self.state = self.scriptDataEscapedEndTagOpenState
        elif data in asciiLetters:
            self.tokenQueue.append(Characters("<" + data))
            self.temporaryBuffer = data
            self.state = self.scriptDataDoubleEscapeStartState
        else:
            self.tokenQueue.append(Characters("<"))
            self.stream.unget(data)
            self.state = self.scriptDataEscapedState
        return True

    def scriptDataEscapedEndTagOpenState(self):
        data = self.stream.char()
        if data in asciiLetters:
            self.temporaryBuffer = data
            self.state = self.scriptDataEscapedEndTagNameState
        else:
            self.tokenQueue.append(Characters("</"))
            self.stream.unget(data)
            self.state = self.scriptDataEscapedState
        return True

    def scriptDataEscapedEndTagNameState(self):
        appropriate = self.currentToken and self.currentToken.name.lower() == self.temporaryBuffer.lower()
        data = self.stream.char()
        if data in spaceCharacters and appropriate:
            self.currentToken = EndTag(name=self.temporaryBuffer)
            self.state = self.beforeAttributeNameState
        elif data == "/" and appropriate:
            self.currentToken = EndTag(name=self.temporaryBuffer)
            self.state = self.selfClosingStartTagState
        elif data == ">" and appropriate:
            self.currentToken = EndTag(name=self.temporaryBuffer)
            self.emitCurrentToken()
            self.state = self.dataState
        elif data in asciiLetters:
            self.temporaryBuffer += data
        else:
            self.tokenQueue.append(Characters("</" + self.temporaryBuffer))
            self.stream.unget(data)
            self.state = self.scriptDataEscapedState
        return True

    def scriptDataDoubleEscapeStartState(self):
        data = self.stream.char()
        if data in (spaceCharacters | frozenset(("/", ">"))):
            self.tokenQueue.append(Characters(data))
            if self.temporaryBuffer.lower() == "script":
                self.state = self.scriptDataDoubleEscapedState
            else:
                self.state = self.scriptDataEscapedState
        elif data in asciiLetters:
            self.tokenQueue.append(Characters(data))
            self.temporaryBuffer += data
        else:
            self.stream.unget(data)
            self.state = self.scriptDataEscapedState
        return True

    def scriptDataDoubleEscapedState(self):
        data = self.stream.char()
        if data == "-":
            self.tokenQueue.append(Characters("-"))
            self.state = self.scriptDataDoubleEscapedDashState
        elif data == "<":
            self.tokenQueue.append(Characters("<"))
            self.state = self.scriptDataDoubleEscapedLessThanSignState
        elif data == "\u0000":
            self.tokenQueue.append(ParseError("invalid-codepoint"))
            self.tokenQueue.append(Characters("\uFFFD"))
        elif data == EOF:
            self.tokenQueue.append(ParseError("eof-in-script-in-script"))
            self.state = self.dataState
        else:
            self.tokenQueue.append(Characters(data))
        return True

    def scriptDataDoubleEscapedDashState(self):
        data = self.stream.char()
        if data == "-":
            self.tokenQueue.append(Characters("-"))
            self.state = self.scriptDataDoubleEscapedDashDashState
        elif data == "<":
            self.tokenQueue.append(Characters("<"))
            self.state = self.scriptDataDoubleEscapedLessThanSignState
        elif data == "\u0000":
            self.tokenQueue.append(ParseError("invalid-codepoint"))
            self.tokenQueue.append(Characters("\uFFFD"))
            self.state = self.scriptDataDoubleEscapedState
        elif data == EOF:
            self.tokenQueue.append(ParseError("eof-in-script-in-script"))
            self.state = self.dataState
        else:
            self.tokenQueue.append(Characters(data))
            self.state = self.scriptDataDoubleEscapedState
        return True

    def scriptDataDoubleEscapedDashDashState(self):
        data = self.stream.char()
        if data == "-":
            self.tokenQueue.append(Characters("-"))
        elif data == "<":
            self.tokenQueue.append(Characters("<"))
            self.state = self.scriptDataDoubleEscapedLessThanSignState
        elif data == ">":
            self.tokenQueue.append(Characters(">"))
            self.state = self.scriptDataState
        elif data == "\u0000":
            self.tokenQueue.append(ParseError("invalid-codepoint"))
            self.tokenQueue.append(Characters("\uFFFD"))
            self.state = self.scriptDataDoubleEscapedState
        elif data == EOF:
            self.tokenQueue.append(ParseError("eof-in-script-in-script"))
            self.state = self.dataState
        else:
            self.tokenQueue.append(Characters(data))
            self.state = self.scriptDataDoubleEscapedState
        return True

    def scriptDataDoubleEscapedLessThanSignState(self):
        data = self.stream.char()
        if data == "/":
            self.tokenQueue.append(Characters("/"))
            self.temporaryBuffer = ""
            self.state = self.scriptDataDoubleEscapeEndState
        else:
            self.stream.unget(data)
            self.state = self.scriptDataDoubleEscapedState
        return True

    def scriptDataDoubleEscapeEndState(self):
        data = self.stream.char()
        if data in (spaceCharacters | frozenset(("/", ">"))):
            self.tokenQueue.append(Characters(data))
            if self.temporaryBuffer.lower() == "script":
                self.state = self.scriptDataEscapedState
            else:
                self.state = self.scriptDataDoubleEscapedState
        elif data in asciiLetters:
            self.tokenQueue.append(Characters(data))
            self.temporaryBuffer += data
        else:
            self.stream.unget(data)
            self.state = self.scriptDataDoubleEscapedState
        return True

    def beforeAttributeNameState(self):
        data = self.stream.char()
        if data in spaceCharacters:
            self.stream.charsUntil(spaceCharacters, True)
        elif data in asciiLetters:
            self.currentToken.clearAttribute()
            self.currentToken.accumulateAttributeName(data)
            self.state = self.attributeNameState
        elif data == ">":
            self.emitCurrentToken()
        elif data == "/":
            self.state = self.selfClosingStartTagState
        elif data in ("'", '"', "=", "<"):
            self.tokenQueue.append(ParseError("invalid-character-in-attribute-name"))
            self.currentToken.clearAttribute()
            self.currentToken.accumulateAttributeName(data)
            self.state = self.attributeNameState
        elif data == "\u0000":
            self.tokenQueue.append(ParseError("invalid-codepoint"))
            self.currentToken.clearAttribute()
            self.currentToken.accumulateAttributeName("\uFFFD")
            self.state = self.attributeNameState
        elif data is EOF:
            self.tokenQueue.append(ParseError("expected-attribute-name-but-got-eof"))
            self.state = self.dataState
        else:
            self.currentToken.clearAttribute()
            self.currentToken.accumulateAttributeName(data)
            self.state = self.attributeNameState
        return True

    def attributeNameState(self):
        data = self.stream.char()
        leavingThisState = True
        emitToken = False
        if data == "=":
            self.state = self.beforeAttributeValueState
        elif data in asciiLetters:
            self.currentToken.accumulateAttributeName(data + self.stream.charsUntil(asciiLetters, True))
            leavingThisState = False
        elif data == ">":
            # XXX If we emit here the attributes are converted to a dict
            # without being checked and when the code below runs we error
            # because data is a dict not a list
            emitToken = True
        elif data in spaceCharacters:
            self.state = self.afterAttributeNameState
        elif data == "/":
            self.state = self.selfClosingStartTagState
        elif data == "\u0000":
            self.tokenQueue.append(ParseError("invalid-codepoint"))
            self.currentToken.accumulateAttributeName("\uFFFD")
            leavingThisState = False
        elif data in ("'", '"', "<"):
            self.tokenQueue.append(ParseError("invalid-character-in-attribute-name"))
            self.currentToken.accumulateAttributeName(data)
            leavingThisState = False
        elif data is EOF:
            self.tokenQueue.append(ParseError("eof-in-attribute-name"))
            self.state = self.dataState
        else:
            self.currentToken.accumulateAttributeName(data)
            leavingThisState = False

        if leavingThisState:
            # Attributes are not dropped at this stage. That happens when the
            # start tag token is emitted so values can still be safely appended
            # to attributes, but we do want to report the parse error in time.
            if self.currentToken.attribute_name in self.currentToken.attributes:
                self.tokenQueue.append(ParseError("duplicate-attribute"))
            # XXX Fix for above XXX
            if emitToken:
                self.emitCurrentToken()
        return True

    def afterAttributeNameState(self):
        data = self.stream.char()
        if data in spaceCharacters:
            self.stream.charsUntil(spaceCharacters, True)
        elif data == "=":
            self.state = self.beforeAttributeValueState
        elif data == ">":
            self.emitCurrentToken()
        elif data in asciiLetters:
            self.currentToken.clearAttribute()
            self.currentToken.accumulateAttributeName(data)
            self.state = self.attributeNameState
        elif data == "/":
            self.state = self.selfClosingStartTagState
        elif data == "\u0000":
            self.tokenQueue.append(ParseError("invalid-codepoint"))
            self.currentToken.clearAttribute()
            self.currentToken.accumulateAttributeName("\uFFFD")
            self.state = self.attributeNameState
        elif data in ("'", '"', "<"):
            self.tokenQueue.append(ParseError("invalid-character-after-attribute-name"))
            self.currentToken.clearAttribute()
            self.currentToken.accumulateAttributeName(data)
            self.state = self.attributeNameState
        elif data is EOF:
            self.tokenQueue.append(ParseError("expected-end-of-tag-but-got-eof"))
            self.state = self.dataState
        else:
            self.currentToken.clearAttribute()
            self.currentToken.accumulateAttributeName(data)
            self.state = self.attributeNameState
        return True

    def beforeAttributeValueState(self):
        data = self.stream.char()
        if data in spaceCharacters:
            self.stream.charsUntil(spaceCharacters, True)
        elif data == "\"":
            self.state = self.attributeValueDoubleQuotedState
        elif data == "&":
            self.state = self.attributeValueUnQuotedState
            self.stream.unget(data)
        elif data == "'":
            self.state = self.attributeValueSingleQuotedState
        elif data == ">":
            self.tokenQueue.append(ParseError("expected-attribute-value-but-got-right-bracket"))
            self.emitCurrentToken()
        elif data == "\u0000":
            self.tokenQueue.append(ParseError("invalid-codepoint"))
            self.currentToken.accumulateAttributeValue("\uFFFD")
            self.state = self.attributeValueUnQuotedState
        elif data in ("=", "<", "`"):
            self.tokenQueue.append(ParseError("equals-in-unquoted-attribute-value"))
            self.currentToken.accumulateAttributeValue(data)
            self.state = self.attributeValueUnQuotedState
        elif data is EOF:
            self.tokenQueue.append(ParseError("expected-attribute-value-but-got-eof"))
            self.state = self.dataState
        else:
            self.currentToken.accumulateAttributeValue(data)
            self.state = self.attributeValueUnQuotedState
        return True

    def attributeValueDoubleQuotedState(self):
        data = self.stream.char()
        if data == "\"":
            self.state = self.afterAttributeValueState
        elif data == "&":
            self.processEntityInAttribute('"')
        elif data == "\u0000":
            self.tokenQueue.append(ParseError("invalid-codepoint"))
            self.currentToken.accumulateAttributeValue("\uFFFD")
        elif data is EOF:
            self.tokenQueue.append(ParseError("eof-in-attribute-value-double-quote"))
            self.state = self.dataState
        else:
            self.currentToken.accumulateAttributeValue(data + self.stream.charsUntil(("\"", "&", "\u0000")))
        return True

    def attributeValueSingleQuotedState(self):
        data = self.stream.char()
        if data == "'":
            self.state = self.afterAttributeValueState
        elif data == "&":
            self.processEntityInAttribute("'")
        elif data == "\u0000":
            self.tokenQueue.append(ParseError("invalid-codepoint"))
            self.currentToken.accumulateAttributeValue("\uFFFD")
        elif data is EOF:
            self.tokenQueue.append(ParseError("eof-in-attribute-value-single-quote"))
            self.state = self.dataState
        else:
            self.currentToken.accumulateAttributeValue(data + self.stream.charsUntil(("'", "&", "\u0000")))
        return True

    def attributeValueUnQuotedState(self):
        data = self.stream.char()
        if data in spaceCharacters:
            self.state = self.beforeAttributeNameState
        elif data == "&":
            self.processEntityInAttribute(">")
        elif data == ">":
            self.emitCurrentToken()
        elif data in ('"', "'", "=", "<", "`"):
            self.tokenQueue.append(ParseError("unexpected-character-in-unquoted-attribute-value"))
            self.currentToken.accumulateAttributeValue(data)
        elif data == "\u0000":
            self.tokenQueue.append(ParseError("invalid-codepoint"))
            self.currentToken.accumulateAttributeValue("\uFFFD")
        elif data is EOF:
            self.tokenQueue.append(ParseError("eof-in-attribute-value-no-quotes"))
            self.state = self.dataState
        else:
            self.currentToken.accumulateAttributeValue(data + self.stream.charsUntil(
                frozenset(("&", ">", '"', "'", "=", "<", "`", "\u0000")) | spaceCharacters))
        return True

    def afterAttributeValueState(self):
        data = self.stream.char()
        if data in spaceCharacters:
            self.state = self.beforeAttributeNameState
        elif data == ">":
            self.emitCurrentToken()
        elif data == "/":
            self.state = self.selfClosingStartTagState
        elif data is EOF:
            self.tokenQueue.append(ParseError("unexpected-EOF-after-attribute-value"))
            self.stream.unget(data)
            self.state = self.dataState
        else:
            self.tokenQueue.append(ParseError("unexpected-character-after-attribute-value"))
            self.stream.unget(data)
            self.state = self.beforeAttributeNameState
        return True

    def selfClosingStartTagState(self):
        data = self.stream.char()
        if data == ">":
            self.currentToken.self_closing = True
            self.emitCurrentToken()
        elif data is EOF:
            self.tokenQueue.append(ParseError("unexpected-EOF-after-solidus-in-tag"))
            self.stream.unget(data)
            self.state = self.dataState
        else:
            self.tokenQueue.append(ParseError("unexpected-character-after-solidus-in-tag"))
            self.stream.unget(data)
            self.state = self.beforeAttributeNameState
        return True

    def bogusCommentState(self):
        # Make a new comment token and give it as value all the characters
        # until the first > or EOF (charsUntil checks for EOF automatically)
        # and emit it.
        data = self.stream.charsUntil(">")
        data = data.replace("\u0000", "\uFFFD")
        self.tokenQueue.append(Comment(data))

        # Eat the character directly after the bogus comment which is either a
        # ">" or an EOF.
        self.stream.char()
        self.state = self.dataState
        return True

    def markupDeclarationOpenState(self):
        charStack = [self.stream.char()]
        if charStack[-1] == "-":
            charStack.append(self.stream.char())
            if charStack[-1] == "-":
                self.currentToken = Comment("")
                self.state = self.commentStartState
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
                self.currentToken = Doctype(name="", public_id=None, system_id=None, correct=True)
                self.state = self.doctypeState
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
                self.state = self.cdataSectionState
                return True

        self.tokenQueue.append(ParseError("expected-dashes-or-doctype"))

        while charStack:
            self.stream.unget(charStack.pop())
        self.state = self.bogusCommentState
        return True

    def commentStartState(self):
        data = self.stream.char()
        if data == "-":
            self.state = self.commentStartDashState
        elif data == "\u0000":
            self.tokenQueue.append(ParseError("invalid-codepoint"))
            self.currentToken.data += "\uFFFD"
        elif data == ">":
            self.tokenQueue.append(ParseError("incorrect-comment"))
            self.tokenQueue.append(self.currentToken)
            self.state = self.dataState
        elif data is EOF:
            self.tokenQueue.append(ParseError("eof-in-comment"))
            self.tokenQueue.append(self.currentToken)
            self.state = self.dataState
        else:
            self.currentToken.data += data
            self.state = self.commentState
        return True

    def commentStartDashState(self):
        data = self.stream.char()
        if data == "-":
            self.state = self.commentEndState
        elif data == "\u0000":
            self.tokenQueue.append(ParseError("invalid-codepoint"))
            self.currentToken.data += "-\uFFFD"
        elif data == ">":
            self.tokenQueue.append(ParseError("incorrect-comment"))
            self.tokenQueue.append(self.currentToken)
            self.state = self.dataState
        elif data is EOF:
            self.tokenQueue.append(ParseError("eof-in-comment"))
            self.tokenQueue.append(self.currentToken)
            self.state = self.dataState
        else:
            self.currentToken.data += "-" + data
            self.state = self.commentState
        return True

    def commentState(self):
        data = self.stream.char()
        if data == "-":
            self.state = self.commentEndDashState
        elif data == "\u0000":
            self.tokenQueue.append(ParseError("invalid-codepoint"))
            self.currentToken.data += "\uFFFD"
        elif data is EOF:
            self.tokenQueue.append(ParseError("eof-in-comment"))
            self.tokenQueue.append(self.currentToken)
            self.state = self.dataState
        else:
            self.currentToken.data += data + \
                self.stream.charsUntil(("-", "\u0000"))
        return True

    def commentEndDashState(self):
        data = self.stream.char()
        if data == "-":
            self.state = self.commentEndState
        elif data == "\u0000":
            self.tokenQueue.append(ParseError("invalid-codepoint"))
            self.currentToken.data += "-\uFFFD"
            self.state = self.commentState
        elif data is EOF:
            self.tokenQueue.append(ParseError("eof-in-comment-end-dash"))
            self.tokenQueue.append(self.currentToken)
            self.state = self.dataState
        else:
            self.currentToken.data += "-" + data
            self.state = self.commentState
        return True

    def commentEndState(self):
        data = self.stream.char()
        if data == ">":
            self.tokenQueue.append(self.currentToken)
            self.state = self.dataState
        elif data == "\u0000":
            self.tokenQueue.append(ParseError("invalid-codepoint"))
            self.currentToken.data += "--\uFFFD"
            self.state = self.commentState
        elif data == "!":
            self.tokenQueue.append(ParseError("unexpected-bang-after-double-dash-in-comment"))
            self.state = self.commentEndBangState
        elif data == "-":
            self.tokenQueue.append(ParseError("unexpected-dash-after-double-dash-in-comment"))
            self.currentToken.data += data
        elif data is EOF:
            self.tokenQueue.append(ParseError("eof-in-comment-double-dash"))
            self.tokenQueue.append(self.currentToken)
            self.state = self.dataState
        else:
            # XXX
            self.tokenQueue.append(ParseError("unexpected-char-in-comment"))
            self.currentToken.data += "--" + data
            self.state = self.commentState
        return True

    def commentEndBangState(self):
        data = self.stream.char()
        if data == ">":
            self.tokenQueue.append(self.currentToken)
            self.state = self.dataState
        elif data == "-":
            self.currentToken.data += "--!"
            self.state = self.commentEndDashState
        elif data == "\u0000":
            self.tokenQueue.append(ParseError("invalid-codepoint"))
            self.currentToken.data += "--!\uFFFD"
            self.state = self.commentState
        elif data is EOF:
            self.tokenQueue.append(ParseError("eof-in-comment-end-bang-state"))
            self.tokenQueue.append(self.currentToken)
            self.state = self.dataState
        else:
            self.currentToken.data += "--!" + data
            self.state = self.commentState
        return True

    def doctypeState(self):
        data = self.stream.char()
        if data in spaceCharacters:
            self.state = self.beforeDoctypeNameState
        elif data is EOF:
            self.tokenQueue.append(ParseError("expected-doctype-name-but-got-eof"))
            self.currentToken.correct = False
            self.tokenQueue.append(self.currentToken)
            self.state = self.dataState
        else:
            self.tokenQueue.append(ParseError("need-space-after-doctype"))
            self.stream.unget(data)
            self.state = self.beforeDoctypeNameState
        return True

    def beforeDoctypeNameState(self):
        data = self.stream.char()
        if data in spaceCharacters:
            pass
        elif data == ">":
            self.tokenQueue.append(ParseError("expected-doctype-name-but-got-right-bracket"))
            self.currentToken.correct = False
            self.tokenQueue.append(self.currentToken)
            self.state = self.dataState
        elif data == "\u0000":
            self.tokenQueue.append(ParseError("invalid-codepoint"))
            self.currentToken.name = "\uFFFD"
            self.state = self.doctypeNameState
        elif data is EOF:
            self.tokenQueue.append(ParseError("expected-doctype-name-but-got-eof"))
            self.currentToken.correct = False
            self.tokenQueue.append(self.currentToken)
            self.state = self.dataState
        else:
            self.currentToken.name = data
            self.state = self.doctypeNameState
        return True

    def doctypeNameState(self):
        data = self.stream.char()
        if data in spaceCharacters:
            self.currentToken.name = self.currentToken.name.translate(asciiUpper2Lower)
            self.state = self.afterDoctypeNameState
        elif data == ">":
            self.currentToken.name = self.currentToken.name.translate(asciiUpper2Lower)
            self.tokenQueue.append(self.currentToken)
            self.state = self.dataState
        elif data == "\u0000":
            self.tokenQueue.append(ParseError("invalid-codepoint"))
            self.currentToken.name += "\uFFFD"
            self.state = self.doctypeNameState
        elif data is EOF:
            self.tokenQueue.append(ParseError("eof-in-doctype-name"))
            self.currentToken.correct = False
            self.currentToken.name = self.currentToken.name.translate(asciiUpper2Lower)
            self.tokenQueue.append(self.currentToken)
            self.state = self.dataState
        else:
            self.currentToken.name += data
        return True

    def afterDoctypeNameState(self):
        data = self.stream.char()
        if data in spaceCharacters:
            pass
        elif data == ">":
            self.tokenQueue.append(self.currentToken)
            self.state = self.dataState
        elif data is EOF:
            self.currentToken.correct = False
            self.stream.unget(data)
            self.tokenQueue.append(ParseError("eof-in-doctype"))
            self.tokenQueue.append(self.currentToken)
            self.state = self.dataState
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
                    self.state = self.afterDoctypePublicKeywordState
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
                    self.state = self.afterDoctypeSystemKeywordState
                    return True

            # All the characters read before the current 'data' will be
            # [a-zA-Z], so they're garbage in the bogus doctype and can be
            # discarded; only the latest character might be '>' or EOF
            # and needs to be ungetted
            self.stream.unget(data)
            self.tokenQueue.append(ParseError("expected-space-or-right-bracket-in-doctype", datavars={"data": data}))
            self.currentToken.correct = False
            self.state = self.bogusDoctypeState

        return True

    def afterDoctypePublicKeywordState(self):
        data = self.stream.char()
        if data in spaceCharacters:
            self.state = self.beforeDoctypePublicIdentifierState
        elif data in ("'", '"'):
            self.tokenQueue.append(ParseError("unexpected-char-in-doctype"))
            self.stream.unget(data)
            self.state = self.beforeDoctypePublicIdentifierState
        elif data is EOF:
            self.tokenQueue.append(ParseError("eof-in-doctype"))
            self.currentToken.correct = False
            self.tokenQueue.append(self.currentToken)
            self.state = self.dataState
        else:
            self.stream.unget(data)
            self.state = self.beforeDoctypePublicIdentifierState
        return True

    def beforeDoctypePublicIdentifierState(self):
        data = self.stream.char()
        if data in spaceCharacters:
            pass
        elif data == "\"":
            self.currentToken.public_id = ""
            self.state = self.doctypePublicIdentifierDoubleQuotedState
        elif data == "'":
            self.currentToken.public_id = ""
            self.state = self.doctypePublicIdentifierSingleQuotedState
        elif data == ">":
            self.tokenQueue.append(ParseError("unexpected-end-of-doctype"))
            self.currentToken.correct = False
            self.tokenQueue.append(self.currentToken)
            self.state = self.dataState
        elif data is EOF:
            self.tokenQueue.append(ParseError("eof-in-doctype"))
            self.currentToken.correct = False
            self.tokenQueue.append(self.currentToken)
            self.state = self.dataState
        else:
            self.tokenQueue.append(ParseError("unexpected-char-in-doctype"))
            self.currentToken.correct = False
            self.state = self.bogusDoctypeState
        return True

    def doctypePublicIdentifierDoubleQuotedState(self):
        data = self.stream.char()
        if data == "\"":
            self.state = self.afterDoctypePublicIdentifierState
        elif data == "\u0000":
            self.tokenQueue.append(ParseError("invalid-codepoint"))
            self.currentToken.public_id += "\uFFFD"
        elif data == ">":
            self.tokenQueue.append(ParseError("unexpected-end-of-doctype"))
            self.currentToken.correct = False
            self.tokenQueue.append(self.currentToken)
            self.state = self.dataState
        elif data is EOF:
            self.tokenQueue.append(ParseError("eof-in-doctype"))
            self.currentToken.correct = False
            self.tokenQueue.append(self.currentToken)
            self.state = self.dataState
        else:
            self.currentToken.public_id += data
        return True

    def doctypePublicIdentifierSingleQuotedState(self):
        data = self.stream.char()
        if data == "'":
            self.state = self.afterDoctypePublicIdentifierState
        elif data == "\u0000":
            self.tokenQueue.append(ParseError("invalid-codepoint"))
            self.currentToken.public_id += "\uFFFD"
        elif data == ">":
            self.tokenQueue.append(ParseError("unexpected-end-of-doctype"))
            self.currentToken.correct = False
            self.tokenQueue.append(self.currentToken)
            self.state = self.dataState
        elif data is EOF:
            self.tokenQueue.append(ParseError("eof-in-doctype"))
            self.currentToken.correct = False
            self.tokenQueue.append(self.currentToken)
            self.state = self.dataState
        else:
            self.currentToken.public_id += data
        return True

    def afterDoctypePublicIdentifierState(self):
        data = self.stream.char()
        if data in spaceCharacters:
            self.state = self.betweenDoctypePublicAndSystemIdentifiersState
        elif data == ">":
            self.tokenQueue.append(self.currentToken)
            self.state = self.dataState
        elif data == '"':
            self.tokenQueue.append(ParseError("unexpected-char-in-doctype"))
            self.currentToken.system_id = ""
            self.state = self.doctypeSystemIdentifierDoubleQuotedState
        elif data == "'":
            self.tokenQueue.append(ParseError("unexpected-char-in-doctype"))
            self.currentToken.system_id = ""
            self.state = self.doctypeSystemIdentifierSingleQuotedState
        elif data is EOF:
            self.tokenQueue.append(ParseError("eof-in-doctype"))
            self.currentToken.correct = False
            self.tokenQueue.append(self.currentToken)
            self.state = self.dataState
        else:
            self.tokenQueue.append(ParseError("unexpected-char-in-doctype"))
            self.currentToken.correct = False
            self.state = self.bogusDoctypeState
        return True

    def betweenDoctypePublicAndSystemIdentifiersState(self):
        data = self.stream.char()
        if data in spaceCharacters:
            pass
        elif data == ">":
            self.tokenQueue.append(self.currentToken)
            self.state = self.dataState
        elif data == '"':
            self.currentToken.system_id = ""
            self.state = self.doctypeSystemIdentifierDoubleQuotedState
        elif data == "'":
            self.currentToken.system_id = ""
            self.state = self.doctypeSystemIdentifierSingleQuotedState
        elif data == EOF:
            self.tokenQueue.append(ParseError("eof-in-doctype"))
            self.currentToken.correct = False
            self.tokenQueue.append(self.currentToken)
            self.state = self.dataState
        else:
            self.tokenQueue.append(ParseError("unexpected-char-in-doctype"))
            self.currentToken.correct = False
            self.state = self.bogusDoctypeState
        return True

    def afterDoctypeSystemKeywordState(self):
        data = self.stream.char()
        if data in spaceCharacters:
            self.state = self.beforeDoctypeSystemIdentifierState
        elif data in ("'", '"'):
            self.tokenQueue.append(ParseError("unexpected-char-in-doctype"))
            self.stream.unget(data)
            self.state = self.beforeDoctypeSystemIdentifierState
        elif data is EOF:
            self.tokenQueue.append(ParseError("eof-in-doctype"))
            self.currentToken.correct = False
            self.tokenQueue.append(self.currentToken)
            self.state = self.dataState
        else:
            self.stream.unget(data)
            self.state = self.beforeDoctypeSystemIdentifierState
        return True

    def beforeDoctypeSystemIdentifierState(self):
        data = self.stream.char()
        if data in spaceCharacters:
            pass
        elif data == "\"":
            self.currentToken.system_id = ""
            self.state = self.doctypeSystemIdentifierDoubleQuotedState
        elif data == "'":
            self.currentToken.system_id = ""
            self.state = self.doctypeSystemIdentifierSingleQuotedState
        elif data == ">":
            self.tokenQueue.append(ParseError("unexpected-char-in-doctype"))
            self.currentToken.correct = False
            self.tokenQueue.append(self.currentToken)
            self.state = self.dataState
        elif data is EOF:
            self.tokenQueue.append(ParseError("eof-in-doctype"))
            self.currentToken.correct = False
            self.tokenQueue.append(self.currentToken)
            self.state = self.dataState
        else:
            self.tokenQueue.append(ParseError("unexpected-char-in-doctype"))
            self.currentToken.correct = False
            self.state = self.bogusDoctypeState
        return True

    def doctypeSystemIdentifierDoubleQuotedState(self):
        data = self.stream.char()
        if data == "\"":
            self.state = self.afterDoctypeSystemIdentifierState
        elif data == "\u0000":
            self.tokenQueue.append(ParseError("invalid-codepoint"))
            self.currentToken.system_id += "\uFFFD"
        elif data == ">":
            self.tokenQueue.append(ParseError("unexpected-end-of-doctype"))
            self.currentToken.correct = False
            self.tokenQueue.append(self.currentToken)
            self.state = self.dataState
        elif data is EOF:
            self.tokenQueue.append(ParseError("eof-in-doctype"))
            self.currentToken.correct = False
            self.tokenQueue.append(self.currentToken)
            self.state = self.dataState
        else:
            self.currentToken.system_id += data
        return True

    def doctypeSystemIdentifierSingleQuotedState(self):
        data = self.stream.char()
        if data == "'":
            self.state = self.afterDoctypeSystemIdentifierState
        elif data == "\u0000":
            self.tokenQueue.append(ParseError("invalid-codepoint"))
            self.currentToken.system_id += "\uFFFD"
        elif data == ">":
            self.tokenQueue.append(ParseError("unexpected-end-of-doctype"))
            self.currentToken.correct = False
            self.tokenQueue.append(self.currentToken)
            self.state = self.dataState
        elif data is EOF:
            self.tokenQueue.append(ParseError("eof-in-doctype"))
            self.currentToken.correct = False
            self.tokenQueue.append(self.currentToken)
            self.state = self.dataState
        else:
            self.currentToken.system_id += data
        return True

    def afterDoctypeSystemIdentifierState(self):
        data = self.stream.char()
        if data in spaceCharacters:
            pass
        elif data == ">":
            self.tokenQueue.append(self.currentToken)
            self.state = self.dataState
        elif data is EOF:
            self.tokenQueue.append(ParseError("eof-in-doctype"))
            self.currentToken.correct = False
            self.tokenQueue.append(self.currentToken)
            self.state = self.dataState
        else:
            self.tokenQueue.append(ParseError("unexpected-char-in-doctype"))
            self.state = self.bogusDoctypeState
        return True

    def bogusDoctypeState(self):
        data = self.stream.char()
        if data == ">":
            self.tokenQueue.append(self.currentToken)
            self.state = self.dataState
        elif data is EOF:
            # XXX EMIT
            self.stream.unget(data)
            self.tokenQueue.append(self.currentToken)
            self.state = self.dataState
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
                self.tokenQueue.append(ParseError("invalid-codepoint"))
            data = data.replace("\u0000", "\uFFFD")
        if data:
            self.tokenQueue.append(Characters(data))
        self.state = self.dataState
        return True
