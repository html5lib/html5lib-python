import os
import sys
import itertools
import copy

#RELEASE remove
# XXX Allow us to import the sibling module
os.chdir(os.path.split(os.path.abspath(__file__))[0])
sys.path.insert(0, os.path.abspath(os.path.join(os.pardir, "src")))

import html5parser
from treebuilders import simpletree
#END RELEASE

#RELEASE add
#import html5lib
#from html5lib import html5parser
#from html5lib.treebuilders import simpletree
#END RELEASE

class HTMLSanitizer(object):

    default_acceptable_elements = ('a', 'abbr', 'acronym', 'address', 'area',
      'b', 'big', 'blockquote', 'br', 'button', 'caption', 'center', 'cite',
      'code', 'col', 'colgroup', 'dd', 'del', 'dfn', 'dir', 'div', 'dl', 'dt',
      'em', 'fieldset', 'font', 'form', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
      'hr', 'i', 'img', 'input', 'ins', 'kbd', 'label', 'legend', 'li', 'map',
      'menu', 'ol', 'optgroup', 'option', 'p', 'pre', 'q', 's', 'samp',
      'select', 'small', 'span', 'strike', 'strong', 'sub', 'sup', 'table',
      'tbody', 'td', 'textarea', 'tfoot', 'th', 'thead', 'tr', 'tt', 'u',
      'ul', 'var')

    default_acceptable_attributes = ('abbr', 'accept', 'accept-charset',
      'accesskey', 'action', 'align', 'alt', 'axis', 'border', 'cellpadding',
      'cellspacing', 'char', 'charoff', 'charset', 'checked', 'cite', 'class',
      'clear', 'cols', 'colspan', 'color', 'compact', 'coords', 'datetime',
      'dir', 'disabled', 'enctype', 'for', 'frame', 'headers', 'height',
      'href', 'hreflang', 'hspace', 'id', 'ismap', 'label', 'lang',
      'longdesc', 'maxlength', 'media', 'method', 'multiple', 'name',
      'nohref', 'noshade', 'nowrap', 'prompt', 'readonly', 'rel', 'rev',
      'rows', 'rowspan', 'rules', 'scope', 'selected', 'shape', 'size',
      'span', 'src', 'start', 'summary', 'tabindex', 'target', 'title',
      'type', 'usemap', 'valign', 'value', 'vspace', 'width', 'xml:lang')

    def __init__(self, acceptable_elements=None, acceptable_attributes=None):
        self.parser = html5parser.HTMLParser()
        if acceptable_elements is None:
            self.acceptable_elements = self.default_acceptable_elements
        else:
            self.acceptable_elements = acceptable_elements
        
        if acceptable_attributes is None:
            self.acceptable_attributes = self.default_acceptable_attributes
        else:
            self.acceptable_attributes = acceptable_attributes
    
    def _sanitizeTree(self, tree):
        tree_copy = copy.copy(tree)
        #Set up a correspondence between the nodes in the original tree and the
        #ones in the new tree
        for originalNode, copyNode in itertools.izip(tree, tree_copy):
            copyNode._orig = originalNode
        #Iterate over a copy of the tree
        for nodeCopy in tree_copy:
            node = nodeCopy._orig
            print node.name, node.name in self.acceptable_elements
            #XXX Need to nead with non-nodes
            if (isinstance(node, simpletree.TextNode) or
                isinstance(node, simpletree.DocumentFragment)):
                continue
            #XXX Need to remove the dependence on parent 
            elif (node.name not in self.acceptable_elements):
                for child in node.childNodes:
                    node.parent.insertBefore(child, node)
                    node.parent.removeChild(node)    

            for attrib in node.attributes.keys()[:]:
                if attrib not in self.acceptable_attributes:
                    del node.attributes[attrib]
        
        return tree
    
    def sanitize(self, fragment):
        tree = self.parser.parseFragment(fragment)
        tree = self._sanitizeTree(tree)
        return tree.toxml()
