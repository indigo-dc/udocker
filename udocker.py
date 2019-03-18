#!/usr/bin/env python2
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
import stat
import string
import re
import subprocess
import time
import pwd
import grp
import platform
import glob
import select
import ast

__author__ = "udocker@lip.pt"
__copyright__ = "Copyright 2017, LIP"
__credits__ = ["PRoot http://proot.me",
               "runC https://runc.io",
               "Fakechroot https://github.com/dex4er/fakechroot",
               "Singularity http://singularity.lbl.gov"
              ]
__license__ = "Licensed under the Apache License, Version 2.0"
__version__ = "1.1.3"
__date__ = "2018"

# Python version major.minor
PY_VER = "%d.%d" % (sys.version_info[0], sys.version_info[1])

START_PATH = os.path.dirname(os.path.realpath(sys.argv[0]))

try:
    import cStringIO
except ImportError:
    from io import BytesIO as cStringIO
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
    import base64
except ImportError:
    pass
try:
    import hashlib
except ImportError:
    pass
try:
    from getpass import getpass
except ImportError:
    getpass = raw_input

try:
    import json
except ImportError:
    sys.path.append(START_PATH + "/../lib/simplejson")
    sys.path.append(os.path.expanduser('~') + "/.udocker/lib/simplejson")
    sys.path.append(str(os.getenv("UDOCKER_DIR")) + "/lib/simplejson")
    try:
        import simplejson as json
    except ImportError:
        pass


class Uprocess(object):
    """Provide alternative implementations for subprocess"""

    def _check_output(self, *popenargs, **kwargs):
        """Alternative to subprocess.check_output"""
        process = subprocess.Popen(*popenargs, stdout=subprocess.PIPE, **kwargs)
        output, dummy = process.communicate()
        retcode = process.poll()
        if retcode:
            cmd = kwargs.get("args")
            if cmd is None:
                cmd = popenargs[0]
            raise subprocess.CalledProcessError(retcode, cmd)
        return output

    def check_output(self, *popenargs, **kwargs):
        """Select check_output implementation"""
        if PY_VER >= "2.7":
            return subprocess.check_output(*popenargs, **kwargs)
        return self._check_output(*popenargs, **kwargs)

    def get_output(self, cmd):
        """Execute a shell command and get its output"""
        try:
            content = self.check_output(cmd, shell=True,
                                        stderr=Msg.chlderr,
                                        close_fds=True)
        except subprocess.CalledProcessError:
            return None
        return content.strip()


class Config(object):
    """Default configuration values for the whole application. Changes
    to these values should be made via a configuration file read via
    self.user_init() and that can reside in ~/.udocker/udocker.conf
    """

    try:
        verbose_level = int(os.getenv("UDOCKER_LOGLEVEL", ""))
    except ValueError:
        verbose_level = 3

    homedir = os.path.expanduser("~") + "/.udocker"

    topdir = homedir
    bindir = None
    libdir = None
    reposdir = None
    layersdir = None
    containersdir = None

    uid = os.getuid()
    gid = os.getgid()

    # udocker installation tarball
    tarball_release = "1.1.3"
    tarball = (
        "https://owncloud.indigo-datacloud.eu/index.php"
        "/s/iv4FOV1jZcfnGFH/download"
        " "
        "https://cernbox.cern.ch/index.php"
        "/s/CS31ycKOpj2KzxO/download?x-access-token=eyJhbGciOiJIUzI1Ni"
        "IsInR5cCI6IkpXVCJ9.eyJleHAiOiIyMDE4LTEwLTMwVDE4OjM1OjMyLjI2MD"
        "AxMDA3OCswMTowMCIsImV4cGlyZXMiOjAsImlkIjoiMTQ1NjgwIiwiaXRlbV9"
        "0eXBlIjowLCJtdGltZSI6MTU0MDkxNzA3Miwib3duZXIiOiJqb3JnZSIsInBh"
        "dGgiOiJlb3Nob21lLWo6MjcyNTgzNjk2NDc1NzUwNDAiLCJwcm90ZWN0ZWQiO"
        "mZhbHNlLCJyZWFkX29ubHkiOnRydWUsInNoYXJlX25hbWUiOiJ1ZG9ja2VyLT"
        "EuMS4zLnRhci5neiIsInRva2VuIjoiQ1MzMXljS09wajJLenhPIn0._9LTvxM"
        "V12NpxcZXaCg3PJeQfz94qYui4ccscrrvgVA"
        " "
        "https://download.ncg.ingrid.pt/webdav/udocker/udocker-1.1.3.tar.gz"
    )

    installinfo = ["https://raw.githubusercontent.com/indigo-dc/udocker/master/messages", ]

    autoinstall = True

    config = "udocker.conf"
    keystore = "keystore"

    # for tmp files only
    tmpdir = "/tmp"

    # defaults for container execution
    cmd = ["/bin/bash", "-i"]  # Comand to execute

    # default path for executables
    root_path = "/usr/sbin:/sbin:/usr/bin:/bin"
    user_path = "/usr/local/bin:/usr/bin:/bin"

    # directories to be mapped in contaners with: run --sysdirs
    sysdirs_list = (
        "/dev", "/proc", "/sys", "/etc/resolv.conf", "/etc/host.conf",
        "/lib/modules",
    )

    # directories to be mapped in contaners with: run --hostauth
    hostauth_list = (
        "/etc/passwd", "/etc/group",
        "/etc/shadow", "/etc/gshadow",
    )

    # directories for DRI (direct rendering)
    dri_list = (
        "/usr/lib64/dri", "/lib64/dri",
        "/usr/lib/dri", "/lib/dri",
    )

    # container execution mode if not set via setup
    # Change it to P2 if execution problems occur
    default_execution_mode = "P1"

    # PRoot override seccomp
    # proot_noseccomp = True
    proot_noseccomp = None

    # PRoot kill-on-exit
    proot_killonexit = True

    # fakechroot engine get ld_library_paths from ld.so.cache
    ld_so_cache = "/etc/ld.so.cache"

    # fakechroot engine override fakechroot.so selection
    # fakechroot_so = "libfakechroot-CentOS-7-x86_64.so"
    fakechroot_so = None

    # fakechroot sharable library directories
    lib_dirs_list_essential = (
        "/lib/x86_64-linux-gnu", "/usr/lib/x86_64-linux-gnu",
        "/lib64", "/usr/lib64", "/lib", "/usr/lib",
    )
    lib_dirs_list_append = (".", )

    # fakechroot access files, used to circunvent openmpi init issues
    access_files = (
        "/sys/class/infiniband", "/dev/open-mx", "/dev/myri0", "/dev/myri1",
        "/dev/myri2", "/dev/myri3", "/dev/myri4", "/dev/myri5", "/dev/myri6",
        "/dev/myri7", "/dev/myri8", "/dev/myri9", "/dev/ipath", "/dev/kgni0",
        "/dev/mic/scif", "/dev/scif",
    )

    # runc parameters
    runc_nomqueue = None

    # singularity options -u --nv -w
    singularity_options = ["-w", ]

    # Pass host env variables
    valid_host_env = ("TERM", "PATH", )
    invalid_host_env = ("VTE_VERSION", )

    # CPU affinity executables to use with: run --cpuset-cpus="1,2,3-4"
    cpu_affinity_exec_tools = (["numactl", "-C", "%s", "--", ],
                               ["taskset", "-c", "%s", ])

    # Containers execution defaults
    location = ""         # run container in this location

    # Curl settings
    http_proxy = ""    # ex. socks5://user:pass@127.0.0.1:1080
    timeout = 12       # default timeout (secs)
    download_timeout = 30 * 60    # file download timeout (secs)
    ctimeout = 6       # default TCP connect timeout (secs)
    http_agent = ""
    http_insecure = False
    use_curl_executable = "" # force use of executable

    # docker hub v1
    dockerio_index_url = "https://index.docker.io"
    # docker hub v2
    dockerio_registry_url = "https://registry-1.docker.io"
    # private repository v2
    # dockerio_registry_url = "http://localhost:5000"

    # registries table
    docker_registries = {"docker.io": ["https://registry-1.docker.io",
                                       "https://index.docker.io"],
                        }

    # nvidia files
    nvi_etc_list = ['vulkan/icd.d/nvidia_icd.json',
                    'OpenCL/vendors/nvidia.icd'
                   ]

    nvi_bin_list = ['nvidia-bug-report.sh', 'nvidia-cuda-mps-control',
                    'nvidia-cuda-mps-server', 'nvidia-debugdump',
                    'nvidia-installer', 'nvidia-persistenced',
                    'nvidia-settings', 'nvidia-smi',
                    'nvidia-uninstall', 'nvidia-xconfig'
                   ]

    nvi_lib_list = ['libOpenCL.', 'libcuda.', 'libnvcuvid.',
                    'libnvidia-cfg.', 'libnvidia-compiler.',
                    'libnvidia-encode.', 'libnvidia-fatbinaryloader.',
                    'libnvidia-fbc.', 'libnvidia-ifr.', 'libnvidia-ml.',
                    'libnvidia-opencl.', 'libnvidia-ptxjitcompiler.',
                    'libnvidia-tls.', 'tls/libnvidia-tls.'
                   ]

    nvi_dev_list = ['/dev/nvidia', ]

    # -------------------------------------------------------------

    def _verify_config(self):
        """Config verification"""
        if not Config.topdir:
            Msg().err("Error: UDOCKER directory not found")
            sys.exit(1)

    def _override_config(self):
        """Override config with environment"""
        Config.topdir = os.getenv("UDOCKER_DIR", Config.topdir)
        Config.bindir = os.getenv("UDOCKER_BIN", Config.bindir)
        Config.libdir = os.getenv("UDOCKER_LIB", Config.libdir)
        Config.reposdir = os.getenv("UDOCKER_REPOS", Config.reposdir)
        Config.layersdir = os.getenv("UDOCKER_LAYERS", Config.layersdir)
        Config.containersdir = os.getenv("UDOCKER_CONTAINERS",
                                         Config.containersdir)
        Config.dockerio_index_url = os.getenv("UDOCKER_INDEX",
                                              Config.dockerio_index_url)
        Config.dockerio_registry_url = os.getenv("UDOCKER_REGISTRY",
                                                 Config.dockerio_registry_url)
        Config.tarball = os.getenv("UDOCKER_TARBALL", Config.tarball)
        Config.fakechroot_so = os.getenv("UDOCKER_FAKECHROOT_SO",
                                         Config.fakechroot_so)
        Config.tmpdir = os.getenv("UDOCKER_TMP", Config.tmpdir)
        Config.keystore = os.getenv("UDOCKER_KEYSTORE", Config.keystore)
        Config.use_curl_executable = os.getenv("UDOCKER_USE_CURL_EXECUTABLE",
                                               Config.use_curl_executable)

    def _read_config(self, config_file):
        """Interpret config file content"""
        cfile = FileUtil(config_file)
        if cfile.size() == -1:
            return False
        data = cfile.getdata()
        for line in data.split("\n"):
            if not line.strip() or "=" not in line or line.startswith("#"):
                continue
            (key, val) = line.strip().split("=", 1)
            key = key.strip()
            Msg().err(config_file, ":", key, "=", val, l=Msg.DBG)
            try:
                dummy = ast.literal_eval(val.strip())
                exec('Config.%s=%s' % (key, val))
            except(NameError, AttributeError, TypeError, IndexError,
                   SyntaxError, ValueError):
                raise ValueError("config file: %s at: %s" %
                                 (config_file, line.strip()))
            if key == "verbose_level":
                Msg().setlevel(Config.verbose_level)
        return True

    def user_init(self, config_file):
        """
        Try to load default values from config file
        Defaults should be in the form x = y
        """
        try:
            if os.getenv("UDOCKER_NOSYSCONF") is None:
                self._read_config("/etc/" + Config.config)
            if self._read_config(config_file):
                return
            self._read_config(Config.topdir + "/" + Config.config)
            if self.topdir != self.homedir:
                self._read_config(Config.homedir + "/" + Config.config)
        except ValueError as error:
            Msg().err("Error:", error)
            sys.exit(1)
        self._override_config()
        self._verify_config()

    def username(self):
        """Get username"""
        try:
            return pwd.getpwuid(Config.uid).pw_name
        except KeyError:
            return ""

    def arch(self):
        """Get the host system architecture"""
        arch = ""
        try:
            machine = platform.machine()
            bits = platform.architecture()[0]
            if machine == "x86_64":
                if bits == "32bit":
                    arch = "i386"
                else:
                    arch = "amd64"
            elif machine in ("i386", "i486", "i586", "i686"):
                arch = "i386"
            elif machine.startswith("arm"):
                if bits == "32bit":
                    arch = "arm"
                else:
                    arch = "arm64"
        except (NameError, AttributeError):
            pass
        return arch

    def osversion(self):
        """Get operating system"""
        try:
            return platform.system().lower()
        except (NameError, AttributeError):
            return ""

    def osdistribution(self):
        """Get operating system distribution"""
        (distribution, version, dummy) = platform.linux_distribution()
        return (distribution.split(" ")[0], version.split(".")[0])

    def oskernel(self):
        """Get operating system"""
        try:
            return platform.release()
        except (NameError, AttributeError):
            return "3.2.1"

    def oskernel_isgreater(self, ref_version):
        """Compare kernel version is greater or equal than ref_version"""
        os_release = self.oskernel().split("-")[0]
        os_version = [int(x) for x in os_release.split(".")]
        for idx in (0, 1, 2):
            if os_version[idx] > ref_version[idx]:
                return True
            elif os_version[idx] < ref_version[idx]:
                return False
        return True


class GuestInfo(object):
    """Get os information from a directory tree"""

    _binarylist = ["/lib64/ld-linux-x86-64.so",
                   "/lib64/ld-linux-x86-64.so.2",
                   "/lib64/ld-linux-x86-64.so.3",
                   "/lib/ld-linux.so.2",
                   "/lib/ld-linux.so",
                   "/bin/sh", "/bin/bash", "/bin/zsh", "/bin/csh", "/bin/tcsh",
                   "/bin/ls", "/bin/busybox",
                   "/system/bin/sh", "/system/bin/ls",
                  ]

    def __init__(self, root_dir):
        self._root_dir = root_dir

    def get_filetype(self, filename):
        """Get the file architecture"""
        if not filename.startswith(self._root_dir):
            filename = self._root_dir + "/" + filename
        if os.path.islink(filename):
            f_path = os.readlink(filename)
            if not f_path.startswith("/"):
                f_path = os.path.dirname(filename) + "/" + f_path
            return self.get_filetype(f_path)
        if os.path.isfile(filename):
            cmd = "file %s" % (filename)
            return Uprocess().get_output(cmd)
        return ""

    def arch(self):
        """Get guest system architecture"""
        for filename in GuestInfo._binarylist:
            f_path = self._root_dir + filename
            filetype = self.get_filetype(f_path)
            if not filetype:
                continue
            if "x86-64," in filetype:
                return "amd64"
            if "80386," in filetype:
                return "i386"
            if "ARM," in filetype:
                if "64-bit" in filetype:
                    return "arm64"
                else:
                    return "arm"
        return ""

    def osdistribution(self):
        """Get guest operating system distribution"""
        for f_path in FileUtil(self._root_dir + "/etc/.+-release").match():
            if os.path.exists(f_path):
                osinfo = FileUtil(f_path).getdata()
                match = re.match(r"([^=]+) release (\d+)", osinfo)
                if match and match.group(1):
                    return (match.group(1).split(" ")[0],
                            match.group(2).split(".")[0])
        f_path = self._root_dir + "/etc/lsb-release"
        if os.path.exists(f_path):
            distribution = ""
            version = ""
            osinfo = FileUtil(f_path).getdata()
            match = re.search(r"DISTRIB_ID=(.+)(\n|$)",
                              osinfo, re.MULTILINE)
            if match:
                distribution = match.group(1).split(" ")[0]
            match = re.search(r"DISTRIB_RELEASE=(.+)(\n|$)",
                              osinfo, re.MULTILINE)
            if match:
                version = match.group(1).split(".")[0]
            if distribution and version:
                return (distribution, version)
        f_path = self._root_dir + "/etc/os-release"
        if os.path.exists(f_path):
            distribution = ""
            version = ""
            osinfo = FileUtil(f_path).getdata()
            match = re.search(r"NAME=\"?(.+)\"?(\n|$)",
                              osinfo, re.MULTILINE)
            if match:
                distribution = match.group(1).split(" ")[0]
            match = re.search(r"VERSION_ID=\"?(.+)\"?(\n|$)",
                              osinfo, re.MULTILINE)
            if match:
                version = match.group(1).split(".")[0]
            if distribution and version:
                return (distribution, version)
        return ("", "")

    def osversion(self):
        """Get guest operating system"""
        if self.osdistribution()[0]:
            return "linux"
        return ""


class KeyStore(object):
    """Basic storage for authentication tokens to be used
    with dockerhub and private repositories
    """

    def __init__(self, keystore_file):
        """Initialize keystone"""
        self.keystore_file = keystore_file
        self.credential = dict()

    def _verify_keystore(self):
        """Verify the keystore file and directory"""
        keystore_uid = FileUtil(self.keystore_file).uid()
        if keystore_uid != -1 and keystore_uid != Config.uid:
            raise IOError("not owner of keystore: %s" %
                          (self.keystore_file))
        keystore_dir = os.path.dirname(self.keystore_file)
        if FileUtil(keystore_dir).uid() != Config.uid:
            raise IOError("keystore dir not found or not owner: %s" %
                          (keystore_dir))
        if (keystore_uid != -1 and
                (os.stat(self.keystore_file).st_mode & 0o077)):
            raise IOError("keystore is accessible to group or others: %s" %
                          (self.keystore_file))

    def _read_all(self):
        """Read all credentials from file"""
        try:
            with open(self.keystore_file, "r") as filep:
                return json.load(filep)
        except (IOError, OSError, ValueError):
            return dict()

    def _shred(self):
        """Shred file content"""
        self._verify_keystore()
        try:
            size = os.stat(self.keystore_file).st_size
            with open(self.keystore_file, "rb+") as filep:
                filep.write(" " * size)
        except (IOError, OSError):
            return False
        return True

    def _write_all(self, auths):
        """Write all credentials to file"""
        self._verify_keystore()
        oldmask = None
        try:
            oldmask = os.umask(0o77)
            with open(self.keystore_file, "w") as filep:
                json.dump(auths, filep)
            os.umask(oldmask)
        except (IOError, OSError):
            if oldmask is not None:
                os.umask(oldmask)
            return False
        return True

    def get(self, url):
        """Get credential from keystore for given url"""
        auths = self._read_all()
        try:
            self.credential = auths[url]
            return self.credential["auth"]
        except KeyError:
            pass
        return ""

    def put(self, url, credential, email):
        """Put credential in keystore for given url"""
        if not credential:
            return False
        auths = self._read_all()
        auths[url] = {"auth": credential, "email": email, }
        self._shred()
        return self._write_all(auths)

    def delete(self, url):
        """Delete credential from keystore for given url"""
        self._verify_keystore()
        auths = self._read_all()
        try:
            del auths[url]
        except KeyError:
            return False
        self._shred()
        return self._write_all(auths)

    def erase(self):
        """Delete all credentials from keystore"""
        self._verify_keystore()
        try:
            self._shred()
            os.unlink(self.keystore_file)
        except (IOError, OSError):
            return False
        return True


class Msg(object):
    """Write messages to stdout and stderr. Allows to filter the
    messages to be displayed through a verbose level, also allows
    to control if child process that produce output through a
    file descriptor should be redirected to /dev/null
    """

    NIL = -1
    ERR = 0
    MSG = 1
    WAR = 2
    INF = 3
    VER = 4
    DBG = 5
    DEF = INF
    level = DEF
    previous = DEF
    nullfp = None
    chlderr = sys.stderr
    chldout = sys.stdout
    chldnul = sys.stderr

    def __init__(self, new_level=None):
        """
        Initialize Msg level and /dev/null file pointers to be
        used in subprocess calls to obfuscate output and errors
        """
        if new_level is not None:
            Msg.level = new_level
        try:
            if Msg.nullfp is None:
                Msg.nullfp = open("/dev/null", "w")
        except (IOError, OSError):
            Msg.chlderr = sys.stderr
            Msg.chldout = sys.stdout
            Msg.chldnul = sys.stderr
        else:
            Msg.chlderr = Msg.nullfp
            Msg.chldout = Msg.nullfp
            Msg.chldnul = Msg.nullfp

    def setlevel(self, new_level=None):
        """Define debug level"""
        if new_level is None:
            new_level = Msg.previous
        else:
            Msg.previous = Msg.level
        Msg.level = new_level
        if Msg.level >= Msg.DBG:
            Msg.chlderr = sys.stderr
            Msg.chldout = sys.stdout
        else:
            Msg.chlderr = Msg.nullfp
            Msg.chldout = Msg.nullfp
        return Msg.previous

    def out(self, *args, **kwargs):
        """Write text to stdout respecting verbose level"""
        level = Msg.MSG
        if "l" in kwargs:
            level = kwargs["l"]
        if level <= Msg.level:
            sys.stdout.write(" ".join([str(x) for x in args]) + '\n')

    def err(self, *args, **kwargs):
        """Write text to stderr respecting verbose level"""
        level = Msg.ERR
        if "l" in kwargs:
            level = kwargs["l"]
        if level <= Msg.level:
            sys.stderr.write(" ".join([str(x) for x in args]) + '\n')


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


