# -*- coding: utf-8 -*-
"""Manage setting nvidia"""

import os
import stat
import glob
import re
import shutil

from udocker import LOG
from udocker.config import Config
from udocker.utils.fileutil import FileUtil
from udocker.utils.uprocess import Uprocess


class NvidiaMode:
    """nvidia-docker like functionality for udocker.
    Make nvidia host libraries available within udocker, this is achieved
    by copy them into the container so that the execution modes that need
    to change libraries may work properly.
    """

    def __init__(self, localrepo, container_id):
        self.localrepo = localrepo               # LocalRepository object
        self.container_id = container_id         # Container id
        self.container_dir = self.localrepo.cd_container(container_id)
        self.container_root = self.container_dir + "/ROOT"
        self._container_nvidia_set = self.container_dir + "/nvidia"
        self._nvidia_main_libs = ("libnvidia-cfg.so", "libcuda.so", )

    def _files_exist(self, cont_dst_dir, files_list):
        """Verify if files already exists"""
        for fname in files_list:
            dstname = self.container_root + '/' + cont_dst_dir + '/' + fname
            if os.path.exists(dstname):
                raise OSError("file already exists", dstname)

    def _copy_files(self, host_src_dir, cont_dst_dir, files_list, force=False):
        """copy or link file to destination creating directories as needed"""
        LOG.debug("Source (host) dir %s", host_src_dir)
        LOG.debug("Destination (container) dir %s", cont_dst_dir)
        for fname in files_list:
            srcname = host_src_dir + '/' + fname
            dstname = self.container_root + '/' + cont_dst_dir + '/' + fname
            if os.path.isfile(dstname) or os.path.islink(dstname):
                if force:
                    try:
                        os.remove(dstname)
                    except OSError:
                        LOG.error("deleting nvidia file %s", dstname)
                else:
                    LOG.info("nvidia file already exists %s, use --force to overwrite", dstname)
                    return False

            srcdir = os.path.dirname(srcname)
            dstdir = os.path.dirname(dstname)
            if not os.path.isdir(dstdir):
                try:
                    os.makedirs(dstdir)
                    os.chmod(dstdir, stat.S_IMODE(os.stat(srcdir).st_mode) | stat.S_IRWXU)
                except OSError:
                    LOG.error("creating nvidia dir %s", dstdir)

            if os.path.islink(srcname):
                linkto = os.readlink(srcname)
                os.symlink(linkto, dstname)
                LOG.info("is link %s to %s", srcname, dstname)
            elif os.path.isfile(srcname):
                shutil.copy2(srcname, dstname)
                LOG.info("is file %s to %s", srcname, dstname)
                try:
                    mask = stat.S_IMODE(os.stat(srcname).st_mode) | stat.S_IWUSR | stat.S_IRUSR
                    if os.access(srcname, os.X_OK):
                        mask = mask | stat.S_IXUSR
                    os.chmod(dstname, mask)
                except (OSError) as error:
                    LOG.error("change mask of nvidia file: %s", error)
            else:
                LOG.warning("nvidia file in config not found: %s", srcname)

        LOG.debug("nvidia copied %s to %s", srcname, dstname)
        return True

    def _get_nvidia_libs(self, host_dir):
        """Expand the library files to include the versions"""
        lib_list = []
        for lib in Config.conf['nvi_lib_list']:
            for expanded_libs in glob.glob(host_dir + '/' + lib + '*'):
                lib_list.append(expanded_libs.replace(host_dir, ''))

        LOG.debug("list nvidia libs: %s", lib_list)
        return lib_list

    def _find_host_dir_ldconfig(self, arch="x86-64"):
        """Find host nvidia libraries via ldconfig"""
        dir_list = set()
        ld_data = Uprocess().get_output(["ldconfig", "-p"])
        if ld_data:
            regexp = "[ |\t]%s[^ ]* .*%s.*=> (/.*)"
            for line in ld_data.split('\n'):
                for lib in self._nvidia_main_libs:
                    match = re.search(regexp % (lib, arch), line)
                    if match:
                        dir_list.add(os.path.realpath(os.path.dirname(match.group(1))) + '/')

        LOG.debug("list nvidia libs via ldconfig: %s", dir_list)
        return dir_list

    def _find_host_dir_ldpath(self, library_path):
        """Find host nvidia libraries via path"""
        dir_list = set()
        if library_path:
            for libdir in library_path.split(':'):
                for lib in self._nvidia_main_libs:
                    if glob.glob(libdir + f"/{lib}*"):
                        dir_list.add(os.path.realpath(libdir) + '/')

        LOG.debug("list nvidia libs via path: %s", dir_list)
        return dir_list

    def _find_host_dir(self):
        """Find the location of the host nvidia libraries"""
        dir_list = set()
        library_path = ':'.join(Config.conf['lib_dirs_list_x86_64'])
        dir_list.update(self._find_host_dir_ldpath(library_path))
        dir_list.update(self._find_host_dir_ldconfig())
        library_path = os.getenv("LD_LIBRARY_PATH", "")
        dir_list.update(self._find_host_dir_ldpath(library_path))
        LOG.debug("host location nvidia: %s", dir_list)
        return dir_list

    def _find_cont_dir(self):
        """Find the location of the host target directory for libraries"""
        for dst_dir in ("/usr/lib/x86_64-linux-gnu", "/usr/lib64"):
            if os.path.isdir(self.container_root + '/' + dst_dir):
                LOG.debug("cont. location nvidia: %s", dst_dir)
                return dst_dir

        return ""

    def _installation_exists(self, nvi_host_dir_list, nvi_cont_dir):
        """Container has files from previous nvidia installation"""
        try:
            for nvi_host_dir in nvi_host_dir_list:
                lib_list = self._get_nvidia_libs(nvi_host_dir)
                self._files_exist(nvi_cont_dir, lib_list)

            self._files_exist("/etc", Config.conf['nvi_etc_list'])
            self._files_exist("/usr/bin", Config.conf['nvi_bin_list'])
            LOG.info("container has files from previous nvidia install")
        except OSError:
            return True

        return False

    def set_mode(self, force=False):
        """Set nvidia mode"""
        if not self.container_dir:
            LOG.error("nvidia set mode container dir not found")
            return False

        nvi_host_dir_list = self._find_host_dir()
        nvi_cont_dir = self._find_cont_dir()
        if not nvi_host_dir_list:
            LOG.error("host nvidia libraries not found")
            return False

        if not nvi_cont_dir:
            LOG.error("destination dir for nvidia libs not found")
            return False

        if (not force) and self._installation_exists(nvi_host_dir_list, nvi_cont_dir):
            LOG.error("nvidia install already exists, --force to overwrite")
            return False

        for nvi_host_dir in nvi_host_dir_list:
            lib_list = self._get_nvidia_libs(nvi_host_dir)
            self._copy_files(nvi_host_dir, nvi_cont_dir, lib_list, force)

        self._copy_files('/etc', '/etc', Config.conf['nvi_etc_list'], force)
        self._copy_files('/usr/bin', '/usr/bin', Config.conf['nvi_bin_list'], force)
        FileUtil(self._container_nvidia_set).putdata("", 'w')
        LOG.info("nvidia mode set")
        return True

    def get_mode(self):
        """Get nvidia mode"""
        return os.path.exists(self._container_nvidia_set)

    def get_devices(self):
        """Get list of nvidia devices related to cuda"""
        dev_list = []
        for dev in Config.conf['nvi_dev_list']:
            for expanded_devs in glob.glob(dev + '*'):
                dev_list.append(expanded_devs)

        LOG.debug("nvidia device list: %s", dev_list)
        return dev_list
