#!/bin/bash

# ##################################################################
#
# Build binaries and create udocker tarball
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
    grep "^__version__" "$REPO_DIR/udocker.py" | cut '-d"' -f2
}

get_proot_static() 
{
    echo "get_proot_static"
    cd "$BUILD_DIR"

    if [ -d "$BUILD_DIR/proot-static-build" ] ; then
        echo "proot static already exists: $BUILD_DIR/proot-static-build"
        return
    fi

    git clone https://github.com/proot-me/proot-static-build 
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

    git clone https://github.com/proot-me/PRoot 
    /bin/mv PRoot "$PROOT_SOURCE_DIR"
}

patch_proot_source1()
{
    echo "patch_proot_source1 : $1"
    local PROOT_SOURCE_DIR="$1"

    cd "$PROOT_SOURCE_DIR/src"

    if [ -e "GNUmakefile.patch" ] ; then
        echo "patch proot source1 already applied: $PROOT_SOURCE_DIR/src/GNUmakefile"
        return
    fi

    cat > GNUmakefile.patch <<'EOF_GNUmakefile.patch'
--- PRoot/src/GNUmakefile	2016-11-28 12:24:12.000000000 +0000
+++ PRoot-static/src/GNUmakefile	2016-12-06 11:35:24.438382099 +0000
@@ -14,11 +14,11 @@
 OBJCOPY  = $(CROSS_COMPILE)objcopy
 OBJDUMP  = $(CROSS_COMPILE)objdump
 
-CPPFLAGS += -D_FILE_OFFSET_BITS=64 -D_GNU_SOURCE -I. -I$(VPATH)
-CFLAGS   += -Wall -Wextra -O2
-LDFLAGS  += -ltalloc
+CPPFLAGS += -D_FILE_OFFSET_BITS=64 -D_GNU_SOURCE -I. -I$(VPATH) 
+CFLAGS   += -Wall -Wextra -O2 
+LDFLAGS  += -L. -ltalloc -static 
 
-CARE_LDFLAGS = -larchive
+CARE_LDFLAGS = -larchive -static 
 
 OBJECTS += \
 	cli/cli.o		\
EOF_GNUmakefile.patch

    patch < GNUmakefile.patch
}

patch_proot_source2()
{
    echo "patch_proot_source2 : $1"
    local PROOT_SOURCE_DIR="$1"

    cd "$PROOT_SOURCE_DIR/src/tracee"

    if [ -e "event.patch" ] ; then
        echo "patch proot source2 already applied: $PROOT_SOURCE_DIR/src/tracee/event.patch"
        return
    fi

    cat > event.patch <<'EOF_event.patch'
--- PRoot/src/tracee/event.c	2017-02-10 23:04:47.000000000 +0000
+++ PROOT/PRoot-new/src/tracee/event.c	2017-02-12 21:27:37.592560666 +0000
@@ -20,6 +20,7 @@
  * 02110-1301 USA.
  */
 
+#include <stdio.h>
 #include <sched.h>      /* CLONE_*,  */
 #include <sys/types.h>  /* pid_t, */
 #include <sys/ptrace.h> /* ptrace(1), PTRACE_*, */
@@ -47,6 +48,7 @@
 #include "attribute.h"
 #include "compat.h"
 
+
 /**
  * Start @tracee->exe with the given @argv[].  This function
  * returns -errno if an error occurred, otherwise 0.
@@ -205,6 +207,27 @@
 static int last_exit_status = -1;
 
 /**
+ * Check if kernel >= 4.8
+ */
+bool is_kernel_4_8(void) {
+	struct utsname utsname;
+        int status;
+        static bool version_48 = false;
+        static int major = 0;
+        static int minor = 0;
+        if (! major) {
+		status = uname(&utsname);
+		if (status < 0)
+			return false;
+		sscanf(utsname.release, "%d.%d", &major, &minor);
+		if (major >= 4)
+			if (minor >= 8)
+				version_48 = true;
+	}
+	return version_48;
+}
+
+/**
  * Check if this instance of PRoot can *technically* handle @tracee.
  */
 static void check_architecture(Tracee *tracee)
@@ -362,6 +385,7 @@
 int handle_tracee_event(Tracee *tracee, int tracee_status)
 {
 	static bool seccomp_detected = false;
+        static bool seccomp_enabled = false;
 	pid_t pid = tracee->pid;
 	long status;
 	int signal;
@@ -432,6 +456,7 @@
 			status = ptrace(PTRACE_SETOPTIONS, tracee->pid, NULL,
 					default_ptrace_options | PTRACE_O_TRACESECCOMP);
 			if (status < 0) {
+				seccomp_enabled = false;
 				/* ... otherwise use default options only.  */
 				status = ptrace(PTRACE_SETOPTIONS, tracee->pid, NULL,
 						default_ptrace_options);
@@ -440,8 +465,71 @@
 					exit(EXIT_FAILURE);
 				}
 			}
+                        else { 
+				if (getenv("PROOT_NO_SECCOMP") == NULL)
+					seccomp_enabled = true;
+			}
 		}
 			/* Fall through. */
