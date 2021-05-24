#!/usr/bin/env python3
#
# html5lib documentation build configuration file, created by
# sphinx-quickstart on Wed May  8 00:04:49 2013.
#
# This file is execfile()d with the current directory set to its containing dir.
#
# Note that not all possible configuration values are present in this
# autogenerated file.
#
# All configuration values have a default; values that are commented out
# serve to show the default.

import sys
import os

# -- General configuration -----------------------------------------------------

# Add any Sphinx extension module names here, as strings. They can be extensions
# coming with Sphinx (named 'sphinx.ext.*') or your custom ones.
extensions = ['sphinx.ext.autodoc', 'sphinx.ext.doctest', 'sphinx.ext.viewcode']

# Add any paths that contain templates here, relative to this directory.
templates_path = ['_templates']

# The suffix of source filenames.
source_suffix = '.rst'

# The master toctree document.
master_doc = 'index'

# General information about the project.
project = 'html5lib'
copyright = '2006 - 2013, James Graham, Sam Sneddon, and contributors'

# The version info for the project you're documenting, acts as replacement for
# |version| and |release|, also used in various other places throughout the
# built documents.
#
# The short X.Y version.
version = '1.0'
# The full version, including alpha/beta/rc tags.
sys.path.append(os.path.abspath('..'))
from html5lib import __version__  # noqa
release = __version__

# List of patterns, relative to source directory, that match files and
# directories to ignore when looking for source files.
exclude_patterns = ['_build', 'theme']

# The name of the Pygments (syntax highlighting) style to use.
pygments_style = 'sphinx'

# -- Options for HTML output ---------------------------------------------------

# The theme to use for HTML and HTML Help pages.  See the documentation for
# a list of builtin themes.
html_theme = 'default'

# Output file base name for HTML help builder.
htmlhelp_basename = 'html5libdoc'


# -- Options for LaTeX output --------------------------------------------------

# Grouping the document tree into LaTeX files. List of tuples
# (source start file, target name, title, author, documentclass [howto/manual]).
latex_documents = [
    ('index', 'html5lib.tex', 'html5lib Documentation',
     'James Graham, Sam Sneddon, and contributors', 'manual'),
]

# -- Options for manual page output --------------------------------------------

# One entry per manual page. List of tuples
# (source start file, name, description, authors, manual section).
man_pages = [
    ('index', 'html5lib', 'html5lib Documentation',
     ['James Graham, Sam Sneddon, and contributors'], 1)
]

# -- Options for Texinfo output ------------------------------------------------

# Grouping the document tree into Texinfo files. List of tuples
# (source start file, target name, title, author,
#  dir menu entry, description, category)
texinfo_documents = [
    ('index', 'html5lib', 'html5lib Documentation',
     'James Graham, Sam Sneddon, and contributors', 'html5lib', 'One line description of project.',
     'Miscellaneous'),
]


class CExtMock:
    """Required for autodoc on readthedocs.org where you cannot build C extensions."""
    def __init__(self, *args, **kwargs):
        pass

    def __call__(self, *args, **kwargs):
        return CExtMock()

    @classmethod
    def __getattr__(cls, name):
        if name in ('__file__', '__path__'):
            return '/dev/null'
        else:
            return CExtMock()


try:
    import lxml   # noqa
except ImportError:
    sys.modules['lxml'] = CExtMock()
    sys.modules['lxml.etree'] = CExtMock()
    print("warning: lxml modules mocked.")

try:
    import genshi  # noqa
except ImportError:
    sys.modules['genshi'] = CExtMock()
    sys.modules['genshi.core'] = CExtMock()
    print("warning: genshi modules mocked.")
