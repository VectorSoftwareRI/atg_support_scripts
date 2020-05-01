#!/usr/bin/env bash

PYTHON_INTERPRETER=python3
SCRIPT_PATH=$(realpath $0)
SERVER_WORKSPACE=$(dirname $SCRIPT_PATH)
cd $SERVER_WORKSPACE

VENV_DIR="$SERVER_WORKSPACE/venv"

if [[ -e "$VENV_DIR" ]];then
    echo "venv already exists, aborting"
    exit 1
fi

${PYTHON_INTERPRETER} -m venv $VENV_DIR
source $VENV_DIR/bin/activate
curl https://bootstrap.pypa.io/get-pip.py | $PYTHON_INTERPRETER
pip install -r $SERVER_WORKSPACE/requirements.txt

#EOF
