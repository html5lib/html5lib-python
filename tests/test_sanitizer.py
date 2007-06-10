import os,sys,unittest

#RELEASE remove
if __name__ == '__main__':
    # XXX Allow us to import the sibling module
    os.chdir(os.path.split(os.path.abspath(__file__))[0])
    sys.path.insert(0, os.path.abspath(os.path.join(os.pardir, "src")))

import html5parser, sanitizer, constants
#END RELEASE

#RELEASE add
#from html5lib import html5parser, sanitizer, constants
#END RELEASE

class SanitizeTest(unittest.TestCase):
  def addTest(cls, name, expected, input):
    setattr(cls, name, 
      lambda self: self.assertEqual(expected, self.sanitize_html(input)))
  addTest = classmethod(addTest)

  def sanitize_html(self,stream):
    return ''.join([token.toxml() for token in
       html5parser.HTMLParser(tokenizer=sanitizer.HTMLSanitizer).
           parseFragment(stream).childNodes])

  def test_should_allow_anchors(self):
    self.assertEqual("<a href=\"foo\">&lt;script&gt;baz&lt;/script&gt;</a>",
     self.sanitize_html("<a href='foo' onclick='bar'><script>baz</script></a>"))

  # RFC 3986, sec 4.2
  def test_allow_colons_in_path_component(self):
    self.assertEqual("<a href=\"./this:that\">foo</a>",
      self.sanitize_html("<a href=\"./this:that\">foo</a>"))

  def test_should_handle_non_html(self):
    self.assertEqual('abc',  self.sanitize_html("abc"))

  def test_should_handle_blank_text(self):
    self.assertEqual('', self.sanitize_html(''))

  def test_should_sanitize_tag_broken_up_by_null(self):
    self.assertEqual(u"&lt;scr\ufffdipt&gt;alert(\"XSS\")&lt;/scr\ufffdipt&gt;", self.sanitize_html("""<scr\0ipt>alert(\"XSS\")</scr\0ipt>"""))

  def test_should_sanitize_invalid_script_tag(self):
    self.assertEqual("&lt;script XSS=\"\" SRC=\"http://ha.ckers.org/xss.js\"&gt;&lt;/script&gt;", self.sanitize_html("""<script/XSS SRC="http://ha.ckers.org/xss.js"></script>"""))

  def test_should_sanitize_script_tag_with_multiple_open_brackets(self):
    self.assertEqual("&lt;&lt;script&gt;alert(\"XSS\");//&lt;&lt;/script&gt;", self.sanitize_html("""<<script>alert("XSS");//<</script>"""))
    self.assertEqual("""&lt;iframe src=\"http://ha.ckers.org/scriptlet.html\"&gt;&lt;""", self.sanitize_html("""<iframe src=http://ha.ckers.org/scriptlet.html\n<"""))

  def test_should_sanitize_unclosed_script(self):
    self.assertEqual("&lt;script src=\"http://ha.ckers.org/xss.js?\"&gt;<b/>", self.sanitize_html("""<script src=http://ha.ckers.org/xss.js?<b>"""))

  def test_should_sanitize_half_open_scripts(self):
    self.assertEqual("<img/>", self.sanitize_html("""<img src="javascript:alert('XSS')"""))

  def test_should_not_fall_for_ridiculous_hack(self):
    img_hack = """<img\nsrc\n=\n"\nj\na\nv\na\ns\nc\nr\ni\np\nt\n:\na\nl\ne\nr\nt\n(\n'\nX\nS\nS\n'\n)\n"\n />"""
    self.assertEqual("<img/>", self.sanitize_html(img_hack))

  def test_platypus(self):
    self.assertEqual("""<a style=\"display: block; width: 100%; height: 100%; background-color: black; background-x: center; background-y: center;\" href=\"http://www.ragingplatypus.com/\">never trust your upstream platypus</a>""",
       self.sanitize_html("""<a href="http://www.ragingplatypus.com/" style="display:block; position:absolute; left:0; top:0; width:100%; height:100%; z-index:1; background-color:black; background-image:url(http://www.ragingplatypus.com/i/cam-full.jpg); background-x:center; background-y:center; background-repeat:repeat;">never trust your upstream platypus</a>"""))

  def test_xul(self):
    self.assertEqual("""<p style="">fubar</p>""",
     self.sanitize_html("""<p style="-moz-binding:url('http://ha.ckers.org/xssmoz.xml#xss')">fubar</p>"""))

  def test_input_image(self):
    self.assertEqual("""<input type="image"/>""",
      self.sanitize_html("""<input type="image" src="javascript:alert('XSS');" />"""))

  def test_non_alpha_non_digit(self):
    self.assertEqual(u"&lt;script XSS=\"\" src=\"http://ha.ckers.org/xss.js\"&gt;&lt;/script&gt;",
      self.sanitize_html("""<script/XSS src="http://ha.ckers.org/xss.js"></script>"""))
    self.assertEqual("<a>foo</a>",
      self.sanitize_html('<a onclick!#$%&()*~+-_.,:;?@[/|\]^`=alert("XSS")>foo</a>'))
    self.assertEqual("<img src=\"http://ha.ckers.org/xss.js\"/>",
      self.sanitize_html('<img/src="http://ha.ckers.org/xss.js"/>'))

  def test_img_dynsrc_lowsrc(self):
     self.assertEqual("<img/>",
       self.sanitize_html("""<img dynsrc="javascript:alert('XSS')" />"""))
     self.assertEqual("<img/>",
       self.sanitize_html("""<img lowsrc="javascript:alert('XSS')" />"""))

  def test_div_background_image_unicode_encoded(self):
    self.assertEqual('<div style="">foo</div>',
      self.sanitize_html("""<div style="background-image:\0075\0072\006C\0028'\006a\0061\0076\0061\0073\0063\0072\0069\0070\0074\003a\0061\006c\0065\0072\0074\0028.1027\0058.1053\0053\0027\0029'\0029">foo</div>"""))

  def test_div_expression(self):
    self.assertEqual(u'<div style="">foo</div>',
      self.sanitize_html("""<div style="width: expression(alert('XSS'));">foo</div>"""))

  def test_img_vbscript(self):
     self.assertEqual(u'<img/>',
       self.sanitize_html("""<img src='vbscript:msgbox("XSS")' />"""))

  def test_should_handle_astral_plane_characters(self):
    self.assertEqual(u"<p>\U0001d4b5 \U0001d538</p>",
      self.sanitize_html("<p>&#x1d4b5; &#x1d538;</p>"))


