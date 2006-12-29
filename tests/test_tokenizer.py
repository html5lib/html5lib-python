import sys
import os
import glob
import StringIO
import unittest
import new

import simplejson

#Allow us to import the parent module
os.chdir(os.path.split(os.path.abspath(__file__))[0])
sys.path.insert(0, os.path.abspath(os.path.join(os.pardir, "src")))

from tokenizer import HTMLTokenizer

class TokenizerTestParser(object):
    def parse(self, stream, innerHTML=False):
        self.outputTokens = []

        self.tokenizer = HTMLTokenizer(stream)

        for token in self.tokenizer:
            getattr(self, 'process%s' % token["type"])(token)

        return self.outputTokens

    def processDoctype(self, token):
        self.outputTokens.append([u"DOCTYPE", token["name"], token["data"]])

    def processStartTag(self, token):
        self.outputTokens.append([u"StartTag", token["name"], token["data"]])

    def processEndTag(self, token):
        self.outputTokens.append([u"EndTag", token["name"]])

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
        self.outputTokens.append(u"ParseError")

    def processAtheistParseError(self, token):
        """This error is not an error"""
        pass

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

def tokensMatch(expectedTokens, recievedTokens):
    """Test whether the test has passed or failed

    For brevity in the tests, the test has passed if the sequence of expected
    tokens appears anywhere in the sequence of returned tokens.
    """
    return expectedTokens == recievedTokens
    for i, token in enumerate(recievedTokens):
        if expectedTokens[0] == token:
            if (len(expectedTokens) <= len(recievedTokens[i:]) and
                recievedTokens[i:i+len(expectedTokens)]):
                return True
    return False


class TestCase(unittest.TestCase):
    def runTokenizerTest(self, input, output):
        #XXX - move this out into the setup function
        #concatenate all consecutive character tokens into a single token
        output = concatenateCharacterTokens(output)
        parser = TokenizerTestParser()
        tokens = parser.parse(input)
        tokens = concatenateCharacterTokens(tokens)
        errorMsg = "\n".join(["\n\nExpected:", str(output), "\nRecieved:",
                             str(tokens)])
        self.assertEquals(tokensMatch(tokens, output), True, errorMsg)


def test_tokenizer():
    for filename in glob.glob('tokenizer/*.test'):
        tests = simplejson.load(file(filename))
        for test in tests['tests']:
            yield (TestCase.runTokenizerTest, test['description'],
                   test['input'], test['output'])

def buildTestSuite():
    tests = 0
    for func, desc, input, output in test_tokenizer():
        tests += 1
        testName = 'test%d' % tests
        testFunc = lambda self, method=func, input=input, output=output: \
            method(self, input, output)
        testFunc.__doc__ = "\t".join([desc, str(input), str(output)])
        instanceMethod = new.instancemethod(testFunc, None, TestCase)
        setattr(TestCase, testName, instanceMethod)
    return unittest.TestLoader().loadTestsFromTestCase(TestCase)

def main():
    buildTestSuite()
    unittest.main()

if __name__ == "__main__":
    main()
