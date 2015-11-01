#!/bin/bash -e

if [[ $USE_OPTIONAL != "true" && $USE_OPTIONAL != "false" ]]; then
  echo "fatal: \$USE_OPTIONAL not set to true or false. Exiting."
  exit 1
fi

# Make sure we're running setuptools >= 18.5
pip install -U pip setuptools

pip install -U -r requirements-test.txt

if [[ $USE_OPTIONAL == "true" ]]; then
  pip install -U -r requirements-optional.txt
fi
