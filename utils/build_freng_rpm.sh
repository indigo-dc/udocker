#!/bin/bash

# ##################################################################
#
# Build udocker-freng rpm package
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

udocker_tarball_url()
{
    $REPO_DIR/utils/udocker.py version | grep "tarball:" | cut -f2- '-d ' | cut -f1 '-d '
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
                          udocker_dir/lib/libfakechroot* udocker_dir/bin/patchelf*
    #git clone --depth=1 --branch=2.18 https://github.com/dex4er/fakechroot
    git clone https://github.com/dex4er/fakechroot
    pushd fakechroot
    git checkout 2.18
    popd
    patch_fakechroot_source
    #git clone --depth=1 --branch=0.9 https://github.com/NixOS/patchelf.git
    git clone https://github.com/NixOS/patchelf.git
    pushd patchelf
    git checkout 0.9
    popd
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


create_specfile() 
{
    cat - > $SPECFILE <<FRENG_SPEC
Name: udocker-freng
Summary: udocker-freng
Version: $VERSION
Release: $RELEASE
Source0: %{name}-%{version}.tar.gz
License: LGPLv2+ and GPLv3+
ExclusiveOS: linux
Group: Applications/Emulators
Provides: %{name} = %{version}
URL: https://www.gitbook.com/book/indigo-dc/udocker/details
BuildRoot: %{_tmppath}/%{name}-%{version}-root
BuildRequires: kernel, kernel-devel, fileutils, findutils, bash, tar, gzip, curl
Requires: udocker, glibc-devel
AutoReqProv: no

%define debug_package %{nil}

%description
Engine to provide chroot and mount like capabilities for containers execution in user mode within udocker using Fakechroot https://github.com/dex4er/fakechroot and Patchelf http://nixos.org/patchelf.html.

%prep
#%setup -q -n $BASE_DIR
/bin/rm -Rf %{_builddir}/%{name}-%{version}

%build
cd %{_builddir}
tar xzvf $SOURCE_TARBALL
cd %{name}-%{version}
cd patchelf
#bash ./bootstrap.sh
#bash ./configure
#make

%install
rm -rf %{buildroot}
#install -m 755 -D %{_builddir}/%{name}-%{version}/patchelf/src/patchelf %{buildroot}/%{_libexecdir}/udocker/patchelf-x86_64
install -m 755 -D %{_builddir}/%{name}-%{version}/udocker_dir/bin/patchelf-x86_64 %{buildroot}/%{_libexecdir}/udocker/patchelf-x86_64
echo "%{_libexecdir}/udocker/patchelf-x86_64" > %{_builddir}/%{name}-%{version}/files.lst
install -m 755 -D %{_builddir}/%{name}-%{version}/udocker_dir/lib/libfakechroot-CentOS-6-x86_64.so %{buildroot}/%{_datarootdir}/udocker/lib/libfakechroot-CentOS-6-x86_64.so
echo "%{_datarootdir}/udocker/lib/libfakechroot-CentOS-6-x86_64.so" >> %{_builddir}/%{name}-%{version}/files.lst
install -m 755 -D %{_builddir}/%{name}-%{version}/udocker_dir/lib/libfakechroot-CentOS-6-x86_64.so %{buildroot}/%{_datarootdir}/udocker/lib/libfakechroot-Debian-7-x86_64.so
echo "%{_datarootdir}/udocker/lib/libfakechroot-Debian-7-x86_64.so" >> %{_builddir}/%{name}-%{version}/files.lst
install -m 755 -D %{_builddir}/%{name}-%{version}/udocker_dir/lib/libfakechroot-CentOS-7-x86_64.so %{buildroot}/%{_datarootdir}/udocker/lib/libfakechroot-CentOS-7-x86_64.so
echo "%{_datarootdir}/udocker/lib/libfakechroot-CentOS-7-x86_64.so" >> %{_builddir}/%{name}-%{version}/files.lst
install -m 755 -D %{_builddir}/%{name}-%{version}/udocker_dir/lib/libfakechroot-Fedora-25-x86_64.so %{buildroot}/%{_datarootdir}/udocker/lib/libfakechroot-Fedora-25-x86_64.so
echo "%{_datarootdir}/udocker/lib/libfakechroot-Fedora-25-x86_64.so" >> %{_builddir}/%{name}-%{version}/files.lst
install -m 755 -D %{_builddir}/%{name}-%{version}/udocker_dir/lib/libfakechroot-Fedora-25-x86_64.so %{buildroot}/%{_datarootdir}/udocker/lib/libfakechroot-Fedora-x86_64.so
echo "%{_datarootdir}/udocker/lib/libfakechroot-Fedora-x86_64.so" >> %{_builddir}/%{name}-%{version}/files.lst
install -m 755 -D %{_builddir}/%{name}-%{version}/udocker_dir/lib/libfakechroot-Ubuntu-14-x86_64.so %{buildroot}/%{_datarootdir}/udocker/lib/libfakechroot-Ubuntu-14-x86_64.so
echo "%{_datarootdir}/udocker/lib/libfakechroot-Ubuntu-14-x86_64.so" >> %{_builddir}/%{name}-%{version}/files.lst
install -m 755 -D %{_builddir}/%{name}-%{version}/udocker_dir/lib/libfakechroot-Ubuntu-14-x86_64.so %{buildroot}/%{_datarootdir}/udocker/lib/libfakechroot-Ubuntu-x86_64.so
echo "%{_datarootdir}/udocker/lib/libfakechroot-Ubuntu-x86_64.so" >> %{_builddir}/%{name}-%{version}/files.lst
install -m 755 -D %{_builddir}/%{name}-%{version}/udocker_dir/lib/libfakechroot-Ubuntu-14-x86_64.so %{buildroot}/%{_datarootdir}/udocker/lib/libfakechroot-CentOS-x86_64.so
echo "%{_datarootdir}/udocker/lib/libfakechroot-CentOS-x86_64.so" >> %{_builddir}/%{name}-%{version}/files.lst
install -m 755 -D %{_builddir}/%{name}-%{version}/udocker_dir/lib/libfakechroot-Ubuntu-14-x86_64.so %{buildroot}/%{_datarootdir}/udocker/lib/libfakechroot-x86_64.so
echo "%{_datarootdir}/udocker/lib/libfakechroot-x86_64.so" >> %{_builddir}/%{name}-%{version}/files.lst
install -m 755 -D %{_builddir}/%{name}-%{version}/udocker_dir/lib/libfakechroot-Ubuntu-16-x86_64.so %{buildroot}/%{_datarootdir}/udocker/lib/libfakechroot-Ubuntu-16-x86_64.so
echo "%{_datarootdir}/udocker/lib/libfakechroot-Ubuntu-16-x86_64.so" >> %{_builddir}/%{name}-%{version}/files.lst

%clean
rm -rf %{buildroot}

%files -f %{_builddir}/%{name}-%{version}/files.lst
%defattr(-,root,root)

%doc %{name}-%{version}/LICENSE-fakechroot %{name}-%{version}/COPYING-fakechroot %{name}-%{version}/THANKS-fakechroot %{name}-%{version}/COPYING-patchelf %{name}-%{version}/README-patchelf

%changelog
* Wed Nov  8 2017 udocker maintainer <udocker@lip.pt> 1.1.1-1
- Repackaging for udocker 1.1.1
* Tue Sep 12 2017 udocker maintainer <udocker@lip.pt> 1.1.0-1 
- Initial rpm package version

FRENG_SPEC
}

# ##################################################################
# MAIN
# ##################################################################

RELEASE="1"

utils_dir="$(dirname $(readlink -e $0))"
REPO_DIR="$(dirname $utils_dir)"
PARENT_DIR="$(dirname $REPO_DIR)"
BASE_DIR="udocker-freng"
VERSION="$(udocker_version)"

TMP_DIR="/tmp"
RPM_DIR="${HOME}/rpmbuild"
SOURCE_TARBALL="${RPM_DIR}/SOURCES/udocker-freng-${VERSION}.tar.gz"
SPECFILE="${RPM_DIR}/SPECS/udocker-freng.spec"

UDOCKER_TARBALL_URL=$(udocker_tarball_url)

cd $REPO_DIR
sanity_check
setup_env
create_source_tarball
create_specfile
rpmbuild -ba $SPECFILE