class ChkSUM(object):
    """Checksumming for files"""

    def __init__(self):
        try:
            dummy = hashlib.sha256()
            self._sha256_call = self._hashlib_sha256
        except NameError:
            self._sha256_call = self._openssl_sha256

    def _hashlib_sha256(self, filename):
        """sha256 calculation using hashlib"""
        hash_sha256 = hashlib.sha256()
        try:
            with open(filename, "rb") as filep:
                for chunk in iter(lambda: filep.read(4096), b""):
                    hash_sha256.update(chunk)
            return hash_sha256.hexdigest()
        except (IOError, OSError):
            return ""

    def _openssl_sha256(self, filename):
        """sha256 calculation using openssl"""
        cmd = "openssl dgst -hex -r -sha256 %s" % (filename)
        output = Uprocess().get_output(cmd)
        if output is None:
            return ""
        match = re.match("^(\\S+) ", output)
        if match:
            return match.group(1)
        return ""

    def sha256(self, filename):
        """
        Call the actual sha256 implementation selected in __init__
        """
        return self._sha256_call(filename)


class FileUtil(object):
    """Some utilities to manipulate files"""

    tmptrash = dict()
    safe_prefixes = []
    orig_umask = None

    def __init__(self, filename=None):
        self._tmpdir = Config.tmpdir
        if filename == "-":
            self.filename = "-"
            self.basename = "-"
            return
        try:
            self.filename = os.path.abspath(filename)
            self.basename = os.path.basename(self.filename)
        except (AttributeError, TypeError):
            self.filename = filename
            self.basename = filename
        self._register_prefix(self._tmpdir)

    def _register_prefix(self, prefix):
        """Register directory prefixes where remove() is allowed"""
        if prefix not in FileUtil.safe_prefixes:
            filename = prefix
            if os.path.isdir(filename) and not filename.endswith("/"):
                FileUtil.safe_prefixes.append(filename + "/")
                FileUtil.safe_prefixes.append(os.path.realpath(filename) + "/")
            else:
                FileUtil.safe_prefixes.append(filename)
                FileUtil.safe_prefixes.append(os.path.realpath(filename))

    def register_prefix(self):
        """Register self.filename as prefix where remove() is allowed"""
        self._register_prefix(self.filename)

    def umask(self, new_umask=None):
        """Set umask"""
        if new_umask is not None:
            try:
                old_umask = os.umask(new_umask)
            except (TypeError, ValueError):
                return False
            if FileUtil.orig_umask is None:
                FileUtil.orig_umask = old_umask
        else:
            try:
                os.umask(FileUtil.orig_umask)
            except (TypeError, ValueError):
                return False
        return True

    def mktmp(self):
        """Generate a temporary filename"""
        while True:
            tmp_file = self._tmpdir + "/" + \
                Unique().filename(self.basename)
            if not os.path.exists(tmp_file):
                FileUtil.tmptrash[tmp_file] = True
                self.filename = tmp_file
                return tmp_file

    def mkdir(self):
        """Create directory"""
        try:
            os.makedirs(self.filename)
        except (OSError, IOError, AttributeError):
            return False
        return True

    def mktmpdir(self):
        """Create temporary directory"""
        dirname = self.mktmp()
        if FileUtil(dirname).mkdir():
            return dirname
        return None

    def uid(self):
        """Get the file owner user id"""
        try:
            return os.stat(self.filename).st_uid
        except (IOError, OSError):
            return -1

    def _is_safe_prefix(self, filename):
        """Check if file prefix falls under valid prefixes"""
        for safe_prefix in FileUtil.safe_prefixes:
            if filename.startswith(safe_prefix):
                return True
        return False

    def remove(self, force=False):
        """Delete files or directories"""
        if not os.path.exists(self.filename):
            pass
        elif self.filename.count("/") < 2:
            Msg().err("Error: delete pathname too short: ", self.filename)
            return False
        elif self.uid() != Config.uid:
            Msg().err("Error: delete not owner: ", self.filename)
            return False
        elif (not force) and (not self._is_safe_prefix(self.filename)):
            Msg().err("Error: delete outside of directory tree: ",
                      self.filename)
            return False
        elif os.path.isfile(self.filename) or os.path.islink(self.filename):
            try:
                os.remove(self.filename)
            except (IOError, OSError):
                Msg().err("Error: deleting file: ", self.filename)
                return False
        elif os.path.isdir(self.filename):
            cmd = "/bin/rm -Rf %s || /bin/chmod -R u+w %s && /bin/rm -Rf %s" % \
                  (self.filename, self.filename, self.filename)
            if subprocess.call(cmd, stderr=Msg.chlderr, shell=True,
                               close_fds=True, env=None):
                Msg().err("Error: deleting directory: ", self.filename)
                return False
        if self.filename in dict(FileUtil.tmptrash):
            del FileUtil.tmptrash[self.filename]
        return True

    def verify_tar(self):
        """Verify a tar file"""
        if not os.path.isfile(self.filename):
            return False
        else:
            cmd = "tar t"
            if Msg.level >= Msg.VER:
                cmd += "v"
            cmd += "f " + self.filename
            if subprocess.call(cmd, shell=True, stderr=Msg.chlderr,
                               stdout=Msg.chldnul, close_fds=True):
                return False
            return True

    def cleanup(self):
        """Delete all temporary files"""
        tmptrash_copy = dict(FileUtil.tmptrash)
        for filename in tmptrash_copy:
            FileUtil(filename).remove()

    def isdir(self):
        """Is filename a directory"""
        try:
            if os.path.isdir(self.filename):
                return True
        except (IOError, OSError, TypeError):
            pass
        return False

    def size(self):
        """File size in bytes"""
        try:
            fstat = os.stat(self.filename)
            return fstat.st_size
        except (IOError, OSError, TypeError):
            return -1

    def getdata(self, mode="rb"):
        """Read file content to a buffer"""
        try:
            filep = open(self.filename, mode)
        except (IOError, OSError, TypeError):
            return ""
        else:
            buf = filep.read()
            filep.close()
            return buf

    def get1stline(self, mode="rb"):
        """Read file 1st line to a buffer"""
        try:
            filep = open(self.filename, mode)
        except (IOError, OSError, TypeError):
            return ""
        else:
            buf = filep.readline().strip()
            filep.close()
            return buf

    def putdata(self, buf, mode="wb"):
        """Write buffer to file"""
        try:
            filep = open(self.filename, mode)
        except (IOError, OSError, TypeError):
            return ""
        else:
            filep.write(buf)
            filep.close()
            return buf

    def _find_exec(self, cmd_to_use):
        """This method is called by find_exec() invokes a command like
        /bin/which or type to obtain the full pathname of an executable
        """
        exec_pathname = Uprocess().get_output(cmd_to_use)
        if exec_pathname is None:
            return ""
        if "not found" in exec_pathname:
            return ""
        if exec_pathname and exec_pathname.startswith("/"):
            return exec_pathname.strip()
        return ""

    def find_exec(self):
        """Find an executable pathname by using which or type -p"""
        cmd = self._find_exec("which " + self.basename)
        if cmd:
            return cmd
        cmd = self._find_exec("type -p " + self.basename)
        if cmd:
            return cmd
        return ""

    def find_inpath(self, path, rootdir=""):
        """Find file in a path set such as PATH=/usr/bin:/bin"""
        if isinstance(path, str):
            if "=" in path:
                path = "".join(path.split("=", 1)[1:])
            path = path.split(":")
        if isinstance(path, (list, tuple)):
            for directory in path:
                full_path = rootdir + directory + "/" + self.basename
                if os.path.lexists(full_path):
                    return directory + "/" + self.basename
            return ""
        return ""

    def list_inpath(self, path, rootdir=""):
        """List files with path PATH=/usr/bin:/bin prepended"""
        full_path_list = []
        if isinstance(path, str):
            if "=" in path:
                path = "".join(path.split("=", 1)[1:])
            path = path.split(":")
        if isinstance(path, (list, tuple)):
            for directory in path:
                full_path_list.append(rootdir + directory + "/" + self.basename)
        return full_path_list

    def rename(self, dest_filename):
        """Rename/move file"""
        try:
            os.rename(self.filename, dest_filename)
        except (IOError, OSError):
            return False
        return True

    def _stream2file(self, dest_filename, mode="w"):
        """Copy from stdin to another file. We avoid shutil to have
        the fewest possible dependencies on other Python modules.
        """
        try:
            fpdst = open(dest_filename, mode + "b")
        except (IOError, OSError):
            return False
        while True:
            copy_buffer = sys.stdin.read(1024 * 1024)
            if not copy_buffer:
                break
            fpdst.write(copy_buffer)
        fpdst.close()
        return True

    def _file2stream(self):
        """Copy self.filename to stdout. We avoid shutil to have
        the fewest possible dependencies on other Python modules.
        """
        try:
            fpsrc = open(self.filename, "rb")
        except (IOError, OSError):
            return False
        while True:
            copy_buffer = fpsrc.read(1024 * 1024)
            if not copy_buffer:
                break
            sys.stdout.write(copy_buffer)
        fpsrc.close()
        return True

    def _file2file(self, dest_filename, mode="w"):
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

    def copyto(self, dest_filename, mode="w"):
        """Copy self.filename to another file. We avoid shutil to have
        the fewest possible dependencies on other Python modules.
        """
        if self.filename == "-" and dest_filename != "-":
            return self._stream2file(dest_filename, mode)
        elif self.filename != "-" and dest_filename == "-":
            return self._file2stream()
        elif self.filename != "-" and dest_filename != "-":
            return self._file2file(dest_filename, mode)
        else:
            return False

    def find_file_in_dir(self, image_list):
        """Find and return first file of list in dir"""
        path_prefix = self.filename
        for image in image_list:
            image_path = path_prefix + "/" + image
            if os.path.exists(image_path):
                return image_path
        return ""

    def _link_change_apply(self, new_l_path, f_path, force):
        """Actually apply the link convertion"""
        p_path = os.path.realpath(os.path.dirname(f_path))
        if force and not os.access(p_path, os.W_OK):
            os.chmod(p_path, stat.S_IMODE(os.stat(p_path).st_mode) | stat.S_IWUSR)
            os.remove(f_path)
            os.symlink(new_l_path, f_path)
            os.chmod(p_path, stat.S_IMODE(os.stat(p_path).st_mode) & ~stat.S_IWUSR)
        else:
            os.remove(f_path)
            os.symlink(new_l_path, f_path)

    def _link_set(self, f_path, orig_path, root_path, force):
        """Convertion to container specific symbolic link"""
        l_path = os.readlink(f_path)
        if not l_path.startswith("/"):
            return False
        new_l_path = ""
        regexp_id = "[a-z0-9]+-[a-z0-9]+-[a-z0-9]+-[a-z0-9]+-[a-z0-9]+"
        recomp = re.compile("(/.*/containers/" + regexp_id + "/ROOT)(/.*)")
        if orig_path == "":
            match = recomp.match(l_path)
            if match:
                orig_path = match.group(1)
        if orig_path and l_path.startswith(orig_path) and orig_path != root_path:
            new_l_path = l_path.replace(orig_path, root_path, 1)
        elif not l_path.startswith(root_path):
            new_l_path = root_path + l_path
        if new_l_path:
            self._link_change_apply(new_l_path, f_path, force)
            return True
        return False

    def _link_restore(self, f_path, orig_path, root_path, force):
        """Convertion for host specific symbolic link"""
        l_path = os.readlink(f_path)
        new_l_path = ""
        if not l_path.startswith("/"):
            return False
        regexp_id = "[a-z0-9]+-[a-z0-9]+-[a-z0-9]+-[a-z0-9]+-[a-z0-9]+"
        recomp = re.compile("(/.*/containers/" + regexp_id + "/ROOT)(/.*)")
        if orig_path and l_path.startswith(orig_path):
            new_l_path = l_path.replace(orig_path, "", 1)
        elif l_path.startswith(root_path):
            new_l_path = l_path.replace(root_path, "", 1)
        elif orig_path == "":
            match = recomp.match(l_path)
            if match:
                new_l_path = l_path.replace(match.group(1), "", 1)
        if new_l_path:
            self._link_change_apply(new_l_path, f_path, force)
            return True
        return False

    def links_conv(self, force=False, to_container=True, orig_path=""):
        """ Convert absolute symbolic links to relative symbolic links
        """
        root_path = os.path.realpath(self.filename)
        links = []
        if not self._is_safe_prefix(root_path):
            Msg().err("Error: links convertion outside of directory tree: ",
                      root_path)
            return None
        for dir_path, dirs, files in os.walk(root_path):
            for f_name in files + dirs:
                try:
                    f_path = dir_path + "/" + f_name
                    if not os.path.islink(f_path):
                        continue
                    if os.lstat(f_path).st_uid != Config.uid:
                        continue
                    if to_container:
                        if self._link_set(f_path, orig_path, root_path, force):
                            links.append(f_path)
                    else:
                        if self._link_restore(f_path, orig_path, root_path, force):
                            links.append(f_path)
                except OSError:
                    continue
        return links

    def match(self):
        """Find matching file with wildcard matching expression"""
        directory = os.path.dirname(self.filename)
        matching_expression = os.path.basename(self.filename)
        matching_files = []
        if not os.path.isdir(directory):
            return []
        for f_name in os.listdir(directory):
            if re.match(matching_expression, f_name):
                matching_files.append(directory + "/" + f_name)
        return matching_files


class UdockerTools(object):
    """Download and setup of the udocker supporting tools
    Includes: proot and alternative python modules, these
    are downloaded to facilitate the installation by the
    end-user.
    """

    def __init__(self, localrepo):
        self.localrepo = localrepo        # LocalRepository object
        self._autoinstall = Config.autoinstall  # True / False
        self._tarball = Config.tarball  # URL or file
        self._installinfo = Config.installinfo  # URL or file
        self._tarball_release = Config.tarball_release
        self._install_json = dict()
        self.curl = GetURL()

    def _version_isequal(self, filename):
        """Is version inside file equal to the taball release requirement"""
        version = FileUtil(filename).getdata().strip()
        return version and version == self._tarball_release

    def is_available(self):
        """Are the tools already installed"""
        return self._version_isequal(self.localrepo.libdir + "/VERSION")

    def _download(self, url):
        """Download a file """
        download_file = FileUtil("udockertools").mktmp()
        if Msg.level <= Msg.DEF:
            Msg().setlevel(Msg.NIL)
        (hdr, dummy) = self.curl.get(url, ofile=download_file)
        if Msg.level == Msg.NIL:
            Msg().setlevel()
        try:
            if "200" in hdr.data["X-ND-HTTPSTATUS"]:
                return download_file
        except (KeyError, TypeError, AttributeError):
            pass
        FileUtil(download_file).remove()
        return ""

    def _get_file(self, locations):
        """Get file from list of possible locations file or internet"""
        for url in locations:
            Msg().err("Info: getting file:", url, l=Msg.VER)
            filename = ""
            if "://" in url:
                filename = self._download(url)
            elif os.path.exists(url):
                filename = os.path.realpath(url)
            if filename and os.path.isfile(filename):
                return (filename, url)
        return ("", "")

    def _verify_version(self, tarball_file):
        """verify the tarball version"""
        if not (tarball_file and os.path.isfile(tarball_file)):
            return False
        tmpdir = FileUtil("VERSION").mktmpdir()
        if not tmpdir:
            return False
        cmd = "cd " + tmpdir + " ; "
        cmd += "tar --strip-components=2 -x"
        if Msg.level >= Msg.VER:
            cmd += "v"
        cmd += "zf " + tarball_file + " udocker_dir/lib/VERSION ; "
        status = subprocess.call(cmd, shell=True, close_fds=True)
        if status:
            return False
        status = self._version_isequal(tmpdir + "/VERSION")
        FileUtil(tmpdir).remove()
        return status

    def purge(self):
        """Remove existing files in bin and lib"""
        for f_name in os.listdir(self.localrepo.bindir):
            FileUtil(self.localrepo.bindir + "/" + f_name).register_prefix()
            FileUtil(self.localrepo.bindir + "/" + f_name).remove()
        for f_name in os.listdir(self.localrepo.libdir):
            FileUtil(self.localrepo.libdir + "/" + f_name).register_prefix()
            FileUtil(self.localrepo.libdir + "/" + f_name).remove()

    def _install(self, tarball_file):
        """Install the tarball"""
        if not (tarball_file and os.path.isfile(tarball_file)):
            return False
        cmd = "cd " + self.localrepo.bindir + " ; "
        cmd += "tar --strip-components=2 -x"
        if Msg.level >= Msg.VER:
            cmd += "v"
        cmd += "zf " + tarball_file + " udocker_dir/bin ; "
        cmd += "/bin/chmod u+rx *"
        status = subprocess.call(cmd, shell=True, close_fds=True)
        if status:
            return False
        cmd = "cd " + self.localrepo.libdir + " ; "
        cmd += "tar --strip-components=2 -x"
        if Msg.level >= Msg.VER:
            cmd += "v"
        cmd += "zf " + tarball_file + " udocker_dir/lib ; "
        cmd += "/bin/chmod u+rx *"
        status = subprocess.call(cmd, shell=True, close_fds=True)
        if status:
            return False
        return True

    def _instructions(self):
        """
        Udocker installation instructions are available at:

          https://github.com/indigo-dc/udocker/tree/master/doc
          https://github.com/indigo-dc/udocker/tree/devel/doc

        Udocker requires additional tools to run. These are available
        in the udocker tarball. The tarballs are available at several
        locations. By default udocker will install from the locations
        defined in Config.tarball.

        To install from files or other URLs use these instructions:

        1) set UDOCKER_TARBALL to a remote URL or local filename:

          $ export UDOCKER_TARBALL=http://host/path
          or
          $ export UDOCKER_TARBALL=/tmp/filename

        2) run udocker with the install command or optionally using
           the option --force to overwrite the local installation:

          ./udocker install
          or
          ./udocker install --force

        3) once installed the binaries and containers will be placed
           by default under $HOME/.udocker

        """
        Msg().out(self._instructions.__doc__, l=Msg.ERR)
        Msg().out("        udocker version:", __version__,
                  "requires tarball release:", self._tarball_release, l=Msg.ERR)

    def _get_mirrors(self, mirrors):
        """Get shuffled list of tarball mirrors"""
        if isinstance(mirrors, str):
            mirrors = mirrors.split(" ")
        try:
            random.shuffle(mirrors)
        except NameError:
            pass
        return mirrors

    def get_installinfo(self):
        """Get json containing installation info"""
        (infofile, dummy) = self._get_file(self._get_mirrors(self._installinfo))
        try:
            with open(infofile, "r") as filep:
                self._install_json = json.load(filep)
            for msg in self._install_json["messages"]:
                Msg().err("Info:", msg)
        except (KeyError, AttributeError, ValueError,
                OSError, IOError):
            Msg().err("Info: no messages available", l=Msg.VER)
        return self._install_json

    def install(self, force=False):
        """Get the udocker tarball and install the binaries"""
        if self.is_available() and not force:
            return True
        elif not self._autoinstall and not force:
            Msg().err("Warning: no engine available and autoinstall disabled",
                      l=Msg.WAR)
            return None
        elif not self._tarball:
            Msg().err("Error: UDOCKER_TARBALL not defined")
        else:
            Msg().err("Info: installing", self._tarball_release, l=Msg.INF)
            (tarfile, url) = self._get_file(self._get_mirrors(self._tarball))
            if tarfile:
                Msg().err("Info: installing from:", url, l=Msg.VER)
                status = False
                if not self._verify_version(tarfile):
                    Msg().err("Error: wrong tarball version:", url)
                else:
                    status = self._install(tarfile)
                if "://" in url:
                    FileUtil(tarfile).remove()
                    if status:
                        self.get_installinfo()
                if status:
                    return True
            Msg().err("Error: installing tarball:", self._tarball)
        self._instructions()
        return False


