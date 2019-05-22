# -*- coding: utf-8 -*-
"""Information about the guest/container"""

import os
import re
from udocker.utils.uprocess import Uprocess
from udocker.utils.fileutil import FileUtil


class GuestInfo(object):
    """Get os information from a directory tree"""

    def __init__(self, conf, root_dir):
        self.conf = conf
        self.root_dir = root_dir
        self.binarylist = ["/lib64/ld-linux-x86-64.so",
                           "/lib64/ld-linux-x86-64.so.2",
                           "/lib64/ld-linux-x86-64.so.3",
                           "/lib/ld-linux.so.2", "/lib/ld-linux.so",
                           "/bin/sh", "/bin/bash", "/bin/zsh", "/bin/csh",
                           "/bin/tcsh", "/bin/ls", "/bin/busybox",
                           "/system/bin/sh", "/system/bin/ls"]

    def get_filetype(self, filename):
        """Get the file architecture"""
        if not filename.startswith(self.root_dir):
            filename = self.root_dir + "/" + filename
        if os.path.islink(filename):
            f_path = os.readlink(filename)
            if not f_path.startswith("/"):
                f_path = os.path.dirname(filename) + "/" + f_path
            return self.get_filetype(f_path)
        if os.path.isfile(filename):
            cmd = "file %s" % (filename)
            return Uprocess().get_output(cmd)
        return ""

    def arch(self):
        """Get guest system architecture"""
        for filename in self.binarylist:
            f_path = self.root_dir + filename
            filetype = self.get_filetype(f_path)
            if not filetype:
                continue
            if "x86-64," in filetype:
                return "amd64"
            if "80386," in filetype:
                return "i386"
            if "ARM," in filetype:
                if "64-bit" in filetype:
                    return "arm64"
                else:
                    return "arm"
        return ""

    def osdistribution(self):
        """Get guest operating system distribution"""
        for f_path in FileUtil(self.conf, self.root_dir + "/etc/.+-release").match():
            if os.path.exists(f_path):
                osinfo = FileUtil(self.conf, f_path).getdata()
                match = re.match(r"([^=]+) release (\d+)", osinfo)
                if match and match.group(1):
                    return (match.group(1).split(" ")[0],
                            match.group(2).split(".")[0])
        f_path = self.root_dir + "/etc/lsb-release"
        if os.path.exists(f_path):
            distribution = ""
            version = ""
            osinfo = FileUtil(self.conf, f_path).getdata()
            match = re.search(r"DISTRIB_ID=(.+)(\n|$)",
                              osinfo, re.MULTILINE)
            if match:
                distribution = match.group(1).split(" ")[0]
            match = re.search(r"DISTRIB_RELEASE=(.+)(\n|$)",
                              osinfo, re.MULTILINE)
            if match:
                version = match.group(1).split("=")[0]
            if distribution and version:
                return (distribution, version)
        f_path = self.root_dir + "/etc/os-release"
        if os.path.exists(f_path):
            distribution = ""
            version = ""
            osinfo = FileUtil(self.conf, f_path).getdata()
            match = re.search(r"NAME=\"?(.+)\"?(\n|$)",
                              osinfo, re.MULTILINE)
            if match:
                distribution = match.group(1).split(" ")[0]
            match = re.search(r"VERSION_ID=\"?(.+)\"?(\n|$)",
                              osinfo, re.MULTILINE)
            if match:
                version = match.group(1).split(".")[0]
            if distribution and version:
                return (distribution, version)
        return ("", "")

    def osversion(self):
        """Get guest operating system"""
        if self.osdistribution()[0]:
            return "linux"
        return ""
