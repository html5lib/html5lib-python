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

def loadTests(f):
    for i, line in enumerate(f):
        if line and not line[0] == "#":
            testList = eval(line)
            yield i+1, tuple(testList)

def test_tokenizer():
    for filename in glob.glob('tokenizer/*.test'):
        tests = simplejson.load(file(filename))
        for test in tests['tests']:
            yield runTokenizerTest, test['description'], test['input'], test['output']

def runTokenizerTest(description, input, output):
    #XXX - move this out into the setup function
    parser = TokenizerTestParser()
    tokens = parser.parse(StringIO.StringIO(input))
    try:
        assert tokens == output
    except AssertionError:
        print "Failed test %s"%(description,)
        print "Got", tokens, "expected", output
        return False
    return True

def main():
    failed = 0
    tests = 0
    for func, desc, input, output in test_tokenizer():
        tests += 1
        passed = func(desc, input, output)
        if not passed: failed +=1
    print "Ran %i tests, failed %i"%(tests, failed)

if __name__ == "__main__":
    main()
