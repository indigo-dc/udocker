#!/bin/bash

# ##################################################################
#
# udocker high level testing
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
# ##################################################################

# Codes
RED='\033[1;31m'
GREEN='\033[1;32m'
BLUE='\033[1;34m'
PURPLE='\033[1;36m'
NC='\033[0m'
ASSERT_STR="${BLUE}Assert:${NC}"
RUNNING_STR="${BLUE}Running:${NC}"
OK_STR="${GREEN}[OK]${NC}"
FAIL_STR="${RED}[FAIL]${NC}"
THIS_SCRIPT_NAME=$( basename "$0" )

# Variables for the tests
declare -a FAILED_TESTS
DEFAULT_UDIR=$HOME/.udocker-tests
TEST_UDIR=$HOME/.udocker-test-h45y7k9X
TAR_IMAGE="centos7.tar"
TAR_CONT="centos7-cont.tar"
TAR_IMAGE_URL="https://download.ncg.ingrid.pt/webdav/udocker_test/${TAR_IMAGE}"
TAR_CONT_URL="https://download.ncg.ingrid.pt/webdav/udocker_test/${TAR_CONT}"
DOCKER_IMG="ubuntu:22.04"
CONT="ubuntu"
export UDOCKER_DIR=${DEFAULT_UDIR}

if [ -n "$1" ]
then
  UDOCKER_CMD="$1"
else
  UDOCKER_CMD=$(type -p udocker)
fi

if [ ! -x "$UDOCKER_CMD" ]
then
  echo "ERROR udocker file not executable: $UDOCKER_CMD"
  exit 1
fi

if [ -n "$2" ]
then
  PYTHON_CMD="$2"
fi

if [ -n "$PYTHON_CMD" -a ! -x "$PYTHON_CMD" ]
then
  echo "ERROR python interpreter not executable: $PYTHON_CMD"
  exit 1
fi

function print_ok
{
  printf "${OK_STR}"
}

function print_fail
{
  printf "${FAIL_STR}"
}

function clean
{
  if [ -d ${DEFAULT_UDIR} ]
  then
    echo "ERROR test directory exists, remove first: ${DEFAULT_UDIR}"
    exit 1
  fi
}

function result
{
  echo " "
  if [ $return == 0 ]; then
      print_ok; echo "    $STRING"
  else
      print_fail; echo "    $STRING"
      FAILED_TESTS+=("$STRING")
  fi
  echo "\____________________________________________________________________________________________________________________________________/"
  echo ""
  echo " ____________________________________________________________________________________________________________________________________ "
  echo "/                                                                                                                                    \ "
}

function result_inv
{
  echo " "
  if [ $return == 1 ]; then
      print_ok; echo "    $STRING"
  else
      print_fail; echo "    $STRING"
      FAILED_TESTS+=("$STRING")
  fi
  echo "\____________________________________________________________________________________________________________________________________/"
  echo ""
  echo " ____________________________________________________________________________________________________________________________________ "
  echo "/                                                                                                                                    \ "
}

function udocker
{
  $PYTHON_CMD $UDOCKER_CMD $*
}

echo "==========================================================="
echo "* This script tests udocker CLI and options for           *"
echo "* install of modules, download modules, show modules, etc.*"
echo "* except the run command and vol. mount options           *"
echo "==========================================================="

STRING="T001: udocker install"
clean
udocker install && ls ${DEFAULT_UDIR}/bin/proot-x86_64; return=$?
result

STRING="T002: udocker install --force"
udocker install --force && \
    ls ${DEFAULT_UDIR}/bin/proot-x86_64 >/dev/null 2>&1; return=$?
result


# Cleanup files containers and images used in the tests
echo "Clean up files containers and images used in the tests"
rm -rf myexportcont.tar "${TEST_UDIR}" "${TAR_IMAGE}" "${TAR_CONT}" > /dev/null 2>&1
udocker rm mycont
udocker rmi mycentos1
echo "\____________________________________________________________________________________________________________________________________/"

# Report failed tests
if [ "${#FAILED_TESTS[*]}" -le 0 ]
then
    printf "${OK_STR}    All tests passed\n"
    exit 0
fi

printf "${FAIL_STR}    The following tests have failed:\n"
for (( i=0; i<${#FAILED_TESTS[@]}; i++ ))
do
    printf "${FAIL_STR}    ${FAILED_TESTS[$i]}\n"
done
exit 1
