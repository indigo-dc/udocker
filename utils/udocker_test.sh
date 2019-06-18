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
DEFAULT_UDIR=$HOME/.udocker
DOCKER_IMG="ubuntu:18.04"
CONT="ubuntu"

function print_ok
{
  printf "  ${OK_STR}"
}

function print_fail
{
  printf "${FAIL_STR}"
}

function clean
{
  rm -rf ${DEFAULT_UDIR}
}

echo "================================================="
echo "* This script tests all udocker CLI and options *"
echo "================================================="

# ##################################################################
echo "------------------------------------------------------------>"
echo "udocker install, udocker install --force"
clean
udocker install && ls ${DEFAULT_UDIR}/bin/proot-x86_64; return=$?
echo " "
if [ $return == 0 ]; then
    print_ok;   echo "    udocker install"
else
    print_fail; echo "    udocker install"
fi

udocker install --force && ls ${DEFAULT_UDIR}/bin/proot-x86_64 >/dev/null 2>&1; return=$?
if [ $return == 0 ]; then
    print_ok;   echo "    udocker install --force"
else
    print_fail; echo "    udocker install --force"
fi

# ##################################################################
echo "------------------------------------------------------------>"
echo "udocker with no options, or udocker help,-h,--help: show help message"
udocker ; return=$?
echo " "
if [ $return == 0 ]; then
    print_ok;   echo "    udocker"
else
    print_fail; echo "    udocker"
fi

udocker help >/dev/null 2>&1 ; return=$?
if [ $return == 0 ]; then
    print_ok;   echo "    udocker help"
else
    print_fail; echo "    udocker help"
fi

udocker -h >/dev/null 2>&1 ; return=$?
if [ $return == 0 ]; then
    print_ok;   echo "    udocker -h"
else
    print_fail; echo "    udocker -h"
fi

# ##################################################################
echo "------------------------------------------------------------>"
echo "udocker listconf"
udocker listconf; return=$?
echo " "
if [ $return == 0 ]; then
    print_ok;   echo "    udocker listconf"
else
    print_fail; echo "    udocker listconf"
fi

# ##################################################################
echo "------------------------------------------------------------>"
echo "udocker version, -V, --version"
udocker version; return=$?
echo " "
if [ $return == 0 ]; then
    print_ok;   echo "    udocker version"
else
    print_fail; echo "    udocker version"
fi

udocker -V >/dev/null 2>&1 ; return=$?
if [ $return == 0 ]; then
    print_ok;   echo "    udocker -V"
else
    print_fail; echo "    udocker -V"
fi

udocker --version >/dev/null 2>&1 ; return=$?
if [ $return == 0 ]; then
    print_ok;   echo "    udocker --version"
else
    print_fail; echo "    udocker --version"
fi

# ##################################################################
echo "------------------------------------------------------------>"
echo "udocker search -a"
udocker search -a gromacs | grep ^gromacs; return=$?
echo " "
if [ $return == 0 ]; then
    print_ok;   echo "    udocker search -a"
else
    print_fail; echo "    udocker search -a"
fi

# ##################################################################
echo "------------------------------------------------------------>"
echo "udocker pull"
udocker pull ${DOCKER_IMG}; return=$?
echo " "
if [ $return == 0 ]; then
    print_ok;   echo "    udocker pull"
else
    print_fail; echo "    udocker pull"
fi

## TODO: Add test to check layers after pull

# ##################################################################
echo "------------------------------------------------------------>"
echo "udocker images"
udocker images; return=$?
echo " "
if [ $return == 0 ]; then
    print_ok;   echo "    udocker images"
else
    print_fail; echo "    udocker images"
fi

# ##################################################################
echo "------------------------------------------------------------>"
echo "udocker create, create --name"
udocker create ${DOCKER_IMG}; return=$?
echo " "
if [ $return == 0 ]; then
    print_ok;   echo "    udocker create"
else
    print_fail; echo "    udocker create"
fi

udocker create --name=${CONT} ${DOCKER_IMG}; return=$?
if [ $return == 0 ]; then
    print_ok;   echo "    udocker create --name="
else
    print_fail; echo "    udocker create --name="
fi

# ##################################################################
echo "------------------------------------------------------------>"
echo "udocker ps"
udocker ps; return=$?
echo " "
if [ $return == 0 ]; then
    print_ok;   echo "    udocker ps"
else
    print_fail; echo "    udocker ps"
fi


