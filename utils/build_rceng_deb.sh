#!/bin/bash

# ##################################################################
#
# Build udocker-rceng debian package
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
    mkdir -p "$BUILD_DIR/udocker-rceng-${VERSION}/debian/source"
}

udocker_version()
{
    $REPO_DIR/utils/info.py | grep "udocker version:" | cut -f3- '-d ' | cut -f1 '-d-'
}

create_source_tarball()
{
    /bin/rm $SOURCE_TARBALL 2> /dev/null
    pushd $TMP_DIR
    /bin/rm -Rf runc ${BASE_DIR}-${VERSION}
    git clone --depth=1 https://github.com/opencontainers/runc
    /bin/mv runc ${BASE_DIR}-${VERSION}
    tar czvf $SOURCE_TARBALL ${BASE_DIR}-${VERSION}
    /bin/rm -Rf ${BASE_DIR}-${VERSION}
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
NOTICE
M_DOCS
}

create_changelog()
{
    cat - > $DEB_CHANGELOG_FILE <<M_CHANGELOG
udocker-rceng (1.1.0-1) trusty; urgency=low

  * Initial debian package

 -- $DEBFULLNAME <$DEBEMAIL>  Tue, 12 Sep 2017 00:28:00 +0000
M_CHANGELOG
}

create_copyright()
{
    cat - > $DEB_COPYRIGHT_FILE <<'M_COPYRIGHT'
Format: http://www.debian.org/doc/packaging-manuals/copyright-format/1.0/
Upstream-Name: runc
Source: https://runc.io/

Files: *
Copyright: 2012-2015, Docker Inc.
License: Apache-2.0

Files: debian/*
Copyright: 2017, udocker maintainer <udocker@lip.pt>
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

SHELL := /bin/bash

# Uncomment this to turn on verbose mode.
export DH_VERBOSE=1

%:
	dh $@ --buildsystem=golang --with=golang

#.ONESHELL:
override_dh_auto_build:
	echo "PWD `pwd`"                                            ; \
	mkdir -p obj-x86_64-linux-gnu/src/github.com/opencontainers ; \
	cd obj-x86_64-linux-gnu/src/github.com/opencontainers       ; \
	ln -s ../../../.. runc                                      ; \
	cd runc                                                     ; \
        [ -d /usr/lib/go-1.6 ] && export PATH=/usr/lib/go-1.6/bin:$$PATH   ; \
	GOPATH=$$(pwd)/obj-x86_64-linux-gnu make

override_dh_auto_test:
	echo overriding dh_auto_test

#.ONESHELL:
override_dh_auto_install:
	if [ "$$DEB_TARGET_ARCH" = "amd64" ]; then       \
	    RUNC="runc-x86_64" ;                         \
	elif [ "$$DEB_TARGET_ARCH" = "i386" ]; then      \
	    RUNC="runc-i386" ;                           \
	elif [ "$$DEB_TARGET_ARCH" = "arm64" ]; then     \
	    RUNC="runc-arm64" ;                          \
	elif [ "$${DEB_TARGET_ARCH:0:3}" = "arm" ]; then \
	    RUNC="runc-arm" ;                            \
	else                                             \
	    RUNC="runc" ;                                \
	fi ;                                             \
	install -g 0 -o 0 -m 755 -D runc debian/udocker-rceng/usr/lib/udocker/$$RUNC ; \
	/bin/rm runc
M_RULES
}

create_include_binaries()
{

    cat - > $DEB_BINARIES_FILE <<M_BINARIES
runc
M_BINARIES
}

create_control() 
{
    cat - > $DEB_CONTROL_FILE <<M_CONTROL
Source: udocker-rceng
Section: utils
Priority: optional
Maintainer: udocker maintainer <udocker@lip.pt>
Build-Depends: debhelper (>= 9.0.0), golang-go, libseccomp-dev, dh-golang
Standards-Version: 3.9.8
Homepage: https://www.gitbook.com/book/indigo-dc/udocker/details

Package: udocker-rceng
Architecture: any
Depends: \${shlibs:Depends}, \${misc:Depends}, udocker (>=$VERSION)
Description: udocker engine for rootless containers execution
 Engine execute containers using rootless containers using runc.
 .
 https://runc.io/ 

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
BASE_DIR="udocker-rceng"
VERSION="$(udocker_version)"

TMP_DIR="/tmp"
BUILD_DIR="${HOME}/debuild"
SOURCE_TARBALL="${BUILD_DIR}/udocker-rceng_${VERSION}.orig.tar.gz"

DEB_CONTROL_FILE="${BUILD_DIR}/udocker-rceng-${VERSION}/debian/control"
DEB_CHANGELOG_FILE="${BUILD_DIR}/udocker-rceng-${VERSION}/debian/changelog"
DEB_COMPAT_FILE="${BUILD_DIR}/udocker-rceng-${VERSION}/debian/compat"
DEB_COPYRIGHT_FILE="${BUILD_DIR}/udocker-rceng-${VERSION}/debian/copyright"
DEB_DOCS_FILE="${BUILD_DIR}/udocker-rceng-${VERSION}/debian/docs"
DEB_RULES_FILE="${BUILD_DIR}/udocker-rceng-${VERSION}/debian/rules"
DEB_SOURCE_DIR="${BUILD_DIR}/udocker-rceng-${VERSION}/debian/source"
DEB_FORMAT_FILE="${BUILD_DIR}/udocker-rceng-${VERSION}/debian/source/format"
DEB_INSTALL_FILE="${BUILD_DIR}/udocker-rceng-${VERSION}/debian/install"
DEB_BINARIES_FILE="${BUILD_DIR}/udocker-rceng-${VERSION}/debian/source/include-binaries"

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
#create_include_binaries
pushd "${BUILD_DIR}/udocker-rceng-${VERSION}/debian"
ls -l
debuild
