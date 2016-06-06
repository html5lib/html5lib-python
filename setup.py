from __future__ import print_function

import ast
import codecs
import sys

from os.path import join, dirname
from setuptools import setup, find_packages, __version__ as setuptools_version
from pkg_resources import parse_version

if parse_version(setuptools_version) < parse_version("18.5"):
    print("html5lib requires setuptools version 18.5 or above; "
          "please upgrade before installing (you have %s)" % setuptools_version)
    sys.exit(1)

classifiers = [
    'Development Status :: 5 - Production/Stable',
    'Intended Audience :: Developers',
    'License :: OSI Approved :: MIT License',
    'Operating System :: OS Independent',
    'Programming Language :: Python',
    'Programming Language :: Python :: 2',
    'Programming Language :: Python :: 2.6',
    'Programming Language :: Python :: 2.7',
    'Programming Language :: Python :: 3',
    'Programming Language :: Python :: 3.3',
    'Programming Language :: Python :: 3.4',
    'Programming Language :: Python :: 3.5',
    'Topic :: Software Development :: Libraries :: Python Modules',
    'Topic :: Text Processing :: Markup :: HTML'
]

here = dirname(__file__)
with codecs.open(join(here, 'README.rst'), 'r', 'utf8') as readme_file:
    with codecs.open(join(here, 'CHANGES.rst'), 'r', 'utf8') as changes_file:
        long_description = readme_file.read() + '\n' + changes_file.read()

version = None
with open(join(here, "html5lib", "__init__.py"), "rb") as init_file:
    t = ast.parse(init_file.read(), filename="__init__.py", mode="exec")
    assert isinstance(t, ast.Module)
    assignments = filter(lambda x: isinstance(x, ast.Assign), t.body)
    for a in assignments:
        if (len(a.targets) == 1 and
                isinstance(a.targets[0], ast.Name) and
                a.targets[0].id == "__version__" and
                isinstance(a.value, ast.Str)):
            version = a.value.s

setup(name='html5lib',
      version=version,
      url='https://github.com/html5lib/html5lib-python',
      license="MIT License",
      description='HTML parser based on the WHATWG HTML specification',
      long_description=long_description,
      classifiers=classifiers,
      maintainer='James Graham',
      maintainer_email='james@hoppipolla.co.uk',
      packages=find_packages(exclude=["*.tests", "*.tests.*", "tests.*", "tests"]),
      install_requires=[
          'six',
          'webencodings',
          'setuptools>=18.5'
      ],
      extras_require={
          # A empty extra that only has a conditional marker will be
          # unconditonally installed when the condition matches.
          ":python_version == '2.6'": ["ordereddict"],

          # A conditional extra will only install these items when the extra is
          # requested and the condition matches.
          "datrie:platform_python_implementation == 'CPython'": ["datrie"],
          "lxml:platform_python_implementation == 'CPython'": ["lxml"],

          # Standard extras, will be installed when the extra is requested.
          "genshi": ["genshi"],
          "chardet": ["chardet>=2.2"],

          # The all extra combines a standard extra which will be used anytime
          # the all extra is requested, and it extends it with a conditional
          # extra that will be installed whenever the condition matches and the
          # all extra is requested.
          "all": ["genshi", "chardet>=2.2"],
          "all:platform_python_implementation == 'CPython'": ["datrie", "lxml"],
      },
      )
