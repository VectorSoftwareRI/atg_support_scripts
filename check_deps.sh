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

bypass_vcm=0
final_result=0

function usage
{
  echo
  echo "Usage: $0 [options] <vcm file>"
  echo
  echo "Provide path to vcm file to run checks on Manage project"
  echo
  echo "Options:"
  echo
  echo " -b bypass the VCM file check"
  echo
}

while getopts "bh" opt; do
  case "$opt" in
    "h")
      usage
      exit
    ;;
    "b")
      bypass_vcm=1
    ;;
    *)
      usage
      exit 1
    ;;
  esac
done

shift $((OPTIND-1))

MANAGE_PROJ_PATH="$1"
if [[ $bypass_vcm -eq 0 ]];then
  if [[ -z "$MANAGE_PROJ_PATH" ]];then
    usage
    exit 1
  fi
else
  MANAGE_PROJ_PATH=""
fi

##
## VectorCAST checks
##
echo -n "Checking VECTORCAST_DIR env variable... "
if [[ -z "$VECTORCAST_DIR" ]];then
  echo -e "$M_FAILED"
  final_result=1
else
  echo -e "$M_OK"
fi

echo -n "Checking clicast... "
CLICAST_RES="$($VECTORCAST_DIR/clicast --version 2>&1)"
clicast_test=$?
if [[ $clicast_test -ne 0 ]];then
  echo -e "$M_FAILED"
  final_result=1
else
  echo -e "$M_OK"
fi

echo -n "Checking VectorCAST version >= $VC_VER... "
CLICAST_VER="$(echo $CLICAST_RES | cut -f2 -d' ')"
if [[ $CLICAST_VER -ge $VC_VER ]];then
  echo -e "$M_OK"
else
  echo -e "$M_FAILED"
  final_result=1
fi

##
## License checks
##
license=0
echo -n "Checking license env variables... "
if [[ -z "$LM_LICENSE_FILE$VECTOR_LICENSE_FILE" ]];then
  echo -e "$M_FAILED"
  final_result=1
else
  echo -e "$M_OK"
  license=1
fi

echo -n "Checking license... "
if [[ $license -eq 1 ]];then
  LIC_LMSTAT_RES="$($VECTORCAST_DIR/flexlm/lmutil lmstat -a 2>&1)"
  LIC_MANAGE_RES="$(echo $LIC_LMSTAT_RES | grep VCAST_MANAGE)"
  LIC_ATG_RES="$(echo $LIC_LMSTAT_RES | grep VCAST_ATG)"
  lic_failed=0
  if [[ "$LIC_MANAGE_RES" != "" ]];then
    echo -n "Manage "
  else
    echo -n "(missing Manage) "
    lic_failed=1
  fi
  if [[ "$LIC_ATG_RES" != "" ]];then
    echo -n "ATG "
  else
    echo -n "(missing ATG) "
    lic_failed=1
  fi
  if [[ $lic_failed -eq 1 ]];then
    echo -e "$M_FAILED"
    final_result=1
  else
    echo -e "$M_OK"
  fi
fi

##
## FS checks
##
echo -n "Checking filesystem... "
FINDMNT_CHECK="$(findmnt -n -T . -o FSTYPE 2>&1)"
findmnt_test=$?
if [[ $findmnt_test -eq 0 ]];then
  BADFS_CHECK=$(echo $FINDMNT_CHECK | egrep '(vmhgfs-fuse|cifs)')
  if [[ "$BADFS_CHECK" = "" ]];then
    echo -e "$M_OK, $FINDMNT_CHECK"
  else
    echo -e "$M_FAILED, unsupported: $FINDMNT_CHECK"
    final_result=1
  fi
else
  echo -e "$M_WARNING, findmnt not available"
  final_result=2
fi

##
## Python 3
##
echo -n "Checking Python3... "
PYTHON_VER="$(python3 --version 2>&1)"
python3_test=$?
if [[ $python3_test -ne 0 ]];then
  echo -e "$M_FAILED"
  final_result=1
else
  echo -e "$M_OK, $PYTHON_VER"
fi

##
## Python venv
##
echo -n "Checking Python venv... "
echo "import venv" | python3 >/dev/null 2>&1
venv_test=$?
if [[ $venv_test -ne 0 ]];then
  echo -e "$M_FAILED"
  final_result=1
else
  echo -e "$M_OK"
fi

##
## Git checks
##
echo -n "Checking git... "
GIT_VER="$(git --version 2>&1)"
git_test=$?
if [[ $git_test -ne 0 ]];then
  echo -e "$M_FAILED"
  final_result=1
else
  echo -e "$M_OK, $GIT_VER"
fi

##
## Compiler checks
##
echo -n "Checking gcc version... "
GCC_VERSION="$(gcc --version | head -1 |& cut -f 3 -d " ")"
if [[ "$GCC_VERSION" = "$GCC_EXPECTED_VERSION" ]];then
  echo -e "$M_OK, gcc version $GCC_VERSION"
else
  echo -e "$M_WARNING, expected $GCC_EXPECTED_VERSION (got $GCC_VERSION)"
  final_result=2
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
    final_result=1
    return
  fi
  
  if [[ ! -e "$MANAGE_PROJ_PATH" ]];then
    echo -e "$M_FAILED, $MANAGE_PROJ_PATH is not a valid (existing) path"
    final_result=1
    return
  fi
  
  if [[ "$(grep "project version" $MANAGE_PROJ_PATH)" != "" ]];then
    echo -e "$M_OK"
  else
    echo -e "$M_FAILED"
    final_result=1
  fi
  
  comebackpath="$(pwd)"
  
  cd "$(dirname $MANAGE_PROJ_PATH)"

  vcmfile="$(basename $MANAGE_PROJ_PATH)"
  
  echo -n "Checking if Manage project is under git control... "
  git ls-files --error-unmatch $vcmfile >/dev/null 2>&1
  git_status=$?
  if [[ $git_status -eq 0 ]];then
    echo -e "$M_OK"
  else
    echo -e "$M_FAILED"
    final_result=1
  fi
  
  cd $comebackpath
}

if [[ -n "$MANAGE_PROJ_PATH" ]];then
  check_manage $MANAGE_PROJ_PATH
fi

##
## Final result
##

if [[ $final_result -eq 0 ]];then
  RES="$M_OK"
  elif [[ $final_result -eq 1 ]];then
  RES="$M_FAILED"
else
  RES="$M_OK with $M_WARNING"
fi
echo
echo -e "RESULT: $RES"
echo

# EOF
