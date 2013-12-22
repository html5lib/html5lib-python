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

from genshi.core import QName
from genshi.core import START, END, XML_NAMESPACE, DOCTYPE, TEXT
from genshi.core import START_NS, END_NS, START_CDATA, END_CDATA, PI, COMMENT

from . import _base

from ..constants import voidElements, namespaces


class TreeWalker(_base.TreeWalker):
    def __iter__(self):
        # Buffer the events so we can pass in the following one
        previous = None
        for event in self.tree:
            if previous is not None:
                for token in self.tokens(previous, event):
                    yield token
            previous = event

        # Don't forget the final event!
        if previous is not None:
            for token in self.tokens(previous, None):
                yield token

    def tokens(self, event, next):
        kind, data, pos = event
        if kind == START:
            tag, attribs = data
            name = tag.localname
            namespace = tag.namespace
            converted_attribs = {}
            for k, v in attribs:
                if isinstance(k, QName):
                    converted_attribs[(k.namespace, k.localname)] = v
                else:
                    converted_attribs[(None, k)] = v

            if namespace == namespaces["html"] and name in voidElements:
                for token in self.emptyTag(namespace, name, converted_attribs,
                                           not next or next[0] != END
                                           or next[1] != tag):
                    yield token
            else:
                yield self.startTag(namespace, name, converted_attribs)

        elif kind == END:
            name = data.localname
            namespace = data.namespace
            if name not in voidElements:
                yield self.endTag(namespace, name)

        elif kind == COMMENT:
            yield self.comment(data)

        elif kind == TEXT:
            for token in self.text(data):
                yield token

        elif kind == DOCTYPE:
            yield self.doctype(*data)

        elif kind in (XML_NAMESPACE, DOCTYPE, START_NS, END_NS,
                      START_CDATA, END_CDATA, PI):
            pass

        else:
            yield self.unknown(kind)
