try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup
import os

long_description="""HTML parser designed to follow the WHATWG HTML5 
specification. The parser is designed to handle all flavours of HTML and 
parses invalid documents using well-defined error handling rules compatible
with the behaviour of major desktop web browsers.

Output is to a tree structure; the current release supports output to
DOM, ElementTree, lxml and BeautifulSoup tree formats as well as a
simple custom format"""

classifiers=[
    'Development Status :: 4 - Beta',
    'Intended Audience :: Developers',
    'License :: OSI Approved :: MIT License',
    'Operating System :: OS Independent',
    'Programming Language :: Python',
    'Topic :: Software Development :: Libraries :: Python Modules',
    'Topic :: Text Processing :: Markup :: HTML'
    ]

setup(name='html5lib',
      version='1.0',
      url='http://code.google.com/p/html5lib/',
      license="MIT License",
      description='HTML parser based on the WHAT-WG Web Applications 1.0' 
                  '("HTML5") specifcation',
      long_description=long_description,
      classifiers=classifiers,
      maintainer='James Graham',
      maintainer_email='jg307@cam.ac.uk',
      packages=['html5lib'] + ['html5lib.'+name
          for name in os.listdir(os.path.join('src','html5lib'))
          if os.path.isdir(os.path.join('src','html5lib',name)) and
              not name.startswith('.')],
      package_dir = {'html5lib': 'src/html5lib'},
      test_suite = "tests.buildTestSuite",
      tests_require = ['simplejson']
      )
