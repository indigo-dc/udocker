#!/bin/bash

# ##################################################################
#
# Build udocker package
#
# ##################################################################

sanity_check() 
{
    echo "sanity_check"
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
    pushd $TMP_DIR
    /bin/rm -Rf PRoot
    git clone https://github.com/proot-me/PRoot 
    /bin/mv PRoot $BASE_DIR
    tar czvf $SOURCE_TARBALL $BASE_DIR
    /bin/rm -Rf $BASE_DIR
    popd
}

get_arch()
{
    local BITS="$(getconf LONG_BIT)"
    local MACH="$(uname -m)"
    local PROOT="proot"

    if [ "$BITS" = "64" -a "$MACH" = "x86_64" ]; then
        PROOT="proot-x86_64"
    elif [ "$BITS" = "32" -a "$MACH" = "x86_64" ]; then
        PROOT="proot-x86"
    elif [ "$BITS" = "32" -a \( "$MACH" = "i386" -o "$MACH" = "i586" -o "$MACH" = "i686" \) ]; then
        PROOT="proot-x86"
    elif [ "$BITS" = "64" -a "${MACH:0:3}" = "arm" ]; then
        PROOT="proot-arm64"
    elif [ "$BITS" = "32" -a "${MACH:0:3}" = "arm" ]; then
        PROOT="proot-arm"
    fi
    echo "$PROOT"
}

create_specfile() 
{
    local PROOT="$(get_arch)"
    cat - > $SPECFILE <<PRENG_SPEC
Name: udocker-preng
Summary: udocker-preng
Version: $VERSION
Release: $RELEASE
Source0: %{name}-%{version}.tar.gz
License: GPLv2
ExclusiveOS: linux
Group: Applications/Emulators
Provides: %{name} = %{version}
URL: https://www.gitbook.com/book/indigo-dc/udocker/details
BuildRoot: %{_tmppath}/%{name}-%{version}-root
BuildRequires: kernel, kernel-devel, fileutils, findutils, bash, tar, gzip, make, libtalloc, libtalloc-devel, gcc, binutils, glibc, glibc-devel, glibc-headers
Requires: libtalloc, glibc, udocker

%define debug_package %{nil}

%description
This package provides the binaries to enable containers execution in udocker using proot. udocker is a simple tool to execute Linux Docker containers in user space without requiring root privileges. Enables basic download and execution of docker containers by non-privileged users in Linux systems were docker is not available. It can be used to access and execute the content of docker containers in Linux batch systems and interactive clusters that are managed by other entities such as grid infrastructures or externaly managed batch or interactive systems.

%prep
%setup -q -n $BASE_DIR

%build
make -C src

%install
rm -rf %{buildroot}
BITS=\$(getconf LONG_BIT)
MACH=\$(uname -m)
if [ "\$BITS" = "64" -a "\$MACH" = "x86_64" ]; then
    PROOT="proot-x86_64"
elif [ "\$BITS" = "32" -a "\$MACH" = "x86_64" ]; then
    PROOT="proot-x86"
elif [ "\$BITS" = "32" -a \\( "\$MACH" = "i386" -o "\$MACH" = "i586" -o "\$MACH" = "i686" \\) ]; then
    PROOT="proot-x86"
elif [ "\$BITS" = "64" -a "\${MACH:0:3}" = "arm" ]; then
    PROOT="proot-arm64"
elif [ "\$BITS" = "32" -a "\${MACH:0:3}" = "arm" ]; then
    PROOT="proot-arm"
else
    PROOT="proot"
fi
install -m 755 -D %{_builddir}/%{name}/src/proot %{buildroot}/%{_libexecdir}/udocker/\$PROOT
echo "%{_libexecdir}/udocker/\$PROOT" > %{_builddir}/files.lst

%clean
rm -rf %{buildroot}

%files -f %{_builddir}/files.lst

%doc README.rst AUTHORS COPYING

%changelog
* Mon Jan  9 2017 udocker maintainer <udocker@lip.pt> $VERSION-$RELEASE
- Initial rpm package version

PRENG_SPEC
}

# ##################################################################
# MAIN
# ##################################################################

RELEASE="1"

utils_dir="$(dirname $(readlink -e $0))"
REPO_DIR="$(dirname $utils_dir)"
PARENT_DIR="$(dirname $REPO_DIR)"
BASE_DIR="udocker-preng"
VERSION="$(udocker_version)"

TMP_DIR="/tmp"
RPM_DIR="${HOME}/rpmbuild"
SOURCE_TARBALL="${RPM_DIR}/SOURCES/udocker-preng-${VERSION}.tar.gz"
SPECFILE="${RPM_DIR}/SPECS/udocker-preng.spec"

cd $REPO_DIR
sanity_check
setup_env
create_source_tarball
create_specfile
rpmbuild -ba $SPECFILE
