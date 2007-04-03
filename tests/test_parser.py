import sys
import os
import glob
import StringIO
import unittest
import new

#RELEASE remove
# XXX Allow us to import the sibling module
os.chdir(os.path.split(os.path.abspath(__file__))[0])
sys.path.insert(0, os.path.abspath(os.path.join(os.pardir, "src")))

import html5parser
#Run tests over all treebuilders
#XXX - it would be nice to automate finding all treebuilders or to allow running just one

from treebuilders import simpletree, etreefull, dom
#END RELEASE

#RELEASE add
#import html5lib
#from html5lib import html5parser
#from html5lib.treebuilders import simpletree, etreefull, dom
#END RELEASE

treetypes = {"simpletree":simpletree.TreeBuilder,
             "DOM":dom.TreeBuilder}

if hasattr(etreefull, "ElementTree"):
    treetypes["ElementTree"]=etreefull.TreeBuilder
else:
    sys.stderr.write('module ElementTree not found, skipping etree tests')

#Run the parse error checks
checkParseErrors = False

def parseTestcase(testString):
    testString = testString.split("\n")
    try:
        if testString[0] != "#data":
            sys.stderr.write(testString)
        assert testString[0] == "#data"
    except:
        raise
    innerHTML = False
    input = []
    output = []
    errors = []
    currentList = input
    for line in testString:
        if line and not (line.startswith("#errors") or
          line.startswith("#document") or line.startswith("#data") or
          line.startswith("#document-fragment")):
            if currentList is output:
                if line.startswith("|"):
                    currentList.append(line[2:])
                else:
                    currentList.append(line)
            else:
                currentList.append(line)
        elif line == "#errors":
            currentList = errors
        elif line == "#document" or line.startswith("#document-fragment"):
            if line.startswith("#document-fragment"):
                innerHTML = line[19:]
                if not innerHTML:
                    sys.stderr.write(testString)
                assert innerHTML
            currentList = output
    return innerHTML, "\n".join(input), "\n".join(output), errors

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
    def runParserTest(self, innerHTML, input, output, errors, treeClass):
        #XXX - move this out into the setup function
        #concatenate all consecutive character tokens into a single token
        p = html5parser.HTMLParser(tree = treeClass)
        if innerHTML:
            document = p.parseFragment(StringIO.StringIO(input), innerHTML)
        else:
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
                innerHTML, input, output, errors = parseTestcase(test)
                yield TestCase.runParserTest, innerHTML, input, output, errors, name, cls

def buildTestSuite():
    tests = 0
    for func, innerHTML, input, output, errors, treeName, treeCls in test_parser():
        tests += 1
        testName = 'test%d' % tests
        testFunc = lambda self, method=func, innerHTML=innerHTML, input=input, output=output, \
            errors=errors, treeCls=treeCls: method(self, innerHTML, input, output, errors, treeCls)
        testFunc.__doc__ = 'Parser %s Tree %s Input: %s'%(testName, treeName, input)
        instanceMethod = new.instancemethod(testFunc, None, TestCase)
        setattr(TestCase, testName, instanceMethod)
    return unittest.TestLoader().loadTestsFromTestCase(TestCase)

def main():
    # the following is temporary while the unit tests for parse errors are
    # still in flux
    if '-p' in sys.argv: # suppress check for parse errors
        sys.argv.remove('-p')
        global checkParseErrors
        checkParseErrors = False
       
    buildTestSuite()
    unittest.main()

if __name__ == "__main__":
    main()
