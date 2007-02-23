import sys
import os
import glob
import StringIO
import unittest
import new
import codecs

# XXX Allow us to import the sibling module
os.chdir(os.path.split(os.path.abspath(__file__))[0])
sys.path.insert(0, os.path.abspath(os.path.join(os.pardir, "src")))

import inputstream


def parseTestcase(testString):
    testString = testString.split("\n")
    try:
        if testString[0] != "#data":
            sys.stderr.write(testString)
        assert testString[0] == "#data"
    except:
        raise
    input = []
    encoding = []
    currentList = input
    for line in testString:
        if line and not (line.startswith("#encoding") or
                         line.startswith("#data")):
            currentList.append(line)
        elif line.startswith("#encoding"):
            currentList = encoding
    return "\n".join(input), encoding[0]

class TestCase(unittest.TestCase):
    def runEncodingTest(self, input, encoding):
        #XXX - move this out into the setup function
        #concatenate all consecutive character tokens into a single token
        stream = inputstream.HTMLInputStream(input)
        
        errorMsg = "\n".join(["\n\nInput", input,"\nExpected:", encoding,
                              "\nRecieved:", stream.charEncoding])
        self.assertEquals(encoding.lower(), stream.charEncoding.lower(),
                          errorMsg)

def test_encoding():
    for filename in glob.glob('encoding/*.dat'):
        f = open(filename)
        tests = f.read().split("#data\n")
        for test in tests:
            if test == "":
                continue
            test = "#data\n" + test
            input, encoding = parseTestcase(test)
            yield TestCase.runEncodingTest, input, encoding

def buildTestSuite():
    tests = 0
    for func, input, encoding in test_encoding():
        tests += 1
        testName = 'test%d' % tests
        testFunc = lambda self, method=func, input=input, encoding=encoding, \
            : method(self, input, encoding)
        testFunc.__doc__ = 'Encoding %s'%(testName)
        instanceMethod = new.instancemethod(testFunc, None, TestCase)
        setattr(TestCase, testName, instanceMethod)
    return unittest.TestLoader().loadTestsFromTestCase(TestCase)

def main():   
    buildTestSuite()
    unittest.main()

if __name__ == "__main__":
    main()