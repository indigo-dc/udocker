#!/bin/bash

# ##################################################################
#
# Build binaries and create the udocker-englib tarball
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

# The tarball containing the build binaries for udocker is
# maintained separately and has its own version. Each release of
# udocker requires a tarball that is equal or greather than a given
# base version.
# i.e. udocker 1.3.0 requires a tarball >= 1.2.8

# This script produces the following udocker-englib tarball

DEVEL3=$(realpath "$0" | grep -E "devel3|devel4")

TARBALL_VERSION_P3="1.2.11"
TARBALL_VERSION_P2="1.1.11"

sanity_check() 
{
    echo "sanity_check"
    local udocker_script
    if [ -n "$DEVEL3" ]; then
        udocker_script="$REPO_DIR/udocker/maincmd.py"
    else
	udocker_script="$REPO_DIR/udocker.py"
    fi
    if [ ! -f "$udocker_script" ] ; then
        echo "$udocker_script not found aborting"
        exit 1
    fi

    if [ -e "$BUILD_DIR" ] ; then
        echo "$BUILD_DIR already exists"
    fi
}

get_proot_static() 
{
    echo "get_proot_static"
    cd "$BUILD_DIR" || exit 1

    if [ -d "$BUILD_DIR/proot-static-build/static" ] ; then
        echo "proot static already exists: $BUILD_DIR/proot-static-build"
        return
    fi

    git clone --depth=1 --branch v5.1.1 https://github.com/proot-me/proot-static-build 
    /bin/rm -Rf "$BUILD_DIR/proot-static-build/.git"
}

get_udocker_static()
{
    local BUILD_VERSION="$1"

    echo "get_udocker_tools"
    cd "$BUILD_DIR" || exit 1

    if [ -d "$BUILD_DIR/proot-static-build/static" ] ; then
	echo "udocker build directory already exists: $BUILD_DIR/proot-static-build"
	return
    fi
    /bin/mkdir -p "$BUILD_DIR/proot-static-build/static"

    curl "https://raw.githubusercontent.com/jorge-lip/udocker-builds/master/tarballs/udocker-englib-${BUILD_VERSION}.tar.gz" > \
	"$BUILD_DIR/proot-static-build/udocker-englib.tar.gz"
    (cd "$BUILD_DIR/proot-static-build"; tar xvf udocker-englib.tar.gz)
    (cd "$BUILD_DIR/proot-static-build"; /bin/mv udocker_dir/bin/proot-x86-4_8_0 static/proot-x86)
    (cd "$BUILD_DIR/proot-static-build"; /bin/mv udocker_dir/bin/proot-x86_64-4_8_0 static/proot-x86_64)
    (cd "$BUILD_DIR/proot-static-build"; /bin/mv udocker_dir/bin/proot-arm static/proot-arm)
    (cd "$BUILD_DIR/proot-static-build"; /bin/mv udocker_dir/bin/proot-arm64-4_8_0 static/proot-arm64)
    chmod u+rx "$BUILD_DIR/proot-static-build/static/*"
}

get_libtalloc()
{
	echo "get_libtalloc"

        if [ -f "$S_PROOT_PACKAGES_DIR/talloc.tar.gz" ] ; then
            echo "talloc.tar.gz already exists: " \
		    "$S_PROOT_PACKAGES_DIR/talloc.tar.gz"
            return
        fi
	[ ! -d "$S_PROOT_PACKAGES_DIR" ] && /bin/mkdir -p "$S_PROOT_PACKAGES_DIR"

	#June 2013
	#https://www.samba.org/ftp/talloc/talloc-2.1.16.tar.gz
	#https://www.samba.org/ftp/talloc/talloc-2.3.4.tar.gz
	#https://www.samba.org/ftp/talloc/talloc-2.4.0.tar.gz
	curl "https://www.samba.org/ftp/talloc/talloc-2.1.16.tar.gz" > \
	    "$S_PROOT_PACKAGES_DIR/talloc.tar.gz"
}

prepare_proot_source()
{
    echo "prepare_proot_source : $1"
    local PROOT_SOURCE_DIR="$1"
    cd "$BUILD_DIR" || exit 1

    if [ -d "$PROOT_SOURCE_DIR" ] ; then
        echo "proot source already exists: $PROOT_SOURCE_DIR"
        return
    fi

    #git clone --branch v5.1.0 --depth=1 https://github.com/proot-me/PRoot 
    #git clone --branch udocker-2 --depth=1 https://github.com/jorge-lip/proot-udocker.git

    git clone --branch udocker-1 https://github.com/jorge-lip/proot-udocker.git

    #/bin/rm -Rf $BUILD_DIR/proot-udocker/.git
    #/bin/rm -Rf $BUILD_DIR/proot-udocker/static/care*
    #/bin/rm -Rf $BUILD_DIR/proot-udocker/packages/care*
    #/bin/rm -Rf $BUILD_DIR/proot-udocker/packages/cpio*
    #/bin/rm -Rf $BUILD_DIR/proot-udocker/packages/glib*
    #/bin/rm -Rf $BUILD_DIR/proot-udocker/packages/libarchive*
    #/bin/rm -Rf $BUILD_DIR/proot-udocker/packages/lzo*
    #/bin/rm -Rf $BUILD_DIR/proot-udocker/packages/zlib*
    #/bin/rm -Rf $BUILD_DIR/proot-udocker/packages/proot*
    #/bin/rm -Rf $BUILD_DIR/proot-udocker/packages/uthash-master*

    /bin/mv proot-udocker "$PROOT_SOURCE_DIR"
}

prepare_patchelf_source_v1()
{
    echo "prepare_patchelf_source : $1"
    local PATCHELF_SOURCE_DIR="$1"
    cd "$BUILD_DIR" || exit 1

    if [ -d "$PATCHELF_SOURCE_DIR" ] ; then
        echo "patchelf source already exists: $PATCHELF_SOURCE_DIR"
        return
    fi

    git clone --branch udocker-1 --depth=1 https://github.com/jorge-lip/patchelf-udocker.git
    /bin/rm -Rf "$BUILD_DIR/patchelf-udocker/.git"
    /bin/mv patchelf-udocker "$PATCHELF_SOURCE_DIR"
}

prepare_patchelf_source_v2()
{
    echo "prepare_patchelf_source : $1"
    local PATCHELF_SOURCE_DIR="$1"
    cd "$BUILD_DIR" || exit 1

    if [ -d "$PATCHELF_SOURCE_DIR" ] ; then
        echo "patchelf source already exists: $PATCHELF_SOURCE_DIR"
        return
    fi

    git clone --branch udocker-2 --depth=1 https://github.com/jorge-lip/patchelf-udocker-2.git
    /bin/rm -Rf "$BUILD_DIR/patchelf-udocker-2/.git"
    /bin/mv patchelf-udocker-2 "$PATCHELF_SOURCE_DIR"
}

prepare_fakechroot_glibc_source()
{
    echo "prepare_fakechroot_glibc_source : $1"
    local FAKECHROOT_SOURCE_DIR="$1"
    cd "$BUILD_DIR" || exit 1

    if [ -d "$FAKECHROOT_SOURCE_DIR" ] ; then
        echo "fakechroot source already exists: $FAKECHROOT_SOURCE_DIR"
        return
    fi

    #git clone --depth=1 --branch 2.18 https://github.com/dex4er/fakechroot.git
    git clone --branch udocker-3 --depth=1 \
        https://github.com/jorge-lip/libfakechroot-glibc-udocker.git
    /bin/rm -Rf "$BUILD_DIR/libfakechroot-glibc-udocker/.git"
    /bin/mv libfakechroot-glibc-udocker "$FAKECHROOT_SOURCE_DIR"
}

prepare_fakechroot_musl_source()
{
    echo "prepare_fakechroot_musl_source : $1"
    local FAKECHROOT_SOURCE_DIR="$1"
    cd "$BUILD_DIR" || exit 1

    if [ -d "$FAKECHROOT_SOURCE_DIR" ] ; then
        echo "fakechroot source already exists: $FAKECHROOT_SOURCE_DIR"
        return
    fi

    #git clone --depth=1 --branch 2.18 https://github.com/dex4er/fakechroot.git
    git clone --branch udocker-4 --depth=1 \
        https://github.com/jorge-lip/libfakechroot-musl-udocker.git
    /bin/rm -Rf "$BUILD_DIR/libfakechroot-musl-udocker/.git"
    /bin/mv libfakechroot-musl-udocker "$FAKECHROOT_SOURCE_DIR"
}

prepare_runc_source()
{
    echo "prepare_runc_source : $1"
    local RUNC_SOURCE_DIR="$1"
    cd "$BUILD_DIR" || exit 1

    #/bin/rm -Rf $RUNC_SOURCE_DIR
    if [ -d "$RUNC_SOURCE_DIR" ] ; then
        echo "runc source already exists: $RUNC_SOURCE_DIR"
        return
    fi
     
    git clone --depth=1 --branch v1.1.4 https://github.com/opencontainers/runc
    #git clone --depth=1 --branch v1.0.0-rc5 https://github.com/opencontainers/runc
    #/bin/rm -Rf $BUILD_DIR/runc/.git
    /bin/mv runc "$RUNC_SOURCE_DIR"
}

prepare_crun_source()
{
    echo "prepare_crun_source : $1"
    local CRUN_SOURCE_DIR="$1"
    cd "$BUILD_DIR" || exit 1

    if [ -d "$CRUN_SOURCE_DIR" ] ; then
        echo "crun source already exists: $CRUN_SOURCE_DIR"
        return
    fi	

    git clone --recursive --branch 1.6 https://github.com/containers/crun
    #git clone https://github.com/containers/libocispec.git
    #git clone https://github.com/opencontainers/image-spec.git
    #git clone https://github.com/opencontainers/runtime-spec.git
    #(cd "crun"; git checkout ac41e19)
    #(cd "libocispec"; git checkout df96ab4041)
    #/bin/rmdir "crun/libocispec"
    #/bin/rmdir "libocispec/image-spec"
    #/bin/rmdir "libocispec/runtime-spec"

    mv crun "$CRUN_SOURCE_DIR"
    #mv libocispec "$CRUN_SOURCE_DIR/"
    #mv image-spec "$CRUN_SOURCE_DIR/libocispec/"
    #mv runtime-spec "$CRUN_SOURCE_DIR/libocispec/"
}

prepare_package()
{
    echo "prepare_package"
    cd "$BUILD_DIR" || exit 1
    if [ "$1" = "ERASE" ] ; then 
        /bin/rm -f "${PACKAGE_DIR}"/udocker_dir/bin/*
        /bin/rm -f "${PACKAGE_DIR}"/udocker_dir/lib/*
        /bin/rm -f "${PACKAGE_DIR}"/udocker_dir/doc/*
        /bin/rm -f "${PACKAGE_DIR}"/udocker_dir/*
    fi	
    if [ ! -d "${PACKAGE_DIR}" ] ; then
        /bin/mkdir -p "${PACKAGE_DIR}"
        /bin/mkdir -p "${PACKAGE_DIR}/udocker_dir/bin"
        /bin/mkdir -p "${PACKAGE_DIR}/udocker_dir/lib"
        /bin/mkdir -p "${PACKAGE_DIR}/udocker_dir/doc"
    fi
}

addto_package_udocker()
{
    if [ -z "$DEVEL3" ]; then
        echo "addto_package_udocker: add udocker for Python2"
        /bin/cp -f -L  "${REPO_DIR}/udocker.py"  "${PACKAGE_DIR}/udocker"
        (cd "${PACKAGE_DIR}"; /bin/ln -s udocker udocker.py)
    else
	/bin/rm -f "${PACKAGE_DIR}/udocker"
	/bin/rm -f "${PACKAGE_DIR}/udocker.py"
    fi
}

addto_package_simplejson()
{
    echo "addto_package_simplejson"
    cd "${PACKAGE_DIR}/udocker_dir/lib" || exit 1

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

addto_package_other()
{
    echo "addto_package_other"
    /bin/cp -f "${REPO_DIR}/LICENSE"                       "${PACKAGE_DIR}/udocker_dir/doc/LICENSE.udocker"
    /bin/cp -f "${REPO_DIR}/README.md"                     "${PACKAGE_DIR}/udocker_dir/doc/"
    /bin/cp -f "${REPO_DIR}/CHANGELOG.md"                  "${PACKAGE_DIR}/udocker_dir/doc/"
    /bin/cp -R "${REPO_DIR}/docs/udocker.1"                "${PACKAGE_DIR}/udocker_dir/doc/"
    /bin/cp -R "${REPO_DIR}/docs/installation_manual.md"   "${PACKAGE_DIR}/udocker_dir/doc/"
    /bin/cp -R "${REPO_DIR}/docs/reference_card.md"        "${PACKAGE_DIR}/udocker_dir/doc/"
    /bin/cp -R "${REPO_DIR}/docs/user_manual.md"           "${PACKAGE_DIR}/udocker_dir/doc/"

    /bin/cp -f "${REPO_DIR}/ansible_install.yaml"          "${PACKAGE_DIR}/"
    /bin/cp -f "${REPO_DIR}/setup.py"                      "${PACKAGE_DIR}/"

    #/bin/cp -f "${S_PROOT_DIR}/proot-x86"                 "${PACKAGE_DIR}/udocker_dir/bin/"
    #/bin/cp -f "${S_PROOT_DIR}/proot-x86_64"              "${PACKAGE_DIR}/udocker_dir/bin/"
    /bin/cp -f "${S_PROOT_DIR}/proot-arm"                 "${PACKAGE_DIR}/udocker_dir/bin/"
    #/bin/cp -f "${S_PROOT_DIR}/proot-arm64"               "${PACKAGE_DIR}/udocker_dir/bin/"
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
reposdir=NONE

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
        --forcearch="$OS_ARCH" \
        gcc kernel-devel make libtalloc libtalloc-devel glibc-static \
	glibc-devel tar python gzip zlib diffutils file dnf which

    $SUDO /usr/bin/dnf -y -c "${OS_ROOTDIR}/etc/dnf/dnf.conf" \
        install  --installroot="$OS_ROOTDIR" --releasever="$OS_RELVER" \
        --forcearch="$OS_ARCH" \
        autoconf m4 gcc-c++ libstdc++-static automake gawk libtool

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
        #PROOT="$S_PROOT_DIR/proot-x86 -q qemu-i386"
        PROOT="$S_PROOT_DIR/proot-x86"
    elif [ "$OS_ARCH" = "x86_64" ]; then
        #PROOT="$HOME/.udocker/bin/proot-x86_64"
	PROOT="$S_PROOT_DIR/proot-x86_64"
    else
        echo "unsupported $OS_NAME architecture: $OS_ARCH"
        exit 2
    fi

    export PROOT_NO_SECCOMP=1

    if [ -x "${PROOT_SOURCE_DIR}/proot-Fedora-25.bin" ] ; then
        echo "proot binary already compiled : ${PROOT_SOURCE_DIR}/proot-Fedora-25.bin"
    else
        # compile proot
        $PROOT -r "$OS_ROOTDIR" -b "${PROOT_SOURCE_DIR}:/proot" -w / -b /dev \
                           -b "${S_PROOT_PACKAGES_DIR}:/proot-static-packages"   /bin/bash <<'EOF_fedora25_proot_1'
cd /proot
/bin/rm -f proot-Fedora-25.bin src/proot src/libtalloc.a src/talloc.h
/bin/rm -Rf talloc*
# BUILD TALLOC
tar xzvf /proot-static-packages/talloc.tar.gz
cd talloc*
make clean
./configure
make
cp talloc.h /proot/src
cd bin/default
[ -f talloc.c.6.o ] && ar qf libtalloc.a talloc.c.6.o
[ -f talloc.c.5.o -a ! -f libtalloc.a ] && ar qf libtalloc.a talloc.c.5.o
cp libtalloc.a /proot/src && make clean
# BUILD PROOT
cd /proot/src
make clean
make loader.elf
make loader-m32.elf
make build.h
LDFLAGS="-L/proot/usr/src -static" make proot
EOF_fedora25_proot_1
    fi

    if [ -e "${PROOT_SOURCE_DIR}/src/proot" ]; then
        mv "${PROOT_SOURCE_DIR}/src/proot" "${PROOT_SOURCE_DIR}/proot-Fedora-25.bin"
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
        #PROOT="$S_PROOT_DIR/proot-x86 -q qemu-i386"
        PROOT="$S_PROOT_DIR/proot-x86"
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

    # compile patchelf
    set -xv
    (cd "${PATCHELF_SOURCE_DIR}" ; bash ./bootstrap.sh)
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
        #PROOT="$S_PROOT_DIR/proot-x86 -q qemu-i386"
        #PROOT="$BUILD_DIR/proot-source-x86/proot-Fedora-25.bin"
        PROOT="$S_PROOT_DIR/proot-x86"
    elif [ "$OS_ARCH" = "x86_64" ]; then
        #PROOT="$BUILD_DIR/proot-source-x86_64/proot-Fedora-25.bin"
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
# Fedora 29
# #############################################################################

fedora29_create_dnf()
{
    echo "fedora29_create_dnf : $1"
    local FILENAME="$1"
    local ARCH="$2"

    cat > "$FILENAME" <<EOF_fedora29_dnf
[main]
gpgcheck=0
installonly_limit=3
clean_requirements_on_remove=True
reposdir=NONE

[fedora-modular]
name=Fedora Modular \$releasever - $ARCH
failovermethod=priority
#baseurl=http://download.fedoraproject.org/pub/fedora/linux/releases/\$releasever/Modular/$ARCH/os/
metalink=https://mirrors.fedoraproject.org/metalink?repo=fedora-modular-\$releasever&arch=$ARCH
enabled=1
#metadata_expire=7d
repo_gpgcheck=0
type=rpm
gpgcheck=0
gpgkey=file:///etc/pki/rpm-gpg/RPM-GPG-KEY-fedora-\$releasever-$ARCH
skip_if_unavailable=False

[fedora]
name=Fedora \$releasever - $ARCH
failovermethod=priority
#baseurl=http://download.fedoraproject.org/pub/fedora/linux/releases/\$releasever/Everything/$ARCH/os/
metalink=https://mirrors.fedoraproject.org/metalink?repo=fedora-\$releasever&arch=$ARCH
enabled=1
metadata_expire=7d
repo_gpgcheck=0
type=rpm
gpgcheck=0
gpgkey=file:///etc/pki/rpm-gpg/RPM-GPG-KEY-fedora-\$releasever-$ARCH
skip_if_unavailable=False

[updates]
name=Fedora \$releasever - $ARCH - Updates
failovermethod=priority
#baseurl=http://download.fedoraproject.org/pub/fedora/linux/updates/\$releasever/Everything/$ARCH/os/
metalink=https://mirrors.fedoraproject.org/metalink?repo=updates-released-f\$releasever&arch=$ARCH
enabled=1
repo_gpgcheck=0
type=rpm
gpgcheck=0
metadata_expire=6h
gpgkey=file:///etc/pki/rpm-gpg/RPM-GPG-KEY-fedora-\$releasever-$ARCH
skip_if_unavailable=False
EOF_fedora29_dnf
}


fedora29_setup()
{
    echo "fedora29_setup : $1"
    local OS_ARCH="$1"
    local OS_NAME="fedora"
    local OS_RELVER="29"
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
    fedora29_create_dnf "${OS_ROOTDIR}/etc/dnf/dnf.conf" "$OS_ARCH"

    $SUDO /usr/bin/dnf -y -c "${OS_ROOTDIR}/etc/dnf/dnf.conf" \
        install  --installroot="$OS_ROOTDIR" --releasever="$OS_RELVER" --forcearch="$OS_ARCH" \
        gcc kernel-devel make libtalloc libtalloc-devel glibc-static glibc-devel tar python \
	python2 gzip zlib diffutils file dnf which

    $SUDO /usr/bin/dnf -y -c "${OS_ROOTDIR}/etc/dnf/dnf.conf" \
        install  --installroot="$OS_ROOTDIR" --releasever="$OS_RELVER" --forcearch="$OS_ARCH" \
        autoconf m4 gcc-c++ libstdc++-static automake gawk libtool

    if [ "$OS_ARCH" = "aarch64" ]; then
        #PROOT="$BUILD_DIR/proot-source-x86_64/proot-Fedora-25.bin -q qemu-aarch64"
	PROOT="$S_PROOT_DIR/proot-x86_64 -q qemu-aarch64"
        export PROOT_NO_SECCOMP=1
	$PROOT -r "$OS_ROOTDIR" -0 -w / -b /dev -b /etc/resolv.conf "dnf -y reinstall $(rpm -qa)"
    fi

    $SUDO /usr/bin/dnf -y -c "${OS_ROOTDIR}/etc/dnf/dnf.conf" \
        clean packages

    $SUDO /bin/chown -R "$(id -u).$(id -g)" "$OS_ROOTDIR"
    $SUDO /bin/chmod -R u+rw "$OS_ROOTDIR"
}


fedora29_build_proot()
{
    echo "fedora29_build_proot : $1"
    local OS_ARCH="$1"
    local PROOT_SOURCE_DIR="$2"
    local OS_NAME="fedora"
    local OS_RELVER="29"
    local OS_ROOTDIR="${BUILD_DIR}/${OS_NAME}_${OS_RELVER}_${OS_ARCH}"
    local PROOT=""

    if [ "$OS_ARCH" = "i386" ]; then
        #PROOT="$BUILD_DIR/proot-source-x86/proot-Fedora-30.bin"
        PROOT="$S_PROOT_DIR/proot-x86"
    elif [ "$OS_ARCH" = "x86_64" ]; then
        #PROOT="$BUILD_DIR/proot-source-x86_64/proot-Fedora-30.bin"
        PROOT="$S_PROOT_DIR/proot-x86_64"
    else
        echo "unsupported $OS_NAME architecture: $OS_ARCH"
        exit 2
    fi

    export PROOT_NO_SECCOMP=1

    if [ -x "${PROOT_SOURCE_DIR}/proot-Fedora-29.bin" ] ; then
        echo "proot binary already compiled : ${PROOT_SOURCE_DIR}/proot-Fedora-29.bin"
    else
        # compile proot
        $PROOT -r "$OS_ROOTDIR" -b "${PROOT_SOURCE_DIR}:/proot" -w / -b /dev \
                           -b "${S_PROOT_PACKAGES_DIR}:/proot-static-packages"   /bin/bash <<'EOF_fedora29_proot_1'
cd /proot
/bin/rm -f proot-Fedora-29.bin src/proot src/libtalloc.a src/talloc.h
/bin/rm -Rf talloc*
# BUILD TALLOC
tar xzvf /proot-static-packages/talloc.tar.gz
cd talloc*
./configure
make
cp talloc.h /proot/src
cd bin/default
[ -f talloc.c.6.o ] && ar qf libtalloc.a talloc.c.6.o
[ -f talloc.c.5.o -a ! -f libtalloc.a ] && ar qf libtalloc.a talloc.c.5.o
cp libtalloc.a /proot/src && make clean
# BUILD PROOT
cd /proot/src
make clean
make loader.elf
make loader-m32.elf
make build.h
LDFLAGS="-L/proot/usr/src -static" make proot
EOF_fedora29_proot_1
    fi

    if [ -e "${PROOT_SOURCE_DIR}/src/proot" ]; then
        mv "${PROOT_SOURCE_DIR}/src/proot" "${PROOT_SOURCE_DIR}/proot-Fedora-29.bin"
    fi

    if [ ! -e "${PROOT_SOURCE_DIR}/proot-Fedora-29.bin" ]; then
        echo "proot compilation failed ${PROOT_SOURCE_DIR}/proot-Fedora-29.bin not found"
        exit 1
    fi
}


fedora29_build_patchelf()
{
    echo "fedora29_build_patchelf : $1"
    local OS_ARCH="$1"
    local PATCHELF_SOURCE_DIR="$2"
    local OS_NAME="fedora"
    local OS_RELVER="29"
    local OS_ROOTDIR="${BUILD_DIR}/${OS_NAME}_${OS_RELVER}_${OS_ARCH}"
    local PROOT=""

    if [ "$OS_ARCH" = "i386" ]; then
        #PROOT="$S_PROOT_DIR/proot-x86 -q qemu-i386"
        #PROOT="$BUILD_DIR/proot-source-x86/proot-Fedora-30.bin"
        PROOT="$S_PROOT_DIR/proot-x86"
    elif [ "$OS_ARCH" = "x86_64" ]; then
        #PROOT="$S_PROOT_DIR/proot-x86_64"
        #PROOT="$BUILD_DIR/proot-source-x86_64/proot-Fedora-30.bin"
        PROOT="$S_PROOT_DIR/proot-x86_64"
    else
        echo "unsupported $OS_NAME architecture: $OS_ARCH"
        exit 2
    fi

    if [ -x "${PATCHELF_SOURCE_DIR}/patchelf-Fedora-29" ] ; then
        echo "patchelf binary already compiled : ${PATCHELF_SOURCE_DIR}/patchelf-Fedora-29"
        return
    fi

    export PROOT_NO_SECCOMP=1

    # compile patchelf
    set -xv
    (cd "${PATCHELF_SOURCE_DIR}" ; bash ./bootstrap.sh)
    $PROOT -r "$OS_ROOTDIR" -b "${PATCHELF_SOURCE_DIR}:/patchelf" -w / -b /dev \
                            /bin/bash <<'EOF_fedora29_patchelf'
cd /patchelf
make clean
# BUILD PATCHELF
#bash bootstrap.sh
bash ./configure
make
cp src/patchelf /patchelf/patchelf-Fedora-29
make clean
EOF_fedora29_patchelf
    set +xv
}

fedora29_build_fakechroot()
{
    echo "fedora29_build_fakechroot : $1"
    local OS_ARCH="$1"
    local FAKECHROOT_SOURCE_DIR="$2"
    local OS_NAME="fedora"
    local OS_RELVER="29"
    local OS_ROOTDIR="${BUILD_DIR}/${OS_NAME}_${OS_RELVER}_${OS_ARCH}"
    local PROOT=""

    if [ "$OS_ARCH" = "i386" ]; then
        #PROOT="$S_PROOT_DIR/proot-x86 -q qemu-i386"
        #PROOT="$BUILD_DIR/proot-source-x86/proot-Fedora-30.bin"
        PROOT="$S_PROOT_DIR/proot-x86"
    elif [ "$OS_ARCH" = "x86_64" ]; then
        #PROOT="$S_PROOT_DIR/proot-x86_64"
        #PROOT="$BUILD_DIR/proot-source-x86_64/proot-Fedora-30.bin"
        PROOT="$S_PROOT_DIR/proot-x86_64"
    else
        echo "unsupported $OS_NAME architecture: $OS_ARCH"
        exit 2
    fi

    if [ -x "${FAKECHROOT_SOURCE_DIR}/libfakechroot-Fedora-29.so" ] ; then
        echo "fakechroot binary already compiled : ${FAKECHROOT_SOURCE_DIR}/libfakechroot-Fedora-29.so"
        return
    fi

    export PROOT_NO_SECCOMP=1

    # compile fakechroot
    set -xv
    SHELL=/bin/bash CONFIG_SHELL=/bin/bash PATH=/bin:/usr/bin:/sbin:/usr/sbin \
        $PROOT -r "$OS_ROOTDIR" -b "${FAKECHROOT_SOURCE_DIR}:/fakechroot" -w / -b /dev \
            /bin/bash <<'EOF_fedora29_fakechroot'
cd /fakechroot
# BUILD FAKECHROOT
make distclean
bash ./configure
make
cp src/.libs/libfakechroot.so libfakechroot-Fedora-29.so
make clean
EOF_fedora29_fakechroot
    set +xv
}


# #############################################################################
# Fedora 30
# #############################################################################

fedora30_create_dnf()
{
    echo "fedora30_create_dnf : $1"
    local FILENAME="$1"
    local ARCH="$2"

    cat > "$FILENAME" <<EOF_fedora30_dnf
[main]
gpgcheck=0
installonly_limit=3
clean_requirements_on_remove=True
reposdir=NONE

[fedora-modular]
name=Fedora Modular \$releasever - $ARCH
#baseurl=http://download.fedoraproject.org/pub/fedora/linux/releases/\$releasever/Modular/$ARCH/os/
metalink=https://mirrors.fedoraproject.org/metalink?repo=fedora-modular-\$releasever&arch=$ARCH
enabled=1
#metadata_expire=7d
repo_gpgcheck=0
type=rpm
gpgcheck=0
gpgkey=file:///etc/pki/rpm-gpg/RPM-GPG-KEY-fedora-\$releasever-$ARCH
skip_if_unavailable=False

[updates]
name=Fedora \$releasever - $ARCH - Updates
#baseurl=http://download.fedoraproject.org/pub/fedora/linux/updates/\$releasever/Everything/$ARCH/os
metalink=https://mirrors.fedoraproject.org/metalink?repo=updates-released-f\$releasever&arch=$ARCH
enabled=1
repo_gpgcheck=0
type=rpm
gpgcheck=0
metadata_expire=6h
gpgkey=file:///etc/pki/rpm-gpg/RPM-GPG-KEY-fedora-\$releasever-$ARCH
skip_if_unavailable=False

[fedora]
name=Fedora \$releasever - $ARCH
#baseurl=http://download.fedoraproject.org/pub/fedora/linux/releases/\$releasever/Everything/$ARCH/os/
metalink=https://mirrors.fedoraproject.org/metalink?repo=fedora-\$releasever&arch=$ARCH
enabled=1
metadata_expire=7d
repo_gpgcheck=0
type=rpm
gpgcheck=0
gpgkey=file:///etc/pki/rpm-gpg/RPM-GPG-KEY-fedora-\$releasever-$ARCH
skip_if_unavailable=False
EOF_fedora30_dnf
}


fedora30_setup()
{
    echo "fedora30_setup : $1"
    local OS_ARCH="$1"
    local OS_NAME="fedora"
    local OS_RELVER="30"
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
    fedora30_create_dnf "${OS_ROOTDIR}/etc/dnf/dnf.conf" "$OS_ARCH"

    $SUDO /usr/bin/dnf -y -c "${OS_ROOTDIR}/etc/dnf/dnf.conf" \
        install  --installroot="$OS_ROOTDIR" --releasever="$OS_RELVER" \
	--forcearch="$OS_ARCH" \
        gcc kernel-devel make libtalloc libtalloc-devel glibc-static glibc-devel \
	tar python python2 gzip zlib diffutils file dnf which

    $SUDO /usr/bin/dnf -y -c "${OS_ROOTDIR}/etc/dnf/dnf.conf" \
        downgrade  --installroot="$OS_ROOTDIR" --releasever="$OS_RELVER" \
        --forcearch="$OS_ARCH" \
        coreutils-8.31-1.fc30.x86_64 coreutils-common-8.31-1.fc30.x86_64

    $SUDO /usr/bin/dnf -y -c "${OS_ROOTDIR}/etc/dnf/dnf.conf" \
        install  --installroot="$OS_ROOTDIR" --releasever="$OS_RELVER" \
        --forcearch="$OS_ARCH" \
        autoconf m4 gcc-c++ libstdc++-static automake gawk libtool

    $SUDO /usr/bin/dnf -y -c "${OS_ROOTDIR}/etc/dnf/dnf.conf" \
        clean packages

    $SUDO /bin/chown -R "$(id -u).$(id -g)" "$OS_ROOTDIR"
    $SUDO /bin/chmod -R u+rw "$OS_ROOTDIR"
}


fedora30_build_proot()
{
    echo "fedora30_build_proot : $1"
    local OS_ARCH="$1"
    local PROOT_SOURCE_DIR="$2"
    local OS_NAME="fedora"
    local OS_RELVER="30"
    local OS_ROOTDIR="${BUILD_DIR}/${OS_NAME}_${OS_RELVER}_${OS_ARCH}"
    local PROOT=""

    if [ "$OS_ARCH" = "i386" ]; then
        #PROOT="$S_PROOT_DIR/proot-x86 -q qemu-i386"
        #PROOT="$BUILD_DIR/proot-source-x86/proot-Fedora-25.bin"
        PROOT="$S_PROOT_DIR/proot-x86"
    elif [ "$OS_ARCH" = "x86_64" ]; then
        #PROOT="$S_PROOT_DIR/proot-x86_64"
        #PROOT="$BUILD_DIR/proot-source-x86_64/proot-Fedora-25.bin"
        PROOT="$S_PROOT_DIR/proot-x86_64"
    else
        echo "unsupported $OS_NAME architecture: $OS_ARCH"
        exit 2
    fi

    export PROOT_NO_SECCOMP=1

    if [ -x "${PROOT_SOURCE_DIR}/proot-Fedora-30.bin" ] ; then
        echo "proot binary already compiled : ${PROOT_SOURCE_DIR}/proot-Fedora-30.bin"
    else
        # compile proot
        $PROOT -r "$OS_ROOTDIR" -b "${PROOT_SOURCE_DIR}:/proot" -w / -b /dev \
                           -b "${S_PROOT_PACKAGES_DIR}:/proot-static-packages"   /bin/bash <<'EOF_fedora30_proot_1'
cd /proot
/bin/rm -f proot-Fedora-30.bin src/proot src/libtalloc.a src/talloc.h
/bin/rm -Rf talloc*
# BUILD TALLOC
tar xzvf /proot-static-packages/talloc.tar.gz
cd talloc*
./configure
make
cp talloc.h /proot/src
cd bin/default
[ -f talloc.c.6.o ] && ar qf libtalloc.a talloc.c.6.o
[ -f talloc.c.5.o -a ! -f libtalloc.a ] && ar qf libtalloc.a talloc.c.5.o
cp libtalloc.a /proot/src && make clean
# BUILD PROOT
cd /proot/src
make clean
make loader.elf
make loader-m32.elf
make build.h
LDFLAGS="-L/proot/usr/src -static" make proot
EOF_fedora30_proot_1
    fi

    if [ -e "${PROOT_SOURCE_DIR}/src/proot" ]; then
        mv "${PROOT_SOURCE_DIR}/src/proot" "${PROOT_SOURCE_DIR}/proot-Fedora-30.bin"
    fi

    if [ ! -e "${PROOT_SOURCE_DIR}/proot-Fedora-30.bin" ]; then
        echo "proot compilation failed ${PROOT_SOURCE_DIR}/proot-Fedora-30.bin not found"
        exit 1
    fi
}


fedora30_build_patchelf()
{
    echo "fedora30_build_patchelf : $1"
    local OS_ARCH="$1"
    local PATCHELF_SOURCE_DIR="$2"
    local OS_NAME="fedora"
    local OS_RELVER="30"
    local OS_ROOTDIR="${BUILD_DIR}/${OS_NAME}_${OS_RELVER}_${OS_ARCH}"
    local PROOT=""

    if [ "$OS_ARCH" = "i386" ]; then
        #PROOT="$S_PROOT_DIR/proot-x86 -q qemu-i386"
        #PROOT="$BUILD_DIR/proot-source-x86/proot-Fedora-30.bin"
        PROOT="$S_PROOT_DIR/proot-x86"
    elif [ "$OS_ARCH" = "x86_64" ]; then
        #PROOT="$S_PROOT_DIR/proot-x86_64"
        #PROOT="$BUILD_DIR/proot-source-x86_64/proot-Fedora-30.bin"
        PROOT="$S_PROOT_DIR/proot-x86_64"
    else
        echo "unsupported $OS_NAME architecture: $OS_ARCH"
        exit 2
    fi

    if [ -x "${PATCHELF_SOURCE_DIR}/patchelf-Fedora-30" ] ; then
        echo "patchelf binary already compiled : ${PATCHELF_SOURCE_DIR}/patchelf-Fedora-30"
        return
    fi

    export PROOT_NO_SECCOMP=1

    # compile patchelf
    set -xv
    (cd "${PATCHELF_SOURCE_DIR}" ; bash ./bootstrap.sh)
    $PROOT -r "$OS_ROOTDIR" -b "${PATCHELF_SOURCE_DIR}:/patchelf" -w / -b /dev \
                            /bin/bash <<'EOF_fedora30_patchelf'
cd /patchelf
make clean
# BUILD PATCHELF
#bash bootstrap.sh
bash ./configure
make
cp src/patchelf /patchelf/patchelf-Fedora-30
make clean
EOF_fedora30_patchelf
    set +xv
}

fedora30_build_fakechroot()
{
    echo "fedora30_build_fakechroot : $1"
    local OS_ARCH="$1"
    local FAKECHROOT_SOURCE_DIR="$2"
    local OS_NAME="fedora"
    local OS_RELVER="30"
    local OS_ROOTDIR="${BUILD_DIR}/${OS_NAME}_${OS_RELVER}_${OS_ARCH}"
    local PROOT=""

    if [ "$OS_ARCH" = "i386" ]; then
        #PROOT="$S_PROOT_DIR/proot-x86 -q qemu-i386"
        #PROOT="$BUILD_DIR/proot-source-x86/proot-Fedora-30.bin"
        PROOT="$S_PROOT_DIR/proot-x86"
    elif [ "$OS_ARCH" = "x86_64" ]; then
        #PROOT="$S_PROOT_DIR/proot-x86_64"
        #PROOT="$BUILD_DIR/proot-source-x86_64/proot-Fedora-30.bin"
        PROOT="$S_PROOT_DIR/proot-x86_64"
    else
        echo "unsupported $OS_NAME architecture: $OS_ARCH"
        exit 2
    fi

    if [ -x "${FAKECHROOT_SOURCE_DIR}/libfakechroot-Fedora-30.so" ] ; then
        echo "fakechroot binary already compiled : ${FAKECHROOT_SOURCE_DIR}/libfakechroot-Fedora-30.so"
        return
    fi

    export PROOT_NO_SECCOMP=1

    # compile fakechroot
    set -xv
    SHELL=/bin/bash CONFIG_SHELL=/bin/bash PATH=/bin:/usr/bin:/sbin:/usr/sbin \
        $PROOT -r "$OS_ROOTDIR" -b "${FAKECHROOT_SOURCE_DIR}:/fakechroot" -w / -b /dev \
            /bin/bash <<'EOF_fedora30_fakechroot'
cd /fakechroot
# BUILD FAKECHROOT
make distclean
bash ./configure
make
cp src/.libs/libfakechroot.so libfakechroot-Fedora-30.so
make clean
EOF_fedora30_fakechroot
    set +xv
}


# #############################################################################
# Fedora 31
# #############################################################################

fedora31_create_dnf()
{
    echo "fedora31_create_dnf : $1"
    local FILENAME="$1"
    local ARCH="$2"

    cat > "$FILENAME" <<EOF_fedora31_dnf
[main]
gpgcheck=0
sslverify=0
installonly_limit=3
clean_requirements_on_remove=True
reposdir=NONE

[fedora-modular]
name=Fedora Modular \$releasever - $ARCH
#baseurl=http://download.fedoraproject.org/pub/fedora/linux/releases/\$releasever/Modular/$ARCH/os/
metalink=https://mirrors.fedoraproject.org/metalink?repo=fedora-modular-\$releasever&arch=$ARCH
enabled=1
#metadata_expire=7d
repo_gpgcheck=0
type=rpm
gpgcheck=0
gpgkey=file:///etc/pki/rpm-gpg/RPM-GPG-KEY-fedora-\$releasever-$ARCH
skip_if_unavailable=False

[updates]
name=Fedora \$releasever - $ARCH - Updates
#baseurl=http://download.fedoraproject.org/pub/fedora/linux/updates/\$releasever/Everything/$ARCH/os
metalink=https://mirrors.fedoraproject.org/metalink?repo=updates-released-f\$releasever&arch=$ARCH
enabled=1
repo_gpgcheck=0
type=rpm
gpgcheck=0
metadata_expire=6h
gpgkey=file:///etc/pki/rpm-gpg/RPM-GPG-KEY-fedora-\$releasever-$ARCH
skip_if_unavailable=False

[fedora]
name=Fedora \$releasever - $ARCH
#baseurl=http://download.fedoraproject.org/pub/fedora/linux/releases/\$releasever/Everything/$ARCH/os/
metalink=https://mirrors.fedoraproject.org/metalink?repo=fedora-\$releasever&arch=$ARCH
enabled=1
metadata_expire=7d
repo_gpgcheck=0
type=rpm
gpgcheck=0
gpgkey=file:///etc/pki/rpm-gpg/RPM-GPG-KEY-fedora-\$releasever-$ARCH
skip_if_unavailable=False
EOF_fedora31_dnf
}


fedora31_setup()
{
    echo "fedora31_setup : $1"

    local OS_ARCH="$1"
    local OS_NAME="fedora"
    local OS_RELVER="31"
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
    fedora31_create_dnf "${OS_ROOTDIR}/etc/dnf/dnf.conf" "$OS_ARCH"

    $SUDO /usr/bin/dnf -y -c "${OS_ROOTDIR}/etc/dnf/dnf.conf" \
        install  --installroot="$OS_ROOTDIR" --releasever="$OS_RELVER" \
	--forcearch="$OS_ARCH" \
        gcc kernel-devel make libtalloc libtalloc-devel glibc-static glibc-devel tar python \
	python2 gzip zlib diffutils file glibc-headers dnf git which

    #$SUDO /usr/bin/dnf -y -c "${OS_ROOTDIR}/etc/dnf/dnf.conf" \
    #    downgrade  --installroot="$OS_ROOTDIR" --releasever="$OS_RELVER" --forcearch="$OS_ARCH" \
    #        coreutils-8.31-1.fc31.x86_64 coreutils-common-8.31-1.fc31.x86_64

    $SUDO /usr/bin/dnf -y -c "${OS_ROOTDIR}/etc/dnf/dnf.conf" \
        install  --installroot="$OS_ROOTDIR" --releasever="$OS_RELVER" --forcearch="$OS_ARCH" \
	--forcearch="$OS_ARCH" \
        autoconf m4 gcc-c++ libstdc++-static automake gawk libtool xz

    if [ "$OS_ARCH" = "aarch64" ]; then
        $SUDO chown -R "$(id -u):$(id -g)" "$OS_ROOTDIR"
        #PROOT="$S_PROOT_DIR/proot-x86_64 -q qemu-aarch64"
        PROOT="$BUILD_DIR/proot-source-x86_64/proot-Fedora-30.bin -q qemu-aarch64"
        export PROOT_NO_SECCOMP=1
	$PROOT -r "$OS_ROOTDIR" -0 -w / -b /dev -b /etc/resolv.conf /bin/bash <<'EOF_fedora31_reinstall'
dnf -y reinstall --releasever=31 $(rpm -qa)
dnf -y install --releasever=31 autoconf m4 gcc-c++ libstdc++-static automake gawk libtool xz
EOF_fedora31_reinstall
    fi

    $SUDO /usr/bin/dnf -y -c "${OS_ROOTDIR}/etc/dnf/dnf.conf" \
        clean packages

    $SUDO /bin/chown -R "$(id -u).$(id -g)" "$OS_ROOTDIR"
    $SUDO /bin/chmod -R u+rw "$OS_ROOTDIR"
}

fedora31_build_proot()
{
    echo "fedora31_build_proot : $1"
    local OS_ARCH="$1"
    local PROOT_SOURCE_DIR="$2"
    local OS_NAME="fedora"
    local OS_RELVER="31"
    local OS_ROOTDIR="${BUILD_DIR}/${OS_NAME}_${OS_RELVER}_${OS_ARCH}"
    local PROOT=""

    if [ "$OS_ARCH" = "i386" ]; then
        #PROOT="$S_PROOT_DIR/proot-x86 -q qemu-i386"
        #PROOT="$S_PROOT_DIR/proot-x86"
        PROOT="$BUILD_DIR/proot-source-x86/proot-Fedora-30.bin"
    elif [ "$OS_ARCH" = "x86_64" ]; then
        #PROOT="$S_PROOT_DIR/proot-x86_64"
        PROOT="$BUILD_DIR/proot-source-x86_64/proot-Fedora-30.bin"
    elif [ "$OS_ARCH" = "aarch64" ]; then
        #PROOT="$S_PROOT_DIR/proot-x86_64 -q qemu-aarch64"
        PROOT="$BUILD_DIR/proot-source-x86_64/proot-Fedora-30.bin -q qemu-aarch64"
    else
        echo "unsupported $OS_NAME architecture: $OS_ARCH"
        exit 2
    fi

    export PROOT_NO_SECCOMP=1

    if [ -x "${PROOT_SOURCE_DIR}/proot-Fedora-31.bin" ] ; then
        echo "proot binary already compiled : ${PROOT_SOURCE_DIR}/proot-Fedora-31.bin"
    else
        # compile proot
        $PROOT -r "$OS_ROOTDIR" -b "${PROOT_SOURCE_DIR}:/proot" -w / -b /dev \
                           -b "${S_PROOT_PACKAGES_DIR}:/proot-static-packages"   /bin/bash <<'EOF_fedora31_proot_1'
cd /usr/bin
rm python
ln -s python2 python
cd /proot
/bin/rm -f proot-Fedora-31.bin src/proot src/libtalloc.a src/talloc.h
/bin/rm -Rf talloc*
# BUILD TALLOC
tar xzvf /proot-static-packages/talloc.tar.gz
cd talloc*
./configure
make
cp talloc.h /proot/src
cd bin/default
[ -f talloc.c.6.o ] && ar qf libtalloc.a talloc.c.6.o
[ -f talloc.c.5.o -a ! -f libtalloc.a ] && ar qf libtalloc.a talloc.c.5.o
cp libtalloc.a /proot/src && make clean
# BUILD PROOT
cd /proot/src
make clean
make loader.elf
make loader-m32.elf
make build.h
LDFLAGS="-L/proot/usr/src -static" make proot
EOF_fedora31_proot_1
    fi

    if [ -e "${PROOT_SOURCE_DIR}/src/proot" ]; then
        mv "${PROOT_SOURCE_DIR}/src/proot" "${PROOT_SOURCE_DIR}/proot-Fedora-31.bin"
    fi

    if [ ! -e "${PROOT_SOURCE_DIR}/proot-Fedora-31.bin" ]; then
        echo "proot compilation failed ${PROOT_SOURCE_DIR}/proot-Fedora-31.bin not found"
        exit 1
    fi
}


fedora31_build_patchelf()
{
    echo "fedora31_build_patchelf : $1"
    local OS_ARCH="$1"
    local PATCHELF_SOURCE_DIR="$2"
    local OS_NAME="fedora"
    local OS_RELVER="31"
    local OS_ROOTDIR="${BUILD_DIR}/${OS_NAME}_${OS_RELVER}_${OS_ARCH}"
    local PROOT=""

    if [ "$OS_ARCH" = "i386" ]; then
        #PROOT="$S_PROOT_DIR/proot-x86 -q qemu-i386"
        #PROOT="$S_PROOT_DIR/proot-x86"
        PROOT="$BUILD_DIR/proot-source-x86/proot-Fedora-30.bin"
    elif [ "$OS_ARCH" = "x86_64" ]; then
        #PROOT="$S_PROOT_DIR/proot-x86_64"
        PROOT="$BUILD_DIR/proot-source-x86_64/proot-Fedora-30.bin"
    elif [ "$OS_ARCH" = "aarch64" ]; then
        #PROOT="$S_PROOT_DIR/proot-x86_64 -q qemu-aarch64"
        PROOT="$BUILD_DIR/proot-source-x86_64/proot-Fedora-30.bin -q qemu-aarch64"
    elif [ "$OS_ARCH" = "ppc64le" ]; then
        #PROOT="$S_PROOT_DIR/proot-x86_64 -q qemu-ppc64le"
        PROOT="$BUILD_DIR/proot-source-x86_64/proot-Fedora-30.bin -q qemu-ppc64le"
    else
        echo "unsupported $OS_NAME architecture: $OS_ARCH"
        exit 2
    fi

    if [ -x "${PATCHELF_SOURCE_DIR}/patchelf-Fedora-31" ] ; then
        echo "patchelf binary already compiled : ${PATCHELF_SOURCE_DIR}/patchelf-Fedora-31"
        return
    fi

    export PROOT_NO_SECCOMP=1

    # compile patchelf
    set -xv
    (cd "${PATCHELF_SOURCE_DIR}" ; bash ./bootstrap.sh)
    $PROOT -r "$OS_ROOTDIR" -b "${PATCHELF_SOURCE_DIR}:/patchelf" -w / -b /dev \
                            /bin/bash <<'EOF_fedora31_patchelf'
cd /patchelf
make clean
# BUILD PATCHELF
#bash bootstrap.sh
bash ./configure
make
cp src/patchelf /patchelf/patchelf-Fedora-31
make clean
EOF_fedora31_patchelf
    set +xv
}

fedora31_build_fakechroot()
{
    echo "fedora31_build_fakechroot : $1"
    local OS_ARCH="$1"
    local FAKECHROOT_SOURCE_DIR="$2"
    local OS_NAME="fedora"
    local OS_RELVER="31"
    local OS_ROOTDIR="${BUILD_DIR}/${OS_NAME}_${OS_RELVER}_${OS_ARCH}"
    local PROOT=""

    if [ "$OS_ARCH" = "i386" ]; then
        #PROOT="$S_PROOT_DIR/proot-x86 -q qemu-i386"
        #PROOT="$S_PROOT_DIR/proot-x86"
        PROOT="$BUILD_DIR/proot-source-x86/proot-Fedora-30.bin"
    elif [ "$OS_ARCH" = "x86_64" ]; then
        #PROOT="$S_PROOT_DIR/proot-x86_64"
        PROOT="$BUILD_DIR/proot-source-x86_64/proot-Fedora-30.bin"
    elif [ "$OS_ARCH" = "aarch64" ]; then
        #PROOT="$S_PROOT_DIR/proot-x86_64 -q qemu-aarch64"
        PROOT="$BUILD_DIR/proot-source-x86_64/proot-Fedora-30.bin -q qemu-aarch64"
    elif [ "$OS_ARCH" = "ppc64le" ]; then
        #PROOT="$S_PROOT_DIR/proot-x86_64 -q qemu-ppc64le"
        PROOT="$BUILD_DIR/proot-source-x86_64/proot-Fedora-30.bin -q qemu-ppc64le"
    else
        echo "unsupported $OS_NAME architecture: $OS_ARCH"
        exit 2
    fi

    if [ -x "${FAKECHROOT_SOURCE_DIR}/libfakechroot-Fedora-31.so" ] ; then
        echo "fakechroot binary already compiled : ${FAKECHROOT_SOURCE_DIR}/libfakechroot-Fedora-31.so"
        return
    fi

    export PROOT_NO_SECCOMP=1

    # compile fakechroot
    set -xv
    SHELL=/bin/bash CONFIG_SHELL=/bin/bash PATH=/bin:/usr/bin:/sbin:/usr/sbin \
        $PROOT -r "$OS_ROOTDIR" -b "${FAKECHROOT_SOURCE_DIR}:/fakechroot" -w / -b /dev \
            /bin/bash <<'EOF_fedora31_fakechroot'
cd /fakechroot
# BUILD FAKECHROOT
make distclean
bash ./configure
make
cp src/.libs/libfakechroot.so libfakechroot-Fedora-31.so
make clean
EOF_fedora31_fakechroot
    set +xv
}


# #############################################################################
# Fedora 32
# #############################################################################

fedora32_create_dnf()
{
    echo "fedora32_create_dnf : $1"
    local FILENAME="$1"
    local ARCH="$2"

    cat > "$FILENAME" <<EOF_fedora32_dnf
[main]
gpgcheck=0
sslverify=0
installonly_limit=3
clean_requirements_on_remove=True
reposdir=NONE

[fedora-modular]
name=Fedora Modular \$releasever - $ARCH
#baseurl=http://download.fedoraproject.org/pub/fedora/linux/releases/\$releasever/Modular/$ARCH/os/
metalink=https://mirrors.fedoraproject.org/metalink?repo=fedora-modular-\$releasever&arch=$ARCH
enabled=1
#metadata_expire=7d
repo_gpgcheck=0
type=rpm
gpgcheck=0
gpgkey=file:///etc/pki/rpm-gpg/RPM-GPG-KEY-fedora-\$releasever-$ARCH
skip_if_unavailable=False

[updates]
name=Fedora \$releasever - $ARCH - Updates
#baseurl=http://download.fedoraproject.org/pub/fedora/linux/updates/\$releasever/Everything/$ARCH/os
metalink=https://mirrors.fedoraproject.org/metalink?repo=updates-released-f\$releasever&arch=$ARCH
enabled=1
repo_gpgcheck=0
type=rpm
gpgcheck=0
metadata_expire=6h
gpgkey=file:///etc/pki/rpm-gpg/RPM-GPG-KEY-fedora-\$releasever-$ARCH
skip_if_unavailable=False

[fedora]
name=Fedora \$releasever - $ARCH
#baseurl=http://download.fedoraproject.org/pub/fedora/linux/releases/\$releasever/Everything/$ARCH/os/
metalink=https://mirrors.fedoraproject.org/metalink?repo=fedora-\$releasever&arch=$ARCH
enabled=1
metadata_expire=7d
repo_gpgcheck=0
type=rpm
gpgcheck=0
gpgkey=file:///etc/pki/rpm-gpg/RPM-GPG-KEY-fedora-\$releasever-$ARCH
skip_if_unavailable=False
EOF_fedora32_dnf
}


fedora32_setup()
{
    echo "fedora32_setup : $1"
    local OS_ARCH="$1"
    local OS_NAME="fedora"
    local OS_RELVER="32"
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
    fedora32_create_dnf "${OS_ROOTDIR}/etc/dnf/dnf.conf" "$OS_ARCH"

    $SUDO /usr/bin/dnf -y -c "${OS_ROOTDIR}/etc/dnf/dnf.conf" \
        install  --installroot="$OS_ROOTDIR" --releasever="$OS_RELVER" --forcearch="$OS_ARCH" \
            gcc kernel-devel make libtalloc libtalloc-devel glibc-static glibc-devel tar python \
	    python2 gzip zlib diffutils file glibc-headers dnf git which

    #$SUDO /usr/bin/dnf -y -c "${OS_ROOTDIR}/etc/dnf/dnf.conf" \
    #    downgrade  --installroot="$OS_ROOTDIR" --releasever="$OS_RELVER" --forcearch="$OS_ARCH" \
    #        coreutils-8.31-1.fc31.x86_64 coreutils-common-8.31-1.fc31.x86_64

    $SUDO /usr/bin/dnf -y -c "${OS_ROOTDIR}/etc/dnf/dnf.conf" \
        install  --installroot="$OS_ROOTDIR" --releasever="$OS_RELVER" --forcearch="$OS_ARCH" \
        autoconf m4 gcc-c++ libstdc++-static automake gawk libtool

    if [ "$OS_ARCH" = "aarch64" ]; then
        $SUDO chown -R "$(id -u):$(id -g)" "$OS_ROOTDIR"
        #PROOT="$S_PROOT_DIR/proot-x86_64 -q qemu-aarch64"
        PROOT="$BUILD_DIR/proot-source-x86_64/proot-Fedora-30.bin -q qemu-aarch64"
        export PROOT_NO_SECCOMP=1
	$PROOT -r "$OS_ROOTDIR" -0 -w / -b /dev -b /etc/resolv.conf /bin/bash <<'EOF_fedora32_reinstall'
dnf -y reinstall $(rpm -qa)
EOF_fedora32_reinstall
    fi

    $SUDO /usr/bin/dnf -y -c "${OS_ROOTDIR}/etc/dnf/dnf.conf" \
        clean packages

    $SUDO /bin/chown -R "$(id -u).$(id -g)" "$OS_ROOTDIR"
    $SUDO /bin/chmod -R u+rw "$OS_ROOTDIR"
}

fedora32_build_proot()
{
    echo "fedora32_build_proot : $1"
    local OS_ARCH="$1"
    local PROOT_SOURCE_DIR="$2"
    local OS_NAME="fedora"
    local OS_RELVER="32"
    local OS_ROOTDIR="${BUILD_DIR}/${OS_NAME}_${OS_RELVER}_${OS_ARCH}"
    local PROOT=""

    if [ "$OS_ARCH" = "i386" ]; then
        #PROOT="$S_PROOT_DIR/proot-x86 -q qemu-i386"
        #PROOT="$S_PROOT_DIR/proot-x86"
        PROOT="$BUILD_DIR/proot-source-x86/proot-Fedora-30.bin"
    elif [ "$OS_ARCH" = "x86_64" ]; then
        #PROOT="$S_PROOT_DIR/proot-x86_64"
        PROOT="$BUILD_DIR/proot-source-x86_64/proot-Fedora-30.bin"
    elif [ "$OS_ARCH" = "aarch64" ]; then
        #PROOT="$S_PROOT_DIR/proot-x86_64 -q qemu-aarch64"
        PROOT="$BUILD_DIR/proot-source-x86_64/proot-Fedora-30.bin -q qemu-aarch64"
    else
        echo "unsupported $OS_NAME architecture: $OS_ARCH"
        exit 2
    fi

    export PROOT_NO_SECCOMP=1

    if [ -x "${PROOT_SOURCE_DIR}/proot-Fedora-32.bin" ] ; then
        echo "proot binary already compiled : ${PROOT_SOURCE_DIR}/proot-Fedora-32.bin"
    else
        # compile proot
        $PROOT -r "$OS_ROOTDIR" -b "${PROOT_SOURCE_DIR}:/proot" -w / -b /dev \
                           -b "${S_PROOT_PACKAGES_DIR}:/proot-static-packages"   /bin/bash <<'EOF_fedora32_proot_1'
cd /usr/bin
rm python
ln -s python2 python
cd /proot
/bin/rm -f proot-Fedora-32.bin src/proot src/libtalloc.a src/talloc.h
/bin/rm -Rf talloc*
# BUILD TALLOC
tar xzvf /proot-static-packages/talloc.tar.gz
cd talloc*
./configure
make
cp talloc.h /proot/src
cd bin/default
[ -f talloc.c.6.o ] && ar qf libtalloc.a talloc.c.6.o
[ -f talloc.c.5.o -a ! -f libtalloc.a ] && ar qf libtalloc.a talloc.c.5.o
cp libtalloc.a /proot/src && make clean
# BUILD PROOT
cd /proot/src
make clean
make loader.elf
make loader-m32.elf
make build.h
LDFLAGS="-L/proot/usr/src -static" make proot
EOF_fedora32_proot_1
    fi

    if [ -e "${PROOT_SOURCE_DIR}/src/proot" ]; then
        mv "${PROOT_SOURCE_DIR}/src/proot" "${PROOT_SOURCE_DIR}/proot-Fedora-32.bin"
    fi

    if [ ! -e "${PROOT_SOURCE_DIR}/proot-Fedora-32.bin" ]; then
        echo "proot compilation failed ${PROOT_SOURCE_DIR}/proot-Fedora-32.bin not found"
        exit 1
    fi
}


fedora32_build_patchelf()
{
    echo "fedora32_build_patchelf : $1"
    local OS_ARCH="$1"
    local PATCHELF_SOURCE_DIR="$2"
    local OS_NAME="fedora"
    local OS_RELVER="32"
    local OS_ROOTDIR="${BUILD_DIR}/${OS_NAME}_${OS_RELVER}_${OS_ARCH}"
    local PROOT=""

    if [ "$OS_ARCH" = "i386" ]; then
        #PROOT="$S_PROOT_DIR/proot-x86 -q qemu-i386"
        #PROOT="$S_PROOT_DIR/proot-x86"
        PROOT="$BUILD_DIR/proot-source-x86/proot-Fedora-30.bin"
    elif [ "$OS_ARCH" = "x86_64" ]; then
        #PROOT="$S_PROOT_DIR/proot-x86_64"
        PROOT="$BUILD_DIR/proot-source-x86_64/proot-Fedora-30.bin"
    elif [ "$OS_ARCH" = "aarch64" ]; then
        #PROOT="$S_PROOT_DIR/proot-x86_64 -q qemu-aarch64"
        PROOT="$BUILD_DIR/proot-source-x86_64/proot-Fedora-30.bin -q qemu-aarch64"
    elif [ "$OS_ARCH" = "ppc64le" ]; then
        #PROOT="$S_PROOT_DIR/proot-x86_64 -q qemu-ppc64le"
        PROOT="$BUILD_DIR/proot-source-x86_64/proot-Fedora-30.bin -q qemu-ppc64le"
    else
        echo "unsupported $OS_NAME architecture: $OS_ARCH"
        exit 2
    fi

    if [ -x "${PATCHELF_SOURCE_DIR}/patchelf-Fedora-32" ] ; then
        echo "patchelf binary already compiled : ${PATCHELF_SOURCE_DIR}/patchelf-Fedora-32"
        return
    fi

    export PROOT_NO_SECCOMP=1

    # compile patchelf
    set -xv
    (cd "${PATCHELF_SOURCE_DIR}" ; bash ./bootstrap.sh)
    $PROOT -r "$OS_ROOTDIR" -b "${PATCHELF_SOURCE_DIR}:/patchelf" -w / -b /dev \
                            /bin/bash <<'EOF_fedora32_patchelf'
cd /patchelf
make clean
# BUILD PATCHELF
#bash bootstrap.sh
bash ./configure
make
cp src/patchelf /patchelf/patchelf-Fedora-32
make clean
EOF_fedora32_patchelf
    set +xv
}

fedora32_build_fakechroot()
{
    echo "fedora32_build_fakechroot : $1"
    local OS_ARCH="$1"
    local FAKECHROOT_SOURCE_DIR="$2"
    local OS_NAME="fedora"
    local OS_RELVER="32"
    local OS_ROOTDIR="${BUILD_DIR}/${OS_NAME}_${OS_RELVER}_${OS_ARCH}"
    local PROOT=""

    if [ "$OS_ARCH" = "i386" ]; then
        #PROOT="$S_PROOT_DIR/proot-x86 -q qemu-i386"
        #PROOT="$S_PROOT_DIR/proot-x86"
        PROOT="$BUILD_DIR/proot-source-x86/proot-Fedora-30.bin"
    elif [ "$OS_ARCH" = "x86_64" ]; then
        #PROOT="$S_PROOT_DIR/proot-x86_64"
        PROOT="$BUILD_DIR/proot-source-x86_64/proot-Fedora-30.bin"
    elif [ "$OS_ARCH" = "aarch64" ]; then
        #PROOT="$S_PROOT_DIR/proot-x86_64 -q qemu-aarch64"
        PROOT="$BUILD_DIR/proot-source-x86_64/proot-Fedora-30.bin -q qemu-aarch64"
    elif [ "$OS_ARCH" = "ppc64le" ]; then
        #PROOT="$S_PROOT_DIR/proot-x86_64 -q qemu-ppc64le"
        PROOT="$BUILD_DIR/proot-source-x86_64/proot-Fedora-30.bin -q qemu-ppc64le"
    else
        echo "unsupported $OS_NAME architecture: $OS_ARCH"
        exit 2
    fi

    if [ -x "${FAKECHROOT_SOURCE_DIR}/libfakechroot-Fedora-32.so" ] ; then
        echo "fakechroot binary already compiled : ${FAKECHROOT_SOURCE_DIR}/libfakechroot-Fedora-32.so"
        return
    fi

    export PROOT_NO_SECCOMP=1

    # compile fakechroot
    set -xv
    SHELL=/bin/bash CONFIG_SHELL=/bin/bash PATH=/bin:/usr/bin:/sbin:/usr/sbin \
        $PROOT -r "$OS_ROOTDIR" -b "${FAKECHROOT_SOURCE_DIR}:/fakechroot" -w / -b /dev \
            /bin/bash <<'EOF_fedora32_fakechroot'
cd /fakechroot
# BUILD FAKECHROOT
make distclean
bash ./configure
make
cp src/.libs/libfakechroot.so libfakechroot-Fedora-32.so
make clean
EOF_fedora32_fakechroot
    set +xv
}


# #############################################################################
# Fedora 33
# #############################################################################

fedora33_create_dnf()
{
    echo "fedora33_create_dnf : $1"
    local FILENAME="$1"
    local ARCH="$2"

    cat > "$FILENAME" <<EOF_fedora33_dnf
[main]
gpgcheck=0
sslverify=0
installonly_limit=3
clean_requirements_on_remove=True
reposdir=NONE

[fedora-modular]
name=Fedora Modular \$releasever - $ARCH
#baseurl=http://download.fedoraproject.org/pub/fedora/linux/releases/\$releasever/Modular/$ARCH/os/
metalink=https://mirrors.fedoraproject.org/metalink?repo=fedora-modular-\$releasever&arch=$ARCH
enabled=1
#metadata_expire=7d
repo_gpgcheck=0
type=rpm
gpgcheck=0
gpgkey=file:///etc/pki/rpm-gpg/RPM-GPG-KEY-fedora-\$releasever-$ARCH
skip_if_unavailable=False

[updates]
name=Fedora \$releasever - $ARCH - Updates
#baseurl=http://download.fedoraproject.org/pub/fedora/linux/updates/\$releasever/Everything/$ARCH/os
metalink=https://mirrors.fedoraproject.org/metalink?repo=updates-released-f\$releasever&arch=$ARCH
enabled=1
repo_gpgcheck=0
type=rpm
gpgcheck=0
metadata_expire=6h
gpgkey=file:///etc/pki/rpm-gpg/RPM-GPG-KEY-fedora-\$releasever-$ARCH
skip_if_unavailable=False

[fedora]
name=Fedora \$releasever - $ARCH
#baseurl=http://download.fedoraproject.org/pub/fedora/linux/releases/\$releasever/Everything/$ARCH/os/
metalink=https://mirrors.fedoraproject.org/metalink?repo=fedora-\$releasever&arch=$ARCH
enabled=1
metadata_expire=7d
repo_gpgcheck=0
type=rpm
gpgcheck=0
gpgkey=file:///etc/pki/rpm-gpg/RPM-GPG-KEY-fedora-\$releasever-$ARCH
skip_if_unavailable=False
EOF_fedora33_dnf
}


fedora33_setup()
{
    echo "fedora33_setup : $1"
    local OS_ARCH="$1"
    local OS_NAME="fedora"
    local OS_RELVER="33"
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
    fedora33_create_dnf "${OS_ROOTDIR}/etc/dnf/dnf.conf" "$OS_ARCH"

    $SUDO /usr/bin/dnf -y -c "${OS_ROOTDIR}/etc/dnf/dnf.conf" \
        install  --installroot="$OS_ROOTDIR" --releasever="$OS_RELVER" --forcearch="$OS_ARCH" \
            gcc kernel-devel make libtalloc libtalloc-devel glibc-static glibc-devel tar python \
	    python2 gzip zlib diffutils file glibc-headers dnf git which

    #$SUDO /usr/bin/dnf -y -c "${OS_ROOTDIR}/etc/dnf/dnf.conf" \
    #    downgrade  --installroot="$OS_ROOTDIR" --releasever="$OS_RELVER" --forcearch="$OS_ARCH" \
    #        coreutils-8.31-1.fc31.x86_64 coreutils-common-8.31-1.fc31.x86_64

    $SUDO /usr/bin/dnf -y -c "${OS_ROOTDIR}/etc/dnf/dnf.conf" \
        install  --installroot="$OS_ROOTDIR" --releasever="$OS_RELVER" --forcearch="$OS_ARCH" \
        autoconf m4 gcc-c++ libstdc++-static automake gawk libtool

    if [ "$OS_ARCH" = "aarch64" ]; then
        $SUDO chown -R "$(id -u):$(id -g)" "$OS_ROOTDIR"
	#PROOT="$S_PROOT_DIR/proot-x86_64 -q qemu-aarch64"
        PROOT="$BUILD_DIR/proot-source-x86_64/proot-Fedora-30.bin -q qemu-aarch64"
        export PROOT_NO_SECCOMP=1
	$PROOT -r "$OS_ROOTDIR" -0 -w / -b /dev -b /etc/resolv.conf /bin/bash <<'EOF_fedora33_reinstall'
dnf -y reinstall $(rpm -qa)
EOF_fedora33_reinstall
    fi

    $SUDO /usr/bin/dnf -y -c "${OS_ROOTDIR}/etc/dnf/dnf.conf" \
        clean packages

    $SUDO /bin/chown -R "$(id -u).$(id -g)" "$OS_ROOTDIR"
    $SUDO /bin/chmod -R u+rw "$OS_ROOTDIR"
}

fedora33_build_proot()
{
    echo "fedora33_build_proot : $1"
    local OS_ARCH="$1"
    local PROOT_SOURCE_DIR="$2"
    local OS_NAME="fedora"
    local OS_RELVER="33"
    local OS_ROOTDIR="${BUILD_DIR}/${OS_NAME}_${OS_RELVER}_${OS_ARCH}"
    local PROOT=""

    if [ "$OS_ARCH" = "i386" ]; then
        #PROOT="$S_PROOT_DIR/proot-x86 -q qemu-i386"
        #PROOT="$S_PROOT_DIR/proot-x86"
        PROOT="$BUILD_DIR/proot-source-x86/proot-Fedora-30.bin"
    elif [ "$OS_ARCH" = "x86_64" ]; then
        #PROOT="$S_PROOT_DIR/proot-x86_64"
        PROOT="$BUILD_DIR/proot-source-x86_64/proot-Fedora-30.bin"
    elif [ "$OS_ARCH" = "aarch64" ]; then
        #PROOT="$S_PROOT_DIR/proot-x86_64 -q qemu-aarch64"
        PROOT="$BUILD_DIR/proot-source-x86_64/proot-Fedora-30.bin -q qemu-aarch64"
    else
        echo "unsupported $OS_NAME architecture: $OS_ARCH"
        exit 2
    fi

    export PROOT_NO_SECCOMP=1

    if [ -x "${PROOT_SOURCE_DIR}/proot-Fedora-33.bin" ] ; then
        echo "proot binary already compiled : ${PROOT_SOURCE_DIR}/proot-Fedora-33.bin"
    else
        # compile proot
        $PROOT -r "$OS_ROOTDIR" -b "${PROOT_SOURCE_DIR}:/proot" -w / -b /dev \
                           -b "${S_PROOT_PACKAGES_DIR}:/proot-static-packages"   /bin/bash <<'EOF_fedora33_proot_1'
cd /usr/bin
rm python
ln -s python2 python
cd /proot
/bin/rm -f proot-Fedora-33.bin src/proot src/libtalloc.a src/talloc.h
/bin/rm -Rf talloc*
# BUILD TALLOC
tar xzvf /proot-static-packages/talloc.tar.gz
cd talloc*
./configure
make
cp talloc.h /proot/src
cd bin/default
[ -f talloc.c.6.o ] && ar qf libtalloc.a talloc.c.6.o
[ -f talloc.c.5.o -a ! -f libtalloc.a ] && ar qf libtalloc.a talloc.c.5.o
cp libtalloc.a /proot/src && make clean
# BUILD PROOT
cd /proot/src
make clean
make loader.elf
make loader-m32.elf
make build.h
LDFLAGS="-L/proot/usr/src -static" make proot
EOF_fedora33_proot_1
    fi

    if [ -e "${PROOT_SOURCE_DIR}/src/proot" ]; then
        mv "${PROOT_SOURCE_DIR}/src/proot" "${PROOT_SOURCE_DIR}/proot-Fedora-33.bin"
    fi

    if [ ! -e "${PROOT_SOURCE_DIR}/proot-Fedora-33.bin" ]; then
        echo "proot compilation failed ${PROOT_SOURCE_DIR}/proot-Fedora-33.bin not found"
        exit 1
    fi
}


fedora33_build_patchelf()
{
    echo "fedora33_build_patchelf : $1"
    local OS_ARCH="$1"
    local PATCHELF_SOURCE_DIR="$2"
    local OS_NAME="fedora"
    local OS_RELVER="33"
    local OS_ROOTDIR="${BUILD_DIR}/${OS_NAME}_${OS_RELVER}_${OS_ARCH}"
    local PROOT=""

    if [ "$OS_ARCH" = "i386" ]; then
        #PROOT="$S_PROOT_DIR/proot-x86 -q qemu-i386"
        #PROOT="$S_PROOT_DIR/proot-x86"
        PROOT="$BUILD_DIR/proot-source-x86/proot-Fedora-30.bin"
    elif [ "$OS_ARCH" = "x86_64" ]; then
        #PROOT="$S_PROOT_DIR/proot-x86_64"
        PROOT="$BUILD_DIR/proot-source-x86_64/proot-Fedora-30.bin"
    elif [ "$OS_ARCH" = "aarch64" ]; then
        #PROOT="$S_PROOT_DIR/proot-x86_64 -q qemu-aarch64"
        PROOT="$BUILD_DIR/proot-source-x86_64/proot-Fedora-30.bin -q qemu-aarch64"
    elif [ "$OS_ARCH" = "ppc64le" ]; then
        #PROOT="$S_PROOT_DIR/proot-x86_64 -q qemu-ppc64le"
        PROOT="$BUILD_DIR/proot-source-x86_64/proot-Fedora-30.bin -q qemu-ppc64le"
    else
        echo "unsupported $OS_NAME architecture: $OS_ARCH"
        exit 2
    fi

    if [ -x "${PATCHELF_SOURCE_DIR}/patchelf-Fedora-33" ] ; then
        echo "patchelf binary already compiled : ${PATCHELF_SOURCE_DIR}/patchelf-Fedora-33"
        return
    fi

    export PROOT_NO_SECCOMP=1

    # compile patchelf
    set -xv
    (cd "${PATCHELF_SOURCE_DIR}" ; bash ./bootstrap.sh)
    $PROOT -r "$OS_ROOTDIR" -b "${PATCHELF_SOURCE_DIR}:/patchelf" -w / -b /dev \
                            /bin/bash <<'EOF_fedora33_patchelf'
cd /patchelf
make clean
# BUILD PATCHELF
#bash bootstrap.sh
bash ./configure
make
cp src/patchelf /patchelf/patchelf-Fedora-33
make clean
EOF_fedora33_patchelf
    set +xv
}

fedora33_build_fakechroot()
{
    echo "fedora33_build_fakechroot : $1"
    local OS_ARCH="$1"
    local FAKECHROOT_SOURCE_DIR="$2"
    local OS_NAME="fedora"
    local OS_RELVER="33"
    local OS_ROOTDIR="${BUILD_DIR}/${OS_NAME}_${OS_RELVER}_${OS_ARCH}"
    local PROOT=""

    if [ "$OS_ARCH" = "i386" ]; then
        #PROOT="$S_PROOT_DIR/proot-x86 -q qemu-i386"
        #PROOT="$S_PROOT_DIR/proot-x86"
        PROOT="$BUILD_DIR/proot-source-x86/proot-Fedora-30.bin"
    elif [ "$OS_ARCH" = "x86_64" ]; then
        #PROOT="$S_PROOT_DIR/proot-x86_64"
        PROOT="$BUILD_DIR/proot-source-x86_64/proot-Fedora-30.bin"
    elif [ "$OS_ARCH" = "aarch64" ]; then
        #PROOT="$S_PROOT_DIR/proot-x86_64 -q qemu-aarch64"
        PROOT="$BUILD_DIR/proot-source-x86_64/proot-Fedora-30.bin -q qemu-aarch64"
    elif [ "$OS_ARCH" = "ppc64le" ]; then
        #PROOT="$S_PROOT_DIR/proot-x86_64 -q qemu-ppc64le"
        PROOT="$BUILD_DIR/proot-source-x86_64/proot-Fedora-30.bin -q qemu-ppc64le"
    else
        echo "unsupported $OS_NAME architecture: $OS_ARCH"
        exit 2
    fi

    if [ -x "${FAKECHROOT_SOURCE_DIR}/libfakechroot-Fedora-33.so" ] ; then
        echo "fakechroot binary already compiled : ${FAKECHROOT_SOURCE_DIR}/libfakechroot-Fedora-33.so"
        return
    fi

    export PROOT_NO_SECCOMP=1

    # compile fakechroot
    set -xv
    SHELL=/bin/bash CONFIG_SHELL=/bin/bash PATH=/bin:/usr/bin:/sbin:/usr/sbin \
        $PROOT -r "$OS_ROOTDIR" -b "${FAKECHROOT_SOURCE_DIR}:/fakechroot" -w / -b /dev \
            /bin/bash <<'EOF_fedora33_fakechroot'
cd /fakechroot
# BUILD FAKECHROOT
make distclean
bash ./configure
make
cp src/.libs/libfakechroot.so libfakechroot-Fedora-33.so
make clean
EOF_fedora33_fakechroot
    set +xv
}


# #############################################################################
# Fedora 34
# #############################################################################

fedora34_create_dnf()
{
    echo "fedora34_create_dnf : $1"
    local FILENAME="$1"
    local ARCH="$2"

    cat > "$FILENAME" <<EOF_fedora34_dnf
[main]
gpgcheck=0
sslverify=0
installonly_limit=3
clean_requirements_on_remove=True
reposdir=NONE

[fedora-modular]
name=Fedora Modular \$releasever - $ARCH
#baseurl=http://download.fedoraproject.org/pub/fedora/linux/releases/\$releasever/Modular/$ARCH/os/
metalink=https://mirrors.fedoraproject.org/metalink?repo=fedora-modular-\$releasever&arch=$ARCH
enabled=1
#metadata_expire=7d
repo_gpgcheck=0
type=rpm
gpgcheck=0
gpgkey=file:///etc/pki/rpm-gpg/RPM-GPG-KEY-fedora-\$releasever-$ARCH
skip_if_unavailable=False

[updates]
name=Fedora \$releasever - $ARCH - Updates
#baseurl=http://download.fedoraproject.org/pub/fedora/linux/updates/\$releasever/Everything/$ARCH/os
metalink=https://mirrors.fedoraproject.org/metalink?repo=updates-released-f\$releasever&arch=$ARCH
enabled=1
repo_gpgcheck=0
type=rpm
gpgcheck=0
metadata_expire=6h
gpgkey=file:///etc/pki/rpm-gpg/RPM-GPG-KEY-fedora-\$releasever-$ARCH
skip_if_unavailable=False

[fedora]
name=Fedora \$releasever - $ARCH
#baseurl=http://download.fedoraproject.org/pub/fedora/linux/releases/\$releasever/Everything/$ARCH/os/
metalink=https://mirrors.fedoraproject.org/metalink?repo=fedora-\$releasever&arch=$ARCH
enabled=1
metadata_expire=7d
repo_gpgcheck=0
type=rpm
gpgcheck=0
gpgkey=file:///etc/pki/rpm-gpg/RPM-GPG-KEY-fedora-\$releasever-$ARCH
skip_if_unavailable=False
EOF_fedora34_dnf
}


fedora34_setup()
{
    echo "fedora34_setup : $1"
    local OS_ARCH="$1"
    local OS_NAME="fedora"
    local OS_RELVER="34"
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
    fedora34_create_dnf "${OS_ROOTDIR}/etc/dnf/dnf.conf" "$OS_ARCH"

    $SUDO /usr/bin/dnf -y -c "${OS_ROOTDIR}/etc/dnf/dnf.conf" \
        install  --installroot="$OS_ROOTDIR" --releasever="$OS_RELVER" --forcearch="$OS_ARCH" \
            gcc kernel-devel make libtalloc libtalloc-devel glibc-static glibc-devel tar python \
	    python2 gzip zlib diffutils file glibc-headers dnf git which

    #$SUDO /usr/bin/dnf -y -c "${OS_ROOTDIR}/etc/dnf/dnf.conf" \
    #    downgrade  --installroot="$OS_ROOTDIR" --releasever="$OS_RELVER" --forcearch="$OS_ARCH" \
    #        coreutils-8.31-1.fc31.x86_64 coreutils-common-8.31-1.fc31.x86_64

    $SUDO /usr/bin/dnf -y -c "${OS_ROOTDIR}/etc/dnf/dnf.conf" \
        install  --installroot="$OS_ROOTDIR" --releasever="$OS_RELVER" --forcearch="$OS_ARCH" \
        autoconf m4 gcc-c++ libstdc++-static automake gawk libtool

    if [ "$OS_ARCH" = "aarch64" ]; then
        $SUDO chown -R "$(id -u):$(id -g)" "$OS_ROOTDIR"
	#PROOT="$S_PROOT_DIR/proot-x86_64 -q qemu-aarch64"
        PROOT="$BUILD_DIR/proot-source-x86_64/proot-Fedora-30.bin -q qemu-aarch64"
        export PROOT_NO_SECCOMP=1
	$PROOT -r "$OS_ROOTDIR" -0 -w / -b /dev -b /etc/resolv.conf /bin/bash <<'EOF_fedora34_reinstall'
dnf -y reinstall $(rpm -qa)
EOF_fedora34_reinstall
    fi

    $SUDO /usr/bin/dnf -y -c "${OS_ROOTDIR}/etc/dnf/dnf.conf" \
        clean packages

    $SUDO /bin/chown -R "$(id -u).$(id -g)" "$OS_ROOTDIR"
    $SUDO /bin/chmod -R u+rw "$OS_ROOTDIR"
}

fedora34_build_proot_c()
{
    echo "fedora34_build_proot : $1"
    local OS_ARCH="$1"
    local PROOT_SOURCE_DIR="$2"
    local OS_NAME="fedora"
    local OS_RELVER="34"
    local OS_ROOTDIR="${BUILD_DIR}/${OS_NAME}_${OS_RELVER}_${OS_ARCH}"
    local PROOT=""

    SUDO=/bin/sudo

    if [ -x "${PROOT_SOURCE_DIR}/proot-Fedora-34.bin" ] ; then
        echo "proot binary already compiled : ${PROOT_SOURCE_DIR}/proot-Fedora-34.bin"
    else
	$SUDO mount --bind "${PROOT_SOURCE_DIR}" "$OS_ROOTDIR/proot"
	$SUDO mount --bind "${S_PROOT_PACKAGES_DIR}" "$OS_ROOTDIR/proot-static-packages"
        # compile proot
        $SUDO chroot --userspec="$USER" "$OS_ROOTDIR" /bin/bash <<'EOF_fedora34_proot_1'
cd /usr/bin
rm python
ln -s python2 python
cd /proot
/bin/rm -f proot-Fedora-34.bin src/proot src/libtalloc.a src/talloc.h
/bin/rm -Rf talloc*
# BUILD TALLOC
tar xzvf /proot-static-packages/talloc.tar.gz
cd talloc*
./configure
make
cp talloc.h /proot/src
cd bin/default
[ -f talloc.c.6.o ] && ar qf libtalloc.a talloc.c.6.o
[ -f talloc.c.5.o -a ! -f libtalloc.a ] && ar qf libtalloc.a talloc.c.5.o
cp libtalloc.a /proot/src && make clean
# BUILD PROOT
cd /proot/src
make clean
make loader.elf
make loader-m32.elf
make build.h
LDFLAGS="-L/proot/usr/src -static" make proot
EOF_fedora34_proot_1
    sync
    $SUDO umount "$OS_ROOTDIR/proot"
    $SUDO umount "$OS_ROOTDIR/proot-static-packages"
    fi

    if [ -e "${PROOT_SOURCE_DIR}/src/proot" ]; then
        mv "${PROOT_SOURCE_DIR}/src/proot" "${PROOT_SOURCE_DIR}/proot-Fedora-34.bin"
    fi

    if [ ! -e "${PROOT_SOURCE_DIR}/proot-Fedora-34.bin" ]; then
        echo "proot compilation failed ${PROOT_SOURCE_DIR}/proot-Fedora-34.bin not found"
        exit 1
    fi
}


fedora34_build_proot()
{
    echo "fedora34_build_proot : $1"
    local OS_ARCH="$1"
    local PROOT_SOURCE_DIR="$2"
    local OS_NAME="fedora"
    local OS_RELVER="34"
    local OS_ROOTDIR="${BUILD_DIR}/${OS_NAME}_${OS_RELVER}_${OS_ARCH}"
    local PROOT=""

    if [ "$OS_ARCH" = "i386" ]; then
        #PROOT="$S_PROOT_DIR/proot-x86 -q qemu-i386"
        #PROOT="$S_PROOT_DIR/proot-x86"
        PROOT="$BUILD_DIR/proot-source-x86/proot-Fedora-30.bin"
    elif [ "$OS_ARCH" = "x86_64" ]; then
        #PROOT="$S_PROOT_DIR/proot-x86_64"
        PROOT="$BUILD_DIR/proot-source-x86_64/proot-Fedora-30.bin"
    elif [ "$OS_ARCH" = "aarch64" ]; then
        #PROOT="$S_PROOT_DIR/proot-x86_64 -q qemu-aarch64"
        PROOT="$BUILD_DIR/proot-source-x86_64/proot-Fedora-30.bin -q qemu-aarch64"
    else
        echo "unsupported $OS_NAME architecture: $OS_ARCH"
        exit 2
    fi

    export PROOT_NO_SECCOMP=1

    if [ -x "${PROOT_SOURCE_DIR}/proot-Fedora-34.bin" ] ; then
        echo "proot binary already compiled : ${PROOT_SOURCE_DIR}/proot-Fedora-34.bin"
    else
        # compile proot
        $PROOT -r "$OS_ROOTDIR" -b "${PROOT_SOURCE_DIR}:/proot" -w / -b /dev \
                           -b "${S_PROOT_PACKAGES_DIR}:/proot-static-packages"   /bin/bash <<'EOF_fedora34_proot_1'
cd /usr/bin
rm python
ln -s python2 python
cd /proot
/bin/rm -f proot-Fedora-34.bin src/proot src/libtalloc.a src/talloc.h
/bin/rm -Rf talloc*
# BUILD TALLOC
tar xzvf /proot-static-packages/talloc.tar.gz
cd talloc*
./configure
make
cp talloc.h /proot/src
cd bin/default
[ -f talloc.c.6.o ] && ar qf libtalloc.a talloc.c.6.o
[ -f talloc.c.5.o -a ! -f libtalloc.a ] && ar qf libtalloc.a talloc.c.5.o
cp libtalloc.a /proot/src && make clean
# BUILD PROOT
cd /proot/src
make clean
make loader.elf
make loader-m32.elf
make build.h
LDFLAGS="-L/proot/usr/src -static" make proot
EOF_fedora34_proot_1
    fi

    if [ -e "${PROOT_SOURCE_DIR}/src/proot" ]; then
        mv "${PROOT_SOURCE_DIR}/src/proot" "${PROOT_SOURCE_DIR}/proot-Fedora-34.bin"
    fi

    if [ ! -e "${PROOT_SOURCE_DIR}/proot-Fedora-34.bin" ]; then
        echo "proot compilation failed ${PROOT_SOURCE_DIR}/proot-Fedora-34.bin not found"
        exit 1
    fi
}


fedora34_build_patchelf()
{
    echo "fedora34_build_patchelf : $1"
    local OS_ARCH="$1"
    local PATCHELF_SOURCE_DIR="$2"
    local OS_NAME="fedora"
    local OS_RELVER="34"
    local OS_ROOTDIR="${BUILD_DIR}/${OS_NAME}_${OS_RELVER}_${OS_ARCH}"
    local PROOT=""

    if [ "$OS_ARCH" = "i386" ]; then
        #PROOT="$S_PROOT_DIR/proot-x86 -q qemu-i386"
        #PROOT="$S_PROOT_DIR/proot-x86"
        PROOT="$BUILD_DIR/proot-source-x86/proot-Fedora-30.bin"
    elif [ "$OS_ARCH" = "x86_64" ]; then
        #PROOT="$S_PROOT_DIR/proot-x86_64"
        PROOT="$BUILD_DIR/proot-source-x86_64/proot-Fedora-30.bin"
    elif [ "$OS_ARCH" = "aarch64" ]; then
        #PROOT="$S_PROOT_DIR/proot-x86_64 -q qemu-aarch64"
        PROOT="$BUILD_DIR/proot-source-x86_64/proot-Fedora-30.bin -q qemu-aarch64"
    elif [ "$OS_ARCH" = "ppc64le" ]; then
        #PROOT="$S_PROOT_DIR/proot-x86_64 -q qemu-ppc64le"
        PROOT="$BUILD_DIR/proot-source-x86_64/proot-Fedora-30.bin -q qemu-ppc64le"
    else
        echo "unsupported $OS_NAME architecture: $OS_ARCH"
        exit 2
    fi

    if [ -x "${PATCHELF_SOURCE_DIR}/patchelf-Fedora-34" ] ; then
        echo "patchelf binary already compiled : ${PATCHELF_SOURCE_DIR}/patchelf-Fedora-34"
        return
    fi

    export PROOT_NO_SECCOMP=1

    # compile patchelf
    set -xv
    (cd "${PATCHELF_SOURCE_DIR}" ; bash ./bootstrap.sh)
    $PROOT -r "$OS_ROOTDIR" -b "${PATCHELF_SOURCE_DIR}:/patchelf" -w / -b /dev \
                            /bin/bash <<'EOF_fedora34_patchelf'
cd /patchelf
make clean
# BUILD PATCHELF
#bash bootstrap.sh
bash ./configure
make
cp src/patchelf /patchelf/patchelf-Fedora-34
make clean
EOF_fedora34_patchelf
    set +xv
}

fedora34_build_fakechroot()
{
    echo "fedora34_build_fakechroot : $1"
    local OS_ARCH="$1"
    local FAKECHROOT_SOURCE_DIR="$2"
    local OS_NAME="fedora"
    local OS_RELVER="34"
    local OS_ROOTDIR="${BUILD_DIR}/${OS_NAME}_${OS_RELVER}_${OS_ARCH}"
    local PROOT=""

    if [ "$OS_ARCH" = "i386" ]; then
        #PROOT="$S_PROOT_DIR/proot-x86 -q qemu-i386"
        #PROOT="$S_PROOT_DIR/proot-x86"
        PROOT="$BUILD_DIR/proot-source-x86/proot-Fedora-30.bin"
    elif [ "$OS_ARCH" = "x86_64" ]; then
        #PROOT="$S_PROOT_DIR/proot-x86_64"
        PROOT="$BUILD_DIR/proot-source-x86_64/proot-Fedora-30.bin"
    elif [ "$OS_ARCH" = "aarch64" ]; then
        #PROOT="$S_PROOT_DIR/proot-x86_64 -q qemu-aarch64"
        PROOT="$BUILD_DIR/proot-source-x86_64/proot-Fedora-30.bin -q qemu-aarch64"
    elif [ "$OS_ARCH" = "ppc64le" ]; then
        #PROOT="$S_PROOT_DIR/proot-x86_64 -q qemu-ppc64le"
        PROOT="$BUILD_DIR/proot-source-x86_64/proot-Fedora-30.bin -q qemu-ppc64le"
    else
        echo "unsupported $OS_NAME architecture: $OS_ARCH"
        exit 2
    fi

    if [ -x "${FAKECHROOT_SOURCE_DIR}/libfakechroot-Fedora-34.so" ] ; then
        echo "fakechroot binary already compiled : ${FAKECHROOT_SOURCE_DIR}/libfakechroot-Fedora-34.so"
        return
    fi

    export PROOT_NO_SECCOMP=1

    # compile fakechroot
    set -xv
    SHELL=/bin/bash CONFIG_SHELL=/bin/bash PATH=/bin:/usr/bin:/sbin:/usr/sbin \
        $PROOT -r "$OS_ROOTDIR" -b "${FAKECHROOT_SOURCE_DIR}:/fakechroot" -w / -b /dev \
            /bin/bash <<'EOF_fedora34_fakechroot'
cd /fakechroot
# BUILD FAKECHROOT
make distclean
bash ./configure
make
cp src/.libs/libfakechroot.so libfakechroot-Fedora-34.so
make clean
EOF_fedora34_fakechroot
    set +xv
}


# #############################################################################
# Fedora 35
# #############################################################################

fedora35_create_dnf()
{
    echo "fedora35_create_dnf : $1"
    local FILENAME="$1"
    local ARCH="$2"

    cat > "$FILENAME" <<EOF_fedora35_dnf
[main]
gpgcheck=0
sslverify=0
installonly_limit=3
clean_requirements_on_remove=True
reposdir=NONE

[fedora-modular]
name=Fedora Modular \$releasever - $ARCH
#baseurl=http://download.fedoraproject.org/pub/fedora/linux/releases/\$releasever/Modular/$ARCH/os/
metalink=https://mirrors.fedoraproject.org/metalink?repo=fedora-modular-\$releasever&arch=$ARCH
enabled=1
#metadata_expire=7d
repo_gpgcheck=0
type=rpm
gpgcheck=0
gpgkey=file:///etc/pki/rpm-gpg/RPM-GPG-KEY-fedora-\$releasever-$ARCH
skip_if_unavailable=False

[updates]
name=Fedora \$releasever - $ARCH - Updates
#baseurl=http://download.fedoraproject.org/pub/fedora/linux/updates/\$releasever/Everything/$ARCH/os
metalink=https://mirrors.fedoraproject.org/metalink?repo=updates-released-f\$releasever&arch=$ARCH
enabled=1
repo_gpgcheck=0
type=rpm
gpgcheck=0
metadata_expire=6h
gpgkey=file:///etc/pki/rpm-gpg/RPM-GPG-KEY-fedora-\$releasever-$ARCH
skip_if_unavailable=False

[fedora]
name=Fedora \$releasever - $ARCH
#baseurl=http://download.fedoraproject.org/pub/fedora/linux/releases/\$releasever/Everything/$ARCH/os/
metalink=https://mirrors.fedoraproject.org/metalink?repo=fedora-\$releasever&arch=$ARCH
enabled=1
metadata_expire=7d
repo_gpgcheck=0
type=rpm
gpgcheck=0
gpgkey=file:///etc/pki/rpm-gpg/RPM-GPG-KEY-fedora-\$releasever-$ARCH
skip_if_unavailable=False
EOF_fedora35_dnf
}


fedora35_setup()
{
    echo "fedora35_setup : $1"
    local OS_ARCH="$1"
    local OS_NAME="fedora"
    local OS_RELVER="35"
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
    fedora35_create_dnf "${OS_ROOTDIR}/etc/dnf/dnf.conf" "$OS_ARCH"

    $SUDO /usr/bin/dnf -y -c "${OS_ROOTDIR}/etc/dnf/dnf.conf" \
        install  --installroot="$OS_ROOTDIR" --releasever="$OS_RELVER" --forcearch="$OS_ARCH" \
            gcc kernel-devel make libtalloc libtalloc-devel glibc-static glibc-devel tar python \
	    python2 gzip zlib diffutils file glibc-headers dnf git which

    #$SUDO /usr/bin/dnf -y -c "${OS_ROOTDIR}/etc/dnf/dnf.conf" \
    #    downgrade  --installroot="$OS_ROOTDIR" --releasever="$OS_RELVER" --forcearch="$OS_ARCH" \
    #        coreutils-8.31-1.fc31.x86_64 coreutils-common-8.31-1.fc31.x86_64

    $SUDO /usr/bin/dnf -y -c "${OS_ROOTDIR}/etc/dnf/dnf.conf" \
        install  --installroot="$OS_ROOTDIR" --releasever="$OS_RELVER" --forcearch="$OS_ARCH" \
        autoconf m4 gcc-c++ libstdc++-static automake gawk libtool

    if [ "$OS_ARCH" = "aarch64" ]; then
        $SUDO chown -R "$(id -u):$(id -g)" "$OS_ROOTDIR"
	#PROOT="$S_PROOT_DIR/proot-x86_64 -q qemu-aarch64"
        PROOT="$BUILD_DIR/proot-source-x86_64/proot-Fedora-30.bin -q qemu-aarch64"
        export PROOT_NO_SECCOMP=1
	$PROOT -r "$OS_ROOTDIR" -0 -w / -b /dev -b /etc/resolv.conf /bin/bash <<'EOF_fedora35_reinstall'
dnf -y reinstall $(rpm -qa)
EOF_fedora35_reinstall
    fi

    $SUDO /usr/bin/dnf -y -c "${OS_ROOTDIR}/etc/dnf/dnf.conf" \
        clean packages

    $SUDO /bin/chown -R "$(id -u).$(id -g)" "$OS_ROOTDIR"
    $SUDO /bin/chmod -R u+rw "$OS_ROOTDIR"
}

fedora35_build_proot_c()
{
    echo "fedora35_build_proot : $1"
    local OS_ARCH="$1"
    local PROOT_SOURCE_DIR="$2"
    local OS_NAME="fedora"
    local OS_RELVER="35"
    local OS_ROOTDIR="${BUILD_DIR}/${OS_NAME}_${OS_RELVER}_${OS_ARCH}"
    local PROOT=""

    SUDO=/bin/sudo

    if [ -x "${PROOT_SOURCE_DIR}/proot-Fedora-35.bin" ] ; then
        echo "proot binary already compiled : ${PROOT_SOURCE_DIR}/proot-Fedora-35.bin"
    else
	$SUDO mount --bind "${PROOT_SOURCE_DIR}" "$OS_ROOTDIR/proot"
	$SUDO mount --bind "${S_PROOT_PACKAGES_DIR}" "$OS_ROOTDIR/proot-static-packages"
        # compile proot
        $SUDO chroot --userspec="$USER" "$OS_ROOTDIR" /bin/bash <<'EOF_fedora35_proot_1'
cd /usr/bin
rm python
ln -s python2 python
cd /proot
/bin/rm -f proot-Fedora-35.bin src/proot src/libtalloc.a src/talloc.h
/bin/rm -Rf talloc*
# BUILD TALLOC
tar xzvf /proot-static-packages/talloc.tar.gz
cd talloc*
./configure
make
cp talloc.h /proot/src
cd bin/default
[ -f talloc.c.6.o ] && ar qf libtalloc.a talloc.c.6.o
[ -f talloc.c.5.o -a ! -f libtalloc.a ] && ar qf libtalloc.a talloc.c.5.o
cp libtalloc.a /proot/src && make clean
# BUILD PROOT
cd /proot/src
make clean
make loader.elf
make loader-m32.elf
make build.h
LDFLAGS="-L/proot/usr/src -static" make proot
EOF_fedora35_proot_1
    sync
    $SUDO umount "$OS_ROOTDIR/proot"
    $SUDO umount "$OS_ROOTDIR/proot-static-packages"
    fi

    if [ -e "${PROOT_SOURCE_DIR}/src/proot" ]; then
        mv "${PROOT_SOURCE_DIR}/src/proot" "${PROOT_SOURCE_DIR}/proot-Fedora-35.bin"
    fi

    if [ ! -e "${PROOT_SOURCE_DIR}/proot-Fedora-35.bin" ]; then
        echo "proot compilation failed ${PROOT_SOURCE_DIR}/proot-Fedora-35.bin not found"
        exit 1
    fi
}


fedora35_build_proot()
{
    echo "fedora35_build_proot : $1"
    local OS_ARCH="$1"
    local PROOT_SOURCE_DIR="$2"
    local OS_NAME="fedora"
    local OS_RELVER="35"
    local OS_ROOTDIR="${BUILD_DIR}/${OS_NAME}_${OS_RELVER}_${OS_ARCH}"
    local PROOT=""

    if [ "$OS_ARCH" = "i386" ]; then
        #PROOT="$S_PROOT_DIR/proot-x86 -q qemu-i386"
        #PROOT="$S_PROOT_DIR/proot-x86"
        PROOT="$BUILD_DIR/proot-source-x86/proot-Fedora-30.bin"
    elif [ "$OS_ARCH" = "x86_64" ]; then
        #PROOT="$S_PROOT_DIR/proot-x86_64"
        PROOT="$BUILD_DIR/proot-source-x86_64/proot-Fedora-30.bin"
    elif [ "$OS_ARCH" = "aarch64" ]; then
        #PROOT="$S_PROOT_DIR/proot-x86_64 -q qemu-aarch64"
        PROOT="$BUILD_DIR/proot-source-x86_64/proot-Fedora-30.bin -q qemu-aarch64"
    else
        echo "unsupported $OS_NAME architecture: $OS_ARCH"
        exit 2
    fi

    export PROOT_NO_SECCOMP=1

    if [ -x "${PROOT_SOURCE_DIR}/proot-Fedora-35.bin" ] ; then
        echo "proot binary already compiled : ${PROOT_SOURCE_DIR}/proot-Fedora-35.bin"
    else
        # compile proot
        $PROOT -r "$OS_ROOTDIR" -b "${PROOT_SOURCE_DIR}:/proot" -w / -b /dev \
                           -b "${S_PROOT_PACKAGES_DIR}:/proot-static-packages"   /bin/bash <<'EOF_fedora35_proot_1'
cd /usr/bin
rm python
ln -s python2 python
cd /proot
/bin/rm -f proot-Fedora-35.bin src/proot src/libtalloc.a src/talloc.h
/bin/rm -Rf talloc*
# BUILD TALLOC
tar xzvf /proot-static-packages/talloc.tar.gz
cd talloc*
./configure
make
cp talloc.h /proot/src
cd bin/default
[ -f talloc.c.6.o ] && ar qf libtalloc.a talloc.c.6.o
[ -f talloc.c.5.o -a ! -f libtalloc.a ] && ar qf libtalloc.a talloc.c.5.o
cp libtalloc.a /proot/src && make clean
# BUILD PROOT
cd /proot/src
make clean
make loader.elf
make loader-m32.elf
make build.h
LDFLAGS="-L/proot/usr/src -static" make proot
EOF_fedora35_proot_1
    fi

    if [ -e "${PROOT_SOURCE_DIR}/src/proot" ]; then
        mv "${PROOT_SOURCE_DIR}/src/proot" "${PROOT_SOURCE_DIR}/proot-Fedora-35.bin"
    fi

    if [ ! -e "${PROOT_SOURCE_DIR}/proot-Fedora-35.bin" ]; then
        echo "proot compilation failed ${PROOT_SOURCE_DIR}/proot-Fedora-35.bin not found"
        exit 1
    fi
}


fedora35_build_patchelf()
{
    echo "fedora35_build_patchelf : $1"
    local OS_ARCH="$1"
    local PATCHELF_SOURCE_DIR="$2"
    local OS_NAME="fedora"
    local OS_RELVER="35"
    local OS_ROOTDIR="${BUILD_DIR}/${OS_NAME}_${OS_RELVER}_${OS_ARCH}"
    local PROOT=""

    if [ "$OS_ARCH" = "i386" ]; then
        #PROOT="$S_PROOT_DIR/proot-x86 -q qemu-i386"
        #PROOT="$S_PROOT_DIR/proot-x86"
        PROOT="$BUILD_DIR/proot-source-x86/proot-Fedora-30.bin"
    elif [ "$OS_ARCH" = "x86_64" ]; then
        #PROOT="$S_PROOT_DIR/proot-x86_64"
        PROOT="$BUILD_DIR/proot-source-x86_64/proot-Fedora-30.bin"
    elif [ "$OS_ARCH" = "aarch64" ]; then
        #PROOT="$S_PROOT_DIR/proot-x86_64 -q qemu-aarch64"
        PROOT="$BUILD_DIR/proot-source-x86_64/proot-Fedora-30.bin -q qemu-aarch64"
    elif [ "$OS_ARCH" = "ppc64le" ]; then
        #PROOT="$S_PROOT_DIR/proot-x86_64 -q qemu-ppc64le"
        PROOT="$BUILD_DIR/proot-source-x86_64/proot-Fedora-30.bin -q qemu-ppc64le"
    else
        echo "unsupported $OS_NAME architecture: $OS_ARCH"
        exit 2
    fi

    if [ -x "${PATCHELF_SOURCE_DIR}/patchelf-Fedora-35" ] ; then
        echo "patchelf binary already compiled : ${PATCHELF_SOURCE_DIR}/patchelf-Fedora-35"
        return
    fi

    export PROOT_NO_SECCOMP=1

    # compile patchelf
    set -xv
    (cd "${PATCHELF_SOURCE_DIR}" ; bash ./bootstrap.sh)
    $PROOT -r "$OS_ROOTDIR" -b "${PATCHELF_SOURCE_DIR}:/patchelf" -w / -b /dev \
                            /bin/bash <<'EOF_fedora35_patchelf'
cd /patchelf
make clean
# BUILD PATCHELF
#bash bootstrap.sh
bash ./configure
make
cp src/patchelf /patchelf/patchelf-Fedora-35
make clean
EOF_fedora35_patchelf
    set +xv
}

fedora35_build_fakechroot()
{
    echo "fedora35_build_fakechroot : $1"
    local OS_ARCH="$1"
    local FAKECHROOT_SOURCE_DIR="$2"
    local OS_NAME="fedora"
    local OS_RELVER="35"
    local OS_ROOTDIR="${BUILD_DIR}/${OS_NAME}_${OS_RELVER}_${OS_ARCH}"
    local PROOT=""

    if [ "$OS_ARCH" = "i386" ]; then
        #PROOT="$S_PROOT_DIR/proot-x86 -q qemu-i386"
        #PROOT="$S_PROOT_DIR/proot-x86"
        PROOT="$BUILD_DIR/proot-source-x86/proot-Fedora-30.bin"
    elif [ "$OS_ARCH" = "x86_64" ]; then
        #PROOT="$S_PROOT_DIR/proot-x86_64"
        PROOT="$BUILD_DIR/proot-source-x86_64/proot-Fedora-30.bin"
    elif [ "$OS_ARCH" = "aarch64" ]; then
        #PROOT="$S_PROOT_DIR/proot-x86_64 -q qemu-aarch64"
        PROOT="$BUILD_DIR/proot-source-x86_64/proot-Fedora-30.bin -q qemu-aarch64"
    elif [ "$OS_ARCH" = "ppc64le" ]; then
        #PROOT="$S_PROOT_DIR/proot-x86_64 -q qemu-ppc64le"
        PROOT="$BUILD_DIR/proot-source-x86_64/proot-Fedora-30.bin -q qemu-ppc64le"
    else
        echo "unsupported $OS_NAME architecture: $OS_ARCH"
        exit 2
    fi

    if [ -x "${FAKECHROOT_SOURCE_DIR}/libfakechroot-Fedora-35.so" ] ; then
        echo "fakechroot binary already compiled : ${FAKECHROOT_SOURCE_DIR}/libfakechroot-Fedora-35.so"
        return
    fi

    export PROOT_NO_SECCOMP=1

    # compile fakechroot
    set -xv
    SHELL=/bin/bash CONFIG_SHELL=/bin/bash PATH=/bin:/usr/bin:/sbin:/usr/sbin \
        $PROOT -r "$OS_ROOTDIR" -b "${FAKECHROOT_SOURCE_DIR}:/fakechroot" -w / -b /dev \
            /bin/bash <<'EOF_fedora35_fakechroot'
cd /fakechroot
# BUILD FAKECHROOT
make distclean
bash ./configure
make
cp src/.libs/libfakechroot.so libfakechroot-Fedora-35.so
make clean
EOF_fedora35_fakechroot
    set +xv
}


# #############################################################################
# Fedora 36
# #############################################################################

fedora36_create_dnf()
{
    echo "fedora36_create_dnf : $1"
    local FILENAME="$1"
    local ARCH="$2"

    cat > "$FILENAME" <<EOF_fedora36_dnf
[main]
gpgcheck=0
sslverify=0
installonly_limit=3
clean_requirements_on_remove=True
reposdir=NONE

[fedora-modular]
name=Fedora Modular \$releasever - $ARCH
#baseurl=http://download.fedoraproject.org/pub/fedora/linux/releases/\$releasever/Modular/$ARCH/os/
metalink=https://mirrors.fedoraproject.org/metalink?repo=fedora-modular-\$releasever&arch=$ARCH
enabled=1
#metadata_expire=7d
repo_gpgcheck=0
type=rpm
gpgcheck=0
gpgkey=file:///etc/pki/rpm-gpg/RPM-GPG-KEY-fedora-\$releasever-$ARCH
skip_if_unavailable=False

[updates]
name=Fedora \$releasever - $ARCH - Updates
#baseurl=http://download.fedoraproject.org/pub/fedora/linux/updates/\$releasever/Everything/$ARCH/os
metalink=https://mirrors.fedoraproject.org/metalink?repo=updates-released-f\$releasever&arch=$ARCH
enabled=1
repo_gpgcheck=0
type=rpm
gpgcheck=0
metadata_expire=6h
gpgkey=file:///etc/pki/rpm-gpg/RPM-GPG-KEY-fedora-\$releasever-$ARCH
skip_if_unavailable=False

[fedora]
name=Fedora \$releasever - $ARCH
#baseurl=http://download.fedoraproject.org/pub/fedora/linux/releases/\$releasever/Everything/$ARCH/os/
metalink=https://mirrors.fedoraproject.org/metalink?repo=fedora-\$releasever&arch=$ARCH
enabled=1
metadata_expire=7d
repo_gpgcheck=0
type=rpm
gpgcheck=0
gpgkey=file:///etc/pki/rpm-gpg/RPM-GPG-KEY-fedora-\$releasever-$ARCH
skip_if_unavailable=False
EOF_fedora36_dnf
}


fedora36_setup()
{
    echo "fedora36_setup : $1"
    local OS_ARCH="$1"
    local OS_NAME="fedora"
    local OS_RELVER="36"
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
    fedora36_create_dnf "${OS_ROOTDIR}/etc/dnf/dnf.conf" "$OS_ARCH"

    $SUDO /usr/bin/dnf -y -c "${OS_ROOTDIR}/etc/dnf/dnf.conf" \
        install  --installroot="$OS_ROOTDIR" --releasever="$OS_RELVER" --forcearch="$OS_ARCH" \
            gcc kernel-devel make libtalloc libtalloc-devel glibc-static glibc-devel tar python \
	    python2 gzip zlib diffutils file glibc-headers dnf git which

    #$SUDO /usr/bin/dnf -y -c "${OS_ROOTDIR}/etc/dnf/dnf.conf" \
    #    downgrade  --installroot="$OS_ROOTDIR" --releasever="$OS_RELVER" --forcearch="$OS_ARCH" \
    #        coreutils-8.31-1.fc31.x86_64 coreutils-common-8.31-1.fc31.x86_64

    $SUDO /usr/bin/dnf -y -c "${OS_ROOTDIR}/etc/dnf/dnf.conf" \
        install  --installroot="$OS_ROOTDIR" --releasever="$OS_RELVER" --forcearch="$OS_ARCH" \
        autoconf m4 gcc-c++ libstdc++-static automake gawk libtool

    if [ "$OS_ARCH" = "aarch64" ]; then
        $SUDO chown -R "$(id -u):$(id -g)" "$OS_ROOTDIR"
	#PROOT="$S_PROOT_DIR/proot-x86_64 -q qemu-aarch64"
        PROOT="$BUILD_DIR/proot-source-x86_64/proot-Fedora-30.bin -q qemu-aarch64"
        export PROOT_NO_SECCOMP=1
	$PROOT -r "$OS_ROOTDIR" -0 -w / -b /dev -b /etc/resolv.conf /bin/bash <<'EOF_fedora36_reinstall'
dnf -y reinstall $(rpm -qa)
EOF_fedora36_reinstall
    fi

    $SUDO /usr/bin/dnf -y -c "${OS_ROOTDIR}/etc/dnf/dnf.conf" \
        clean packages

    $SUDO /bin/chown -R "$(id -u).$(id -g)" "$OS_ROOTDIR"
    $SUDO /bin/chmod -R u+rw "$OS_ROOTDIR"
}

fedora36_build_proot_c()
{
    echo "fedora36_build_proot : $1"
    local OS_ARCH="$1"
    local PROOT_SOURCE_DIR="$2"
    local OS_NAME="fedora"
    local OS_RELVER="36"
    local OS_ROOTDIR="${BUILD_DIR}/${OS_NAME}_${OS_RELVER}_${OS_ARCH}"
    local PROOT=""

    SUDO=/bin/sudo

    if [ -x "${PROOT_SOURCE_DIR}/proot-Fedora-36.bin" ] ; then
        echo "proot binary already compiled : ${PROOT_SOURCE_DIR}/proot-Fedora-36.bin"
    else
	$SUDO mount --bind "${PROOT_SOURCE_DIR}" "$OS_ROOTDIR/proot"
	$SUDO mount --bind "${S_PROOT_PACKAGES_DIR}" "$OS_ROOTDIR/proot-static-packages"
        # compile proot
        $SUDO chroot --userspec="$USER" "$OS_ROOTDIR" /bin/bash <<'EOF_fedora36_proot_1'
cd /usr/bin
rm python
ln -s python2 python
cd /proot
/bin/rm -f proot-Fedora-36.bin src/proot src/libtalloc.a src/talloc.h
/bin/rm -Rf talloc*
# BUILD TALLOC
tar xzvf /proot-static-packages/talloc.tar.gz
cd talloc*
./configure
make
cp talloc.h /proot/src
cd bin/default
[ -f talloc.c.6.o ] && ar qf libtalloc.a talloc.c.6.o
[ -f talloc.c.5.o -a ! -f libtalloc.a ] && ar qf libtalloc.a talloc.c.5.o
cp libtalloc.a /proot/src && make clean
# BUILD PROOT
cd /proot/src
make clean
make loader.elf
make loader-m32.elf
make build.h
LDFLAGS="-L/proot/usr/src -static" make proot
EOF_fedora36_proot_1
    sync
    $SUDO umount "$OS_ROOTDIR/proot"
    $SUDO umount "$OS_ROOTDIR/proot-static-packages"
    fi

    if [ -e "${PROOT_SOURCE_DIR}/src/proot" ]; then
        mv "${PROOT_SOURCE_DIR}/src/proot" "${PROOT_SOURCE_DIR}/proot-Fedora-36.bin"
    fi

    if [ ! -e "${PROOT_SOURCE_DIR}/proot-Fedora-36.bin" ]; then
        echo "proot compilation failed ${PROOT_SOURCE_DIR}/proot-Fedora-36.bin not found"
        exit 1
    fi
}


fedora36_build_proot()
{
    echo "fedora36_build_proot : $1"
    local OS_ARCH="$1"
    local PROOT_SOURCE_DIR="$2"
    local OS_NAME="fedora"
    local OS_RELVER="36"
    local OS_ROOTDIR="${BUILD_DIR}/${OS_NAME}_${OS_RELVER}_${OS_ARCH}"
    local PROOT=""

    if [ "$OS_ARCH" = "i386" ]; then
        #PROOT="$S_PROOT_DIR/proot-x86 -q qemu-i386"
        #PROOT="$S_PROOT_DIR/proot-x86"
        PROOT="$BUILD_DIR/proot-source-x86/proot-Fedora-30.bin"
    elif [ "$OS_ARCH" = "x86_64" ]; then
        #PROOT="$S_PROOT_DIR/proot-x86_64"
        PROOT="$BUILD_DIR/proot-source-x86_64/proot-Fedora-30.bin"
    elif [ "$OS_ARCH" = "aarch64" ]; then
        #PROOT="$S_PROOT_DIR/proot-x86_64 -q qemu-aarch64"
        PROOT="$BUILD_DIR/proot-source-x86_64/proot-Fedora-30.bin -q qemu-aarch64"
    else
        echo "unsupported $OS_NAME architecture: $OS_ARCH"
        exit 2
    fi

    export PROOT_NO_SECCOMP=1

    if [ -x "${PROOT_SOURCE_DIR}/proot-Fedora-36.bin" ] ; then
        echo "proot binary already compiled : ${PROOT_SOURCE_DIR}/proot-Fedora-36.bin"
    else
        # compile proot
        $PROOT -r "$OS_ROOTDIR" -b "${PROOT_SOURCE_DIR}:/proot" -w / -b /dev \
                           -b "${S_PROOT_PACKAGES_DIR}:/proot-static-packages"   /bin/bash <<'EOF_fedora36_proot_1'
cd /usr/bin
rm python
ln -s python2 python
cd /proot
/bin/rm -f proot-Fedora-36.bin src/proot src/libtalloc.a src/talloc.h
/bin/rm -Rf talloc*
# BUILD TALLOC
tar xzvf /proot-static-packages/talloc.tar.gz
cd talloc*
./configure
make
cp talloc.h /proot/src
cd bin/default
[ -f talloc.c.6.o ] && ar qf libtalloc.a talloc.c.6.o
[ -f talloc.c.5.o -a ! -f libtalloc.a ] && ar qf libtalloc.a talloc.c.5.o
cp libtalloc.a /proot/src && make clean
# BUILD PROOT
cd /proot/src
make clean
make loader.elf
make loader-m32.elf
make build.h
LDFLAGS="-L/proot/usr/src -static" make proot
EOF_fedora36_proot_1
    fi

    if [ -e "${PROOT_SOURCE_DIR}/src/proot" ]; then
        mv "${PROOT_SOURCE_DIR}/src/proot" "${PROOT_SOURCE_DIR}/proot-Fedora-36.bin"
    fi

    if [ ! -e "${PROOT_SOURCE_DIR}/proot-Fedora-36.bin" ]; then
        echo "proot compilation failed ${PROOT_SOURCE_DIR}/proot-Fedora-36.bin not found"
        exit 1
    fi
}


fedora36_build_patchelf()
{
    echo "fedora36_build_patchelf : $1"
    local OS_ARCH="$1"
    local PATCHELF_SOURCE_DIR="$2"
    local OS_NAME="fedora"
    local OS_RELVER="36"
    local OS_ROOTDIR="${BUILD_DIR}/${OS_NAME}_${OS_RELVER}_${OS_ARCH}"
    local PROOT=""

    if [ "$OS_ARCH" = "i386" ]; then
        #PROOT="$S_PROOT_DIR/proot-x86 -q qemu-i386"
        #PROOT="$S_PROOT_DIR/proot-x86"
        PROOT="$BUILD_DIR/proot-source-x86/proot-Fedora-30.bin"
    elif [ "$OS_ARCH" = "x86_64" ]; then
        #PROOT="$S_PROOT_DIR/proot-x86_64"
        PROOT="$BUILD_DIR/proot-source-x86_64/proot-Fedora-30.bin"
    elif [ "$OS_ARCH" = "aarch64" ]; then
        #PROOT="$S_PROOT_DIR/proot-x86_64 -q qemu-aarch64"
        PROOT="$BUILD_DIR/proot-source-x86_64/proot-Fedora-30.bin -q qemu-aarch64"
    elif [ "$OS_ARCH" = "ppc64le" ]; then
        #PROOT="$S_PROOT_DIR/proot-x86_64 -q qemu-ppc64le"
        PROOT="$BUILD_DIR/proot-source-x86_64/proot-Fedora-30.bin -q qemu-ppc64le"
    else
        echo "unsupported $OS_NAME architecture: $OS_ARCH"
        exit 2
    fi

    if [ -x "${PATCHELF_SOURCE_DIR}/patchelf-Fedora-36" ] ; then
        echo "patchelf binary already compiled : ${PATCHELF_SOURCE_DIR}/patchelf-Fedora-36"
        return
    fi

    export PROOT_NO_SECCOMP=1

    # compile patchelf
    set -xv
    (cd "${PATCHELF_SOURCE_DIR}" ; bash ./bootstrap.sh)
    $PROOT -r "$OS_ROOTDIR" -b "${PATCHELF_SOURCE_DIR}:/patchelf" -w / -b /dev \
                            /bin/bash <<'EOF_fedora36_patchelf'
cd /patchelf
make clean
# BUILD PATCHELF
#bash bootstrap.sh
bash ./configure
make
cp src/patchelf /patchelf/patchelf-Fedora-36
make clean
EOF_fedora36_patchelf
    set +xv
}

fedora36_build_fakechroot()
{
    echo "fedora36_build_fakechroot : $1"
    local OS_ARCH="$1"
    local FAKECHROOT_SOURCE_DIR="$2"
    local OS_NAME="fedora"
    local OS_RELVER="36"
    local OS_ROOTDIR="${BUILD_DIR}/${OS_NAME}_${OS_RELVER}_${OS_ARCH}"
    local PROOT=""

    if [ "$OS_ARCH" = "i386" ]; then
        #PROOT="$S_PROOT_DIR/proot-x86 -q qemu-i386"
        #PROOT="$S_PROOT_DIR/proot-x86"
        PROOT="$BUILD_DIR/proot-source-x86/proot-Fedora-30.bin"
    elif [ "$OS_ARCH" = "x86_64" ]; then
        #PROOT="$S_PROOT_DIR/proot-x86_64"
        PROOT="$BUILD_DIR/proot-source-x86_64/proot-Fedora-30.bin"
    elif [ "$OS_ARCH" = "aarch64" ]; then
        #PROOT="$S_PROOT_DIR/proot-x86_64 -q qemu-aarch64"
        PROOT="$BUILD_DIR/proot-source-x86_64/proot-Fedora-30.bin -q qemu-aarch64"
    elif [ "$OS_ARCH" = "ppc64le" ]; then
        #PROOT="$S_PROOT_DIR/proot-x86_64 -q qemu-ppc64le"
        PROOT="$BUILD_DIR/proot-source-x86_64/proot-Fedora-30.bin -q qemu-ppc64le"
    else
        echo "unsupported $OS_NAME architecture: $OS_ARCH"
        exit 2
    fi

    if [ -x "${FAKECHROOT_SOURCE_DIR}/libfakechroot-Fedora-36.so" ] ; then
        echo "fakechroot binary already compiled : ${FAKECHROOT_SOURCE_DIR}/libfakechroot-Fedora-36.so"
        return
    fi

    export PROOT_NO_SECCOMP=1

    # compile fakechroot
    set -xv
    SHELL=/bin/bash CONFIG_SHELL=/bin/bash PATH=/bin:/usr/bin:/sbin:/usr/sbin \
        $PROOT -r "$OS_ROOTDIR" -b "${FAKECHROOT_SOURCE_DIR}:/fakechroot" -w / -b /dev \
            /bin/bash <<'EOF_fedora36_fakechroot'
cd /fakechroot
# BUILD FAKECHROOT
make distclean
bash ./configure
make
cp src/.libs/libfakechroot.so libfakechroot-Fedora-36.so
make clean
EOF_fedora36_fakechroot
    set +xv
}


# #############################################################################
# Fedora 38
# #############################################################################

fedora38_create_dnf()
{
    echo "fedora38_create_dnf : $1"
    local FILENAME="$1"
    local ARCH="$2"

    cat > "$FILENAME" <<EOF_fedora38_dnf
[main]
gpgcheck=0
sslverify=0
installonly_limit=3
clean_requirements_on_remove=True
reposdir=NONE

[fedora-modular]
name=Fedora Modular \$releasever - $ARCH
#baseurl=http://download.fedoraproject.org/pub/fedora/linux/releases/\$releasever/Modular/$ARCH/os/
metalink=https://mirrors.fedoraproject.org/metalink?repo=fedora-modular-\$releasever&arch=$ARCH
enabled=1
#metadata_expire=7d
repo_gpgcheck=0
type=rpm
gpgcheck=0
gpgkey=file:///etc/pki/rpm-gpg/RPM-GPG-KEY-fedora-\$releasever-$ARCH
skip_if_unavailable=False

[updates]
name=Fedora \$releasever - $ARCH - Updates
#baseurl=http://download.fedoraproject.org/pub/fedora/linux/updates/\$releasever/Everything/$ARCH/os
metalink=https://mirrors.fedoraproject.org/metalink?repo=updates-released-f\$releasever&arch=$ARCH
enabled=1
repo_gpgcheck=0
type=rpm
gpgcheck=0
metadata_expire=6h
gpgkey=file:///etc/pki/rpm-gpg/RPM-GPG-KEY-fedora-\$releasever-$ARCH
skip_if_unavailable=False

[fedora]
name=Fedora \$releasever - $ARCH
#baseurl=http://download.fedoraproject.org/pub/fedora/linux/releases/\$releasever/Everything/$ARCH/os/
metalink=https://mirrors.fedoraproject.org/metalink?repo=fedora-\$releasever&arch=$ARCH
enabled=1
metadata_expire=7d
repo_gpgcheck=0
type=rpm
gpgcheck=0
gpgkey=file:///etc/pki/rpm-gpg/RPM-GPG-KEY-fedora-\$releasever-$ARCH
skip_if_unavailable=False
EOF_fedora38_dnf
}


fedora38_setup()
{
    echo "fedora38_setup : $1"
    local OS_ARCH="$1"
    local OS_NAME="fedora"
    local OS_RELVER="38"
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
    fedora38_create_dnf "${OS_ROOTDIR}/etc/dnf/dnf.conf" "$OS_ARCH"

    $SUDO /usr/bin/dnf -y -c "${OS_ROOTDIR}/etc/dnf/dnf.conf" \
        install  --installroot="$OS_ROOTDIR" --releasever="$OS_RELVER" --forcearch="$OS_ARCH" \
            gcc kernel-devel make libtalloc libtalloc-devel glibc-static glibc-devel tar python \
	    python2 gzip zlib diffutils file glibc-headers dnf git which

    #$SUDO /usr/bin/dnf -y -c "${OS_ROOTDIR}/etc/dnf/dnf.conf" \
    #    downgrade  --installroot="$OS_ROOTDIR" --releasever="$OS_RELVER" --forcearch="$OS_ARCH" \
    #        coreutils-8.31-1.fc31.x86_64 coreutils-common-8.31-1.fc31.x86_64

    $SUDO /usr/bin/dnf -y -c "${OS_ROOTDIR}/etc/dnf/dnf.conf" \
        install  --installroot="$OS_ROOTDIR" --releasever="$OS_RELVER" --forcearch="$OS_ARCH" \
        autoconf m4 gcc-c++ libstdc++-static automake gawk libtool

    if [ "$OS_ARCH" = "aarch64" ]; then
        $SUDO chown -R "$(id -u):$(id -g)" "$OS_ROOTDIR"
	#PROOT="$S_PROOT_DIR/proot-x86_64 -q qemu-aarch64"
        PROOT="$BUILD_DIR/proot-source-x86_64/proot-Fedora-30.bin -q qemu-aarch64"
        export PROOT_NO_SECCOMP=1
	$PROOT -r "$OS_ROOTDIR" -0 -w / -b /dev -b /etc/resolv.conf /bin/bash <<'EOF_fedora38_reinstall'
dnf -y reinstall $(rpm -qa)
EOF_fedora38_reinstall
    fi

    $SUDO /usr/bin/dnf -y -c "${OS_ROOTDIR}/etc/dnf/dnf.conf" \
        clean packages

    $SUDO /bin/chown -R "$(id -u).$(id -g)" "$OS_ROOTDIR"
    $SUDO /bin/chmod -R u+rw "$OS_ROOTDIR"
}

fedora38_build_proot_c()
{
    echo "fedora38_build_proot : $1"
    local OS_ARCH="$1"
    local PROOT_SOURCE_DIR="$2"
    local OS_NAME="fedora"
    local OS_RELVER="38"
    local OS_ROOTDIR="${BUILD_DIR}/${OS_NAME}_${OS_RELVER}_${OS_ARCH}"
    local PROOT=""

    SUDO=/bin/sudo

    if [ -x "${PROOT_SOURCE_DIR}/proot-Fedora-38.bin" ] ; then
        echo "proot binary already compiled : ${PROOT_SOURCE_DIR}/proot-Fedora-38.bin"
    else
	$SUDO mount --bind "${PROOT_SOURCE_DIR}" "$OS_ROOTDIR/proot"
	$SUDO mount --bind "${S_PROOT_PACKAGES_DIR}" "$OS_ROOTDIR/proot-static-packages"
        # compile proot
        $SUDO chroot --userspec="$USER" "$OS_ROOTDIR" /bin/bash <<'EOF_fedora38_proot_1'
cd /usr/bin
rm python
ln -s python2 python
cd /proot
/bin/rm -f proot-Fedora-38.bin src/proot src/libtalloc.a src/talloc.h
/bin/rm -Rf talloc*
# BUILD TALLOC
tar xzvf /proot-static-packages/talloc.tar.gz
cd talloc*
./configure
make
cp talloc.h /proot/src
cd bin/default
[ -f talloc.c.6.o ] && ar qf libtalloc.a talloc.c.6.o
[ -f talloc.c.5.o -a ! -f libtalloc.a ] && ar qf libtalloc.a talloc.c.5.o
cp libtalloc.a /proot/src && make clean
# BUILD PROOT
cd /proot/src
make clean
make loader.elf
make loader-m32.elf
make build.h
LDFLAGS="-L/proot/usr/src -static" make proot
EOF_fedora38_proot_1
    sync
    $SUDO umount "$OS_ROOTDIR/proot"
    $SUDO umount "$OS_ROOTDIR/proot-static-packages"
    fi

    if [ -e "${PROOT_SOURCE_DIR}/src/proot" ]; then
        mv "${PROOT_SOURCE_DIR}/src/proot" "${PROOT_SOURCE_DIR}/proot-Fedora-38.bin"
    fi

    if [ ! -e "${PROOT_SOURCE_DIR}/proot-Fedora-38.bin" ]; then
        echo "proot compilation failed ${PROOT_SOURCE_DIR}/proot-Fedora-38.bin not found"
        exit 1
    fi
}


fedora38_build_proot()
{
    echo "fedora38_build_proot : $1"
    local OS_ARCH="$1"
    local PROOT_SOURCE_DIR="$2"
    local OS_NAME="fedora"
    local OS_RELVER="38"
    local OS_ROOTDIR="${BUILD_DIR}/${OS_NAME}_${OS_RELVER}_${OS_ARCH}"
    local PROOT=""

    if [ "$OS_ARCH" = "i386" ]; then
        #PROOT="$S_PROOT_DIR/proot-x86 -q qemu-i386"
        #PROOT="$S_PROOT_DIR/proot-x86"
        PROOT="$BUILD_DIR/proot-source-x86/proot-Fedora-30.bin"
    elif [ "$OS_ARCH" = "x86_64" ]; then
        #PROOT="$S_PROOT_DIR/proot-x86_64"
        PROOT="$BUILD_DIR/proot-source-x86_64/proot-Fedora-30.bin"
    elif [ "$OS_ARCH" = "aarch64" ]; then
        #PROOT="$S_PROOT_DIR/proot-x86_64 -q qemu-aarch64"
        PROOT="$BUILD_DIR/proot-source-x86_64/proot-Fedora-30.bin -q qemu-aarch64"
    else
        echo "unsupported $OS_NAME architecture: $OS_ARCH"
        exit 2
    fi

    export PROOT_NO_SECCOMP=1

    if [ -x "${PROOT_SOURCE_DIR}/proot-Fedora-38.bin" ] ; then
        echo "proot binary already compiled : ${PROOT_SOURCE_DIR}/proot-Fedora-38.bin"
    else
        # compile proot
        $PROOT -r "$OS_ROOTDIR" -b "${PROOT_SOURCE_DIR}:/proot" -w / -b /dev \
                           -b "${S_PROOT_PACKAGES_DIR}:/proot-static-packages"   /bin/bash <<'EOF_fedora38_proot_1'
cd /usr/bin
rm python
ln -s python2 python
cd /proot
/bin/rm -f proot-Fedora-38.bin src/proot src/libtalloc.a src/talloc.h
/bin/rm -Rf talloc*
# BUILD TALLOC
tar xzvf /proot-static-packages/talloc.tar.gz
cd talloc*
./configure
make
cp talloc.h /proot/src
cd bin/default
[ -f talloc.c.6.o ] && ar qf libtalloc.a talloc.c.6.o
[ -f talloc.c.5.o -a ! -f libtalloc.a ] && ar qf libtalloc.a talloc.c.5.o
cp libtalloc.a /proot/src && make clean
# BUILD PROOT
cd /proot/src
make clean
make loader.elf
make loader-m32.elf
make build.h
LDFLAGS="-L/proot/usr/src -static" make proot
EOF_fedora38_proot_1
    fi

    if [ -e "${PROOT_SOURCE_DIR}/src/proot" ]; then
        mv "${PROOT_SOURCE_DIR}/src/proot" "${PROOT_SOURCE_DIR}/proot-Fedora-38.bin"
    fi

    if [ ! -e "${PROOT_SOURCE_DIR}/proot-Fedora-38.bin" ]; then
        echo "proot compilation failed ${PROOT_SOURCE_DIR}/proot-Fedora-38.bin not found"
        exit 1
    fi
}


fedora38_build_patchelf()
{
    echo "fedora38_build_patchelf : $1"
    local OS_ARCH="$1"
    local PATCHELF_SOURCE_DIR="$2"
    local OS_NAME="fedora"
    local OS_RELVER="38"
    local OS_ROOTDIR="${BUILD_DIR}/${OS_NAME}_${OS_RELVER}_${OS_ARCH}"
    local PROOT=""

    if [ "$OS_ARCH" = "i386" ]; then
        #PROOT="$S_PROOT_DIR/proot-x86 -q qemu-i386"
        #PROOT="$S_PROOT_DIR/proot-x86"
        PROOT="$BUILD_DIR/proot-source-x86/proot-Fedora-30.bin"
    elif [ "$OS_ARCH" = "x86_64" ]; then
        #PROOT="$S_PROOT_DIR/proot-x86_64"
        PROOT="$BUILD_DIR/proot-source-x86_64/proot-Fedora-30.bin"
    elif [ "$OS_ARCH" = "aarch64" ]; then
        #PROOT="$S_PROOT_DIR/proot-x86_64 -q qemu-aarch64"
        PROOT="$BUILD_DIR/proot-source-x86_64/proot-Fedora-30.bin -q qemu-aarch64"
    elif [ "$OS_ARCH" = "ppc64le" ]; then
        #PROOT="$S_PROOT_DIR/proot-x86_64 -q qemu-ppc64le"
        PROOT="$BUILD_DIR/proot-source-x86_64/proot-Fedora-30.bin -q qemu-ppc64le"
    else
        echo "unsupported $OS_NAME architecture: $OS_ARCH"
        exit 2
    fi

    if [ -x "${PATCHELF_SOURCE_DIR}/patchelf-Fedora-38" ] ; then
        echo "patchelf binary already compiled : ${PATCHELF_SOURCE_DIR}/patchelf-Fedora-38"
        return
    fi

    export PROOT_NO_SECCOMP=1

    # compile patchelf
    set -xv
    (cd "${PATCHELF_SOURCE_DIR}" ; bash ./bootstrap.sh)
    $PROOT -r "$OS_ROOTDIR" -b "${PATCHELF_SOURCE_DIR}:/patchelf" -w / -b /dev \
                            /bin/bash <<'EOF_fedora38_patchelf'
cd /patchelf
make clean
# BUILD PATCHELF
#bash bootstrap.sh
bash ./configure
make
cp src/patchelf /patchelf/patchelf-Fedora-38
make clean
EOF_fedora38_patchelf
    set +xv
}

fedora38_build_fakechroot()
{
    echo "fedora38_build_fakechroot : $1"
    local OS_ARCH="$1"
    local FAKECHROOT_SOURCE_DIR="$2"
    local OS_NAME="fedora"
    local OS_RELVER="38"
    local OS_ROOTDIR="${BUILD_DIR}/${OS_NAME}_${OS_RELVER}_${OS_ARCH}"
    local PROOT=""

    if [ "$OS_ARCH" = "i386" ]; then
        #PROOT="$S_PROOT_DIR/proot-x86 -q qemu-i386"
        #PROOT="$S_PROOT_DIR/proot-x86"
        PROOT="$BUILD_DIR/proot-source-x86/proot-Fedora-30.bin"
    elif [ "$OS_ARCH" = "x86_64" ]; then
        #PROOT="$S_PROOT_DIR/proot-x86_64"
        PROOT="$BUILD_DIR/proot-source-x86_64/proot-Fedora-30.bin"
    elif [ "$OS_ARCH" = "aarch64" ]; then
        #PROOT="$S_PROOT_DIR/proot-x86_64 -q qemu-aarch64"
        PROOT="$BUILD_DIR/proot-source-x86_64/proot-Fedora-30.bin -q qemu-aarch64"
    elif [ "$OS_ARCH" = "ppc64le" ]; then
        #PROOT="$S_PROOT_DIR/proot-x86_64 -q qemu-ppc64le"
        PROOT="$BUILD_DIR/proot-source-x86_64/proot-Fedora-30.bin -q qemu-ppc64le"
    else
        echo "unsupported $OS_NAME architecture: $OS_ARCH"
        exit 2
    fi

    if [ -x "${FAKECHROOT_SOURCE_DIR}/libfakechroot-Fedora-38.so" ] ; then
        echo "fakechroot binary already compiled : ${FAKECHROOT_SOURCE_DIR}/libfakechroot-Fedora-38.so"
        return
    fi

    export PROOT_NO_SECCOMP=1

    # compile fakechroot
    set -xv
    SHELL=/bin/bash CONFIG_SHELL=/bin/bash PATH=/bin:/usr/bin:/sbin:/usr/sbin \
        $PROOT -r "$OS_ROOTDIR" -b "${FAKECHROOT_SOURCE_DIR}:/fakechroot" -w / -b /dev \
            /bin/bash <<'EOF_fedora38_fakechroot'
cd /fakechroot
# BUILD FAKECHROOT
make distclean
bash ./configure
make
cp src/.libs/libfakechroot.so libfakechroot-Fedora-38.so
make clean
EOF_fedora38_fakechroot
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
distroverpkg=centos-release

# PUT YOUR REPOS HERE OR IN separate files named file.repo
# in /etc/yum.repos.d
reposdir=NONE

[base]
name=CentOS-$releasever - Base
#mirrorlist=http://mirrorlist.centos.org/?release=$releasever&arch=$basearch&repo=os&infra=$infra
baseurl=http://vault.centos.org/centos/$releasever/os/$basearch/
gpgcheck=0
gpgkey=file:///etc/pki/rpm-gpg/RPM-GPG-KEY-CentOS-6

#released updates 
[updates]
name=CentOS-$releasever - Updates
#mirrorlist=http://mirrorlist.centos.org/?release=$releasever&arch=$basearch&repo=updates&infra=$infra
baseurl=http://vault.centos.org/centos/$releasever/updates/$basearch/
gpgcheck=0
gpgkey=file:///etc/pki/rpm-gpg/RPM-GPG-KEY-CentOS-6

#additional packages that may be useful
[extras]
name=CentOS-$releasever - Extras
#mirrorlist=http://mirrorlist.centos.org/?release=$releasever&arch=$basearch&repo=extras&infra=$infra
baseurl=http://vault.centos.org/centos/$releasever/extras/$basearch/
gpgcheck=0
gpgkey=file:///etc/pki/rpm-gpg/RPM-GPG-KEY-CentOS-6

#additional packages that extend functionality of existing packages
[centosplus]
name=CentOS-$releasever - Plus
#mirrorlist=http://mirrorlist.centos.org/?release=$releasever&arch=$basearch&repo=centosplus&infra=$infra
baseurl=http://vault.centos.org/centos/$releasever/centosplus/$basearch/
gpgcheck=0
enabled=0
gpgkey=file:///etc/pki/rpm-gpg/RPM-GPG-KEY-CentOS-6

#contrib - packages by Centos Users
[contrib]
name=CentOS-$releasever - Contrib
#mirrorlist=http://mirrorlist.centos.org/?release=$releasever&arch=$basearch&repo=contrib&infra=$infra
baseurl=http://vault.centos.org/centos/$releasever/contrib/$basearch/
gpgcheck=0
enabled=0
gpgkey=file:///etc/pki/rpm-gpg/RPM-GPG-KEY-CentOS-6

#[base-debuginfo]
#name=CentOS-6 - Debuginfo
#baseurl=http://debuginfo.centos.org/6/$basearch/
#gpgcheck=0
#gpgkey=file:///etc/pki/rpm-gpg/RPM-GPG-KEY-CentOS-Debug-6
#enabled=0

# EPEL

[epel]
name=Extra Packages for Enterprise Linux 6 - $basearch
#baseurl=http://archives.fedoraproject.org/pub/epel/6/$basearch
baseurl=https://archives.fedoraproject.org/pub/archive/epel/6/$basearch
#mirrorlist=https://mirrors.fedoraproject.org/metalink?repo=epel-6&arch=$basearch
failovermethod=priority
enabled=1
gpgcheck=1
gpgkey=file:///etc/pki/rpm-gpg/RPM-GPG-KEY-EPEL-6

#[epel-debuginfo]
#name=Extra Packages for Enterprise Linux 6 - $basearch - Debug
##baseurl=http://download.fedoraproject.org/pub/epel/6/$basearch/debug
#mirrorlist=https://mirrors.fedoraproject.org/metalink?repo=epel-debug-6&arch=$basearch
#failovermethod=priority
#enabled=0
#gpgkey=file:///etc/pki/rpm-gpg/RPM-GPG-KEY-EPEL-6
#gpgcheck=1
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
            gcc make libtalloc libtalloc-devel glibc-static glibc-devel \
	    tar python gzip zlib diffutils file git which

    $SUDO /usr/bin/yum -y -c "${OS_ROOTDIR}/etc/yum.conf" \
        install  --installroot="$OS_ROOTDIR" --releasever="$OS_RELVER" \
        autoconf m4 gcc-c++ automake gawk libtool

    $SUDO /usr/bin/yum -y -c "${OS_ROOTDIR}/etc/yum.conf" \
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
        #PROOT="$S_PROOT_DIR/proot-x86 -q qemu-i386"
        #PROOT="$S_PROOT_DIR/proot-x86"
        #PROOT="$S_PROOT_DIR/proot-x86"
        PROOT="$BUILD_DIR/proot-source-x86/proot-Fedora-30.bin"
    elif [ "$OS_ARCH" = "x86_64" ]; then
        #PROOT="$S_PROOT_DIR/proot-x86_64"
        PROOT="$BUILD_DIR/proot-source-x86_64/proot-Fedora-30.bin"
    elif [ "$OS_ARCH" = "aarch64" ]; then
        #PROOT="$S_PROOT_DIR/proot-x86_64 -q qemu-aarch64"
        PROOT="$BUILD_DIR/proot-source-x86_64/proot-Fedora-30.bin -q qemu-aarch64"
    elif [ "$OS_ARCH" = "ppc64le" ]; then
        #PROOT="$S_PROOT_DIR/proot-x86_64 -q qemu-ppc64le"
        PROOT="$BUILD_DIR/proot-source-x86_64/proot-Fedora-30.bin -q qemu-ppc64le"
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
reposdir=NONE

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
	    --forcearch="$OS_ARCH" \
            gcc make libtalloc libtalloc-devel glibc-static glibc-devel \
            tar python gzip zlib diffutils file git which curl libseccomp-devel \
	    libseccomp-static

    $SUDO /usr/bin/yum -y -c "${OS_ROOTDIR}/etc/yum.conf" \
        install  --installroot="$OS_ROOTDIR" --releasever="$OS_RELVER" \
            --forcearch="$OS_ARCH" \
            autoconf m4 gcc-c++ libstdc++-static automake gawk libtool xz

    REPOSECCOMP="https://cbs.centos.org/kojifiles/packages/libseccomp/2.3.0"
    curl "$REPOSECCOMP/1.el7/${OS_ARCH}/libseccomp-2.3.0-1.el7.${OS_ARCH}.rpm" > \
	    "$OS_ROOTDIR/root/libseccomp-2.3.0-1.el7.${OS_ARCH}.rpm"
    curl "$REPOSECCOMP/1.el7/${OS_ARCH}/libseccomp-static-2.3.0-1.el7.${OS_ARCH}.rpm" > \
	    "$OS_ROOTDIR/root/libseccomp-static-2.3.0-1.el7.${OS_ARCH}.rpm"
    curl "$REPOSECCOMP/1.el7/${OS_ARCH}/libseccomp-devel-2.3.0-1.el7.${OS_ARCH}.rpm" > \
	    "$OS_ROOTDIR/root/libseccomp-devel-2.3.0-1.el7.${OS_ARCH}.rpm"

    $SUDO /usr/bin/yum -y -c "${OS_ROOTDIR}/etc/yum.conf" \
        localinstall  --installroot="$OS_ROOTDIR" --releasever="$OS_RELVER" \
            --forcearch="$OS_ARCH" \
	    "$OS_ROOTDIR/root/libseccomp-2.3.0-1.el7.${OS_ARCH}.rpm" \
	    "$OS_ROOTDIR/root/libseccomp-static-2.3.0-1.el7.${OS_ARCH}.rpm" \
	    "$OS_ROOTDIR/root/libseccomp-devel-2.3.0-1.el7.${OS_ARCH}.rpm"

    $SUDO /usr/bin/yum -y -c "${OS_ROOTDIR}/etc/yum.conf" \
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
        #PROOT="$S_PROOT_DIR/proot-x86 -q qemu-i386"
        #PROOT="$S_PROOT_DIR/proot-x86"
        PROOT="$BUILD_DIR/proot-source-x86/proot-Fedora-30.bin"
    elif [ "$OS_ARCH" = "x86_64" ]; then
        #PROOT="$S_PROOT_DIR/proot-x86_64"
        PROOT="$BUILD_DIR/proot-source-x86_64/proot-Fedora-30.bin"
    elif [ "$OS_ARCH" = "aarch64" ]; then
        #PROOT="$S_PROOT_DIR/proot-x86_64 -q qemu-aarch64"
        PROOT="$BUILD_DIR/proot-source-x86_64/proot-Fedora-30.bin -q qemu-aarch64"
    elif [ "$OS_ARCH" = "ppc64le" ]; then
        #PROOT="$S_PROOT_DIR/proot-x86_64 -q qemu-ppc64le"
        PROOT="$BUILD_DIR/proot-source-x86_64/proot-Fedora-30.bin -q qemu-ppc64le"
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

centos7_build_proot()
{
    echo "centos7_build_proot : $1"
    local OS_ARCH="$1"
    local PROOT_SOURCE_DIR="$2"
    local OS_NAME="centos"
    local OS_RELVER="7"
    local OS_ROOTDIR="${BUILD_DIR}/${OS_NAME}_${OS_RELVER}_${OS_ARCH}"
    local PROOT=""

    if [ "$OS_ARCH" = "i386" ]; then
        #PROOT="$S_PROOT_DIR/proot-x86 -q qemu-i386"
        #PROOT="$S_PROOT_DIR/proot-x86"
        PROOT="$BUILD_DIR/proot-source-x86_64/proot-Fedora-30.bin"
    elif [ "$OS_ARCH" = "x86_64" ]; then
        #PROOT="$HOME/.udocker/bin/proot-x86_64"
        PROOT="$BUILD_DIR/proot-source-x86_64/proot-Fedora-30.bin"
    elif [ "$OS_ARCH" = "aarch64" ]; then
        #PROOT="$S_PROOT_DIR/proot-x86_64 -q qemu-aarch64"
        PROOT="$BUILD_DIR/proot-source-x86_64/proot-Fedora-30.bin -q qemu-aarch64"
    else
        echo "unsupported $OS_NAME architecture: $OS_ARCH"
        exit 2
    fi

    export PROOT_NO_SECCOMP=1

    if [ -x "${PROOT_SOURCE_DIR}/proot-CentOS-7.bin" ] ; then
        echo "proot binary already compiled : ${PROOT_SOURCE_DIR}/proot-CentOS-7.bin"
    else
        # compile proot
        $PROOT -r "$OS_ROOTDIR" -b "${PROOT_SOURCE_DIR}:/proot" -w / -b /dev \
                           -b "${S_PROOT_PACKAGES_DIR}:/proot-static-packages"   /bin/bash <<'EOF_centos7_proot_1'
cd /proot
/bin/rm -f proot-CentOS-7.bin src/proot src/libtalloc.a src/talloc.h
/bin/rm -Rf talloc*
# BUILD TALLOC
tar xzvf /proot-static-packages/talloc.tar.gz
cd talloc*
make clean
./configure
make
cp talloc.h /proot/src
cd bin/default
[ -f talloc.c.6.o ] && ar qf libtalloc.a talloc.c.6.o
[ -f talloc.c.5.o -a ! -f libtalloc.a ] && ar qf libtalloc.a talloc.c.5.o
cp libtalloc.a /proot/src && make clean
# BUILD PROOT
cd /proot/src
make clean
make loader.elf
make loader-m32.elf
make build.h
LDFLAGS="-L/proot/usr/src -static" make proot
EOF_centos7_proot_1
    fi

    if [ -e "${PROOT_SOURCE_DIR}/src/proot" ]; then
        mv "${PROOT_SOURCE_DIR}/src/proot" "${PROOT_SOURCE_DIR}/proot-CentOS-7.bin"
    fi

    if [ ! -e "${PROOT_SOURCE_DIR}/proot-CentOS-7.bin" ]; then
        echo "proot compilation failed ${PROOT_SOURCE_DIR}/proot-CentOS-7.bin not found"
        exit 1
    fi
}

centos7_build_patchelf()
{
    echo "centos7_build_patchelf : $1"
    local OS_ARCH="$1"
    local PATCHELF_SOURCE_DIR="$2"
    local OS_NAME="centos"
    local OS_RELVER="7"
    local OS_ROOTDIR="${BUILD_DIR}/${OS_NAME}_${OS_RELVER}_${OS_ARCH}"
    local PROOT=""

    if [ "$OS_ARCH" = "i386" ]; then
        #PROOT="$S_PROOT_DIR/proot-x86 -q qemu-i386"
        #PROOT="$S_PROOT_DIR/proot-x86"
        PROOT="$BUILD_DIR/proot-source-x86/proot-Fedora-30.bin"
    elif [ "$OS_ARCH" = "x86_64" ]; then
        #PROOT="$S_PROOT_DIR/proot-x86_64"
        PROOT="$BUILD_DIR/proot-source-x86_64/proot-Fedora-30.bin"
    elif [ "$OS_ARCH" = "aarch64" ]; then
        #PROOT="$S_PROOT_DIR/proot-x86_64 -q qemu-aarch64"
        PROOT="$BUILD_DIR/proot-source-x86_64/proot-Fedora-30.bin -q qemu-aarch64"
    elif [ "$OS_ARCH" = "ppc64le" ]; then
        #PROOT="$S_PROOT_DIR/proot-x86_64 -q qemu-ppc64le"
        PROOT="$BUILD_DIR/proot-source-x86_64/proot-Fedora-30.bin -q qemu-ppc64le"
    else
        echo "unsupported $OS_NAME architecture: $OS_ARCH"
        exit 2
    fi

    if [ -x "${PATCHELF_SOURCE_DIR}/patchelf-CentOS-7" ] ; then
        echo "patchelf binary already compiled : ${PATCHELF_SOURCE_DIR}/patchelf-CentOS-7"
        return
    fi

    export PROOT_NO_SECCOMP=1

    # compile patchelf
    set -xv
    (cd "${PATCHELF_SOURCE_DIR}" ; bash ./bootstrap.sh)
    $PROOT -r "$OS_ROOTDIR" -b "${PATCHELF_SOURCE_DIR}:/patchelf" -w / -b /dev \
                            /bin/bash <<'EOF_centos7_patchelf'
cd /patchelf
make clean
# BUILD PATCHELF
#bash bootstrap.sh
bash ./configure
make
cp src/patchelf /patchelf/patchelf-CentOS-7
make clean
EOF_centos7_patchelf
    set +xv
}


centos7_build_runc()
{
    echo "centos7_build_runc : $1"
    local OS_ARCH="$1"
    local RUNC_SOURCE_DIR="$2"
    local OS_NAME="centos"
    local OS_RELVER="7"
    local OS_ROOTDIR="${BUILD_DIR}/${OS_NAME}_${OS_RELVER}_${OS_ARCH}"
    local PROOT=""

    if [ "$OS_ARCH" = "i386" ]; then
        #PROOT="$S_PROOT_DIR/proot-x86 -q qemu-i386"
        #PROOT="$S_PROOT_DIR/proot-x86"
        PROOT="$BUILD_DIR/proot-source-x86/proot-Fedora-30.bin"
    elif [ "$OS_ARCH" = "amd64" ]; then
        #PROOT="$S_PROOT_DIR/proot-x86_64"
        PROOT="$BUILD_DIR/proot-source-x86_64/proot-Fedora-30.bin"
    elif [ "$OS_ARCH" = "arm64" ]; then
        #PROOT="$S_PROOT_DIR/proot-x86_64 -q qemu-aarch64"
        PROOT="$BUILD_DIR/proot-source-x86_64/proot-Fedora-30.bin -q qemu-aarch64"
    elif [ "$OS_ARCH" = "ppc64el" ]; then
        #PROOT="$S_PROOT_DIR/proot-x86_64 -q qemu-ppc64le"
        PROOT="$BUILD_DIR/proot-source-x86_64/proot-Fedora-30.bin -q qemu-ppc64le"
    else
        echo "unsupported $OS_NAME architecture: $OS_ARCH"
        exit 2
    fi

    if [ -x "${RUNC_SOURCE_DIR}/runc-centos-7.bin" ] ; then
        echo "runc binary already compiled : ${RUNC_SOURCE_DIR}/runc-centos-7.bin"
        return
    fi

    export PROOT_NO_SECCOMP=1

    # compile runc
    mkdir -p "${OS_ROOTDIR}/go/src/github.com/opencontainers"
    SHELL=/bin/bash CONFIG_SHELL=/bin/bash PATH=/bin:/usr/bin:/sbin:/usr/sbin:/usr/lib \
        $PROOT -0 -r "$OS_ROOTDIR" -b "${RUNC_SOURCE_DIR}:/go/src/github.com/opencontainers/runc" -w / -b /dev \
            -b /etc/resolv.conf:/etc/resolv.conf /bin/bash <<'EOF_centos7_runc'
cd /root
curl https://dl.google.com/go/go1.16.linux-amd64.tar.gz --output go.tgz
tar xzvf go.tgz
export PATH=$PATH:/root/go/bin
export GOROOT=/root/go
export GOPATH=/go
go version
export PATH=$GOPATH/bin:$GOROOT/bin:$PATH
go get github.com/sirupsen/logrus
cd /go/src/github.com/opencontainers/runc
make clean
make static
/bin/mv runc runc-centos-7.bin
EOF_centos7_runc

}


# #############################################################################
# CentOS 8 *** OLD ***
# #############################################################################

centos8_create_yum()
{
    echo "centos8_create_yum : $1"
    local FILENAME="$1"
    local ARCH="$2"

    cat > "${FILENAME}" <<'EOF_centos8_yum_conf'
[main]
cachedir=/var/cache/yum/$basearch/$releasever
keepcache=0
debuglevel=2
exactarch=1
obsoletes=1
gpgcheck=0
plugins=1
installonly_limit=5
distroverpkg=centos-release

# PUT YOUR REPOS HERE OR IN separate files named file.repo
# in /etc/yum.repos.d
reposdir=NONE


[AppStream]
name=CentOS-$releasever - AppStream
mirrorlist=http://mirrorlist.centos.org/?release=$releasever&arch=$basearch&repo=AppStream&infra=$infra
#baseurl=http://mirror.centos.org/$contentdir/$releasever/AppStream/$basearch/os/
gpgcheck=0
enabled=1
gpgkey=file:///etc/pki/rpm-gpg/RPM-GPG-KEY-centosofficial

[BaseOS]
name=CentOS-$releasever - Base
mirrorlist=http://mirrorlist.centos.org/?release=$releasever&arch=$basearch&repo=BaseOS&infra=$infra
#baseurl=http://mirror.centos.org/$contentdir/$releasever/BaseOS/$basearch/os/
gpgcheck=0
enabled=1
gpgkey=file:///etc/pki/rpm-gpg/RPM-GPG-KEY-centosofficial

[cr]
name=CentOS-$releasever - cr
baseurl=http://mirror.centos.org/$contentdir/$releasever/cr/$basearch/os/
gpgcheck=0
enabled=0
gpgkey=file:///etc/pki/rpm-gpg/RPM-GPG-KEY-centosofficial

[extras]
name=CentOS-$releasever - Extras
mirrorlist=http://mirrorlist.centos.org/?release=$releasever&arch=$basearch&repo=extras&infra=$infra
#baseurl=http://mirror.centos.org/$contentdir/$releasever/extras/$basearch/os/
gpgcheck=0
enabled=1
gpgkey=file:///etc/pki/rpm-gpg/RPM-GPG-KEY-centosofficial

[c8-media-BaseOS]
name=CentOS-BaseOS-$releasever - Media
baseurl=file:///media/CentOS/BaseOS
        file:///media/cdrom/BaseOS
        file:///media/cdrecorder/BaseOS
gpgcheck=0
enabled=0
gpgkey=file:///etc/pki/rpm-gpg/RPM-GPG-KEY-centosofficial

[c8-media-AppStream]
name=CentOS-AppStream-$releasever - Media
baseurl=file:///media/CentOS/AppStream
        file:///media/cdrom/AppStream
        file:///media/cdrecorder/AppStream
gpgcheck=1
enabled=0
gpgkey=file:///etc/pki/rpm-gpg/RPM-GPG-KEY-centosofficial

[PowerTools]
name=CentOS-$releasever - PowerTools
mirrorlist=http://mirrorlist.centos.org/?release=$releasever&arch=$basearch&repo=PowerTools&infra=$infra
#baseurl=http://mirror.centos.org/$contentdir/$releasever/PowerTools/$basearch/os/
gpgcheck=0
enabled=1
gpgkey=file:///etc/pki/rpm-gpg/RPM-GPG-KEY-centosofficial

[centosplus]
name=CentOS-$releasever - Plus
mirrorlist=http://mirrorlist.centos.org/?release=$releasever&arch=$basearch&repo=centosplus&infra=$infra
#baseurl=http://mirror.centos.org/$contentdir/$releasever/centosplus/$basearch/os/
gpgcheck=0
enabled=0
gpgkey=file:///etc/pki/rpm-gpg/RPM-GPG-KEY-centosofficial

[fasttrack]
name=CentOS-$releasever - fasttrack
mirrorlist=http://mirrorlist.centos.org/?release=$releasever&arch=$basearch&repo=fasttrack&infra=$infra
#baseurl=http://mirror.centos.org/$contentdir/$releasever/fasttrack/$basearch/os/
gpgcheck=0
enabled=0
gpgkey=file:///etc/pki/rpm-gpg/RPM-GPG-KEY-centosofficial


#############################################################

[epel-playground]
name=Extra Packages for Enterprise Linux $releasever - Playground - $basearch
#baseurl=https://download.fedoraproject.org/pub/epel/playground/$releasever/Everything/$basearch/os
metalink=https://mirrors.fedoraproject.org/metalink?repo=playground-epel$releasever&arch=$basearch&infra=$infra&content=$contentdir
failovermethod=priority
enabled=0
gpgcheck=0
gpgkey=file:///etc/pki/rpm-gpg/RPM-GPG-KEY-EPEL-8

[epel]
name=Extra Packages for Enterprise Linux $releasever - $basearch
#baseurl=https://download.fedoraproject.org/pub/epel/$releasever/Everything/$basearch
metalink=https://mirrors.fedoraproject.org/metalink?repo=epel-$releasever&arch=$basearch&infra=$infra&content=$contentdir
failovermethod=priority
enabled=1
gpgcheck=0
gpgkey=file:///etc/pki/rpm-gpg/RPM-GPG-KEY-EPEL-8
EOF_centos8_yum_conf
}


centos8_setup()
{
    echo "centos8_setup : $1"
    local OS_ARCH="$1"
    local OS_NAME="centos"
    local OS_RELVER="8"
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
    centos8_create_yum "${OS_ROOTDIR}/etc/yum.conf" "$OS_ARCH"

    $SUDO /usr/bin/yum -y -c "${OS_ROOTDIR}/etc/yum.conf" \
        install  --installroot="$OS_ROOTDIR" --releasever="$OS_RELVER" \
	--setopt=module_platform_id=platform:el$OS_RELVER \
	--forcearch="$OS_ARCH" \
        dnf dnf-data gcc make libtalloc libtalloc-devel glibc-static \
	glibc-devel tar python3 python2 gzip zlib diffutils file git which

    $SUDO /usr/bin/yum -y -c "${OS_ROOTDIR}/etc/yum.conf" \
        install  --installroot="$OS_ROOTDIR" --releasever="$OS_RELVER" \
	--forcearch="$OS_ARCH" \
        autoconf m4 gcc-c++ automake gawk libtool

    $SUDO /usr/bin/yum -y -c "${OS_ROOTDIR}/etc/yum.conf" \
        clean packages

    $SUDO /bin/chown -R "$(id -u).$(id -g)" "$OS_ROOTDIR"
    $SUDO /bin/chmod -R u+rw "$OS_ROOTDIR"
}


centos8_build_fakechroot()
{
    echo "centos8_build_fakechroot : $1"
    local OS_ARCH="$1"
    local FAKECHROOT_SOURCE_DIR="$2"
    local OS_NAME="centos"
    local OS_RELVER="8"
    local OS_ROOTDIR="${BUILD_DIR}/${OS_NAME}_${OS_RELVER}_${OS_ARCH}"
    local PROOT=""

    if [ "$OS_ARCH" = "i386" ]; then
        #PROOT="$S_PROOT_DIR/proot-x86 -q qemu-i386"
        #PROOT="$S_PROOT_DIR/proot-x86"
        PROOT="$BUILD_DIR/proot-source-x86/proot-Fedora-30.bin"
    elif [ "$OS_ARCH" = "x86_64" ]; then
        #PROOT="$S_PROOT_DIR/proot-x86_64"
        PROOT="$BUILD_DIR/proot-source-x86_64/proot-Fedora-30.bin"
    elif [ "$OS_ARCH" = "aarch64" ]; then
        #PROOT="$S_PROOT_DIR/proot-x86_64 -q qemu-aarch64"
        PROOT="$BUILD_DIR/proot-source-x86_64/proot-Fedora-30.bin -q qemu-aarch64"
    elif [ "$OS_ARCH" = "ppc64le" ]; then
        #PROOT="$S_PROOT_DIR/proot-x86_64 -q qemu-ppc64le"
        PROOT="$BUILD_DIR/proot-source-x86_64/proot-Fedora-30.bin -q qemu-ppc64le"
    else
        echo "unsupported $OS_NAME architecture: $OS_ARCH"
        exit 2
    fi

    if [ -x "${FAKECHROOT_SOURCE_DIR}/libfakechroot-CentOS-8.so" ] ; then
        echo "fakechroot binary already compiled : ${FAKECHROOT_SOURCE_DIR}/libfakechroot-CentOS-8.so"
        return
    fi

    export PROOT_NO_SECCOMP=1

    # compile fakechroot
    set -xv
    SHELL=/bin/bash CONFIG_SHELL=/bin/bash PATH=/bin:/usr/bin:/sbin:/usr/sbin \
        $PROOT -r "$OS_ROOTDIR" -b "${FAKECHROOT_SOURCE_DIR}:/fakechroot" -w / -b /dev \
            /bin/bash <<'EOF_centos8_fakechroot'
cd /fakechroot
# BUILD FAKECHROOT
make distclean
bash ./configure
make
cp src/.libs/libfakechroot.so libfakechroot-CentOS-8.so
make clean
EOF_centos8_fakechroot
    set +xv
}


# #############################################################################
# CentOS 8 *** Stream ***
# #############################################################################

centos_stream8_create_yum()
{
    echo "centos_stream8_create_yum : $1"
    local FILENAME="$1"
    local ARCH="$2"

    cat > "${FILENAME}" <<'EOF_centos_stream8_yum_conf'
[main]
cachedir=/var/cache/yum/$basearch/$releasever
keepcache=0
debuglevel=2
exactarch=1
obsoletes=1
gpgcheck=0
plugins=1
installonly_limit=5

# PUT YOUR REPOS HERE OR IN separate files named file.repo
# in /etc/yum.repos.d
reposdir=NONE

[appstream]
name=CentOS Stream $releasever - AppStream
mirrorlist=http://mirrorlist.centos.org/?release=8-stream&arch=$basearch&repo=AppStream&infra=$infra
#baseurl=http://mirror.centos.org/$contentdir/$stream/AppStream/$basearch/os/
gpgcheck=0
enabled=1
gpgkey=file:///etc/pki/rpm-gpg/RPM-GPG-KEY-centosofficial

[baseos]
name=CentOS Stream $releasever - BaseOS
mirrorlist=http://mirrorlist.centos.org/?release=8-stream&arch=$basearch&repo=BaseOS&infra=$infra
#baseurl=http://mirror.centos.org/$contentdir/$stream/BaseOS/$basearch/os/
gpgcheck=0
enabled=1
gpgkey=file:///etc/pki/rpm-gpg/RPM-GPG-KEY-centosofficial

[extras-common]
name=CentOS Stream $releasever - Extras common packages
mirrorlist=http://mirrorlist.centos.org/?release=8-stream&arch=$basearch&repo=extras-extras-common
#baseurl=http://mirror.centos.org/$contentdir/$stream/extras/$basearch/extras-common/
gpgcheck=0
enabled=1
gpgkey=file:///etc/pki/rpm-gpg/RPM-GPG-KEY-CentOS-SIG-Extras

[extras]
name=CentOS Stream $releasever - Extras
mirrorlist=http://mirrorlist.centos.org/?release=8-stream&arch=$basearch&repo=extras&infra=$infra
#baseurl=http://mirror.centos.org/$contentdir/$stream/extras/$basearch/os/
gpgcheck=0
enabled=1
gpgkey=file:///etc/pki/rpm-gpg/RPM-GPG-KEY-centosofficial

[ha]
name=CentOS Stream $releasever - HighAvailability
mirrorlist=http://mirrorlist.centos.org/?release=8-stream&arch=$basearch&repo=HighAvailability&infra=$infra
#baseurl=http://mirror.centos.org/$contentdir/$stream/HighAvailability/$basearch/os/
gpgcheck=0
enabled=0
gpgkey=file:///etc/pki/rpm-gpg/RPM-GPG-KEY-centosofficial

[media-baseos]
name=CentOS Stream $releasever - Media - BaseOS
baseurl=file:///media/CentOS/BaseOS
        file:///media/cdrom/BaseOS
        file:///media/cdrecorder/BaseOS
gpgcheck=0
enabled=0
gpgkey=file:///etc/pki/rpm-gpg/RPM-GPG-KEY-centosofficial

[media-appstream]
name=CentOS Stream $releasever - Media - AppStream
baseurl=file:///media/CentOS/AppStream
        file:///media/cdrom/AppStream
        file:///media/cdrecorder/AppStream
gpgcheck=0
enabled=0
gpgkey=file:///etc/pki/rpm-gpg/RPM-GPG-KEY-centosofficial

[nfv]
name=CentOS Stream $releasever - NFV
mirrorlist=http://mirrorlist.centos.org/?release=8-stream&arch=$basearch&repo=NFV&infra=$infra
#baseurl=http://mirror.centos.org/$contentdir/$stream/NFV/$basearch/os/
gpgcheck=0
enabled=0
gpgkey=file:///etc/pki/rpm-gpg/RPM-GPG-KEY-centosofficial

[powertools]
name=CentOS Stream $releasever - PowerTools
mirrorlist=http://mirrorlist.centos.org/?release=8-stream&arch=$basearch&repo=PowerTools&infra=$infra
#baseurl=http://mirror.centos.org/$contentdir/$stream/PowerTools/$basearch/os/
gpgcheck=0
enabled=0
gpgkey=file:///etc/pki/rpm-gpg/RPM-GPG-KEY-centosofficial

[rt]
name=CentOS Stream $releasever - RealTime
mirrorlist=http://mirrorlist.centos.org/?release=8-stream&arch=$basearch&repo=RT&infra=$infra
#baseurl=http://mirror.centos.org/$contentdir/$stream/RT/$basearch/os/
gpgcheck=0
enabled=0
gpgkey=file:///etc/pki/rpm-gpg/RPM-GPG-KEY-centosofficial

[resilientstorage]
name=CentOS Stream $releasever - ResilientStorage
mirrorlist=http://mirrorlist.centos.org/?release=8-stream&arch=$basearch&repo=ResilientStorage&infra=$infra
#baseurl=http://mirror.centos.org/$contentdir/$stream/ResilientStorage/$basearch/os/
gpgcheck=0
enabled=0
gpgkey=file:///etc/pki/rpm-gpg/RPM-GPG-KEY-centosofficial

#############################################################

[epel-playground]
name=Extra Packages for Enterprise Linux $releasever - Playground - $basearch
#baseurl=https://download.fedoraproject.org/pub/epel/playground/$releasever/Everything/$basearch/os
metalink=https://mirrors.fedoraproject.org/metalink?repo=playground-epel$releasever&arch=$basearch&infra=$infra&content=$contentdir
failovermethod=priority
enabled=0
gpgcheck=0
gpgkey=file:///etc/pki/rpm-gpg/RPM-GPG-KEY-EPEL-8

[epel]
name=Extra Packages for Enterprise Linux $releasever - $basearch
#baseurl=https://download.fedoraproject.org/pub/epel/$releasever/Everything/$basearch
metalink=https://mirrors.fedoraproject.org/metalink?repo=epel-$releasever&arch=$basearch&infra=$infra&content=$contentdir
failovermethod=priority
enabled=1
gpgcheck=0
gpgkey=file:///etc/pki/rpm-gpg/RPM-GPG-KEY-EPEL-8
EOF_centos_stream8_yum_conf
}


centos_stream8_setup()
{
    echo "centos_stream8_setup : $1"
    local OS_ARCH="$1"
    local OS_NAME="centos"
    local OS_RELVER="8"
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
    centos_stream8_create_yum "${OS_ROOTDIR}/etc/yum.conf" "$OS_ARCH"

    $SUDO /usr/bin/yum -y -c "${OS_ROOTDIR}/etc/yum.conf" \
        install  --installroot="$OS_ROOTDIR" --releasever="$OS_RELVER" \
	    --setopt=module_platform_id=platform:el${OS_RELVER} \
	    --forcearch="$OS_ARCH" \
            dnf dnf-data gcc make libtalloc libtalloc-devel glibc-devel tar \
	    python3 python2 gzip zlib diffutils file git which

    $SUDO /usr/bin/yum -y -c "${OS_ROOTDIR}/etc/yum.conf" \
        install  --installroot="$OS_ROOTDIR" --releasever="$OS_RELVER" \
	--forcearch="$OS_ARCH" \
        autoconf m4 gcc-c++ automake gawk libtool

    $SUDO /usr/bin/yum -y -c "${OS_ROOTDIR}/etc/yum.conf" \
        clean packages

    $SUDO /bin/chown -R "$(id -u).$(id -g)" "$OS_ROOTDIR"
    $SUDO /bin/chmod -R u+rw "$OS_ROOTDIR"
}


centos_stream8_build_fakechroot()
{
    echo "centos_stream8_build_fakechroot : $1"
    local OS_ARCH="$1"
    local FAKECHROOT_SOURCE_DIR="$2"
    local OS_NAME="centos"
    local OS_RELVER="8"
    local OS_ROOTDIR="${BUILD_DIR}/${OS_NAME}_${OS_RELVER}_${OS_ARCH}"
    local PROOT=""

    if [ "$OS_ARCH" = "i386" ]; then
        #PROOT="$S_PROOT_DIR/proot-x86 -q qemu-i386"
        #PROOT="$S_PROOT_DIR/proot-x86"
        PROOT="$BUILD_DIR/proot-source-x86/proot-Fedora-30.bin"
    elif [ "$OS_ARCH" = "x86_64" ]; then
        #PROOT="$S_PROOT_DIR/proot-x86_64"
        PROOT="$BUILD_DIR/proot-source-x86_64/proot-Fedora-30.bin"
    elif [ "$OS_ARCH" = "aarch64" ]; then
        #PROOT="$S_PROOT_DIR/proot-x86_64 -q qemu-aarch64"
        PROOT="$BUILD_DIR/proot-source-x86_64/proot-Fedora-30.bin -q qemu-aarch64"
    elif [ "$OS_ARCH" = "ppc64le" ]; then
        #PROOT="$S_PROOT_DIR/proot-x86_64 -q qemu-ppc64le"
        PROOT="$BUILD_DIR/proot-source-x86_64/proot-Fedora-30.bin -q qemu-ppc64le"
    else
        echo "unsupported $OS_NAME architecture: $OS_ARCH"
        exit 2
    fi

    if [ -x "${FAKECHROOT_SOURCE_DIR}/libfakechroot-CentOS-8.so" ] ; then
        echo "fakechroot binary already compiled : ${FAKECHROOT_SOURCE_DIR}/libfakechroot-CentOS-8.so"
        return
    fi

    export PROOT_NO_SECCOMP=1

    # compile fakechroot
    set -xv
    SHELL=/bin/bash CONFIG_SHELL=/bin/bash PATH=/bin:/usr/bin:/sbin:/usr/sbin \
        $PROOT -r "$OS_ROOTDIR" -b "${FAKECHROOT_SOURCE_DIR}:/fakechroot" -w / -b /dev \
            /bin/bash <<'EOF_centos_stream8_fakechroot'
cd /fakechroot
# BUILD FAKECHROOT
make distclean
bash ./configure
make
cp src/.libs/libfakechroot.so libfakechroot-CentOS-8.so
make clean
EOF_centos_stream8_fakechroot
    set +xv
}


# #############################################################################
# CentOS 9 *** Stream ***
# #############################################################################

centos_stream9_create_yum()
{
    echo "centos_stream9_create_yum : $1"
    local FILENAME="$1"
    local ARCH="$2"

    cat > "${FILENAME}" <<'EOF_centos_stream9_yum_conf'
[main]
cachedir=/var/cache/yum/$basearch/$releasever
keepcache=0
debuglevel=2
exactarch=1
obsoletes=1
gpgcheck=0
plugins=1
installonly_limit=5

# PUT YOUR REPOS HERE OR IN separate files named file.repo
# in /etc/yum.repos.d
reposdir=NONE

[highavailability]
name=CentOS Stream $releasever - HighAvailability
metalink=https://mirrors.centos.org/metalink?repo=centos-highavailability-9-stream&arch=$basearch&protocol=https,http
gpgkey=file:///etc/pki/rpm-gpg/RPM-GPG-KEY-centosofficial
gpgcheck=0
repo_gpgcheck=0
metadata_expire=6h
countme=1
enabled=0

[nfv]
name=CentOS Stream $releasever - NFV
metalink=https://mirrors.centos.org/metalink?repo=centos-nfv-9-stream&arch=$basearch&protocol=https,http
gpgkey=file:///etc/pki/rpm-gpg/RPM-GPG-KEY-centosofficial
gpgcheck=0
repo_gpgcheck=0
metadata_expire=6h
countme=1
enabled=0

[rt]
name=CentOS Stream $releasever - RT
metalink=https://mirrors.centos.org/metalink?repo=centos-rt-9-stream&arch=$basearch&protocol=https,http
gpgkey=file:///etc/pki/rpm-gpg/RPM-GPG-KEY-centosofficial
gpgcheck=0
repo_gpgcheck=0
metadata_expire=6h
countme=1
enabled=0

[resilientstorage]
name=CentOS Stream $releasever - ResilientStorage
metalink=https://mirrors.centos.org/metalink?repo=centos-resilientstorage-9-stream&arch=$basearch&protocol=https,http
gpgkey=file:///etc/pki/rpm-gpg/RPM-GPG-KEY-centosofficial
gpgcheck=0
repo_gpgcheck=0
metadata_expire=6h
countme=1
enabled=0

[extras-common]
name=CentOS Stream $releasever - Extras packages
metalink=https://mirrors.centos.org/metalink?repo=centos-extras-sig-extras-common-9-stream&arch=$basearch&protocol=https,http
gpgkey=file:///etc/pki/rpm-gpg/RPM-GPG-KEY-CentOS-SIG-Extras-SHA512
gpgcheck=0
repo_gpgcheck=0
metadata_expire=6h
countme=1
enabled=1

[baseos]
name=CentOS Stream $releasever - BaseOS
metalink=https://mirrors.centos.org/metalink?repo=centos-baseos-9-stream&arch=$basearch&protocol=https,http
gpgkey=file:///etc/pki/rpm-gpg/RPM-GPG-KEY-centosofficial
gpgcheck=0
repo_gpgcheck=0
metadata_expire=6h
countme=1
enabled=1

[appstream]
name=CentOS Stream $releasever - AppStream
metalink=https://mirrors.centos.org/metalink?repo=centos-appstream-9-stream&arch=$basearch&protocol=https,http
gpgkey=file:///etc/pki/rpm-gpg/RPM-GPG-KEY-centosofficial
gpgcheck=0
repo_gpgcheck=0
metadata_expire=6h
countme=1
enabled=1

[crb]
name=CentOS Stream $releasever - CRB
metalink=https://mirrors.centos.org/metalink?repo=centos-crb-9-stream&arch=$basearch&protocol=https,http
gpgkey=file:///etc/pki/rpm-gpg/RPM-GPG-KEY-centosofficial
gpgcheck=0
repo_gpgcheck=0
metadata_expire=6h
countme=1
enabled=0

#############################################################

[epel-playground]
name=Extra Packages for Enterprise Linux $releasever - Playground - $basearch
#baseurl=https://download.fedoraproject.org/pub/epel/playground/$releasever/Everything/$basearch/os
metalink=https://mirrors.fedoraproject.org/metalink?repo=playground-epel$releasever&arch=$basearch&infra=$infra&content=$contentdir
failovermethod=priority
enabled=0
gpgcheck=0
gpgkey=file:///etc/pki/rpm-gpg/RPM-GPG-KEY-EPEL-9

[epel]
name=Extra Packages for Enterprise Linux $releasever - $basearch
#baseurl=https://download.fedoraproject.org/pub/epel/$releasever/Everything/$basearch
metalink=https://mirrors.fedoraproject.org/metalink?repo=epel-$releasever&arch=$basearch&infra=$infra&content=$contentdir
failovermethod=priority
enabled=1
gpgcheck=0
gpgkey=file:///etc/pki/rpm-gpg/RPM-GPG-KEY-EPEL-9
EOF_centos_stream9_yum_conf
}


centos_stream9_setup()
{
    echo "centos_stream9_setup : $1"
    local OS_ARCH="$1"
    local OS_NAME="centos"
    local OS_RELVER="9"
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
    centos_stream9_create_yum "${OS_ROOTDIR}/etc/yum.conf" "$OS_ARCH"

    $SUDO /usr/bin/yum -y -c "${OS_ROOTDIR}/etc/yum.conf" \
        install  --installroot="$OS_ROOTDIR" --releasever="$OS_RELVER" \
	--setopt=module_platform_id=platform:el${OS_RELVER} \
	--forcearch="$OS_ARCH" \
        dnf dnf-data gcc make libtalloc libtalloc-devel glibc-devel tar \
	python3 python2 gzip zlib diffutils file git which

    $SUDO /usr/bin/yum -y -c "${OS_ROOTDIR}/etc/yum.conf" \
        install  --installroot="$OS_ROOTDIR" --releasever="$OS_RELVER" \
	--forcearch="$OS_ARCH" \
        autoconf m4 gcc-c++ automake gawk libtool

    $SUDO /usr/bin/yum -y -c "${OS_ROOTDIR}/etc/yum.conf" \
        clean packages

    $SUDO /bin/chown -R "$(id -u).$(id -g)" "$OS_ROOTDIR"
    $SUDO /bin/chmod -R u+rw "$OS_ROOTDIR"
}


centos_stream9_build_fakechroot()
{
    echo "centos_stream9_build_fakechroot : $1"
    local OS_ARCH="$1"
    local FAKECHROOT_SOURCE_DIR="$2"
    local OS_NAME="centos"
    local OS_RELVER="9"
    local OS_ROOTDIR="${BUILD_DIR}/${OS_NAME}_${OS_RELVER}_${OS_ARCH}"
    local PROOT=""

    if [ "$OS_ARCH" = "i386" ]; then
        #PROOT="$S_PROOT_DIR/proot-x86 -q qemu-i386"
        #PROOT="$S_PROOT_DIR/proot-x86"
        PROOT="$BUILD_DIR/proot-source-x86/proot-Fedora-30.bin"
    elif [ "$OS_ARCH" = "x86_64" ]; then
        #PROOT="$S_PROOT_DIR/proot-x86_64"
        PROOT="$BUILD_DIR/proot-source-x86_64/proot-Fedora-30.bin"
    elif [ "$OS_ARCH" = "aarch64" ]; then
        #PROOT="$S_PROOT_DIR/proot-x86_64 -q qemu-aarch64"
        PROOT="$BUILD_DIR/proot-source-x86_64/proot-Fedora-30.bin -q qemu-aarch64"
    elif [ "$OS_ARCH" = "ppc64le" ]; then
        #PROOT="$S_PROOT_DIR/proot-x86_64 -q qemu-ppc64le"
        PROOT="$BUILD_DIR/proot-source-x86_64/proot-Fedora-30.bin -q qemu-ppc64le"
    else
        echo "unsupported $OS_NAME architecture: $OS_ARCH"
        exit 2
    fi

    if [ -x "${FAKECHROOT_SOURCE_DIR}/libfakechroot-CentOS-9.so" ] ; then
        echo "fakechroot binary already compiled : ${FAKECHROOT_SOURCE_DIR}/libfakechroot-CentOS-9.so"
        return
    fi

    export PROOT_NO_SECCOMP=1

    # compile fakechroot
    set -xv
    SHELL=/bin/bash CONFIG_SHELL=/bin/bash PATH=/bin:/usr/bin:/sbin:/usr/sbin \
        $PROOT -r "$OS_ROOTDIR" -b "${FAKECHROOT_SOURCE_DIR}:/fakechroot" -w / -b /dev \
            /bin/bash <<'EOF_centos_stream9_fakechroot'
cd /fakechroot
# BUILD FAKECHROOT
make distclean
bash ./configure
make
cp src/.libs/libfakechroot.so libfakechroot-CentOS-9.so
make clean
EOF_centos_stream9_fakechroot
    set +xv
}


# #############################################################################
# Rocky 8
# #############################################################################

rocky8_create_yum()
{
    echo "rocky8_create_yum : $1"
    local FILENAME="$1"
    local ARCH="$2"

    cat > "${FILENAME}" <<'EOF_rocky8_yum_conf'
[main]
cachedir=/var/cache/yum/$basearch/$releasever
keepcache=0
debuglevel=2
exactarch=1
obsoletes=1
gpgcheck=0
plugins=1
installonly_limit=5
distroverpkg=centos-release

# PUT YOUR REPOS HERE OR IN separate files named file.repo
# in /etc/yum.repos.d
reposdir=NONE

[appstream]
name=Rocky Linux $releasever - AppStream
mirrorlist=https://mirrors.rockylinux.org/mirrorlist?arch=$basearch&repo=AppStream-$releasever
#baseurl=http://dl.rockylinux.org/$contentdir/$releasever/AppStream/$basearch/os/
gpgcheck=0
enabled=1
countme=1
gpgkey=file:///etc/pki/rpm-gpg/RPM-GPG-KEY-rockyofficial

[baseos]
name=Rocky Linux $releasever - BaseOS
mirrorlist=https://mirrors.rockylinux.org/mirrorlist?arch=$basearch&repo=BaseOS-$releasever
#baseurl=http://dl.rockylinux.org/$contentdir/$releasever/BaseOS/$basearch/os/
gpgcheck=0
enabled=1
countme=1
gpgkey=file:///etc/pki/rpm-gpg/RPM-GPG-KEY-rockyofficial

[extras]
name=Rocky Linux $releasever - Extras
mirrorlist=https://mirrors.rockylinux.org/mirrorlist?arch=$basearch&repo=extras-$releasever
#baseurl=http://dl.rockylinux.org/$contentdir/$releasever/extras/$basearch/os/
gpgcheck=0
enabled=1
countme=1
gpgkey=file:///etc/pki/rpm-gpg/RPM-GPG-KEY-rockyofficial

[ha]
name=Rocky Linux $releasever - HighAvailability
mirrorlist=https://mirrors.rockylinux.org/mirrorlist?arch=$basearch&repo=HighAvailability-$releasever
#baseurl=http://dl.rockylinux.org/$contentdir/$releasever/HighAvailability/$basearch/os/
gpgcheck=0
enabled=0
countme=1
gpgkey=file:///etc/pki/rpm-gpg/RPM-GPG-KEY-rockyofficial

[media-baseos]
name=Rocky Linux $releasever - Media - BaseOS
baseurl=file:///media/Rocky/BaseOS
        file:///media/cdrom/BaseOS
        file:///media/cdrecorder/BaseOS
gpgcheck=0
enabled=0
gpgkey=file:///etc/pki/rpm-gpg/RPM-GPG-KEY-rockyofficial

[media-appstream]
name=Rocky Linux $releasever - Media - AppStream
baseurl=file:///media/Rocky/AppStream
        file:///media/cdrom/AppStream
        file:///media/cdrecorder/AppStream
gpgcheck=0
enabled=0
gpgkey=file:///etc/pki/rpm-gpg/RPM-GPG-KEY-rockyofficial

[nfv]
name=Rocky Linux $releasever - NFV
mirrorlist=https://mirrors.rockylinux.org/mirrorlist?arch=$basearch&repo=NFV-$releasever
#baseurl=http://dl.rockylinux.org/$contentdir/$releasever/nfv/$basearch/os/
gpgcheck=0
enabled=0
countme=1
gpgkey=file:///etc/pki/rpm-gpg/RPM-GPG-KEY-rockyofficial

[plus]
name=Rocky Linux $releasever - Plus
mirrorlist=https://mirrors.rockylinux.org/mirrorlist?arch=$basearch&repo=rockyplus-$releasever
#baseurl=http://dl.rockylinux.org/$contentdir/$releasever/plus/$basearch/os/
gpgcheck=0
enabled=0
countme=1
gpgkey=file:///etc/pki/rpm-gpg/RPM-GPG-KEY-rockyofficial

[powertools]
name=Rocky Linux $releasever - PowerTools
mirrorlist=https://mirrors.rockylinux.org/mirrorlist?arch=$basearch&repo=PowerTools-$releasever
#baseurl=http://dl.rockylinux.org/$contentdir/$releasever/PowerTools/$basearch/os/
gpgcheck=0
enabled=0
countme=1
gpgkey=file:///etc/pki/rpm-gpg/RPM-GPG-KEY-rockyofficial

[resilient-storage]
name=Rocky Linux $releasever - ResilientStorage
mirrorlist=https://mirrors.rockylinux.org/mirrorlist?arch=$basearch&repo=ResilientStorage-$releasever
#baseurl=http://dl.rockylinux.org/$contentdir/$releasever/ResilientStorage/$basearch/os/
gpgcheck=0
enabled=0
countme=1
gpgkey=file:///etc/pki/rpm-gpg/RPM-GPG-KEY-rockyofficial

[rt]
name=Rocky Linux $releasever - Realtime
mirrorlist=https://mirrors.rockylinux.org/mirrorlist?arch=$basearch&repo=RT-$releasever
#baseurl=http://dl.rockylinux.org/$contentdir/$releasever/RT/$basearch/os/
gpgcheck=0
enabled=0
countme=1
gpgkey=file:///etc/pki/rpm-gpg/RPM-GPG-KEY-rockyofficial


#############################################################

[epel-playground]
name=Extra Packages for Enterprise Linux $releasever - Playground - $basearch
#baseurl=https://download.fedoraproject.org/pub/epel/playground/$releasever/Everything/$basearch/os
metalink=https://mirrors.fedoraproject.org/metalink?repo=playground-epel$releasever&arch=$basearch&infra=$infra&content=$contentdir
failovermethod=priority
enabled=0
gpgcheck=0
gpgkey=file:///etc/pki/rpm-gpg/RPM-GPG-KEY-EPEL-8

[epel]
name=Extra Packages for Enterprise Linux $releasever - $basearch
#baseurl=https://download.fedoraproject.org/pub/epel/$releasever/Everything/$basearch
metalink=https://mirrors.fedoraproject.org/metalink?repo=epel-$releasever&arch=$basearch&infra=$infra&content=$contentdir
failovermethod=priority
enabled=1
gpgcheck=0
gpgkey=file:///etc/pki/rpm-gpg/RPM-GPG-KEY-EPEL-8
EOF_rocky8_yum_conf
}


rocky8_setup()
{
    echo "rocky8_setup : $1"
    local OS_ARCH="$1"
    local OS_NAME="rocky"
    local OS_RELVER="8"
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
    rocky8_create_yum "${OS_ROOTDIR}/etc/yum.conf" "$OS_ARCH"

    $SUDO /usr/bin/yum -y -c "${OS_ROOTDIR}/etc/yum.conf" \
        install  --installroot="$OS_ROOTDIR" --releasever="$OS_RELVER" \
	--setopt=module_platform_id=platform:el$OS_RELVER \
	--forcearch="$OS_ARCH" \
        dnf rpm dnf-data gcc make libtalloc libtalloc-devel glibc-devel tar \
	python3 python2 gzip zlib diffutils file git which

    $SUDO /usr/bin/yum -y -c "${OS_ROOTDIR}/etc/yum.conf" \
        install  --installroot="$OS_ROOTDIR" --releasever="$OS_RELVER" \
	--forcearch="$OS_ARCH" --enablerepo=crb \
        autoconf m4 gcc-c++ libstdc++-static glibc-static automake gawk libtool

    $SUDO /usr/bin/yum -y -c "${OS_ROOTDIR}/etc/yum.conf" \
        clean packages

    $SUDO /bin/chown -R "$(id -u).$(id -g)" "$OS_ROOTDIR"
    $SUDO /bin/chmod -R u+rw "$OS_ROOTDIR"
}


rocky8_build_fakechroot()
{
    echo "rocky8_build_fakechroot : $1"
    local OS_ARCH="$1"
    local FAKECHROOT_SOURCE_DIR="$2"
    local OS_NAME="rocky"
    local OS_RELVER="8"
    local OS_ROOTDIR="${BUILD_DIR}/${OS_NAME}_${OS_RELVER}_${OS_ARCH}"
    local PROOT=""

    if [ "$OS_ARCH" = "i386" ]; then
        #PROOT="$S_PROOT_DIR/proot-x86 -q qemu-i386"
        #PROOT="$S_PROOT_DIR/proot-x86"
        PROOT="$BUILD_DIR/proot-source-x86/proot-Fedora-30.bin"
    elif [ "$OS_ARCH" = "x86_64" ]; then
        #PROOT="$S_PROOT_DIR/proot-x86_64"
        PROOT="$BUILD_DIR/proot-source-x86_64/proot-Fedora-30.bin"
    elif [ "$OS_ARCH" = "aarch64" ]; then
        #PROOT="$S_PROOT_DIR/proot-x86_64 -q qemu-aarch64"
        PROOT="$BUILD_DIR/proot-source-x86_64/proot-Fedora-30.bin -q qemu-aarch64"
    elif [ "$OS_ARCH" = "ppc64le" ]; then
        #PROOT="$S_PROOT_DIR/proot-x86_64 -q qemu-ppc64le"
        PROOT="$BUILD_DIR/proot-source-x86_64/proot-Fedora-30.bin -q qemu-ppc64le"
    else
        echo "unsupported $OS_NAME architecture: $OS_ARCH"
        exit 2
    fi

    if [ -x "${FAKECHROOT_SOURCE_DIR}/libfakechroot-Rocky-8.so" ] ; then
        echo "fakechroot binary already compiled : ${FAKECHROOT_SOURCE_DIR}/libfakechroot-Rocky-8.so"
        return
    fi

    export PROOT_NO_SECCOMP=1

    # compile fakechroot
    set -xv
    SHELL=/bin/bash CONFIG_SHELL=/bin/bash PATH=/bin:/usr/bin:/sbin:/usr/sbin \
        $PROOT -r "$OS_ROOTDIR" -b "${FAKECHROOT_SOURCE_DIR}:/fakechroot" -w / -b /dev \
            /bin/bash <<'EOF_rocky8_fakechroot'
cd /fakechroot
# BUILD FAKECHROOT
make distclean
bash ./configure
make
cp src/.libs/libfakechroot.so libfakechroot-Rocky-8.so
make clean
EOF_rocky8_fakechroot
    set +xv
}



# #############################################################################
# Rocky 9
# #############################################################################

rocky9_create_yum()
{
    echo "rocky9_create_yum : $1"
    local FILENAME="$1"
    local ARCH="$2"

    cat > "${FILENAME}" <<'EOF_rocky9_yum_conf'
[main]
cachedir=/var/cache/yum/$basearch/$releasever
keepcache=0
debuglevel=2
exactarch=1
obsoletes=1
gpgcheck=0
plugins=1
installonly_limit=5

# PUT YOUR REPOS HERE OR IN separate files named file.repo
# in /etc/yum.repos.d
reposdir=NONE


[highavailability]
name=Rocky Linux $releasever - High Availability
mirrorlist=https://mirrors.rockylinux.org/mirrorlist?arch=$basearch&repo=HighAvailability-$releasever
#baseurl=http://dl.rockylinux.org/$contentdir/$releasever/HighAvailability/$basearch/os/
gpgcheck=0
enabled=0
countme=1
metadata_expire=6h
gpgkey=file:///etc/pki/rpm-gpg/RPM-GPG-KEY-Rocky-9

[resilientstorage]
name=Rocky Linux $releasever - Resilient Storage
mirrorlist=https://mirrors.rockylinux.org/mirrorlist?arch=$basearch&repo=ResilientStorage-$releasever
#baseurl=http://dl.rockylinux.org/$contentdir/$releasever/ResilientStorage/$basearch/os/
gpgcheck=0
enabled=0
countme=1
metadata_expire=6h
gpgkey=file:///etc/pki/rpm-gpg/RPM-GPG-KEY-Rocky-9

[nfv]
name=Rocky Linux $releasever - NFV
mirrorlist=https://mirrors.rockylinux.org/mirrorlist?arch=$basearch&repo=NFV-$releasever
#baseurl=http://dl.rockylinux.org/$contentdir/$releasever/NFV/$basearch/os/
gpgcheck=0
enabled=0
countme=1
metadata_expire=6h
gpgkey=file:///etc/pki/rpm-gpg/RPM-GPG-KEY-Rocky-9

[rt]
name=Rocky Linux $releasever - Realtime
mirrorlist=https://mirrors.rockylinux.org/mirrorlist?arch=$basearch&repo=RT-$releasever
#baseurl=http://dl.rockylinux.org/$contentdir/$releasever/RT/$basearch/os/
gpgcheck=0
enabled=0
countme=1
metadata_expire=6h
gpgkey=file:///etc/pki/rpm-gpg/RPM-GPG-KEY-Rocky-9

[sap]
name=Rocky Linux $releasever - SAP
mirrorlist=https://mirrors.rockylinux.org/mirrorlist?arch=$basearch&repo=SAP-$releasever
#baseurl=http://dl.rockylinux.org/$contentdir/$releasever/SAP/$basearch/os/
gpgcheck=0
enabled=0
countme=1
metadata_expire=6h
gpgkey=file:///etc/pki/rpm-gpg/RPM-GPG-KEY-Rocky-9

[saphana]
name=Rocky Linux $releasever - SAPHANA
mirrorlist=https://mirrors.rockylinux.org/mirrorlist?arch=$basearch&repo=SAPHANA-$releasever
#baseurl=http://dl.rockylinux.org/$contentdir/$releasever/SAPHANA/$basearch/os/
gpgcheck=0
enabled=0
countme=1
metadata_expire=6h
gpgkey=file:///etc/pki/rpm-gpg/RPM-GPG-KEY-Rocky-9

[devel]
name=Rocky Linux $releasever - Devel WARNING! FOR BUILDROOT ONLY DO NOT LEAVE ENABLED
mirrorlist=https://mirrors.rockylinux.org/mirrorlist?arch=$basearch&repo=devel-$releasever
#baseurl=http://dl.rockylinux.org/$contentdir/$releasever/devel/$basearch/os/
gpgcheck=0
enabled=0
countme=1
gpgkey=file:///etc/pki/rpm-gpg/RPM-GPG-KEY-Rocky-9

[extras]
name=Rocky Linux $releasever - Extras
mirrorlist=https://mirrors.rockylinux.org/mirrorlist?arch=$basearch&repo=extras-$releasever
#baseurl=http://dl.rockylinux.org/$contentdir/$releasever/extras/$basearch/os/
gpgcheck=0
enabled=1
countme=1
metadata_expire=6h
gpgkey=file:///etc/pki/rpm-gpg/RPM-GPG-KEY-Rocky-9

[plus]
name=Rocky Linux $releasever - Plus
mirrorlist=https://mirrors.rockylinux.org/mirrorlist?arch=$basearch&repo=rockyplus-$releasever
#baseurl=http://dl.rockylinux.org/$contentdir/$releasever/plus/$basearch/os/
gpgcheck=0
enabled=0
countme=1
metadata_expire=6h
gpgkey=file:///etc/pki/rpm-gpg/RPM-GPG-KEY-Rocky-9

[baseos]
name=Rocky Linux $releasever - BaseOS
mirrorlist=https://mirrors.rockylinux.org/mirrorlist?arch=$basearch&repo=BaseOS-$releasever
#baseurl=http://dl.rockylinux.org/$contentdir/$releasever/BaseOS/$basearch/os/
gpgcheck=0
enabled=1
countme=1
metadata_expire=6h
gpgkey=file:///etc/pki/rpm-gpg/RPM-GPG-KEY-Rocky-9

[appstream]
name=Rocky Linux $releasever - AppStream
mirrorlist=https://mirrors.rockylinux.org/mirrorlist?arch=$basearch&repo=AppStream-$releasever
#baseurl=http://dl.rockylinux.org/$contentdir/$releasever/AppStream/$basearch/os/
gpgcheck=0
enabled=1
countme=1
metadata_expire=6h
gpgkey=file:///etc/pki/rpm-gpg/RPM-GPG-KEY-Rocky-9

[crb]
name=Rocky Linux $releasever - CRB
mirrorlist=https://mirrors.rockylinux.org/mirrorlist?arch=$basearch&repo=CRB-$releasever
#baseurl=http://dl.rockylinux.org/$contentdir/$releasever/CRB/$basearch/os/
gpgcheck=0
enabled=0
countme=1
metadata_expire=6h
gpgkey=file:///etc/pki/rpm-gpg/RPM-GPG-KEY-Rocky-9


#############################################################

[epel-playground]
name=Extra Packages for Enterprise Linux $releasever - Playground - $basearch
#baseurl=https://download.fedoraproject.org/pub/epel/playground/$releasever/Everything/$basearch/os
metalink=https://mirrors.fedoraproject.org/metalink?repo=playground-epel$releasever&arch=$basearch&infra=$infra&content=$contentdir
failovermethod=priority
enabled=0
gpgcheck=0
gpgkey=file:///etc/pki/rpm-gpg/RPM-GPG-KEY-EPEL-9

[epel]
name=Extra Packages for Enterprise Linux $releasever - $basearch
#baseurl=https://download.fedoraproject.org/pub/epel/$releasever/Everything/$basearch
metalink=https://mirrors.fedoraproject.org/metalink?repo=epel-$releasever&arch=$basearch&infra=$infra&content=$contentdir
failovermethod=priority
enabled=1
gpgcheck=0
gpgkey=file:///etc/pki/rpm-gpg/RPM-GPG-KEY-EPEL-9
EOF_rocky9_yum_conf
}


rocky9_setup()
{
    echo "rocky9_setup : $1"
    local OS_ARCH="$1"
    local OS_NAME="rocky"
    local OS_RELVER="9"
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
    rocky9_create_yum "${OS_ROOTDIR}/etc/yum.conf" "$OS_ARCH"

    $SUDO /usr/bin/yum -y -c "${OS_ROOTDIR}/etc/yum.conf" \
        install  --installroot="$OS_ROOTDIR" --releasever="$OS_RELVER" \
	--setopt=module_platform_id=platform:el$OS_RELVER \
	--forcearch="$OS_ARCH" \
        dnf rpm dnf-data gcc make libtalloc libtalloc-devel glibc-devel tar \
	python3 python2 gzip zlib diffutils file git which

    $SUDO /usr/bin/yum -y -c "${OS_ROOTDIR}/etc/yum.conf" \
        install  --installroot="$OS_ROOTDIR" --releasever="$OS_RELVER" \
	--forcearch="$OS_ARCH" --enablerepo=crb \
        autoconf m4 gcc-c++ libstdc++-static glibc-static automake gawk libtool

    $SUDO /usr/bin/yum -y -c "${OS_ROOTDIR}/etc/yum.conf" \
        clean packages

    $SUDO /bin/chown -R "$(id -u).$(id -g)" "$OS_ROOTDIR"
    $SUDO /bin/chmod -R u+rw "$OS_ROOTDIR"
}


rocky9_build_fakechroot()
{
    echo "rocky9_build_fakechroot : $1"
    local OS_ARCH="$1"
    local FAKECHROOT_SOURCE_DIR="$2"
    local OS_NAME="rocky"
    local OS_RELVER="9"
    local OS_ROOTDIR="${BUILD_DIR}/${OS_NAME}_${OS_RELVER}_${OS_ARCH}"
    local PROOT=""

    if [ "$OS_ARCH" = "i386" ]; then
        #PROOT="$S_PROOT_DIR/proot-x86 -q qemu-i386"
        #PROOT="$S_PROOT_DIR/proot-x86"
        PROOT="$BUILD_DIR/proot-source-x86/proot-Fedora-30.bin"
    elif [ "$OS_ARCH" = "x86_64" ]; then
        #PROOT="$S_PROOT_DIR/proot-x86_64"
        PROOT="$BUILD_DIR/proot-source-x86_64/proot-Fedora-30.bin"
    elif [ "$OS_ARCH" = "aarch64" ]; then
        #PROOT="$S_PROOT_DIR/proot-x86_64 -q qemu-aarch64"
        PROOT="$BUILD_DIR/proot-source-x86_64/proot-Fedora-30.bin -q qemu-aarch64"
    elif [ "$OS_ARCH" = "ppc64le" ]; then
        #PROOT="$S_PROOT_DIR/proot-x86_64 -q qemu-ppc64le"
	PROOT="$BUILD_DIR/proot-source-x86_64/proot-Fedora-30.bin -q qemu-ppc64le"
    else
        echo "unsupported $OS_NAME architecture: $OS_ARCH"
        exit 2
    fi

    if [ -x "${FAKECHROOT_SOURCE_DIR}/libfakechroot-Rocky-9.so" ] ; then
        echo "fakechroot binary already compiled : ${FAKECHROOT_SOURCE_DIR}/libfakechroot-Rocky-9.so"
        return
    fi

    export PROOT_NO_SECCOMP=1

    # compile fakechroot
    set -xv
    SHELL=/bin/bash CONFIG_SHELL=/bin/bash PATH=/bin:/usr/bin:/sbin:/usr/sbin \
        $PROOT -r "$OS_ROOTDIR" -b "${FAKECHROOT_SOURCE_DIR}:/fakechroot" -w / -b /dev \
            /bin/bash <<'EOF_rocky9_fakechroot'
cd /fakechroot
# BUILD FAKECHROOT
make distclean
bash ./configure
make
cp src/.libs/libfakechroot.so libfakechroot-Rocky-9.so
make clean
EOF_rocky9_fakechroot
    set +xv
}



# #############################################################################
# Alma 8
# #############################################################################

alma8_create_yum()
{
    echo "alma8_create_yum : $1"
    local FILENAME="$1"
    local ARCH="$2"

    cat > "${FILENAME}" <<'EOF_alma8_yum_conf'
[main]
cachedir=/var/cache/yum/$basearch/$releasever
keepcache=0
debuglevel=2
exactarch=1
obsoletes=1
gpgcheck=0
plugins=1
installonly_limit=5

# PUT YOUR REPOS HERE OR IN separate files named file.repo
# in /etc/yum.repos.d
reposdir=NONE

[appstream]
name=AlmaLinux $releasever - AppStream
mirrorlist=https://mirrors.almalinux.org/mirrorlist/$releasever/appstream
# baseurl=https://repo.almalinux.org/almalinux/$releasever/AppStream/$basearch/os/
enabled=1
gpgcheck=0
countme=1
gpgkey=file:///etc/pki/rpm-gpg/RPM-GPG-KEY-AlmaLinux-8
metadata_expire=86400
enabled_metadata=1

[baseos]
name=AlmaLinux $releasever - BaseOS
mirrorlist=https://mirrors.almalinux.org/mirrorlist/$releasever/baseos
# baseurl=https://repo.almalinux.org/almalinux/$releasever/BaseOS/$basearch/os/
enabled=1
gpgcheck=0
countme=1
gpgkey=file:///etc/pki/rpm-gpg/RPM-GPG-KEY-AlmaLinux-8
metadata_expire=86400
enabled_metadata=1

[crb]
name=AlmaLinux $releasever - CRB
mirrorlist=https://mirrors.almalinux.org/mirrorlist/$releasever/crb
# baseurl=https://repo.almalinux.org/almalinux/$releasever/CRB/$basearch/os/
enabled=0
gpgcheck=0
countme=1
gpgkey=file:///etc/pki/rpm-gpg/RPM-GPG-KEY-AlmaLinux-8
metadata_expire=86400
enabled_metadata=0

[extras]
name=AlmaLinux $releasever - Extras
mirrorlist=https://mirrors.almalinux.org/mirrorlist/$releasever/extras
# baseurl=https://repo.almalinux.org/almalinux/$releasever/extras/$basearch/os/
enabled=1
gpgcheck=0
countme=1
gpgkey=file:///etc/pki/rpm-gpg/RPM-GPG-KEY-AlmaLinux-8
metadata_expire=86400
enabled_metadata=0

[highavailability]
name=AlmaLinux $releasever - HighAvailability
mirrorlist=https://mirrors.almalinux.org/mirrorlist/$releasever/highavailability
# baseurl=https://repo.almalinux.org/almalinux/$releasever/HighAvailability/$basearch/os/
enabled=0
gpgcheck=0
countme=1
gpgkey=file:///etc/pki/rpm-gpg/RPM-GPG-KEY-AlmaLinux-8
metadata_expire=86400
enabled_metadata=0

[nfv]
name=AlmaLinux $releasever - NFV
mirrorlist=https://mirrors.almalinux.org/mirrorlist/$releasever/nfv
# baseurl=https://repo.almalinux.org/almalinux/$releasever/NFV/$basearch/os/
enabled=0
gpgcheck=0
countme=1
gpgkey=file:///etc/pki/rpm-gpg/RPM-GPG-KEY-AlmaLinux-8
metadata_expire=86400
enabled_metadata=0

[plus]
name=AlmaLinux $releasever - Plus
mirrorlist=https://mirrors.almalinux.org/mirrorlist/$releasever/plus
# baseurl=https://repo.almalinux.org/almalinux/$releasever/plus/$basearch/os/
enabled=0
gpgcheck=0
countme=1
gpgkey=file:///etc/pki/rpm-gpg/RPM-GPG-KEY-AlmaLinux-8
metadata_expire=86400
enabled_metadata=0

[resilientstorage]
name=AlmaLinux $releasever - ResilientStorage
mirrorlist=https://mirrors.almalinux.org/mirrorlist/$releasever/resilientstorage
# baseurl=https://repo.almalinux.org/almalinux/$releasever/ResilientStorage/$basearch/os/
enabled=0
gpgcheck=0
countme=1
gpgkey=file:///etc/pki/rpm-gpg/RPM-GPG-KEY-AlmaLinux-8
metadata_expire=86400
enabled_metadata=0

[rt]
name=AlmaLinux $releasever - RT
mirrorlist=https://mirrors.almalinux.org/mirrorlist/$releasever/rt
# baseurl=https://repo.almalinux.org/almalinux/$releasever/RT/$basearch/os/
enabled=0
gpgcheck=0
countme=1
gpgkey=file:///etc/pki/rpm-gpg/RPM-GPG-KEY-AlmaLinux-8
metadata_expire=86400
enabled_metadata=0

[sap]
name=AlmaLinux $releasever - SAP
mirrorlist=https://mirrors.almalinux.org/mirrorlist/$releasever/sap
# baseurl=https://repo.almalinux.org/almalinux/$releasever/SAP/$basearch/os/
enabled=0
gpgcheck=0
countme=1
gpgkey=file:///etc/pki/rpm-gpg/RPM-GPG-KEY-AlmaLinux-8
metadata_expire=86400
enabled_metadata=0

[saphana]
name=AlmaLinux $releasever - SAPHANA
mirrorlist=https://mirrors.almalinux.org/mirrorlist/$releasever/saphana
# baseurl=https://repo.almalinux.org/almalinux/$releasever/SAPHANA/$basearch/os/
enabled=0
gpgcheck=0
countme=1
gpgkey=file:///etc/pki/rpm-gpg/RPM-GPG-KEY-AlmaLinux-8
metadata_expire=86400
enabled_metadata=0

#############################################################

[epel-playground]
name=Extra Packages for Enterprise Linux $releasever - Playground - $basearch
#baseurl=https://download.fedoraproject.org/pub/epel/playground/$releasever/Everything/$basearch/os
metalink=https://mirrors.fedoraproject.org/metalink?repo=playground-epel$releasever&arch=$basearch&infra=$infra&content=$contentdir
failovermethod=priority
enabled=0
gpgcheck=0
gpgkey=file:///etc/pki/rpm-gpg/RPM-GPG-KEY-EPEL-8

[epel]
name=Extra Packages for Enterprise Linux $releasever - $basearch
#baseurl=https://download.fedoraproject.org/pub/epel/$releasever/Everything/$basearch
metalink=https://mirrors.fedoraproject.org/metalink?repo=epel-$releasever&arch=$basearch&infra=$infra&content=$contentdir
failovermethod=priority
enabled=1
gpgcheck=0
gpgkey=file:///etc/pki/rpm-gpg/RPM-GPG-KEY-EPEL-8
EOF_alma8_yum_conf
}


alma8_setup()
{
    echo "alma8_setup : $1"
    local OS_ARCH="$1"
    local OS_NAME="alma"
    local OS_RELVER="8"
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
    alma8_create_yum "${OS_ROOTDIR}/etc/yum.conf" "$OS_ARCH"

    $SUDO /usr/bin/yum -y -c "${OS_ROOTDIR}/etc/yum.conf" \
        install  --installroot="$OS_ROOTDIR" --releasever="$OS_RELVER" \
	--setopt=module_platform_id=platform:el$OS_RELVER \
	--forcearch="$OS_ARCH"   --enablerepo=crb  \
        dnf rpm dnf-data gcc make libtalloc libtalloc-devel glibc-devel tar \
	python3 python2 gzip zlib diffutils file git which

    $SUDO /usr/bin/yum -y -c "${OS_ROOTDIR}/etc/yum.conf" \
        install  --installroot="$OS_ROOTDIR" --releasever="$OS_RELVER" \
	--forcearch="$OS_ARCH" --enablerepo=crb \
        autoconf m4 gcc-c++ libstdc++-static glibc-static automake gawk libtool

    $SUDO /usr/bin/yum -y -c "${OS_ROOTDIR}/etc/yum.conf" \
        clean packages

    $SUDO /bin/chown -R "$(id -u).$(id -g)" "$OS_ROOTDIR"
    $SUDO /bin/chmod -R u+rw "$OS_ROOTDIR"
}


alma8_build_fakechroot()
{
    echo "alma8_build_fakechroot : $1"
    local OS_ARCH="$1"
    local FAKECHROOT_SOURCE_DIR="$2"
    local OS_NAME="alma"
    local OS_RELVER="8"
    local OS_ROOTDIR="${BUILD_DIR}/${OS_NAME}_${OS_RELVER}_${OS_ARCH}"
    local PROOT=""

    if [ "$OS_ARCH" = "i386" ]; then
        #PROOT="$S_PROOT_DIR/proot-x86 -q qemu-i386"
        #PROOT="$S_PROOT_DIR/proot-x86"
        PROOT="$BUILD_DIR/proot-source-x86/proot-Fedora-30.bin"
    elif [ "$OS_ARCH" = "x86_64" ]; then
        #PROOT="$S_PROOT_DIR/proot-x86_64"
        PROOT="$BUILD_DIR/proot-source-x86_64/proot-Fedora-30.bin"
    elif [ "$OS_ARCH" = "aarch64" ]; then
        #PROOT="$S_PROOT_DIR/proot-x86_64 -q qemu-aarch64"
        PROOT="$BUILD_DIR/proot-source-x86_64/proot-Fedora-30.bin -q qemu-aarch64"
    elif [ "$OS_ARCH" = "ppc64le" ]; then
        #PROOT="$S_PROOT_DIR/proot-x86_64 -q qemu-ppc64le"
        PROOT="$BUILD_DIR/proot-source-x86_64/proot-Fedora-30.bin -q qemu-ppc64le"
    else
        echo "unsupported $OS_NAME architecture: $OS_ARCH"
        exit 2
    fi

    if [ -x "${FAKECHROOT_SOURCE_DIR}/libfakechroot-AlmaLinux-8.so" ] ; then
        echo "fakechroot binary already compiled : ${FAKECHROOT_SOURCE_DIR}/libfakechroot-AlmaLinux-8.so"
        return
    fi

    export PROOT_NO_SECCOMP=1

    # compile fakechroot
    set -xv
    SHELL=/bin/bash CONFIG_SHELL=/bin/bash PATH=/bin:/usr/bin:/sbin:/usr/sbin \
        $PROOT -r "$OS_ROOTDIR" -b "${FAKECHROOT_SOURCE_DIR}:/fakechroot" -w / -b /dev \
            /bin/bash <<'EOF_alma8_fakechroot'
cd /fakechroot
# BUILD FAKECHROOT
make distclean
bash ./configure
make
cp src/.libs/libfakechroot.so libfakechroot-AlmaLinux-8.so
make clean
EOF_alma8_fakechroot
    set +xv
}



# #############################################################################
# Alma 9
# #############################################################################

alma9_create_yum()
{
    echo "alma9_create_yum : $1"
    local FILENAME="$1"
    local ARCH="$2"

    cat > "${FILENAME}" <<'EOF_alma9_yum_conf'
[main]
cachedir=/var/cache/yum/$basearch/$releasever
keepcache=0
debuglevel=2
exactarch=1
obsoletes=1
gpgcheck=0
plugins=1
installonly_limit=5

# PUT YOUR REPOS HERE OR IN separate files named file.repo
# in /etc/yum.repos.d
reposdir=NONE

[appstream]
name=AlmaLinux $releasever - AppStream
mirrorlist=https://mirrors.almalinux.org/mirrorlist/$releasever/appstream
# baseurl=https://repo.almalinux.org/almalinux/$releasever/AppStream/$basearch/os/
enabled=1
gpgcheck=0
countme=1
gpgkey=file:///etc/pki/rpm-gpg/RPM-GPG-KEY-AlmaLinux-9
metadata_expire=86400
enabled_metadata=1

[baseos]
name=AlmaLinux $releasever - BaseOS
mirrorlist=https://mirrors.almalinux.org/mirrorlist/$releasever/baseos
# baseurl=https://repo.almalinux.org/almalinux/$releasever/BaseOS/$basearch/os/
enabled=1
gpgcheck=0
countme=1
gpgkey=file:///etc/pki/rpm-gpg/RPM-GPG-KEY-AlmaLinux-9
metadata_expire=86400
enabled_metadata=1

[crb]
name=AlmaLinux $releasever - CRB
mirrorlist=https://mirrors.almalinux.org/mirrorlist/$releasever/crb
# baseurl=https://repo.almalinux.org/almalinux/$releasever/CRB/$basearch/os/
enabled=0
gpgcheck=0
countme=1
gpgkey=file:///etc/pki/rpm-gpg/RPM-GPG-KEY-AlmaLinux-9
metadata_expire=86400
enabled_metadata=0

[extras]
name=AlmaLinux $releasever - Extras
mirrorlist=https://mirrors.almalinux.org/mirrorlist/$releasever/extras
# baseurl=https://repo.almalinux.org/almalinux/$releasever/extras/$basearch/os/
enabled=1
gpgcheck=0
countme=1
gpgkey=file:///etc/pki/rpm-gpg/RPM-GPG-KEY-AlmaLinux-9
metadata_expire=86400
enabled_metadata=0

[highavailability]
name=AlmaLinux $releasever - HighAvailability
mirrorlist=https://mirrors.almalinux.org/mirrorlist/$releasever/highavailability
# baseurl=https://repo.almalinux.org/almalinux/$releasever/HighAvailability/$basearch/os/
enabled=0
gpgcheck=0
countme=1
gpgkey=file:///etc/pki/rpm-gpg/RPM-GPG-KEY-AlmaLinux-9
metadata_expire=86400
enabled_metadata=0

[nfv]
name=AlmaLinux $releasever - NFV
mirrorlist=https://mirrors.almalinux.org/mirrorlist/$releasever/nfv
# baseurl=https://repo.almalinux.org/almalinux/$releasever/NFV/$basearch/os/
enabled=0
gpgcheck=0
countme=1
gpgkey=file:///etc/pki/rpm-gpg/RPM-GPG-KEY-AlmaLinux-9
metadata_expire=86400
enabled_metadata=0

[plus]
name=AlmaLinux $releasever - Plus
mirrorlist=https://mirrors.almalinux.org/mirrorlist/$releasever/plus
# baseurl=https://repo.almalinux.org/almalinux/$releasever/plus/$basearch/os/
enabled=0
gpgcheck=0
countme=1
gpgkey=file:///etc/pki/rpm-gpg/RPM-GPG-KEY-AlmaLinux-9
metadata_expire=86400
enabled_metadata=0

[resilientstorage]
name=AlmaLinux $releasever - ResilientStorage
mirrorlist=https://mirrors.almalinux.org/mirrorlist/$releasever/resilientstorage
# baseurl=https://repo.almalinux.org/almalinux/$releasever/ResilientStorage/$basearch/os/
enabled=0
gpgcheck=0
countme=1
gpgkey=file:///etc/pki/rpm-gpg/RPM-GPG-KEY-AlmaLinux-9
metadata_expire=86400
enabled_metadata=0

[rt]
name=AlmaLinux $releasever - RT
mirrorlist=https://mirrors.almalinux.org/mirrorlist/$releasever/rt
# baseurl=https://repo.almalinux.org/almalinux/$releasever/RT/$basearch/os/
enabled=0
gpgcheck=0
countme=1
gpgkey=file:///etc/pki/rpm-gpg/RPM-GPG-KEY-AlmaLinux-9
metadata_expire=86400
enabled_metadata=0

[sap]
name=AlmaLinux $releasever - SAP
mirrorlist=https://mirrors.almalinux.org/mirrorlist/$releasever/sap
# baseurl=https://repo.almalinux.org/almalinux/$releasever/SAP/$basearch/os/
enabled=0
gpgcheck=0
countme=1
gpgkey=file:///etc/pki/rpm-gpg/RPM-GPG-KEY-AlmaLinux-9
metadata_expire=86400
enabled_metadata=0

[saphana]
name=AlmaLinux $releasever - SAPHANA
mirrorlist=https://mirrors.almalinux.org/mirrorlist/$releasever/saphana
# baseurl=https://repo.almalinux.org/almalinux/$releasever/SAPHANA/$basearch/os/
enabled=0
gpgcheck=0
countme=1
gpgkey=file:///etc/pki/rpm-gpg/RPM-GPG-KEY-AlmaLinux-9
metadata_expire=86400
enabled_metadata=0

#############################################################

[epel-playground]
name=Extra Packages for Enterprise Linux $releasever - Playground - $basearch
#baseurl=https://download.fedoraproject.org/pub/epel/playground/$releasever/Everything/$basearch/os
metalink=https://mirrors.fedoraproject.org/metalink?repo=playground-epel$releasever&arch=$basearch&infra=$infra&content=$contentdir
failovermethod=priority
enabled=0
gpgcheck=0
gpgkey=file:///etc/pki/rpm-gpg/RPM-GPG-KEY-EPEL-9

[epel]
name=Extra Packages for Enterprise Linux $releasever - $basearch
#baseurl=https://download.fedoraproject.org/pub/epel/$releasever/Everything/$basearch
metalink=https://mirrors.fedoraproject.org/metalink?repo=epel-$releasever&arch=$basearch&infra=$infra&content=$contentdir
failovermethod=priority
enabled=1
gpgcheck=0
gpgkey=file:///etc/pki/rpm-gpg/RPM-GPG-KEY-EPEL-9
EOF_alma9_yum_conf
}


alma9_setup()
{
    echo "alma9_setup : $1"
    local OS_ARCH="$1"
    local OS_NAME="alma"
    local OS_RELVER="9"
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
    alma9_create_yum "${OS_ROOTDIR}/etc/yum.conf" "$OS_ARCH"

    $SUDO /usr/bin/yum -y -c "${OS_ROOTDIR}/etc/yum.conf" \
        install  --installroot="$OS_ROOTDIR" --releasever="$OS_RELVER" \
	--setopt=module_platform_id=platform:el$OS_RELVER \
	--forcearch="$OS_ARCH" \
        dnf rpm dnf-data gcc make libtalloc libtalloc-devel glibc-devel tar \
	python3 python2 gzip zlib diffutils file git which

    $SUDO /usr/bin/yum -y -c "${OS_ROOTDIR}/etc/yum.conf" \
        install  --installroot="$OS_ROOTDIR" --releasever="$OS_RELVER" \
	--forcearch="$OS_ARCH"  --enablerepo=crb  \
        autoconf m4 gcc-c++ libstdc++-static glibc-static automake gawk libtool 

    $SUDO /usr/bin/yum -y -c "${OS_ROOTDIR}/etc/yum.conf" \
        clean packages

    $SUDO /bin/chown -R "$(id -u).$(id -g)" "$OS_ROOTDIR"
    $SUDO /bin/chmod -R u+rw "$OS_ROOTDIR"
}

alma9_build_patchelf()
{
    echo "alma9_build_patchelf : $1"
    local OS_ARCH="$1"
    local PATCHELF_SOURCE_DIR="$2"
    local OS_NAME="alma"
    local OS_RELVER="9"
    local OS_ROOTDIR="${BUILD_DIR}/${OS_NAME}_${OS_RELVER}_${OS_ARCH}"
    local PROOT=""

    if [ "$OS_ARCH" = "i386" ]; then
        #PROOT="$S_PROOT_DIR/proot-x86"
        PROOT="$BUILD_DIR/proot-source-x86/proot-Fedora-30.bin"
    elif [ "$OS_ARCH" = "x86_64" ]; then
        #PROOT="$S_PROOT_DIR/proot-x86_64"
        PROOT="$BUILD_DIR/proot-source-x86_64/proot-Fedora-30.bin"
    elif [ "$OS_ARCH" = "aarch64" ]; then
        #PROOT="$S_PROOT_DIR/proot-x86_64 -q qemu-aarch64"
        PROOT="$BUILD_DIR/proot-source-x86_64/proot-Fedora-30.bin -q qemu-aarch64"
    elif [ "$OS_ARCH" = "ppc64le" ]; then
        #PROOT="$S_PROOT_DIR/proot-x86_64 -q qemu-ppc64le"
        PROOT="$BUILD_DIR/proot-source-x86_64/proot-Fedora-30.bin -q qemu-ppc64le"
    else
        echo "unsupported $OS_NAME architecture: $OS_ARCH"
        exit 2
    fi

    if [ -x "${PATCHELF_SOURCE_DIR}/patchelf-AlmaLinux-9" ] ; then
        echo "patchelf binary already compiled : ${PATCHELF_SOURCE_DIR}/patchelf-AlmaLinux-9"
        return
    fi

    export PROOT_NO_SECCOMP=1

    # compile patchelf
    set -xv
    (cd "${PATCHELF_SOURCE_DIR}" ; bash ./bootstrap.sh)
    $PROOT -r "$OS_ROOTDIR" -b "${PATCHELF_SOURCE_DIR}:/patchelf" -w / -b /dev \
                            /bin/bash <<'EOF_alma9_patchelf'
cd /patchelf
make clean
# BUILD PATCHELF
#bash bootstrap.sh
bash ./configure
make
cp src/patchelf /patchelf/patchelf-AlmaLinux-9
make clean
EOF_alma9_patchelf
    set +xv
}

alma9_build_fakechroot()
{
    echo "alma9_build_fakechroot : $1"
    local OS_ARCH="$1"
    local FAKECHROOT_SOURCE_DIR="$2"
    local OS_NAME="alma"
    local OS_RELVER="9"
    local OS_ROOTDIR="${BUILD_DIR}/${OS_NAME}_${OS_RELVER}_${OS_ARCH}"
    local PROOT=""

    if [ "$OS_ARCH" = "i386" ]; then
        #PROOT="$S_PROOT_DIR/proot-x86 -q qemu-i386"
        #PROOT="$S_PROOT_DIR/proot-x86"
        PROOT="$BUILD_DIR/proot-source-x86/proot-Fedora-30.bin"
    elif [ "$OS_ARCH" = "x86_64" ]; then
        #PROOT="$S_PROOT_DIR/proot-x86_64"
        PROOT="$BUILD_DIR/proot-source-x86_64/proot-Fedora-30.bin"
    elif [ "$OS_ARCH" = "aarch64" ]; then
        #PROOT="$S_PROOT_DIR/proot-x86_64 -q qemu-aarch64"
        PROOT="$BUILD_DIR/proot-source-x86_64/proot-Fedora-30.bin -q qemu-aarch64"
    elif [ "$OS_ARCH" = "ppc64le" ]; then
        #PROOT="$S_PROOT_DIR/proot-x86_64 -q qemu-ppc64le"
        PROOT="$BUILD_DIR/proot-source-x86_64/proot-Fedora-30.bin -q qemu-ppc64le"
    else
        echo "unsupported $OS_NAME architecture: $OS_ARCH"
        exit 2
    fi

    if [ -x "${FAKECHROOT_SOURCE_DIR}/libfakechroot-AlmaLinux-9.so" ] ; then
        echo "fakechroot binary already compiled : ${FAKECHROOT_SOURCE_DIR}/libfakechroot-AlmaLinux-9.so"
        return
    fi

    export PROOT_NO_SECCOMP=1

    # compile fakechroot
    set -xv
    SHELL=/bin/bash CONFIG_SHELL=/bin/bash PATH=/bin:/usr/bin:/sbin:/usr/sbin \
        $PROOT -r "$OS_ROOTDIR" -b "${FAKECHROOT_SOURCE_DIR}:/fakechroot" -w / -b /dev \
            /bin/bash <<'EOF_alma9_fakechroot'
cd /fakechroot
# BUILD FAKECHROOT
make distclean
bash ./configure
make
cp src/.libs/libfakechroot.so libfakechroot-AlmaLinux-9.so
make clean
EOF_alma9_fakechroot
    set +xv
}



# #############################################################################
# Ubuntu 12.04
# #############################################################################

ubuntu12_setup()
{
    echo "ubuntu12_setup : $1"
    local OS_ARCH="$1"
    local OS_NAME="ubuntu"
    local OS_RELVER="12"
    local OS_ROOTDIR="${BUILD_DIR}/${OS_NAME}_${OS_RELVER}_${OS_ARCH}"

    if [ -x "${OS_ROOTDIR}/usr/lib/gcc" ] ; then
        echo "os already setup : ${OS_ROOTDIR}"
        return
    fi

    SUDO=sudo

    $SUDO debootstrap --no-check-gpg --arch="$OS_ARCH" --variant=buildd \
	    precise "$OS_ROOTDIR" http://old-releases.ubuntu.com/ubuntu/

    $SUDO /bin/chown -R "$(id -u).$(id -g)" "$OS_ROOTDIR"
    $SUDO /bin/chmod -R u+rw "$OS_ROOTDIR"
}

ubuntu12_build_fakechroot()
{
    echo "ubuntu12_build_fakechroot : $1"
    local OS_ARCH="$1"
    local FAKECHROOT_SOURCE_DIR="$2"
    local OS_NAME="ubuntu"
    local OS_RELVER="12"
    local OS_ROOTDIR="${BUILD_DIR}/${OS_NAME}_${OS_RELVER}_${OS_ARCH}"
    local PROOT=""

    if [ "$OS_ARCH" = "i386" ]; then
        #PROOT="$S_PROOT_DIR/proot-x86 -q qemu-i386"
        #PROOT="$S_PROOT_DIR/proot-x86"
        PROOT="$BUILD_DIR/proot-source-x86/proot-Fedora-30.bin"
    elif [ "$OS_ARCH" = "amd64" ]; then
        #PROOT="$S_PROOT_DIR/proot-x86_64"
        PROOT="$BUILD_DIR/proot-source-x86_64/proot-Fedora-30.bin"
    else
        echo "unsupported $OS_NAME architecture: $OS_ARCH"
        exit 2
    fi

    if [ -x "${FAKECHROOT_SOURCE_DIR}/libfakechroot-Ubuntu-12.so" ] ; then
        echo "fakechroot binary already compiled : ${FAKECHROOT_SOURCE_DIR}/libfakechroot-Ubuntu-12.so"
        return
    fi

    export PROOT_NO_SECCOMP=1

    # compile fakechroot
    set -xv
    SHELL=/bin/bash CONFIG_SHELL=/bin/bash PATH=/bin:/usr/bin:/sbin:/usr/sbin:/usr/lib \
        $PROOT -0 -r "$OS_ROOTDIR" -b "${FAKECHROOT_SOURCE_DIR}:/fakechroot" -w / -b /dev \
            -b /etc/resolv.conf:/etc/resolv.conf /bin/bash <<'EOF_ubuntu12_packages'
apt-get -y update
apt-get -y --no-install-recommends install wget debconf devscripts gnupg nano 
apt-get -y update
apt-get -y install locales build-essential gcc make autoconf m4 automake gawk libtool bash
apt-get -y install diffutils file which
EOF_ubuntu12_packages

    SHELL=/bin/bash CONFIG_SHELL=/bin/bash PATH=/bin:/usr/bin:/sbin:/usr/sbin:/usr/lib \
        $PROOT -r "$OS_ROOTDIR" -b "${FAKECHROOT_SOURCE_DIR}:/fakechroot" -w / -b /dev \
            /bin/bash <<'EOF_ubuntu12_fakechroot'
# BUILD FAKECHROOT
export SHELL=/bin/bash
export CONFIG_SHELL=/bin/bash
export PATH=/bin:/usr/bin:/sbin:/usr/sbin:/usr/lib
cd /fakechroot
make distclean
bash ./configure
make
cp src/.libs/libfakechroot.so libfakechroot-Ubuntu-12.so
make clean
EOF_ubuntu12_fakechroot
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

    $SUDO debootstrap --arch="$OS_ARCH" --variant=buildd trusty "$OS_ROOTDIR" http://archive.ubuntu.com/ubuntu/

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
        #PROOT="$S_PROOT_DIR/proot-x86 -q qemu-i386"
        #PROOT="$S_PROOT_DIR/proot-x86"
        PROOT="$BUILD_DIR/proot-source-x86/proot-Fedora-30.bin"
    elif [ "$OS_ARCH" = "amd64" ]; then
        #PROOT="$S_PROOT_DIR/proot-x86_64"
        PROOT="$BUILD_DIR/proot-source-x86_64/proot-Fedora-30.bin"
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
    if [ ! -x "$OS_ROOTDIR/bin/bash" ] ; then
        SHELL=/bin/bash CONFIG_SHELL=/bin/bash PATH=/bin:/usr/bin:/sbin:/usr/sbin:/usr/lib \
            $PROOT -0 -r "$OS_ROOTDIR" -b "${FAKECHROOT_SOURCE_DIR}:/fakechroot" -w / -b /dev \
                -b /etc/resolv.conf:/etc/resolv.conf /bin/bash <<'EOF_ubuntu14_packages'
apt-get -y update
apt-get -y --no-install-recommends install wget debconf devscripts gnupg nano 
apt-get -y update
apt-get -y install locales build-essential gcc make autoconf m4 automake gawk libtool bash 
apt-get -y install diffutils file which
EOF_ubuntu14_packages
    fi

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

    if [ "$OS_ARCH" = "amd64" ] || [ "$OS_ARCH" = "i386" ]; then
        REPOSITORY_URL="http://archive.ubuntu.com/ubuntu/"
        #REPOSITORY_URL="http://old-releases.ubuntu.com/ubuntu/"
    else
        REPOSITORY_URL="http://ports.ubuntu.com/ubuntu-ports/"
        #REPOSITORY_URL="http://old-releases.ubuntu.com/ubuntu/"
    fi

    $SUDO debootstrap --arch="$OS_ARCH" --variant=buildd xenial "$OS_ROOTDIR" "$REPOSITORY_URL"

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
        #PROOT="$S_PROOT_DIR/proot-x86 -q qemu-i386"
        #PROOT="$S_PROOT_DIR/proot-x86"
        PROOT="$BUILD_DIR/proot-source-x86/proot-Fedora-30.bin"
    elif [ "$OS_ARCH" = "amd64" ]; then
        #PROOT="$S_PROOT_DIR/proot-x86_64"
        PROOT="$BUILD_DIR/proot-source-x86_64/proot-Fedora-30.bin"
    elif [ "$OS_ARCH" = "arm64" ]; then
        #PROOT="$S_PROOT_DIR/proot-x86_64 -q qemu-aarch64"
        PROOT="$BUILD_DIR/proot-source-x86_64/proot-Fedora-30.bin -q qemu-aarch64"
    elif [ "$OS_ARCH" = "ppc64el" ]; then
        #PROOT="$S_PROOT_DIR/proot-x86_64 -q qemu-ppc64le"
        PROOT="$BUILD_DIR/proot-source-x86_64/proot-Fedora-30.bin -q qemu-ppc64le"
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
    if [ ! -x "$OS_ROOTDIR/bin/bash" ] ; then
        SHELL=/bin/bash CONFIG_SHELL=/bin/bash PATH=/bin:/usr/bin:/sbin:/usr/sbin:/usr/lib \
            $PROOT -0 -r "$OS_ROOTDIR" -b "${FAKECHROOT_SOURCE_DIR}:/fakechroot" -w / -b /dev \
                -b /etc/resolv.conf:/etc/resolv.conf /bin/bash <<'EOF_ubuntu16_packages'
apt-get -y update
apt-get -y --no-install-recommends install wget debconf devscripts gnupg nano
apt-get -y update
apt-get -y install locales build-essential gcc make autoconf m4 automake gawk libtool bash 
apt-get -y install diffutils file which
EOF_ubuntu16_packages
    fi

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
        #PROOT="$S_PROOT_DIR/proot-x86 -q qemu-i386"
        #PROOT="$S_PROOT_DIR/proot-x86"
        PROOT="$BUILD_DIR/proot-source-x86/proot-Fedora-30.bin"
    elif [ "$OS_ARCH" = "amd64" ]; then
        #PROOT="$S_PROOT_DIR/proot-x86_64"
        PROOT="$BUILD_DIR/proot-source-x86_64/proot-Fedora-30.bin"
    elif [ "$OS_ARCH" = "arm64" ]; then
        #PROOT="$S_PROOT_DIR/proot-x86_64 -q qemu-aarch64"
        PROOT="$BUILD_DIR/proot-source-x86_64/proot-Fedora-30.bin -q qemu-aarch64"
    elif [ "$OS_ARCH" = "ppc64el" ]; then
        #PROOT="$S_PROOT_DIR/proot-x86_64 -q qemu-ppc64le"
        PROOT="$BUILD_DIR/proot-source-x86_64/proot-Fedora-30.bin -q qemu-ppc64le"
    else
        echo "unsupported $OS_NAME architecture: $OS_ARCH"
        exit 2
    fi

    if [ -x "${RUNC_SOURCE_DIR}/runc-Ubuntu-16.bin" ] ; then
        echo "runc binary already compiled : ${RUNC_SOURCE_DIR}/runc-Ubuntu-16.bin"
        return
    fi

    export PROOT_NO_SECCOMP=1

    # compile runc
    mkdir -p "${OS_ROOTDIR}/go/src/github.com/opencontainers"
    set -xv
    SHELL=/bin/bash CONFIG_SHELL=/bin/bash PATH=/bin:/usr/bin:/sbin:/usr/sbin:/usr/lib \
        $PROOT -0 -r "$OS_ROOTDIR" -b "${RUNC_SOURCE_DIR}:/go/src/github.com/opencontainers/runc" -w / -b /dev \
            -b /etc/resolv.conf:/etc/resolv.conf /bin/bash <<'EOF_ubuntu16_runc'
apt-get -y update
apt-get -y install golang libseccomp-dev git
export GOPATH=/go
cd /go/src/github.com/opencontainers/runc
make clean
make static
/bin/mv runc runc-Ubuntu-16.bin
EOF_ubuntu16_runc

    set +xv
}

# #############################################################################
# Ubuntu 18.04
# #############################################################################

ubuntu18_setup()
{
    echo "ubuntu18_setup : $1"
    local OS_ARCH="$1"
    local OS_NAME="ubuntu"
    local OS_RELVER="18"
    local OS_ROOTDIR="${BUILD_DIR}/${OS_NAME}_${OS_RELVER}_${OS_ARCH}"

    if [ -x "${OS_ROOTDIR}/usr/lib/gcc" ] ; then
        echo "os already setup : ${OS_ROOTDIR}"
        return
    fi

    SUDO=sudo

    if [ "$OS_ARCH" = "amd64" ] || [ "$OS_ARCH" = "i386" ]; then
        REPOSITORY_URL="http://archive.ubuntu.com/ubuntu/"
        #REPOSITORY_URL="http://old-releases.ubuntu.com/ubuntu/"
    else
        REPOSITORY_URL="http://ports.ubuntu.com/ubuntu-ports/"
        #REPOSITORY_URL="http://old-releases.ubuntu.com/ubuntu/"
    fi

    $SUDO debootstrap --arch="$OS_ARCH" --variant=buildd bionic "$OS_ROOTDIR" "$REPOSITORY_URL"

    $SUDO /bin/chown -R "$(id -u).$(id -g)" "$OS_ROOTDIR"
    $SUDO /bin/chmod -R u+rw "$OS_ROOTDIR"
}

ubuntu18_build_fakechroot()
{
    echo "ubuntu18_build_fakechroot : $1"
    local OS_ARCH="$1"
    local FAKECHROOT_SOURCE_DIR="$2"
    local OS_NAME="ubuntu"
    local OS_RELVER="18"
    local OS_ROOTDIR="${BUILD_DIR}/${OS_NAME}_${OS_RELVER}_${OS_ARCH}"
    local PROOT=""

    if [ "$OS_ARCH" = "i386" ]; then
        #PROOT="$S_PROOT_DIR/proot-x86 -q qemu-i386"
        #PROOT="$S_PROOT_DIR/proot-x86"
        PROOT="$BUILD_DIR/proot-source-x86/proot-Fedora-30.bin"
    elif [ "$OS_ARCH" = "amd64" ]; then
        #PROOT="$S_PROOT_DIR/proot-x86_64"
        PROOT="$BUILD_DIR/proot-source-x86_64/proot-Fedora-30.bin"
    elif [ "$OS_ARCH" = "arm64" ]; then
        #PROOT="$S_PROOT_DIR/proot-x86_64 -q qemu-aarch64"
        PROOT="$BUILD_DIR/proot-source-x86_64/proot-Fedora-30.bin -q qemu-aarch64"
    elif [ "$OS_ARCH" = "ppc64el" ]; then
        #PROOT="$S_PROOT_DIR/proot-x86_64 -q qemu-ppc64le"
        PROOT="$BUILD_DIR/proot-source-x86_64/proot-Fedora-30.bin -q qemu-ppc64le"
    else
        echo "unsupported $OS_NAME architecture: $OS_ARCH"
        exit 2
    fi

    if [ -x "${FAKECHROOT_SOURCE_DIR}/libfakechroot-Ubuntu-18.so" ] ; then
        echo "fakechroot binary already compiled : ${FAKECHROOT_SOURCE_DIR}/libfakechroot-Ubuntu-18.so"
        return
    fi

    export PROOT_NO_SECCOMP=1

    # compile fakechroot
    set -xv
    if [ ! -x "$OS_ROOTDIR/bin/bash" ] ; then
        SHELL=/bin/bash CONFIG_SHELL=/bin/bash PATH=/bin:/usr/bin:/sbin:/usr/sbin:/usr/lib \
            $PROOT -0 -r "$OS_ROOTDIR" -b "${FAKECHROOT_SOURCE_DIR}:/fakechroot" -w / -b /dev \
                -b /etc/resolv.conf:/etc/resolv.conf /bin/bash <<'EOF_ubuntu18_packages'
apt-get -y update
apt-get -y --no-install-recommends install wget debconf devscripts gnupg nano
apt-get -y update
apt-get -y install locales build-essential gcc make autoconf m4 automake gawk libtool bash 
apt-get -y install diffutils file which
EOF_ubuntu18_packages
    fi

    SHELL=/bin/bash CONFIG_SHELL=/bin/bash PATH=/bin:/usr/bin:/sbin:/usr/sbin:/usr/lib \
        $PROOT -r "$OS_ROOTDIR" -b "${FAKECHROOT_SOURCE_DIR}:/fakechroot" -w / -b /dev \
            /bin/bash <<'EOF_ubuntu18_fakechroot'
# BUILD FAKECHROOT
export SHELL=/bin/bash
export CONFIG_SHELL=/bin/bash
export PATH=/bin:/usr/bin:/sbin:/usr/sbin:/usr/lib
cd /fakechroot
make distclean
bash ./configure
make
cp src/.libs/libfakechroot.so libfakechroot-Ubuntu-18.so
make clean
EOF_ubuntu18_fakechroot
    set +xv
}

ubuntu18_build_runc()
{
    echo "ubuntu18_build_runc : $1"
    local OS_ARCH="$1"
    local RUNC_SOURCE_DIR="$2"
    local OS_NAME="ubuntu"
    local OS_RELVER="18"
    local OS_ROOTDIR="${BUILD_DIR}/${OS_NAME}_${OS_RELVER}_${OS_ARCH}"
    local PROOT=""

    if [ "$OS_ARCH" = "i386" ]; then
        #PROOT="$S_PROOT_DIR/proot-x86 -q qemu-i386"
        #PROOT="$S_PROOT_DIR/proot-x86"
        PROOT="$BUILD_DIR/proot-source-x86/proot-Fedora-30.bin"
    elif [ "$OS_ARCH" = "amd64" ]; then
        #PROOT="$S_PROOT_DIR/proot-x86_64"
        PROOT="$BUILD_DIR/proot-source-x86_64/proot-Fedora-30.bin"
    elif [ "$OS_ARCH" = "arm64" ]; then
        #PROOT="$S_PROOT_DIR/proot-x86_64 -q qemu-aarch64"
        PROOT="$BUILD_DIR/proot-source-x86_64/proot-Fedora-30.bin -q qemu-aarch64"
    elif [ "$OS_ARCH" = "ppc64el" ]; then
        #PROOT="$S_PROOT_DIR/proot-x86_64 -q qemu-ppc64le"
        PROOT="$BUILD_DIR/proot-source-x86_64/proot-Fedora-30.bin -q qemu-ppc64le"
    else
        echo "unsupported $OS_NAME architecture: $OS_ARCH"
        exit 2
    fi

    if [ -x "${RUNC_SOURCE_DIR}/runc-Ubuntu-18.bin" ] ; then
        echo "runc binary already compiled : ${RUNC_SOURCE_DIR}/runc-Ubuntu-18.bin"
        return
    fi

    export PROOT_NO_SECCOMP=1

    # compile runc
    mkdir -p "${OS_ROOTDIR}/go/src/github.com/opencontainers"
    SHELL=/bin/bash CONFIG_SHELL=/bin/bash PATH=/bin:/usr/bin:/sbin:/usr/sbin:/usr/lib \
        $PROOT -0 -r "$OS_ROOTDIR" -b "${RUNC_SOURCE_DIR}:/go/src/github.com/opencontainers/runc" -w / -b /dev \
            -b /etc/resolv.conf:/etc/resolv.conf /bin/bash <<'EOF_ubuntu18_runc'
apt-get -y update
apt-get -y install golang libseccomp-dev git software-properties-common
add-apt-repository ppa:gophers/archive
apt-get -y update
apt-get -y install golang-1.11-go
export GOROOT=/usr/lib/go-1.11
export GOPATH=/go
export PATH=$GOPATH/bin:$GOROOT/bin:$PATH
go get github.com/sirupsen/logrus
cd /go/src/github.com/opencontainers/runc
make clean
make static
/bin/mv runc runc-Ubuntu-18.bin
EOF_ubuntu18_runc

}


# #############################################################################
# Ubuntu 19.10
# #############################################################################

ubuntu19_setup()
{
    echo "ubuntu19_setup : $1"
    local OS_ARCH="$1"
    local OS_NAME="ubuntu"
    local OS_RELVER="19"
    local OS_ROOTDIR="${BUILD_DIR}/${OS_NAME}_${OS_RELVER}_${OS_ARCH}"

    if [ -x "${OS_ROOTDIR}/usr/lib/gcc" ] ; then
        echo "os already setup : ${OS_ROOTDIR}"
        return
    fi

    SUDO=sudo

    #$SUDO debootstrap --arch="$OS_ARCH" --variant=buildd eoan "$OS_ROOTDIR" http://archive.ubuntu.com/ubuntu/
    $SUDO debootstrap --arch="$OS_ARCH" --variant=buildd eoan "$OS_ROOTDIR" http://old-releases.ubuntu.com/ubuntu/

    $SUDO /bin/chown -R "$(id -u).$(id -g)" "$OS_ROOTDIR"
    $SUDO /bin/chmod -R u+rw "$OS_ROOTDIR"
}

ubuntu19_build_fakechroot()
{
    echo "ubuntu19_build_fakechroot : $1"
    local OS_ARCH="$1"
    local FAKECHROOT_SOURCE_DIR="$2"
    local OS_NAME="ubuntu"
    local OS_RELVER="19"
    local OS_ROOTDIR="${BUILD_DIR}/${OS_NAME}_${OS_RELVER}_${OS_ARCH}"
    local PROOT=""

    if [ "$OS_ARCH" = "i386" ]; then
        #PROOT="$S_PROOT_DIR/proot-x86 -q qemu-i386"
        #PROOT="$S_PROOT_DIR/proot-x86"
	PROOT="$BUILD_DIR/proot-source-x86/proot-Fedora-30.bin"
    elif [ "$OS_ARCH" = "amd64" ]; then
        #PROOT="$S_PROOT_DIR/proot-x86_64"
	PROOT="$BUILD_DIR/proot-source-x86_64/proot-Fedora-30.bin"
    elif [ "$OS_ARCH" = "arm64" ]; then
        #PROOT="$S_PROOT_DIR/proot-x86_64 -q qemu-aarch64"
        PROOT="$BUILD_DIR/proot-source-x86_64/proot-Fedora-30.bin -q qemu-aarch64"
    elif [ "$OS_ARCH" = "ppc64el" ]; then
        #PROOT="$S_PROOT_DIR/proot-x86_64 -q qemu-ppc64le"
        PROOT="$BUILD_DIR/proot-source-x86_64/proot-Fedora-30.bin -q qemu-ppc64le"
    else
        echo "unsupported $OS_NAME architecture: $OS_ARCH"
        exit 2
    fi

    if [ -x "${FAKECHROOT_SOURCE_DIR}/libfakechroot-Ubuntu-19.so" ] ; then
        echo "fakechroot binary already compiled : ${FAKECHROOT_SOURCE_DIR}/libfakechroot-Ubuntu-19.so"
        return
    fi

    export PROOT_NO_SECCOMP=1

    # compile fakechroot
    set -xv
    if [ ! -x "$OS_ROOTDIR/bin/bash" ] ; then
        SHELL=/bin/bash CONFIG_SHELL=/bin/bash PATH=/bin:/usr/bin:/sbin:/usr/sbin:/usr/lib \
            $PROOT -0 -r "$OS_ROOTDIR" -b "${FAKECHROOT_SOURCE_DIR}:/fakechroot" -w / -b /dev \
                -b /etc/resolv.conf:/etc/resolv.conf /bin/bash <<'EOF_ubuntu19_packages'
apt-get -y update
apt-get -y --no-install-recommends install wget debconf devscripts gnupg nano
apt-get -y update
apt-get -y install locales build-essential gcc make autoconf m4 automake gawk libtool bash 
apt-get -y install diffutils file which
EOF_ubuntu19_packages
    fi

    SHELL=/bin/bash CONFIG_SHELL=/bin/bash PATH=/bin:/usr/bin:/sbin:/usr/sbin:/usr/lib \
        $PROOT -r "$OS_ROOTDIR" -b "${FAKECHROOT_SOURCE_DIR}:/fakechroot" -w / -b /dev \
            /bin/bash <<'EOF_ubuntu19_fakechroot'
# BUILD FAKECHROOT
export SHELL=/bin/bash
export CONFIG_SHELL=/bin/bash
export PATH=/bin:/usr/bin:/sbin:/usr/sbin:/usr/lib
cd /fakechroot
make distclean
bash ./configure
make
cp src/.libs/libfakechroot.so libfakechroot-Ubuntu-19.so
make clean
EOF_ubuntu19_fakechroot
    set +xv
}

ubuntu19_build_runc()
{
    echo "ubuntu19_build_runc : $1"
    local OS_ARCH="$1"
    local RUNC_SOURCE_DIR="$2"
    local OS_NAME="ubuntu"
    local OS_RELVER="19"
    local OS_ROOTDIR="${BUILD_DIR}/${OS_NAME}_${OS_RELVER}_${OS_ARCH}"
    local PROOT=""

    if [ "$OS_ARCH" = "i386" ]; then
        #PROOT="$S_PROOT_DIR/proot-x86 -q qemu-i386"
        #PROOT="$S_PROOT_DIR/proot-x86"
        PROOT="$BUILD_DIR/proot-source-x86/proot-Fedora-30.bin"
    elif [ "$OS_ARCH" = "amd64" ]; then
        #PROOT="$S_PROOT_DIR/proot-x86_64"
        PROOT="$BUILD_DIR/proot-source-x86_64/proot-Fedora-30.bin"
    elif [ "$OS_ARCH" = "arm64" ]; then
        #PROOT="$S_PROOT_DIR/proot-x86_64 -q qemu-aarch64"
        PROOT="$BUILD_DIR/proot-source-x86_64/proot-Fedora-30.bin -q qemu-aarch64"
    elif [ "$OS_ARCH" = "ppc64el" ]; then
        #PROOT="$S_PROOT_DIR/proot-x86_64 -q qemu-ppc64le"
        PROOT="$BUILD_DIR/proot-source-x86_64/proot-Fedora-30.bin -q qemu-ppc64le"
    else
        echo "unsupported $OS_NAME architecture: $OS_ARCH"
        exit 2
    fi

    if [ -x "${RUNC_SOURCE_DIR}/runc-Ubuntu-19.bin" ] ; then
        echo "runc binary already compiled : ${RUNC_SOURCE_DIR}/runc-Ubuntu-19.bin"
        return
    fi

    export PROOT_NO_SECCOMP=1

    # compile runc
    mkdir -p "${OS_ROOTDIR}/go/src/github.com/opencontainers"
    set -xv
    SHELL=/bin/bash CONFIG_SHELL=/bin/bash PATH=/bin:/usr/bin:/sbin:/usr/sbin:/usr/lib \
        $PROOT -0 -r "$OS_ROOTDIR" -b "${RUNC_SOURCE_DIR}:/go/src/github.com/opencontainers/runc" -w / -b /dev \
            -b /etc/resolv.conf:/etc/resolv.conf /bin/bash <<'EOF_ubuntu19_runc'
apt-get -y update
apt-get -y install golang libseccomp-dev git software-properties-common
add-apt-repository ppa:gophers/archive
apt-get -y update
apt-get -y install golang-1.11-go
export GOROOT=/usr/lib/go-1.11
export GOPATH=/go
export PATH=$GOPATH/bin:$GOROOT/bin:$PATH
go get github.com/sirupsen/logrus
cd /go/src/github.com/opencontainers/runc
make clean
make static
/bin/mv runc runc-Ubuntu-19.bin
EOF_ubuntu19_runc

    set +xv
}


# #############################################################################
# Ubuntu 20.04
# #############################################################################

ubuntu20_setup()
{
    echo "ubuntu20_setup : $1"
    local OS_ARCH="$1"
    local OS_NAME="ubuntu"
    local OS_RELVER="20"
    local OS_ROOTDIR="${BUILD_DIR}/${OS_NAME}_${OS_RELVER}_${OS_ARCH}"

    if [ -x "${OS_ROOTDIR}/usr/lib/gcc" ] ; then
        echo "os already setup : ${OS_ROOTDIR}"
        return
    fi

    SUDO=sudo

    if [ "$OS_ARCH" = "amd64" ] || [ "$OS_ARCH" = "i386" ]; then
	REPOSITORY_URL="http://archive.ubuntu.com/ubuntu/"
    else
	REPOSITORY_URL="http://ports.ubuntu.com/ubuntu-ports/"
    fi

    $SUDO debootstrap --arch="$OS_ARCH" --variant=buildd focal "$OS_ROOTDIR" "$REPOSITORY_URL"

    $SUDO /bin/chown -R "$(id -u).$(id -g)" "$OS_ROOTDIR"
    $SUDO /bin/chmod -R u+rw "$OS_ROOTDIR"
}

ubuntu20_build_fakechroot()
{
    echo "ubuntu20_build_fakechroot : $1"
    local OS_ARCH="$1"
    local FAKECHROOT_SOURCE_DIR="$2"
    local OS_NAME="ubuntu"
    local OS_RELVER="20"
    local OS_ROOTDIR="${BUILD_DIR}/${OS_NAME}_${OS_RELVER}_${OS_ARCH}"
    local PROOT=""

    if [ "$OS_ARCH" = "i386" ]; then
        #PROOT="$S_PROOT_DIR/proot-x86 -q qemu-i386"
        #PROOT="$S_PROOT_DIR/proot-x86"
	PROOT="$BUILD_DIR/proot-source-x86/proot-Fedora-30.bin"
    elif [ "$OS_ARCH" = "amd64" ]; then
        #PROOT="$S_PROOT_DIR/proot-x86_64"
	PROOT="$BUILD_DIR/proot-source-x86_64/proot-Fedora-30.bin"
    elif [ "$OS_ARCH" = "arm64" ]; then
        #PROOT="$S_PROOT_DIR/proot-x86_64 -q qemu-aarch64"
        PROOT="$BUILD_DIR/proot-source-x86_64/proot-Fedora-30.bin -q qemu-aarch64"
    elif [ "$OS_ARCH" = "ppc64el" ]; then
        #PROOT="$S_PROOT_DIR/proot-x86_64 -q qemu-ppc64le"
        PROOT="$BUILD_DIR/proot-source-x86_64/proot-Fedora-30.bin -q qemu-ppc64le"
    else
        echo "unsupported $OS_NAME architecture: $OS_ARCH"
        exit 2
    fi

    if [ -x "${FAKECHROOT_SOURCE_DIR}/libfakechroot-Ubuntu-20.so" ] ; then
        echo "fakechroot binary already compiled : ${FAKECHROOT_SOURCE_DIR}/libfakechroot-Ubuntu-20.so"
        return
    fi

    export PROOT_NO_SECCOMP=1

    # compile fakechroot
    set -xv
    if [ ! -x "$OS_ROOTDIR/bin/bash" ] ; then
        SHELL=/bin/bash CONFIG_SHELL=/bin/bash PATH=/bin:/usr/bin:/sbin:/usr/sbin:/usr/lib \
            $PROOT -0 -r "$OS_ROOTDIR" -b "${FAKECHROOT_SOURCE_DIR}:/fakechroot" -w / -b /dev \
                -b /etc/resolv.conf:/etc/resolv.conf /bin/bash <<'EOF_ubuntu20_packages'
apt-get -y update
apt-get -y --no-install-recommends install wget debconf devscripts gnupg nano
apt-get -y update
apt-get -y install locales build-essential gcc make autoconf m4 automake gawk libtool bash 
apt-get -y install diffutils file which
EOF_ubuntu20_packages
    fi

    SHELL=/bin/bash CONFIG_SHELL=/bin/bash PATH=/bin:/usr/bin:/sbin:/usr/sbin:/usr/lib \
        $PROOT -r "$OS_ROOTDIR" -b "${FAKECHROOT_SOURCE_DIR}:/fakechroot" -w / -b /dev \
            /bin/bash <<'EOF_ubuntu20_fakechroot'
# BUILD FAKECHROOT
export SHELL=/bin/bash
export CONFIG_SHELL=/bin/bash
export PATH=/bin:/usr/bin:/sbin:/usr/sbin:/usr/lib
cd /fakechroot
make distclean
bash ./configure
make
cp src/.libs/libfakechroot.so libfakechroot-Ubuntu-20.so
make clean
EOF_ubuntu20_fakechroot
    set +xv
}

ubuntu20_build_runc()
{
    echo "ubuntu20_build_runc : $1"
    local OS_ARCH="$1"
    local RUNC_SOURCE_DIR="$2"
    local OS_NAME="ubuntu"
    local OS_RELVER="20"
    local OS_ROOTDIR="${BUILD_DIR}/${OS_NAME}_${OS_RELVER}_${OS_ARCH}"
    local PROOT=""

    if [ "$OS_ARCH" = "i386" ]; then
        #PROOT="$S_PROOT_DIR/proot-x86 -q qemu-i386"
        #PROOT="$S_PROOT_DIR/proot-x86"
        PROOT="$BUILD_DIR/proot-source-x86/proot-Fedora-30.bin"
    elif [ "$OS_ARCH" = "amd64" ]; then
        #PROOT="$S_PROOT_DIR/proot-x86_64"
        PROOT="$BUILD_DIR/proot-source-x86_64/proot-Fedora-30.bin"
    elif [ "$OS_ARCH" = "arm64" ]; then
        #PROOT="$S_PROOT_DIR/proot-x86_64 -q qemu-aarch64"
        PROOT="$BUILD_DIR/proot-source-x86_64/proot-Fedora-30.bin -q qemu-aarch64"
    elif [ "$OS_ARCH" = "ppc64el" ]; then
        #PROOT="$S_PROOT_DIR/proot-x86_64 -q qemu-ppc64le"
        PROOT="$BUILD_DIR/proot-source-x86_64/proot-Fedora-30.bin -q qemu-ppc64le"
    else
        echo "unsupported $OS_NAME architecture: $OS_ARCH"
        exit 2
    fi

    if [ -x "${RUNC_SOURCE_DIR}/runc-Ubuntu-20.bin" ] ; then
        echo "runc binary already compiled : ${RUNC_SOURCE_DIR}/runc-Ubuntu-20.bin"
        return
    fi

    export PROOT_NO_SECCOMP=1

    # compile runc
    mkdir -p "${OS_ROOTDIR}/go/src/github.com/opencontainers"
    set -xv
    SHELL=/bin/bash CONFIG_SHELL=/bin/bash PATH=/bin:/usr/bin:/sbin:/usr/sbin:/usr/lib \
        $PROOT -0 -r "$OS_ROOTDIR" -b "${RUNC_SOURCE_DIR}:/go/src/github.com/opencontainers/runc" -w / -b /dev \
            -b /etc/resolv.conf:/etc/resolv.conf /bin/bash <<'EOF_ubuntu20_runc'
apt-get -y update
apt-get -y install golang libseccomp-dev git software-properties-common
add-apt-repository ppa:gophers/archive
apt-get -y update
apt-get -y install golang-1.11-go
export GOROOT=/usr/lib/go-1.11
export GOPATH=/go
export PATH=$GOPATH/bin:$GOROOT/bin:$PATH
go get github.com/sirupsen/logrus
cd /go/src/github.com/opencontainers/runc
make clean
make static
/bin/mv runc runc-Ubuntu-20.bin
EOF_ubuntu20_runc

    set +xv
}


# #############################################################################
# Ubuntu 21.04
# #############################################################################

ubuntu21_setup()
{
    echo "ubuntu21_setup : $1"
    local OS_ARCH="$1"
    local OS_NAME="ubuntu"
    local OS_RELVER="21"
    local OS_ROOTDIR="${BUILD_DIR}/${OS_NAME}_${OS_RELVER}_${OS_ARCH}"

    if [ -x "${OS_ROOTDIR}/usr/lib/gcc" ] ; then
        echo "os already setup : ${OS_ROOTDIR}"
        return
    fi

    SUDO=sudo

    if [ "$OS_ARCH" = "amd64" ] || [ "$OS_ARCH" = "i386" ]; then
	#REPOSITORY_URL="http://archive.ubuntu.com/ubuntu/"
	REPOSITORY_URL="http://old-releases.ubuntu.com/ubuntu/"
    else
	#REPOSITORY_URL="http://ports.ubuntu.com/ubuntu-ports/"
	REPOSITORY_URL="http://old-releases.ubuntu.com/ubuntu/"
    fi
    $SUDO debootstrap --arch="$OS_ARCH" --variant=buildd hirsute "$OS_ROOTDIR" "$REPOSITORY_URL"

    $SUDO /bin/chown -R "$(id -u).$(id -g)" "$OS_ROOTDIR"
    $SUDO /bin/chmod -R u+rw "$OS_ROOTDIR"
}

ubuntu21_build_fakechroot()
{
    echo "ubuntu21_build_fakechroot : $1"
    local OS_ARCH="$1"
    local FAKECHROOT_SOURCE_DIR="$2"
    local OS_NAME="ubuntu"
    local OS_RELVER="21"
    local OS_ROOTDIR="${BUILD_DIR}/${OS_NAME}_${OS_RELVER}_${OS_ARCH}"
    local PROOT=""

    if [ "$OS_ARCH" = "i386" ]; then
        #PROOT="$S_PROOT_DIR/proot-x86 -q qemu-i386"
        #PROOT="$S_PROOT_DIR/proot-x86"
	PROOT="$BUILD_DIR/proot-source-x86/proot-Fedora-30.bin"
    elif [ "$OS_ARCH" = "amd64" ]; then
        #PROOT="$S_PROOT_DIR/proot-x86_64"
	PROOT="$BUILD_DIR/proot-source-x86_64/proot-Fedora-30.bin"
    elif [ "$OS_ARCH" = "arm64" ]; then
        #PROOT="$S_PROOT_DIR/proot-x86_64 -q qemu-aarch64"
        PROOT="$BUILD_DIR/proot-source-x86_64/proot-Fedora-30.bin -q qemu-aarch64"
    elif [ "$OS_ARCH" = "ppc64el" ]; then
        #PROOT="$S_PROOT_DIR/proot-x86_64 -q qemu-ppc64le"
        PROOT="$BUILD_DIR/proot-source-x86_64/proot-Fedora-30.bin -q qemu-ppc64le"
    else
        echo "unsupported $OS_NAME architecture: $OS_ARCH"
        exit 2
    fi

    if [ -x "${FAKECHROOT_SOURCE_DIR}/libfakechroot-Ubuntu-21.so" ] ; then
        echo "fakechroot binary already compiled : ${FAKECHROOT_SOURCE_DIR}/libfakechroot-Ubuntu-21.so"
        return
    fi

    export PROOT_NO_SECCOMP=1

    # compile fakechroot
    set -xv
    if [ ! -x "$OS_ROOTDIR/bin/bash" ] ; then
        SHELL=/bin/bash CONFIG_SHELL=/bin/bash PATH=/bin:/usr/bin:/sbin:/usr/sbin:/usr/lib \
            $PROOT -0 -r "$OS_ROOTDIR" -b "${FAKECHROOT_SOURCE_DIR}:/fakechroot" -w / -b /dev \
                -b /etc/resolv.conf:/etc/resolv.conf /bin/bash <<'EOF_ubuntu21_packages'
apt-get -y update
apt-get -y --no-install-recommends install wget debconf devscripts gnupg nano
apt-get -y update
apt-get -y install locales build-essential gcc make autoconf m4 automake gawk libtool bash 
apt-get -y install diffutils file which
EOF_ubuntu21_packages
    fi

    SHELL=/bin/bash CONFIG_SHELL=/bin/bash PATH=/bin:/usr/bin:/sbin:/usr/sbin:/usr/lib \
        $PROOT -r "$OS_ROOTDIR" -b "${FAKECHROOT_SOURCE_DIR}:/fakechroot" -w / -b /dev \
            /bin/bash <<'EOF_ubuntu21_fakechroot'
# BUILD FAKECHROOT
export SHELL=/bin/bash
export CONFIG_SHELL=/bin/bash
export PATH=/bin:/usr/bin:/sbin:/usr/sbin:/usr/lib
cd /fakechroot
make distclean
bash ./configure
make
cp src/.libs/libfakechroot.so libfakechroot-Ubuntu-21.so
make clean
EOF_ubuntu21_fakechroot
    set +xv
}

ubuntu21_build_runc()
{
    echo "ubuntu21_build_runc : $1"
    local OS_ARCH="$1"
    local RUNC_SOURCE_DIR="$2"
    local OS_NAME="ubuntu"
    local OS_RELVER="21"
    local OS_ROOTDIR="${BUILD_DIR}/${OS_NAME}_${OS_RELVER}_${OS_ARCH}"
    local PROOT=""

    if [ "$OS_ARCH" = "i386" ]; then
        #PROOT="$S_PROOT_DIR/proot-x86 -q qemu-i386"
        #PROOT="$S_PROOT_DIR/proot-x86"
        PROOT="$BUILD_DIR/proot-source-x86/proot-Fedora-30.bin"
    elif [ "$OS_ARCH" = "amd64" ]; then
        #PROOT="$S_PROOT_DIR/proot-x86_64"
        PROOT="$BUILD_DIR/proot-source-x86_64/proot-Fedora-30.bin"
    elif [ "$OS_ARCH" = "arm64" ]; then
        #PROOT="$S_PROOT_DIR/proot-x86_64 -q qemu-aarch64"
        PROOT="$BUILD_DIR/proot-source-x86_64/proot-Fedora-30.bin -q qemu-aarch64"
    elif [ "$OS_ARCH" = "ppc64el" ]; then
        #PROOT="$S_PROOT_DIR/proot-x86_64 -q qemu-ppc64le"
        PROOT="$BUILD_DIR/proot-source-x86_64/proot-Fedora-30.bin -q qemu-ppc64le"
    else
        echo "unsupported $OS_NAME architecture: $OS_ARCH"
        exit 2
    fi

    if [ -x "${RUNC_SOURCE_DIR}/runc-Ubuntu-21.bin" ] ; then
        echo "runc binary already compiled : ${RUNC_SOURCE_DIR}/runc-Ubuntu-21.bin"
        return
    fi

    export PROOT_NO_SECCOMP=1

    # compile runc
    mkdir -p "${OS_ROOTDIR}/go/src/github.com/opencontainers"
    set -xv
    SHELL=/bin/bash CONFIG_SHELL=/bin/bash PATH=/bin:/usr/bin:/sbin:/usr/sbin:/usr/lib \
        $PROOT -0 -r "$OS_ROOTDIR" -b "${RUNC_SOURCE_DIR}:/go/src/github.com/opencontainers/runc" -w / -b /dev \
            -b /etc/resolv.conf:/etc/resolv.conf /bin/bash <<'EOF_ubuntu21_runc'
apt-get -y update
apt-get -y install golang libseccomp-dev git software-properties-common
add-apt-repository ppa:gophers/archive
apt-get -y update
apt-get -y install golang-1.11-go
export GOROOT=/usr/lib/go-1.11
export GOPATH=/go
export PATH=$GOPATH/bin:$GOROOT/bin:$PATH
go get github.com/sirupsen/logrus
cd /go/src/github.com/opencontainers/runc
make clean
make static
/bin/mv runc runc-Ubuntu-21.bin
EOF_ubuntu21_runc

    set +xv
}


# #############################################################################
# Ubuntu 22.04
# #############################################################################

ubuntu22_setup()
{
    echo "ubuntu22_setup : $1"
    local OS_ARCH="$1"
    local OS_NAME="ubuntu"
    local OS_RELVER="22"
    local OS_ROOTDIR="${BUILD_DIR}/${OS_NAME}_${OS_RELVER}_${OS_ARCH}"

    if [ -x "${OS_ROOTDIR}/usr/lib/gcc" ] ; then
        echo "os already setup : ${OS_ROOTDIR}"
        return
    fi

    SUDO=sudo

    if [ "$OS_ARCH" = "amd64" ] || [ "$OS_ARCH" = "i386" ]; then
	REPOSITORY_URL="http://archive.ubuntu.com/ubuntu/"
    else
	REPOSITORY_URL="http://ports.ubuntu.com/ubuntu-ports/"
    fi

    $SUDO debootstrap --arch="$OS_ARCH" --variant=buildd jammy "$OS_ROOTDIR" "$REPOSITORY_URL"

    $SUDO /bin/chown -R "$(id -u).$(id -g)" "$OS_ROOTDIR"
    $SUDO /bin/chmod -R u+rw "$OS_ROOTDIR"
}

ubuntu22_build_fakechroot()
{
    echo "ubuntu22_build_fakechroot : $1"
    local OS_ARCH="$1"
    local FAKECHROOT_SOURCE_DIR="$2"
    local OS_NAME="ubuntu"
    local OS_RELVER="22"
    local OS_ROOTDIR="${BUILD_DIR}/${OS_NAME}_${OS_RELVER}_${OS_ARCH}"
    local PROOT=""

    if [ "$OS_ARCH" = "i386" ]; then
        #PROOT="$S_PROOT_DIR/proot-x86"
        PROOT="$BUILD_DIR/proot-source-x86/proot-Fedora-30.bin"
    elif [ "$OS_ARCH" = "amd64" ]; then
        #PROOT="$S_PROOT_DIR/proot-x86_64"
        PROOT="$BUILD_DIR/proot-source-x86_64/proot-Fedora-30.bin"
    elif [ "$OS_ARCH" = "arm64" ]; then
        #PROOT="$S_PROOT_DIR/proot-x86_64 -q qemu-aarch64"
        PROOT="$BUILD_DIR/proot-source-x86_64/proot-Fedora-30.bin -q qemu-aarch64"
    elif [ "$OS_ARCH" = "armhf" ]; then
        #PROOT="$S_PROOT_DIR/proot-x86_64 -q qemu-aarch64"
        PROOT="$BUILD_DIR/proot-source-x86_64/proot-Fedora-30.bin -q qemu-aarch64"
    elif [ "$OS_ARCH" = "ppc64el" ]; then
        #PROOT="$S_PROOT_DIR/proot-x86_64 -q qemu-ppc64le"
        PROOT="$BUILD_DIR/proot-source-x86_64/proot-Fedora-30.bin -q qemu-ppc64le"
    elif [ "$OS_ARCH" = "riscv64" ]; then
        #PROOT="$S_PROOT_DIR/proot-x86_64 -q qemu-riscv64"
        PROOT="$BUILD_DIR/proot-source-x86_64/proot-Fedora-30.bin -q qemu-riscv64"
    else
        echo "unsupported $OS_NAME architecture: $OS_ARCH"
        exit 2
    fi

    if [ -x "${FAKECHROOT_SOURCE_DIR}/libfakechroot-Ubuntu-22.so" ] ; then
        echo "fakechroot binary already compiled : ${FAKECHROOT_SOURCE_DIR}/libfakechroot-Ubuntu-22.so"
        return
    fi

    export PROOT_NO_SECCOMP=1

    # compile fakechroot
    set -xv
    if [ ! -x "$OS_ROOTDIR/bin/bash" ] ; then
        SHELL=/bin/bash CONFIG_SHELL=/bin/bash PATH=/bin:/usr/bin:/sbin:/usr/sbin:/usr/lib \
            $PROOT -0 -r "$OS_ROOTDIR" -b "${FAKECHROOT_SOURCE_DIR}:/fakechroot" -w / -b /dev \
                -b /etc/resolv.conf:/etc/resolv.conf /bin/bash <<'EOF_ubuntu22_packages'
apt-get -y update
apt-get -y --no-install-recommends install wget debconf devscripts gnupg nano
apt-get -y update
apt-get -y install locales build-essential gcc make autoconf m4 automake gawk libtool bash 
apt-get -y install diffutils file which
EOF_ubuntu22_packages
    fi

    SHELL=/bin/bash CONFIG_SHELL=/bin/bash PATH=/bin:/usr/bin:/sbin:/usr/sbin:/usr/lib \
        $PROOT -r "$OS_ROOTDIR" -b "${FAKECHROOT_SOURCE_DIR}:/fakechroot" -w / -b /dev \
            /bin/bash <<'EOF_ubuntu22_fakechroot'
# BUILD FAKECHROOT
export SHELL=/bin/bash
export CONFIG_SHELL=/bin/bash
export PATH=/bin:/usr/bin:/sbin:/usr/sbin:/usr/lib
cd /fakechroot
make distclean
bash ./configure
make
cp src/.libs/libfakechroot.so libfakechroot-Ubuntu-22.so
make clean
EOF_ubuntu22_fakechroot
    set +xv
}

ubuntu22_build_runc()
{
    echo "ubuntu22_build_runc : $1"
    local OS_ARCH="$1"
    local RUNC_SOURCE_DIR="$2"
    local OS_NAME="ubuntu"
    local OS_RELVER="22"
    local OS_ROOTDIR="${BUILD_DIR}/${OS_NAME}_${OS_RELVER}_${OS_ARCH}"
    local PROOT=""

    if [ "$OS_ARCH" = "i386" ]; then
        #PROOT="$S_PROOT_DIR/proot-x86"
        PROOT="$BUILD_DIR/proot-source-x86/proot-Fedora-30.bin"
    elif [ "$OS_ARCH" = "amd64" ]; then
        #PROOT="$S_PROOT_DIR/proot-x86_64"
        PROOT="$BUILD_DIR/proot-source-x86_64/proot-Fedora-30.bin"
    elif [ "$OS_ARCH" = "arm64" ]; then
        #PROOT="$S_PROOT_DIR/proot-x86_64 -q qemu-aarch64"
        PROOT="$BUILD_DIR/proot-source-x86_64/proot-Fedora-30.bin -q qemu-aarch64"
    elif [ "$OS_ARCH" = "ppc64el" ]; then
        #PROOT="$S_PROOT_DIR/proot-x86_64 -q qemu-ppc64le"
        PROOT="$BUILD_DIR/proot-source-x86_64/proot-Fedora-30.bin -q qemu-ppc64le"
    else
        echo "unsupported $OS_NAME architecture: $OS_ARCH"
        exit 2
    fi

    if [ -x "${RUNC_SOURCE_DIR}/runc-Ubuntu-22.bin" ] ; then
        echo "runc binary already compiled : ${RUNC_SOURCE_DIR}/runc-Ubuntu-22.bin"
        return
    fi

    #export PROOT_NO_SECCOMP=1
    unset PROOT_NO_SECCOMP

    # compile runc
    mkdir -p "${OS_ROOTDIR}/go/src/github.com/opencontainers"
    set -xv
    SHELL=/bin/bash CONFIG_SHELL=/bin/bash PATH=/bin:/usr/bin:/sbin:/usr/sbin:/usr/lib \
        $PROOT -0 -r "$OS_ROOTDIR" -b "${RUNC_SOURCE_DIR}:/go/src/github.com/opencontainers/runc" -w / -b /dev \
            -b /etc/resolv.conf:/etc/resolv.conf /bin/bash <<'EOF_ubuntu22_runc'
apt-get -y update
apt-get -y install golang libseccomp-dev git software-properties-common
#add-apt-repository ppa:gophers/archive
#apt-get -y update
#apt-get -y install golang-1.11-go
#export GOROOT=/usr/lib/go-1.11
#export GOPATH=/go
#export PATH=$GOPATH/bin:$GOROOT/bin:$PATH
#go get github.com/sirupsen/logrus
cd /go/src/github.com/opencontainers/runc
make clean
make static
/bin/mv runc runc-Ubuntu-22.bin
EOF_ubuntu22_runc

    set +xv
}

ubuntu22_build_runc_root()
{
    echo "ubuntu22_build_runc : $1"
    local OS_ARCH="$1"
    local RUNC_SOURCE_DIR="$2"
    local OS_NAME="ubuntu"
    local OS_RELVER="22"
    local OS_ROOTDIR="${BUILD_DIR}/${OS_NAME}_${OS_RELVER}_${OS_ARCH}"
    local PROOT=""

    if [ "$OS_ARCH" = "i386" ]; then
        QEMU=""
    elif [ "$OS_ARCH" = "amd64" ]; then
        QEMU=""
    elif [ "$OS_ARCH" = "arm64" ]; then
	QEMU="/qemu"
	/bin/cp -f "$(which qemu-aarch64-static)" "${OS_ROOTDIR}/${QEMU}"
	chmod u+rx "${OS_ROOTDIR}/${QEMU}"
    elif [ "$OS_ARCH" = "ppc64el" ]; then
	QEMU="/qemu"
	/bin/cp -f "$(which qemu-ppc64le-static)" "${OS_ROOTDIR}/${QEMU}"
	chmod u+rx "${OS_ROOTDIR}/${QEMU}"
    else
        echo "unsupported $OS_NAME architecture: $OS_ARCH"
        exit 2
    fi

    if [ -x "${RUNC_SOURCE_DIR}/runc-Ubuntu-22.bin" ] ; then
        echo "runc binary already compiled : ${RUNC_SOURCE_DIR}/runc-Ubuntu-22.bin"
        return
    fi

    #export PROOT_NO_SECCOMP=1
    unset PROOT_NO_SECCOMP

    # compile runc
    mkdir -p "${OS_ROOTDIR}/go/src/github.com/opencontainers"
    set -xv
    $SUDO mount --bind "${RUNC_SOURCE_DIR}" "$OS_ROOTDIR/go/src/github.com/opencontainers/runc"
    $SUDO mount --bind "/etc/resolv.conf" "$OS_ROOTDIR/etc/resolv.conf"

    $SUDO chroot --userspec="root" "$OS_ROOTDIR" /qemu /bin/bash <<EOF_ubuntu22_root_setup
groupadd --gid "$(id -g)" "$USER"
adduser --home / --uid "$(id -u)" --gid "$(id -g)" --no-create-home --shell /bin/bash "$USER"
EOF_ubuntu22_root_setup

    $SUDO chroot --userspec="jorge" "$OS_ROOTDIR" /qemu /bin/bash <<'EOF_ubuntu22_runc_root'
export SHELL=/bin/bash 
export CONFIG_SHELL=/bin/bash
export PATH=/bin:/usr/bin:/sbin:/usr/sbin:/usr/lib
apt-get -y update
apt-get -y install golang libseccomp-dev git software-properties-common
#add-apt-repository ppa:gophers/archive
#apt-get -y update
#apt-get -y install golang-1.11-go
#export GOROOT=/usr/lib/go-1.11
#export GOPATH=/go
#export PATH=$GOPATH/bin:$GOROOT/bin:$PATH
#go get github.com/sirupsen/logrus
cd /go/src/github.com/opencontainers/runc
make clean
make static
/bin/mv runc runc-Ubuntu-22.bin
EOF_ubuntu22_runc_root
    $SUDO umount "$OS_ROOTDIR/go/src/github.com/opencontainers/runc"
    $SUDO umount "$OS_ROOTDIR/etc/resolv.conf"
    set +xv
}


# #############################################################################
# Ubuntu 23.04
# #############################################################################

ubuntu23_setup()
{
    echo "ubuntu23_setup : $1"
    local OS_ARCH="$1"
    local OS_NAME="ubuntu"
    local OS_RELVER="23"
    local OS_ROOTDIR="${BUILD_DIR}/${OS_NAME}_${OS_RELVER}_${OS_ARCH}"

    if [ -x "${OS_ROOTDIR}/usr/lib/gcc" ] ; then
        echo "os already setup : ${OS_ROOTDIR}"
        return
    fi

    SUDO=sudo

    if [ "$OS_ARCH" = "amd64" ] || [ "$OS_ARCH" = "i386" ]; then
	REPOSITORY_URL="http://archive.ubuntu.com/ubuntu/"
    else
	REPOSITORY_URL="http://ports.ubuntu.com/ubuntu-ports/"
    fi

    $SUDO debootstrap --arch="$OS_ARCH" --variant=buildd lunar "$OS_ROOTDIR" "$REPOSITORY_URL"

    $SUDO /bin/chown -R "$(id -u).$(id -g)" "$OS_ROOTDIR"
    $SUDO /bin/chmod -R u+rw "$OS_ROOTDIR"
}

ubuntu23_build_fakechroot()
{
    echo "ubuntu23_build_fakechroot : $1"
    local OS_ARCH="$1"
    local FAKECHROOT_SOURCE_DIR="$2"
    local OS_NAME="ubuntu"
    local OS_RELVER="23"
    local OS_ROOTDIR="${BUILD_DIR}/${OS_NAME}_${OS_RELVER}_${OS_ARCH}"
    local PROOT=""

    if [ "$OS_ARCH" = "i386" ]; then
        #PROOT="$S_PROOT_DIR/proot-x86 -q qemu-i386"
        #PROOT="$S_PROOT_DIR/proot-x86"
	PROOT="$BUILD_DIR/proot-source-x86/proot-Fedora-30.bin"
    elif [ "$OS_ARCH" = "amd64" ]; then
        #PROOT="$S_PROOT_DIR/proot-x86_64"
	PROOT="$BUILD_DIR/proot-source-x86_64/proot-Fedora-30.bin"
    elif [ "$OS_ARCH" = "arm64" ]; then
        #PROOT="$S_PROOT_DIR/proot-x86_64 -q qemu-aarch64"
        PROOT="$BUILD_DIR/proot-source-x86_64/proot-Fedora-30.bin -q qemu-aarch64"
    elif [ "$OS_ARCH" = "ppc64el" ]; then
        #PROOT="$S_PROOT_DIR/proot-x86_64 -q qemu-ppc64le"
        PROOT="$BUILD_DIR/proot-source-x86_64/proot-Fedora-30.bin -q qemu-ppc64le"
    else
        echo "unsupported $OS_NAME architecture: $OS_ARCH"
        exit 2
    fi

    if [ -x "${FAKECHROOT_SOURCE_DIR}/libfakechroot-Ubuntu-23.so" ] ; then
        echo "fakechroot binary already compiled : ${FAKECHROOT_SOURCE_DIR}/libfakechroot-Ubuntu-23.so"
        return
    fi

    export PROOT_NO_SECCOMP=1

    # compile fakechroot
    set -xv
    if [ ! -x "$OS_ROOTDIR/bin/bash" ] ; then
        SHELL=/bin/bash CONFIG_SHELL=/bin/bash PATH=/bin:/usr/bin:/sbin:/usr/sbin:/usr/lib \
            $PROOT -0 -r "$OS_ROOTDIR" -b "${FAKECHROOT_SOURCE_DIR}:/fakechroot" -w / -b /dev \
                -b /etc/resolv.conf:/etc/resolv.conf /bin/bash <<'EOF_ubuntu23_packages'
apt-get -y update
apt-get -y --no-install-recommends install wget debconf devscripts gnupg nano
apt-get -y update
apt-get -y install locales build-essential gcc make autoconf m4 automake gawk libtool bash 
apt-get -y install diffutils file which
EOF_ubuntu23_packages
    fi

    SHELL=/bin/bash CONFIG_SHELL=/bin/bash PATH=/bin:/usr/bin:/sbin:/usr/sbin:/usr/lib \
        $PROOT -r "$OS_ROOTDIR" -b "${FAKECHROOT_SOURCE_DIR}:/fakechroot" -w / -b /dev \
            /bin/bash <<'EOF_ubuntu23_fakechroot'
# BUILD FAKECHROOT
export SHELL=/bin/bash
export CONFIG_SHELL=/bin/bash
export PATH=/bin:/usr/bin:/sbin:/usr/sbin:/usr/lib
cd /fakechroot
make distclean
bash ./configure
make
cp src/.libs/libfakechroot.so libfakechroot-Ubuntu-23.so
make clean
EOF_ubuntu23_fakechroot
    set +xv
}

ubuntu23_build_runc()
{
    echo "ubuntu23_build_runc : $1"
    local OS_ARCH="$1"
    local RUNC_SOURCE_DIR="$2"
    local OS_NAME="ubuntu"
    local OS_RELVER="23"
    local OS_ROOTDIR="${BUILD_DIR}/${OS_NAME}_${OS_RELVER}_${OS_ARCH}"
    local PROOT=""

    if [ "$OS_ARCH" = "i386" ]; then
        #PROOT="$S_PROOT_DIR/proot-x86 -q qemu-i386"
        #PROOT="$S_PROOT_DIR/proot-x86"
        PROOT="$BUILD_DIR/proot-source-x86/proot-Fedora-30.bin"
    elif [ "$OS_ARCH" = "amd64" ]; then
        #PROOT="$S_PROOT_DIR/proot-x86_64"
        PROOT="$BUILD_DIR/proot-source-x86_64/proot-Fedora-30.bin"
    elif [ "$OS_ARCH" = "arm64" ]; then
        #PROOT="$S_PROOT_DIR/proot-x86_64 -q qemu-aarch64"
        PROOT="$BUILD_DIR/proot-source-x86_64/proot-Fedora-30.bin -q qemu-aarch64"
    elif [ "$OS_ARCH" = "ppc64el" ]; then
        #PROOT="$S_PROOT_DIR/proot-x86_64 -q qemu-ppc64le"
        PROOT="$BUILD_DIR/proot-source-x86_64/proot-Fedora-30.bin -q qemu-ppc64le"
    else
        echo "unsupported $OS_NAME architecture: $OS_ARCH"
        exit 2
    fi

    if [ -x "${RUNC_SOURCE_DIR}/runc-Ubuntu-23.bin" ] ; then
        echo "runc binary already compiled : ${RUNC_SOURCE_DIR}/runc-Ubuntu-23.bin"
        return
    fi

    export PROOT_NO_SECCOMP=1

    # compile runc
    mkdir -p "${OS_ROOTDIR}/go/src/github.com/opencontainers"
    set -xv
    SHELL=/bin/bash CONFIG_SHELL=/bin/bash PATH=/bin:/usr/bin:/sbin:/usr/sbin:/usr/lib \
        $PROOT -0 -r "$OS_ROOTDIR" -b "${RUNC_SOURCE_DIR}:/go/src/github.com/opencontainers/runc" -w / -b /dev \
            -b /etc/resolv.conf:/etc/resolv.conf /bin/bash <<'EOF_ubuntu23_runc'
apt-get -y update
apt-get -y install golang libseccomp-dev git software-properties-common
#add-apt-repository ppa:gophers/archive
#apt-get -y update
#apt-get -y install golang-1.11-go
#export GOROOT=/usr/lib/go-1.11
#export GOPATH=/go
#export PATH=$GOPATH/bin:$GOROOT/bin:$PATH
#go get github.com/sirupsen/logrus
cd /go/src/github.com/opencontainers/runc
make static
/bin/mv runc runc-Ubuntu-23.bin
EOF_ubuntu23_runc

    set +xv
}


# #############################################################################
# Debian 10
# #############################################################################

debian10_setup()
{
    echo "debian10_setup : $1"
    local OS_ARCH="$1"
    local OS_NAME="debian"
    local OS_RELVER="10"
    local OS_ROOTDIR="${BUILD_DIR}/${OS_NAME}_${OS_RELVER}_${OS_ARCH}"

    if [ -x "${OS_ROOTDIR}/usr/lib/gcc" ] ; then
        echo "os already setup : ${OS_ROOTDIR}"
        return
    fi

    SUDO=sudo

    if [ "$OS_ARCH" = "amd64" ] || [ "$OS_ARCH" = "i386" ]; then
	REPOSITORY_URL="http://ftp.debian.org/debian/"
    else
	REPOSITORY_URL="http://ftp.debian.org/debian/"
    fi

    #$SUDO debootstrap --arch=armhf sid /chroots/sid-armhf http://ftp.debian.org/debian/
    $SUDO debootstrap --arch="$OS_ARCH" buster "$OS_ROOTDIR" "$REPOSITORY_URL"

    $SUDO /bin/chown -R "$(id -u).$(id -g)" "$OS_ROOTDIR"
    $SUDO /bin/chmod -R u+rw "$OS_ROOTDIR"
}


debian10_build_proot()
{
    echo "debian10_build_proot : $1"
    local OS_ARCH="$1"
    local PROOT_SOURCE_DIR="$2"
    local OS_NAME="debian"
    local OS_RELVER="10"
    local OS_ROOTDIR="${BUILD_DIR}/${OS_NAME}_${OS_RELVER}_${OS_ARCH}"
    local PROOT=""

    if [ "$OS_ARCH" = "i386" ]; then
        #PROOT="$S_PROOT_DIR/proot-x86"
        PROOT="$BUILD_DIR/proot-source-x86/proot-Fedora-30.bin"
    elif [ "$OS_ARCH" = "x86_64" ]; then
        #PROOT="$HOME/.udocker/bin/proot-x86_64"
        PROOT="$BUILD_DIR/proot-source-x86_64/proot-Fedora-30.bin"
    elif [ "$OS_ARCH" = "aarch64" ]; then
        #PROOT="$S_PROOT_DIR/proot-x86_64 -q qemu-aarch64"
        PROOT="$BUILD_DIR/proot-source-x86_64/proot-Fedora-30.bin -q qemu-aarch64"
    elif [ "$OS_ARCH" = "armhf" ]; then
        #PROOT="$S_PROOT_DIR/proot-x86_64 -q qemu-arm"
        PROOT="$BUILD_DIR/proot-source-x86_64/proot-Fedora-30.bin -q qemu-arm"
    elif [ "$OS_ARCH" = "armel" ]; then
        #PROOT="$S_PROOT_DIR/proot-x86_64 -q qemu-arm"
        PROOT="$BUILD_DIR/proot-source-x86_64/proot-Fedora-30.bin -q qemu-arm"
    else
        echo "unsupported $OS_NAME architecture: $OS_ARCH"
        exit 2
    fi

    export PROOT_NO_SECCOMP=1

    if [ -x "${PROOT_SOURCE_DIR}/proot-Debian-10.bin" ] ; then
        echo "proot binary already compiled : ${PROOT_SOURCE_DIR}/proot-Debian-10.bin"
    else
        # compile proot
        $PROOT -0 -r "$OS_ROOTDIR" -b "${PROOT_SOURCE_DIR}:/proot" -w / -b /dev \
                           -b "${S_PROOT_PACKAGES_DIR}:/proot-static-packages"   /bin/bash <<'EOF_debian10_proot_1'
apt-get -y update
apt-get -y install locales build-essential gcc make autoconf m4 automake gawk libtool bash
apt-get -y install diffutils file make python3 python3-dev
cd /proot
/bin/rm -f proot-Debian-10.bin src/proot src/libtalloc.a src/talloc.h
/bin/rm -Rf talloc*
# BUILD TALLOC
tar xzvf /proot-static-packages/talloc.tar.gz
cd talloc*
make clean
./configure
make
cp talloc.h /proot/src
cd bin/default
[ -f talloc.c.6.o ] && ar qf libtalloc.a talloc.c.6.o
[ -f talloc.c.5.o -a ! -f libtalloc.a ] && ar qf libtalloc.a talloc.c.5.o
cp libtalloc.a /proot/src && make clean
# BUILD PROOT
cd /proot/src
make clean
make loader.elf
make loader-m32.elf
make build.h
LDFLAGS="-L/proot/usr/src -static" make proot
EOF_debian10_proot_1
    fi

    if [ -e "${PROOT_SOURCE_DIR}/src/proot" ]; then
        mv "${PROOT_SOURCE_DIR}/src/proot" "${PROOT_SOURCE_DIR}/proot-Debian-10.bin"
    fi

    if [ ! -e "${PROOT_SOURCE_DIR}/proot-Debian-10.bin" ]; then
        echo "proot compilation failed ${PROOT_SOURCE_DIR}/proot-Debian-10.bin not found"
        exit 1
    fi
}

# #############################################################################
# Debian 12
# #############################################################################

debian12_setup()
{
    echo "debian12_setup : $1"
    local OS_ARCH="$1"
    local OS_NAME="debian"
    local OS_RELVER="12"
    local OS_ROOTDIR="${BUILD_DIR}/${OS_NAME}_${OS_RELVER}_${OS_ARCH}"

    if [ -x "${OS_ROOTDIR}/usr/lib/gcc" ] ; then
        echo "os already setup : ${OS_ROOTDIR}"
        return
    fi

    SUDO=sudo

    if [ "$OS_ARCH" = "amd64" ] || [ "$OS_ARCH" = "i386" ]; then
	REPOSITORY_URL="http://ftp.debian.org/debian/"
    else
	REPOSITORY_URL="http://ftp.debian.org/debian/"
    fi

    #$SUDO debootstrap --arch=armhf sid /chroots/sid-armhf http://ftp.debian.org/debian/
    $SUDO debootstrap --arch="$OS_ARCH" buster "$OS_ROOTDIR" "$REPOSITORY_URL"

    $SUDO /bin/chown -R "$(id -u).$(id -g)" "$OS_ROOTDIR"
    $SUDO /bin/chmod -R u+rw "$OS_ROOTDIR"
}


debian12_build_fakechroot()
{
    echo "debian12_build_fakechroot : $1"
    local OS_ARCH="$1"
    local FAKECHROOT_SOURCE_DIR="$2"
    local OS_NAME="debian"
    local OS_RELVER="12"
    local OS_ROOTDIR="${BUILD_DIR}/${OS_NAME}_${OS_RELVER}_${OS_ARCH}"
    local PROOT=""

    if [ "$OS_ARCH" = "i386" ]; then
        #PROOT="$S_PROOT_DIR/proot-x86"
        PROOT="$BUILD_DIR/proot-source-x86/proot-Fedora-30.bin"
    elif [ "$OS_ARCH" = "amd64" ]; then
        #PROOT="$S_PROOT_DIR/proot-x86_64"
        PROOT="$BUILD_DIR/proot-source-x86_64/proot-Fedora-30.bin"
    elif [ "$OS_ARCH" = "arm64" ]; then
        #PROOT="$S_PROOT_DIR/proot-x86_64 -q qemu-aarch64"
        PROOT="$BUILD_DIR/proot-source-x86_64/proot-Fedora-30.bin -q qemu-aarch64"
    elif [ "$OS_ARCH" = "armhf" ]; then
        #PROOT="$S_PROOT_DIR/proot-x86_64 -q qemu-aarch64"
        PROOT="$BUILD_DIR/proot-source-x86_64/proot-Fedora-30.bin -q qemu-aarch64"
    elif [ "$OS_ARCH" = "ppc64el" ]; then
        #PROOT="$S_PROOT_DIR/proot-x86_64 -q qemu-ppc64le"
        PROOT="$BUILD_DIR/proot-source-x86_64/proot-Fedora-30.bin -q qemu-ppc64le"
    elif [ "$OS_ARCH" = "riscv64" ]; then
        #PROOT="$S_PROOT_DIR/proot-x86_64 -q qemu-riscv64"
        PROOT="$BUILD_DIR/proot-source-x86_64/proot-Fedora-30.bin -q qemu-riscv64"
    else
        echo "unsupported $OS_NAME architecture: $OS_ARCH"
        exit 2
    fi

    if [ -x "${FAKECHROOT_SOURCE_DIR}/libfakechroot-debian-12.so" ] ; then
        echo "fakechroot binary already compiled : ${FAKECHROOT_SOURCE_DIR}/libfakechroot-debian-12.so"
        return
    fi

    export PROOT_NO_SECCOMP=1

    # compile fakechroot
    set -xv
    if [ ! -x "$OS_ROOTDIR/usr/bin/make" ] ; then
        SHELL=/bin/bash CONFIG_SHELL=/bin/bash PATH=/bin:/usr/bin:/sbin:/usr/sbin:/usr/lib \
            $PROOT -0 -r "$OS_ROOTDIR" -b "${FAKECHROOT_SOURCE_DIR}:/fakechroot" -w / -b /dev \
                -b /etc/resolv.conf:/etc/resolv.conf /bin/bash <<'EOF_debian12_packages'
apt-get -y update
apt-get -y --no-install-recommends install wget debconf devscripts gnupg nano
apt-get -y update
apt-get -y install locales build-essential gcc make autoconf m4 automake gawk libtool bash 
apt-get -y install diffutils file which
EOF_debian12_packages
    fi

    SHELL=/bin/bash CONFIG_SHELL=/bin/bash PATH=/bin:/usr/bin:/sbin:/usr/sbin:/usr/lib \
        $PROOT -r "$OS_ROOTDIR" -b "${FAKECHROOT_SOURCE_DIR}:/fakechroot" -w / -b /dev \
            /bin/bash <<'EOF_debian12_fakechroot'
# BUILD FAKECHROOT
export SHELL=/bin/bash
export CONFIG_SHELL=/bin/bash
export PATH=/bin:/usr/bin:/sbin:/usr/sbin:/usr/lib
cd /fakechroot
make distclean
bash ./configure
make
cp src/.libs/libfakechroot.so libfakechroot-debian-12.so
make clean
EOF_debian12_fakechroot
    set +xv
}


# #############################################################################
# Alpine 3.6.x
# #############################################################################

alpine36_setup()
{
    echo "alpine36_setup : $1"
    local ALPINE_MIRROR="http://dl-5.alpinelinux.org/alpine"
    local APK_TOOLS="apk-tools-static-2.7.6-r0.apk"
    local APK_TOOLS_DIR="${BUILD_DIR}/apk-tools-2.7.6-r0"
    local OS_ARCH="$1"
    local OS_NAME="alpine"
    local OS_RELVER="v3.6"
    local OS_ROOTDIR="${BUILD_DIR}/${OS_NAME}_${OS_RELVER}_${OS_ARCH}"

    if [ -x "${OS_ROOTDIR}/etc/alpine-release" ] ; then
        echo "os already setup : ${OS_ROOTDIR}"
        return
    fi

    if [ -e "${APK_TOOLS_DIR}/sbin" ] ; then
        echo "apk-tools already installed : ${APK_TOOLS_DIR}"
    else
        /bin/rm -f "${APK_TOOLS}"
        mkdir "${APK_TOOLS_DIR}"
        local APK_TOOLS_URL="${ALPINE_MIRROR}/${OS_RELVER}/main/${OS_ARCH}/${APK_TOOLS}"
        echo "download apk-tools : ${APK_TOOLS_URL}"
	(cd "${APK_TOOLS_DIR}"; curl "${APK_TOOLS_URL}" > "${APK_TOOLS}")
	(cd "${APK_TOOLS_DIR}"; tar xzvf "${APK_TOOLS}")
        if [ ! -e "${APK_TOOLS_DIR}/sbin" ] ; then
            echo "apk-tools install failed: ${APK_TOOLS_DIR}"
            exit
        fi
    fi

    SUDO=sudo

    $SUDO "${APK_TOOLS_DIR}/sbin/apk.static" \
        -X "${ALPINE_MIRROR}/${OS_RELVER}/main" \
        -U \
        --allow-untrusted \
        --root "${OS_ROOTDIR}" \
        --initdb add alpine-base alpine-sdk bash libc-dev make autoconf m4 automake \
                     libbsd libbsd-dev fts fts-dev libconfig-dev musl-dev bash diffutils \
		     file

    $SUDO /bin/chown -R "$(id -u).$(id -g)" "${OS_ROOTDIR}"
    $SUDO /bin/chmod -R u+rw "${OS_ROOTDIR}"
    /bin/mkdir -p "${OS_ROOTDIR}/proc"
    /bin/mkdir -p "${OS_ROOTDIR}/root"
    /bin/mkdir -p "${OS_ROOTDIR}/etc/apk"
    /bin/echo "$ALPINE_MIRROR/$OS_RELVER/main" >  "${OS_ROOTDIR}/etc/apk/repositories"
}

alpine36_build_fakechroot()
{
    echo "alpine36_build_fakechroot : $1"
    local OS_ARCH="$1"
    local FAKECHROOT_SOURCE_DIR="$2"
    local OS_NAME="alpine"
    local OS_RELVER="v3.6"
    local OS_ROOTDIR="${BUILD_DIR}/${OS_NAME}_${OS_RELVER}_${OS_ARCH}"
    local PROOT=""

    if [ "$OS_ARCH" = "i386" ]; then
        #PROOT="$S_PROOT_DIR/proot-x86 -q qemu-i386"
        #PROOT="$S_PROOT_DIR/proot-x86"
        PROOT="$BUILD_DIR/proot-source-x86/proot-Fedora-30.bin"
    elif [ "$OS_ARCH" = "x86_64" ]; then
        #PROOT="$S_PROOT_DIR/proot-x86_64"
        PROOT="$BUILD_DIR/proot-source-x86_64/proot-Fedora-30.bin"
    else
        echo "unsupported $OS_NAME architecture: $OS_ARCH"
        exit 2
    fi

    if [ -x "${FAKECHROOT_SOURCE_DIR}/libfakechroot-Alpine-3.6.so" ] ; then
        echo "fakechroot binary already compiled : ${FAKECHROOT_SOURCE_DIR}/libfakechroot-Alpine-3.6.so"
        return
    fi

    export PROOT_NO_SECCOMP=1

    # compile fakechroot
    set -xv

    SHELL=/bin/bash CONFIG_SHELL=/bin/bash PATH=/bin:/usr/bin:/sbin:/usr/sbin:/usr/lib \
        $PROOT -r "$OS_ROOTDIR" -b "${FAKECHROOT_SOURCE_DIR}:/fakechroot" -w / -b /dev \
            /bin/bash <<'EOF_alpine36_fakechroot'
# BUILD FAKECHROOT
export SHELL=/bin/bash
export CONFIG_SHELL=/bin/bash
export PATH=/bin:/usr/bin:/sbin:/usr/sbin:/usr/lib
cd /fakechroot
make distclean
bash ./configure
make
cp src/.libs/libfakechroot.so libfakechroot-Alpine-3.6.so
make clean
EOF_alpine36_fakechroot
    set +xv
}

# #############################################################################
# Alpine 3.8.x
# #############################################################################

alpine38_setup()
{
    echo "alpine38_setup : $1"
    local ALPINE_MIRROR="http://dl-5.alpinelinux.org/alpine"
    local APK_TOOLS="apk-tools-static-2.10.6-r0.apk"
    local APK_TOOLS_DIR="${BUILD_DIR}/apk-tools-2.10.6-r0"
    local OS_ARCH="$1"
    local OS_NAME="alpine"
    local OS_RELVER="v3.8"
    local OS_ROOTDIR="${BUILD_DIR}/${OS_NAME}_${OS_RELVER}_${OS_ARCH}"

    if [ -x "${OS_ROOTDIR}/etc/alpine-release" ] ; then
        echo "os already setup : ${OS_ROOTDIR}"
        return
    fi

    if [ -e "${APK_TOOLS_DIR}/sbin" ] ; then
        echo "apk-tools already installed : ${APK_TOOLS_DIR}"
    else
        /bin/rm -f "${APK_TOOLS}"
        mkdir "${APK_TOOLS_DIR}"
        local APK_TOOLS_URL="${ALPINE_MIRROR}/${OS_RELVER}/main/${OS_ARCH}/${APK_TOOLS}"
        echo "download apk-tools : ${APK_TOOLS_URL}"
	(cd "${APK_TOOLS_DIR}"; curl "${APK_TOOLS_URL}" > "${APK_TOOLS}")
	(cd "${APK_TOOLS_DIR}"; tar xzvf "${APK_TOOLS}")
        if [ ! -e "${APK_TOOLS_DIR}/sbin" ] ; then
            echo "apk-tools install failed: ${APK_TOOLS_DIR}"
            exit
        fi
    fi

    SUDO=sudo

    $SUDO "${APK_TOOLS_DIR}/sbin/apk.static" \
        -X "${ALPINE_MIRROR}/${OS_RELVER}/main" \
        -U \
        --allow-untrusted \
        --root "${OS_ROOTDIR}" \
        --initdb add alpine-base alpine-sdk bash libc-dev make autoconf m4 automake \
                     libbsd libbsd-dev fts fts-dev libconfig-dev musl-dev bash diffutils file

    $SUDO /bin/chown -R "$(id -u).$(id -g)" "${OS_ROOTDIR}"
    $SUDO /bin/chmod -R u+rw "${OS_ROOTDIR}"
    /bin/mkdir -p "${OS_ROOTDIR}/proc"
    /bin/mkdir -p "${OS_ROOTDIR}/root"
    /bin/mkdir -p "${OS_ROOTDIR}/etc/apk"
    /bin/echo "$ALPINE_MIRROR/$OS_RELVER/main" >  "${OS_ROOTDIR}/etc/apk/repositories"
}

alpine38_build_fakechroot()
{
    echo "alpine38_build_fakechroot : $1"
    local OS_ARCH="$1"
    local FAKECHROOT_SOURCE_DIR="$2"
    local OS_NAME="alpine"
    local OS_RELVER="v3.8"
    local OS_ROOTDIR="${BUILD_DIR}/${OS_NAME}_${OS_RELVER}_${OS_ARCH}"
    local PROOT=""

    if [ "$OS_ARCH" = "i386" ]; then
        #PROOT="$S_PROOT_DIR/proot-x86 -q qemu-i386"
        #PROOT="$S_PROOT_DIR/proot-x86"
        PROOT="$BUILD_DIR/proot-source-x86/proot-Fedora-30.bin"
    elif [ "$OS_ARCH" = "x86_64" ]; then
        #PROOT="$S_PROOT_DIR/proot-x86_64"
        PROOT="$BUILD_DIR/proot-source-x86_64/proot-Fedora-30.bin"
    else
        echo "unsupported $OS_NAME architecture: $OS_ARCH"
        exit 2
    fi

    if [ -x "${FAKECHROOT_SOURCE_DIR}/libfakechroot-Alpine-3.8.so" ] ; then
        echo "fakechroot binary already compiled : ${FAKECHROOT_SOURCE_DIR}/libfakechroot-Alpine-3.8.so"
        return
    fi

    export PROOT_NO_SECCOMP=1

    # compile fakechroot
    set -xv

    SHELL=/bin/bash CONFIG_SHELL=/bin/bash PATH=/bin:/usr/bin:/sbin:/usr/sbin:/usr/lib \
        $PROOT -r "$OS_ROOTDIR" -b "${FAKECHROOT_SOURCE_DIR}:/fakechroot" -w / -b /dev \
            /bin/bash <<'EOF_alpine38_fakechroot'
# BUILD FAKECHROOT
export SHELL=/bin/bash
export CONFIG_SHELL=/bin/bash
export PATH=/bin:/usr/bin:/sbin:/usr/sbin:/usr/lib
cd /fakechroot
make distclean
bash ./configure
make
cp src/.libs/libfakechroot.so libfakechroot-Alpine-3.8.so
make clean
EOF_alpine38_fakechroot
    set +xv
}

# #############################################################################
# Alpine 3.9.x
# #############################################################################

alpine39_setup()
{
    echo "alpine39_setup : $1"
    local ALPINE_MIRROR="http://dl-5.alpinelinux.org/alpine"
    local APK_TOOLS="apk-tools-static-2.10.6-r0.apk"
    local APK_TOOLS_DIR="${BUILD_DIR}/apk-tools-2.10.6-r0"
    local OS_ARCH="$1"
    local OS_NAME="alpine"
    local OS_RELVER="v3.9"
    local OS_ROOTDIR="${BUILD_DIR}/${OS_NAME}_${OS_RELVER}_${OS_ARCH}"

    if [ -x "${OS_ROOTDIR}/etc/alpine-release" ] ; then
        echo "os already setup : ${OS_ROOTDIR}"
        return
    fi

    if [ -e "${APK_TOOLS_DIR}/sbin" ] ; then
        echo "apk-tools already installed : ${APK_TOOLS_DIR}"
    else
        /bin/rm -f "${APK_TOOLS}"
        mkdir "${APK_TOOLS_DIR}"
        local APK_TOOLS_URL="${ALPINE_MIRROR}/${OS_RELVER}/main/${OS_ARCH}/${APK_TOOLS}"
        echo "download apk-tools : ${APK_TOOLS_URL}"
	(cd "${APK_TOOLS_DIR}"; curl "${APK_TOOLS_URL}" > "${APK_TOOLS}")
	(cd "${APK_TOOLS_DIR}"; tar xzvf "${APK_TOOLS}")
        if [ ! -e "${APK_TOOLS_DIR}/sbin" ] ; then
            echo "apk-tools install failed: ${APK_TOOLS_DIR}"
            exit
        fi
    fi

    SUDO=sudo

    $SUDO "${APK_TOOLS_DIR}/sbin/apk.static" \
        -X "${ALPINE_MIRROR}/${OS_RELVER}/main" \
        -U \
        --allow-untrusted \
        --root "${OS_ROOTDIR}" \
        --initdb add alpine-base alpine-sdk bash libc-dev make autoconf m4 automake \
                     libbsd libbsd-dev fts fts-dev libconfig-dev musl-dev bash diffutils file

    $SUDO /bin/chown -R "$(id -u).$(id -g)" "${OS_ROOTDIR}"
    $SUDO /bin/chmod -R u+rw "${OS_ROOTDIR}"
    /bin/mkdir -p "${OS_ROOTDIR}/proc"
    /bin/mkdir -p "${OS_ROOTDIR}/root"
    /bin/mkdir -p "${OS_ROOTDIR}/etc/apk"
    /bin/echo "$ALPINE_MIRROR/$OS_RELVER/main" >  "${OS_ROOTDIR}/etc/apk/repositories"
}

alpine39_build_fakechroot()
{
    echo "alpine39_build_fakechroot : $1"
    local OS_ARCH="$1"
    local FAKECHROOT_SOURCE_DIR="$2"
    local OS_NAME="alpine"
    local OS_RELVER="v3.9"
    local OS_ROOTDIR="${BUILD_DIR}/${OS_NAME}_${OS_RELVER}_${OS_ARCH}"
    local PROOT=""

    if [ "$OS_ARCH" = "i386" ]; then
        #PROOT="$S_PROOT_DIR/proot-x86 -q qemu-i386"
        #PROOT="$S_PROOT_DIR/proot-x86"
        PROOT="$BUILD_DIR/proot-source-x86/proot-Fedora-30.bin"
    elif [ "$OS_ARCH" = "x86_64" ]; then
        #PROOT="$S_PROOT_DIR/proot-x86_64"
        PROOT="$BUILD_DIR/proot-source-x86_64/proot-Fedora-30.bin"
    else
        echo "unsupported $OS_NAME architecture: $OS_ARCH"
        exit 2
    fi

    if [ -x "${FAKECHROOT_SOURCE_DIR}/libfakechroot-Alpine-3.9.so" ] ; then
        echo "fakechroot binary already compiled : ${FAKECHROOT_SOURCE_DIR}/libfakechroot-Alpine-3.9.so"
        return
    fi

    export PROOT_NO_SECCOMP=1

    # compile fakechroot
    set -xv

    SHELL=/bin/bash CONFIG_SHELL=/bin/bash PATH=/bin:/usr/bin:/sbin:/usr/sbin:/usr/lib \
        $PROOT -r "$OS_ROOTDIR" -b "${FAKECHROOT_SOURCE_DIR}:/fakechroot" -w / -b /dev \
            /bin/bash <<'EOF_alpine39_fakechroot'
# BUILD FAKECHROOT
export SHELL=/bin/bash
export CONFIG_SHELL=/bin/bash
export PATH=/bin:/usr/bin:/sbin:/usr/sbin:/usr/lib
cd /fakechroot
make distclean
bash ./configure
make
cp src/.libs/libfakechroot.so libfakechroot-Alpine-3.9.so
make clean
EOF_alpine39_fakechroot
    set +xv
}


# #############################################################################
# Alpine 3.10.x
# #############################################################################

alpine310_setup()
{
    echo "alpine310_setup : $1"
    local ALPINE_MIRROR="http://dl-5.alpinelinux.org/alpine"
    local APK_TOOLS="apk-tools-static-2.10.8-r0.apk"
    local APK_TOOLS_DIR="${BUILD_DIR}/apk-tools-2.10.8-r0"
    local OS_ARCH="$1"
    local OS_NAME="alpine"
    local OS_RELVER="v3.10"
    local OS_ROOTDIR="${BUILD_DIR}/${OS_NAME}_${OS_RELVER}_${OS_ARCH}"

    if [ -x "${OS_ROOTDIR}/etc/alpine-release" ] ; then
        echo "os already setup : ${OS_ROOTDIR}"
        return
    fi

    if [ -e "${APK_TOOLS_DIR}/sbin" ] ; then
        echo "apk-tools already installed : ${APK_TOOLS_DIR}"
    else
        /bin/rm -f "${APK_TOOLS}"
        mkdir "${APK_TOOLS_DIR}"
        local APK_TOOLS_URL="${ALPINE_MIRROR}/${OS_RELVER}/main/${OS_ARCH}/${APK_TOOLS}"
        echo "download apk-tools : ${APK_TOOLS_URL}"
	(cd "${APK_TOOLS_DIR}"; curl "${APK_TOOLS_URL}" > "${APK_TOOLS}")
	(cd "${APK_TOOLS_DIR}"; tar xzvf "${APK_TOOLS}")
        if [ ! -e "${APK_TOOLS_DIR}/sbin" ] ; then
            echo "apk-tools install failed: ${APK_TOOLS_DIR}"
            exit
        fi
    fi

    SUDO=sudo

    $SUDO "${APK_TOOLS_DIR}/sbin/apk.static" \
        -X "${ALPINE_MIRROR}/${OS_RELVER}/main" \
        -U \
        --allow-untrusted \
        --root "${OS_ROOTDIR}" \
        --initdb add alpine-base alpine-sdk bash libc-dev make autoconf m4 automake \
                     libbsd libbsd-dev fts fts-dev libconfig-dev musl-dev bash diffutils file

    $SUDO /bin/chown -R "$(id -u).$(id -g)" "${OS_ROOTDIR}"
    $SUDO /bin/chmod -R u+rw "${OS_ROOTDIR}"
    /bin/mkdir -p "${OS_ROOTDIR}/proc"
    /bin/mkdir -p "${OS_ROOTDIR}/root"
    /bin/mkdir -p "${OS_ROOTDIR}/etc/apk"
    /bin/echo "$ALPINE_MIRROR/$OS_RELVER/main" >  "${OS_ROOTDIR}/etc/apk/repositories"
}

alpine310_build_fakechroot()
{
    echo "alpine310_build_fakechroot : $1"
    local OS_ARCH="$1"
    local FAKECHROOT_SOURCE_DIR="$2"
    local OS_NAME="alpine"
    local OS_RELVER="v3.10"
    local OS_ROOTDIR="${BUILD_DIR}/${OS_NAME}_${OS_RELVER}_${OS_ARCH}"
    local PROOT=""

    if [ "$OS_ARCH" = "i386" ]; then
        #PROOT="$S_PROOT_DIR/proot-x86 -q qemu-i386"
        #PROOT="$S_PROOT_DIR/proot-x86"
        PROOT="$BUILD_DIR/proot-source-x86/proot-Fedora-30.bin"
    elif [ "$OS_ARCH" = "x86_64" ]; then
        #PROOT="$S_PROOT_DIR/proot-x86_64"
        PROOT="$BUILD_DIR/proot-source-x86_64/proot-Fedora-30.bin"
    else
        echo "unsupported $OS_NAME architecture: $OS_ARCH"
        exit 2
    fi

    if [ -x "${FAKECHROOT_SOURCE_DIR}/libfakechroot-Alpine-3.10.so" ] ; then
        echo "fakechroot binary already compiled : ${FAKECHROOT_SOURCE_DIR}/libfakechroot-Alpine-3.10.so"
        return
    fi

    export PROOT_NO_SECCOMP=1

    # compile fakechroot
    set -xv

    SHELL=/bin/bash CONFIG_SHELL=/bin/bash PATH=/bin:/usr/bin:/sbin:/usr/sbin:/usr/lib \
        $PROOT -r "$OS_ROOTDIR" -b "${FAKECHROOT_SOURCE_DIR}:/fakechroot" -w / -b /dev \
            /bin/bash <<'EOF_alpine310_fakechroot'
# BUILD FAKECHROOT
export SHELL=/bin/bash
export CONFIG_SHELL=/bin/bash
export PATH=/bin:/usr/bin:/sbin:/usr/sbin:/usr/lib
cd /fakechroot
make distclean
bash ./configure
make
cp src/.libs/libfakechroot.so libfakechroot-Alpine-3.10.so
make clean
EOF_alpine310_fakechroot
    set +xv
}


# #############################################################################
# Alpine 3.11.x
# #############################################################################

alpine311_setup()
{
    echo "alpine311_setup : $1"
    local ALPINE_MIRROR="http://dl-5.alpinelinux.org/alpine"
    local APK_TOOLS="apk-tools-static-2.10.8-r0.apk"
    local APK_TOOLS_DIR="${BUILD_DIR}/apk-tools-2.10.8-r0"
    local OS_ARCH="$1"
    local OS_NAME="alpine"
    local OS_RELVER="v3.11"
    local OS_ROOTDIR="${BUILD_DIR}/${OS_NAME}_${OS_RELVER}_${OS_ARCH}"

    if [ -x "${OS_ROOTDIR}/etc/alpine-release" ] ; then
        echo "os already setup : ${OS_ROOTDIR}"
        return
    fi

    if [ -e "${APK_TOOLS_DIR}/sbin" ] ; then
        echo "apk-tools already installed : ${APK_TOOLS_DIR}"
    else
        /bin/rm -f "${APK_TOOLS}"
        mkdir "${APK_TOOLS_DIR}"
        local APK_TOOLS_URL="${ALPINE_MIRROR}/${OS_RELVER}/main/${OS_ARCH}/${APK_TOOLS}"
        echo "download apk-tools : ${APK_TOOLS_URL}"
	(cd "${APK_TOOLS_DIR}"; curl "${APK_TOOLS_URL}" > "${APK_TOOLS}")
	(cd "${APK_TOOLS_DIR}"; tar xzvf "${APK_TOOLS}")
        if [ ! -e "${APK_TOOLS_DIR}/sbin" ] ; then
            echo "apk-tools install failed: ${APK_TOOLS_DIR}"
            exit
        fi
    fi

    SUDO=sudo

    $SUDO "${APK_TOOLS_DIR}/sbin/apk.static" \
        -X "${ALPINE_MIRROR}/${OS_RELVER}/main" \
        -U \
        --allow-untrusted \
        --root "${OS_ROOTDIR}" \
        --initdb add alpine-base alpine-sdk bash libc-dev make autoconf m4 automake \
                     libbsd libbsd-dev fts fts-dev libconfig-dev musl-dev bash diffutils file

    $SUDO /bin/chown -R "$(id -u).$(id -g)" "${OS_ROOTDIR}"
    $SUDO /bin/chmod -R u+rw "${OS_ROOTDIR}"
    /bin/mkdir -p "${OS_ROOTDIR}/proc"
    /bin/mkdir -p "${OS_ROOTDIR}/root"
    /bin/mkdir -p "${OS_ROOTDIR}/etc/apk"
    /bin/echo "$ALPINE_MIRROR/$OS_RELVER/main" >  "${OS_ROOTDIR}/etc/apk/repositories"
}

alpine311_build_fakechroot()
{
    echo "alpine311_build_fakechroot : $1"
    local OS_ARCH="$1"
    local FAKECHROOT_SOURCE_DIR="$2"
    local OS_NAME="alpine"
    local OS_RELVER="v3.11"
    local OS_ROOTDIR="${BUILD_DIR}/${OS_NAME}_${OS_RELVER}_${OS_ARCH}"
    local PROOT=""

    if [ "$OS_ARCH" = "i386" ]; then
        #PROOT="$S_PROOT_DIR/proot-x86 -q qemu-i386"
        #PROOT="$S_PROOT_DIR/proot-x86"
        PROOT="$BUILD_DIR/proot-source-x86/proot-Fedora-30.bin"
    elif [ "$OS_ARCH" = "x86_64" ]; then
        #PROOT="$S_PROOT_DIR/proot-x86_64"
        PROOT="$BUILD_DIR/proot-source-x86_64/proot-Fedora-30.bin"
    else
        echo "unsupported $OS_NAME architecture: $OS_ARCH"
        exit 2
    fi

    if [ -x "${FAKECHROOT_SOURCE_DIR}/libfakechroot-Alpine-3.11.so" ] ; then
        echo "fakechroot binary already compiled : ${FAKECHROOT_SOURCE_DIR}/libfakechroot-Alpine-3.11.so"
        return
    fi

    export PROOT_NO_SECCOMP=1

    # compile fakechroot
    set -xv

    SHELL=/bin/bash CONFIG_SHELL=/bin/bash PATH=/bin:/usr/bin:/sbin:/usr/sbin:/usr/lib \
        $PROOT -r "$OS_ROOTDIR" -b "${FAKECHROOT_SOURCE_DIR}:/fakechroot" -w / -b /dev \
            /bin/bash <<'EOF_alpine311_fakechroot'
# BUILD FAKECHROOT
export SHELL=/bin/bash
export CONFIG_SHELL=/bin/bash
export PATH=/bin:/usr/bin:/sbin:/usr/sbin:/usr/lib
cd /fakechroot
make distclean
bash ./configure
make
cp src/.libs/libfakechroot.so libfakechroot-Alpine-3.11.so
make clean
EOF_alpine311_fakechroot
    set +xv
}


# #############################################################################
# Alpine 3.12.x
# #############################################################################

alpine312_setup()
{
    echo "alpine312_setup : $1"
    local ALPINE_MIRROR="http://dl-5.alpinelinux.org/alpine"
    local APK_TOOLS="apk-tools-static-2.10.8-r0.apk"
    local APK_TOOLS_DIR="${BUILD_DIR}/apk-tools-2.10.8-r0"
    local OS_ARCH="$1"
    local OS_NAME="alpine"
    local OS_RELVER="v3.12"
    local OS_ROOTDIR="${BUILD_DIR}/${OS_NAME}_${OS_RELVER}_${OS_ARCH}"

    if [ -x "${OS_ROOTDIR}/etc/alpine-release" ] ; then
        echo "os already setup : ${OS_ROOTDIR}"
        return
    fi

    if [ -e "${APK_TOOLS_DIR}/sbin" ] ; then
        echo "apk-tools already installed : ${APK_TOOLS_DIR}"
    else
        /bin/rm -f "${APK_TOOLS}"
        mkdir "${APK_TOOLS_DIR}"
        local APK_TOOLS_URL="${ALPINE_MIRROR}/${OS_RELVER}/main/${OS_ARCH}/${APK_TOOLS}"
        echo "download apk-tools : ${APK_TOOLS_URL}"
	(cd "${APK_TOOLS_DIR}"; curl "${APK_TOOLS_URL}" > "${APK_TOOLS}")
	(cd "${APK_TOOLS_DIR}"; tar xzvf "${APK_TOOLS}")
        if [ ! -e "${APK_TOOLS_DIR}/sbin" ] ; then
            echo "apk-tools install failed: ${APK_TOOLS_DIR}"
            exit
        fi
    fi

    SUDO=sudo

    $SUDO "${APK_TOOLS_DIR}/sbin/apk.static" \
        -X "${ALPINE_MIRROR}/${OS_RELVER}/main" \
        -U \
        --allow-untrusted \
        --root "${OS_ROOTDIR}" \
        --initdb add alpine-base alpine-sdk bash libc-dev make autoconf m4 automake \
                     libbsd libbsd-dev fts fts-dev libconfig-dev musl-dev bash diffutils \
		     file

    $SUDO /bin/chown -R "$(id -u).$(id -g)" "${OS_ROOTDIR}"
    $SUDO /bin/chmod -R u+rw "${OS_ROOTDIR}"
    /bin/mkdir -p "${OS_ROOTDIR}/proc"
    /bin/mkdir -p "${OS_ROOTDIR}/root"
    /bin/mkdir -p "${OS_ROOTDIR}/etc/apk"
    /bin/echo "$ALPINE_MIRROR/$OS_RELVER/main" >  "${OS_ROOTDIR}/etc/apk/repositories"
}

alpine312_build_fakechroot()
{
    echo "alpine312_build_fakechroot : $1"
    local OS_ARCH="$1"
    local FAKECHROOT_SOURCE_DIR="$2"
    local OS_NAME="alpine"
    local OS_RELVER="v3.12"
    local OS_ROOTDIR="${BUILD_DIR}/${OS_NAME}_${OS_RELVER}_${OS_ARCH}"
    local PROOT=""

    if [ "$OS_ARCH" = "i386" ]; then
        #PROOT="$S_PROOT_DIR/proot-x86 -q qemu-i386"
        #PROOT="$S_PROOT_DIR/proot-x86"
        PROOT="$BUILD_DIR/proot-source-x86/proot-Fedora-30.bin"
    elif [ "$OS_ARCH" = "x86_64" ]; then
        #PROOT="$S_PROOT_DIR/proot-x86_64"
        PROOT="$BUILD_DIR/proot-source-x86_64/proot-Fedora-30.bin"
    else
        echo "unsupported $OS_NAME architecture: $OS_ARCH"
        exit 2
    fi

    if [ -x "${FAKECHROOT_SOURCE_DIR}/libfakechroot-Alpine-3.12.so" ] ; then
        echo "fakechroot binary already compiled : ${FAKECHROOT_SOURCE_DIR}/libfakechroot-Alpine-3.12.so"
        return
    fi

    export PROOT_NO_SECCOMP=1

    # compile fakechroot
    set -xv

    SHELL=/bin/bash CONFIG_SHELL=/bin/bash PATH=/bin:/usr/bin:/sbin:/usr/sbin:/usr/lib \
        $PROOT -r "$OS_ROOTDIR" -b "${FAKECHROOT_SOURCE_DIR}:/fakechroot" -w / -b /dev \
            /bin/bash <<'EOF_alpine312_fakechroot'
# BUILD FAKECHROOT
export SHELL=/bin/bash
export CONFIG_SHELL=/bin/bash
export PATH=/bin:/usr/bin:/sbin:/usr/sbin:/usr/lib
cd /fakechroot
make distclean
bash ./configure
make
cp src/.libs/libfakechroot.so libfakechroot-Alpine-3.12.so
make clean
EOF_alpine312_fakechroot
    set +xv
}


# #############################################################################
# Alpine 3.13.x
# #############################################################################

alpine313_setup()
{
    echo "alpine313_setup : $1"
    local ALPINE_MIRROR="http://dl-5.alpinelinux.org/alpine"
    local APK_TOOLS="apk-tools-static-2.12.7-r0.apk"
    local APK_TOOLS_DIR="${BUILD_DIR}/apk-tools-2.12.7-r0"
    local OS_ARCH="$1"
    local OS_NAME="alpine"
    local OS_RELVER="v3.13"
    local OS_ROOTDIR="${BUILD_DIR}/${OS_NAME}_${OS_RELVER}_${OS_ARCH}"

    if [ -x "${OS_ROOTDIR}/etc/alpine-release" ] ; then
        echo "os already setup : ${OS_ROOTDIR}"
        return
    fi

    if [ -e "${APK_TOOLS_DIR}/sbin" ] ; then
        echo "apk-tools already installed : ${APK_TOOLS_DIR}"
    else
        /bin/rm -f "${APK_TOOLS}"
        mkdir "${APK_TOOLS_DIR}"
        local APK_TOOLS_URL="${ALPINE_MIRROR}/${OS_RELVER}/main/${OS_ARCH}/${APK_TOOLS}"
        echo "download apk-tools : ${APK_TOOLS_URL}"
	(cd "${APK_TOOLS_DIR}"; curl "${APK_TOOLS_URL}" > "${APK_TOOLS}")
	(cd "${APK_TOOLS_DIR}"; tar xzvf "${APK_TOOLS}")
        if [ ! -e "${APK_TOOLS_DIR}/sbin" ] ; then
            echo "apk-tools install failed: ${APK_TOOLS_DIR}"
            exit
        fi
    fi

    SUDO=sudo

    $SUDO "${APK_TOOLS_DIR}/sbin/apk.static" \
        -X "${ALPINE_MIRROR}/${OS_RELVER}/main" \
        -U \
        --allow-untrusted \
        --root "${OS_ROOTDIR}" \
        --initdb add alpine-base alpine-sdk bash libc-dev make autoconf m4 automake \
                     libbsd libbsd-dev fts fts-dev libconfig-dev musl-dev bash diffutils \
		     file

    $SUDO /bin/chown -R "$(id -u).$(id -g)" "${OS_ROOTDIR}"
    $SUDO /bin/chmod -R u+rw "${OS_ROOTDIR}"
    /bin/mkdir -p "${OS_ROOTDIR}/proc"
    /bin/mkdir -p "${OS_ROOTDIR}/root"
    /bin/mkdir -p "${OS_ROOTDIR}/etc/apk"
    /bin/echo "$ALPINE_MIRROR/$OS_RELVER/main" >  "${OS_ROOTDIR}/etc/apk/repositories"
}

alpine313_build_fakechroot()
{
    echo "alpine313_build_fakechroot : $1"
    local OS_ARCH="$1"
    local FAKECHROOT_SOURCE_DIR="$2"
    local OS_NAME="alpine"
    local OS_RELVER="v3.13"
    local OS_ROOTDIR="${BUILD_DIR}/${OS_NAME}_${OS_RELVER}_${OS_ARCH}"
    local PROOT=""

    if [ "$OS_ARCH" = "i386" ]; then
        #PROOT="$S_PROOT_DIR/proot-x86 -q qemu-i386"
        #PROOT="$S_PROOT_DIR/proot-x86"
        PROOT="$BUILD_DIR/proot-source-x86/proot-Fedora-30.bin"
    elif [ "$OS_ARCH" = "x86_64" ]; then
        #PROOT="$S_PROOT_DIR/proot-x86_64"
        PROOT="$BUILD_DIR/proot-source-x86_64/proot-Fedora-30.bin"
    else
        echo "unsupported $OS_NAME architecture: $OS_ARCH"
        exit 2
    fi

    if [ -x "${FAKECHROOT_SOURCE_DIR}/libfakechroot-Alpine-3.13.so" ] ; then
        echo "fakechroot binary already compiled : ${FAKECHROOT_SOURCE_DIR}/libfakechroot-Alpine-3.13.so"
        return
    fi

    export PROOT_NO_SECCOMP=1

    # compile fakechroot
    set -xv

    SHELL=/bin/bash CONFIG_SHELL=/bin/bash PATH=/bin:/usr/bin:/sbin:/usr/sbin:/usr/lib \
        $PROOT -r "$OS_ROOTDIR" -b "${FAKECHROOT_SOURCE_DIR}:/fakechroot" -w / -b /dev \
            /bin/bash <<'EOF_alpine313_fakechroot'
# BUILD FAKECHROOT
export SHELL=/bin/bash
export CONFIG_SHELL=/bin/bash
export PATH=/bin:/usr/bin:/sbin:/usr/sbin:/usr/lib
cd /fakechroot
make distclean
bash ./configure
make
cp src/.libs/libfakechroot.so libfakechroot-Alpine-3.13.so
make clean
EOF_alpine313_fakechroot
    set +xv
}


# #############################################################################
# Alpine 3.14.x
# #############################################################################

alpine314_setup()
{
    echo "alpine314_setup : $1"
    local ALPINE_MIRROR="http://dl-5.alpinelinux.org/alpine"
    local APK_TOOLS="apk-tools-static-2.12.7-r0.apk"
    local APK_TOOLS_DIR="${BUILD_DIR}/apk-tools-2.12.7-r0"
    local OS_ARCH="$1"
    local OS_NAME="alpine"
    local OS_RELVER="v3.14"
    local OS_ROOTDIR="${BUILD_DIR}/${OS_NAME}_${OS_RELVER}_${OS_ARCH}"

    if [ -x "${OS_ROOTDIR}/etc/alpine-release" ] ; then
        echo "os already setup : ${OS_ROOTDIR}"
        return
    fi

    if [ -e "${APK_TOOLS_DIR}/sbin" ] ; then
        echo "apk-tools already installed : ${APK_TOOLS_DIR}"
    else
        /bin/rm -f "${APK_TOOLS}"
        mkdir "${APK_TOOLS_DIR}"
        local APK_TOOLS_URL="${ALPINE_MIRROR}/${OS_RELVER}/main/${OS_ARCH}/${APK_TOOLS}"
        echo "download apk-tools : ${APK_TOOLS_URL}"
	(cd "${APK_TOOLS_DIR}"; curl "${APK_TOOLS_URL}" > "${APK_TOOLS}")
	(cd "${APK_TOOLS_DIR}"; tar xzvf "${APK_TOOLS}")
        if [ ! -e "${APK_TOOLS_DIR}/sbin" ] ; then
            echo "apk-tools install failed: ${APK_TOOLS_DIR}"
            exit
        fi
    fi

    SUDO=sudo

    $SUDO "${APK_TOOLS_DIR}/sbin/apk.static" \
        -X "${ALPINE_MIRROR}/${OS_RELVER}/main" \
        -U \
        --allow-untrusted \
        --root "${OS_ROOTDIR}" \
        --initdb add alpine-base alpine-sdk bash libc-dev make autoconf m4 automake \
                     libbsd libbsd-dev fts fts-dev libconfig-dev musl-dev bash diffutils \
		     file

    $SUDO /bin/chown -R "$(id -u).$(id -g)" "${OS_ROOTDIR}"
    $SUDO /bin/chmod -R u+rw "${OS_ROOTDIR}"
    /bin/mkdir -p "${OS_ROOTDIR}/proc"
    /bin/mkdir -p "${OS_ROOTDIR}/root"
    /bin/mkdir -p "${OS_ROOTDIR}/etc/apk"
    /bin/echo "$ALPINE_MIRROR/$OS_RELVER/main" >  "${OS_ROOTDIR}/etc/apk/repositories"
}

alpine314_build_fakechroot()
{
    echo "alpine314_build_fakechroot : $1"
    local OS_ARCH="$1"
    local FAKECHROOT_SOURCE_DIR="$2"
    local OS_NAME="alpine"
    local OS_RELVER="v3.14"
    local OS_ROOTDIR="${BUILD_DIR}/${OS_NAME}_${OS_RELVER}_${OS_ARCH}"
    local PROOT=""

    if [ "$OS_ARCH" = "i386" ]; then
        #PROOT="$S_PROOT_DIR/proot-x86 -q qemu-i386"
        #PROOT="$S_PROOT_DIR/proot-x86"
	PROOT="$BUILD_DIR/proot-source-x86/proot-Fedora-30.bin"
    elif [ "$OS_ARCH" = "x86_64" ]; then
        #PROOT="$S_PROOT_DIR/proot-x86_64"
	PROOT="$BUILD_DIR/proot-source-x86_64/proot-Fedora-30.bin"
    else
        echo "unsupported $OS_NAME architecture: $OS_ARCH"
        exit 2
    fi

    if [ -x "${FAKECHROOT_SOURCE_DIR}/libfakechroot-Alpine-3.14.so" ] ; then
        echo "fakechroot binary already compiled : ${FAKECHROOT_SOURCE_DIR}/libfakechroot-Alpine-3.14.so"
        return
    fi

    export PROOT_NO_SECCOMP=1

    # compile fakechroot
    set -xv

    SHELL=/bin/bash CONFIG_SHELL=/bin/bash PATH=/bin:/usr/bin:/sbin:/usr/sbin:/usr/lib \
        $PROOT -r "$OS_ROOTDIR" -b "${FAKECHROOT_SOURCE_DIR}:/fakechroot" -w / -b /dev \
            /bin/bash <<'EOF_alpine314_fakechroot'
# BUILD FAKECHROOT
export SHELL=/bin/bash
export CONFIG_SHELL=/bin/bash
export PATH=/bin:/usr/bin:/sbin:/usr/sbin:/usr/lib
cd /fakechroot
make distclean
bash ./configure
make
cp src/.libs/libfakechroot.so libfakechroot-Alpine-3.14.so
make clean
EOF_alpine314_fakechroot
    set +xv
}


# #############################################################################
# Alpine 3.15.x
# #############################################################################

alpine315_setup()
{
    echo "alpine315_setup : $1"
    local ALPINE_MIRROR="http://dl-5.alpinelinux.org/alpine"
    local APK_TOOLS="apk-tools-static-2.12.7-r3.apk"
    local APK_TOOLS_DIR="${BUILD_DIR}/apk-tools-2.12.7-r3"
    local OS_ARCH="$1"
    local OS_NAME="alpine"
    local OS_RELVER="v3.15"
    local OS_ROOTDIR="${BUILD_DIR}/${OS_NAME}_${OS_RELVER}_${OS_ARCH}"

    if [ -x "${OS_ROOTDIR}/etc/alpine-release" ] ; then
        echo "os already setup : ${OS_ROOTDIR}"
        return
    fi

    if [ -e "${APK_TOOLS_DIR}/sbin" ] ; then
        echo "apk-tools already installed : ${APK_TOOLS_DIR}"
    else
        /bin/rm -f "${APK_TOOLS}"
        mkdir "${APK_TOOLS_DIR}"
        local APK_TOOLS_URL="${ALPINE_MIRROR}/${OS_RELVER}/main/${OS_ARCH}/${APK_TOOLS}"
        echo "download apk-tools : ${APK_TOOLS_URL}"
	(cd "${APK_TOOLS_DIR}"; curl "${APK_TOOLS_URL}" > "${APK_TOOLS}")
	(cd "${APK_TOOLS_DIR}"; tar xzvf "${APK_TOOLS}")
        if [ ! -e "${APK_TOOLS_DIR}/sbin" ] ; then
            echo "apk-tools install failed: ${APK_TOOLS_DIR}"
            exit
        fi
    fi

    SUDO=sudo

    $SUDO "${APK_TOOLS_DIR}/sbin/apk.static" \
        -X "${ALPINE_MIRROR}/${OS_RELVER}/main" \
        -U \
        --allow-untrusted \
        --root "${OS_ROOTDIR}" \
        --initdb add alpine-base alpine-sdk bash libc-dev make autoconf m4 automake \
                     libbsd libbsd-dev fts fts-dev libconfig-dev musl-dev bash diffutils \
		     file

    $SUDO /bin/chown -R "$(id -u).$(id -g)" "${OS_ROOTDIR}"
    $SUDO /bin/chmod -R u+rw "${OS_ROOTDIR}"
    /bin/mkdir -p "${OS_ROOTDIR}/proc"
    /bin/mkdir -p "${OS_ROOTDIR}/root"
    /bin/mkdir -p "${OS_ROOTDIR}/etc/apk"
    /bin/echo "$ALPINE_MIRROR/$OS_RELVER/main" >  "${OS_ROOTDIR}/etc/apk/repositories"
}

alpine315_build_fakechroot()
{
    echo "alpine315_build_fakechroot : $1"
    local OS_ARCH="$1"
    local FAKECHROOT_SOURCE_DIR="$2"
    local OS_NAME="alpine"
    local OS_RELVER="v3.15"
    local OS_ROOTDIR="${BUILD_DIR}/${OS_NAME}_${OS_RELVER}_${OS_ARCH}"
    local PROOT=""

    if [ "$OS_ARCH" = "i386" ]; then
        #PROOT="$S_PROOT_DIR/proot-x86 -q qemu-i386"
        #PROOT="$S_PROOT_DIR/proot-x86"
	PROOT="$BUILD_DIR/proot-source-x86/proot-Fedora-30.bin"
    elif [ "$OS_ARCH" = "x86_64" ]; then
        #PROOT="$S_PROOT_DIR/proot-x86_64"
	PROOT="$BUILD_DIR/proot-source-x86_64/proot-Fedora-30.bin"
    else
        echo "unsupported $OS_NAME architecture: $OS_ARCH"
        exit 2
    fi

    if [ -x "${FAKECHROOT_SOURCE_DIR}/libfakechroot-Alpine-3.15.so" ] ; then
        echo "fakechroot binary already compiled : ${FAKECHROOT_SOURCE_DIR}/libfakechroot-Alpine-3.15.so"
        return
    fi

    export PROOT_NO_SECCOMP=1

    # compile fakechroot
    set -xv

    SHELL=/bin/bash CONFIG_SHELL=/bin/bash PATH=/bin:/usr/bin:/sbin:/usr/sbin:/usr/lib \
        $PROOT -r "$OS_ROOTDIR" -b "${FAKECHROOT_SOURCE_DIR}:/fakechroot" -w / -b /dev \
            /bin/bash <<'EOF_alpine315_fakechroot'
# BUILD FAKECHROOT
export SHELL=/bin/bash
export CONFIG_SHELL=/bin/bash
export PATH=/bin:/usr/bin:/sbin:/usr/sbin:/usr/lib
cd /fakechroot
make distclean
bash ./configure
make
cp src/.libs/libfakechroot.so libfakechroot-Alpine-3.15.so
make clean
EOF_alpine315_fakechroot
    set +xv
}


# #############################################################################
# Alpine 3.16.x
# #############################################################################

alpine316_setup()
{
    echo "alpine316_setup : $1"
    local ALPINE_MIRROR="http://dl-5.alpinelinux.org/alpine"
    local APK_TOOLS="apk-tools-static-2.12.9-r3.apk"
    local APK_TOOLS_DIR="${BUILD_DIR}/apk-tools-2.12.9-r3"
    local OS_ARCH="$1"
    local OS_NAME="alpine"
    local OS_RELVER="v3.16"
    local OS_ROOTDIR="${BUILD_DIR}/${OS_NAME}_${OS_RELVER}_${OS_ARCH}"

    if [ -x "${OS_ROOTDIR}/etc/alpine-release" ] ; then
        echo "os already setup : ${OS_ROOTDIR}"
        return
    fi

    if [ -e "${APK_TOOLS_DIR}/sbin" ] ; then
        echo "apk-tools already installed : ${APK_TOOLS_DIR}"
    else
        /bin/rm -f "${APK_TOOLS}"
        mkdir "${APK_TOOLS_DIR}"
        local APK_TOOLS_URL="${ALPINE_MIRROR}/${OS_RELVER}/main/${OS_ARCH}/${APK_TOOLS}"
        echo "download apk-tools : ${APK_TOOLS_URL}"
	(cd "${APK_TOOLS_DIR}"; curl "${APK_TOOLS_URL}" > "${APK_TOOLS}")
	(cd "${APK_TOOLS_DIR}"; tar xzvf "${APK_TOOLS}")
        if [ ! -e "${APK_TOOLS_DIR}/sbin" ] ; then
            echo "apk-tools install failed: ${APK_TOOLS_DIR}"
            exit
        fi
    fi

    SUDO=sudo

    $SUDO "${APK_TOOLS_DIR}/sbin/apk.static" \
        -X "${ALPINE_MIRROR}/${OS_RELVER}/main" \
        -U \
        --allow-untrusted \
        --root "${OS_ROOTDIR}" \
        --initdb add alpine-base alpine-sdk bash libc-dev make autoconf m4 automake \
                     libbsd libbsd-dev fts fts-dev libconfig-dev musl-dev bash diffutils \
		     file

    $SUDO /bin/chown -R "$(id -u).$(id -g)" "${OS_ROOTDIR}"
    $SUDO /bin/chmod -R u+rw "${OS_ROOTDIR}"
    /bin/mkdir -p "${OS_ROOTDIR}/proc"
    /bin/mkdir -p "${OS_ROOTDIR}/root"
    /bin/mkdir -p "${OS_ROOTDIR}/etc/apk"
    /bin/echo "$ALPINE_MIRROR/$OS_RELVER/main" >  "${OS_ROOTDIR}/etc/apk/repositories"
}

alpine316_build_fakechroot()
{
    echo "alpine316_build_fakechroot : $1"
    local OS_ARCH="$1"
    local FAKECHROOT_SOURCE_DIR="$2"
    local OS_NAME="alpine"
    local OS_RELVER="v3.16"
    local OS_ROOTDIR="${BUILD_DIR}/${OS_NAME}_${OS_RELVER}_${OS_ARCH}"
    local PROOT=""

    if [ "$OS_ARCH" = "i386" ]; then
        #PROOT="$S_PROOT_DIR/proot-x86 -q qemu-i386"
        #PROOT="$S_PROOT_DIR/proot-x86"
	PROOT="$BUILD_DIR/proot-source-x86/proot-Fedora-30.bin"
    elif [ "$OS_ARCH" = "x86_64" ]; then
        #PROOT="$S_PROOT_DIR/proot-x86_64"
	PROOT="$BUILD_DIR/proot-source-x86_64/proot-Fedora-30.bin"
    else
        echo "unsupported $OS_NAME architecture: $OS_ARCH"
        exit 2
    fi

    if [ -x "${FAKECHROOT_SOURCE_DIR}/libfakechroot-Alpine-3.16.so" ] ; then
        echo "fakechroot binary already compiled : ${FAKECHROOT_SOURCE_DIR}/libfakechroot-Alpine-3.16.so"
        return
    fi

    export PROOT_NO_SECCOMP=1

    # compile fakechroot
    set -xv

    SHELL=/bin/bash CONFIG_SHELL=/bin/bash PATH=/bin:/usr/bin:/sbin:/usr/sbin:/usr/lib \
        $PROOT -r "$OS_ROOTDIR" -b "${FAKECHROOT_SOURCE_DIR}:/fakechroot" -w / -b /dev \
            /bin/bash <<'EOF_alpine316_fakechroot'
# BUILD FAKECHROOT
export SHELL=/bin/bash
export CONFIG_SHELL=/bin/bash
export PATH=/bin:/usr/bin:/sbin:/usr/sbin:/usr/lib
cd /fakechroot
make distclean
bash ./configure
make
cp src/.libs/libfakechroot.so libfakechroot-Alpine-3.16.so
make clean
EOF_alpine316_fakechroot
    set +xv
}


# #############################################################################
# Alpine 3.17.x
# #############################################################################

alpine317_setup()
{
    echo "alpine317_setup : $1"
    local ALPINE_MIRROR="http://dl-5.alpinelinux.org/alpine"
    local APK_TOOLS="apk-tools-static-2.12.9-r3.apk"
    local APK_TOOLS_DIR="${BUILD_DIR}/apk-tools-2.12.9-r3"
    local OS_ARCH="$1"
    local OS_NAME="alpine"
    local OS_RELVER="v3.17"
    local OS_ROOTDIR="${BUILD_DIR}/${OS_NAME}_${OS_RELVER}_${OS_ARCH}"

    if [ -x "${OS_ROOTDIR}/etc/alpine-release" ] ; then
        echo "os already setup : ${OS_ROOTDIR}"
        return
    fi

    if [ -e "${APK_TOOLS_DIR}/sbin" ] ; then
        echo "apk-tools already installed : ${APK_TOOLS_DIR}"
    else
        /bin/rm -f "${APK_TOOLS}"
        mkdir "${APK_TOOLS_DIR}"
        local APK_TOOLS_URL="${ALPINE_MIRROR}/${OS_RELVER}/main/${OS_ARCH}/${APK_TOOLS}"
        echo "download apk-tools : ${APK_TOOLS_URL}"
	(cd "${APK_TOOLS_DIR}"; curl "${APK_TOOLS_URL}" > "${APK_TOOLS}")
	(cd "${APK_TOOLS_DIR}"; tar xzvf "${APK_TOOLS}")
        if [ ! -e "${APK_TOOLS_DIR}/sbin" ] ; then
            echo "apk-tools install failed: ${APK_TOOLS_DIR}"
            exit
        fi
    fi

    SUDO=sudo

    set -x
    $SUDO "${APK_TOOLS_DIR}/sbin/apk.static" \
        -X "${ALPINE_MIRROR}/${OS_RELVER}/main" \
        -U \
        --allow-untrusted \
        --root "${OS_ROOTDIR}" \
        --initdb add alpine-base alpine-sdk bash libc-dev make autoconf m4 automake \
                     libbsd libbsd-dev musl-fts musl-fts-dev libconfig-dev musl-dev bash \
		     diffutils file
    set +x

    $SUDO /bin/chown -R "$(id -u).$(id -g)" "${OS_ROOTDIR}"
    $SUDO /bin/chmod -R u+rw "${OS_ROOTDIR}"
    /bin/mkdir -p "${OS_ROOTDIR}/proc"
    /bin/mkdir -p "${OS_ROOTDIR}/root"
    /bin/mkdir -p "${OS_ROOTDIR}/etc/apk"
    /bin/echo "$ALPINE_MIRROR/$OS_RELVER/main" >  "${OS_ROOTDIR}/etc/apk/repositories"
}

alpine317_build_fakechroot()
{
    echo "alpine317_build_fakechroot : $1"
    local OS_ARCH="$1"
    local FAKECHROOT_SOURCE_DIR="$2"
    local OS_NAME="alpine"
    local OS_RELVER="v3.17"
    local OS_ROOTDIR="${BUILD_DIR}/${OS_NAME}_${OS_RELVER}_${OS_ARCH}"
    local PROOT=""

    if [ "$OS_ARCH" = "i386" ]; then
        #PROOT="$S_PROOT_DIR/proot-x86 -q qemu-i386"
        #PROOT="$S_PROOT_DIR/proot-x86"
	PROOT="$BUILD_DIR/proot-source-x86/proot-Fedora-30.bin"
    elif [ "$OS_ARCH" = "x86_64" ]; then
        #PROOT="$S_PROOT_DIR/proot-x86_64"
	PROOT="$BUILD_DIR/proot-source-x86_64/proot-Fedora-30.bin"
    else
        echo "unsupported $OS_NAME architecture: $OS_ARCH"
        exit 2
    fi

    if [ -x "${FAKECHROOT_SOURCE_DIR}/libfakechroot-Alpine-3.17.so" ] ; then
        echo "fakechroot binary already compiled : ${FAKECHROOT_SOURCE_DIR}/libfakechroot-Alpine-3.17.so"
        return
    fi

    export PROOT_NO_SECCOMP=1

    # compile fakechroot
    set -xv

    SHELL=/bin/bash CONFIG_SHELL=/bin/bash PATH=/bin:/usr/bin:/sbin:/usr/sbin:/usr/lib \
        $PROOT -r "$OS_ROOTDIR" -b "${FAKECHROOT_SOURCE_DIR}:/fakechroot" -w / -b /dev \
            /bin/bash <<'EOF_alpine317_fakechroot'
# BUILD FAKECHROOT
export SHELL=/bin/bash
export CONFIG_SHELL=/bin/bash
export PATH=/bin:/usr/bin:/sbin:/usr/sbin:/usr/lib
cd /fakechroot
make distclean
bash ./configure
make
cp src/.libs/libfakechroot.so libfakechroot-Alpine-3.17.so
make clean
EOF_alpine317_fakechroot
    set +xv
}


# #############################################################################
# Alpine 3.18.x
# #############################################################################

alpine318_setup()
{
    echo "alpine318_setup : $1"
    local ALPINE_MIRROR="http://dl-5.alpinelinux.org/alpine"
    local APK_TOOLS="apk-tools-static-2.12.9-r3.apk"
    local APK_TOOLS_DIR="${BUILD_DIR}/apk-tools-2.12.9-r3"
    local OS_ARCH="$1"
    local OS_NAME="alpine"
    local OS_RELVER="v3.18"
    local OS_ROOTDIR="${BUILD_DIR}/${OS_NAME}_${OS_RELVER}_${OS_ARCH}"

    if [ -x "${OS_ROOTDIR}/etc/alpine-release" ] ; then
        echo "os already setup : ${OS_ROOTDIR}"
        return
    fi

    if [ -e "${APK_TOOLS_DIR}/sbin" ] ; then
        echo "apk-tools already installed : ${APK_TOOLS_DIR}"
    else
        /bin/rm -f "${APK_TOOLS}"
        mkdir "${APK_TOOLS_DIR}"
        local APK_TOOLS_URL="${ALPINE_MIRROR}/${OS_RELVER}/main/${OS_ARCH}/${APK_TOOLS}"
        echo "download apk-tools : ${APK_TOOLS_URL}"
	(cd "${APK_TOOLS_DIR}"; curl "${APK_TOOLS_URL}" > "${APK_TOOLS}")
	(cd "${APK_TOOLS_DIR}"; tar xzvf "${APK_TOOLS}")
        if [ ! -e "${APK_TOOLS_DIR}/sbin" ] ; then
            echo "apk-tools install failed: ${APK_TOOLS_DIR}"
            exit
        fi
    fi

    SUDO=sudo

    set -x
    $SUDO "${APK_TOOLS_DIR}/sbin/apk.static" \
        -X "${ALPINE_MIRROR}/${OS_RELVER}/main" \
        -U \
        --allow-untrusted \
        --root "${OS_ROOTDIR}" \
        --initdb add alpine-base alpine-sdk bash libc-dev make autoconf m4 automake \
                     libbsd libbsd-dev musl-fts musl-fts-dev libconfig-dev musl-dev bash \
		     diffutils file
    set +x

    $SUDO /bin/chown -R "$(id -u).$(id -g)" "${OS_ROOTDIR}"
    $SUDO /bin/chmod -R u+rw "${OS_ROOTDIR}"
    /bin/mkdir -p "${OS_ROOTDIR}/proc"
    /bin/mkdir -p "${OS_ROOTDIR}/root"
    /bin/mkdir -p "${OS_ROOTDIR}/etc/apk"
    /bin/echo "$ALPINE_MIRROR/$OS_RELVER/main" >  "${OS_ROOTDIR}/etc/apk/repositories"
}

alpine318_build_fakechroot()
{
    echo "alpine318_build_fakechroot : $1"
    local OS_ARCH="$1"
    local FAKECHROOT_SOURCE_DIR="$2"
    local OS_NAME="alpine"
    local OS_RELVER="v3.18"
    local OS_ROOTDIR="${BUILD_DIR}/${OS_NAME}_${OS_RELVER}_${OS_ARCH}"
    local PROOT=""

    if [ "$OS_ARCH" = "i386" ]; then
        #PROOT="$S_PROOT_DIR/proot-x86 -q qemu-i386"
        #PROOT="$S_PROOT_DIR/proot-x86"
	PROOT="$BUILD_DIR/proot-source-x86/proot-Fedora-30.bin"
    elif [ "$OS_ARCH" = "x86_64" ]; then
        #PROOT="$S_PROOT_DIR/proot-x86_64"
	PROOT="$BUILD_DIR/proot-source-x86_64/proot-Fedora-30.bin"
    else
        echo "unsupported $OS_NAME architecture: $OS_ARCH"
        exit 2
    fi

    if [ -x "${FAKECHROOT_SOURCE_DIR}/libfakechroot-Alpine-3.18.so" ] ; then
        echo "fakechroot binary already compiled : ${FAKECHROOT_SOURCE_DIR}/libfakechroot-Alpine-3.18.so"
        return
    fi

    export PROOT_NO_SECCOMP=1

    # compile fakechroot
    set -xv

    SHELL=/bin/bash CONFIG_SHELL=/bin/bash PATH=/bin:/usr/bin:/sbin:/usr/sbin:/usr/lib \
        $PROOT -r "$OS_ROOTDIR" -b "${FAKECHROOT_SOURCE_DIR}:/fakechroot" -w / -b /dev \
            /bin/bash <<'EOF_alpine318_fakechroot'
# BUILD FAKECHROOT
export SHELL=/bin/bash
export CONFIG_SHELL=/bin/bash
export PATH=/bin:/usr/bin:/sbin:/usr/sbin:/usr/lib
cd /fakechroot
make distclean
bash ./configure
make
cp src/.libs/libfakechroot.so libfakechroot-Alpine-3.18.so
make clean
EOF_alpine318_fakechroot
    set +xv
}


# #############################################################################
# Nix using chroot
# #############################################################################

nix_setup()
{
    echo "nix_setup : $1"
    local OS_ARCH="$1"
    local OS_NAME="fedora"
    local OS_RELVER="36"
    local OS_ROOTDIR="${BUILD_DIR}/${OS_NAME}_${OS_RELVER}_${OS_ARCH}"

    if [ -x "${OS_ROOTDIR}/nix" ] ; then
        echo "nix already setup : ${OS_ROOTDIR}/nix"
        return
    fi

    SUDO=/bin/sudo

    /bin/mkdir -p "${OS_ROOTDIR}/nix"
    /bin/mkdir -p "${OS_ROOTDIR}/crun"
    #/bin/mkdir -p "${OS_ROOTDIR}/etc"

    curl -L https://nixos.org/nix/install > "$OS_ROOTDIR/nix_installer.sh"

    /bin/rm -f "${OS_ROOTDIR}/etc/resolv.conf"
    /bin/cp -f /etc/resolv.conf "${OS_ROOTDIR}/etc"	    
    $SUDO mount --bind /dev "${OS_ROOTDIR}/dev"	    
    $SUDO mount --bind /proc "${OS_ROOTDIR}/proc"	    
    $SUDO mount --bind /sys "${OS_ROOTDIR}/sys"	    
    $SUDO mount --bind /dev/pts "${OS_ROOTDIR}/dev/pts"
    #$SUDO mount -t devpts none "${OS_ROOTDIR}/dev/pts" -o ptmxmode=0666,newinstance

    set -xv
    $SUDO /usr/sbin/chroot --userspec="$USER" "${OS_ROOTDIR}" /bin/bash <<'EOF_nix_setup_1'
export HOME=/home/user
export USER=user
export LOGNAME=user
echo "user:x:$(id -u):$(id -g)::/home/user:/bin/bash" >> /etc/passwd
mkdir -p /home/user/.config/nix
echo "sandbox = false" > /home/user/.config/nix/nix.conf
echo "filter-syscalls = false" >> /home/user/.config/nix/nix.conf
sh nix_installer.sh --no-daemon
EOF_nix_setup_1
     set +xv
     sync
     $SUDO umount "${OS_ROOTDIR}/dev/pts"
     $SUDO umount "${OS_ROOTDIR}/dev"
     $SUDO umount "${OS_ROOTDIR}/sys"
     $SUDO umount "${OS_ROOTDIR}/proc"
}

nix_build_crun()
{
    echo "nix_build_crun : $1"
    local OS_ARCH="$1"
    local CRUN_SOURCE_DIR="$2"
    local OS_NAME="fedora"
    local OS_RELVER="36"
    local OS_ROOTDIR="${BUILD_DIR}/${OS_NAME}_${OS_RELVER}_${OS_ARCH}"

    if [ -x "${CRUN_SOURCE_DIR}/crun-nix-latest" ] ; then
        echo "crun binary already compiled : ${CRUN_SOURCE_DIR}/crun-nix-latest"
        return
    fi

    SUDO=/bin/sudo

    /bin/cp -f /etc/resolv.conf "${OS_ROOTDIR}/etc"	    
    $SUDO mount --bind "${CRUN_SOURCE_DIR}" "${OS_ROOTDIR}/crun"
    $SUDO mount --bind /dev "${OS_ROOTDIR}/dev"	    
    $SUDO mount --bind /proc "${OS_ROOTDIR}/proc"	    
    $SUDO mount --bind /sys "${OS_ROOTDIR}/sys"	    
    $SUDO mount --bind /dev/pts "${OS_ROOTDIR}/dev/pts"
    #$SUDO mount -t devpts none "${OS_ROOTDIR}/dev/pts" -o ptmxmode=0666,newinstance
    set -xv
    $SUDO /usr/sbin/chroot --userspec="$USER" "${OS_ROOTDIR}" /bin/bash <<'EOF_nix_crun_1'
export HOME=/home/user
export USER=user
export LOGNAME=user
. /home/user/.nix-profile/etc/profile.d/nix.sh
cd /crun
nix-build --cores 2 --max-jobs 4 nix
cp result/bin/crun crun-nix-latest
#nix-collect-garbage -d
EOF_nix_crun_1
    set +xv
    $SUDO umount "${OS_ROOTDIR}/dev/pts"
    $SUDO umount "${OS_ROOTDIR}/dev"
    $SUDO umount "${OS_ROOTDIR}/sys"
    $SUDO umount "${OS_ROOTDIR}/proc"
    $SUDO umount "${OS_ROOTDIR}/crun"
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

copy_file()
{
    local SOURCE_FILE="${BUILD_DIR}/${1}"
    local TARGET_FILE="${PACKAGE_DIR}/udocker_dir/${2}"
    if [ ! -f "$SOURCE_FILE" ] ; then
        echo "ERROR: copy_file file not found : $SOURCE_FILE"
        exit 1
    fi
    if [ -e "$TARGET_FILE" ] ; then
        echo "ERROR: copy_file target file already exists : $TARGET_FILE"
        exit 1
    fi
    /bin/cp -f  "$SOURCE_FILE"  "$TARGET_FILE"
}

link_file()
{
    local SOURCE_FILE="${PACKAGE_DIR}/udocker_dir/${1}"
    local TARGET_FILE="$2"
    if [ ! -f "$SOURCE_FILE" ] ; then
        echo "ERROR: link_file file not found : $SOURCE_FILE"
        exit 1
    fi
    SOURCE_DIR=$(dirname "$SOURCE_FILE")
    SOURCE_BASENAME=$(basename "$SOURCE_FILE")
    TARGET_BASENAME=$(basename "$TARGET_FILE")
    if [ -z "$SOURCE_DIR" ] || [ -z "$SOURCE_BASENAME" ] ; then
	echo "ERROR: link_file directory or filename is empty : $SOURCE_FILE"
	exit 1
    fi
    if [ -e "${SOURCE_DIR}/${TARGET_BASENAME}" ]; then
	echo "ERROR: link_file target for link already exists : ${SOURCE_DIR}/${TARGET_BASENAME}"
	exit 1
    fi
    ( cd "$SOURCE_DIR"; /bin/ln -s  "$SOURCE_BASENAME"  "$TARGET_BASENAME" )
}


create_package_tarball()
{
    echo "create_package_tarball : $TARBALL_FILE"

    if [ -n "$DEVEL3" ] ; then
        echo "$TARBALL_VERSION_P3"
        echo "$TARBALL_VERSION_P3" > "${PACKAGE_DIR}/udocker_dir/lib/VERSION"
    else
        echo "$TARBALL_VERSION_P2"
        echo "$TARBALL_VERSION_P2" > "${PACKAGE_DIR}/udocker_dir/lib/VERSION"
    fi

    # documents ----------------------------------------------------------------------------------------------
    copy_file proot-source-x86_64/COPYING                                 doc/COPYING.proot
    copy_file patchelf-source-x86_64/COPYING                              doc/COPYING.patchelf
    copy_file fakechroot-source-glibc-x86_64/LICENSE                      doc/LICENSE.fakechroot
    copy_file fakechroot-source-glibc-x86_64/COPYING                      doc/COPYING.fakechroot
    copy_file runc-source-x86_64/LICENSE                                  doc/LICENSE.runc 
    copy_file crun-source-x86_64/COPYING                                  doc/COPYING.crun

    # x86 ----------------------------------------------------------------------------------------------------
    copy_file proot-source-x86/proot-Fedora-25.bin                        bin/proot-x86
    copy_file proot-source-x86/proot-Fedora-30.bin                        bin/proot-x86-4_8_0

    # armhf --------------------------------------------------------------------------------------------------
    copy_file proot-source-armhf/proot-Debian-10.bin                      bin/proot-armhf

    # armel --------------------------------------------------------------------------------------------------
    copy_file proot-source-armel/proot-Debian-10.bin                      bin/proot-armel
    
    # x86_64 -------------------------------------------------------------------------------------------------
    copy_file proot-source-x86_64/proot-Fedora-25.bin                     bin/proot-x86_64
    copy_file proot-source-x86_64/proot-Fedora-30.bin                     bin/proot-x86_64-4_8_0

    copy_file patchelf-source-x86_64/patchelf-Fedora-25                   bin/patchelf-x86_64
   #copy_file patchelf-source-x86_64/patchelf-Fedora-38                   bin/patchelf-x86_64

    copy_file runc-source-x86_64/runc-Ubuntu-22.bin                       bin/runc-x86_64
    copy_file crun-source-x86_64/crun-nix-latest                          bin/crun-x86_64

    copy_file fakechroot-source-glibc-x86_64/libfakechroot-Fedora-25.so   lib/libfakechroot-Fedora-25-x86_64.so
    link_file lib/libfakechroot-Fedora-25-x86_64.so                       libfakechroot-Fedora-18-x86_64.so
    link_file lib/libfakechroot-Fedora-25-x86_64.so                       libfakechroot-Fedora-19-x86_64.so
    link_file lib/libfakechroot-Fedora-25-x86_64.so                       libfakechroot-Fedora-20-x86_64.so
    link_file lib/libfakechroot-Fedora-25-x86_64.so                       libfakechroot-Fedora-21-x86_64.so
    link_file lib/libfakechroot-Fedora-25-x86_64.so                       libfakechroot-Fedora-22-x86_64.so
    link_file lib/libfakechroot-Fedora-25-x86_64.so                       libfakechroot-Fedora-23-x86_64.so
    link_file lib/libfakechroot-Fedora-25-x86_64.so                       libfakechroot-Fedora-24-x86_64.so
    link_file lib/libfakechroot-Fedora-25-x86_64.so                       libfakechroot-Fedora-26-x86_64.so
    link_file lib/libfakechroot-Fedora-25-x86_64.so                       libfakechroot-Fedora-27-x86_64.so
    link_file lib/libfakechroot-Fedora-25-x86_64.so                       libfakechroot-Fedora-28-x86_64.so
    copy_file fakechroot-source-glibc-x86_64/libfakechroot-Fedora-29.so   lib/libfakechroot-Fedora-29-x86_64.so
    copy_file fakechroot-source-glibc-x86_64/libfakechroot-Fedora-30.so   lib/libfakechroot-Fedora-30-x86_64.so
    copy_file fakechroot-source-glibc-x86_64/libfakechroot-Fedora-31.so   lib/libfakechroot-Fedora-31-x86_64.so
    copy_file fakechroot-source-glibc-x86_64/libfakechroot-Fedora-32.so   lib/libfakechroot-Fedora-32-x86_64.so
    copy_file fakechroot-source-glibc-x86_64/libfakechroot-Fedora-33.so   lib/libfakechroot-Fedora-33-x86_64.so
    copy_file fakechroot-source-glibc-x86_64/libfakechroot-Fedora-34.so   lib/libfakechroot-Fedora-34-x86_64.so
    copy_file fakechroot-source-glibc-x86_64/libfakechroot-Fedora-35.so   lib/libfakechroot-Fedora-35-x86_64.so
    copy_file fakechroot-source-glibc-x86_64/libfakechroot-Fedora-36.so   lib/libfakechroot-Fedora-36-x86_64.so
    link_file lib/libfakechroot-Fedora-36-x86_64.so                       libfakechroot-Fedora-37-x86_64.so
    copy_file fakechroot-source-glibc-x86_64/libfakechroot-Fedora-38.so   lib/libfakechroot-Fedora-38-x86_64.so
    link_file lib/libfakechroot-Fedora-38-x86_64.so                       libfakechroot-Fedora-x86_64.so

    copy_file fakechroot-source-glibc-x86_64/libfakechroot-CentOS-6.so    lib/libfakechroot-CentOS-6-x86_64.so
    copy_file fakechroot-source-glibc-x86_64/libfakechroot-CentOS-7.so    lib/libfakechroot-CentOS-7-x86_64.so
    copy_file fakechroot-source-glibc-x86_64/libfakechroot-CentOS-8.so    lib/libfakechroot-CentOS-8-x86_64.so
    copy_file fakechroot-source-glibc-x86_64/libfakechroot-CentOS-9.so    lib/libfakechroot-CentOS-9-x86_64.so
    link_file lib/libfakechroot-CentOS-6-x86_64.so                        libfakechroot-CentOS-4-x86_64.so
    link_file lib/libfakechroot-CentOS-6-x86_64.so                        libfakechroot-CentOS-5-x86_64.so
    link_file lib/libfakechroot-CentOS-9-x86_64.so                        libfakechroot-CentOS-x86_64.so

   #copy_file fakechroot-source-glibc-x86_64/libfakechroot-Rocky-8.so     lib/libfakechroot-Rocky-8-x86_64.so
   #copy_file fakechroot-source-glibc-x86_64/libfakechroot-Rocky-9.so     lib/libfakechroot-Rocky-9-x86_64.so
   #link_file fakechroot-source-glibc-x86_64/libfakechroot-Rocky-9.so     libfakechroot-Rocky-x86_64.so

    copy_file fakechroot-source-glibc-x86_64/libfakechroot-AlmaLinux-8.so  lib/libfakechroot-AlmaLinux-8-x86_64.so
    copy_file fakechroot-source-glibc-x86_64/libfakechroot-AlmaLinux-9.so  lib/libfakechroot-AlmaLinux-9-x86_64.so
    link_file lib/libfakechroot-AlmaLinux-9-x86_64.so                      libfakechroot-AlmaLinux-x86_64.so

    link_file lib/libfakechroot-CentOS-6-x86_64.so                        libfakechroot-Red-4-x86_64.so
    link_file lib/libfakechroot-CentOS-6-x86_64.so                        libfakechroot-Red-5-x86_64.so
    link_file lib/libfakechroot-CentOS-6-x86_64.so                        libfakechroot-Red-6-x86_64.so
    link_file lib/libfakechroot-CentOS-7-x86_64.so                        libfakechroot-Red-7-x86_64.so
    link_file lib/libfakechroot-AlmaLinux-8-x86_64.so                     libfakechroot-Red-8-x86_64.so
    link_file lib/libfakechroot-AlmaLinux-9-x86_64.so                     libfakechroot-Red-9-x86_64.so
    link_file lib/libfakechroot-AlmaLinux-9-x86_64.so                     libfakechroot-Red-x86_64.so

    link_file lib/libfakechroot-CentOS-6-x86_64.so                        libfakechroot-Scientific-4-x86_64.so
    link_file lib/libfakechroot-CentOS-6-x86_64.so                        libfakechroot-Scientific-5-x86_64.so
    link_file lib/libfakechroot-CentOS-6-x86_64.so                        libfakechroot-Scientific-6-x86_64.so
    link_file lib/libfakechroot-CentOS-7-x86_64.so                        libfakechroot-Scientific-7-x86_64.so
    link_file lib/libfakechroot-AlmaLinux-8-x86_64.so                     libfakechroot-Scientific-8-x86_64.so
    link_file lib/libfakechroot-AlmaLinux-9-x86_64.so                     libfakechroot-Scientific-9-x86_64.so
    link_file lib/libfakechroot-AlmaLinux-9-x86_64.so                     libfakechroot-Scientific-x86_64.so

    link_file lib/libfakechroot-AlmaLinux-8-x86_64.so                     libfakechroot-Rocky-8-x86_64.so
    link_file lib/libfakechroot-AlmaLinux-9-x86_64.so                     libfakechroot-Rocky-9-x86_64.so
    link_file lib/libfakechroot-AlmaLinux-9-x86_64.so                     libfakechroot-Rocky-x86_64.so

    copy_file fakechroot-source-glibc-x86_64/libfakechroot-Ubuntu-12.so   lib/libfakechroot-Ubuntu-12-x86_64.so
    copy_file fakechroot-source-glibc-x86_64/libfakechroot-Ubuntu-14.so   lib/libfakechroot-Ubuntu-14-x86_64.so
    link_file lib/libfakechroot-Ubuntu-14-x86_64.so                       libfakechroot-x86_64.so
    copy_file fakechroot-source-glibc-x86_64/libfakechroot-Ubuntu-16.so   lib/libfakechroot-Ubuntu-16-x86_64.so
    copy_file fakechroot-source-glibc-x86_64/libfakechroot-Ubuntu-18.so   lib/libfakechroot-Ubuntu-18-x86_64.so
    copy_file fakechroot-source-glibc-x86_64/libfakechroot-Ubuntu-19.so   lib/libfakechroot-Ubuntu-19-x86_64.so
    copy_file fakechroot-source-glibc-x86_64/libfakechroot-Ubuntu-20.so   lib/libfakechroot-Ubuntu-20-x86_64.so
    copy_file fakechroot-source-glibc-x86_64/libfakechroot-Ubuntu-21.so   lib/libfakechroot-Ubuntu-21-x86_64.so
    copy_file fakechroot-source-glibc-x86_64/libfakechroot-Ubuntu-22.so   lib/libfakechroot-Ubuntu-22-x86_64.so
    copy_file fakechroot-source-glibc-x86_64/libfakechroot-Ubuntu-23.so   lib/libfakechroot-Ubuntu-23-x86_64.so
    link_file lib/libfakechroot-Ubuntu-12-x86_64.so                       libfakechroot-Ubuntu-9-x86_64.so
    link_file lib/libfakechroot-Ubuntu-12-x86_64.so                       libfakechroot-Ubuntu-10-x86_64.so
    link_file lib/libfakechroot-Ubuntu-12-x86_64.so                       libfakechroot-Ubuntu-11-x86_64.so
    link_file lib/libfakechroot-Ubuntu-14-x86_64.so                       libfakechroot-Ubuntu-13-x86_64.so
    link_file lib/libfakechroot-Ubuntu-16-x86_64.so                       libfakechroot-Ubuntu-15-x86_64.so
    link_file lib/libfakechroot-Ubuntu-18-x86_64.so                       libfakechroot-Ubuntu-17-x86_64.so
    link_file lib/libfakechroot-Ubuntu-23-x86_64.so                       libfakechroot-Ubuntu-x86_64.so

    link_file lib/libfakechroot-Ubuntu-12-x86_64.so                       libfakechroot-Debian-7-x86_64.so
    link_file lib/libfakechroot-Ubuntu-14-x86_64.so                       libfakechroot-Debian-8-x86_64.so
    link_file lib/libfakechroot-Ubuntu-16-x86_64.so                       libfakechroot-Debian-9-x86_64.so
    link_file lib/libfakechroot-Ubuntu-19-x86_64.so                       libfakechroot-Debian-10-x86_64.so
    link_file lib/libfakechroot-Ubuntu-20-x86_64.so                       libfakechroot-Debian-11-x86_64.so
    link_file lib/libfakechroot-Ubuntu-22-x86_64.so                       libfakechroot-Debian-12-x86_64.so
    link_file lib/libfakechroot-Ubuntu-23-x86_64.so                       libfakechroot-Debian-x86_64.so

    link_file lib/libfakechroot-Ubuntu-12-x86_64.so                       libfakechroot-LinuxMint-10-x86_64.so
    link_file lib/libfakechroot-Ubuntu-12-x86_64.so                       libfakechroot-LinuxMint-11-x86_64.so
    link_file lib/libfakechroot-Ubuntu-12-x86_64.so                       libfakechroot-LinuxMint-12-x86_64.so
    link_file lib/libfakechroot-Ubuntu-14-x86_64.so                       libfakechroot-LinuxMint-13-x86_64.so
    link_file lib/libfakechroot-Ubuntu-14-x86_64.so                       libfakechroot-LinuxMint-14-x86_64.so
    link_file lib/libfakechroot-Ubuntu-16-x86_64.so                       libfakechroot-LinuxMint-15-x86_64.so
    link_file lib/libfakechroot-Ubuntu-16-x86_64.so                       libfakechroot-LinuxMint-16-x86_64.so
    link_file lib/libfakechroot-Ubuntu-18-x86_64.so                       libfakechroot-LinuxMint-17-x86_64.so
    link_file lib/libfakechroot-Ubuntu-18-x86_64.so                       libfakechroot-LinuxMint-18-x86_64.so
    link_file lib/libfakechroot-Ubuntu-19-x86_64.so                       libfakechroot-LinuxMint-19-x86_64.so
    link_file lib/libfakechroot-Ubuntu-20-x86_64.so                       libfakechroot-LinuxMint-20-x86_64.so
    link_file lib/libfakechroot-Ubuntu-21-x86_64.so                       libfakechroot-LinuxMint-21-x86_64.so
    link_file lib/libfakechroot-Ubuntu-22-x86_64.so                       libfakechroot-LinuxMint-22-x86_64.so
    link_file lib/libfakechroot-Ubuntu-23-x86_64.so                       libfakechroot-LinuxMint-23-x86_64.so
    link_file lib/libfakechroot-Ubuntu-23-x86_64.so                       libfakechroot-LinuxMint-x86_64.so

    copy_file fakechroot-source-musl-x86_64/libfakechroot-Alpine-3.6.so   lib/libfakechroot-Alpine-3.6-x86_64.so
    copy_file fakechroot-source-musl-x86_64/libfakechroot-Alpine-3.8.so   lib/libfakechroot-Alpine-3.8-x86_64.so
    copy_file fakechroot-source-musl-x86_64/libfakechroot-Alpine-3.9.so   lib/libfakechroot-Alpine-3.9-x86_64.so 
    copy_file fakechroot-source-musl-x86_64/libfakechroot-Alpine-3.10.so  lib/libfakechroot-Alpine-3.10-x86_64.so
    copy_file fakechroot-source-musl-x86_64/libfakechroot-Alpine-3.11.so  lib/libfakechroot-Alpine-3.11-x86_64.so
    copy_file fakechroot-source-musl-x86_64/libfakechroot-Alpine-3.12.so  lib/libfakechroot-Alpine-3.12-x86_64.so
    copy_file fakechroot-source-musl-x86_64/libfakechroot-Alpine-3.13.so  lib/libfakechroot-Alpine-3.13-x86_64.so
    copy_file fakechroot-source-musl-x86_64/libfakechroot-Alpine-3.14.so  lib/libfakechroot-Alpine-3.14-x86_64.so
    copy_file fakechroot-source-musl-x86_64/libfakechroot-Alpine-3.15.so  lib/libfakechroot-Alpine-3.15-x86_64.so
    copy_file fakechroot-source-musl-x86_64/libfakechroot-Alpine-3.16.so  lib/libfakechroot-Alpine-3.16-x86_64.so
    copy_file fakechroot-source-musl-x86_64/libfakechroot-Alpine-3.17.so  lib/libfakechroot-Alpine-3.17-x86_64.so
    copy_file fakechroot-source-musl-x86_64/libfakechroot-Alpine-3.18.so  lib/libfakechroot-Alpine-3.18-x86_64.so
    link_file lib/libfakechroot-Alpine-3.6-x86_64.so                      libfakechroot-Alpine-3.0-x86_64.so
    link_file lib/libfakechroot-Alpine-3.6-x86_64.so                      libfakechroot-Alpine-3.1-x86_64.so
    link_file lib/libfakechroot-Alpine-3.6-x86_64.so                      libfakechroot-Alpine-3.2-x86_64.so
    link_file lib/libfakechroot-Alpine-3.6-x86_64.so                      libfakechroot-Alpine-3.3-x86_64.so
    link_file lib/libfakechroot-Alpine-3.6-x86_64.so                      libfakechroot-Alpine-3.4-x86_64.so
    link_file lib/libfakechroot-Alpine-3.6-x86_64.so                      libfakechroot-Alpine-3.5-x86_64.so
    link_file lib/libfakechroot-Alpine-3.18-x86_64.so                     libfakechroot-Alpine-x86_64.so

    # arch64 / amd64 -----------------------------------------------------------------------------------------
    copy_file proot-source-aarch64/proot-Fedora-31.bin                      bin/proot-arm64-4_8_0
    link_file bin/proot-arm64-4_8_0                                         proot-arm64
    copy_file patchelf-source-aarch64/patchelf-AlmaLinux-9                  bin/patchelf-arm64
    copy_file runc-source-aarch64/runc-Ubuntu-22.bin                        bin/runc-arm64

    copy_file fakechroot-source-glibc-aarch64/libfakechroot-Fedora-36.so    lib/libfakechroot-Fedora-36-arm64.so
    copy_file fakechroot-source-glibc-aarch64/libfakechroot-Fedora-38.so    lib/libfakechroot-Fedora-38-arm64.so
    link_file lib/libfakechroot-Fedora-36-arm64.so                          libfakechroot-Fedora-37-arm64.so
    link_file lib/libfakechroot-Fedora-38-arm64.so                          libfakechroot-Fedora-arm64.so

    copy_file fakechroot-source-glibc-aarch64/libfakechroot-CentOS-7.so     lib/libfakechroot-CentOS-7-arm64.so
    copy_file fakechroot-source-glibc-aarch64/libfakechroot-AlmaLinux-8.so  lib/libfakechroot-AlmaLinux-8-arm64.so
    copy_file fakechroot-source-glibc-aarch64/libfakechroot-AlmaLinux-9.so  lib/libfakechroot-AlmaLinux-9-arm64.so

    copy_file fakechroot-source-glibc-aarch64/libfakechroot-Ubuntu-16.so    lib/libfakechroot-Ubuntu-16-arm64.so
    copy_file fakechroot-source-glibc-aarch64/libfakechroot-Ubuntu-18.so    lib/libfakechroot-Ubuntu-18-arm64.so
    copy_file fakechroot-source-glibc-aarch64/libfakechroot-Ubuntu-20.so    lib/libfakechroot-Ubuntu-20-arm64.so
    copy_file fakechroot-source-glibc-aarch64/libfakechroot-Ubuntu-22.so    lib/libfakechroot-Ubuntu-22-arm64.so
    link_file lib/libfakechroot-Ubuntu-18-arm64.so                          libfakechroot-Ubuntu-17-arm64.so
    link_file lib/libfakechroot-Ubuntu-20-arm64.so                          libfakechroot-Ubuntu-19-arm64.so
    link_file lib/libfakechroot-Ubuntu-22-arm64.so                          libfakechroot-Ubuntu-21-arm64.so
    link_file lib/libfakechroot-Ubuntu-22-arm64.so                          libfakechroot-Ubuntu-arm64.so

    link_file lib/libfakechroot-Ubuntu-16-arm64.so                          libfakechroot-LinuxMint-16-arm64.so
    link_file lib/libfakechroot-Ubuntu-18-arm64.so                          libfakechroot-LinuxMint-17-arm64.so
    link_file lib/libfakechroot-Ubuntu-18-arm64.so                          libfakechroot-LinuxMint-18-arm64.so
    link_file lib/libfakechroot-Ubuntu-20-arm64.so                          libfakechroot-LinuxMint-19-arm64.so
    link_file lib/libfakechroot-Ubuntu-20-arm64.so                          libfakechroot-LinuxMint-20-arm64.so
    link_file lib/libfakechroot-Ubuntu-22-arm64.so                          libfakechroot-LinuxMint-21-arm64.so
    link_file lib/libfakechroot-Ubuntu-22-arm64.so                          libfakechroot-LinuxMint-22-arm64.so
    link_file lib/libfakechroot-Ubuntu-22-arm64.so                          libfakechroot-LinuxMint-arm64.so

    link_file lib/libfakechroot-Ubuntu-16-arm64.so                          libfakechroot-Debian-9-arm64.so
    link_file lib/libfakechroot-Ubuntu-18-arm64.so                          libfakechroot-Debian-10-arm64.so
    link_file lib/libfakechroot-Ubuntu-20-arm64.so                          libfakechroot-Debian-11-arm64.so
    link_file lib/libfakechroot-Ubuntu-22-arm64.so                          libfakechroot-Debian-12-arm64.so
    link_file lib/libfakechroot-Ubuntu-22-arm64.so                          libfakechroot-Debian-arm64.so

    link_file lib/libfakechroot-AlmaLinux-8-arm64.so                        libfakechroot-CentOS-8-arm64.so
    link_file lib/libfakechroot-AlmaLinux-9-arm64.so                        libfakechroot-CentOS-9-arm64.so
    link_file lib/libfakechroot-AlmaLinux-9-arm64.so                        libfakechroot-CentOS-arm64.so

    link_file lib/libfakechroot-AlmaLinux-8-arm64.so                        libfakechroot-Rocky-8-arm64.so
    link_file lib/libfakechroot-AlmaLinux-9-arm64.so                        libfakechroot-Rocky-9-arm64.so
    link_file lib/libfakechroot-AlmaLinux-9-arm64.so                        libfakechroot-Rocky-arm64.so

    link_file lib/libfakechroot-AlmaLinux-8-arm64.so                        libfakechroot-Red-8-arm64.so
    link_file lib/libfakechroot-AlmaLinux-9-arm64.so                        libfakechroot-Red-9-arm64.so
    link_file lib/libfakechroot-AlmaLinux-9-arm64.so                        libfakechroot-Red-arm64.so

    # ppc64le ------------------------------------------------------------------------------------------------
    copy_file patchelf-source-ppc64le/patchelf-AlmaLinux-9                  bin/patchelf-ppc64le
    copy_file runc-source-ppc64le/runc-Ubuntu-22.bin                        bin/runc-ppc64le

    copy_file fakechroot-source-glibc-ppc64le/libfakechroot-CentOS-7.so     lib/libfakechroot-CentOS-7-ppc64le.so
    copy_file fakechroot-source-glibc-ppc64le/libfakechroot-AlmaLinux-8.so  lib/libfakechroot-AlmaLinux-8-ppc64le.so
    copy_file fakechroot-source-glibc-ppc64le/libfakechroot-AlmaLinux-9.so  lib/libfakechroot-AlmaLinux-9-ppc64le.so
    copy_file fakechroot-source-glibc-ppc64le/libfakechroot-AlmaLinux-9.so  lib/libfakechroot-AlmaLinux-ppc64le.so

    copy_file fakechroot-source-glibc-ppc64le/libfakechroot-Fedora-38.so    lib/libfakechroot-Fedora-38-ppc64le.so
    link_file lib/libfakechroot-Fedora-38-ppc64le.so                        libfakechroot-Fedora-ppc64le.so

    copy_file fakechroot-source-glibc-ppc64le/libfakechroot-Ubuntu-16.so    lib/libfakechroot-Ubuntu-16-ppc64le.so
    copy_file fakechroot-source-glibc-ppc64le/libfakechroot-Ubuntu-18.so    lib/libfakechroot-Ubuntu-18-ppc64le.so
    copy_file fakechroot-source-glibc-ppc64le/libfakechroot-Ubuntu-20.so    lib/libfakechroot-Ubuntu-20-ppc64le.so
    copy_file fakechroot-source-glibc-ppc64le/libfakechroot-Ubuntu-22.so    lib/libfakechroot-Ubuntu-22-ppc64le.so
    link_file lib/libfakechroot-Ubuntu-18-ppc64le.so                        libfakechroot-Ubuntu-17-ppc64le.so
    link_file lib/libfakechroot-Ubuntu-20-ppc64le.so                        libfakechroot-Ubuntu-19-ppc64le.so
    link_file lib/libfakechroot-Ubuntu-22-ppc64le.so                        libfakechroot-Ubuntu-21-ppc64le.so
    link_file lib/libfakechroot-Ubuntu-22-ppc64le.so                        libfakechroot-Ubuntu-ppc64le.so

    link_file lib/libfakechroot-Ubuntu-16-ppc64le.so                        libfakechroot-LinuxMint-16-ppc64le.so
    link_file lib/libfakechroot-Ubuntu-18-ppc64le.so                        libfakechroot-LinuxMint-17-ppc64le.so
    link_file lib/libfakechroot-Ubuntu-18-ppc64le.so                        libfakechroot-LinuxMint-18-ppc64le.so
    link_file lib/libfakechroot-Ubuntu-20-ppc64le.so                        libfakechroot-LinuxMint-19-ppc64le.so
    link_file lib/libfakechroot-Ubuntu-20-ppc64le.so                        libfakechroot-LinuxMint-20-ppc64le.so
    link_file lib/libfakechroot-Ubuntu-22-ppc64le.so                        libfakechroot-LinuxMint-21-ppc64le.so
    link_file lib/libfakechroot-Ubuntu-22-ppc64le.so                        libfakechroot-LinuxMint-22-ppc64le.so
    link_file lib/libfakechroot-Ubuntu-22-ppc64le.so                        libfakechroot-LinuxMint-ppc64le.so

    link_file lib/libfakechroot-Ubuntu-16-ppc64le.so                        libfakechroot-Debian-9-ppc64le.so
    link_file lib/libfakechroot-Ubuntu-18-ppc64le.so                        libfakechroot-Debian-10-ppc64le.so
    link_file lib/libfakechroot-Ubuntu-20-ppc64le.so                        libfakechroot-Debian-11-ppc64le.so
    link_file lib/libfakechroot-Ubuntu-22-ppc64le.so                        libfakechroot-Debian-12-ppc64le.so
    link_file lib/libfakechroot-Ubuntu-22-ppc64le.so                        libfakechroot-Debian-ppc64le.so

    link_file lib/libfakechroot-AlmaLinux-8-ppc64le.so                      libfakechroot-CentOS-8-ppc64le.so
    link_file lib/libfakechroot-AlmaLinux-9-ppc64le.so                      libfakechroot-CentOS-9-ppc64le.so
    link_file lib/libfakechroot-AlmaLinux-9-ppc64le.so                      libfakechroot-CentOS-ppc64le.so

    link_file lib/libfakechroot-AlmaLinux-8-ppc64le.so                      libfakechroot-Rocky-8-ppc64le.so
    link_file lib/libfakechroot-AlmaLinux-9-ppc64le.so                      libfakechroot-Rocky-9-ppc64le.so
    link_file lib/libfakechroot-AlmaLinux-9-ppc64le.so                      libfakechroot-Rocky-ppc64le.so

    link_file lib/libfakechroot-AlmaLinux-8-ppc64le.so                      libfakechroot-Red-8-ppc64le.so
    link_file lib/libfakechroot-AlmaLinux-9-ppc64le.so                      libfakechroot-Red-9-ppc64le.so
    link_file lib/libfakechroot-AlmaLinux-9-ppc64le.so                      libfakechroot-Red-ppc64le.so

    # package ------------------------------------------------------------------------------------------------
    find "${PACKAGE_DIR}" -type d -exec /bin/chmod u=rwx,og=rx  {} \;
    find "${PACKAGE_DIR}" -type f -exec /bin/chmod u=+r+w,og=r  {} \;
    find "${PACKAGE_DIR}/udocker_dir/bin" -type f -exec /bin/chmod u=rwx,og=rx  {} \;
    /bin/chmod u=rwx,og=rx "${PACKAGE_DIR}/setup.py"
    [ -e "${PACKAGE_DIR}/udocker" ] && \
        /bin/chmod u=rwx,og=rx "${PACKAGE_DIR}/udocker" 
    [ -e "${PACKAGE_DIR}/setup.py" ] && \
        /bin/chmod u=rwx,og=rx "${PACKAGE_DIR}/setup.py" 

    /bin/rm -f "$TARBALL_FILE" > /dev/null 2>&1

    cd "$PACKAGE_DIR"
    /bin/rm -f "$TARBALL_FILE"
    tar --owner=root --group=root -czvf "$TARBALL_FILE" $(ls -A)
}

# ##################################################################
# MAIN
# ##################################################################

utils_dir="$(dirname $(readlink -e "$0"))"
REPO_DIR="$(dirname $utils_dir)"

sanity_check

BUILD_DIR="${HOME}/udocker-englib-${TARBALL_VERSION_P3}"
S_PROOT_DIR="${BUILD_DIR}/proot-static-build/static"
S_PROOT_PACKAGES_DIR="${BUILD_DIR}/proot-static-build/packages"
PACKAGE_DIR="${BUILD_DIR}/package"
#TALLOC_TAR="$BUILD_DIR/libtalloc/talloc.tar.gz"

if [ -n "$DEVEL3" ]; then
    TARBALL_FILE="${BUILD_DIR}/udocker-englib-${TARBALL_VERSION_P3}.tar.gz"
else
    TARBALL_FILE="${BUILD_DIR}/udocker-${TARBALL_VERSION_P2}.tar.gz"
fi

[ ! -e "$BUILD_DIR" ] && /bin/mkdir -p "$BUILD_DIR"

# #######
# Prepare
# #######

#get_proot_static 

get_udocker_static "1.2.10"

get_libtalloc

prepare_crun_source "${BUILD_DIR}/crun-source-x86_64"

prepare_package ERASE


# #######
# i386
# #######
prepare_proot_source "${BUILD_DIR}/proot-source-x86"
#
fedora25_setup "i386"
fedora25_build_proot "i386" "${BUILD_DIR}/proot-source-x86"
#ostree_delete "i386" "fedora" "25"
#
fedora30_setup "i386"
fedora30_build_proot "i386" "${BUILD_DIR}/proot-source-x86"
#ostree_delete "i386" "fedora" "30"


# #######
# x86_64
# #######
prepare_proot_source "${BUILD_DIR}/proot-source-x86_64"
prepare_patchelf_source_v1 "${BUILD_DIR}/patchelf-source-x86_64"
prepare_fakechroot_glibc_source "${BUILD_DIR}/fakechroot-source-glibc-x86_64"
prepare_fakechroot_musl_source "${BUILD_DIR}/fakechroot-source-musl-x86_64"
prepare_runc_source "${BUILD_DIR}/runc-source-x86_64"


fedora25_setup "x86_64"
fedora25_build_proot "x86_64" "${BUILD_DIR}/proot-source-x86_64"
fedora25_build_patchelf "x86_64" "${BUILD_DIR}/patchelf-source-x86_64"
fedora25_build_fakechroot "x86_64" "${BUILD_DIR}/fakechroot-source-glibc-x86_64"
#ostree_delete "x86_64" "fedora" "25"
#
fedora30_setup "x86_64"
fedora30_build_proot "x86_64" "${BUILD_DIR}/proot-source-x86_64"
#fedora30_build_patchelf "x86_64" "${BUILD_DIR}/patchelf-source-x86_64"
fedora30_build_fakechroot "x86_64" "${BUILD_DIR}/fakechroot-source-glibc-x86_64"
#ostree_delete "x86_64" "fedora" "30"
#
fedora31_setup "x86_64"
#fedora31_build_proot "x86_64" "${BUILD_DIR}/proot-source-x86_64"
#fedora31_build_patchelf "x86_64" "${BUILD_DIR}/patchelf-source-x86_64"
fedora31_build_fakechroot "x86_64" "${BUILD_DIR}/fakechroot-source-glibc-x86_64"
#
fedora32_setup "x86_64"
#fedora32_build_proot "x86_64" "${BUILD_DIR}/proot-source-x86_64"
#fedora32_build_patchelf "x86_64" "${BUILD_DIR}/patchelf-source-x86_64"
fedora32_build_fakechroot "x86_64" "${BUILD_DIR}/fakechroot-source-glibc-x86_64"
#ostree_delete "x86_64" "fedora" "32"
#
fedora33_setup "x86_64"
#fedora33_build_proot "x86_64" "${BUILD_DIR}/proot-source-x86_64"
#fedora33_build_patchelf "x86_64" "${BUILD_DIR}/patchelf-source-x86_64"
fedora33_build_fakechroot "x86_64" "${BUILD_DIR}/fakechroot-source-glibc-x86_64"
#ostree_delete "x86_64" "fedora" "33"
#
fedora34_setup "x86_64"
#fedora34_build_proot "x86_64" "${BUILD_DIR}/proot-source-x86_64"
#fedora34_build_patchelf "x86_64" "${BUILD_DIR}/patchelf-source-x86_64"
fedora34_build_fakechroot "x86_64" "${BUILD_DIR}/fakechroot-source-glibc-x86_64"
#ostree_delete "x86_64" "fedora" "33"
#
fedora35_setup "x86_64"
#fedora35_build_proot "x86_64" "${BUILD_DIR}/proot-source-x86_64"
#fedora35_build_patchelf "x86_64" "${BUILD_DIR}/patchelf-source-x86_64"
fedora35_build_fakechroot "x86_64" "${BUILD_DIR}/fakechroot-source-glibc-x86_64"
#
fedora36_setup "x86_64"
#fedora36_build_proot "x86_64" "${BUILD_DIR}/proot-source-x86_64"
#fedora36_build_patchelf "x86_64" "${BUILD_DIR}/patchelf-source-x86_64"
fedora36_build_fakechroot "x86_64" "${BUILD_DIR}/fakechroot-source-glibc-x86_64"
#ostree_delete "x86_64" "fedora" "36"
#
fedora38_setup "x86_64"
#fedora38_build_proot "x86_64" "${BUILD_DIR}/proot-source-x86_64"
#fedora38_build_patchelf "x86_64" "${BUILD_DIR}/patchelf-source-x86_64"
fedora38_build_fakechroot "x86_64" "${BUILD_DIR}/fakechroot-source-glibc-x86_64"
#ostree_delete "x86_64" "fedora" "38"

fedora29_setup "x86_64"
#fedora29_build_proot "x86_64" "${BUILD_DIR}/proot-source-x86_64"
#fedora29_build_patchelf "x86_64" "${BUILD_DIR}/patchelf-source-x86_64"
fedora29_build_fakechroot "x86_64" "${BUILD_DIR}/fakechroot-source-glibc-x86_64"
#ostree_delete "x86_64" "fedora" "29"

alpine36_setup "x86_64"
alpine36_build_fakechroot "x86_64" "${BUILD_DIR}/fakechroot-source-musl-x86_64"
#ostree_delete "x86_64" "alpine" "3.6"
#
alpine38_setup "x86_64"
alpine38_build_fakechroot "x86_64" "${BUILD_DIR}/fakechroot-source-musl-x86_64"
#ostree_delete "x86_64" "alpine" "3.8"
#
alpine39_setup "x86_64"
alpine39_build_fakechroot "x86_64" "${BUILD_DIR}/fakechroot-source-musl-x86_64"
#ostree_delete "x86_64" "alpine" "3.9"
#
alpine310_setup "x86_64"
alpine310_build_fakechroot "x86_64" "${BUILD_DIR}/fakechroot-source-musl-x86_64"
#ostree_delete "x86_64" "alpine" "3.10"
#
alpine311_setup "x86_64"
alpine311_build_fakechroot "x86_64" "${BUILD_DIR}/fakechroot-source-musl-x86_64"
#ostree_delete "x86_64" "alpine" "3.11"
#
alpine312_setup "x86_64"
alpine312_build_fakechroot "x86_64" "${BUILD_DIR}/fakechroot-source-musl-x86_64"
#ostree_delete "x86_64" "alpine" "3.12"
#
alpine313_setup "x86_64"
alpine313_build_fakechroot "x86_64" "${BUILD_DIR}/fakechroot-source-musl-x86_64"
#ostree_delete "x86_64" "alpine" "3.13"
#
alpine314_setup "x86_64"
alpine314_build_fakechroot "x86_64" "${BUILD_DIR}/fakechroot-source-musl-x86_64"
#ostree_delete "x86_64" "alpine" "3.14"
#
alpine315_setup "x86_64"
alpine315_build_fakechroot "x86_64" "${BUILD_DIR}/fakechroot-source-musl-x86_64"
#ostree_delete "x86_64" "alpine" "3.15"
#
alpine316_setup "x86_64"
alpine316_build_fakechroot "x86_64" "${BUILD_DIR}/fakechroot-source-musl-x86_64"
#ostree_delete "x86_64" "alpine" "3.16"
#
alpine317_setup "x86_64"
alpine317_build_fakechroot "x86_64" "${BUILD_DIR}/fakechroot-source-musl-x86_64"
#ostree_delete "x86_64" "alpine" "3.17"
#
alpine318_setup "x86_64"
alpine318_build_fakechroot "x86_64" "${BUILD_DIR}/fakechroot-source-musl-x86_64"
#ostree_delete "x86_64" "alpine" "3.18"

centos6_setup "x86_64"
#centos6_build_proot "x86_64" "${BUILD_DIR}/proot-source-x86_64"
centos6_build_fakechroot "x86_64" "${BUILD_DIR}/fakechroot-source-glibc-x86_64"
#ostree_delete "x86_64" "centos" "6"
#
centos7_setup "x86_64"
#centos7_build_proot "x86_64" "${BUILD_DIR}/proot-source-x86_64"
centos7_build_fakechroot "x86_64" "${BUILD_DIR}/fakechroot-source-glibc-x86_64"
#ostree_delete "x86_64" "centos" "7"
#
centos_stream8_setup "x86_64"
centos_stream8_build_fakechroot "x86_64" "${BUILD_DIR}/fakechroot-source-glibc-x86_64"
#ostree_delete "x86_64" "centos" "8"
#
centos_stream9_setup "x86_64"
centos_stream9_build_fakechroot "x86_64" "${BUILD_DIR}/fakechroot-source-glibc-x86_64"
#ostree_delete "x86_64" "centos" "9"

#rocky8_setup "x86_64"
#rocky8_build_fakechroot "x86_64" "${BUILD_DIR}/fakechroot-source-glibc-x86_64"
#ostree_delete "x86_64" "rocky" "8"
#
#rocky9_setup "x86_64"
#rocky9_build_fakechroot "x86_64" "${BUILD_DIR}/fakechroot-source-glibc-x86_64"
#ostree_delete "x86_64" "rocky" "9"

alma8_setup "x86_64"
alma8_build_fakechroot "x86_64" "${BUILD_DIR}/fakechroot-source-glibc-x86_64"
#ostree_delete "x86_64" "alma" "8"
#
alma9_setup "x86_64"
alma9_build_fakechroot "x86_64" "${BUILD_DIR}/fakechroot-source-glibc-x86_64"
#ostree_delete "x86_64" "alma" "9"

#
ubuntu12_setup "amd64"
ubuntu12_build_fakechroot "amd64" "${BUILD_DIR}/fakechroot-source-glibc-x86_64"
#ostree_delete "amd64" "ubuntu" "12"
#
ubuntu14_setup "amd64"
ubuntu14_build_fakechroot "amd64" "${BUILD_DIR}/fakechroot-source-glibc-x86_64"
#ostree_delete "amd64" "ubuntu" "14"
#
ubuntu16_setup "amd64"
ubuntu16_build_fakechroot "amd64" "${BUILD_DIR}/fakechroot-source-glibc-x86_64"
#ostree_delete "amd64" "ubuntu" "16"
#
ubuntu18_setup "amd64"
ubuntu18_build_fakechroot "amd64" "${BUILD_DIR}/fakechroot-source-glibc-x86_64"
#ostree_delete "amd64" "ubuntu" "18"
#
ubuntu19_setup "amd64"
ubuntu19_build_fakechroot "amd64" "${BUILD_DIR}/fakechroot-source-glibc-x86_64"
#ostree_delete "amd64" "ubuntu" "19"
#
ubuntu20_setup "amd64"
ubuntu20_build_fakechroot "amd64" "${BUILD_DIR}/fakechroot-source-glibc-x86_64"
#ostree_delete "amd64" "ubuntu" "20"
#
ubuntu21_setup "amd64"
ubuntu21_build_fakechroot "amd64" "${BUILD_DIR}/fakechroot-source-glibc-x86_64"
#ostree_delete "amd64" "ubuntu" "21"
#
ubuntu22_setup "amd64"
ubuntu22_build_fakechroot "amd64" "${BUILD_DIR}/fakechroot-source-glibc-x86_64"
ubuntu22_build_runc "amd64" "${BUILD_DIR}/runc-source-x86_64"
#ostree_delete "amd64" "ubuntu" "22"
#
ubuntu23_setup "amd64"
ubuntu23_build_fakechroot "amd64" "${BUILD_DIR}/fakechroot-source-glibc-x86_64"
#ubuntu23_build_runc "amd64" "${BUILD_DIR}/runc-source-x86_64"
#ostree_delete "amd64" "ubuntu" "23"

#debian12_setup "amd64"
#debian12_build_fakechroot "amd64" "${BUILD_DIR}/fakechroot-source-glibc-x86_64"

# #######
# armhf
# #######
prepare_proot_source "${BUILD_DIR}/proot-source-armhf"
debian10_setup "armhf"
debian10_build_proot "armhf" "${BUILD_DIR}/proot-source-armhf"

# #######
# armel
# #######
prepare_proot_source "${BUILD_DIR}/proot-source-armel"
debian10_setup "armel"
debian10_build_proot "armel" "${BUILD_DIR}/proot-source-armel"

# #######
# aarch64
# #######
prepare_proot_source "${BUILD_DIR}/proot-source-aarch64"
prepare_patchelf_source_v2 "${BUILD_DIR}/patchelf-source-aarch64"
prepare_fakechroot_glibc_source "${BUILD_DIR}/fakechroot-source-glibc-aarch64"
prepare_runc_source "${BUILD_DIR}/runc-source-aarch64"
#
fedora31_setup "aarch64"
fedora31_build_proot "aarch64" "${BUILD_DIR}/proot-source-aarch64"
#fedora31_build_patchelf "aarch64" "${BUILD_DIR}/patchelf-source-aarch64"
#ostree_delete "aarch64" "fedora" "31"
#
fedora36_setup "aarch64"
fedora36_build_fakechroot "aarch64" "${BUILD_DIR}/fakechroot-source-glibc-aarch64"
#ostree_delete "aarch64" "fedora" "36"
#
fedora38_setup "aarch64"
fedora38_build_fakechroot "aarch64" "${BUILD_DIR}/fakechroot-source-glibc-aarch64"
#fedora38_build_patchelf "aarch64" "${BUILD_DIR}/patchelf-source-aarch64"
#ostree_delete "aarch64" "fedora" "38"
#
centos7_setup "aarch64"
centos7_build_fakechroot "aarch64" "${BUILD_DIR}/fakechroot-source-glibc-aarch64"
#ostree_delete "aarch64" "centos" "7"

#centos_stream8_setup "aarch64"
#centos_stream8_build_fakechroot "aarch64" "${BUILD_DIR}/fakechroot-source-glibc-aarch64"
#ostree_delete "aarch64" "centos" "8"
#
#centos_stream9_setup "aarch64"
#centos_stream9_build_fakechroot "aarch64" "${BUILD_DIR}/fakechroot-source-glibc-aarch64"
#ostree_delete "aarch64" "centos" "9"

alma8_setup "aarch64"
alma8_build_fakechroot "aarch64" "${BUILD_DIR}/fakechroot-source-glibc-aarch64"
#ostree_delete "aarch64" "alma" "8"
#
alma9_setup "aarch64"
alma9_build_fakechroot "aarch64" "${BUILD_DIR}/fakechroot-source-glibc-aarch64"
alma9_build_patchelf "aarch64" "${BUILD_DIR}/patchelf-source-aarch64"
#ostree_delete "aarch64" "alma" "9"

ubuntu16_setup "arm64"
ubuntu16_build_fakechroot "arm64" "${BUILD_DIR}/fakechroot-source-glibc-aarch64"
#ostree_delete "arm64" "ubuntu" "16"

ubuntu18_setup "arm64"
ubuntu18_build_fakechroot "arm64" "${BUILD_DIR}/fakechroot-source-glibc-aarch64"
#ostree_delete "arm64" "ubuntu" "18"

ubuntu20_setup "arm64"
ubuntu20_build_fakechroot "arm64" "${BUILD_DIR}/fakechroot-source-glibc-aarch64"
#ostree_delete "arm64" "ubuntu" "20"

ubuntu22_setup "arm64"
ubuntu22_build_fakechroot "arm64" "${BUILD_DIR}/fakechroot-source-glibc-aarch64"
#ubuntu22_build_runc "arm64" "${BUILD_DIR}/runc-source-aarch64"
ubuntu22_build_runc_root "arm64" "${BUILD_DIR}/runc-source-aarch64"
#ostree_delete "arm64" "ubuntu" "22"

# #######
# ppc64le
# #######
prepare_proot_source "${BUILD_DIR}/proot-source-ppc64le"
prepare_patchelf_source_v2 "${BUILD_DIR}/patchelf-source-ppc64le"
prepare_fakechroot_glibc_source "${BUILD_DIR}/fakechroot-source-glibc-ppc64le"
prepare_runc_source "${BUILD_DIR}/runc-source-ppc64le"
#
fedora38_setup "ppc64le"
fedora38_build_fakechroot "ppc64le" "${BUILD_DIR}/fakechroot-source-glibc-ppc64le"
#ostree_delete "ppc64le" "fedora" "38"
#
centos7_setup "ppc64le"
centos7_build_fakechroot "ppc64le" "${BUILD_DIR}/fakechroot-source-glibc-ppc64le"
#ostree_delete "ppc64le" "centos" "7"
#
alma8_setup "ppc64le"
alma8_build_fakechroot "ppc64le" "${BUILD_DIR}/fakechroot-source-glibc-ppc64le"
#ostree_delete "ppc64le" "alma" "8"
#
alma9_setup "ppc64le"
alma9_build_fakechroot "ppc64le" "${BUILD_DIR}/fakechroot-source-glibc-ppc64le"
alma9_build_patchelf "ppc64le" "${BUILD_DIR}/patchelf-source-ppc64le"
#ostree_delete "ppc64le" "alma" "9"

ubuntu16_setup "ppc64el"
ubuntu16_build_fakechroot "ppc64el" "${BUILD_DIR}/fakechroot-source-glibc-ppc64le"
#ostree_delete "ppc64el" "ubuntu" "16"

ubuntu18_setup "ppc64el"
ubuntu18_build_fakechroot "ppc64el" "${BUILD_DIR}/fakechroot-source-glibc-ppc64le"
#ostree_delete "ppc64el" "ubuntu" "18"

ubuntu20_setup "ppc64el"
ubuntu20_build_fakechroot "ppc64el" "${BUILD_DIR}/fakechroot-source-glibc-ppc64le"
#ostree_delete "ppc64el" "ubuntu" "20"

ubuntu22_setup "ppc64el"
ubuntu22_build_fakechroot "ppc64el" "${BUILD_DIR}/fakechroot-source-glibc-ppc64le"
#ubuntu22_build_runc "ppc64el" "${BUILD_DIR}/runc-source-ppc64le"
ubuntu22_build_runc_root "ppc64el" "${BUILD_DIR}/runc-source-ppc64le"
#ostree_delete "ppc64el" "ubuntu" "22"

# ###############################
# x86_64 Nix build uses Fedora 36
# ###############################
prepare_crun_source "${BUILD_DIR}/crun-source-x86_64"
nix_setup "x86_64"
nix_build_crun "x86_64" "${BUILD_DIR}/crun-source-x86_64"
#ostree_delete "x86_64" "fedora" "36"

#prepare_crun_source "${BUILD_DIR}/crun-source-ppc64le"
#nix_setup "ppc64le"
#nix_build_crun "ppc64le" "${BUILD_DIR}/crun-source-ppc64le"
#ostree_delete "ppc64le" "fedora" "36"

# #######
# package
# #######
#addto_package_simplejson
addto_package_other
addto_package_udocker
create_package_tarball

