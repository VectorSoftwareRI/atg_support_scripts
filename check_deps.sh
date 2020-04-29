#!/bin/bash

C_RED="\e[1;31m"
C_GREEN="\e[1;32m"
C_ZERO="\e[0m"

M_OK="${C_GREEN}ok${C_ZERO}"
M_FAILED="${C_RED}failed${C_ZERO}"

VC_VER=20

failed=0

MANAGE_PROJ_PATH="$1"

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

echo -n "Checking Python3... "
PYTHON_VER=$(python3 --version 2>&1)
python3_test=$?
if [[ $python3_test -ne 0 ]];then
    echo -e "$M_FAILED"
    failed=1
else
    echo -e "$M_OK, $PYTHON_VER"
fi

echo -n "Checking git... "
GIT_VER=$(git --version 2>&1)
git_test=$?
if [[ $git_test -ne 0 ]];then
    echo -e "$M_FAILED"
    failed=1
else
    echo -e "$M_OK, $GIT_VER"
fi


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
    fi

    cd $comebackpath

}

if [[ ! -z "$MANAGE_PROJ_PATH" ]];then
    check_manage $MANAGE_PROJ_PATH
fi

if [[ $failed -eq 1 ]];then
    RES="$M_FAILED"
else
    RES="$M_OK"
fi
echo 
echo -e "RESULT: $RES"
echo

# EOF
