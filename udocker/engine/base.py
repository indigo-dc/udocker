# -*- coding: utf-8 -*-
import os
import string
import re

from udocker.config import Config
from udocker.msg import Msg
from udocker.utils.fileutil import FileUtil
from udocker.helper.nixauth import NixAuthentication
from udocker.container.structure import ContainerStructure
from udocker.utils.filebind import FileBind
from udocker.engine.execmode import ExecutionMode


class ExecutionEngineCommon(object):
    """Docker container execution engine parent class
    Provides the container execution methods that are common to
    the execution drivers.
    """

    def __init__(self, localrepo):
        self.localrepo = localrepo               # LocalRepository instance
        self.container_id = ""                   # Container id
        self.container_dir = ""                  # Container directory
        self.container_root = ""                 # ROOT of container filesystem
        self.container_names = []                # Container names
        self.imagerepo = None                    # Imagerepo of container image
        self.hostauth_list = Config.hostauth_list  # passwd and group
        self.exec_mode = None                    # ExecutionMode instance
        # Metadata defaults
        self.opt = dict()                        # Run options
        self.opt["nometa"] = False               # Don't load metadata
        self.opt["nosysdirs"] = False            # Bind host dirs
        self.opt["dri"] = False                  # Directories needed for DRI
        self.opt["bindhome"] = False             # Bind user home dir
        self.opt["hostenv"] = False              # Pass host env
        self.opt["hostauth"] = False             # Use hostauth_list
        self.opt["novol"] = []                   # Volume bindings to ignore
        self.opt["env"] = []                     # Environment from container
        self.opt["vol"] = []                     # Volumes to mount
        self.opt["cpuset"] = ""                  # Container CPU affinity
        self.opt["user"] = ""                    # User to run in the container
        self.opt["cwd"] = ""                     # Default dir in the container
        self.opt["entryp"] = ""                  # Container entrypoint
        self.opt["cmd"] = Config.cmd             # Comand to execute
        self.opt["hostname"] = ""                # Hostname TBD
        self.opt["domain"] = ""                  # Host domainname TBD
        self.opt["volfrom"] = []                 # Mount vol from container TBD
        self.opt["portsmap"] = []                # Ports mapped in container
        self.opt["portsexp"] = []                # Ports exposed by container
        self.opt["devices"] = []                 # Devices passed to container

    def _get_portsmap(self, by_container=True):
        """List of TCP/IP ports mapped indexed by container port"""
        indexed_portmap = dict()
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
                    if port_number in mapped_ports.keys():
                        if mapped_ports[port_number] >= 1024:
                            continue
                    exposes_priv = True
        if exposes_priv and Config.uid != 0:
            Msg().err("Error: this container exposes privileged TCP/IP ports")
            return False
        if exposes_port:
            Msg().err("Warning: this container exposes TCP/IP ports", l=Msg.WAR)
        return True

    def _set_cpu_affinity(self):
        """Set the cpu affinity string for container run command"""
        # find set affinity executable
        if not self.opt["cpuset"]:
            return []
        exec_cmd = []
        for exec_cmd in Config.cpu_affinity_exec_tools:
            exec_name = \
                FileUtil(exec_cmd[0]).find_exec()
            if exec_name:
                exec_cmd[0] = exec_name
                for (index, arg) in enumerate(exec_cmd):
                    if arg == "%s":
                        exec_cmd[index] = self.opt["cpuset"]
                return exec_cmd
        self.opt["cpuset"] = ""
        return []

    def _cleanpath(self, pathname):
        """Remove duplicate and trailing slashes"""
        clean_path = ""
        p_char = ''
        for char in str(pathname):
            if not clean_path:
                clean_path = char
            else:
                if not (char == p_char and char == '/'):
                    clean_path += char
            p_char = char
        if clean_path == "/":
            return clean_path
        else:
            return clean_path.rstrip('/')

    def _vol_split(self, vol):
        """Split volume string host_path:container_path into list"""
        try:
            (host_dir, cont_dir) = vol.split(":", 1)
            if not cont_dir:
                cont_dir = host_dir
        except ValueError:
            host_dir = vol
            cont_dir = vol
        return (self._cleanpath(host_dir), self._cleanpath(cont_dir))

    def _cont2host(self, pathname):
        """Translate container path to host path"""
        if not (pathname and pathname.startswith("/")):
            return ""
        path = ""
        real_container_root = os.path.realpath(self.container_root)
        pathname = re.sub("/+", "/", os.path.normpath(pathname))
        for vol in self.opt["vol"]:
            (host_path, cont_path) = self._vol_split(vol)
            if cont_path != host_path:
                if pathname.startswith(cont_path):
                    path = host_path + pathname[len(cont_path):]
                    break
            elif pathname.startswith(host_path):
                path = pathname
                break
        if not path:
            path = real_container_root + "/" + pathname
        f_path = ""
        for d_comp in path.split("/")[1:]:
            f_path = f_path + "/" + d_comp
            while os.path.islink(f_path):
                real_path = os.readlink(f_path)
                if real_path.startswith("/"):
                    if f_path.startswith(real_container_root): # in container
                        if real_path.startswith(real_container_root):
                            f_path = real_path
                        else:
                            f_path = real_container_root + real_path
                    else:
                        f_path = real_path
                else:
                    f_path = os.path.dirname(f_path) + "/" + real_path
        return os.path.realpath(f_path)

    def _create_mountpoint(self, host_path, cont_path):
        """Create mountpoint"""
        mountpoint = self.container_root + cont_path
        if not os.path.exists(host_path):
            return False
        if os.path.exists(mountpoint):
            return True
        if os.path.isfile(host_path):
            return FileUtil(mountpoint).putdata("")
        elif os.path.isdir(host_path):
            return FileUtil(mountpoint).mkdir()
        return False

    def _check_volumes(self):
        """Check volume paths"""
        for vol in list(self.opt["vol"]):
            (host_path, cont_path) = self._vol_split(vol)
            if not host_path:
                Msg().err("Error: invalid volume host directory:", host_path)
                return False
            if cont_path and not cont_path.startswith("/"):
                Msg().err("Error: invalid volume container directory:", cont_path)
                return False
            if host_path and not host_path.startswith("/"):
                Msg().err("Error: invalid volume host directory:", host_path)
                return False
            if not os.path.exists(host_path):
                if (host_path in Config.dri_list or
                        host_path in Config.sysdirs_list or
                        host_path in Config.hostauth_list):
                    self.opt["vol"].remove(vol)
                else:
                    Msg().err("Error: invalid host volume path:", host_path)
                    return False
            self._create_mountpoint(host_path, cont_path)
        return True

    def _get_bindhome(self):
        """Binding of the host $HOME in to the container $HOME"""
        if self.opt["bindhome"]:
            return NixAuthentication().get_home()
        return ""

    def _is_volume(self, path):
        """Is path a host_path in the volumes list"""
        for vol in list(self.opt["vol"]):
            (host_path, dummy) = self._vol_split(vol)
            if host_path and host_path == self._cleanpath(path):
                return True
        return False

    def _set_volume_bindings(self):
        """Set the volume bindings string for container run command"""
        # predefined volume bindings --sysdirs --hostauth --dri
        if not self.opt["nosysdirs"]:
            self.opt["vol"].extend(Config.sysdirs_list)
        if self.opt["hostauth"]:
            self.opt["vol"].extend(self.hostauth_list)
        if self.opt["dri"]:
            self.opt["vol"].extend(Config.dri_list)
        home = self._get_bindhome()
        if home:
            self.opt["vol"].append(home)
        # remove directory bindings specified with --novol
        for novolume in list(self.opt["novol"]):
            found = False
            for vol in list(self.opt["vol"]):
                if novolume == vol or novolume == vol.split(":")[0]:
                    self.opt["vol"].remove(vol)
                    found = True
            if not found:
                Msg().err("Warning: --novol %s not in volumes list" %
                          novolume, l=Msg.WAR)
        return self._check_volumes()

    def _check_paths(self):
        """Make sure we have a reasonable default PATH and CWD"""
        if not self._getenv("PATH"):
            if self.opt["uid"] == "0":
                path = Config.root_path
            else:
                path = Config.user_path
            self.opt["env"].append("PATH=%s" % path)
        # verify if the working directory is valid and fix it
        if not self.opt["cwd"]:
            self.opt["cwd"] = self.opt["home"]
        if os.path.isdir(self._cont2host(self.opt["cwd"])):
            return True
        Msg().err("Error: invalid working directory: ", self.opt["cwd"])
        return False

    def _check_executable(self):
        """Check if executable exists and has execute permissions"""
        exec_path_list = []
        path = self._getenv("PATH")
        if self.opt["entryp"] and isinstance(self.opt["entryp"], str):
            self.opt["cmd"] = self.opt["entryp"].strip().split(" ")
        elif self.opt["entryp"] and isinstance(self.opt["entryp"], list):
            if self.opt["cmd"]:                                     # and cmd
                cmd_args = self.opt["cmd"]
                self.opt["cmd"] = self.opt["entryp"]
                self.opt["cmd"].extend(cmd_args)   # cmd=args entryp
            else:
                self.opt["cmd"] = self.opt["entryp"]
        if not self.opt["cmd"]:
            self.opt["cmd"] = Config.cmd
            Msg().err("Warning: no command assuming:", self.opt["cmd"],
                      l=Msg.WAR)
        exec_name = self.opt["cmd"][0]            # exec pathname without args
        if exec_name.startswith("/"):
            exec_path_list.append(exec_name)
        elif exec_name.startswith("./") or exec_name.startswith("../"):
            exec_path_list.append(self.opt["cwd"] + "/" + exec_name)
        else:
            exec_path_list = \
                FileUtil(exec_name).list_inpath(path, "/")
        for exec_path in exec_path_list:
            host_exec_path = self._cont2host(exec_path)
            if (os.path.isfile(host_exec_path) and
                    os.access(host_exec_path, os.X_OK)):
                return self.container_root + "/" + exec_path
        Msg().err("Error: command not found or has no execute bit set: ",
                  self.opt["cmd"])
        return ""

    def _run_load_metadata(self, container_id):
        """Load container metadata from container JSON payload"""
        # get container metadata unless we are dealing with a simple directory
        # tree in which case we don't have metadata
        if Config.location:
            container_dir = ""
            container_json = []
        else:
            container_structure = \
                ContainerStructure(self.localrepo, container_id)
            (container_dir, container_json) = \
                container_structure.get_container_attr()
            if not container_dir:
                return(None, None)
            # load metadata from container
            if not self.opt["nometa"]:
                if not self.opt["user"]:
                    self.opt["user"] = \
                        container_structure.get_container_meta(
                            "User", "", container_json)
                if not self.opt["cwd"]:
                    self.opt["cwd"] = \
                        container_structure.get_container_meta(
                            "WorkingDir", "", container_json)
                if not self.opt["hostname"]:
                    self.opt["hostname"] = \
                        container_structure.get_container_meta(
                            "Hostname", "", container_json)
                if not self.opt["domain"]:
                    self.opt["domain"] = \
                        container_structure.get_container_meta(
                            "Domainname", "", container_json)
                if not self.opt["cmd"]:
                    self.opt["cmd"] = \
                        container_structure.get_container_meta(
                            "Cmd", [], container_json)
                if not self.opt["entryp"]:
                    self.opt["entryp"] = \
                        container_structure.get_container_meta(
                            "Entrypoint", [], container_json)
                self.opt["Volumes"] = \
                    container_structure.get_container_meta(
                        "Volumes", [], container_json)
                self.opt["portsexp"].extend(
                    container_structure.get_container_meta(
                        "ExposedPorts", [], container_json))
                meta_env = \
                    container_structure.get_container_meta(
                        "Env", [], container_json)
                if meta_env:
                    meta_env.extend(self.opt["env"])
                    self.opt["env"] = meta_env
        return(container_dir, container_json)

    def _check_env(self):
        """Sanitize the environment variables"""
        for pair in list(self.opt["env"]):
            if not pair:
                self.opt["env"].remove(pair)
                continue
            if "=" not in pair:
                self.opt["env"].remove(pair)
                val = os.getenv(pair, "")
                if val:
                    self.opt["env"].append('%s=%s' % (pair, val))
                continue
            (key, val) = pair.split("=", 1)
            if " " in key or key[0] in string.digits:
                Msg().err("Error: in environment:", pair)
                return False
            if " " in pair and "'" not in pair and '"' not in pair:
                self.opt["env"].remove(pair)
                self.opt["env"].append('%s=%s' % (key, val))
        return True

    def _getenv(self, search_key):
        """A getenv() for the container environment metadata."""
        for pair in self.opt["env"]:
            if pair:
                if "=" in pair:
                    (key, val) = pair.split("=", 1)
                else:
                    key = pair
                    val = ""
                if key == search_key:
                    return str(val)
        return None

    def _uid_gid_from_str(self, expression):
        """Parse strings containing uid:gid"""
        uid = None
        gid = None
        try:
            match = re.match("^(\\d+):(\\d+)$", expression)
            uid = match.group(1)
            gid = match.group(2)
        except AttributeError:
            Msg().err("Error: invalid syntax user must be uid:gid or username")
        return (uid, gid)

    def _select_auth_files(self):
        """Select authentication files to use /etc/passwd /etc/group"""
        cont_passwd = self.container_root + "/etc/passwd"
        cont_group = self.container_root + "/etc/group"
        bind_passwd = self.container_dir + FileBind.orig_dir + "/#etc#passwd"
        bind_group = self.container_dir + FileBind.orig_dir + "/#etc#group"
        #
        if os.path.islink(cont_passwd) and os.path.isfile(bind_passwd):
            passwd = bind_passwd
        else:
            passwd = cont_passwd
        if os.path.islink(cont_group) and os.path.isfile(bind_group):
            group = bind_group
        else:
            group = cont_group
        return (passwd, group)

    def _setup_container_user(self, user):
        """Once we know which username to use inside the container
        we need to check if it exists in the passwd file that will
        be used inside the container. Since we can override the
        usage of the container /etc/passwd and /etc/group with
        files passed from the host, then we must check if this
        username is in the appropriate file so:
        1. check if the passwd will be the one of the host system
           either because we passwd --hostauth or because we did
           --volume=/etc/passwd:/etc/passwd
        2. else we are using the container original /etc/passwd
        In either case the user specified may not exist, in which
        case we copy the passwd file to a new file and we create
        the intended user. The file is then passwd/mapped into
        the container.
        """
        self.opt["user"] = "root"
        self.opt["uid"] = "0"
        self.opt["gid"] = "0"
        self.opt["home"] = "/"
        self.opt["gecos"] = ""
        self.opt["shell"] = ""
        host_auth = NixAuthentication()
        (passwd, group) = self._select_auth_files()
        container_auth = NixAuthentication(passwd, group)
        if not user:
            user = self.opt["user"]
        if ":" in user:
            (found_uid, found_gid) = self._uid_gid_from_str(user)
            if found_gid is None:
                return False
            if "/etc/passwd" in self.opt["vol"] or self.opt["hostauth"]:
                (found_user, dummy, dummy, found_gecos, found_home,
                 found_shell) = host_auth.get_user(found_uid)
            else:
                (found_user, dummy, dummy,
                 found_gecos, found_home, found_shell) = \
                    container_auth.get_user(found_uid)
        else:
            if "/etc/passwd" in self.opt["vol"] or self.opt["hostauth"]:
                (found_user, found_uid, found_gid, found_gecos, found_home,
                 found_shell) = host_auth.get_user(user)
            else:
                (found_user, found_uid, found_gid,
                 found_gecos, found_home, found_shell) = \
                    container_auth.get_user(user)
        if found_user:
            self.opt["user"] = found_user
            self.opt["uid"] = found_uid
            self.opt["gid"] = found_gid
            self.opt["home"] = found_home
            self.opt["gecos"] = found_gecos
            self.opt["shell"] = found_shell
        else:
            if "/etc/passwd" in self.opt["vol"] or self.opt["hostauth"]:
                Msg().err("Error: user not found")
                return False
            else:
                if ":" not in user:
                    self.opt["user"] = user
                    self.opt["uid"] = ""
                    self.opt["gid"] = ""
                elif self.opt["uid"] > 0:
                    self.opt["user"] = ""
                Msg().err("Warning: non-existing user will be created",
                          l=Msg.WAR)
        self._create_user(container_auth, host_auth)
        return True

    def _create_user(self, container_auth, host_auth):
        """If we need to create a new user then we first
        copy /etc/passwd and /etc/group to new files and them
        we add the user account into these copied files which
        later are binding/mapped/passed to the container. So
        setup this binding as well via hostauth.
        """
        FileUtil().umask(0o077)
        tmp_passwd = FileUtil("passwd").mktmp()
        tmp_group = FileUtil("group").mktmp()
        FileUtil(container_auth.passwd_file).copyto(tmp_passwd)
        FileUtil(container_auth.group_file).copyto(tmp_group)
        FileUtil().umask()
        if not self.opt["uid"]:
            self.opt["uid"] = str(Config.uid)
        if not self.opt["gid"]:
            self.opt["gid"] = str(Config.gid)
        if not self.opt["user"]:
            self.opt["user"] = "udoc" + self.opt["uid"][0:4]
        if self.opt["user"] == "root":
            self.opt["home"] = "/"
        elif not self.opt["home"]:
            self.opt["home"] = "/home/" + self.opt["user"]
        if not self.opt["shell"]:
            self.opt["shell"] = "/bin/sh"
        if not self.opt["gecos"]:
            self.opt["gecos"] = "*UDOCKER*"
        new_auth = NixAuthentication(tmp_passwd, tmp_group)
        if (not new_auth.add_user(self.opt["user"], "x",
                                  self.opt["uid"], self.opt["gid"],
                                  self.opt["gecos"], self.opt["home"],
                                  self.opt["shell"])):
            return False
        (group, dummy, dummy) = host_auth.get_group(self.opt["gid"])
        if not group:
            group = self.opt["user"]
        new_auth.add_group(group, self.opt["gid"])
        for sup_gid in os.getgroups():
            new_auth.add_group("G" + str(sup_gid), str(sup_gid))
        self.opt["hostauth"] = True
        self.hostauth_list = (tmp_passwd + ":/etc/passwd",
                              tmp_group + ":/etc/group")
        return True

    def _uid_check_noroot(self):
        """Set the uid_map string for engines without root support
        """
        if ("user" not in self.opt or (not self.opt["user"]) or
                self.opt["user"] == "root" or self.opt["user"] == "0"):
            Msg().err("Warning: running as uid 0 is not supported by this engine",
                      l=Msg.WAR)
            self.opt["user"] = Config().username()

    def _setup_container_user_noroot(self, user):
        """ Setup user for engines without root support.
        Equivalent to _setup_container_user() for engines without root support.
        """
        self.opt["user"] = Config().username()
        self.opt["uid"] = str(Config.uid)
        self.opt["gid"] = str(Config.gid)
        self.opt["home"] = "/"
        self.opt["gecos"] = ""
        self.opt["shell"] = ""
        host_auth = NixAuthentication()
        container_auth = NixAuthentication(self.container_root + "/etc/passwd",
                                           self.container_root + "/etc/group")
        if not user:
            user = self.opt["user"]
        if ":" in user:
            (found_uid, found_gid) = self._uid_gid_from_str(user)
            if found_gid is None:
                return False
            if "/etc/passwd" in self.opt["vol"] or self.opt["hostauth"]:
                (found_user, dummy, dummy, found_gecos, found_home,
                 found_shell) = host_auth.get_user(found_uid)
            else:
                (found_user, dummy, dummy,
                 found_gecos, found_home, found_shell) = \
                    container_auth.get_user(found_uid)
        else:
            if "/etc/passwd" in self.opt["vol"] or self.opt["hostauth"]:
                (found_user, dummy, dummy, found_gecos, found_home,
                 found_shell) = host_auth.get_user(user)
            else:
                (found_user, dummy, dummy,
                 found_gecos, found_home, found_shell) = \
                    container_auth.get_user(user)
        if found_user:
            self.opt["user"] = found_user
            self.opt["home"] = found_home
            self.opt["gecos"] = found_gecos
            self.opt["shell"] = found_shell
        else:
            if "/etc/passwd" in self.opt["vol"] or self.opt["hostauth"]:
                Msg().err("Error: user not found")
                return False
            else:
                if ":" not in user:
                    self.opt["user"] = user
                Msg().err("Warning: non-existing user will be created",
                          l=Msg.WAR)
        self._create_user(container_auth, host_auth)
        return True

    def _run_banner(self, cmd, char="*"):
        """Print a container startup banner"""
        Msg().err("",
                  "\n", char * 78,
                  "\n", char, " " * 74, char,
                  "\n", char,
                  ("STARTING " + self.container_id).center(74, " "), char,
                  "\n", char, " " * 74, char,
                  "\n", char * 78, "\n",
                  "executing:", os.path.basename(cmd), l=Msg.INF)

    def _run_env_cleanup_dict(self):
        """Allow only to pass essential environment variables."""
        environ_copy = os.environ.copy()
        for env_var in environ_copy:
            if env_var in Config.invalid_host_env:
                del os.environ[env_var]
                continue
            if not self.opt["hostenv"]:
                if env_var not in Config.valid_host_env:
                    del os.environ[env_var]

    def _run_env_cleanup_list(self):
        """ Allow only to pass essential environment variables.
            Overriding parent ExecutionEngineCommon() class.
        """
        container_env = []
        for env_str in self.opt["env"]:
            (env_var, dummy) = env_str.split("=", 1)
            if env_var:
                container_env.append(env_var)
        for (env_var, value) in os.environ.iteritems():
            if not env_var:
                continue
            if env_var in Config.invalid_host_env or env_var in container_env:
                continue
            if ((not self.opt["hostenv"]) and
                    env_var not in Config.valid_host_env):
                continue
            self.opt["env"].append("%s=%s" % (env_var, value))

    def _run_env_get(self):
        """Get environment list"""
        env_dict = dict()
        for env_pair in self.opt["env"]:
            (key, val) = env_pair.split("=", 1)
            env_dict[key] = val
        return env_dict

    def _run_env_set(self):
        """Environment variables to set"""
        if not any(entry.startswith("HOME=") for entry in self.opt["env"]):
            self.opt["env"].append("HOME=" + self.opt["home"])
        self.opt["env"].append("USER=" + self.opt["user"])
        self.opt["env"].append("LOGNAME=" + self.opt["user"])
        self.opt["env"].append("USERNAME=" + self.opt["user"])

        if  str(self.opt["uid"]) == "0":
            self.opt["env"].append(r"PS1=%s# " % self.container_id[:8])
        else:
            self.opt["env"].append(r"PS1=%s\$ " % self.container_id[:8])

        self.opt["env"].append("SHLVL=0")
        self.opt["env"].append("container_ruser=" + Config().username())
        self.opt["env"].append("container_root=" + self.container_root)
        self.opt["env"].append("container_uuid=" + self.container_id)
        self.opt["env"].append("container_execmode=" + self.exec_mode.get_mode())
        names = str(self.container_names).translate(None, " '\"[]")
        self.opt["env"].append("container_names=" + names)

    def _run_init(self, container_id):
        """Prepare execution of the container
        To be called by the run() method of the actual ExecutionEngine
        """
        try:
            (container_dir, dummy) = \
                self._run_load_metadata(container_id)
        except (ValueError, TypeError):
            return ""

        if Config.location:                   # using specific root tree
            self.container_root = Config.location
        else:
            self.container_root = container_dir + "/ROOT"

        # container name(s) from container_id
        self.container_names = self.localrepo.get_container_name(container_id)
        self.container_id = container_id
        self.container_dir = container_dir

        # execution mode
        self.exec_mode = ExecutionMode(self.localrepo, self.container_id)

        # check if exposing privileged ports
        self._check_exposed_ports()

        # which user to use inside the container and setup its account
        if not self._setup_container_user(self.opt["user"]):
            return ""

        if not self._set_volume_bindings():
            return ""

        if not self._check_paths():
            return ""

        exec_path = self._check_executable()

        return exec_path
