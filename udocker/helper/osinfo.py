# -*- coding: utf-8 -*-
"""Information about the host or guest/container"""

import os
import re
import json

from udocker.utils.uprocess import Uprocess
from udocker.utils.fileutil import FileUtil
from udocker.helper.archinfo import ArchInfo


class OSInfo(ArchInfo):
    """Get os information"""

    def __init__(self, root_dir):
        self._root_dir = root_dir

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
            filetype = Uprocess().get_output(["readelf", "-h", filename])
            if filetype:
                return ("readelf", filetype)
            filetype = Uprocess().get_output(["file", filename])
            if filetype and ":" in filetype:
                return ("file", filetype.split(":", 1)[1])
        return ("", "")

    def is_binary_executable(self, filename):
        """Check if file is a binary executable"""
        filename = self._root_dir + '/' + filename
        if not FileUtil(filename).isexecutable():
            return False
        (sourcetype, filetype) = self.get_filetype(filename)
        if sourcetype:
            if ("ELF" in filetype and "rror" not in filetype):
                return True
        else:
            elf_pattern = "\x7fELF".encode()
            bin_head = FileUtil(filename).getdata('rb', 4)
            if elf_pattern == bin_head[0:4]:
                return True
        return False

    def arch_from_binaries(self, target="UDOCKER"):
        """Get OS architecture from binaries"""
        for filename in self.get_binaries_list():
            f_path = self._root_dir + "/" + filename
            (sourcetype, fileinfo) = self.get_filetype(f_path)
            if not sourcetype:
                continue

            arch = self.get_arch(sourcetype, fileinfo, target)
            try:
                return arch[0]
            except IndexError:
                continue
        return ""

    def _load_config_json(self):
        """Load metadata form json config file"""
        for filename in ("container.json", "config.json"):
            f_path = self._root_dir + "/../" + filename
            try:
                with open(f_path, 'r') as infile:
                    json_obj = json.load(infile)
                    return json_obj
            except (IOError, OSError, AttributeError,
                    ValueError, TypeError):
                continue
        return None

    def arch_from_metadata(self, target="UDOCKER"):
        """Get OS architecture from container metadata"""
        config_json = self._load_config_json()
        if not config_json:
            return ""
        try:
            architecture = config_json['architecture']
            if not architecture:
                return ""
            arch_var = architecture
        except KeyError:
            return ""
        try:
            variant = config_json['variant']
            if variant:
                arch_var = architecture + "/" + variant
        except KeyError:
            pass
        arch = self.get_arch("arch/var", arch_var, target)
        try:
            return arch[0]
        except IndexError:
            return ""

    def arch(self, target="UDOCKER"):
        """Get container / directory tree arechitecture"""
        architecture = self.arch_from_metadata(target)
        if not architecture:
            architecture = self.arch_from_binaries(target)
        return architecture

    def is_same_arch(self, other_root_dir="/", target="UDOCKER"):
        """Compare architectures for two system trees"""
        this_arch = self.arch(target)
        other_arch = OSInfo(other_root_dir).arch(target)
        if not (this_arch and other_arch):
            return None
        return this_arch == other_arch

    def _osdistribution(self):
        """Get guest operating system distribution"""
        for f_path in FileUtil(self._root_dir + "/etc/.+-release").match():
            if os.path.exists(f_path):
                osinfo = FileUtil(f_path).getdata('r')
                match = re.match(r"([^=]+) release (\d+)", osinfo)
                if match and match.group(1):
                    return (match.group(1).split(' ')[0], match.group(2))

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
                version = match.group(1)

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

            match = re.search(r"VERSION_ID=\"?([^ \n\"]+).*\"?(\n|$)", osinfo, re.MULTILINE)
            if match:
                version = match.group(1)

            if distribution and version:
                return (distribution, version)

        return ("", "")

    def osdistribution(self):
        """Get guest operating system distribution"""
        (distribution, version) = self._osdistribution()
        if version.count(".") >= 2:
            version = ".".join(version.split(".")[0:2])
        else:
            version = version.split(".")[0]
        return(distribution, version)

    def osversion(self):
        """Get guest operating system"""
        if self.osdistribution()[0]:
            return "linux"
        return ""
