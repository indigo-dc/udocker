#!/bin/bash

# ##################################################################
#
# Get, prepare and install udocker
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

VER="1.2.5"
echo "=========================================================="
echo "* This script gets the udocker-${VER}.tar.gz, unpacks it *"
echo "* makes a link for the udocker executable and puts it in *"
echo "* the PATH                                               *"
echo "=========================================================="

rm -f udocker-${VER}.tar.gz
rm -rf udocker
wget https://github.com/mariojmdavid/udocker/releases/download/v${VER}/udocker-${VER}.tar.gz
tar zxvf udocker-${VER}.tar.gz
export PATH=`pwd`/udocker:$PATH
