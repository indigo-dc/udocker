#!/bin/bash

# ##################################################################
#
# Build binaries and create udocker tarball
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
    echo "sanity_check"
    if [ ! -f "$REPO_DIR/udocker.py" ] ; then
        echo "$REPO_DIR/udocker.py not found aborting"
        exit 1
    fi

    if [ -e "$BUILD_DIR" ] ; then
        echo "$BUILD_DIR already exists"
    fi
}

udocker_version()
{
    $REPO_DIR/utils/info.py | grep "udocker version:" | cut -f3- '-d '
    # remove candidate version extension
    # $REPO_DIR/utils/info.py | grep "udocker version:" | cut -f3- '-d ' | cut -f1 '-d-'
}

get_proot_static() 
{
    echo "get_proot_static"
    cd "$BUILD_DIR"

    if [ -d "$BUILD_DIR/proot-static-build" ] ; then
        echo "proot static already exists: $BUILD_DIR/proot-static-build"
        return
    fi

    git clone --depth=1 --branch v5.1.1 https://github.com/proot-me/proot-static-build 
    /bin/rm -Rf $BUILD_DIR/proot-static-build/.git
}

prepare_proot_source()
{
    echo "prepare_proot_source : $1"
    local PROOT_SOURCE_DIR="$1"
    cd "$BUILD_DIR"

    if [ -d "$PROOT_SOURCE_DIR" ] ; then
        echo "proot source already exists: $PROOT_SOURCE_DIR"
        return
    fi

    #git clone --branch v5.1.0 --depth=1 https://github.com/proot-me/PRoot 
    git clone --branch udocker-1.1.1 --depth=1 https://github.com/jorge-lip/PRoot.git
    /bin/rm -Rf $BUILD_DIR/PRoot/.git
    /bin/rm -Rf $BUILD_DIR/PRoot/static/care*
    /bin/rm -Rf $BUILD_DIR/PRoot/packages/care*
    /bin/rm -Rf $BUILD_DIR/PRoot/packages/cpio*
    /bin/rm -Rf $BUILD_DIR/PRoot/packages/glib*
    /bin/rm -Rf $BUILD_DIR/PRoot/packages/libarchive*
    /bin/rm -Rf $BUILD_DIR/PRoot/packages/lzo*
    /bin/rm -Rf $BUILD_DIR/PRoot/packages/zlib*
    /bin/rm -Rf $BUILD_DIR/PRoot/packages/proot*
    /bin/rm -Rf $BUILD_DIR/PRoot/packages/uthash-master*
    /bin/mv PRoot "$PROOT_SOURCE_DIR"
}

prepare_patchelf_source()
{
    echo "prepare_patchelf_source : $1"
    local PATCHELF_SOURCE_DIR="$1"
    cd "$BUILD_DIR"

    if [ -d "$PATCHELF_SOURCE_DIR" ] ; then
        echo "patchelf source already exists: $PATCHELF_SOURCE_DIR"
        return
    fi

    # tag for 0.10 not yet in github getting latest
    git clone --depth=1 --branch=0.9 https://github.com/NixOS/patchelf.git
    /bin/mv patchelf "$PATCHELF_SOURCE_DIR"
}

patch_patchelf_source1()
{
    echo "patch_patchelf_source1 : $1"
    local PATCHELF_SOURCE_DIR="$1"

    cd "$PATCHELF_SOURCE_DIR"

    if [ -e "makefile.am.patch" ] ; then
        echo "patch patchelf source1 already applied: $PATCHELF_SOURCE_DIR/makefile.am.patch"
        return
    fi

    cp ${utils_dir}/patchelf_make_static.patch makefile.am.patch
    patch -p1 < makefile.am.patch
}

patch_patchelf_source2()
{
    echo "patch_patchelf_source2 : $1"
    local PATCHELF_SOURCE_DIR="$1"

    cd "$PATCHELF_SOURCE_DIR"

    if [ -e "patchelf.patch" ] ; then
        echo "patch patchelf source1 already applied: $PATCHELF_SOURCE_DIR/patchelf.patch"
        return
    fi

    cp ${utils_dir}/patchelf_code.patch patchelf.patch
    patch -p1 < patchelf.patch
}

prepare_fakechroot_source()
{
    echo "prepare_fakechroot_source : $1"
    local FAKECHROOT_SOURCE_DIR="$1"
    cd "$BUILD_DIR"

    if [ -d "$FAKECHROOT_SOURCE_DIR" ] ; then
        echo "fakechroot source already exists: $FAKECHROOT_SOURCE_DIR"
        return
    fi

    git clone --depth=1 --branch 2.18 https://github.com/dex4er/fakechroot.git
    /bin/rm -Rf $BUILD_DIR/fakechroot/.git
    /bin/mv fakechroot "$FAKECHROOT_SOURCE_DIR"
}

patch_fakechroot_source1()
{
    echo "patch_fakechroot_source1 : $1"
    local FAKECHROOT_SOURCE_DIR="$1"

    cd "$FAKECHROOT_SOURCE_DIR"

    if [ -e "Fakechroot.patch" ] ; then
        echo "patch fakechroot source1 already applied: $FAKECHROOT_SOURCE_DIR/Fakechroot.patch"
        return
    fi

    cp ${utils_dir}/fakechroot_source.patch Fakechroot.patch
    patch -p1 < Fakechroot.patch
}

prepare_runc_source()
{
    echo "prepare_runc_source : $1"
    local RUNC_SOURCE_DIR="$1"
    cd "$BUILD_DIR"

    if [ -d "$RUNC_SOURCE_DIR" ] ; then
        echo "runc source already exists: $RUNC_SOURCE_DIR"
        return
    fi

    git clone --depth=1 https://github.com/opencontainers/runc
    /bin/rm -Rf $BUILD_DIR/runc/.git
    /bin/mv runc "$RUNC_SOURCE_DIR"
}

prepare_package()
{
    echo "prepare_package"
    cd "$BUILD_DIR"
    if [ ! -d "${PACKAGE_DIR}" ] ; then
        /bin/mkdir -p "${PACKAGE_DIR}"
        /bin/mkdir -p "${PACKAGE_DIR}/udocker_dir/bin"
        /bin/mkdir -p "${PACKAGE_DIR}/udocker_dir/lib"
    fi

    #/bin/cp -f "${S_PROOT_DIR}/proot-x86"    "${PACKAGE_DIR}/udocker_dir/bin/"
    #/bin/cp -f "${S_PROOT_DIR}/proot-x86_64" "${PACKAGE_DIR}/udocker_dir/bin/"
    /bin/cp -f "${S_PROOT_DIR}/proot-arm"    "${PACKAGE_DIR}/udocker_dir/bin/"
    /bin/cp -f "${S_PROOT_DIR}/proot-arm64"  "${PACKAGE_DIR}/udocker_dir/bin/"

    echo $(udocker_version) > "${PACKAGE_DIR}/udocker_dir/lib/VERSION"
}

