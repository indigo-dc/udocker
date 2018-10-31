#!/bin/bash

# ##################################################################
#
# Build udocker debian package
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
    mkdir -p "$BUILD_DIR/udocker-${VERSION}/debian/source"
}

udocker_version()
{
    $REPO_DIR/udocker.py version | grep "version:" | cut -f2- '-d ' | cut -f1 '-d-'
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
udocker (1.1.3-1) trusty; urgency=low

  * Support for nvidia drivers on ubuntu
  * Installation improvements

 -- $DEBFULLNAME <$DEBEMAIL>  Tue, 30 Oct 2018 17:30:00 +0000

udocker (1.1.2-1) trusty; urgency=low

  * Improve parsing of quotes in the command line
  * Fix version command to exit with 0
  * Add kill-on-exit to proot on P modes
  * Improve download of udocker utils
  * Handle authentication headers when pulling
  * Handle of redirects when pulling
  * Fix registries table
  * Support search quay.io
  * Fix auth header when no standard Docker registry is used
  * Add registry detection on image name
  * Add --version option
  * Force python2 as interpreter
  * Fix handling of volumes in metadata
  * Handle empty metadata
  * Fix http proxy functionality
  * Ignore --no-trunc and --all in the images command
  * Implement verification of layers in manifest
  * Add --nvidia to support GPUs and related drivers
  * Send download messages to stderr
  * Enable override of curl executable
  * Fix building on CentOS 6.1
  * Mitigation for upstream limitation in runC without tty
  * Fix detection of executable with symlinks in container

 -- $DEBFULLNAME <$DEBEMAIL>  Fri, 26 Oct 2018 00:59:16 +0000

udocker (1.1.1-1) trusty; urgency=low

  * New execution engine using singularity
  * Updated documentation with OpenMPI information and examples
  * Additional unit tests
  * Redirect messages to stderr
  * Improved parsing of quotes in the command line
  * Allow override of the HOME environment variable
  * Allow override of libfakechroot.so at the container level
  * Automatic selection of libfakechroot.so from container info
  * Improve automatic install
  * Enable resetting prefix paths in Fn modes in remote hosts
  * Do not set AF_UNIX_PATH in Fn modes when the host /tmp is a volume
  * Export containers in both docker and udocker format
  * Import containers docker and udocker format
  * Load, import and export to/from stdin/stdout
  * Clone existing containers
  * Fix run with basenames failing

 -- $DEBFULLNAME <$DEBEMAIL>  Wed, 8 Nov 2017 12:28:00 +0000

udocker (1.1.0-1) trusty; urgency=low

  * Support image names prefixed by registry similarly to docker
  * Add execution engine selection logic
  * Add fr execution engine based on shared library interception
  * Add rc execution engine based on rootless namespaces
  * Add environment variable UDOCKER_KEYSTORE
  * Prevent creation of .udocker when UDOCKER_KEYSTORE is used

 -- $DEBFULLNAME <$DEBEMAIL>  Tue, 12 Sep 2017 00:14:00 +0000

udocker (1.0.3-1) trusty; urgency=low

  * Support for import containers in newer Docker format
  * Restructuring to support additional execution engines
  * Support further elements in ENTRYPOINT
  * Increase name alias length
  * Add support for change dir into volume directories
  * Fix owner error upon temporary file removal
  * Improve support for variables with spaces in command line
  * Change misleading behavior of import from move to copy
  * Fix validation of volumes to impose absolute paths

 -- $DEBFULLNAME <$DEBEMAIL>  Wed, 22 Mar 2017 14:39:40 +0000

udocker (1.0.2-1) trusty; urgency=low

  * Fix download on repositories that fail authentication on /v2
  * Fix run verification binaries with recursive symbolic links

 -- $DEBFULLNAME <$DEBEMAIL>  Tue, 14 Feb 2017 22:36:00 +0000

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

create_manpages()
{
    cat - > $DEB_MANPAGE_FILE <<'M_MANPAGE'
doc/udocker.1
M_MANPAGE
}

create_control() 
{
    cat - > $DEB_CONTROL_FILE <<'M_CONTROL'
Source: udocker
Section: utils
Priority: optional
Maintainer: udocker maintainer <udocker@lip.pt>
Build-Depends: debhelper (>= 9.0.0), python (>= 2.7)
Standards-Version: 3.9.8
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
DEB_MANPAGE_FILE="${BUILD_DIR}/udocker-${VERSION}/debian/udocker.manpages"
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
create_manpages
create_rules
create_format
create_control
pushd "${BUILD_DIR}/udocker-${VERSION}/debian"
debuild
