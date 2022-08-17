# -*- coding: utf-8 -*-
"""fakechroot execution engine"""

import os
import sys
import re
import subprocess

from udocker import is_genstr
from udocker.engine.base import ExecutionEngineCommon
from udocker.helper.osinfo import OSInfo
from udocker.msg import Msg
from udocker.config import Config
from udocker.utils.fileutil import FileUtil
from udocker.utils.uvolume import Uvolume
from udocker.helper.elfpatcher import ElfPatcher


class FakechrootEngine(ExecutionEngineCommon):
    """Docker container execution engine using Fakechroot
    Provides a chroot like environment to run containers.
    Uses Fakechroot as chroot alternative.
    Inherits from ContainerEngine class
    """

    def __init__(self, localrepo, exec_mode):
        super(FakechrootEngine, self).__init__(localrepo, exec_mode)
        self._fakechroot_so = ""
        self._elfpatcher = None
        self._recommend_expand_symlinks = False

    def select_fakechroot_so(self):
        """Select fakechroot sharable object library"""
        image_list = []
        if Config.conf['fakechroot_so']:
            if isinstance(Config.conf['fakechroot_so'], list):
                image_list = Config.conf['fakechroot_so']
            elif is_genstr(Config.conf['fakechroot_so']):
                image_list = [Config.conf['fakechroot_so'], ]

            if "/" in Config.conf['fakechroot_so']:
                if os.path.exists(Config.conf['fakechroot_so']):
                    return os.path.realpath(Config.conf['fakechroot_so'])
        elif os.path.exists(self.container_dir + "/libfakechroot.so"):
            return self.container_dir + "/libfakechroot.so"
        else:
            lib = "libfakechroot"
            deflib = "libfakechroot.so"
            image_list = [deflib, ]
            guest = OSInfo(self.container_root)
            arch = guest.arch()
            (distro, version) = guest.osdistribution()
            if "Alpine" not in distro:
                version = version.split(".")[0]

            if arch == "amd64":
                image_list = [f"{lib}-{distro}-{version}-x86_64.so",
                              f"{lib}-{distro}-x86_64.so",
                              f"{lib}-x86_64.so", deflib]
            elif arch == "i386":
                image_list = [f"{lib}-{distro}-{version}-x86.so",
                              f"{lib}-{distro}-x86.so",
                              f"{lib}-x86.so", deflib]
            elif arch == "arm64":
                image_list = [f"{lib}-{distro}-{version}-arm64.so",
                              f"{lib}-{distro}-arm64.so",
                              f"{lib}-arm64.so", deflib]
            elif arch == "arm":
                image_list = [f"{lib}-{distro}-{version}-arm.so",
                              f"{lib}-{distro}-arm.so",
                              f"{lib}-arm.so", deflib]

        f_util = FileUtil(self.localrepo.libdir)
        fakechroot_so = f_util.find_file_in_dir(image_list)
        if not os.path.exists(fakechroot_so):
            Msg().err("Error: no libfakechroot found", image_list)
            sys.exit(1)

        Msg().out("Info: fakechroot_so:", fakechroot_so, l=Msg.DBG)
        return fakechroot_so

    def _setup_container_user(self, user):
        """Override of _setup_container_user()"""
        return self._setup_container_user_noroot(user)

    def _uid_check(self):
        """Check the uid_map string for container run command"""
        if ("user" in self.opt and (self.opt["user"] == '0' or
                                    self.opt["user"] == "root")):
            Msg().out("Warning: this engine does not support execution as root",
                      l=Msg.WAR)

    def _get_volume_bindings(self):
        """Get the volume bindings string for fakechroot run"""
        host_volumes_list = []
        map_volumes_list = []
        map_volumes_dict = {}
        for vol in self.opt["vol"]:
            (host_path, cont_path) = Uvolume(vol).split()
            if not (host_path and cont_path):
                continue
            real_host_path = os.path.realpath(host_path)
            if (host_path == cont_path and
                    Config.conf['fakechroot_expand_symlinks'] is False):
                host_volumes_list.append(host_path)
            elif (host_path == cont_path and
                  host_path in Config.conf['sysdirs_list']):
                host_volumes_list.append(host_path)
            elif host_path == cont_path and not os.path.isdir(real_host_path):
                host_volumes_list.append(host_path)
            else:
                map_volumes_dict[cont_path] = real_host_path + '!' + cont_path
                if host_path != real_host_path or os.path.isdir(real_host_path):
                    self._recommend_expand_symlinks = True
        for cont_path in sorted(map_volumes_dict, reverse=True):
            map_volumes_list.append(map_volumes_dict[cont_path])
        return (':'.join(host_volumes_list), ':'.join(map_volumes_list))

    def _get_access_filesok(self):
        """
        Circunvent mpi init issues when calling access()
        A list of certain existing files is provided
        """
        file_list = []
        for c_path in Config.conf['access_files']:
            h_file = FileUtil(self.container_root).cont2host(c_path,
                                                             self.opt["vol"])
            if h_file and os.path.exists(h_file):
                file_list.append(c_path)
        return ":".join(file_list)

    def _fakechroot_env_set(self):
        """fakechroot environment variables to set"""
        (host_volumes, map_volumes) = self._get_volume_bindings()
        self._fakechroot_so = self.select_fakechroot_so()
        access_filesok = self._get_access_filesok()
        self.opt["env"].append("PWD=" + self.opt["cwd"])
        self.opt["env"].append("FAKECHROOT_BASE=" +
                               os.path.realpath(self.container_root))
        self.opt["env"].append("LD_PRELOAD=" + self._fakechroot_so)
        if Config.conf['fakechroot_expand_symlinks'] is None:
            self.opt["env"].append("FAKECHROOT_EXPAND_SYMLINKS=" + \
                    str(self._recommend_expand_symlinks).lower())
        else:
            self.opt["env"].append("FAKECHROOT_EXPAND_SYMLINKS=" + \
                    str(Config.conf['fakechroot_expand_symlinks']).lower())

        if not self._is_volume("/tmp"):
            self.opt["env"].append("FAKECHROOT_AF_UNIX_PATH=" +
                                   Config.conf['tmpdir'])

        if host_volumes:
            self.opt["env"].append("FAKECHROOT_EXCLUDE_PATH=" + host_volumes)

        if map_volumes:
            self.opt["env"].append("FAKECHROOT_DIR_MAP=" + map_volumes)

        if Msg.level >= Msg.DBG:
            self.opt["env"].append("FAKECHROOT_DEBUG=true")
            self.opt["env"].append("LD_DEBUG=libs:files")

        if access_filesok:
            self.opt["env"].append("FAKECHROOT_ACCESS_FILESOK=" +
                                   access_filesok)

        # execution mode
        ld_library_real = self._elfpatcher.get_ld_library_path()
        xmode = self.exec_mode.get_mode()
        if xmode == "F1":
            self.opt["env"].append("FAKECHROOT_ELFLOADER=" +
                                   self._elfpatcher.get_container_loader())
            self.opt["env"].append("LD_LIBRARY_PATH=" + ld_library_real)
        elif xmode == "F2":
            self.opt["env"].append("FAKECHROOT_ELFLOADER=" +
                                   self._elfpatcher.get_container_loader())
            self.opt["env"].append("FAKECHROOT_LIBRARY_ORIG=" + ld_library_real)
            self.opt["env"].append("LD_LIBRARY_REAL=" + ld_library_real)
            self.opt["env"].append("LD_LIBRARY_PATH=" + ld_library_real)
        elif xmode == "F3":
            self.opt["env"].append("FAKECHROOT_LIBRARY_ORIG=" + ld_library_real)
            self.opt["env"].append("LD_LIBRARY_REAL=" + ld_library_real)
            self.opt["env"].append("LD_LIBRARY_PATH=" + ld_library_real)
        elif xmode == "F4":
            self.opt["env"].append("FAKECHROOT_LIBRARY_ORIG=" + ld_library_real)
            self.opt["env"].append("LD_LIBRARY_REAL=" + ld_library_real)
            self.opt["env"].append("LD_LIBRARY_PATH=" + ld_library_real)
            patchelf_exec = self._elfpatcher.select_patchelf()
            if patchelf_exec:
                self.opt["env"].append("FAKECHROOT_PATCH_PATCHELF=" +
                                       patchelf_exec)
                self.opt["env"].append("FAKECHROOT_PATCH_ELFLOADER=" +
                                       self._elfpatcher.get_container_loader())
                self.opt["env"].append("FAKECHROOT_PATCH_LAST_TIME=" +
                                       self._elfpatcher.get_patch_last_time())

    def _run_invalid_options(self):
        """check -p --publish -P --publish-all --net-coop"""
        if self.opt["portsmap"]:
            Msg().out("Warning: this execution mode does not support "
                      "-p --publish", l=Msg.WAR)
        if self.opt["netcoop"]:
            Msg().out("Warning: this execution mode does not support "
                      "-P --netcoop --publish-all", l=Msg.WAR)

    def _run_add_script_support(self, exec_path):
        """Add an interpreter for non binary executables (scripts)"""
        filetype = OSInfo(self.container_root).get_filetype(exec_path)
        if "ELF" in filetype and ("static" in filetype or
                                  "dynamic" in filetype):
            self.opt["cmd"][0] = exec_path
            return []
        env_exec = FileUtil("env").find_exec("/bin:/usr/bin",
                                             self.container_root)
        if  env_exec:
            return [self.container_root + '/' + env_exec, ]
        relc_path = exec_path.split(self.container_root, 1)[-1]
        real_path = FileUtil(self.container_root).cont2host(relc_path,
                                                            self.opt["vol"])
        hashbang = FileUtil(real_path).get1stline()
        match = re.match("#! *([^ ]+)(.*)", hashbang)
        if match and not match.group(1).startswith('/'):
            Msg().err("Error: no such file", match.group(1), "in", exec_path)
            sys.exit(1)
        elif match:
            interpreter = [self.container_root + '/' + match.group(1), ]
            if match.group(2):
                interpreter.extend(match.group(2).strip().split(' '))
            self.opt["cmd"][0] = exec_path.split(self.container_root, 1)[-1]
            return interpreter
        sh_exec = FileUtil("sh").find_exec(self.opt["env"].getenv("PATH"),
                                           self.container_root)
        if sh_exec:
            return [self.container_root + '/' + sh_exec, ]
        Msg().err("Error: sh not found")
        sys.exit(1)

    def run(self, container_id):
        """Execute a Docker container using Fakechroot. This is the main
        method invoked to run the a container with Fakechroot.
          * argument: container_id or name
          * options:  many via self.opt see the help
        """

        # warning root execution not supported
        self._uid_check()

        # setup execution
        exec_path = self._run_init(container_id)
        if not exec_path:
            return 2

        self._run_invalid_options()

        # execution mode and get patcher
        xmode = self.exec_mode.get_mode()
        self._elfpatcher = ElfPatcher(self.localrepo, self.container_id)

        # verify if container pathnames are correct for this mode
        if not self._elfpatcher.check_container_path():
            Msg().out("Warning: container path mismatch, use setup to convert",
                      l=Msg.WAR)

        # set basic environment variables
        self._run_env_set()
        self._fakechroot_env_set()

        # if not --hostenv clean the environment
        self._run_env_cleanup_list()

        # build the actual command
        cmd_l = self._set_cpu_affinity()
        cmd_l.extend(["env", "-i", ])
        cmd_l.extend(self.opt["env"].list())
        if xmode in ("F1", "F2"):
            container_loader = self._elfpatcher.get_container_loader()
            if container_loader:
                cmd_l.append(container_loader)
        cmd_l.extend(self._run_add_script_support(exec_path))
        cmd_l.extend(self.opt["cmd"])
        Msg().out("CMD =", cmd_l, l=Msg.VER)

        # execute
        self._run_banner(self.opt["cmd"][0], '#')
        cwd = FileUtil(self.container_root).cont2host(self.opt["cwd"],
                                                      self.opt["vol"])
        status = subprocess.call(cmd_l, shell=False, close_fds=True, cwd=cwd)
        return status
