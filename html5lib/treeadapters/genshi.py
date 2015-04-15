from __future__ import absolute_import, division, unicode_literals

from genshi.core import QName, Attrs
from genshi.core import START, END, TEXT, COMMENT, DOCTYPE


def to_genshi(walker):
    text = None
    for token in walker:
        type = token["type"]
        if type in ("Characters", "SpaceCharacters"):
            if text is None:
                text = token["data"]
            else:
                text += token["data"]
        elif text is not None:
            yield TEXT, text, (None, -1, -1)
            text = None

        if type in ("StartTag", "EmptyTag"):
            if token["namespace"]:
                name = "{%s}%s" % (token["namespace"], token["name"])
            else:
                name = token["name"]
            attrs = Attrs([(QName("{%s}%s" % attr if attr[0] is not None else attr[1]), value)
                           for attr, value in token["data"].items()])
            yield (START, (QName(name), attrs), (None, -1, -1))
            if type == "EmptyTag":
                type = "EndTag"

        if type == "EndTag":
            if token["namespace"]:
                name = "{%s}%s" % (token["namespace"], token["name"])
            else:
                name = token["name"]

            yield END, QName(name), (None, -1, -1)

        elif type == "Comment":
            yield COMMENT, token["data"], (None, -1, -1)

        elif type == "Doctype":
            yield DOCTYPE, (token["name"], token["publicId"],
                            token["systemId"]), (None, -1, -1)

        else:
            pass  # FIXME: What to do?

    if text is not None:
        yield TEXT, text, (None, -1, -1)
