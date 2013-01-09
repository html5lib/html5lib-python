from __future__ import with_statement
from __future__ import absolute_import
import os
import unittest
from .support import get_data_files
from itertools import imap
from io import open

try:
    import json
except ImportError:
    import simplejson as json

try:
    unittest.TestCase.assertEqual
except AttributeError:
    unittest.TestCase.assertEqual = unittest.TestCase.assertEquals

import html5lib
from html5lib import html5parser, serializer, constants
from html5lib.treewalkers._base import TreeWalker

optionals_loaded = []

try:
    from lxml import etree
    optionals_loaded.append(u"lxml")
except ImportError:
    pass

default_namespace = constants.namespaces[u"html"]

class JsonWalker(TreeWalker):
    def __iter__(self):
        for token in self.tree:
            type = token[0]
            if type == u"StartTag":
                if len(token) == 4:
                    namespace, name, attrib = token[1:4]
                else:
                    namespace = default_namespace
                    name, attrib = token[1:3]
                yield self.startTag(namespace, name, self._convertAttrib(attrib))
            elif type == u"EndTag":
                if len(token) == 3:
                    namespace, name = token[1:3]
                else:
                    namespace = default_namespace
                    name = token[1]
                yield self.endTag(namespace, name)
            elif type == u"EmptyTag":
                if len(token) == 4:
                    namespace, name, attrib = token[1:]
                else:
                    namespace = default_namespace
                    name, attrib = token[1:]
                for token in self.emptyTag(namespace, name, self._convertAttrib(attrib)):
                    yield token
            elif type == u"Comment":
                yield self.comment(token[1])
            elif type in (u"Characters", u"SpaceCharacters"):
                for token in self.text(token[1]):
                    yield token
            elif type == u"Doctype":
                if len(token) == 4:
                    yield self.doctype(token[1], token[2], token[3])
                elif len(token) == 3:
                    yield self.doctype(token[1], token[2])
                else:
                    yield self.doctype(token[1])
            else:
                raise ValueError(u"Unknown token type: " + type)
    __iter__.func_annotations = {}
    
    def _convertAttrib(self, attribs):
        u"""html5lib tree-walkers use a dict of (namespace, name): value for
        attributes, but JSON cannot represent this. Convert from the format
        in the serializer tests (a list of dicts with "namespace", "name",
        and "value" as keys) to html5lib's tree-walker format."""
        attrs = {}
        for attrib in attribs:
            name = (attrib[u"namespace"], attrib[u"name"])
            assert(name not in attrs)
            attrs[name] = attrib[u"value"]
        return attrs
    _convertAttrib.func_annotations = {}


def serialize_html(input, options):
    options = dict([(unicode(k),v) for k,v in options.items()])
    return serializer.HTMLSerializer(**options).render(JsonWalker(input),options.get(u"encoding",None))
serialize_html.func_annotations = {}

def serialize_xhtml(input, options):
    options = dict([(unicode(k),v) for k,v in options.items()])
    return serializer.XHTMLSerializer(**options).render(JsonWalker(input),options.get(u"encoding",None))
serialize_xhtml.func_annotations = {}

def runSerializerTest(input, expected, xhtml, options):
    encoding = options.get(u"encoding", None)

    if encoding:
        encode = lambda x: x.encode(encoding)
        expected = list(imap(encode, expected))
        if xhtml:
            xhtml = list(imap(encode, xhtml))
        
    
    result = serialize_html(input, options)
    if len(expected) == 1:
        assert expected[0] == result, u"Expected:\n%s\nActual:\n%s\nOptions\nxhtml:False\n%s"%(expected[0], result, unicode(options))
    elif result not in expected:
        assert False, u"Expected: %s, Received: %s" % (expected, result)

    if not xhtml:
        return

    result = serialize_xhtml(input, options)
    if len(xhtml) == 1:
        assert xhtml[0] == result, u"Expected:\n%s\nActual:\n%s\nOptions\nxhtml:True\n%s"%(xhtml[0], result, unicode(options))
    elif result not in xhtml:
        assert False, u"Expected: %s, Received: %s" % (xhtml, result)
runSerializerTest.func_annotations = {}


