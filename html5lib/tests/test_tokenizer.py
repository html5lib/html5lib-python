

from __future__ import with_statement
from __future__ import absolute_import
import sys
import os
import io
import warnings
import re
from itertools import izip
from io import open

try:
    import json
except ImportError:
    import simplejson as json

from .support import get_data_files
from html5lib.tokenizer import HTMLTokenizer
from html5lib import constants

class TokenizerTestParser(object):
    def __init__(self, initialState, lastStartTag=None):
        self.tokenizer = HTMLTokenizer
        self._state = initialState
        self._lastStartTag = lastStartTag
    __init__.func_annotations = {}

    def parse(self, stream, encoding=None, innerHTML=False):
        tokenizer = self.tokenizer(stream, encoding)
        self.outputTokens = []

        tokenizer.state = getattr(tokenizer, self._state)
        if self._lastStartTag is not None:
            tokenizer.currentToken = {u"type": u"startTag", 
                                      u"name":self._lastStartTag}

        types = dict((v,k) for k,v in constants.tokenTypes.items())
        for token in tokenizer:
            getattr(self, u'process%s' % types[token[u"type"]])(token)

        return self.outputTokens
    parse.func_annotations = {}

    def processDoctype(self, token):
        self.outputTokens.append([u"DOCTYPE", token[u"name"], token[u"publicId"],
                                  token[u"systemId"], token[u"correct"]])
    processDoctype.func_annotations = {}

    def processStartTag(self, token):
        self.outputTokens.append([u"StartTag", token[u"name"], 
                                  dict(token[u"data"][::-1]), token[u"selfClosing"]])
    processStartTag.func_annotations = {}

    def processEmptyTag(self, token):
        if token[u"name"] not in constants.voidElements:
            self.outputTokens.append(u"ParseError")
        self.outputTokens.append([u"StartTag", token[u"name"], dict(token[u"data"][::-1])])
    processEmptyTag.func_annotations = {}

    def processEndTag(self, token):
        self.outputTokens.append([u"EndTag", token[u"name"], 
                                  token[u"selfClosing"]])
    processEndTag.func_annotations = {}

    def processComment(self, token):
        self.outputTokens.append([u"Comment", token[u"data"]])
    processComment.func_annotations = {}

    def processSpaceCharacters(self, token):
        self.outputTokens.append([u"Character", token[u"data"]])
        self.processSpaceCharacters = self.processCharacters
    processSpaceCharacters.func_annotations = {}

    def processCharacters(self, token):
        self.outputTokens.append([u"Character", token[u"data"]])
    processCharacters.func_annotations = {}

    def processEOF(self, token):
        pass
    processEOF.func_annotations = {}

    def processParseError(self, token):
        self.outputTokens.append([u"ParseError", token[u"data"]])
    processParseError.func_annotations = {}

def concatenateCharacterTokens(tokens):
    outputTokens = []
    for token in tokens:
        if not u"ParseError" in token and token[0] == u"Character":
            if (outputTokens and not u"ParseError" in outputTokens[-1] and
                outputTokens[-1][0] == u"Character"):
                outputTokens[-1][1] += token[1]
            else:
                outputTokens.append(token)
        else:
            outputTokens.append(token)
    return outputTokens
concatenateCharacterTokens.func_annotations = {}

def normalizeTokens(tokens):
    # TODO: convert tests to reflect arrays
    for i, token in enumerate(tokens):
        if token[0] == u'ParseError':
            tokens[i] = token[0]
    return tokens
normalizeTokens.func_annotations = {}

def tokensMatch(expectedTokens, receivedTokens, ignoreErrorOrder,
                ignoreErrors=False):
    u"""Test whether the test has passed or failed

    If the ignoreErrorOrder flag is set to true we don't test the relative
    positions of parse errors and non parse errors
    """
    checkSelfClosing= False
    for token in expectedTokens:
        if (token[0] == u"StartTag" and len(token) == 4
            or token[0] == u"EndTag" and len(token) == 3):
            checkSelfClosing = True
            break

    if not checkSelfClosing:
        for token in receivedTokens:
            if token[0] == u"StartTag" or token[0] == u"EndTag":
                token.pop()

    if not ignoreErrorOrder and not ignoreErrors:
        return expectedTokens == receivedTokens
    else:
        #Sort the tokens into two groups; non-parse errors and parse errors
        tokens = {u"expected":[[],[]], u"received":[[],[]]}
        for tokenType, tokenList in izip(list(tokens.keys()),
                                         (expectedTokens, receivedTokens)):
            for token in tokenList:
                if token != u"ParseError":
                    tokens[tokenType][0].append(token)
                else:
                    if not ignoreErrors:
                        tokens[tokenType][1].append(token)
        return tokens[u"expected"] == tokens[u"received"]
tokensMatch.func_annotations = {}

def unescape(test):
    def decode(inp):
        return inp.encode(u"utf-8").decode(u"unicode-escape")
    decode.func_annotations = {}

    test[u"input"] = decode(test[u"input"])
    for token in test[u"output"]:
        if token == u"ParseError":
            continue
        else:
            token[1] = decode(token[1])
            if len(token) > 2:
                for key, value in token[2]:
                    del token[2][key]
                    token[2][decode(key)] = decode(value)
    return test
unescape.func_annotations = {}

def runTokenizerTest(test):
    warnings.resetwarnings()
    warnings.simplefilter(u"error")
    #XXX - move this out into the setup function
    #concatenate all consecutive character tokens into a single token
    if u'doubleEscaped' in test:
        test = unescape(test)

    expected = concatenateCharacterTokens(test[u'output'])            
    if u'lastStartTag' not in test:
        test[u'lastStartTag'] = None
    parser = TokenizerTestParser(test[u'initialState'], 
                                 test[u'lastStartTag'])
    tokens = parser.parse(test[u'input'])
    tokens = concatenateCharacterTokens(tokens)
    received = normalizeTokens(tokens)
    errorMsg = u"\n".join([u"\n\nInitial state:",
                          test[u'initialState'] ,
                          u"\nInput:", unicode(test[u'input']),
                          u"\nExpected:", unicode(expected),
                          u"\nreceived:", unicode(tokens)])
    errorMsg = errorMsg
    ignoreErrorOrder = test.get(u'ignoreErrorOrder', False)
    assert tokensMatch(expected, received, ignoreErrorOrder, True), errorMsg
runTokenizerTest.func_annotations = {}

def _doCapitalize(match):
    return match.group(1).upper()
_doCapitalize.func_annotations = {}

_capitalizeRe = re.compile(ur"\W+(\w)").sub

def capitalize(s):
    s = s.lower()
    s = _capitalizeRe(_doCapitalize, s)
    return s
capitalize.func_annotations = {}

def testTokenizer():
    for filename in get_data_files(u'tokenizer', u'*.test'):
        with open(filename) as fp:
            tests = json.load(fp)
            testName = os.path.basename(filename).replace(u".test",u"")
            if u'tests' in tests:
                for index,test in enumerate(tests[u'tests']):
                #Skip tests with a self closing flag
                    skip = False
                    if u'initialStates' not in test:
                        test[u"initialStates"] = [u"Data state"]
                    for initialState in test[u"initialStates"]:
                        test[u"initialState"] = capitalize(initialState)
                        yield runTokenizerTest, test
testTokenizer.func_annotations = {}
