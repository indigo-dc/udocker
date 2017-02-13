#!/bin/bash

# ##################################################################
#
# Build udocker-preng rpm package
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

patch_proot_source2()
{
    echo "patch_proot_source2"

    pushd "$TMP_DIR/$BASE_DIR/src/tracee"

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
    /bin/rm -Rf PRoot
    git clone https://github.com/proot-me/PRoot 
    /bin/mv PRoot $BASE_DIR
    patch_proot_source2
    tar czvf $SOURCE_TARBALL $BASE_DIR
    /bin/rm -Rf $BASE_DIR
    popd
}

create_specfile() 
{
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
Engine to provide chroot and mount like capabilities for containers execution in user mode within udocker using PRoot https://github.com/proot-me. PRoot is a user-space implementation of chroot, mount --bind, and binfmt_misc. Technically PRoot relies on ptrace, an unprivileged system-call available in every Linux kernel.

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
%defattr(-,root,root)

%doc README.rst AUTHORS COPYING

%changelog
* Tue Feb 14 2017 udocker maintainer <udocker@lip.pt> 1.0.2-1 
- Fix accelerated seccomp on kernels >= 4.8.0
* Mon Jan  9 2017 udocker maintainer <udocker@lip.pt> 1.0.1-1 
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
