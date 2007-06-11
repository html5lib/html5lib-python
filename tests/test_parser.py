import sys
import StringIO
import unittest
from support import html5lib_test_files

#RELEASE remove
import html5parser
#Run tests over all treebuilders
#XXX - it would be nice to automate finding all treebuilders or to allow running just one

import treebuilders
#END RELEASE

#RELEASE add
#import html5lib
#from html5lib import html5parser
#from html5lib.treebuilders import simpletree, etreefull, dom
#END RELEASE

treeTypes = {"simpletree":treebuilders.getTreeBuilder("simpletree"),
             "DOM":treebuilders.getTreeBuilder("dom")}

#Try whatever etree implementations are avaliable from a list that are
#"supposed" to work
try:
    import xml.etree.ElementTree as ElementTree
    treeTypes['ElementTree'] = treebuilders.getTreeBuilder("etree", ElementTree, fullTree=True)
except ImportError:
    try:
        import elementtree.ElementTree as ElementTree
        treeTypes['ElementTree'] = treebuilders.getTreeBuilder("etree", ElementTree, fullTree=True)
    except ImportError:
        pass

try:
    import xml.etree.cElementTree as cElementTree
    treeTypes['cElementTree'] = treebuilders.getTreeBuilder("etree", cElementTree, fullTree=True)
except ImportError:
    try:
        import cElementTree
        treeTypes['cElementTree'] = treebuilders.getTreeBuilder("etree", cElementTree, fullTree=True)
    except ImportError:
        pass
    
try:
    import lxml.etree as lxml
    treeTypes['lxml'] = treebuilders.getTreeBuilder("etree", lxml, fullTree=True)
except ImportError:
    pass

try:
    import BeautifulSoup
    treeTypes["beautifulsoup"] = treebuilders.getTreeBuilder("beautifulsoup", fullTree=True)
except ImportError:
    pass

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
    expected = []
    errors = []
    currentList = input
    for line in testString:
        if line and not (line.startswith("#errors") or
          line.startswith("#document") or line.startswith("#data") or
          line.startswith("#document-fragment")):
            if currentList is expected:
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
            currentList = expected
    return innerHTML, "\n".join(input), "\n".join(expected), errors

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

import re
attrlist = re.compile(r"^(\s+)\w+=.*(\n\1\w+=.*)+",re.M)
def sortattrs(x):
  lines = x.group(0).split("\n")
  lines.sort()
  return "\n".join(lines)

class TestCase(unittest.TestCase):
    def runParserTest(self, innerHTML, input, expected, errors, treeClass):
        #XXX - move this out into the setup function
        #concatenate all consecutive character tokens into a single token
        p = html5parser.HTMLParser(tree = treeClass)
        if innerHTML:
            document = p.parseFragment(StringIO.StringIO(input), innerHTML)
        else:
            document = p.parse(StringIO.StringIO(input))
        output = convertTreeDump(p.tree.testSerializer(document))
        output = attrlist.sub(sortattrs, output)
        expected = attrlist.sub(sortattrs, expected)
        errorMsg = "\n".join(["\n\nExpected:", expected,
                                 "\nRecieved:", output])
        self.assertEquals(expected, output, errorMsg)
        errStr = ["Line: %i Col: %i %s"%(line, col, message) for
                  ((line,col), message) in p.errors]
        errorMsg2 = "\n".join(["\n\nInput errors:\n" + "\n".join(errors),
                               "Actual errors:\n" + "\n".join(errStr)])
        if checkParseErrors:
            self.assertEquals(len(p.errors), len(errors), errorMsg2)

def test_parser():
    sys.stdout.write('Testing tree builders '+ " ".join(treeTypes.keys()) + "\n")
    for name, cls in treeTypes.iteritems():
        for filename in html5lib_test_files('tree-construction'):
            f = open(filename)
            tests = f.read().split("#data\n")
            for test in tests:
                if test == "":
                    continue
                test = "#data\n" + test
                innerHTML, input, expected, errors = parseTestcase(test)
                yield TestCase.runParserTest, innerHTML, input, expected, errors, name, cls

def buildTestSuite():
    tests = 0
    for func, innerHTML, input, expected, errors, treeName, treeCls in test_parser():
        tests += 1
        testName = 'test%d' % tests
        testFunc = lambda self, method=func, innerHTML=innerHTML, input=input, expected=expected, \
            errors=errors, treeCls=treeCls: method(self, innerHTML, input, expected, errors, treeCls)
        testFunc.__doc__ = 'Parser %s Tree %s Input: %s'%(testName, treeName, input)
        setattr(TestCase, testName, testFunc)
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
