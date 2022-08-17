# -*- coding: utf-8 -*-
"""Configurations options and treatment/overrinding"""
import os
import sys
from udocker.msg import Msg

# if Python 3
if sys.version_info[0] >= 3:
    from configparser import ConfigParser
else:
    from ConfigParser import ConfigParser


class Config(object):
    """Default configuration values for the whole application. Changes
    to these values should be made via a configuration file read via
    Config.init() and that can reside in ~/.udocker/udocker.conf
    """
    conf = {}
    conf['verbose_level'] = 3
    conf['homedir'] = os.path.expanduser("~") + "/.udocker"
    conf['topdir'] = conf['homedir']
    conf['bindir'] = None
    conf['libdir'] = None
    conf['docdir'] = None
    conf['reposdir'] = None
    conf['layersdir'] = None
    conf['containersdir'] = None

    # udocker installation tarball the release is the minimum requirement
    # the actual tarball used in the installation can have a higher version
    conf['tarball_release'] = "1.2.8"
    conf['tarball'] = (
        "https://download.ncg.ingrid.pt/"
        "webdav/udocker/udocker-englib-1.2.8.tar.gz"
        " "
        "https://raw.githubusercontent.com"
        "/jorge-lip/udocker-builds/master/tarballs/udocker-englib-1.2.8.tar.gz"
    )
    conf['installinfo'] = [
        "https://raw.githubusercontent.com/indigo-dc/udocker/master/messages", ]
    conf['installretry'] = 3
    conf['autoinstall'] = True
    conf['config'] = "udocker.conf"
    conf['keystore'] = "keystore"
    conf['tmpdir'] = os.getenv("TMPDIR", "/tmp")    # for tmp files only

    # defaults for container execution
    conf['cmd'] = ["/bin/bash", "-i"]  # Comand to execute

    # default path for executables
    conf['root_path'] = "/usr/sbin:/sbin:/usr/bin:/bin"
    conf['user_path'] = "/usr/local/bin:/usr/bin:/bin"

    # directories to be mapped in containers with: run --sysdirs
    conf['sysdirs_list'] = ("/dev", "/proc", "/sys",
                            "/etc/resolv.conf", "/etc/host.conf",
                            "/lib/modules", )

    # POSSIBLE DEPRECATED
    # directories to be mapped in containers with: run --hostauth
    # conf['hostauth_list'] = ("/etc/passwd", "/etc/group",
    #                               "/etc/shadow", "/etc/gshadow", )

    # directories for DRI (direct rendering)
    conf['dri_list'] = ("/usr/lib64/dri", "/lib64/dri",
                        "/usr/lib/dri", "/lib/dri", )

    # allowed file mountpoints for runC, these files can be copied in
    conf['mountpoint_prefixes'] = ("/etc", )

    # container execution mode if not set via setup
    # Change it to P2 if execution problems occur
    conf['default_execution_mode'] = "P1"

    # PRoot override seccomp
    # conf['proot_noseccomp'] = True
    conf['proot_noseccomp'] = None
    conf['proot_killonexit'] = True   # PRoot kill-on-exit

    # fakechroot engine get ld_library_paths from ld.so.cache
    conf['ld_so_cache'] = "/etc/ld.so.cache"

    # fakechroot engine override fakechroot.so selection
    # conf['fakechroot_so'] = "libfakechroot-CentOS-7-x86_64.so"
    conf['fakechroot_so'] = None

    # translate symbolic links in pathnames None means automatic
    conf['fakechroot_expand_symlinks'] = None

    # sharable library directories
    conf['lib_dirs_list_x86_64'] = ("/usr/lib/x86_64-linux-gnu",
                                    "/usr/lib64",)

    # fakechroot sharable library directories
    conf['lib_dirs_list_essential'] = ("/lib/x86_64-linux-gnu",
                                       "/usr/lib/x86_64-linux-gnu",
                                       "/lib64", "/usr/lib64", "/lib",
                                       "/usr/lib", )
    conf['lib_dirs_list_append'] = (".", )

    # fakechroot access files, used to circunvent openmpi init issues
    conf['access_files'] = ("/sys/class/infiniband", "/dev/open-mx",
                            "/dev/myri0", "/dev/myri1", "/dev/myri2",
                            "/dev/myri3", "/dev/myri4", "/dev/myri5",
                            "/dev/myri6", "/dev/myri7", "/dev/myri8",
                            "/dev/myri9", "/dev/ipath", "/dev/kgni0",
                            "/dev/mic/scif", "/dev/scif", )

    # Force the use of specific executables
    # UDOCKER = use executable from the udocker binary distribution/tarball
    conf['use_proot_executable'] = "UDOCKER"
    conf['use_runc_executable'] = ""
    conf['use_singularity_executable'] = ""

    # runc parameters
    conf['runc_nomqueue'] = None   # runc parameters
    conf['runc_capabilities'] = [
        "CAP_KILL", "CAP_NET_BIND_SERVICE", "CAP_CHOWN", "CAP_DAC_OVERRIDE",
        "CAP_FOWNER", "CAP_FSETID", "CAP_KILL", "CAP_SETGID", "CAP_SETUID",
        "CAP_SETPCAP", "CAP_NET_BIND_SERVICE", "CAP_NET_RAW",
        "CAP_SYS_CHROOT", "CAP_MKNOD", "CAP_AUDIT_WRITE", "CAP_SETFCAP",
    ]

    # singul. opts -u --nv -w
    conf['singularity_options'] = ["-w", ]

    # Pass host env vars
    conf['valid_host_env'] = ("TERM", "PATH", "PROOT_TMP_DIR", )
    conf['invalid_host_env'] = ("VTE_VERSION", )

    # CPU affinity executables to use with: run --cpuset-cpus="1,2,3-4"
    conf['cpu_affinity_exec_tools'] = (["numactl", "-C", "%s", "--", ],
                                       ["taskset", "-c", "%s", ])

    # Containers execution defaults
    conf['location'] = ""      # run container in this location

    # Curl settings
    conf['http_proxy'] = ""    # ex. socks5://user:pass@127.0.0.1:1080
    conf['timeout'] = 12       # default timeout (secs)
    conf['download_timeout'] = 30 * 60  # file download timeout (secs)
    conf['ctimeout'] = 6       # default TCP connect timeout (secs)
    conf['http_agent'] = ""
    conf['http_insecure'] = False
    conf['use_curl_executable'] = ""  # force use of executable

    # docker hub index
    conf['dockerio_index_url'] = "https://hub.docker.com"
    # docker hub registry
    #conf['dockerio_registry_url'] = "https://registry.hub.docker.com"
    conf['dockerio_registry_url'] = "https://registry-1.docker.io"
    # private repository v2
    # conf['dockerio_registry_url'] = "http://localhost:5000"

    # registries table
    conf['docker_registries'] = {"docker.io": [conf['dockerio_registry_url'],
                                               conf['dockerio_index_url']],
                                }

    # nvidia files
    conf['nvi_etc_list'] = ['vulkan/icd.d/nvidia_icd.json',
                            'OpenCL/vendors/nvidia.icd']

    conf['nvi_bin_list'] = ['nvidia-bug-report.sh',
                            'nvidia-cuda-mps-control',
                            'nvidia-cuda-mps-server',
                            'nvidia-debugdump', 'nvidia-installer',
                            'nvidia-persistenced', 'nvidia-settings',
                            'nvidia-smi', 'nvidia-uninstall',
                            'nvidia-xconfig']

    conf['nvi_lib_list'] = ['libOpenCL.', 'libcuda.', 'libnvcuvid.',
                            'libnvidia-cfg.', 'libnvidia-compiler.',
                            'libnvidia-encode.',
                            'libnvidia-fatbinaryloader.',
                            'libnvidia-fbc.', 'libnvidia-ifr.',
                            'libnvidia-ml.', 'libnvidia-opencl.',
                            'libnvidia-ptxjitcompiler.',
                            'libnvidia-tls.', 'tls/libnvidia-tls.']

    conf['nvi_dev_list'] = ['/dev/nvidia', ]

    def _conf_file_read(self, cfpath, ignore_keys=None):
        """
        Read config file
        """
        Msg().out('Info: using config file: ', cfpath)
        cfnparser = ConfigParser()
        cfnparser.read(cfpath)
        for (key, val) in cfnparser.items('DEFAULT'):
            if ignore_keys and key in ignore_keys:
                continue
            if val is not None:
                Config.conf[key] = val

    def _file_override(self, user_cfile, ignore_keys=None):
        """
        Override values from config file
        """
        if os.path.exists('/etc/' + Config.conf['config']):
            self._conf_file_read('/etc/' + Config.conf['config'], ignore_keys)

        cfpath = Config.conf['homedir'] + '/' + Config.conf['config']
        if os.path.exists(cfpath):
            self._conf_file_read(cfpath, ignore_keys)

        if Config.conf['topdir'] != Config.conf['homedir']:
            cfpath = Config.conf['topdir'] + '/'  + Config.conf['config']
            if os.path.exists(cfpath):
                self._conf_file_read(cfpath, ignore_keys)

        if os.path.exists(user_cfile):
            self._conf_file_read(user_cfile, ignore_keys)

    def _env_override(self):
        """Override config with environment"""
        Config.conf['verbose_level'] = \
            int(os.getenv("UDOCKER_LOGLEVEL", Config.conf['verbose_level']))
        Config.conf['topdir'] = os.getenv("UDOCKER_DIR", Config.conf['topdir'])
        Config.conf['bindir'] = os.getenv("UDOCKER_BIN", Config.conf['bindir'])
        Config.conf['libdir'] = os.getenv("UDOCKER_LIB", Config.conf['libdir'])
        Config.conf['docdir'] = os.getenv("UDOCKER_DOC", Config.conf['docdir'])
        Config.conf['reposdir'] = \
            os.getenv("UDOCKER_REPOS", Config.conf['reposdir'])
        Config.conf['layersdir'] = \
            os.getenv("UDOCKER_LAYERS", Config.conf['layersdir'])
        Config.conf['containersdir'] = \
            os.getenv("UDOCKER_CONTAINERS", Config.conf['containersdir'])
        Config.conf['dockerio_index_url'] = \
            os.getenv("UDOCKER_INDEX", Config.conf['dockerio_index_url'])
        Config.conf['dockerio_registry_url'] = \
            os.getenv("UDOCKER_REGISTRY", Config.conf['dockerio_registry_url'])
        Config.conf['tarball'] = \
            os.getenv("UDOCKER_TARBALL", Config.conf['tarball'])
        Config.conf['default_execution_mode'] = \
            os.getenv("UDOCKER_DEFAULT_EXECUTION_MODE",
                      Config.conf['default_execution_mode'])
        Config.conf['fakechroot_so'] = \
            os.getenv("UDOCKER_FAKECHROOT_SO", Config.conf['fakechroot_so'])
        Config.conf['tmpdir'] = os.getenv("UDOCKER_TMP", Config.conf['tmpdir'])
        Config.conf['keystore'] = \
            os.getenv("UDOCKER_KEYSTORE", Config.conf['keystore'])
        Config.conf['use_curl_executable'] = \
            os.getenv("UDOCKER_USE_CURL_EXECUTABLE",
                      Config.conf['use_curl_executable'])
        Config.conf['use_proot_executable'] = \
            os.getenv("UDOCKER_USE_PROOT_EXECUTABLE",
                      Config.conf['use_proot_executable'])
        Config.conf['use_runc_executable'] = \
            os.getenv("UDOCKER_USE_RUNC_EXECUTABLE",
                      Config.conf['use_runc_executable'])
        Config.conf['use_singularity_executable'] = \
            os.getenv("UDOCKER_USE_SINGULARITY_EXECUTABLE",
                      Config.conf['use_singularity_executable'])

        Config.conf['fakechroot_expand_symlinks'] = \
            os.getenv("UDOCKER_FAKECHROOT_EXPAND_SYMLINKS",
                      str(Config.conf['fakechroot_expand_symlinks'])).lower()
        os.environ["PROOT_TMP_DIR"] = os.getenv("PROOT_TMP_DIR",
                                                Config.conf['tmpdir'])

    def getconf(self, user_cfile="u.conf"):
        """Return all configuration variables"""
        self._file_override(user_cfile) # Override with variables in conf file
        self._env_override()          # Override with variables in environment

    def container(self, user_cfile="u.conf"):
        """
        Load configuration for a container
        Values should be in the form x = y
        """
        ignore_keys = ["topdir", "homedir", "reposdir", "layersdir",
                       "containersdir", "location", ]
        self._file_override(user_cfile, ignore_keys)
