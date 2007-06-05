try:
    frozenset
except NameError:
    # Import from the sets module for python 2.3
    from sets import ImmutableSet as frozenset

import gettext
_ = gettext.gettext

from constants import voidElements, booleanAttributes, spaceCharacters

spaceCharacters = u"".join(spaceCharacters)

try:
    from codecs import register_error, xmlcharrefreplace_errors
except ImportError:
    unicode_encode_errors = "strict"
else:
    unicode_encode_errors = "htmlentityreplace"

    from constants import entities

    encode_entity_map = {}
    for k, v in entities.items():
        if v != "&" and encode_entity_map.get(v) != k.lower():
            # prefer &lt; over &LT; and similarly for &amp;, &gt;, etc.
            encode_entity_map[v] = k

    def htmlentityreplace_errors(exc):
        if isinstance(exc, (UnicodeEncodeError, UnicodeTranslateError)):
            res = []
            for c in ex.object[exc.start:exc.end]:
                c = encode_entity_map.get(c)
                if c:
                    res.append("&")
                    res.append(c)
                    res.append(";")
                else:
                    res.append(c.encode(exc.encoding, "xmlcharrefreplace"))
            return (u"".join(res), exc.end)
        else:
            return xmlcharrefreplace_errors(exc)

    register_error(unicode_encode_errors, htmlentityreplace_errors)

    del register_error

def escape_text(text, encoding):
    return text.replace("&", "&amp;").encode(encoding, unicode_encode_errors)

