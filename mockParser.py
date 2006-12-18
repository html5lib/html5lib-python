import sys

from tokenizer import HTMLTokenizer

class HTMLParser(object):
    """ Fake parser to test tokenizer output """
    def parse(self, stream):
        tokenizer = HTMLTokenizer(stream)
        for token in tokenizer:
            print token

if __name__ == "__main__":
    x = HTMLParser()
    if len(sys.argv) > 1:
        x.parse(sys.argv[1])
    else:
        print "Usage: python mockParser.py filename"
