import sys
import os
import glob
import StringIO
import unittest
import new

# XXX Allow us to import the sibling module
os.chdir(os.path.split(os.path.abspath(__file__))[0])
sys.path.insert(0, os.path.abspath(os.path.join(os.pardir, "src")))

import html5parser
#Run tests over all treebuilders
#XXX - it would be nice to automate finding all treebuilders or to allow running just one

from treebuilders import simpletree, etree, dom

treetypes = {"simpletree":simpletree.TreeBuilder,
             "ElementTree":etree.TreeBuilder,
             "DOM":dom.TreeBuilder}

#Run the parse error checks
#XXX - ideally want this to be a command line argument
checkParseErrors = True

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
    def runParserTest(self, input, output, errors, treeClass):
        #XXX - move this out into the setup function
        #concatenate all consecutive character tokens into a single token
        p = html5parser.HTMLParser(tree = treeClass)
        document = p.parse(StringIO.StringIO(input))
        errorMsg = "\n".join(["\n\nExpected:", output, "\nRecieved:",
                              convertTreeDump(p.tree.testSerializer(document))])
        self.assertEquals(output,
                          convertTreeDump(p.tree.testSerializer(document)),
                          errorMsg)
        errStr = ["Line: %i Col: %i %s"%(line, col, message) for
                  ((line,col), message) in p.errors]
        errorMsg2 = "\n".join(["\n\nInput errors:\n" + "\n".join(errors),
                               "Actual errors:\n" + "\n".join(errStr)])
        if checkParseErrors:
            self.assertEquals(len(p.errors), len(errors), errorMsg2)

def test_parser():
    for name, cls in treetypes.iteritems():
        for filename in glob.glob('tree-construction/*.dat'):
            f = open(filename)
            tests = f.read().split("#data\n")
            for test in tests:
                if test == "":
                    continue
                test = "#data\n" + test
                input, output, errors = parseTestcase(test)
                yield TestCase.runParserTest, input, output, errors, name, cls

def buildTestSuite():
    tests = 0
    for func, input, output, errors, treeName, treeCls in test_parser():
        tests += 1
        testName = 'test%d' % tests
        testFunc = lambda self, method=func, input=input, output=output, \
            errors=errors, treeCls=treeCls: method(self, input, output, errors, treeCls)
        testFunc.__doc__ = 'Parser %s Tree %s Input: %s'%(testName, treeName, input)
        instanceMethod = new.instancemethod(testFunc, None, TestCase)
        setattr(TestCase, testName, instanceMethod)
    return unittest.TestLoader().loadTestsFromTestCase(TestCase)

def main():
    buildTestSuite()
    unittest.main()

if __name__ == "__main__":
    main()
