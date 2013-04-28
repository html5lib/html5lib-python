html5lib
========

html5lib is a pure-python library for parsing HTML. It is designed to
conform to the HTML specification, as is implemented by all major web
browsers.


Requirements
------------

Python 2.6 and above as well as Python 3.0 and above are
supported. Implementations known to work are CPython (as the reference
implementation) and PyPy. Jython is known *not* to work due to various
bugs in its implementation of the language. Others such as IronPython
may or may not work; if you wish to try, you are strongly encouraged
to run the testsuite and report back!

The only required library dependency is ``six``, this can be found
packaged in PyPi.

Optionally:

- ``datrie`` can be used to improve parsing performance (though in
  almost all cases the improvement is marginal);

- ``lxml`` is supported as a tree format (for both building and
  walking) under CPython (but *not* PyPy where it is known to cause
  segfaults);

- ``genshi`` has a treewalker (but not builder); and

- ``chardet`` can be used as a fallback when character encoding cannot
  be determined (note currently this is only packaged on PyPi for
  Python 2, though several package managers include unofficial ports
  to Python 3).


Installation
------------

html5lib is packaged with distutils. To install it use::

  $ python setup.py install


Usage
-----

Simple usage follows this pattern::

  import html5lib
  with open("mydocument.html", "r") as fp:
      document = html5lib.parse(f)

or::

  import html5lib
  document = html5lib.parse("<p>Hello World!")

More documentation is available in the docstrings.


Bugs
----

Please report any bugs on the `issue tracker
<https://github.com/html5lib/html5lib-python/issues>`_.


Tests
-----

These are contained in the html5lib-tests repository and included as a
submodule, thus for git checkouts they must be initialized (for
release tarballs this is unneeded)::

  $ git submodule init
  $ git submodule update

And then they can be run, with ``nose`` installed, using the
``nosetests`` command in the root directory. All should pass.


Contributing
------------

Pull requests are more than welcome — both to the library and to the
documentation. Some useful information:

- We aim to follow PEP 8 in the library, but ignoring the
  79-character-per-line limit, instead following a soft limit of 99,
  but allowing lines over this where it is the readable thing to do.

- We keep pyflakes reporting no errors or warnings at all times.

- We keep the master branch passing all tests at all times on all
  supported versions.

Travis CI is run against all pull requests and should enforce all of
the above.

We also use an external code-review tool, which uses your GitHub login
to authenticate. You'll get emails for changes on the review.


Questions?
----------

There's a mailing list available for support on Google Groups,
`html5lib-discuss <http://groups.google.com/group/html5lib-discuss>`_,
though you may have more success (and get a far quicker response)
asking on IRC in #whatwg on irc.freenode.net.