class EncodingTestCase(unittest.TestCase):
    def throwsWithLatin1(self, input):
        self.assertRaises(UnicodeEncodeError, serialize_html, input, {u"encoding": u"iso-8859-1"})
    throwsWithLatin1.func_annotations = {}

    def testDoctypeName(self):
        self.throwsWithLatin1([[u"Doctype", u"\u0101"]])
    testDoctypeName.func_annotations = {}

    def testDoctypePublicId(self):
        self.throwsWithLatin1([[u"Doctype", u"potato", u"\u0101"]])
    testDoctypePublicId.func_annotations = {}

    def testDoctypeSystemId(self):
        self.throwsWithLatin1([[u"Doctype", u"potato", u"potato", u"\u0101"]])
    testDoctypeSystemId.func_annotations = {}

    def testCdataCharacters(self):
        runSerializerTest([[u"StartTag", u"http://www.w3.org/1999/xhtml", u"style", {}], [u"Characters", u"\u0101"]],
                          [u"<style>&amacr;"], None, {u"encoding": u"iso-8859-1"})
    testCdataCharacters.func_annotations = {}

    def testCharacters(self):
        runSerializerTest([[u"Characters", u"\u0101"]],
                          [u"&amacr;"], None, {u"encoding": u"iso-8859-1"})
    testCharacters.func_annotations = {}

    def testStartTagName(self):
        self.throwsWithLatin1([[u"StartTag", u"http://www.w3.org/1999/xhtml", u"\u0101", []]])
    testStartTagName.func_annotations = {}

    def testEmptyTagName(self):
        self.throwsWithLatin1([[u"EmptyTag", u"http://www.w3.org/1999/xhtml", u"\u0101", []]])
    testEmptyTagName.func_annotations = {}

    def testAttributeName(self):
        self.throwsWithLatin1([[u"StartTag", u"http://www.w3.org/1999/xhtml", u"span", [{u"namespace": None, u"name": u"\u0101", u"value": u"potato"}]]])
    testAttributeName.func_annotations = {}

    def testAttributeValue(self):
        runSerializerTest([[u"StartTag", u"http://www.w3.org/1999/xhtml", u"span",
                            [{u"namespace": None, u"name": u"potato", u"value": u"\u0101"}]]],
                          [u"<span potato=&amacr;>"], None, {u"encoding": u"iso-8859-1"})
    testAttributeValue.func_annotations = {}

    def testEndTagName(self):
        self.throwsWithLatin1([[u"EndTag", u"http://www.w3.org/1999/xhtml", u"\u0101"]])
    testEndTagName.func_annotations = {}

    def testComment(self):
        self.throwsWithLatin1([[u"Comment", u"\u0101"]])
    testComment.func_annotations = {}


if u"lxml" in optionals_loaded:
    class LxmlTestCase(unittest.TestCase):
        def setUp(self):
            self.parser = etree.XMLParser(resolve_entities=False)
            self.treewalker = html5lib.getTreeWalker(u"lxml")
            self.serializer = serializer.HTMLSerializer()
        setUp.func_annotations = {}

        def testEntityReplacement(self):
            doc = u"""<!DOCTYPE html SYSTEM "about:legacy-compat"><html>&beta;</html>"""
            tree = etree.fromstring(doc, parser = self.parser).getroottree()
            result = serializer.serialize(tree, tree=u"lxml", omit_optional_tags=False)
            self.assertEqual(u"""<!DOCTYPE html SYSTEM "about:legacy-compat"><html>\u03B2</html>""", result)
        testEntityReplacement.func_annotations = {}

        def testEntityXML(self):
            doc = u"""<!DOCTYPE html SYSTEM "about:legacy-compat"><html>&gt;</html>"""
            tree = etree.fromstring(doc, parser = self.parser).getroottree()
            result = serializer.serialize(tree, tree=u"lxml", omit_optional_tags=False)
            self.assertEqual(u"""<!DOCTYPE html SYSTEM "about:legacy-compat"><html>&gt;</html>""", result)
        testEntityXML.func_annotations = {}

        def testEntityNoResolve(self):
            doc = u"""<!DOCTYPE html SYSTEM "about:legacy-compat"><html>&beta;</html>"""
            tree = etree.fromstring(doc, parser = self.parser).getroottree()
            result = serializer.serialize(tree, tree=u"lxml", omit_optional_tags=False,
                                          resolve_entities=False)
            self.assertEqual(u"""<!DOCTYPE html SYSTEM "about:legacy-compat"><html>&beta;</html>""", result)
        testEntityNoResolve.func_annotations = {}

def test_serializer():
    for filename in get_data_files(u'serializer', u'*.test'):
        with open(filename) as fp:
            tests = json.load(fp)
            test_name = os.path.basename(filename).replace(u'.test',u'')
            for index, test in enumerate(tests[u'tests']):
                xhtml = test.get(u"xhtml", test[u"expected"])
                if test_name == u'optionaltags': 
                    xhtml = None
                yield runSerializerTest, test[u"input"], test[u"expected"], xhtml, test.get(u"options", {})
test_serializer.func_annotations = {}