class ElfPatcher(object):
    """Patch container executables"""

    BIN = 1
    LIB = 2
    LOADER = 4
    ABORT_ON_ERROR = 8
    ONE_SUCCESS = 16
    ONE_OUTPUT = 32

    def __init__(self, localrepo, container_id):
        self._localrepo = localrepo
        self._container_dir = \
            os.path.realpath(self._localrepo.cd_container(container_id))
        if not self._container_dir:
            raise ValueError("invalid container id")
        self._container_root = self._container_dir + "/ROOT"
        self._container_ld_so_path = self._container_dir + "/ld.so.path"
        self._container_ld_so_orig = self._container_dir + "/ld.so.orig"
        self._container_ld_libdirs = self._container_dir + "/ld.lib.dirs"
        self._container_patch_time = self._container_dir + "/patch.time"
        self._container_patch_path = self._container_dir + "/patch.path"
        self._shlib = re.compile(r"^lib\S+\.so(\.\d+)*$")
        self._uid = Config.uid

    def select_patchelf(self):
        """Set patchelf executable"""
        conf = Config()
        arch = conf.arch()
        if arch == "amd64":
            image_list = ["patchelf-x86_64", "patchelf"]
        elif arch == "i386":
            image_list = ["patchelf-x86", "patchelf"]
        elif arch == "arm64":
            image_list = ["patchelf-arm64", "patchelf"]
        elif arch == "arm":
            image_list = ["patchelf-arm", "patchelf"]
        f_util = FileUtil(self._localrepo.bindir)
        patchelf_exec = f_util.find_file_in_dir(image_list)
        if not patchelf_exec:
            Msg().err("Error: patchelf executable not found")
            sys.exit(1)
        return patchelf_exec

    def _walk_fs(self, cmd, root_path, action=BIN):
        """Execute a shell command over each executable file in a given
        dir_path, action can be ABORT_ON_ERROR, return upon first success
        ONE_SUCCESS, or return upon the first non empty output. #f is the
        placeholder for the filename.
        """
        status = False
        for dir_path, dummy, files in os.walk(root_path):
            for f_name in files:
                try:
                    f_path = dir_path + "/" + f_name
                    if os.path.islink(f_path):
                        continue
                    if os.stat(f_path).st_uid != self._uid:
                        if action & self.ABORT_ON_ERROR:
                            return None
                        else:
                            continue
                    if ((action & self.BIN and os.access(f_path, os.X_OK)) or
                            (action & self.LIB and self._shlib.match(f_name))):
                        out = Uprocess().get_output(cmd.replace("#f", f_path))
                        if out:
                            status = out
                    if action & self.ABORT_ON_ERROR and status is None:
                        return None
                    elif action & self.ONE_SUCCESS and status is not None:
                        return status
                    elif action & self.ONE_OUTPUT and status:
                        return status
                except OSError:
                    pass
        return status

    def guess_elf_loader(self):
        """Search for executables and try to read the ld.so pathname"""
        patchelf_exec = self.select_patchelf()
        cmd = "%s -q --print-interpreter #f" % (patchelf_exec)
        for d_name in ("/bin", "/usr/bin", "/lib64"):
            elf_loader = self._walk_fs(cmd, self._container_root + d_name,
                                       self.ONE_OUTPUT | self.BIN)
            if elf_loader and ".so" in elf_loader:
                return elf_loader
        return ""

    def get_original_loader(self):
        """Get the pathname of the original ld.so"""
        if os.path.exists(self._container_ld_so_path):
            return FileUtil(self._container_ld_so_path).getdata().strip()
        elf_loader = self.guess_elf_loader()
        if elf_loader:
            FileUtil(self._container_ld_so_path).putdata(elf_loader)
        return elf_loader

    def get_container_loader(self):
        """Get an absolute pathname to the container ld.so"""
        elf_loader = self.get_original_loader()
        if not elf_loader:
            return ""
        elf_loader = self._container_root + "/" + elf_loader
        return elf_loader if os.path.exists(elf_loader) else ""

    def get_patch_last_path(self):
        """get last host pathname to the patched container"""
        last_path = FileUtil(self._container_patch_path).getdata()
        if last_path and isinstance(last_path, str):
            return last_path.strip()
        return ""

    def check_container_path(self):
        """verify if path to container is ok"""
        last_path = self.get_patch_last_path()
        if last_path and last_path != self._container_dir:
            return False
        return True

    def get_patch_last_time(self):
        """get time in seconds of last full patch of container"""
        last_time = FileUtil(self._container_patch_time).getdata()
        try:
            return str(int(last_time))
        except ValueError:
            return "0"

    def patch_binaries(self):
        """Set all executables and libs to the ld.so absolute pathname"""
        if not self.check_container_path():
            self.restore_binaries()
        last_time = "0"
        patchelf_exec = self.select_patchelf()
        elf_loader = self.get_container_loader()
        cmd = "%s --set-root-prefix %s #f" % \
            (patchelf_exec, self._container_root)
        self._walk_fs(cmd, self._container_root, self.BIN | self.LIB)
        newly_set = self.guess_elf_loader()
        if newly_set == elf_loader:
            try:
                last_time = str(int(time.time()))
            except ValueError:
                pass
            return (FileUtil(self._container_patch_time).putdata(last_time) and
                    FileUtil(self._container_patch_path).putdata(self._container_dir))
        return False

    def restore_binaries(self):
        """Restore all executables and libs to the original ld.so pathname"""
        patchelf_exec = self.select_patchelf()
        elf_loader = self.get_original_loader()
        last_path = self.get_patch_last_path()
        if last_path:
            cmd = "%s --restore-root-prefix %s #f" % \
                (patchelf_exec, last_path + "/ROOT")
        else:
            cmd = "%s --restore-root-prefix %s #f" % \
                (patchelf_exec, self._container_root)
        self._walk_fs(cmd, self._container_root, self.BIN | self.LIB)
        newly_set = self.guess_elf_loader()
        if newly_set == elf_loader:
            FileUtil(self._container_patch_path).remove()
            FileUtil(self._container_patch_time).remove()
        return newly_set == elf_loader

    def patch_ld(self, output_elf=None):
        """Patch ld.so"""
        elf_loader = self.get_container_loader()
        if FileUtil(self._container_ld_so_orig).size() == -1:
            status = FileUtil(elf_loader).copyto(self._container_ld_so_orig)
            if not status:
                return False
        ld_data = FileUtil(self._container_ld_so_orig).getdata()
        if not ld_data:
            ld_data = FileUtil(elf_loader).getdata()
            if not ld_data:
                return False
        nul_etc = "\x00/\x00\x00\x00\x00\x00\x00\x00\x00\x00"
        nul_lib = "\x00/\x00\x00\x00"
        nul_usr = "\x00/\x00\x00\x00"
        etc = "\x00/etc/ld.so"
        lib = "\x00/lib"
        usr = "\x00/usr"
        ld_data = ld_data.replace(etc, nul_etc).\
            replace(lib, nul_lib).replace(usr, nul_usr)
        ld_library_path_orig = "\x00LD_LIBRARY_PATH\x00"
        ld_library_path_new = "\x00LD_LIBRARY_REAL\x00"
        ld_data = ld_data.replace(ld_library_path_orig, ld_library_path_new)
        if output_elf is None:
            return bool(FileUtil(elf_loader).putdata(ld_data))
        return bool(FileUtil(output_elf).putdata(ld_data))

    def restore_ld(self):
        """Restore ld.so"""
        elf_loader = self.get_container_loader()
        if FileUtil(self._container_ld_so_orig).size() <= 0:
            Msg().err("Error: original loader not found or empty")
            return False
        if not FileUtil(self._container_ld_so_orig).copyto(elf_loader):
            Msg().err("Error: in loader copy or file locked by other process")
            return False
        return True

    def _get_ld_config(self):
        """Get get directories from container ld.so.cache"""
        cmd = "ldconfig -p -C %s/%s" % (self._container_root,
                                        Config.ld_so_cache)
        ld_dict = dict()
        ld_data = Uprocess().get_output(cmd)
        if not ld_data:
            return []
        for line in ld_data.split("\n"):
            match = re.search("([^ ]+) => ([^ ]+)", line)
            if match:
                ld_dict[self._container_root + \
                        os.path.dirname(match.group(2))] = True
        return ld_dict.keys()

    # pylint: disable=too-many-nested-blocks
    def _find_ld_libdirs(self, root_path=None):
        """search for library directories in container"""
        if root_path is None:
            root_path = self._container_root
        ld_list = []
        for dir_path, dummy, files in os.walk(root_path):
            for f_name in files:
                try:
                    f_path = dir_path + "/" + f_name
                    if not os.access(f_path, os.R_OK):
                        continue
                    elif os.path.isfile(f_path):
                        if self._shlib.match(f_name):
                            if dir_path not in ld_list:
                                ld_list.append(dir_path)
                except OSError:
                    continue
        return ld_list

    def get_ld_libdirs(self, force=False):
        """Get ld library paths"""
        if force or not os.path.exists(self._container_ld_libdirs):
            ld_list = self._find_ld_libdirs()
            ld_str = ":".join(ld_list)
            FileUtil(self._container_ld_libdirs).putdata(ld_str)
            return ld_list
        ld_str = FileUtil(self._container_ld_libdirs).getdata()
        return ld_str.split(":")

    def get_ld_library_path(self):
        """Get ld library paths"""
        ld_list = self._get_ld_config()
        ld_list.extend(self.get_ld_libdirs())
        for ld_dir in Config.lib_dirs_list_essential:
            ld_dir = self._container_root + "/" + ld_dir
            if ld_dir not in ld_list:
                ld_list.insert(0, ld_dir)
        ld_list.extend(Config.lib_dirs_list_append)
        return ":".join(ld_list)


class NixAuthentication(object):
    """Provides abstraction and useful methods to manage
    passwd and group based authentication, both for the
    host system and for the container.
    If passwd_file and group_file are None then the host
    system authentication databases are used.
    """

    def __init__(self, passwd_file=None, group_file=None):
        self.passwd_file = passwd_file
        self.group_file = group_file

    def _get_user_from_host(self, wanted_user):
        """get user information from the host /etc/passwd"""
        wanted_uid = ""
        if (isinstance(wanted_user, (int, long)) or
                re.match("^\\d+$", wanted_user)):
            wanted_uid = str(wanted_user)
            wanted_user = ""
        if wanted_uid:
            try:
                usr = pwd.getpwuid(int(wanted_uid))
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

    def _get_group_from_host(self, wanted_group):
        """get group information from the host /etc/group"""
        wanted_gid = ""
        if (isinstance(wanted_group, (int, long)) or
                re.match("^\\d+$", wanted_group)):
            wanted_gid = str(wanted_group)
            wanted_group = ""
        if wanted_gid:
            try:
                hgr = grp.getgrgid(int(wanted_gid))
            except (IOError, OSError, KeyError):
                return("", "", "")
            return(str(hgr.gr_name), str(hgr.gr_gid), str(hgr.gr_mem))
        else:
            try:
                hgr = grp.getgrnam(wanted_group)
            except (IOError, OSError, KeyError):
                return("", "", "")
            return(str(hgr.gr_name), str(hgr.gr_gid), str(hgr.gr_mem))

    def _get_user_from_file(self, wanted_user):
        """Get user from a passwd file"""
        wanted_uid = ""
        if (isinstance(wanted_user, (int, long)) or
                re.match("^\\d+$", wanted_user)):
            wanted_uid = str(wanted_user)
            wanted_user = ""
        try:
            inpasswd = open(self.passwd_file)
        except (IOError, OSError):
            return("", "", "", "", "", "")
        else:
            for line in inpasswd:
                (user, dummy, uid, gid, gecos, home,
                 shell) = line.strip().split(":")
                if wanted_user and user == wanted_user:
                    return(user, uid, gid, gecos, home, shell)
                if wanted_uid and uid == wanted_uid:
                    return(user, uid, gid, gecos, home, shell)
            inpasswd.close()
            return("", "", "", "", "", "")

    def _get_group_from_file(self, wanted_group):
        """Get group from a group file"""
        wanted_gid = ""
        if (isinstance(wanted_group, (int, long)) or
                re.match("^\\d+$", wanted_group)):
            wanted_gid = str(wanted_group)
            wanted_group = ""
        try:
            ingroup = open(self.group_file)
        except (IOError, OSError):
            return("", "", "")
        else:
            for line in ingroup:
                (group, dummy, gid, users) = line.strip().split(":")
                if wanted_group and group == wanted_group:
                    return(group, gid, users)
                if wanted_gid and gid == wanted_gid:
                    return(group, gid, users)
            ingroup.close()
            return("", "", "")

    def add_user(self, user, passw, uid, gid, gecos,
                 home, shell):
        """Add a *nix user to a /etc/passwd file"""
        try:
            outpasswd = open(self.passwd_file, "ab")
        except (IOError, OSError):
            return False
        else:
            outpasswd.write("%s:%s:%s:%s:%s:%s:%s\n" %
                            (user, passw, uid, gid, gecos, home, shell))
            outpasswd.close()
            return True

    def add_group(self, group, gid):
        """Add a group to a /etc/passwd file"""
        try:
            outgroup = open(self.group_file, "ab")
        except (IOError, OSError):
            return False
        else:
            outgroup.write("%s:x:%s:\n" % (group, gid))
            outgroup.close()
            return True

    def get_user(self, wanted_user):
        """Get host or container user"""
        if self.passwd_file:
            return self._get_user_from_file(wanted_user)
        return self._get_user_from_host(wanted_user)

    def get_group(self, wanted_group):
        """Get host or container group"""
        if self.group_file:
            return self._get_group_from_file(wanted_group)
        return self._get_group_from_host(wanted_group)

    def get_home(self):
        """Get host or container home directory"""
        (r_user, dummy, dummy, dummy, r_home,
         dummy) = self.get_user(Config.uid)
        if r_user:
            return r_home
        return ""


class FileBind(object):
    """Alternative method to allow host files to be visible inside
    a container when binding of files is not possible such as when
    using rootless namespaces.
    """

    bind_dir = "/.bind_host_files"
    orig_dir = "/.bind_orig_files"

    def __init__(self, localrepo, container_id):
        self.localrepo = localrepo               # LocalRepository object
        self.container_id = container_id         # Container id
        self.container_dir = \
            os.path.realpath(self.localrepo.cd_container(container_id))
        self.container_root = self.container_dir + "/ROOT"
        self.container_bind_dir = self.container_root + self.bind_dir
        self.container_orig_dir = self.container_dir + self.orig_dir
        self.host_bind_dir = None

    def setup(self):
        """Prepare container for FileBind"""
        if not os.path.isdir(self.container_orig_dir):
            if not FileUtil(self.container_orig_dir).mkdir():
                Msg().err("Error: creating dir:", self.container_orig_dir)
                return False
        if not os.path.isdir(self.container_bind_dir):
            if not FileUtil(self.container_bind_dir).mkdir():
                Msg().err("Error: creating dir:", self.container_bind_dir)
                return False
        return True

    def restore(self):
        """Restore container files after FileBind"""
        error = False
        if not os.path.isdir(self.container_orig_dir):
            return
        for f_name in os.listdir(self.container_orig_dir):
            orig_file = self.container_orig_dir + "/" + f_name
            if not os.path.isfile(orig_file):
                continue
            cont_file = os.path.basename(f_name).replace('#', '/')
            cont_file = self.container_root + "/" + cont_file
            if os.path.islink(cont_file):
                FileUtil(cont_file).remove()
            elif os.path.exists(cont_file):
                continue
            if not FileUtil(orig_file).rename(cont_file):
                Msg().err("Error: restoring binded file:", cont_file)
                error = True
        if not error:
            FileUtil(self.container_orig_dir).remove()
        FileUtil(self.container_bind_dir).remove()

    def start(self, files_list):
        """Prepare host files to be made available inside container
        files_list: is the initial list of files to be made available
        returns: the directory that holds the files and that must be
                 binded inside the container
        """
        self.host_bind_dir = FileUtil("BIND_FILES").mktmpdir()
        for f_name in files_list:
            if not os.path.isfile(f_name):
                continue
            orig_file = f_name.replace('/', '#')
            orig_file_path = self.container_orig_dir + "/" + orig_file
            cont_file = self.container_root + "/" + f_name
            link_path = self.bind_dir + "/" + orig_file
            if not os.path.exists(orig_file_path):
                if os.path.exists(cont_file):
                    os.rename(cont_file, orig_file_path)
                else:
                    FileUtil(orig_file_path).putdata("")
                os.symlink(link_path, cont_file)
            FileUtil(orig_file_path).copyto(self.host_bind_dir)
        return (self.host_bind_dir, self.bind_dir)

    def finish(self):
        """Cleanup after run"""
        pass
        #return FileUtil(self.host_bind_dir).remove()

    def add(self, host_file, cont_file):
        """Add file to be made available inside container"""
        replace_file = cont_file.replace('/', '#')
        replace_file = self.host_bind_dir + "/" + replace_file
        FileUtil(replace_file).remove()
        FileUtil(host_file).copyto(replace_file)


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


class PRootEngine(ExecutionEngineCommon):
    """Docker container execution engine using PRoot
    Provides a chroot like environment to run containers.
    Uses PRoot both as chroot alternative and as emulator of
    the root identity and privileges.
    Inherits from ContainerEngine class
    """

    def __init__(self, localrepo):
        super(PRootEngine, self).__init__(localrepo)
        conf = Config()
        self.proot_exec = None                   # PRoot
        self.proot_noseccomp = False             # Noseccomp mode
        self._kernel = conf.oskernel()           # Emulate kernel

    def _select_proot(self):
        """Set proot executable and related variables"""
        conf = Config()
        arch = conf.arch()
        if arch == "amd64":
            if conf.oskernel_isgreater((4, 8, 0)):
                image_list = ["proot-x86_64-4_8_0", "proot-x86_64", "proot"]
            else:
                image_list = ["proot-x86_64", "proot"]
        elif arch == "i386":
            if conf.oskernel_isgreater((4, 8, 0)):
                image_list = ["proot-x86-4_8_0", "proot-x86", "proot"]
            else:
                image_list = ["proot-x86", "proot"]
        elif arch == "arm64":
            if conf.oskernel_isgreater((4, 8, 0)):
                image_list = ["proot-arm64-4_8_0", "proot-arm64", "proot"]
            else:
                image_list = ["proot-arm64", "proot"]
        elif arch == "arm":
            if conf.oskernel_isgreater((4, 8, 0)):
                image_list = ["proot-arm-4_8_0", "proot-arm", "proot"]
            else:
                image_list = ["proot-arm", "proot"]
        f_util = FileUtil(self.localrepo.bindir)
        self.proot_exec = f_util.find_file_in_dir(image_list)
        if not self.proot_exec:
            Msg().err("Error: proot executable not found")
            sys.exit(1)
        if conf.oskernel_isgreater((4, 8, 0)):
            if conf.proot_noseccomp is not None:
                self.proot_noseccomp = conf.proot_noseccomp
            if self.exec_mode.get_mode() == "P2":
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
        for (cont_port, host_port) in self._get_portsmap().iteritems():
            proot_netmap_list.extend(["-p", "%d:%d " % (cont_port, host_port)])
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

        if Config.proot_killonexit:
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