addto_package_simplejson()
{
    echo "addto_package_simplejson"
    cd "${PACKAGE_DIR}/udocker_dir/lib"

    if [ -d "simplejson" ] ; then
        echo "simplejson already exists: $PACKAGE_DIR/simplejson"
        return
    fi

    git clone --depth=1 https://github.com/simplejson/simplejson.git --branch python2.2 
    /bin/rm -Rf simplejson/.git
    /bin/rm -Rf simplejson/docs
    /bin/rm -Rf simplejson/scripts
    /bin/rm -Rf simplejson/simplejson/tests
}

addto_package_udocker()
{
    echo "addto_package_udocker"
    /bin/cp -f -L  "${REPO_DIR}/udocker.py"  "${PACKAGE_DIR}/udocker" 
    (cd ${PACKAGE_DIR}; /bin/ln -s udocker udocker.py)
}

addto_package_other()
{
    echo "addto_package_other"
    /bin/cp -f "${REPO_DIR}/LICENSE"    "${PACKAGE_DIR}/"
    /bin/cp -f "${REPO_DIR}/README.md"  "${PACKAGE_DIR}/"
    /bin/cp -f "${REPO_DIR}/changelog"  "${PACKAGE_DIR}/"
    /bin/cp -R "${REPO_DIR}/doc"        "${PACKAGE_DIR}/udocker_dir/"

    /bin/cp -f "${REPO_DIR}/ansible_install.yaml" "${PACKAGE_DIR}/"
    /bin/cp -f "${REPO_DIR}/setup.py"             "${PACKAGE_DIR}/"
}

# #############################################################################
# Fedora 25
# #############################################################################

fedora25_create_dnf()
{
    echo "fedora25_create_dnf : $1"
    local FILENAME="$1"
    local ARCH="$2"

    cat > "$FILENAME" <<EOF_fedora25_dnf
[main]
gpgcheck=0
installonly_limit=3
clean_requirements_on_remove=True
reposdir=

[fedora]
name=Fedora \$releasever - $ARCH
failovermethod=priority
#baseurl=http://download.fedoraproject.org/pub/fedora/linux/releases/\$releasever/Everything/$ARCH/os/
metalink=https://mirrors.fedoraproject.org/metalink?repo=fedora-\$releasever&arch=$ARCH
enabled=1
metadata_expire=7d
gpgcheck=0
gpgkey=file:///etc/pki/rpm-gpg/RPM-GPG-KEY-fedora-\$releasever-$ARCH
skip_if_unavailable=False

[fedora-debuginfo]
name=Fedora \$releasever - $ARCH - Debug
failovermethod=priority
#baseurl=http://download.fedoraproject.org/pub/fedora/linux/releases/\$releasever/Everything/$ARCH/debug/
metalink=https://mirrors.fedoraproject.org/metalink?repo=fedora-debug-\$releasever&arch=$ARCH
enabled=0
metadata_expire=7d
gpgcheck=0
gpgkey=file:///etc/pki/rpm-gpg/RPM-GPG-KEY-fedora-\$releasever-$ARCH
skip_if_unavailable=False
EOF_fedora25_dnf
}


fedora25_setup()
{
    echo "fedora25_setup : $1"
    local OS_ARCH="$1"
    local OS_NAME="fedora"
    local OS_RELVER="25"
    local OS_ROOTDIR="${BUILD_DIR}/${OS_NAME}_${OS_RELVER}_${OS_ARCH}"

    if [ -x "${OS_ROOTDIR}/bin/gcc" ] ; then
        echo "os already setup : ${OS_ROOTDIR}"
        return
    fi

    SUDO=sudo

    /bin/mkdir -p "${OS_ROOTDIR}/tmp"
    /bin/mkdir -p "${OS_ROOTDIR}/proot"
    /bin/mkdir -p "${OS_ROOTDIR}/proot-static-packages"
    /bin/mkdir -p "${OS_ROOTDIR}/etc/dnf"
    fedora25_create_dnf "${OS_ROOTDIR}/etc/dnf/dnf.conf" "$OS_ARCH"

    $SUDO /usr/bin/dnf -y -c "${OS_ROOTDIR}/etc/dnf/dnf.conf" \
        install  --installroot="$OS_ROOTDIR" --releasever="$OS_RELVER" \
            gcc kernel-devel make libtalloc libtalloc-devel glibc-static glibc-devel tar python gzip zlib

    if [ "$OS_ARCH" = "x86_64" ]; then
        $SUDO /usr/bin/dnf -y -c "${OS_ROOTDIR}/etc/dnf/dnf.conf" \
            install  --installroot="$OS_ROOTDIR" --releasever="$OS_RELVER" \
                autoconf m4 gcc-c++ libstdc++-static automake gawk libtool
    fi

    $SUDO /usr/bin/dnf -y -c "${OS_ROOTDIR}/etc/dnf/dnf.conf" \
        clean packages

    $SUDO /bin/chown -R "$(id -u).$(id -g)" "$OS_ROOTDIR"
    $SUDO /bin/chmod -R u+rw "$OS_ROOTDIR"
}


