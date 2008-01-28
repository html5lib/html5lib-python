import os
import sys
import traceback
import StringIO
import unittest
import warnings

warnings.simplefilter("error")

from support import html5lib_test_files, TestData, convert, convertExpected
from html5lib import html5parser, treebuilders, constants

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
    try:
        import lxml.html as lxml
    except ImportError:
        import lxml.etree as lxml
    treeTypes['lxml'] = treebuilders.getTreeBuilder("lxml", lxml, fullTree=True)
except ImportError:
    pass

try:
    import BeautifulSoup
    treeTypes["beautifulsoup"] = treebuilders.getTreeBuilder("beautifulsoup", fullTree=True)
except ImportError:
    pass

#Run the parse error checks
checkParseErrors = False # TODO

#XXX - There should just be one function here but for some reason the testcase
#format differs from the treedump format by a single space character
def convertTreeDump(data):
    return "\n".join(convert(3)(data).split("\n")[1:])

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
        
        try:
            if innerHTML:
                document = p.parseFragment(StringIO.StringIO(input), innerHTML)
            else:
                try:
                    document = p.parse(StringIO.StringIO(input))
                except constants.DataLossWarning:
                    sys.stderr.write("Test input causes known dataloss, skipping")
                    return 
        except:
            errorMsg = "\n".join(["\n\nInput:", input, "\nExpected:", expected,
                                  "\nTraceback:", traceback.format_exc()])
            self.assertTrue(False, errorMsg)
        
        output = convertTreeDump(p.tree.testSerializer(document))
        output = attrlist.sub(sortattrs, output)
        
        expected = convertExpected(expected)
        expected = attrlist.sub(sortattrs, expected)
        errorMsg = "\n".join(["\n\nInput:", input, "\nExpected:", expected,
                              "\nRecieved:", output])
        self.assertEquals(expected, output, errorMsg)
        errStr = ["Line: %i Col: %i %s"%(line, col, constants.E[errorcode] % datavars) for
                  ((line,col), errorcode, datavars) in p.errors]
        errorMsg2 = "\n".join(["\n\nInput errors (" + str(len(errors)) + "):\n" + "\n".join(errors),
                               "Actual errors (" + str(len(p.errors)) + "):\n" + "\n".join(errStr)])
        self.assertEquals(len(p.errors), len(errors), errorMsg2)

def buildTestSuite():
    sys.stdout.write('Testing tree builders '+ " ".join(treeTypes.keys()) + "\n")

    for treeName, treeCls in treeTypes.iteritems():
        for filename in html5lib_test_files('tree-construction'):
            testName = os.path.basename(filename).replace(".dat","")

            tests = TestData(filename, "data")

            for index, test in enumerate(tests):
                input, errors, innerHTML, expected = [test[key] for key in
                                                      'data', 'errors',
                                                      'document-fragment',
                                                      'document']
                if errors:
                    errors = errors.split("\n")
                def testFunc(self, innerHTML=innerHTML, input=input,
                    expected=expected, errors=errors, treeCls=treeCls): 
                    return self.runParserTest(innerHTML, input, expected, errors, treeCls)
                setattr(TestCase, "test_%s_%d_%s" % (testName,index+1,treeName),
                     testFunc)

    return unittest.TestLoader().loadTestsFromTestCase(TestCase)

def main():
    # the following is temporary while the unit tests for parse errors are
    # still in flux
    if '-p' in sys.argv: # suppress check for parse errors
        sys.argv.remove('-p')
        global checkParseErrors
        checkParseErrors = True
       
    buildTestSuite()
    unittest.main()

if __name__ == "__main__":
    main()
