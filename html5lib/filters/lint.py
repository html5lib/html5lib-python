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
from ..constants import cdataElements, rcdataElements, voidElements

from ..constants import spaceCharacters
spaceCharacters = "".join(spaceCharacters)


class LintError(Exception):
    pass


class Filter(_base.Filter):
    def __iter__(self):
        open_elements = []
        contentModelFlag = "PCDATA"
        for token in _base.Filter.__iter__(self):
            type = token["type"]
            if type in ("StartTag", "EmptyTag"):
                name = token["name"]
                if contentModelFlag != "PCDATA":
                    raise LintError("StartTag not in PCDATA content model flag: %(tag)s" % {"tag": name})
                if not isinstance(name, str):
                    raise LintError("Tag name is not a string: %(tag)r" % {"tag": name})
                if not name:
                    raise LintError("Empty tag name")
                if type == "StartTag" and name in voidElements:
                    raise LintError("Void element reported as StartTag token: %(tag)s" % {"tag": name})
                elif type == "EmptyTag" and name not in voidElements:
                    raise LintError("Non-void element reported as EmptyTag token: %(tag)s" % {"tag": token["name"]})
                if type == "StartTag":
                    open_elements.append(name)
                for name, value in token["data"]:
                    if not isinstance(name, str):
                        raise LintError("Attribute name is not a string: %(name)r" % {"name": name})
                    if not name:
                        raise LintError("Empty attribute name")
                    if not isinstance(value, str):
                        raise LintError("Attribute value is not a string: %(value)r" % {"value": value})
                if name in cdataElements:
                    contentModelFlag = "CDATA"
                elif name in rcdataElements:
                    contentModelFlag = "RCDATA"
                elif name == "plaintext":
                    contentModelFlag = "PLAINTEXT"

            elif type == "EndTag":
                name = token["name"]
                if not isinstance(name, str):
                    raise LintError("Tag name is not a string: %(tag)r" % {"tag": name})
                if not name:
                    raise LintError("Empty tag name")
                if name in voidElements:
                    raise LintError("Void element reported as EndTag token: %(tag)s" % {"tag": name})
                start_name = open_elements.pop()
                if start_name != name:
                    raise LintError("EndTag (%(end)s) does not match StartTag (%(start)s)" % {"end": name, "start": start_name})
                contentModelFlag = "PCDATA"

            elif type == "Comment":
                if contentModelFlag != "PCDATA":
                    raise LintError("Comment not in PCDATA content model flag")

            elif type in ("Characters", "SpaceCharacters"):
                data = token["data"]
                if not isinstance(data, str):
                    raise LintError("Attribute name is not a string: %(name)r" % {"name": data})
                if not data:
                    raise LintError("%(type)s token with empty data" % {"type": type})
                if type == "SpaceCharacters":
                    data = data.strip(spaceCharacters)
                    if data:
                        raise LintError("Non-space character(s) found in SpaceCharacters token: %(token)r" % {"token": data})

            elif type == "Doctype":
                name = token["name"]
                if contentModelFlag != "PCDATA":
                    raise LintError("Doctype not in PCDATA content model flag: %(name)s" % {"name": name})
                if not isinstance(name, str):
                    raise LintError("Tag name is not a string: %(tag)r" % {"tag": name})
                # XXX: what to do with token["data"] ?

            elif type in ("ParseError", "SerializeError"):
                pass

            else:
                raise LintError("Unknown token type: %(type)s" % {"type": type})

            yield token
