#!/bin/bash

# ##################################################################
#
# Build udocker-freng debian package
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
    mkdir -p "$BUILD_DIR/udocker-freng-${VERSION}/debian/source"
}

udocker_version()
{
    $REPO_DIR/utils/info.py | grep "udocker version:" | cut -f3- '-d ' | cut -f1 '-d-'
}

udocker_tarball_url()
{
    $REPO_DIR/utils/info.py | grep "udocker tarball:" | cut -f3- '-d '
}

patch_fakechroot_source()
{
    echo "patch_fakechroot_source"

    pushd "$TMP_DIR/${BASE_DIR}-${VERSION}/fakechroot"

    if [ -e "Fakechroot.patch" ] ; then
        echo "patch fakechroot source already applied: $PWD/Fakechroot.patch"
        return
    fi

    cp ${utils_dir}/fakechroot_source.patch Fakechroot.patch
    patch -p1 < Fakechroot.patch
    popd
}

patch_patchelf_source1()
{
    echo "patch_patchelf_source1"

    pushd "$TMP_DIR/${BASE_DIR}-${VERSION}/patchelf/src"

    if [ -e "Patchelf_make.patch" ] ; then
        echo "patch patchelf make already applied: $PWD/Patchelf_make.patch"
        return
    fi

    cp ${utils_dir}/patchelf_make_dynamic.patch Patchelf_make.patch
    patch < Patchelf_make.patch
    popd
}

patch_patchelf_source2()
{
    echo "patch_patchelf_source2"

    pushd "$TMP_DIR/${BASE_DIR}-${VERSION}/patchelf/src"

    if [ -e "Patchelf_code.patch" ] ; then
        echo "patch patchelf code already applied: $PWD/Patchelf_code.patch"
        return
    fi

    cp ${utils_dir}/patchelf_code.patch Patchelf_code.patch
    patch < Patchelf_code.patch
    popd
}

create_source_tarball()
{
    /bin/rm $SOURCE_TARBALL 2> /dev/null
    pushd $TMP_DIR
    /bin/rm -Rf ${BASE_DIR}-${VERSION}
    /bin/rm -Rf udocker_tarball.tgz
    curl $UDOCKER_TARBALL_URL > udocker_tarball.tgz
    /bin/mkdir ${BASE_DIR}-${VERSION}
    pushd ${BASE_DIR}-${VERSION}
    tar --wildcards -xzvf ../udocker_tarball.tgz \
                          udocker_dir/lib/libfakechroot*
    git clone --depth=1 --branch=2.18 https://github.com/dex4er/fakechroot
    patch_fakechroot_source
    git clone --depth=1 --branch=0.9 https://github.com/NixOS/patchelf.git
    patch_patchelf_source1
    patch_patchelf_source2

    /bin/cp -f fakechroot/COPYING COPYING-fakechroot
    /bin/cp -f fakechroot/LICENSE LICENSE-fakechroot
    /bin/cp -f fakechroot/THANKS THANKS-fakechroot
    /bin/cp -f patchelf/COPYING COPYING-patchelf
    /bin/cp -f patchelf/README README-patchelf
    popd
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
COPYING-fakechroot
LICENSE-fakechroot
THANKS-fakechroot
COPYING-patchelf
README-patchelf
M_DOCS
}

create_changelog()
{
    cat - > $DEB_CHANGELOG_FILE <<M_CHANGELOG
udocker-freng (1.1.0-1) trusty; urgency=low

  * Initial debian package

 -- $DEBFULLNAME <$DEBEMAIL>  Tue, 12 Sep 2017 10:20:00 +0000
M_CHANGELOG
}

