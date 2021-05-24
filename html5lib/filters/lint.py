from six import text_type

from . import base
from ..constants import namespaces, voidElements

from ..constants import spaceCharacters
spaceCharacters = "".join(spaceCharacters)


class Filter(base.Filter):
    """Lints the token stream for errors

    If it finds any errors, it'll raise an ``AssertionError``.

    """
    def __init__(self, source, require_matching_tags=True):
        """Creates a Filter

        :arg source: the source token stream

        :arg require_matching_tags: whether or not to require matching tags

        """
        super().__init__(source)
        self.require_matching_tags = require_matching_tags

    def __iter__(self):
        open_elements = []
        for token in base.Filter.__iter__(self):
            type = token["type"]
            if type in ("StartTag", "EmptyTag"):
                namespace = token["namespace"]
                name = token["name"]
                assert namespace is None or isinstance(namespace, str)
                assert namespace != ""
                assert isinstance(name, str)
                assert name != ""
                assert isinstance(token["data"], dict)
                if (not namespace or namespace == namespaces["html"]) and name in voidElements:
                    assert type == "EmptyTag"
                else:
                    assert type == "StartTag"
                if type == "StartTag" and self.require_matching_tags:
                    open_elements.append((namespace, name))
                for (namespace, name), value in token["data"].items():
                    assert namespace is None or isinstance(namespace, str)
                    assert namespace != ""
                    assert isinstance(name, str)
                    assert name != ""
                    assert isinstance(value, str)

            elif type == "EndTag":
                namespace = token["namespace"]
                name = token["name"]
                assert namespace is None or isinstance(namespace, str)
                assert namespace != ""
                assert isinstance(name, str)
                assert name != ""
                if (not namespace or namespace == namespaces["html"]) and name in voidElements:
                    assert False, "Void element reported as EndTag token: {tag}".format(tag=name)
                elif self.require_matching_tags:
                    start = open_elements.pop()
                    assert start == (namespace, name)

            elif type == "Comment":
                data = token["data"]
                assert isinstance(data, str)

            elif type in ("Characters", "SpaceCharacters"):
                data = token["data"]
                assert isinstance(data, str)
                assert data != ""
                if type == "SpaceCharacters":
                    assert data.strip(spaceCharacters) == ""

            elif type == "Doctype":
                name = token["name"]
                assert name is None or isinstance(name, str)
                assert token["publicId"] is None or isinstance(name, str)
                assert token["systemId"] is None or isinstance(name, str)

            elif type == "Entity":
                assert isinstance(token["name"], str)

            elif type == "SerializerError":
                assert isinstance(token["data"], str)

            else:
                assert False, "Unknown token type: {type}".format(type=type)

            yield token
