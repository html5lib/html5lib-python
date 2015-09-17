Change Log
----------

0.99999999/1.0b9
~~~~~~~~~~~~~~~~

Released on XXX

* Minor fix on error reporting message.


0.9999999/1.0b8
~~~~~~~~~~~~~~~

Released on September 10, 2015

* Fix #195: fix the sanitizer to drop broken URLs (it threw an
  exception between 0.9999 and 0.999999).


0.999999/1.0b7
~~~~~~~~~~~~~~

Released on July 7, 2015

* Fix #189: fix the sanitizer to allow relative URLs again (as it did
  prior to 0.9999/1.0b5).


0.99999/1.0b6
~~~~~~~~~~~~~

Released on April 30, 2015

* Fix #188: fix the sanitizer to not throw an exception when sanitizing
  bogus data URLs.


0.9999/1.0b5
~~~~~~~~~~~~

Released on April 29, 2015

* Fix #153: Sanitizer fails to treat some attributes as URLs. Despite how
  this sounds, this has no known security implications.  No known version
  of IE (5.5 to current), Firefox (3 to current), Safari (6 to current),
  Chrome (1 to current), or Opera (12 to current) will run any script
  provided in these attributes.

* Pass error message to the ParseError exception in strict parsing mode.

* Allow data URIs in the sanitizer, with a whitelist of content-types.

* Add support for Python implementations that don't support lone
  surrogates (read: Jython). Fixes #2.

* Remove localization of error messages. This functionality was totally
  unused (and untested that everything was localizable), so we may as
  well follow numerous browsers in not supporting translating technical
  strings.

* Expose treewalkers.pprint as a public API.

* Add a documentEncoding property to HTML5Parser, fix #121.


0.999
~~~~~

Released on December 23, 2013

* Fix #127: add work-around for CPython issue #20007: .read(0) on
  http.client.HTTPResponse drops the rest of the content.

* Fix #115: lxml treewalker can now deal with fragments containing, at
  their root level, text nodes with non-ASCII characters on Python 2.


0.99
~~~~

Released on September 10, 2013

* No library changes from 1.0b3; released as 0.99 as pip has changed
  behaviour from 1.4 to avoid installing pre-release versions per
  PEP 440.


1.0b3
~~~~~

Released on July 24, 2013

* Removed ``RecursiveTreeWalker`` from ``treewalkers._base``. Any
  implementation using it should be moved to
  ``NonRecursiveTreeWalker``, as everything bundled with html5lib has
  for years.

* Fix #67 so that ``BufferedStream`` to correctly returns a bytes
  object, thereby fixing any case where html5lib is passed a
  non-seekable RawIOBase-like object.


1.0b2
~~~~~

Released on June 27, 2013

* Removed reordering of attributes within the serializer. There is now
  an ``alphabetical_attributes`` option which preserves the previous
  behaviour through a new filter. This allows attribute order to be
  preserved through html5lib if the tree builder preserves order.

* Removed ``dom2sax`` from DOM treebuilders. It has been replaced by
  ``treeadapters.sax.to_sax`` which is generic and supports any
  treewalker; it also resolves all known bugs with ``dom2sax``.

* Fix treewalker assertions on hitting bytes strings on
  Python 2. Previous to 1.0b1, treewalkers coped with mixed
  bytes/unicode data on Python 2; this reintroduces this prior
  behaviour on Python 2. Behaviour is unchanged on Python 3.


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
