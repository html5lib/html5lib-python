#!/bin/bash -ex

if [[ $PIP_VERSION ]]; then
  pip install "pip==$PIP_VERSION"
else
  pip install -U pip setuptools wheel
fi

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
