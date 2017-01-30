#!/bin/bash

# ##################################################################
#
# Build udocker debian package
#
# ##################################################################

sanity_check() 
{
    if [ ! -f "$REPO_DIR/udocker.py" ] ; then
        echo "$REPO_DIR/udocker.py not found aborting"
        exit 1
    fi
}

setup_env()
{
    mkdir -p "$BUILD_DIR/udocker-${VERSION}/debian/source"
}

udocker_version()
{
    grep "^__version__" "$REPO_DIR/udocker.py" | cut '-d"' -f2 
}

create_source_tarball()
{
    /bin/rm $SOURCE_TARBALL 2> /dev/null
    pushd $PARENT_DIR
    tar -czv --xform "s/^$BASE_DIR/udocker-$VERSION/"  -f $SOURCE_TARBALL \
       $BASE_DIR/doc $BASE_DIR/README.md $BASE_DIR/LICENSE \
       $BASE_DIR/changelog $BASE_DIR/udocker.py
    popd
}

untar_source_tarball()
{
    pushd $BUILD_DIR
    tar xzvf $SOURCE_TARBALL
    popd
}

create_compat()
{
    echo "9" > $DEB_COMPAT_FILE
}

create_format()
{
    echo "3.0 (quilt)" > $DEB_FORMAT_FILE
}

create_docs()
{
    cat - > $DEB_DOCS_FILE <<M_DOCS
README.md
doc/user_manual.md
doc/installation_manual.md
M_DOCS
}

create_changelog()
{
    cat - > $DEB_CHANGELOG_FILE <<M_CHANGELOG
udocker (1.0.1-1) trusty; urgency=low

  * Initial debian package

 -- $DEBFULLNAME <$DEBEMAIL>  Fri, 27 Jan 2017 22:15:39 +0000
M_CHANGELOG
}

create_copyright()
{
    cat - > $DEB_COPYRIGHT_FILE <<'M_COPYRIGHT'
Format: http://www.debian.org/doc/packaging-manuals/copyright-format/1.0/
Upstream-Name: udocker
Source: https://github.com/indigo-dc/udocker

Files: *
Copyright: 2016 2017, udocker maintainer <udocker@lip.pt>
License: Apache-2.0

Files: debian/*
Copyright: 2016 2017, udocker maintainer <udocker@lip.pt>
License: Apache-2.0

License: Apache-2.0
 Licensed under the Apache License, Version 2.0 (the "License");
 you may not use this file except in compliance with the License.
 You may obtain a copy of the License at
 .
 http://www.apache.org/licenses/LICENSE-2.0
 .
 Unless required by applicable law or agreed to in writing, software
 distributed under the License is distributed on an "AS IS" BASIS,
 WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 See the License for the specific language governing permissions and
 limitations under the License.
 .
 On Debian systems, the complete text of the Apache version 2.0 license
 can be found in "/usr/share/common-licenses/Apache-2.0".
M_COPYRIGHT
}

create_rules()
{
    cat - > $DEB_RULES_FILE <<'M_RULES'
#!/usr/bin/make -f
# -*- makefile -*-

# Uncomment this to turn on verbose mode.
export DH_VERBOSE=1

%:
	dh $@ --with python2

override_dh_auto_build:
	grep "^__version__" udocker.py | cut '-d"' -f2 > VERSION
	echo 'bindir = "/usr/lib/udocker"' > udocker.conf
	echo 'libdir = "/usr/lib/udocker"' >> udocker.conf
	echo 'tarball =  ""' >> udocker.conf
	echo 'autoinstall = False' >> udocker.conf
	dh_auto_build

override_dh_auto_install:
	install -g 0 -o 0 -m 755 -D udocker.py debian/udocker/usr/bin/udocker
	install -g 0 -o 0 -m 644 -D udocker.conf debian/udocker/etc/udocker.conf
	install -g 0 -o 0 -m 755 -d debian/udocker/usr/lib/udocker
	install -g 0 -o 0 -m 644 -D VERSION debian/udocker/usr/lib/udocker/VERSION
	dh_auto_install

override_dh_clean:
	-rm udocker.conf VERSION
	dh_clean
M_RULES
}

create_control() 
{
    cat - > $DEB_CONTROL_FILE <<'M_CONTROL'
Source: udocker
Section: utils
Priority: optional
Maintainer: udocker maintainer <udocker@lip.pt>
Build-Depends: debhelper (>= 9.0.0), python (>= 2.7)
Standards-Version: 3.9.7
Homepage: https://github.com/indigo-dc/udocker

Package: udocker
Architecture: all
Depends: python (>= 2.7), python-pycurl, openssl, numactl,
 ${misc:Depends}, ${python:Depends}
Description: Tool to execute Linux Docker containers in user space
 udocker is a tool to execute Linux Docker containers in user space
 without requiring root privileges. Enables basic download and execution
 of docker containers by non-privileged users in Linux systems were docker
 is not available. It can be used to access and execute the content of
 docker containers in Linux batch systems and interactive clusters that
 are managed by other entities such as grid infrastructures or externaly
 managed batch or interactive systems.
M_CONTROL
}

# ##################################################################
# MAIN
# ##################################################################

RELEASE="1"

export DEBFULLNAME="udocker maintainer"
export DEBEMAIL="udocker@lip.pt"

utils_dir="$(dirname $(readlink -e $0))"
REPO_DIR="$(dirname $utils_dir)"
PARENT_DIR="$(dirname $REPO_DIR)"
BASE_DIR="$(basename $REPO_DIR)"
VERSION="$(udocker_version)"

BUILD_DIR="${HOME}/debuild"
SOURCE_TARBALL="${BUILD_DIR}/udocker_${VERSION}.orig.tar.gz"

DEB_CONTROL_FILE="${BUILD_DIR}/udocker-${VERSION}/debian/control"
DEB_CHANGELOG_FILE="${BUILD_DIR}/udocker-${VERSION}/debian/changelog"
DEB_COMPAT_FILE="${BUILD_DIR}/udocker-${VERSION}/debian/compat"
DEB_COPYRIGHT_FILE="${BUILD_DIR}/udocker-${VERSION}/debian/copyright"
DEB_DOCS_FILE="${BUILD_DIR}/udocker-${VERSION}/debian/docs"
DEB_RULES_FILE="${BUILD_DIR}/udocker-${VERSION}/debian/rules"
DEB_SOURCE_DIR="${BUILD_DIR}/udocker-${VERSION}/debian/source"
DEB_FORMAT_FILE="${BUILD_DIR}/udocker-${VERSION}/debian/source/format"
DEB_INSTALL_FILE="${BUILD_DIR}/udocker-${VERSION}/debian/install"

pushd $REPO_DIR
sanity_check
setup_env
create_source_tarball
untar_source_tarball
create_control
create_changelog
create_compat
create_copyright
create_docs
create_rules
create_format
create_control
pushd "${BUILD_DIR}/udocker-${VERSION}/debian"
debuild
