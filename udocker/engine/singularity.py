# -*- coding: utf-8 -*-
"""Singularity execution engine"""

import sys
import os
import subprocess

from udocker.engine.base import ExecutionEngineCommon
from udocker.msg import Msg
from udocker.config import Config
from udocker.utils.fileutil import FileUtil
from udocker.utils.uvolume import Uvolume
from udocker.helper.nixauth import NixAuthentication
from udocker.utils.filebind import FileBind
from udocker.helper.unique import Unique
from udocker.helper.hostinfo import HostInfo

class SingularityEngine(ExecutionEngineCommon):
    """Docker container execution engine using singularity
    Provides a namespaces based user space container.
    Inherits from ContainerEngine class
    """

    def __init__(self, localrepo, exec_mode):
        super(SingularityEngine, self).__init__(localrepo, exec_mode)
        self.executable = None                   # singularity
        self.execution_id = None

    def select_singularity(self):
        """Set singularity executable and related variables"""
        self.executable = Config.conf['use_singularity_executable']
        if self.executable != "UDOCKER" and not self.executable:
            self.executable = FileUtil("singularity").find_exec()

        if self.executable == "UDOCKER" or not self.executable:
            self.executable = ""
            arch = HostInfo().arch()
            image_list = []
            if arch == "amd64":
                image_list = ["singularity-x86_64", "singularity"]
            elif arch == "i386":
                image_list = ["singularity-x86", "singularity"]
            elif arch == "arm64":
                image_list = ["singularity-arm64", "singularity"]
            elif arch == "arm":
                image_list = ["singularity-arm", "singularity"]

            f_util = FileUtil(self.localrepo.bindir)
            self.executable = f_util.find_file_in_dir(image_list)

        if not os.path.exists(self.executable):
            Msg().err("Error: singularity executable not found")
            sys.exit(1)

    def _get_volume_bindings(self):
        """Get the volume bindings string for singularity exec"""
        vol_list = []
        home_dir = NixAuthentication().get_home()
        home_is_binded = False
        tmp_is_binded = False
        vartmp_is_binded = False
        for vol in self.opt["vol"]:
            (host_path, cont_path) = Uvolume(vol).split()
            if os.path.isdir(host_path):
                if host_path == home_dir and cont_path in ("", host_path):
                    home_is_binded = True
                elif host_path == "/tmp" and cont_path in ("", "/tmp"):
                    tmp_is_binded = True
                elif host_path == "/var/tmp" and cont_path in ("", "/var/tmp"):
                    vartmp_is_binded = True
            vol_list.extend(["-B", f"{host_path}:{cont_path}", ])
        if not home_is_binded:
            vol_list.extend(["--home", f"{self.container_root}/root:/root", ])
        if not tmp_is_binded:
            vol_list.extend(["-B", f"{self.container_root}/tmp:/tmp", ])
        if not vartmp_is_binded:
            vol_list.extend(["-B", f"{self.container_root}/var/tmp:/var/tmp", ])
        return vol_list

    def _singularity_env_get(self):
        """Build environment string with user specified environment in
        the form SINGULARITYENV_var=value
        """
        singularityenv = {}
        for (key, val) in self.opt["env"]:
            singularityenv[f'SINGULARITYENV_{key}'] = val
        return singularityenv

    def _make_container_directories(self):
        """Create directories expected by Singularity"""
        FileUtil(self.container_root + "/var/tmp").mkdir()
        FileUtil(self.container_root + "/tmp").mkdir()
        FileUtil(self.container_root + "/proc").mkdir()
        FileUtil(self.container_root + "/dev").mkdir()
        FileUtil(self.container_root + "/sys").mkdir()
        FileUtil(self.container_root + "/root").mkdir()

    def _run_invalid_options(self):
        """check -p --publish -P --publish-all --net-coop"""
        if self.opt["portsmap"]:
            Msg().out("Warning: this execution mode does not support "
                      "-p --publish", l=Msg.WAR)
        if self.opt["netcoop"]:
            Msg().out("Warning: this execution mode does not support "
                      "-P --netcoop --publish-all", l=Msg.WAR)

    def _run_as_root(self):
        """Set configure running as normal user or as root via --fakeroot
        """
        username = HostInfo().username()
        if "user" in self.opt:
            if self.opt["user"] == username:
                return False

            if self.opt["user"] != "root" and self.opt["uid"] != '0':
                Msg().out("Warning: running as another user not supported")
                return False

            if self._has_option("--fakeroot", "exec"):
                if (NixAuthentication().user_in_subuid(username) and
                        NixAuthentication().user_in_subgid(username)):
                    Config.conf['singularity_options'].extend(["--fakeroot", ])
                    return True

        self.opt["user"] = username
        return False

    def run(self, container_id):
        """Execute a Docker container using singularity.
        This is the main method invoked to run a container with singularity.
          * argument: container_id or name
          * options:  many via self.opt see the help
        """

        if os.path.isdir(
                FileBind(self.localrepo, container_id).container_orig_dir):
            FileBind(self.localrepo, container_id).restore() # legacy 1.1.3

        Config.conf['sysdirs_list'] = (
            # "/dev", "/proc", "/sys",
            "/etc/resolv.conf", "/etc/host.conf",
            "/lib/modules",
        )

        # setup execution
        exec_path = self._run_init(container_id)
        if not exec_path:
            return 2
        self.opt["cmd"][0] = exec_path.replace(self.container_root + "/", "")

        self._run_invalid_options()

        self._make_container_directories()

        self.select_singularity()

        self._run_as_root()

        # set environment variables
        self._run_env_set()

        if Msg.level >= Msg.DBG:
            singularity_debug = ["--debug", "-v", ]
        elif self._has_option("--silent"):
            singularity_debug = ["--silent", ]
        elif self._has_option("--quiet"):
            singularity_debug = ["--quiet", ]
        else:
            singularity_debug = []

        if self.executable.startswith(self.localrepo.bindir):
            Config.conf['singularity_options'].extend(["-u", ])

        #if FileUtil("nvidia-smi").find_exec():
        #    Config.conf['singularity_options'].extend(["--nv", ])

        singularity_vol_list = self._get_volume_bindings()

        # build the actual command
        self.execution_id = Unique().uuid(self.container_id)
        cmd_l = self._set_cpu_affinity()
        cmd_l.append(self.executable)
        cmd_l.extend(singularity_debug)
        cmd_l.append("exec")
        cmd_l.extend(Config.conf['singularity_options'])
        if self.opt["cwd"]:
            cmd_l.extend(["--pwd", self.opt["cwd"], ])
        cmd_l.extend(singularity_vol_list)
        cmd_l.append(self.container_root)
        cmd_l.extend(self.opt["cmd"])
        Msg().out("CMD =", cmd_l, l=Msg.VER)

        # if not --hostenv clean the environment
        self._run_env_cleanup_dict()

        # execute
        self._run_banner(self.opt["cmd"][0], '/')
        status = subprocess.call(cmd_l, shell=False, close_fds=True, \
            env=os.environ.update(self._singularity_env_get()))
        return status
