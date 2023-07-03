# -*- coding: utf-8 -*-
"""Information about the host"""

import os
import re
import pwd
import platform

from udocker.genstr import is_genstr
from udocker.utils.uprocess import Uprocess
from udocker.helper.archinfo import ArchInfo


class HostInfo(ArchInfo):
    """Get information from the host system"""
    uid = os.getuid()
    gid = os.getgid()

    def username(self):
        """Get username"""
        try:
            return pwd.getpwuid(self.uid).pw_name
        except KeyError:
            return ""

    def arch(self, target="UDOCKER"):
        """Get the host system architecture"""
        machine = platform.machine()
        arch = self.get_arch("uname", machine, target)
        return arch[0] if arch[0] else ""

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

    def parse_platform(self, platform_in):
        """Convert a platform string or dict into (os, architecture, variant)"""
        if isinstance(platform_in, dict):
            p_os = ""
            p_architecture = ""
            p_variant = ""
            for (key, val) in platform_in.items():
                if key == "os":
                    p_os = val.lower()
                elif key == "architecture":
                    p_architecture = val.lower()
                elif key == "variant":
                    p_variant = val.lower()
            return (p_os, p_architecture, p_variant)
        if isinstance(platform_in, str):
            try:
                (p_os, p_architecture, p_variant) = platform_in.lower().split("/")
                return (p_os, p_architecture, p_variant)
            except ValueError:
                try:
                    (p_os, p_architecture) = platform_in.split("/")
                    return (p_os, p_architecture, "")
                except ValueError:
                    return (platform_in.strip(), "", "")
        return ("", "", "")

    def platform_to_str(self, platform_in):
        """Parse platform and return a string with os/architecture/variant"""
        parsed_platform = self.parse_platform(platform_in)
        if parsed_platform[2]:
            return "%s/%s/%s" % parsed_platform
        if parsed_platform[1]:
            return "%s/%s" % parsed_platform[0:2]
        return parsed_platform[0]

    def platform(self, return_str=True):
        """get docker platform os/architecture/variant"""
        architecture = self.arch("docker")
        host_platform = self.osversion() + "/" + architecture
        if return_str:
            return host_platform.lower()
        return self.parse_platform(host_platform)

    def is_same_platform(self, platform_in):
        """Compare some platform against the host platform"""
        if self.parse_platform(platform_in) == self.platform(return_str=False):
            return True
        return False

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
