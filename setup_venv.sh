#!/usr/bin/env bash

PYTHON_INTERPRETER=python3
SCRIPT_PATH=$(realpath $0)
SERVER_WORKSPACE=$(dirname $SCRIPT_PATH)
VENV_DIR="$SERVER_WORKSPACE/venv"

if [[ -e "$VENV_DIR" ]];then
    echo "venv already exists... not creating"
    exit 1
fi

${PYTHON_INTERPRETER} -m venv $VENV_DIR
source $VENV_DIR/bin/activate
pip3 install -U pip
pip3 install -r $SERVER_WORKSPACE/requirements.txt

#EOF
