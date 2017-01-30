#!/bin/bash

# ##################################################################
#
# Build udocker rpm package
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
    grep "^__version__" "$REPO_DIR/udocker.py" | cut '-d"' -f2 
}

create_source_tarball()
{
    /bin/rm $SOURCE_TARBALL 2> /dev/null
    pushd $PARENT_DIR
    tar czvf $SOURCE_TARBALL \
       $BASE_DIR/doc $BASE_DIR/README.md $BASE_DIR/LICENSE \
       $BASE_DIR/changelog $BASE_DIR/udocker.py
    popd
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
%setup -q -n $BASE_DIR

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

