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

UTILS_DIR="$(dirname $0)"
UDOCKER_CMD="${UTILS_DIR}/../udocker/maincmd.py"
PYTHON_LIST="$(type -p python2.7) $(type -p python3.6) $(type -p python3.11)" 

for PYTHON_CMD in $PYTHON_LIST
do
  /bin/rm -rf ${HOME}/.udocker-tests > /dev/null 2>&1
  sh ${UTILS_DIR}/udocker_test.sh $UDOCKER_CMD $PYTHON_CMD

  /bin/rm -rf ${HOME}/.udocker-tests > /dev/null 2>&1
  sh ${UTILS_DIR}/udocker_test-run.sh $UDOCKER_CMD $PYTHON_CMD
done
/bin/rm -rf ${HOME}/.udocker-tests > /dev/null 2>&1
