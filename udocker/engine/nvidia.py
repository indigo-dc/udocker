# -*- coding: utf-8 -*-
import os
import stat
import glob
import re

from udocker.msg import Msg
from udocker.utils.fileutil import FileUtil
from udocker.config import Config
from udocker.utils.uprocess import Uprocess


class NvidiaMode(object):
    """nvidia-docker like functionality for udocker.
    Make nvidia host libraries available within udocker, this is achieved
    by copy them into the container so that the execution modes that need
    to change libraries may work properly.
    """

    def __init__(self, localrepo, container_id):
        self.localrepo = localrepo               # LocalRepository object
        self.container_id = container_id         # Container id
        self.container_dir = self.localrepo.cd_container(container_id)
        if not self.container_dir:
            raise ValueError("invalid container id")
        self.container_root = self.container_dir + "/ROOT"
        self._container_nvidia_set = self.container_dir + "/nvidia"

    def _files_exist(self, cont_dst_dir, files_list):
        """Verify if files already exists"""
        for fname in files_list:
            dstname = self.container_root + '/' + cont_dst_dir + '/' + fname
            if os.path.exists(dstname):
                raise OSError("file already exists", dstname)

    def _copy_files(self, host_src_dir, cont_dst_dir, files_list, force=False):
        """copy or link file to destination creating directories as needed"""
        for fname in files_list:
            srcname = host_src_dir + '/' + fname
            dstname = self.container_root + '/' + cont_dst_dir + '/' + fname
            if os.path.isfile(dstname) or os.path.islink(dstname):
                if force:
                    try:
                        os.remove(dstname)
                    except OSError:
                        Msg().err("Error: deleting nvidia file", dstname)
                else:
                    Msg().err("Error: nvidia file already exists", dstname,
                              ", use --force to overwrite")
                    return
            if os.path.isfile(srcname):
                srcdir = os.path.dirname(srcname)
                dstdir = os.path.dirname(dstname)
                if not os.path.isdir(dstdir):
                    try:
                        os.makedirs(dstdir)
                        os.chmod(dstdir, stat.S_IMODE(os.stat(srcdir).st_mode) |
                                 stat.S_IRWXU)
                    except OSError:
                        Msg().err("Error: creating nvidia dir", dstdir)
                if not FileUtil(srcname).copyto(dstname):
                    Msg().err("Error: copying file", srcname, "to", dstname)
                    return
                try:
                    mask = stat.S_IMODE(os.stat(srcname).st_mode) | \
                                        stat.S_IWUSR | stat.S_IRUSR
                    if os.access(srcname, os.X_OK):
                        mask = mask | stat.S_IXUSR
                    os.chmod(dstname, mask)
                except (IOError, OSError) as error:
                    Msg().err("Error: change mask of nvidia file", error)
                Msg().err("nvidia copied", srcname, "to", dstname, l=Msg.DBG)

    def _get_nvidia_libs(self, host_dir):
        """Expand the library files to include the versions"""
        lib_list = []
        for lib in Config.nvi_lib_list:
            for expanded_libs in glob.glob(host_dir + '/' + lib + '*'):
                lib_list.append(expanded_libs.replace(host_dir, ''))
        return lib_list

    def _find_host_dir(self):
        """Find the location of the host nvidia libraries"""
        dir_list = set()
        ld_library_path = os.getenv("LD_LIBRARY_PATH")
        if ld_library_path:
            for libdir in ld_library_path.split(':'):
                if glob.glob(libdir + '/libnvidia-cfg.so*'):
                    dir_list.add(libdir + '/')
                if glob.glob(libdir + '/libcuda.so*'):
                    dir_list.add(libdir + '/')
        ld_data = Uprocess().get_output("ldconfig -p")
        if not ld_data:
            return ""
        for line in ld_data.split("\n"):
            match = re.search("[ |\t]libnvidia-cfg.so[^ ]* .*x86-64.*=> (/.*)", line)
            if match:
                dir_list.add(os.path.dirname(match.group(1)) + '/')
            match = re.search("[ |\t]libcuda.so[^ ]* .*x86-64.*=> (/.*)", line)
            if match:
                dir_list.add(os.path.dirname(match.group(1)) + '/')
        return dir_list

    def _find_cont_dir(self):
        """Find the location of the host target directory for libraries"""
        for dst_dir in ('/usr/lib/x86_64-linux-gnu', '/usr/lib64'):
            if os.path.isdir(self.container_root + "/" + dst_dir):
                return dst_dir
        return ""

    def _installation_exists(self, nvi_host_dir_list, nvi_cont_dir):
        """Container has files from previous nvidia installation"""
        try:
            for nvi_host_dir in nvi_host_dir_list:
                lib_list = self._get_nvidia_libs(nvi_host_dir)
                self._files_exist(nvi_cont_dir, lib_list)
            self._files_exist('/etc', Config.nvi_etc_list)
            self._files_exist('/usr/bin', Config.nvi_bin_list)
        except OSError:
            return True
        return False

    def set_mode(self, force=False):
        """Set nvidia mode"""
        if not self.container_dir:
            Msg().err("Error: nvidia set mode container dir not found")
            return
        nvi_host_dir_list = self._find_host_dir()
        nvi_cont_dir = self._find_cont_dir()
        if not nvi_host_dir_list:
            Msg().err("Error: host nvidia libraries not found")
            return
        if not nvi_cont_dir:
            Msg().err("Error: destination directory for nvidia libs not found")
            return
        if (not force) and self._installation_exists(nvi_host_dir_list, nvi_cont_dir):
            Msg().err("Error: nvidia installation already exists"
                      ", use --force to overwrite")
            return
        for nvi_host_dir in nvi_host_dir_list:
            lib_list = self._get_nvidia_libs(nvi_host_dir)
            self._copy_files(nvi_host_dir, nvi_cont_dir, lib_list, force)
        self._copy_files('/etc', '/etc', Config.nvi_etc_list, force)
        self._copy_files('/usr/bin', '/usr/bin', Config.nvi_bin_list, force)
        FileUtil(self._container_nvidia_set).putdata("")

    def get_mode(self):
        """Get nvidia mode"""
        return os.path.exists(self._container_nvidia_set)

    def get_devices(self):
        """Get list of nvidia devices related to cuda"""
        dev_list = []
        for dev in Config.nvi_dev_list:
            for expanded_devs in glob.glob(dev + '*'):
                dev_list.append(expanded_devs)
        return dev_list
