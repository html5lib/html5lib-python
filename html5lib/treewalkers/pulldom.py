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

from xml.dom.pulldom import START_ELEMENT, END_ELEMENT, \
    COMMENT, IGNORABLE_WHITESPACE, CHARACTERS

from . import _base

from ..constants import voidElements


class TreeWalker(_base.TreeWalker):
    def __iter__(self):
        ignore_until = None
        previous = None
        for event in self.tree:
            if previous is not None and \
                    (ignore_until is None or previous[1] is ignore_until):
                if previous[1] is ignore_until:
                    ignore_until = None
                for token in self.tokens(previous, event):
                    yield token
                    if token["type"] == "EmptyTag":
                        ignore_until = previous[1]
            previous = event
        if ignore_until is None or previous[1] is ignore_until:
            for token in self.tokens(previous, None):
                yield token
        elif ignore_until is not None:
            raise ValueError("Illformed DOM event stream: void element without END_ELEMENT")

    def tokens(self, event, next):
        type, node = event
        if type == START_ELEMENT:
            name = node.nodeName
            namespace = node.namespaceURI
            attrs = {}
            for attr in list(node.attributes.keys()):
                attr = node.getAttributeNode(attr)
                attrs[(attr.namespaceURI, attr.localName)] = attr.value
            if name in voidElements:
                for token in self.emptyTag(namespace,
                                           name,
                                           attrs,
                                           not next or next[1] is not node):
                    yield token
            else:
                yield self.startTag(namespace, name, attrs)

        elif type == END_ELEMENT:
            name = node.nodeName
            namespace = node.namespaceURI
            if name not in voidElements:
                yield self.endTag(namespace, name)

        elif type == COMMENT:
            yield self.comment(node.nodeValue)

        elif type in (IGNORABLE_WHITESPACE, CHARACTERS):
            for token in self.text(node.nodeValue):
                yield token

        else:
            yield self.unknown(type)