fedora25_build_proot()
{
    echo "fedora25_build_proot : $1"
    local OS_ARCH="$1"
    local PROOT_SOURCE_DIR="$2"
    local OS_NAME="fedora"
    local OS_RELVER="25"
    local OS_ROOTDIR="${BUILD_DIR}/${OS_NAME}_${OS_RELVER}_${OS_ARCH}"
    local PROOT=""

    if [ "$OS_ARCH" = "i386" ]; then
        PROOT="$S_PROOT_DIR/proot-x86 -q qemu-i386"
    elif [ "$OS_ARCH" = "x86_64" ]; then
        PROOT="$S_PROOT_DIR/proot-x86_64"
    else
        echo "unsupported $OS_NAME architecture: $OS_ARCH"
        exit 2
    fi

    export PROOT_NO_SECCOMP=1

    if [ -x "${PROOT_SOURCE_DIR}/proot-Fedora-25.bin" ] ; then
        echo "proot binary already compiled : ${PROOT_SOURCE_DIR}/proot-Fedora-25.bin"
    else
        # compile PRoot
        $PROOT -r "$OS_ROOTDIR" -b "${PROOT_SOURCE_DIR}:/proot" -w / -b /dev \
                           -b "${S_PROOT_PACKAGES_DIR}:/proot-static-packages"   /bin/bash <<'EOF_fedora25_proot_1'
cd /proot
/bin/rm -f proot-Fedora-25.bin src/proot
# BUILD TALLOC
tar xzvf /proot-static-packages/talloc-2.1.1.tar.gz
cd talloc-2.1.1
./configure
make
cp talloc.h /proot/src
cd bin/default
ar qf libtalloc.a talloc_3.o
cp libtalloc.a /proot/src && make clean
# BUILD PROOT
cd /proot/src
make clean
make
mv proot /proot/proot-Fedora-25.bin
EOF_fedora25_proot_1
    fi

    if [ ! -e "${PROOT_SOURCE_DIR}/proot-Fedora-25.bin" ]; then
        echo "proot compilation failed ${PROOT_SOURCE_DIR}/proot-Fedora-25.bin not found"
        exit 1
    fi
}


fedora25_build_patchelf()
{
    echo "fedora25_build_patchelf : $1"
    local OS_ARCH="$1"
    local PATCHELF_SOURCE_DIR="$2"
    local OS_NAME="fedora"
    local OS_RELVER="25"
    local OS_ROOTDIR="${BUILD_DIR}/${OS_NAME}_${OS_RELVER}_${OS_ARCH}"
    local PROOT=""

    if [ "$OS_ARCH" = "i386" ]; then
        PROOT="$S_PROOT_DIR/proot-x86 -q qemu-i386"
    elif [ "$OS_ARCH" = "x86_64" ]; then
        PROOT="$S_PROOT_DIR/proot-x86_64"
    else
        echo "unsupported $OS_NAME architecture: $OS_ARCH"
        exit 2
    fi

    if [ -x "${PATCHELF_SOURCE_DIR}/patchelf-Fedora-25" ] ; then
        echo "patchelf binary already compiled : ${PATCHELF_SOURCE_DIR}/patchelf-Fedora-25"
        return
    fi

    export PROOT_NO_SECCOMP=1

    patch_patchelf_source1 "${PATCHELF_SOURCE_DIR}"
    patch_patchelf_source2 "${PATCHELF_SOURCE_DIR}"

    # compile patchelf
    set -xv
    (cd ${PATCHELF_SOURCE_DIR} ; bash ./bootstrap.sh)
    $PROOT -r "$OS_ROOTDIR" -b "${PATCHELF_SOURCE_DIR}:/patchelf" -w / -b /dev \
                            /bin/bash <<'EOF_fedora25_patchelf'
cd /patchelf
make clean
# BUILD PATCHELF
#bash bootstrap.sh
bash ./configure
make
cp src/patchelf /patchelf/patchelf-Fedora-25
make clean
EOF_fedora25_patchelf
    set +xv
}

fedora25_build_fakechroot()
{
    echo "fedora25_build_fakechroot : $1"
    local OS_ARCH="$1"
    local FAKECHROOT_SOURCE_DIR="$2"
    local OS_NAME="fedora"
    local OS_RELVER="25"
    local OS_ROOTDIR="${BUILD_DIR}/${OS_NAME}_${OS_RELVER}_${OS_ARCH}"
    local PROOT=""

    if [ "$OS_ARCH" = "i386" ]; then
        PROOT="$S_PROOT_DIR/proot-x86 -q qemu-i386"
    elif [ "$OS_ARCH" = "x86_64" ]; then
        PROOT="$S_PROOT_DIR/proot-x86_64"
    else
        echo "unsupported $OS_NAME architecture: $OS_ARCH"
        exit 2
    fi

    if [ -x "${FAKECHROOT_SOURCE_DIR}/libfakechroot-Fedora-25.so" ] ; then
        echo "fakechroot binary already compiled : ${FAKECHROOT_SOURCE_DIR}/libfakechroot-Fedora-25.so"
        return
    fi

    export PROOT_NO_SECCOMP=1

    patch_fakechroot_source1 "${FAKECHROOT_SOURCE_DIR}"

    # compile fakechroot
    set -xv
    SHELL=/bin/bash CONFIG_SHELL=/bin/bash PATH=/bin:/usr/bin:/sbin:/usr/sbin \
        $PROOT -r "$OS_ROOTDIR" -b "${FAKECHROOT_SOURCE_DIR}:/fakechroot" -w / -b /dev \
            /bin/bash <<'EOF_fedora25_fakechroot'
cd /fakechroot
# BUILD FAKECHROOT
make distclean
bash ./configure
make
cp src/.libs/libfakechroot.so libfakechroot-Fedora-25.so
make clean
EOF_fedora25_fakechroot
    set +xv
}

# #############################################################################
# CentOS 6
# #############################################################################

