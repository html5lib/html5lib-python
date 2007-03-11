import sys
import os
import glob
import StringIO
import unittest
import new
import codecs

#RELEASE remove
# XXX Allow us to import the sibling module
os.chdir(os.path.split(os.path.abspath(__file__))[0])
sys.path.insert(0, os.path.abspath(os.path.join(os.pardir, "src")))

import inputstream
#END RELEASE

#RELEASE add
#import html5lib
#from html5lib import inputstream
#END RELEASE

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
        stream = inputstream.HTMLInputStream(input, chardet=False)
        
        errorMsg = "\n".join(["\n\nInput", input,"\nExpected:", encoding,
                              "\nRecieved:", stream.charEncoding])
        self.assertEquals(encoding.lower(), stream.charEncoding.lower(),
                          errorMsg)

class ChardetTest(unittest.TestCase):
    def testChardet(self):
        f = open("encoding/chardet/test_big5.txt")
        stream = inputstream.HTMLInputStream(f.read(), chardet=True)
        self.assertEquals("big5", stream.charEncoding.lower(),
                          "Chardet failed: expected big5 got "+
                          stream.charEncoding.lower())

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
    testSuite = unittest.TestLoader().loadTestsFromTestCase(TestCase)
    try:
        import chardet
        testSuite.addTest(ChardetTest('testChardet'))  
    except ImportError:
        print "chardet not found, skipping chardet tests"
    return testSuite

def main():
    unittest.main(defaultTest="buildTestSuite")

if __name__ == "__main__":
    main()