import sys

from parser import *

class HTMLParser(object):
    """Main parser class"""

    def __init__(self, output=sys.stdout):
        #Raise an exception on the first error encountered
        self.output = output


    def parse(self, stream):
        """Stream should be a stream of unicode bytes. Character encoding
        issues have not yet been dealt with."""

        self.tokenizer = tokenizer.HTMLTokenizer(self)
        self.tokenizer.tokenize(stream)

    def processDoctype(self, name, error):
        if self.output is not None: 
            self.output.write("DOCTYPE:", name, error)

    def processStartTag(self, name, attributes):
        if self.output is not None: 
            self.output.write("StartTag:", name, attributes)

    def processEndTag(self, name):
        if self.output is not None: 
            self.output.write("EndTag:", name)

    def processComment(self, data):
        if self.output is not None: 
            self.output.write("Comment:", data)

    def processCharacter(self, data):
        if self.output is not None:
            self.output.write("Character:", data)
        
    def processEOF(self):
        if self.output is not None:
            self.output.write("EOF")

    def parseError(self):
        if self.output is not None:
            self.output.write("Parse Error")

    def atheistParseError(self):
        """This error is not an error"""
        if self.output is not None:
            self.output.write("Atheist Parse Error")

if __name__ == "__main__":
    x = HTMLParser()
    if len(sys.argv) > 1:
        x.parse(open(sys.argv[1]))
    else:
        print "Usage: python mockParser.py filename"
