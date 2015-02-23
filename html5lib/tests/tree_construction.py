from __future__ import absolute_import, division, unicode_literals

import warnings
import re

import pytest

from .support import TestData, convert, convertExpected, treeTypes
from html5lib import html5parser, constants


class TreeConstructionFile(pytest.File):
    def collect(self):
        tests = TestData(str(self.fspath), "data")
        for i, test in enumerate(tests):
            for treeName, treeClass in sorted(treeTypes.items()):
                for namespaceHTMLElements in (True, False):
                    if namespaceHTMLElements:
                        nodeid = "%d::%s::namespaced" % (i, treeName)
                    else:
                        nodeid = "%d::%s::void-namespace" % (i, treeName)
                    item = ParserTest(nodeid, self,
                                      test, treeClass, namespaceHTMLElements)
                    item.add_marker(getattr(pytest.mark, treeName))
                    if namespaceHTMLElements:
                        item.add_marker(pytest.mark.namespaced)
                    if treeClass is None:
                        item.add_marker(pytest.mark.skipif(True, reason="Treebuilder not loaded"))
                    yield item


def convertTreeDump(data):
    return "\n".join(convert(3)(data).split("\n")[1:])

namespaceExpected = re.compile(r"^(\s*)<(\S+)>", re.M).sub


class ParserTest(pytest.Item):
    def __init__(self, name, parent, test, treeClass, namespaceHTMLElements):
        super(ParserTest, self).__init__(name, parent)
        self.obj = lambda: 1  # this is to hack around skipif needing a function!
        self.test = test
        self.treeClass = treeClass
        self.namespaceHTMLElements = namespaceHTMLElements

    def runtest(self):
        p = html5parser.HTMLParser(tree=self.treeClass,
                                   namespaceHTMLElements=self.namespaceHTMLElements)

        input = self.test['data']
        fragmentContainer = self.test['document-fragment']
        expected = self.test['document']
        expectedErrors = self.test['errors'].split("\n") if self.test['errors'] else []

        with warnings.catch_warnings():
            warnings.simplefilter("error")
            try:
                if fragmentContainer:
                    document = p.parseFragment(input, fragmentContainer)
                else:
                    document = p.parse(input)
            except constants.DataLossWarning:
                pytest.skip("data loss warning")

        output = convertTreeDump(p.tree.testSerializer(document))

        expected = convertExpected(expected)
        if self.namespaceHTMLElements:
            expected = namespaceExpected(r"\1<html \2>", expected)

        errorMsg = "\n".join(["\n\nInput:", input, "\nExpected:", expected,
                              "\nReceived:", output])
        assert expected == output, errorMsg

        errStr = []
        for (line, col), errorcode, datavars in p.errors:
            assert isinstance(datavars, dict), "%s, %s" % (errorcode, repr(datavars))
            errStr.append("Line: %i Col: %i %s" % (line, col,
                                                   constants.E[errorcode] % datavars))

        errorMsg2 = "\n".join(["\n\nInput:", input,
                               "\nExpected errors (" + str(len(expectedErrors)) + "):\n" + "\n".join(expectedErrors),
                               "\nActual errors (" + str(len(p.errors)) + "):\n" + "\n".join(errStr)])
        if False:  # we're currently not testing parse errors
            assert len(p.errors) == len(expectedErrors), errorMsg2

    def repr_failure(self, excinfo):
        traceback = excinfo.traceback
        ntraceback = traceback.cut(path=__file__)
        excinfo.traceback = ntraceback.filter()

        return excinfo.getrepr(funcargs=True,
                               showlocals=False,
                               style="short", tbfilter=False)
