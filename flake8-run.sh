#!/bin/bash -e

# SPDX-FileCopyrightText: 2006-2021 html5lib contributors. See AUTHORS.rst
#
# SPDX-License-Identifier: MIT

if [[ ! -x $(which flake8) ]]; then
  echo "fatal: flake8 not found on $PATH. Exiting."
  exit 1
fi

flake8 `dirname $0`
exit $?
