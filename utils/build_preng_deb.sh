#!/bin/bash

# ##################################################################
#
# Build udocker-preng debian package
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

sanity_check() 
{
    if [ ! -f "$REPO_DIR/udocker.py" ] ; then
        echo "$REPO_DIR/udocker.py not found aborting"
        exit 1
    fi
}

setup_env()
{
    mkdir -p "$BUILD_DIR/udocker-preng-${VERSION}/debian/source"
}

udocker_version()
{
    $REPO_DIR/udocker.py version | grep "version:" | cut -f2- '-d ' | cut -f1 '-d-'
}

create_source_tarball()
{
    /bin/rm $SOURCE_TARBALL 2> /dev/null
    pushd $TMP_DIR
    /bin/rm -Rf PRoot ${BASE_DIR}-${VERSION}
    #git clone https://github.com/proot-me/PRoot
    #pushd PRoot
    #git checkout v5.1.0
    #popd
    git clone https://github.com/jorge-lip/PRoot.git
    pushd PRoot
    git checkout udocker-1.1.1-dyn
    popd
    /bin/mv PRoot ${BASE_DIR}-${VERSION}
    tar czvf $SOURCE_TARBALL ${BASE_DIR}-${VERSION}
    /bin/rm -Rf $BASE_DIR ${BASE_DIR}-${VERSION}
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
README.rst
AUTHORS
M_DOCS
}

create_changelog()
{
    cat - > $DEB_CHANGELOG_FILE <<M_CHANGELOG
udocker-preng (1.1.3-1) trusty; urgency=low

  * Repackaging for udocker 1.1.3

 -- $DEBFULLNAME <$DEBEMAIL>  Tue, 30 Oct 2018 17:30:00 +0000

udocker-preng (1.1.2-1) trusty; urgency=low

  * Repackaging for udocker 1.1.2

 -- $DEBFULLNAME <$DEBEMAIL>  Fri, 26 Oct 2018 01:10:05 +0000

udocker-preng (1.1.1-1) trusty; urgency=low

  * Repackaging for udocker 1.1.1

 -- $DEBFULLNAME <$DEBEMAIL>  Wed, 8 Nov 2017 12:35:00 +0000

udocker-preng (1.1.0-1) trusty; urgency=low

  * Repackaging for udocker 1.1.0

 -- $DEBFULLNAME <$DEBEMAIL>  Tue, 12 Sep 2017 10:20:00 +0000

udocker-preng (1.0.3-1) trusty; urgency=low

  * Repackaging for udocker 1.0.3

 -- $DEBFULLNAME <$DEBEMAIL>  Wed, 22 Mar 2017 14:37:40 +0000

udocker-preng (1.0.2-1) trusty; urgency=low

  * Fix accelerated seccomp on kernels >= 4.8.0

 -- $DEBFULLNAME <$DEBEMAIL>  Tue, 14 Feb 2017 22:38:38 +0000

udocker-preng (1.0.1-1) trusty; urgency=low

  * Initial debian package

 -- $DEBFULLNAME <$DEBEMAIL>  Fri, 27 Jan 2017 22:15:39 +0000
M_CHANGELOG
}

