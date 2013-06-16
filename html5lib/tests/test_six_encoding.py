
from html5lib import html5parser, treewalkers, serializer
from nose.tools import eq_

def test_treewalker6():
    """Str/Unicode mix. If str attrs added to tree"""
    
    text = '<a href="http://example.com">Example</a>'
    end_text = '<a href="http://example.com" class="test123">Example</a>'
    parser = html5parser.HTMLParser()
    walker = treewalkers.getTreeWalker('etree')
    serializr = serializer.HTMLSerializer(quote_attr_values=True)
    domtree = parser.parseFragment(text)

    # at this point domtree should be a DOCUMENT_FRAGMENT
    domtree[0].set('class', 'test123')
    eq_(end_text, serializr.render(walker(domtree)))
