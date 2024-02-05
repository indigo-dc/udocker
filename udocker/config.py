# -*- coding: utf-8 -*-
"""Configurations options and treatment/overriding"""
import os
import logging

from configparser import ConfigParser
from udocker import LOG


class Config:
    """ Default configuration values for the whole application. Changes
        to these values should be made via a configuration file read via
        Config.init() and that can reside in ~/.udocker/udocker.conf
    """
    conf = {}
    conf['verbose_level'] = logging.INFO
    conf['homedir'] = os.path.expanduser("~") + "/.udocker"  # dir with keystore file
    conf['topdir'] = conf['homedir']      # dir with images and containers
    conf['installdir'] = conf['topdir']   # dir with exec engines bin, lib and doc licenses
    conf['tardir'] = None
    conf['reposdir'] = None
    conf['layersdir'] = None
    conf['containersdir'] = None

    # udocker installation tarball the release is the minimum requirement
    # the actual tarball used in the installation can have a higher version
    conf['tarball_release'] = "1.2.11"
    conf['tarball'] = (
        "https://download.ncg.ingrid.pt/"
        "webdav/udocker/udocker-englib-1.2.11.tar.gz"
        " "
        "https://raw.githubusercontent.com"
        "/jorge-lip/udocker-builds/master/tarballs/udocker-englib-1.2.11.tar.gz"
    )
    # Either remove, as not been used
    # conf['installinfo'] = ["https://raw.githubusercontent.com/indigo-dc/udocker/master/messages"]

    conf['installretry'] = 3
    conf['autoinstall'] = True
    conf['config'] = 'udocker.conf'
    conf['keystore'] = 'keystore'
    conf['tmpdir'] = os.getenv("TMPDIR", "/tmp")    # for tmp files only

    # new conf options and commands for install
    base_url = ['https://download.ncg.ingrid.pt/webdav/udocker/engines/',
                'https://github.com/LIP-Computing/udocker_tools/raw/main/data/']

    conf['installed_json'] = 'installed.json'
    conf['metadata_json'] = 'metadata.json'
    conf['metadata_url'] = []
    for url in base_url:
        conf['metadata_url'].append(url + conf['metadata_json'])

    # defaults for container execution
    conf['cmd'] = ["bash", "-i"]  # Command to execute

    # default path for executables
    conf['root_path'] = '/usr/sbin:/sbin:/usr/bin:/bin'
    conf['user_path'] = '/usr/local/bin:/usr/bin:/bin'

    # directories to be mapped in containers with: run --sysdirs
    conf['sysdirs_list'] = ("/dev", "/proc", "/sys", "/etc/resolv.conf",
                            "/etc/host.conf", "/lib/modules", )

    # directories for DRI (direct rendering)
    conf['dri_list'] = ("/usr/lib64/dri", "/lib64/dri", "/usr/lib/dri", "/lib/dri", )

    # allowed file mountpoints for runC, these files can be copied in
    conf['mountpoint_prefixes'] = ("/etc", )

    # container execution mode if not set via setup
    # Change it to P2 if execution problems occur
    conf['default_execution_mode'] = "P1"
    conf['override_default_execution_mode'] = ""
    conf['default_execution_modes'] = {'x86_64': "P1", 'x86': "P1",
                                       'arm64': "P1", 'arm': "P2",
                                       'ppc64le': "R1", 'DEFAULT': "R1"}

    # PRoot override seccomp
    conf['proot_noseccomp'] = None
    conf['proot_killonexit'] = True   # PRoot --kill-on-exit
    conf['proot_link2symlink'] = False   # PRoot --link2symlink

    # fakechroot engine get ld_library_paths from ld.so.cache
    conf['ld_so_cache'] = "/etc/ld.so.cache"

    # fakechroot engine override fakechroot.so selection
    conf['fakechroot_so'] = None

    # translate symbolic links into pathnames None means automatic
    conf['fakechroot_expand_symlinks'] = None

    conf['fakechroot_cmd_subst'] = \
        "/sbin/ldconfig=#RETURN(TRUE)#:/usr/sbin/ldconfig=#RETURN(TRUE)#"

    # patterns to search for libc.so in fakechroot
    conf['libc_search'] = ("/usr/lib64/libc.so.[0-9]",
                           "/usr/lib/x86_64-linux-gnu/libc.so.[0-9]",
                           "/lib64/libc.so.[0-9]",
                           "/usr/lib/libc.so.[0-9]",
                           "/lib/libc.so.[0-9]",
                           "/usr/libc.so.[0-9]",
                           "/libc.so.[0-9]",
                           "/libc.so",)

    # override the above search for libc with a specific pathname
    # relative to the container root directory (excluding host prefix)
    conf['fakechroot_libc'] = None

    # sharable library directories
    conf['lib_dirs_list_nvidia'] = ("/usr/lib/x86_64-linux-gnu", "/usr/lib64",)

    # fakechroot sharable library directories
    conf['lib_dirs_list_essential'] = ("/lib/x86_64-linux-gnu", "/usr/lib/x86_64-linux-gnu",
                                       "/lib64", "/usr/lib64", "/lib", "/usr/lib", )
    conf['lib_dirs_list_append'] = (".", )

    # fakechroot access files, used to circumvent openmpi init issues
    conf['access_files'] = ("/sys/class/infiniband", "/dev/open-mx", "/dev/myri0", "/dev/myri1",
                            "/dev/myri2", "/dev/myri3", "/dev/myri4", "/dev/myri5", "/dev/myri6",
                            "/dev/myri7", "/dev/myri8", "/dev/myri9", "/dev/ipath", "/dev/kgni0",
                            "/dev/mic/scif", "/dev/scif", )

    # Force the use of specific executables
    # UDOCKER = use executable from the udocker binary distribution/tarball
    conf['use_proot_executable'] = "UDOCKER"
    conf['use_patchelf_executable'] = "UDOCKER"
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
    conf['cpu_affinity_exec_tools'] = (["numactl", "-C", "%s", "--", ], ["taskset", "-c", "%s", ])

    # Containers execution defaults
    conf['location'] = ''                # run container in this location

    # Curl settings
    conf['http_proxy'] = ''               # ex. socks5://user:pass@127.0.0.1:1080
    conf['timeout'] = 12                  # default timeout (secs)
    conf['download_timeout'] = 30 * 60    # file download timeout (secs)
    conf['ctimeout'] = 6                  # default TCP connect timeout (secs)
    conf['http_agent'] = ''
    conf['http_insecure'] = False
    conf['use_curl_executable'] = ''      # force use of executable

    # docker hub index
    conf['dockerio_index_url'] = "https://hub.docker.com"

    # docker hub registry
    conf['dockerio_registry_url'] = "https://registry-1.docker.io"

    # registries table
    conf['docker_registries'] = {"docker.io": [conf['dockerio_registry_url'],
                                               conf['dockerio_index_url']], }

    # nvidia files
    conf['nvi_etc_list'] = ['vulkan/icd.d/nvidia_icd.json', 'OpenCL/vendors/nvidia.icd']

    conf['nvi_bin_list'] = ['nvidia-bug-report.sh', 'nvidia-cuda-mps-control',
                            'nvidia-cuda-mps-server', 'nvidia-debugdump', 'nvidia-installer',
                            'nvidia-persistenced', 'nvidia-settings', 'nvidia-smi',
                            'nvidia-uninstall', 'nvidia-xconfig']

    conf['nvi_lib_list'] = ['libOpenCL.', 'libcuda.', 'libnvcuvid.', 'libnvidia-cfg.',
                            'libnvidia-compiler.', 'libnvidia-encode.',
                            'libnvidia-fatbinaryloader.', 'libnvidia-fbc.', 'libnvidia-ifr.',
                            'libnvidia-ml.', 'libnvidia-opencl.', 'libnvidia-ptxjitcompiler.',
                            'libnvidia-tls.', 'tls/libnvidia-tls.']

    conf['nvi_dev_list'] = ['/dev/nvidia', ]

    def _conf_file_read(self, cfpath, ignore_keys=None):
        """Read config file"""
        LOG.info('using config file: %s', cfpath)
        cfnparser = ConfigParser()
        cfnparser.read(cfpath)
        for (key, val) in cfnparser.items('DEFAULT'):
            if ignore_keys and key in ignore_keys:
                continue
            if val is not None:
                Config.conf[key] = val

    def _file_override(self, user_cfile, ignore_keys=None):
        """Override values from config file"""
        if os.path.exists('/etc/' + Config.conf['config']):
            self._conf_file_read('/etc/' + Config.conf['config'], ignore_keys)

        cfpath = Config.conf['homedir'] + '/' + Config.conf['config']
        if os.path.exists(cfpath):
            self._conf_file_read(cfpath, ignore_keys)

        if Config.conf['topdir'] != Config.conf['homedir']:
            cfpath = Config.conf['topdir'] + '/' + Config.conf['config']
            if os.path.exists(cfpath):
                self._conf_file_read(cfpath, ignore_keys)

        if os.path.exists(user_cfile):
            self._conf_file_read(user_cfile, ignore_keys)

    def _env_override(self):
        """Override config with environment"""
        Config.conf['verbose_level'] = int(os.getenv("UDOCKER_LOGLEVEL",
                                           Config.conf['verbose_level']))
        Config.conf['topdir'] = os.getenv("UDOCKER_DIR", Config.conf['topdir'])
        Config.conf['installdir'] = os.getenv("UDOCKER_INSTALL", Config.conf['installdir'])
        Config.conf['reposdir'] = os.getenv("UDOCKER_REPOS", Config.conf['reposdir'])
        Config.conf['layersdir'] = os.getenv("UDOCKER_LAYERS", Config.conf['layersdir'])
        Config.conf['containersdir'] = os.getenv("UDOCKER_CONTAINERS",
                                                 Config.conf['containersdir'])
        Config.conf['dockerio_index_url'] = os.getenv("UDOCKER_INDEX",
                                                      Config.conf['dockerio_index_url'])
        Config.conf['dockerio_registry_url'] = os.getenv("UDOCKER_REGISTRY",
                                                         Config.conf['dockerio_registry_url'])
        Config.conf['override_default_execution_mode'] = \
            os.getenv("UDOCKER_DEFAULT_EXECUTION_MODE",
                      Config.conf['override_default_execution_mode'])
        Config.conf['fakechroot_libc'] = \
            os.getenv("UDOCKER_FAKECHROOT_LIBC", Config.conf['fakechroot_libc'])

        Config.conf['default_execution_mode'] = os.getenv("UDOCKER_DEFAULT_EXECUTION_MODE",
                                                          Config.conf['default_execution_mode'])
        Config.conf['fakechroot_so'] = os.getenv("UDOCKER_FAKECHROOT_SO",
                                                 Config.conf['fakechroot_so'])
        Config.conf['tmpdir'] = os.getenv("UDOCKER_TMP", Config.conf['tmpdir'])
        Config.conf['keystore'] = os.getenv("UDOCKER_KEYSTORE", Config.conf['keystore'])
        Config.conf['use_curl_executable'] = os.getenv("UDOCKER_USE_CURL_EXECUTABLE",
                                                       Config.conf['use_curl_executable'])
        Config.conf['use_proot_executable'] = os.getenv("UDOCKER_USE_PROOT_EXECUTABLE",
                                                        Config.conf['use_proot_executable'])
        Config.conf['use_runc_executable'] = os.getenv("UDOCKER_USE_RUNC_EXECUTABLE",
                                                       Config.conf['use_runc_executable'])
        Config.conf['use_singularity_executable'] = \
            os.getenv("UDOCKER_USE_SINGULARITY_EXECUTABLE",
                      Config.conf['use_singularity_executable'])
        Config.conf['use_patchelf_executable'] = \
            os.getenv("UDOCKER_USE_PATCHELF_EXECUTABLE",
                      Config.conf['use_patchelf_executable'])
        Config.conf['fakechroot_cmd_subst'] = \
            os.getenv("UDOCKER_FAKECHROOT_CMD_SUBST",
                      Config.conf['fakechroot_cmd_subst'])

        Config.conf['fakechroot_expand_symlinks'] = \
            os.getenv("UDOCKER_FAKECHROOT_EXPAND_SYMLINKS",
                      str(Config.conf['fakechroot_expand_symlinks'])).lower()

        os.environ["PROOT_TMP_DIR"] = os.getenv("PROOT_TMP_DIR",
                                                Config.conf['tmpdir'])

    def getconf(self, user_cfile="u.conf"):
        """Return all configuration variables"""
        self._file_override(user_cfile)  # Override with variables in conf file
        self._env_override()             # Override with variables in environment
