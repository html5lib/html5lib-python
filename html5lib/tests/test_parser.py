# Copyright (c) 2006-2013 James Graham and other contributors
#
# Permission is hereby granted, free of charge, to any person obtaining
# a copy of this software and associated documentation files (the
# "Software"), to deal in the Software without restriction, including
# without limitation the rights to use, copy, modify, merge, publish,
# distribute, sublicense, and/or sell copies of the Software, and to
# permit persons to whom the Software is furnished to do so, subject to
# the following conditions:
#
# The above copyright notice and this permission notice shall be
# included in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
# MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
# NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE
# LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION
# OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION
# WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

from __future__ import absolute_import, division, unicode_literals

import os
import sys
import traceback
import warnings
import re

warnings.simplefilter("error")

from .support import get_data_files
from .support import TestData, convert, convertExpected, treeTypes
from html5lib import html5parser, constants

# Run the parse error checks
checkParseErrors = False

# XXX - There should just be one function here but for some reason the testcase
# format differs from the treedump format by a single space character


def convertTreeDump(data):
    return "\n".join(convert(3)(data).split("\n")[1:])

namespaceExpected = re.compile(r"^(\s*)<(\S+)>", re.M).sub


def runParserTest(innerHTML, input, expected, errors, treeClass,
                  namespaceHTMLElements):
    with warnings.catch_warnings(record=True) as caughtWarnings:
        warnings.simplefilter("always")
        p = html5parser.HTMLParser(tree=treeClass,
                                   namespaceHTMLElements=namespaceHTMLElements)

        try:
            if innerHTML:
                document = p.parseFragment(input, innerHTML)
            else:
                document = p.parse(input)
        except:
            errorMsg = "\n".join(["\n\nInput:", input, "\nExpected:", expected,
                                  "\nTraceback:", traceback.format_exc()])
            assert False, errorMsg

    otherWarnings = [x for x in caughtWarnings
                     if not issubclass(x.category, constants.DataLossWarning)]
    assert len(otherWarnings) == 0, [(x.category, x.message) for x in otherWarnings]
    if len(caughtWarnings):
        return

    output = convertTreeDump(p.tree.testSerializer(document))

    expected = convertExpected(expected)
    if namespaceHTMLElements:
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
                           "\nExpected errors (" + str(len(errors)) + "):\n" + "\n".join(errors),
                           "\nActual errors (" + str(len(p.errors)) + "):\n" + "\n".join(errStr)])
    if checkParseErrors:
            assert len(p.errors) == len(errors), errorMsg2


def test_parser():
    sys.stderr.write('Testing tree builders ' + " ".join(list(treeTypes.keys())) + "\n")
    files = get_data_files('tree-construction')

    for filename in files:
        testName = os.path.basename(filename).replace(".dat", "")
        if testName in ("template",):
            continue

        tests = TestData(filename, "data")

        for index, test in enumerate(tests):
            input, errors, innerHTML, expected = [test[key] for key in
                                                  ('data', 'errors',
                                                   'document-fragment',
                                                   'document')]
            if errors:
                errors = errors.split("\n")

            for treeName, treeCls in treeTypes.items():
                for namespaceHTMLElements in (True, False):
                    yield (runParserTest, innerHTML, input, expected, errors, treeCls,
                           namespaceHTMLElements)