+		case SIGTRAP | PTRACE_EVENT_SECCOMP2 << 8:
+		case SIGTRAP | PTRACE_EVENT_SECCOMP << 8:
+
+			if (is_kernel_4_8()) { 
+	                	if (seccomp_enabled) {
+					if (!seccomp_detected) {
+						VERBOSE(tracee, 1, "ptrace acceleration (seccomp mode 2) enabled");
+						tracee->seccomp = ENABLED;
+						seccomp_detected = true;
+					}
+	
+					unsigned long flags = 0;
+					status = ptrace(PTRACE_GETEVENTMSG, tracee->pid, NULL, &flags);
+					if (status < 0)
+						break;
+           	             	}
+			}
+			else if (signal == (SIGTRAP | PTRACE_EVENT_SECCOMP2 << 8) ||
+                                 signal == (SIGTRAP | PTRACE_EVENT_SECCOMP << 8)) {
+				unsigned long flags = 0;
+
+				signal = 0;
+
+                	        if (!seccomp_detected) {
+                        	        VERBOSE(tracee, 1, "ptrace acceleration (seccomp mode 2) enabled");
+                                	tracee->seccomp = ENABLED;
+         	                	seccomp_detected = true;
+                	        }
+
+                        	/* Use the common ptrace flow if seccomp was
+				 * explicitely disabled for this tracee.  */
+        	                if (tracee->seccomp != ENABLED)
+                	                break;
+
+                        	status = ptrace(PTRACE_GETEVENTMSG, tracee->pid, NULL, &flags);
+                        	if (status < 0)
+                                	break;
+
+                        	/* Use the common ptrace flow when
+				 * sysexit has to be handled.  */
+                        	if ((flags & FILTER_SYSEXIT) != 0) {
+                                	tracee->restart_how = PTRACE_SYSCALL;
+                                	break;
+                        	}
+
+                        	/* Otherwise, handle the sysenter
+                        	 * stage right now.  */
+                        	tracee->restart_how = PTRACE_CONT;
+                        	translate_syscall(tracee);
+
+                        	/* This syscall has disabled seccomp, so move
+                        	 * the ptrace flow back to the common path to
+                       		 * ensure its sysexit will be handled.  */
+                        	if (tracee->seccomp == DISABLING)
+                                	tracee->restart_how = PTRACE_SYSCALL;
+                        	break;
+                	}
+
+			/* Fall through. */
 		case SIGTRAP | 0x80:
 			signal = 0;
 
@@ -458,17 +546,20 @@
 				if (IS_IN_SYSENTER(tracee)) {
 					/* sysenter: ensure the sysexit
 					 * stage will be hit under seccomp.  */
+				        VERBOSE(tracee, 1, "SYSENTER");
 					tracee->restart_how = PTRACE_SYSCALL;
 					tracee->sysexit_pending = true;
 				}
 				else {
 					/* sysexit: the next sysenter
 					 * will be notified by seccomp.  */
+				        VERBOSE(tracee, 1, "SYSEXIT");
 					tracee->restart_how = PTRACE_CONT;
 					tracee->sysexit_pending = false;
 				}
 				/* Fall through.  */
 			case DISABLED:
