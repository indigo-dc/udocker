# -*- coding: utf-8 -*-
"""Information about the host"""

import os
import re
import pwd
import platform

from udocker import is_genstr
from udocker.utils.uprocess import Uprocess

class HostInfo(object):
    """Get information from the host system"""

    uid = os.getuid()
    gid = os.getgid()

    def username(self):
        """Get username"""
        try:
            return pwd.getpwuid(self.uid).pw_name
        except KeyError:
            return ""

    def arch(self):
        """Get the host system architecture"""
        arch = ""
        try:
            machine = platform.machine()
            bits = platform.architecture()[0]
            if machine == "x86_64":
                if bits == "32bit":
                    arch = "i386"
                else:
                    arch = "amd64"
            elif machine in ("i386", "i486", "i586", "i686"):
                arch = "i386"
            elif machine.startswith("arm") or machine.startswith("aarch"):
                if bits == "32bit":
                    arch = "arm"
                else:
                    arch = "arm64"
        except (NameError, AttributeError):
            pass
        return arch

    def osversion(self):
        """Get operating system"""
        try:
            return platform.system().lower()
        except (NameError, AttributeError):
            return ""

    def oskernel(self):
        """Get operating system"""
        try:
            return platform.release()
        except (NameError, AttributeError):
            return "6.1.1"

    def oskernel_isgreater(self, version):
        """Compare kernel version is greater or equal than ref_version
        version: list [int, int, int]
        """
        match = re.search(r"([0-9.]+)", self.oskernel())
        if match:
            os_release = match.group(1)
        else:
            return True

        for (idx, os_version) in enumerate(os_release.split('.')):
            if idx >= len(version):
                break
            if int(os_version) > int(version[idx]):
                return True
            if int(os_version) < int(version[idx]):
                return False

        return True

    def cmd_has_option(self, executable, search_option, arg=None):
        """Check if executable has a given cli option"""
        if not executable:
            return False
        arg_list = []
        if arg and is_genstr(arg):
            arg_list = [arg]
        elif isinstance(arg, list):
            arg_list = arg
        out = Uprocess().get_output([executable] + arg_list + ["--help"])
        if out and search_option in re.split(r"[=|\*\[\]\n,; ]+", out):
            return True
        return False

    def termsize(self):
        """Get guest operating system terminal size"""
        try:
            with open("/dev/tty") as tty:
                cmd = ['stty', 'size']
                lines, cols = Uprocess().check_output(cmd, stdin=tty).split()
                return (int(lines), int(cols))
        except (OSError, IOError):
            pass
        return (24, 80)
