# -*- coding: utf-8 -*-
"""Configurations options and treatment/overrinding"""
import os
import sys
import platform
import pwd
from udocker.msg import Msg
from udocker.helper.osinfo import OSInfo


# Python version major.minor
PY_VER = "%d.%d" % (sys.version_info[0], sys.version_info[1])

if PY_VER >= "3":
    from configparser import ConfigParser
else:
    from ConfigParser import ConfigParser


class Config(object):
    """Default configuration values for the whole application. Changes
    to these values should be made via a configuration file read via
    self.user_init() and that can reside in ~/.udocker/udocker.conf
    """

    def __init__(self, user_cfile="u.conf"):
        """Initialize configuration variables with default values"""
        self.user_cfile = user_cfile
        self.conf = dict()
        self.conf['verbose_level'] = 3
        self.conf['homedir'] = os.path.expanduser("~")
        self.conf['topdir'] = self.conf['homedir'] + "/.udocker"
        self.conf['bindir'] = None
        self.conf['libdir'] = None
        self.conf['reposdir'] = None
        self.conf['layersdir'] = None
        self.conf['containersdir'] = None

        # udocker installation tarball
        tar_url = "https://download.ncg.ingrid.pt/webdav/udocker_test/"
        self.conf['tarball_release'] = "1.2.4"
        self.conf['tarball'] = (tar_url + "udocker-englib-1.2.4.tar.gz")