centos6_create_yum()
{
    echo "centos6_create_yum : $1"
    local FILENAME="$1"
    local ARCH="$2"

    cat > "${FILENAME}" <<'EOF_centos6_yum_conf'
[main]
cachedir=/var/cache/yum/$basearch/$releasever
keepcache=0
debuglevel=2
exactarch=1
obsoletes=1
gpgcheck=0
plugins=1
installonly_limit=5
#logfile=/var/log/yum.log
#bugtracker_url=http://bugs.centos.org/set_project.php?project_id=19&ref=http://bugs.centos.org/bug_report_page.php?category=yum
distroverpkg=centos-release

# PUT YOUR REPOS HERE OR IN separate files named file.repo
# in /etc/yum.repos.d
reposdir=

[base]
name=CentOS-$releasever - Base
mirrorlist=http://mirrorlist.centos.org/?release=$releasever&arch=$basearch&repo=os&infra=$infra
#baseurl=http://mirror.centos.org/centos/$releasever/os/$basearch/
gpgcheck=0
gpgkey=file:///etc/pki/rpm-gpg/RPM-GPG-KEY-CentOS-6

#released updates 
[updates]
name=CentOS-$releasever - Updates
mirrorlist=http://mirrorlist.centos.org/?release=$releasever&arch=$basearch&repo=updates&infra=$infra
#baseurl=http://mirror.centos.org/centos/$releasever/updates/$basearch/
gpgcheck=0
gpgkey=file:///etc/pki/rpm-gpg/RPM-GPG-KEY-CentOS-6

#additional packages that may be useful
[extras]
name=CentOS-$releasever - Extras
mirrorlist=http://mirrorlist.centos.org/?release=$releasever&arch=$basearch&repo=extras&infra=$infra
#baseurl=http://mirror.centos.org/centos/$releasever/extras/$basearch/
gpgcheck=0
gpgkey=file:///etc/pki/rpm-gpg/RPM-GPG-KEY-CentOS-6

#additional packages that extend functionality of existing packages
[centosplus]
name=CentOS-$releasever - Plus
mirrorlist=http://mirrorlist.centos.org/?release=$releasever&arch=$basearch&repo=centosplus&infra=$infra
#baseurl=http://mirror.centos.org/centos/$releasever/centosplus/$basearch/
gpgcheck=0
enabled=0
gpgkey=file:///etc/pki/rpm-gpg/RPM-GPG-KEY-CentOS-6

#contrib - packages by Centos Users
[contrib]
name=CentOS-$releasever - Contrib
mirrorlist=http://mirrorlist.centos.org/?release=$releasever&arch=$basearch&repo=contrib&infra=$infra
#baseurl=http://mirror.centos.org/centos/$releasever/contrib/$basearch/
gpgcheck=0
enabled=0
gpgkey=file:///etc/pki/rpm-gpg/RPM-GPG-KEY-CentOS-6

[base-debuginfo]
name=CentOS-6 - Debuginfo
baseurl=http://debuginfo.centos.org/6/$basearch/
gpgcheck=0
gpgkey=file:///etc/pki/rpm-gpg/RPM-GPG-KEY-CentOS-Debug-6
enabled=0

# EPEL

[epel]
name=Extra Packages for Enterprise Linux 6 - $basearch
#baseurl=http://download.fedoraproject.org/pub/epel/6/$basearch
mirrorlist=https://mirrors.fedoraproject.org/metalink?repo=epel-6&arch=$basearch
failovermethod=priority
enabled=1
gpgcheck=1
gpgkey=file:///etc/pki/rpm-gpg/RPM-GPG-KEY-EPEL-6

[epel-debuginfo]
name=Extra Packages for Enterprise Linux 6 - $basearch - Debug
#baseurl=http://download.fedoraproject.org/pub/epel/6/$basearch/debug
mirrorlist=https://mirrors.fedoraproject.org/metalink?repo=epel-debug-6&arch=$basearch
failovermethod=priority
enabled=0
gpgkey=file:///etc/pki/rpm-gpg/RPM-GPG-KEY-EPEL-6
gpgcheck=1
EOF_centos6_yum_conf
}


centos6_setup()
{
    echo "centos6_setup : $1"
    local OS_ARCH="$1"
    local OS_NAME="centos"
    local OS_RELVER="6"
    local OS_ROOTDIR="${BUILD_DIR}/${OS_NAME}_${OS_RELVER}_${OS_ARCH}"

    if [ -x "${OS_ROOTDIR}/usr/bin/gcc" ] ; then
        echo "os already setup : ${OS_ROOTDIR}"
        return
    fi

    SUDO=sudo

    /bin/mkdir -p "${OS_ROOTDIR}/tmp"
    /bin/mkdir -p "${OS_ROOTDIR}/proot"
    /bin/mkdir -p "${OS_ROOTDIR}/proot-static-packages"
    /bin/mkdir -p "${OS_ROOTDIR}/etc/yum"
    /bin/mkdir -p "${OS_ROOTDIR}/etc/yum.repos.d"
    centos6_create_yum "${OS_ROOTDIR}/etc/yum.conf" "$OS_ARCH"

    $SUDO /usr/bin/yum -y -c "${OS_ROOTDIR}/etc/yum.conf" \
        install  --installroot="$OS_ROOTDIR" --releasever="$OS_RELVER" \
            gcc make libtalloc libtalloc-devel glibc-static glibc-devel tar python gzip zlib

    if [ "$OS_ARCH" = "x86_64" ]; then
        $SUDO /usr/bin/yum -y -c "${OS_ROOTDIR}/etc/yum.conf" \
            install  --installroot="$OS_ROOTDIR" --releasever="$OS_RELVER" \
                autoconf m4 gcc-c++ automake gawk libtool
    fi

    $SUDO /usr/bin/ym -y -c "${OS_ROOTDIR}/etc/yum.conf" \
        clean packages

    $SUDO /bin/chown -R "$(id -u).$(id -g)" "$OS_ROOTDIR"
    $SUDO /bin/chmod -R u+rw "$OS_ROOTDIR"
}


centos6_build_fakechroot()
{
    echo "centos6_build_fakechroot : $1"
    local OS_ARCH="$1"
    local FAKECHROOT_SOURCE_DIR="$2"
    local OS_NAME="centos"
    local OS_RELVER="6"
    local OS_ROOTDIR="${BUILD_DIR}/${OS_NAME}_${OS_RELVER}_${OS_ARCH}"
    local PROOT=""

    if [ "$OS_ARCH" = "i386" ]; then
        PROOT="$S_PROOT_DIR/proot-x86 -q qemu-i386"
    elif [ "$OS_ARCH" = "x86_64" ]; then
        PROOT="$S_PROOT_DIR/proot-x86_64"
    else
        echo "unsupported $OS_NAME architecture: $OS_ARCH"
        exit 2
    fi

    if [ -x "${FAKECHROOT_SOURCE_DIR}/libfakechroot-CentOS-6.so" ] ; then
        echo "fakechroot binary already compiled : ${FAKECHROOT_SOURCE_DIR}/libfakechroot-CentOS-6.so"
        return
    fi

    export PROOT_NO_SECCOMP=1

    # compile fakechroot
    set -xv
    SHELL=/bin/bash CONFIG_SHELL=/bin/bash PATH=/bin:/usr/bin:/sbin:/usr/sbin \
        $PROOT -r "$OS_ROOTDIR" -b "${FAKECHROOT_SOURCE_DIR}:/fakechroot" -w / -b /dev \
            /bin/bash <<'EOF_centos6_fakechroot'
cd /fakechroot
# BUILD FAKECHROOT
make distclean
bash ./configure
make
cp src/.libs/libfakechroot.so libfakechroot-CentOS-6.so
make clean
EOF_centos6_fakechroot
    set +xv
}

# #############################################################################
# CentOS 7
# #############################################################################

