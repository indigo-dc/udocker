# -*- coding: utf-8 -*-
"""ElfPatcher management and tools"""

import re
import os
import sys
import time

from udocker import is_genstr
from udocker.msg import Msg
from udocker.config import Config
from udocker.utils.uprocess import Uprocess
from udocker.utils.fileutil import FileUtil
from udocker.helper.hostinfo import HostInfo


class ElfPatcher(object):
    """Patch container executables"""

    BIN = 1
    LIB = 2
    LOADER = 4
    ABORT_ON_ERROR = 8
    ONE_SUCCESS = 16
    ONE_OUTPUT = 32

    def __init__(self, localrepo, container_id):
        self.localrepo = localrepo
        self._container_dir = \
            os.path.realpath(self.localrepo.cd_container(container_id))
        if not self._container_dir:
            raise ValueError("invalid container id")
        self._container_root = self._container_dir + "/ROOT"
        self._container_ld_so_path = self._container_dir + "/ld.so.path"
        self._container_ld_so_orig = self._container_dir + "/ld.so.orig"
        self._container_ld_libdirs = self._container_dir + "/ld.lib.dirs"
        self._container_patch_time = self._container_dir + "/patch.time"
        self._container_patch_path = self._container_dir + "/patch.path"
        self._shlib = re.compile(r"^lib\S+\.so(\.\d+)*$")
        self._uid = HostInfo.uid

    def select_patchelf(self):
        """Set patchelf executable"""
        arch = HostInfo().arch()
        image_list = []
        if arch == "amd64":
            image_list = ["patchelf-x86_64", "patchelf"]
        elif arch == "i386":
            image_list = ["patchelf-x86", "patchelf"]
        elif arch == "arm64":
            image_list = ["patchelf-arm64", "patchelf"]
        elif arch == "arm":
            image_list = ["patchelf-arm", "patchelf"]

        f_util = FileUtil(self.localrepo.bindir)
        patchelf_exec = f_util.find_file_in_dir(image_list)
        if not os.path.exists(patchelf_exec):
            Msg().err("Error: patchelf executable not found")
            sys.exit(1)

        return patchelf_exec

    def _replace(self, cmd, path):
        """Replace #f in cmd[] by path"""
        cmd_out = []
        for arg in cmd:
            if "#f" in arg:
                arg = arg.replace("#f", path)
            cmd_out.append(arg)
        return cmd_out

    def _walk_fs(self, cmd, root_path, action=BIN):
        """Execute a shell command over each executable file in a given
        dir_path, action can be ABORT_ON_ERROR, return upon first success
        ONE_SUCCESS, or return upon the first non empty output. #f is the
        placeholder for the filename.
        """
        status = ""
        for dir_path, dummy, files in os.walk(root_path):
            for f_name in files:
                try:
                    f_path = dir_path + '/' + f_name
                    if os.path.islink(f_path):
                        continue

                    if os.stat(f_path).st_uid != self._uid:
                        if action & self.ABORT_ON_ERROR:
                            return ""

                        continue

                    if ((action & self.BIN and os.access(f_path, os.X_OK)) or
                            (action & self.LIB and self._shlib.match(f_name))):
                        out = Uprocess().get_output(self._replace(cmd, f_path))
                        if out:
                            status = out

                    if action & self.ABORT_ON_ERROR and status is None:
                        return ""

                    if action & self.ONE_SUCCESS and status is not None:
                        return status

                    if action & self.ONE_OUTPUT and status:
                        return status

                except OSError:
                    pass

        return status

    def guess_elf_loader(self):
        """Search for executables and try to read the ld.so pathname"""
        patchelf_exec = self.select_patchelf()
        cmd = [patchelf_exec, "-q", "--print-interpreter", "#f"]
        for d_name in ("/bin", "/usr/bin", "/lib64"):
            elf_loader = self._walk_fs(cmd, self._container_root + d_name,
                                       self.ONE_OUTPUT | self.BIN)
            if elf_loader and ".so" in elf_loader:
                return elf_loader
        return ""

    def get_original_loader(self):
        """Get the pathname of the original ld.so"""
        if os.path.exists(self._container_ld_so_path):
            return FileUtil(self._container_ld_so_path).getdata('r').strip()
        elf_loader = self.guess_elf_loader()
        if elf_loader:
            FileUtil(self._container_ld_so_path).putdata(elf_loader, 'w')
        return elf_loader

    def get_container_loader(self):
        """Get an absolute pathname to the container ld.so"""
        elf_loader = self.get_original_loader()
        if not elf_loader:
            return ""
        elf_loader = self._container_root + "/" + elf_loader
        return elf_loader if os.path.exists(elf_loader) else ""

    def get_patch_last_path(self):
        """get last host pathname to the patched container"""
        last_path = FileUtil(self._container_patch_path).getdata('r')
        if last_path and is_genstr(last_path):
            return last_path.strip()
        return ""

    def check_container_path(self):
        """verify if path to container is ok"""
        last_path = self.get_patch_last_path()
        if last_path and last_path != self._container_dir:
            return False
        return True

    def get_patch_last_time(self):
        """get time in seconds of last full patch of container"""
        last_time = FileUtil(self._container_patch_time).getdata('r').strip()
        try:
            return str(int(last_time))
        except ValueError:
            return "0"

    def patch_binaries(self):
        """Set all executables and libs to the ld.so absolute pathname"""
        if not self.check_container_path():
            self.restore_binaries()
        last_time = '0'
        patchelf_exec = self.select_patchelf()
        elf_loader = self.get_container_loader()
        cmd = [patchelf_exec, "--set-root-prefix", self._container_root, "#f"]
        self._walk_fs(cmd, self._container_root, self.BIN | self.LIB)
        newly_set = self.guess_elf_loader()
        if newly_set == elf_loader:
            try:
                last_time = str(int(time.time()))
            except ValueError:
                pass
            futil_time = FileUtil(self._container_patch_time)
            futil_path = FileUtil(self._container_patch_path)
            return (futil_time.putdata(last_time, 'w') and
                    futil_path.putdata(self._container_dir, 'w'))
        return False

    def restore_binaries(self):
        """Restore all executables and libs to the original ld.so pathname"""
        patchelf_exec = self.select_patchelf()
        elf_loader = self.get_original_loader()
        last_path = self.get_patch_last_path()
        if last_path:
            cmd = [patchelf_exec, "--restore-root-prefix",
                   last_path + "/ROOT", "#f"]
        else:
            cmd = [patchelf_exec, "--restore-root-prefix",
                   self._container_root, "#f"]
        self._walk_fs(cmd, self._container_root, self.BIN | self.LIB)
        newly_set = self.guess_elf_loader()
        if newly_set == elf_loader:
            FileUtil(self._container_patch_path).remove()
            FileUtil(self._container_patch_time).remove()
        return newly_set == elf_loader

    def patch_ld(self, output_elf=None):
        """Patch ld.so"""
        elf_loader = self.get_container_loader()
        if FileUtil(self._container_ld_so_orig).size() == -1:
            status = FileUtil(elf_loader).copyto(self._container_ld_so_orig)
            if not status:
                return False

        ld_data = FileUtil(self._container_ld_so_orig).getdata('rb')
        if not ld_data:
            ld_data = FileUtil(elf_loader).getdata('rb')
            if not ld_data:
                return False

        nul_etc = "\x00/\x00\x00\x00\x00\x00\x00\x00\x00\x00".encode()
        nul_lib = "\x00/\x00\x00\x00".encode()
        nul_usr = "\x00/\x00\x00\x00".encode()
        etc = "\x00/etc/ld.so".encode()
        lib = "\x00/lib".encode()
        usr = "\x00/usr".encode()
        ld_data = ld_data.replace(etc, nul_etc).\
            replace(lib, nul_lib).replace(usr, nul_usr)
        ld_library_path_orig = "\x00LD_LIBRARY_PATH\x00".encode()
        ld_library_path_new = "\x00LD_LIBRARY_REAL\x00".encode()
        ld_data = ld_data.replace(ld_library_path_orig, ld_library_path_new)
        if output_elf is None:
            return bool(FileUtil(elf_loader).putdata(ld_data, 'wb'))

        return bool(FileUtil(output_elf).putdata(ld_data, 'wb'))

    def restore_ld(self):
        """Restore ld.so"""
        elf_loader = self.get_container_loader()
        futil_ldso = FileUtil(self._container_ld_so_orig)
        if futil_ldso.size() <= 0:
            Msg().err("Error: original loader not found or empty")
            return False

        if not futil_ldso.copyto(elf_loader):
            Msg().err("Error: in loader copy or file locked by other process")
            return False

        return True

    def _get_ld_config(self):
        """Get get directories from container ld.so.cache"""
        cmd = ["ldconfig", "-p", "-C",
               f"{self._container_root}/{Config.conf['ld_so_cache']}", ]
        ld_dict = {}
        ld_data = Uprocess().get_output(cmd)
        if not ld_data:
            return []
        for line in ld_data.split('\n'):
            match = re.search("([^ ]+) => ([^ ]+)", line)
            if match:
                ld_dict[self._container_root + \
                        os.path.dirname(match.group(2))] = True
        return list(ld_dict.keys())

    # pylint: disable=too-many-nested-blocks
    def _find_ld_libdirs(self, root_path=None):
        """search for library directories in container"""
        if root_path is None:
            root_path = self._container_root
        ld_list = []
        for dir_path, dummy, files in os.walk(root_path):
            for f_name in files:
                try:
                    f_path = dir_path + '/' + f_name
                    if not os.access(f_path, os.R_OK):
                        continue
                    if os.path.isfile(f_path):
                        if self._shlib.match(f_name):
                            if dir_path not in ld_list:
                                ld_list.append(dir_path)
                except OSError:
                    continue
        return ld_list

    def get_ld_libdirs(self, force=False):
        """Get ld library paths"""
        if force or not os.path.exists(self._container_ld_libdirs):
            ld_list = self._find_ld_libdirs()
            ld_str = ':'.join(ld_list)
            FileUtil(self._container_ld_libdirs).putdata(ld_str, 'w')
            return ld_list
        ld_str = FileUtil(self._container_ld_libdirs).getdata('r')
        return ld_str.split(':')

    def get_ld_library_path(self):
        """Get ld library paths"""
        ld_list = self._get_ld_config()
        ld_list.extend(self.get_ld_libdirs())
        for ld_dir in Config.conf['lib_dirs_list_essential']:
            ld_dir = self._container_root + '/' + ld_dir
            if ld_dir not in ld_list:
                ld_list.insert(0, ld_dir)
        ld_list.extend(Config.conf['lib_dirs_list_append'])
        return ':'.join(ld_list)
