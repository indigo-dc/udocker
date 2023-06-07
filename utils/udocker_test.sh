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
  echo "|                                                                                                                                    |"
  echo ".____________________________________________________________________________________________________________________________________."
  echo ""
  echo ".____________________________________________________________________________________________________________________________________."
  echo "|                                                                                                                                    |"
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
  echo "|                                                                                                                                    |"
  echo ".____________________________________________________________________________________________________________________________________."
  echo ""
  echo ".____________________________________________________________________________________________________________________________________."
  echo "|                                                                                                                                    |"
}

function udocker
{
  $PYTHON_CMD $UDOCKER_CMD $*
}

echo "================================================="
echo "* This script tests all udocker CLI and options *"
echo "* except the run command and vol. mount options *"
echo "================================================="

STRING="T001: udocker install"
clean
udocker install && ls ${DEFAULT_UDIR}/bin/proot-x86_64; return=$?
result

STRING="T002: udocker install --force"
udocker install --force && \
    ls ${DEFAULT_UDIR}/bin/proot-x86_64 >/dev/null 2>&1; return=$?
result

STRING="T003: udocker (with no options)"
udocker ; return=$?
result

STRING="T004: udocker help"
udocker help >/dev/null 2>&1 ; return=$?
result

STRING="T005: udocker -h"
udocker -h >/dev/null 2>&1 ; return=$?
result

STRING="T006: udocker showconf"
udocker showconf; return=$?
result

STRING="T007: udocker version"
udocker version; return=$?
result

STRING="T008: udocker -D version"
udocker -D version; return=$?
result

STRING="T009: udocker --quiet version"
udocker --quiet version; return=$?
result

STRING="T010: udocker -q version"
udocker -q version; return=$?
result

STRING="T011: udocker --debug version"
udocker --debug version; return=$?
result

STRING="T012: udocker -V"
udocker -V >/dev/null 2>&1 ; return=$?
result

STRING="T013: udocker --version"
udocker --version >/dev/null 2>&1 ; return=$?
result

STRING="T014: udocker search -a"
udocker search -a gromacs | grep ^gromacs; return=$?
result

STRING="T015: udocker pull ${DOCKER_IMG}"
udocker pull ${DOCKER_IMG}; return=$?
result

STRING="T016: udocker --insecure pull ${DOCKER_IMG}"
udocker --insecure pull ${DOCKER_IMG}; return=$?
result

STRING="T017: udocker verify ${DOCKER_IMG}"
udocker verify ${DOCKER_IMG}; return=$?
result
## TODO: Add test to check layers after pull

STRING="T018: udocker images"
udocker images; return=$?
result

STRING="T019: udocker inspect (image)"
udocker inspect ${DOCKER_IMG}; return=$?
result

STRING="T020: udocker create ${DOCKER_IMG}"
export `udocker create ${DOCKER_IMG}`; return=$?
CONT_ID=$ContainerID
result

STRING="T021: udocker create --name=${CONT} ${DOCKER_IMG}"
CONT_ID_NAME=`udocker create --name=${CONT} ${DOCKER_IMG}`; return=$?
result

STRING="T022: udocker ps"
udocker ps; return=$?
result

STRING="T023: udocker name ${CONT_ID}"
udocker name ${CONT_ID} conti; return=$?
udocker ps |grep conti
result

STRING="T024: udocker rmname"
udocker rmname conti; return=$?
udocker ps |grep ${CONT_ID}
result

STRING="T025: udocker inspect (container ${CONT_ID})"
udocker inspect ${CONT_ID}; return=$?
result

STRING="T026: udocker clone --name=myclone ${CONT_ID}"
udocker clone --name=myclone ${CONT_ID}; return=$?
result

STRING="T027: udocker export -o myexportcont.tar ${CONT_ID}"
chmod -R u+x ${DEFAULT_UDIR}/containers/${CONT_ID}/ROOT
udocker export -o myexportcont.tar ${CONT_ID}; return=$?
result

STRING="T028: udocker rm ${CONT_ID}"
udocker rm ${CONT_ID}; return=$?
result

STRING="T029: udocker setup ${CONT}"
udocker setup ${CONT}; return=$?
result

rm -Rf "${TEST_UDIR}" > /dev/null 2>&1

STRING="T030: udocker mkrepo ${TEST_UDIR}"
udocker mkrepo ${TEST_UDIR}; return=$?
result

