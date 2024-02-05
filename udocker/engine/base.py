# -*- coding: utf-8 -*-
"""Superclass for the execution engines"""

import os
import re
import json

from udocker import LOG, MSG
from udocker.config import Config
from udocker.utils.fileutil import FileUtil
from udocker.utils.uenv import Uenv
from udocker.utils.uvolume import Uvolume
from udocker.helper.nixauth import NixAuthentication
from udocker.helper.hostinfo import HostInfo
from udocker.helper.osinfo import OSInfo
from udocker.container.structure import ContainerStructure
from udocker.utils.filebind import FileBind
from udocker.utils.mountpoint import MountPoint


class ExecutionEngineCommon:
    """Docker container execution engine parent class
    Provides the container execution methods that are common to
    the execution drivers.
    """

    # Metadata defaults
    opt = {}                     # Run options
    opt["nometa"] = False            # Don't load metadata
    opt["nosysdirs"] = False         # Bind host dirs
    opt["dri"] = False               # Directories needed for DRI
    opt["bindhome"] = False          # Bind user home dir
    opt["hostenv"] = False           # Pass host env
    opt["hostauth"] = False          # Use hostauth_list
    opt["containerauth"] = False     # Authentication from container
    opt["novol"] = []                # Volume bindings to ignore
    opt["env"] = Uenv()              # Environment from container
    opt["envfile"] = []              # File with environment variables
    opt["vol"] = []                  # Volumes to mount
    opt["cpuset"] = ""               # Container CPU affinity
    opt["user"] = ""                 # User to run in the container
    opt["cwd"] = ""                  # Default dir in the container
    opt["entryp"] = ""               # Container entrypoint
    opt["cmd"] = []                  # Command to execute
    opt["hostname"] = ""             # Hostname TBD
    opt["domain"] = ""               # Host domainname TBD
    opt["volfrom"] = []              # Mount vol from container TBD
    opt["portsmap"] = []             # Ports mapped in container
    opt["portsexp"] = []             # Ports exposed by container
    opt["devices"] = []              # Devices passed to container
    opt["nobanner"] = False          # Printing of startup banner

    def __init__(self, localrepo, exec_mode):
        self.localrepo = localrepo            # LocalRepository instance
        self.container_id = ""                # Container id
        self.container_dir = ""               # Container directory
        self.container_root = ""              # ROOT of container filesystem
        self.container_names = []             # Container names
        self.imagerepo = None                 # Imagerepo of container image
        self.hostauth_list = ()               # Authentication files to be used
        self.exec_mode = exec_mode            # ExecutionMode instance
        self.mountp = None                    # MountPoint object
        self.executable = ""                  # Executable proot, runc, etc
        self.container_os = ""                # Container operating system
        self.container_architecture = ""      # Container architecture
        self.container_variant = ""           # Container variant

    def _has_option(self, search_option, arg=None):
        """Check if executable has a given cli option"""
        return HostInfo().cmd_has_option(self.executable, search_option, arg)

    def _get_portsmap(self, by_container=True):
        """List of TCP/IP ports mapped indexed by container port"""
        indexed_portmap = {}
        for portmap in self.opt["portsmap"]:
            pmap = portmap.split(":")
            try:
                host_port = int(pmap[0])
                cont_port = int(pmap[1])
            except (ValueError, TypeError):
                try:
                    host_port = int(pmap[1])
                    cont_port = int(pmap[2])
                except (ValueError, TypeError):
                    host_port = None
                    cont_port = None

            if host_port:
                if by_container:
                    indexed_portmap[cont_port] = host_port
                else:
                    indexed_portmap[host_port] = cont_port

        return indexed_portmap

    def _check_exposed_ports(self):
        """TCP/UDP ports < 1024 in ExposedPorts JSON metadata
        The exposed ports format is  ExposedPorts:{ "80/tcp":{}, }
        """
        mapped_ports = self._get_portsmap()
        exposes_priv = False
        exposes_port = False
        for port in self.opt["portsexp"]:
            try:
                port_number = int(port.split("/")[0])
                exposes_port = True
            except (ValueError, TypeError):
                pass
            else:
                if port_number < 1024:
                    # if port_number in list(mapped_ports.keys()):
                    #     if mapped_ports[port_number] >= 1024:
                    #         continue
                    for (mports, dummy) in mapped_ports.items():
                        if mports >= 1024:
                            continue
                    exposes_priv = True

        if exposes_priv and HostInfo.uid != 0:
            LOG.error("this container exposes privileged TCP/IP ports")
            return False

        if exposes_port:
            LOG.warning("this container exposes TCP/IP ports")

        return True

    def _set_cpu_affinity(self):
        """Set the cpu affinity string for container run command"""
        # find set affinity executable
        if not self.opt["cpuset"]:
            return []

        exec_cmd = []
        for exec_cmd in Config.conf['cpu_affinity_exec_tools']:
            exec_name = FileUtil(exec_cmd[0]).find_exec()
            if exec_name:
                exec_cmd[0] = exec_name
                for (index, arg) in enumerate(exec_cmd):
                    if arg == "%s":
                        exec_cmd[index] = self.opt["cpuset"]

                return exec_cmd

        self.opt["cpuset"] = ""
        return []

    def _create_mountpoint(self, host_path, cont_path, dirs_only=False):
        """Create mountpoint"""
        if dirs_only and not FileUtil(host_path).isdir():
            return True

        if self.mountp.create(host_path, cont_path):
            self.mountp.save(cont_path)
            return True

        return False

    def _check_volumes(self):
        """Check volume paths"""
        for vol in list(self.opt["vol"]):
            (host_path, cont_path) = Uvolume(vol).split()
            if not (host_path and host_path.startswith('/')):
                LOG.error("invalid host volume path: %s", host_path)
                return False

            if not (cont_path and cont_path != '/' and cont_path.startswith('/')):
                LOG.error("invalid container volume path: %s", cont_path)
                return False

            if not os.path.exists(host_path):
                dril = Config.conf['dri_list']
                sysl = Config.conf['sysdirs_list']
                if (host_path in dril or host_path in sysl):
                    self.opt["vol"].remove(vol)
                    continue

                LOG.error("invalid host volume path: %s", host_path)
                return False

            if not self._create_mountpoint(host_path, cont_path):
                LOG.error("creating mountpoint: %s:%s", host_path, cont_path)
                return False

        return True

    def _get_bindhome(self):
        """Binding of the host $HOME in to the container $HOME"""
        if self.opt["bindhome"]:
            return NixAuthentication().get_home()

        return ""

    def _is_volume(self, path):
        """Is path a host_path in the volumes list"""
        for vol in list(self.opt["vol"]):
            (host_path, cont_path) = Uvolume(vol).split()
            if host_path and host_path == Uvolume().cleanpath(path):
                return cont_path

        return ""

    def _is_mountpoint(self, path):
        """Is path a host_path in the volumes list"""
        for vol in list(self.opt["vol"]):
            (host_path, cont_path) = Uvolume(vol).split()
            if cont_path and cont_path == Uvolume().cleanpath(path):
                return host_path

        return ""

    def _set_volume_bindings(self):
        """Set the volume bindings string for container run command"""
        # predefined volume bindings --sysdirs --hostauth --dri
        if not self.opt["nosysdirs"]:
            self.opt["vol"].extend(Config.conf['sysdirs_list'])

        if self.opt["hostauth"]:
            self.opt["vol"].extend(self.hostauth_list)

        if self.opt["dri"]:
            self.opt["vol"].extend(Config.conf['dri_list'])

        home = self._get_bindhome()
        if home:
            self.opt["vol"].append(home)

        # remove directory bindings specified with --novol
        for novolume in list(self.opt["novol"]):
            found = False
            for vol in list(self.opt["vol"]):
                if novolume in (vol, vol.split(':')[0]):
                    self.opt["vol"].remove(vol)
                    found = True

            if not found:
                LOG.warning("--novol %s not in volumes list", novolume)
        return self._check_volumes()

    def _check_paths(self):
        """Make sure we have a reasonable default PATH and CWD"""
        if not self.opt["env"].getenv("PATH"):
            if self.opt["uid"] == "0":
                path = Config.conf['root_path']
            else:
                path = Config.conf['user_path']

            self.opt["env"].append(f"PATH={path}")

        # verify if the working directory is valid and fix it
        if not self.opt["cwd"]:
            self.opt["cwd"] = self.opt["home"]

        cwd_path = FileUtil(self.container_root).cont2host(self.opt["cwd"], self.opt["vol"])
        if os.path.isdir(cwd_path):
            return True

        LOG.error("invalid working directory: %s", self.opt["cwd"])
        return False

    def _check_executable(self):
        """Check if executable exists and has execute permissions"""
        if self.opt["entryp"] and isinstance(self.opt["entryp"], str):
            self.opt["entryp"] = self.opt["entryp"].strip().split(' ')

        if isinstance(self.opt["entryp"], list):
            if self.opt["cmd"]:                  # and cmd
                cmd_args = self.opt["cmd"]
                self.opt["cmd"] = self.opt["entryp"]
                self.opt["cmd"].extend(cmd_args)   # cmd=args entryp
            else:
                self.opt["cmd"] = self.opt["entryp"]

        if not self.opt["cmd"]:
            self.opt["cmd"] = Config.conf['cmd']
            LOG.warning("no command assuming: %s", self.opt["cmd"])

        exec_name = self.opt["cmd"][0]            # exec pathname without args
        if exec_name.startswith("./") or exec_name.startswith("../"):
            exec_name = self.opt["cwd"] + '/' + exec_name

        path = self.opt["env"].getenv("PATH")
        exec_name = FileUtil(exec_name).find_exec(path, self.container_root,
                                                  self.opt["vol"], self.opt["cwd"])
        if exec_name:
            return self.container_root + '/' + exec_name

        LOG.error("command not found/no execute bit set: %s", self.opt["cmd"])
        return ""

    def _run_load_metadata(self, container_id):
        """Load container metadata from container JSON payload"""
        # get container metadata unless we are dealing with a simple directory
        # tree in which case we don't have metadata
        if Config.conf['location']:
            cont_dir = ""
            cntjson = []
        else:
            cstruc = ContainerStructure(self.localrepo, container_id)
            (cont_dir, cntjson) = cstruc.get_container_attr()
            if not cont_dir:
                return (None, None)

            # load metadata from container
            if not self.opt["nometa"]:
                if not self.opt["user"]:
                    self.opt["user"] = cstruc.get_container_meta("User", "", cntjson)

                if not self.opt["cwd"]:
                    self.opt["cwd"] = cstruc.get_container_meta("WorkingDir", "", cntjson)

                if not self.opt["hostname"]:
                    self.opt["hostname"] = cstruc.get_container_meta("Hostname", "", cntjson)

                if not self.opt["domain"]:
                    self.opt["domain"] = cstruc.get_container_meta("Domainname", "", cntjson)

                if self.opt["entryp"] is False:
                    self.opt["entryp"] = cstruc.get_container_meta("Entrypoint", [], cntjson)
                    if not self.opt["cmd"]:
                        self.opt["cmd"] = cstruc.get_container_meta("Cmd", [], cntjson)
                elif not self.opt["entryp"]:
                    self.opt["entryp"] = []
                elif isinstance(self.opt["entryp"], str):
                    self.opt["entryp"] = self.opt["entryp"].strip().split(' ')

                self.opt["Volumes"] = cstruc.get_container_meta("Volumes", [], cntjson)
                self.opt["portsexp"].extend(cstruc.get_container_meta("ExposedPorts", [], cntjson))
                self.opt["env"].extendif(cstruc.get_container_meta("Env", [], cntjson))

                self.container_os = cstruc.get_container_meta("os", "", cntjson)
                self.container_architecture = cstruc.get_container_meta("architecture",
                                                                        "", cntjson)
                self.container_variant = cstruc.get_container_meta("variant", "", cntjson)

        return (cont_dir, cntjson)

    def _select_auth_files(self):
        """select authentication files to use /etc/passwd /etc/group"""
        cont_passwd = self.container_root + "/etc/passwd"
        cont_group = self.container_root + "/etc/group"
        bind_passwd = self.container_dir + FileBind.orig_dir + "/#etc#passwd"
        bind_group = self.container_dir + FileBind.orig_dir + "/#etc#group"
        if os.path.islink(cont_passwd) and os.path.isfile(bind_passwd):
            passwd = bind_passwd
        else:
            passwd = cont_passwd

        if os.path.islink(cont_group) and os.path.isfile(bind_group):
            group = bind_group
        else:
            group = cont_group

        if self._is_mountpoint("/etc/passwd"):
            passwd = self._is_mountpoint("/etc/passwd")

        if self._is_mountpoint("/etc/group"):
            group = self._is_mountpoint("/etc/group")

        return (passwd, group)

    def _validate_user_str(self, user):
        """parse string with uid:gid or username"""
        user_id = {}
        if not isinstance(user, str):
            return user_id

        if re.match("^[a-za-z_][a-za-z0-9_-]*$", user):
            user_id["user"] = user
            return user_id

        match = re.match("^(\\d+)(:(\\d+)){0,1}$", user)
        if match:
            user_id["uid"] = match.group(1)
            if match.group(3):
                user_id["gid"] = match.group(3)

        return user_id

    def _user_from_str(self, user, host_auth=None, container_auth=None):
        """user password entry from host or container passwd
           returns (valid_user: bool, user_passwd_fields: dict)
        """
        user_id = self._validate_user_str(user)
        if not user_id:
            return (False, user_id)

        search_field = user_id.get("uid", user_id.get("user", ""))
        if self.opt["hostauth"]:
            (self.opt["user"], self.opt["uid"], self.opt["gid"],
             self.opt["gecos"], self.opt["home"], self.opt["shell"]) = \
                host_auth.get_user(search_field)
        else:
            (self.opt["user"], self.opt["uid"], self.opt["gid"],
             self.opt["gecos"], self.opt["home"], self.opt["shell"]) = \
                container_auth.get_user(search_field)

        return (True, user_id)

    def _setup_container_user(self, user):
        """once we know which username to use inside the container
        we need to check if it exists in the passwd file that will
        be used inside the container. since we can override the
        usage of the container /etc/passwd and /etc/group with
        files passed from the host, then we must check if this
        username is in the appropriate file so:
        1. check if the passwd will be the one of the host system
           either because we passwd --hostauth or because we did
           --volume=/etc/passwd:/etc/passwd
        2. else we are using the container original /etc/passwd
        in either case the user specified may not exist, in which
        case we copy the passwd file to a new file, and we create
        the intended user. the file is then passwd/mapped into
        the container.
        """
        host_auth = NixAuthentication()
        (passwd, group) = self._select_auth_files()
        container_auth = NixAuthentication(passwd, group)
        if not user:
            user = "root"

        (valid_user, user_id) = self._user_from_str(user, host_auth, container_auth)
        if not valid_user:
            LOG.error("invalid syntax for user; %s", user)
            return False

        if (self._is_mountpoint("/etc/passwd") or self._is_mountpoint("/etc/group")):
            self.opt["hostauth"] = self.opt["containerauth"] = False
            return True

        if self.opt["user"]:
            if self.opt["user"] != "root":
                self.opt["uid"] = str(HostInfo.uid)
                self.opt["gid"] = str(HostInfo.gid)
        else:
            if self.opt["hostauth"] or self.opt["containerauth"]:
                LOG.error("user not found")
                return False

            self.opt["user"] = user_id["user"] if "user" in user_id else user
            self.opt["uid"] = user_id["uid"] if "uid" in user_id else ""
            self.opt["gid"] = user_id["gid"] if "gid" in user_id else ""

        self._create_user(container_auth, host_auth)
        return True

    def _setup_container_user_noroot(self, user):
        """ setup user for engines without root support.
        equivalent to _setup_container_user() for engines without root support.
        """
        host_auth = NixAuthentication()
        (passwd, group) = self._select_auth_files()
        container_auth = NixAuthentication(passwd, group)
        if not user:
            user = HostInfo().username()

        (valid_user, user_id) = self._user_from_str(user, host_auth, container_auth)
        if not valid_user:
            LOG.error("invalid syntax for user: %s", user)
            return False

        if self.opt["user"] == "root":
            self.opt["user"] = HostInfo().username()
            self.opt["uid"] = str(HostInfo.uid)
            self.opt["gid"] = str(HostInfo.gid)

        if (self._is_mountpoint("/etc/passwd") or self._is_mountpoint("/etc/group")):
            self.opt["hostauth"] = self.opt["containerauth"] = False
            return True

        if self.opt["user"]:
            self.opt["uid"] = str(HostInfo.uid)
            self.opt["gid"] = str(HostInfo.gid)
        else:
            if self.opt["hostauth"] or self.opt["containerauth"]:
                LOG.error("user not found on host")
                return False

            self.opt["user"] = user_id["user"] if "user" in user_id else user
            self.opt["uid"] = user_id["uid"] if "uid" in user_id else ""
            self.opt["gid"] = user_id["gid"] if "gid" in user_id else ""

        self._create_user(container_auth, host_auth)
        return True

    def _fill_user(self):
        """fill in values for user to be used in the account creation.
        provide default values in case the required fields are empty.
        """
        if not self.opt["uid"]:
            self.opt["uid"] = str(HostInfo.uid)

        if not self.opt["gid"]:
            self.opt["gid"] = str(HostInfo.gid)

        if not self.opt["user"]:
            self.opt["user"] = "udoc" + self.opt["uid"][0:4]

        if self.opt["bindhome"]:
            self.opt["home"] = NixAuthentication().get_home()

        if not self.opt["home"]:
            self.opt["home"] = '/'

        if not self.opt["shell"]:
            self.opt["shell"] = "/bin/sh"

        if not self.opt["gecos"]:
            self.opt["gecos"] = "*udocker*"

    def _create_user(self, container_auth, host_auth):
        """if we need to create a new user then we first
        copy /etc/passwd and /etc/group to new files and them
        we add the user account into these copied files which
        later are binding/mapped/passed to the container. so
        setup this binding as well via hostauth.
        """
        if self.opt["containerauth"]:
            tmp_passwd = container_auth.passwd_file
            tmp_group = container_auth.group_file
            self.opt["hostauth"] = False
        else:
            FileUtil().umask(0o077)
            tmp_passwd = FileUtil("passwd").mktmp()
            tmp_group = FileUtil("group").mktmp()
            if self.opt["hostauth"]:
                FileUtil("/etc/passwd").copyto(tmp_passwd)
                FileUtil("/etc/group").copyto(tmp_group)
            else:
                FileUtil(container_auth.passwd_file).copyto(tmp_passwd)
                FileUtil(container_auth.group_file).copyto(tmp_group)

            FileUtil().umask()

        if not (self.opt["containerauth"] or self.opt["hostauth"]):
            LOG.warning("non-existing user will be created")
            self._fill_user()
            new_auth = NixAuthentication(tmp_passwd, tmp_group)
            new_auth.add_user(self.opt["user"], 'x', self.opt["uid"], self.opt["gid"],
                              self.opt["gecos"], self.opt["home"], self.opt["shell"])
            (group, dummy, dummy) = host_auth.get_group(self.opt["gid"])
            if not group:
                new_auth.add_group(self.opt["user"], self.opt["gid"])

            for sup_gid in os.getgroups():
                new_auth.add_group('g' + str(sup_gid), str(sup_gid), [self.opt["user"], ])

        if not self.opt["containerauth"]:
            self.opt["hostauth"] = True
            self.hostauth_list = (tmp_passwd + ":/etc/passwd", tmp_group + ":/etc/group")

        return True

    def _run_banner(self, cmd):
        """print a container startup banner"""
        if not self.opt["nobanner"]:
            msgout = 76*"#" + "\n"
            msgout = msgout + "|" + 74*" " + "|\n"
            msgout = msgout + "|"
            msgout = msgout + ("starting " + self.container_id).center(74, " ")
            msgout = msgout + "|" + "\n"
            msgout = msgout + "|" + 74*" " + "|\n"
            msgout = msgout + 76*"#" + "\n\n"
            msgout = msgout + "executing: " + os.path.basename(cmd) + "\n"
            msgout = msgout + 76*"_" + "\n"
            MSG.info(msgout)

    def _run_env_cleanup_dict(self):
        """allow only to pass essential environment variables."""
        environ_copy = os.environ.copy()
        for env_var in environ_copy:
            if env_var in Config.conf['invalid_host_env']:
                del os.environ[env_var]
                continue

            if not self.opt["hostenv"]:
                if env_var not in Config.conf['valid_host_env']:
                    del os.environ[env_var]

    def _run_env_cleanup_list(self):
        """ allow only to pass essential environment variables.
            overriding parent executionenginecommon() class.
        """
        container_env = self.opt["env"].keys()
        for (env_var, value) in list(os.environ.items()):
            if not env_var:
                continue

            if (env_var in Config.conf['invalid_host_env'] or env_var in container_env):
                continue

            if ((not self.opt["hostenv"]) and env_var not in Config.conf['valid_host_env']):
                continue

            self.opt["env"].append(f"{env_var}={value}")

    def _run_env_set(self):
        """environment variables to set"""
        self.opt["env"].appendif("home=" + self.opt["home"])
        self.opt["env"].append("user=" + self.opt["user"])
        self.opt["env"].append("logname=" + self.opt["user"])
        self.opt["env"].append("username=" + self.opt["user"])
        if str(self.opt["uid"]) == "0":
            self.opt["env"].append(fr'ps1={self.container_id[:8]} # ')
        else:
            self.opt["env"].append(fr'ps1={self.container_id[:8]} \$ ')

        self.opt["env"].append("shlvl=0")
        self.opt["env"].append("container_ruser=" + HostInfo().username())
        self.opt["env"].append("container_root=" + self.container_root)
        self.opt["env"].append("container_uuid=" + self.container_id)
        self.opt["env"].append("container_execmode=" + self.exec_mode.get_mode())
        cont_name = self.container_names
        names = str(cont_name).translate(str.maketrans('', '', " '\"[]"))
        self.opt["env"].append("container_names=" + names)

    def _run_env_cmdoptions(self):
        """load environment from file --env-file="""
        for envfile in self.opt["envfile"]:
            envdata = FileUtil(envfile).getdata('r')
            for line in envdata.split("\n"):
                self.opt["env"].appendif(line)

    def _check_platform(self):
        """Check if container platform matches the host"""
        container_platform = HostInfo().platform_to_str("%s/%s/%s" %
                                                        (self.container_os,
                                                         self.container_architecture,
                                                         self.container_variant))
        if not container_platform:
            return

        if not HostInfo().is_same_platform(container_platform):
            LOG.warning("container platform (%s) does not match host platform (%s)",
                        container_platform, HostInfo().platform())

    def _run_init(self, container_id):
        """prepare execution of the container
        to be called by the run() method of the actual executionengine
        """
        try:
            (container_dir, dummy) = self._run_load_metadata(container_id)
        except (ValueError, TypeError):
            return ""
        if not (container_dir or Config.conf['location']):
            return ""

        self._check_platform()

        self._run_env_cmdoptions()
        if Config.conf['location']:               # using specific root tree
            self.container_root = Config.conf['location']
        else:
            self.container_root = container_dir + "/ROOT"

        # container name(s) from container_id
        self.container_names = self.localrepo.get_container_name(container_id)
        self.container_id = container_id
        self.container_dir = container_dir

        # execution mode
        # self.exec_mode = ExecutionMode(self.localrepo, self.container_id)

        # check if exposing privileged ports
        self._check_exposed_ports()

        # which user to use inside the container and set up its account
        if not self._setup_container_user(self.opt["user"]):
            return ""

        # setup mountpoints
        self.mountp = MountPoint(self.localrepo, self.container_id)
        if not self._set_volume_bindings():
            return ""

        if not self._check_paths():
            return ""

        exec_path = self._check_executable()
        return exec_path

    def _get_saved_osenv(self, filename):
        """get saved osenv from json file"""
        try:
            return json.loads(FileUtil(filename).getdata())
        except (IOError, OSError, ValueError, TypeError):
            return {}

    def _is_same_osenv(self, filename):
        """Check if the host has changed"""
        saved = self._get_saved_osenv(filename)
        try:
            if (saved["osversion"] == HostInfo().osversion() and
                    saved["oskernel"] == HostInfo().oskernel() and
                    saved["arch"] == HostInfo().arch() and
                    saved["osdistribution"] == str(OSInfo("/").osdistribution())):
                return saved
        except (ValueError, TypeError, KeyError):
            pass

        return {}

    def _save_osenv(self, filename, save=None):
        """Save host info for is_same_host()"""
        if save is None:
            save = {}

        try:
            save["osversion"] = HostInfo().osversion()
            save["oskernel"] = HostInfo().oskernel()
            save["arch"] = HostInfo().arch()
            save["osdistribution"] = str(OSInfo("/").osdistribution())
            if FileUtil(filename).putdata(json.dumps(save)):
                return True
        except (ValueError, TypeError, IndexError, KeyError):
            pass

        return False

    def _check_arch(self, fail=False):
        """Check if architecture is the same"""
        same_arch = OSInfo(self.container_root).is_same_arch()
        if same_arch is None:
            return True
        if not same_arch:
            if fail:
                LOG.error("host and container architectures mismatch")
                return False
            LOG.warning("host and container architectures mismatch")
        return True

    def _get_qemu(self, return_path=False):
        """Get the qemu binary name if emulation needed"""
        container_qemu_arch = OSInfo(self.container_root).arch("qemu")
        host_qemu_arch = OSInfo("/").arch("qemu")
        if not (container_qemu_arch and host_qemu_arch):
            return ""
        if container_qemu_arch == host_qemu_arch:
            return ""
        qemu_filename = "qemu-%s" % container_qemu_arch
        qemu_path = FileUtil(qemu_filename).find_exec()
        if not qemu_path:
            LOG.error("qemu required but not available")
            return ""
        return qemu_path if return_path else qemu_filename
