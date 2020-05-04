#!/usr/bin/env bash

# The MIT License
#
# Copyright (c) 2020 Vector Informatik, GmbH. http://vector.com
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.

set -eu

PYTHON_INTERPRETER=python3
SCRIPT_PATH=$(realpath $0)
SERVER_WORKSPACE=$(dirname $SCRIPT_PATH)
VENV_DIR="$SERVER_WORKSPACE/venv"

if [[ -e "$VENV_DIR" ]];then
  echo "venv already exists!"
  
  # Unhappy path
  status=1
else
  echo "Setting up new venv ..."
  
  # Create new venv
  ${PYTHON_INTERPRETER} -m venv $VENV_DIR --without-pip
  
  # Activate it
  source $VENV_DIR/bin/activate
  
  # Install pip
  curl https://bootstrap.pypa.io/get-pip.py 2>/dev/null | $PYTHON_INTERPRETER
  
  # Update pip
  pip3 install -U pip
  
  # Install the required packages
  pip3 install -r $SERVER_WORKSPACE/requirements.txt
  
  echo "venv successfully created!"
  
  # Happy path
  status=0
fi

# Tell the user what to do
echo -e "\nPlease run: "
echo "    source $SERVER_WORKSPACE/venv/bin/activate"

# Exit with our status
exit ${status}

# EOF
