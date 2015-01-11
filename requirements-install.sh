#!/bin/bash -e

if [[ $USE_OPTIONAL != "true" && $USE_OPTIONAL != "false" ]]; then
  echo "fatal: \$USE_OPTIONAL not set to true or false. Exiting."
  exit 1
fi

pip install -r requirements-test.txt

if [[ $USE_OPTIONAL == "true" ]]; then
  if [[ $TRAVIS_PYTHON_VERSION == "pypy" || $TRAVIS_PYTHON_VERSION == "pypy3" ]]; then
    pip install -r requirements-optional.txt
  elif [[ $TRAVIS_PYTHON_VERSION == "2.6" ]]; then
    pip install -r requirements-optional-2.6.txt
  else
    pip install -r requirements-optional-cpython.txt
  fi
fi
