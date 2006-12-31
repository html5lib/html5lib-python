import sys
import os
import glob
import StringIO
import unittest
import new

# XXX Allow us to import the sibling module
os.chdir(os.path.split(os.path.abspath(__file__))[0])
sys.path.insert(0, os.path.abspath(os.path.join(os.pardir, "src")))

import parser
import treebuilders

def parseTestcase(testString):
    testString = testString.split("\n")
    try:
        if testString[0] != "#data":
            print testString
        assert testString[0] == "#data"
    except:
        raise
    input = []
    output = []
    errors = []
    currentList = input
    for line in testString:
        if line and not (line.startswith("#errors") or
          line.startswith("#document") or line.startswith("#data")):
            if currentList is output:
                if line.startswith("|"):
                    currentList.append(line[2:])
                else:
                    currentList.append(line)
            else:
                currentList.append(line)
        elif line == "#errors":
            currentList = errors
        elif line == "#document":
            currentList = output
    return "\n".join(input), "\n".join(output), errors

def convertTreeDump(treedump):
    """convert the output of str(document) to the format used in the testcases"""
    treedump = treedump.split("\n")[1:]
    rv = []
    for line in treedump:
        if line.startswith("|"):
            rv.append(line[3:])
        else:
            rv.append(line)
    return "\n".join(rv)

class TestCase(unittest.TestCase):
    def runParserTest(self, input, output, errors):
        #XXX - move this out into the setup function
        #concatenate all consecutive character tokens into a single token
        from treebuilders import etree
        treebuilder = etree.TreeBuilder

        p = parser.HTMLParser(tree = treebuilder)
        document = p.parse(StringIO.StringIO(input))
        errorMsg = "\n".join(["\n\nExpected:", output, "\nRecieved:",
          convertTreeDump(p.tree.testSerializer(document))])
        self.assertEquals(output, 
                          convertTreeDump(p.tree.testSerializer(document)),
                          errorMsg)
        #errorMsg2 = "\n".join(["\n\nInput errors:\n" + "\n".join(errors),
        #  "Actual errors:\n" + "\n".join(p.errors)])
        #self.assertEquals(len(p.errors), len(errors), errorMsg2)

def test_parser():
    for filename in glob.glob('tree-construction/*.dat'):
        f = open(filename)
        tests = f.read().split("#data\n")
        for test in tests:
            if test == "":
                continue
            test = "#data\n" + test
            input, output, errors = parseTestcase(test)
            yield TestCase.runParserTest, input, output, errors

def buildTestSuite():
    tests = 0
    for func, input, output, errors in test_parser():
        tests += 1
        testName = 'test%d' % tests
        testFunc = lambda self, method=func, input=input, output=output, \
            errors=errors: method(self, input, output, errors)
        testFunc.__doc__ = 'Parser %s: %s' % (testName, input)
        instanceMethod = new.instancemethod(testFunc, None, TestCase)
        setattr(TestCase, testName, instanceMethod)
    return unittest.TestLoader().loadTestsFromTestCase(TestCase)

def main():
    buildTestSuite()
    unittest.main()

if __name__ == "__main__":
    # XXX Allow us to import the sibling module
    os.chdir(os.path.split(os.path.abspath(__file__))[0])
    sys.path.insert(0, os.path.abspath(os.path.join(os.pardir, "src")))
    main()
