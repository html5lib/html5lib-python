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

import unittest, re

def sortattrs(match):
  name = match.group(1)
  attrs = re.findall('([-:\w]+)="([^"]*)"', match.group(2))
  if not attrs: return "<%s%s%s>" % match.groups()
  attrs.sort()
  attrs = ' '.join(['%s="%s"' % (n,v) for n,v in attrs])
  return "<%s %s%s>" % (name, attrs, match.group(3))

def ncr(match):
  return unichr(int(match.group(1))).encode('utf-8')

xmlelem = re.compile(r'<(\w+)((?: [-:\w]+="[^"]*")+)(/?)>')

class Xhtml5Test(unittest.TestCase):

  def assertXmlEquals(self, input, expected=None, parser=XMLParser):
    document = parser(tree=dom.TreeBuilder).parse(input).documentElement
    if not expected:
       expected = xmlelem.sub(sortattrs, input)
       expected = re.sub('&#(\d+);', ncr, expected)
       output = xmlelem.sub(sortattrs, document.toxml('utf-8'))
       self.assertEquals(expected, output)
    else:
       self.assertEquals(expected, document.toxml('utf-8'))

  def assertXhtmlEquals(self, input, expected=None, parser=XHTMLParser):
    self.assertXmlEquals(input, expected, parser)

class BasicXhtml5Test(Xhtml5Test):

  def test_title_body_mismatched_close(self):
    self.assertXhtmlEquals(
      '<title>Xhtml</title><b><i>content</b></i>',
      '<html xmlns="http://www.w3.org/1999/xhtml">'
        '<head><title>Xhtml</title></head>' + 
        '<body><b><i>content</i></b></body>' +
      '</html>')

  def test_title_body_named_charref(self):
    self.assertXhtmlEquals(
      '<title>mdash</title>A &mdash B',
      '<html xmlns="http://www.w3.org/1999/xhtml">'
        '<head><title>mdash</title></head>' + 
        '<body>A '+ unichr(0x2014).encode('utf-8') + ' B</body>' +
      '</html>')

class BasicXmlTest(Xhtml5Test):

  def test_comment(self):
    self.assertXmlEquals("<x><!-- foo --></x>")

  def test_cdata(self):
    self.assertXmlEquals("<x><![CDATA[foo]]></x>","<x>foo</x>")

class OpmlTest(Xhtml5Test):

  def test_mixedCaseElement(self):
    self.assertXmlEquals(
      '<opml version="1.0">' +
        '<head><ownerName>Dave Winer</ownerName></head>' +
      '</opml>')

  def test_mixedCaseAttribute(self):
    self.assertXmlEquals(
      '<opml version="1.0">' +
        '<body><outline isComment="true"/></body>' +
      '</opml>')

  def test_malformed(self):
    self.assertXmlEquals(
      '<opml version="1.0">' +
        '<body><outline text="Odds & Ends"/></body>' +
      '</opml>',
      '<opml version="1.0">' +
        '<body><outline text="Odds &amp; Ends"/></body>' +
      '</opml>',)

class XhtmlTest(Xhtml5Test):

  def test_mathml(self):
    self.assertXhtmlEquals("""<html xmlns="http://www.w3.org/1999/xhtml">
<head><title>MathML</title></head>
<body>
  <math xmlns="http://www.w3.org/1998/Math/MathML">
    <mrow>
      <mi>x</mi>
      <mo>=</mo>

      <mfrac>
        <mrow>
          <mrow>
            <mo>-</mo>
            <mi>b</mi>
          </mrow>
          <mo>&#177;</mo>
          <msqrt>

            <mrow>
              <msup>
                <mi>b</mi>
                <mn>2</mn>
              </msup>
              <mo>-</mo>
              <mrow>

                <mn>4</mn>
                <mo>&#8290;</mo>
                <mi>a</mi>
                <mo>&#8290;</mo>
                <mi>c</mi>
              </mrow>
            </mrow>

          </msqrt>
        </mrow>
        <mrow>
          <mn>2</mn>
          <mo>&#8290;</mo>
          <mi>a</mi>
        </mrow>
      </mfrac>

    </mrow>
  </math>
</body></html>""")

  def test_svg(self):
    self.assertXhtmlEquals("""<html xmlns="http://www.w3.org/1999/xhtml">
<head><title>SVG</title></head>
<body>
  <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100">
    <path d="M38,38c0-12,24-15,23-2c0,9-16,13-16,23v7h11v-4c0-9,17-12,17-27
             c-2-22-45-22-45,3zM45,70h11v11h-11z" fill="#371">
    </path>
    <circle cx="50" cy="50" r="45" fill="none" stroke="#371" stroke-width="10">
    </circle>

  </svg>
</body></html>""")

  def test_xlink(self):
    self.assertXhtmlEquals("""<html xmlns="http://www.w3.org/1999/xhtml">
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

  def test_br(self):
    self.assertXhtmlEquals("""<html xmlns="http://www.w3.org/1999/xhtml">
<head><title>XLINK</title></head>
<body>
<br/>
</body></html>""")

  def test_strong(self):
    self.assertXhtmlEquals("""<html xmlns="http://www.w3.org/1999/xhtml">
<head><title>XLINK</title></head>
<body>
<strong></strong>
</body></html>""")

def buildTestSuite():
  return unittest.defaultTestLoader.loadTestsFromName(__name__)

def main():
    buildTestSuite()
    unittest.main()

if __name__ == '__main__':
    main()
