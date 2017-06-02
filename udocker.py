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
import stat
import string
import re
import subprocess
import time
import pwd
import grp
import platform

__author__ = "udocker@lip.pt"
__credits__ = ["PRoot http://proot.me"]
__license__ = "Licensed under the Apache License, Version 2.0"
__version__ = "1.1.0-RC2"
__date__ = "2017"

# Python version major.minor
PY_VER = "%d.%d" % (sys.version_info[0], sys.version_info[1])

START_PATH = os.path.dirname(os.path.realpath(sys.argv[0]))

try:
    from cStringIO import StringIO
except ImportError:
    from io import BytesIO as StringIO
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
    long
except:
    long=int
try:
    raw_input
except:
    raw_input=input

if PY_VER < "2.6":
    try:
        import posixpath
    except ImportError:
        pass

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
        else:
            return self._check_output(*popenargs, **kwargs)

    def get_output(self, cmd):
        """Execute a shell command and get its output"""
        try:
            content = self.check_output(cmd, shell=True,
                                        stderr=Msg.chlderr,
                                        close_fds=True)
        except subprocess.CalledProcessError:
            return None
        return content.decode("utf-8").strip()


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
    tarball = (
        "https://owncloud.indigo-datacloud.eu/index.php"
        "/s/lR6CsSP5HfEc5uZ/download"
    )
    autoinstall = True

    config = "udocker.conf"
    keystore = "keystore"

    # for tmp files only
    tmpdir = "/tmp"

    # defaults for container execution
    cmd = ["/bin/bash", "-i"]  # Comand to execute

    # dafault path for executables
    root_path = "/usr/sbin:/sbin:/usr/bin:/bin"
    user_path = "/usr/local/bin:/usr/bin:/bin"

    # directories to be mapped in contaners with: run --sysdirs
    sysdirs_list = (
        "/dev", "/proc", "/sys",
        "/etc/resolv.conf", "/etc/host.conf",
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
    default_execution_mode = "P2"

    # PRoot override seccomp
    # proot_noseccomp = True
    proot_noseccomp = None

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

    # access files, used to circunvent openmpi init issues in fakechroot
    access_files = (
        "/sys/class/infiniband", "/dev/open-mx", "/dev/myri0", "/dev/myri1",
        "/dev/myri2", "/dev/myri3", "/dev/myri4", "/dev/myri5", "/dev/myri6",
        "/dev/myri7", "/dev/myri8", "/dev/myri9", "/dev/ipath", "/dev/kgni0",
        "/dev/mic/scif", "/dev/scif",
    )

    # runc parameters
    runc_nomqueue = None

    # Pass host env variables
    valid_host_env = ("TERM", "PATH", )

    # CPU affinity executables to use with: run --cpuset-cpus="1,2,3-4"
    cpu_affinity_exec_tools = ("taskset -c ", "numactl -C ")

    # Containers execution defaults
    location = ""         # run container in this location

    # Curl settings
    http_proxy = ""    # ex. socks5://user:pass@127.0.0.1:1080
    timeout = 12       # default timeout (secs)
    download_timeout = 30 * 60    # file download timeout (secs)
    ctimeout = 6       # default TCP connect timeout (secs)
    http_agent = ""
    http_insecure = False

    # docker hub v1
    dockerio_index_url = "https://index.docker.io"
    # docker hub v2
    dockerio_registry_url = "https://registry-1.docker.io"
    # private repository v2
    # dockerio_registry_url = "http://localhost:5000"

    # registries table
    docker_registries = {"docker.io": ["https://registry-1.docker.io"
                                       "https://index.docker.io"],
                        }
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

    def _read_config(self, config_file):
        """Interpret config file content"""
        if not config_file:
            return False
        cfile = FileUtil(config_file)
        if cfile.size() == -1:
            return False
        data = cfile.getdata()
        for line in data.split("\n"):
            if not line.strip() or "=" not in line or line.startswith("#"):
                continue
            (key, val) = line.strip().split("=", 1)
            key = key.strip()
            Msg().out(config_file, ":", key, "=", val, l=Msg.DBG)
            try:
                exec('Config.%s=%s' % (key, val))
            except(NameError, AttributeError, TypeError, IndexError,
                   SyntaxError):
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
            self._read_config("/etc/" + Config.config)
            if self._read_config(config_file):
                return True
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
                filep.write((" " * size).encode())
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

    ERR = 0
    MSG = 1
    WAR = 2
    INF = 3
    VER = 4
    DBG = 5
    DEF = INF
    level = DEF
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

    def setlevel(self, new_level):
        """Define debug level"""
        Msg.level = new_level
        if Msg.level >= Msg.DBG:
            Msg.chlderr = sys.stderr
            Msg.chldout = sys.stdout
        else:
            Msg.chlderr = Msg.nullfp
            Msg.chldout = Msg.nullfp

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
        try:
            self.filename = os.path.abspath(filename)
            self.basename = os.path.basename(self.filename)
        except (AttributeError, TypeError):
            self.filename = filename
            self.basename = filename
        self._tmpdir = Config.tmpdir
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
            else:
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
            return b""
        else:
            buf = filep.read()
            filep.close()
            return buf

    def putdata(self, buf, mode="wb"):
        """Write buffer to file"""
        try:
            filep = open(self.filename, mode)
        except (IOError, OSError, TypeError):
            return ""
        else:
            filep.write(buf.encode())
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
        if isinstance(path, list) or isinstance(path, tuple):
            for directory in path:
                full_path = rootdir + directory + "/" + self.basename
                if os.path.exists(full_path):
                    return directory + "/" + self.basename
            return ""
        return ""

    def rename(self, dest_filename):
        """Rename/move file"""
        try:
            os.rename(self.filename, dest_filename)
        except (IOError, OSError):
            return False
        return True

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

    def find_file_in_dir(self, image_list):
        """Find and return first file of list in dir"""
        path_prefix = self.filename
        for image in image_list:
            image_path = path_prefix + "/" + image
            if os.path.exists(image_path):
                return image_path
        return ""

    def _link_set(self, f_path, root_path, force):
        """Actual convertion to container specific symbolic link"""
        l_path = os.readlink(f_path)
        if l_path.startswith("/") and not l_path.startswith(self.filename):
            p_path = os.path.realpath(os.path.dirname(f_path))
            new_l_path = root_path + l_path
            if force and not os.access(p_path, os.W_OK):
                os.chmod(p_path, stat.S_IMODE(os.stat(p_path).st_mode) | stat.S_IWUSR)
                os.remove(f_path)
                os.symlink(new_l_path, f_path)
                os.chmod(p_path, stat.S_IMODE(os.stat(p_path).st_mode) & ~stat.S_IWUSR)
            else:
                os.remove(f_path)
                os.symlink(new_l_path, f_path)
            return True
        return False

    def _link_restore(self, f_path, root_path, force):
        """Actual convertion for host specific symbolic link"""
        l_path = os.readlink(f_path)
        new_l_path = ""
        if l_path.startswith(self.filename):
            new_l_path = l_path.replace(self.filename, "", 1)
        elif l_path.startswith(root_path):
            new_l_path = l_path.replace(root_path, "", 1)
        if new_l_path:
            p_path = os.path.realpath(os.path.dirname(f_path))
            if force and not os.access(p_path, os.W_OK):
                os.chmod(p_path, stat.S_IMODE(os.stat(p_path).st_mode) | stat.S_IWUSR)
                os.remove(f_path)
                os.symlink(new_l_path, f_path)
                os.chmod(p_path, stat.S_IMODE(os.stat(p_path).st_mode) & ~stat.S_IWUSR)
            else:
                os.remove(f_path)
                os.symlink(new_l_path, f_path)
            return True
        return False

    def links_conv(self, force=False, to_container=True, root_path=""):
        """ Convert absolute symbolic links to relative symbolic links
        """
        if not root_path:
            root_path = os.path.realpath(self.filename)
        links = []
        if not self._is_safe_prefix(root_path):
            Msg().err("Error: links convertion outside of directory tree: ",
                      root_path)
            return None
        for dir_path, dummy, files in os.walk(root_path):
            for f_name in files:
                try:
                    f_path = dir_path + "/" + f_name
                    if not os.path.islink(f_path):
                        continue
                    if os.lstat(f_path).st_uid != Config.uid:
                        continue
                    if to_container:
                        if self._link_set(f_path, root_path, force):
                            links.append(f_path)
                    else:
                        if self._link_restore(f_path, root_path, force):
                            links.append(f_path)
                except OSError:
                    continue
        return links

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
        self.curl = GetURL()

    def _version_isequal(self, filename):
        """Is version inside file equal to this udocker version"""
        version = FileUtil(filename).getdata().strip().decode("utf-8")
        return version and version == __version__

    def is_available(self):
        """Are the tools already installed"""
        return self._version_isequal(self.localrepo.libdir + "/VERSION")

    def _download(self):
        """Get the tools tarball containing the binaries"""
        tarball_file = FileUtil("udockertools").mktmp()
        (hdr, dummy) = self.curl.get(self._tarball, ofile=tarball_file)
        if hdr.data["X-ND-CURLSTATUS"]:
            return ""
        else:
            return tarball_file

    def _verify_version(self, tarball_file):
        """verify the tarball version"""
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

          https://indigo-dc.gitbooks.io/udocker/content/

        Udocker requires additional tools to run. These are available
        in the tarball that comprises udocker. The tarballs are available
        at the INDIGO-DataCloud repository under tarballs at:

          http://repo.indigo-datacloud.eu/

        Udocker can be installed with these instructions:

        1) set UDOCKER_TARBALL to a remote URL or local filename e.g.

          $ export UDOCKER_TARBALL=http://host/path
          or
          $ export UDOCKER_TARBALL=/tmp/filename

        2) run udocker and installation will proceed

          ./udocker version

        The correct tarball version for this udocker executable is:
        """
        Msg().out(self._instructions.__doc__, __version__, l=Msg.ERR)

    def install(self, force=False):
        """Get the udocker tarball and install the binaries"""
        if self.is_available() and not force:
            return True
        elif not self._autoinstall and not force:
            Msg().out("Warning: no engine available and autoinstall disabled",
                      l=Msg.WAR)
            return None
        elif not self._tarball:
            Msg().err("Error: UDOCKER_TARBALL not defined")
            self._instructions()
            return False
        else:
            Msg().out("Info: installing from tarball", __version__,
                      l=Msg.INF)
            tarball_file = ""
            if "://" in self._tarball:
                Msg().out("Info: downloading: %s" % (self._tarball), l=Msg.INF)
                tarball_file = self._download()
            elif os.path.exists(self._tarball):
                tarball_file = self._tarball
            if not tarball_file:
                Msg().err("Error: accessing tarball:",
                          self._tarball)
                self._instructions()
            else:
                if not self._verify_version(tarball_file):
                    Msg().err("Error: wrong tarball version:",
                              self._tarball)
                    self._instructions()
                elif self._install(tarball_file):
                    return True
                else:
                    Msg().err("Error: installing tarball:",
                              self._tarball)
                    self._instructions()
                if "://" in self._tarball:
                    FileUtil(tarball_file).remove()
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
        else:
            return ""

    def check_container(self):
        """verify if path to container is ok"""
        last_path = self.get_patch_last_path()
        if last_path and last_path != self._container_dir:
            Msg().err("Error: mismatch, convert execmode to P and then to F")
            sys.exit(1)

    def get_patch_last_time(self):
        """get time in seconds of last full patch of container"""
        last_time = FileUtil(self._container_patch_time).getdata()
        try:
            return str(int(last_time))
        except ValueError:
            return "0"

    def patch_binaries(self):
        """Set all executables and libs to the ld.so absolute pathname"""
        self.check_container()
        last_time = "0"
        patchelf_exec = self.select_patchelf()
        elf_loader = self.get_container_loader()
        #cmd = "%s --set-interpreter %s --set-root-prefix %s #f" % \
        #    (patchelf_exec, elf_loader, self._container_root)
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
        #cmd = "%s --set-interpreter %s --restore-root-prefix %s #f" % \
        #    (patchelf_exec, elf_loader, self._container_root)
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
        self.check_container()
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
        nul = "\x00/\x00\x00\x00"
        etc = "\x00/etc"
        lib = "\x00/lib"
        usr = "\x00/usr"
        ld_data = ld_data.replace(etc, nul).replace(lib, nul).replace(usr, nul)
        ld_library_path_orig = "\x00LD_LIBRARY_PATH\x00"
        ld_library_path_new = "\x00LD_LIBRARY_REAL\x00"
        ld_data = ld_data.replace(ld_library_path_orig, ld_library_path_new)
        if output_elf is None:
            return bool(FileUtil(elf_loader).putdata(ld_data))
        else:
            return bool(FileUtil(output_elf).putdata(ld_data))

    def restore_ld(self):
        """Restore ld.so"""
        elf_loader = self.get_container_loader()
        if FileUtil(self._container_ld_so_orig).size() == -1:
            return False
        else:
            return FileUtil(self._container_ld_so_orig).copyto(elf_loader)

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
        self.check_container()
        if force or not os.path.exists(self._container_ld_libdirs):
            ld_list = self._find_ld_libdirs()
            ld_str = ":".join(ld_list)
            FileUtil(self._container_ld_libdirs).putdata(ld_str)
            return ld_list
        else:
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
            outpasswd.write(("%s:%s:%s:%s:%s:%s:%s\n" %
                            (user, passw, uid, gid, gecos,
                             home, shell)).encode())
            outpasswd.close()
            return True

    def add_group(self, group, gid):
        """Add a group to a /etc/passwd file"""
        try:
            outgroup = open(self.group_file, "ab")
        except (IOError, OSError):
            return False
        else:
            outgroup.write(("%s:x:%s:\n" % (group, gid)).encode())
            outgroup.close()
            return True

    def get_user(self, wanted_user):
        """Get host or container user"""
        if self.passwd_file:
            return self._get_user_from_file(wanted_user)
        else:
            return self._get_user_from_host(wanted_user)

    def get_group(self, wanted_group):
        """Get host or container group"""
        if self.group_file:
            return self._get_group_from_file(wanted_group)
        else:
            return self._get_group_from_host(wanted_group)


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
        return True

    def restore(self):
        """Restore container files after FileBind"""
        error = False
        if not os.path.isdir(self.container_orig_dir):
            return True
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
        """Prepare to run"""
        self.host_bind_dir = FileUtil("BIND_FILES").mktmpdir()
        for f_name in files_list:
            if not os.path.isfile(f_name):
                continue
            orig_file = f_name.replace('/', '#')
            orig_file_path = self.container_orig_dir + "/" + orig_file
            cont_file = self.container_root + "/" + f_name
            link_path = self.bind_dir + "/" + orig_file
            if not os.path.exists(orig_file_path):
                os.rename(cont_file, orig_file_path)
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

    def _check_exposed_ports(self, exposed_ports):
        """TCP/UDP ports < 1024 in ExposedPorts JSON metadata
        The exposed ports format is  ExposedPorts:{ "80/tcp":{}, }
        """
        port_number = -1
        if exposed_ports:
            for port in exposed_ports:
                try:
                    port_number = int(port.split("/")[0])
                except (ValueError, TypeError):
                    pass
                else:
                    if port_number < 1024:
                        Msg().err("Error: this container exposes privileged"
                                  " TCP/IP ports (< 1024) not supported")
                        return True
        if port_number != -1:
            Msg().out("Warning: this container exposes TCP/IP"
                      " ports this may not work", l=Msg.WAR)
        return False

    def _set_cpu_affinity(self):
        """set the cpu affinity string for container run command"""
        # find set affinity executable
        cpu_affinity_exec = ""
        for exec_cmd in Config.cpu_affinity_exec_tools:
            exec_name = \
                FileUtil(exec_cmd.split(" ", 1)[0]).find_exec()
            if exec_name:
                cpu_affinity_exec = exec_name + \
                    " " + exec_cmd.split(" ", 1)[1]
        # if no cpu affinity executable available ignore affinity set
        if not cpu_affinity_exec:
            self.opt["cpuset"] = ""
            return " "
        elif self.opt["cpuset"]:
            self.opt["cpuset"] = "'" + self.opt["cpuset"] + "'"
            return " %s %s " % (cpu_affinity_exec, self.opt["cpuset"])
        else:
            self.opt["cpuset"] = ""
            return " "

    def _cont2host(self, pathname):
        """Translate container path to host path"""
        if not (pathname and pathname.startswith("/")):
            return ""
        path = ""
        real_container_root = os.path.realpath(self.container_root)
        for vol in self.opt["vol"]:
            if ":" in vol:
                (host_path, cont_path) = vol.split(":")
                if pathname.startswith(cont_path):
                    path = host_path + pathname[len(cont_path):]
                    break
            elif pathname.startswith(vol):
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
                    if f_path.startswith(real_container_root):
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
            status = FileUtil(mountpoint).putdata("")
        elif os.path.isdir(host_path):
            status = FileUtil(mountpoint).mkdir()
        return status

    def _check_volumes(self):
        """Check volume paths"""
        for vol in list(self.opt["vol"]):
            if ":" in vol:
                (host_path, cont_path) = vol.split(":")
                self._create_mountpoint(host_path, cont_path)
            else:
                host_path = vol
                cont_path = ""
                self._create_mountpoint(host_path, host_path)
            if cont_path and not cont_path.startswith("/"):
                Msg().err("Error: invalid volume destination path:", cont_path)
                return False
            elif not (host_path and host_path.startswith("/")):
                Msg().err("Error: invalid volume spec:", vol)
                return False
            elif not os.path.exists(host_path):
                if host_path in Config.dri_list:
                    self.opt["vol"].remove(vol)
                else:
                    Msg().err("Error: invalid host volume path:", host_path)
                    return False
        return True

    def _get_bindhome(self):
        """Binding of the host $HOME in to the container $HOME"""
        if self.opt["bindhome"]:
            host_auth = NixAuthentication()
            (r_user, dummy, dummy, dummy, r_home,
             dummy) = host_auth.get_user(Config.uid)
            if r_user:
                return r_home
        return ""

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
                Msg().out("Warning: --novol %s not in volumes list" %
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

    def _quote(self, argv):
        """Iterate over argv and quote items containing spaces. This is
        useful in case an interpreter is used in the command e.g.:
        $ udocker.py run container bash -c 'echo hello'
        """
        _argv = []
        for arg in argv:
            if ' ' in arg:
                arg = "'{}'".format(arg)
            _argv.append(arg)
        return _argv

    def _check_executable(self):
        """Check if executable exists and has execute permissions"""
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
            Msg().out("Warning: no command assuming:", self.opt["cmd"],
                      l=Msg.WAR)
        exec_name = self.opt["cmd"][0]            # exec pathname without args
        self.opt["cmd"] = self._quote(self.opt["cmd"])
        if exec_name.startswith("/"):
            exec_path = exec_name
        elif exec_name.startswith("./") or exec_name.startswith("../"):
            exec_path = self.opt["cwd"] + "/" + exec_name
        else:
            exec_path = \
                FileUtil(exec_name).find_inpath(path, self.container_root + "/")
        host_exec_path = self._cont2host(exec_path)
        if (os.path.isfile(host_exec_path) and
                os.access(host_exec_path, os.X_OK)):
            return host_exec_path
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
                self.opt["vol"].extend(
                    container_structure.get_container_meta(
                        "Volumes", [], container_json))
                exposed_ports = \
                    container_structure.get_container_meta(
                        "ExposedPorts", [], container_json)
                self._check_exposed_ports(exposed_ports)
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
                    self.opt["env"].append('%s="%s"' % (pair, val))
                continue
            (key, val) = pair.split("=", 1)
            if " " in key or key[0] in string.digits:
                Msg().err("Error: in environment:", pair)
                return False
            if " " in pair and "'" not in pair and '"' not in pair:
                self.opt["env"].remove(pair)
                self.opt["env"].append('%s="%s"' % (key, val))
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
        self.opt["uid"] = 0
        self.opt["gid"] = 0
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
                Msg().out("Warning: non-existing user will be created",
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

    def _run_env_cleanup(self):
        """Allow only to pass essential environment variables."""
        environ_copy = os.environ.copy()
        for env_var in environ_copy:
            if env_var not in Config.valid_host_env:
                del os.environ[env_var]

    def _run_env_set(self):
        """Environment variables to set"""
        self.opt["env"].append("HOME=" + self.opt["home"])
        self.opt["env"].append("USER=" + self.opt["user"])
        self.opt["env"].append("LOGNAME=" + self.opt["user"])
        self.opt["env"].append("USERNAME=" + self.opt["user"])

        self.opt["env"].append(r"PS1=%s[\W]\$ " % self.container_id[:8])

        self.opt["env"].append("SHLVL=0")
        self.opt["env"].append("container_ruser=" + Config().username())
        self.opt["env"].append("container_root=" + self.container_root)
        self.opt["env"].append("container_uuid=" + self.container_id)
        self.opt["env"].append("container_execmode=" + self.exec_mode.get_mode())
        #names = str(self.container_names).translate(None, " '\"[]")
        names = ",".join(self.container_names)
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

        # Execution Mode
        self.exec_mode = ExecutionMode(self.localrepo, self.container_id)

        # which user to use inside the container and setup its account
        if not self._setup_container_user(self.opt["user"]):
            return ""

        if not self._set_volume_bindings():
            return ""

        if not self._check_paths():
            return ""

        exec_path = self._check_executable()

#        exec_path = self._check_executable()
#        if not (self._check_paths() and exec_path):
#            return ""

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
            uid_map = " -0 "
        else:
            uid_map = \
                " -i " + self.opt["uid"] + ":" + self.opt["gid"] + " "
        return uid_map

    def _create_mountpoint(self, host_path, cont_path):
        """Override create mountpoint"""
        return True

    def _get_volume_bindings(self):
        """Get the volume bindings string for container run command"""
        if self.opt["vol"]:
            vol_str = " -b " + " -b ".join(self.opt["vol"])
        else:
            vol_str = " "
        return vol_str

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
            proot_verbose = " -v 9 "
        else:
            proot_verbose = ""

        # build the actual command
        cmd_t = (r"unset VTE_VERSION;",
                 " ".join(self.opt["env"]),
                 self._set_cpu_affinity(),
                 self.proot_exec,
                 proot_verbose,
                 self._get_volume_bindings(),
                 self._set_uid_map(),
                 "-k", self._kernel,
                 "-r", self.container_root,
                 " ",)
        cmd = " ".join(cmd_t)
        if self.opt["cwd"]:  # set current working directory
            cmd += " -w " + self.opt["cwd"] + " "
        cmd += " ".join(self.opt["cmd"])
        Msg().out("CMD = " + cmd, l=Msg.VER)

        # if not --hostenv clean the environment
        if not self.opt["hostenv"]:
            self._run_env_cleanup()

        # execute
        self._run_banner(self.opt["cmd"][0])
        status = subprocess.call(cmd, shell=True, close_fds=True)
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
            cmd = self.runc_exec + " spec --rootless --bundle " \
                 + os.path.realpath(self.container_dir)
            status = subprocess.call(cmd, shell=True, stderr=Msg.chlderr,
                                     close_fds=True)
            if status:
                return False
        json_obj = None
        infile = None
        try:
            infile = open(self._container_specfile)
            json_obj = json.load(infile)
            if (json_obj["platform"]["os"] != "linux" or
                    json_obj["platform"]["arch"] != Config().arch()):
                json_obj = None
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
        json_obj["process"]["env"] = []
        for env_str in self.opt["env"]:
            (env_var, value) = env_str.split("=", 1)
            if env_var:
                json_obj["process"]["env"].append("%s=%s" % (env_var, value))
        for idmap in json_obj["linux"]["uidMappings"]:
            if "hostID" in idmap:
                idmap["hostID"] = os.getuid()
        for idmap in json_obj["linux"]["gidMappings"]:
            if "hostID" in idmap:
                idmap["hostID"] = os.getgid()
        json_obj["process"]["args"] = self.opt["cmd"]
        return json_obj

    def _uid_check(self):
        """Check the uid_map string for container run command"""
        if ("user" in self.opt and self.opt["user"] != "0" and
                self.opt["user"] != "root"):
            Msg().out("Warning: this engine only supports execution as root",
                      l=Msg.WAR)

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
        for volume in self.opt["vol"]:
            try:
                (host_dir, cont_dir) = volume.split(":")
            except ValueError:
                host_dir = volume
                cont_dir = volume
            if os.path.isdir(host_dir):
                if host_dir == "/dev":
                    Msg().out("Warning: this engine does not support -v",
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

    def _run_env_addhost(self):
        """Add host env to spec"""
        container_env = []
        for env_str in self.opt["env"]:
            (env_var, dummy) = env_str.split("=", 1)
            if env_var:
                container_env.append(env_var)
        for (env_var, value) in os.environ.items():
            if not env_var:
                continue
            if env_var in ("VTE_VERSION") or env_var in container_env:
                continue
            self.opt["env"].append("%s=%s" % (env_var, value))

    def _run_env_cleanup(self):
        """ Allow only to pass essential environment variables.
            Overriding parent ExecutionEngineCommon() class.
        """
        for (index, env_str) in enumerate(self.opt["env"]):
            (env_var, dummy) = env_str.split("=", 1)
            if env_var not in Config.valid_host_env:
                del self.opt["env"][index]

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

        self._container_specfile = self.container_dir + "/config.json"
        self._filebind = FileBind(self.localrepo, self.container_id)

        self._select_runc()

        # create new OCI spec file
        if not self._load_spec(new=True):
            return 4

        self._uid_check()

        # if not --hostenv clean the environment
        if self.opt["hostenv"]:
            self._run_env_addhost()
        else:
            self._run_env_cleanup()

        # set environment variables
        self._run_env_set()
        if not self._check_env():
            return 5

        self._set_spec()
        if (Config.runc_nomqueue or (Config.runc_nomqueue is None and not
                                     Config().oskernel_isgreater("4.8.0"))):
            self._del_mount_spec("mqueue", "/dev/mqueue")
        self._add_volume_bindings()
        self._save_spec()

        if Msg.level >= Msg.DBG:
            runc_debug = " --debug "
        else:
            runc_debug = ""

        # build the actual command
        self.execution_id = Unique().uuid(self.container_id)
        cmd = self.runc_exec + runc_debug + " --root " + self.container_dir + \
              " run --bundle " + self.container_dir + " " + self.execution_id
        Msg().out("CMD = " + cmd, l=Msg.VER)

        # execute
        self._run_banner(self.opt["cmd"][0], '%')
        status = subprocess.call(cmd, shell=True, close_fds=True)
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
        else:
            lib = "libfakechroot"
            deflib = "libfakechroot.so"
            arch = conf.arch()
            (distro, version) = conf.osdistribution()
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
            Msg().err("Error: no libfakechroot found for this host os")
            sys.exit(1)
        Msg().out("fakechroot_so:", fakechroot_so, l=Msg.DBG)
        return fakechroot_so

    def _uid_check(self):
        """Set the uid_map string for container run command"""
        if ("user" not in self.opt or (not self.opt["user"]) or
                self.opt["user"] == "root" or self.opt["user"] == "0"):
            Msg().out("Warning: running as uid 0 is not supported by this engine",
                      l=Msg.WAR)
            self.opt["user"] = Config().username()

    def _setup_container_user(self, user):
        """ Override method ExecutionEngineCommon._setup_container_user()
        """
        self.opt["user"] = Config().username()
        self.opt["uid"] = str(Config.uid)
        self.opt["gid"] = str(Config.gid)
        self.opt["home"] = "/"
        #self.opt["home"] = os.path.expanduser("~")
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
                Msg().out("Warning: non-existing user will be created",
                          l=Msg.WAR)
        self._create_user(container_auth, host_auth)
        return True

    def _get_volume_bindings(self):
        """Get the volume bindings string for fakechroot run"""
        host_volumes_list = []
        map_volumes_list = []
        map_volumes_dict = dict()
        for volume in self.opt["vol"]:
            try:
                (host_dir, cont_dir) = volume.split(":")
            except ValueError:
                host_dir = volume
                cont_dir = ""
            if (not cont_dir) or host_dir == cont_dir:
                host_volumes_list.append(host_dir)
            else:
                map_volumes_dict[cont_dir] = host_dir + "!" + cont_dir
        for cont_dir in sorted(map_volumes_dict, reverse=True):
            map_volumes_list.append(map_volumes_dict[cont_dir])
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
        self.opt["env"].append("FAKECHROOT_BASE=" +
                               os.path.realpath(self.container_root))
        self.opt["env"].append("LD_PRELOAD=" + self._fakechroot_so)
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

    def run(self, container_id):
        """Execute a Docker container using Fakechroot. This is the main
        method invoked to run the a container with Fakechroot.

          * argument: container_id or name
          * options:  many via self.opt see the help
        """

        # this engine does not support root check and fix
        self._uid_check()

        # setup execution
        exec_path = self._run_init(container_id)
        if not exec_path:
            return 2

        # execution mode and get patcher
        xmode = self.exec_mode.get_mode()
        self._elfpatcher = ElfPatcher(self.localrepo, self.container_id)

        # verify if container pathnames are correct for this mode
        self._elfpatcher.check_container()

        # set basic environment variables
        self._run_env_set()
        self._fakechroot_env_set()
        if not self._check_env():
            return 4

        # build the actual command
        self.opt["cmd"][0] = exec_path
        cmd_t = (r"unset VTE_VERSION;",
                 " export ",
                 "; export ".join(self.opt["env"]),
                 " ; export PWD=" + self.opt["cwd"] + " ;", )
        cmd = " ".join(cmd_t)
        if xmode in ("F1", "F2"):
            cmd += " " + self._elfpatcher.get_container_loader() + " "
        cmd += " ".join(self.opt["cmd"])
        Msg().out("CMD = " + cmd, l=Msg.VER)

        # if not --hostenv clean the environment
        if not self.opt["hostenv"]:
            self._run_env_cleanup()

        # execute
        self._run_banner(self.opt["cmd"][0], "#")
        cwd = self._cont2host(self.opt["cwd"])
        status = subprocess.call(cmd, shell=True, close_fds=True, cwd=cwd)
        return status


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
    """

    def __init__(self, localrepo, container_id):
        self.localrepo = localrepo               # LocalRepository object
        self.container_id = container_id         # Container id
        self.container_dir = \
            os.path.realpath(self.localrepo.cd_container(container_id))
        self.container_root = self.container_dir + "/ROOT"
        self.container_execmode = self.container_dir + "/execmode"
        self.exec_engine = None
        self.valid_modes = ("P1", "P2", "F1", "F2", "F3", "F4", "R1")

    def get_mode(self):
        """Get execution mode"""
        xmode = FileUtil(self.container_execmode).getdata()
        if not xmode:
            xmode = Config.default_execution_mode
        return xmode

    def set_mode(self, xmode, force=False):
        """Set execution mode"""
        status = False
        prev_xmode = self.get_mode()
        elfpatcher = ElfPatcher(self.localrepo, self.container_id)
        filebind = FileBind(self.localrepo, self.container_id)
        if xmode not in self.valid_modes:
            Msg().err("Error: invalid execmode:", xmode)
            return status
        if not (force or xmode != prev_xmode):
            return True
        if prev_xmode in ("R1", ) and xmode not in ("R1", ):
            filebind.restore()
        if xmode.startswith("F"):
            if force or prev_xmode[0] in ("P", "R"):
                status = (FileUtil(self.container_root).links_conv(force, True)
                          and elfpatcher.get_ld_libdirs(force))
        if xmode in ("P1", "P2", "F1", "R1"):
            if force or prev_xmode in ("F2", "F3", "F4"):
                status = (elfpatcher.restore_ld() and
                          elfpatcher.restore_binaries())
            elif prev_xmode in ("P1", "P2", "R1"):
                status = True
            if xmode in ("R1", ):
                filebind.setup()
        elif xmode in ("F2", ):
            if force or prev_xmode in ("F3", "F4"):
                status = elfpatcher.restore_binaries()
            if force or prev_xmode in ("P1", "P2", "F1", "R1"):
                status = elfpatcher.patch_ld()
        elif xmode in ("F3", "F4"):
            if force or prev_xmode in ("P1", "P2", "F1", "F2", "R1"):
                status = (elfpatcher.patch_ld() and
                          elfpatcher.patch_binaries())
            elif prev_xmode in ("F3", "F4"):
                status = True
        if xmode[0] in ("P", "R"):
            if force or prev_xmode.startswith("F"):
                status = FileUtil(self.container_root).links_conv(force, False)
        if status:
            status = FileUtil(self.container_execmode).putdata(xmode)
        if not status:
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
        return self.exec_engine


