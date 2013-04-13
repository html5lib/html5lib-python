from distutils.core import setup
import os

long_description="""HTML parser designed to follow the WHATWG HTML
specification. The parser is designed to handle all flavours of HTML and
parses invalid documents using well-defined error handling rules compatible
with the behaviour of major desktop web browsers.

Output is to a tree structure; the current release supports output to
DOM, ElementTree, and lxml tree formats as well as a
simple custom format"""

classifiers=[
    'Development Status :: 5 - Production/Stable',
    'Intended Audience :: Developers',
    'License :: OSI Approved :: MIT License',
    'Operating System :: OS Independent',
    'Programming Language :: Python',
    'Programming Language :: Python :: 2',
    'Programming Language :: Python :: 3',
    'Topic :: Software Development :: Libraries :: Python Modules',
    'Topic :: Text Processing :: Markup :: HTML'
    ]


packages = ['html5lib'] + ['html5lib.'+name
                           for name in os.listdir(os.path.join('html5lib'))
                           if os.path.isdir(os.path.join('html5lib', name)) and
                           not name.startswith('.') and name != 'tests']

setup(name='html5lib',
      version='1.0b1',
      url='https://github.com/html5lib/html5lib-python',
      license="MIT License",
      description='HTML parser based on the WHATWG HTML specifcation',
      long_description=long_description,
      classifiers=classifiers,
      maintainer='James Graham',
      maintainer_email='james@hoppipolla.co.uk',
      packages=packages
      )
