try:
    from sets import ImmutableSet as frozenset
except:
    pass

import string

from constants import contentModelFlags, spaceCharacters
from constants import entitiesWindows1252, entities, voidElements

# Data representing the end of the input stream
EOF = None

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
        self.name = name
        self.error = True

class TagToken(Token):
    """Token representing a tag.
    Attributes - name:       The tag name
                 attributes: A list of (attribute-name,value) lists
    """

    # Note: the parser gets a dict, not a list of lists.

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
    def __init__(self, data=""):
        self.data = data

class HTMLTokenizer(object):
    """This class has various attributes:

    * self.parser
      Points to the parser object that implements the following methods:

      - processDoctype(name, error)
      - processStartTag(tagname, attributes{})
      - processEndTag(tagname)
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
            "markupDeclarationOpen":self.markupDeclarationOpenState,
            "comment":self.commentState,
            "commentDash":self.commentDashState,
            "commentEnd":self.commentEndState,
            "doctype":self.doctypeState,
            "beforeDoctypeName":self.beforeDoctypeNameState,
            "doctypeName":self.doctypeNameState,
            "afterDoctypeName":self.afterDoctypeNameState,
            "bogusDoctype":self.bogusDoctypeState
        }

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

        if self.currentToken.name in voidElements and data == u">":
            self.parser.atheistParseError()
        else:
            self.parser.parseError()

        # The character we just consumed need to be put back on the stack so it
        # doesn't get lost...
        self.characterQueue.append(data)

    def consumeNumberEntity(self, isHex):
        """This function returns either U+FFFD or the character based on the
        decimal or hexadecimal representation. It also discards ";" if present.
        If not present self.parser.parseError() is invoked.
        """

        allowed = string.digits
        radix = 10
        if isHex:
            allowed = string.hexdigits
            radix = 16

        char = u"\uFFFD"
        charStack = []

        # Consume all the characters that are in range while making sure we
        # don't hit an EOF.
        c = self.consumeChar()
        while c in allowed and c is not EOF:
            charStack.append(c)
            c = self.consumeChar()

        # Convert the set of characters consumed to an int.
        charAsInt = int("".join(charStack), radix)

        # If the integer is between 127 and 160 (so 128 and bigger and 159 and
        # smaller) we need to do the "windows trick".
        if 127 < charAsInt < 160:
            charAsInt = entitiesWindows1252[128 - charAsInt]

        # 0 is not a good number.
        if charAsInt == 0:
            charAsInt = 65533

        try:
            # XXX We should have a separate function that does "int" to
            # "unicodestring" conversion since this doesn't always work
            # according to hsivonen. Also, unichr has a limitation of 65535
            char = unichr(charAsInt)
        except:
            pass

        # Discard the ; if present. Otherwise, put it back on the queue and
        # invoke parseError on parser.
        if c != u";":
            self.parser.parseError()
            self.characterQueue.append(c)

        return char

    def consumeEntity(self):
        char = None
        charStack = []
        charStack.append(self.consumeChar())
        if charStack[0] == u"#":
            charStack.append(self.consumeChar())
            charStack.append(self.consumeChar())
            if EOF in charStack:
                # If we reach the end of the file put everything up to EOF
                # back in the queue
                charStack = charStack[:charStack.index(EOF)]
                self.characterQueue.extend(charStack)
                self.parser.parseError()
            else:
                if charStack[1].lower() == u"x" \
                  and charStack[2] in string.hexdigits:
                    # Hexadecimal entity detected.
                    self.characterQueue.append(charStack[2])
                    char = self.consumeNumberEntity(True)
                elif charStack[1] in string.digits:
                    # Decimal entity detected.
                    self.characterQueue.extend(charStack[1:])
                    char = self.consumeNumberEntity(False)
                else:
                    # No number entity detected.
                    self.characterQueue.extend(charStack)
                    self.parser.parseError()
        # Break out if we reach the end of the file
        elif charStack[0] == EOF:
            self.parser.parseError()
        else:
            # At this point in the process might have named entity. Entities
            # are stored in the global variable "entities".

            # Consume characters and compare to these to a substring of the
            # entity names in the list until the substring no longer matches.
            filteredEntityList = [e for e in entities if \
              e.startswith(charStack[0])]

            def entitiesStartingWith(name):
                return [e for e in filteredEntityList if e.startswith(name)]

            while (charStack[-1] != EOF and
                   entitiesStartingWith("".join(charStack))):
                charStack.append(self.consumeChar())

            # At this point we have a string that starts with some characters
            # that may match an entity
            entityName = None

            # Try to find the longest entity the string will match
            for entityLength in xrange(len(charStack)-1,1,-1):
                possibleEntityName = "".join(charStack[:entityLength])
                if possibleEntityName in entities:
                    entityName = possibleEntityName
                    break

            if entityName is not None:
                char = entities[entityName]

                # Check whether or not the last character returned can be
                # discarded or needs to be put back.
                if not charStack[-1] == ";":
                    self.parser.parseError()
                    self.characterQueue.extend(charStack[entityLength:])
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

        token = self.currentToken
        if isinstance(token, StartTagToken):
            # We need to remove the duplicate attributes and convert attributes
            # to a dict so that [["x", "y"], ["x", "z"]] becomes {"x": "y"}

            # AT When Python 2.4 is widespread we should use
            # dict(reversed(self.currentToken.attributes))
            attrsDict = dict(token.attributes[::-1])
            self.parser.processStartTag(token.name, attrsDict)
        elif isinstance(token, EndTagToken):
            # If an end tag has attributes it's a parse error.
            if token.attributes:
                self.parser.parseError()
            self.contentModelFlag = contentModelFlags["PCDATA"]
            self.parser.processEndTag(token.name)
        elif isinstance(token, CommentToken):
            self.parser.processComment(token.data)
        elif isinstance(token, DoctypeToken):
            self.parser.processDoctype(token.name, token.error)
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
            self.changeState("entityData")
        elif (data == u"<" and
          self.contentModelFlag != contentModelFlags["PLAINTEXT"]):
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
                self.changeState("markupDeclarationOpen")
            elif data == u"/":
                self.changeState("closeTagOpen")
            elif data in string.ascii_letters:
                self.currentToken = StartTagToken(data.lower())
                self.changeState("tagName")
            elif data == u">":
                self.parser.parseError()
                self.parser.processCharacter(u"<")
                self.parser.processCharacter(u">")
                self.changeState("data")
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

            # XXX what if we hit EOF!!!
            for x in xrange(len(self.currentToken.name)+1):
                charStack.append(self.consumeChar())

            # Since this is just for checking. We put the characters back on
            # the stack.
            self.characterQueue.extend(charStack)

            if not self.currentToken.name == "".join(charStack[:-1]).lower() \
              and not charStack[-1] in (spaceCharacters |
              frozenset((u">", u"/", u"<", EOF))):
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
            self.changeState("attributeName")
        elif data == u"/":
            self.processSolidusInTag()
        elif data == u"<" or data == EOF:
            self.emitCurrentTokenWithParseError(data)
        else:
            self.currentToken.attributes.append([data, ""])
            self.changeState("attributeName")
        return True

    def attributeNameState(self):
        data = self.consumeChar()
        leavingThisState = True
        if data in spaceCharacters:
            self.changeState("afterAttributeName")
        elif data == u"=":
            self.changeState("beforeAttributeValue")
        elif data == u">":
            self.emitCurrentToken()
        elif data in string.ascii_uppercase:
            self.currentToken.attributes[-1][0] += data.lower()
            leavingThisState = False
        elif data == u"/":
            self.processSolidusInTag()
            self.changeState("beforeAttributeName")
        elif data == u"<" or data == EOF:
            self.emitCurrentTokenWithParseError(data)
        else:
            self.currentToken.attributes[-1][0] += data
            leavingThisState = False

        if leavingThisState:
            # Attributes are not dropped at this stage. That happens when the
            # start tag token is emitted so values can still be safely appended
            # to attributes, but we do want to report the parse error in time.
            for name, value in self.currentToken.attributes[:-1]:
                if self.currentToken.attributes[-1][0] == name:
                    self.parser.parseError()
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
        data = self.consumeChar()
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
            self.currentToken.attributes[-1][1] += data
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
        assert self.contentModelFlag == contentModelFlags["PCDATA"]

        charStack = [self.consumeChar()]
        while charStack[-1] not in [u">", EOF]:
            charStack.append(self.consumeChar())

        if charStack[-1] == EOF:
            self.characterQueue.append(EOF)

        # Make a new comment token and give it as value the characters the loop
        # consumed. The last character is either > or EOF and should not be
        # part of the comment data.
        self.currentToken = CommentToken("".join(charStack[:-1]))
        self.emitCurrentToken()
        return True

    def markupDeclarationOpenState(self):
        assert self.contentModelFlag == contentModelFlags["PCDATA"]

        charStack = [self.consumeChar(), self.consumeChar()]
        if charStack == [u"-", u"-"]:
            self.currentToken = CommentToken()
            self.changeState("comment")
        else:
            for x in xrange(5):
                charStack.append(self.consumeChar())
            #XXX - put in explicit None check
            if (not EOF in charStack and
                "".join(charStack).upper() == u"DOCTYPE"):
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
            self.changeState("doctypeName")
        elif data == u">":
            # Character needs to be consumed per the specification so don't
            # invoke emitCurrentTokenWithParseError with "data" as argument.
            self.emitCurrentTokenWithParseError()
        elif data == EOF:
            self.emitCurrentTokenWithParseError(data)
        else:
            self.currentToken = DoctypeToken(data)
            self.changeState("doctypeName")
        return True

    def doctypeNameState(self):
        data = self.consumeChar()
        needsDoctypeCheck = False
        if data in spaceCharacters:
            self.changeState("afterDoctypeName")
            needsDoctypeCheck = True
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
            needsDoctypeCheck = True

        # After some iterations through this state it should eventually say
        # "HTML". Otherwise there's an error.
        if needsDoctypeCheck and self.currentToken.name == u"HTML":
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
