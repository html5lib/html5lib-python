
from html5lib import html5parser, treewalkers, treebuilders, serializer


def test_treewalker_six_mix():
    """Str/Unicode mix. If str attrs added to tree"""

    text = '<a href="http://example.com">Example</a>'
    end_texts = ('<a href="http://example.com" class="test123">Example</a>',
                 '<a class="test123" href="http://example.com">Example</a>')
    parser = html5parser.HTMLParser(tree=treebuilders.getTreeBuilder('dom'))
    walker = treewalkers.getTreeWalker('dom')
    serializr = serializer.HTMLSerializer(quote_attr_values=True)
    domtree = parser.parseFragment(text)

    # at this point domtree should be a DOCUMENT_FRAGMENT
    domtree[0].set('class', 'test123')
    out = serializr.render(walker(domtree))
    if not out in end_texts:
        raise AssertionError('%r not in %r' % (out, end_texts))
