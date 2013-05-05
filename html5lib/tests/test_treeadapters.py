from __future__ import absolute_import, division, unicode_literals

from . import support  # flake8: noqa
from html5lib import html5parser
from html5lib.treebuilders import dom


def test_dom2sax():
    handler = support.TracingSaxHandler()
    parser = html5parser.HTMLParser(tree=dom.TreeBuilder)
    dom_object = parser.parse("""<html xml:lang="en">
        <title>Directory Listing</title>
        <a href="/"><b/></p>
    """)
    dom.dom2sax(dom_object, handler)
    expected = [
        'startDocument',
        ('startElementNS', ('http://www.w3.org/1999/xhtml', 'html'),
            'html', {('http://www.w3.org/XML/1998/namespace', 'lang'): 'en'}),
        ('startElementNS', ('http://www.w3.org/1999/xhtml', 'head'), 'head', {}),
        ('startElementNS', ('http://www.w3.org/1999/xhtml', 'title'), 'title', {}),
        ('characters', 'Directory Listing'),
        ('endElementNS', ('http://www.w3.org/1999/xhtml', 'title'), 'title'),
        ('characters', '\n        '),
        ('endElementNS', ('http://www.w3.org/1999/xhtml', 'head'), 'head'),
        ('startElementNS',  ('http://www.w3.org/1999/xhtml', 'body'), 'body', {}),
        ('startElementNS', ('http://www.w3.org/1999/xhtml', 'a'), 'a', {(None,'href'): '/'}),
        ('startElementNS', ('http://www.w3.org/1999/xhtml', 'b'), 'b', {}),
        ('startElementNS', ('http://www.w3.org/1999/xhtml', 'p'), 'p', {}),
        ('endElementNS', ('http://www.w3.org/1999/xhtml', 'p'), 'p'),
        ('characters', '\n    '),
        ('endElementNS', ('http://www.w3.org/1999/xhtml', 'b'), 'b'),
        ('endElementNS', ('http://www.w3.org/1999/xhtml', 'a'), 'a'),
        ('endElementNS', ('http://www.w3.org/1999/xhtml', 'body'), 'body'),
        ('endElementNS', ('http://www.w3.org/1999/xhtml', 'html'), 'html'),
        'endDocument',
    ]
    assert expected == handler.visited
