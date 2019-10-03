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
TEST_UDIR=$HOME/.udockermy
TAR_IMAGE="centos7.tar"
TAR_CONT="centos7-cont.tar"
TAR_IMAGE_URL="https://download.ncg.ingrid.pt/webdav/udocker_test/${TAR_IMAGE}"
TAR_CONT_URL="https://download.ncg.ingrid.pt/webdav/udocker_test/${TAR_CONT}"
DOCKER_IMG="ubuntu:18.04"
CONT="ubuntu"

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
  rm -rf ${DEFAULT_UDIR}
}

function result
{
  if [ $1 == 0 ]; then
      print_ok; echo $2
  else
      print_fail; echo $2
  fi
}

echo "================================================="
echo "* This script tests all udocker CLI and options *"
echo "================================================="

# ##################################################################
echo "------------------------------------------------------------>"
STRING="    T001-> udocker install"
clean
udocker install && ls ${DEFAULT_UDIR}/bin/proot-x86_64; return=$?
result $return $STRING

# ##################################################################
echo "------------------------------------------------------------>"
STRING="    T002-> udocker install --force"
udocker install --force && ls ${DEFAULT_UDIR}/bin/proot-x86_64 >/dev/null 2>&1; return=$?
result $return $STRING

# ##################################################################
echo "------------------------------------------------------------>"
udocker ; return=$?
if [ $return == 0 ]; then
    print_ok;   echo "    udocker (with no options)"
else
    print_fail; echo "    udocker (with no options)"
fi

# ##################################################################
echo "------------------------------------------------------------>"
echo "udocker help"
udocker help >/dev/null 2>&1 ; return=$?
echo " "
if [ $return == 0 ]; then
    print_ok;   echo "    udocker help"
else
    print_fail; echo "    udocker help"
fi

# ##################################################################
echo "------------------------------------------------------------>"
echo "udocker -h"
udocker -h >/dev/null 2>&1 ; return=$?
echo " "
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
echo "udocker version"
udocker version; return=$?
echo " "
if [ $return == 0 ]; then
    print_ok;   echo "    udocker version"
else
    print_fail; echo "    udocker version"
fi

# ##################################################################
echo "------------------------------------------------------------>"
echo "udocker -V"
udocker -V >/dev/null 2>&1 ; return=$?
echo " "
if [ $return == 0 ]; then
    print_ok;   echo "    udocker -V"
else
    print_fail; echo "    udocker -V"
fi

# ##################################################################
echo "------------------------------------------------------------>"
echo "udocker --version"
udocker --version >/dev/null 2>&1 ; return=$?
echo " "
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
echo "udocker pull ${DOCKER_IMG}"
udocker pull ${DOCKER_IMG}; return=$?
echo " "
if [ $return == 0 ]; then
    print_ok;   echo "    udocker pull"
else
    print_fail; echo "    udocker pull"
fi

# ##################################################################
echo "------------------------------------------------------------>"
echo "udocker verify ${DOCKER_IMG}"
udocker verify ${DOCKER_IMG}; return=$?
echo " "
if [ $return == 0 ]; then
    print_ok;   echo "    udocker verify"
else
    print_fail; echo "    udocker verify"
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
echo "udocker inspect (image)"
udocker inspect ${DOCKER_IMG}; return=$?
echo " "
if [ $return == 0 ]; then
    print_ok;   echo "    udocker inspect (image)"
else
    print_fail; echo "    udocker inspect (image)"
fi

# ##################################################################
echo "------------------------------------------------------------>"
echo "udocker create ${DOCKER_IMG}"
CONT_ID=`udocker create ${DOCKER_IMG}`; return=$?
echo "ContainerID = ${CONT_ID}"
echo " "
if [ $return == 0 ]; then
    print_ok;   echo "    udocker create ${DOCKER_IMG}"
else
    print_fail; echo "    udocker create ${DOCKER_IMG}"
fi

# ##################################################################
echo "------------------------------------------------------------>"
echo "udocker create --name=${CONT} ${DOCKER_IMG}"
CONT_ID_NAME=`udocker create --name=${CONT} ${DOCKER_IMG}`; return=$?
if [ $return == 0 ]; then
    print_ok;   echo "    udocker create --name=${CONT} ${DOCKER_IMG}"
else
    print_fail; echo "    udocker create --name=${CONT} ${DOCKER_IMG}"
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