centos7_create_yum()
{
    echo "centos7_create_yum : $1"
    local FILENAME="$1"
    local ARCH="$2"

    cat > "${FILENAME}" <<'EOF_centos7_yum_conf'
[main]
cachedir=/var/cache/yum/$basearch/$releasever
keepcache=0
debuglevel=2
exactarch=1
obsoletes=1
gpgcheck=0
plugins=1
installonly_limit=5
#logfile=/var/log/yum.log
#bugtracker_url=http://bugs.centos.org/set_project.php?project_id=19&ref=http://bugs.centos.org/bug_report_page.php?category=yum
distroverpkg=centos-release

# PUT YOUR REPOS HERE OR IN separate files named file.repo
# in /etc/yum.repos.d
reposdir=

[base]
name=CentOS-$releasever - Base
mirrorlist=http://mirrorlist.centos.org/?release=$releasever&arch=$basearch&repo=os&infra=$infra
#baseurl=http://mirror.centos.org/centos/$releasever/os/$basearch/
gpgcheck=0
gpgkey=file:///etc/pki/rpm-gpg/RPM-GPG-KEY-CentOS-7

#released updates 
[updates]
name=CentOS-$releasever - Updates
mirrorlist=http://mirrorlist.centos.org/?release=$releasever&arch=$basearch&repo=updates&infra=$infra
#baseurl=http://mirror.centos.org/centos/$releasever/updates/$basearch/
gpgcheck=0
gpgkey=file:///etc/pki/rpm-gpg/RPM-GPG-KEY-CentOS-7

#additional packages that may be useful
[extras]
name=CentOS-$releasever - Extras
mirrorlist=http://mirrorlist.centos.org/?release=$releasever&arch=$basearch&repo=extras&infra=$infra
#baseurl=http://mirror.centos.org/centos/$releasever/extras/$basearch/
gpgcheck=0
gpgkey=file:///etc/pki/rpm-gpg/RPM-GPG-KEY-CentOS-7

#additional packages that extend functionality of existing packages
[centosplus]
name=CentOS-$releasever - Plus
mirrorlist=http://mirrorlist.centos.org/?release=$releasever&arch=$basearch&repo=centosplus&infra=$infra
#baseurl=http://mirror.centos.org/centos/$releasever/centosplus/$basearch/
gpgcheck=0
enabled=0
gpgkey=file:///etc/pki/rpm-gpg/RPM-GPG-KEY-CentOS-7


# EPEL

[epel]
name=Extra Packages for Enterprise Linux 7 - $basearch
#baseurl=http://download.fedoraproject.org/pub/epel/7/$basearch
mirrorlist=https://mirrors.fedoraproject.org/metalink?repo=epel-7&arch=$basearch
failovermethod=priority
enabled=1
gpgcheck=0
gpgkey=file:///etc/pki/rpm-gpg/RPM-GPG-KEY-EPEL-7

[epel-debuginfo]
name=Extra Packages for Enterprise Linux 7 - $basearch - Debug
#baseurl=http://download.fedoraproject.org/pub/epel/7/$basearch/debug
mirrorlist=https://mirrors.fedoraproject.org/metalink?repo=epel-debug-7&arch=$basearch
failovermethod=priority
enabled=0
gpgkey=file:///etc/pki/rpm-gpg/RPM-GPG-KEY-EPEL-7
gpgcheck=0
EOF_centos7_yum_conf
}


centos7_setup()
{
    echo "centos7_setup : $1"
    local OS_ARCH="$1"
    local OS_NAME="centos"
    local OS_RELVER="7"
    local OS_ROOTDIR="${BUILD_DIR}/${OS_NAME}_${OS_RELVER}_${OS_ARCH}"

    if [ -x "${OS_ROOTDIR}/bin/gcc" ] ; then
        echo "os already setup : ${OS_ROOTDIR}"
        return
    fi

    SUDO=sudo

    /bin/mkdir -p "${OS_ROOTDIR}/tmp"
    /bin/mkdir -p "${OS_ROOTDIR}/proot"
    /bin/mkdir -p "${OS_ROOTDIR}/proot-static-packages"
    /bin/mkdir -p "${OS_ROOTDIR}/etc/yum"
    /bin/mkdir -p "${OS_ROOTDIR}/etc/yum.repos.d"
    centos7_create_yum "${OS_ROOTDIR}/etc/yum.conf" "$OS_ARCH"

    $SUDO /usr/bin/yum -y -c "${OS_ROOTDIR}/etc/yum.conf" \
        install  --installroot="$OS_ROOTDIR" --releasever="$OS_RELVER" \
            gcc make libtalloc libtalloc-devel glibc-static glibc-devel tar python gzip zlib

    if [ "$OS_ARCH" = "x86_64" ]; then
        $SUDO /usr/bin/yum -y -c "${OS_ROOTDIR}/etc/yum.conf" \
            install  --installroot="$OS_ROOTDIR" --releasever="$OS_RELVER" \
                autoconf m4 gcc-c++ automake gawk libtool
    fi

    $SUDO /usr/bin/ym -y -c "${OS_ROOTDIR}/etc/yum.conf" \
        clean packages

    $SUDO /bin/chown -R "$(id -u).$(id -g)" "$OS_ROOTDIR"
    $SUDO /bin/chmod -R u+rw "$OS_ROOTDIR"
}


centos7_build_fakechroot()
{
    echo "centos7_build_fakechroot : $1"
    local OS_ARCH="$1"
    local FAKECHROOT_SOURCE_DIR="$2"
    local OS_NAME="centos"
    local OS_RELVER="7"
    local OS_ROOTDIR="${BUILD_DIR}/${OS_NAME}_${OS_RELVER}_${OS_ARCH}"
    local PROOT=""

    if [ "$OS_ARCH" = "i386" ]; then
        PROOT="$S_PROOT_DIR/proot-x86 -q qemu-i386"
    elif [ "$OS_ARCH" = "x86_64" ]; then
        PROOT="$S_PROOT_DIR/proot-x86_64"
    else
        echo "unsupported $OS_NAME architecture: $OS_ARCH"
        exit 2
    fi

    if [ -x "${FAKECHROOT_SOURCE_DIR}/libfakechroot-CentOS-7.so" ] ; then
        echo "fakechroot binary already compiled : ${FAKECHROOT_SOURCE_DIR}/libfakechroot-CentOS-7.so"
        return
    fi

    export PROOT_NO_SECCOMP=1

    # compile fakechroot
    set -xv
    SHELL=/bin/bash CONFIG_SHELL=/bin/bash PATH=/bin:/usr/bin:/sbin:/usr/sbin \
        $PROOT -r "$OS_ROOTDIR" -b "${FAKECHROOT_SOURCE_DIR}:/fakechroot" -w / -b /dev \
            /bin/bash <<'EOF_centos7_fakechroot'
cd /fakechroot
# BUILD FAKECHROOT
make distclean
bash ./configure
make
cp src/.libs/libfakechroot.so libfakechroot-CentOS-7.so
make clean
EOF_centos7_fakechroot
    set +xv
}


