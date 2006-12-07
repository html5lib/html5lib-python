import sys
import glob
import StringIO

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
        self.outputTokens.append(["DOCTYPE", name, error])

    def processStartTag(self, name, attributes):
        self.outputTokens.append(["StartTag", name, attributes])

    def processEndTag(self, name):
        self.outputTokens.append(["EndTag", name])

    def processComment(self, data):
        self.outputTokens.append(["Comment", data])

    def processCharacter(self, data):
        self.outputTokens.append(["Character", data])
        
    def processEOF(self):
        pass

    def parseError(self):
        self.outputTokens.append("ParseError")

    def atheistParseError(self):
        """This error is not an error"""
        self.outputTokens.append("AtheistParseError")

def loadTests(f):
    for i, line in enumerate(f):
        if line and not line[0] == "#":
            testList = eval(line)
            yield i+1, tuple(testList)

def testTokenizer():
    parser = TokenizerTestParser()
    for filename in glob.glob('tokenizer/*.test'):
        for i, (input, output, description)  in loadTests(open(filename)):
            tokens = parser.parse(StringIO.StringIO(input))
            try:
                assert tokens == output
            except AssertionError:
                print "Failed test on line %i, %s"%(i, description)
                print "Got", tokens, "expected", output 