class RuncEngine(ExecutionEngineCommon):
    """Docker container execution engine using runc
    Provides a namespaces based user space container.
    Inherits from ContainerEngine class
    """

    def __init__(self, localrepo):
        super(RuncEngine, self).__init__(localrepo)
        self.runc_exec = None                   # runc
        self._container_specjson = None
        self._container_specfile = None
        self._filebind = None
        self.execution_id = None

    def _select_runc(self):
        """Set runc executable and related variables"""
        conf = Config()
        arch = conf.arch()
        if arch == "amd64":
            image_list = ["runc-x86_64", "runc"]
        elif arch == "i386":
            image_list = ["runc-x86", "runc"]
        elif arch == "arm64":
            image_list = ["runc-arm64", "runc"]
        elif arch == "arm":
            image_list = ["runc-arm", "runc"]
        f_util = FileUtil(self.localrepo.bindir)
        self.runc_exec = f_util.find_file_in_dir(image_list)
        if not self.runc_exec:
            Msg().err("Error: runc executable not found")
            sys.exit(1)

    def _load_spec(self, new=False):
        """Generate runc spec file"""
        if FileUtil(self._container_specfile).size() != -1 and new:
            FileUtil(self._container_specfile).remove()
        if FileUtil(self._container_specfile).size() == -1:
            cmd_l = [self.runc_exec, "spec", "--rootless", "--bundle",
                     os.path.realpath(self.container_dir)]
            status = subprocess.call(cmd_l, shell=False, stderr=Msg.chlderr,
                                     close_fds=True)
            if status:
                return False
        json_obj = None
        infile = None
        try:
            infile = open(self._container_specfile)
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
            outfile = open(self._container_specfile, 'w')
            json.dump(self._container_specjson, outfile)
        except (IOError, OSError, AttributeError, ValueError, TypeError):
            if outfile:
                outfile.close()
            return False
        outfile.close()
        return True

    def _remove_quotes(self, argv):
        """Remove quotes from string"""
        unquoted_argv = []
        for arg in argv:
            if " " in arg and arg[0] in ('"', "'") and arg[-1] in ('"', "'"):
                unquoted_argv.append(arg.strip(arg[0]))
            else:
                unquoted_argv.append(arg)
        return unquoted_argv

    def _set_spec(self):
        """Set spec values"""
        json_obj = self._container_specjson
        json_obj["root"]["path"] = os.path.realpath(self.container_root)
        json_obj["root"]["readonly"] = False
        if "." in self.opt["hostname"]:
            json_obj["hostname"] = self.opt["hostname"]
        else:
            json_obj["hostname"] = platform.node()
        if self.opt["cwd"]:
            json_obj["process"]["cwd"] = self.opt["cwd"]
        json_obj["process"]["terminal"] = sys.stdout.isatty()
        json_obj["process"]["env"] = []
        for env_str in self.opt["env"]:
            (env_var, value) = env_str.split("=", 1)
            if env_var:
                json_obj["process"]["env"].append("%s=%s" % (env_var, value))
        for idmap in json_obj["linux"]["uidMappings"]:
            if "hostID" in idmap:
                idmap["hostID"] = Config.uid
        for idmap in json_obj["linux"]["gidMappings"]:
            if "hostID" in idmap:
                idmap["hostID"] = Config.gid
        #json_obj["process"]["args"] = self._remove_quotes(self.opt["cmd"])
        json_obj["process"]["args"] = self.opt["cmd"]
        return json_obj

    def _uid_check(self):
        """Check the uid_map string for container run command"""
        if ("user" in self.opt and self.opt["user"] != "0" and
                self.opt["user"] != "root"):
            Msg().err("Warning: this engine only supports execution as root",
                      l=Msg.WAR)

    def _add_device_spec(self, dev_path, mode="rwm"):
        """Add device to the configuration"""
        if not (os.path.exists(dev_path) and dev_path.startswith("/dev/")):
            Msg().err("Error: device not found", dev_path)
            return False
        dev_stat = os.stat(dev_path)
        if stat.S_ISBLK(dev_stat.st_mode):
            dev_type = "b"
        elif stat.S_ISCHR(dev_stat.st_mode):
            dev_type = "c"
        else:
            Msg().err("Error: not a device", dev_path)
            return False
        filemode = 0
        if "r" in mode.lower():
            filemode += 0o444
        if "w" in mode.lower():
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
            "uid": Config.uid,
            "gid": Config.uid,
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

    def _create_mountpoint(self, host_path, cont_path):
        """Override create mountpoint"""
        return True

    def _add_mount_spec(self, host_source, cont_dest, rwmode=False):
        """Add one mount point"""
        if rwmode:
            mode = "rw"
        else:
            mode = "ro"
        mount = {"destination": cont_dest,
                 "type": "none",
                 "source": host_source,
                 "options": ["rbind", "nosuid",
                             "noexec", "nodev",
                             mode, ], }
        self._container_specjson["mounts"].append(mount)

    def _del_mount_spec(self, host_source, cont_dest):
        """Remove one mount point"""
        for (index, mount) in enumerate(self._container_specjson["mounts"]):
            if (mount["destination"] == cont_dest and
                    mount["source"] == host_source):
                del self._container_specjson["mounts"][index]

    def _add_volume_bindings(self):
        """Get the volume bindings string for runc"""
        (host_dir, cont_dir) = self._filebind.start(Config.sysdirs_list)
        self._add_mount_spec(host_dir, cont_dir, rwmode=True)
        for vol in self.opt["vol"]:
            (host_dir, cont_dir) = self._vol_split(vol)
            if os.path.isdir(host_dir):
                if host_dir == "/dev":
                    Msg().err("Warning: this engine does not support -v",
                              host_dir, l=Msg.WAR)
                    continue
                self._add_mount_spec(host_dir, cont_dir, rwmode=True)
            elif os.path.isfile(host_dir):
                if cont_dir not in Config.sysdirs_list:
                    Msg().err("Error: engine does not support file mounting:",
                              host_dir)
                else:
                    self._filebind.add(host_dir, cont_dir)

    def _check_env(self):
        """Sanitize environment variables
           Overriding parent ExecutionEngineCommon() class.
        """
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
        return True

    def _run_invalid_options(self):
        """check -p --publish -P --publish-all --net-coop"""
        if self.opt["portsmap"]:
            Msg().err("Warning: this execution mode does not support "
                      "-p --publish", l=Msg.WAR)
        if self.opt["netcoop"]:
            Msg().err("Warning: this execution mode does not support "
                      "-P --netcoop --publish-all", l=Msg.WAR)

    def run(self, container_id):
        """Execute a Docker container using runc. This is the main method
        invoked to run the a container with runc.

          * argument: container_id or name
          * options:  many via self.opt see the help
        """

        Config.sysdirs_list = (
            "/etc/resolv.conf", "/etc/host.conf",
            "/etc/passwd", "/etc/group",
        )

        # setup execution
        if not self._run_init(container_id):
            return 2

        self._run_invalid_options()

        self._container_specfile = self.container_dir + "/config.json"
        self._filebind = FileBind(self.localrepo, self.container_id)

        self._select_runc()

        # create new OCI spec file
        if not self._load_spec(new=True):
            return 4

        self._uid_check()

        # if not --hostenv clean the environment
        self._run_env_cleanup_list()

        # set environment variables
        self._run_env_set()
        if not self._check_env():
            return 5

        self._set_spec()
        if (Config.runc_nomqueue or (Config.runc_nomqueue is None and not
                                     Config().oskernel_isgreater("4.8.0"))):
            self._del_mount_spec("mqueue", "/dev/mqueue")
        self._add_volume_bindings()
        self._add_devices()
        self._save_spec()

        if Msg.level >= Msg.DBG:
            runc_debug = ["--debug", ]
        else:
            runc_debug = []

        # build the actual command
        self.execution_id = Unique().uuid(self.container_id)
        cmd_l = self._set_cpu_affinity()
        cmd_l.append(self.runc_exec)
        cmd_l.extend(runc_debug)
        cmd_l.extend(["--root", self.container_dir, "run"])
        cmd_l.extend(["--bundle", self.container_dir, self.execution_id])
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
                    sys.stdout.write(os.read(pmaster, 1))
                except OSError:
                    break
        try:
            status.terminate()
        except OSError:
            pass
        self._filebind.finish()
        return status


class SingularityEngine(ExecutionEngineCommon):
    """Docker container execution engine using singularity
    Provides a namespaces based user space container.
    Inherits from ContainerEngine class
    """

    def __init__(self, localrepo):
        super(SingularityEngine, self).__init__(localrepo)
        self.singularity_exec = None                   # singularity
        self._filebind = None
        self.execution_id = None

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
        self._run_env_set()
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


class FakechrootEngine(ExecutionEngineCommon):
    """Docker container execution engine using Fakechroot
    Provides a chroot like environment to run containers.
    Uses Fakechroot as chroot alternative.
    Inherits from ContainerEngine class
    """

    def __init__(self, localrepo):
        super(FakechrootEngine, self).__init__(localrepo)
        self._fakechroot_so = ""
        self._elfpatcher = None

    def _select_fakechroot_so(self):
        """Select fakechroot sharable object library"""
        conf = Config()
        if conf.fakechroot_so:
            if isinstance(conf.fakechroot_so, list):
                image_list = conf.fakechroot_so
            elif isinstance(conf.fakechroot_so, str):
                image_list = [conf.fakechroot_so, ]
            if "/" in conf.fakechroot_so:
                if os.path.exists(conf.fakechroot_so):
                    return os.path.realpath(conf.fakechroot_so)
        elif os.path.exists(self.container_dir + "/libfakechroot.so"):
            return self.container_dir + "/libfakechroot.so"
        else:
            lib = "libfakechroot"
            deflib = "libfakechroot.so"
            image_list = [deflib, ]
            guest = GuestInfo(self.container_root)
            arch = guest.arch()
            (distro, version) = guest.osdistribution()
            version = version.split(".")[0]
            if arch == "amd64":
                image_list = ["%s-%s-%s-x86_64.so" % (lib, distro, version),
                              "%s-%s-x86_64.so" % (lib, distro),
                              "%s-x86_64.so" % (lib), deflib]
            elif arch == "i386":
                image_list = ["%s-%s-%s-x86.so" % (lib, distro, version),
                              "%s-%s-x86.so" % (lib, distro),
                              "%s-x86.so" % (lib), deflib]
            elif arch == "arm64":
                image_list = ["%s-%s-%s-arm64.so" % (lib, distro, version),
                              "%s-%s-arm64.so" % (lib, distro),
                              "%s-arm64.so" % (lib), deflib]
            elif arch == "arm":
                image_list = ["%s-%s-%s-arm.so" % (lib, distro, version),
                              "%s-%s-arm.so" % (lib, distro),
                              "%s-arm.so" % (lib), deflib]
        f_util = FileUtil(self.localrepo.libdir)
        fakechroot_so = f_util.find_file_in_dir(image_list)
        if not fakechroot_so:
            Msg().err("Error: no libfakechroot found", image_list)
            sys.exit(1)
        Msg().err("fakechroot_so:", fakechroot_so, l=Msg.DBG)
        return fakechroot_so

    def _setup_container_user(self, user):
        """Override of _setup_container_user()"""
        return self._setup_container_user_noroot(user)

    def _get_volume_bindings(self):
        """Get the volume bindings string for fakechroot run"""
        host_volumes_list = []
        map_volumes_list = []
        map_volumes_dict = dict()
        for vol in self.opt["vol"]:
            (host_path, cont_path) = self._vol_split(vol)
            if host_path == cont_path:
                host_volumes_list.append(host_path)
            else:
                map_volumes_dict[cont_path] = host_path + "!" + cont_path
        for cont_path in sorted(map_volumes_dict, reverse=True):
            map_volumes_list.append(map_volumes_dict[cont_path])
        return (":".join(host_volumes_list), ":".join(map_volumes_list))

    def _get_access_filesok(self):
        """
        Circunvent mpi init issues when calling access()
        A list of certain existing files is provided
        """
        file_list = []
        for c_path in Config.access_files:
            h_file = self._cont2host(c_path)
            if h_file and os.path.exists(h_file):
                file_list.append(c_path)
        return ":".join(file_list)

    def _fakechroot_env_set(self):
        """fakechroot environment variables to set"""
        (host_volumes, map_volumes) = self._get_volume_bindings()
        self._fakechroot_so = self._select_fakechroot_so()
        access_filesok = self._get_access_filesok()
        #
        self.opt["env"].append("PWD=" + self.opt["cwd"])
        self.opt["env"].append("FAKECHROOT_BASE=" +
                               os.path.realpath(self.container_root))
        self.opt["env"].append("LD_PRELOAD=" + self._fakechroot_so)
        if not self._is_volume("/tmp"):
            self.opt["env"].append("FAKECHROOT_AF_UNIX_PATH=" + Config.tmpdir)
        #
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
            self.opt["env"].append("FAKECHROOT_DISALLOW_ENV_CHANGES=true")
        elif xmode == "F3":
            self.opt["env"].append("FAKECHROOT_LIBRARY_ORIG=" + ld_library_real)
            self.opt["env"].append("LD_LIBRARY_REAL=" + ld_library_real)
            self.opt["env"].append("FAKECHROOT_DISALLOW_ENV_CHANGES=true")
        elif xmode == "F4":
            self.opt["env"].append("FAKECHROOT_LIBRARY_ORIG=" + ld_library_real)
            self.opt["env"].append("LD_LIBRARY_REAL=" + ld_library_real)
            self.opt["env"].append("FAKECHROOT_DISALLOW_ENV_CHANGES=true")
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
            Msg().err("Warning: this execution mode does not support "
                      "-p --publish", l=Msg.WAR)
        if self.opt["netcoop"]:
            Msg().err("Warning: this execution mode does not support "
                      "-P --netcoop --publish-all", l=Msg.WAR)

    def _run_add_script_support(self, exec_path):
        """Add an interpreter for non binary executables (scripts)"""
        filetype = GuestInfo(self.container_root).get_filetype(exec_path)
        if "ELF" in filetype and ("static" in filetype or
                                  "dynamic" in filetype):
            self.opt["cmd"][0] = exec_path
            return []
        env_exec = FileUtil("env").find_inpath("/bin:/usr/bin",
                                               self.container_root)
        if  env_exec:
            return [self.container_root + "/" + env_exec, ]
        real_path = self._cont2host(exec_path.split(self.container_root, 1)[-1])
        hashbang = FileUtil(real_path).get1stline()
        match = re.match("#! *([^ ]+)(.*)", hashbang)
        if match and not match.group(1).startswith("/"):
            Msg().err("Error: no such file", match.group(1), "in", exec_path)
            sys.exit(1)
        elif match:
            interpreter = [self.container_root + "/" + match.group(1), ]
            if match.group(2):
                interpreter.extend(match.group(2).strip().split(" "))
            self.opt["cmd"][0] = exec_path.split(self.container_root, 1)[-1]
            return interpreter
        sh_exec = FileUtil("sh").find_inpath(self._getenv("PATH"),
                                             self.container_root)
        if sh_exec:
            return [self.container_root + "/" + sh_exec, ]
        Msg().err("Error: sh not found")
        sys.exit(1)

    def run(self, container_id):
        """Execute a Docker container using Fakechroot. This is the main
        method invoked to run the a container with Fakechroot.

          * argument: container_id or name
          * options:  many via self.opt see the help
        """

        # this engine does not support root check and fix
        self._uid_check_noroot()

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
            Msg().err("Warning: container path mismatch, use setup to convert",
                      l=Msg.WAR)

        # set basic environment variables
        self._run_env_set()
        self._fakechroot_env_set()
        if not self._check_env():
            return 4

        # if not --hostenv clean the environment
        self._run_env_cleanup_list()

        # build the actual command
        cmd_l = self._set_cpu_affinity()
        cmd_l.extend(["env", "-i", ])
        cmd_l.extend(self.opt["env"])
        if xmode in ("F1", "F2"):
            container_loader = self._elfpatcher.get_container_loader()
            if container_loader:
                cmd_l.append(container_loader)
        cmd_l.extend(self._run_add_script_support(exec_path))
        cmd_l.extend(self.opt["cmd"])
        Msg().err("CMD =", cmd_l, l=Msg.VER)

        # execute
        self._run_banner(self.opt["cmd"][0], "#")
        cwd = self._cont2host(self.opt["cwd"])
        status = subprocess.call(cmd_l, shell=False, close_fds=True, cwd=cwd)
        return status


class NvidiaMode(object):
    """nvidia-docker like functionality for udocker.
    Make nvidia host libraries available within udocker, this is achieved
    by copy them into the container so that the execution modes that need
    to change libraries may work properly.
    """

    def __init__(self, localrepo, container_id):
        self.localrepo = localrepo               # LocalRepository object
        self.container_id = container_id         # Container id
        self.container_dir = self.localrepo.cd_container(container_id)
        if not self.container_dir:
            raise ValueError("invalid container id")
        self.container_root = self.container_dir + "/ROOT"
        self._container_nvidia_set = self.container_dir + "/nvidia"

    def _files_exist(self, cont_dst_dir, files_list):
        """Verify if files already exists"""
        for fname in files_list:
            dstname = self.container_root + '/' + cont_dst_dir + '/' + fname
            if os.path.exists(dstname):
                raise OSError("file already exists", dstname)

    def _copy_files(self, host_src_dir, cont_dst_dir, files_list, force=False):
        """copy or link file to destination creating directories as needed"""
        for fname in files_list:
            srcname = host_src_dir + '/' + fname
            dstname = self.container_root + '/' + cont_dst_dir + '/' + fname
            if os.path.isfile(dstname) or os.path.islink(dstname):
                if force:
                    try:
                        os.remove(dstname)
                    except OSError:
                        Msg().err("Error: deleting nvidia file", dstname)
                else:
                    Msg().err("Error: nvidia file already exists", dstname,
                              ", use --force to overwrite")
                    return
            if os.path.isfile(srcname):
                srcdir = os.path.dirname(srcname)
                dstdir = os.path.dirname(dstname)
                if not os.path.isdir(dstdir):
                    try:
                        os.makedirs(dstdir)
                        os.chmod(dstdir, stat.S_IMODE(os.stat(srcdir).st_mode) |
                                 stat.S_IRWXU)
                    except OSError:
                        Msg().err("Error: creating nvidia dir", dstdir)
                if not FileUtil(srcname).copyto(dstname):
                    Msg().err("Error: copying file", srcname, "to", dstname)
                    return
                try:
                    mask = stat.S_IMODE(os.stat(srcname).st_mode) | \
                                        stat.S_IWUSR | stat.S_IRUSR
                    if os.access(srcname, os.X_OK):
                        mask = mask | stat.S_IXUSR
                    os.chmod(dstname, mask)
                except (IOError, OSError) as error:
                    Msg().err("Error: change mask of nvidia file", error)
                Msg().err("nvidia copied", srcname, "to", dstname, l=Msg.DBG)

    def _get_nvidia_libs(self, host_dir):
        """Expand the library files to include the versions"""
        lib_list = []
        for lib in Config.nvi_lib_list:
            for expanded_libs in glob.glob(host_dir + '/' + lib + '*'):
                lib_list.append(expanded_libs.replace(host_dir, ''))
        return lib_list

    def _find_host_dir(self):
        """Find the location of the host nvidia libraries"""
        dir_list = set()
        ld_library_path = os.getenv("LD_LIBRARY_PATH")
        if ld_library_path:
            for libdir in ld_library_path.split(':'):
                if glob.glob(libdir + '/libnvidia-cfg.so*'):
                    dir_list.add(libdir + '/')
                if glob.glob(libdir + '/libcuda.so*'):
                    dir_list.add(libdir + '/')
        ld_data = Uprocess().get_output("ldconfig -p")
        if not ld_data:
            return ""
        for line in ld_data.split("\n"):
            match = re.search("[ |\t]libnvidia-cfg.so[^ ]* .*x86-64.*=> (/.*)", line)
            if match:
                dir_list.add(os.path.dirname(match.group(1)) + '/')
            match = re.search("[ |\t]libcuda.so[^ ]* .*x86-64.*=> (/.*)", line)
            if match:
                dir_list.add(os.path.dirname(match.group(1)) + '/')
        return dir_list

    def _find_cont_dir(self):
        """Find the location of the host target directory for libraries"""
        for dst_dir in ('/usr/lib/x86_64-linux-gnu', '/usr/lib64'):
            if os.path.isdir(self.container_root + "/" + dst_dir):
                return dst_dir
        return ""

    def _installation_exists(self, nvi_host_dir_list, nvi_cont_dir):
        """Container has files from previous nvidia installation"""
        try:
            for nvi_host_dir in nvi_host_dir_list:
                lib_list = self._get_nvidia_libs(nvi_host_dir)
                self._files_exist(nvi_cont_dir, lib_list)
            self._files_exist('/etc', Config.nvi_etc_list)
            self._files_exist('/usr/bin', Config.nvi_bin_list)
        except OSError:
            return True
        return False

    def set_mode(self, force=False):
        """Set nvidia mode"""
        if not self.container_dir:
            Msg().err("Error: nvidia set mode container dir not found")
            return
        nvi_host_dir_list = self._find_host_dir()
        nvi_cont_dir = self._find_cont_dir()
        if not nvi_host_dir_list:
            Msg().err("Error: host nvidia libraries not found")
            return
        if not nvi_cont_dir:
            Msg().err("Error: destination directory for nvidia libs not found")
            return
        if (not force) and self._installation_exists(nvi_host_dir_list, nvi_cont_dir):
            Msg().err("Error: nvidia installation already exists"
                      ", use --force to overwrite")
            return
        for nvi_host_dir in nvi_host_dir_list:
            lib_list = self._get_nvidia_libs(nvi_host_dir)
            self._copy_files(nvi_host_dir, nvi_cont_dir, lib_list, force)
        self._copy_files('/etc', '/etc', Config.nvi_etc_list, force)
        self._copy_files('/usr/bin', '/usr/bin', Config.nvi_bin_list, force)
        FileUtil(self._container_nvidia_set).putdata("")

    def get_mode(self):
        """Get nvidia mode"""
        return os.path.exists(self._container_nvidia_set)

    def get_devices(self):
        """Get list of nvidia devices related to cuda"""
        dev_list = []
        for dev in Config.nvi_dev_list:
            for expanded_devs in glob.glob(dev + '*'):
                dev_list.append(expanded_devs)
        return dev_list


