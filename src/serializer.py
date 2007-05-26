from constants import voidElements, booleanAttributes

try:
    frozenset
except NameError:
    # Import from the sets module for python 2.3
    from sets import ImmutableSet as frozenset

import gettext
_ = gettext.gettext

def _slide(iterator):
    previous = None
    for token in iterator:
        if previous is not None:
            yield previous, token
        previous = token
    yield previous, None

class HTMLSerializer(object):
    cdata_elements = frozenset(("style", "script", "xmp", "iframe", "noembed", "noframes", "noscript"))
    
    quote_attr_values = False
    quote_char = '"'
    minimize_boolean_attributes = True
    
    trailing_solidus = " /"
    
    omit_optional_tags = True
    
    def __init__(self, **kwargs):
        for attr in ("quote_attr_values", "quote_char",
          "minimize_boolean_attributes", "trailing_solidus",
          "omit_optional_tags"):
            if attr in kwargs:
                setattr(self, attr, kwargs[attr])
        self.errors = []
    
    def serialize(self, treewalker):
        in_cdata = False
        self.errors = []
        if self.omit_optional_tags:
            treewalker = self.filter(treewalker)
        for token in treewalker:
            type = token["type"]
            if type == "Doctype":
                yield u"<!DOCTYPE %s>" % token["name"]
            
            elif type in ("Characters", "SpaceCharacters"):
                if type == "SpaceCharacters" or in_cdata:
                    if in_cdata and token["data"].find("</") >= 0:
                        self.serializeError(_("Unexpected </ in CDATA"))
                    yield token["data"]
                else:
                    yield token["data"] \
                        .replace("&", "&amp;") \
                        .replace("<", "&lt;")  \
                        .replace(">", "&gt;")  \
            
            elif type in ("StartTag", "EmptyTag"):
                name = token["name"]
                if name in self.cdata_elements:
                    in_cdata = True
                elif in_cdata:
                    self.serializeError(_("Unexpected child element of a CDATA element"))
                attrs = token["data"]
                attrs.sort()
                attributes = []
                for k,v in attrs:
                    attributes.append(' ')
                    attributes.append(k)
                    if not self.minimize_boolean_attributes or \
                      (k not in booleanAttributes.get(name, tuple()) \
                      and k not in booleanAttributes.get("", tuple())):
                        attributes.append("=")
                        v = v.replace("&", "&amp;")
                        if self.quote_attr_values:
                            quote_attr = True
                        else:
                            quote_attr = reduce(lambda x,y: x or y in v,
                                spaceCharacters + "<>\"'", False)
                        if quote_attr:
                            if self.quote_char == '"':
                                v = v.replace('"', "&quot;")
                            else:
                                v = v.replace(self.quote_char, "&#%u;" % ord(self.quote_char))
                            attributes.append(self.quote_char)
                            attributes.append(v)
                            attributes.append(self.quote_char)
                        else:
                            attributes.append(v)
                if name in voidElements and self.include_trailing_slashes:
                    attributes.append(" /")
                yield u"<%s%s>" % (name, u"".join(attributes))
            
            elif type == "EndTag":
                name = token["name"]
                if name in self.cdata_elements:
                    in_cdata = False
                elif in_cdata:
                    self.serializeError(_("Unexpected child element of a CDATA element"))
                yield u"</%s>" % name
            
            elif type == "Comment":
                data = token["data"]
                if data.find("--") >= 0:
                    self.serializeError(_("Comment contains --"))
                yield u"<!--%s-->" % token["data"]
            
            else:
                self.serializeError(token["data"])
    
    def render(self, treewalker, encoding='UTF-8', errors="strict"):
        u''.join(list(self.serialize(treewalker))).encode(encoding, errors)
    
    def filter(self, treewalker):
        for token, next in _slide(treewalker):
            type = token["type"]
            if type == "StartTag":
                if token["data"] or not self.is_optional_start(token["name"], next):
                    yield token
            elif type == "EndTag":
                if not self.is_optional_end(token["name"], next):
                    yield token
            else:
                yield token
    
    def serializeError(self, data="XXX ERROR MESSAGE NEEDED"):
        # XXX The idea is to make data mandatory.
        self.errors.append(data)
        if self.strict:
            raise SerializeError

    def is_optional_start(self, tagname, next):
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
                # followed by another colgroup element. See _is_optional_end.
                return next["name"] == "col"
            else:
                return False
        elif tagname == 'tbody':
            # A tbody element's start tag may be omitted if the first thing
            # inside the tbody element is a tr element, and if the element is
            # not immediately preceeded by a tbody, thead, or tfoot element
            # whose end tag has been omitted.
            if type == "StartTag":
                # XXX: we do not look at the preceding event, so instead we never
                # omit the thead and tfoot elements' end tag when they are
                # immediately followed by a tbody element. See _is_optional_end.
                return next["name"] == 'tr'
            else:
                return False
        # TODO
        return False
    
    def _is_optional_end(self, tagname, next_event):
        type, data = next_event
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
                # element. See _is_optional_start.
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
            # a tbody. See _is_optional_start.
            if type == "StartTag":
                return next["name"] == 'tfoot'
            elif tagname == 'tbody':
                return type == "EndTag" or type is None
            else:
                return False
        elif tagname == 'tfoot':
            # A tfoot element's end tag may be omitted if the tfoot element
            # is immediately followed by a tbody element, or if there is no
            # more content in the parent element.
            # XXX: we never omit the end tag when the following element is
            # a tbody. See _is_optional_start.
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
        # TODO
        return False
    
def SerializeError(Exception):
    """Error in serialized tree"""
    pass
