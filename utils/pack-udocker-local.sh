#!/bin/bash
cd ../
VERSION=`grep __version__ udocker/__init__.py | cut -d'"' -f 2`
echo $VERSION
#VERSION="1.0.11"
tar zcvf udocker-${VERSION}.tgz udocker
