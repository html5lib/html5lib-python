import ast
import os
import codecs

from setuptools import setup


classifiers=[
    'Development Status :: 5 - Production/Stable',
    'Intended Audience :: Developers',
    'License :: OSI Approved :: MIT License',
    'Operating System :: OS Independent',
    'Programming Language :: Python',
    'Programming Language :: Python :: 2',
    'Programming Language :: Python :: 2.6',
    'Programming Language :: Python :: 2.7',
    'Programming Language :: Python :: 3',
    'Programming Language :: Python :: 3.2',
    'Programming Language :: Python :: 3.3',
    'Programming Language :: Python :: 3.4',
    'Topic :: Software Development :: Libraries :: Python Modules',
    'Topic :: Text Processing :: Markup :: HTML'
    ]

packages = ['html5lib'] + ['html5lib.'+name
                           for name in os.listdir(os.path.join('html5lib'))
                           if os.path.isdir(os.path.join('html5lib', name)) and
                           not name.startswith('.') and name != 'tests']

current_dir = os.path.dirname(__file__)
with codecs.open(os.path.join(current_dir, 'README.rst'), 'r', 'utf8') as readme_file:
    with codecs.open(os.path.join(current_dir, 'CHANGES.rst'), 'r', 'utf8') as changes_file:
        long_description = readme_file.read() + '\n' + changes_file.read()

version = None
with open(os.path.join("html5lib", "__init__.py"), "rb") as init_file:
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
      packages=packages,
      install_requires=[
          'six',
      ],
      extras_require={
          # A empty extra that only has a conditional marker will be
          # unconditonally installed when the condition matches.
          ":python_version == '2.6'": ["ordereddict"],

          # A conditional extra will only install these items when the extra is
          # requested and the condition matches.
          "lxml:python_implementation == 'CPython'": ["lxml"],

          # Standard extras, will be installed when the extra is requested.
          "genshi": ["genshi"],
          "datrie": ["datrie"],
          "charade": ["charade"],

          # The all extra combines a standard extra which will be used anytime
          # the all extra is requested, and it extends it with a conditional
          # extra that will be installed whenever the condition matches and the
          # all extra is requested.
          "all": ["genshi", "datrie", "charade"],
          "all:python_implementation == 'CPython'": ["lxml"],
      },
      )