class ExecutionMode(object):
    """Generic execution engine class to encapsulate the specific
    execution engines and their execution modes.
    P1: proot with seccomp
    P2: proot without seccomp (slower)
    F1: fakeroot running executables via direct loader invocation
    F2: similar to F1 with protected environment and modified ld.so
    F3: fakeroot patching the executables elf headers
    F4: similar to F3 with support to newly created executables
        dynamic patching of elf headers
    S1: singularity
    """

    def __init__(self, localrepo, container_id):
        self.localrepo = localrepo               # LocalRepository object
        self.container_id = container_id         # Container id
        self.container_dir = self.localrepo.cd_container(container_id)
        self.container_root = self.container_dir + "/ROOT"
        self.container_execmode = self.container_dir + "/execmode"
        self.container_orig_root = self.container_dir + "/root.path"
        self.exec_engine = None
        self.valid_modes = ("P1", "P2", "F1", "F2", "F3", "F4", "R1", "S1")

    def get_mode(self):
        """Get execution mode"""
        xmode = FileUtil(self.container_execmode).getdata().strip()
        if not xmode:
            xmode = Config.default_execution_mode
        return xmode

    def set_mode(self, xmode, force=False):
        """Set execution mode"""
        status = False
        prev_xmode = self.get_mode()
        elfpatcher = ElfPatcher(self.localrepo, self.container_id)
        filebind = FileBind(self.localrepo, self.container_id)
        orig_path = FileUtil(self.container_orig_root).getdata().strip()
        if xmode not in self.valid_modes:
            Msg().err("Error: invalid execmode:", xmode)
            return status
        if not (force or xmode != prev_xmode):
            return True
        if prev_xmode in ("R1", "S1") and xmode not in ("R1", "S1"):
            filebind.restore()
        if xmode.startswith("F"):
            if force or prev_xmode[0] in ("P", "R", "S"):
                status = (FileUtil(self.container_root).links_conv(force, True,
                                                                   orig_path)
                          and elfpatcher.get_ld_libdirs(force))
        if xmode in ("P1", "P2", "F1", "R1", "S1"):
            if prev_xmode in ("P1", "P2", "F1", "R1", "S1"):
                status = True
            elif force or prev_xmode in ("F2", "F3", "F4"):
                status = ((elfpatcher.restore_ld() or force) and
                          elfpatcher.restore_binaries())
            if xmode in ("R1", "S1"):
                filebind.setup()
        elif xmode in ("F2", ):
            if force or prev_xmode in ("F3", "F4"):
                status = elfpatcher.restore_binaries()
            if force or prev_xmode in ("P1", "P2", "F1", "R1", "S1"):
                status = elfpatcher.patch_ld()
        elif xmode in ("F3", "F4"):
            if force or prev_xmode in ("P1", "P2", "F1", "F2", "R1", "S1"):
                status = (elfpatcher.patch_ld() and
                          elfpatcher.patch_binaries())
            elif prev_xmode in ("F3", "F4"):
                status = True
        if xmode[0] in ("P", "R", "S"):
            if force or (status and prev_xmode.startswith("F")):
                status = FileUtil(self.container_root).links_conv(force, False,
                                                                  orig_path)
        if status or force:
            status = FileUtil(self.container_execmode).putdata(xmode)
        if status or force:
            status = FileUtil(self.container_orig_root).putdata(
                os.path.realpath(self.container_root))
        if (not status) and (not force):
            Msg().err("Error: container setup failed")
        return status

    def get_engine(self):
        """get execution engine instance"""
        xmode = self.get_mode()
        if xmode.startswith("P"):
            self.exec_engine = PRootEngine(self.localrepo)
        elif xmode.startswith("F"):
            self.exec_engine = FakechrootEngine(self.localrepo)
        elif xmode.startswith("R"):
            self.exec_engine = RuncEngine(self.localrepo)
        elif xmode.startswith("S"):
            self.exec_engine = SingularityEngine(self.localrepo)
        return self.exec_engine


class ContainerStructure(object):
    """Docker container structure.
    Creation of a container filesystem from a repository image.
    Creation of a container filesystem from a layer tar file.
    Access to container metadata.
    """

    def __init__(self, localrepo, container_id=None):
        self.localrepo = localrepo
        self.container_id = container_id
        self.tag = ""
        self.imagerepo = ""

    def get_container_attr(self):
        """Get container directory and JSON metadata by id or name"""
        if Config.location:
            container_dir = ""
            container_json = []
        else:
            container_dir = self.localrepo.cd_container(self.container_id)
            if not container_dir:
                Msg().err("Error: container id or name not found")
                return(False, False)
            container_json = self.localrepo.load_json(
                container_dir + "/container.json")
            if not container_json:
                Msg().err("Error: invalid container json metadata")
                return(False, False)
        return(container_dir, container_json)

    def _chk_container_root(self, container_id=None):
        """Check container ROOT sanity"""
        if container_id:
            container_dir = self.localrepo.cd_container(container_id)
        else:
            container_dir = self.localrepo.cd_container(self.container_id)
        if not container_dir:
            return 0
        container_root = container_dir + "/ROOT"
        check_list = ["/lib", "/bin", "/etc", "/tmp", "/var", "/usr", "/sys",
                      "/dev", "/data", "/home", "/system", "/root", "/proc", ]
        found = 0
        for f_path in check_list:
            if os.path.exists(container_root + f_path):
                found += 1
        return found

    def create_fromimage(self, imagerepo, tag):
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
            Msg().err("Error: create container: imagerepo is invalid")
            return False
        (container_json, layer_files) = self.localrepo.get_image_attributes()
        if not container_json:
            Msg().err("Error: create container: getting layers or json")
            return False
        if not self.container_id:
            self.container_id = Unique().uuid(os.path.basename(self.imagerepo))
        container_dir = self.localrepo.setup_container(
            self.imagerepo, self.tag, self.container_id)
        if not container_dir:
            Msg().err("Error: create container: setting up container")
            return False
        self.localrepo.save_json(
            container_dir + "/container.json", container_json)
        status = self._untar_layers(layer_files, container_dir + "/ROOT")
        if not status:
            Msg().err("Error: creating container:", self.container_id)
        elif not self._chk_container_root():
            Msg().err("Warning: check container content:", self.container_id,
                      l=Msg.WAR)
        return self.container_id

    def create_fromlayer(self, imagerepo, tag, layer_file, container_json):
        """Create a container from a layer file exported by Docker.
        """
        self.imagerepo = imagerepo
        self.tag = tag
        if not self.container_id:
            self.container_id = Unique().uuid(os.path.basename(self.imagerepo))
        if not container_json:
            Msg().err("Error: create container: getting json")
            return False
        container_dir = self.localrepo.setup_container(
            self.imagerepo, self.tag, self.container_id)
        if not container_dir:
            Msg().err("Error: create container: setting up")
            return False
        self.localrepo.save_json(
            container_dir + "/container.json", container_json)
        status = self._untar_layers([layer_file, ], container_dir + "/ROOT")
        if not status:
            Msg().err("Error: creating container:", self.container_id)
        elif not self._chk_container_root():
            Msg().err("Warning: check container content:", self.container_id,
                      l=Msg.WAR)
        return self.container_id

    def clone_fromfile(self, clone_file):
        """Create a cloned container from a file containing a cloned container
        exported by udocker.
        """
        if not self.container_id:
            self.container_id = Unique().uuid(os.path.basename(self.imagerepo))
        container_dir = self.localrepo.setup_container(
            "CLONING", "inprogress", self.container_id)
        if not container_dir:
            Msg().err("Error: create container: setting up")
            return False
        status = self._untar_layers([clone_file, ], container_dir)
        if not status:
            Msg().err("Error: creating container clone:", self.container_id)
        elif not self._chk_container_root():
            Msg().err("Warning: check container content:", self.container_id,
                      l=Msg.WAR)
        return self.container_id

    def _apply_whiteouts(self, tarf, destdir):
        """The layered filesystem od docker uses whiteout files
        to identify files or directories to be removed.
        The format is .wh.<filename>
        """
        cmd = r"tar tf %s '*\/\.wh\.*'" % (tarf)
        proc = subprocess.Popen(cmd, shell=True, stderr=Msg.chlderr,
                                stdout=subprocess.PIPE, close_fds=True)
        while True:
            wh_filename = proc.stdout.readline().strip()
            if wh_filename:
                wh_basename = os.path.basename(wh_filename)
                if wh_basename.startswith(".wh."):
                    rm_filename = destdir + "/" \
                        + os.path.dirname(wh_filename) + "/" \
                        + wh_basename.replace(".wh.", "", 1)
                    FileUtil(rm_filename).remove()
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
        status = True
        gid = str(os.getgid())
        for tarf in tarfiles:
            if tarf != "-":
                self._apply_whiteouts(tarf, destdir)
            cmd = "umask 022 ; tar -C %s -x " % destdir
            if Msg.level >= Msg.VER:
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
            status = subprocess.call(cmd, shell=True, stderr=Msg.chlderr,
                                     close_fds=True)
            if status:
                Msg().err("Error: while extracting image layer")
        return not status

    def _tar(self, tarfile, sourcedir):
        """Create a tar file for a given sourcedir
        """
        cmd = "tar -C %s -c " % sourcedir
        if Msg.level >= Msg.VER:
            cmd += " -v "
        cmd += r" --one-file-system "
        #cmd += r" --xform 's:^\./::' "
        cmd += r" -S --xattrs -f " + tarfile + " . "
        status = subprocess.call(cmd, shell=True, stderr=Msg.chlderr,
                                 close_fds=True)
        if status:
            Msg().err("Error: creating tar file:", tarfile)
        return not status

    def _copy(self, sourcedir, destdir):
        """Copy directories
        """
        cmd = "tar -C %s -c " % sourcedir
        if Msg.level >= Msg.VER:
            cmd += " -v "
        cmd += r" --one-file-system -S --xattrs -f - . "
        cmd += r"|tar -C %s -x " % destdir
        cmd += r" -f - "
        status = subprocess.call(cmd, shell=True, stderr=Msg.chlderr,
                                 close_fds=True)
        if status:
            Msg().err("Error: copying:", sourcedir, " to ", destdir)
        return not status

    def get_container_meta(self, param, default, container_json):
        """Get the container metadata from the container"""
        if "config" in container_json:
            confidx = "config"
        elif "container_config" in container_json:
            confidx = "container_config"
        if container_json[confidx]  and param in container_json[confidx]:
            if container_json[confidx][param] is None:
                pass
            elif (isinstance(container_json[confidx][param], str) and (
                    isinstance(default, (list, tuple)))):
                return container_json[confidx][param].strip().split()
            elif (isinstance(default, str) and (
                    isinstance(container_json[confidx][param], (list, tuple)))):
                return " ".join(container_json[confidx][param])
            elif (isinstance(default, str) and (
                    isinstance(container_json[confidx][param], dict))):
                return self._dict_to_str(container_json[confidx][param])
            elif (isinstance(default, list) and (
                    isinstance(container_json[confidx][param], dict))):
                return self._dict_to_list(container_json[confidx][param])
            else:
                return container_json[confidx][param]
        return default

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

    def export_tofile(self, clone_file):
        """Export a container creating a tar file of the rootfs
        """
        container_dir = self.localrepo.cd_container(self.container_id)
        if not container_dir:
            Msg().err("Error: container not found:", self.container_id)
            return False
        status = self._tar(clone_file, container_dir + "/ROOT")
        if not status:
            Msg().err("Error: exporting container file system:", self.container_id)
        return self.container_id

    def clone_tofile(self, clone_file):
        """Create a cloned container tar file containing both the rootfs
        and all udocker control files. This is udocker specific.
        """
        container_dir = self.localrepo.cd_container(self.container_id)
        if not container_dir:
            Msg().err("Error: container not found:", self.container_id)
            return False
        status = self._tar(clone_file, container_dir)
        if not status:
            Msg().err("Error: exporting container as clone:", self.container_id)
        return self.container_id

    def clone(self):
        """Clone a container by creating a complete copy
        """
        source_container_dir = self.localrepo.cd_container(self.container_id)
        if not source_container_dir:
            Msg().err("Error: source container not found:", self.container_id)
            return False
        dest_container_id = Unique().uuid(os.path.basename(self.imagerepo))
        dest_container_dir = self.localrepo.setup_container(
            "CLONING", "inprogress", dest_container_id)
        if not dest_container_dir:
            Msg().err("Error: create destination container: setting up")
            return False
        status = self._copy(source_container_dir, dest_container_dir)
        if not status:
            Msg().err("Error: creating container:", dest_container_id)
        elif not self._chk_container_root(dest_container_id):
            Msg().err("Warning: check container content:", dest_container_id,
                      l=Msg.WAR)
        return dest_container_id


class LocalRepository(object):
    """Implements a basic repository for images and containers.
    The repository will be usually in the user home directory.
    The repository has a simple directory structure:
    1. layers    : one dir containing all image layers so that
                   layers shared among images are not duplicated
    2. containers: has inside one directory per container,
                   each dir has a ROOT with the extracted image
    3. repos:      has inside a directory tree of repos the
                   leaf repo dirs are called tags and contain the
                   image data (these are links both to layer tarballs
                   and json metadata files.
    4. bin:        contains executables (PRoot)
    5. lib:        contains python libraries
    """

    def __init__(self, topdir=None):
        if topdir:
            self.topdir = topdir
        else:
            self.topdir = Config.topdir

        self.bindir = Config.bindir
        self.libdir = Config.libdir
        self.reposdir = Config.reposdir
        self.layersdir = Config.layersdir
        self.containersdir = Config.containersdir
        self.homedir = Config.homedir

        if not self.bindir:
            self.bindir = self.topdir + "/bin"
        if not self.libdir:
            self.libdir = self.topdir + "/lib"
        if not self.reposdir:
            self.reposdir = self.topdir + "/repos"
        if not self.layersdir:
            self.layersdir = self.topdir + "/layers"
        if not self.containersdir:
            self.containersdir = self.topdir + "/containers"

        self.cur_repodir = ""
        self.cur_tagdir = ""
        self.cur_containerdir = ""

        FileUtil(self.reposdir).register_prefix()
        FileUtil(self.layersdir).register_prefix()
        FileUtil(self.containersdir).register_prefix()

    def setup(self, topdir=None):
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
            if not os.path.exists(self.libdir):
                os.makedirs(self.libdir)
            if not (Config.keystore.startswith("/") or os.path.exists(self.homedir)):
                os.makedirs(self.homedir)
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
                      os.path.exists(self.libdir),
                      os.path.exists(self.homedir)]
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
        """Set the protection mark in a container or image tag"""
        try:
            # touch create version file
            open(directory + "/PROTECT", 'w').close()
            return True
        except (IOError, OSError):
            return False

    def _unprotect(self, directory):
        """Remove protection mark from container or image tag"""
        return FileUtil(directory + "/PROTECT").remove()

    def _isprotected(self, directory):
        """See if container or image tag are protected"""
        return os.path.exists(directory + "/PROTECT")

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

    def _symlink(self, existing_file, link_file):
        """Create relative symbolic links"""
        if os.path.exists(link_file):
            return False
        rel_path_to_existing = os.path.relpath(
            existing_file, os.path.dirname(link_file))
        try:
            os.symlink(rel_path_to_existing, link_file)
        except (IOError, OSError):
            return False
        return True

    def _name_is_valid(self, name):
        """Check name alias validity"""
        invalid_chars = ("/", ".", " ", "[", "]")
        if name and any(x in name for x in invalid_chars):
            return False
        return not len(name) > 2048

    def set_container_name(self, container_id, name):
        """Associates a name to a container id The container can
        then be referenced either by its id or by its name.
        """
        if self._name_is_valid(name):
            container_dir = self.cd_container(container_id)
            if container_dir:
                linkname = self.containersdir + "/" + name
                if os.path.exists(linkname):
                    return False
                return self._symlink(container_dir, linkname)
        return False

    def del_container_name(self, name):
        """Remove a name previously associated to a container"""
        if self._name_is_valid(name):
            linkname = self.containersdir + "/" + name
            if os.path.exists(linkname):
                return FileUtil(linkname).remove()
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

    def _find(self, filename, in_dir):
        """is a specific layer filename referenced by another image TAG"""
        found_list = []
        if FileUtil(in_dir).isdir():
            for fullname in os.listdir(in_dir):
                f_path = in_dir + "/" + fullname
                if os.path.islink(f_path):
                    if filename in fullname:       # match .layer or .json
                        found_list.append(f_path)  # found reference to layer
                elif os.path.isdir(f_path):
                    found_list.extend(self._find(filename, f_path))
        return found_list

    def _inrepository(self, filename):
        """Check if a given file is in the repository"""
        return self._find(filename, self.reposdir)

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
            FileUtil(linkname).remove()
        self._symlink(filename, linkname)
        return True

    def setup_imagerepo(self, imagerepo):
        """Create directory for an image repository"""
        if not imagerepo:
            return None
        directory = self.reposdir + "/" + imagerepo
        try:
            if not os.path.exists(directory):
                os.makedirs(directory)
                self.cur_repodir = directory
                return True
            else:
                self.cur_repodir = directory
                return False
        except (IOError, OSError):
            return None

    def setup_tag(self, tag):
        """Create directory structure for an image TAG
        to be invoked after setup_imagerepo()
        """
        directory = self.cur_repodir + "/" + tag
        try:
            if not os.path.exists(directory):
                os.makedirs(directory)
            self.cur_tagdir = directory
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
                    FileUtil(directory + "/v1").remove()
                    FileUtil(directory + "/v2").remove()
                except (IOError, OSError):
                    pass
                if os.listdir(directory):
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
            if manifest and manifest["fsLayers"]:
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
                        Msg().err("Warning: unkwnon file in layer:", f_path,
                                  l=Msg.WAR)
                elif fname in ("TAG", "v1", "v2", "PROTECT"):
                    pass
                else:
                    Msg().err("Warning: unkwnon file in image:", f_path,
                              l=Msg.WAR)
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

    def _verify_layer_file(self, structure, layer_id):
        """Verify layer file in repository"""
        layer_f = structure["layers"][layer_id]["layer_f"]
        if not (os.path.exists(layer_f) and
                os.path.islink(layer_f)):
            Msg().err("Error: layer data file symbolic link not found",
                      layer_id)
            return False
        if not os.path.exists(self.cur_tagdir + "/" +
                              os.readlink(layer_f)):
            Msg().err("Error: layer data file not found")
            return False
        if not FileUtil(layer_f).verify_tar():
            Msg().err("Error: layer file not ok:", layer_f)
            return False
        match = re.search("/sha256:(\\S+)$", layer_f)
        if match:
            layer_f_chksum = ChkSUM().sha256(layer_f)
            if layer_f_chksum != match.group(1):
                Msg().err("Error: layer file chksum error:", layer_f)
                return False
        return True

    def verify_image(self):
        """Verify the structure of an image repository"""
        Msg().out("Info: loading structure", l=Msg.INF)
        structure = self._load_structure(self.cur_tagdir)
        if not structure:
            Msg().err("Error: load of image tag structure failed")
            return False
        Msg().out("Info: finding top layer id", l=Msg.INF)
        top_layer_id = self._find_top_layer_id(structure)
        if not top_layer_id:
            Msg().err("Error: finding top layer id")
            return False
        Msg().out("Info: sorting layers", l=Msg.INF)
        layers_list = self._sorted_layers(structure, top_layer_id)
        status = True
        if "ancestry" in structure:
            layer = iter(layers_list)
            for ancestry_layer in structure["ancestry"]:
                verify_layer = layer.next()
                if ancestry_layer != verify_layer:
                    Msg().err("Error: ancestry and layers do not match",
                              ancestry_layer, verify_layer)
                    status = False
                    continue
        elif "manifest" in structure:
            for manifest_layer in structure["manifest"]["fsLayers"]:
                if manifest_layer["blobSum"] not in structure["layers"]:
                    Msg().err("Error: layer in manifest does not exist",
                              " in repo", manifest_layer)
                    status = False
                    continue
        for layer_id in structure["layers"]:
            if "layer_f" not in structure["layers"][layer_id]:
                Msg().err("Error: layer file not found in structure",
                          layer_id)
                status = False
                continue
            layer_status = self._verify_layer_file(structure, layer_id)
            if not layer_status:
                status = False
                continue
            Msg().out("Info: layer ok:", layer_id, l=Msg.INF)
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
        return None

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
        self.timeout = Config.timeout
        self.ctimeout = Config.ctimeout
        self.download_timeout = Config.download_timeout
        self.agent = Config.http_agent
        self.http_proxy = Config.http_proxy
        self.cache_support = False
        self.insecure = Config.http_insecure
        self._curl_executable = Config.use_curl_executable
        self._select_implementation()

    # pylint: disable=locally-disabled
    def _select_implementation(self):
        """Select which implementation to use"""
        if GetURLpyCurl().is_available() and not self._curl_executable:
            self._geturl = GetURLpyCurl()
            self.cache_support = True
        elif GetURLexeCurl().is_available():
            self._geturl = GetURLexeCurl()
        else:
            Msg().err("Error: need curl or pycurl to perform downloads")
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
        self._geturl.insecure = bool_value

    def set_proxy(self, http_proxy):
        """Specify a socks http proxy"""
        self.http_proxy = http_proxy
        self._geturl.http_proxy = http_proxy

    def get(self, *args, **kwargs):
        """Get URL using selected implementation
        Example:
            get(url, ctimeout=5, timeout=5, header=[]):
        """
        if len(args) != 1:
            raise TypeError('wrong number of arguments')
        return self._geturl.get(*args, **kwargs)

    def post(self, *args, **kwargs):
        """POST using selected implementation"""
        if len(args) != 2:
            raise TypeError('wrong number of arguments')
        kwargs["post"] = args[1]
        return self._geturl.get(args[0], **kwargs)

    def _get_status_code(self, status_line):
        """
        get http status code from http status line.
        Status-Line = HTTP-Version SP Status-Code SP Reason-Phrase CRLF
        """
        parts = status_line.split(" ")
        try:
            return int(parts[1])
        except ValueError:
            return 400


