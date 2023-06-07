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

function result
{
  echo " "
  if [ $return == 0 ]; then
      print_ok; echo "    $STRING"
  else
      print_fail; echo "    $STRING"
      FAILED_TESTS+=("$STRING")
  fi
  echo "|______________________________________________________________________________|"
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
  echo "|______________________________________________________________________________|"
}

function udocker
{
   $PYTHON_CMD $UDOCKER_CMD $*
}

echo "============================================="
echo "* This script tests udocker run and options *"
echo "* and volume mount options                  *"
echo "============================================="

DEFAULT_UDIR=$HOME/.udocker-tests
export UDOCKER_DIR=${DEFAULT_UDIR}
if [ -d ${DEFAULT_UDIR} ]
then
  echo "ERROR test directory exists, remove first: ${DEFAULT_UDIR}"
  exit 1
fi

echo "|______________________________________________________________________________|"
udocker rm c7
udocker rm ub22
udocker rm jv

## Use openjdk:8-jdk-alpine for regression of issue #363

echo "|______________________________________________________________________________|"
udocker rmi centos:7
udocker rmi ubuntu:22.04
udocker rmi openjdk:8-jdk-alpine

echo "|______________________________________________________________________________|"
udocker pull centos:7; return=$?
udocker pull ubuntu:22.04; return=$?
udocker pull openjdk:8-jdk-alpine; return=$?

echo "|______________________________________________________________________________|"
udocker images; return=$?
udocker create --name=c7 centos:7; return=$?
udocker create --name=ub22 ubuntu:22.04; return=$?
udocker create --name=jv openjdk:8-jdk-alpine; return=$?
udocker ps; return=$?

echo "===================="
echo "* Test udocker run *"
echo "===================="

echo "===================================== execmode = P1"
STRING="T001: udocker setup jv == execmode = P1"
udocker setup jv; return=$?
result

STRING="T002: udocker run jv java -version == execmode = P1"
udocker run --env="LANG=C" jv java -version; return=$?
result

STRING="T003: udocker setup c7 == execmode = P1"
udocker setup c7; return=$?
result

STRING="T004: udocker run c7 ls --version == execmode = P1"
udocker run c7 ls --version; return=$?
result

STRING="T005: udocker setup ub22 == execmode = P1"
udocker setup ub22; return=$?
result

STRING="T006: udocker run ub22 ls --version == execmode = P1"
udocker run ub22 ls --version; return=$?
result

echo "===================================== execmode = P2"
STRING="T007: udocker setup --execmode=P2 jv == execmode = P2"
udocker setup --execmode=P2 jv; return=$?
result

STRING="T008: udocker run jv java -version == execmode = P2"
udocker run --env="LANG=C" jv java -version; return=$?
result

STRING="T009: udocker setup --execmode=P2 c7 == execmode = P2"
udocker setup --execmode=P2 c7; return=$?
result

STRING="T010: udocker run c7 ls --version == execmode = P2"
udocker run c7 ls --version; return=$?
result

STRING="T011: udocker setup --execmode=P2 ub22 == execmode = P2"
udocker setup --execmode=P2 ub22; return=$?
result

STRING="T012: udocker run ub22 ls --version == execmode = P2"
udocker run ub22 ls --version; return=$?
result

echo "===================================== execmode = F1"
STRING="T013: udocker setup --execmode=F1 c7 == execmode = F1"
udocker setup --execmode=F1 c7; return=$?
result

STRING="T014: udocker run c7 ls --version == execmode = F1"
udocker run c7 ls --version; return=$?
result

STRING="T015: udocker setup --execmode=F1 ub22 == execmode = F1"
udocker setup --execmode=F1 ub22; return=$?
result

STRING="T016: udocker run ub22 ls --version == execmode = F1"
udocker run ub22 ls --version; return=$?
result

echo "===================================== execmode = F2"
STRING="T017: udocker setup --execmode=F2 c7 == execmode = F2"
udocker setup --execmode=F2 c7; return=$?
result

STRING="T018: udocker run c7 ls --version == execmode = F2"
udocker run c7 ls --version; return=$?
result

STRING="T019: udocker setup --execmode=F2 ub22 == execmode = F2"
udocker setup --execmode=F2 ub22; return=$?
result

