#!/bin/bash -ex

pip install -r requirements-test.txt

if [[ $USE_OPTIONAL == "true" ]]; then
  pip install -r requirements-optional.txt
fi

if [[ $CI == "true" ]]; then
  pip install codecov
fi
