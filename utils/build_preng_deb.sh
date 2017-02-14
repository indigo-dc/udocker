#!/bin/bash

# ##################################################################
#
# Build udocker-preng debian package
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
    mkdir -p "$BUILD_DIR/udocker-preng-${VERSION}/debian/source"
}

udocker_version()
{
    grep "^__version__" "$REPO_DIR/udocker.py" | cut '-d"' -f2 
}

patch_proot_source2()
{
    echo "patch_proot_source2"

    pushd "$TMP_DIR/${BASE_DIR}-${VERSION}/src/tracee"

    if [ -e "event.patch" ] ; then
        echo "patch proot source2 already applied: $PWD/event.patch"
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
    popd
}

create_source_tarball()
{
    /bin/rm $SOURCE_TARBALL 2> /dev/null
    pushd $TMP_DIR
    /bin/rm -Rf PRoot ${BASE_DIR}-${VERSION}
    git clone https://github.com/proot-me/PRoot
    /bin/mv PRoot ${BASE_DIR}-${VERSION}
    patch_proot_source2
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
README.rst
AUTHORS
M_DOCS
}

create_changelog()
{
    cat - > $DEB_CHANGELOG_FILE <<M_CHANGELOG
udocker-preng (1.0.2-1) trusty; urgency=low

  * Fix accelerated seccomp on kernels >= 4.8.0

 -- $DEBFULLNAME <$DEBEMAIL>  Tue, 14 Feb 2017 22:38:38 +0000

udocker-preng (1.0.1-1) trusty; urgency=low

  * Initial debian package

 -- $DEBFULLNAME <$DEBEMAIL>  Fri, 27 Jan 2017 22:15:39 +0000
M_CHANGELOG
}

create_copyright()
{
    cat - > $DEB_COPYRIGHT_FILE <<'M_COPYRIGHT'
Format: http://www.debian.org/doc/packaging-manuals/copyright-format/1.0/
Upstream-Name: proot
Source: http://proot.me

Files: *
Copyright: 2013, Cédric VINCENT <cedric.vincent@st.com>
           2013, Rémi DURAFFORT <remi.duraffort@st.com>
           2013, Yves JANIN <yves.janin@st.com>
           2013, Claire ROBINE <claire.robine@st.com>
           2013, Clément BAZIN <clement@bazin-fr.org>
           2013, Christophe GUILLON <christophe.guillon@st.com>
           2013, Christian BERTIN <christian.bertin@st.com>
           2013, Denis FERRANTI <denis.ferranti@st.com>
           2013, Paul GHALEB <paul.ghaleb@st.com>
           2013, STMicroelectronics
License: GPL-2+

Files: debian/*
Copyright: 2017, udocker maintainer <udocker@lip.pt>
License: GPL-2+

License: GPL-2+
 This package is free software; you can redistribute it and/or modify
 it under the terms of the GNU General Public License as published by
 the Free Software Foundation; either version 2 of the License, or
 (at your option) any later version.
 .
 This package is distributed in the hope that it will be useful,
 but WITHOUT ANY WARRANTY; without even the implied warranty of
 MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 GNU General Public License for more details.
 .
 You should have received a copy of the GNU General Public License
 along with this program. If not, see <http://www.gnu.org/licenses/>
 .
 On Debian systems, the complete text of the GNU General
 Public License version 2 can be found in "/usr/share/common-licenses/GPL-2".
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
	dh $@ --sourcedirectory=src

.ONESHELL:
override_dh_auto_install:
	if [ "$$DEB_TARGET_ARCH" = "amd64" ]; then 
	    PROOT="proot-x86_64"
	elif [ "$$DEB_TARGET_ARCH" = "i386" ]; then
	    PROOT="proot-i386"
	elif [ "$$DEB_TARGET_ARCH" = "arm64" ]; then
	    PROOT="proot-arm64"
	elif [ "$${DEB_TARGET_ARCH:0:3}" = "arm" ]; then
	    PROOT="proot-arm"
	else
	    PROOT="proot"
	fi
	install -g 0 -o 0 -m 755 -D src/proot debian/udocker-preng/usr/lib/udocker/$$PROOT
M_RULES
}

create_control() 
{
    cat - > $DEB_CONTROL_FILE <<M_CONTROL
Source: udocker-preng
Section: utils
Priority: optional
Maintainer: udocker maintainer <udocker@lip.pt>
Build-Depends: debhelper (>= 9.0.0), libtalloc-dev
Standards-Version: 3.9.7
Homepage: https://www.gitbook.com/book/indigo-dc/udocker/details

Package: udocker-preng
Architecture: any
Depends: \${shlibs:Depends}, \${misc:Depends}, udocker (>=$VERSION)
Description: udocker proot engine for containers execution
 Engine to provide chroot and mount like capabilities for containers
 execution in user mode within udocker using PRoot https://github.com/proot-me.
 .
 PRoot is a user-space implementation of chroot, mount --bind,
 and binfmt_misc.
 .
 Technically PRoot relies on ptrace, an unprivileged system-call available in
 every Linux kernel.

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
BASE_DIR="udocker-preng"
VERSION="$(udocker_version)"

TMP_DIR="/tmp"
BUILD_DIR="${HOME}/debuild"
SOURCE_TARBALL="${BUILD_DIR}/udocker-preng_${VERSION}.orig.tar.gz"

DEB_CONTROL_FILE="${BUILD_DIR}/udocker-preng-${VERSION}/debian/control"
DEB_CHANGELOG_FILE="${BUILD_DIR}/udocker-preng-${VERSION}/debian/changelog"
DEB_COMPAT_FILE="${BUILD_DIR}/udocker-preng-${VERSION}/debian/compat"
DEB_COPYRIGHT_FILE="${BUILD_DIR}/udocker-preng-${VERSION}/debian/copyright"
DEB_DOCS_FILE="${BUILD_DIR}/udocker-preng-${VERSION}/debian/docs"
DEB_RULES_FILE="${BUILD_DIR}/udocker-preng-${VERSION}/debian/rules"
DEB_SOURCE_DIR="${BUILD_DIR}/udocker-preng-${VERSION}/debian/source"
DEB_FORMAT_FILE="${BUILD_DIR}/udocker-preng-${VERSION}/debian/source/format"
DEB_INSTALL_FILE="${BUILD_DIR}/udocker-preng-${VERSION}/debian/install"

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
pushd "${BUILD_DIR}/udocker-preng-${VERSION}/debian"
ls -l
debuild