class GetURLpyCurl(GetURL):
    """Downloader implementation using PyCurl"""

    def __init__(self):
        GetURL.__init__(self)
        self._url = None

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
        if self.insecure:
            pyc.setopt(pyc.SSL_VERIFYPEER, 0)
            pyc.setopt(pyc.SSL_VERIFYHOST, 0)
        pyc.setopt(pyc.FOLLOWLOCATION, False)
        pyc.setopt(pyc.FAILONERROR, False)
        pyc.setopt(pyc.NOPROGRESS, True)
        pyc.setopt(pyc.HEADERFUNCTION, hdr.write)
        pyc.setopt(pyc.USERAGENT, self.agent)
        pyc.setopt(pyc.CONNECTTIMEOUT, self.ctimeout)
        pyc.setopt(pyc.TIMEOUT, self.timeout)
        pyc.setopt(pyc.PROXY, self.http_proxy)
        if Msg.level >= Msg.DBG:
            pyc.setopt(pyc.VERBOSE, True)
        else:
            pyc.setopt(pyc.VERBOSE, False)
        self._url = ""

    def _mkpycurl(self, pyc, hdr, buf, *args, **kwargs):
        """Prepare curl command line according to invocation options"""
        self._url = str(args[0])
        pyc.setopt(pycurl.URL, self._url)
        if "post" in kwargs:
            pyc.setopt(pyc.POST, 1)
            pyc.setopt(pyc.HTTPHEADER, ['Content-Type: application/json'])
            pyc.setopt(pyc.POSTFIELDS, json.dumps(kwargs["post"]))
        if "sizeonly" in kwargs:
            hdr.sizeonly = True
        if "proxy" in kwargs and kwargs["proxy"]:
            pyc.setopt(pyc.PROXY, pyc.USERAGENT, kwargs["proxy"])
        if "ctimeout" in kwargs:
            pyc.setopt(pyc.CONNECTTIMEOUT, kwargs["ctimeout"])
        if "header" in kwargs:  # avoid known pycurl bug
            clean_header_list = []
            for header_item in kwargs["header"]:
                if str(header_item).startswith("Authorization: Bearer"):
                    if "Signature=" in self._url:
                        continue
                    if "redirect" in kwargs:
                        continue
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
                Msg().err("Error: opening download file: %s" % output_file)
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
        cont_redirs = 0
        max_redirs = 10
        status_code = 302
        while status_code >= 300 and status_code <= 308 and cont_redirs < max_redirs:
            cont_redirs += 1
            hdr = CurlHeader()
            buf = cStringIO.StringIO()
            pyc = pycurl.Curl()
            self._set_defaults(pyc, hdr)
            try:
                (output_file, filep) = self._mkpycurl(pyc, hdr, buf, *args, **kwargs)
                Msg().err("curl url: ", self._url, l=Msg.DBG)
                Msg().err("curl arg: ", kwargs, l=Msg.DBG)
                pyc.perform()     # call pyculr
            except(IOError, OSError):
                return(None, None)
            except pycurl.error as error:
                errno, errstr = error
                hdr.data["X-ND-CURLSTATUS"] = errno
                if not hdr.data["X-ND-HTTPSTATUS"]:
                    hdr.data["X-ND-HTTPSTATUS"] = errstr
            status_code = self._get_status_code(hdr.data["X-ND-HTTPSTATUS"])
            if status_code >= 300 and status_code <= 308:
                args = (hdr.data['location'],)
                kwargs["redirect"] = True

        if "header" in kwargs:
            hdr.data["X-ND-HEADERS"] = kwargs["header"]
        if "ofile" in kwargs:
            filep.close()
            if status_code == 401:  # needs authentication
                pass
            elif status_code == 206 and "resume" in kwargs:
                pass
            elif status_code == 416 and "resume" in kwargs:
                kwargs["resume"] = False
                (hdr, buf) = self.get(self._url, **kwargs)
            elif status_code != 200:
                Msg().err("Error: in download: " + str(
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
            "other": "-s -q -S"
        }
        if self.insecure:
            self._opts["insecure"] = "-k"
        if Msg().level > Msg.DBG:
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
        if "post" in kwargs:
            self._opts["post"] = "-X POST -H Content-Type: application/json' "
            self._opts["post"] += "-d '%s'" % (json.dumps(kwargs["post"]))
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
                if str(header_item).startswith("Authorization: Bearer"):
                    if "Signature=" in self._files["url"]:
                        continue
                    if "redirect" in kwargs:
                        continue
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
        curl_executable = "curl"
        if self._curl_executable and isinstance(self._curl_executable, str):
            curl_executable = self._curl_executable
        return(curl_executable + " " + " ".join(self._opts.values()) +
               " -D %s -o %s --stderr %s '%s'" %
               (self._files["header_file"], self._files["output_file"],
                self._files["error_file"], self._files["url"]))

    def get(self, *args, **kwargs):
        """http get implementation using the curl cli executable"""
        cont_redirs = 0
        max_redirs = 10
        status_code = 302
        while status_code >= 300 and status_code <= 308 and cont_redirs < max_redirs:
            cont_redirs += 1
            hdr = CurlHeader()
            buf = cStringIO.StringIO()
            self._set_defaults()
            cmd = self._mkcurlcmd(*args, **kwargs)
            status = subprocess.call(cmd, shell=True, close_fds=True) # call curl
            hdr.setvalue_from_file(self._files["header_file"])
            hdr.data["X-ND-CURLSTATUS"] = status
            if status:
                Msg().err("Error: in download: %s"
                          % str(FileUtil(self._files["error_file"]).getdata()))
                FileUtil(self._files["output_file"]).remove()
                return(hdr, buf)
            status_code = self._get_status_code(hdr.data["X-ND-HTTPSTATUS"])
            if status_code >= 300 and status_code <= 308:
                args = (hdr.data['location'],)
                kwargs["redirect"] = True

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
                Msg().err("Error: in download: ", str(
                    hdr.data["X-ND-HTTPSTATUS"]), ": ", str(status))
                FileUtil(self._files["output_file"]).remove()
            else:  # OK downloaded
                os.rename(self._files["output_file"], kwargs["ofile"])
        else:
            try:
                buf = cStringIO.StringIO(open(self._files["output_file"],
                                              "r").read())
            except(IOError, OSError):
                Msg().err("Error: reading curl output file to buffer")
            FileUtil(self._files["output_file"]).remove()
        FileUtil(self._files["error_file"]).remove()
        FileUtil(self._files["header_file"]).remove()
        return(hdr, buf)


class DockerIoAPI(object):
    """Class to encapsulate the access to the Docker Hub service
    Allows to search and download images from Docker Hub
    """

    def __init__(self, localrepo):
        self.index_url = Config.dockerio_index_url
        self.registry_url = Config.dockerio_registry_url
        self.v1_auth_header = ""
        self.v2_auth_header = ""
        self.v2_auth_token = ""
        self.localrepo = localrepo
        self.curl = GetURL()
        self.docker_registry_domain = "docker.io"
        self.search_link = ""
        self.search_pause = True
        self.search_page = 0
        self.search_lines = 25
        self.search_link = ""
        self.search_ended = False

    def set_proxy(self, http_proxy):
        """Select a socks http proxy for API access and file download"""
        self.curl.set_proxy(http_proxy)

    def set_registry(self, registry_url):
        """Change docker registry url"""
        self.registry_url = registry_url

    def set_index(self, index_url):
        """Change docker index url"""
        self.index_url = index_url

    def is_repo_name(self, imagerepo):
        """Check if name matches authorized characters for a docker repo"""
        if imagerepo and re.match("^[a-zA-Z0-9][a-zA-Z0-9-_./:]+$", imagerepo):
            return True
        Msg().err("Error: invalid repo name syntax")
        return False

    def _is_docker_registry(self):
        """Check if registry is dockerhub"""
        regexp = r"%s(\:\d+)?(\/)?$" % (self.docker_registry_domain)
        return re.search(regexp, self.registry_url)

    def _get_url(self, *args, **kwargs):
        """Encapsulates the call to GetURL.get() so that authentication
        for v1 and v2 repositories can be treated differently.
        Example:
             _get_url(url, ctimeout=5, timeout=5, header=[]):
        """
        url = str(args[0])
        if "RETRY" not in kwargs:
            kwargs["RETRY"] = 3
        kwargs["RETRY"] -= 1
        (hdr, buf) = self.curl.get(*args, **kwargs)
        Msg().err("header: %s" % (hdr.data), l=Msg.DBG)
        if ("X-ND-HTTPSTATUS" in hdr.data and
                "401" in hdr.data["X-ND-HTTPSTATUS"]):
            if "www-authenticate" in hdr.data and hdr.data["www-authenticate"]:
                if "RETRY" in kwargs and kwargs["RETRY"]:
                    auth_header = ""
                    if "/v2/" in url:
                        auth_header = self._get_v2_auth(
                            hdr.data["www-authenticate"], kwargs["RETRY"])
                    elif "/v1/" in url:
                        auth_header = self._get_v1_auth(
                            hdr.data["www-authenticate"])
                    auth_kwargs = kwargs.copy()
                    auth_kwargs.update({"header": [auth_header]})
                    if "location" in hdr.data and hdr.data['location']:
                        args = hdr.data['location']
                    (hdr, buf) = self._get_url(*args, **auth_kwargs)
                else:
                    hdr.data["X-ND-CURLSTATUS"] = 13  # Permission denied
        return(hdr, buf)

    def _get_file(self, url, filename, cache_mode):
        """Get a file and check its size. Optionally enable other
        capabilities such as caching to check if the
        file already exists locally and whether its size is the
        same to avoid downloaded it again.
        """
        match = re.search("/sha256:(\\S+)$", filename)
        if match:
            layer_f_chksum = ChkSUM().sha256(filename)
            if layer_f_chksum == match.group(1):
                return True             # is cached skip download
            else:
                cache_mode = 0
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
            Msg().err("Error: file size mismatch:", filename,
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

    def get_v1_repo(self, imagerepo):
        """Get list of images in a repo from Docker Hub"""
        url = self.index_url + "/v1/repositories/" + imagerepo + "/images"
        Msg().err("repo url:", url, l=Msg.DBG)
        (hdr, buf) = self._get_url(url, header=["X-Docker-Token: true"])
        try:
            self.v1_auth_header = "Authorization: Token " + \
                hdr.data["x-docker-token"]
            return hdr.data, json.loads(buf.getvalue())
        except (IOError, OSError, AttributeError,
                ValueError, TypeError, KeyError):
            self.v1_auth_header = ""
            return hdr.data, []

    def _get_v1_auth(self, www_authenticate):
        """Authentication for v1 API"""
        if "Token" in www_authenticate:
            return self.v1_auth_header
        return ""

    def get_v1_image_tags(self, endpoint, imagerepo):
        """Get list of tags in a repo from Docker Hub"""
        url = endpoint + "/v1/repositories/" + imagerepo + "/tags"
        Msg().err("tags url:", url, l=Msg.DBG)
        (hdr, buf) = self._get_url(url)
        try:
            return(hdr.data, json.loads(buf.getvalue()))
        except (IOError, OSError, AttributeError, ValueError, TypeError):
            return(hdr.data, [])

    def get_v1_image_tag(self, endpoint, imagerepo, tag):
        """Get list of tags in a repo from Docker Hub"""
        url = endpoint + "/v1/repositories/" + imagerepo + "/tags/" + tag
        Msg().err("tags url:", url, l=Msg.DBG)
        (hdr, buf) = self._get_url(url)
        try:
            return(hdr.data, json.loads(buf.getvalue()))
        except (IOError, OSError, AttributeError, ValueError, TypeError):
            return(hdr.data, [])

    def get_v1_image_ancestry(self, endpoint, image_id):
        """Get the ancestry which is an ordered list of layers"""
        url = endpoint + "/v1/images/" + image_id + "/ancestry"
        Msg().err("ancestry url:", url, l=Msg.DBG)
        (hdr, buf) = self._get_url(url)
        try:
            return(hdr.data, json.loads(buf.getvalue()))
        except (IOError, OSError, AttributeError, ValueError, TypeError):
            return(hdr.data, [])

    def get_v1_image_json(self, endpoint, layer_id):
        """Get the JSON metadata for a specific layer"""
        url = endpoint + "/v1/images/" + layer_id + "/json"
        Msg().err("json url:", url, l=Msg.DBG)
        filename = self.localrepo.layersdir + "/" + layer_id + ".json"
        if self._get_file(url, filename, 0):
            self.localrepo.add_image_layer(filename)
            return True
        return False

    def get_v1_image_layer(self, endpoint, layer_id):
        """Get a specific layer data file (layer files are tarballs)"""
        url = endpoint + "/v1/images/" + layer_id + "/layer"
        Msg().err("layer url:", url, l=Msg.DBG)
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
                Msg().err("Downloading layer:", layer_id, l=Msg.INF)
                filesize = self.get_v1_image_json(endpoint, layer_id)
                if not filesize:
                    return []
                files.append(layer_id + ".json")
                filesize = self.get_v1_image_layer(endpoint, layer_id)
                if not filesize:
                    return []
                files.append(layer_id + ".layer")
        return files

    def _get_v2_auth(self, www_authenticate, retry):
        """Authentication for v2 API"""
        auth_header = ""
        (bearer, auth_data) = www_authenticate.rsplit(" ", 1)
        if bearer == "Bearer":
            auth_fields = self._split_fields(auth_data)
            if "realm" in auth_fields:
                auth_url = auth_fields["realm"] + "?"
                for field in auth_fields:
                    if field != "realm":
                        auth_url += field + "=" + auth_fields[field] + "&"
                header = []
                if self.v2_auth_token:
                    header = ["Authorization: Basic %s" % (self.v2_auth_token)]
                (dummy, auth_buf) = self._get_url(auth_url, header=header, RETRY=retry)
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
        # PR #126
        elif 'BASIC' in bearer or 'Basic' in bearer:
            auth_header = "Authorization: Basic %s" %(self.v2_auth_token)
            self.v2_auth_header = auth_header
        return auth_header

    def get_v2_login_token(self, username, password):
        """Get a login token from username and password"""
        if not (username and password):
            return ""
        try:
            self.v2_auth_token = \
                base64.b64encode("%s:%s" % (username, password))
        except (KeyError, AttributeError, TypeError, ValueError, NameError):
            self.v2_auth_token = ""
        return self.v2_auth_token

    def set_v2_login_token(self, v2_auth_token):
        """Load previously created login token"""
        self.v2_auth_token = v2_auth_token

    def is_v2(self):
        """Check if registry is of type v2"""
        (hdr, dummy) = self._get_url(self.registry_url + "/v2/")
        try:
            if ("200" in hdr.data["X-ND-HTTPSTATUS"] or
                    "401" in hdr.data["X-ND-HTTPSTATUS"]):
                return True
        except (KeyError, AttributeError, TypeError):
            pass
        return False

    def get_v2_image_manifest(self, imagerepo, tag):
        """Get the image manifest which contains JSON metadata
        that is common to all layers in this image tag
        """
        if self._is_docker_registry() and "/" not in imagerepo:
            url = self.registry_url + "/v2/library/" + \
                imagerepo + "/manifests/" + tag
        else:
            url = self.registry_url + "/v2/" + imagerepo + \
                "/manifests/" + tag
        Msg().err("manifest url:", url, l=Msg.DBG)
        (hdr, buf) = self._get_url(url)
        try:
            return(hdr.data, json.loads(buf.getvalue()))
        except (IOError, OSError, AttributeError, ValueError, TypeError):
            return(hdr.data, [])

    def get_v2_image_layer(self, imagerepo, layer_id):
        """Get one image layer data file (tarball)"""
        if self._is_docker_registry() and "/" not in imagerepo:
            url = self.registry_url + "/v2/library/" + \
                imagerepo + "/blobs/" + layer_id
        else:
            url = self.registry_url + "/v2/" + imagerepo + \
                "/blobs/" + layer_id
        Msg().err("layer url:", url, l=Msg.DBG)
        filename = self.localrepo.layersdir + "/" + layer_id
        if self._get_file(url, filename, 3):
            self.localrepo.add_image_layer(filename)
            return True
        return False

    def get_v2_layers_all(self, imagerepo, fslayers):
        """Get all layer data files belonging to a image tag"""
        files = []
        if fslayers:
            for layer in reversed(fslayers):
                Msg().err("Downloading layer:", layer["blobSum"],
                          l=Msg.INF)
                if not self.get_v2_image_layer(imagerepo, layer["blobSum"]):
                    return []
                files.append(layer["blobSum"])
        return files

    def get_v2(self, imagerepo, tag):
        """Pull container with v2 API"""
        files = []
        (dummy, manifest) = self.get_v2_image_manifest(imagerepo, tag)
        try:
            if not (self.localrepo.setup_tag(tag) and
                    self.localrepo.set_version("v2")):
                Msg().err("Error: setting localrepo v2 tag and version")
                return []
            self.localrepo.save_json("manifest", manifest)
            Msg().err("v2 layers: %s" % (imagerepo), l=Msg.DBG)
            files = self.get_v2_layers_all(imagerepo,
                                           manifest["fsLayers"])
        except (KeyError, AttributeError, IndexError, ValueError, TypeError):
            pass
        return files

    def _get_v1_id_from_tags(self, tags_obj, tag):
        """Get image id from array of tags"""
        if isinstance(tags_obj, dict):
            try:
                return tags_obj[tag]
            except KeyError:
                pass
        elif isinstance(tags_obj, []):
            try:
                for tag_dict in tags_obj:
                    if tag_dict["name"] == tag:
                        return tag_dict["layer"]
            except KeyError:
                pass
        return ""

    def _get_v1_id_from_images(self, images_array, short_id):
        """Get long image id from array of images using the short id"""
        try:
            for image_dict in images_array:
                if image_dict["id"][0:8] == short_id:
                    return image_dict["id"]
        except KeyError:
            pass
        return ""

    def get_v1(self, imagerepo, tag):
        """Pull container with v1 API"""
        Msg().err("v1 image id: %s" % (imagerepo), l=Msg.DBG)
        (hdr, images_array) = self.get_v1_repo(imagerepo)
        if not images_array:
            Msg().err("Error: image not found")
            return []
        try:
            endpoint = "http://" + hdr["x-docker-endpoints"]
        except KeyError:
            endpoint = self.index_url
        (dummy, tags_array) = self.get_v1_image_tags(endpoint, imagerepo)
        image_id = self._get_v1_id_from_tags(tags_array, tag)
        if not image_id:
            Msg().err("Error: image tag not found")
            return []
        if len(image_id) <= 8:
            image_id = self._get_v1_id_from_images(images_array, image_id)
            if not image_id:
                Msg().err("Error: image id not found")
                return []
        if not (self.localrepo.setup_tag(tag) and
                self.localrepo.set_version("v1")):
            Msg().err("Error: setting localrepo v1 tag and version")
            return []
        Msg().err("v1 ancestry: %s" % image_id, l=Msg.DBG)
        (dummy, ancestry) = self.get_v1_image_ancestry(endpoint, image_id)
        if not ancestry:
            Msg().err("Error: ancestry not found")
            return []
        self.localrepo.save_json("ancestry", ancestry)
        Msg().err("v1 layers: %s" % image_id, l=Msg.DBG)
        files = self.get_v1_layers_all(endpoint, ancestry)
        return files

    def _parse_imagerepo(self, imagerepo):
        """Parse imagerepo to extract registry"""
        remoterepo = imagerepo
        registry = ""
        registry_url = ""
        index_url = ""
        components = imagerepo.split("/")
        if '.' in components[0] and len(components) >= 2:
            registry = components[0]
            if components[1] == "library":
                remoterepo = "/".join(components[2:])
                del components[1]
                imagerepo = "/".join(components)
            else:
                remoterepo = "/".join(components[1:])
        else:
            if components[0] == "library" and len(components) >= 1:
                del components[0]
                remoterepo = "/".join(components)
                imagerepo = "/".join(components)
        if registry:
            try:
                registry_url = Config.docker_registries[registry][0]
                index_url = Config.docker_registries[registry][1]
            except (KeyError, NameError, TypeError):
                registry_url = "https://%s" % registry
                index_url = registry_url
            if registry_url:
                self.registry_url = registry_url
            if index_url:
                self.index_url = index_url
        return (imagerepo, remoterepo)

    def get(self, imagerepo, tag):
        """Pull a docker image from a v2 registry or v1 index"""
        Msg().err("get imagerepo: %s tag: %s" % (imagerepo, tag), l=Msg.DBG)
        (imagerepo, remoterepo) = self._parse_imagerepo(imagerepo)
        if self.localrepo.cd_imagerepo(imagerepo, tag):
            new_repo = False
        else:
            self.localrepo.setup_imagerepo(imagerepo)
            new_repo = True
        if self.is_v2():
            files = self.get_v2(remoterepo, tag)  # try v2
        else:
            files = self.get_v1(remoterepo, tag)  # try v1
        if new_repo and not files:
            self.localrepo.del_imagerepo(imagerepo, tag, False)
        return files

    def search_init(self, pause):
        """Setup new search"""
        self.search_pause = pause
        self.search_page = 0
        self.search_link = ""
        self.search_ended = False

    def search_get_page_v1(self, expression):
        """Get search results from Docker Hub using v1 API"""
        if expression:
            url = self.index_url + "/v1/search?q=" + expression
        else:
            url = self.index_url + "/v1/search?"
        url += "&page=" + str(self.search_page)
        (dummy, buf) = self._get_url(url)
        try:
            repo_list = json.loads(buf.getvalue())
            if repo_list["page"] == repo_list["num_pages"]:
                self.search_ended = True
            return repo_list
        except (IOError, OSError, AttributeError,
                ValueError, TypeError):
            self.search_ended = True
            return []

    def catalog_get_page_v2(self, lines):
        """Get search results from Docker Hub using v2 API"""
        url = self.registry_url + "/v2/_catalog"
        if self.search_pause:
            if self.search_page == 1:
                url += "?n=" + str(lines)
            else:
                url = self.registry_url + self.search_link
        (hdr, buf) = self._get_url(url)
        try:
            match = re.search(r"\<([^>]+)\>", hdr.data["link"])
            if match:
                self.search_link = match.group(1)
        except (AttributeError, NameError, KeyError):
            self.search_ended = True
        try:
            return json.loads(buf.getvalue())
        except (IOError, OSError, AttributeError,
                ValueError, TypeError):
            self.search_ended = True
            return []

    def search_get_page(self, expression):
        """Get search results from Docker Hub"""
        if self.search_ended:
            return []
        else:
            self.search_page += 1
        if self.is_v2() and not self._is_docker_registry():
            return self.catalog_get_page_v2(self.search_lines)
        return self.search_get_page_v1(expression)


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
                elif fname == "manifest.json":
                    pass
                elif len(fname) == 69 and fname.endswith(".json"):
                    pass
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
                            Msg().err("Warning: unkwnon file in layer:",
                                      f_path, l=Msg.WAR)
                else:
                    Msg().err("Warning: unkwnon file in image:", f_path,
                              l=Msg.WAR)
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
            Msg().err("Error: repository and tag already exist",
                      imagerepo, tag)
            return []
        else:
            self.localrepo.setup_imagerepo(imagerepo)
            tag_dir = self.localrepo.setup_tag(tag)
            if not tag_dir:
                Msg().err("Error: setting up repository", imagerepo, tag)
                return []
            if not self.localrepo.set_version("v1"):
                Msg().err("Error: setting repository version")
                return []
            try:
                top_layer_id = structure["repositories"][imagerepo][tag]
            except (IndexError, NameError, KeyError):
                top_layer_id = self._find_top_layer_id(structure)
            for layer_id in self._sorted_layers(structure, top_layer_id):
                if str(structure["layers"][layer_id]["VERSION"]) != "1.0":
                    Msg().err("Error: layer version unknown")
                    return []
                for layer_item in ("json_f", "layer_f"):
                    filename = str(structure["layers"][layer_id][layer_item])
                    if not self._copy_layer_to_repo(filename, layer_id):
                        Msg().err("Error: copying %s file %s"
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
        if Msg.level >= Msg.VER:
            cmd += " -v "
        cmd += " --one-file-system --no-same-owner "
        cmd += " --no-same-permissions --overwrite -f " + tarfile
        status = subprocess.call(cmd, shell=True, stderr=Msg.chlderr,
                                 close_fds=True)
        return not status

    def load(self, imagefile):
        """Load a Docker file created with docker save, mimic Docker
        load. The file is a tarball containing several layers, each
        layer has metadata and data content (directory tree) stored
        as a tar file.
        """
        if not os.path.exists(imagefile) and imagefile != "-":
            Msg().err("Error: image file does not exist:", imagefile)
            return False
        tmp_imagedir = FileUtil("import").mktmp()
        try:
            os.makedirs(tmp_imagedir)
        except (IOError, OSError):
            return False
        if not self._untar_saved_container(imagefile, tmp_imagedir):
            Msg().err("Error: failed to extract container:", imagefile)
            FileUtil(tmp_imagedir).remove()
            return False
        structure = self._load_structure(tmp_imagedir)
        if not structure:
            Msg().err("Error: failed to load image structure", imagefile)
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
        container_json["architecture"] = Config().arch()
        container_json["os"] = Config().osversion()
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

    def import_toimage(self, tarfile, imagerepo, tag, move_tarball=True):
        """Import a tar file containing a simple directory tree possibly
        created with Docker export and create local image"""
        if not os.path.exists(tarfile) and tarfile != "-":
            Msg().err("Error: tar file does not exist: ", tarfile)
            return False
        self.localrepo.setup_imagerepo(imagerepo)
        tag_dir = self.localrepo.cd_imagerepo(imagerepo, tag)
        if tag_dir:
            Msg().err("Error: tag already exists in repo:", tag)
            return False
        tag_dir = self.localrepo.setup_tag(tag)
        if not tag_dir:
            Msg().err("Error: creating repo and tag")
            return False
        if not self.localrepo.set_version("v1"):
            Msg().err("Error: setting repository version")
            return False
        layer_id = Unique().layer_v1()
        layer_file = self.localrepo.layersdir + "/" + layer_id + ".layer"
        json_file = self.localrepo.layersdir + "/" + layer_id + ".json"
        if move_tarball:
            try:
                os.rename(tarfile, layer_file)
            except(IOError, OSError):
                pass
        if not os.path.exists(layer_file):
            if not FileUtil(tarfile).copyto(layer_file):
                Msg().err("Error: in move/copy file", tarfile)
                return False
        self.localrepo.add_image_layer(layer_file)
        self.localrepo.save_json("ancestry", [layer_id])
        container_json = self.create_container_meta(layer_id)
        self.localrepo.save_json(json_file, container_json)
        self.localrepo.add_image_layer(json_file)
        Msg().out("Info: added layer", layer_id, l=Msg.INF)
        return layer_id

    def import_tocontainer(self, tarfile, imagerepo, tag, container_name):
        """Import a tar file containing a simple directory tree possibly
        created with Docker export and create local container ready to use"""
        if not imagerepo:
            imagerepo = "IMPORTED"
            tag = "latest"
        if not os.path.exists(tarfile) and tarfile != "-":
            Msg().err("Error: tar file does not exist:", tarfile)
            return False
        if container_name:
            if self.localrepo.get_container_id(container_name):
                Msg().err("Error: container name already exists:",
                          container_name)
                return False
        layer_id = Unique().layer_v1()
        container_json = self.create_container_meta(layer_id)
        container_id = ContainerStructure(self.localrepo).create_fromlayer(
            imagerepo, tag, tarfile, container_json)
        if container_name:
            self.localrepo.set_container_name(container_id, container_name)
        return container_id

    def import_clone(self, tarfile, container_name):
        """Import a tar file containing a clone of a udocker container
        created with export --clone and create local cloned container
        ready to use
        """
        if not os.path.exists(tarfile) and tarfile != "-":
            Msg().err("Error: tar file does not exist:", tarfile)
            return False
        if container_name:
            if self.localrepo.get_container_id(container_name):
                Msg().err("Error: container name already exists:",
                          container_name)
                return False
        container_id = ContainerStructure(self.localrepo).clone_fromfile(
            tarfile)
        if container_name:
            self.localrepo.set_container_name(container_id, container_name)
        return container_id

    def clone_container(self, container_id, container_name):
        """Clone/duplicate an existing container creating a complete
        copy including metadata, control files, and rootfs, The copy
        will have a new id.
        """
        if container_name:
            if self.localrepo.get_container_id(container_name):
                Msg().err("Error: container name already exists:",
                          container_name)
                return False
        dest_container_id = ContainerStructure(self.localrepo,
                                               container_id).clone()
        if container_name:
            self.localrepo.set_container_name(dest_container_id,
                                              container_name)
        exec_mode = ExecutionMode(self.localrepo, dest_container_id)
        xmode = exec_mode.get_mode()
        if xmode.startswith("F"):
            exec_mode.set_mode(xmode, True)
        return dest_container_id


class Udocker(object):
    """Implements most of the command line interface.
    These methods correspond directly to the commands that can
    be invoked via the command line interface.
    """

    def __init__(self, localrepo):
        self.localrepo = localrepo
        self.dockerioapi = DockerIoAPI(localrepo)
        self.dockerlocalfileapi = DockerLocalFileAPI(localrepo)
        if Config.keystore.startswith("/"):
            self.keystore = KeyStore(Config.keystore)
        else:
            self.keystore = \
                KeyStore(self.localrepo.homedir + "/" + Config.keystore)

    def _cdrepo(self, cmdp):
        """Select the top directory of a local repository"""
        topdir = cmdp.get("P1")
        if cmdp.missing_options():               # syntax error
            return False
        if not FileUtil(topdir).isdir():
            Msg().err("Warning: localrepo directory is invalid: ", topdir,
                      l=Msg.WAR)
            return False
        self.localrepo.setup(topdir)
        return True

    def _check_imagespec(self, imagespec, def_imagespec=None):
        """Perform the image verification"""
        if (not imagespec) and def_imagespec:
            imagespec = def_imagespec
        try:
            (imagerepo, tag) = imagespec.rsplit(":", 1)
        except (ValueError, AttributeError):
            imagerepo = imagespec
            tag = "latest"
        if not (imagerepo and tag and
                self.dockerioapi.is_repo_name(imagespec)):
            Msg().err("Error: must specify image:tag or repository/image:tag")
            return(None, None)
        return imagerepo, tag

    def do_mkrepo(self, cmdp):
        """
        mkrepo: create a local repository in a specified directory
        mkrepo <directory>
        """
        topdir = cmdp.get("P1")
        if not topdir or not os.path.exists(topdir):
            self.localrepo.setup(topdir)
            if self.localrepo.create_repo():
                return True
            else:
                Msg().err("Error: localrepo creation failure: ", topdir)
                return False
        else:
            Msg().err("Error: localrepo directory already exists: ", topdir)
            return False

    def _search_print_v1(self, repo_list):
        """Print search results from v1 API"""
        for repo in repo_list["results"]:
            if "is_official" in repo and repo["is_official"]:
                is_official = "[OK]"
            else:
                is_official = "----"
            description = ""
            if "description" in repo and repo["description"] is not None:
                for char in repo["description"]:
                    if char in string.printable:
                        description += char
            Msg().out("%-40.40s %8.8s %s"
                      % (repo["name"], is_official, description))

    def _search_print_v2(self, repo_list):
        """Print catalog results from v2 API"""
        for reponame in repo_list["repositories"]:
            Msg().out("%-40.40s %8.8s"
                      % (reponame, "    "))

    def do_search(self, cmdp):
        """
        search: search dockerhub for container images
        search [options]  <expression>
        -a                                              :do not pause
        --index=https://index.docker.io/v1              :docker index
        --registry=https://registry-1.docker.io         :docker registry
        """
        pause = not cmdp.get("-a")
        index_url = cmdp.get("--index=")
        registry_url = cmdp.get("--registry=")
        expression = cmdp.get("P1")
        if index_url:
            self.dockerioapi.set_index(index_url)
        if registry_url:
            self.dockerioapi.set_registry(registry_url)
        if cmdp.missing_options():               # syntax error
            return False
        Msg().out("%-40.40s %8.8s %s" %
                  ("NAME", "OFFICIAL", "DESCRIPTION"), l=Msg.INF)
        self.dockerioapi.search_init(pause)
        v2_auth_token = self.keystore.get(self.dockerioapi.registry_url)
        self.dockerioapi.set_v2_login_token(v2_auth_token)
        while True:
            repo_list = self.dockerioapi.search_get_page(expression)
            if not repo_list:
                return True
            elif "results" in repo_list:
                self._search_print_v1(repo_list)
            elif "repositories" in repo_list:
                self._search_print_v2(repo_list)
            if pause and not self.dockerioapi.search_ended:
                key_press = raw_input("[press return or q to quit]")
                if key_press in ("q", "Q", "e", "E"):
                    return True

    def do_load(self, cmdp):
        """
        load: load a container image saved by docker with 'docker save'
        load --input=<docker-saved-container-file>
        load -i <docker-saved-container-file>
        load < <docker-saved-container-file>
        """
        imagefile = cmdp.get("--input=")
        if not imagefile:
            imagefile = cmdp.get("-i=")
            if imagefile is False:
                imagefile = "-"
        if cmdp.missing_options():  # syntax error
            return False
        if not imagefile:
            Msg().err("Error: must specify filename of docker exported image")
            return False
        repos = self.dockerlocalfileapi.load(imagefile)
        if not repos:
            Msg().err("Error: loading failed")
            return False
        else:
            for repo_item in repos:
                Msg().out(repo_item)
            return True

    def do_import(self, cmdp):
        """
        import : import image (directory tree) from tar file or stdin
        import <tar-file> <repo/image:tag>
        import - <repo/image:tag>
        --mv                       :if possible move tar-file instead of copy
        --tocontainer              :import to container, no image is created
        --clone                    :import udocker container format with metadata
        --name=<container-name>    :with --tocontainer or --clone to add an alias
        """
        move_tarball = cmdp.get("--mv")
        to_container = cmdp.get("--tocontainer")
        name = cmdp.get("--name=")
        clone = cmdp.get("--clone")
        from_stdin = cmdp.get("-")
        if from_stdin:
            tarfile = "-"
            imagespec = cmdp.get("P1")
            move_tarball = False
        else:
            tarfile = cmdp.get("P1")
            imagespec = cmdp.get("P2")
        if not tarfile:
            Msg().err("Error: must specify tar filename")
            return False
        if cmdp.missing_options():  # syntax error
            return False
        if to_container or clone:
            if clone:
                container_id = self.dockerlocalfileapi.import_clone(
                    tarfile, name)
            else:
                (imagerepo, tag) = self._check_imagespec(imagespec,
                                                         "IMPORTED:unknown")
                container_id = self.dockerlocalfileapi.import_tocontainer(
                    tarfile, imagerepo, tag, name)
            if container_id:
                Msg().out(container_id)
                return True
        else:
            (imagerepo, tag) = self._check_imagespec(imagespec)
            if not imagerepo:
                return False
            if self.dockerlocalfileapi.import_toimage(tarfile, imagerepo, tag,
                                                      move_tarball):
                return True
        Msg().err("Error: importing")
        return False

    def do_export(self, cmdp):
        """
        export : export container (directory tree) to a tar file or stdin
        export -o <tar-file> <container-id>
        export - <container-id>
        -o                         :export to file, instead of stdout
        --clone                    :export in clone (udocker) format
        """
        to_file = cmdp.get("-o")
        clone = cmdp.get("--clone")
        if to_file:
            tarfile = cmdp.get("P1")
            container_id = cmdp.get("P2")
        else:
            tarfile = "-"
            container_id = cmdp.get("P1")
        container_id = self.localrepo.get_container_id(container_id)
        if not container_id:
            Msg().err("Error: invalid container id", container_id)
            return False
        if not tarfile:
            Msg().err("Error: invalid output file name", tarfile)
            return False
        if clone:
            if ContainerStructure(self.localrepo,
                                  container_id).clone_tofile(tarfile):
                return True
        else:
            if ContainerStructure(self.localrepo,
                                  container_id).export_tofile(tarfile):
                return True
        Msg().err("Error: exporting")
        return False

    def do_clone(self, cmdp):
        """
        clone : create a duplicate copy of an existing container
        clone <source-container-id>
        --name=<container-name>    :add an alias to the cloned container
        """
        name = cmdp.get("--name=")
        container_id = cmdp.get("P1")
        container_id = self.localrepo.get_container_id(container_id)
        if not container_id:
            Msg().err("Error: invalid container id", container_id)
            return False
        if self.dockerlocalfileapi.clone_container(container_id, name):
            Msg().out(container_id)
            return True
        Msg().err("Error: cloning")
        return False

    def do_login(self, cmdp):
        """
        login: authenticate into docker repository e.g. dockerhub
        --username=username
        --password=password
        --registry=https://registry-1.docker.io
        """
        username = cmdp.get("--username=")
        password = cmdp.get("--password=")
        registry_url = cmdp.get("--registry=")
        if registry_url:
            self.dockerioapi.set_registry(registry_url)
        if not username:
            username = raw_input("username: ")
        if not password:
            password = getpass("password: ")
        if password and password == password.upper():
            Msg().err("Warning: password in uppercase",
                      "Caps Lock ?", l=Msg.WAR)
        v2_auth_token = \
            self.dockerioapi.get_v2_login_token(username, password)
        if self.keystore.put(self.dockerioapi.registry_url, v2_auth_token, ""):
            return True
        Msg().err("Error: invalid credentials")
        return False

    def do_logout(self, cmdp):
        """
        logout: authenticate into docker repository e.g. dockerhub
        -a remove all authentication credentials
        --registry=https://registry-1.docker.io
        """
        all_credentials = cmdp.get("-a")
        registry_url = cmdp.get("--registry=")
        if registry_url:
            self.dockerioapi.set_registry(registry_url)
        if all_credentials:
            status = self.keystore.erase()
        else:
            status = self.keystore.delete(self.dockerioapi.registry_url)
        if not status:
            Msg().err("Error: deleting credentials")
        return status

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
        index_url = cmdp.get("--index=")
        registry_url = cmdp.get("--registry=")
        http_proxy = cmdp.get("--httpproxy=")
        (imagerepo, tag) = self._check_imagespec(cmdp.get("P1"))
        if not registry_url and self.keystore.get(imagerepo.split("/")[0]):
            registry_url = imagerepo.split("/")[0]
        if (not imagerepo) or cmdp.missing_options():    # syntax error
            return False
        else:
            if http_proxy:
                self.dockerioapi.set_proxy(http_proxy)
            if index_url:
                self.dockerioapi.set_index(index_url)
            if registry_url:
                self.dockerioapi.set_registry(registry_url)
            v2_auth_token = self.keystore.get(self.dockerioapi.registry_url)
            self.dockerioapi.set_v2_login_token(v2_auth_token)
            if self.dockerioapi.get(imagerepo, tag):
                return True
            else:
                Msg().err("Error: no files downloaded")
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
            Msg().out(container_id)
            if name and not self.localrepo.set_container_name(container_id,
                                                              name):
                Msg().err("Error: invalid container name may already exist "
                          "or wrong format")
                return False
            return True
        return False

    def _create(self, imagespec):
        """Auxiliary to create(), performs the creation"""
        if not self.dockerioapi.is_repo_name(imagespec):
            Msg().err("Error: must specify image:tag or repository/image:tag")
            return False
        (imagerepo, tag) = self._check_imagespec(imagespec)
        if imagerepo:
            return ContainerStructure(self.localrepo).create_fromimage(
                imagerepo, tag)
        return False

    def _get_run_options(self, cmdp, exec_engine=None):
        """Read command line options into variables"""
        cmdp.declare_options("-v= -e= -w= -u= -p= -i -t -a -P")
        cmd_options = {
            "netcoop": {
                "fl": ("-P", "--publish-all", "--netcoop",), "act": "R",
                "p2": "CMD_OPT", "p3": False
            },
            "portsmap": {
                "fl": ("-p=", "--publish=",), "act": "E",
                "p2": "CMD_OPT", "p3": True
            },
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
            },
            "devices": {
                "fl": ("--device=",), "act": "E",
                "p2": "CMD_OPT", "p3": True
            }
        }
        for option, cmdp_args in cmd_options.iteritems():
            last_value = None
            for cmdp_fl in cmdp_args["fl"]:
                option_value = cmdp.get(cmdp_fl,
                                        cmdp_args["p2"], cmdp_args["p3"])
                if not exec_engine:
                    continue
                if cmdp_args["act"] == "R":   # action is replace
                    if option_value or last_value is None:
                        exec_engine.opt[option] = option_value
                elif cmdp_args["act"] == "E":   # action is extend
                    exec_engine.opt[option].extend(option_value)
                last_value = option_value

    def do_run(self, cmdp):
        """
        run: execute a container
        run [options] <container-id-or-name>
        run [options] <repo/image:tag>
        --rm                       :delete container upon exit
        --workdir=/home/userXX     :working directory set to /home/userXX
        --user=userXX              :run as userXX
        --user=root                :run as root
        --volume=/data:/mnt        :mount host directory /data in /mnt
        --novol=/proc              :remove /proc from list of volumes to mount
        --env="MYTAG=xxx"          :set environment variable
        --hostauth                 :bind the host /etc/passwd /etc/group ...
        --nosysdirs                :do not bind the host /proc /sys /run /dev
        --nometa                   :ignore container metadata
        --dri                      :bind directories relevant for dri graphics
        --hostenv                  :pass the host environment to the container
        --cpuset-cpus=<1,2,3-4>    :CPUs in which to allow execution
        --name=<container-name>    :set or change the name of the container
        --bindhome                 :bind the home directory into the container
        --location=<path-to-dir>   :use root tree outside the repository
        --kernel=<kernel-id>       :use this Linux kernel identifier
        --device=/dev/xxx          :pass device to container (R1 mode only)

        Only available in Pn execution modes:
        --publish=<hport:cport>    :map container TCP/IP <cport> into <hport>
        --publish-all              :bind and connect to random ports

        run <container-id-or-name> executes an existing container, previously
        created from an image by using: create <repo/image:tag>

        run <repo/image:tag> always creates a new container from the image
        if needed the image is pulled. This is slow and may waste storage.
        """
        self._get_run_options(cmdp)
        container_or_image = cmdp.get("P1")
        Config.location = cmdp.get("--location=")
        delete = cmdp.get("--rm")
        name = cmdp.get("--name=")
        #
        if cmdp.missing_options(): # syntax error
            return False
        if Config.location:
            container_id = ""
        elif not container_or_image:
            Msg().err("Error: must specify container_id or image:tag")
            return False
        else:
            container_id = self.localrepo.get_container_id(container_or_image)
            if not container_id:
                (imagerepo, tag) = self._check_imagespec(container_or_image)
                if (imagerepo and
                        self.localrepo.cd_imagerepo(imagerepo, tag)):
                    container_id = self._create(imagerepo+":"+tag)
                if not container_id:
                    self.do_pull(cmdp)
                    if self.localrepo.cd_imagerepo(imagerepo, tag):
                        container_id = self._create(imagerepo+":"+tag)
                    if not container_id:
                        Msg().err("Error: image or container not available")
                        return False
            if name and container_id:
                if not self.localrepo.set_container_name(container_id, name):
                    Msg().err("Error: invalid container name format")
                    return False
        exec_engine = ExecutionMode(self.localrepo, container_id).get_engine()
        if not exec_engine:
            Msg().err("Error: no execution engine for this execmode")
            return False
        self._get_run_options(cmdp, exec_engine)
        status = exec_engine.run(container_id)
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
        dummy = cmdp.get("--no-trunc")
        dummy = cmdp.get("--all")
        if cmdp.missing_options():               # syntax error
            return False
        images_list = self.localrepo.get_imagerepos()
        Msg().out("REPOSITORY", l=Msg.INF)
        for (imagerepo, tag) in images_list:
            prot = (".", "P")[
                self.localrepo.isprotected_imagerepo(imagerepo, tag)]
            Msg().out("%-60.60s %c" % (imagerepo + ":" + tag, prot))
            if verbose:
                imagerepo_dir = self.localrepo.cd_imagerepo(imagerepo, tag)
                Msg().out("  %s" % (imagerepo_dir))
                layers_list = self.localrepo.get_layers(imagerepo, tag)
                if layers_list:
                    for (layer_name, size) in layers_list:
                        file_size = size / (1024 * 1024)
                        if not file_size and size:
                            file_size = 1
                        Msg().out("    %s (%d MB)" %
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
        Msg().out("%-36.36s %c %c %-18s %-s" %
                  ("CONTAINER ID", "P", "M", "NAMES", "IMAGE"), l=Msg.INF)
        for (container_id, reponame, names) in containers_list:
            prot = (".", "P")[
                self.localrepo.isprotected_container(container_id)]
            write = ("R", "W", "N", "D")[
                self.localrepo.iswriteable_container(container_id)]
            Msg().out("%-36.36s %c %c %-18s %-s" %
                      (container_id, prot, write, names, reponame))
        return True

    def do_rm(self, cmdp):
        """
        rm: delete a container
        rm <container_id>
        """
        container_id_list = cmdp.get("P*")
        if cmdp.missing_options():               # syntax error
            return False
        if not container_id_list:
            Msg().err("Error: must specify image:tag or repository/image:tag")
            return False
        status = True
        for container_id in cmdp.get("P*"):
            container_id = self.localrepo.get_container_id(container_id)
            if not container_id:
                Msg().err("Error: invalid container id", container_id)
                status = False
                continue
            else:
                if self.localrepo.isprotected_container(container_id):
                    Msg().err("Error: container is protected")
                    status = False
                    continue
                Msg().out("Info: deleting container:",
                          str(container_id), l=Msg.INF)
                if not self.localrepo.del_container(container_id):
                    Msg().err("Error: deleting container")
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
        if not imagerepo:
            return False
        else:
            if self.localrepo.isprotected_imagerepo(imagerepo, tag):
                Msg().err("Error: image repository is protected")
                return False
            Msg().out("Info: deleting image:", imagespec, l=Msg.INF)
            if not self.localrepo.del_imagerepo(imagerepo, tag, force):
                Msg().err("Error: deleting image")
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
                Msg().err("Error: protect container failed")
                return False
            return True
        else:
            (imagerepo, tag) = self._check_imagespec(arg)
            if imagerepo:
                if self.localrepo.protect_imagerepo(imagerepo, tag):
                    return True
            Msg().err("Error: protect image failed")
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
                Msg().err("Error: unprotect container failed")
                return False
            return True
        else:
            (imagerepo, tag) = self._check_imagespec(arg)
            if imagerepo:
                if self.localrepo.unprotect_imagerepo(imagerepo, tag):
                    return True
            Msg().err("Error: unprotect image failed")
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
            Msg().err("Error: invalid container id or name")
            return False
        if not self.localrepo.set_container_name(container_id, name):
            Msg().err("Error: invalid container name")
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
            Msg().err("Error: invalid container id or name")
            return False
        if not self.localrepo.del_container_name(name):
            Msg().err("Error: removing container name")
            return False
        return True

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
            (container_dir, container_json) = ContainerStructure(
                self.localrepo, container_id).get_container_attr()
        else:
            (imagerepo, tag) = self._check_imagespec(container_or_image)
            if self.localrepo.cd_imagerepo(imagerepo, tag):
                (container_json, dummy) = self.localrepo.get_image_attributes()
            else:
                return False
        if print_dir:
            if container_id and container_dir:
                Msg().out(str(container_dir) + "/ROOT")
                return True
        elif container_json:
            try:
                Msg().out(json.dumps(container_json, sort_keys=True,
                                     indent=4, separators=(',', ': ')))
            except (IOError, OSError, AttributeError, ValueError, TypeError):
                Msg().out(container_json)
            return True
        return False

    def do_verify(self, cmdp):
        """
        verify: verify an image
        verify <repo/image:tag>
        """
        (imagerepo, tag) = self._check_imagespec(cmdp.get("P1"))
        if (not imagerepo) or cmdp.missing_options():  # syntax error
            return False
        else:
            Msg().out("Info: verifying: %s:%s" % (imagerepo, tag), l=Msg.INF)
            if not self.localrepo.cd_imagerepo(imagerepo, tag):
                Msg().err("Error: selecting image and tag")
                return False
            elif self.localrepo.verify_image():
                Msg().out("Info: image Ok", l=Msg.INF)
                return True
        Msg().err("Error: image verification failure")
        return False

    def do_setup(self, cmdp):
        """
        setup: change container execution settings
        setup [options] <container-id>
        --execmode=<mode>          :select execution mode from below
        --force                    :force setup change
        --nvidia                   :add NVIDIA libraries and binaries
                                    (nvidia support is EXPERIMENTAL)

        <mode> is one of the following execution modes:
        P1: proot accelerated mode using seccomp filtering (default)
        P2: proot accelerated mode disabled
        F1: fakechroot starting executables via direct loader invocation
        F2: like F1 plus protected environment and modified ld.so
        F3: fakechroot plus patching of elf headers in binaries and libs
        F4: like F3 plus support for newly created executables via
            dynamic patching of elf headers in binaries and libs
        R1: runc using rootless namespaces, requires recent kernel
        S1: singularity, requires a local installation of singularity,
            if singularity is available in the PATH udocker will use
            it to execute the container
        """
        container_id = cmdp.get("P1")
        xmode = cmdp.get("--execmode=")
        force = cmdp.get("--force")
        nvidia = cmdp.get("--nvidia")
        if cmdp.missing_options():               # syntax error
            return False
        if not self.localrepo.cd_container(container_id):
            Msg().err("Error: invalid container id")
            return False
        elif xmode and self.localrepo.isprotected_container(container_id):
            Msg().err("Error: container is protected")
            return False
        if nvidia:
            nvidia_mode = NvidiaMode(self.localrepo, container_id)
            nvidia_mode.set_mode(force)
        exec_mode = ExecutionMode(self.localrepo, container_id)
        if xmode:
            return exec_mode.set_mode(xmode.upper(), force)
        Msg().out("execmode: %s" % (exec_mode.get_mode()))
        return True

    def do_install(self, cmdp):
        """
        install: install udocker and its tools
        install [options]
        --force                    :force reinstall
        --purge                    :remove files (be careful)
        """
        if cmdp is not None:
            force = cmdp.get("--force")
            purge = cmdp.get("--purge")
        else:
            force = False
            purge = False
        utools = UdockerTools(self.localrepo)
        if purge:
            utools.purge()
        status = utools.install(force)
        if status is not None and not status:
            Msg().err("Error: installation of udockertools failed")
            return False
        Msg().err("Info: installation of udockertools successful", l=Msg.VER)
        return True

    def do_help(self, cmdp, cmds=None):
        """
        Syntax:
          udocker  <command>  [command_options]  <command_args>

        Commands:
          search <repo/image:tag>       :Search dockerhub for container images
          pull <repo/image:tag>         :Pull container image from dockerhub
          images                        :List container images
          create <repo/image:tag>       :Create container from a pulled image
          ps                            :List created containers
          rm  <container>               :Delete container
          run <container>               :Execute container
          inspect <container>           :Low level information on container
          name <container_id> <name>    :Give name to container
          rmname <name>                 :Delete name from container

          rmi <repo/image:tag>          :Delete image
          rm <container-id>             :Delete container
          import <tar> <repo/image:tag> :Import tar file (exported by docker)
          import - <repo/image:tag>     :Import from stdin (exported by docker)
          load -i <exported-image>      :Load image from file (saved by docker)
          load                          :Load image from stdin (saved by docker)
          export -o <tar> <container>   :Export container rootfs to file
          export - <container>          :Export container rootfs to stdin
          inspect <repo/image:tag>      :Return low level information on image
          verify <repo/image:tag>       :Verify a pulled image
          clone <container>             :duplicate container

          protect <repo/image:tag>      :Protect repository
          unprotect <repo/image:tag>    :Unprotect repository
          protect <container>           :Protect container
          unprotect <container>         :Unprotect container

          mkrepo <topdir>               :Create repository in another location
          setup                         :Change container execution settings
          login                         :Login into docker repository
          logout                        :Logout from docker repository

          version                       :Shows udocker version and exits

          help                          :This help
          run --help                    :Command specific help

        Options common to all commands must appear before the command:
          -D                            :Debug
          --quiet                       :Less verbosity
          --repo=<directory>            :Use repository at directory

        Examples:
          udocker search fedora
          udocker pull fedora
          udocker create --name=fed  fedora
          udocker run  fed  cat /etc/redhat-release
          udocker run --hostauth --hostenv --bindhome  fed
          udocker run --user=root  fed  yum install firefox
          udocker run --hostauth --hostenv --bindhome fed   firefox
          udocker run --hostauth --hostenv --bindhome fed   /bin/bash -i
          udocker run --user=root  fed  yum install cheese
          udocker run --hostauth --hostenv --bindhome --dri fed  cheese
          udocker --repo=/home/x/.udocker  images
          udocker -D run --user=1001:5001  fedora
          udocker export -o fedora.tar fedora
          udocker import fedora.tar myfedoraimage
          udocker create --name=myfedoracontainer myfedoraimage
          udocker export -o fedora_all.tar --clone fedora
          udocker import --clone fedora_all.tar

        Notes:
          * by default the binaries, images and containers are placed in
               $HOME/.udocker
          * by default the following host directories are mounted in the
            container:
               /dev /proc /sys
               /etc/resolv.conf /etc/host.conf /etc/hostname
          * to prevent the mount of the above directories use:
               run  --nosysdirs  <container>
          * additional host directories to be mounted are specified with:
               run --volume=/data:/mnt --volume=/etc/hosts  <container>
               run --nosysdirs --volume=/dev --volume=/proc  <container>

        See: https://github.com/indigo-dc/udocker/blob/master/SUMMARY.md
        """
        if cmds is None:
            cmds = dict()
        cmd_help = cmdp.get("", "CMD")
        try:
            text = cmds[cmd_help].__doc__
            if text:
                Msg().out(text)
                return
        except (AttributeError, SyntaxError, KeyError):
            pass
        Msg().out(self.do_help.__doc__)
        return True

    def do_version(self, cmdp):
        """
        version: Print version information
        """
        if cmdp.missing_options():  # syntax error
            return False
        try:
            Msg().out("%s %s" % ("version:", __version__))
            Msg().out("%s %s" % ("tarball:", Config.tarball))
            Msg().out("%s %s" % ("tarball_release:", Config.tarball_release))
        except NameError:
            pass
        return True


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
        self._argv_split['CMD'] = ""
        self._argv_split['GEN_OPT'] = []
        self._argv_split['CMD_OPT'] = []
        self._argv_consumed_options['GEN_OPT'] = []
        self._argv_consumed_options['CMD_OPT'] = []
        self._argv_consumed_params['GEN_OPT'] = []
        self._argv_consumed_params['CMD_OPT'] = []

    def parse(self, argv):
        """Parse a command line string.
        Divides the string in three blocks: general_options,
        command name, and command options+arguments
        """
        step = 1
        for arg in argv[1:]:
            if step == 1:
                if arg[0] in string.ascii_letters:
                    self._argv_split['CMD'] = arg
                    step = 2
                else:
                    self._argv_split['GEN_OPT'].append(arg)
            elif step == 2:
                self._argv_split['CMD_OPT'].append(arg)
        return step == 2

    def missing_options(self):
        """Get comamnd line options not used/fetched by Cmdp.get()
        """
        all_opt = []
        for pos in range(len(self._argv_split['GEN_OPT'])):
            if (pos not in self._argv_consumed_options['GEN_OPT'] and
                    pos not in self._argv_consumed_params['GEN_OPT']):
                all_opt.append(self._argv_split['GEN_OPT'][pos])
        for pos in range(len(self._argv_split['CMD_OPT'])):
            if (pos not in self._argv_consumed_options['CMD_OPT'] and
                    pos not in self._argv_consumed_params['CMD_OPT']):
                all_opt.append(self._argv_split['CMD_OPT'][pos])
        return all_opt

    def get(self, opt_name, opt_where="CMD_OPT", opt_multiple=False):
        """Get the value of a command line option --xyz=
        multiple=true  multiple occurences of option can be present
        """
        if opt_where == "CMD":
            return self._argv_split["CMD"]
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
        opt_list = self._argv_split[opt_where]
        while pos < len(opt_list):
            for opt_name in opts_string.strip().split():
                if opt_name.endswith("="):
                    if opt_list[pos].startswith(opt_name):
                        self._argv_consumed_options[opt_where].append(pos)
                    elif opt_list[pos] == opt_name[:-1]:
                        self._argv_consumed_options[opt_where].append(pos)
                        if pos + 1 == len(opt_list):
                            break   # error -x without argument at end of line
                        if (pos < len(opt_list) and
                                not opt_list[pos+1].startswith("-")):
                            self._argv_consumed_options[opt_where].\
                                append(pos + 1)
                elif opt_list[pos] == opt_name:
                    self._argv_consumed_options[opt_where].append(pos)
            pos += 1

    def _get_option(self, opt_name, opt_list, consumed, opt_multiple):
        """Get command line options such as: -x -x= --x --x=
        The options may exist in the first and third part of the udocker
        command line.
        """
        all_args = []
        pos = 0
        list_len = len(opt_list)
        while pos < list_len:
            opt_arg = None
            if ((not opt_list[pos].startswith("-")) and
                    (pos < 1 or (pos not in consumed and not
                                 opt_list[pos-1].endswith("=")))):
                break        # end of options and start of arguments
            elif opt_name.endswith("="):
                if opt_list[pos].startswith(opt_name):
                    opt_arg = opt_list[pos].split("=", 1)[1].strip()
                elif (opt_list[pos] == opt_name[:-1] and
                      pos + 1 == list_len):
                    break    # error --arg at end of line
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
        return False

    def _get_param(self, opt_name, opt_list, consumed, consumed_params):
        """Get command line parameters
        The CLI of udocker has 3 parts, first options, second command name
        third everything after the command name. The params are the arguments
        that do not start with - and may exist after the options.
        """
        all_args = []
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
        return None


class Main(object):
    """Get options, parse and execute the command line"""

    def __init__(self):
        self.cmdp = CmdParser()
        parseok = self.cmdp.parse(sys.argv)
        if not parseok and not self.cmdp.get("--version", "GEN_OPT"):
            Msg().err("Error: parsing command line, use: udocker help")
            sys.exit(1)
        if not (os.geteuid() or self.cmdp.get("--allow-root", "GEN_OPT")):
            Msg().err("Error: do not run as root !")
            sys.exit(1)
        Config().user_init(self.cmdp.get("--config=", "GEN_OPT")) # read config
        if (self.cmdp.get("--debug", "GEN_OPT") or
                self.cmdp.get("-D", "GEN_OPT")):
            Config.verbose_level = Msg.DBG
        elif (self.cmdp.get("--quiet", "GEN_OPT") or
              self.cmdp.get("-q", "GEN_OPT")):
            Config.verbose_level = Msg.MSG
        Msg().setlevel(Config.verbose_level)
        if self.cmdp.get("--insecure", "GEN_OPT"):
            Config.http_insecure = True
        if self.cmdp.get("--repo=", "GEN_OPT"):  # override repo root tree
            Config.topdir = self.cmdp.get("--repo=", "GEN_OPT")
            if not LocalRepository(Config.topdir).is_repo():
                Msg().err("Error: invalid udocker repository:",
                          Config.topdir)
                sys.exit(1)
        self.localrepo = LocalRepository(Config.topdir)
        if (self.cmdp.get("", "CMD") == "version" or
                self.cmdp.get("--version", "GEN_OPT")):
            Udocker(self.localrepo).do_version(self.cmdp)
            sys.exit(0)
        if not self.localrepo.is_repo():
            Msg().out("Info: creating repo: " + Config.topdir, l=Msg.INF)
            self.localrepo.create_repo()
        self.udocker = Udocker(self.localrepo)

    def execute(self):
        """Command parsing and selection"""
        cmds = {
            "version": self.udocker.do_version,
            "help": self.udocker.do_help, "search": self.udocker.do_search,
            "images": self.udocker.do_images, "pull": self.udocker.do_pull,
            "create": self.udocker.do_create, "ps": self.udocker.do_ps,
            "run": self.udocker.do_run,
            "rmi": self.udocker.do_rmi, "mkrepo": self.udocker.do_mkrepo,
            "import": self.udocker.do_import, "load": self.udocker.do_load,
            "export": self.udocker.do_export, "clone": self.udocker.do_clone,
            "protect": self.udocker.do_protect, "rm": self.udocker.do_rm,
            "name": self.udocker.do_name, "rmname": self.udocker.do_rmname,
            "verify": self.udocker.do_verify, "logout": self.udocker.do_logout,
            "unprotect": self.udocker.do_unprotect,
            "inspect": self.udocker.do_inspect, "login": self.udocker.do_login,
            "setup":self.udocker.do_setup, "install":self.udocker.do_install,
        }
        if (self.cmdp.get("--help", "GEN_OPT") or
                self.cmdp.get("-h", "GEN_OPT")):
            self.udocker.do_help(self.cmdp)
            return 0
        else:
            command = self.cmdp.get("", "CMD")
            if command in cmds:
                if command != "install":
                    cmds["install"](None)
                if self.cmdp.get("--help") or self.cmdp.get("-h"):
                    self.udocker.do_help(self.cmdp, cmds)   # help on command
                    return 0
                status = cmds[command](self.cmdp)     # executes the command
                if self.cmdp.missing_options():
                    Msg().err("Error: syntax error at: %s" %
                              " ".join(self.cmdp.missing_options()))
                    return 1
                if isinstance(status, bool):
                    return not status
                elif isinstance(status, (int, long)):
                    return status                     # return command status
            else:
                Msg().err("Error: invalid command:", command, "\n")
                self.udocker.do_help(self.cmdp)
        return 1

    def start(self):
        """Program start and exception handling"""
        try:
            exit_status = self.execute()
        except (KeyboardInterrupt, SystemExit):
            FileUtil().cleanup()
            return 1
        except:
            FileUtil().cleanup()
            raise
        else:
            FileUtil().cleanup()
            return exit_status

if __name__ == "__main__":
    sys.exit(Main().start())