STRING="T031: udocker --repo=${TEST_UDIR} pull ${DOCKER_IMG}"
udocker --repo=${TEST_UDIR} pull ${DOCKER_IMG}; return=$?
result

STRING="T032: udocker --repo=${TEST_UDIR} verify ${DOCKER_IMG}"
udocker --repo=${TEST_UDIR} verify ${DOCKER_IMG}; return=$?
result

STRING="T033: UDOCKER_DIR=${TEST_UDIR} udocker verify ${DOCKER_IMG}"
UDOCKER_DIR=${TEST_UDIR} udocker verify ${DOCKER_IMG}; return=$?
result

rm -f ${TAR_IMAGE} > /dev/null 2>&1
echo "Download a docker tar img file ${TAR_IMAGE_URL}"
wget --no-check-certificate ${TAR_IMAGE_URL}
echo "|______________________________________________________________________________|"

STRING="T034: udocker load -i ${TAR_IMAGE}"
udocker load -i ${TAR_IMAGE}; return=$?
result

STRING="T035: udocker protect ${CONT} (container)"
udocker protect ${CONT}; return=$?
result

STRING="T036: udocker rm ${CONT} (try to remove protected container)"
udocker rm ${CONT}; return=$?
result_inv

STRING="T037: udocker unprotect ${CONT} (container)"
udocker unprotect ${CONT}; return=$?
result

STRING="T038: udocker rm ${CONT} (try to remove unprotected container)"
udocker rm ${CONT}; return=$?
result

rm -f ${TAR_CONT} > /dev/null 2>&1
echo "Download a docker tar container file ${TAR_CONT_URL}"
wget --no-check-certificate ${TAR_CONT_URL}
echo "|______________________________________________________________________________|"

STRING="T039: udocker import ${TAR_CONT} mycentos1:latest"
udocker import ${TAR_CONT} mycentos1:latest; return=$?
result

STRING="T040: udocker import --tocontainer --name=mycont ${TAR_CONT}"
udocker import --tocontainer --name=mycont ${TAR_CONT}; return=$?
result

STRING="T041: udocker import --clone --name=clone_cont ${TAR_CONT}"
udocker import --clone --name=clone_cont ${TAR_CONT}; return=$?
result

STRING="T042: udocker rmi ${DOCKER_IMG}"
udocker rmi ${DOCKER_IMG}; return=$?
result

STRING="T043: udocker ps -m"
udocker ps -m; return=$?
result

STRING="T044: udocker ps -s -m"
udocker ps -s -m; return=$?
result

STRING="T045: udocker images -l"
udocker images -l; return=$?
result

STRING="T046: udocker pull docker.io/python:3-slim <REGRESSION test for issue #359>"
udocker pull docker.io/python:3-slim; return=$?
result

STRING="T047: udocker create --name=py3slim docker.io/python:3-slim <REGRESSION test for issue #359>"
udocker create --name=py3slim docker.io/python:3-slim; return=$?
result

STRING="T048: udocker run py3slim python3 --version <REGRESSION test for issue #359>"
udocker run py3slim python3 --version; return=$?
result

STRING="T049: udocker pull public.ecr.aws/docker/library/redis <REGRESSION test for issue #168>"
udocker pull public.ecr.aws/docker/library/redis; return=$?
result

STRING="T050: udocker create --name=redis public.ecr.aws/docker/library/redis <REGRESSION test for issue #168>"
udocker create --name=redis public.ecr.aws/docker/library/redis; return=$?
result

STRING="T051: udocker run redis redis-server --version <REGRESSION test for issue #168>"
udocker run redis redis-server --version; return=$?
result

STRING="T052: udocker login --username=username --password=password"
udocker login --username=username --password=password; return=$?
result

STRING="T053: udocker logout -a"
udocker logout -a; return=$?
result

# Cleanup files containers and images used in the tests
echo "Clean up files containers and images used in the tests"
rm -rf myexportcont.tar "${TEST_UDIR}" "${TAR_IMAGE}" "${TAR_CONT}" > /dev/null 2>&1
udocker rm mycont
udocker rm clone_cont
udocker rm myclone
udocker rm py3slim
udocker rm redis
udocker rmi mycentos1
udocker rmi centos:7
udocker rmi docker.io/python:3-slim
udocker rmi public.ecr.aws/docker/library/redis
echo "|______________________________________________________________________________|"

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
