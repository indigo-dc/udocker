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

echo "============================================="
echo "* This script tests udocker run and options *"
echo "* and volume mount options                  *"
echo "============================================="

DEFAULT_UDIR=$HOME/.udocker-tests
export UDOCKER_DIR=${DEFAULT_UDIR}
if [ -d ${DEFAULT_UDIR} ]
then
  echo "${DEFAULT_UDIR} exists, will not run tests"
  exit 1
fi

udocker rm c7
udocker rm ub18
udocker rm jv
udocker rmi centos:7
udocker rmi ubuntu:18.04
udocker rmi java

udocker pull centos:7; return=$?
udocker pull ubuntu:18.04; return=$?
udocker pull java; return=$?
udocker images; return=$?
udocker create --name=c7 centos:7; return=$?
udocker create --name=ub18 ubuntu:18.04; return=$?
udocker create --name=jv java; return=$?
udocker ps; return=$?

echo "===================="
echo "* Test udocker run *"
echo "===================="

echo "===================================== execmode = P1"
STRING="T006: udocker setup jv"
udocker setup jv; return=$?
result

STRING="T007: udocker run jv java -version"
udocker run jv java -version; return=$?
result

STRING="T008: udocker setup c7"
udocker setup c7; return=$?
result

STRING="T009: udocker run c7 env|sort"
udocker run c7 env; return=$?
result

STRING="T010: udocker setup ub18"
udocker setup ub18; return=$?
result

STRING="T011: udocker run ub18 env|sort"
udocker run ub18 env; return=$?
result

echo "===================================== execmode = P2"
STRING="T006: udocker setup --execmode=P2 jv"
udocker setup --execmode=P2 jv; return=$?
result

STRING="T007: udocker run jv java -version"
udocker run jv java -version; return=$?
result

STRING="T012: udocker setup --execmode=P2 c7"
udocker setup --execmode=P2 c7; return=$?
result

STRING="T013: udocker run c7 env|sort"
udocker run c7 env; return=$?
result

STRING="T014: udocker setup --execmode=P2 ub18"
udocker setup --execmode=P2 ub18; return=$?
result

STRING="T015: udocker run ub18 env|sort"
udocker run ub18 env; return=$?
result

echo "===================================== execmode = F1"
STRING="T016: udocker setup --execmode=F1 c7"
udocker setup --execmode=F1 c7; return=$?
result

STRING="T017: udocker run c7 env|sort"
udocker run c7 env; return=$?
result

STRING="T018: udocker setup --execmode=F1 ub18"
udocker setup --execmode=F1 ub18; return=$?
result

STRING="T019: udocker run ub18 env|sort"
udocker run ub18 env; return=$?
result

echo "===================================== execmode = F2"
STRING="T016: udocker setup --execmode=F2 c7"
udocker setup --execmode=F2 c7; return=$?
result

STRING="T017: udocker run c7 env|sort"
udocker run c7 env; return=$?
result

STRING="T018: udocker setup --execmode=F2 ub18"
udocker setup --execmode=F2 ub18; return=$?
result

STRING="T019: udocker run ub18 env|sort"
udocker run ub18 env; return=$?
result

echo "===================================== execmode = F3"
STRING="T006: udocker setup --execmode=F3 jv"
udocker setup --execmode=F3 jv; return=$?
result

STRING="T007: udocker run jv java -version"
udocker run --env="LANG=C" jv java -version; return=$?
result

STRING="T016: udocker setup --execmode=F3 c7"
udocker setup --execmode=F3 c7; return=$?
result

STRING="T017: udocker run c7 env|sort"
udocker run c7 env; return=$?
result

STRING="T018: udocker setup --execmode=F3 ub18"
udocker setup --execmode=F3 ub18; return=$?
result

STRING="T019: udocker run ub18 env|sort"
udocker run ub18 env; return=$?
result

echo "===================================== execmode = F4"
STRING="T006: udocker setup --execmode=F4 jv"
udocker setup --execmode=F4 jv; return=$?
result

STRING="T007: udocker run jv java -version"
udocker run --env="LANG=C" jv java -version; return=$?
result

STRING="T016: udocker setup --execmode=F4 c7"
udocker setup --execmode=F4 c7; return=$?
result

STRING="T017: udocker run c7 env|sort"
udocker run c7 env; return=$?
result

STRING="T018: udocker setup --execmode=F4 ub18"
udocker setup --execmode=F4 ub18; return=$?
result

STRING="T019: udocker run ub18 env|sort"
udocker run ub18 env; return=$?
result

echo "===================================== execmode = R1"
STRING="T006: udocker setup --execmode=R1 jv"
udocker setup --execmode=R1 jv; return=$?
result

STRING="T007: udocker run jv java -version"
udocker run jv java -version; return=$?
result

STRING="T020: udocker setup --execmode=R1 c7"
udocker setup --execmode=R1 c7; return=$?
result

STRING="T021: udocker run c7 env|sort"
udocker run c7 env; return=$?
result

STRING="T022: udocker setup --execmode=R1 ub18"
udocker setup --execmode=R1 ub18; return=$?
result

STRING="T023: udocker run ub18 env|sort"
udocker run ub18 env; return=$?
result

echo "===================================== execmode = R2"
STRING="T006: udocker setup --execmode=R2 jv"
udocker setup --execmode=R2 jv; return=$?
result

STRING="T007: udocker run jv java -version"
udocker run jv java -version; return=$?
result

STRING="T024: udocker setup --execmode=R2 c7"
udocker setup --execmode=R2 c7; return=$?
result

STRING="T025: udocker run c7 env|sort"
udocker run c7 env; return=$?
result

STRING="T026: udocker setup --execmode=R2 ub18"
udocker setup --execmode=R2 ub18; return=$?
result

STRING="T027: udocker run ub18 env|sort"
udocker run ub18 env; return=$?
result

echo "===================================== execmode = R3"
STRING="T006: udocker setup --execmode=R3 jv"
udocker setup --execmode=R3 jv; return=$?
result

STRING="T007: udocker run jv java -version"
udocker run jv java -version; return=$?
result

STRING="T028: udocker setup --execmode=R3 c7"
udocker setup --execmode=R3 c7; return=$?
result

STRING="T029: udocker run c7 env|sort"
udocker run c7 env; return=$?
result

STRING="T030: udocker setup --execmode=R3 ub18"
udocker setup --execmode=R3 ub18; return=$?
result

STRING="T031: udocker run ub18 env|sort"
udocker run ub18 env; return=$?
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

