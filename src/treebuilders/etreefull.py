try:
    from xml.etree import ElementTree
except ImportError:
    try:
        from elementtree import ElementTree
    except:
        pass

import _base
from _etreebase import *