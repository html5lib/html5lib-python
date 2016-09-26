#!/bin/bash -e

if [[ $USE_OPTIONAL != "true" && $USE_OPTIONAL != "false" ]]; then
  echo "fatal: \$USE_OPTIONAL not set to true or false. Exiting."
  exit 1
fi

pip install -U -r requirements-test.txt

if [[ $USE_OPTIONAL == "true" ]]; then
  pip install -U -r requirements-optional.txt
fi

if [[ $SIX_VERSION != "false" ]]; then
  pip install six==$SIX_VERSION
fi

if [[ $CI == "true" ]]; then
  pip install -U codecov
fi
