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

from genshi.core import QName, Attrs
from genshi.core import START, END, TEXT, COMMENT, DOCTYPE


def to_genshi(walker):
    text = []
    for token in walker:
        type = token["type"]
        if type in ("Characters", "SpaceCharacters"):
            text.append(token["data"])
        elif text:
            yield TEXT, "".join(text), (None, -1, -1)
            text = []

        if type in ("StartTag", "EmptyTag"):
            if token["namespace"]:
                name = "{%s}%s" % (token["namespace"], token["name"])
            else:
                name = token["name"]
            attrs = Attrs([(QName("{%s}%s" % attr if attr[0] is not None else attr[1]), value)
                           for attr, value in token["data"].items()])
            yield (START, (QName(name), attrs), (None, -1, -1))
            if type == "EmptyTag":
                type = "EndTag"

        if type == "EndTag":
            if token["namespace"]:
                name = "{%s}%s" % (token["namespace"], token["name"])
            else:
                name = token["name"]

            yield END, QName(name), (None, -1, -1)

        elif type == "Comment":
            yield COMMENT, token["data"], (None, -1, -1)

        elif type == "Doctype":
            yield DOCTYPE, (token["name"], token["publicId"],
                            token["systemId"]), (None, -1, -1)

        else:
            pass  # FIXME: What to do?

    if text:
        yield TEXT, "".join(text), (None, -1, -1)
