#!/usr/bin/env python
"""
========
udocker
========
Wrapper to execute basic docker containers without using docker.
This tool is a last resort for the execution of docker containers
where docker is unavailable. It only provides a limited set of
functionalities.

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""
import sys
import os
import cStringIO
import string
import re
import subprocess
import time
import pwd
import platform

__author__ = "udocker@lip.pt"
__credits__ = ["PRoot http://proot.me"]
__license__ = "Licensed under the Apache License, Version 2.0"
__version__ = "0.0.1-1"
__date__ = "2016"

# Python version major.minor
PY_VER = "%d.%d" % (sys.version_info[0], sys.version_info[1])

if os.path.islink(sys.argv[0]):
    START_PATH = os.path.dirname(os.readlink(sys.argv[0]))
else:
    START_PATH = os.path.dirname(sys.argv[0])

try:
    import pycurl
except ImportError:
    pass
try:
    import uuid
except ImportError:
    pass
try:
    import random
except ImportError:
    pass
try:
    import json
except ImportError:
    pass
if PY_VER < "2.6":
    try:
        import posixpath
    except ImportError:
        pass


def import_modules():
    """Import modules for which we provide an alternative"""
    global json                    # pylint: disable=invalid-name
    sys.path.append(START_PATH + "/../lib/simplejson")
    sys.path.append(str(os.getenv("HOME")) + "/.udocker/lib/simplejson")
    sys.path.append(str(os.getenv("UDOCKER")) + "/.udocker/lib/simplejson")
    try:
        dummy = json.loads("[]")
    except NameError:
        try:
            # pylint: disable=redefined-outer-name,import-error
            import simplejson as json
        except ImportError:
            pass


class Config(object):
    """Default configuration values for the whole application. Changes
    to these values should be made via a configuration file read via
    self.user_init() and that can reside in ~/.udocker/udocker.conf
    """

    # pylint: disable=too-many-instance-attributes
    def __init__(self):
        """Initial default values. Can be overloaded by user_init()"""
        self.verbose_level = 0
        self.def_topdir = os.getenv("UDOCKER_DIR")
        if not self.def_topdir:
            if os.getenv("HOME"):                 # default home dir
                self.def_topdir = os.getenv("HOME") + "/.udocker"
            else:
                msg.out("Error: environment variable $HOME not defined")
                sys.exit(1)
        self.config_file = ""
        self.user_config = "udocker.conf"

        # for tmp files only
        self.tmpdir = "/tmp"
        self.tmptrash = dict()

        # tarball containing auxiliary files (PROOT, simplejson, etc)
        self.tarball_url = (
            "https://owncloud.indigo-datacloud.eu/index.php"
            "/s/TOZkjHmw0jHsUS2/download"
        )
        self.osver = self._osversion()
        self.arch = self._sysarch()
        if self.arch == "amd64":
            self.proot_exec = "proot-x86_64"
        elif self.arch == "i386":
            self.proot_exec = "proot-x86"
        self.kernel = self._oskernel()

        # defaults for container execution
        self.cmd = ["/bin/bash", "-i"]  # Comand to execute

        # directories to be mapped in contaners with: run --sysdirs
        self.sysdirs_list = (
            "/dev", "/proc", "/sys",
            "/etc/resolv.conf", "/etc/host.conf",
            "/lib/modules",
        )

        # directories to be mapped in contaners with: run --hostauth
        self.hostauth_list = (
            "/etc/passwd", "/etc/group",
            "/etc/shadow", "/etc/gshadow",
        )

        # directories for DRI (direct rendering)
        self.dri_list = (
            "/usr/lib/dri", "/lib/dri",
            "/usr/lib64/dri", "/lib64/dri",
        )

        # CPU affinity executables to use with: run --cpuset-cpus="1,2,3-4"
        self.cpu_affinity_exec_tools = ("taskset -c ", "numactl -C ")

        # Containers execution defaults
        self.location = ""         # run os in a ROOT dir

        # Curl settings
        self.http_proxy = ""    # ex. socks5://user:pass@127.0.0.1:1080
        self.timeout = 12       # default timeout (secs)
        self.download_timeout = 30 * 60    # file download timeout (secs)
        self.ctimeout = 6       # default TCP connect timeout (secs)
        self.http_agent = ""
        self.http_insecure = False

        # docker hub
        self.dockerio_index_url = "https://index.docker.io/v1"
        self.dockerio_registry_url = "https://registry-1.docker.io"

        # -------------------------------------------------------------

    def user_init(self, config_file):
        """
        Try to load default values from config file
        Defaults should be in the form x = y
        """
        if config_file:
            self.config_file = config_file
        else:
            self.config_file = self.def_topdir + "/" + self.user_config
        cfile = FileUtil(self.config_file)
        if cfile.size() > 1024 * 2:
            msg.out("Error: file size too big:", self.config_file)
            return False
        data = cfile.getdata()
        for line in data.split("\n"):
            if not line.strip() or "=" not in line or line.startswith("#"):
                continue
            (key, val) = line.strip().split("=", 1)
            try:
                exec('self.%s=%s' % (key.strip(), val.strip()))
            except(NameError, AttributeError, TypeError, IndexError,
                   SyntaxError):
                msg.out("Error: error in config file:", line.strip())
                return False
        msg.setlevel(self.verbose_level)
        return True

    def _sysarch(self):
        """Get the host system architecture"""
        arch = ""
        try:
            mach = platform.machine()
            if mach == "x86_64":
                arch = "amd64"
            elif mach in ("i386", "i586", "i686"):
                arch = "i386"
        except (NameError, AttributeError):
            if sys.maxsize > 2 ** 32:
                arch = "amd64"
            else:
                arch = "i386"
        return arch

    def _osversion(self):
        """Get operating system"""
        try:
            return platform.system().lower()
        except (NameError, AttributeError):
            return ""

    def _oskernel(self):
        """Get operating system"""
        try:
            return platform.release()
        except (NameError, AttributeError):
            return "4.2.0"


class Msg(object):
    """Write messages to stdout and stderr. Allows to filter the
    messages to be displayed through a verbose level, also allows
    to control if child process that produce output through a
    file descriptor should be redirected to /dev/null
    """

    def __init__(self, level=0):
        """
        Initialize Msg level=0 and /dev/null file pointers to be
        used in subprocess calls to obfuscate output and errors
        """
        self.level = level
        self.stdout = sys.stdout
        self.stderr = sys.stderr
        try:
            self.nullfp = open("/dev/null", "w")
        except (IOError, OSError):
            self.chlderr = self.stderr
            self.chldout = self.stdout
            self.chldnul = self.stderr
        else:
            self.chlderr = self.nullfp
            self.chldout = self.nullfp
            self.chldnul = self.nullfp

    def setlevel(self, new_level):
        """Define debug level"""
        self.level = new_level
        if self.level > 1:
            self.chlderr = self.stderr
            self.chldout = self.stdout

    def out(self, *args, **kwargs):
        """Write text to stdout respecting verbose level"""
        level = 0
        if "l" in kwargs:
            level = kwargs["l"]
        if level <= self.level:
            self.stdout.write(" ".join(map(str, args)) + '\n')


class Unique(object):
    """Produce unique identifiers for container names, temporary
    file names and other purposes. If module uuid does not exist
    it tries to use as last option the random generator.
    """
    def __init__(self):
        self.string_set = "abcdef"
        self.def_name = "udocker"

    def _rnd(self, size):
        """Generate a random string"""
        return "".join(
            random.sample(self.string_set * 64 + string.digits * 64, size))

    def uuid(self, name):
        """Get an ID"""
        if not name:
            name = self.def_name
        try:
            return str(uuid.uuid3(uuid.uuid4(), str(name) + str(time.time())))
        except (NameError, AttributeError):
            return(("%s-%s-%s-%s-%s") %
                   (self._rnd(8), self._rnd(4), self._rnd(4),
                    self._rnd(4), self._rnd(12)))

    def imagename(self):
        """Get a container image name"""
        return self._rnd(16)

    def layer_v1(self):
        """Get a container layer name"""
        return self._rnd(64)

    def filename(self, filename):
        """Get a filename"""
        prefix = self.def_name + "-" + str(os.getpid()) + "-"
        try:
            return(prefix +
                   str(uuid.uuid3(uuid.uuid4(), str(time.time()))) +
                   "-" + str(filename))
        except (NameError, AttributeError):
            return prefix + self.uuid(filename) + "-" + str(filename)


class FileUtil(object):
    """Some utilities to manipulate files"""

    def __init__(self, filename):
        self.filename = filename
        self.tmpdir = conf.tmpdir
        self.topdir = conf.def_topdir

    def mktmp(self):
        """Create a temporary filename"""
        tmp_file = conf.tmpdir + "/" + \
            Unique().filename(os.path.basename(self.filename))
        conf.tmptrash[tmp_file] = True
        return tmp_file

    def uid(self):
        """Get the file owner user id"""
        try:
            return os.stat(self.filename).st_uid
        except (IOError, OSError):
            return -1

    def remove(self):
        """Delete files or directories"""
        filename = os.path.abspath(self.filename)
        if not (filename.startswith(self.topdir) or
                filename.startswith(self.tmpdir) or
                filename.startswith("/tmp/")):
            msg.out("Error: deleting file off limits: ", filename)
            return False
        elif self.uid() != os.getuid():
            return False
        elif os.path.isfile(filename) or os.path.islink(filename):
            try:
                os.remove(filename)
            except (IOError, OSError):
                msg.out("Error: deleting file: ", filename)
                return False
            return True
        elif os.path.isdir(filename):
            cmd = "/bin/rm -Rf --preserve-root "
            cmd += filename
            if not subprocess.call(cmd, shell=True, stderr=msg.chlderr,
                                   close_fds=True, env=None):
                if self.filename in conf.tmptrash:
                    del conf.tmptrash[self.filename]
                return True
        msg.out("Error: deleting directory: ", filename)
        return False

    def verify_tar(self):
        """Verify a tar file"""
        if not os.path.isfile(self.filename):
            return False
        else:
            cmd = "tar t"
            if msg.level > 1:
                cmd += "v"
            cmd += "f " + self.filename
            if subprocess.call(cmd, shell=True, stderr=msg.chlderr,
                               stdout=msg.chldnul, close_fds=True):
                return False
            else:
                return True

    def cleanup(self):
        """Delete all temporary files"""
        for filename in conf.tmptrash.keys():
            FileUtil(filename).remove()

    def isdir(self):
        """Is filename a directory"""
        try:
            if os.path.isdir(self.filename):
                return True
        except (IOError, OSError):
            pass
        return False

    def size(self):
        """File size in bytes"""
        try:
            fstat = os.stat(self.filename)
            return fstat.st_size
        except (IOError, OSError):
            return -1

    def getdata(self):
        """Read file content to a buffer"""
        try:
            filep = open(self.filename, "r")
        except (IOError, OSError):
            return ""
        else:
            buf = filep.read()
            filep.close()
            return buf

    def _find_exec(self, cmd_to_use):
        """This method is called by find_exec() invokes a command like
        /bin/which or type to obtain the full pathname of an executable
        """
        out_file = FileUtil("findexec").mktmp()
        try:
            filep = open(out_file, "w")
        except (IOError, OSError):
            return ""
        subprocess.call(cmd_to_use, shell=True, stderr=msg.chlderr,
                        stdout=filep, close_fds=True)
        exec_pathname = FileUtil(out_file).getdata()
        filep.close()
        FileUtil(out_file).remove()
        if "not found" in exec_pathname:
            return ""
        if exec_pathname and exec_pathname.startswith("/"):
            return exec_pathname.strip()
        return ""

    def find_exec(self):
        """Find an executable pathname invoking which or type -p"""
        cmd = self._find_exec("which " + self.filename)
        if cmd:
            return cmd
        cmd = self._find_exec("type -p " + self.filename)
        if cmd:
            return cmd
        return ""

    def find_inpath(self, path, rootdir=""):
        """Find file in a path set such as PATH=/usr/bin:/bin"""
        if isinstance(path, str):
            if "=" in path:
                path = "".join(path.split("=", 1)[1:])
            path = path.split(":")
        if isinstance(path, list) or isinstance(path, tuple):
            for directory in path:
                full_path = rootdir + directory + "/" + self.filename
                if os.path.exists(full_path):
                    return full_path
            return ""
        return ""

    def copyto(self, dest_filename, mode="w"):
        """Copy self.filename to another file. We avoid shutil to have
        the fewest possible dependencies on other Python modules.
        """
        try:
            fpsrc = open(self.filename, "rb")
        except (IOError, OSError):
            return False
        try:
            fpdst = open(dest_filename, mode + "b")
        except (IOError, OSError):
            fpsrc.close()
            return False
        while True:
            copy_buffer = fpsrc.read(1024 * 1024)
            if not copy_buffer:
                break
            fpdst.write(copy_buffer)
        fpsrc.close()
        fpdst.close()
        return True


class UdockerTools(object):
    """Download and setup of the udocker supporting tools
    Includes: proot and alternative python modules, these
    are downloaded to facilitate the installation by the
    end-user.
    """

    def __init__(self, localrepo):
        self.localrepo = localrepo               # LocalRepository object
        self.tmpdir = conf.tmpdir                # Dir for temporary files
        self.tarball_url = conf.tarball_url      # URL to download PRoot
        self.proot = self.localrepo.bindir + "/" + conf.proot_exec  # PRoot
        self.curl = GetURL()

    def is_available(self):
        """Are the tools locally available (already downloaded)"""
        return os.path.exists(self.proot)

    def download(self):
        """Get the tools tarball containing the PRoot binaries"""
        tgz_file = FileUtil("udockertools").mktmp()
        if not self.is_available():
            msg.out("Info: installing udockertools ...")
            (hdr, dummy) = self.curl.get(self.tarball_url, ofile=tgz_file)
            if hdr.data["X-ND-CURLSTATUS"]:
                return False
            cmd = "cd " + self.localrepo.topdir + " ; "
            cmd += "tar x"
            if msg.level > 1:
                cmd += "v"
            cmd += "zf " + tgz_file + " ; "
            cmd += "/bin/chmod u+rx bin/*"
            status = subprocess.call(cmd, shell=True, close_fds=True)
            FileUtil(tgz_file).remove()
            if status:
                return False
        return True


class Container(object):
    """Docker container management. Encapsulates the Docker
    containers specificities mainly the container execution.
    Allows the execution of container layers extracted to the
    local filesystem via a mechanism similar to chroot but not
    requiring root privileges.
    It uses PRoot both as chroot alternative and as emulator of
    the root identity and privileges.
    """

    # pylint: disable=too-many-instance-attributes
    def __init__(self, localrepo):
        self.localrepo = localrepo               # LocalRepository object
        self.tmpdir = conf.tmpdir                # Dir for temporary files
        self.proot = self.localrepo.bindir + "/" + conf.proot_exec  # PRoot
        self.curl = GetURL()
        self.valid_host_env = ("TERM")           # Pass host env variables
        self._cpu_affinity_exec_tools = conf.cpu_affinity_exec_tools
        self._kernel = conf.kernel               # Emulate this kernel
        self.sysdirs_list = conf.sysdirs_list    # Host dirs to pass
        self.hostauth_list = conf.hostauth_list  # Bind passwd and group
        self.dri_list = conf.dri_list            # Bind direct rendering libs
        self.cmd = conf.cmd                      # Default command
        self.opt = dict()                        # Run options
        self.imagerepo = None                    # Imagerepo of container image
        self.container_id = ""                   # Container id
        self.tag = None                          # Tag of container image
        self.exposed_ports = None
        # Metadata defaults
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
        self.opt["cmd"] = conf.cmd               # Comand to execute
        self.opt["hostname"] = ""                # Hostname TBD
        self.opt["domain"] = ""                  # Host domainname TBD
        self.opt["volfrom"] = []                 # Mount vol from container TBD

    def _banner(self, cmd=""):
        """Print a container startup banner"""
        msg.out("",
                "\n", "*" * 78,
                "\n", "*", " " * 74, "*",
                "\n", "*",
                ("STARTING " + self.container_id).center(74, " "), "*",
                "\n", "*", " " * 74, "*",
                "\n", "*" * 78, "\n",
                "executing:", os.path.basename(cmd))

    def get_container_attr(self, container_id):
        """Get container directory and JSON metadata by id or name"""
        if conf.location:
            container_dir = ""
            container_json = []
        else:
            container_dir = self.localrepo.cd_container(container_id)
            if not container_dir:
                msg.out("Error: container id or name not found")
                return(False, False)
            container_json = self.localrepo.load_json(
                container_dir + "/container.json")
            if not container_json:
                msg.out("Error: invalid container json metadata")
                return(False, False)
        return(container_dir, container_json)

    def _check_exposed_ports(self):
        """TCP/UDP ports < 1024 in ExposedPorts JSON metadata
        The exposed ports format is  ExposedPorts:{ "80/tcp":{}, }
        """
        port_number = -1
        if self.exposed_ports:
            for port in self.exposed_ports:
                try:
                    port_number = int(port.split("/")[0])
                except (ValueError, TypeError):
                    pass
                else:
                    if port_number < 1024:
                        msg.out("Error: this container exposes privileged"
                                " TCP/IP ports (< 1024) not supported")
                        return True
        if port_number != -1:
            msg.out("Warning: this container exposes TCP/IP"
                    " ports this may not work")
        return False

    def _set_cpu_affinity(self):
        """set the cpu affinity string for container run command"""
        # find set affinity executable
        for exec_cmd in self._cpu_affinity_exec_tools:
            exec_name = FileUtil(exec_cmd.split(" ", 1)[0]).find_exec()
            if exec_name:
                cpu_affinity_exec = exec_name + \
                    " " + exec_cmd.split(" ", 1)[1]
        # if no cpu affinity executable available ignore affinity set
        if not cpu_affinity_exec:
            self.opt["cpuset"] = ""
            return " "
        elif self.opt["cpuset"]:
            self.opt["cpuset"] = " '" + self.opt["cpuset"] + "' "
            return " %s %s " % (cpu_affinity_exec, self.opt["cpuset"])
        else:
            self.opt["cpuset"] = ""
            return " "

    def _set_uid_map(self):
        """Set the uid_map string for container run command"""
        if self.opt["uid"] == "0":
            uid_map = " -0 "
        else:
            uid_map = \
                " -i " + self.opt["uid"] + ":" + self.opt["gid"] + " "
        return uid_map

    def _set_volume_bindings(self):
        """Set the volume bindings string for container run command"""
        # predefined volume bindings --sysdirs --hostauth --dri
        if not self.opt["nosysdirs"]:
            self.opt["vol"].extend(self.sysdirs_list)
        if self.opt["hostauth"]:
            self.opt["vol"].extend(self.hostauth_list)
        if self.opt["dri"]:
            self.opt["vol"].extend(self.dri_list)
        # remove directory bindings specified with --novol
        for novolume in list(set(self.opt["novol"])):
            try:
                self.opt["vol"].remove(novolume)
            except ValueError:
                msg.out("Warning:  novol %s not in volumes list" %
                        novolume)
        for volume in self.opt["vol"]:
            host_dir_file = volume.split(":")[0]
            if not os.path.exists(host_dir_file):
                msg.out("Warning: host dir not found: -v %s" % host_dir_file)
                self.opt["vol"].remove(volume)
        # build the volumes list
        if self.opt["vol"]:
            vol_str = " -b " + " -b ".join(self.opt["vol"])
        else:
            vol_str = " "
        return vol_str

    def _set_bindhome(self):
        """Binding of the host $HOME in to the container $HOME"""
        if self.opt["bindhome"]:
            (r_user, dummy, dummy, dummy, dummy, r_home,
             dummy) = self._get_user(os.getuid(), "/etc/passwd")
            if r_user:
                return " -b " + r_home
        else:
            return " "

    def _check_paths(self, container_root):
        """Make sure we have a reasonable default PATH and CWD"""
        path = self._getenv("PATH")
        if not path and self.opt["uid"] == "0":
            path = "/usr/sbin:/sbin:/usr/bin:/bin"
        elif not path:
            path = "/usr/bin:/bin"
        self.opt["env"].append("PATH=%s" % path)
        # verify if the working directory is valid and fixit
        if not self.opt["cwd"]:
            self.opt["cwd"] = self.opt["home"]
        if (self.opt["cwd"] and not (self.opt["bindhome"] or self.opt["cwd"]
                                     in self.opt["vol"])):
            if (not (os.path.exists(container_root + "/" + self.opt["cwd"]) and
                     os.path.isdir(container_root + "/" + self.opt["cwd"]))):
                msg.out("Error: invalid working directory: ", self.opt["cwd"])
                return False
        return True

    def _check_executable(self, container_root):
        """Check if executable exists and has execute permissions"""
        path = self._getenv("PATH")
        if self.opt["entryp"] and isinstance(self.opt["entryp"], str):
            self.opt["cmd"] = self.opt["entryp"].strip().split(" ")
        elif self.opt["entryp"] and isinstance(self.opt["entryp"], list):
            if self.opt["cmd"]:                                     # and cmd
                cmd_args = self.opt["cmd"]
                self.opt["cmd"] = [self.opt["entryp"][0]]
                self.opt["cmd"].extend(cmd_args)   # cmd=args entryp
            else:
                self.opt["cmd"] = self.opt["entryp"]
        if not self.opt["cmd"]:
            self.opt["cmd"] = self.cmd
            msg.out("Warning: no command assuming:", self.opt["cmd"], l=2)
        exec_name = self.opt["cmd"][0]            # exec pathname without args
        if exec_name.startswith("/"):
            exec_path = container_root + exec_name
        else:
            exec_path = \
                FileUtil(exec_name).find_inpath(path, container_root + "/")
        if (not (exec_path and os.path.exists(exec_path) and
                 os.path.isfile(exec_path) and os.access(exec_path, os.X_OK))):
            msg.out("Error: command not found or has no execute bit set: ",
                    self.opt["cmd"])
            return False
        else:
            return True

    def _run_load_metadata(self, container_id):
        """Load container metadata from container JSON payload"""
        # get container metadata unless we are dealing with a simple directory
        # tree in which case we don't have metadata
        if conf.location:
            container_dir = ""
            container_json = []
        else:
            (container_dir, container_json) = \
                self.get_container_attr(container_id)
            if not container_dir:
                return(None, None)
            # load metadata from container
            if not self.opt["nometa"]:
                if not self.opt["user"]:
                    self.opt["user"] = \
                        self._get_container_meta(
                            "User", "", container_json)
                if not self.opt["cwd"]:
                    self.opt["cwd"] = \
                        self._get_container_meta(
                            "WorkingDir", "", container_json)
                if not self.opt["hostname"]:
                    self.opt["hostname"] = \
                        self._get_container_meta(
                            "Hostname", "", container_json)
                if not self.opt["domain"]:
                    self.opt["domain"] = \
                        self._get_container_meta(
                            "Domainname", "", container_json)
                if not self.opt["cmd"]:
                    self.opt["cmd"] = \
                        self._get_container_meta(
                            "Cmd", [], container_json)
                if not self.opt["entryp"]:
                    self.opt["entryp"] = self._get_container_meta(
                        "Entrypoint", [], container_json)
                self.opt["vol"].extend(
                    self._get_container_meta(
                        "Volumes", [], container_json))
                self.exposed_ports = \
                    self._get_container_meta(
                        "ExposedPorts", [], container_json)
                self._check_exposed_ports()
                meta_env = \
                    self._get_container_meta("Env", [], container_json)
                if meta_env:
                    meta_env.extend(self.opt["env"])
                    self.opt["env"] = meta_env
        return(container_dir, container_json)

    def _getenv(self, search_key):
        """A getenv() for the container environment metadata."""
        for pair in self.opt["env"]:
            if pair:
                (key, val) = pair.split("=", 1)
                if key == search_key:
                    return str(val)
        return None

    def _environ_cleanup(self):
        """Allow only to pass essential environment variables."""
        environ_copy = os.environ.copy()
        for env_var in environ_copy:
            if env_var not in self.valid_host_env:
                del os.environ[env_var]

    def _files_exist(self, host_files):
        """Check if files in a list are valid exist."""
        valid_files = []
        for filepath in host_files:
            if os.path.exists(filepath):
                valid_files.append(filepath)
        return valid_files

    def _setup_container_user(self, user, container_root):
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
        if not user:
            user = self.opt["user"]
        if ":" in user:
            matched = re.match(("^(\\d+):(\\d+)$"), user)
            try:
                self.opt["uid"] = matched.group(1)
                self.opt["gid"] = matched.group(1)
            except AttributeError:
                msg.out("Error: invalid user syntax use uid:gid or username")
                return False
            if "/etc/passwd" in self.opt["vol"] or self.opt["hostauth"]:
                (found_user, found_uid, found_gid, found_gecos, found_home,
                 found_shell) = self._get_host_user(self.opt["uid"])
            else:
                (found_user, dummy, found_uid, found_gid,
                 found_gecos, found_home, found_shell) = \
                    self._get_user(self.opt["uid"],
                                   container_root + "/etc/passwd")
        else:
            if "/etc/passwd" in self.opt["vol"] or self.opt["hostauth"]:
                (found_user, found_uid, found_gid, found_gecos, found_home,
                 found_shell) = self._get_host_user(user)
            else:
                (found_user, dummy, found_uid, found_gid,
                 found_gecos, found_home, found_shell) = \
                    self._get_user(user, container_root + "/etc/passwd")
        if found_user:
            self.opt["user"] = found_user
            self.opt["uid"] = found_uid
            self.opt["gid"] = found_gid
            self.opt["home"] = found_home
            self.opt["gecos"] = found_gecos
            self.opt["shell"] = found_shell
        else:
            if "/etc/passwd" in self.opt["vol"] or self.opt["hostauth"]:
                msg.out("Error: user not found")
                return False
            else:
                if ":" not in user:
                    self.opt["user"] = user
                    self.opt["uid"] = ""
                    self.opt["gid"] = ""
                elif self.opt["uid"] > 0:
                    self.opt["user"] = ""
                msg.out("Warning: non-existing user will be created")
                self._create_user(container_root + "/etc/passwd",
                                  container_root + "/etc/group")
        return True

    def run(self, container_id):
        """Execute a Docker container using PRoot. This is the main method
        invoked to run the a container with PRoot.

          * argument: container_id or name
          * options:  many see the help

        Steps:
          1. initialize execution parameters via _run_init()
          2. identify the user to run inside the container
          3. setup environment variables, uid mapping and cwd
          4. bind host directories into the container
          5. verify the execution PATH
          6. prepare the command to be executed inside the container
          7. build PRoot command line and execute
        """
        try:
            (container_dir, dummy) = \
                self._run_load_metadata(container_id)
        except (ValueError, TypeError):
            return False

        if conf.location:                   # using specific root tree
            container_root = conf.location
        else:
            container_root = container_dir + "/ROOT"

        # container name(s) from container_id
        container_names = self.localrepo.get_container_name(container_id)
        self.container_id = container_id
        # which user to use inside the container and setup its account
        if not self._setup_container_user(self.opt["user"], container_root):
            return 2

        # setup environment variables, uid mapping, and default dir
        self.opt["env"].append("HOME=" + self.opt["home"])
        self.opt["env"].append("USER=" + self.opt["user"])
        self.opt["env"].append("LOGNAME=" + self.opt["user"])
        self.opt["env"].append("USERNAME=" + self.opt["user"])

        bindhome = self._set_bindhome()
        uid_map = self._set_uid_map()
        cpu_affinity_str = self._set_cpu_affinity()
        vol_str = self._set_volume_bindings()
        if (not (self._check_paths(container_root) and
                 self._check_executable(container_root))):
            return 2

        if self.opt["kernel"]:
            self._kernel = self.opt["kernel"]

        # build the actual command
        cmd_t = (r"unset VTE_VERSION; PS1='%s[\W]\$ ' " % container_id[:8],
                 " ".join(self.opt["env"]),
                 " SHLVL=0 container_uuid=" + container_id,
                 "container_name='",
                 str(container_names).strip("'\"[]") + "' ",
                 cpu_affinity_str,
                 self.proot,
                 bindhome,
                 vol_str,
                 uid_map,
                 "-k", self._kernel,
                 "-r", container_root,
                 " ",)
        cmd = " ".join(cmd_t)
        if self.opt["cwd"]:  # set current working directory
            cmd += " -w " + self.opt["cwd"] + " "
        cmd += " ".join(self.opt["cmd"])
        msg.out("CMD = " + cmd, l=1)

        # if not --hostenv clean the environment and execute
        if not self.opt["hostenv"]:
            self._environ_cleanup()
        self._banner(self.opt["cmd"][0])
        status = subprocess.call(cmd, shell=True, close_fds=True)
        return status

    def _create_user(self, passwd_file, group_file):
        """If we need to create a new user then we first
        copy /etc/passwd and /etc/group to new files and them
        we add the user account into these copied files which
        later are binding/mapped/passed to the container. So
        setup this binding as well via hostauth.
        """
        tmp_passwd = FileUtil("p").mktmp()
        tmp_group = FileUtil("g").mktmp()
        FileUtil(passwd_file).copyto(tmp_passwd, "w")
        FileUtil(group_file).copyto(tmp_group, "w")
        if not self.opt["uid"]:
            self.opt["uid"] = str(os.getuid())
        if not self.opt["gid"]:
            self.opt["gid"] = str(os.getgid())
        if not self.opt["user"]:
            self.opt["user"] = "udoc" + self.opt["uid"][0:4]
        if self.opt["user"] == "root":
            self.opt["home"] = "/"
        elif not self.opt["home"]:
            self.opt["home"] = "/home/" + self.opt["user"]
        self.opt["shell"] = "/bin/sh"
        if (not self._add_user(tmp_passwd, self.opt["user"], "x",
                               self.opt["uid"], self.opt["gid"],
                               "*UDOCKER*", self.opt["home"],
                               self.opt["shell"])):
            return False
        group = self.opt["user"]
        self._add_group(tmp_group, group, self.opt["gid"])
        for sup_gid in os.getgroups():
            self._add_group(tmp_group, "G" + str(sup_gid), str(sup_gid))
        self.opt["hostauth"] = True
        self.hostauth_list = (tmp_passwd + ":/etc/passwd",
                              tmp_group + ":/etc/group")
        return True

    def _get_host_user(self, wanted_user):
        """get user information from the host /etc/passwd etc
        Notice that this also works for other types of user
        databases such as LDAP, NIS etc
        """
        wanted_uid = ""
        if (isinstance(wanted_user, (int, long)) or
                re.match("^\\d+$", wanted_user)):
            wanted_uid = str(wanted_user)
            wanted_user = ""
        if wanted_uid:
            try:
                usr = pwd.getpwuid(wanted_user)
            except (IOError, OSError, KeyError):
                return("", "", "", "", "", "")
            return(str(usr.pw_name), str(usr.pw_uid), str(usr.pw_gid),
                   str(usr.pw_gecos), usr.pw_dir, usr.pw_shell)
        else:
            try:
                usr = pwd.getpwnam(wanted_user)
            except (IOError, OSError, KeyError):
                return("", "", "", "", "", "")
            return(str(usr.pw_name), str(usr.pw_uid), str(usr.pw_gid),
                   str(usr.pw_gecos), usr.pw_dir, usr.pw_shell)

    def _get_user(self, wanted_user, passwd_file):
        """Get a *nix user from a passwd file"""
        wanted_uid = ""
        if (isinstance(wanted_user, (int, long)) or
                re.match("^\\d+$", wanted_user)):
            wanted_uid = str(wanted_user)
            wanted_user = ""
        try:
            inpasswd = open(passwd_file)
        except (IOError, OSError):
            return("", "", "", "", "", "", "")
        else:
            for line in inpasswd:
                (user, passw, uid, gid, gecos, home,
                 shell) = line.strip().split(":")
                if wanted_user and user == wanted_user:
                    return(user, passw, uid, gid, gecos, home, shell)
                if wanted_uid and uid == wanted_uid:
                    return(user, passw, uid, gid, gecos, home, shell)
            inpasswd.close()
            return("", "", "", "", "", "", "")

    # pylint: disable=too-many-arguments
    def _add_user(self, passwd_file, user, passw, uid, gid, gecos,
                  home, shell):
        """Add a *nix user to a /etc/passwd file"""
        try:
            outpasswd = open(passwd_file, "ab")
        except (IOError, OSError):
            return False
        else:
            outpasswd.write("%s:%s:%s:%s:%s:%s:%s\n" %
                            (user, passw, uid, gid, gecos, home, shell))
            outpasswd.close()
            return True

    def _add_group(self, group_file, group, gid):
        """Add a group to a /etc/passwd file"""
        try:
            outgroup = open(group_file, "ab")
        except (IOError, OSError):
            return False
        else:
            outgroup.write("%s:x:%s:\n" % (group, gid))
            outgroup.close()
            return True

    def create(self, imagerepo, tag):
        """Create a container from an image in the repository.
        Since images are stored as layers in tar files, this
        step consists in extracting those layers into a ROOT
        directory in the appropriate sequence.
        first argument: imagerepo
        second argument: image tag in that repo
        """
        self.imagerepo = imagerepo
        self.tag = tag
        image_dir = self.localrepo.cd_imagerepo(self.imagerepo, self.tag)
        if not image_dir:
            msg.out("Error: create container: imagerepo is invalid")
            return False
        (container_json, layer_files) = self.localrepo.get_image_attributes()
        if not container_json:
            msg.out("Error: create container: getting layers or json")
            return False
        container_id = Unique().uuid(os.path.basename(self.imagerepo))
        container_dir = self.localrepo.setup_container(
            self.imagerepo, self.tag, container_id)
        if not container_dir:
            msg.out("Error: create container: setting up container")
            return False
        self.localrepo.save_json(
            container_dir + "/container.json", container_json)
        status = self._untar_layers(layer_files, container_dir + "/ROOT")
        if not status:
            msg.out("Error: creating container:", container_id)
        return container_id

    def _apply_whiteouts(self, tarf, destdir):
        """The layered filesystem od docker uses whiteout files
        to identify files or directories to be removed.
        The format is .wh.<filename>
        """
        cmd = r"tar tf %s '*\/\.wh\.*'" % (tarf)
        proc = subprocess.Popen(cmd, shell=True, stderr=msg.chlderr,
                                stdout=subprocess.PIPE, close_fds=True)
        while True:
            wh_filename = proc.stdout.readline().strip()
            if wh_filename:
                wh_basename = os.path.basename(wh_filename)
                if wh_basename.startswith(".wh."):
                    rm_filename = os.path.dirname(wh_filename) + "/" \
                        + wh_basename.replace(".wh.", "", 1)
                    FileUtil(destdir + "/" + rm_filename).remove()
            else:
                try:
                    proc.stdout.close()
                    proc.terminate()
                except(NameError, AttributeError):
                    pass
                break
        return True

    def _untar_layers(self, tarfiles, destdir):
        """Untar all container layers. Each layer is extracted
        and permissions are changed to avoid file permission
        issues when extracting the next layer.
        """
        gid = str(os.getgid())
        for tarf in tarfiles:
            self._apply_whiteouts(tarf, destdir)
            # cmd = "umask 022 ; tar -C %s -x --delay-directory-restore " % \
            cmd = "umask 022 ; tar -C %s -x " % destdir
            if msg.level > 1:
                cmd += " -v "
            cmd += r" --one-file-system --no-same-owner "
            cmd += r"--no-same-permissions --overwrite -f " + tarf
            cmd += r"; find " + destdir
            cmd += r" \( -type d ! -perm -u=x -exec /bin/chmod u+x {} \; \) , "
            cmd += r" \( ! -perm -u=w -exec /bin/chmod u+w {} \; \) , "
            cmd += r" \( ! -gid " + gid + r" -exec /bin/chgrp " + gid
            cmd += r" {} \; \) , "
            cmd += r" \( -name '.wh.*' -exec "
            cmd += r" /bin/rm -f --preserve-root {} \; \)"
            status = subprocess.call(cmd, shell=True, stderr=msg.chlderr,
                                     close_fds=True)
            if status:
                msg.out("Error: while extracting image layer")
        return not status

    def _dict_to_str(self, in_dict):
        """Convert dict to str"""
        out_str = ""
        for (key, val) in in_dict.iteritems():
            out_str += "%s:%s " % (str(key), str(val))
        return out_str

    def _dict_to_list(self, in_dict):
        """Convert dict to list"""
        out_list = []
        for (key, val) in in_dict.iteritems():
            out_list.append("%s:%s" % (str(key), str(val)))
        return out_list

    def _get_container_meta(self, param, default, container_json):
        """Get the container metadata from the container"""
        if "config" in container_json:
            confidx = "config"
        elif "container_config" in container_json:
            confidx = "container_config"
        if param in container_json[confidx]:
            if container_json[confidx][param] is None:
                return default
            elif (isinstance(container_json[confidx][param], str) and (
                    isinstance(default, list) or isinstance(default, tuple))):
                return container_json[confidx][param].strip().split()
            elif (isinstance(default, str) and (
                    isinstance(container_json[confidx][param], list) or
                    isinstance(container_json[confidx][param], tuple))):
                return " ".join(container_json[confidx][param])
            elif (isinstance(default, str) and (
                    isinstance(container_json[confidx][param], dict))):
                return self._dict_to_str(container_json[confidx][param])
            elif (isinstance(default, list) and (
                    isinstance(container_json[confidx][param], dict))):
                return self._dict_to_list(container_json[confidx][param])
            else:
                return container_json[confidx][param]

    def set_proxy(self, http_proxy):
        """Set a http socks proxy for downloads in this case
        to download auxiliary programs such as PRoot itself.
        """
        self.curl.set_proxy(http_proxy)


# pylint: disable=too-many-instance-attributes
# pylint: disable=too-many-public-methods
class LocalRepository(object):
    """Implements a basic repository for images and containers.
    The repository will be usually in the user home directory.
    The repository has a simple directory structure:
    1. layers    : one dir containing all image layers so that
                   layers share among images are not duplicated
    2. containers: has inside one directory per container,
                   each dir has a ROOT with the extracted image
    3. repos:      has inside a directory tree of repos the
                   leaf repo dirs are called tags and contain the
                   image data (actually links both to layer tarballs
                   and json metadata files.
    d) bin:        contains executables (PRoot is stored here)
    """

    def __init__(self, topdir):
        self.topdir = topdir
        self.def_reposdir = "repos"
        self.def_layersdir = "layers"
        self.def_containersdir = "containers"
        self.def_bindir = "bin"
        self.def_libdir = "lib"
        self.reposdir = self.topdir + "/" + self.def_reposdir
        self.layersdir = self.topdir + "/" + self.def_layersdir
        self.containersdir = self.topdir + "/" + self.def_containersdir
        self.bindir = self.topdir + "/" + self.def_bindir
        self.libdir = self.topdir + "/" + self.def_libdir
        self.tmpdir = conf.tmpdir
        self.cur_repodir = ""
        self.cur_tagdir = ""
        self.cur_containerdir = ""

    def setup(self, topdir):
        """change to a different localrepo"""
        self.__init__(topdir)

    def create_repo(self):
        """creates properties with pathnames for easy
        access to the several repository directories
        """
        try:
            if not os.path.exists(self.topdir):
                os.makedirs(self.topdir)
            if not os.path.exists(self.reposdir):
                os.makedirs(self.reposdir)
            if not os.path.exists(self.layersdir):
                os.makedirs(self.layersdir)
            if not os.path.exists(self.containersdir):
                os.makedirs(self.containersdir)
            if not os.path.exists(self.bindir):
                os.makedirs(self.bindir)
            if not os.path.exists(self.tmpdir):
                os.makedirs(self.tmpdir)
            if not os.path.exists(self.libdir):
                os.makedirs(self.libdir)
        except(IOError, OSError):
            return False
        else:
            return True

    def is_repo(self):
        """check if directory structure corresponds to a repo"""
        dirs_exist = [os.path.exists(self.reposdir),
                      os.path.exists(self.layersdir),
                      os.path.exists(self.containersdir),
                      os.path.exists(self.bindir),
                      os.path.exists(self.libdir)]
        return all(dirs_exist)

    def is_container_id(self, obj):
        """Verify if the provided object matches the format of a
        local container id.
        """
        if not isinstance(obj, str):
            return False
        match = re.match(
            "^[a-z0-9]+-[a-z0-9]+-[a-z0-9]+-[a-z0-9]+-[a-z0-9]+$", obj)
        if match:
            return True
        return False

    def protect_container(self, container_id):
        """Protect a container directory against deletion"""
        return self._protect(self.cd_container(container_id))

    def unprotect_container(self, container_id):
        """Remove the protection against deletion"""
        return self._unprotect(self.cd_container(container_id))

    def isprotected_container(self, container_id):
        """See if a container directory is protected"""
        return self._isprotected(self.cd_container(container_id))

    def _protect(self, directory):
        """The the protection mark in a container or image tag"""
        try:
            # touch create version file
            open(directory + "/PROTECT", 'w').close()
            return True
        except (IOError, OSError):
            return False

    def _unprotect(self, directory):
        """Remove protection mark from container or image tag"""
        try:
            os.remove(directory + "/PROTECT")
            return True
        except (IOError, OSError):
            return False

    def _isprotected(self, directory):
        """See if container or image tag are protected"""
        if os.path.exists(directory + "/PROTECT"):
            return True
        return False

    def iswriteable_container(self, container_id):
        """See if a container root dir is writable by this user"""
        container_root = self.cd_container(container_id) + "/ROOT"
        if not os.path.exists(container_root):
            return 2
        if not os.path.isdir(container_root):
            return 3
        if os.access(container_root, os.W_OK):
            return 1
        return 0

    def get_containers_list(self, dir_only=True):
        """Get a list of all containers in the local repo
        dir_only: is optional and indicates
                  if True a summary list of container_ids and names
                  if False  an extended listing containing further
                  container information
        """
        containers_list = []
        if not os.path.isdir(self.containersdir):
            return []
        for fname in os.listdir(self.containersdir):
            container_dir = self.containersdir + "/" + fname
            if os.path.isdir(container_dir):
                try:
                    filep = open(container_dir + "/imagerepo.name", "r")
                except (IOError, OSError):
                    reponame = ""
                else:
                    reponame = filep.read()
                    filep.close()
                if dir_only:
                    containers_list.append(container_dir)
                elif not os.path.islink(container_dir):
                    names = self.get_container_name(fname)
                    if not names:
                        names = ""
                    containers_list.append((fname, reponame, str(names)))
        return containers_list

    def del_container(self, container_id):
        """Delete a container tree, the image layers are untouched"""
        container_dir = self.cd_container(container_id)
        if not container_dir:
            return False
        else:
            if container_dir in self.get_containers_list(True):
                for name in self.get_container_name(container_id):
                    self.del_container_name(name)  # delete aliases links
                if FileUtil(container_dir).remove():
                    self.cur_containerdir = ""
                    return True
        return False

    def cd_container(self, container_id):
        """Select a container directory for further operations"""
        container_dir = self.containersdir + "/" + str(container_id)
        if os.path.exists(container_dir):
            if container_dir in self.get_containers_list(True):
                return container_dir
        return ""

    def _relpath(self, path, start):
        """An alternative to os.path.relpath()"""
        if not path:
            raise ValueError("no path specified")
        start_list = posixpath.abspath(start).split(posixpath.sep)
        path_list = posixpath.abspath(path).split(posixpath.sep)
        # Work out how much of the filepath is shared by start and path.
        i = len(posixpath.commonprefix([start_list, path_list]))
        rel_list = [posixpath.pardir] * (len(start_list) - i) + path_list[i:]
        if not rel_list:
            return posixpath.curdir
        return posixpath.join(*rel_list)

    def _symlink(self, existing_file, link_file):
        """Create relative symbolic links"""
        if os.path.exists(link_file):
            return False
        try:
            rel_path_to_existing = os.path.relpath(
                existing_file, os.path.dirname(link_file))
        except (AttributeError, NameError):
            rel_path_to_existing = self._relpath(
                existing_file, os.path.dirname(link_file))
        os.symlink(rel_path_to_existing, link_file)
        return True

    def set_container_name(self, container_id, name):
        """Associates a name to a container id The container can
        then be referenced either by its id or by its name.
        """
        invalid_chars = ("/", ".", " ", "[", "]")
        if name and any(x in name for x in invalid_chars):
            return False
        if len(name) > 30:
            return False
        container_dir = self.cd_container(container_id)
        if container_dir:
            linkname = self.containersdir + "/" + name
            if os.path.exists(linkname):
                return False
            self._symlink(container_dir, linkname)
            return True
        return False

    def del_container_name(self, name):
        """Remove a name previously associated to a container"""
        if "/" in name or "." in name or " " in name or len(name) > 30:
            return False
        linkname = self.containersdir + "/" + name
        if os.path.exists(linkname):
            os.remove(linkname)
            return True
        return False

    def get_container_id(self, container_name):
        """From a container name obtain its container_id"""
        if container_name:
            pathname = self.containersdir + "/" + container_name
            if os.path.islink(pathname):
                return os.path.basename(os.readlink(pathname))
            elif os.path.isdir(pathname):
                return container_name
        return ""

    def get_container_name(self, container_id):
        """From a container_id obtain its name(s)"""
        if not os.path.isdir(self.containersdir):
            return []
        link_list = []
        for fname in os.listdir(self.containersdir):
            container = self.containersdir + "/" + fname
            if os.path.islink(container):
                real_container = os.readlink(container)
                if os.path.basename(real_container) == container_id:
                    link_list.append(fname)
        return link_list

    def setup_container(self, imagerepo, tag, container_id):
        """Create the directory structure for a container"""
        container_dir = self.containersdir + "/" + str(container_id)
        if os.path.exists(container_dir):
            return ""
        try:
            os.makedirs(container_dir + "/ROOT")
            out_imagerepo = open(container_dir + "/imagerepo.name", 'w')
        except (IOError, OSError):
            return None
        else:
            out_imagerepo.write(imagerepo + ":" + tag)
            out_imagerepo.close()
            self.cur_containerdir = container_dir
            return container_dir

    def _is_tag(self, tag_dir):
        """Does this directory contain an image tag ?
        An image TAG indicates that this repo directory
        contains references to layers and metadata from
        which we can extract a container.
        """
        try:
            if os.path.isfile(tag_dir + "/TAG"):
                return True
        except (IOError, OSError):
            pass
        return False

    def protect_imagerepo(self, imagerepo, tag):
        """Protect an image repo TAG against deletion"""
        return self._protect(self.reposdir + "/" + imagerepo + "/" + tag)

    def unprotect_imagerepo(self, imagerepo, tag):
        """Removes the deletion protection"""
        return self._unprotect(self.reposdir + "/" + imagerepo + "/" + tag)

    def isprotected_imagerepo(self, imagerepo, tag):
        """See if this image TAG is protected against deletion"""
        return self._isprotected(self.reposdir + "/" + imagerepo + "/" + tag)

    def cd_imagerepo(self, imagerepo, tag):
        """Select an image TAG for further operations"""
        if imagerepo and tag:
            tag_dir = self.reposdir + "/" + imagerepo + "/" + tag
            if os.path.exists(tag_dir):
                if self._is_tag(tag_dir):
                    self.cur_repodir = self.reposdir + "/" + imagerepo
                    self.cur_tagdir = self.cur_repodir + "/" + tag
                    return self.cur_tagdir
        return ""

    def _findfile(self, filename, in_dir):
        """is a specific layer filename referenced by another image TAG"""
        found_list = []
        if FileUtil(in_dir).isdir():
            for fullname in os.listdir(in_dir):
                f_path = in_dir + "/" + fullname
                if os.path.islink(f_path):
                    if filename in fullname:            # match .layer or .json
                        found_list.append(f_path)  # found reference to layer
                elif os.path.isdir(f_path):
                    found_list.extend(self._findfile(filename, f_path))
        return found_list

    def _inrepository(self, filename):
        """Check if a given file is in the repository"""
        return self._findfile(filename, self.reposdir)

    def _remove_layers(self, tag_dir, force):
        """Remove link to image layer and corresponding layer
        if not being used by other images
        """
        for fname in os.listdir(tag_dir):
            f_path = tag_dir + "/" + fname  # link to layer
            if os.path.islink(f_path):
                layer_file = tag_dir + "/" + os.readlink(f_path)
                if not FileUtil(f_path).remove() and not force:
                    return False
                if not self._inrepository(fname):
                    # removing actual layers not reference by other repos
                    if not FileUtil(layer_file).remove() and not force:
                        return False
        return True

    def del_imagerepo(self, imagerepo, tag, force=False):
        """Delete an image repository and its layers"""
        tag_dir = self.cd_imagerepo(imagerepo, tag)
        if (tag_dir and
                self._remove_layers(tag_dir, force) and
                FileUtil(tag_dir).remove()):
            self.cur_repodir = ""
            self.cur_tagdir = ""
            return True
        else:
            return False

    def _get_tags(self, tag_dir):
        """Get image tags from repository
        The tags identify actual usable containers
        """
        tag_list = []
        if FileUtil(tag_dir).isdir():
            for fname in os.listdir(tag_dir):
                f_path = tag_dir + "/" + fname
                if self._is_tag(f_path):
                    tag_list.append(
                        (tag_dir.replace(self.reposdir + "/", ""), fname))
                elif os.path.isdir(f_path):
                    tag_list.extend(self._get_tags(f_path))
        return tag_list

    def get_imagerepos(self):
        """get all images repositories with tags"""
        return self._get_tags(self.reposdir)

    def get_layers(self, imagerepo, tag):
        """Get all layers for a given image image tag"""
        layers_list = []
        tag_dir = self.cd_imagerepo(imagerepo, tag)
        if tag_dir:
            for fname in os.listdir(tag_dir):
                filename = tag_dir + "/" + fname
                if os.path.islink(filename):
                    size = FileUtil(filename).size()
                    layers_list.append((filename, size))
        return layers_list

    def add_image_layer(self, filename):
        """Add a layer to an image TAG"""
        if not (self.cur_repodir and self.cur_tagdir):
            return False
        if not os.path.exists(filename):
            return False
        if not os.path.exists(self.cur_repodir):
            return False
        if not os.path.exists(self.cur_tagdir):
            return False
        linkname = self.cur_tagdir + "/" + os.path.basename(filename)
        if os.path.islink(linkname):
            os.remove(linkname)
        self._symlink(filename, linkname)
        return True

    def setup_imagerepo(self, imagerepo):
        """Create directory for an image repository"""
        if not imagerepo:
            return False
        directory = self.reposdir + "/" + imagerepo
        if not os.path.exists(directory):
            os.makedirs(directory)
        self.cur_repodir = directory
        return True

    def setup_tag(self, tag):
        """Create directory structure for an image TAG
        to be invoked after setup_imagerepo()
        """
        directory = self.cur_repodir + "/" + tag
        if not os.path.exists(directory):
            os.makedirs(directory)
        self.cur_tagdir = directory
        try:
            out_tag = open(directory + "/TAG", 'w')
        except (IOError, OSError):
            return False
        else:
            out_tag.write(self.cur_repodir + ":" + tag)
            out_tag.close()
        return True

    def set_version(self, version):
        """Set the version of the image TAG repository currently
        it supports Docker images with versions v1 and v2
        to be invoked after setup_tag()
        """
        if not (self.cur_repodir and self.cur_tagdir):
            return False
        if not os.path.exists(self.cur_repodir):
            return False
        if not os.path.exists(self.cur_tagdir):
            return False
        directory = self.cur_tagdir
        if (os.path.exists(directory + "/v1") and version != "v1" or
                os.path.exists(directory + "/v2") and version != "v2"):
            if len(os.listdir(directory)) == 1:
                try:
                    os.remove(directory + "/v1")
                    os.remove(directory + "/v2")
                except (IOError, OSError):
                    pass
                if len(os.listdir(directory)) != 0:
                    return False
        try:
            # Create version file
            open(directory + "/" + version, 'a').close()
        except (IOError, OSError):
            return False
        return True

    def get_image_attributes(self):
        """Load attributes from image TAGs that have been previously
        selected via cd_imagerepo(). Supports images of type v1 and v2.
        Returns: (container JSON, list of layer files).
        """
        files = []
        directory = self.cur_tagdir
        if os.path.exists(directory + "/v1"):   # if dockerhub API v1
            layer_list = self.load_json("ancestry")
            if layer_list:
                for layer_id in reversed(layer_list):
                    layer_file = directory + "/" + layer_id + ".layer"
                    if not os.path.exists(layer_file):
                        return(None, None)
                    files.append(layer_file)
                json_file = directory + "/" + layer_list[0] + ".json"
                if os.path.exists(json_file):
                    container_json = self.load_json(json_file)
                    return(container_json, files)
        elif os.path.exists(directory + "/v2"):  # if dockerhub API v1
            manifest = self.load_json("manifest")
            if manifest:
                for layer in reversed(manifest["fsLayers"]):
                    layer_file = directory + "/" + layer["blobSum"]
                    if not os.path.exists(layer_file):
                        return(None, None)
                    files.append(layer_file)
                json_string = manifest["history"][0]["v1Compatibility"].strip()
                try:
                    container_json = json.loads(json_string)
                except (IOError, OSError, AttributeError,
                        ValueError, TypeError):
                    return(None, None)
                return(container_json, files)
        return(None, None)

    def save_json(self, filename, data):
        """Save container json to a file in the image TAG directory
        that has been previously selected via cd_imagerepo()
        or if the file starts with "/" to that specific file.
        """
        if filename.startswith("/"):
            out_filename = filename
        else:
            if not (self.cur_repodir and self.cur_tagdir):
                return False
            if not os.path.exists(self.cur_repodir):
                return False
            if not os.path.exists(self.cur_tagdir):
                return False
            out_filename = self.cur_tagdir + "/" + filename
        outfile = None
        try:
            outfile = open(out_filename, 'w')
            json.dump(data, outfile)
        except (IOError, OSError, AttributeError, ValueError, TypeError):
            if outfile:
                outfile.close()
            return False
        outfile.close()
        return True

    def load_json(self, filename):
        """Load container json from a file in the image TAG directory
        that has been previously selected via cd_imagerepo()
        or if the file starts with "/" from that specific file.
        """
        if filename.startswith("/"):
            in_filename = filename
        else:
            if not (self.cur_repodir and self.cur_tagdir):
                return False
            if not os.path.exists(self.cur_repodir):
                return False
            if not os.path.exists(self.cur_tagdir):
                return False
            in_filename = self.cur_tagdir + "/" + filename
        json_obj = None
        infile = None
        try:
            infile = open(in_filename)
            json_obj = json.load(infile)
        except (IOError, OSError, AttributeError, ValueError, TypeError):
            pass
        if infile:
            infile.close()
        return json_obj

    def _load_structure(self, imagetagdir):
        """Scan the repository structure of a given image tag"""
        structure = {}
        structure["layers"] = dict()
        if FileUtil(imagetagdir).isdir():
            for fname in os.listdir(imagetagdir):
                f_path = imagetagdir + "/" + fname
                if fname == "ancestry":
                    structure["ancestry"] = self.load_json(f_path)
                elif fname == "manifest":
                    structure["manifest"] = self.load_json(f_path)
                elif len(fname) >= 64:
                    layer_id = fname.replace(".json", "").replace(".layer", "")
                    if layer_id not in structure["layers"]:
                        structure["layers"][layer_id] = dict()
                    if fname.endswith("json"):
                        structure["layers"][layer_id]["json"] = \
                            self.load_json(f_path)
                        structure["layers"][layer_id]["json_f"] = f_path
                    elif fname.endswith("layer"):
                        structure["layers"][layer_id]["layer_f"] = f_path
                    elif fname.startswith("sha"):
                        structure["layers"][layer_id]["layer_f"] = f_path
                    else:
                        msg.out("Warning: unkwnon file in layer:", f_path)
                elif fname in ("TAG", "v1", "v2", "PROTECT"):
                    pass
                else:
                    msg.out("Warning: unkwnon file in image:", f_path)
        return structure

    def _find_top_layer_id(self, structure, my_layer_id=""):
        """Find the id of the top layer of a given image tag in a
        structure produced by _load_structure()
        """
        if "layers" not in structure:
            return []
        else:
            if not my_layer_id:
                my_layer_id = structure["layers"].keys()[0]
            found = ""
            for layer_id in structure["layers"]:
                if "json" not in structure["layers"][layer_id]:   # v2
                    continue
                elif "parent" not in structure["layers"][layer_id]["json"]:
                    continue
                elif (my_layer_id ==
                      structure["layers"][layer_id]["json"]["parent"]):
                    found = self._find_top_layer_id(structure, layer_id)
                    break
            if not found:
                return my_layer_id
            else:
                return found

    def _sorted_layers(self, structure, top_layer_id):
        """Return the image layers sorted"""
        sorted_layers = []
        next_layer = top_layer_id
        while next_layer:
            sorted_layers.append(next_layer)
            if "json" not in structure["layers"][next_layer]:   # v2
                break
            if "parent" not in structure["layers"][next_layer]["json"]:
                break
            else:
                next_layer = structure["layers"][next_layer]["json"]["parent"]
                if not next_layer:
                    break
        return sorted_layers

    # pylint: disable=too-many-branches
    def verify_image(self):
        """Verify the structure of an image repository"""
        msg.out("Loading structure")
        structure = self._load_structure(self.cur_tagdir)
        if not structure:
            msg.out("Error: load of image tag structure failed")
            return False
        msg.out("Finding top layer id")
        top_layer_id = self._find_top_layer_id(structure)
        if not top_layer_id:
            msg.out("Error: finding top layer id")
            return False
        msg.out("Sorting layers")
        layers_list = self._sorted_layers(structure, top_layer_id)
        status = True
        if "ancestry" in structure:
            layer = iter(layers_list)
            for ancestry_layer in structure["ancestry"]:
                verify_layer = layer.next()
                if ancestry_layer != verify_layer:
                    msg.out("Error: ancestry and layers do not match",
                            ancestry_layer, verify_layer)
                    status = False
                    continue
        elif "manifest" in structure:
            for manifest_layer in structure["manifest"]["fsLayers"]:
                if manifest_layer["blobSum"] not in structure["layers"]:
                    msg.out("Error: layer in manifest does not exist in repo",
                            manifest_layer)
                    status = False
                    continue
        for layer_id in structure["layers"]:
            if "layer_f" not in structure["layers"][layer_id]:
                msg.out("Error: layer file not found in structure", layer_id)
                status = False
                continue
            layer_f = structure["layers"][layer_id]["layer_f"]
            if not (os.path.exists(layer_f) and
                    os.path.islink(layer_f)):
                msg.out("Error: layer data file symbolic link not found",
                        layer_id)
                status = False
                continue
            if not os.path.exists(self.cur_tagdir + "/" +
                                  os.readlink(layer_f)):
                msg.out("Error: layer data file not found")
                status = False
                continue
            if not FileUtil(layer_f).verify_tar():
                status = False
                msg.out("Error: layer file not ok:", layer_f)
            msg.out("Info: layer in repo:", layer_id)
        return status


class CurlHeader(object):
    """An http header parser to be used with PyCurl
    Allows to retrieve the header fields and the status.
    Allows to obtain just the header by stopping the
    download (returning -1) e.g to get the content length
    this is useful if the RESTful interface or web server
    does not implement HEAD.
    """

    def __init__(self):
        self.sizeonly = False
        self.data = dict()
        self.data["X-ND-HTTPSTATUS"] = ""
        self.data["X-ND-CURLSTATUS"] = ""

    def write(self, buff):
        """Write is called by Curl()"""
        pair = buff.split(":", 1)
        if len(pair) == 2:
            key = pair[0].strip().lower()
            if key:
                self.data[key] = pair[1].strip()
        elif pair[0].startswith("HTTP/"):
            self.data["X-ND-HTTPSTATUS"] = buff.strip()
        elif (self.sizeonly and
              pair[0].strip() == "" and
              "location" not in self.data):
            return -1

    def setvalue_from_file(self, in_filename):
        """Load header content from file instead of from Curl()
        Alternative to write() to be used with the curl executable
        version.
        """
        try:
            infile = open(in_filename)
        except (IOError, OSError):
            return False
        for line in infile:
            self.write(line)
        infile.close()
        return True

    def getvalue(self):
        """Return the curl data buffer"""
        return str(self.data)

    def __str__(self):
        """Return a string representation"""
        return str(self.data)


class GetURL(object):
    """File downloader using PyCurl or a curl cli executable"""

    def __init__(self):
        """Load configuration common to the implementations"""
        self.timeout = conf.timeout
        self.ctimeout = conf.ctimeout
        self.download_timeout = conf.download_timeout
        self.agent = conf.http_agent
        self.http_proxy = conf.http_proxy
        self.cache_support = False
        self._select_implementation()
        self.insecure = conf.http_insecure

    def _select_implementation(self):
        """Select which implementation to use"""
        if GetURLpyCurl().is_available():
            self._geturl = GetURLpyCurl()
            self.cache_support = True
        elif GetURLexeCurl().is_available():
            self._geturl = GetURLexeCurl()
        else:
            msg.out("Error: need curl or pycurl to perform downloads")
            raise NameError('need curl or pycurl')

    def get_content_length(self, hdr):
        """Get content length from the http header"""
        try:
            return int(hdr.data["content-length"])
        except (ValueError, TypeError):
            return -1

    def set_insecure(self, bool_value=True):
        """Use insecure downloads no SSL verification"""
        self.insecure = bool_value

    def set_proxy(self, http_proxy):
        """Specify a socks http proxy"""
        self.http_proxy = http_proxy

    def get(self, *args, **kwargs):
        """Get URL using selected implementation
        Example:
            get(url, ctimeout=5, timeout=5, v=true, header=[]):
        """
        if len(args) != 1:
            raise TypeError('wrong number of arguments')
        return self._geturl.get(*args, **kwargs)


class GetURLpyCurl(GetURL):
    """Downloader implementation using PyCurl"""

    def is_available(self):
        """Can we use this approach for download"""
        try:
            dummy = pycurl.Curl()
        except (NameError, AttributeError):
            return False
        return True

    def _select_implementation(self):
        """Override the parent class method"""
        pass

    def _set_defaults(self, pyc, hdr):
        """Set options for pycurl"""
        pyc.setopt(pyc.SSL_VERIFYPEER, not self.insecure)
        pyc.setopt(pyc.FOLLOWLOCATION, True)
        pyc.setopt(pyc.FAILONERROR, False)
        pyc.setopt(pyc.NOPROGRESS, True)
        pyc.setopt(pyc.HEADERFUNCTION, hdr.write)
        pyc.setopt(pyc.USERAGENT, self.agent)
        pyc.setopt(pyc.CONNECTTIMEOUT, self.ctimeout)
        pyc.setopt(pyc.TIMEOUT, self.timeout)
        pyc.setopt(pyc.PROXY, self.http_proxy)
        if conf.verbose_level > 1:
            pyc.setopt(pyc.VERBOSE, True)
        else:
            pyc.setopt(pyc.VERBOSE, False)

    def _mkpycurl(self, pyc, hdr, buf, **kwargs):
        """Prepare curl command line according to invocation options"""
        if "sizeonly" in kwargs:
            hdr.sizeonly = True
        if "proxy" in kwargs and kwargs["proxy"]:
            pyc.setopt(pyc.PROXY, pyc.USERAGENT, kwargs["proxy"])
        if "ctimeout" in kwargs:
            pyc.setopt(pyc.CONNECTTIMEOUT, kwargs["ctimeout"])
        if "header" in kwargs:  # avoid known pycurl bug
            clean_header_list = []
            for header_item in kwargs["header"]:
                clean_header_list.append(str(header_item))
            pyc.setopt(pyc.HTTPHEADER, clean_header_list)
        if "v" in kwargs:
            pyc.setopt(pyc.VERBOSE, kwargs["v"])
        if "nobody" in kwargs:
            pyc.setopt(pyc.NOBODY, kwargs["nobody"])  # header only no content
        if "timeout" in kwargs:
            pyc.setopt(pyc.TIMEOUT, kwargs["timeout"])
        if "ofile" in kwargs:
            output_file = kwargs["ofile"]
            pyc.setopt(pyc.TIMEOUT, self.download_timeout)
            openflags = "wb"
            if "resume" in kwargs and kwargs["resume"]:
                pyc.setopt(pyc.RESUME_FROM, FileUtil(output_file).size())
                openflags = "ab"
            try:
                filep = open(output_file, openflags)
            except(IOError, OSError):
                msg.out("Error: opening download file: %s" % output_file)
                raise
            pyc.setopt(pyc.WRITEDATA, filep)
        else:
            filep = None
            output_file = ""
            pyc.setopt(pyc.WRITEFUNCTION, buf.write)
        hdr.data["X-ND-CURLSTATUS"] = 0
        return(output_file, filep)

    def get(self, *args, **kwargs):
        """http get implementation using the PyCurl"""
        buf = cStringIO.StringIO()
        hdr = CurlHeader()
        pyc = pycurl.Curl()
        url = str(args[0])
        pyc.setopt(pyc.URL, url)
        self._set_defaults(pyc, hdr)
        try:
            (output_file, filep) = self._mkpycurl(pyc, hdr, buf, **kwargs)
            pyc.perform()
        except(IOError, OSError):
            return(None, None)
        except pycurl.error, error:
            errno, errstr = error
            hdr.data["X-ND-CURLSTATUS"] = errno
            if not hdr.data["X-ND-HTTPSTATUS"]:
                hdr.data["X-ND-HTTPSTATUS"] = errstr
        if "header" in kwargs:
            hdr.data["X-ND-HEADERS"] = kwargs["header"]
        if "ofile" in kwargs:
            filep.close()
            if " 401" in hdr.data["X-ND-HTTPSTATUS"]:  # needs authentication
                pass
            elif " 206" in hdr.data["X-ND-HTTPSTATUS"] and "resume" in kwargs:
                pass
            elif " 416" in hdr.data["X-ND-HTTPSTATUS"] and "resume" in kwargs:
                kwargs["resume"] = False
                (hdr, buf) = self.get(url, **kwargs)
            elif " 200" not in hdr.data["X-ND-HTTPSTATUS"]:
                msg.out("Error: in download: " + str(
                    hdr.data["X-ND-HTTPSTATUS"]))
                FileUtil(output_file).remove()
        return(hdr, buf)


class GetURLexeCurl(GetURL):
    """Downloader implementation using curl cli executable"""

    def __init__(self):
        GetURL.__init__(self)
        self._opts = None
        self._files = None

    def is_available(self):
        """Can we use this approach for download"""
        return bool(FileUtil("curl").find_exec())

    def _select_implementation(self):
        """Override the parent class method"""
        pass

    def _set_defaults(self):
        """Set defaults for curl command line options"""
        self._opts = {
            "insecure": "",
            "header": "",
            "verbose": "",
            "nobody": "",
            "proxy": "",
            "resume": "",
            "ctimeout": "--connect-timeout " + str(self.ctimeout),
            "timeout": "-m " + str(self.timeout),
            "other": "--max-redirs 10 -s -q -S -L "
        }
        if self.insecure:
            self._opts["insecure"] = "-k"
        if conf.verbose_level > 1:
            self._opts["verbose"] = "-v"
        self._files = {
            "url":  "",
            "error_file": FileUtil("execurl_err").mktmp(),
            "output_file": FileUtil("execurl_out").mktmp(),
            "header_file": FileUtil("execurl_hdr").mktmp()
        }

    def _mkcurlcmd(self, *args, **kwargs):
        """Prepare curl command line according to invocation options"""
        self._files["url"] = str(args[0])
        if "ctimeout" in kwargs:
            self._opts["ctimeout"] = "--connect-timeout %s" \
                % (str(kwargs["ctimeout"]))
        if "timeout" in kwargs:
            self._opts["timeout"] = "-m %s" % (str(kwargs["timeout"]))
        if "proxy" in kwargs and kwargs["proxy"]:
            self._opts["proxy"] = "--proxy '%s'" % (str(kwargs["proxy"]))
        elif self.http_proxy:
            self._opts["proxy"] = "--proxy '%s'" % (self.http_proxy)
        if "header" in kwargs:
            for header_item in kwargs["header"]:
                self._opts["header"] += "-H '%s'" % (str(header_item))
        if "v" in kwargs and kwargs["v"]:
            self._opts["verbose"] = "-v"
        if "nobody" in kwargs and kwargs["nobody"]:
            self._opts["nobody"] = "--head"
        if "ofile" in kwargs:
            FileUtil(self._files["output_file"]).remove()
            self._files["output_file"] = kwargs["ofile"] + ".tmp"
            self._opts["timeout"] = "-m %s" % (str(self.download_timeout))
            if "resume" in kwargs and kwargs["resume"]:
                self._opts["resume"] = "-C -"
        return("curl " + " ".join(self._opts.values()) +
               " -D %s -o %s --stderr %s '%s'" %
               (self._files["header_file"], self._files["output_file"],
                self._files["error_file"], self._files["url"]))

    def get(self, *args, **kwargs):
        """http get implementation using the curl cli executable"""
        hdr = CurlHeader()
        buf = cStringIO.StringIO()
        self._set_defaults()
        cmd = self._mkcurlcmd(*args, **kwargs)
        status = subprocess.call(cmd, shell=True, close_fds=True)
        hdr.setvalue_from_file(self._files["header_file"])
        hdr.data["X-ND-CURLSTATUS"] = status
        if status:
            msg.out("Error: in download: %s"
                    % str(FileUtil(self._files["error_file"]).getdata()))
            return(hdr, buf)
        if "header" in kwargs:
            hdr.data["X-ND-HEADERS"] = kwargs["header"]
        if "ofile" in kwargs:
            if " 401" in hdr.data["X-ND-HTTPSTATUS"]:  # needs authentication
                pass
            elif " 206" in hdr.data["X-ND-HTTPSTATUS"] and "resume" in kwargs:
                os.rename(self._files["output_file"], kwargs["ofile"])
            elif " 416" in hdr.data["X-ND-HTTPSTATUS"]:
                if "resume" in kwargs:
                    kwargs["resume"] = False
                (hdr, buf) = self.get(self._files["url"], **kwargs)
            elif " 200" not in hdr.data["X-ND-HTTPSTATUS"]:
                msg.out("Error: in download: ", str(
                    hdr.data["X-ND-HTTPSTATUS"]), ": ", str(status))
                FileUtil(self._files["output_file"]).remove()
            else:  # OK downloaded
                os.rename(self._files["output_file"], kwargs["ofile"])
        else:
            try:
                buf = cStringIO.StringIO(open(self._files["output_file"],
                                              "r").read())
            except(IOError, OSError):
                msg.out("Error: reading curl output file to buffer")
            FileUtil(self._files["output_file"]).remove()
        FileUtil(self._files["error_file"]).remove()
        FileUtil(self._files["header_file"]).remove()
        return(hdr, buf)


class DockerIoAPI(object):
    """Class to encapsulate the access to the Docker Hub service
    Allows to search and download images from Docker Hub
    """

    def __init__(self, localrepo):
        self.index_url = conf.dockerio_index_url
        self.registry_url = conf.dockerio_registry_url
        self.v1_auth_header = ""
        self.v2_auth_header = ""
        self.localrepo = localrepo
        self.curl = GetURL()

    def set_proxy(self, http_proxy):
        """Select a socks http proxy for API access and file download"""
        self.curl.set_proxy(http_proxy)

    def is_repo_name(self, imagerepo):
        """Check if name matches authorized characters for a docker repo"""
        if re.match("^[a-zA-Z0-9-_./:]*$", imagerepo):
            return True
        msg.out("Error: invalid repo name syntax")
        return False

    def _get_url(self, *args, **kwargs):
        """Encapsulates the call to GetURL.get() so that authentication
        for v1 and v2 repositories can be treated differently.
        Example:
             _get_url(url, ctimeout=5, timeout=5, v=true, header=[]):
        """
        url = str(args[0])
        (hdr, buf) = self.curl.get(*args, **kwargs)
        msg.out("header: %s" % (hdr.data), l=3)
        if ("X-ND-HTTPSTATUS" in hdr.data and
                "401" in hdr.data["X-ND-HTTPSTATUS"]):
            if "www-authenticate" in hdr.data and hdr.data["www-authenticate"]:
                if "RETRY" not in kwargs:
                    kwargs["RETRY"] = 3
                if "RETRY" in kwargs and kwargs["RETRY"]:
                    auth_header = ""
                    if "/v2/" in url:
                        auth_header = self._get_v2_auth(
                            hdr.data["www-authenticate"])
                    elif "/v1/" in url:
                        auth_header = self._get_v1_auth(
                            hdr.data["www-authenticate"], "")
                    auth_kwargs = kwargs.copy()
                    auth_kwargs.update({"header": [auth_header]})
                    retry = kwargs["RETRY"] - 1
                    auth_kwargs.update({"RETRY": retry})
                    (hdr, buf) = self._get_url(*args, **auth_kwargs)
                else:
                    hdr.data["X-ND-CURLSTATUS"] = 13  # Permission denied
        return(hdr, buf)

    def _get_file(self, url, filename, cache_mode):
        """Get a file and check its size. Optionally enable other
        capabilities such as caching meaning check if the
        file already exists locally and whether its size is the
        same to avoid downloaded it again.
        """
        if self.curl.cache_support and cache_mode:
            if cache_mode == 1:
                (hdr, dummy) = self._get_url(url, nobody=1)
            elif cache_mode == 3:
                (hdr, dummy) = self._get_url(url, sizeonly=True)
            remote_size = self.curl.get_content_length(hdr)
            if remote_size == FileUtil(filename).size():
                return True             # is cached skip download
        else:
            remote_size = -1
        resume = False
        if filename.endswith("layer"):
            resume = True
        (hdr, dummy) = self._get_url(url, ofile=filename, resume=resume)
        if remote_size == -1:
            remote_size = self.curl.get_content_length(hdr)
        if (remote_size != FileUtil(filename).size() and
                hdr.data["X-ND-CURLSTATUS"]):
            msg.out("Error: file size mismatch:", filename,
                    remote_size, FileUtil(filename).size())
            return False
        return True

    def _split_fields(self, buf):
        """Split  fields, used in the web authentication"""
        all_fields = dict()
        for field in buf.split(","):
            pair = field.split("=", 1)
            if len(pair) == 2:
                all_fields[pair[0]] = pair[1].strip('"')
        return all_fields

    def get_repo_info(self, imagerepo):
        """Get repo info from Docker Hub"""
        url = self.index_url + "/repositories/" + imagerepo + "/"
        msg.out("repo url:", url, l=2)
        (hdr, buf) = self._get_url(url)
        try:
            return(hdr.data, json.loads(buf.getvalue()))
        except (IOError, OSError, AttributeError, ValueError, TypeError):
            return(hdr.data, [])

    def get_repo_list(self, imagerepo):
        """Get list of images in a repo from Docker Hub"""
        url = self.index_url + "/repositories/" + imagerepo + "/images"
        msg.out("repo url:", url, l=2)
        (hdr, buf) = self._get_url(url)
        try:
            return hdr.data, json.loads(buf.getvalue())
        except (IOError, OSError, AttributeError, ValueError, TypeError):
            return hdr.data, []

    def _get_v1_auth(self, www_authenticate, imagerepo):
        """Authentication for v1 API"""
        auth_header = ""
        if "Token" in www_authenticate:
            if imagerepo:
                auth_url = self.index_url + \
                    "/repositories/" + imagerepo + "/images"
                (auth_hdr, dummy) = self._get_url(
                    auth_url, header=["X-Docker-Token: true"])
                try:
                    auth_header = "Authorization: Token " + \
                        auth_hdr.data["x-docker-token"]
                except(IndexError, TypeError, KeyError):
                    return ""
                self.v1_auth_header = auth_header
            elif self.v1_auth_header:
                return self.v1_auth_header
        return auth_header

    def get_v1_image_tags(self, endpoint, imagerepo):
        """Get list of tags in a repo from Docker Hub"""
        url = endpoint + "/v1/repositories/" + imagerepo + "/tags"
        msg.out("tags url:", url, l=2)
        (hdr, buf) = self._get_url(url)
        try:
            return(hdr.data, json.loads(buf.getvalue()))
        except (IOError, OSError, AttributeError, ValueError, TypeError):
            return(hdr.data, dict())

    def get_v1_image_ancestry(self, endpoint, image_id):
        """Get the ancestry which is an ordered list of layers"""
        url = endpoint + "/v1/images/" + image_id + "/ancestry"
        msg.out("ancestry url:", url, l=2)
        (hdr, buf) = self._get_url(url)
        try:
            return(hdr.data, json.loads(buf.getvalue()))
        except (IOError, OSError, AttributeError, ValueError, TypeError):
            return(hdr.data, [])

    def get_v1_image_json(self, endpoint, layer_id):
        """Get the JSON metadata for a specific layer"""
        url = endpoint + "/v1/images/" + layer_id + "/json"
        msg.out("json url:", url, l=2)
        filename = self.localrepo.layersdir + "/" + layer_id + ".json"
        if self._get_file(url, filename, 0):
            self.localrepo.add_image_layer(filename)
            return True
        return False

    def get_v1_image_layer(self, endpoint, layer_id):
        """Get a specific layer data file (layer files are tarballs)"""
        url = endpoint + "/v1/images/" + layer_id + "/layer"
        msg.out("layer url:", url, l=2)
        filename = self.localrepo.layersdir + "/" + layer_id + ".layer"
        if self._get_file(url, filename, 3):
            self.localrepo.add_image_layer(filename)
            return True
        return False

    def get_v1_layers_all(self, endpoint, layer_list):
        """Using a layer list download data and metadata files"""
        files = []
        if layer_list:
            for layer_id in reversed(layer_list):
                msg.out("Downloading layer:", layer_id)
                filesize = self.get_v1_image_json(endpoint, layer_id)
                if not filesize:
                    return []
                files.append(layer_id + ".json")
                filesize = self.get_v1_image_layer(endpoint, layer_id)
                if not filesize:
                    return []
                files.append(layer_id + ".layer")
        return files

    def _get_v2_auth(self, www_authenticate):
        """Authentication for v2 API"""
        auth_header = ""
        (bearer, auth_data) = www_authenticate.split(" ", 1)
        if bearer == "Bearer":
            auth_fields = self._split_fields(auth_data)
            if "realm" in auth_fields:
                auth_url = auth_fields["realm"] + "?"
                for field in auth_fields:
                    if field != "realm":
                        auth_url += field + "=" + auth_fields[field] + "&"
                (dummy, auth_buf) = self._get_url(auth_url)
                token_buf = auth_buf.getvalue()
                if token_buf and "token" in token_buf:
                    try:
                        auth_token = json.loads(token_buf)
                    except (IOError, OSError, AttributeError,
                            ValueError, TypeError):
                        return auth_header
                    auth_header = "Authorization: Bearer " + \
                        auth_token["token"]
                    self.v2_auth_header = auth_header
        return auth_header

    def get_v2_image_manifest(self, endpoint, imagerepo, tag):
        """Get the image manifest which contains JSON metadata
        that is common to all layers in this image tag
        """
        if "/" in imagerepo:
            url = endpoint + "/v2/" + imagerepo + "/manifests/" + tag
        else:
            url = endpoint + "/v2/library/" + imagerepo + "/manifests/" + tag
        msg.out("manifest url:", url, l=2)
        (hdr, buf) = self._get_url(url)
        try:
            return(hdr.data, json.loads(buf.getvalue()))
        except (IOError, OSError, AttributeError, ValueError, TypeError):
            return(hdr.data, [])

    def get_v2_image_layer(self, endpoint, imagerepo, layer_id):
        """Get one image layer data file (tarball)"""
        if "/" in imagerepo:
            url = endpoint + "/v2/" + imagerepo + "/blobs/" + layer_id
        else:
            url = endpoint + "/v2/library/" + imagerepo + "/blobs/" + layer_id
        msg.out("layer url:", url, l=2)
        filename = self.localrepo.layersdir + "/" + layer_id
        if self._get_file(url, filename, 3):
            self.localrepo.add_image_layer(filename)
            return True
        return False

    def get_v2_layers_all(self, endpoint, imagerepo, fslayers):
        """Get all layer data files belonging to a image tag"""
        files = []
        if fslayers:
            for layer in reversed(fslayers):
                msg.out("Downloading layer:", layer["blobSum"])
                if not self.get_v2_image_layer(endpoint,
                                               imagerepo, layer["blobSum"]):
                    return []
                files.append(layer["blobSum"])
        return files

    def get_v2(self, endpoint, imagerepo, tag):
        """Pull container with v2 API"""
        (dummy, res) = self.get_v2_image_manifest(endpoint, imagerepo, tag)
        if "name" in res and imagerepo in res["name"] and "fsLayers" in res:
            if not (self.localrepo.setup_tag(tag) and
                    self.localrepo.set_version("v2")):
                msg.out("Error: setting localrepo v2 tag and version")
                return []
            self.localrepo.save_json("manifest", res)
            msg.out("v2 layers: %s" % (imagerepo), l=1)
            files = self.get_v2_layers_all(endpoint, imagerepo,
                                           res["fsLayers"])
            return files

    def get_v1(self, endpoint, imagerepo, tag):
        """Pull container with v1 API"""
        if not self._get_v1_auth("Token", imagerepo):
            return []
        msg.out("v1 tags: %s" % (imagerepo), l=1)
        (dummy, res) = self.get_v1_image_tags(endpoint, imagerepo)
        try:
            image_id = res[tag]
        except IndexError:
            return []
        if not (self.localrepo.setup_tag(tag) and
                self.localrepo.set_version("v1")):
            msg.out("Error: setting localrepo v1 tag and version")
            return []
        msg.out("v1 ancestry: %s" % image_id, l=1)
        (dummy, res) = self.get_v1_image_ancestry(endpoint, image_id)
        if res:
            self.localrepo.save_json("ancestry", res)
            msg.out("v1 layers: %s" % image_id, l=1)
            files = self.get_v1_layers_all(endpoint, res)
            return files

    def get(self, imagerepo, tag):
        """Pull a docker image from Docker Hub.
        Try the v2 API and if the download fails then try the v1 API.
        """
        msg.out("get imagerepo: %s tag: %s" % (imagerepo, tag))
        (hdr, dummy) = self.get_repo_list(imagerepo)
        if hdr and "x-docker-endpoints" in hdr:
            endpoint = "http://" + hdr["x-docker-endpoints"]
        else:
            if (hdr and "X-ND-HTTPSTATUS" in hdr and
                    "401" in hdr["X-ND-HTTPSTATUS"]):
                endpoint = self.registry_url          # Try docker registry
            elif (hdr and "X-ND-HTTPSTATUS" in hdr and
                  "404" in hdr["X-ND-HTTPSTATUS"]):
                msg.out("Error: image not found")
                return []
            else:
                msg.out("Error: failed to get endpoints:", str(hdr))
                return []
        self.localrepo.setup_imagerepo(imagerepo)
        files = self.get_v2(endpoint, imagerepo, tag)      # try v2
        if not files:
            files = self.get_v1(endpoint, imagerepo, tag)  # try v1
        return files

    def search_get_page(self, expression, page):
        """Get search result pages from Docker Hub"""
        if expression:
            url = self.index_url + "/search?q=" + expression
        else:
            url = self.index_url + "/search?"
        if page:
            url += "&page=" + str(page)
        (dummy, buf) = self._get_url(url)
        try:
            return json.loads(buf.getvalue())
        except (IOError, OSError, AttributeError, ValueError, TypeError):
            return []


class DockerLocalFileAPI(object):
    """Manipulate container and/or image files produced by Docker"""

    def __init__(self, localrepo):
        self.localrepo = localrepo

    def _load_structure(self, tmp_imagedir):
        """Load the structure of a Docker pulled image"""
        structure = {}
        structure["layers"] = dict()
        if FileUtil(tmp_imagedir).isdir():
            for fname in os.listdir(tmp_imagedir):
                f_path = tmp_imagedir + "/" + fname
                if fname == "repositories":
                    structure["repositories"] = (
                        self.localrepo.load_json(f_path))
                elif len(fname) == 64 and FileUtil(f_path).isdir():
                    layer_id = fname
                    structure["layers"][layer_id] = dict()
                    for layer_f in os.listdir(f_path):
                        layer_f_path = f_path + "/" + layer_f
                        if layer_f == "VERSION":
                            structure["layers"][layer_id]["VERSION"] = \
                                self.localrepo.load_json(layer_f_path)
                        elif layer_f == "json":
                            structure["layers"][layer_id]["json"] = \
                                self.localrepo.load_json(layer_f_path)
                            structure["layers"][layer_id]["json_f"] = (
                                layer_f_path)
                        elif "layer" in layer_f:
                            structure["layers"][layer_id]["layer_f"] = (
                                layer_f_path)
                        else:
                            msg.out("Warning: unkwnon file in layer:", f_path)
                else:
                    msg.out("Warning: unkwnon file in image:", f_path)
        return structure

    def _find_top_layer_id(self, structure, my_layer_id=""):
        """Find the top layer within a Docker image"""
        if "layers" not in structure:
            return []
        else:
            if not my_layer_id:
                my_layer_id = structure["layers"].keys()[0]
            found = ""
            for layer_id in structure["layers"]:
                if "parent" not in structure["layers"][layer_id]["json"]:
                    continue
                elif (my_layer_id ==
                      structure["layers"][layer_id]["json"]["parent"]):
                    found = self._find_top_layer_id(structure, layer_id)
                    break
            if not found:
                return my_layer_id
            else:
                return found

    def _sorted_layers(self, structure, top_layer_id):
        """Return the layers sorted"""
        sorted_layers = []
        next_layer = top_layer_id
        while next_layer:
            sorted_layers.append(next_layer)
            if "parent" not in structure["layers"][next_layer]["json"]:
                break
            else:
                next_layer = structure["layers"][next_layer]["json"]["parent"]
                if not next_layer:
                    break
        return sorted_layers

    def _copy_layer_to_repo(self, filepath, layer_id):
        """Move an image layer file to a repository (mv or cp)"""
        if filepath.endswith("json"):
            target_file = self.localrepo.layersdir + "/" + layer_id + ".json"
        elif filepath.endswith("layer.tar"):
            target_file = self.localrepo.layersdir + "/" + layer_id + ".layer"
        else:
            return False
        try:
            os.rename(filepath, target_file)
        except(IOError, OSError):
            if not FileUtil(filepath).copyto(target_file):
                return False
        self.localrepo.add_image_layer(target_file)
        return True

    def _load_image(self, structure, imagerepo, tag):
        """Load a container image into a repository mimic docker load"""
        if self.localrepo.cd_imagerepo(imagerepo, tag):
            msg.out("Error: repository and tag already exist", imagerepo, tag)
            return []
        else:
            self.localrepo.setup_imagerepo(imagerepo)
            tag_dir = self.localrepo.setup_tag(tag)
            if not tag_dir:
                msg.out("Error: setting up repository", imagerepo, tag)
                return []
            if not self.localrepo.set_version("v1"):
                msg.out("Error: setting repository version")
                return []
            try:
                top_layer_id = structure["repositories"][imagerepo][tag]
            except (IndexError, NameError):
                top_layer_id = self._find_top_layer_id(structure)
            for layer_id in self._sorted_layers(structure, top_layer_id):
                if str(structure["layers"][layer_id]["VERSION"]) != "1.0":
                    msg.out("Error: layer version unknown")
                    return []
                for layer_item in ("json_f", "layer_f"):
                    filename = str(structure["layers"][layer_id][layer_item])
                    if not self._copy_layer_to_repo(filename, layer_id):
                        msg.out("Error: copying %s file %s"
                                % (layer_item[:-2], filename))
                        return []
            self.localrepo.save_json("ancestry",
                                     self._sorted_layers(structure,
                                                         top_layer_id))
            return [imagerepo + ":" + tag]

    def _load_repositories(self, structure):
        """Load other image repositories into this local repo"""
        if "repositories" not in structure:
            return False
        loaded_repositories = []
        for imagerepo in structure["repositories"]:
            for tag in structure["repositories"][imagerepo]:
                if imagerepo and tag:
                    if self._load_image(structure,
                                        imagerepo, tag):
                        loaded_repositories.append(imagerepo + ":" + tag)
        return loaded_repositories

    def _untar_saved_container(self, tarfile, destdir):
        """Untar container created with docker save"""
        cmd = "umask 022 ; tar -C " + \
            destdir + " -x --delay-directory-restore "
        if msg.level > 1:
            cmd += " -v "
        cmd += " --one-file-system --no-same-owner "
        cmd += " --no-same-permissions --overwrite -f " + tarfile
        status = subprocess.call(cmd, shell=True, stderr=msg.chlderr,
                                 close_fds=True)
        return not status

    def load(self, imagefile):
        """Load a Docker file created with docker save, mimic Docker
        load. The file is a tarball containing several layers, each
        layer has metadata and data content (directory tree) stored
        as a tar file.
        """
        if not os.path.exists(imagefile):
            msg.out("Error: image file does not exist: ", imagefile)
            return False
        tmp_imagedir = FileUtil("import").mktmp()
        os.makedirs(tmp_imagedir)
        if not self._untar_saved_container(imagefile, tmp_imagedir):
            msg.out("Error: failed to extract container:", imagefile)
            FileUtil(tmp_imagedir).remove()
            return False
        structure = self._load_structure(tmp_imagedir)
        if not structure:
            msg.out("Error: failed to load image structure", imagefile)
            FileUtil(tmp_imagedir).remove()
            return False
        else:
            if "repositories" in structure and structure["repositories"]:
                repositories = self._load_repositories(structure)
            else:
                imagerepo = Unique().imagename()
                tag = "latest"
                repositories = self._load_image(structure, imagerepo, tag)
            FileUtil(tmp_imagedir).remove()
            return repositories

    def create_container_meta(self, layer_id, comment="created by udocker"):
        """Create metadata for a given container layer, used in import.
        A file for import is a tarball of a directory tree, does not contain
        metadata. This method creates minimal metadata.
        """
        container_json = dict()
        container_json["id"] = layer_id
        container_json["comment"] = comment
        container_json["created"] = \
            time.strftime("%Y-%m-%dT%H:%M:%S.000000000Z")
        container_json["architecture"] = conf.arch
        container_json["os"] = conf.osver
        layer_file = self.localrepo.layersdir + "/" + layer_id + ".layer"
        container_json["size"] = FileUtil(layer_file).size()
        if container_json["size"] == -1:
            container_json["size"] = 0
        container_json["container_config"] = {
            "Hostname": "",
            "Domainname": "",
            "User": "",
            "Memory": 0,
            "MemorySwap": 0,
            "CpusShares": 0,
            "Cpuset": "",
            "AttachStdin": False,
            "AttachStdout": False,
            "AttachStderr": False,
            "PortSpecs": None,
            "ExposedPorts": None,
            "Tty": False,
            "OpenStdin": False,
            "StdinOnce": False,
            "Env": None,
            "Cmd": None,
            "Image": "",
            "Volumes": None,
            "WorkingDir": "",
            "Entrypoint": None,
            "NetworkDisable": False,
            "MacAddress": "",
            "OnBuild": None,
            "Labels": None
        }
        container_json["config"] = {
            "Hostname": "",
            "Domainname": "",
            "User": "",
            "Memory": 0,
            "MemorySwap": 0,
            "CpusShares": 0,
            "Cpuset": "",
            "AttachStdin": False,
            "AttachStdout": False,
            "AttachStderr": False,
            "PortSpecs": None,
            "ExposedPorts": None,
            "Tty": False,
            "OpenStdin": False,
            "StdinOnce": False,
            "Env": None,
            "Cmd": None,
            "Image": "",
            "Volumes": None,
            "WorkingDir": "",
            "Entrypoint": None,
            "NetworkDisable": False,
            "MacAddress": "",
            "OnBuild": None,
            "Labels": None
        }
        return container_json

    def import_(self, tarfile, imagerepo, tag):
        """Import a tar file containing a simple directory tree possibly
        created with Docker export"""
        if not os.path.exists(tarfile):
            msg.out("Error: tar file does not exist: ", tarfile)
            return False
        self.localrepo.setup_imagerepo(imagerepo)
        tag_dir = self.localrepo.cd_imagerepo(imagerepo, tag)
        if tag_dir:
            msg.out("Error: tag already exists in repo: ", tag)
            return False
        tag_dir = self.localrepo.setup_tag(tag)
        if not tag_dir:
            msg.out("Error: creating repo and tag")
            return False
        if not self.localrepo.set_version("v1"):
            msg.out("Error: setting repository version")
            return False
        layer_id = Unique().layer_v1()
        layer_file = self.localrepo.layersdir + "/" + layer_id + ".layer"
        json_file = self.localrepo.layersdir + "/" + layer_id + ".json"
        try:
            os.rename(tarfile, layer_file)
        except(IOError, OSError):
            if not FileUtil(tarfile).copyto(layer_file):
                msg.out("Error: in move/copy file", tarfile)
                return False
        self.localrepo.add_image_layer(layer_file)
        self.localrepo.save_json("ancestry", [layer_id])
        container_json = self.create_container_meta(layer_id)
        self.localrepo.save_json(json_file, container_json)
        self.localrepo.add_image_layer(json_file)
        msg.out("Info: added layer", layer_id, l=1)
        return layer_id


class Udocker(object):
    """Implements most of the command line interface.
    These methods correspond directly to the commands that can
    be invoked via the command line interface.
    """

    def __init__(self, localrepo):
        self.localrepo = localrepo
        self.dockerioapi = DockerIoAPI(localrepo)
        self.dockerlocalfileapi = DockerLocalFileAPI(localrepo)

    def _cdrepo(self, cmdp):
        """Select the top directory of a local repository"""
        home = cmdp.get("P1")
        if cmdp.missing_options():               # syntax error
            return False
        if not FileUtil(home).isdir():
            msg.out("Warning: localrepo directory is invalid: ", home)
            return False
        self.localrepo.setup(home)
        return True

    def do_mkrepo(self, cmdp):
        """
        mkrepo: create a local repository in a specified directory
        mkrepo <directory>
        """
        home = cmdp.get("P1")
        if not home or not os.path.exists(home):
            self.localrepo.setup(home)
            if self.localrepo.create_repo():
                return True
            else:
                msg.out("Error: localrepo creation failure: ", home)
                return False
        else:
            msg.out("Error: localrepo directory already exists: ", home)
            return False

    def do_search(self, cmdp):
        """
        search: search dockerhub for container images
        search [options]  <expression>
        -a                         :show all entries, do not pause
        """
        pause = not cmdp.get("-a")
        expression = cmdp.get("P1")
        if cmdp.missing_options():               # syntax error
            return False
        if not self.dockerioapi.is_repo_name(expression):
            return False
        msg.out("%-40.40s %8.8s %s" %
                ("NAME", "OFFICIAL", "DESCRIPTION"))
        page = 1
        while True:
            repo_list = self.dockerioapi.search_get_page(expression, page)
            if not(repo_list and "results" in repo_list):
                return False
            if repo_list["page"] == repo_list["num_pages"]:
                return True
            if pause and page > 1:
                key_press = raw_input("press return")
                if key_press in ("q", "Q", "e", "E"):
                    return True
            for repo in repo_list["results"]:
                if repo["is_official"]:
                    is_official = "[OK]"
                else:
                    is_official = "----"
                description = ""
                for char in repo["description"]:
                    if char in string.printable:
                        description += char
                msg.out("%-40.40s %8.8s %s"
                        % (repo["name"], is_official, description))
            page += 1

    def do_load(self, cmdp):
        """
        load: load a container image saved by docker with 'docker save'
        load --input=<docker-exported-container-file>
        load -i <docker-exported-container-file>
        """
        imagefile = cmdp.get("--input=")
        if not imagefile:
            imagefile = cmdp.get("-i=")
        if cmdp.missing_options():  # syntax error
            return False
        if not imagefile:
            msg.out("Error: must specify filename of docker exported image")
            return False
        repos = self.dockerlocalfileapi.load(imagefile)
        if not repos:
            msg.out("Error: loading failed")
            return False
        else:
            for repo_item in repos:
                msg.out(repo_item)
            return True

    def do_import(self, cmdp):
        """
        import : import image (directory tree) from tar file
        import <tar-file> <repo/image:tag>
        """
        tarfile = cmdp.get("P1")
        imagespec = cmdp.get("P2")
        if cmdp.missing_options():               # syntax error
            return False
        if not tarfile:
            msg.out("Error: must specify tar filename")
            return False
        if not imagespec:
            msg.out("Error: must specify image:tag or repository/image:tag")
            return False
        imagerepo = imagespec
        tag = "latest"
        if imagespec and ":" in imagespec:
            (imagerepo, tag) = imagespec.split(":")
        if not self.dockerlocalfileapi.import_(tarfile, imagerepo, tag):
            msg.out("Error: importing file")
            return False
        return True

    def do_pull(self, cmdp):
        """
        pull: download images from docker hub
        pull [options] <repo/image:tag>
        --httpproxy=socks4://user:pass@host:port        :use http proxy
        --httpproxy=socks5://user:pass@host:port        :use http proxy
        --httpproxy=socks4://host:port                  :use http proxy
        --httpproxy=socks5://host:port                  :use http proxy
        --index=https://index.docker.io/v1              :docker index
        --registry=https://registry-1.docker.io         :docker registry
        """
        conf.dockerio_index_url = cmdp.get("--index=")
        conf.dockerio_registry_url = cmdp.get("--registry=")
        http_proxy = cmdp.get("--httpproxy=")
        imagespec = cmdp.get("P1")
        if cmdp.missing_options():               # syntax error
            return False
        if not imagespec:
            msg.out("Error: must specify image:tag or repository/image:tag")
            return False
        if not self.dockerioapi.is_repo_name(imagespec):
            return False
        imagerepo = imagespec
        tag = "latest"
        if imagespec and ":" in imagespec:
            (imagerepo, tag) = imagespec.split(":")
        if imagerepo and tag:
            if http_proxy:
                self.dockerioapi.set_proxy(http_proxy)
            files = self.dockerioapi.get(imagerepo, tag)
            if files:
                msg.out(files)
                return True
        return False

    def do_create(self, cmdp):
        """
        create: extract image layers and create a container
        create [options]  <repo/image:tag>
        --name=xxxx                :set or change the name of the container
        """
        imagespec = cmdp.get("P1")
        name = cmdp.get("--name=")
        if cmdp.missing_options():               # syntax error
            return False
        container_id = self._create(imagespec)
        if container_id:
            msg.out(container_id)
            if name and not self.localrepo.set_container_name(container_id,
                                                              name):
                msg.out("Error: invalid container name may already exist "
                        "or wrong format")
                return False
            return True
        else:
            return False

    def _create(self, imagespec):
        """Auxiliary to create(), performs the creation"""
        if not imagespec:
            msg.out("Error: must specify image:tag or repository/image:tag")
            return False
        imagerepo = imagespec
        tag = "latest"
        if imagespec and ":" in imagespec:
            (imagerepo, tag) = imagespec.split(":")
        if imagerepo and tag:
            container = Container(self.localrepo)
            return container.create(imagerepo, tag)
        return False

    def _get_run_options(self, cmdp, container):
        """Read command line options into variables"""
        cmdp.declare_options("-v= -e= -w= -u= -i -t -a")
        cmd_options = {
            "novol": {
                "fl": ("--novol=",), "act": "R",
                "p2": "CMD_OPT", "p3": True
            },
            "vol": {
                "fl": ("-v=", "--volume=",), "act": "E",
                "p2": "CMD_OPT", "p3": True
            },
            "env": {
                "fl": ("-e=", "--env=",), "act": "E",
                "p2": "CMD_OPT", "p3": True
            },
            "user": {
                "fl": ("-u=", "--user=",), "act": "R",
                "p2": "CMD_OPT", "p3": False
            },
            "cwd": {
                "fl": ("-w=", "--workdir=",), "act": "R",
                "p2": "CMD_OPT", "p3": False
            },
            "entryp": {
                "fl": ("--entrypoint=",), "act": "R",
                "p2": "CMD_OPT", "p3": False
            },
            "cpuset": {
                "fl": ("--cpuset-cpus=",), "act": "R",
                "p2": "CMD_OPT", "p3": False
            },
            "hostauth": {
                "fl": ("--hostauth",), "act": "R",
                "p2": "CMD_OPT", "p3": False
            },
            "nosysdirs": {
                "fl": ("--nosysdirs",), "act": "R",
                "p2": "CMD_OPT", "p3": False
            },
            "hostenv": {
                "fl": ("--hostenv",), "act": "R",
                "p2": "CMD_OPT", "p3": False
            },
            "bindhome": {
                "fl": ("--bindhome",), "act": "R",
                "p2": "CMD_OPT", "p3": False
            },
            "nometa": {
                "fl": ("--nometa",), "act": "R",
                "p2": "CMD_OPT", "p3": False
            },
            "dri": {
                "fl": ("--dri",), "act": "R",
                "p2": "CMD_OPT", "p3": False
            },
            "cmd": {
                "fl": ("P+",), "act": "R",
                "p2": "CMD_OPT", "p3": False
            },
            "volfrom": {
                "fl": ("--volumes-from=",), "act": "R",
                "p2": "CMD_OPT", "p3": False
            },
            "dns": {
                "fl": ("--dns=",), "act": "R",
                "p2": "CMD_OPT", "p3": False
            },
            "dnssearch": {
                "fl": ("--dns-search=",), "act": "R",
                "p2": "CMD_OPT", "p3": False
            },
            "kernel": {
                "fl": ("--kernel=",), "act": "R",
                "p2": "CMD_OPT", "p3": False
            }
        }
        for option, cmdp_args in cmd_options.iteritems():
            last_value = None
            for cmdp_fl in cmdp_args["fl"]:
                option_value = cmdp.get(cmdp_fl,
                                        cmdp_args["p2"], cmdp_args["p3"])
                if cmdp_args["act"] == "R":   # action is replace
                    if option_value or last_value is None:
                        container.opt[option] = option_value
                elif cmdp_args["act"] == "E":   # action is extend
                    container.opt[option].extend(option_value)
                last_value = option_value

    def do_run(self, cmdp):
        """
        run: execute a container
        run [options] <container-id-or-name>
        --rm                       :delete container upon exit
        --workdir=/home/userXX     :working directory set to /home/userXX
        --user=userXX              :run as userXX
        --user=root                :run as root
        --volume=/data:/mnt        :run mounting host directory /data in /mnt
        --novol=/proc              :remove /proc from list of volumes to mount
        --env="MYTAG=xxx"          :set environment variable
        --hostauth                 :bind the host /etc/passwd /etc/group ...
        --nosysdirs                :do not bind the host /proc /sys /run /dev
        --nometa                   :ignore container metadata
        --dri                      :bind directories relevant for dri graphics
        --hostenv                  :pass the host environment to the container
        --cpuset-cpus=<1,2,3-4>    :pass the host environment to the container
        --name=<container-name>    :set or change the name of the container
        --bindhome                 :bind the home directory into the container
        --location=<path-to-dir>   :use root tree outside the repository
        --kernel=<kernel-id>       :use this Linux kernel identifier
        """
        container = Container(self.localrepo)
        self._get_run_options(cmdp, container)
        container_or_image = cmdp.get("P1")
        conf.location = cmdp.get("--location=")
        delete = cmdp.get("--rm")
        name = cmdp.get("--name=")
        #
        if cmdp.missing_options():               # syntax error
            return False
        if conf.location:
            container_id = ""
        else:
            container_id = self.localrepo.get_container_id(container_or_image)
            if not container_id:
                imagerepo = container_or_image
                tag = "latest"
                if imagerepo and ":" in imagerepo:
                    (imagerepo, tag) = imagerepo.split(":")
                if (imagerepo and tag and
                        self.localrepo.cd_imagerepo(imagerepo, tag)):
                    container_id = self._create(imagerepo+":"+tag)
                if not container_id:
                    msg.out("Error: image or container not available")
                    return False
            if name and container_id:
                if not self.localrepo.set_container_name(container_id, name):
                    msg.out("Error: invalid container name format")
                    return False
        status = container.run(container_id)
        if delete and not self.localrepo.isprotected_container(container_id):
            self.localrepo.del_container(container_id)
        return status

    def do_images(self, cmdp):
        """
        images: list container images
        images [options]
        -l                         :long format
        """
        verbose = cmdp.get("-l")
        if cmdp.missing_options():               # syntax error
            return False
        images_list = self.localrepo.get_imagerepos()
        msg.out("REPOSITORY")
        for (imagerepo, tag) in images_list:
            prot = (".", "P")[
                self.localrepo.isprotected_imagerepo(imagerepo, tag)]
            msg.out("%-60.60s %c" % (imagerepo + ":" + tag, prot))
            if verbose:
                imagerepo_dir = self.localrepo.cd_imagerepo(imagerepo, tag)
                msg.out("  %s" % (imagerepo_dir))
                layers_list = self.localrepo.get_layers(imagerepo, tag)
                if layers_list:
                    for (layer_name, size) in layers_list:
                        file_size = size / (1024 * 1024)
                        if not file_size and size:
                            file_size = 1
                        msg.out("    %s (%d MB)" %
                                (layer_name.replace(imagerepo_dir, ""),
                                 file_size))
        return True

    def do_ps(self, cmdp):
        """
        ps: list containers
        """
        if cmdp.missing_options():               # syntax error
            return False
        containers_list = self.localrepo.get_containers_list(False)
        msg.out("%-36.36s %c %c %-18s %-s" %
                ("CONTAINER ID", "P", "M", "NAMES", "IMAGE"))
        for (container_id, reponame, names) in containers_list:
            prot = (".", "P")[
                self.localrepo.isprotected_container(container_id)]
            write = ("R", "W", "N", "D")[
                self.localrepo.iswriteable_container(container_id)]
            msg.out("%-36.36s %c %c %-18s %-s" %
                    (container_id, prot, write, names, reponame))

    def do_rm(self, cmdp):
        """
        rm: delete a container
        rm <container_id>
        """
        container_id_list = cmdp.get("P*")
        if cmdp.missing_options():               # syntax error
            return False
        if not container_id_list:
            msg.out("Error: must specify image:tag or repository/image:tag")
            return False
        status = True
        for container_id in cmdp.get("P*"):
            container_id = self.localrepo.get_container_id(container_id)
            if not container_id:
                msg.out("Error: invalid container id", container_id)
                status = False
                continue
            else:
                if self.localrepo.isprotected_container(container_id):
                    msg.out("Error: container is protected")
                    status = False
                    continue
                msg.out("Deleting container:", str(container_id), l=1)
                if not self.localrepo.del_container(container_id):
                    msg.out("Error: deleting container")
                    status = False
        return status

    def do_rmi(self, cmdp):
        """
        rmi: delete an image in the local repository
        rmi [options] <repo/image:tag>
        -f                          :force removal
        """
        force = cmdp.get("-f")
        imagespec = str(cmdp.get("P1"))
        (imagerepo, tag) = self._check_imagespec(imagespec)
        if cmdp.missing_options():               # syntax error
            return False
        if not (imagerepo and tag):
            return False
        else:
            if self.localrepo.isprotected_imagerepo(imagerepo, tag):
                msg.out("Error: image repository is protected")
                return False
            msg.out("Deleting image:", imagespec, l=1)
            if not self.localrepo.del_imagerepo(imagerepo, tag, force):
                msg.out("Error: deleting image")
                return False
            return True

    def do_protect(self, cmdp):
        """
        protect: protect a container or image against deletion
        protect <container-id or repo/image:tag>
        """
        arg = cmdp.get("P1")
        if cmdp.missing_options():               # syntax error
            return False
        if self.localrepo.get_container_id(arg):
            if not self.localrepo.protect_container(arg):
                msg.out("Error: protect container failed")
                return False
            else:
                return True
        else:
            (imagerepo, tag) = self._check_imagespec(cmdp.get("P1"))
            if imagerepo and tag:
                if self.localrepo.protect_imagerepo(imagerepo, tag):
                    return True
            msg.out("Error: protect image failed")
            return False

    def do_unprotect(self, cmdp):
        """
        unprotect: remove delete protection
        unprotect <container-id or repo/image:tag>
        """
        arg = cmdp.get("P1")
        if cmdp.missing_options():               # syntax error
            return False
        if self.localrepo.get_container_id(arg):
            if not self.localrepo.unprotect_container(arg):
                msg.out("Error: unprotect container failed")
                return False
            else:
                return True
        else:
            (imagerepo, tag) = self._check_imagespec(cmdp.get("P1"))
            if imagerepo and tag:
                if self.localrepo.unprotect_imagerepo(imagerepo, tag):
                    return True
            msg.out("Error: unprotect image failed")
            return False

    def do_name(self, cmdp):
        """
        name: give a name alias to a container
        name <container-id> <container-name>
        """
        container_id = cmdp.get("P1")
        name = cmdp.get("P2")
        if cmdp.missing_options():               # syntax error
            return False
        if not (self.localrepo.get_container_id(container_id) and name):
            msg.out("Error: invalid container id or name")
            return False
        if not self.localrepo.set_container_name(container_id, name):
            msg.out("Error: invalid container name")
            return False
        return True

    def do_rmname(self, cmdp):
        """
        rmname: remove name from container
        rmname <container-name>
        """
        name = cmdp.get("P1")
        if cmdp.missing_options():               # syntax error
            return False
        if not name:
            msg.out("Error: invalid container id or name")
            return False
        if not self.localrepo.del_container_name(name):
            msg.out("Error: removing container name")
            return False
        return True

    def _check_imagespec(self, imagespec):
        """Perform the image verification"""
        imagerepo = imagespec
        tag = "latest"
        if imagespec and ":" in imagespec:
            (imagerepo, tag) = imagespec.split(":")
        if not (imagespec and tag):
            msg.out("Error: must specify image:tag or repository/image:tag")
            return(False, False)
        return imagerepo, tag

    def do_inspect(self, cmdp):
        """
        inspect: print container metadata JSON from an imagerepo or container
        inspect <container-id or repo/image:tag>
        -p                         :print container directory path on host
        """
        container_or_image = cmdp.get("P1")
        container_id = self.localrepo.get_container_id(container_or_image)
        print_dir = cmdp.get("-p")
        if cmdp.missing_options():               # syntax error
            return False
        if container_id:
            (container_dir, container_json) = \
                Container(self.localrepo).get_container_attr(container_id)
        else:
            (imagerepo, tag) = self._check_imagespec(container_or_image)
            if self.localrepo.cd_imagerepo(imagerepo, tag):
                (container_json, dummy) = self.localrepo.get_image_attributes()
            else:
                return False
        if print_dir:
            if container_id and container_dir:
                msg.out(str(container_dir) + "/ROOT")
                return True
        elif container_json:
            try:
                msg.out(json.dumps(container_json, sort_keys=True,
                                   indent=4, separators=(',', ': ')))
            except (IOError, OSError, AttributeError, ValueError, TypeError):
                msg.out(container_json)
            return True
        return False

    def do_verify(self, cmdp):
        """
        verify: verify an image
        verify <repo/image:tag>
        """
        (imagerepo, tag) = self._check_imagespec(cmdp.get("P1"))
        if cmdp.missing_options():               # syntax error
            return False
        if not (imagerepo and tag):
            return False
        else:
            msg.out("Verifying: %s:%s" % (imagerepo, tag))
            if not self.localrepo.cd_imagerepo(imagerepo, tag):
                msg.out("Error: selecting image and tag")
                return False
            else:
                if self.localrepo.verify_image():
                    msg.out("Image Ok")
                    return True
                else:
                    msg.out("Error: image verification failure")
                    return False

    def do_version(self, dummy):
        """Print the version number"""
        try:
            msg.out("%s %s" % ("udocker", __version__))
        except NameError:
            pass

    def do_help(self, cmdp):
        """
        Syntax:
          udocker  <command>  [command_options]  <command_args>

        Commands:
          search <repo/image:tag>     :Search dockerhub for container images
          pull <repo/image:tag>       :Pull container image from dockerhub
          images                      :List container images
          create <repo/image:tag>     :Create container from a pulled image
          ps                          :List created containers
          rm  <container_id>          :Delete container
          run <container_id>          :Execute container
          inspect <container_id>      :Low level information on container
          name <container_id> <name>  :Give name to container
          rmname <name>               :Delete name from container

          rmi <repo/image:tag>        :Delete image
          rm <container-id>           :Delete container
          import <container-id>       :Import tar file (exported by docker)
          load -i <exported-image>    :Load container image saved by docker
          inspect <repo/image:tag>    :Return low level information on image
          verify <repo/image:tag>     :Verify a pulled image

          protect <repo/image:tag>    :Protect repository
          unprotect <repo/image:tag>  :Unprotect repository
          protect <container_id>      :Protect container
          unprotect <container_id>    :Unprotect container

          mkrepo <topdir>             :Create repository in another location

          help                        :This help
          run --help                  :Command specific help

        Options common to all commands must appear before the command:
          -D                          :Debug
          --repo=<directory>          :Use repository at directory

        Examples:
          1. udocker search fedora
          2. udocker pull fedora
          3. udocker create --name=fed  fedora
          4. udocker run  fed  cat /etc/redhat-release
          5. udocker run --hostauth --hostenv --bindhome  fed
          6. udocker run --user=root  fed  yum install firefox
          7. udocker run --hostauth --hostenv --bindhome fed   firefox
          8. udocker run --hostauth --hostenv --bindhome fed   /bin/bash -i
          9. udocker run --user=root  fed  yum install cheese
         10. udocker run --hostauth --hostenv --bindhome --dri fed  cheese
         11. udocker --repo=/home/x/.udocker  images
         12. udocker -D run --user=1001:5001  fedora

        Notes:
          1. by default the following host directories are mounted in the
             container:
               /dev /proc /sys
               /etc/resolv.conf /etc/host.conf /etc/hostname
          2. to prevent the mount of the above directories use:
               run  --nosysdirs  <container_id>
          3. additional host directories to be mounted are specified with:
               run --volume=/data:/mnt --volume=/etc/hosts  <container_id>
               run --nosysdirs --volume=/dev --volume=/proc  <container_id>
        """
        cmd_help = cmdp.get("", "CMD")
        try:
            text = eval("self.do_" + cmd_help + ".__doc__")
            if text:
                msg.out(text)
                return
        except AttributeError:
            pass
        msg.out(self.do_help.__doc__)


class CmdParser(object):
    """Implements a simple command line parser.
    Divides the command into parameters and options
    that can be queried for presence and value.
    The general command format is:
      $ udocker command arg1 arg2 --opta --optb=zzz
    """

    def __init__(self):
        """constructor parses the user command line"""
        self._argv = ""
        self._argv_split = dict()
        self._argv_consumed_options = dict()
        self._argv_consumed_params = dict()
        self._regex_argv = \
            "[^ ]+((?: +--?[a-zA-Z0-9_]+(?:=[^ ]+)?)+)?( +[a-zA-Z0-9_]+)?(.*)"
        self._argv_split['CMD'] = ""
        self._argv_split['GEN_OPT'] = ""
        self._argv_split['CMD_OPT'] = ""
        self._argv_consumed_options['GEN_OPT'] = []
        self._argv_consumed_options['CMD_OPT'] = []
        self._argv_consumed_params['GEN_OPT'] = []
        self._argv_consumed_params['CMD_OPT'] = []

    def parse(self, argv):
        """Parse a command line string passed to the constructor
        divides the string in three blocks udocker general_options
        udocker command and udocker command options/arguments
        """
        self._argv = argv
        matched = re.match(self._regex_argv, " ".join(self._argv))
        if matched:
            if matched.group(1):
                self._argv_split['GEN_OPT'] = matched.group(1).strip()
            if matched.group(3):
                self._argv_split['CMD_OPT'] = matched.group(3).strip()
            if matched.group(2):
                self._argv_split['CMD'] = matched.group(2).strip()
            return True
        else:
            return False

    def missing_options(self):
        """Get comamnd line options not used/fetched by Cmdp.get()
        """
        all_opt = []
        for pos in range(len(self._argv_split['GEN_OPT'].split())):
            if (pos not in self._argv_consumed_options['GEN_OPT'] and
                    pos not in self._argv_consumed_params['GEN_OPT']):
                all_opt.append(self._argv_split['GEN_OPT'].split(" ")[pos])
        for pos in range(len(self._argv_split['CMD_OPT'].split())):
            if (pos not in self._argv_consumed_options['CMD_OPT'] and
                    pos not in self._argv_consumed_params['CMD_OPT']):
                all_opt.append(self._argv_split['CMD_OPT'].split(" ")[pos])
        return all_opt

    def get(self, opt_name, opt_where="CMD_OPT", opt_multiple=False):
        """Get the value of a command line option --xyz=
        multiple=true  multiple occurences of option can be present
        """
        if opt_where == "CMD":
            return self._argv_split[opt_where]
        elif opt_where in ("CMD_OPT", "GEN_OPT"):
            if opt_name.startswith("P"):
                return(self._get_param(opt_name,
                                       self._argv_split[opt_where],
                                       self._argv_consumed_options[opt_where],
                                       self._argv_consumed_params[opt_where]))
            elif opt_name.startswith("-"):
                return(self._get_option(opt_name,
                                        self._argv_split[opt_where],
                                        self._argv_consumed_options[opt_where],
                                        opt_multiple))
        return None

    def declare_options(self, opts_string, opt_where="CMD_OPT"):
        """Declare in advance options that are part of the command line
        """
        pos = 0
        opt_list = self._argv_split[opt_where].strip().split()
        while pos < len(opt_list):
            for opt_name in opts_string.strip().split():
                if opt_name.endswith("="):
                    if opt_list[pos].startswith(opt_name):
                        self._argv_consumed_options[opt_where].append(pos)
                    elif opt_list[pos] == opt_name[:-1]:
                        self._argv_consumed_options[opt_where].append(pos)
                        if (pos < len(opt_list) and
                                not opt_list[pos+1].startswith("-")):
                            self._argv_consumed_options[opt_where].\
                                append(pos + 1)
                elif opt_list[pos] == opt_name:
                    self._argv_consumed_options[opt_where].append(pos)
            pos += 1

    def _get_option(self, opt_name, opt_string, consumed, opt_multiple):
        """Get command line options such as: -x -x= --x --x=
        The options may exist in the first and third part od the udocker
        command line.
        """
        all_args = []
        opt_list = opt_string.split(" ")
        pos = 0
        while pos < len(opt_list):
            opt_arg = None
            if ((not opt_list[pos].startswith("-")) and
                    (pos < 1 or (pos not in consumed and not
                                 opt_list[pos-1].endswith("=")))):
                break        # end of options and start of arguments
            elif opt_name.endswith("="):
                if opt_list[pos].startswith(opt_name):
                    opt_arg = opt_list[pos].split("=", 1)[1].strip().strip('"')
                elif (opt_list[pos] == opt_name[:-1] and
                      not opt_list[pos + 1].startswith("-")):
                    consumed.append(pos)
                    pos += 1
                    opt_arg = opt_list[pos]
            elif opt_list[pos] == opt_name:
                consumed.append(pos)
                opt_arg = True
            pos += 1
            if opt_arg is None:
                continue
            else:
                consumed.append(pos-1)
                if opt_multiple:
                    all_args.append(opt_arg)
                else:
                    return opt_arg
        if opt_multiple:
            return all_args
        else:
            return False

    def _get_param(self, opt_name, opt_string, consumed, consumed_params):
        """Get command line parameters
        The CLI of udocker has 3 parts, first options, second command name
        third everything after the command name. The params are the arguments
        that do not start with - and may exist after the options.
        """
        all_args = []
        opt_list = opt_string.split(" ")
        pos = 0
        param_num = 0
        skip_opts = True
        while pos < len(opt_list):
            if not (skip_opts and
                    (opt_list[pos].startswith("-") or pos in consumed)):
                skip_opts = False
                param_num += 1
                if opt_name[1:] == str(param_num):
                    consumed_params.append(pos)
                    return opt_list[pos]
                elif opt_name[1] == '*':
                    consumed_params.append(pos)
                    all_args.append(opt_list[pos])
                elif opt_name[1] == '+' and param_num > 0:
                    consumed_params.append(pos)
                    all_args.append(opt_list[pos])
            pos += 1
        if opt_name[1] == '*':
            return all_args
        elif opt_name[1] == '+':
            return all_args[1:]
        else:
            return None


class Main(object):
    """Get options, parse and execute the command line"""
    def __init__(self):
        self.cmdp = CmdParser()
        if not self.cmdp.parse(sys.argv):
            msg.out("Error: parsing command line, use: udocker --help")
            sys.exit(1)
        conf.user_init(self.cmdp.get("--config=", "GEN_OPT"))
        if (self.cmdp.get("--debug", "GEN_OPT") or
                self.cmdp.get("-D", "GEN_OPT")):
            conf.verbose_level = 3
        msg.setlevel(conf.verbose_level)
        if self.cmdp.get("--repo=", "GEN_OPT"):  # override repo root tree
            conf.def_topdir = self.cmdp.get("--repo=", "GEN_OPT")
            if not LocalRepository(conf.def_topdir).is_repo():
                msg.out("Error: invalid udocker repository: " +
                        conf.def_topdir)
                sys.exit(1)
        self.localrepo = LocalRepository(conf.def_topdir)
        if not LocalRepository(conf.def_topdir).is_repo():
            msg.out("Info: creating repo: " + conf.def_topdir)
            self.localrepo.create_repo()
        self.udocker = Udocker(self.localrepo)
        if self.cmdp.get("--insecure", "GEN_OPT"):  # override repo root tree
            conf.http_insecure = True
        if not UdockerTools(self.localrepo).download():
            msg.out("Error: install of udockertools failed")
        import_modules()

    def execute(self):
        """Command parsing and selection"""
        cmds = {
            "help": self.udocker.do_help, "search": self.udocker.do_search,
            "images": self.udocker.do_images, "pull": self.udocker.do_pull,
            "create": self.udocker.do_create, "ps": self.udocker.do_ps,
            "run": self.udocker.do_run, "version": self.udocker.do_version,
            "rmi": self.udocker.do_rmi, "mkrepo": self.udocker.do_mkrepo,
            "import": self.udocker.do_import, "load": self.udocker.do_load,
            "protect": self.udocker.do_protect, "rm": self.udocker.do_rm,
            "name": self.udocker.do_name, "rmname": self.udocker.do_rmname,
            "unprotect": self.udocker.do_unprotect,
            "inspect": self.udocker.do_inspect,
            "verify": self.udocker.do_verify,
        }
        if (self.cmdp.get("--help", "GEN_OPT") or
                self.cmdp.get("-h", "GEN_OPT")):
            self.udocker.do_help(self.cmdp)
            return 0
        else:
            command = self.cmdp.get("", "CMD")
            if command in cmds:
                if self.cmdp.get("--help") or self.cmdp.get("-h"):
                    self.udocker.do_help(self.cmdp)   # help on command
                    return 0
                status = cmds[command](self.cmdp)     # executes the command
                if self.cmdp.missing_options():
                    msg.out("Error: syntax error at: %s" %
                            " ".join(self.cmdp.missing_options()))
                    return 1
                if isinstance(status, bool):
                    return not status
                elif isinstance(status, (int, long)):
                    return status                     # return command status
            else:
                msg.out("Error: invalid command:", command, "\n")
                self.udocker.do_help(self.cmdp)

    def start(self):
        """Program start and exception handling"""
        try:
            exit_status = self.execute()
        except (KeyboardInterrupt, SystemExit):
            FileUtil("").cleanup()
            return 1
        except:
            FileUtil("").cleanup()
            raise
        else:
            FileUtil("").cleanup()
            return exit_status

# pylint: disable=invalid-name
if __name__ == "__main__":
    msg = Msg()
    if not os.geteuid():
        msg.out("Error: do not run as root !")
        sys.exit(1)
    conf = Config()
    sys.exit(Main().start())
