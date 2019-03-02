# -*- coding: utf-8 -*-
import sys
import os
import subprocess

from udocker.engine.base import ExecutionEngineCommon
from udocker.config import Config
from udocker.msg import Msg
from udocker.utils.fileutil import FileUtil
from udocker.helper.nixauth import NixAuthentication
from udocker.utils.filebind import FileBind
from udocker.utils.uprocess import Uprocess
from udocker.helper.unique import Unique

class SingularityEngine(ExecutionEngineCommon):
    """Docker container execution engine using singularity
    Provides a namespaces based user space container.
    Inherits from ContainerEngine class
    """

    def __init__(self, localrepo, xmode):
        super(SingularityEngine, self).__init__(localrepo)
        self.singularity_exec = None                   # singularity
        self._filebind = None
        self.execution_id = None
        self.exec_mode = xmode

    def _select_singularity(self):
        """Set singularity executable and related variables"""
        conf = Config()
        arch = conf.arch()
        if arch == "amd64":
            image_list = ["singularity-x86_64", "singularity"]
        elif arch == "i386":
            image_list = ["singularity-x86", "singularity"]
        elif arch == "arm64":
            image_list = ["singularity-arm64", "singularity"]
        elif arch == "arm":
            image_list = ["singularity-arm", "singularity"]
        f_util = FileUtil(self.localrepo.bindir)
        self.singularity_exec = f_util.find_file_in_dir(image_list)
        if not self.singularity_exec:
            self.singularity_exec = FileUtil("singularity").find_exec()
        if not self.singularity_exec:
            Msg().err("Error: singularity executable not found")
            sys.exit(1)

    def _get_volume_bindings(self):
        """Get the volume bindings string for singularity exec"""
        vol_list = []
        (tmphost_path, tmpcont_path) = self._filebind.start(Config.sysdirs_list)
        vol_list.extend(["-B", "%s:%s" % (tmphost_path, tmpcont_path), ])
        home_dir = NixAuthentication().get_home()
        home_is_binded = False
        tmp_is_binded = False
        vartmp_is_binded = False
        for vol in self.opt["vol"]:
            (host_path, cont_path) = self._vol_split(vol)
            if os.path.isdir(host_path):
                if host_path == home_dir and cont_path in ("", host_path):
                    home_is_binded = True
                elif host_path == "/tmp" and cont_path in ("", "/tmp"):
                    tmp_is_binded = True
                elif host_path == "/var/tmp" and cont_path in ("", "/var/tmp"):
                    vartmp_is_binded = True
                else:
                    vol_list.extend(["-B", "%s:%s" % (host_path, cont_path), ])
            elif os.path.isfile(host_path):
                if cont_path not in Config.sysdirs_list:
                    Msg().err("Error: engine does not support file mounting:",
                              host_path)
                else:
                    self._filebind.add(host_path, cont_path)
        if not home_is_binded:
            vol_list.extend(["--home", "%s/root:%s" % (self.container_root, "/root"), ])
        if not tmp_is_binded:
            vol_list.extend(["-B", "%s/tmp:/tmp" % (self.container_root), ])
        if not vartmp_is_binded:
            vol_list.extend(["-B", "%s/var/tmp:/var/tmp" % (self.container_root), ])
        return vol_list

    def _singularity_env_get(self):
        """Build environment string with user specified environment in
        the form SINGULARITYENV_var=value
        """
        singularityenv = dict()
        for pair in list(self.opt["env"]):
            (key, val) = pair.split("=", 1)
            singularityenv['SINGULARITYENV_%s' % key] = val
        return singularityenv

    def _setup_container_user(self, user):
        """Override of _setup_container_user()"""
        return self._setup_container_user_noroot(user)

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
            Msg().err("Warning: this execution mode does not support "
                      "-p --publish", l=Msg.WAR)
        if self.opt["netcoop"]:
            Msg().err("Warning: this execution mode does not support "
                      "-P --netcoop --publish-all", l=Msg.WAR)

    def _has_option(self, option):
        """Check if singularity has a given cli option"""
        if option in Uprocess().get_output("singularity --help"):
            return True
        return False

    def run(self, container_id):
        """Execute a Docker container using singularity.
        This is the main method invoked to run a container with singularity.

          * argument: container_id or name
          * options:  many via self.opt see the help
        """

        Config.sysdirs_list = (
            # "/dev", "/proc", "/sys",
            "/etc/passwd", "/etc/group",
            "/lib/modules",
        )

        # setup execution
        if not self._run_init(container_id):
            return 2

        self._run_invalid_options()

        self._make_container_directories()

        self._filebind = FileBind(self.localrepo, self.container_id)

        self._select_singularity()

        self._uid_check_noroot()

        # set environment variables
        self._run_env_set(self.exec_mode)
        if not self._check_env():
            return 5

        if Msg.level >= Msg.DBG:
            singularity_debug = ["--debug", "-x", "-v", ]
        elif self._has_option("--silent"):
            singularity_debug = ["--silent", ]
        elif self._has_option("--quiet"):
            singularity_debug = ["--quiet", ]
        else:
            singularity_debug = []

        if self.singularity_exec.startswith(self.localrepo.bindir):
            Config.singularity_options.extend(["-u", ])

        #if FileUtil("nvidia-smi").find_exec():
        #    Config.singularity_options.extend(["--nv", ])

        singularity_vol_list = self._get_volume_bindings()

        # build the actual command
        self.execution_id = Unique().uuid(self.container_id)
        cmd_l = self._set_cpu_affinity()
        cmd_l.append(self.singularity_exec)
        cmd_l.extend(singularity_debug)
        cmd_l.append("exec")
        cmd_l.extend(Config.singularity_options)
        if self.opt["cwd"]:
            cmd_l.extend(["--pwd", self.opt["cwd"], ])
        cmd_l.extend(singularity_vol_list)
        cmd_l.append(self.container_root)
        cmd_l.extend(self.opt["cmd"])
        Msg().err("CMD =", cmd_l, l=Msg.VER)

        # if not --hostenv clean the environment
        self._run_env_cleanup_dict()

        # execute
        self._run_banner(self.opt["cmd"][0], '/')
        status = subprocess.call(cmd_l, shell=False, close_fds=True, \
            env=os.environ.update(self._singularity_env_get()))
        self._filebind.finish()
        return status
