from __future__ import absolute_import, division, unicode_literals

from six import text_type

from . import _base
from ..constants import namespaces, voidElements

from ..constants import spaceCharacters
spaceCharacters = "".join(spaceCharacters)


class LintError(Exception):
    pass


class Filter(_base.Filter):
    def __iter__(self):
        open_elements = []
        for token in _base.Filter.__iter__(self):
            type = token["type"]
            if type in ("StartTag", "EmptyTag"):
                namespace = token["namespace"]
                name = token["name"]
                if namespace is not None and not isinstance(namespace, text_type):
                    raise LintError("Tag namespace is not a string or None: %(name)r" % {"name": namespace})
                if namespace == "":
                    raise LintError("Empty tag namespace")
                if not isinstance(name, text_type):
                    raise LintError("Tag name is not a string: %(tag)r" % {"tag": name})
                if not name:
                    raise LintError("Empty tag name")
                if type == "StartTag" and (not namespace or namespace == namespaces["html"]) and name in voidElements:
                    raise LintError("Void element reported as StartTag token: %(tag)s" % {"tag": name})
                elif type == "EmptyTag" and (not namespace or namespace == namespaces["html"]) and name not in voidElements:
                    raise LintError("Non-void element reported as EmptyTag token: %(tag)s" % {"tag": token["name"]})
                if type == "StartTag":
                    open_elements.append((namespace, name))
                for (namespace, localname), value in token["data"].items():
                    if namespace is not None and not isinstance(namespace, text_type):
                        raise LintError("Attribute namespace is not a string or None: %(name)r" % {"name": namespace})
                    if namespace == "":
                        raise LintError("Empty attribute namespace")
                    if not isinstance(localname, text_type):
                        raise LintError("Attribute localname is not a string: %(name)r" % {"name": localname})
                    if not localname:
                        raise LintError("Empty attribute localname")
                    if not isinstance(value, text_type):
                        raise LintError("Attribute value is not a string: %(value)r" % {"value": value})

            elif type == "EndTag":
                namespace = token["namespace"]
                name = token["name"]
                if namespace is not None and not isinstance(namespace, text_type):
                    raise LintError("Tag namespace is not a string or None: %(name)r" % {"name": namespace})
                if namespace == "":
                    raise LintError("Empty tag namespace")
                if not isinstance(name, text_type):
                    raise LintError("Tag name is not a string: %(tag)r" % {"tag": name})
                if not name:
                    raise LintError("Empty tag name")
                if (not namespace or namespace == namespaces["html"]) and name in voidElements:
                    raise LintError("Void element reported as EndTag token: %(tag)s" % {"tag": name})
                start_name = open_elements.pop()
                if start_name != (namespace, name):
                    raise LintError("EndTag (%(end)s) does not match StartTag (%(start)s)" % {"end": name, "start": start_name})

            elif type == "Comment":
                pass

            elif type in ("Characters", "SpaceCharacters"):
                data = token["data"]
                if not isinstance(data, text_type):
                    raise LintError("Attribute name is not a string: %(name)r" % {"name": data})
                if not data:
                    raise LintError("%(type)s token with empty data" % {"type": type})
                if type == "SpaceCharacters":
                    data = data.strip(spaceCharacters)
                    if data:
                        raise LintError("Non-space character(s) found in SpaceCharacters token: %(token)r" % {"token": data})

            elif type == "Doctype":
                name = token["name"]
                if name is not None and not isinstance(name, text_type):
                    raise LintError("Tag name is not a string or None: %(tag)r" % {"tag": name})
                # XXX: what to do with token["data"] ?

            elif type in ("ParseError", "SerializeError"):
                pass

            else:
                raise LintError("Unknown token type: %(type)s" % {"type": type})

            yield token
