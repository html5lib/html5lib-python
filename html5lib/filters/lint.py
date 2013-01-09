from __future__ import absolute_import
from gettext import gettext
_ = gettext

from . import _base
from html5lib.constants import cdataElements, rcdataElements, voidElements

from html5lib.constants import spaceCharacters
spaceCharacters = u"".join(spaceCharacters)

class LintError(Exception): pass

class Filter(_base.Filter):
    def __iter__(self):
        open_elements = []
        contentModelFlag = u"PCDATA"
        for token in _base.Filter.__iter__(self):
            type = token[u"type"]
            if type in (u"StartTag", u"EmptyTag"):
                name = token[u"name"]
                if contentModelFlag != u"PCDATA":
                    raise LintError(_(u"StartTag not in PCDATA content model flag: %s") % name)
                if not isinstance(name, unicode):
                    raise LintError(_(u"Tag name is not a string: %r") % name)
                if not name:
                    raise LintError(_(u"Empty tag name"))
                if type == u"StartTag" and name in voidElements:
                    raise LintError(_(u"Void element reported as StartTag token: %s") % name)
                elif type == u"EmptyTag" and name not in voidElements:
                    raise LintError(_(u"Non-void element reported as EmptyTag token: %s") % token[u"name"])
                if type == u"StartTag":
                    open_elements.append(name)
                for name, value in token[u"data"]:
                    if not isinstance(name, unicode):
                        raise LintError(_(u"Attribute name is not a string: %r") % name)
                    if not name:
                        raise LintError(_(u"Empty attribute name"))
                    if not isinstance(value, unicode):
                        raise LintError(_(u"Attribute value is not a string: %r") % value)
                if name in cdataElements:
                    contentModelFlag = u"CDATA"
                elif name in rcdataElements:
                    contentModelFlag = u"RCDATA"
                elif name == u"plaintext":
                    contentModelFlag = u"PLAINTEXT"

            elif type == u"EndTag":
                name = token[u"name"]
                if not isinstance(name, unicode):
                    raise LintError(_(u"Tag name is not a string: %r") % name)
                if not name:
                    raise LintError(_(u"Empty tag name"))
                if name in voidElements:
                    raise LintError(_(u"Void element reported as EndTag token: %s") % name)
                start_name = open_elements.pop()
                if start_name != name:
                    raise LintError(_(u"EndTag (%s) does not match StartTag (%s)") % (name, start_name))
                contentModelFlag = u"PCDATA"

            elif type == u"Comment":
                if contentModelFlag != u"PCDATA":
                    raise LintError(_(u"Comment not in PCDATA content model flag"))

            elif type in (u"Characters", u"SpaceCharacters"):
                data = token[u"data"]
                if not isinstance(data, unicode):
                    raise LintError(_(u"Attribute name is not a string: %r") % data)
                if not data:
                    raise LintError(_(u"%s token with empty data") % type)
                if type == u"SpaceCharacters":
                    data = data.strip(spaceCharacters)
                    if data:
                        raise LintError(_(u"Non-space character(s) found in SpaceCharacters token: ") % data)

            elif type == u"Doctype":
                name = token[u"name"]
                if contentModelFlag != u"PCDATA":
                    raise LintError(_(u"Doctype not in PCDATA content model flag: %s") % name)
                if not isinstance(name, unicode):
                    raise LintError(_(u"Tag name is not a string: %r") % name)
                # XXX: what to do with token["data"] ?

            elif type in (u"ParseError", u"SerializeError"):
                pass

            else:
                raise LintError(_(u"Unknown token type: %s") % type)

            yield token
    __iter__.func_annotations = {}
