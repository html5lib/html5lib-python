from __future__ import absolute_import, division, unicode_literals

import io

from . import support  # flake8: noqa
from html5lib import html5parser
from html5lib.constants import namespaces
from html5lib.treebuilders import dom

import unittest

# tests that aren't autogenerated from text files


class MoreParserTests(unittest.TestCase):

    def test_assertDoctypeCloneable(self):
        parser = html5parser.HTMLParser(tree=dom.TreeBuilder)
        doc = parser.parse('<!DOCTYPE HTML>')
        self.assertTrue(doc.cloneNode(True))

    def test_line_counter(self):
        # http://groups.google.com/group/html5lib-discuss/browse_frm/thread/f4f00e4a2f26d5c0
        parser = html5parser.HTMLParser(tree=dom.TreeBuilder)
        parser.parse("<pre>\nx\n&gt;\n</pre>")

    def test_namespace_html_elements_0(self):
        parser = html5parser.HTMLParser(namespaceHTMLElements=True)
        doc = parser.parse("<html></html>")
        self.assertTrue(doc.childNodes[0].namespace == namespaces["html"])

    def test_namespace_html_elements_1(self):
        parser = html5parser.HTMLParser(namespaceHTMLElements=False)
        doc = parser.parse("<html></html>")
        self.assertTrue(doc.childNodes[0].namespace == None)

    def test_unicode_file(self):
        parser = html5parser.HTMLParser()
        parser.parse(io.StringIO("a"))


def buildTestSuite():
    return unittest.defaultTestLoader.loadTestsFromName(__name__)


def main():
    buildTestSuite()
    unittest.main()

if __name__ == '__main__':
    main()