class OptionalTagFilter:
    def __init__(self, source):
        self.source = source

    def slider(self):
        previous1 = previous2 = None
        for token in self.source:
            if previous1 is not None:
                yield previous2, previous1, token
            previous2 = previous1
            previous1 = token
        yield previous2, previous1, None

    def __iter__(self):
        for previous, token, next in self.slider():
            type = token["type"]
            if type == "StartTag":
                if token["data"] or not self.is_optional_start(token["name"], previous, next):
                    yield token
            elif type == "EndTag":
                if not self.is_optional_end(token["name"], next):
                    yield token
            else:
                yield token

    def is_optional_start(self, tagname, previous, next):
        type = next and next["type"] or None
        if tagname in 'html':
            # An html element's start tag may be omitted if the first thing
            # inside the html element is not a space character or a comment.
            return type not in ("Comment", "SpaceCharacters")
        elif tagname == 'head':
            # A head element's start tag may be omitted if the first thing
            # inside the head element is an element.
            return type == "StartTag"
        elif tagname == 'body':
            # A body element's start tag may be omitted if the first thing
            # inside the body element is not a space character or a comment,
            # except if the first thing inside the body element is a script
            # or style element and the node immediately preceding the body
            # element is a head element whose end tag has been omitted.
            if type in ("Comment", "SpaceCharacters"):
                return False
            elif type == "StartTag":
                # XXX: we do not look at the preceding event, so we never omit
                # the body element's start tag if it's followed by a script or
                # a style element.
                return next["name"] not in ('script', 'style')
            else:
                return True
        elif tagname == 'colgroup':
            # A colgroup element's start tag may be omitted if the first thing
            # inside the colgroup element is a col element, and if the element
            # is not immediately preceeded by another colgroup element whose
            # end tag has been omitted.
            if type == "StartTag":
                # XXX: we do not look at the preceding event, so instead we never
                # omit the colgroup element's end tag when it is immediately
                # followed by another colgroup element. See is_optional_end.
                return next["name"] == "col"
            else:
                return False
        elif tagname == 'tbody':
            # A tbody element's start tag may be omitted if the first thing
            # inside the tbody element is a tr element, and if the element is
            # not immediately preceeded by a tbody, thead, or tfoot element
            # whose end tag has been omitted.
            if type == "StartTag":
                # omit the thead and tfoot elements' end tag when they are
                # immediately followed by a tbody element. See is_optional_end.
                if previous and previous['type'] == 'EndTag' and \
                  previous['name'] in ('tbody','thead','tfoot'):
                    return False
                return next["name"] == 'tr'
            else:
                return False
        return False

    def is_optional_end(self, tagname, next):
        type = next and next["type"] or None
        if tagname in ('html', 'head', 'body'):
            # An html element's end tag may be omitted if the html element
            # is not immediately followed by a space character or a comment.
            return type not in ("Comment", "SpaceCharacters")
        elif tagname in ('li', 'optgroup', 'option', 'tr'):
            # A li element's end tag may be omitted if the li element is
            # immediately followed by another li element or if there is
            # no more content in the parent element.
            # An optgroup element's end tag may be omitted if the optgroup
            # element is immediately followed by another optgroup element,
            # or if there is no more content in the parent element.
            # An option element's end tag may be omitted if the option
            # element is immediately followed by another option element,
            # or if there is no more content in the parent element.
            # A tr element's end tag may be omitted if the tr element is
            # immediately followed by another tr element, or if there is
            # no more content in the parent element.
            if type == "StartTag":
                return next["name"] == tagname
            else:
                return type == "EndTag" or type is None
        elif tagname in ('dt', 'dd'):
            # A dt element's end tag may be omitted if the dt element is
            # immediately followed by another dt element or a dd element.
            # A dd element's end tag may be omitted if the dd element is
            # immediately followed by another dd element or a dt element,
            # or if there is no more content in the parent element.
            if type == "StartTag":
                return next["name"] in ('dt', 'dd')
            elif tagname == 'dd':
                return type == "EndTag" or type is None
            else:
                return False
        elif tagname == 'p':
            # A p element's end tag may be omitted if the p element is
            # immediately followed by an address, blockquote, dl, fieldset,
            # form, h1, h2, h3, h4, h5, h6, hr, menu, ol, p, pre, table,
            # or ul  element, or if there is no more content in the parent
            # element.
            if type == "StartTag":
                return next["name"] in ('address', 'blockquote', \
                    'dl', 'fieldset', 'form', 'h1', 'h2', 'h3', 'h4', 'h5', \
                    'h6', 'hr', 'menu', 'ol', 'p', 'pre', 'table', 'ul')
            else:
                return type == "EndTag" or type is None
        elif tagname == 'colgroup':
            # A colgroup element's end tag may be omitted if the colgroup
            # element is not immediately followed by a space character or
            # a comment.
            if type in ("Comment", "SpaceCharacters"):
                return False
            elif type == "StartTag":
                # XXX: we also look for an immediately following colgroup
                # element. See is_optional_start.
                return next["name"] != 'colgroup'
            else:
                return True
        elif tagname in ('thead', 'tbody'):
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
            if type == "StartTag":
                return next["name"] in ['tbody', 'tfoot']
            elif tagname == 'tbody':
                return type == "EndTag" or type is None
            else:
                return False
        elif tagname == 'tfoot':
            # A tfoot element's end tag may be omitted if the tfoot element
            # is immediately followed by a tbody element, or if there is no
            # more content in the parent element.
            # XXX: we never omit the end tag when the following element is
            # a tbody. See is_optional_start.
            if type == "StartTag":
                return next["name"] == 'tbody'
            else:
                return type == "EndTag" or type is None
        elif tagname in ('td', 'th'):
            # A td element's end tag may be omitted if the td element is
            # immediately followed by a td or th element, or if there is
            # no more content in the parent element.
            # A th element's end tag may be omitted if the th element is
            # immediately followed by a td or th element, or if there is
            # no more content in the parent element.
            if type == "StartTag":
                return next["name"] in ('td', 'th')
            else:
                return type == "EndTag" or type is None
        return False