create_copyright()
{
    cat - > $DEB_COPYRIGHT_FILE <<'M_COPYRIGHT'
Format: http://www.debian.org/doc/packaging-manuals/copyright-format/1.0/
Upstream-Name: proot
Source: http://proot.me

Files: *
Copyright: 2013, Cédric VINCENT <cedric.vincent@st.com>
           2013, Rémi DURAFFORT <remi.duraffort@st.com>
           2013, Yves JANIN <yves.janin@st.com>
           2013, Claire ROBINE <claire.robine@st.com>
           2013, Clément BAZIN <clement@bazin-fr.org>
           2013, Christophe GUILLON <christophe.guillon@st.com>
           2013, Christian BERTIN <christian.bertin@st.com>
           2013, Denis FERRANTI <denis.ferranti@st.com>
           2013, Paul GHALEB <paul.ghaleb@st.com>
           2013, STMicroelectronics
License: GPL-2+

Files: debian/*
Copyright: 2017, udocker maintainer <udocker@lip.pt>
License: GPL-2+

License: GPL-2+
 This package is free software; you can redistribute it and/or modify
 it under the terms of the GNU General Public License as published by
 the Free Software Foundation; either version 2 of the License, or
 (at your option) any later version.
 .
 This package is distributed in the hope that it will be useful,
 but WITHOUT ANY WARRANTY; without even the implied warranty of
 MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 GNU General Public License for more details.
 .
 You should have received a copy of the GNU General Public License
 along with this program. If not, see <http://www.gnu.org/licenses/>
 .
 On Debian systems, the complete text of the GNU General
 Public License version 2 can be found in "/usr/share/common-licenses/GPL-2".
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
	dh $@ --sourcedirectory=src

#.ONESHELL:
override_dh_auto_install:
	if [ "$$DEB_TARGET_ARCH" = "amd64" ]; then      \
	    PROOT="proot-x86_64" ;                      \
	elif [ "$$DEB_TARGET_ARCH" = "i386" ]; then     \
	    PROOT="proot-i386"   ;                      \
	elif [ "$$DEB_TARGET_ARCH" = "arm64" ]; then    \
	    PROOT="proot-arm64"  ;                      \
	elif [ "${DEB_TARGET_ARCH:0:3}" = "arm" ]; then \
	    PROOT="proot-arm"    ;                      \
	else                                            \
	    PROOT="proot"        ;                      \
	fi ;                                            \
	install -g 0 -o 0 -m 755 -D src/proot debian/udocker-preng/usr/lib/udocker/$$PROOT
M_RULES
}

create_control() 
{
    cat - > $DEB_CONTROL_FILE <<M_CONTROL
Source: udocker-preng
Section: utils
Priority: optional
Maintainer: udocker maintainer <udocker@lip.pt>
Build-Depends: debhelper (>= 9.0.0), libtalloc-dev
Standards-Version: 3.9.8
Homepage: https://www.gitbook.com/book/indigo-dc/udocker/details

Package: udocker-preng
Architecture: any
Depends: \${shlibs:Depends}, \${misc:Depends}, udocker (>=$VERSION)
Description: udocker proot engine for containers execution
 Engine to provide chroot and mount like capabilities for containers
 execution in user mode within udocker using PRoot https://github.com/proot-me.
 .
 PRoot is a user-space implementation of chroot, mount --bind,
 and binfmt_misc.
 .
 Technically PRoot relies on ptrace, an unprivileged system-call available in
 every Linux kernel.

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
BASE_DIR="udocker-preng"
VERSION="$(udocker_version)"

TMP_DIR="/tmp"
BUILD_DIR="${HOME}/debuild"
SOURCE_TARBALL="${BUILD_DIR}/udocker-preng_${VERSION}.orig.tar.gz"

DEB_CONTROL_FILE="${BUILD_DIR}/udocker-preng-${VERSION}/debian/control"
DEB_CHANGELOG_FILE="${BUILD_DIR}/udocker-preng-${VERSION}/debian/changelog"
DEB_COMPAT_FILE="${BUILD_DIR}/udocker-preng-${VERSION}/debian/compat"
DEB_COPYRIGHT_FILE="${BUILD_DIR}/udocker-preng-${VERSION}/debian/copyright"
DEB_DOCS_FILE="${BUILD_DIR}/udocker-preng-${VERSION}/debian/docs"
DEB_RULES_FILE="${BUILD_DIR}/udocker-preng-${VERSION}/debian/rules"
DEB_SOURCE_DIR="${BUILD_DIR}/udocker-preng-${VERSION}/debian/source"
DEB_FORMAT_FILE="${BUILD_DIR}/udocker-preng-${VERSION}/debian/source/format"
DEB_INSTALL_FILE="${BUILD_DIR}/udocker-preng-${VERSION}/debian/install"

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
pushd "${BUILD_DIR}/udocker-preng-${VERSION}/debian"
ls -l
debuild
