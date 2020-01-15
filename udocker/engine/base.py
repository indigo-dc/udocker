# -*- coding: utf-8 -*-
"""Superclass for the execution engines"""

import os
import sys
import string
import re

from udocker.msg import Msg
from udocker.config import Config
from udocker.utils.fileutil import FileUtil
from udocker.helper.nixauth import NixAuthentication
from udocker.helper.hostinfo import HostInfo
from udocker.container.structure import ContainerStructure
from udocker.utils.filebind import FileBind
from udocker.utils.mountpoint import MountPoint

# Python version major.minor
PY_VER = "%d.%d" % (sys.version_info[0], sys.version_info[1])


class ExecutionEngineCommon(object):
    """Docker container execution engine parent class
    Provides the container execution methods that are common to
    the execution drivers.
    """

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
        # Metadata defaults
        self.opt = dict()                     # Run options
        self.opt["nometa"] = False            # Don't load metadata
        self.opt["nosysdirs"] = False         # Bind host dirs
        self.opt["dri"] = False               # Directories needed for DRI
        self.opt["bindhome"] = False          # Bind user home dir
        self.opt["hostenv"] = False           # Pass host env
        self.opt["hostauth"] = False          # Use hostauth_list
        self.opt["containerauth"] = False     # Authentication from container
        self.opt["novol"] = []                # Volume bindings to ignore
        self.opt["env"] = []                  # Environment from container
        self.opt["envfile"] = []              # File with environment variables
        self.opt["vol"] = []                  # Volumes to mount
        self.opt["cpuset"] = ""               # Container CPU affinity
        self.opt["user"] = ""                 # User to run in the container
        self.opt["cwd"] = ""                  # Default dir in the container
        self.opt["entryp"] = ""               # Container entrypoint
        self.opt["cmd"] = Config.conf['cmd']  # Comand to execute
        self.opt["hostname"] = ""             # Hostname TBD
        self.opt["domain"] = ""               # Host domainname TBD
        self.opt["volfrom"] = []              # Mount vol from container TBD
        self.opt["portsmap"] = []             # Ports mapped in container
        self.opt["portsexp"] = []             # Ports exposed by container
        self.opt["devices"] = []              # Devices passed to container

    def _has_option(self, search_option, arg=None):
        """Check if executable has a given cli option"""
        return HostInfo().cmd_has_option(self.executable, search_option, arg)

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
                    if port_number in list(mapped_ports.keys()):
                        if mapped_ports[port_number] >= 1024:
                            continue
                    exposes_priv = True
        if exposes_priv and HostInfo.uid != 0:
            Msg().err("Error: this container exposes privileged TCP/IP ports")
            return False
        if exposes_port:
            Msg().out("Warning: this container exposes TCP/IP ports", l=Msg.WAR)
        return True

    def _set_cpu_affinity(self):
        """Set the cpu affinity string for container run command"""
        # find set affinity executable
        if not self.opt["cpuset"]:
            return []
        exec_cmd = []
        for exec_cmd in Config.conf['cpu_affinity_exec_tools']:
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
            (host_path, cont_path) = self._vol_split(vol)
            if not (host_path and host_path.startswith('/')):
                Msg().err("Error: invalid host volume path:", host_path)
                return False
            if not (cont_path and cont_path != '/' and
                    cont_path.startswith('/')):
                Msg().err("Error: invalid container volume path:", cont_path)
                return False
            if not os.path.exists(host_path):
                if (host_path in Config.conf['dri_list'] or
                        host_path in Config.conf['sysdirs_list']):
                    self.opt["vol"].remove(vol)
                else:
                    Msg().err("Error: invalid host volume path:", host_path)
                    return False
            if not self._create_mountpoint(host_path, cont_path):
                Msg().err("Error: creating mountpoint:", host_path, cont_path)
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
            (host_path, cont_path) = self._vol_split(vol)
            if host_path and host_path == self._cleanpath(path):
                return cont_path
        return ""

    def _is_mountpoint(self, path):
        """Is path a host_path in the volumes list"""
        for vol in list(self.opt["vol"]):
            (host_path, cont_path) = self._vol_split(vol)
            if cont_path and cont_path == self._cleanpath(path):
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
                Msg().err("Warning: --novol %s not in volumes list" %
                          novolume, l=Msg.WAR)
        return self._check_volumes()

    def _check_paths(self):
        """Make sure we have a reasonable default PATH and CWD"""
        if not self._getenv("PATH"):
            if self.opt["uid"] == "0":
                path = Config.conf['root_path']
            else:
                path = Config.conf['user_path']
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
            self.opt["cmd"] = Config.conf['cmd']
            Msg().out("Warning: no command assuming:", self.opt["cmd"],
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
        if Config.conf['location']:
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
            # check: Why this conditional is not for runc
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
        if self._is_mountpoint("/etc/passwd"):
            passwd = self._is_mountpoint("/etc/passwd")
        if self._is_mountpoint("/etc/group"):
            group = self._is_mountpoint("/etc/group")
        return (passwd, group)

    def _validate_user_str(self, user):
        """Parse string with uid:gid or username"""
        user_id = dict()
        if not isinstance(user, str):
            return user_id
        if re.match("^[a-zA-Z_][a-zA-Z0-9_-]*$", user):
            user_id["user"] = user
            return user_id
        else:
            match = re.match("^(\\d+)(:(\\d+)){0,1}$", user)
            if match:
                user_id["uid"] = match.group(1)
                if match.group(3):
                    user_id["gid"] = match.group(3)
        return user_id

    def _user_from_str(self, user, host_auth=None, container_auth=None):
        """user password entry from host or container passwd
           Returns (valid_user: bool, user_passwd_fields: dict)
        """
        user_id = self._validate_user_str(user)
        if not user_id:
            return (False, user_id)
        search_field = user_id.get("uid", user_id["user"])
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
        host_auth = NixAuthentication()
        (passwd, group) = self._select_auth_files()
        container_auth = NixAuthentication(passwd, group)
        if not user:
            user = "root"
        (valid_user, user_id) = self._user_from_str(user,
                                                    host_auth, container_auth)
        if not valid_user:
            Msg().err("Error: invalid syntax for user", user)
            return False
        if (self._is_mountpoint("/etc/passwd") or
                self._is_mountpoint("/etc/group")):
            self.opt["hostauth"] = self.opt["containerauth"] = False
            return True
        if self.opt["user"]:
            if self.opt["user"] != "root":
                self.opt["uid"] = str(HostInfo.uid)
                self.opt["gid"] = str(HostInfo.gid)
        else:
            if self.opt["hostauth"] or self.opt["containerauth"]:
                Msg().err("Error: user not found")
                return False
            self.opt["user"] = user_id["user"] if "user" in user_id else user
            self.opt["uid"] = user_id["uid"] if "uid" in user_id else ""
            self.opt["gid"] = user_id["gid"] if "gid" in user_id else ""
        self._create_user(container_auth, host_auth)
        return True

    def _setup_container_user_noroot(self, user):
        """ Setup user for engines without root support.
        Equivalent to _setup_container_user() for engines without root support.
        """
        host_auth = NixAuthentication()
        (passwd, group) = self._select_auth_files()
        container_auth = NixAuthentication(passwd, group)
        if not user:
            user = HostInfo().username()
        (valid_user, user_id) = self._user_from_str(user,
                                                    host_auth, container_auth)
        if not valid_user:
            Msg().err("Error: invalid syntax for user", user)
            return False
        if self.opt["user"] == "root":
            self.opt["user"] = HostInfo().username()
            self.opt["uid"] = str(HostInfo.uid)
            self.opt["gid"] = str(HostInfo.gid)
        if (self._is_mountpoint("/etc/passwd") or
                self._is_mountpoint("/etc/group")):
            self.opt["hostauth"] = self.opt["containerauth"] = False
            return True
        if self.opt["user"]:
            self.opt["uid"] = str(HostInfo.uid)
            self.opt["gid"] = str(HostInfo.gid)
        else:
            if self.opt["hostauth"] or self.opt["containerauth"]:
                Msg().err("Error: user not found on host")
                return False
            self.opt["user"] = user_id["user"] if "user" in user_id else user
            self.opt["uid"] = user_id["uid"] if "uid" in user_id else ""
            self.opt["gid"] = user_id["gid"] if "gid" in user_id else ""
        self._create_user(container_auth, host_auth)
        return True

    def _fill_user(self):
        """Fill in values for user to be used in the account creation.
        Provide default values in case the required fields are empty.
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
            self.opt["gecos"] = "*UDOCKER*"

    def _create_user(self, container_auth, host_auth):
        """If we need to create a new user then we first
        copy /etc/passwd and /etc/group to new files and them
        we add the user account into these copied files which
        later are binding/mapped/passed to the container. So
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
            Msg().out("Warning: non-existing user will be created",
                      l=Msg.WAR)
            self._fill_user()
            new_auth = NixAuthentication(tmp_passwd, tmp_group)
            new_auth.add_user(self.opt["user"], 'x',
                              self.opt["uid"], self.opt["gid"],
                              self.opt["gecos"], self.opt["home"],
                              self.opt["shell"])
            (group, dummy, dummy) = host_auth.get_group(self.opt["gid"])
            if not group:
                new_auth.add_group(self.opt["user"], self.opt["gid"])
            for sup_gid in os.getgroups():
                new_auth.add_group('G' + str(sup_gid), str(sup_gid),
                                   [self.opt["user"], ])
        if not self.opt["containerauth"]:
            self.opt["hostauth"] = True
            self.hostauth_list = (tmp_passwd + ":/etc/passwd",
                                  tmp_group + ":/etc/group")
        return True

    def _run_banner(self, cmd, char="*"):
        """Print a container startup banner"""
        Msg().out("",
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
            if env_var in Config.conf['invalid_host_env']:
                del os.environ[env_var]
                continue
            if not self.opt["hostenv"]:
                if env_var not in Config.conf['valid_host_env']:
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
        for (env_var, value) in list(os.environ.items()):
            if not env_var:
                continue
            if   (env_var in Config.conf['invalid_host_env'] or
                  env_var in container_env):
                continue
            if   ((not self.opt["hostenv"]) and
                  env_var not in Config.conf['valid_host_env']):
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

        if str(self.opt["uid"]) == "0":
            self.opt["env"].append(r"PS1=%s# " % self.container_id[:8])
        else:
            self.opt["env"].append(r"PS1=%s\$ " % self.container_id[:8])

        self.opt["env"].append("SHLVL=0")
        self.opt["env"].append("container_ruser=" + HostInfo().username())
        self.opt["env"].append("container_root=" + self.container_root)
        self.opt["env"].append("container_uuid=" + self.container_id)
        self.opt["env"].append("container_execmode=" +
                               self.exec_mode.get_mode())
        cont_name = self.container_names
        if PY_VER >= "3":
            names = str(cont_name).translate(str.maketrans('', '', " '\"[]"))
        else:
            names = str(cont_name).translate(None, " '\"[]")

        self.opt["env"].append("container_names=" + names)

    def _run_env_cmdoptions(self):
        """Load environment from file --env-file="""
        for envfile in self.opt["envfile"]:
            envdata = FileUtil(envfile).getdata()
            for line in envdata.split("\n"):
                try:
                    (key, val) = line.split("=", 2)
                except (ValueError, NameError, AttributeError):
                    continue
                for quote in ("'", '"'):
                    if quote == val[0]:
                        val = val.strip(quote)
                self.opt["env"].append(key + "=" + val)

    def _run_init(self, container_id):
        """Prepare execution of the container
        To be called by the run() method of the actual ExecutionEngine
        """
        try:
            (container_dir, dummy) = \
                self._run_load_metadata(container_id)
        except (ValueError, TypeError):
            return ""

        if not (container_dir or Config.conf['location']):
            return ""

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
        #self.exec_mode = ExecutionMode(self.localrepo, self.container_id)

        # check if exposing privileged ports
        self._check_exposed_ports()

        # which user to use inside the container and setup its account
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
