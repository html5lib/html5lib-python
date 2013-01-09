from __future__ import absolute_import
from . import _base

class Filter(_base.Filter):
    def slider(self):
        previous1 = previous2 = None
        for token in self.source:
            if previous1 is not None:
                yield previous2, previous1, token
            previous2 = previous1
            previous1 = token
        yield previous2, previous1, None
    slider.func_annotations = {}

    def __iter__(self):
        for previous, token, next in self.slider():
            type = token[u"type"]
            if type == u"StartTag":
                if (token[u"data"] or 
                    not self.is_optional_start(token[u"name"], previous, next)):
                    yield token
            elif type == u"EndTag":
                if not self.is_optional_end(token[u"name"], next):
                    yield token
            else:
                yield token
    __iter__.func_annotations = {}

    def is_optional_start(self, tagname, previous, next):
        type = next and next[u"type"] or None
        if tagname in u'html':
            # An html element's start tag may be omitted if the first thing
            # inside the html element is not a space character or a comment.
            return type not in (u"Comment", u"SpaceCharacters")
        elif tagname == u'head':
            # A head element's start tag may be omitted if the first thing
            # inside the head element is an element.
            # XXX: we also omit the start tag if the head element is empty
            if type in (u"StartTag", u"EmptyTag"):
                return True
            elif type == u"EndTag":
                return next[u"name"] == u"head"
        elif tagname == u'body':
            # A body element's start tag may be omitted if the first thing
            # inside the body element is not a space character or a comment,
            # except if the first thing inside the body element is a script
            # or style element and the node immediately preceding the body
            # element is a head element whose end tag has been omitted.
            if type in (u"Comment", u"SpaceCharacters"):
                return False
            elif type == u"StartTag":
                # XXX: we do not look at the preceding event, so we never omit
                # the body element's start tag if it's followed by a script or
                # a style element.
                return next[u"name"] not in (u'script', u'style')
            else:
                return True
        elif tagname == u'colgroup':
            # A colgroup element's start tag may be omitted if the first thing
            # inside the colgroup element is a col element, and if the element
            # is not immediately preceeded by another colgroup element whose
            # end tag has been omitted.
            if type in (u"StartTag", u"EmptyTag"):
                # XXX: we do not look at the preceding event, so instead we never
                # omit the colgroup element's end tag when it is immediately
                # followed by another colgroup element. See is_optional_end.
                return next[u"name"] == u"col"
            else:
                return False
        elif tagname == u'tbody':
            # A tbody element's start tag may be omitted if the first thing
            # inside the tbody element is a tr element, and if the element is
            # not immediately preceeded by a tbody, thead, or tfoot element
            # whose end tag has been omitted.
            if type == u"StartTag":
                # omit the thead and tfoot elements' end tag when they are
                # immediately followed by a tbody element. See is_optional_end.
                if previous and previous[u'type'] == u'EndTag' and \
                  previous[u'name'] in (u'tbody',u'thead',u'tfoot'):
                    return False
                return next[u"name"] == u'tr'
            else:
                return False
        return False
    is_optional_start.func_annotations = {}

    def is_optional_end(self, tagname, next):
        type = next and next[u"type"] or None
        if tagname in (u'html', u'head', u'body'):
            # An html element's end tag may be omitted if the html element
            # is not immediately followed by a space character or a comment.
            return type not in (u"Comment", u"SpaceCharacters")
        elif tagname in (u'li', u'optgroup', u'tr'):
            # A li element's end tag may be omitted if the li element is
            # immediately followed by another li element or if there is
            # no more content in the parent element.
            # An optgroup element's end tag may be omitted if the optgroup
            # element is immediately followed by another optgroup element,
            # or if there is no more content in the parent element.
            # A tr element's end tag may be omitted if the tr element is
            # immediately followed by another tr element, or if there is
            # no more content in the parent element.
            if type == u"StartTag":
                return next[u"name"] == tagname
            else:
                return type == u"EndTag" or type is None
        elif tagname in (u'dt', u'dd'):
            # A dt element's end tag may be omitted if the dt element is
            # immediately followed by another dt element or a dd element.
            # A dd element's end tag may be omitted if the dd element is
            # immediately followed by another dd element or a dt element,
            # or if there is no more content in the parent element.
            if type == u"StartTag":
                return next[u"name"] in (u'dt', u'dd')
            elif tagname == u'dd':
                return type == u"EndTag" or type is None
            else:
                return False
        elif tagname == u'p':
            # A p element's end tag may be omitted if the p element is
            # immediately followed by an address, article, aside,
            # blockquote, datagrid, dialog, dir, div, dl, fieldset,
            # footer, form, h1, h2, h3, h4, h5, h6, header, hr, menu,
            # nav, ol, p, pre, section, table, or ul, element, or if
            # there is no more content in the parent element.
            if type in (u"StartTag", u"EmptyTag"):
                return next[u"name"] in (u'address', u'article', u'aside',
                                        u'blockquote', u'datagrid', u'dialog', 
                                        u'dir', u'div', u'dl', u'fieldset', u'footer',
                                        u'form', u'h1', u'h2', u'h3', u'h4', u'h5', u'h6',
                                        u'header', u'hr', u'menu', u'nav', u'ol', 
                                        u'p', u'pre', u'section', u'table', u'ul')
            else:
                return type == u"EndTag" or type is None
        elif tagname == u'option':
            # An option element's end tag may be omitted if the option
            # element is immediately followed by another option element,
            # or if it is immediately followed by an <code>optgroup</code>
            # element, or if there is no more content in the parent
            # element.
            if type == u"StartTag":
                return next[u"name"] in (u'option', u'optgroup')
            else:
                return type == u"EndTag" or type is None
        elif tagname in (u'rt', u'rp'):
            # An rt element's end tag may be omitted if the rt element is
            # immediately followed by an rt or rp element, or if there is
            # no more content in the parent element.
            # An rp element's end tag may be omitted if the rp element is
            # immediately followed by an rt or rp element, or if there is
            # no more content in the parent element.
            if type == u"StartTag":
                return next[u"name"] in (u'rt', u'rp')
            else:
                return type == u"EndTag" or type is None
        elif tagname == u'colgroup':
            # A colgroup element's end tag may be omitted if the colgroup
            # element is not immediately followed by a space character or
            # a comment.
            if type in (u"Comment", u"SpaceCharacters"):
                return False
            elif type == u"StartTag":
                # XXX: we also look for an immediately following colgroup
                # element. See is_optional_start.
                return next[u"name"] != u'colgroup'
            else:
                return True
        elif tagname in (u'thead', u'tbody'):
            # A thead element's end tag may be omitted if the thead element
            # is immediately followed by a tbody or tfoot element.
            # A tbody element's end tag may be omitted if the tbody element
            # is immediately followed by a tbody or tfoot element, or if
            # there is no more content in the parent element.
            # A tfoot element's end tag may be omitted if the tfoot element
            # is immediately followed by a tbody element, or if there is no
            # more content in the parent element.
            # XXX: we never omit the end tag when the following element is
            # a tbody. See is_optional_start.
            if type == u"StartTag":
                return next[u"name"] in [u'tbody', u'tfoot']
            elif tagname == u'tbody':
                return type == u"EndTag" or type is None
            else:
                return False
        elif tagname == u'tfoot':
            # A tfoot element's end tag may be omitted if the tfoot element
            # is immediately followed by a tbody element, or if there is no
            # more content in the parent element.
            # XXX: we never omit the end tag when the following element is
            # a tbody. See is_optional_start.
            if type == u"StartTag":
                return next[u"name"] == u'tbody'
            else:
                return type == u"EndTag" or type is None
        elif tagname in (u'td', u'th'):
            # A td element's end tag may be omitted if the td element is
            # immediately followed by a td or th element, or if there is
            # no more content in the parent element.
            # A th element's end tag may be omitted if the th element is
            # immediately followed by a td or th element, or if there is
            # no more content in the parent element.
            if type == u"StartTag":
                return next[u"name"] in (u'td', u'th')
            else:
                return type == u"EndTag" or type is None
        return False
    is_optional_end.func_annotations = {}