for i,img_hack in enumerate(
  ["""<img src="javascript:alert('XSS');" />""",
   """<img src=javascript:alert('XSS') />""",
   """<img src="JaVaScRiPt:alert('XSS')" />""",
   """<img src='javascript:alert(&quot;XSS&quot;)' />""",
   """<img src='javascript:alert(String.fromCharCode(88,83,83))' />""",
   """<img src='&#106;&#97;&#118;&#97;&#115;&#99;&#114;&#105;&#112;&#116;&#58;&#97;&#108;&#101;&#114;&#116;&#40;&#39;&#88;&#83;&#83;&#39;&#41;' />""",
   """<img src='&#0000106;&#0000097;&#0000118;&#0000097;&#0000115;&#0000099;&#0000114;&#0000105;&#0000112;&#0000116;&#0000058;&#0000097;&#0000108;&#0000101;&#0000114;&#0000116;&#0000040;&#0000039;&#0000088;&#0000083;&#0000083;&#0000039;&#0000041' />""",
   """<img src='&#x6A;&#x61;&#x76;&#x61;&#x73;&#x63;&#x72;&#x69;&#x70;&#x74;&#x3A;&#x61;&#x6C;&#x65;&#x72;&#x74;&#x28;&#x27;&#x58;&#x53;&#x53;&#x27;&#x29' />""",
   """<img src="jav\tascript:alert('XSS');" />""",
   """<img src="jav&#x09;ascript:alert('XSS');" />""",
   """<img src="jav&#x0A;ascript:alert('XSS');" />""",
   """<img src="jav&#x0D;ascript:alert('XSS');" />""",
   """<img src=" &#14;  javascript:alert('XSS');" />""",
   """<img src="&#x20;javascript:alert('XSS');" />""",
   """<img src="&#xA0;javascript:alert('XSS');" />"""]):
    SanitizeTest.addTest("test_should_not_fall_for_xss_image_hack_#%d"%i,
      "<img/>", img_hack)

