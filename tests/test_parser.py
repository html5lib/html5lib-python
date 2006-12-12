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

def parseTestcase(testString):
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
                currentList.append(line[2:])
                # XXX the line might not start with a "|" if it's a
                # continuation line, e.g. if a text node contained a linefeed
            else:
                currentList.append(line)
        elif line == "#errors":
            currentList = errors
        elif line == "#document":
            currentList = output
    return "\n".join(input), "\n".join(output), errors

def convertTreeDump(treedump):
    """convert the output of str(document) to the format used in the testcases"""
    treedump = treedump.split("\n")
    rv = []
    for line in treedump:
        if line.startswith("#document"):
            pass
        else:
            rv.append(line[3:])
    return "\n".join(rv)

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
                input, output, errors = parseTestcase("\n".join(test))
                yield runParserTest, input, output, errors
                test = []
            lastLine = line

def runParserTest(input, output, errors):
    #XXX - move this out into the setup function
    #concatenate all consecutive character tokens into a single token
    p = parser.HTMLParser()
    document = p.parse(StringIO.StringIO(input))
    try:
        #Need a check on the number of parse errors here
        assert output == convertTreeDump(document.printTree())
    except AssertionError:
        print "input"
        print input
        print "expected output"
        print output
        print "recieved"
        print convertTreeDump(document.printTree())
        print ""
        raise

def main():
    failed = 0
    tests = 0
    for func, input, output, errors in test_parser():
        tests += 1
        testName = 'test%d' % tests
        try:
            runParserTest(input, output, errors)
        except AssertionError:
            failed += 1

    print "Ran %i tests, failed %i"%(tests, failed)

#         def testFunc(self, method=func, input=input,
#                      output=output, errors=errors):
#             method(self, input, output, errors)
#         testFunc.__doc__ = "\t".join([str(input)]) 
#         instanceMethod = new
#        setattr(TestCase, testName, instanceMethod)
#   unittest.main()

if __name__ == "__main__":
    main()
