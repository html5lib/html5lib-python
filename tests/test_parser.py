import sys
import os
import glob
import StringIO
import unittest
import new

#Allow us to import the parent module
os.chdir(os.path.split(os.path.abspath(__file__))[0])
sys.path.insert(0, os.path.abspath(os.pardir))

import parser

def testParser(testString):
    testString = testString.split("\n")
    try:
        assert testString[0] == "#data"
    except:
        raise
    input = []
    output = []
    errors = []
    currentList = input
    for line in testString:
        if line and line[0] != "#":
            if currentList is output:
                assert line[0] == "|"
                currentList.append(line[1:])
            else:
                currentList.append(line)
        elif line == "#errors":
            currentList = errors
        elif line == "#document":
            currentList = output
    return "\n".join(input), "\n".join(output), errors

def test_parser():
    for filename in glob.glob('tree-construction/*.dat'):
        f = file(filename)
        test = []
        lastLine = ""
        for line in f:
            #Assume tests are seperated by a blank line
            if not (line == "\n" and lastLine[0] == "|"):
                #Strip out newlinw characters from the end of the string
                test.append(line[:-1])
            else:
                input, output, errors = testParser("\n".join(test))
                yield TestCase.runParserTest, input, output, errors
                test = []
            lastLine = line

class TestCase(unittest.TestCase):
    def runParserTest(self, input, output, errors):
        #XXX - move this out into the setup function
        #concatenate all consecutive character tokens into a single token
        p = parser.HTMLParser()
        document = p.parse(StringIO.StringIO(input))
        try:
            #Need a check on the number of parse errors here
            print str(document)
            self.assertTrue(output == str(document))
        except AssertionError:
            raise
def main():
    failed = 0
    tests = 0
    for func, input, output, errors in test_parser():
        tests += 1
        testName = 'test%d' % tests
        def testFunc(self, method=func, input=input,
                     output=output, errors=errors):
            method(self, input, output, errors)
        testFunc.__doc__ = "\t".join([str(input)]) 
        instanceMethod = new.instancemethod(testFunc, None, TestCase)
        setattr(TestCase, testName, instanceMethod)
    unittest.main()

if __name__ == "__main__":
    main()