for tag, attr in [('img','src'), ('a','href')]:
    close = tag in constants.voidElements and "/>boo" or ">boo</%s>" % tag

    SanitizeTest.addTest("test_should_strip_%s_attribute_in_%s_with_bad_protocols" % (attr,tag),
      """<%s title="1"%s""" % (tag, close),
      """<%s %s="javascript:XSS" title="1">boo</%s>""" % (tag,attr,tag))

    SanitizeTest.addTest("test_should_strip_%s_attribute_in_%s_with_bad_protocols_and_whitespace" % (attr,tag),
      """<%s title="1"%s""" % (tag, close),
      """<%s %s=" javascript:XSS" title="1">boo</%s>""" % (tag,attr,tag))

for img_attr in ['src', 'width', 'height', 'alt']:
    SanitizeTest.addTest("test_should_allow_image_%s_attribute" % img_attr,
      "<img %s=\"foo\"/>" % img_attr,
      "<img %s='foo' onclick='bar' />" % img_attr)

for tag_name in sanitizer.HTMLSanitizer.allowed_elements:
    if tag_name in ['caption', 'col', 'colgroup', 'optgroup', 'option', 'table', 'tbody', 'td', 'tfoot', 'th', 'thead', 'tr']: continue ### TODO
    if tag_name != tag_name.lower(): continue ### TODO
    if tag_name == 'image':
        SanitizeTest.addTest("test_should_allow_%s_tag" % tag_name,
          "<img title=\"1\"/>foo &lt;bad&gt;bar&lt;/bad&gt; baz",
          "<%s title='1'>foo <bad>bar</bad> baz</%s>" % (tag_name,tag_name))
    elif tag_name in constants.voidElements:
        SanitizeTest.addTest("test_should_allow_%s_tag" % tag_name,
          "<%s title=\"1\"/>foo &lt;bad&gt;bar&lt;/bad&gt; baz" % tag_name,
          "<%s title='1'>foo <bad>bar</bad> baz</%s>" % (tag_name,tag_name))
    else:
        SanitizeTest.addTest("test_should_allow_%s_tag" % tag_name,
          "<%s title=\"1\">foo &lt;bad&gt;bar&lt;/bad&gt; baz</%s>" % (tag_name,tag_name),
          "<%s title='1'>foo <bad>bar</bad> baz</%s>" % (tag_name,tag_name))

for tag_name in sanitizer.HTMLSanitizer.allowed_elements:
    tag_name = tag_name.upper()
    SanitizeTest.addTest("test_should_forbid_%s_tag" % tag_name,
      "&lt;%s title=\"1\"&gt;foo &lt;bad&gt;bar&lt;/bad&gt; baz&lt;/%s&gt;" % (tag_name,tag_name),
      "<%s title='1'>foo <bad>bar</bad> baz</%s>" % (tag_name,tag_name))

for attribute_name in sanitizer.HTMLSanitizer.allowed_attributes:
    if attribute_name != attribute_name.lower(): continue ### TODO
    if attribute_name == 'style': continue
    SanitizeTest.addTest("test_should_allow_%s_attribute" % attribute_name,
      "<p %s=\"foo\">foo &lt;bad&gt;bar&lt;/bad&gt; baz</p>" % attribute_name,
      "<p %s='foo'>foo <bad>bar</bad> baz</p>" % attribute_name)

for attribute_name in sanitizer.HTMLSanitizer.allowed_attributes:
    attribute_name = attribute_name.upper()
    SanitizeTest.addTest("test_should_forbid_%s_attribute" % attribute_name,
      "<p>foo &lt;bad&gt;bar&lt;/bad&gt; baz</p>",
      "<p %s='display: none;'>foo <bad>bar</bad> baz</p>" % attribute_name)

for protocol in sanitizer.HTMLSanitizer.allowed_protocols:
    SanitizeTest.addTest("test_should_allow_%s_uris" % protocol,
      "<a href=\"%s\">foo</a>" % protocol,
      """<a href="%s">foo</a>""" % protocol)

for protocol in sanitizer.HTMLSanitizer.allowed_protocols:
    SanitizeTest.addTest("test_should_allow_uppercase_%s_uris" % protocol,
      "<a href=\"%s\">foo</a>" % protocol,
      """<a href="%s">foo</a>""" % protocol)

def buildTestSuite():
    return unittest.TestLoader().loadTestsFromTestCase(SanitizeTest)

def main():
    buildTestSuite()
    unittest.main()

if __name__ == "__main__":
    main()