# #############################################################################
# Ubuntu 14.04
# #############################################################################

ubuntu14_setup()
{
    echo "ubuntu14_setup : $1"
    local OS_ARCH="$1"
    local OS_NAME="ubuntu"
    local OS_RELVER="14"
    local OS_ROOTDIR="${BUILD_DIR}/${OS_NAME}_${OS_RELVER}_${OS_ARCH}"

    if [ -x "${OS_ROOTDIR}/usr/lib/gcc" ] ; then
        echo "os already setup : ${OS_ROOTDIR}"
        return
    fi

    SUDO=sudo

    $SUDO debootstrap --arch=$OS_ARCH --variant=buildd trusty $OS_ROOTDIR http://archive.ubuntu.com/ubuntu/

    $SUDO /bin/chown -R "$(id -u).$(id -g)" "$OS_ROOTDIR"
    $SUDO /bin/chmod -R u+rw "$OS_ROOTDIR"
}

ubuntu14_build_fakechroot()
{
    echo "ubuntu14_build_fakechroot : $1"
    local OS_ARCH="$1"
    local FAKECHROOT_SOURCE_DIR="$2"
    local OS_NAME="ubuntu"
    local OS_RELVER="14"
    local OS_ROOTDIR="${BUILD_DIR}/${OS_NAME}_${OS_RELVER}_${OS_ARCH}"
    local PROOT=""

    if [ "$OS_ARCH" = "i386" ]; then
        PROOT="$S_PROOT_DIR/proot-x86 -q qemu-i386"
    elif [ "$OS_ARCH" = "amd64" ]; then
        PROOT="$S_PROOT_DIR/proot-x86_64"
    else
        echo "unsupported $OS_NAME architecture: $OS_ARCH"
        exit 2
    fi

    if [ -x "${FAKECHROOT_SOURCE_DIR}/libfakechroot-Ubuntu-14.so" ] ; then
        echo "fakechroot binary already compiled : ${FAKECHROOT_SOURCE_DIR}/libfakechroot-Ubuntu-14.so"
        return
    fi

    export PROOT_NO_SECCOMP=1

    # compile fakechroot
    set -xv
    SHELL=/bin/bash CONFIG_SHELL=/bin/bash PATH=/bin:/usr/bin:/sbin:/usr/sbin:/usr/lib \
        $PROOT -0 -r "$OS_ROOTDIR" -b "${FAKECHROOT_SOURCE_DIR}:/fakechroot" -w / -b /dev \
            -b /etc/resolv.conf:/etc/resolv.conf /bin/bash <<'EOF_ubuntu14_packages'
apt-get -y update
apt-get -y --no-install-recommends install wget debconf devscripts gnupg nano
apt-get -y update
apt-get -y install locales build-essential gcc make autoconf m4 automake gawk libtool bash
EOF_ubuntu14_packages

    SHELL=/bin/bash CONFIG_SHELL=/bin/bash PATH=/bin:/usr/bin:/sbin:/usr/sbin:/usr/lib \
        $PROOT -r "$OS_ROOTDIR" -b "${FAKECHROOT_SOURCE_DIR}:/fakechroot" -w / -b /dev \
            /bin/bash <<'EOF_ubuntu14_fakechroot'
# BUILD FAKECHROOT
export SHELL=/bin/bash
export CONFIG_SHELL=/bin/bash
export PATH=/bin:/usr/bin:/sbin:/usr/sbin:/usr/lib
cd /fakechroot
make distclean
bash ./configure
make
cp src/.libs/libfakechroot.so libfakechroot-Ubuntu-14.so
make clean
EOF_ubuntu14_fakechroot
    set +xv
}

# #############################################################################
# Ubuntu 16.04
# #############################################################################

ubuntu16_setup()
{
    echo "ubuntu16_setup : $1"
    local OS_ARCH="$1"
    local OS_NAME="ubuntu"
    local OS_RELVER="16"
    local OS_ROOTDIR="${BUILD_DIR}/${OS_NAME}_${OS_RELVER}_${OS_ARCH}"

    if [ -x "${OS_ROOTDIR}/usr/lib/gcc" ] ; then
        echo "os already setup : ${OS_ROOTDIR}"
        return
    fi

    SUDO=sudo

    $SUDO debootstrap --arch=$OS_ARCH --variant=buildd xenial $OS_ROOTDIR http://archive.ubuntu.com/ubuntu/

    $SUDO /bin/chown -R "$(id -u).$(id -g)" "$OS_ROOTDIR"
    $SUDO /bin/chmod -R u+rw "$OS_ROOTDIR"
}

