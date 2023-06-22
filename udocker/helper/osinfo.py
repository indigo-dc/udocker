# -*- coding: utf-8 -*-
"""Information about the host or guest/container"""

import os
import re

from udocker.utils.uprocess import Uprocess
from udocker.utils.fileutil import FileUtil
from udocker.helper.archinfo import ArchInfo

class OSInfo(ArchInfo):
    """Get os information"""

    def __init__(self, root_dir):
        self._root_dir = root_dir

    # ARCH NEW
    def get_filetype(self, filename):
        """Get architecture information from binary using file and readelf"""
        if not filename.startswith(self._root_dir):
            filename = self._root_dir + '/' + filename
        if os.path.islink(filename):
            f_path = os.readlink(filename)
            if not f_path.startswith('/'):
                f_path = os.path.dirname(filename) + '/' + f_path
            return self.get_filetype(f_path)
        if os.path.isfile(filename):
            filetype = Uprocess().get_output(["file", filename])
            if filetype and ":" in filetype:
                return ("file", filetype.split(":", 1)[1])
            filetype = Uprocess().get_output(["readelf", "-h", filename])
            if filetype:
                return ("readelf", filetype)
        return ("", "")

    # ARCH NEW
    def arch(self, target="UDOCKER"):
        """Get OS architecture"""
        for filename in self.get_binaries_list():
            f_path = self._root_dir + "/" + filename
            (sourcetype, fileinfo) = self.get_filetype(f_path)
            if not sourcetype:
                continue

            (arch, dummy, dummy) = self.get_arch(sourcetype, fileinfo, target)
            return arch[0] if arch[0] else ""

    # ARCH NEW
    def is_same_arch(self, other_root_dir="/" ,target="UDOCKER"):
        """Compare architectures for two system trees"""
        this_arch = self.arch(target)
        other_arch = OSInfo(other_root_dir).arch(target)
        if not (this_arch and other_arch):
            return None
        return this_arch == other_arch

    def osdistribution(self):
        """Get guest operating system distribution"""
        for f_path in FileUtil(self._root_dir + "/etc/.+-release").match():
            if os.path.exists(f_path):
                osinfo = FileUtil(f_path).getdata('r')
                match = re.match(r"([^=]+) release (\d+)", osinfo)
                if match and match.group(1):
                    return (match.group(1).split(' ')[0], match.group(2).split('.')[0])
        f_path = self._root_dir + "/etc/lsb-release"
        if os.path.exists(f_path):
            distribution = ""
            version = ""
            osinfo = FileUtil(f_path).getdata('r')
            match = re.search(r"DISTRIB_ID=(.+)(\n|$)", osinfo, re.MULTILINE)
            if match:
                distribution = match.group(1).split(' ')[0]

            match = re.search(r"DISTRIB_RELEASE=(.+)(\n|$)", osinfo, re.MULTILINE)
            if match:
                version = match.group(1).split('.')[0]

            if distribution and version:
                return (distribution, version)

        f_path = self._root_dir + "/etc/os-release"
        if os.path.exists(f_path):
            distribution = ""
            version = ""
            osinfo = FileUtil(f_path).getdata('r')
            match = re.search(r"NAME=\"?([^ \n\"\.]+).*\"?(\n|$)", osinfo, re.MULTILINE)
            if match:
                distribution = match.group(1).split(' ')[0]

            match = re.search(r"VERSION_ID=\"?([^ \n\"\.]+).*\"?(\n|$)", osinfo, re.MULTILINE)
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
