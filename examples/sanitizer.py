import os
import sys
import itertools
import copy
import urlparse

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

    defaults = { 
    
    "acceptable_elements":('a', 'abbr', 'acronym', 'address', 'area',
      'b', 'big', 'blockquote', 'br', 'button', 'caption', 'center', 'cite',
      'code', 'col', 'colgroup', 'dd', 'del', 'dfn', 'dir', 'div', 'dl', 'dt',
      'em', 'fieldset', 'font', 'form', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
      'hr', 'i', 'img', 'input', 'ins', 'kbd', 'label', 'legend', 'li', 'map',
      'menu', 'ol', 'optgroup', 'option', 'p', 'pre', 'q', 's', 'samp',
      'select', 'small', 'span', 'strike', 'strong', 'sub', 'sup', 'table',
      'tbody', 'td', 'textarea', 'tfoot', 'th', 'thead', 'tr', 'tt', 'u',
      'ul', 'var'),

    "acceptable_attributes":('abbr', 'accept', 'accept-charset',
      'accesskey', 'action', 'align', 'alt', 'axis', 'border', 'cellpadding',
      'cellspacing', 'char', 'charoff', 'charset', 'checked', 'cite', 'class',
      'clear', 'cols', 'colspan', 'color', 'compact', 'coords', 'datetime',
      'dir', 'disabled', 'enctype', 'for', 'frame', 'headers', 'height',
      'href', 'hreflang', 'hspace', 'id', 'ismap', 'label', 'lang',
      'longdesc', 'maxlength', 'media', 'method', 'multiple', 'name',
      'nohref', 'noshade', 'nowrap', 'prompt', 'readonly', 'rel', 'rev',
      'rows', 'rowspan', 'rules', 'scope', 'selected', 'shape', 'size',
      'span', 'src', 'start', 'summary', 'tabindex', 'target', 'title',
      'type', 'usemap', 'valign', 'value', 'vspace', 'width', 'xml:lang'),
        
    "acceptable_schemes":('ed2k', 'ftp', 'http', 'https', 'irc',
      'mailto', 'news', 'gopher', 'nntp', 'telnet', 'webcal',
      'xmpp', 'callto', 'feed', 'urn', 'aim', 'rsync', 'tag',
      'ssh', 'sftp', 'rtsp', 'afs'),
    
    "attr_val_is_uri":('href', 'src', 'action', 'longdesc')
    }

    def __init__(self, **kwargs):
        """Class for filtering unsafe markup out of HTML.
        
        Extra keyword arguments:
        acceptable_elements - Elements that should be allowed through the filter
        acceptable_attributes - Attributes that should be allowed through the
                                filter
        acceptable_schemes - URI schemes that should be allowed
        attr_val_is_uri - Attributes with URI values"""
        
        self.parser = html5parser.HTMLParser()
        for property,value in self.defaults.iteritems():
            if property in kwargs:
                value = kwargs[property]
            setattr(self, property, value)
    
    
    def sanitize(self, fragment):
        """Remove unsafe markup from a fragment of HTML and return a string
        containing the sanitized markup.
        """
        
        tree = self.parser.parseFragment(fragment)
        tree = self._sanitizeTree(tree)
        return tree.toxml()
    
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
                elif (attrib in self.attr_val_is_uri and not
                      self.acceptableURI(node.attributes[attrib])):
                    del node.attributes[attrib]
        
        return tree
    
    def acceptableURI(self, uri):
        return urlparse.urlparse(uri)[0] in self.acceptable_schemes