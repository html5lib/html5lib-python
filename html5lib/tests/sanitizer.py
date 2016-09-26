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

import codecs
import json

import pytest

from html5lib import parseFragment, serialize


class SanitizerFile(pytest.File):
    def collect(self):
        with codecs.open(str(self.fspath), "r", encoding="utf-8") as fp:
            tests = json.load(fp)
        for i, test in enumerate(tests):
            yield SanitizerTest(str(i), self, test=test)


class SanitizerTest(pytest.Item):
    def __init__(self, name, parent, test):
        super(SanitizerTest, self).__init__(name, parent)
        self.obj = lambda: 1  # this is to hack around skipif needing a function!
        self.test = test

    def runtest(self):
        input = self.test["input"]
        expected = self.test["output"]

        parsed = parseFragment(input)
        serialized = serialize(parsed,
                               sanitize=True,
                               omit_optional_tags=False,
                               use_trailing_solidus=True,
                               space_before_trailing_solidus=False,
                               quote_attr_values="always",
                               quote_char="'",
                               alphabetical_attributes=True)
        errorMsg = "\n".join(["\n\nInput:", input,
                              "\nExpected:", expected,
                              "\nReceived:", serialized])
        assert expected == serialized, errorMsg

    def repr_failure(self, excinfo):
        traceback = excinfo.traceback
        ntraceback = traceback.cut(path=__file__)
        excinfo.traceback = ntraceback.filter()

        return excinfo.getrepr(funcargs=True,
                               showlocals=False,
                               style="short", tbfilter=False)
