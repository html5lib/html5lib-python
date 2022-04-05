#!/bin/bash -ex

# SPDX-FileCopyrightText: 2006-2021 html5lib contributors. See AUTHORS.rst
#
# SPDX-License-Identifier: MIT

if [[ $SIX_VERSION ]]; then
  pip install six==$SIX_VERSION
fi

pip install -r requirements-test.txt

if [[ $USE_OPTIONAL == "true" ]]; then
  pip install -r requirements-optional.txt
fi

if [[ $CI == "true" ]]; then
  pip install codecov
fi
