Change Log
----------

1.0
~~~

Released on XXX, 2013

* Python 3.2+ supported in a single codebase using the ``six`` library.

* Removed support for Python 2.5 and older.

* Removed the deprecated Beautiful Soup 3 treebuilder.
  ``beautifulsoup4`` can use ``html5lib`` as a parser instead.

* Removed ``simpletree`` from the package. The default tree builder is
  now ``etree`` (using the ``xml.etree.ElementTree/cElementTree``
  implementation).

* Removed the ``XHTMLSerializer`` which never actually guaranteed its
  output was well-formed XML, and hence provided little of use.

* Optional heuristic character encoding detection now based on
  ``charade`` for Python 2.6 - 3.3 compatibility.

* Optional ``Genshi`` treewalker support fixed.

* Implementation of the `adoption agency algorithm
  <http://www.whatwg.org/specs/web-apps/current-work/#adoptionAgency>`_
  updated to `SVN <http://svn.whatwg.org/webapps/>`_ revision r7867.

* Removed the "seeding a form with initial values" algorithm
  implementation as it was removed from the spec.

* ``<main>`` tag supported.

* Many bugfixes, including:

  * #33: null in attribute value breaks XML AttValue;

  * #4: nested, indirect descendant, <button> causes infinite loop;

  * `Google Code 215
    <http://code.google.com/p/html5lib/issues/detail?id=215>`_: Properly
    detect seekable streams;

  * `Google Code 206
    <http://code.google.com/p/html5lib/issues/detail?id=206`_: add
    support for <video preload=...>, <audio preload=...>;

  * `Google Code 205
    <http://code.google.com/p/html5lib/issues/detail?id=205>`_: add
    support for <video poster=...>;

  * `Google Code 202
    <http://code.google.com/p/html5lib/issues/detail?id=202>`_: Unicode
    file breaks InputStream.

* Source code is now mostly PEP8 compliant.

* Test harness has been improved and now depends on ``nose``.


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