ubuntu16_build_fakechroot()
{
    echo "ubuntu16_build_fakechroot : $1"
    local OS_ARCH="$1"
    local FAKECHROOT_SOURCE_DIR="$2"
    local OS_NAME="ubuntu"
    local OS_RELVER="16"
    local OS_ROOTDIR="${BUILD_DIR}/${OS_NAME}_${OS_RELVER}_${OS_ARCH}"
    local PROOT=""

    if [ "$OS_ARCH" = "i386" ]; then
        PROOT="$S_PROOT_DIR/proot-x86 -q qemu-i386"
    elif [ "$OS_ARCH" = "amd64" ]; then
        PROOT="$S_PROOT_DIR/proot-x86_64"
    else
        echo "unsupported $OS_NAME architecture: $OS_ARCH"
        exit 2
    fi

    if [ -x "${FAKECHROOT_SOURCE_DIR}/libfakechroot-Ubuntu-16.so" ] ; then
        echo "fakechroot binary already compiled : ${FAKECHROOT_SOURCE_DIR}/libfakechroot-Ubuntu-16.so"
        return
    fi

    export PROOT_NO_SECCOMP=1

    # compile fakechroot
    set -xv
    SHELL=/bin/bash CONFIG_SHELL=/bin/bash PATH=/bin:/usr/bin:/sbin:/usr/sbin:/usr/lib \
        $PROOT -0 -r "$OS_ROOTDIR" -b "${FAKECHROOT_SOURCE_DIR}:/fakechroot" -w / -b /dev \
            -b /etc/resolv.conf:/etc/resolv.conf /bin/bash <<'EOF_ubuntu16_packages'
apt-get -y update
apt-get -y --no-install-recommends install wget debconf devscripts gnupg nano
apt-get -y update
apt-get -y install locales build-essential gcc make autoconf m4 automake gawk libtool bash
EOF_ubuntu16_packages

    SHELL=/bin/bash CONFIG_SHELL=/bin/bash PATH=/bin:/usr/bin:/sbin:/usr/sbin:/usr/lib \
        $PROOT -r "$OS_ROOTDIR" -b "${FAKECHROOT_SOURCE_DIR}:/fakechroot" -w / -b /dev \
            /bin/bash <<'EOF_ubuntu16_fakechroot'
# BUILD FAKECHROOT
export SHELL=/bin/bash
export CONFIG_SHELL=/bin/bash
export PATH=/bin:/usr/bin:/sbin:/usr/sbin:/usr/lib
cd /fakechroot
make distclean
bash ./configure
make
cp src/.libs/libfakechroot.so libfakechroot-Ubuntu-16.so
make clean
EOF_ubuntu16_fakechroot
    set +xv
}

ubuntu16_build_runc()
{
    echo "ubuntu16_build_runc : $1"
    local OS_ARCH="$1"
    local RUNC_SOURCE_DIR="$2"
    local OS_NAME="ubuntu"
    local OS_RELVER="16"
    local OS_ROOTDIR="${BUILD_DIR}/${OS_NAME}_${OS_RELVER}_${OS_ARCH}"
    local PROOT=""

    if [ "$OS_ARCH" = "i386" ]; then
        PROOT="$S_PROOT_DIR/proot-x86 -q qemu-i386"
    elif [ "$OS_ARCH" = "amd64" ]; then
        PROOT="$S_PROOT_DIR/proot-x86_64"
    else
        echo "unsupported $OS_NAME architecture: $OS_ARCH"
        exit 2
    fi

    if [ -x "${RUNC_SOURCE_DIR}/runc" ] ; then
        echo "runc binary already compiled : ${RUNC_SOURCE_DIR}/runc"
        return
    fi

    export PROOT_NO_SECCOMP=1

    # compile runc
    mkdir -p ${OS_ROOTDIR}/go/src/github.com/opencontainers
    set -xv
    SHELL=/bin/bash CONFIG_SHELL=/bin/bash PATH=/bin:/usr/bin:/sbin:/usr/sbin:/usr/lib \
        $PROOT -0 -r "$OS_ROOTDIR" -b "${RUNC_SOURCE_DIR}:/go/src/github.com/opencontainers/runc" -w / -b /dev \
            -b /etc/resolv.conf:/etc/resolv.conf /bin/bash <<'EOF_ubuntu16_runc'
apt-get -y update
apt-get -y install golang libseccomp-dev
export GOPATH=/go
cd /go/src/github.com/opencontainers/runc
make static
EOF_ubuntu16_runc

    set +xv
}

# #############################################################################
# TOOLS
# #############################################################################

ostree_delete()
{
    local OS_ARCH="$1"
    local OS_NAME="$2"
    local OS_RELVER="$3"
    local OS_ROOTDIR="${BUILD_DIR}/${OS_NAME}_${OS_RELVER}_${OS_ARCH}"

    echo "ostree_delete : $OS_ROOTDIR"
    [[ "$OS_ROOTDIR" =~ ^$BUILD_DIR/.+ ]] && /bin/rm -Rf "$OS_ROOTDIR"
}

# #############################################################################
# CREATE TARBALL PACKAGE
# #############################################################################

