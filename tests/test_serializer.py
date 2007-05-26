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
import serializer
#Run tests over all treewalkers
#XXX - it would be nice to automate finding all treewalkers or to allow running just one

import treewalkers
#END RELEASE

#RELEASE add
#import html5lib
#from html5lib import html5parser, serializer, treewalkers
#END RELEASE

treeTypes = {"simpletree":treewalkers.getTreeWalker("simpletree"),
             "DOM":treewalkers.getTreeWalker("dom")}

#Try whatever etree implementations are available from a list that are
#"supposed" to work
try:
    import xml.etree.ElementTree as ElementTree
    treeTypes['ElementTree'] = treewalkers.getTreeWalker("etree", ElementTree)
except ImportError:
    try:
        import elementtree.ElementTree as ElementTree
        treeTypes['ElementTree'] = treewalkers.getTreeWalker("etree", ElementTree)
    except ImportError:
        pass

try:
    import xml.etree.cElementTree as cElementTree
    treeTypes['cElementTree'] = treewalkers.getTreeWalker("etree", cElementTree)
except ImportError:
    try:
        import cElementTree
        treeTypes['cElementTree'] = treewalkers.getTreeWalker("etree", cElementTree)
    except ImportError:
        pass
    
try:
    import lxml.etree as lxml
    treeTypes['lxml'] = treewalkers.getTreeWalker("etree", lxml)
except ImportError:
    pass

try:
    import BeautifulSoup
    treeTypes["beautifulsoup"] = treewalkers.getTreeWalker("beautifulsoup")
except ImportError:
    pass

sys.stdout.write('Testing trees '+ " ".join(treeTypes.keys()) + "\n")

#Run the serialize error checks
checkSerializeErrors = False

class SerializeTest(unittest.TestCase):
  def addTest(cls, name, expected, input):
    func = lambda self: self.assertEqual(expected, self.serialize_html(input))
    setattr(cls, name, new.instancemethod(func, None, cls))
  addTest = classmethod(addTest)

  def serialize_html(self,stream):
    return ''.join([token.toxml() for token in
       html5parser.HTMLParser(tokenizer=sanitizer.HTMLSanitizer).
           parseFragment(stream).childNodes])

# TODO: add tests

def buildTestSuite():
    return unittest.TestLoader().loadTestsFromTestCase(SerializeTest)

def main():
    buildTestSuite()
    unittest.main()

if __name__ == "__main__":
    main()
