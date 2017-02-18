#!/bin/bash -ex

pip install pip==6.1.0

pip install -U -r requirements-test.txt

if [[ $USE_OPTIONAL == "true" ]]; then
  pip install -U -r requirements-optional.txt
fi

if [[ $SIX_VERSION ]]; then
  pip install six==$SIX_VERSION
fi

if [[ $CI == "true" ]]; then
  pip install -U codecov
fi
