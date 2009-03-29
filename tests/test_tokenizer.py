import sys
import os
import unittest
import cStringIO
import warnings

from support import simplejson, html5lib_test_files

from html5lib.tokenizer import HTMLTokenizer
from html5lib import constants

class TokenizerTestParser(object):
    def __init__(self, contentModelFlag, lastStartTag=None):
        self.tokenizer = HTMLTokenizer
        self._contentModelFlag = constants.contentModelFlags[contentModelFlag]
        self._lastStartTag = lastStartTag

    def parse(self, stream, encoding=None, innerHTML=False):
        tokenizer = self.tokenizer(stream, encoding)
        self.outputTokens = []

        tokenizer.contentModelFlag = self._contentModelFlag
        if self._lastStartTag is not None:
            tokenizer.currentToken = {"type": "startTag", 
                                      "name":self._lastStartTag}

        types = dict((v,k) for k,v in constants.tokenTypes.iteritems())
        for token in tokenizer:
            getattr(self, 'process%s' % types[token["type"]])(token)

        return self.outputTokens

    def processDoctype(self, token):
        self.outputTokens.append([u"DOCTYPE", token["name"], token["publicId"],
                                  token["systemId"], token["correct"]])

    def processStartTag(self, token):
        self.outputTokens.append([u"StartTag", token["name"], 
                                  dict(token["data"][::-1]), token["selfClosing"]])

    def processEmptyTag(self, token):
        if token["name"] not in constants.voidElements:
            self.outputTokens.append(u"ParseError")
        self.outputTokens.append([u"StartTag", token["name"], dict(token["data"][::-1])])

    def processEndTag(self, token):
        self.outputTokens.append([u"EndTag", token["name"], 
                                  token["selfClosing"]])

    def processComment(self, token):
        self.outputTokens.append([u"Comment", token["data"]])

    def processSpaceCharacters(self, token):
        self.outputTokens.append([u"Character", token["data"]])
        self.processSpaceCharacters = self.processCharacters

    def processCharacters(self, token):
        self.outputTokens.append([u"Character", token["data"]])

    def processEOF(self, token):
        pass

    def processParseError(self, token):
        self.outputTokens.append([u"ParseError", token["data"]])

def concatenateCharacterTokens(tokens):
    outputTokens = []
    for token in tokens:
        if not "ParseError" in token and token[0] == "Character":
            if (outputTokens and not "ParseError" in outputTokens[-1] and
                outputTokens[-1][0] == "Character"):
                outputTokens[-1][1] += token[1]
            else:
                outputTokens.append(token)
        else:
            outputTokens.append(token)
    return outputTokens

def normalizeTokens(tokens):
    # TODO: convert tests to reflect arrays
    for i, token in enumerate(tokens):
        if token[0] == u'ParseError':
            tokens[i] = token[0]
    return simplejson.loads(simplejson.dumps(tokens))

def tokensMatch(expectedTokens, receivedTokens, ignoreErrorOrder):
    """Test whether the test has passed or failed

    If the ignoreErrorOrder flag is set to true we don't test the relative
    positions of parse errors and non parse errors
    """
    checkSelfClosing= False
    for token in expectedTokens:
        if (token[0] == "StartTag" and len(token) == 4
            or token[0] == "EndTag" and len(token) == 3):
            checkSelfClosing = True
            break

    if not checkSelfClosing:
        for token in receivedTokens:
            if token[0] == "StartTag" or token[0] == "EndTag":
                token.pop()

    if not ignoreErrorOrder:    
        return expectedTokens == receivedTokens
    else:
        #Sort the tokens into two groups; non-parse errors and parse errors
        tokens = {"expected":[[],[]], "received":[[],[]]}
        for tokenType, tokenList in zip(tokens.keys(),
                                         (expectedTokens, receivedTokens)):
            for token in tokenList:
                if token != "ParseError":
                    tokens[tokenType][0].append(token)
                else:
                    tokens[tokenType][1].append(token)
        
        return tokens["expected"] == tokens["received"]


class TestCase(unittest.TestCase):
    def runTokenizerTest(self, test):
        #XXX - move this out into the setup function
        #concatenate all consecutive character tokens into a single token
        expected = concatenateCharacterTokens(test['output'])
        if 'lastStartTag' not in test:
            test['lastStartTag'] = None
        outBuffer = cStringIO.StringIO()
        stdout = sys.stdout
        sys.stdout = outBuffer
        parser = TokenizerTestParser(test['contentModelFlag'], 
                                     test['lastStartTag'])
        tokens = parser.parse(test['input'])
        tokens = concatenateCharacterTokens(tokens)
        received = normalizeTokens(tokens)
        errorMsg = u"\n".join(["\n\nContent Model Flag:",
                              test['contentModelFlag'] ,
                              "\nInput:", unicode(test['input']),
                              "\nExpected:", unicode(expected),
                              "\nreceived:", unicode(tokens)])
        errorMsg = errorMsg.encode("utf-8")
        ignoreErrorOrder = test.get('ignoreErrorOrder', False)
        self.assertEquals(tokensMatch(expected, received, ignoreErrorOrder), 
                          True, errorMsg)

def buildTestSuite():
    for filename in html5lib_test_files('tokenizer', '*.test'):
        print filename
        tests = simplejson.load(file(filename))
        testName = os.path.basename(filename).replace(".test","")
        if 'tests' in tests:
            for index,test in enumerate(tests['tests']):
                #Skip tests with a self closing flag
                skip = False
                if 'contentModelFlags' not in test:
                    test["contentModelFlags"] = ["PCDATA"]
                for contentModelFlag in test["contentModelFlags"]:
                    test["contentModelFlag"] = contentModelFlag
                    def testFunc(self, test=test):
                        self.runTokenizerTest(test)
                    testFunc.__doc__ = "\t".join([testName, 
                                                  test['description']])
                    setattr(TestCase, 'test_%s_%d' % (testName, index), testFunc)
    return unittest.TestLoader().loadTestsFromTestCase(TestCase)

def main():
    buildTestSuite()
    unittest.main()

if __name__ == "__main__":
    main()
