#!/bin/bash -e

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

if [[ $USE_OPTIONAL != "true" && $USE_OPTIONAL != "false" ]]; then
  echo "fatal: \$USE_OPTIONAL not set to true or false. Exiting."
  exit 1
fi

pip install -r requirements-test.txt --use-mirrors

if [[ $USE_OPTIONAL == "true" && $TRAVIS_PYTHON_VERSION != "pypy" ]]; then
  if [[ $TRAVIS_PYTHON_VERSION == "2.6" ]]; then
    pip install -r requirements-optional-2.6.txt --use-mirrors
  else
    pip install -r requirements-optional-cpython.txt --use-mirrors
  fi
fi

if [[ $FLAKE == "true" ]]; then
  pip install --use-mirrors flake8
fi