create_package_tarball()
{
    echo "create_package_tarball : $TARBALL_FILE"
    if [ ! -f "${BUILD_DIR}/proot-source-x86/proot-Fedora-25.bin" ] ; then
        echo "ERROR: failed to compile : ${BUILD_DIR}/proot-source-x86/proot-Fedora-25.bin"
        return
    fi
    if [ ! -f "${BUILD_DIR}/proot-source-x86_64/proot-Fedora-25.bin" ] ; then
        echo "ERROR: failed to compile : ${BUILD_DIR}/proot-source-x86_64/proot-Fedora-25.bin"
        return
    fi
    if [ ! -f "${BUILD_DIR}/patchelf-source-x86_64/patchelf-Fedora-25" ] ; then
        echo "ERROR: failed to compile : ${BUILD_DIR}/patchelf-source-x86_64/patchelf-Fedora-25"
        return
    fi
    if [ ! -f "${BUILD_DIR}/fakechroot-source-x86_64/libfakechroot-Fedora-25.so" ] ; then
        echo "ERROR: failed to compile : ${BUILD_DIR}/fakechroot-source-x86_64/libfakechroot-Fedora-25.so"
        return
    fi
    if [ ! -f "${BUILD_DIR}/fakechroot-source-x86_64/libfakechroot-CentOS-6.so" ] ; then
        echo "ERROR: failed to compile : ${BUILD_DIR}/fakechroot-source-x86_64/libfakechroot-CentOS-6.so"
        return
    fi
    if [ ! -f "${BUILD_DIR}/fakechroot-source-x86_64/libfakechroot-CentOS-7.so" ] ; then
        echo "ERROR: failed to compile : ${BUILD_DIR}/fakechroot-source-x86_64/libfakechroot-CentOS-7.so"
        return
    fi
    if [ ! -f "${BUILD_DIR}/fakechroot-source-x86_64/libfakechroot-Ubuntu-14.so" ] ; then
        echo "ERROR: failed to compile : ${BUILD_DIR}/fakechroot-source-x86_64/libfakechroot-Ubuntu-14.so"
        return
    fi
    if [ ! -f "${BUILD_DIR}/fakechroot-source-x86_64/libfakechroot-Ubuntu-16.so" ] ; then
        echo "ERROR: failed to compile : ${BUILD_DIR}/fakechroot-source-x86_64/libfakechroot-Ubuntu-16.so"
        return
    fi
    if [ ! -f "${BUILD_DIR}/runc-source-x86_64/runc" ] ; then
        echo "ERROR: failed to compile : ${BUILD_DIR}/runc-source-x86_64/runc"
        return
    fi

    /bin/cp -f "${BUILD_DIR}/proot-source-x86/proot-Fedora-25.bin" \
               "${PACKAGE_DIR}/udocker_dir/bin/proot-x86"
    /bin/cp -f "${BUILD_DIR}/proot-source-x86_64/proot-Fedora-25.bin" \
               "${PACKAGE_DIR}/udocker_dir/bin/proot-x86_64"
    /bin/cp -f "${BUILD_DIR}/patchelf-source-x86_64/patchelf-Fedora-25" \
               "${PACKAGE_DIR}/udocker_dir/bin/patchelf-x86_64"
    /bin/cp -f "${BUILD_DIR}/fakechroot-source-x86_64/libfakechroot-Fedora-25.so" \
               "${PACKAGE_DIR}/udocker_dir/lib/libfakechroot-Fedora-25-x86_64.so"
    /bin/cp -f "${BUILD_DIR}/fakechroot-source-x86_64/libfakechroot-CentOS-6.so" \
               "${PACKAGE_DIR}/udocker_dir/lib/libfakechroot-CentOS-6-x86_64.so"
    /bin/cp -f "${BUILD_DIR}/fakechroot-source-x86_64/libfakechroot-CentOS-7.so" \
               "${PACKAGE_DIR}/udocker_dir/lib/libfakechroot-CentOS-7-x86_64.so"
    /bin/cp -f "${BUILD_DIR}/fakechroot-source-x86_64/libfakechroot-Ubuntu-14.so" \
               "${PACKAGE_DIR}/udocker_dir/lib/libfakechroot-Ubuntu-14-x86_64.so"
    /bin/cp -f "${BUILD_DIR}/fakechroot-source-x86_64/libfakechroot-Ubuntu-16.so" \
               "${PACKAGE_DIR}/udocker_dir/lib/libfakechroot-Ubuntu-16-x86_64.so"
    /bin/cp -f "${BUILD_DIR}/runc-source-x86_64/runc" \
               "${PACKAGE_DIR}/udocker_dir/bin/runc-x86_64"

    (cd "${PACKAGE_DIR}/udocker_dir/bin"; \
	ln -s proot-x86 proot-x86-4_8_0 ; \
	ln -s proot-x86_64 proot-x86_64-4_8_0)

    (cd "${PACKAGE_DIR}/udocker_dir/lib"; \
        ln -s libfakechroot-Ubuntu-14-x86_64.so libfakechroot-x86_64.so ; \
        ln -s libfakechroot-Ubuntu-14-x86_64.so libfakechroot-Ubuntu-x86_64.so ; \
        ln -s libfakechroot-Fedora-25-x86_64.so libfakechroot-Fedora-x86_64.so ; \
        ln -s libfakechroot-CentOS-6-x86_64.so  libfakechroot-Debian-7-x86_64.so ; \
        ln -s libfakechroot-Ubuntu-16-x86_64.so libfakechroot-CentOS-x86_64.so)

    find "${PACKAGE_DIR}" -type d -exec /bin/chmod u=rwx,og=rx  {} \;
    find "${PACKAGE_DIR}" -type f -exec /bin/chmod u=+r+w,og=r  {} \;
    find "${PACKAGE_DIR}/udocker_dir/bin" -type f -exec /bin/chmod u=rwx,og=rx  {} \;
    /bin/chmod u=rwx,og=rx ${PACKAGE_DIR}/udocker
    /bin/chmod u=rwx,og=rx ${PACKAGE_DIR}/setup.py

    /bin/rm -f $TARBALL_FILE 2>&1 > /dev/null

    cd "$PACKAGE_DIR"
    tar --owner=root --group=root -czvf "$TARBALL_FILE" $(ls -A)
}

# ##################################################################
# MAIN
# ##################################################################

utils_dir="$(dirname $(realpath $0))"
REPO_DIR="$(dirname $utils_dir)"

sanity_check

BUILD_DIR=${HOME}/udocker-build-$(udocker_version)
S_PROOT_DIR="${BUILD_DIR}/proot-static-build/static"
S_PROOT_PACKAGES_DIR="${BUILD_DIR}/proot-static-build/packages"
PACKAGE_DIR="${BUILD_DIR}/package"
TARBALL_FILE="${BUILD_DIR}/udocker-$(udocker_version).tar.gz"


[ ! -e "$BUILD_DIR" ] && /bin/mkdir -p "$BUILD_DIR"

get_proot_static 
prepare_package
addto_package_simplejson
addto_package_udocker
addto_package_other

# #######
# i386
# #######
prepare_proot_source "${BUILD_DIR}/proot-source-x86"
#
fedora25_setup "i386"
fedora25_build_proot "i386" "${BUILD_DIR}/proot-source-x86"
#ostree_delete "i386" "fedora" "25"

# #######
# x86_64
# #######
prepare_proot_source "${BUILD_DIR}/proot-source-x86_64"
prepare_patchelf_source "${BUILD_DIR}/patchelf-source-x86_64"
prepare_fakechroot_source "${BUILD_DIR}/fakechroot-source-x86_64"
prepare_runc_source "${BUILD_DIR}/runc-source-x86_64"
#
fedora25_setup "x86_64"
fedora25_build_proot "x86_64" "${BUILD_DIR}/proot-source-x86_64"
fedora25_build_patchelf "x86_64" "${BUILD_DIR}/patchelf-source-x86_64"
fedora25_build_fakechroot "x86_64" "${BUILD_DIR}/fakechroot-source-x86_64"
#ostree_delete "x86_64" "fedora" "25"
#
centos6_setup "x86_64"
centos6_build_fakechroot "x86_64" "${BUILD_DIR}/fakechroot-source-x86_64"
#ostree_delete "x86_64" "centos" "6"
#
centos7_setup "x86_64"
centos7_build_fakechroot "x86_64" "${BUILD_DIR}/fakechroot-source-x86_64"
#ostree_delete "x86_64" "centos" "7"
#
ubuntu14_setup "amd64"
ubuntu14_build_fakechroot "amd64" "${BUILD_DIR}/fakechroot-source-x86_64"
#ostree_delete "amd64" "ubuntu" "14"

ubuntu16_setup "amd64"
ubuntu16_build_fakechroot "amd64" "${BUILD_DIR}/fakechroot-source-x86_64"
ubuntu16_build_runc "amd64" "${BUILD_DIR}/runc-source-x86_64"
#ostree_delete "amd64" "ubuntu" "16"

create_package_tarball