STRING="T020: udocker run ub22 ls --version == execmode = F2"
udocker run ub22 ls --version; return=$?
result

echo "===================================== execmode = F3"
STRING="T021: udocker setup --execmode=F3 jv == execmode = F3"
udocker setup --execmode=F3 jv; return=$?
result

STRING="T022: udocker run jv java -version == execmode = F3"
udocker run --env="LANG=C" jv java -version; return=$?
result

STRING="T023: udocker setup --execmode=F3 c7 == execmode = F3"
udocker setup --execmode=F3 c7; return=$?
result

STRING="T024: udocker run c7 ls --version == execmode = F3"
udocker run c7 ls --version; return=$?
result

STRING="T025: udocker setup --execmode=F3 ub22 == execmode = F3"
udocker setup --execmode=F3 ub22; return=$?
result

STRING="T026: udocker run ub22 ls --version == execmode = F3"
udocker run ub22 ls --version; return=$?
result

echo "===================================== execmode = F4"
STRING="T027: udocker setup --execmode=F4 jv == execmode = F4"
udocker setup --execmode=F4 jv; return=$?
result

STRING="T028: udocker run jv java -version == execmode = F4"
udocker run --env="LANG=C" jv java -version; return=$?
result

STRING="T029: udocker setup --execmode=F4 c7 == execmode = F4"
udocker setup --execmode=F4 c7; return=$?
result

STRING="T030: udocker run c7 ls --version == execmode = F4"
udocker run c7 ls --version; return=$?
result

STRING="T031: udocker setup --execmode=F4 ub22 == execmode = F4"
udocker setup --execmode=F4 ub22; return=$?
result

STRING="T032: udocker run ub22 ls --version == execmode = F4"
udocker run ub22 ls --version; return=$?
result

echo "===================================== execmode = R1"
STRING="T033: udocker setup --execmode=R1 jv == execmode = R1"
udocker setup --execmode=R1 jv; return=$?
result

STRING="T034: udocker run jv java -version == execmode = R1"
udocker run --env="LANG=C" jv java -version; return=$?
result

STRING="T035: udocker setup --execmode=R1 c7 == execmode = R1"
udocker setup --execmode=R1 c7; return=$?
result

STRING="T036: udocker run c7 ls --version == execmode = R1"
udocker run c7 ls --version; return=$?
result

STRING="T037: udocker setup --execmode=R1 ub22 == execmode = R1"
udocker setup --execmode=R1 ub22; return=$?
result

STRING="T038: udocker run ub22 ls --version == execmode = R1"
udocker run ub22 ls --version; return=$?
result

echo "===================================== execmode = R2"
STRING="T039: udocker setup --execmode=R2 jv == execmode = R2"
udocker setup --execmode=R2 jv; return=$?
result

STRING="T040: udocker run jv java -version == execmode = R2"
udocker run --env="LANG=C" jv java -version; return=$?
result

STRING="T041: udocker setup --execmode=R2 c7 == execmode = R2"
udocker setup --execmode=R2 c7; return=$?
result

STRING="T042: udocker run c7 ls --version == execmode = R2"
udocker run c7 ls --version; return=$?
result

STRING="T043: udocker setup --execmode=R2 ub22 == execmode = R2"
udocker setup --execmode=R2 ub22; return=$?
result

STRING="T044: udocker run ub22 ls --version == execmode = R2"
udocker run ub22 ls --version; return=$?
result

echo "===================================== execmode = R3"
STRING="T045: udocker setup --execmode=R3 jv == execmode = R3"
udocker setup --execmode=R3 jv; return=$?
result

STRING="T046: udocker run jv java -version == execmode = R3"
udocker run --env="LANG=C" jv java -version; return=$?
result

STRING="T047: udocker setup --execmode=R3 c7 == execmode = R3"
udocker setup --execmode=R3 c7; return=$?
result

STRING="T048: udocker run c7 ls --version == execmode = R3"
udocker run c7 ls --version; return=$?
result

STRING="T049: udocker setup --execmode=R3 ub22 == execmode = R3"
udocker setup --execmode=R3 ub22; return=$?
result

STRING="T050: udocker run ub22 ls --version == execmode = R3"
udocker run ub22 ls --version; return=$?
result

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

