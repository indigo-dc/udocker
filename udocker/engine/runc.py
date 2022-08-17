# -*- coding: utf-8 -*-
"""runc execution engine"""

import sys
import os
import subprocess
import platform
import stat
import select
import json

from udocker.engine.base import ExecutionEngineCommon
from udocker.engine.proot import PRootEngine
from udocker.msg import Msg
from udocker.config import Config
from udocker.utils.fileutil import FileUtil
from udocker.utils.uvolume import Uvolume
from udocker.engine.nvidia import NvidiaMode
from udocker.utils.filebind import FileBind
from udocker.helper.unique import Unique
from udocker.helper.hostinfo import HostInfo


class RuncEngine(ExecutionEngineCommon):
    """Docker container execution engine using runc
    Provides a namespaces based user space container.
    Inherits from ContainerEngine class
    """

    def __init__(self, localrepo, exec_mode):
        super(RuncEngine, self).__init__(localrepo, exec_mode)
        self.executable = None                   # runc
        self._container_specjson = None
        self._container_specfile = None
        self._container_specdir = self.container_dir
        self._filebind = None
        self.execution_id = None
        self.engine_type = ""

    def select_runc(self):
        """Set runc executable and related variables"""
        self.executable = Config.conf['use_runc_executable']
        if self.executable != "UDOCKER" and not self.executable:
            self.executable = FileUtil("runc").find_exec()

        if self.executable != "UDOCKER" and not self.executable:
            self.executable = FileUtil("crun").find_exec()

        if self.executable == "UDOCKER" or not self.executable:
            self.executable = ""
            arch = HostInfo().arch()
            image_list = []
            eng = ["runc", "crun"]
            if "cgroup2" in FileUtil("/proc/filesystems").getdata('r'):
                eng = ["crun", "runc"]

            if arch == "amd64":
                image_list = [eng[0]+"-x86_64", eng[0],
                              eng[1]+"-x86_64", eng[1]]
            elif arch == "i386":
                image_list = [eng[0]+"-x86", eng[0], eng[1]+"-x86", eng[1]]
            elif arch == "arm64":
                image_list = [eng[0]+"-arm64", eng[0], eng[1]+"-arm64", eng[1]]
            elif arch == "arm":
                image_list = [eng[0]+"-arm", eng[0], eng[1]+"-arm", eng[1]]

            f_util = FileUtil(self.localrepo.bindir)
            self.executable = f_util.find_file_in_dir(image_list)

        if not os.path.exists(self.executable):
            Msg().err("Error: runc/crun executable not found")
            sys.exit(1)
        if "crun" in os.path.basename(self.executable):
            self.engine_type = "crun"
        elif "runc" in os.path.basename(self.executable):
            self.engine_type = "runc"

    def _load_spec(self, new=False):
        """Generate runc spec file"""
        if FileUtil(self._container_specfile).size() != -1 and new:
            FileUtil(self._container_specfile).register_prefix()
            FileUtil(self._container_specfile).remove()

        if FileUtil(self._container_specfile).size() == -1:
            cmd_l = [self.executable, "spec", "--rootless", ]
            status = subprocess.call(cmd_l, shell=False, stderr=Msg.chlderr,
                                     close_fds=True,
                                     cwd=os.path.realpath(\
                                         self._container_specdir))
            if status:
                return False

        json_obj = None
        infile = None
        try:
            infile = open(self._container_specfile, 'r', encoding='utf-8')
            json_obj = json.load(infile)
        except (IOError, OSError, AttributeError, ValueError, TypeError):
            json_obj = None

        if infile:
            infile.close()

        self._container_specjson = json_obj
        return json_obj

    def _save_spec(self):
        """Save spec file"""
        outfile = None
        try:
            outfile = open(self._container_specfile, 'w', encoding='utf-8')
            json.dump(self._container_specjson, outfile)
        except (IOError, OSError, AttributeError, ValueError, TypeError):
            if outfile:
                outfile.close()
            return False
        outfile.close()
        return True

    def _set_spec(self):
        """Set spec values"""
        json_obj = self._container_specjson
        json_obj["root"]["path"] = os.path.realpath(self.container_root)
        json_obj["root"]["readonly"] = False
        if '.' in self.opt["hostname"]:
            json_obj["hostname"] = self.opt["hostname"]
        else:
            json_obj["hostname"] = platform.node()

        if self.opt["cwd"]:
            json_obj["process"]["cwd"] = self.opt["cwd"]

        json_obj["process"]["terminal"] = sys.stdout.isatty()
        if self.engine_type == "crun":
            json_obj["process"]["terminal"] = False

        json_obj["process"]["env"] = []
        for (env_key, env_val) in self.opt["env"]:
            json_obj["process"]["env"].append(f"{env_key}={env_val}")

        json_obj["process"]["args"] = self.opt["cmd"]
        return json_obj

    def _set_id_mappings(self):
        """set uid and gid mappings"""
        json_obj = self._container_specjson
        if "uidMappings" in json_obj["linux"]:
            for idmap in json_obj["linux"]["uidMappings"]:
                if "hostID" in idmap:
                    idmap["hostID"] = HostInfo.uid
        else:
            json_obj["linux"]["uidMappings"] = [ \
                    {"containerID": 0, "hostID": HostInfo.uid, "size":1, }, ]
        if "gidMappings" in json_obj["linux"]:
            for idmap in json_obj["linux"]["gidMappings"]:
                if "hostID" in idmap:
                    idmap["hostID"] = HostInfo.gid
        else:
            json_obj["linux"]["gidMappings"] = [ \
                    {"containerID": 0, "hostID": HostInfo.gid, "size":1, }, ]

    def _del_namespace_spec(self, namespace):
        """Remove a namespace"""
        try:
            json_obj = self._container_specjson
            json_obj["linux"]["namespaces"].remove({"type": namespace})
        except ValueError:
            pass

    def _uid_check(self):
        """Check the uid_map string for container run command"""
        if ("user" in self.opt and self.opt["user"] != "0" and
                self.opt["user"] != "root"):
            Msg().out("Warning: this engine only supports execution as root",
                      l=Msg.WAR)

    def _add_capabilities_spec(self):
        """Set the spec capabilities"""
        if not Config.conf['runc_capabilities']:
            return
        self._container_specjson["process"]["capabilities"]["ambient"] = \
            Config.conf['runc_capabilities']
        self._container_specjson["process"]["capabilities"]["bounding"] = \
            Config.conf['runc_capabilities']
        self._container_specjson["process"]["capabilities"]["effective"] = \
            Config.conf['runc_capabilities']
        self._container_specjson["process"]["capabilities"]["inheritable"] = \
            Config.conf['runc_capabilities']
        self._container_specjson["process"]["capabilities"]["permitted"] = \
            Config.conf['runc_capabilities']

    def _add_device_spec(self, dev_path, mode="rwm"):
        """Add device to the configuration"""
        if not (os.path.exists(dev_path) and dev_path.startswith("/dev/")):
            Msg().err("Error: device not found", dev_path)
            return False
        dev_stat = os.stat(dev_path)
        if stat.S_ISBLK(dev_stat.st_mode):
            dev_type = 'b'
        elif stat.S_ISCHR(dev_stat.st_mode):
            dev_type = 'c'
        else:
            Msg().err("Error: not a device", dev_path)
            return False
        filemode = 0
        if 'r' in mode.lower():
            filemode += 0o444
        if 'w' in mode.lower():
            filemode += 0o222
        if not filemode:
            filemode = 0o666
        if "devices" not in self._container_specjson["linux"]:
            self._container_specjson["linux"]["devices"] = []
        device = {
            "path": dev_path,
            "type": dev_type,
            "major": os.major(dev_stat.st_dev),
            "minor": os.minor(dev_stat.st_dev),
            "fileMode": filemode,
            "uid": HostInfo.uid,
            "gid": HostInfo.gid,
        }
        self._container_specjson["linux"]["devices"].append(device)
        return True

    def _add_devices(self):
        """Add devices to container"""
        added_devices = []
        for dev in self.opt["devices"]:
            dev_name = dev.split(':')[0]
            if self._add_device_spec(dev_name):
                added_devices.append(dev_name)
        if "/dev/nvidiactl" not in added_devices:
            nvidia_mode = NvidiaMode(self.localrepo, self.container_id)
            if nvidia_mode.get_mode():
                for dev_name in nvidia_mode.get_devices():
                    if dev_name not in added_devices:
                        self._add_device_spec(dev_name)

    def _add_mount_spec(self, host_source, cont_dest, rwmode=False,
                        fstype="none", options=None):
        """Add one mount point"""
        if rwmode:
            mode = "rw"
        else:
            mode = "ro"
        mount = {"destination": cont_dest,
                 "type": fstype,
                 "source": host_source,
                 "options": ["rbind", "nosuid", "nodev", mode, ], }
        if options is not None:
            mount["options"] = options
        self._container_specjson["mounts"].append(mount)

    def _del_mount_spec(self, host_source, cont_dest):
        """Remove one mount point"""
        index = self._sel_mount_spec(host_source, cont_dest)
        if index:
            del self._container_specjson["mounts"][index]

    def _sel_mount_spec(self, host_source, cont_dest):
        """Select mount point"""
        for (index, mount) in enumerate(self._container_specjson["mounts"]):
            if (mount["destination"] == cont_dest and
                    mount["source"] == host_source):
                return index
        return None

    def _mod_mount_spec(self, host_source, cont_dest, new):
        """Modify mount spec"""
        index = self._sel_mount_spec(host_source, cont_dest)
        if index is None:
            return False
        mount = self._container_specjson["mounts"][index]
        for new_item in new:
            if new_item == "options":
                if "options" not in mount:
                    mount["options"] = []
                for (new_index, dummy) in enumerate(new["options"]):
                    option_prefix = new["options"][new_index].split('=', 1)[0]
                    for (index, opt) in enumerate(mount["options"]):
                        if opt.startswith(option_prefix):
                            del mount["options"][index]
                    mount["options"] += new["options"]
            else:
                mount[new_item] = new[new_item]
        return True

    def _add_volume_bindings(self):
        """Get the volume bindings string for runc"""
        (host_dir, cont_dir) = self._filebind.start(Config.conf['sysdirs_list'])
        self._add_mount_spec(host_dir, cont_dir, rwmode=True)
        for vol in self.opt["vol"]:
            (host_dir, cont_dir) = Uvolume(vol).split()
            if os.path.isdir(host_dir):
                if host_dir == "/dev":
                    Msg().out("Warning: engine does not support -v",
                              host_dir, l=Msg.WAR)
                    continue
                self._add_mount_spec(host_dir, cont_dir, rwmode=True)
            elif os.path.isfile(host_dir):
                if (host_dir not in Config.conf['sysdirs_list'] and
                        host_dir + ":" + cont_dir not in self.hostauth_list and
                        os.path.dirname(cont_dir) not in
                        Config.conf['mountpoint_prefixes']):
                    Msg().err("Error: engine does not support file mounting:",
                              host_dir)
                else:
                    self._filebind.set_file(host_dir, cont_dir)
                    self._filebind.add_file(host_dir, cont_dir)

    def _run_invalid_options(self):
        """check -p --publish -P --publish-all --net-coop"""
        if self.opt["portsmap"]:
            Msg().out("Warning: this execution mode does not support "
                      "-p --publish", l=Msg.WAR)
        if self.opt["netcoop"]:
            Msg().out("Warning: this execution mode does not support "
                      "-P --netcoop --publish-all", l=Msg.WAR)

    def _proot_overlay(self, proot_mode="P2"):
        """Execute proot within runc"""
        xmode = self.exec_mode.get_mode()
        if xmode not in ("R2", "R3"):
            return False

        preng = PRootEngine(self.localrepo, self.exec_mode)
        preng.exec_mode.force_mode = proot_mode
        preng.select_proot()
        if preng.proot_noseccomp or os.getenv("PROOT_NO_SECCOMP"):
            env_noseccomp = "PROOT_NO_SECCOMP=1"

        if xmode == "R2":
            env_noseccomp = ""

        if xmode == "R3":
            env_noseccomp = "PROOT_NO_SECCOMP=1"

        if env_noseccomp:
            self._container_specjson["process"]["env"].append(env_noseccomp)

        host_executable = preng.executable
        cont_executable = "/.udocker/bin/" + os.path.basename(host_executable)
        self._create_mountpoint(host_executable, cont_executable,
                                dirs_only=False)
        self._filebind.set_file(host_executable, cont_executable)
        self._filebind.add_file(host_executable, cont_executable)
        mode = stat.S_IRUSR | stat.S_IWUSR | stat.S_IXUSR
        FileUtil(self._filebind.get_path(cont_executable)).chmod(mode)
        self._container_specjson["process"]["args"] = \
                [cont_executable, "-0"] + self.opt["cmd"]
        return True

    def run(self, container_id):
        """Execute a Docker container using runc. This is the main method
        invoked to run the a container with runc.
          * argument: container_id or name
          * options:  many via self.opt see the help
        """

        Config.conf['sysdirs_list'] = (
            "/etc/resolv.conf", "/etc/host.conf",
            # "/etc/passwd", "/etc/group",
        )

        # setup execution
        if not self._run_init(container_id):
            return 2

        self._run_invalid_options()

        self._container_specfile = "config.json"
        if self.container_dir:
            if self.localrepo.iswriteable_container(container_id):
                self._container_specdir = self.container_dir
            else:
                self._container_specdir = FileUtil("SPECDIR").mktmpdir()
                FileUtil(self._container_specdir).register_prefix()
            self._container_specfile = \
                    self._container_specdir + '/' + self._container_specfile

        self._filebind = FileBind(self.localrepo, container_id)
        self._filebind.setup()
        self.select_runc()

        # create new OCI spec file
        if not self._load_spec(new=True):
            return 4

        self._uid_check()

        # if not --hostenv clean the environment
        self._run_env_cleanup_list()

        # set environment variables
        self._run_env_set()
        self._set_spec()
        if (Config.conf['runc_nomqueue'] or
                (Config.conf['runc_nomqueue'] is None and not
                 HostInfo().oskernel_isgreater([4, 8, 0]))):
            self._del_mount_spec("mqueue", "/dev/mqueue")

        self._del_mount_spec("cgroup", "/sys/fs/cgroup")
        self._del_namespace_spec("network")
        self._set_id_mappings()
        self._add_volume_bindings()
        self._add_devices()
        self._add_capabilities_spec()
        self._mod_mount_spec("shm", "/dev/shm", {"options": ["size=2g"]})
        self._proot_overlay()
        self._save_spec()
        if Msg.level >= Msg.DBG:
            runc_debug = ["--debug", ]
            Msg().out(json.dumps(self._container_specjson,
                                 indent=4, sort_keys=True))
        else:
            runc_debug = []

       # build the actual command
        self.execution_id = Unique().uuid(self.container_id)
        cmd_l = self._set_cpu_affinity()
        cmd_l.append(self.executable)
        cmd_l.extend(runc_debug)
        cmd_l.extend(["--root", self._container_specdir, "run"])
        cmd_l.extend(["--bundle", self._container_specdir, self.execution_id])
        Msg().err("CMD =", cmd_l, l=Msg.VER)
        self._run_banner(self.opt["cmd"][0], '%')
        if sys.stdout.isatty():
            return self.run_pty(cmd_l)

        return self.run_nopty(cmd_l)

    def run_pty(self, cmd_l):
        """runc from a terminal"""
        status = subprocess.call(cmd_l, shell=False, close_fds=True)
        self._filebind.finish()
        return status

    def run_nopty(self, cmd_l):
        """runc without a terminal"""
        (pmaster, pslave) = os.openpty()
        status = subprocess.Popen(cmd_l, shell=False, close_fds=True,
                                  stdout=pslave, stderr=pslave)
        os.close(pslave)
        while True:
            status.poll()
            if status.returncode is not None:
                break
            readable, dummy, exception = \
                select.select([pmaster, ], [], [pmaster, ], 5)
            if exception:
                break
            if readable:
                try:
                    if sys.version_info[0] >= 3:
                        sys.stdout.write(os.read(pmaster, 1).decode())
                    else:
                        sys.stdout.write(os.read(pmaster, 1))
                except OSError:
                    break
        try:
            status.terminate()
        except OSError:
            pass
        self._filebind.finish()
        return status
