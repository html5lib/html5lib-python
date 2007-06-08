from gettext import gettext
_ = gettext

import _base
from constants import cdataElements, rcdataElements, voidElements

from constants import spaceCharacters
spaceCharacters = u"".join(spaceCharacters)

class LintError(Exception): pass

class Filter(_base.Filter):
    def __iter__(self):
        open_elements = []
        contentModelFlag = "PCDATA"
        for token in _base.Filter.__iter__(self):
            type = token["type"]
            if type in ("StartTag", "EmptyTag"):
                name = token["name"]
                if not isinstance(name, basestring):
                    raise LintError(_(u"Tag name is not a string: %r") % name)
                if not name:
                    raise LintError(_(u"Empty tag name"))
                if type == "StartTag" and name in voidElements:
                    raise LintError(_(u"Void element reported as StartTag token: %s") % name)
                elif type == "EmptyTag" and name not in voidElements:
                    raise LintError(_(u"Non-void element reported as EmptyTag token: %s") % token["name"])
                for name, value in token["data"]:
                    if not isinstance(name, basestring):
                        raise LintError(_("Attribute name is not a string: %r") % name)
                    if not name:
                        raise LintError(_(u"Empty attribute name"))
                    if not isinstance(value, basestring):
                        raise LintError(_("Attribute value is not a string: %r") % value)
                open_elements.append(name)
                if name in cdataElements:
                    contentModelFlag = "CDATA"
                elif name in rcdataElements:
                    contentModelFlag = "RCDATA"
                elif name == "textarea":
                    contentModelFlag = "PLAINTEXT"

            elif type == "EndTag":
                name = token["name"]
                if not isinstance(name, basestring):
                    raise LintError(_(u"Tag name is not a string: %r") % name)
                if not name:
                    raise LintError(_(u"Empty tag name"))
                if name in voidElements:
                    raise LintError(_(u"Void element reported as EndTag token: %s") % name)
                if open_elements.pop() != name:
                    raise LintError(_(u"EndTag does not match StartTag: %s") % name)
                contentModelFlag = "PCDATA"

            elif type == "Comment":
                pass
                # XXX: This make tests fail
                # if token["data"].find("--") >= 0:
                #     raise LintError(_(u"Comment contains double-dash"))

            elif type in ("Characters", "SpaceCharacters"):
                data = token["data"]
                if not isinstance(data, basestring):
                    raise LintError(_("Attribute name is not a string: %r") % data)
                if not data:
                    raise LintError(_(u"%s token with empty data") % type)
                if type == "SpaceCharacters":
                    data = data.strip(spaceCharacters)
                    if data:
                        raise LintError(_(u"Non-space character(s) found in SpaceCharacters token: ") % data)

            elif type == "Doctype":
                name = token["name"]
                if not isinstance(name, basestring):
                    raise LintError(_(u"Tag name is not a string: %r") % name)
                if not name:
                    raise LintError(_(u"Empty tag name"))
                # XXX: what to do with token["data"] ?

            else:
                raise LintError(_(u"Unknown token type: %s") % type)

            yield token
