#!/bin/bash

# ##################################################################
#
# Build udocker-rceng rpm package
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
    grep "^__version__" "$REPO_DIR/udocker.py" | cut '-d"' -f2 | cut '-d-' -f1
}

create_source_tarball()
{
    /bin/rm $SOURCE_TARBALL 2> /dev/null
    pushd $TMP_DIR
    /bin/rm -Rf $BASE_DIR
    /bin/mkdir -p $BASE_DIR/go/src/github.com/opencontainers
    cd $TMP_DIR/$BASE_DIR/go/src/github.com/opencontainers
    git clone --depth=1 https://github.com/opencontainers/runc
    cd $TMP_DIR
    tar czvf $SOURCE_TARBALL $BASE_DIR
    /bin/rm -Rf $BASE_DIR
    popd
}

create_specfile() 
{
    cat - > $SPECFILE <<RCENG_SPEC
Name: udocker-rceng
Summary: udocker-rceng
Version: $VERSION
Release: $RELEASE
Source0: %{name}-%{version}.tar.gz
License: GPLv2
ExclusiveOS: linux
Group: Applications/Emulators
Provides: %{name} = %{version}
URL: https://www.gitbook.com/book/indigo-dc/udocker/details
BuildRoot: %{_tmppath}/%{name}-%{version}-root
BuildRequires: kernel, kernel-devel, fileutils, findutils, bash, tar, gzip, make, golang, binutils
Requires: udocker

%define debug_package %{nil}

%description
Engine to provide containers execution in user mode within udocker using runc https://runc.io/.

%prep
%setup -q -n $BASE_DIR

%build
export GOPATH=\$PWD/go
cd \$GOPATH/src/github.com/opencontainers/runc
make

%install
rm -rf %{buildroot}
BITS=\$(getconf LONG_BIT)
MACH=\$(uname -m)
if [ "\$BITS" = "64" -a "\$MACH" = "x86_64" ]; then
    RUNC="runc-x86_64"
elif [ "\$BITS" = "32" -a "\$MACH" = "x86_64" ]; then
    RUNC="runc-x86"
elif [ "\$BITS" = "32" -a \\( "\$MACH" = "i386" -o "\$MACH" = "i586" -o "\$MACH" = "i686" \\) ]; then
    RUNC="runc-x86"
elif [ "\$BITS" = "64" -a "\${MACH:0:3}" = "arm" ]; then
    RUNC="runc-arm64"
elif [ "\$BITS" = "32" -a "\${MACH:0:3}" = "arm" ]; then
    RUNC="runc-arm"
else
    RUNC="runc"
fi
install -m 755 -D %{_builddir}/%{name}/go/src/github.com/opencontainers/runc/runc %{buildroot}/%{_libexecdir}/udocker/\$RUNC
echo "%{_libexecdir}/udocker/\$RUNC" > %{_builddir}/files.lst

%clean
rm -rf %{buildroot}

%files -f %{_builddir}/files.lst
%defattr(-,root,root)

%doc go/src/github.com/opencontainers/runc/LICENSE go/src/github.com/opencontainers/runc/README.md go/src/github.com/opencontainers/runc/NOTICE

%changelog
* Thu Apr 27 2017 udocker maintainer <udocker@lip.pt> 1.1.0-1
- Initial rpm package version

RCENG_SPEC
}

# ##################################################################
# MAIN
# ##################################################################

RELEASE="1"

utils_dir="$(dirname $(readlink -e $0))"
REPO_DIR="$(dirname $utils_dir)"
PARENT_DIR="$(dirname $REPO_DIR)"
BASE_DIR="udocker-rceng"
VERSION="$(udocker_version)"

TMP_DIR="/tmp"
RPM_DIR="${HOME}/rpmbuild"
SOURCE_TARBALL="${RPM_DIR}/SOURCES/udocker-rceng-${VERSION}.tar.gz"
SPECFILE="${RPM_DIR}/SPECS/udocker-rceng.spec"

cd $REPO_DIR
sanity_check
setup_env
create_source_tarball
create_specfile
rpmbuild -ba $SPECFILE