class HTMLSerializer(object):
    cdata_elements = frozenset(("style", "script", "xmp", "iframe", "noembed", "noframes", "noscript"))

    quote_attr_values = False
    quote_char = '"'
    use_best_quote_char = True
    minimize_boolean_attributes = True

    use_trailing_solidus = False
    space_before_trailing_solidus = True

    omit_optional_tags = True

    strip_whitespace = False

    inject_meta_charset = True

    def __init__(self, **kwargs):
        if kwargs.has_key('quote_char'):
            self.use_best_quote_char = False
        for attr in ("quote_attr_values", "quote_char", "use_best_quote_char",
          "minimize_boolean_attributes", "use_trailing_solidus",
          "space_before_trailing_solidus", "omit_optional_tags",
          "strip_whitespace", "inject_meta_charset"):
            setattr(self, attr, kwargs.get(attr, getattr(self, attr)))
        self.errors = []
        self.strict = False

    def serialize(self, treewalker, encoding=None):
        in_cdata = False
        self.errors = []
        if encoding and self.inject_meta_charset:
            treewalker = self.filter_inject_meta_charset(treewalker, encoding)
        if self.strip_whitespace:
            treewalker = self.filter_whitespace(treewalker)
        if self.omit_optional_tags:
            treewalker = OptionalTagFilter(treewalker)
        for token in treewalker:
            type = token["type"]
            if type == "Doctype":
                doctype = u"<!DOCTYPE %s>" % token["name"]
                if encoding:
                    yield doctype.encode(encoding)
                else:
                    yield doctype

            elif type in ("Characters", "SpaceCharacters"):
                if type == "SpaceCharacters" or in_cdata:
                    if in_cdata and token["data"].find("</") >= 0:
                        self.serializeError(_("Unexpected </ in CDATA"))
                    if encoding:
                        yield token["data"].encode(encoding, "strict")
                    else:
                        yield token["data"]
                elif encoding:
                    yield escape_text(token["data"], encoding)
                else:
                    yield token["data"] \
                        .replace("&", "&amp;") \
                        .replace("<", "&lt;")  \
                        .replace(">", "&gt;")

            elif type in ("StartTag", "EmptyTag"):
                name = token["name"]
                if name in self.cdata_elements:
                    in_cdata = True
                elif in_cdata:
                    self.serializeError(_("Unexpected child element of a CDATA element"))
                attrs = token["data"]
                if hasattr(attrs, "items"):
                    attrs = attrs.items()
                attrs.sort()
                attributes = []
                for k,v in attrs:
                    if encoding:
                        k = k.encode(encoding, "strict")
                    attributes.append(' ')

                    attributes.append(k)
                    if not self.minimize_boolean_attributes or \
                      (k not in booleanAttributes.get(name, tuple()) \
                      and k not in booleanAttributes.get("", tuple())):
                        attributes.append("=")
                        if self.quote_attr_values or not v:
                            quote_attr = True
                        else:
                            quote_attr = reduce(lambda x,y: x or (y in v),
                                spaceCharacters + "<>\"'", False)
                        if encoding:
                            v = escape_text(v, encoding)
                        else:
                            v = v.replace("&", "&amp;")
                        if quote_attr:
                            quote_char = self.quote_char
                            if self.use_best_quote_char:
                                if "'" in v and '"' not in v:
                                    quote_char = '"'
                                elif '"' in v and "'" not in v:
                                    quote_char = "'"
                            if quote_char == "'":
                                v = v.replace("'", "&#39;")
                            else:
                                v = v.replace('"', "&quot;")
                            attributes.append(quote_char)
                            attributes.append(v)
                            attributes.append(quote_char)
                        else:
                            attributes.append(v)
                if name in voidElements and self.use_trailing_solidus:
                    if self.space_before_trailing_solidus:
                        attributes.append(" /")
                    else:
                        attributes.append("/")
                if encoding:
                    yield "<%s%s>" % (name.encode(encoding, "strict"), "".join(attributes))
                else:
                    yield u"<%s%s>" % (name, u"".join(attributes))

            elif type == "EndTag":
                name = token["name"]
                if name in self.cdata_elements:
                    in_cdata = False
                elif in_cdata:
                    self.serializeError(_("Unexpected child element of a CDATA element"))
                end_tag = u"</%s>" % name
                if encoding:
                    end_tag = end_tag.encode(encoding, "strict")
                yield end_tag

            elif type == "Comment":
                data = token["data"]
                if data.find("--") >= 0:
                    self.serializeError(_("Comment contains --"))
                comment = u"<!--%s-->" % token["data"]
                if encoding:
                    comment = comment.encode(encoding, unicode_encode_errors)
                yield comment

            else:
                self.serializeError(token["data"])

    def render(self, treewalker, encoding=None):
        if encoding:
            return "".join(list(self.serialize(treewalker, encoding)))
        else:
            return u"".join(list(self.serialize(treewalker)))

    def serializeError(self, data="XXX ERROR MESSAGE NEEDED"):
        # XXX The idea is to make data mandatory.
        self.errors.append(data)
        if self.strict:
            raise SerializeError

    def filter_inject_meta_charset(self, treewalker, encoding):
        done = False
        for token in treewalker:
            if not done and token["type"] == "StartTag" \
              and token["name"].lower() == "head":
                yield {"type": "EmptyTag", "name": "meta", \
                    "data": {"charset": encoding}}
            yield token

    def filter_whitespace(self, treewalker):
        raise NotImplementedError

def SerializeError(Exception):
    """Error in serialized tree"""
    pass
