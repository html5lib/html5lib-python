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

from xml.sax.xmlreader import AttributesNSImpl

from ..constants import adjustForeignAttributes, unadjustForeignAttributes

prefix_mapping = {}
for prefix, localName, namespace in adjustForeignAttributes.values():
    if prefix is not None:
        prefix_mapping[prefix] = namespace


def to_sax(walker, handler):
    """Call SAX-like content handler based on treewalker walker"""
    handler.startDocument()
    for prefix, namespace in prefix_mapping.items():
        handler.startPrefixMapping(prefix, namespace)

    for token in walker:
        type = token["type"]
        if type == "Doctype":
            continue
        elif type in ("StartTag", "EmptyTag"):
            attrs = AttributesNSImpl(token["data"],
                                     unadjustForeignAttributes)
            handler.startElementNS((token["namespace"], token["name"]),
                                   token["name"],
                                   attrs)
            if type == "EmptyTag":
                handler.endElementNS((token["namespace"], token["name"]),
                                     token["name"])
        elif type == "EndTag":
            handler.endElementNS((token["namespace"], token["name"]),
                                 token["name"])
        elif type in ("Characters", "SpaceCharacters"):
            handler.characters(token["data"])
        elif type == "Comment":
            pass
        else:
            assert False, "Unknown token type"

    for prefix, namespace in prefix_mapping.items():
        handler.endPrefixMapping(prefix)
    handler.endDocument()
