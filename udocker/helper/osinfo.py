# -*- coding: utf-8 -*-
"""Information about the host or guest/container"""

import os
import re

from udocker.utils.uprocess import Uprocess
from udocker.utils.fileutil import FileUtil


class OSInfo(object):
    """Get os information from a directory tree"""

    _binarylist = ["/lib64/ld-linux-x86-64.so",
                   "/lib64/ld-linux-x86-64.so.2",
                   "/lib64/ld-linux-x86-64.so.3",
                   "/bin/bash", "/bin/sh", "/bin/zsh",
                   "/bin/csh", "/bin/tcsh", "/bin/ash",
                   "/bin/ls", "/bin/busybox",
                   "/system/bin/sh", "/system/bin/ls",
                   "/lib/ld-linux.so",
                   "/lib/ld-linux.so.2",
                  ]

    def __init__(self, root_dir):
        self._root_dir = root_dir

    def get_filetype(self, filename):
        """Get the file architecture"""
        filetype = ""
        if not filename.startswith(self._root_dir):
            filename = self._root_dir + '/' + filename
        if os.path.islink(filename):
            f_path = os.readlink(filename)
            if not f_path.startswith('/'):
                f_path = os.path.dirname(filename) + '/' + f_path
            return self.get_filetype(f_path)
        if os.path.isfile(filename):
            filetype = Uprocess().get_output(["file", filename])
            if not filetype:
                filetype = Uprocess().get_output(["readelf", "-h", filename])
        return filetype

    def arch(self):
        """Get guest system architecture"""
        for filename in OSInfo._binarylist:
            f_path = self._root_dir + filename
            filetype = self.get_filetype(f_path)
            if not filetype:
                continue
            if "x86-64" in filetype.lower():
                return "amd64"
            if "Intel 80386" in filetype:
                return "i386"
            if "aarch64" in filetype.lower():
                return "arm64"
            if " ARM" in filetype:
                return "arm"
        return ""

    def osdistribution(self):
        """Get guest operating system distribution"""
        for f_path in FileUtil(self._root_dir + "/etc/.+-release").match():
            if os.path.exists(f_path):
                osinfo = FileUtil(f_path).getdata('r')
                match = re.match(r"([^=]+) release (\d+)", osinfo)
                if match and match.group(1):
                    return (match.group(1).split(' ')[0],
                            match.group(2).split('.')[0])
        f_path = self._root_dir + "/etc/lsb-release"
        if os.path.exists(f_path):
            distribution = ""
            version = ""
            osinfo = FileUtil(f_path).getdata('r')
            match = re.search(r"DISTRIB_ID=(.+)(\n|$)",
                              osinfo, re.MULTILINE)
            if match:
                distribution = match.group(1).split(' ')[0]
            match = re.search(r"DISTRIB_RELEASE=(.+)(\n|$)",
                              osinfo, re.MULTILINE)
            if match:
                version = match.group(1).split('.')[0]
            if distribution and version:
                return (distribution, version)
        f_path = self._root_dir + "/etc/os-release"
        if os.path.exists(f_path):
            distribution = ""
            version = ""
            osinfo = FileUtil(f_path).getdata('r')
            match = re.search(r"NAME=\"?([^ \n\"\.]+).*\"?(\n|$)",
                              osinfo, re.MULTILINE)
            if match:
                distribution = match.group(1).split(' ')[0]
            match = re.search(r"VERSION_ID=\"?([^ \n\"\.]+).*\"?(\n|$)",
                              osinfo, re.MULTILINE)
            if match:
                version = match.group(1).split('.')[0]
            if distribution and version:
                return (distribution, version)
        return ("", "")

    def osversion(self):
        """Get guest operating system"""
        if self.osdistribution()[0]:
            return "linux"
        return ""
