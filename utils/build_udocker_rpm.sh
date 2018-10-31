#!/bin/bash

# ##################################################################
#
# Build udocker rpm package
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
    mkdir -p ~/rpmbuild/{BUILD,RPMS,SOURCES,SPECS,SRPMS}
    if [ ! -e ~/.rpmmacros ]; then
        echo '%_topdir %(echo $HOME)/rpmbuild' > ~/.rpmmacros
    fi
}

udocker_version()
{
    $REPO_DIR/udocker.py version | grep "version:" | cut -f2- '-d ' | cut -f1 '-d-'
}

create_source_tarball()
{
    /bin/rm $SOURCE_TARBALL 2> /dev/null
    pushd $PARENT_DIR
    tar -czv --xform "s/^$BASE_DIR/udocker/" -f $SOURCE_TARBALL \
       $BASE_DIR/doc $BASE_DIR/README.md $BASE_DIR/LICENSE \
       $BASE_DIR/changelog $BASE_DIR/udocker.py
    popd
    tar tzvf $SOURCE_TARBALL
}

create_specfile() 
{
    cat - > $SPECFILE << UDOCKER_SPEC
Name: udocker
Summary: udocker
Version: $VERSION
Release: $RELEASE
Source0: %{name}-%{version}.tar.gz
License: ASL 2.0
ExclusiveOS: linux
Group: Applications/Emulators
Provides: %{name} = %{version}
URL: https://www.gitbook.com/book/indigo-dc/udocker/details
BuildArch: noarch
BuildRoot: %{_tmppath}/%{name}-%{version}-root
BuildRequires: fileutils, findutils, bash, tar, gzip
Requires: fileutils, findutils, bash, python-pycurl, openssl, tar, gzip, which, numactl

%define debug_package %{nil}

%description
A simple tool to execute Linux Docker containers in user space without requiring root privileges. Enables basic download and execution of docker containers by non-privileged users in Linux systems were docker is not available. It can be used to access and execute the content of docker containers in Linux batch systems and interactive clusters that are managed by other entities such as grid infrastructures or externaly managed batch or interactive systems.

%prep
%setup -q -n udocker

%build
cp %{_builddir}/%{name}/udocker.py %{_builddir}/%{name}/udocker
echo $VERSION > %{_builddir}/%{name}/VERSION
cat - > %{_builddir}/%{name}/udocker.conf <<UCONF
bindir = "%{_libexecdir}/udocker"
libdir = "%{_datarootdir}/udocker/lib"
tarball =  ""
autoinstall = False
UCONF

%install
rm -rf %{buildroot}
install -m 755 -D %{_builddir}/%{name}/udocker %{buildroot}/%{_bindir}/udocker
install -m 644 -D %{_builddir}/%{name}/udocker.conf %{buildroot}/%{_sysconfdir}/udocker.conf
install -m 755 -d %{buildroot}/%{_libexecdir}/udocker
install -m 755 -d %{buildroot}/%{_datarootdir}/udocker/lib
install -m 644 -D %{_builddir}/%{name}/VERSION %{buildroot}/%{_datarootdir}/udocker/lib/VERSION
install -D %{_builddir}/%{name}/doc/udocker.1 %{buildroot}/%{_mandir}/man1/udocker.1

%clean
rm -rf %{buildroot}

%files 
%defattr(-,root,root)
%{_bindir}/udocker
%{_libexecdir}/udocker
%{_datarootdir}/udocker/lib

%config(noreplace) %{_sysconfdir}/udocker.conf

%doc README.md changelog doc/installation_manual.md doc/user_manual.md LICENSE
%doc %{_mandir}/man1/udocker.1*

%changelog
* Tue Oct 30 2018 udocker maintainer <udocker@lip.pt> 1.1.3-1
- Support for nvidia drivers on ubuntu
- Installation improvements
* Fri Oct 26 2018 udocker maintainer <udocker@lip.pt> 1.1.2-1
- Improve parsing of quotes in the command line
- Fix version command to exit with 0
- Add kill-on-exit to proot on P modes
- Improve download of udocker utils
- Handle authentication headers when pulling
- Handle of redirects when pulling
- Fix registries table
- Support search quay.io
- Fix auth header when no standard Docker registry is used
- Add registry detection on image name
- Add --version option
- Force python2 as interpreter
- Fix handling of volumes in metadata
- Handle empty metadata
- Fix http proxy functionality
- Ignore --no-trunc and --all in the images command
- Implement verification of layers in manifest
- Add --nvidia to support GPUs and related drivers
- Send download messages to stderr
- Enable override of curl executable
- Fix building on CentOS 6.1
- Mitigation for upstream limitation in runC without tty
- Fix detection of executable with symlinks in container
* Wed Nov 8 2017 udocker maintainer <udocker@lip.pt> 1.1.1-1
- New execution engine using singularity
- Updated documentation with OpenMPI information and examples
- Additional unit tests
- Redirect messages to stderr
- Improved parsing of quotes in the command line
- Allow override of the HOME environment variable
- Allow override of libfakechroot.so at the container level
- Automatic selection of libfakechroot.so from container info
- Improve automatic install
- Enable resetting prefix paths in Fn modes in remote hosts
- Do not set AF_UNIX_PATH in Fn modes when the host /tmp is a volume
- Export containers in both docker and udocker format
- Import containers docker and udocker format
- Load, import and export to/from stdin/stdout
- Clone existing containers
- Fix run with basenames failing
* Tue Sep 12 2017 udocker maintainer <udocker@lip.pt> 1.1.0-1
- Support image names prefixed by registry similarly to docker
- Add execution engine selection logic
- Add fr execution engine based on shared library interception
- Add rc execution engine based on rootless namespaces
- Add environment variable UDOCKER_KEYSTORE
- Prevent creation of .udocker when UDOCKER_KEYSTORE is used
* Wed Mar 22 2017 udocker maintainer <udocker@lip.pt> 1.0.3-1 
- Support for import containers in newer Docker format
- Restructuring to support additional execution engines
- Support further elements in ENTRYPOINT
- Increase name alias length
- Add support for change dir into volume directories
- Fix owner error upon temporary file removal
- Improve support for variables with spaces in command line
- Change misleading behavior of import from move to copy
- Fix validation of volumes to impose absolute paths
* Tue Feb 14 2017 udocker maintainer <udocker@lip.pt> 1.0.2-1 
- Fix download on repositories that fail authentication on /v2
- Fix run verification binaries with recursive symbolic links
* Mon Jan  9 2017 udocker maintainer <udocker@lip.pt> 1.0.1-1
- Initial rpm package version

UDOCKER_SPEC
}

# ##################################################################
# MAIN
# ##################################################################

RELEASE="1"

utils_dir="$(dirname $(readlink -e $0))"
REPO_DIR="$(dirname $utils_dir)"
PARENT_DIR="$(dirname $REPO_DIR)"
BASE_DIR="$(basename $REPO_DIR)"
VERSION="$(udocker_version)"

RPM_DIR="${HOME}/rpmbuild"
SOURCE_TARBALL="${RPM_DIR}/SOURCES/udocker-${VERSION}.tar.gz"
SPECFILE="${RPM_DIR}/SPECS/udocker.spec"

cd $REPO_DIR
sanity_check
setup_env
create_source_tarball
create_specfile
rpmbuild -ba $SPECFILE