# ##################################################################
echo "------------------------------------------------------------>"
echo "udocker name ${CONT_ID}"
udocker name ${CONT_ID} conti; return=$?
udocker ps |grep conti
echo " "
if [ $return == 0 ]; then
    print_ok;   echo "    udocker name"
else
    print_fail; echo "    udocker name"
fi

# ##################################################################
echo "------------------------------------------------------------>"
echo "udocker rmname"
udocker rmname conti; return=$?
udocker ps |grep ${CONT_ID}
echo " "
if [ $return == 0 ]; then
    print_ok;   echo "    udocker rmname"
else
    print_fail; echo "    udocker rmname"
fi

# ##################################################################
echo "------------------------------------------------------------>"
echo "udocker inspect (container ${CONT_ID})"
udocker inspect ${CONT_ID}; return=$?
echo " "
if [ $return == 0 ]; then
    print_ok;   echo "    udocker inspect (container)"
else
    print_fail; echo "    udocker inspect (container)"
fi

# ##################################################################
echo "------------------------------------------------------------>"
echo "udocker clone --name=myclone ${CONT_ID}"
udocker clone --name=myclone ${CONT_ID}; return=$?
echo " "
if [ $return == 0 ]; then
    print_ok;   echo "    udocker clone --name=myclone ${CONT_ID}"
else
    print_fail; echo "    udocker clone --name=myclone ${CONT_ID}"
fi

# ##################################################################
echo "------------------------------------------------------------>"
echo "udocker export -o myexportcont.tar ${CONT_ID}"
chmod -R u+x ${DEFAULT_UDIR}/containers/${CONT_ID}/ROOT
udocker export -o myexportcont.tar ${CONT_ID}; return=$?
echo " "
if [ $return == 0 ]; then
    print_ok;   echo "    udocker export -o myexportcont.tar ${CONT_ID}"
else
    print_fail; echo "    udocker export -o myexportcont.tar ${CONT_ID}"
fi

# ##################################################################
echo "------------------------------------------------------------>"
echo "udocker rm ${CONT_ID}"
udocker rm ${CONT_ID}; return=$?
echo " "
if [ $return == 0 ]; then
    print_ok;   echo "    udocker rm (container)"
else
    print_fail; echo "    udocker rm (container)"
fi

# ##################################################################
echo "------------------------------------------------------------>"
echo "udocker setup ${CONT}"
udocker setup ${CONT}; return=$?
echo " "
if [ $return == 0 ]; then
    print_ok;   echo "    udocker setup ${CONT}"
else
    print_fail; echo "    udocker setup ${CONT}"
fi

# ##################################################################
echo "------------------------------------------------------------>"
echo "udocker run ${CONT} env|sort"
udocker run ${CONT} env|sort; return=$?
echo " "
if [ $return == 0 ]; then
    print_ok;   echo "    udocker run ${CONT} env|sort"
else
    print_fail; echo "    udocker run ${CONT} env|sort"
fi

# ##################################################################
echo "------------------------------------------------------------>"
echo "udocker setup --execmode=F3 ${CONT}"
udocker setup --execmode=F3 ${CONT}; return=$?
echo " "
if [ $return == 0 ]; then
    print_ok;   echo "    udocker setup --execmode=F3 ${CONT}"
else
    print_fail; echo "    udocker setup --execmode=F3 ${CONT}"
fi

# ##################################################################
echo "------------------------------------------------------------>"
echo "udocker mkrepo ${TEST_UDIR}"
udocker mkrepo ${TEST_UDIR}; return=$?
echo " "
if [ $return == 0 ]; then
    print_ok;   echo "    udocker mkrepo ${TEST_UDIR}"
else
    print_fail; echo "    udocker mkrepo ${TEST_UDIR}"
fi

# ##################################################################
echo "------------------------------------------------------------>"
echo "udocker --repo=${TEST_UDIR} pull ${DOCKER_IMG}"
udocker --repo=${TEST_UDIR} pull ${DOCKER_IMG}; return=$?
echo " "
if [ $return == 0 ]; then
    print_ok;   echo "    udocker --repo=${TEST_UDIR} pull ${DOCKER_IMG}"
else
    print_fail; echo "    udocker --repo=${TEST_UDIR} pull ${DOCKER_IMG}"
fi

# ##################################################################
echo "------------------------------------------------------------>"
echo "udocker --repo=${TEST_UDIR} verify ${DOCKER_IMG}"
udocker --repo=${TEST_UDIR} verify ${DOCKER_IMG}; return=$?
echo " "
if [ $return == 0 ]; then
    print_ok;   echo "    udocker --repo=${TEST_UDIR} verify ${DOCKER_IMG}"
