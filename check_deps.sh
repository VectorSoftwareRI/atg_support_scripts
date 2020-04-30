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

C_RED="\e[1;31m"
C_GREEN="\e[1;32m"
C_YELLOW="\e[1;33m"
C_ZERO="\e[0m"

M_OK="${C_GREEN}ok${C_ZERO}"
M_FAILED="${C_RED}failed${C_ZERO}"
M_WARNING="${C_YELLOW}warning${C_ZERO}"

VC_VER=20
GCC_EXPECTED_VERSION="8.3.1"
OPENSSL_HEADER="/usr/include/openssl/opensslconf-i386.h"

failed=0

function usage
{
        echo
        echo "Usage: $0 [options] [vcm file]"
        echo
		echo "Provide path to vcm file to run checks on Manage project"
        echo
}

while getopts "h" opt; do
        case "$opt" in
                "h")
                        usage
						exit
                        ;;
                *)
                        usage
						exit 1
                        ;;
        esac
done

shift $((OPTIND-1))

MANAGE_PROJ_PATH="$1"

##
## VectorCAST checks
##

echo -n "Checking VECTORCAST_DIR env variable... "
if [[ -z "$VECTORCAST_DIR" ]];then
    echo -e "$M_FAILED"
    failed=1
else
    echo -e "$M_OK"
fi

echo -n "Checking clicast... "
CLICAST_RES=$($VECTORCAST_DIR/clicast --version 2>&1)
clicast_test=$?
if [[ $clicast_test -ne 0 ]];then
    echo -e "$M_FAILED"
    failed=1
else
    echo -e "$M_OK"
fi

echo -n "Checking VectorCAST version >= $VC_VER... "
CLICAST_VER=$(echo $CLICAST_RES | cut -f2 -d' ')
if [[ $CLICAST_VER -ge $VC_VER ]];then
    echo -e "$M_OK"
else
    echo -e "$M_FAILED"
    failed=1
fi

##
## Python 3
##

echo -n "Checking Python3... "
PYTHON_VER=$(python3 --version 2>&1)
python3_test=$?
if [[ $python3_test -ne 0 ]];then
    echo -e "$M_FAILED"
    failed=1
else
    echo -e "$M_OK, $PYTHON_VER"
fi

##
## Python venv
##

echo -n "Checking Python venv... "
PYTHON_VENV=$(echo "import venv" | python3 >/dev/null 2>&1)
venv_test=$?
if [[ $venv_test -ne 0 ]];then
    echo -e "$M_FAILED"
    failed=1
else
    echo -e "$M_OK"
fi

##
## Git checks
##

echo -n "Checking git... "
GIT_VER=$(git --version 2>&1)
git_test=$?
if [[ $git_test -ne 0 ]];then
    echo -e "$M_FAILED"
    failed=1
else
    echo -e "$M_OK, $GIT_VER"
fi

##
## Linux distribution checks
##

lsb_release=0
echo -n "Checking for lsb_release... "
if [[ -x /usr/bin/lsb_release ]];then
    echo -e "$M_OK" 
    lsb_release=1
else
    echo -e "$M_WARNING, failed to check lsb_release"
fi

if [[ $lsb_release -eq 1 ]];then
    DISTRIB=$(/usr/bin/lsb_release -i | cut -f2)
    RELEASE_VER=$(/usr/bin/lsb_release -sr | cut -f1 -d.)

    echo -n "Checking Linux distribution... "
    if [[ "$DISTRIB" = "CentOS" ]];then
        echo -e "$M_OK"
    else
        echo -e "$M_WARNING, expected CentOS (got $DISTRIB)"
    fi

    echo -n "Checking CentOS version..."
    if [[ "$RELEASE_VER" = "8" ]];then
        echo -e "$M_OK"
    else
        echo -e "$M_WARNING, expected 8 (got $RELEASE_VER)"
    fi
fi

##
## Compiler checks
##
echo -n "Checking gcc version... "
GCC_VERSION=$(gcc --version | head -1 |& cut -f 3 -d " ")
if [[ "$GCC_VERSION" = "$GCC_EXPECTED_VERSION" ]];then
    echo -e "$M_OK"
else
    echo -e "$M_WARNING, expected $GCC_EXPECTED_VERSION (got $GCC_VERSION)"
fi

##
## OpenSSL checks
##
echo -n "Checking OpenSSL... "
if [[ -f "$OPENSSL_HEADER" ]];then
    echo -e "$M_OK"
else
    echo -e "$M_WARNING, missing $OPENSSL_HEADER"
fi

##
## Manage project checks
##

function check_manage
{
    MANAGE_PROJ_PATH="$1"

    ext="${MANAGE_PROJ_PATH##*.}"

    echo -n "Checking Manage project... "

    if [[ "$ext" != "vcm" ]];then
        echo -e "$M_FAILED, Invalid Manage project path"
        failed=1
        return
    fi

    if [[ -e "$MANAGE_PROJ_PATH" ]];then
        echo -e "$M_OK"
    else
        echo -e "$M_FAILED, $MANAGE_PROJ_PATH is not a valid (existing) path"
        failed=1
        return
    fi

    comebackpath="$(pwd)"

    cd $(dirname $MANAGE_PROJ_PATH)

    echo -n "Checking if Manage project is under git control... "
    git status >/dev/null 2>&1
    git_status=$?
    if [[ $git_status -eq 0 ]];then
        echo -e "$M_OK"  
    else
        echo -e "$M_FAILED"
        failed=1
    fi

    cd $comebackpath

}

if [[ ! -z "$MANAGE_PROJ_PATH" ]];then
    check_manage $MANAGE_PROJ_PATH
fi

##
## Final result
##

if [[ $failed -eq 1 ]];then
    RES="$M_FAILED"
else
    RES="$M_OK"
fi
echo 
echo -e "RESULT: $RES"
echo

# EOF
