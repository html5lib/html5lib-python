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

from . import support  # flake8: noqa

import html5lib
from html5lib.treeadapters import sax
from html5lib.treewalkers import getTreeWalker


def test_to_sax():
    handler = support.TracingSaxHandler()
    tree = html5lib.parse("""<html xml:lang="en">
        <title>Directory Listing</title>
        <a href="/"><b/></p>
    """, treebuilder="etree")
    walker = getTreeWalker("etree")
    sax.to_sax(walker(tree), handler)
    expected = [
        'startDocument',
        ('startElementNS', ('http://www.w3.org/1999/xhtml', 'html'),
            'html', {(None, 'xml:lang'): 'en'}),
        ('startElementNS', ('http://www.w3.org/1999/xhtml', 'head'), 'head', {}),
        ('startElementNS', ('http://www.w3.org/1999/xhtml', 'title'), 'title', {}),
        ('characters', 'Directory Listing'),
        ('endElementNS', ('http://www.w3.org/1999/xhtml', 'title'), 'title'),
        ('characters', '\n        '),
        ('endElementNS', ('http://www.w3.org/1999/xhtml', 'head'), 'head'),
        ('startElementNS',  ('http://www.w3.org/1999/xhtml', 'body'), 'body', {}),
        ('startElementNS', ('http://www.w3.org/1999/xhtml', 'a'), 'a', {(None, 'href'): '/'}),
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
