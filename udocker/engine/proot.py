# -*- coding: utf-8 -*-
"""PRoot execution engine"""

import sys
import os
import subprocess

from udocker.engine.base import ExecutionEngineCommon
from udocker.utils.fileutil import FileUtil
from udocker.msg import Msg


class PRootEngine(ExecutionEngineCommon):
    """Docker container execution engine using PRoot
    Provides a chroot like environment to run containers.
    Uses PRoot both as chroot alternative and as emulator of
    the root identity and privileges.
    Inherits from ContainerEngine class
    """

    def __init__(self, conf, localrepo, xmode):
        super(PRootEngine, self).__init__(conf, localrepo, xmode)
        self.proot_exec = None                   # PRoot
        self.proot_noseccomp = False             # Noseccomp mode
        self._kernel = self.conf['oskernel']   # Emulate kernel
        self.exec_mode = xmode

    def _select_proot(self):
        """Set proot executable and related variables"""
        arch = self.conf['arch']
        image_list = []
        if arch == "amd64":
            if self._oskernel_isgreater((4, 8, 0)):
                image_list = ["proot-x86_64-4_8_0", "proot-x86_64", "proot"]
            else:
                image_list = ["proot-x86_64", "proot"]
        elif arch == "i386":
            if self._oskernel_isgreater((4, 8, 0)):
                image_list = ["proot-x86-4_8_0", "proot-x86", "proot"]
            else:
                image_list = ["proot-x86", "proot"]
        elif arch == "arm64":
            if self._oskernel_isgreater((4, 8, 0)):
                image_list = ["proot-arm64-4_8_0", "proot-arm64", "proot"]
            else:
                image_list = ["proot-arm64", "proot"]
        elif arch == "arm":
            if self._oskernel_isgreater((4, 8, 0)):
                image_list = ["proot-arm-4_8_0", "proot-arm", "proot"]
            else:
                image_list = ["proot-arm", "proot"]
        f_util = FileUtil(self.conf, self.localrepo.bindir)
        self.proot_exec = f_util.find_file_in_dir(image_list)
        if not self.proot_exec:
            Msg().err("Error: proot executable not found")
            sys.exit(1)
        if self._oskernel_isgreater((4, 8, 0)):
            if self.conf['proot_noseccomp'] is not None:
                self.proot_noseccomp = self.conf['proot_noseccomp']
            if self.exec_mode == "P2":
                self.proot_noseccomp = True

    def _set_uid_map(self):
        """Set the uid_map string for container run command"""
        if self.opt["uid"] == "0":
            uid_map_list = ["-0", ]
        else:
            uid_map_list = \
                ["-i", self.opt["uid"] + ":" + self.opt["gid"], ]
        return uid_map_list

    def _create_mountpoint(self, host_path, cont_path):
        """Override create mountpoint"""
        return True

    def _get_volume_bindings(self):
        """Get the volume bindings string for container run command"""
        proot_vol_list = []
        for vol in self.opt["vol"]:
            proot_vol_list.extend(["-b", "%s:%s" % self._vol_split(vol)])
        return proot_vol_list

    def _get_network_map(self):
        """Get mapping of TCP/IP ports"""
        proot_netmap_list = []
        for (cont_port, host_port) in list(self._get_portsmap().items()):
            proot_netmap_list.extend(["-p", "%d:%d" % (cont_port, host_port)])
        if self.opt["netcoop"]:
            proot_netmap_list.extend(["-n", ])
        return proot_netmap_list

    def run(self, container_id):
        """Execute a Docker container using PRoot. This is the main method
        invoked to run the a container with PRoot.

          * argument: container_id or name
          * options:  many via self.opt see the help
        """

        # setup execution
        if not self._run_init(container_id):
            return 2

        self._select_proot()

        # seccomp and ptrace behavior change on 4.8.0 onwards
        if self.proot_noseccomp or os.getenv("PROOT_NO_SECCOMP"):
            self.opt["env"].append("PROOT_NO_SECCOMP=1")

        if self.opt["kernel"]:
            self._kernel = self.opt["kernel"]

        # set environment variables
        self._run_env_set()
        if not self._check_env():
            return 4

        if Msg.level >= Msg.DBG:
            proot_verbose = ["-v", "9", ]
        else:
            proot_verbose = []

        if self.conf['proot_killonexit']:
            proot_kill_on_exit = ["--kill-on-exit", ]
        else:
            proot_kill_on_exit = []

        # build the actual command
        cmd_l = self._set_cpu_affinity()
        cmd_l.append(self.proot_exec)
        cmd_l.extend(proot_verbose)
        cmd_l.extend(proot_kill_on_exit)
        cmd_l.extend(self._get_volume_bindings())
        cmd_l.extend(self._set_uid_map())
        cmd_l.extend(["-k", self._kernel, ])
        cmd_l.extend(self._get_network_map())
        cmd_l.extend(["-r", self.container_root, ])

        if self.opt["cwd"]:  # set current working directory
            cmd_l.extend(["-w", self.opt["cwd"], ])
        cmd_l.extend(self.opt["cmd"])
        Msg().err("CMD =", cmd_l, l=Msg.VER)

        # cleanup the environment
        self._run_env_cleanup_dict()

        # execute
        self._run_banner(self.opt["cmd"][0])
        status = subprocess.call(cmd_l, shell=False, close_fds=True,
                                 env=os.environ.update(self._run_env_get()))
        return status
