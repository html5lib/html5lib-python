# Copyright (c) 2006-2013 James Graham and other contributors
#
# Permission is hereby granted, free of charge, to any person obtaining
# a copy of this software and associated documentation files (the
# "Software"), to deal in the Software without restriction, including
# without limitation the rights to use, copy, modify, merge, publish,
# distribute, sublicense, and/or sell copies of the Software, and to
# permit persons to whom the Software is furnished to do so, subject to
# the following conditions:
#
# The above copyright notice and this permission notice shall be
# included in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
# MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
# NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE
# LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION
# OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION
# WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

from distutils.core import setup
import os
import codecs

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

setup(name='html5lib',
      version='0.999-dev',
      url='https://github.com/html5lib/html5lib-python',
      license="MIT License",
      description='HTML parser based on the WHATWG HTML specifcation',
      long_description=long_description,
      classifiers=classifiers,
      maintainer='James Graham',
      maintainer_email='james@hoppipolla.co.uk',
      packages=packages,
      install_requires=[
          'six',
      ],
      )