#        self.conf['tarball'] = (
#           "https://download.ncg.ingrid.pt/webdav/udocker/udocker-1.1.3.tar.gz"
#           " "
#           "https://owncloud.indigo-datacloud.eu/index.php"
#           "/s/iv4FOV1jZcfnGFH/download"
#           " "
#           "https://cernbox.cern.ch/index.php"
#           "/s/CS31ycKOpj2KzxO/download?x-access-token=eyJhbGciOiJIUzI1Ni"
#           "IsInR5cCI6IkpXVCJ9.eyJleHAiOiIyMDE4LTEwLTMwVDE4OjM1OjMyLjI2MD"
#           "AxMDA3OCswMTowMCIsImV4cGlyZXMiOjAsImlkIjoiMTQ1NjgwIiwiaXRlbV9"
#           "0eXBlIjowLCJtdGltZSI6MTU0MDkxNzA3Miwib3duZXIiOiJqb3JnZSIsInBh"
#           "dGgiOiJlb3Nob21lLWo6MjcyNTgzNjk2NDc1NzUwNDAiLCJwcm90ZWN0ZWQiO"
#           "mZhbHNlLCJyZWFkX29ubHkiOnRydWUsInNoYXJlX25hbWUiOiJ1ZG9ja2VyLT"
#           "EuMS4zLnRhci5neiIsInRva2VuIjoiQ1MzMXljS09wajJLenhPIn0._9LTvxM"
#           "V12NpxcZXaCg3PJeQfz94qYui4ccscrrvgVA"
#           )

        self.info = ("https://raw.githubusercontent.com/"
                     "indigo-dc/udocker/master/messages")
        self.conf['installinfo'] = [self.info, ]
        self.conf['autoinstall'] = True
        self.conf['config'] = "udocker.conf"
        self.conf['keystore'] = "keystore"
        self.conf['tmpdir'] = "/tmp"    # for tmp files only

        # defaults for container execution
        self.conf['cmd'] = ["/bin/bash", "-i"]  # Comand to execute

        # default path for executables
        self.conf['root_path'] = "/usr/sbin:/sbin:/usr/bin:/bin"
        self.conf['user_path'] = "/usr/local/bin:/usr/bin:/bin"

        # directories to be mapped in containers with: run --sysdirs
        self.conf['sysdirs_list'] = ("/dev", "/proc", "/sys",
                                     "/etc/resolv.conf", "/etc/host.conf",
                                     "/lib/modules", )

        # directories to be mapped in containers with: run --hostauth
        self.conf['hostauth_list'] = ("/etc/passwd", "/etc/group",
                                      "/etc/shadow", "/etc/gshadow", )

        # directories for DRI (direct rendering)
        self.conf['dri_list'] = ("/usr/lib64/dri", "/lib64/dri",
                                 "/usr/lib/dri", "/lib/dri", )

        # container execution mode if not set via setup
        # Change it to P2 if execution problems occur
        self.conf['default_execution_mode'] = "P1"

        # PRoot override seccomp
        # self.conf['proot_noseccomp'] = True
        self.conf['proot_noseccomp'] = None
        self.conf['proot_killonexit'] = True   # PRoot kill-on-exit

        # fakechroot engine get ld_library_paths from ld.so.cache
        self.conf['ld_so_cache'] = "/etc/ld.so.cache"

        # fakechroot engine override fakechroot.so selection
        # self.conf['fakechroot_so'] = "libfakechroot-CentOS-7-x86_64.so"
        self.conf['fakechroot_so'] = None

        # fakechroot sharable library directories
        self.conf['lib_dirs_list_essential'] = ("/lib/x86_64-linux-gnu",
                                                "/usr/lib/x86_64-linux-gnu",
                                                "/lib64", "/usr/lib64", "/lib",
                                                "/usr/lib", )
        self.conf['lib_dirs_list_append'] = (".", )

        # fakechroot access files, used to circunvent openmpi init issues
        self.conf['access_files'] = ("/sys/class/infiniband", "/dev/open-mx",
                                     "/dev/myri0", "/dev/myri1", "/dev/myri2",
                                     "/dev/myri3", "/dev/myri4", "/dev/myri5",
                                     "/dev/myri6", "/dev/myri7", "/dev/myri8",
                                     "/dev/myri9", "/dev/ipath", "/dev/kgni0",
                                     "/dev/mic/scif", "/dev/scif", )
        self.conf['runc_nomqueue'] = None   # runc parameters
        self.conf['singularity_options'] = ["-w", ]  # singul. opts -u --nv -w
        self.conf['valid_host_env'] = ("TERM", "PATH", )  # Pass host env vars
        self.conf['invalid_host_env'] = ("VTE_VERSION", )

        # CPU affinity executables to use with: run --cpuset-cpus="1,2,3-4"
        self.conf['cpu_affinity_exec_tools'] = (["numactl", "-C", "%s", "--", ],
                                                ["taskset", "-c", "%s", ])

        # Containers execution defaults
        self.conf['location'] = ""      # run container in this location

        # Curl settings
        self.conf['http_proxy'] = ""    # ex. socks5://user:pass@127.0.0.1:1080
        self.conf['timeout'] = 12       # default timeout (secs)
        self.conf['download_timeout'] = 30 * 60  # file download timeout (secs)
        self.conf['ctimeout'] = 6       # default TCP connect timeout (secs)
        self.conf['http_agent'] = ""
        self.conf['http_insecure'] = False
        self.conf['use_curl_exec'] = ""  # force use of executable

        # docker hub v1
        self.conf['dockerio_index_url'] = "https://index.docker.io"
        # docker hub v2
        self.conf['dockerio_registry_url'] = "https://registry-1.docker.io"

        # private repository v2
        # self.conf['dockerio_registry_url'] = "http://localhost:5000"

        # registries table
        self.conf['docker_registries'] = {"docker.io":
                                              ["https://registry-1.docker.io",
                                               "https://index.docker.io"]}

        # nvidia files
        self.conf['nvi_etc_list'] = ['vulkan/icd.d/nvidia_icd.json',
                                     'OpenCL/vendors/nvidia.icd']

        self.conf['nvi_bin_list'] = ['nvidia-bug-report.sh',
                                     'nvidia-cuda-mps-control',
                                     'nvidia-cuda-mps-server',
                                     'nvidia-debugdump', 'nvidia-installer',
                                     'nvidia-persistenced', 'nvidia-settings',
                                     'nvidia-smi', 'nvidia-uninstall',
                                     'nvidia-xconfig']

        self.conf['nvi_lib_list'] = ['libOpenCL.', 'libcuda.', 'libnvcuvid.',
                                     'libnvidia-cfg.', 'libnvidia-compiler.',
                                     'libnvidia-encode.',
                                     'libnvidia-fatbinaryloader.',
                                     'libnvidia-fbc.', 'libnvidia-ifr.',
                                     'libnvidia-ml.', 'libnvidia-opencl.',
                                     'libnvidia-ptxjitcompiler.',
                                     'libnvidia-tls.', 'tls/libnvidia-tls.']

        self.conf['nvi_dev_list'] = ['/dev/nvidia', ]

    def _file_override(self):
        """
        Override values from config file
        """
        cfpath = '/etc/' + self.conf['config']
        if os.path.exists(cfpath):
            Msg().out('Using config file: %s', cfpath)
            config = ConfigParser()
            config.read(cfpath)
            for (key, val) in config.items(['DEFAULT']):
                if val is not None:
                    self.conf[key] = val

        cfpath = self.conf['homedir'] + self.conf['config']
        if os.path.exists(cfpath):
            Msg().out('Using config file: %s', cfpath)
            config = ConfigParser()
            config.read(cfpath)
            for (key, val) in config.items(['DEFAULT']):
                if val is not None:
                    self.conf[key] = val

        cfpath = self.user_cfile
        if os.path.exists(cfpath):
            Msg().out('Using config file: %s', cfpath)
            config = ConfigParser()
            config.read(cfpath)
            for (key, val) in config.items(['DEFAULT']):
                if val is not None:
                    self.conf[key] = val

    def _env_override(self):
        """Override config with environment"""
        self.conf['verbose_level'] = int(os.getenv("UDOCKER_LOGLEVEL",
                                                   self.conf['verbose_level']))
        self.conf['topdir'] = os.getenv("UDOCKER_DIR", self.conf['topdir'])
        self.conf['bindir'] = os.getenv("UDOCKER_BIN", self.conf['bindir'])
        self.conf['libdir'] = os.getenv("UDOCKER_LIB", self.conf['libdir'])
        self.conf['reposdir'] = \
            os.getenv("UDOCKER_REPOS", self.conf['reposdir'])
        self.conf['layersdir'] = \
            os.getenv("UDOCKER_LAYERS", self.conf['layersdir'])
        self.conf['containersdir'] = \
            os.getenv("UDOCKER_CONTAINERS", self.conf['containersdir'])
        self.conf['dockerio_index_url'] = \
            os.getenv("UDOCKER_INDEX", self.conf['dockerio_index_url'])
        self.conf['dockerio_registry_url'] = \
            os.getenv("UDOCKER_REGISTRY", self.conf['dockerio_registry_url'])
        self.conf['tarball'] = \
            os.getenv("UDOCKER_TARBALL", self.conf['tarball'])
        self.conf['fakechroot_so'] = \
            os.getenv("UDOCKER_FAKECHROOT_SO", self.conf['fakechroot_so'])
        self.conf['tmpdir'] = os.getenv("UDOCKER_TMP", self.conf['tmpdir'])
        self.conf['keystore'] = \
            os.getenv("UDOCKER_KEYSTORE", self.conf['keystore'])
        self.conf['use_curl_exec'] = \
            os.getenv("UDOCKER_USE_CURL_EXEC", self.conf['use_curl_exec'])

    def getconf(self):
        """Return all configuration variables"""
        osinfo = OSInfo(self.conf, "")
        self.conf['uid'] = os.getuid()
        self.conf['gid'] = os.getgid()
        self.conf['username'] = pwd.getpwuid(self.conf['uid']).pw_name
        self.conf['oskernel'] = platform.release()
        self.conf['arch'] = osinfo.arch()
        self.conf['osversion'] = osinfo.osversion()
        self.conf['osdistribution'] = osinfo.osdistribution()
        self._file_override()   # Override with variables in conf file
        self._env_override()    # Override with variables in environment
        return self.conf