+				VERBOSE(tracee, 1, "TRANSLATE (in fall through)");
 				translate_syscall(tracee);
 
 				/* This syscall has disabled seccomp.  */
@@ -490,47 +581,6 @@
 			}
 			break;
 
-		case SIGTRAP | PTRACE_EVENT_SECCOMP2 << 8:
-		case SIGTRAP | PTRACE_EVENT_SECCOMP << 8: {
-			unsigned long flags = 0;
-
-			signal = 0;
-
-			if (!seccomp_detected) {
-				VERBOSE(tracee, 1, "ptrace acceleration (seccomp mode 2) enabled");
-				tracee->seccomp = ENABLED;
-				seccomp_detected = true;
-			}
-
-			/* Use the common ptrace flow if seccomp was
-			 * explicitely disabled for this tracee.  */
-			if (tracee->seccomp != ENABLED)
-				break;
-
-			status = ptrace(PTRACE_GETEVENTMSG, tracee->pid, NULL, &flags);
-			if (status < 0)
-				break;
-
-			/* Use the common ptrace flow when
-			 * sysexit has to be handled.  */
-			if ((flags & FILTER_SYSEXIT) != 0) {
-				tracee->restart_how = PTRACE_SYSCALL;
-				break;
-			}
-
-			/* Otherwise, handle the sysenter
-			 * stage right now.  */
-			tracee->restart_how = PTRACE_CONT;
-			translate_syscall(tracee);
-
-			/* This syscall has disabled seccomp, so move
-			 * the ptrace flow back to the common path to
-			 * ensure its sysexit will be handled.  */
-			if (tracee->seccomp == DISABLING)
-				tracee->restart_how = PTRACE_SYSCALL;
-			break;
-		}
-
 		case SIGTRAP | PTRACE_EVENT_VFORK << 8:
 			signal = 0;
 			(void) new_child(tracee, CLONE_VFORK);
EOF_event.patch

    patch < event.patch
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

    /bin/cp -f "${S_PROOT_DIR}/proot-x86"    "${PACKAGE_DIR}/udocker_dir/bin/"
    /bin/cp -f "${S_PROOT_DIR}/proot-x86_64" "${PACKAGE_DIR}/udocker_dir/bin/"
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

    git clone https://github.com/simplejson/simplejson.git --branch python2.2 
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

create_package_tarball()
{
    echo "create_package_tarball : $TARBALL_FILE"
    if [ ! -f "${BUILD_DIR}/proot-source-x86/src/proot" ] ; then
        echo "failed to compile : ${BUILD_DIR}/proot-source-x86/src/proot"
        return
    fi
    if [ ! -f "${BUILD_DIR}/proot-source-x86_64/src/proot" ] ; then
        echo "failed to compile : ${BUILD_DIR}/proot-source-x86_64/src/proot"
        return
    fi

    /bin/cp -f "${BUILD_DIR}/proot-source-x86/src/proot"  "${PACKAGE_DIR}/udocker_dir/bin/proot-x86-4_8_0"
    /bin/cp -f "${BUILD_DIR}/proot-source-x86_64/src/proot"  "${PACKAGE_DIR}/udocker_dir/bin/proot-x86_64-4_8_0"

    find "${PACKAGE_DIR}" -type d -exec /bin/chmod u=rwx,og=rx  {} \;
    find "${PACKAGE_DIR}" -type f -exec /bin/chmod u=+r+w,og=r  {} \;
    find "${PACKAGE_DIR}/udocker_dir/bin" -type f -exec /bin/chmod u=rwx,og=rx  {} \;
    /bin/chmod u=rwx,og=rx ${PACKAGE_DIR}/udocker
    /bin/chmod u=rwx,og=rx ${PACKAGE_DIR}/setup.py

    /bin/rm -f $TARBALL_FILE 2>&1 > /dev/null

    cd "$PACKAGE_DIR"
    tar --owner=root --group=root -czvf "$TARBALL_FILE" $(ls -A)
}

