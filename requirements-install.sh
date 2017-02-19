#!/bin/bash -ex

pip install pip==6.1.0

if [[ $DEP_VERSION == "min" ]]; then
  sed -i'' -e 's/>=/==/g' requirements*.txt
fi

pip install -U -r requirements-test.txt

if [[ $USE_OPTIONAL == "true" ]]; then
  pip install -U -r requirements-optional.txt
fi

if [[ $CI == "true" ]]; then
  pip install codecov
fi