else
    print_fail; echo "    udocker --repo=${TEST_UDIR} verify ${DOCKER_IMG}"
fi

# ##################################################################
echo "------------------------------------------------------------>"

if [[ -f ${TAR_IMAGE} ]];
then
    echo "tar img file exists ${TAR_IMAGE_URL}"
else
    echo "Download a docker tar img file ${TAR_IMAGE_URL}"
    wget ${TAR_IMAGE_URL}
fi

# ##################################################################
echo "------------------------------------------------------------>"
echo "udocker load -i ${TAR_IMAGE}"
udocker load -i ${TAR_IMAGE}; return=$?
echo " "
if [ $return == 0 ]; then
    print_ok;   echo "    udocker load -i ${TAR_IMAGE}"
else
    print_fail; echo "    udocker load -i ${TAR_IMAGE}"
fi

# ##################################################################
echo "------------------------------------------------------------>"
echo "udocker protect ${CONT} (container)"
udocker protect ${CONT}; return=$?
echo " "
if [ $return == 0 ]; then
    print_ok;   echo "    udocker protect ${CONT}"
else
    print_fail; echo "    udocker protect ${CONT}"
fi

# ##################################################################
echo "------------------------------------------------------------>"
echo "udocker rm ${CONT} (try to remove protected container)"
udocker rm ${CONT}; return=$?
echo " "
if [ $return == 1 ]; then
    print_ok;   echo "    try to remove protected container ${CONT}"
else
    print_fail; echo "    try to remove protected container ${CONT}"
fi

# ##################################################################
echo "------------------------------------------------------------>"
echo "udocker unprotect ${CONT} (container)"
udocker unprotect ${CONT}; return=$?
echo " "
if [ $return == 0 ]; then
    print_ok;   echo "    udocker unprotect ${CONT}"
else
    print_fail; echo "    udocker unprotect ${CONT}"
fi

# ##################################################################
echo "------------------------------------------------------------>"
echo "udocker rm ${CONT} (try to remove unprotected container)"
udocker rm ${CONT}; return=$?
echo " "
if [ $return == 0 ]; then
    print_ok;   echo "    try to remove unprotected container ${CONT}"
else
    print_fail; echo "    try to remove unprotected container ${CONT}"
fi

# ##################################################################
echo "------------------------------------------------------------>"

if [[ -f ${TAR_CONT} ]];
then
    echo "tar container file exists ${TAR_CONT_URL}"
else
    echo "Download a docker tar container file ${TAR_CONT_URL}"
    wget ${TAR_CONT_URL}
fi

# ##################################################################
echo "------------------------------------------------------------>"
echo "udocker import ${TAR_CONT} mycentos1:latest"
udocker import ${TAR_CONT} mycentos1:latest; return=$?
echo " "
if [ $return == 0 ]; then
    print_ok;   echo "    udocker import ${TAR_CONT} mycentos1:latest"
else
    print_fail; echo "    udocker import ${TAR_CONT} mycentos1:latest"
fi

# ##################################################################
echo "------------------------------------------------------------>"
echo "udocker import --tocontainer --name=mycont ${TAR_CONT}"
udocker import --tocontainer --name=mycont ${TAR_CONT}; return=$?
echo " "
if [ $return == 0 ]; then
    print_ok;   echo "    udocker import --tocontainer --name=mycont ${TAR_CONT}"
else
    print_fail; echo "    udocker import --tocontainer --name=mycont ${TAR_CONT}"
fi

# ##################################################################
echo "------------------------------------------------------------>"
echo "udocker import --clone --name=clone_cont ${TAR_CONT}"
udocker import --clone --name=clone_cont ${TAR_CONT}; return=$?
echo " "
if [ $return == 0 ]; then
    print_ok;   echo "    udocker import --clone --name=clone_cont ${TAR_CONT}"
else
    print_fail; echo "    udocker import --clone --name=clone_cont ${TAR_CONT}"
fi

# ##################################################################
echo "------------------------------------------------------------>"
echo "udocker rmi ${DOCKER_IMG}"
udocker rmi ${DOCKER_IMG}; return=$?
echo " "
if [ $return == 0 ]; then
    print_ok;   echo "    udocker rmi ${DOCKER_IMG}"
else
    print_fail; echo "    udocker rmi ${DOCKER_IMG}"
fi