fedora25_create_dnf()
{
    echo "fedora25_create_dnf : $1"
    local FILENAME="$1"
    local ARCH="$2"

    cat > "$FILENAME" <<EOF_dnf
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

[fedora-source]
name=Fedora \$releasever - Source
failovermethod=priority
#baseurl=http://download.fedoraproject.org/pub/fedora/linux/releases/\$releasever/Everything/source/tree/
metalink=https://mirrors.fedoraproject.org/metalink?repo=fedora-source-\$releasever&arch=$ARCH
enabled=0
metadata_expire=7d
gpgcheck=0
gpgkey=file:///etc/pki/rpm-gpg/RPM-GPG-KEY-fedora-\$releasever-$ARCH
skip_if_unavailable=False
EOF_dnf
}


fedora25_build()
{
    echo "fedora25_build : $1"
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

    if [ -x "${PROOT_SOURCE_DIR}/src/proot" ] ; then
        echo "proot binary already compiled : ${PROOT_SOURCE_DIR}/src/proot"
        return
    fi

    export PROOT_NO_SECCOMP=1

    SUDO=sudo

    /bin/mkdir -p "${OS_ROOTDIR}/tmp"
    /bin/mkdir -p "${OS_ROOTDIR}/proot"
    /bin/mkdir -p "${OS_ROOTDIR}/proot-static-packages"
    /bin/mkdir -p "${OS_ROOTDIR}/etc/dnf"
    fedora25_create_dnf "${OS_ROOTDIR}/etc/dnf/dnf.conf" "$OS_ARCH"

    $SUDO /usr/bin/dnf -y -c "${OS_ROOTDIR}/etc/dnf/dnf.conf" \
        group install  --installroot="$OS_ROOTDIR" --releasever="$OS_RELVER" \
        Core 

    $SUDO /usr/bin/dnf -y -c "${OS_ROOTDIR}/etc/dnf/dnf.conf" \
        install  --installroot="$OS_ROOTDIR" --releasever="$OS_RELVER" \
        gcc kernel-devel make libtalloc libtalloc-devel glibc-static glibc-devel tar python

    $SUDO /bin/chown -R "$(id -u).$(id -g)" "$OS_ROOTDIR"
    $SUDO /bin/chmod -R u+rw "$OS_ROOTDIR"

    $PROOT -r "$OS_ROOTDIR" -b "${PROOT_SOURCE_DIR}:/proot" -w / -b /dev \
                           -b "${S_PROOT_PACKAGES_DIR}:/proot-static-packages"   /bin/bash <<'EOF_compile'
cd /proot
# BUILD TALLOC
tar xzvf /proot-static-packages/talloc-2.1.1.tar.gz
cd talloc-2.1.1
./configure
make
cp talloc.h /proot/src
cd bin/default
ar qf libtalloc.a talloc_3.o
cp libtalloc.a /proot/src
# BUILD PROOT
cd /proot/src
make
EOF_compile

}


# ##################################################################
# MAIN
# ##################################################################

utils_dir="$(dirname $(realpath $0))"
REPO_DIR="$(dirname $utils_dir)"

sanity_check

BUILD_DIR=/tmp/udocker-build
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

prepare_proot_source "${BUILD_DIR}/proot-source-x86"
patch_proot_source1 "${BUILD_DIR}/proot-source-x86"
patch_proot_source2 "${BUILD_DIR}/proot-source-x86"
fedora25_build "i386" "${BUILD_DIR}/proot-source-x86"

prepare_proot_source "${BUILD_DIR}/proot-source-x86_64"
patch_proot_source1 "${BUILD_DIR}/proot-source-x86_64"
patch_proot_source2 "${BUILD_DIR}/proot-source-x86_64"
fedora25_build "x86_64" "${BUILD_DIR}/proot-source-x86_64"

create_package_tarball

