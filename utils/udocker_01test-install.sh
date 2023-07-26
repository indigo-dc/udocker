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
TAR_IMAGE="centos7.tar"
TAR_CONT="centos7-cont.tar"
TAR_IMAGE_URL="https://download.ncg.ingrid.pt/webdav/udocker_test/${TAR_IMAGE}"
TAR_CONT_URL="https://download.ncg.ingrid.pt/webdav/udocker_test/${TAR_CONT}"
TAR_DIR=$HOME/.udocker_tar
DOCKER_IMG="ubuntu:22.04"
CONT="ubuntu"
export UDOCKER_DIR=$HOME/.udocker_tests
export UDOCKER_INSTALL=$HOME/.udocker_install

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
  if [ -d ${UDOCKER_DIR} ]
  then
    echo "ERROR test directory exists, remove first: ${UDOCKER_DIR}"
    exit 1
  fi
  if [ -d ${UDOCKER_INSTALL} ]
  then
    echo "ERROR install directory exists, remove first: ${UDOCKER_INSTALL}"
    exit 1
  fi
  if [ -d ${TAR_DIR} ]
  then
    echo "ERROR install directory exists, remove first: ${UDOCKER_INSTALL}"
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

is_file_not_empty() {
    [[ ! -f "${1}" || ! -s "${1}" ]] && return 1 || return 0
}

echo "==========================================================="
echo "* This script tests udocker CLI and options for           *"
echo "* install of modules, download modules, show modules, etc.*"
echo "==========================================================="

echo "Manually clean directories before the tests"
clean
echo "rm -rf ${UDOCKER_DIR} ${UDOCKER_INSTALL} ${TAR_DIR} > /dev/null 2>&1"
mkdir -p ${TAR_DIR} ${UDOCKER_INSTALL}/tar
wget https://download.ncg.ingrid.pt/webdav/udocker/engines/tarballs/crun-x86_64.tgz -P ${TAR_DIR}

STRING="T001: udocker showconf"
udocker showconf; return=$?
result

touch ${UDOCKER_INSTALL}/metadata.json
STRING="T002: udocker availmod --force"
udocker availmod --force && is_file_not_empty ${UDOCKER_INSTALL}/metadata.json; return=$?
result

STRING="T003: udocker availmod"
udocker availmod >/dev/null 2>&1 && is_file_not_empty ${UDOCKER_INSTALL}/metadata.json; return=$?
result

STRING="T004: udocker rmmeta"
udocker rmmeta && ! is_file_not_empty ${UDOCKER_INSTALL}/metadata.json; return=$?
result

STRING="T005: udocker downloadtar to default dir ${UDOCKER_INSTALL}/tar"
udocker downloadtar && ls ${UDOCKER_INSTALL}/tar/libfakechroot.tgz; return=$?
result

STRING="T006: udocker downloadtar --prefix=${TAR_DIR}"
udocker downloadtar --prefix=${TAR_DIR} && ls ${TAR_DIR}/libfakechroot.tgz; return=$?
result

STRING="T007: udocker downloadtar --from=${TAR_DIR} 1 (UID =1 is crun)"
udocker downloadtar --from=${TAR_DIR} 1 && ls ${TAR_DIR}/crun-x86_64.tgz; return=$?
result

STRING="T008: udocker verifytar"
udocker verifytar; return=$?
result

STRING="T009: udocker verifytar --prefix=${TAR_DIR}"
udocker verifytar --prefix=${TAR_DIR}; return=$?
result

STRING="T010: udocker rmtar (Remove all tarballs from default dir ${UDOCKER_INSTALL}/tar)"
udocker rmtar; return=$?
result

STRING="T011: udocker rmtar --prefix=${TAR_DIR} 1 (Remove crun from ${TAR_DIR})"
udocker rmtar --prefix=${TAR_DIR} 1; return=$?
result

STRING="T012: udocker install"
udocker install && ls ${UDOCKER_INSTALL}/bin/patchelf-x86_64 && \
  ls ${UDOCKER_INSTALL}/lib/libfakechroot-x86_64.so && \
  ls ${UDOCKER_INSTALL}/doc/LICENSE.udocker; return=$?
result

STRING="T013: udocker install 1 (Install crun)"
udocker install 1 && ls ${UDOCKER_INSTALL}/bin/crun-x86_64; return=$?
result
date_ini=`stat --printf='%Z\n' ${UDOCKER_INSTALL}/bin/crun-x86_64`
echo $date_ini
sleep 1

STRING="T014: udocker install --force 1"
udocker install --force 1 && \
  date_last=`stat --printf='%Z\n' ${UDOCKER_INSTALL}/bin/crun-x86_64` && \
  echo $date_last && \
  [ $date_ini -ne $date_last ] ; return=$?
result

echo "==========================================================="
echo "* End of tests                                            *"
echo "==========================================================="

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
