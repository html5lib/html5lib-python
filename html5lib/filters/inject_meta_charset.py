from __future__ import absolute_import
from . import _base

class Filter(_base.Filter):
    def __init__(self, source, encoding):
        _base.Filter.__init__(self, source)
        self.encoding = encoding
    __init__.func_annotations = {}

    def __iter__(self):
        state = u"pre_head"
        meta_found = (self.encoding is None)
        pending = []

        for token in _base.Filter.__iter__(self):
            type = token[u"type"]
            if type == u"StartTag":
                if token[u"name"].lower() == u"head":
                    state = u"in_head"

            elif type == u"EmptyTag":
                if token[u"name"].lower() == u"meta":
                   # replace charset with actual encoding
                   has_http_equiv_content_type = False
                   for (namespace,name),value in token[u"data"].items():
                       if namespace != None:
                           continue
                       elif name.lower() == u'charset':
                          token[u"data"][(namespace,name)] = self.encoding
                          meta_found = True
                          break
                       elif name == u'http-equiv' and value.lower() == u'content-type':
                           has_http_equiv_content_type = True
                   else:
                       if has_http_equiv_content_type and (None, u"content") in token[u"data"]:
                           token[u"data"][(None, u"content")] = u'text/html; charset=%s' % self.encoding
                           meta_found = True

                elif token[u"name"].lower() == u"head" and not meta_found:
                    # insert meta into empty head
                    yield {u"type": u"StartTag", u"name": u"head",
                           u"data": token[u"data"]}
                    yield {u"type": u"EmptyTag", u"name": u"meta",
                           u"data": {(None, u"charset"): self.encoding}}
                    yield {u"type": u"EndTag", u"name": u"head"}
                    meta_found = True
                    continue

            elif type == u"EndTag":
                if token[u"name"].lower() == u"head" and pending:
                    # insert meta into head (if necessary) and flush pending queue
                    yield pending.pop(0)
                    if not meta_found:
                        yield {u"type": u"EmptyTag", u"name": u"meta",
                               u"data": {(None, u"charset"): self.encoding}}
                    while pending:
                        yield pending.pop(0)
                    meta_found = True
                    state = u"post_head"

            if state == u"in_head":
                pending.append(token)
            else:
                yield token
    __iter__.func_annotations = {}
