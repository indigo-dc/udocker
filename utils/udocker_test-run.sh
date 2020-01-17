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
  fi
  echo "------------------------------------------------------------>"
}

function result_inv
{
  echo " "
  if [ $return == 1 ]; then
      print_ok; echo "    $STRING"
  else
      print_fail; echo "    $STRING"
  fi
  echo "------------------------------------------------------------>"
}

echo "============================================="
echo "* This script tests udocker run and options *"
echo "* and volume mount options                  *"
echo "============================================="
udocker pull centos:7; return=$?
udocker pull ubuntu:18.04; return=$?
udocker images; return=$?
udocker create --name=c7 centos:7; return=$?
udocker create --name=ub18 ubuntu:18.04; return=$?
udocker ps; return=$?

echo "===================="
echo "* Test udocker run *"
echo "===================="

echo "===================================== execmode = P1"
STRING="T008: udocker setup c7"
udocker setup c7; return=$?
result

STRING="T009: udocker run c7 env|sort"
udocker run c7 env|sort; return=$?
result

STRING="T010: udocker setup ub18"
udocker setup ub18; return=$?
result

STRING="T011: udocker run ub18 env|sort"
udocker run ub18 env|sort; return=$?
result

echo "===================================== execmode = P2"
STRING="T012: udocker setup --execmode=P2 c7"
udocker setup --execmode=P2 c7; return=$?
result

STRING="T013: udocker run c7 env|sort"
udocker run c7 env|sort; return=$?
result

STRING="T014: udocker setup --execmode=P2 ub18"
udocker setup --execmode=P2 ub18; return=$?
result

STRING="T015: udocker run ub18 env|sort"
udocker run ub18 env|sort; return=$?
result

echo "===================================== execmode = F1"
STRING="T016: udocker setup --execmode=F1 c7"
udocker setup --execmode=F1 c7; return=$?
result

STRING="T017: udocker run c7 env|sort"
udocker run c7 env|sort; return=$?
result

STRING="T018: udocker setup --execmode=F1 ub18"
udocker setup --execmode=F1 ub18; return=$?
result

STRING="T019: udocker run ub18 env|sort"
udocker run ub18 env|sort; return=$?
result

echo "===================================== execmode = F2"
STRING="T016: udocker setup --execmode=F2 c7"
udocker setup --execmode=F2 c7; return=$?
result

STRING="T017: udocker run c7 env|sort"
udocker run c7 env|sort; return=$?
result

STRING="T018: udocker setup --execmode=F2 ub18"
udocker setup --execmode=F2 ub18; return=$?
result

STRING="T019: udocker run ub18 env|sort"
udocker run ub18 env|sort; return=$?
result

echo "===================================== execmode = F3"
STRING="T016: udocker setup --execmode=F3 c7"
udocker setup --execmode=F3 c7; return=$?
result

STRING="T017: udocker run c7 env|sort"
udocker run c7 env|sort; return=$?
result

STRING="T018: udocker setup --execmode=F3 ub18"
udocker setup --execmode=F3 ub18; return=$?
result

STRING="T019: udocker run ub18 env|sort"
udocker run ub18 env|sort; return=$?
result

echo "===================================== execmode = F4"
STRING="T016: udocker setup --execmode=F4 c7"
udocker setup --execmode=F4 c7; return=$?
result

STRING="T017: udocker run c7 env|sort"
udocker run c7 env|sort; return=$?
result

STRING="T018: udocker setup --execmode=F4 ub18"
udocker setup --execmode=F4 ub18; return=$?
result

STRING="T019: udocker run ub18 env|sort"
udocker run ub18 env|sort; return=$?
result

echo "===================================== execmode = R1"
STRING="T020: udocker setup --execmode=R1 c7"
udocker setup --execmode=R1 c7; return=$?
result

STRING="T021: udocker run c7 env|sort"
udocker run c7 env|sort; return=$?
result

STRING="T022: udocker setup --execmode=R1 ub18"
udocker setup --execmode=R1 ub18; return=$?
result

STRING="T023: udocker run ub18 env|sort"
udocker run ub18 env|sort; return=$?
result

echo "===================================== execmode = R2"
STRING="T024: udocker setup --execmode=R2 c7"
udocker setup --execmode=R2 c7; return=$?
result

STRING="T025: udocker run c7 env|sort"
udocker run c7 env|sort; return=$?
result

STRING="T026: udocker setup --execmode=R2 ub18"
udocker setup --execmode=R2 ub18; return=$?
result

STRING="T027: udocker run ub18 env|sort"
udocker run ub18 env|sort; return=$?
result

echo "===================================== execmode = R3"
STRING="T028: udocker setup --execmode=R3 c7"
udocker setup --execmode=R3 c7; return=$?
result

STRING="T029: udocker run c7 env|sort"
udocker run c7 env|sort; return=$?
result

STRING="T030: udocker setup --execmode=R3 ub18"
udocker setup --execmode=R3 ub18; return=$?
result

STRING="T031: udocker run ub18 env|sort"
udocker run ub18 env|sort; return=$?
result
