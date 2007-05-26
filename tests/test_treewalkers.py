import sys
import os
import glob
import StringIO
import unittest
import new

try:
    import simplejson
except:
    import re
    class simplejson:
        def load(f):
            true, false = True, False
            input=re.sub(r'(".*?(?<!\\)")',r'u\1',f.read().decode('utf-8'))
            return eval(input)
        load = staticmethod(load)

sys.path.insert(0, os.path.split(os.path.abspath(__file__))[0])
from test_parser import parseTestcase

#RELEASE remove
# XXX Allow us to import the sibling module
os.chdir(os.path.split(os.path.abspath(__file__))[0])
sys.path.insert(0, os.path.abspath(os.path.join(os.pardir, "src")))

import html5parser
import serializer
#Run tests over all treewalkers/treebuilders pairs
#XXX - it would be nice to automate finding all treewalkers or to allow running just one

import treewalkers
import treebuilders
#END RELEASE

#RELEASE add
#import html5lib
#from html5lib import html5parser, serializer, treewalkers, treebuilders
#END RELEASE

treeTypes = {
"simpletree":  (treebuilders.getTreeBuilder("simpletree"),
                treewalkers.getTreeWalker("simpletree")),
"DOM":         (treebuilders.getTreeBuilder("dom"),
                treewalkers.getTreeWalker("dom")),
}

#Try whatever etree implementations are available from a list that are
#"supposed" to work
try:
    import xml.etree.ElementTree as ElementTree
    treeTypes['ElementTree'] = \
        (treebuilders.getTreeBuilder("etree", ElementTree),
         treewalkers.getTreeWalker("etree", ElementTree))
except ImportError:
    try:
        import elementtree.ElementTree as ElementTree
        treeTypes['ElementTree'] = \
            (treebuilders.getTreeBuilder("etree", ElementTree),
             treewalkers.getTreeWalker("etree", ElementTree))
    except ImportError:
        pass

try:
    import xml.etree.cElementTree as cElementTree
    treeTypes['cElementTree'] = \
        (treebuilders.getTreeBuilder("etree", cElementTree),
         treewalkers.getTreeWalker("etree", cElementTree))
except ImportError:
    try:
        import cElementTree
        treeTypes['cElementTree'] = \
            (treebuilders.getTreeBuilder("etree", cElementTree),
             treewalkers.getTreeWalker("etree", cElementTree))
    except ImportError:
        pass
    
try:
    import lxml.etree as lxml
    treeTypes['lxml'] = \
        (treebuilders.getTreeBuilder("etree", lxml),
         treewalkers.getTreeWalker("etree", lxml))
except ImportError:
    pass

try:
    import BeautifulSoup
    treeTypes["beautifulsoup"] = \
        (treebuilders.getTreeBuilder("beautifulsoup"),
         treewalkers.getTreeWalker("beautifulsoup"))
except ImportError:
    pass

def concatenateCharacterTokens(tokens):
    charactersToken = None
    for token in tokens:
        type = token["type"]
        if type in ("Characters", "SpaceCharacters"):
            if charactersToken is None:
                charactersToken = {"type": "Characters", "data": token["data"]}
            else:
                charactersToken["data"] += token["data"]
        else:
            if charactersToken is not None:
                yield charactersToken
                charactersToken = None
            yield token
    if charactersToken is not None:
        yield charactersToken

def convertTokens(tokens):
    output = []
    indent = 0
    for token in concatenateCharacterTokens(tokens):
        type = token["type"]
        if type in ("StartTag", "EmptyTag"):
            output.append(u"%s<%s>" % (" "*indent, token["name"]))
            indent += 2
            attrs = token["data"]
            if attrs:
                if hasattr(attrs, "items"):
                    attrs = attrs.items()
                attrs.sort()
                for name, value in attrs:
                    output.append(u"%s%s=\"%s\"" % (" "*indent, name, value))
            if type == "EmptyTag":
                indent -= 2
        elif type == "EndTag":
            indent -= 2
        elif type == "Comment":
            output.append("%s<!-- %s -->" % (" "*indent, token["data"]))
        elif type == "Doctype":
            output.append("%s<!DOCTYPE %s>" % (" "*indent, token["name"]))
        elif type in ("Characters", "SpaceCharacters"):
            output.append("%s\"%s\"" % (" "*indent, token["data"]))
        else:
            pass # TODO: what to do with errors?
    return u"\n".join(output)

import re
attrlist = re.compile(r"^(\s+)\w+=.*(\n\1\w+=.*)+",re.M)
def sortattrs(x):
  lines = x.group(0).split("\n")
  lines.sort()
  return "\n".join(lines)

class TestCase(unittest.TestCase):
    def runTest(self, innerHTML, input, expected, errors, treeClass):
        p = html5parser.HTMLParser(tree = treeClass[0])
        if innerHTML:
            document = p.parseFragment(StringIO.StringIO(input), innerHTML)
        else:
            document = p.parse(StringIO.StringIO(input))
        output = convertTokens(treeClass[1]().walk(document))
        output = attrlist.sub(sortattrs, output)
        expected = attrlist.sub(sortattrs, expected)
        errorMsg = "\n".join(["\n\nExpected:", expected,
                                 "\nRecieved:", output])
        self.assertEquals(expected, output, errorMsg)

def test_treewalker():
    sys.stdout.write('Testing tree walkers '+ " ".join(treeTypes.keys()) + "\n")

    for name, cls in treeTypes.iteritems():
        for filename in glob.glob('tree-construction/*.dat'):
            f = open(filename)
            tests = f.read().split("#data\n")
            for test in tests:
                if test == "":
                    continue
                test = "#data\n" + test
                innerHTML, input, expected, errors = parseTestcase(test)
                yield TestCase.runTest, innerHTML, input, expected, errors, name, cls

def buildTestSuite():
    tests = 0
    for func, innerHTML, input, expected, errors, treeName, treeCls in test_treewalker():
        tests += 1
        testName = 'test%d' % tests
        testFunc = lambda self, method=func, innerHTML=innerHTML, input=input, expected=expected, \
            errors=errors, treeCls=treeCls: method(self, innerHTML, input, expected, errors, treeCls)
        testFunc.__doc__ = 'Parser %s Tree %s Input: %s'%(testName, treeName, input)
        instanceMethod = new.instancemethod(testFunc, None, TestCase)
        setattr(TestCase, testName, instanceMethod)
    return unittest.TestLoader().loadTestsFromTestCase(TestCase)

def main():
    buildTestSuite()
    unittest.main()

if __name__ == "__main__":
    main()
