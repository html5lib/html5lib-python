Change Log
----------

1.0b1
~~~~~

Released on May 17, 2013

* Implementation updated to implement the `HTML specification
  <http://www.whatwg.org/specs/web-apps/current-work/>`_ as of 5th May
  2013 (`SVN <http://svn.whatwg.org/webapps/>`_ revision r7867).

* Python 3.2+ supported in a single codebase using the ``six`` library.

* Removed support for Python 2.5 and older.

* Removed the deprecated Beautiful Soup 3 treebuilder.
  ``beautifulsoup4`` can use ``html5lib`` as a parser instead. Note that
  since it doesn't support namespaces, foreign content like SVG and
  MathML is parsed incorrectly.

* Removed ``simpletree`` from the package. The default tree builder is
  now ``etree`` (using the ``xml.etree.cElementTree`` implementation if
  available, and ``xml.etree.ElementTree`` otherwise).

* Removed the ``XHTMLSerializer`` as it never actually guaranteed its
  output was well-formed XML, and hence provided little of use.

* Removed default DOM treebuilder, so ``html5lib.treebuilders.dom`` is no
  longer supported. ``html5lib.treebuilders.getTreeBuilder("dom")`` will
  return the default DOM treebuilder, which uses ``xml.dom.minidom``.

* Optional heuristic character encoding detection now based on
  ``charade`` for Python 2.6 - 3.3 compatibility.

* Optional ``Genshi`` treewalker support fixed.

* Many bugfixes, including:

  * #33: null in attribute value breaks XML AttValue;

  * #4: nested, indirect descendant, <button> causes infinite loop;

  * `Google Code 215
    <http://code.google.com/p/html5lib/issues/detail?id=215>`_: Properly
    detect seekable streams;

  * `Google Code 206
    <http://code.google.com/p/html5lib/issues/detail?id=206>`_: add
    support for <video preload=...>, <audio preload=...>;

  * `Google Code 205
    <http://code.google.com/p/html5lib/issues/detail?id=205>`_: add
    support for <video poster=...>;

  * `Google Code 202
    <http://code.google.com/p/html5lib/issues/detail?id=202>`_: Unicode
    file breaks InputStream.

* Source code is now mostly PEP 8 compliant.

* Test harness has been improved and now depends on ``nose``.

* Documentation updated and moved to http://html5lib.readthedocs.org/.


0.95
~~~~

Released on February 11, 2012


0.90
~~~~

Released on January 17, 2010


0.11.1
~~~~~~

Released on June 12, 2008


0.11
~~~~

Released on June 10, 2008


0.10
~~~~

Released on October 7, 2007


0.9
~~~

Released on March 11, 2007


0.2
~~~

Released on January 8, 2007
