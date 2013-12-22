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

from . import _base


class Filter(_base.Filter):
    def __init__(self, source, encoding):
        _base.Filter.__init__(self, source)
        self.encoding = encoding

    def __iter__(self):
        state = "pre_head"
        meta_found = (self.encoding is None)
        pending = []

        for token in _base.Filter.__iter__(self):
            type = token["type"]
            if type == "StartTag":
                if token["name"].lower() == "head":
                    state = "in_head"

            elif type == "EmptyTag":
                if token["name"].lower() == "meta":
                    # replace charset with actual encoding
                    has_http_equiv_content_type = False
                    for (namespace, name), value in token["data"].items():
                        if namespace is not None:
                            continue
                        elif name.lower() == 'charset':
                            token["data"][(namespace, name)] = self.encoding
                            meta_found = True
                            break
                        elif name == 'http-equiv' and value.lower() == 'content-type':
                            has_http_equiv_content_type = True
                    else:
                        if has_http_equiv_content_type and (None, "content") in token["data"]:
                            token["data"][(None, "content")] = 'text/html; charset=%s' % self.encoding
                            meta_found = True

                elif token["name"].lower() == "head" and not meta_found:
                    # insert meta into empty head
                    yield {"type": "StartTag", "name": "head",
                           "data": token["data"]}
                    yield {"type": "EmptyTag", "name": "meta",
                           "data": {(None, "charset"): self.encoding}}
                    yield {"type": "EndTag", "name": "head"}
                    meta_found = True
                    continue

            elif type == "EndTag":
                if token["name"].lower() == "head" and pending:
                    # insert meta into head (if necessary) and flush pending queue
                    yield pending.pop(0)
                    if not meta_found:
                        yield {"type": "EmptyTag", "name": "meta",
                               "data": {(None, "charset"): self.encoding}}
                    while pending:
                        yield pending.pop(0)
                    meta_found = True
                    state = "post_head"

            if state == "in_head":
                pending.append(token)
            else:
                yield token
