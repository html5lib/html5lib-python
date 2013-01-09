from __future__ import absolute_import
import os
import sys
import unittest

try:
    import json
except ImportError:
    import simplejson as json

from html5lib import html5parser, sanitizer, constants

def runSanitizerTest(name, expected, input):
    expected = u''.join([token.toxml() for token in html5parser.HTMLParser().
                         parseFragment(expected).childNodes])
    expected = json.loads(json.dumps(expected))
    assert expected == sanitize_html(input)
runSanitizerTest.func_annotations = {}

def sanitize_html(stream):
    return u''.join([token.toxml() for token in
                    html5parser.HTMLParser(tokenizer=sanitizer.HTMLSanitizer).
                     parseFragment(stream).childNodes])
sanitize_html.func_annotations = {}

def test_should_handle_astral_plane_characters():
    assert u"<p>\U0001d4b5 \U0001d538</p>" == sanitize_html(u"<p>&#x1d4b5; &#x1d538;</p>")
test_should_handle_astral_plane_characters.func_annotations = {}

def test_sanitizer():
    for tag_name in sanitizer.HTMLSanitizer.allowed_elements:
        if tag_name in [u'caption', u'col', u'colgroup', u'optgroup', u'option', u'table', u'tbody', u'td', u'tfoot', u'th', u'thead', u'tr']:
            continue ### TODO
        if tag_name != tag_name.lower():
            continue ### TODO
        if tag_name == u'image':
            yield (runSanitizerTest, u"test_should_allow_%s_tag" % tag_name,
              u"<img title=\"1\"/>foo &lt;bad&gt;bar&lt;/bad&gt; baz",
              u"<%s title='1'>foo <bad>bar</bad> baz</%s>" % (tag_name,tag_name))
        elif tag_name == u'br':
            yield (runSanitizerTest, u"test_should_allow_%s_tag" % tag_name,
              u"<br title=\"1\"/>foo &lt;bad&gt;bar&lt;/bad&gt; baz<br/>",
              u"<%s title='1'>foo <bad>bar</bad> baz</%s>" % (tag_name,tag_name))
        elif tag_name in constants.voidElements:
            yield (runSanitizerTest, u"test_should_allow_%s_tag" % tag_name,
              u"<%s title=\"1\"/>foo &lt;bad&gt;bar&lt;/bad&gt; baz" % tag_name,
              u"<%s title='1'>foo <bad>bar</bad> baz</%s>" % (tag_name,tag_name))
        else:
            yield (runSanitizerTest, u"test_should_allow_%s_tag" % tag_name,
              u"<%s title=\"1\">foo &lt;bad&gt;bar&lt;/bad&gt; baz</%s>" % (tag_name,tag_name),
              u"<%s title='1'>foo <bad>bar</bad> baz</%s>" % (tag_name,tag_name))

    for tag_name in sanitizer.HTMLSanitizer.allowed_elements:
        tag_name = tag_name.upper()
        yield (runSanitizerTest, u"test_should_forbid_%s_tag" % tag_name,
          u"&lt;%s title=\"1\"&gt;foo &lt;bad&gt;bar&lt;/bad&gt; baz&lt;/%s&gt;" % (tag_name,tag_name),
          u"<%s title='1'>foo <bad>bar</bad> baz</%s>" % (tag_name,tag_name))

    for attribute_name in sanitizer.HTMLSanitizer.allowed_attributes:
        if attribute_name != attribute_name.lower(): continue ### TODO
        if attribute_name == u'style': continue
        yield (runSanitizerTest, u"test_should_allow_%s_attribute" % attribute_name,
          u"<p %s=\"foo\">foo &lt;bad&gt;bar&lt;/bad&gt; baz</p>" % attribute_name,
          u"<p %s='foo'>foo <bad>bar</bad> baz</p>" % attribute_name)

    for attribute_name in sanitizer.HTMLSanitizer.allowed_attributes:
        attribute_name = attribute_name.upper()
        yield (runSanitizerTest, u"test_should_forbid_%s_attribute" % attribute_name,
          u"<p>foo &lt;bad&gt;bar&lt;/bad&gt; baz</p>",
          u"<p %s='display: none;'>foo <bad>bar</bad> baz</p>" % attribute_name)

    for protocol in sanitizer.HTMLSanitizer.allowed_protocols:
        yield (runSanitizerTest, u"test_should_allow_%s_uris" % protocol,
          u"<a href=\"%s\">foo</a>" % protocol,
          u"""<a href="%s">foo</a>""" % protocol)

    for protocol in sanitizer.HTMLSanitizer.allowed_protocols:
        yield (runSanitizerTest, u"test_should_allow_uppercase_%s_uris" % protocol,
          u"<a href=\"%s\">foo</a>" % protocol,
        u"""<a href="%s">foo</a>""" % protocol)
test_sanitizer.func_annotations = {}