create_copyright()
{
    cat - > $DEB_COPYRIGHT_FILE <<'M_COPYRIGHT'
Format: http://www.debian.org/doc/packaging-manuals/copyright-format/1.0/
Upstream-Name: Fakechroot
Source: https://github.com/dex4er/fakechroot

Files: *
Copyright: 2003, 2005, 2007-2011, 2013 Piotr Roszatycki <dexter@debian.org>
           2007 Mark Eichin <eichin@metacarta.com>
           2006, 2007 Alexander Shishkin <virtuoso@slind.org>
           2006, 2007 Lionel Tricon <lionel.tricon@free.fr>
License: LGPL

Files: debian/*
Copyright: 2003-2010, Piotr Roszatycki <dexter@debian.org>
           2017, udocker maintainer <udocker@lip.pt>
License: GPL-2+

Files: patchelf/*
Copyright: 2004-2016 Eelco Dolstra <eelco.dolstra@logicblox.com>
License: GPL-3+

Files: src/__opendir2.c
Copyright: 1983, 1993 The Regents of the University of California.
           2000 Daniel Eischen.
License: BSD-3-clause

Files: src/clearenv.c src/setenv.c src/unsetenv.c
Copyright: 1992,95,96,97,98,99,2000,2001 Free Software Foundation, Inc.
License: LGPL

Files: src/dedotdot.c
Copyright: 1999,2000 by Jef Poskanzer <jef@mail.acme.com>.
License: BSD-2-clause

Files: src/execl.c
Copyright: 1991,92,94,97,98,99,2002,2005 Free Software Foundation, Inc.
License: LGPL

Files: src/execle.c
Copyright: 1991,97,98,99,2002,2005 Free Software Foundation, Inc.
License: LGPL

Files: src/execlp.c
Copyright: 1991,93,96,97,98,99,2002,2005 Free Software Foundation, Inc.
License: LGPL

Files: src/execvp.c
Copyright: 1991,92, 1995-99, 2002, 2004, 2005, 2007, 2009 Free Software
           Foundation, Inc.
License: LGPL

Files: src/fts.c
Copyright: 1990, 1993, 1994 The Regents of the University of California.
License: BSD-3-clause

Files: src/ftw.c src/ftw64.c
Copyright: 1996-2004, 2006-2008, 2010 Free Software Foundation, Inc.
           This file is part of the GNU C Library.
           Contributed by Ulrich Drepper <drepper@cygnus.com>, 1996.
License: LGPL

Files: src/getcwd_real.c
Copyright: 1989, 1991, 1993 The Regents of the University of California.
           2000-2006 Erik Andersen <andersen@uclibc.org>
License: BSD-3-clause and LGPL

Files: src/popen.c
Copyright: 1988, 1993 The Regents of the University of California.
License: BSD-3-clause

Files: src/rawmemchr.c
Copyright: 2002 Manuel Novoa III
           2000-2005 Erik Andersen <andersen@uclibc.org>
License: LGPL

Files: src/realpath.c
Copyright: 1996-2010 Free Software Foundation, Inc.
License: LGPL

Files: src/rpl_lstat.c
Copyright: 1997-2006, 2008-2010 Free Software Foundation, Inc.
License: LGPL

Files: src/stpcpy.c
Copyright: 1992, 1995, 1997-1998, 2006, 2009-2010 Free Software
           Foundation, Inc.
License: LGPL

Files: src/strchrnul.c
Copyright: 2003, 2007, 2008, 2009, 2010 Free Software Foundation, Inc.
License: LGPL

Files: src/strlcpy.c
Copyright: 1998 Todd C. Miller <Todd.Miller@courtesan.com>
License: BSD-1-clause

License: BSD-1-clause
 Copyright (c) The Regents of the University of California.
 All rights reserved.
 .
 Permission to use, copy, modify, and distribute this software for any
 purpose with or without fee is hereby granted, provided that the above
 copyright notice and this permission notice appear in all copies.
 .
 THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.

License: BSD-2-clause
 Copyright (c) The Regents of the University of California.
 All rights reserved.
 .
 Redistribution and use in source and binary forms, with or without
 modification, are permitted provided that the following conditions
 are met:
 1. Redistributions of source code must retain the above copyright
    notice, this list of conditions and the following disclaimer.
 2. Redistributions in binary form must reproduce the above copyright
    notice, this list of conditions and the following disclaimer in the
    documentation and/or other materials provided with the distribution.
 .
 THIS SOFTWARE IS PROVIDED BY THE AUTHOR AND CONTRIBUTORS ``AS IS'' AND
 ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
 IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
 ARE DISCLAIMED.  IN NO EVENT SHALL THE AUTHOR OR CONTRIBUTORS BE LIABLE
 FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
 DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS
 OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION)
 HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT
 LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY
 OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF
 SUCH DAMAGE.

License: BSD-3-clause
 Copyright (c) The Regents of the University of California.
 All rights reserved.
 .
 Redistribution and use in source and binary forms, with or without
 modification, are permitted provided that the following conditions
 are met:
 1. Redistributions of source code must retain the above copyright
    notice, this list of conditions and the following disclaimer.
 2. Redistributions in binary form must reproduce the above copyright
    notice, this list of conditions and the following disclaimer in the
    documentation and/or other materials provided with the distribution.
 3. Neither the name of the University nor the names of its contributors
    may be used to endorse or promote products derived from this software
    without specific prior written permission.
 .
 THIS SOFTWARE IS PROVIDED BY THE REGENTS AND CONTRIBUTORS ``AS IS'' AND
 ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
 IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
 ARE DISCLAIMED.  IN NO EVENT SHALL THE REGENTS OR CONTRIBUTORS BE LIABLE
 FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
 DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS
 OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION)
 HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT
 LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY
 OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF
 SUCH DAMAGE.

License: GPL-2+
 On Debian systems, the full text of the GNU General Public
 License can be found in the file
 `/usr/share/common-licenses/GPL'.

License: LGPL
 On Debian systems, the full text of the GNU Lesser General Public
 License can be found in the file
 `/usr/share/common-licenses/LGPL'.

License: GPL-3+
 On Debian systems, the full text of the GNU General Public
 License can be found in the file
 `/usr/share/common-licenses/GPL'.

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
	dh $@  --sourcedirectory=patchelf

override_dh_auto_configure:
	cd patchelf ; bash bootstrap.sh ; bash ./configure

#override_dh_auto_build:
#	/bin/true

override_dh_auto_install:
	install -g 0 -o 0 -m 755 -D patchelf/src/patchelf debian/udocker-freng/usr/lib/udocker/patchelf-x86_64
	install -g 0 -o 0 -m 755 -D udocker_dir/lib/libfakechroot-CentOS-6-x86_64.so debian/udocker-freng/usr/lib/udocker/libfakechroot-CentOS-6-x86_64.so
	install -g 0 -o 0 -m 755 -D udocker_dir/lib/libfakechroot-CentOS-6-x86_64.so debian/udocker-freng/usr/lib/udocker/libfakechroot-Debian-7-x86_64.so
	install -g 0 -o 0 -m 755 -D udocker_dir/lib/libfakechroot-CentOS-7-x86_64.so debian/udocker-freng/usr/lib/udocker/libfakechroot-CentOS-7-x86_64.so
	install -g 0 -o 0 -m 755 -D udocker_dir/lib/libfakechroot-Fedora-25-x86_64.so debian/udocker-freng/usr/lib/udocker/libfakechroot-Fedora-25-x86_64.so
	install -g 0 -o 0 -m 755 -D udocker_dir/lib/libfakechroot-Fedora-25-x86_64.so debian/udocker-freng/usr/lib/udocker/libfakechroot-Fedora-x86_64.so
	install -g 0 -o 0 -m 755 -D udocker_dir/lib/libfakechroot-Ubuntu-14-x86_64.so debian/udocker-freng/usr/lib/udocker/libfakechroot-Ubuntu-14-x86_64.so
	install -g 0 -o 0 -m 755 -D udocker_dir/lib/libfakechroot-Ubuntu-14-x86_64.so debian/udocker-freng/usr/lib/udocker/libfakechroot-Ubuntu-x86_64.so
	install -g 0 -o 0 -m 755 -D udocker_dir/lib/libfakechroot-Ubuntu-14-x86_64.so debian/udocker-freng/usr/lib/udocker/libfakechroot-CentOS-x86_64.so
	install -g 0 -o 0 -m 755 -D udocker_dir/lib/libfakechroot-Ubuntu-14-x86_64.so debian/udocker-freng/usr/lib/udocker/libfakechroot-x86_64.so
	install -g 0 -o 0 -m 755 -D udocker_dir/lib/libfakechroot-Ubuntu-16-x86_64.so debian/udocker-freng/usr/lib/udocker/libfakechroot-Ubuntu-16-x86_64.so



ln -s libfakechroot-CentOS-6-x86_64.so  libfakechroot-Debian-7-x86_64.so ; \
M_RULES
}

create_control() 
{
    cat - > $DEB_CONTROL_FILE <<M_CONTROL
Source: udocker-freng
Section: utils
Priority: optional
Maintainer: udocker maintainer <udocker@lip.pt>
Build-Depends: debhelper (>= 9.0.0), wget
Standards-Version: 3.9.8
Homepage: https://www.gitbook.com/book/indigo-dc/udocker/details

Package: udocker-freng
Architecture: any
Depends: \${shlibs:Depends}, \${misc:Depends}, udocker (>=$VERSION)
Description: udocker Fakechroot engine for containers execution
 Engine to provide chroot and mount like capabilities for containers
 execution in user mode within udocker using Fakechroot and Patchelf
 https://github.com/dex4er/fakechroot http://nixos.org/patchelf.html

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
BASE_DIR="udocker-freng"
VERSION="$(udocker_version)"

TMP_DIR="/tmp"
BUILD_DIR="${HOME}/debuild"
SOURCE_TARBALL="${BUILD_DIR}/udocker-freng_${VERSION}.orig.tar.gz"

DEB_CONTROL_FILE="${BUILD_DIR}/udocker-freng-${VERSION}/debian/control"
DEB_CHANGELOG_FILE="${BUILD_DIR}/udocker-freng-${VERSION}/debian/changelog"
DEB_COMPAT_FILE="${BUILD_DIR}/udocker-freng-${VERSION}/debian/compat"
DEB_COPYRIGHT_FILE="${BUILD_DIR}/udocker-freng-${VERSION}/debian/copyright"
DEB_DOCS_FILE="${BUILD_DIR}/udocker-freng-${VERSION}/debian/docs"
DEB_RULES_FILE="${BUILD_DIR}/udocker-freng-${VERSION}/debian/rules"
DEB_SOURCE_DIR="${BUILD_DIR}/udocker-freng-${VERSION}/debian/source"
DEB_FORMAT_FILE="${BUILD_DIR}/udocker-freng-${VERSION}/debian/source/format"
DEB_INSTALL_FILE="${BUILD_DIR}/udocker-freng-${VERSION}/debian/install"

UDOCKER_TARBALL_URL=$(udocker_tarball_url)

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
pushd "${BUILD_DIR}/udocker-freng-${VERSION}/debian"
ls -l
debuild
