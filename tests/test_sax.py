import StringIO
import xml.sax
import new
import unittest

PREFERRED_XML_PARSERS = ["drv_libxml2"]

#RELEASE remove
if __name__ == '__main__':
  import os, sys
  os.chdir(os.path.split(os.path.abspath(__file__))[0])
  sys.path.insert(0, os.path.abspath(os.path.join(os.pardir, "src")))

from liberalxmlparser import *
from treebuilders import dom
#END RELEASE

#RELEASE add
#import html5lib
#from html5lib.treebuilders import dom
#from html5lib.liberalxmlparser import *
#END RELEASE

class SAXLogger: 
  def __init__(self):
    self.log = []
  def setDocumentLocator(self, locator):
    pass
  def startElement(self, name, attrs):
    self.log.append(['startElement', name, dict(attrs.items())])
  def startElementNS(self, name, qname, attrs):
    self.log.append(['startElementNS', name, qname, dict(attrs.items())])
  def __getattr__(self, name):
    def function(self, *args): self.log.append([name]+list(args))
    return new.instancemethod(function, self, SAXLogger)

class SAXTest(unittest.TestCase):
  def DOMParse(self, input):
    return XMLParser(tree=dom.TreeBuilder).parse(input)

  def setNS(self, saxparser):
    import xml.dom
    saxparser.setFeature(xml.sax.handler.feature_namespaces, 1)
    return {'xml':xml.dom.XML_NAMESPACE}

  def saxdiff(self, input):
    domhandler = SAXLogger()

    saxhandler = SAXLogger()
    saxparser = xml.sax.make_parser(PREFERRED_XML_PARSERS)

    dom.dom2sax(self.DOMParse(input), domhandler, self.setNS(saxparser))

    saxparser.setContentHandler(saxhandler)
    source = xml.sax.xmlreader.InputSource()
    source.setByteStream(StringIO.StringIO(input))
    saxparser.parse(source)

    for i in range(0,len(saxhandler.log)):
      if i > len(domhandler.log):
        self.assertEqual(saxhandler.log[i:], domhandler.log[i:])
      elif saxhandler.log[i] != domhandler.log[i]:
        self.assertEqual(saxhandler.log[i], domhandler.log[i])
    else:
      self.assertEquals(saxhandler.log, domhandler.log)

  def test_nodes(self):
    self.saxdiff('<!DOCTYPE foo><foo a="1" b="1">&apos;<bar/>x<!--cmt-->' +
      '<![CDATA[data]]></foo>')

  def test_xmllang(self):
    self.saxdiff('<!DOCTYPE html><html xmlns="http://www.w3.org/1999/xhtml">'
      "<body xml:lang='en-us'>foo</body></html>")

  def test_ns(self):
    self.saxdiff(
"""<html xmlns="http://www.w3.org/1999/xhtml">
<head><title>XLINK</title></head>
<body>
  <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100">
    <defs xmlns:l="http://www.w3.org/1999/xlink">
      <radialGradient id="s1" fx=".4" fy=".2" r=".7">
        <stop stop-color="#FE8"/>
        <stop stop-color="#D70" offset="1"/>
      </radialGradient>
      <radialGradient id="s2" fx=".8" fy=".5" l:href="#s1"/>
      <radialGradient id="s3" fx=".5" fy=".9" l:href="#s1"/>
      <radialGradient id="s4" fx=".1" fy=".5" l:href="#s1"/>
    </defs>
    <g stroke="#940">
      <path d="M73,29c-37-40-62-24-52,4l6-7c-8-16,7-26,42,9z" fill="url(#s1)"/>
      <path d="M47,8c33-16,48,21,9,47l-6-5c38-27,20-44,5-37z" fill="url(#s2)"/>
      <path d="M77,32c22,30,10,57-39,51l-1-8c3,3,67,5,36-36z" fill="url(#s3)"/>

      <path d="M58,84c-4,20-38-4-8-24l-6-5c-36,43,15,56,23,27z" fill="url(#s4)"/>
      <path d="M40,14c-40,37-37,52-9,68l1-8c-16-13-29-21,16-56z" fill="url(#s1)"/>
      <path d="M31,33c19,23,20,7,35,41l-9,1.7c-4-19-8-14-31-37z" fill="url(#s2)"/>
    </g>
  </svg>
</body></html>""")

# Repeat tests without namespace support
class nonamespaceTest(SAXTest):
  def setNS(self, saxparser):
    return None

# Redundantly rerun all tests using the "real" minidom parser, just to be
# sure that the output is consistent
class minidomTest(SAXTest):
  def DOMParse(self, input):
    return xml.dom.minidom.parseString(input)

def buildTestSuite():
  return unittest.defaultTestLoader.loadTestsFromName(__name__)

def main():
    buildTestSuite()
    unittest.main()

if __name__ == '__main__':
    main()