class ContainerStructure(object):
    """Docker container structure.
    Creation of a container filesystem from a repository image.
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
            Msg().err("Error: create container: imagerepo is invalid")
            return False
        (container_json, layer_files) = self.localrepo.get_image_attributes()
        if not container_json:
            Msg().err("Error: create container: getting layers or json")
            return False
        container_id = Unique().uuid(os.path.basename(self.imagerepo))
        container_dir = self.localrepo.setup_container(
            self.imagerepo, self.tag, container_id)
        if not container_dir:
            Msg().err("Error: create container: setting up container")
            return False
        self.localrepo.save_json(
            container_dir + "/container.json", container_json)
        status = self._untar_layers(layer_files, container_dir + "/ROOT")
        if not status:
            Msg().err("Error: creating container:", container_id)
        self.container_id = container_id
        return container_id

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
            self._apply_whiteouts(tarf, destdir)
            # cmd = "umask 022 ; tar -C %s -x --delay-directory-restore " % \
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

    def get_container_meta(self, param, default, container_json):
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

    def _dict_to_str(self, in_dict):
        """Convert dict to str"""
        out_str = ""
        for (key, val) in in_dict.items():
            out_str += "%s:%s " % (str(key), str(val))
        return out_str

    def _dict_to_list(self, in_dict):
        """Convert dict to list"""
        out_list = []
        for (key, val) in in_dict.items():
            out_list.append("%s:%s" % (str(key), str(val)))
        return out_list


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
            if not os.path.exists(self.homedir):
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
                        Msg().out("Warning: unkwnon file in layer:", f_path,
                                  l=Msg.WAR)
                elif fname in ("TAG", "v1", "v2", "PROTECT"):
                    pass
                else:
                    Msg().out("Warning: unkwnon file in image:", f_path,
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
        pair = buff.decode("utf-8").split(":", 1)
        if len(pair) == 2:
            key = pair[0].strip().lower()
            if key:
                self.data[key] = pair[1].strip()
        elif pair[0].startswith("HTTP/"):
            self.data["X-ND-HTTPSTATUS"] = buff.decode("utf-8").strip()
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
        self.timeout = Config.timeout
        self.ctimeout = Config.ctimeout
        self.download_timeout = Config.download_timeout
        self.agent = Config.http_agent
        self.http_proxy = Config.http_proxy
        self.cache_support = False
        self.insecure = Config.http_insecure
        self._select_implementation()

    # pylint: disable=redefined-variable-type
    # pylint: disable=locally-disabled
    def _select_implementation(self):
        """Select which implementation to use"""
        if GetURLpyCurl().is_available():
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

    def set_proxy(self, http_proxy):
        """Specify a socks http proxy"""
        self.http_proxy = http_proxy

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
        if self.insecure:
            pyc.setopt(pyc.SSL_VERIFYPEER, 0)
            pyc.setopt(pyc.SSL_VERIFYHOST, 0)
        pyc.setopt(pyc.FOLLOWLOCATION, True)
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

    def _mkpycurl(self, pyc, hdr, buf, **kwargs):
        """Prepare curl command line according to invocation options"""
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
        buf = StringIO()
        hdr = CurlHeader()
        pyc = pycurl.Curl()
        url = str(args[0])
        pyc.setopt(pycurl.URL, url)
        self._set_defaults(pyc, hdr)
        try:
            (output_file, filep) = self._mkpycurl(pyc, hdr, buf, **kwargs)
            pyc.perform()
        except(IOError, OSError):
            return(None, None)
        except pycurl.error as error:
            errno, errstr = error.args
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
                Msg().err("Error: in download: " + hdr.data["X-ND-HTTPSTATUS"])
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
        buf = StringIO()
        self._set_defaults()
        cmd = self._mkcurlcmd(*args, **kwargs)
        status = subprocess.call(cmd, shell=True, close_fds=True)
        hdr.setvalue_from_file(self._files["header_file"])
        hdr.data["X-ND-CURLSTATUS"] = status
        if status:
            Msg().err("Error: in download: %s"
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
                Msg().err("Error: in download: ", str(
                    hdr.data["X-ND-HTTPSTATUS"]), ": ", str(status))
                FileUtil(self._files["output_file"]).remove()
            else:  # OK downloaded
                os.rename(self._files["output_file"], kwargs["ofile"])
        else:
            try:
                buf = StringIO(open(self._files["output_file"],
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
        Msg().out("header: %s" % (hdr.data), l=Msg.DBG)
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
        Msg().out("repo url:", url, l=Msg.DBG)
        (hdr, buf) = self._get_url(url, header=["X-Docker-Token: true"])
        try:
            self.v1_auth_header = "Authorization: Token " + \
                hdr.data["x-docker-token"]
            return hdr.data, json.loads(buf.getvalue().decode("utf-8"))
        except (IOError, OSError, AttributeError,
                ValueError, TypeError, KeyError):
            self.v1_auth_header = ""
            return hdr.data, []

    def _get_v1_auth(self, www_authenticate):
        """Authentication for v1 API"""
        if "Token" in www_authenticate:
            return self.v1_auth_header
        else:
            return ""

    def get_v1_image_tags(self, endpoint, imagerepo):
        """Get list of tags in a repo from Docker Hub"""
        url = endpoint + "/v1/repositories/" + imagerepo + "/tags"
        Msg().out("tags url:", url, l=Msg.DBG)
        (hdr, buf) = self._get_url(url)
        try:
            return(hdr.data, json.loads(buf.getvalue().decode("utf-8")))
        except (IOError, OSError, AttributeError, ValueError, TypeError):
            return(hdr.data, [])

    def get_v1_image_tag(self, endpoint, imagerepo, tag):
        """Get list of tags in a repo from Docker Hub"""
        url = endpoint + "/v1/repositories/" + imagerepo + "/tags/" + tag
        Msg().out("tags url:", url, l=Msg.DBG)
        (hdr, buf) = self._get_url(url)
        try:
            return(hdr.data, json.loads(buf.getvalue().decode("utf-8")))
        except (IOError, OSError, AttributeError, ValueError, TypeError):
            return(hdr.data, [])

    def get_v1_image_ancestry(self, endpoint, image_id):
        """Get the ancestry which is an ordered list of layers"""
        url = endpoint + "/v1/images/" + image_id + "/ancestry"
        Msg().out("ancestry url:", url, l=Msg.DBG)
        (hdr, buf) = self._get_url(url)
        try:
            return(hdr.data, json.loads(buf.getvalue().decode("utf-8")))
        except (IOError, OSError, AttributeError, ValueError, TypeError):
            return(hdr.data, [])

    def get_v1_image_json(self, endpoint, layer_id):
        """Get the JSON metadata for a specific layer"""
        url = endpoint + "/v1/images/" + layer_id + "/json"
        Msg().out("json url:", url, l=Msg.DBG)
        filename = self.localrepo.layersdir + "/" + layer_id + ".json"
        if self._get_file(url, filename, 0):
            self.localrepo.add_image_layer(filename)
            return True
        return False

    def get_v1_image_layer(self, endpoint, layer_id):
        """Get a specific layer data file (layer files are tarballs)"""
        url = endpoint + "/v1/images/" + layer_id + "/layer"
        Msg().out("layer url:", url, l=Msg.DBG)
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
                Msg().out("Downloading layer:", layer_id, l=Msg.INF)
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
                token_buf = auth_buf.getvalue().decode("utf-8")
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
        Msg().out("manifest url:", url, l=Msg.DBG)
        (hdr, buf) = self._get_url(url)
        try:
            return(hdr.data, json.loads(buf.getvalue().decode("utf-8")))
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
        Msg().out("layer url:", url, l=Msg.DBG)
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
                Msg().out("Downloading layer:", layer["blobSum"],
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
            Msg().out("v2 layers: %s" % (imagerepo), l=Msg.DBG)
            files = self.get_v2_layers_all(imagerepo,
                                           manifest["fsLayers"])
        except (KeyError, AttributeError, IndexError, ValueError, TypeError) as ex:
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
        Msg().out("v1 image id: %s" % (imagerepo), l=Msg.DBG)
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
        Msg().out("v1 ancestry: %s" % image_id, l=Msg.DBG)
        (dummy, ancestry) = self.get_v1_image_ancestry(endpoint, image_id)
        if not ancestry:
            Msg().err("Error: ancestry not found")
            return []
        self.localrepo.save_json("ancestry", ancestry)
        Msg().out("v1 layers: %s" % image_id, l=Msg.DBG)
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
        Msg().out("get imagerepo: %s tag: %s" % (imagerepo, tag), l=Msg.DBG)
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
            repo_list = json.loads(buf.getvalue().decode("utf-8"))
            if repo_list["page"] == repo_list["num_pages"]:
                self.search_ended = True
                return []
            else:
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
            return json.loads(buf.getvalue().decode("utf-8"))
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
        else:
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
                            Msg().out("Warning: unkwnon file in layer:",
                                      f_path, l=Msg.WAR)
                else:
                    Msg().out("Warning: unkwnon file in image:", f_path,
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
        if not os.path.exists(imagefile):
            Msg().err("Error: image file does not exist: ", imagefile)
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

    def import_(self, tarfile, imagerepo, tag, move_tarball=True):
        """Import a tar file containing a simple directory tree possibly
        created with Docker export"""
        if not os.path.exists(tarfile):
            Msg().err("Error: tar file does not exist: ", tarfile)
            return False
        self.localrepo.setup_imagerepo(imagerepo)
        tag_dir = self.localrepo.cd_imagerepo(imagerepo, tag)
        if tag_dir:
            Msg().err("Error: tag already exists in repo: ", tag)
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
            Msg().out("Warning: localrepo directory is invalid: ", topdir,
                      l=Msg.WAR)
            return False
        self.localrepo.setup(topdir)
        return True

    def _check_imagespec(self, imagespec):
        """Perform the image verification"""
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
            if repo["is_official"]:
                is_official = "[OK]"
            else:
                is_official = "----"
            description = ""
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
        """
        imagefile = cmdp.get("--input=")
        if not imagefile:
            imagefile = cmdp.get("-i=")
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
        import : import image (directory tree) from tar file
        import <tar-file> <repo/image:tag>
        --mv                       :if possible move tar-file instead of copy
        """
        tarfile = cmdp.get("P1")
        move_tarball = cmdp.get("--mv")
        if not tarfile:
            Msg().err("Error: must specify tar filename")
            return False
        (imagerepo, tag) = self._check_imagespec(cmdp.get("P2"))
        if (not imagerepo) or cmdp.missing_options():  # syntax error
            return False
        if self.dockerlocalfileapi.import_(tarfile, imagerepo, tag, move_tarball):
            return True
        else:
            Msg().err("Error: importing file")
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
            Msg().out("Warning: password in uppercase",
                      "Caps Lock ?", l=Msg.WAR)
        v2_auth_token = \
            self.dockerioapi.get_v2_login_token(username, password)
        if self.keystore.put(self.dockerioapi.registry_url, v2_auth_token, ""):
            return True
        else:
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
            files = self.dockerioapi.get(imagerepo, tag)
            if files:
                Msg().out(files)
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
            else:
                return True
        return False

    def _create(self, imagespec):
        """Auxiliary to create(), performs the creation"""
        if not self.dockerioapi.is_repo_name(imagespec):
            Msg().err("Error: must specify image:tag or repository/image:tag")
            return False
        (imagerepo, tag) = self._check_imagespec(imagespec)
        if imagerepo:
            return ContainerStructure(self.localrepo).create(imagerepo, tag)
        return False

    def _get_run_options(self, cmdp, exec_engine=None):
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
        for option, cmdp_args in cmd_options.items():
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
        --entrypoint=<entrypoint>  :overwrite the default entrypoint set by the image
        """
        self._get_run_options(cmdp)
        container_or_image = cmdp.get("P1")
        Config.location = cmdp.get("--location=")
        delete = cmdp.get("--rm")
        name = cmdp.get("--name=")
        #
        if cmdp.missing_options():               # syntax error
            return False
        if Config.location:
            container_id = ""
        else:
            container_id = self.localrepo.get_container_id(container_or_image)
            if not container_id:
                (imagerepo, tag) = self._check_imagespec(container_or_image)
                if (imagerepo and
                        self.localrepo.cd_imagerepo(imagerepo, tag)):
                    container_id = self._create(imagerepo+":"+tag)
                if not container_id:
                    self.do_pull(cmdp)
                    self.localrepo.cd_imagerepo(imagerepo, tag)
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
            else:
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
            else:
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
            else:
                Msg().err("Error: image verification failure")
                return False

    def do_setup(self, cmdp):
        """
        setup: change container execution settings
        setup [options] <container-id>
        --execmode=<Pn>            :select execution mode
        --execmode=<Fn>            :select execution mode
        --force                    :force setup

        execution engines and their execution modes:
        P1: proot accelerated mode using seccomp
        P2: proot accelerated mode disabled
        F1: fakeroot starting executables via direct loader invocation
        F2: similar to F1 with protected environment and modified ld.so
        F3: fakeroot patching elf headers in libraries and executables
        F4: similar to F3 with support for newly created executables via
            dynamic patching elf headers of libraries and executables
        R1: runc rootless
        """
        container_id = cmdp.get("P1")
        xmode = cmdp.get("--execmode=")
        force = cmdp.get("--force")
        if cmdp.missing_options():               # syntax error
            return False
        if not self.localrepo.cd_container(container_id):
            Msg().err("Error: invalid container id")
            return False
        elif xmode and self.localrepo.isprotected_container(container_id):
            Msg().err("Error: container is protected")
            return False
        exec_mode = ExecutionMode(self.localrepo, container_id)
        if xmode:
            return exec_mode.set_mode(xmode.upper(), force)
        else:
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
            Msg().err("Error: install of udockertools failed")

    def do_version(self, cmdp):
        """Print the version number"""
        if cmdp.missing_options():               # syntax error
            return False
        try:
            Msg().out("%s %s" % ("udocker", __version__))
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
          setup                       :Change container execution settings
          login                       :Login into docker repository
          logout                      :Logout from docker repository

          help                        :This help
          run --help                  :Command specific help

        Options common to all commands must appear before the command:
          -D                          :Debug
          --quiet                     :Less verbosity
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
                Msg().out(text)
                return
        except AttributeError:
            pass
        Msg().out(self.do_help.__doc__)


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
        """Parse a command line string passed to the constructor
        divides the string in three blocks: general_options,
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
        while pos < len(opt_list):
            opt_arg = None
            if ((not opt_list[pos].startswith("-")) and
                    (pos < 1 or (pos not in consumed and not
                                 opt_list[pos-1].endswith("=")))):
                break        # end of options and start of arguments
            elif opt_name.endswith("="):
                if opt_list[pos].startswith(opt_name):
                    #opt_arg = opt_list[pos].split("=", 1)[1].strip().strip('"')
                    opt_arg = opt_list[pos].split("=", 1)[1].strip()
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
        else:
            return None


class Main(object):
    """Get options, parse and execute the command line"""

    def __init__(self):
        self.cmdp = CmdParser()
        if not self.cmdp.parse(sys.argv):
            Msg().err("Error: parsing command line, use: udocker help")
            sys.exit(1)
        Config().user_init(self.cmdp.get("--config=", "GEN_OPT"))
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
        if not self.localrepo.is_repo():
            Msg().out("Info: creating repo: " + Config.topdir, l=Msg.INF)
            self.localrepo.create_repo()
        self.udocker = Udocker(self.localrepo)
#        status = UdockerTools(self.localrepo).install()
#        if status is not None and not status:
#            Msg().err("Error: install of udockertools failed")

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
                    self.udocker.do_help(self.cmdp)   # help on command
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
    if not os.geteuid():
        Msg().err("Error: do not run as root !")
        sys.exit(1)
    sys.exit(Main().start())
