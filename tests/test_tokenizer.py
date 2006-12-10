import sys
import glob
import StringIO

import simplejson

#Allow us to import the parent module
sys.path.insert(0, "../")

import tokenizer

class TokenizerTestParser(object):
    def parse(self, stream, innerHTML=False):
        """Stream should be a stream of unicode bytes. Character encoding
        issues have not yet been dealt with."""

        self.outputTokens = []        

        self.tokenizer = tokenizer.HTMLTokenizer(self)
        self.tokenizer.tokenize(stream)
        
        return self.outputTokens

    def processDoctype(self, name, error):
        self.outputTokens.append([u"DOCTYPE", name, error])

    def processStartTag(self, name, attributes):
        self.outputTokens.append([u"StartTag", name, attributes])

    def processEndTag(self, name):
        self.outputTokens.append([u"EndTag", name])

    def processComment(self, data):
        self.outputTokens.append([u"Comment", data])

    def processCharacter(self, data):
        self.outputTokens.append([u"Character", data])
        
    def processEOF(self):
        pass

    def parseError(self):
        self.outputTokens.append(u"ParseError")

    def atheistParseError(self):
        """This error is not an error"""
        self.outputTokens.append(u"AtheistParseError")

def concatanateCharacterTokens(tokens):
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
    tokens appears anywhere in the sequqnce of returned tokens.
    """
    return expectedTokens == recievedTokens
    for i, token in enumerate(recievedTokens):
        if expectedTokens[0] == token:
            if (len(expectedTokens) <= len(recievedTokens[i:]) and
                recievedTokens[i:i+len(expectedTokens)]):
                return True
    return False
        

def test_tokenizer():
    for filename in glob.glob('tokenizer/*.test'):
        tests = simplejson.load(file(filename))
        for test in tests['tests']:
            yield (runTokenizerTest, test['description'], test['input'], 
                   test['output'])

def runTokenizerTest(description, input, output):
    #XXX - move this out into the setup function
    #concatanate all consecutive character tokens into a single token
    output = concatanateCharacterTokens(output)
    parser = TokenizerTestParser()
    tokens = parser.parse(StringIO.StringIO(input))
    tokens = concatanateCharacterTokens(tokens)
    print "Got", tokens, "expected", output
    assert tokensMatch(tokens, output)

def main():
    failed = 0
    tests = 0
    for func, desc, input, output in test_tokenizer():
        tests += 1
        try:
            func(desc, input, output)
        except AssertionError:
            print "Failed test %s"%(desc,)
            parser = TokenizerTestParser()
            tokens = parser.parse(StringIO.StringIO(input))
            print "Got", tokens, "expected", output
            failed +=1
    print "Ran %i tests, failed %i"%(tests, failed)

if __name__ == "__main__":
    main()
