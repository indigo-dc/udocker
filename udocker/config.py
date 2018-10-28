# -*- coding: utf-8 -*-
import os
import sys
import pwd
import platform
import logging
from udocker import PY_VER
from msg import Msg
from utils.fileutils import FileUtil
if PY_VER >= '3':
    from configparser import ConfigParser as confparser
else:
    from ConfigParser import SafeConfigParser as confparser


logger = logging.getLogger('udocker')


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
        "/s/AFImjw8ii0X72xf/download"
        " "
        "https://cernbox.cern.ch/index.php"
        "/s/VC7GuVWA7mYRAiy/download"
        " "
        "http://repo.indigo-datacloud.eu/repository"
        "/indigo/2/centos7/x86_64/tgz/udocker-1.1.1.tar.gz"
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
        parser = confparser.ConfigParser()
        parser.read(config_file)
        ver_level = parser.get('DEFAULT', 'verbose_level')
        Msg().setlevel(ver_level)
        return True

    def _read_configOLD(self, config_file):
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

