#!/usr/bin/env python2
"""
udocker unit tests.

Unit tests for udocker, a wrapper to execute basic docker containers
without using docker.

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

import grp
import os
import pwd
import subprocess
import sys
import json
import unittest

try:
    from StringIO import StringIO
except ImportError:
    from io import StringIO

import mock

try:
    import udocker
except ImportError:
    sys.path.append('.')
    sys.path.append('../')
    import udocker

__author__ = "udocker@lip.pt"
__credits__ = ["PRoot http://proot.me"]
__license__ = "Licensed under the Apache License, Version 2.0"
__version__ = "1.1.3"
__date__ = "2019"

STDOUT = sys.stdout
STDERR = sys.stderr
UDOCKER_TOPDIR = "test_topdir"

if sys.version_info[0] >= 3:
    BUILTINS = "builtins"
else:
    BUILTINS = "__builtin__"


def set_env():
    """Set environment variables."""
    if not os.getenv("HOME"):
        os.environ["HOME"] = os.getcwd()


def find_str(self, find_exp, where):
    """Find string in test output messages."""
    found = False
    for item in where:
        if find_exp in str(item):
            self.assertTrue(True)
            found = True
            break
    if not found:
        self.assertTrue(False)


def is_writable_file(obj):
    """Check if obj is a file."""
    try:
        obj.write("")
    except(AttributeError, OSError, IOError):
        return False
    else:
        return True


class ConfigTestCase(unittest.TestCase):
    """Test case for the udocker configuration."""

    @classmethod
    def setUpClass(cls):
        """Setup test."""
        set_env()

    def _verify_config(self, conf):
        """Test Config._verify_config() parameters."""
        self.assertIsInstance(conf.verbose_level, int)
        self.assertIsInstance(conf.topdir, str)
        self.assertIs(conf.bindir, None)
        self.assertIs(conf.libdir, None)
        self.assertIs(conf.reposdir, None)
        self.assertIs(conf.layersdir, None)
        self.assertIs(conf.containersdir, None)
        self.assertIsInstance(conf.homedir, str)
        self.assertIsInstance(conf.config, str)
        self.assertIsInstance(conf.keystore, str)
        self.assertIsInstance(conf.tmpdir, str)
        self.assertIsInstance(conf.tarball, str)
        self.assertIsInstance(conf.cmd, list)
        self.assertIsInstance(conf.sysdirs_list, tuple)
        self.assertIsInstance(conf.dri_list, tuple)
        self.assertIsInstance(conf.cpu_affinity_exec_tools, tuple)
        self.assertIsInstance(conf.location, str)
        self.assertIsInstance(conf.http_proxy, str)
        self.assertIsInstance(conf.timeout, int)
        self.assertIsInstance(conf.download_timeout, int)
        self.assertIsInstance(conf.ctimeout, int)
        self.assertIsInstance(conf.http_agent, str)
        self.assertIsInstance(conf.http_insecure, bool)
        self.assertIsInstance(conf.dockerio_index_url, str)
        self.assertIsInstance(conf.dockerio_registry_url, str)

    def test_01_init(self):
        """Test01 Config() constructor."""
        conf = udocker.Config()
        self._verify_config(conf)

    @mock.patch('udocker.Config.__init__')
    @mock.patch('udocker.Msg')
    def test_02__verify_config(self, mock_msg, mock_conf_init):
        """Test02 Config._verify_config()."""
        mock_conf_init.return_value = None
        udocker.Config.topdir = "/.udocker"
        conf = udocker.Config()
        conf._verify_config()
        self.assertFalse(mock_msg.return_value.err.called)

        mock_conf_init.return_value = None
        udocker.Config.topdir = ""
        conf = udocker.Config()
        with self.assertRaises(SystemExit) as confexpt:
            conf._verify_config()
        self.assertEqual(confexpt.exception.code, 1)

    # def test_03__override_config(self):
    #     """Test03 Config._override_config()."""
    #     pass

    @mock.patch('udocker.FileUtil')
    def test_04__read_config(self, mock_futil):
        """Test04 Config._read_config()."""
        conf = udocker.Config()
        mock_futil.return_value.size.return_value = -1
        status = conf._read_config(conf)
        self.assertFalse(status)

    @mock.patch('udocker.Config._verify_config')
    @mock.patch('udocker.Config._override_config')
    @mock.patch('udocker.Config._read_config')
    @mock.patch('udocker.Msg')
    def test_05_init_good(self, mock_msg,
                          mock_readc, mock_overrride, mock_verify):
        """Test05 Config.init() with good data."""
        udocker.Msg = mock_msg
        conf = udocker.Config()
        conf_data = '# comment\nverbose_level = 100\n'
        conf_data += 'tmpdir = "/xpto"\ncmd = ["/bin/ls", "-l"]\n'
        mock_readc.return_value = conf_data
        conf.init("filename.conf")
        self.assertFalse(mock_verify.called)
        self.assertFalse(mock_overrride.called)
        self.assertTrue(mock_readc.called)

    @mock.patch('udocker.Msg')
    @mock.patch('udocker.FileUtil')
    @mock.patch('udocker.sys.exit')
    def test_06_init_bad(self, mock_exit, mock_fileutil, mock_msg):
        """Test06 Config.init() with bad config data."""
        udocker.Msg = mock_msg
        conf = udocker.Config()
        conf_data = 'hh +=* ffhdklfh\n'
        mock_fileutil.return_value.size.return_value = 10
        mock_fileutil.return_value.getdata.return_value = conf_data
        conf.init("filename.conf")
        self.assertTrue(mock_exit.called)

    @mock.patch('udocker.Config._verify_config')
    @mock.patch('udocker.Config._override_config')
    @mock.patch('udocker.Config._read_config')
    @mock.patch('udocker.Msg')
    def test_07_container(self, mock_msg, mock_readc,
                          mock_overrride, mock_verify):
        """Test07 Config.container()."""
        udocker.Msg = mock_msg
        conf = udocker.Config()
        mock_readc.return_value = True
        conf.container("cfn")
        self.assertTrue(mock_verify.called)
        self.assertTrue(mock_overrride.called)
        self.assertTrue(mock_readc.called)


class UprocessTestCase(unittest.TestCase):
    """Test case for the Uprocess class."""

    @classmethod
    def setUpClass(cls):
        """Setup test."""
        set_env()

    @mock.patch('udocker.subprocess.Popen')
    def test_01__check_output(self, mock_popen):
        """Test01 Uprocess._check_output()."""
        mock_popen.return_value.communicate.return_value = ("OUTPUT", None)
        mock_popen.return_value.poll.return_value = 0
        uproc = udocker.Uprocess()
        status = uproc._check_output("CMD")
        self.assertEqual(status, "OUTPUT")

        mock_popen.return_value.communicate.return_value = ("OUTPUT", None)
        mock_popen.return_value.poll.return_value = 1
        uproc = udocker.Uprocess()
        self.assertRaises(subprocess.CalledProcessError,
                          uproc._check_output, "CMD")

    @mock.patch('udocker.Uprocess._check_output')
    @mock.patch('udocker.subprocess.check_output')
    def test_02_check_output(self, mock_subp_chkout, mock_uproc_chkout):
        """Test02 Uprocess.check_output()."""
        uproc = udocker.Uprocess()
        uproc.check_output("CMD")
        udocker.PY_VER = "%d.%d" % (sys.version_info[0], sys.version_info[1])
        if udocker.PY_VER >= "2.7":
            self.assertTrue(mock_subp_chkout.called)
        else:
            self.assertTrue(mock_uproc_chkout.called)

        # Making sure we cover both cases
        udocker.PY_VER = "3.5"
        uproc.check_output("CMD")
        self.assertTrue(mock_subp_chkout.called)
        udocker.PY_VER = "2.6"
        uproc.check_output("CMD")
        self.assertTrue(mock_uproc_chkout.called)

    @mock.patch('udocker.FileUtil')
    @mock.patch('udocker.Uprocess.check_output')
    def test_03_get_output_01(self, mock_uproc_chkout, mock_futil):
        """Test03 Uprocess.get_output()."""
        mock_uproc_chkout.return_value = "OUTPUT"
        mock_futil.return_value.find_inpath.return_value = "/bin/ls"
        uproc = udocker.Uprocess()
        status = uproc.get_output("/bin/ls")
        self.assertEqual("OUTPUT", status)

    def test_04_get_output_02(self):
        """Test04 Raises Uprocess.get_output()."""
        uproc = udocker.Uprocess()
        self.assertRaises(subprocess.CalledProcessError,
                          uproc.get_output("/bin/false"))

    # def test_05_call(self):
    #     """Test05 Uprocess.call()."""
    #     pass

    # def test_06_pipe(self):
    #     """Test06 Uprocess.pipe()."""
    #     pass


class HostInfoTestCase(unittest.TestCase):
    """Test HostInfo() class."""

    @classmethod
    def setUpClass(cls):
        """Setup test."""
        set_env()

    @mock.patch('udocker.HostInfo.__init__')
    def test_01_username(self, mock_hinfo):
        """Test01 HostInfo.username()."""
        mock_hinfo.return_value = None
        hinfo = udocker.HostInfo()
        user = hinfo.username()
        self.assertEqual(user, pwd.getpwuid(os.getuid()).pw_name)

    @mock.patch('udocker.HostInfo.__init__')
    @mock.patch('udocker.platform.architecture')
    @mock.patch('udocker.platform.machine')
    def test_02_arch(self, mock_machine, mock_architecture, mock_hinfo):
        """Test02 HostInfo.arch()."""
        mock_hinfo.return_value = None
        mock_machine.return_value = "x86_64"
        mock_architecture.return_value = ["32bit", ]
        hinfo = udocker.HostInfo()
        status = hinfo.arch()
        self.assertEqual(status, "i386")

        mock_hinfo.return_value = None
        mock_machine.return_value = "x86_64"
        mock_architecture.return_value = ["", ]
        hinfo = udocker.HostInfo()
        status = hinfo.arch()
        self.assertEqual(status, "amd64")

        mock_hinfo.return_value = None
        mock_machine.return_value = "i686"
        mock_architecture.return_value = ["", ]
        hinfo = udocker.HostInfo()
        status = hinfo.arch()
        self.assertEqual(status, "i386")

        mock_hinfo.return_value = None
        mock_machine.return_value = "armXX"
        mock_architecture.return_value = ["32bit", ]
        hinfo = udocker.HostInfo()
        status = hinfo.arch()
        self.assertEqual(status, "arm")

        mock_hinfo.return_value = None
        mock_machine.return_value = "armXX"
        mock_architecture.return_value = ["", ]
        hinfo = udocker.HostInfo()
        status = hinfo.arch()
        self.assertEqual(status, "arm64")

    @mock.patch('udocker.HostInfo.__init__')
    @mock.patch('udocker.platform.system')
    def test_03_osversion(self, mock_system, mock_hinfo):
        """Test03 HostInfo.osversion()."""
        mock_hinfo.return_value = None
        mock_system.return_value = "Linux"
        hinfo = udocker.HostInfo()
        status = hinfo.osversion()
        self.assertEqual(status, "linux")

        mock_hinfo.return_value = None
        mock_system.return_value = "Linux"
        mock_system.side_effect = NameError('platform system')
        hinfo = udocker.HostInfo()
        status = hinfo.osversion()
        self.assertEqual(status, "")

    @mock.patch('udocker.HostInfo.__init__')
    @mock.patch('udocker.platform.linux_distribution')
    def test_04_osdistribution(self, mock_distribution, mock_hinfo):
        """Test04 HostInfo.osdistribution()."""
        mock_hinfo.return_value = None
        mock_distribution.return_value = ("DISTRO XX", "1.0", "DUMMY")
        hinfo = udocker.HostInfo()
        status = hinfo.osdistribution()
        self.assertEqual(status, ("DISTRO", "1"))

    @mock.patch('udocker.HostInfo.__init__')
    @mock.patch('udocker.platform.release')
    def test_05_oskernel(self, mock_release, mock_hinfo):
        """Test05 HostInfo.oskernel()."""
        mock_hinfo.return_value = None
        mock_release.return_value = "1.2.3"
        hinfo = udocker.HostInfo()
        status = hinfo.oskernel()
        self.assertEqual(status, "1.2.3")

        mock_hinfo.return_value = None
        mock_release.return_value = "1.2.3"
        mock_release.side_effect = NameError('platform release')
        hinfo = udocker.HostInfo()
        status = hinfo.oskernel()
        self.assertEqual(status, "3.2.1")

    @mock.patch('udocker.HostInfo.oskernel')
    @mock.patch('udocker.Msg')
    def test_06_oskernel_isgreater(self, mock_msg, mock_oskern):
        """Test06 HostInfo.oskernel_isgreater()."""
        udocker.Msg = mock_msg
        hinfo = udocker.HostInfo()

        mock_oskern.return_value = "1.1.2-"
        status = hinfo.oskernel_isgreater([1, 1, 1])
        self.assertTrue(status)

        mock_oskern.return_value = "1.2.1-"
        status = hinfo.oskernel_isgreater([1, 1, 1])
        self.assertTrue(status)

        mock_oskern.return_value = "1.0.1-"
        status = hinfo.oskernel_isgreater([1, 1, 1])
        self.assertFalse(status)

    # def test_07_cmd_has_option(self):
    #     """Test07 HostInfo.cmd_has_option()."""
    #     pass

    # def test_08_termsize(self):
    #     """Test08 HostInfo.termsize()."""
    #     pass


class GuestInfoTestCase(unittest.TestCase):
    """Test GuestInfo() class."""

    @classmethod
    def setUpClass(cls):
        """Setup test."""
        set_env()

    def _init(self):
        """Common variables."""
        self.rootdir = "~/.udocker/container/abcd0/ROOT"
        self.file = "/bin/ls"
        self.ftype = "/bin/ls: yyy, x86-64, xxx"
        self.nofile = "ddd: cannot open"
        self.osdist = ("Ubuntu", "16")
        self.noosdist = ("", "xx")

    def test_01_init(self):
        """Test01 GuestInfo() constructor."""
        self._init()
        ginfo = udocker.GuestInfo(self.rootdir)
        self.assertEqual(ginfo._root_dir, self.rootdir)

    @mock.patch('udocker.Uprocess.get_output')
    @mock.patch('udocker.os.path.isfile')
    def test_02_get_filetype(self, mock_isfile, mock_getout):
        """Test02 GuestInfo.get_filetype(filename)"""
        self._init()
        # full filepath exists
        mock_isfile.return_value = True
        mock_getout.return_value = self.ftype
        ginfo = udocker.GuestInfo(self.rootdir)
        self.assertEqual(ginfo.get_filetype(self.file), self.ftype)

        # file does not exist
        mock_isfile.return_value = False
        mock_getout.return_value = self.nofile
        ginfo = udocker.GuestInfo(self.rootdir)
        self.assertEqual(ginfo.get_filetype(self.nofile), "")

    @mock.patch('udocker.GuestInfo.get_filetype')
    def test_03_arch(self, mock_getftype):
        """Test03 GuestInfo.arch()"""
        self._init()
        # arch is x86_64
        filetype = "/bin/ls: yyy, x86-64, xxx"
        mock_getftype.return_value = filetype
        ginfo = udocker.GuestInfo(self.rootdir)
        status = ginfo.arch()
        self.assertEqual(status, "amd64")

    @mock.patch('udocker.os.path.exists')
    @mock.patch('udocker.FileUtil')
    def test_04_osdistribution(self, mock_futil, mock_exists):
        """Test04 GuestInfo.osdistribution()"""
        self._init()
        # has /etc/lsb-release
        lsbdata = "DISTRIB_ID=Ubuntu\n" \
                  "DISTRIB_RELEASE=16.04\n" \
                  "DISTRIB_CODENAME=xenial\n" \
                  "DISTRIB_DESCRIPTION=Ubuntu 16.04.5 LTS\n"
        mock_futil.return_value.match.return_value = ["/etc/lsb-release"]
        mock_exists.return_value = True
        mock_futil.return_value.getdata.return_value = lsbdata
        ginfo = udocker.GuestInfo(self.rootdir)
        self.assertEqual(ginfo.osdistribution(), self.osdist)

        # has /etc/centos-release
        centos_rel = "CentOS release 6.10 (Final)\n"
        c6dist = ("CentOS", "6")
        mock_futil.return_value.match.return_value = ["/etc/centos-release"]
        mock_exists.return_value = True
        mock_futil.return_value.getdata.return_value = centos_rel
        ginfo = udocker.GuestInfo(self.rootdir)
        self.assertEqual(ginfo.osdistribution(), c6dist)

        # has /etc/os-release
        os_rel = '''
            NAME="CentOS Linux"
            VERSION="7 (Core)"
            ID="centos"
            ID_LIKE="rhel fedora"
            VERSION_ID="7"
            PRETTY_NAME="CentOS Linux 7 (Core)"
            ANSI_COLOR="0;31"
            CPE_NAME="cpe:/o:centos:centos:7"
            HOME_URL="https://www.centos.org/"
            BUG_REPORT_URL="https://bugs.centos.org/"

            CENTOS_MANTISBT_PROJECT="CentOS-7"
            CENTOS_MANTISBT_PROJECT_VERSION="7"
            REDHAT_SUPPORT_PRODUCT="centos"
            REDHAT_SUPPORT_PRODUCT_VERSION="7"
            '''

        # c7dist = ("CentOS", "7")
        mock_futil.return_value.match.return_value = ["/etc/os-release"]
        mock_exists.return_value = True
        mock_futil.return_value.getdata.return_value = os_rel
        ginfo = udocker.GuestInfo(self.rootdir)
        # self.assertEqual(ginfo.osdistribution(), c7dist)

    @mock.patch('udocker.GuestInfo.osdistribution')
    def test_05_osversion(self, mock_osdist):
        """Test05 GuestInfo.osversion()"""
        self._init()
        # has osdistro
        mock_osdist.return_value = self.osdist
        ginfo = udocker.GuestInfo(self.rootdir)
        self.assertEqual(ginfo.osversion(), "linux")

        # has no osdistro
        mock_osdist.return_value = self.noosdist
        ginfo = udocker.GuestInfo(self.rootdir)
        self.assertEqual(ginfo.osversion(), "")


# class UnshareTestCase(unittest.TestCase):
#     """Test Unshare()."""

#     @classmethod
#     def setUpClass(cls):
#         """Setup test."""
#         set_env()

#     def test_01_unshare(self):
#         """Test01 Unshare.unshare()."""
#         pass

#     def test_02_namespace_exec(self):
#         """Test02 Unshare.namespace_exec()."""
#         pass


class KeyStoreTestCase(unittest.TestCase):
    """Test KeyStore() local basic credentials storage."""

    @classmethod
    def setUpClass(cls):
        """Setup test."""
        set_env()

    def _init(self):
        """Common variables."""
        self.url = u'https://xxx'
        self.email = u'user@domain'
        self.auth = u'xxx'
        self.credentials = {self.url: {u'email': self.email,
                                       u'auth': self.auth}}

    def test_01_init(self):
        """Test01 KeyStore() constructor."""
        kstore = udocker.KeyStore("filename")
        self.assertEqual(kstore.keystore_file, "filename")

    # def test_02__verify_keystore(self):
    #     """Test02 KeyStore._verify_keystore()."""
    #     pass

    @mock.patch('udocker.json.load')
    def test_03__read_all(self, mock_jload):
        """Test03 KeyStore()._read_all() read credentials."""
        self._init()
        mock_jload.return_value = self.credentials
        with mock.patch(BUILTINS + '.open', mock.mock_open()):
            kstore = udocker.KeyStore("filename")
            self.assertEqual(self.credentials, kstore._read_all())

    @mock.patch('udocker.Config')
    @mock.patch('udocker.KeyStore._verify_keystore')
    def test_04__shred(self, mock_verks, mock_config):
        """Test04 KeyStore()._shred() erase file content size 0."""
        udocker.Config = mock_config
        udocker.Config.tmpdir = "/tmp"
        mock_verks.return_value = None
        with mock.patch(BUILTINS + '.open', mock.mock_open()):
            kstore = udocker.KeyStore("filename")
            self.assertFalse(kstore._shred())

    @mock.patch('udocker.Config')
    @mock.patch('udocker.KeyStore._verify_keystore')
    @mock.patch('udocker.os.stat')
    def test_05__shred(self, mock_stat, mock_verks, mock_config):
        """Test05 KeyStore()._shred() erase file content size > 0."""
        udocker.Config = mock_config
        udocker.Config.tmpdir = "/tmp"
        mock_stat.return_value.st_size = 123
        mock_verks.return_value = None
        with mock.patch(BUILTINS + '.open', mock.mock_open()):
            kstore = udocker.KeyStore("filename")
            self.assertTrue(kstore._shred())

    @mock.patch('udocker.Config')
    @mock.patch('udocker.KeyStore._verify_keystore')
    @mock.patch('udocker.json.dump')
    @mock.patch('udocker.os.umask')
    def test_06__write_all(self, mock_umask, mock_jdump,
                           mock_verks, mock_config):
        """Test06 KeyStore()._write_all() write all credentials to file."""
        self._init()
        udocker.Config = mock_config
        udocker.Config.tmpdir = "/tmp"
        mock_umask.return_value = 0o77
        mock_verks.return_value = None
        mock_jdump.side_effect = IOError('json dump')
        with mock.patch(BUILTINS + '.open', mock.mock_open()):
            kstore = udocker.KeyStore("filename")
            self.assertFalse(kstore._write_all(self.credentials))

    @mock.patch('udocker.Config')
    @mock.patch('udocker.KeyStore._read_all')
    def test_07_get(self, mock_readall, mock_config):
        """Test07 KeyStore().get() get credential for url from file."""
        self._init()
        udocker.Config = mock_config
        udocker.Config.tmpdir = "/tmp"
        mock_readall.return_value = self.credentials
        kstore = udocker.KeyStore("filename")
        self.assertTrue(kstore.get(self.url))
        self.assertFalse(kstore.get("NOT EXISTING ENTRY"))

    @mock.patch('udocker.Config')
    @mock.patch('udocker.KeyStore._shred')
    @mock.patch('udocker.KeyStore._write_all')
    @mock.patch('udocker.KeyStore._read_all')
    def test_08_put(self, mock_readall, mock_writeall, mock_shred,
                    mock_config):
        """Test08 KeyStore().put() put credential for url to file."""
        self._init()
        udocker.Config = mock_config
        udocker.Config.tmpdir = "/tmp"
        mock_shred.return_value = True
        kstore = udocker.KeyStore("filename")
        self.assertFalse(kstore.put("", "", ""))
        mock_readall.return_value = dict()
        kstore.put(self.url, self.auth, self.email)
        mock_writeall.assert_called_once_with(self.credentials)

    @mock.patch('udocker.Config')
    @mock.patch('udocker.KeyStore._verify_keystore')
    @mock.patch('udocker.KeyStore._shred')
    @mock.patch('udocker.KeyStore._write_all')
    @mock.patch('udocker.KeyStore._read_all')
    def test_09_delete(self, mock_readall, mock_writeall, mock_shred,
                       mock_verks, mock_config):
        """Test09 KeyStore().delete() delete credential for url from file."""
        self._init()
        udocker.Config = mock_config
        udocker.Config.tmpdir = "/tmp"
        mock_readall.return_value = self.credentials
        mock_shred.return_value = True
        kstore = udocker.KeyStore("filename")
        kstore.delete(self.url)
        mock_writeall.assert_called_once_with({})
        mock_verks.side_effect = KeyError
        # self.assertFalse(kstore.delete(self.url))

    @mock.patch('udocker.Config')
    @mock.patch('udocker.KeyStore._verify_keystore')
    @mock.patch('udocker.os.remove')
    @mock.patch('udocker.KeyStore._shred')
    def test_10_erase(self, mock_shred, mock_osrm, mock_verks, mock_config):
        """Test10 KeyStore().erase() erase credentials file."""
        self._init()
        udocker.Config = mock_config
        udocker.Config.tmpdir = "/tmp"
        mock_verks.return_value = None
        mock_shred.return_value = True
        mock_osrm.return_value = None
        kstore = udocker.KeyStore("filename")
        status = kstore.erase()
        self.assertTrue(mock_osrm.called)
        self.assertTrue(status)

        mock_verks.return_value = None
        mock_shred.return_value = False
        mock_osrm.side_effect = IOError
        kstore = udocker.KeyStore("filename")
        status = kstore.erase()
        self.assertFalse(status)


class MsgTestCase(unittest.TestCase):
    """Test Msg() class screen error and info messages."""

    @classmethod
    def setUpClass(cls):
        """Setup test."""
        set_env()

    def _verify_descriptors(self, msg):
        """Verify Msg() file descriptors."""
        self.assertTrue(is_writable_file(msg.chlderr))
        self.assertTrue(is_writable_file(msg.chldout))
        self.assertTrue(is_writable_file(msg.chldnul))

    def test_01_init(self):
        """Test01 Msg() constructor."""
        msg = udocker.Msg(0)
        self._verify_descriptors(msg)
        self.assertEqual(msg.level, 0)

    def test_02_setlevel(self):
        """Test02 Msg.setlevel() change of log level."""
        msg = udocker.Msg(5)
        self._verify_descriptors(msg)
        self.assertEqual(msg.level, 5)
        msg = udocker.Msg(0)
        msg.setlevel(7)
        self._verify_descriptors(msg)
        self.assertEqual(msg.level, 7)

    @mock.patch('udocker.sys.stdout', new_callable=StringIO)
    def test_03_out(self, mock_stdout):
        """Test03 Msg.out() screen messages."""
        msg = udocker.Msg(udocker.Msg.MSG)
        msg.out("111", "222", "333", 444, ('555'))
        self.assertEqual("111 222 333 444 555\n", mock_stdout.getvalue())
        sys.stdout = STDOUT
        sys.stderr = STDERR

    @mock.patch('udocker.sys.stderr', new_callable=StringIO)
    def test_04_err(self, mock_stderr):
        """Test04 Msg.err() screen messages."""
        msg = udocker.Msg(udocker.Msg.ERR)
        msg.err("111", "222", "333", 444, ('555'))
        self.assertEqual("111 222 333 444 555\n", mock_stderr.getvalue())
        sys.stdout = STDOUT
        sys.stderr = STDERR


class UniqueTestCase(unittest.TestCase):
    """Test Unique() class."""

    @classmethod
    def setUpClass(cls):
        """Setup test."""
        set_env()

    def test_01_init(self):
        """Test01 Unique() constructor."""
        uniq = udocker.Unique()
        self.assertEqual(uniq.def_name, "udocker")

    def test_02__rnd(self):
        """Test02 Unique._rnd()."""
        uniq = udocker.Unique()
        rand = uniq._rnd(64)
        self.assertIsInstance(rand, str)
        self.assertEqual(len(rand), 64)

    def test_03_uuid(self):
        """Test03 Unique.uuid()."""
        uniq = udocker.Unique()
        rand = uniq.uuid("zxcvbnm")
        self.assertEqual(len(rand), 36)
        rand = uniq.uuid(789)
        self.assertEqual(len(rand), 36)

    def test_04_imagename(self):
        """Test04 Unique.imagename()."""
        uniq = udocker.Unique()
        rand = uniq.imagename()
        self.assertEqual(len(rand), 16)

    def test_05_layer_v1(self):
        """Test05 Unique.layer_v1()."""
        uniq = udocker.Unique()
        rand = uniq.layer_v1()
        self.assertEqual(len(rand), 64)

    def test_06_filename(self):
        """Test06 Unique.filename()."""
        uniq = udocker.Unique()
        rand = uniq.filename("zxcvbnmasdf")
        self.assertTrue(rand.endswith("zxcvbnmasdf"))
        self.assertTrue(rand.startswith("udocker"))
        self.assertGreater(len(rand.strip()), 56)
        rand = uniq.filename(12345)
        self.assertTrue(rand.endswith("12345"))
        self.assertTrue(rand.startswith("udocker"))
        self.assertGreater(len(rand.strip()), 50)


class ChkSUMTestCase(unittest.TestCase):
    """Test ChkSUM() performs checksums portably."""

    @classmethod
    def setUpClass(cls):
        """Setup test."""
        set_env()

    @mock.patch('udocker.hashlib.sha256')
    def test_01_init(self, mock_hashlib_sha):
        """Test01 ChkSUM() constructor."""
        mock_hashlib_sha.return_value = True
        cksum = udocker.ChkSUM()
        self.assertTrue(mock_hashlib_sha.called)

    # def test_02__hashlib(self):
    #     """Test02 ChkSUM()._hashlib()."""
    #     pass

    def test_03__hashlib_sha256(self):
        """Test03 ChkSUM()._hashlib_sha256()."""
        sha256sum = (
            "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855")
        cksum = udocker.ChkSUM()
        file_data = StringIO("qwerty")
        with mock.patch(BUILTINS + '.open', mock.mock_open()) as mopen:
            mopen.return_value.__iter__ = (
                lambda self: iter(file_data.readline, ''))
            status = cksum._hashlib_sha256("filename")
            self.assertEqual(status, sha256sum)

    # def test_04__hashlib_sha512(self):
    #     """Test04 ChkSUM()._hashlib_sha512()."""
    #     pass

    # def test_05__openssl(self):
    #     """Test05 ChkSUM()._openssl()."""
    #     pass

    @mock.patch('udocker.Uprocess.get_output')
    @mock.patch('udocker.Msg')
    def test_06__openssl_sha256(self, mock_msg, mock_subproc):
        """Test06 ChkSUM()._openssl_sha256()."""
        udocker.Msg = mock_msg
        udocker.Msg.return_value.chlderr = open("/dev/null", "w")
        udocker.Msg.chlderr = open("/dev/null", "w")
        mock_subproc.return_value = "123456 "
        cksum = udocker.ChkSUM()
        status = cksum._openssl_sha256("filename")
        self.assertEqual(status, "123456")

    # def test_07__openssl_sha512(self):
    #     """Test07 ChkSUM()._openssl_sha512()."""
    #     pass

    # def test_08_sha256(self):
    #     """Test08 ChkSUM().sha256()."""
    #     mock_call = mock.MagicMock()
    #     cksum = udocker.ChkSUM()
    #     mock_call.return_value = True
    #     cksum._sha256_call = mock_call
    #     status = cksum.sha256("filename")
    #     self.assertTrue(status)

    #     mock_call.return_value = False
    #     cksum._sha256_call = mock_call
    #     status = cksum.sha256("filename")
    #     self.assertFalse(status)

    # def test_09_sha512(self):
    #     """Test09 ChkSUM().sha512()."""
    #     pass

    def test_10_hash(self):
        """Test10 ChkSUM().hash()."""
        sha256sum = (
            "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855")
        cksum = udocker.ChkSUM()
        file_data = StringIO("qwerty")
        with mock.patch(BUILTINS + '.open', mock.mock_open()) as mopen:
            mopen.return_value.__iter__ = (
                lambda self: iter(file_data.readline, ''))
            status = cksum.hash("filename", "sha256")
            self.assertEqual(status, sha256sum)

        sha512sum = ("cf83e1357eefb8bdf1542850d66d8007d620e4050b"
                     "5715dc83f4a921d36ce9ce47d0d13c5d85f2b0ff831"
                     "8d2877eec2f63b931bd47417a81a538327af927da3e")
        cksum = udocker.ChkSUM()
        file_data = StringIO("qwerty")
        with mock.patch(BUILTINS + '.open', mock.mock_open()) as mopen:
            mopen.return_value.__iter__ = (
                lambda self: iter(file_data.readline, ''))
            status = cksum.hash("filename", "sha512")
            self.assertEqual(status, sha512sum)


class FileUtilTestCase(unittest.TestCase):
    """Test FileUtil() file manipulation methods."""

    @classmethod
    def setUpClass(cls):
        """Setup test."""
        set_env()

    @mock.patch('udocker.Config')
    def test_01_init(self, mock_config):
        """Test01 FileUtil() constructor."""
        udocker.Config = mock_config
        udocker.Config.tmpdir = "/tmp"
        futil = udocker.FileUtil("filename.txt")
        self.assertEqual(futil.filename, os.path.abspath("filename.txt"))
        self.assertTrue(udocker.Config.tmpdir)

        mock_config.side_effect = AttributeError("abc")
        futil = udocker.FileUtil()
        self.assertEqual(futil.filename, None)

    @mock.patch('udocker.os.path.realpath')
    @mock.patch('udocker.os.path.isdir')
    def test_02__register_prefix(self, mock_isdir, mock_rpath):
        """Test02 FileUtil._register_prefix()."""
        mock_isdir.return_value = True
        mock_rpath.return_value = "/dir/somefile"
        futil = udocker.FileUtil("somefile")
        futil.safe_prefixes = ["somefile1", "somefile2"]
        futil._register_prefix("somefile")
        self.assertTrue(mock_rpath.called)

    @mock.patch('udocker.FileUtil._register_prefix')
    def test_03_register_prefix(self, mock_regpref):
        """Test03 FileUtil.register_prefix()."""
        mock_regpref.return_value = None
        futil = udocker.FileUtil("somefile")
        futil.register_prefix()
        self.assertTrue(mock_regpref.called)

    @mock.patch('udocker.FileUtil._register_prefix')
    @mock.patch('udocker.os.umask')
    def test_04_umask(self, mock_umask, mock_regpref):
        """Test04 FileUtil.umask()."""
        mock_umask.return_value = 0
        mock_regpref.return_value = None
        futil = udocker.FileUtil("somedir")
        status = futil.umask()
        self.assertTrue(status)

        mock_umask.return_value = 0
        mock_regpref.return_value = None
        futil = udocker.FileUtil("somedir")
        udocker.FileUtil.orig_umask = 0
        status = futil.umask(1)
        self.assertTrue(status)
        self.assertEqual(udocker.FileUtil.orig_umask, 0)

        mock_umask.return_value = 0
        mock_regpref.return_value = None
        futil = udocker.FileUtil("somedir")
        udocker.FileUtil.orig_umask = None
        status = futil.umask(1)
        self.assertTrue(status)
        self.assertEqual(udocker.FileUtil.orig_umask, 0)

    def test_05_mktmp(self):
        """Test05 FileUtil.mktmp()."""
        udocker.Config.tmpdir = "/somewhere"
        tmp_file = udocker.FileUtil("filename2.txt").mktmp()
        self.assertTrue(tmp_file.endswith("-filename2.txt"))
        self.assertTrue(tmp_file.startswith("/somewhere/udocker-"))
        self.assertGreater(len(tmp_file.strip()), 68)

    @mock.patch('udocker.os.makedirs')
    def test_06_mkdir(self, mock_mkdirs):
        """Test06 FileUtil.mkdir Create directory"""
        mock_mkdirs.return_value = None
        futil = udocker.FileUtil("somedir")
        status = futil.mkdir()
        self.assertTrue(status)

        futil = udocker.FileUtil("somedir")
        mock_mkdirs.side_effect = OSError("fail")
        status = futil.mkdir()
        # self.assertFalse(status)

    @mock.patch('udocker.FileUtil')
    @mock.patch('udocker.os.rmdir')
    def test_07_rmdir(self, mock_rmdir, mock_futil):
        """Test07 FileUtil.rmdir."""
        mock_rmdir.return_value = True
        status = mock_futil.rmdir()
        self.assertTrue(status)

        mock_rmdir.side_effect = OSError("fail")
        status = mock_futil.rmdir()
        # self.assertFalse(status)

    @mock.patch('udocker.FileUtil.mktmp')
    @mock.patch('udocker.FileUtil.mkdir')
    def test_08_mktmpdir(self, mock_umkdir, mock_umktmp):
        """Test08 FileUtil.mktmpdir()."""
        mock_umktmp.return_value = "/dir"
        mock_umkdir.return_value = True
        futil = udocker.FileUtil("somedir")
        status = futil.mktmpdir()
        self.assertEqual(status, "/dir")

        mock_umktmp.return_value = "/dir"
        mock_umkdir.return_value = False
        futil = udocker.FileUtil("somedir")
        status = futil.mktmpdir()
        self.assertEqual(status, None)

    @mock.patch('udocker.os.stat')
    def test_09_uid(self, mock_stat):
        """Test09 FileUtil.uid()."""
        mock_stat.return_value.st_uid = 1234
        uid = udocker.FileUtil("filename3.txt").uid()
        self.assertEqual(uid, 1234)

    def test_10__is_safe_prefix(self):
        """Test10 FileUtil._is_safe_prefix()."""
        futil = udocker.FileUtil("somedir")
        udocker.FileUtil.safe_prefixes = []
        status = futil._is_safe_prefix("/AAA")
        self.assertFalse(status)

        futil = udocker.FileUtil("somedir")
        udocker.FileUtil.safe_prefixes = ["/AAA", ]
        status = futil._is_safe_prefix("/AAA")
        self.assertTrue(status)

    @mock.patch('udocker.FileUtil._chmod')
    def test_11_chown(self, mock_fchmod):
        """Test11 FileUtil.chown()."""
        mock_fchmod.return_value = None
        futil = udocker.FileUtil("somefile")
        status = futil.chown()
        self.assertTrue(mock_fchmod.called)
        self.assertTrue(status)

    # def test_12_rchown(self):
    #     """Test12 FileUtil.rchown()."""
    #     pass

    # def test_13__chmod(self):
    #     """Test13 FileUtil._chmod()."""
    #     pass

    @mock.patch('udocker.FileUtil._chmod')
    def test_14_chmod(self, mock_fchmod):
        """Test14 FileUtil.chmod()."""
        mock_fchmod.return_value = None
        futil = udocker.FileUtil("somefile")
        status = futil.chmod()
        self.assertTrue(mock_fchmod.called)
        self.assertTrue(status)

    # def test_14_rchmod(self):
    #     """Test14 FileUtil.rchmod()."""
    #     pass

    # def test_15__removedir(self):
    #     """Test15 FileUtil._removedir()."""
    #     pass

    @mock.patch('udocker.Config')
    @mock.patch('udocker.os.path.realpath')
    @mock.patch('udocker.os.path.exists')
    @mock.patch('udocker.os.remove')
    @mock.patch('udocker.os.path.islink')
    @mock.patch('udocker.os.path.isfile')
    @mock.patch('udocker.os.path.isdir')
    @mock.patch('udocker.FileUtil.uid')
    @mock.patch('udocker.FileUtil._is_safe_prefix')
    def test_16_remove_file(self, mock_safe, mock_uid, mock_isdir,
                            mock_isfile, mock_islink, mock_remove,
                            mock_exists, mock_realpath, mock_config):
        """Test16 FileUtil.remove() with plain files."""
        # file does not exist (regression of #50)
        mock_uid.return_value = os.getuid()
        mock_isdir.return_value = True
        mock_isfile.return_value = True
        mock_islink.return_value = False
        mock_remove.return_value = None
        mock_exists.return_value = True
        mock_safe.return_value = True
        udocker.Config = mock_config
        udocker.Config.uid = os.getuid()
        udocker.Config.tmpdir = "/tmp"
        mock_realpath.return_value = "/tmp"

        # under /
        futil = udocker.FileUtil("/filename4.txt")
        status = futil.remove()
        self.assertFalse(status)

        # wrong uid
        mock_uid.return_value = os.getuid() + 1
        futil = udocker.FileUtil("/tmp/filename4.txt")
        status = futil.remove()
        self.assertFalse(status)

        # under /tmp
        mock_uid.return_value = os.getuid()
        futil = udocker.FileUtil("/tmp/filename4.txt")
        status = futil.remove()
        self.assertTrue(status)

        # under user home
        futil = udocker.FileUtil("/home/user/.udocker/filename4.txt")
        futil.safe_prefixes.append("/home/user/.udocker")
        status = futil.remove()
        self.assertTrue(status)

        # outside of scope 1
        mock_safe.return_value = False
        futil = udocker.FileUtil("/etc/filename4.txt")
        futil.safe_prefixes = []
        status = futil.remove()
        self.assertFalse(status)

    @mock.patch('udocker.Config')
    @mock.patch('udocker.os.path.exists')
    @mock.patch('udocker.subprocess.call')
    @mock.patch('udocker.os.path.isdir')
    @mock.patch('udocker.os.path.islink')
    @mock.patch('udocker.os.path.isfile')
    @mock.patch('udocker.FileUtil.uid')
    @mock.patch('udocker.FileUtil._is_safe_prefix')
    def test_17_remove_dir(self, mock_safe, mock_uid, mock_isfile,
                           mock_islink, mock_isdir, mock_call,
                           mock_exists, mock_config):
        """Test17 FileUtil.remove() with directories."""
        mock_uid.return_value = os.getuid()
        mock_isfile.return_value = False
        mock_islink.return_value = False
        mock_isdir.return_value = False
        mock_exists.return_value = True
        mock_safe.return_value = True
        mock_call.return_value = 0
        udocker.Config = mock_config
        udocker.Config.uid = os.getuid()
        udocker.Config.tmpdir = "/tmp"
        # remove directory under /tmp OK
        futil = udocker.FileUtil("/tmp/directory")
        status = futil.remove()
        self.assertTrue(status)

        # remove directory under /tmp NOT OK
        mock_isfile.return_value = False
        mock_islink.return_value = False
        mock_isdir.return_value = True
        mock_exists.return_value = True
        mock_safe.return_value = True
        mock_call.return_value = 1
        udocker.Config = mock_config
        udocker.Config.uid = os.getuid()
        udocker.Config.tmpdir = "/tmp"
        futil = udocker.FileUtil("/tmp/directory")
        status = futil.remove()
        self.assertFalse(status)

    @mock.patch('udocker.Msg')
    @mock.patch('udocker.subprocess.call')
    @mock.patch('udocker.os.path.isfile')
    def test_18_verify_tar(self, mock_isfile, mock_call, mock_msg):
        """Test18 FileUtil.verify_tar() check tar file False."""
        # check tar file False
        mock_msg.level = 0
        mock_isfile.return_value = False
        mock_call.return_value = 0
        status = udocker.FileUtil("tarball.tar").verify_tar()
        self.assertFalse(status)

        # check tar file True
        mock_msg.level = 0
        mock_isfile.return_value = True
        mock_call.return_value = 0
        status = udocker.FileUtil("tarball.tar").verify_tar()
        self.assertTrue(status)

        # check tar file True call 1
        mock_msg.level = 0
        mock_isfile.return_value = True
        mock_call.return_value = 1
        status = udocker.FileUtil("tarball.tar").verify_tar()
        self.assertFalse(status)

    # def test_19_copydir(self):
    #     """Test19 FileUtil.copydir()."""
    #     pass

    @mock.patch('udocker.Config')
    @mock.patch('udocker.FileUtil.remove')
    def test_20_cleanup(self, mock_remove, mock_config):
        """Test20 FileUtil.cleanup() delete tmp files."""
        udocker.Config = mock_config
        udocker.Config.tmpdir = "/tmp"
        udocker.FileUtil.tmptrash = {'file1.txt': None, 'file2.txt': None}
        udocker.FileUtil("").cleanup()
        self.assertEqual(mock_remove.call_count, 2)

    @mock.patch('udocker.os.path.isdir')
    def test_21_isdir(self, mock_isdir):
        """Test21 FileUtil.isdir()."""
        mock_isdir.return_value = True
        status = udocker.FileUtil("somedir").isdir()
        self.assertTrue(status)
        mock_isdir.return_value = False
        status = udocker.FileUtil("somedir").isdir()
        self.assertFalse(status)

    @mock.patch('udocker.os.stat')
    def test_22_size(self, mock_stat):
        """Test22 FileUtil.size() get file size."""
        mock_stat.return_value.st_size = 4321
        size = udocker.FileUtil("somefile").size()
        self.assertEqual(size, 4321)

    def test_23_getdata(self):
        """Test23 FileUtil.getdata() get file content."""
        with mock.patch(BUILTINS + '.open',
                        mock.mock_open(read_data='qwerty')):
            data = udocker.FileUtil("somefile").getdata()
            self.assertEqual(data, 'qwerty')

    def test_24_get1stline(self):
        """Test24 FileUtil.get1stline()."""
        data = "line1\n" \
               "line2\n" \
               "line3\n"
        with mock.patch(BUILTINS + '.open',
                        mock.mock_open(read_data=data)):
            data = udocker.FileUtil("somefile").get1stline()
            self.assertEqual(data, 'line1')

    def test_25_putdata(self):
        """Test25 FileUtil.putdata()"""
        futil = udocker.FileUtil("somefile")
        futil.filename = ""
        data = futil.putdata("qwerty")
        self.assertFalse(data)

        with mock.patch(BUILTINS + '.open', mock.mock_open()):
            data = udocker.FileUtil("somefile").putdata("qwerty")
            self.assertEqual(data, 'qwerty')

    @mock.patch('udocker.os.path.exists')
    def test_26_getvalid_path(self, mock_pexist):
        """Test26 FileUtil.getvalid_path()."""
        mock_pexist.return_value = True
        futil = udocker.FileUtil("/somedir/somefile")
        status = futil.getvalid_path()
        self.assertEqual(status, "/somedir/somefile")

    # def test_27__find_exec(self):
    #     """Test27 FileUtil._find_exec()."""
    #     pass

    @mock.patch('udocker.Uprocess')
    def test_28_find_exec(self, mock_call):
        """Test28 FileUtil.find_exec() find executable."""
        mock_call.return_value.get_output.return_value = None
        filename = udocker.FileUtil("executable").find_exec()
        self.assertEqual(filename, "")

        mock_call.return_value.get_output.return_value = "/bin/ls"
        filename = udocker.FileUtil("executable").find_exec()
        self.assertEqual(filename, "/bin/ls")

        mock_call.return_value.get_output.return_value = "not found"
        filename = udocker.FileUtil("executable").find_exec()
        self.assertEqual(filename, "")

    @mock.patch('udocker.os.path.lexists')
    def test_29_find_inpath(self, mock_exists):
        """Test29 FileUtil.find_inpath() file is in a path."""
        # exist
        mock_exists.return_value = True
        filename = udocker.FileUtil("exec").find_inpath("/bin:/usr/bin")
        self.assertEqual(filename, "/bin/exec")

        # does not exist
        mock_exists.return_value = False
        filename = udocker.FileUtil("exec").find_inpath("/bin:/usr/bin")
        self.assertEqual(filename, "")

        # exist PATH=
        mock_exists.return_value = True
        filename = udocker.FileUtil("exec").find_inpath("PATH=/bin:/usr/bin")
        self.assertEqual(filename, "/bin/exec")

        # does not exist PATH=
        mock_exists.return_value = False
        filename = udocker.FileUtil("exec").find_inpath("PATH=/bin:/usr/bin")
        self.assertEqual(filename, "")

    @mock.patch('udocker.FileUtil._register_prefix')
    def test_30_list_inpath(self, mock_regpref):
        """Test30 FileUtil.list_inpath()."""
        path = "/bin"
        mock_regpref.return_value = None
        futil = udocker.FileUtil("somefile")
        status = futil.list_inpath(path)
        self.assertEqual(status, ["/bin/somefile"])

    @mock.patch('udocker.os.rename')
    def test_31_rename(self, mock_rename):
        """Test31 FileUtil.rename()."""
        mock_rename.return_value = None
        status = udocker.FileUtil("somefile").rename("otherfile")
        self.assertTrue(status)

    # def test_32__stream2file(self):
    #     """Test32 FileUtil._stream2file()."""
    #     pass

    # def test_33__file2stream(self):
    #     """Test33 FileUtil._file2stream()."""
    #     pass

    # def test_34__file2file(self):
    #     """Test34 FileUtil._file2file()."""
    #     pass

    def test_35_copyto(self):
        """Test35 FileUtil.copyto() file copy."""
        with mock.patch(BUILTINS + '.open', mock.mock_open()):
            status = udocker.FileUtil("source").copyto("dest")
            self.assertTrue(status)
            status = udocker.FileUtil("source").copyto("dest", "w")
            self.assertTrue(status)
            status = udocker.FileUtil("source").copyto("dest", "a")
            self.assertTrue(status)

    @mock.patch('udocker.os.path.exists')
    def test_36_find_file_in_dir(self, mock_exists):
        """Test36 FileUtil.find_file_in_dir()."""
        file_list = []
        status = udocker.FileUtil("/dir").find_file_in_dir(file_list)
        self.assertEqual(status, "")

        file_list = ["F1", "F2"]
        mock_exists.side_effect = [False, False]
        status = udocker.FileUtil("/dir").find_file_in_dir(file_list)
        self.assertEqual(status, "")

        file_list = ["F1", "F2"]
        mock_exists.side_effect = [False, True]
        status = udocker.FileUtil("/dir").find_file_in_dir(file_list)
        self.assertEqual(status, "/dir/F2")

    @mock.patch('udocker.os.symlink')
    @mock.patch('udocker.os.remove')
    @mock.patch('udocker.os.stat')
    @mock.patch('udocker.os.chmod')
    @mock.patch('udocker.os.access')
    @mock.patch('udocker.os.path.dirname')
    @mock.patch('udocker.os.path.realpath')
    @mock.patch('udocker.os.readlink')
    def test_37__link_change_apply(self, mock_readlink,
                                   mock_realpath, mock_dirname,
                                   mock_access, mock_chmod, mock_stat,
                                   mock_remove, mock_symlink):
        """Test37 FileUtil._link_change_apply Apply the link convertion."""
        mock_readlink.return_value = "/HOST/DIR"
        mock_realpath.return_value = "/HOST/DIR"
        mock_dirname.return_value = "/HOST"
        mock_access.return_value = True
        futil = udocker.FileUtil("/con")
        futil._link_change_apply("/con/lnk_new", "/con/lnk", False)
        self.assertTrue(mock_remove.called)
        self.assertTrue(mock_symlink.called)

        mock_access.return_value = False
        mock_remove.reset_mock()
        mock_symlink.reset_mock()
        futil = udocker.FileUtil("/con")
        futil._link_change_apply("/con/lnk_new", "/con/lnk", True)
        self.assertTrue(mock_chmod.called)
        self.assertTrue(mock_remove.called)
        self.assertTrue(mock_symlink.called)

    @mock.patch('udocker.os.symlink')
    @mock.patch('udocker.os.remove')
    @mock.patch('udocker.os.stat')
    @mock.patch('udocker.os.chmod')
    @mock.patch('udocker.os.access')
    @mock.patch('udocker.os.path.dirname')
    @mock.patch('udocker.os.path.realpath')
    @mock.patch('udocker.os.readlink')
    def test_38__link_set(self, mock_readlink, mock_realpath, mock_dirname,
                          mock_access, mock_chmod, mock_stat, mock_remove,
                          mock_symlink):
        """Test38 FileUtil._link_set()."""
        mock_readlink.return_value = "X"
        mock_dirname.return_value = "/HOST"
        futil = udocker.FileUtil("/con")
        status = futil._link_set("/con/lnk", "", "/con", False)
        self.assertFalse(status)

        mock_readlink.return_value = "/con"
        futil = udocker.FileUtil("/con")
        status = futil._link_set("/con/lnk", "", "/con", False)
        self.assertFalse(status)

        mock_readlink.return_value = "/HOST/DIR"
        mock_realpath.return_value = "/HOST/DIR"
        mock_remove.reset_mock()
        mock_symlink.reset_mock()
        mock_chmod.reset_mock()
        futil = udocker.FileUtil("/con")
        status = futil._link_set("/con/lnk", "", "/con", False)
        self.assertTrue(mock_remove.called)
        self.assertTrue(mock_symlink.called)
        self.assertFalse(mock_chmod.called)
        self.assertTrue(status)

        mock_readlink.return_value = "/HOST/DIR"
        mock_realpath.return_value = "/HOST/DIR"
        mock_access.return_value = True
        mock_remove.reset_mock()
        mock_symlink.reset_mock()
        mock_chmod.reset_mock()
        futil = udocker.FileUtil("/con")
        status = futil._link_set("/con/lnk", "", "/con", True)
        self.assertTrue(mock_remove.called)
        self.assertTrue(mock_symlink.called)
        self.assertFalse(mock_chmod.called)
        self.assertTrue(status)

        mock_readlink.return_value = "/HOST/DIR"
        mock_realpath.return_value = "/HOST/DIR"
        mock_access.return_value = False
        mock_remove.reset_mock()
        mock_symlink.reset_mock()
        mock_chmod.reset_mock()
        futil = udocker.FileUtil("/con")
        status = futil._link_set("/con/lnk", "", "/con", True)
        self.assertTrue(mock_remove.called)
        self.assertTrue(mock_symlink.called)
        self.assertTrue(mock_chmod.called)
        self.assertTrue(status)

    @mock.patch('udocker.os.symlink')
    @mock.patch('udocker.os.remove')
    @mock.patch('udocker.os.stat')
    @mock.patch('udocker.os.chmod')
    @mock.patch('udocker.os.access')
    @mock.patch('udocker.os.path.dirname')
    @mock.patch('udocker.os.path.realpath')
    @mock.patch('udocker.os.readlink')
    def test_39__link_restore(self, mock_readlink, mock_realpath,
                              mock_dirname, mock_access, mock_chmod,
                              mock_stat, mock_remove, mock_symlink):
        """Test39 FileUtil._link_restore()."""
        mock_readlink.return_value = "/con/AAA"
        futil = udocker.FileUtil("/con")
        status = futil._link_restore("/con/lnk", "/con", "/root", False)
        self.assertTrue(status)

        mock_readlink.return_value = "/con/AAA"
        mock_symlink.reset_mock()
        mock_chmod.reset_mock()
        futil = udocker.FileUtil("/con")
        status = futil._link_restore("/con/lnk", "/con", "/root", False)
        self.assertTrue(status)
        self.assertTrue(mock_symlink.called_with("/con/lnk", "/AAA"))

        mock_readlink.return_value = "/root/BBB"
        mock_symlink.reset_mock()
        mock_chmod.reset_mock()
        futil = udocker.FileUtil("/con")
        status = futil._link_restore("/con/lnk", "/con", "/root", False)
        self.assertTrue(status)
        self.assertTrue(mock_symlink.called_with("/con/lnk", "/BBB"))

        mock_readlink.return_value = "/XXX"
        futil = udocker.FileUtil("/con")
        status = futil._link_restore("/con/lnk", "/con", "/root", False)
        self.assertFalse(status)

        mock_readlink.return_value = "/root/BBB"
        mock_symlink.reset_mock()
        mock_chmod.reset_mock()
        futil = udocker.FileUtil("/con")
        status = futil._link_restore("/con/lnk", "/con", "/root", True)
        self.assertTrue(status)
        self.assertTrue(mock_symlink.called_with("/con/lnk", "/BBB"))
        self.assertFalse(mock_chmod.called)

        mock_readlink.return_value = "/root/BBB"
        mock_access.return_value = False
        mock_symlink.reset_mock()
        mock_chmod.reset_mock()
        futil = udocker.FileUtil("/con")
        status = futil._link_restore("/con/lnk", "", "/root", True)
        self.assertTrue(status)
        self.assertTrue(mock_symlink.called_with("/con/lnk", "/BBB"))
        self.assertTrue(mock_chmod.called)
        self.assertTrue(mock_remove.called)
        self.assertTrue(mock_symlink.called)

    @mock.patch('udocker.FileUtil._link_restore')
    @mock.patch('udocker.FileUtil._link_set')
    @mock.patch('udocker.Msg')
    @mock.patch('udocker.FileUtil._is_safe_prefix')
    @mock.patch('udocker.os.lstat')
    @mock.patch('udocker.os.path.islink')
    @mock.patch('udocker.os.walk')
    @mock.patch('udocker.os.path.realpath')
    def test_40_links_conv(self, mock_realpath, mock_walk, mock_islink,
                           mock_lstat, mock_is_safe_prefix, mock_msg,
                           mock_link_set, mock_link_restore):
        """Test40 FileUtil.links_conv()."""
        mock_realpath.return_value = "/ROOT"
        mock_is_safe_prefix.return_value = False
        status = udocker.FileUtil("/ROOT").links_conv(False, True, "")
        self.assertEqual(status, None)

        mock_realpath.return_value = "/ROOT"
        mock_is_safe_prefix.return_value = True
        mock_walk.return_value = []
        status = udocker.FileUtil("/ROOT").links_conv(False, True, "")
        self.assertEqual(status, [])

        mock_realpath.return_value = "/ROOT"
        mock_is_safe_prefix.return_value = True
        mock_walk.return_value = [("/", [], []), ]
        status = udocker.FileUtil("/ROOT").links_conv(False, True, "")
        self.assertEqual(status, [])

        mock_realpath.return_value = "/ROOT"
        mock_is_safe_prefix.return_value = True
        mock_islink = False
        mock_walk.return_value = [("/", [], ["F1", "F2"]), ]
        status = udocker.FileUtil("/ROOT").links_conv(False, True, "")
        self.assertEqual(status, [])

        mock_realpath.return_value = "/ROOT"
        mock_is_safe_prefix.return_value = True
        mock_islink = True
        mock_lstat.return_value.st_uid = 1
        udocker.Config.uid = 0
        mock_walk.return_value = [("/", [], ["F1", "F2"]), ]
        status = udocker.FileUtil("/ROOT").links_conv(False, True, "")
        self.assertEqual(status, [])

        mock_realpath.return_value = "/ROOT"
        mock_is_safe_prefix.return_value = True
        mock_islink = True
        mock_lstat.return_value.st_uid = 1
        mock_link_set.reset_mock()
        mock_link_restore.reset_mock()
        udocker.Config.uid = 1
        mock_walk.return_value = [("/", [], ["F1", "F2"]), ]
        status = udocker.FileUtil("/ROOT").links_conv(False, True, "")
        # self.assertTrue(mock_link_set.called)
        self.assertFalse(mock_link_restore.called)

        mock_realpath.return_value = "/ROOT"
        mock_is_safe_prefix.return_value = True
        mock_islink = True
        mock_lstat.return_value.st_uid = 1
        mock_link_set.reset_mock()
        mock_link_restore.reset_mock()
        udocker.Config.uid = 1
        mock_walk.return_value = [("/", [], ["F1", "F2"]), ]
        status = udocker.FileUtil("/ROOT").links_conv(False, False, "")
        self.assertFalse(mock_link_set.called)
        # self.assertTrue(mock_link_restore.called)

    @mock.patch('udocker.os.listdir')
    @mock.patch('udocker.os.path.isdir')
    @mock.patch('udocker.os.path.basename')
    @mock.patch('udocker.os.path.dirname')
    @mock.patch('udocker.FileUtil._register_prefix')
    def test_41_match(self, mock_regpref, mock_dir, mock_base,
                      mock_isdir, mock_listdir):
        """Test41 FileUtil.match()."""
        mock_regpref.return_value = None
        mock_dir.return_value = "/dir"
        mock_base.return_value = "file*"
        mock_isdir.return_value = False
        futil = udocker.FileUtil("/dir")
        status = futil.match()
        self.assertEqual(status, [])

        mock_regpref.return_value = None
        mock_dir.return_value = "/dir"
        mock_base.return_value = "file*"
        mock_isdir.return_value = True
        mock_listdir.return_value = ["file1", "file2"]
        futil = udocker.FileUtil("/dir")
        status = futil.match()
        self.assertEqual(status, ["/dir/file1", "/dir/file2"])


class UdockerToolsTestCase(unittest.TestCase):
    """Test UdockerTools() download and setup of tools needed by udocker."""

    @classmethod
    def setUpClass(cls):
        """Setup test."""
        set_env()

    @mock.patch('udocker.GetURL')
    @mock.patch('udocker.LocalRepository')
    @mock.patch('udocker.Config')
    def test_01_init(self, mock_config, mock_localrepo, mock_geturl):
        """Test01 UdockerTools() constructor."""
        mock_geturl.return_value = None
        udocker.Config = mock_config
        udocker.Config.tmpdir = "/tmp"
        udocker.Config.tarball = "/tmp/xxx"
        udocker.Config.installinfo = "/tmp/xxx"
        udocker.Config._tarball_release = "0.0.0"
        localrepo = mock_localrepo
        localrepo.bindir = "/bindir"
        utools = udocker.UdockerTools(localrepo)
        self.assertEqual(utools.localrepo, localrepo)

    @mock.patch('udocker.Msg')
    @mock.patch('udocker.LocalRepository')
    def test_02__instructions(self, mock_localrepo, mock_msg):
        """Test02 UdockerTools._instructions()."""
        utools = udocker.UdockerTools(mock_localrepo)
        utools._instructions()
        self.assertTrue(mock_msg.return_value.out.called)

    @mock.patch('udocker.LocalRepository')
    @mock.patch('udocker.FileUtil')
    def test_03__get_version(self, futil, mock_localrepo):
        """Test03 UdockerTools._get_version()."""
        futil.return_value.getdata.return_value = "0.0.0"
        utools = udocker.UdockerTools(mock_localrepo)
        utools._tarball_release = "0.0.0"
        status = utools._get_version("versionfile")
        self.assertEqual(status, "0.0.0")

    @mock.patch('udocker.LocalRepository')
    @mock.patch('udocker.FileUtil')
    def test_04__version_isequal(self, futil, mock_localrepo):
        """Test04 UdockerTools._version_isequal()."""
        futil.return_value.getdata.return_value = "0.0.0"
        utools = udocker.UdockerTools(mock_localrepo)
        utools._tarball_release = "0.0.0"
        status = utools._version_isequal("0.0.0")
        self.assertTrue(status)

        futil.return_value.getdata.return_value = "0.0.0"
        utools = udocker.UdockerTools(mock_localrepo)
        utools._tarball_release = "1.1.1"
        status = utools._version_isequal("0.0.0")
        self.assertFalse(status)

    @mock.patch('udocker.UdockerTools._version_isequal')
    @mock.patch('udocker.LocalRepository')
    def test_05_is_available(self, mock_localrepo, mock_version_isequal):
        """Test05 UdockerTools.is_available()."""
        mock_version_isequal.return_value = False
        utools = udocker.UdockerTools(mock_localrepo)
        status = utools.is_available()
        self.assertFalse(status)

        mock_version_isequal.return_value = True
        utools = udocker.UdockerTools(mock_localrepo)
        status = utools.is_available()
        self.assertTrue(status)

    @mock.patch('udocker.GetURL')
    @mock.patch('udocker.FileUtil')
    @mock.patch('udocker.UdockerTools.__init__')
    def test_06__download(self, mock_init, mock_futil, mock_gurl):
        """Test06 UdockerTools._download()."""
        mock_init.return_value = None
        utools = udocker.UdockerTools(None)
        utools.curl = mock_gurl
        utools._tarball = "http://node.domain/filename.tgz"
        hdr = udocker.CurlHeader()
        hdr.data["X-ND-HTTPSTATUS"] = "200"
        hdr.data["X-ND-CURLSTATUS"] = 0
        mock_futil.return_value.mktmp.return_value = "tmptarball"
        mock_gurl.get.return_value = (hdr, "")
        status = utools._download(utools._tarball)
        self.assertEqual(status, "tmptarball")

        hdr.data["X-ND-HTTPSTATUS"] = "400"
        hdr.data["X-ND-CURLSTATUS"] = 1
        status = utools._download(utools._tarball)
        self.assertEqual(status, "")

    @mock.patch('udocker.GetURL')
    @mock.patch('udocker.os.path.isfile')
    @mock.patch('udocker.os.path.realpath')
    @mock.patch('udocker.os.path.exists')
    @mock.patch('udocker.UdockerTools._download')
    def test_07__get_file(self, mock_download, mock_exists,
                          mock_rpath, mock_isfile, mock_gurl):
        """Test07 UdockerTools._get_file()."""
        mock_download.return_value = "file1"
        mock_exists.return_value = False
        mock_isfile.return_value = True
        url = "http://my.com/file1"
        utools = udocker.UdockerTools(None)
        utools.curl = mock_gurl
        status = utools._get_file(url)
        self.assertTrue(mock_download.called)
        self.assertTrue(mock_isfile.called)
        self.assertEqual(status, "file1")

        mock_exists.return_value = True
        mock_isfile.return_value = True
        mock_rpath.return_value = "file1"
        url = "/dir/file1"
        utools = udocker.UdockerTools(None)
        utools.curl = mock_gurl
        status = utools._get_file(url)
        self.assertTrue(mock_rpath.called)
        self.assertTrue(mock_isfile.called)
        self.assertEqual(status, "file1")

    @mock.patch('udocker.os.path.isfile')
    @mock.patch('udocker.UdockerTools._version_isequal')
    @mock.patch('udocker.Msg')
    @mock.patch('udocker.subprocess.call')
    @mock.patch('udocker.FileUtil')
    @mock.patch('udocker.UdockerTools.__init__')
    def test_08__verify_version(self, mock_init, mock_futil, mock_call,
                                mock_msg, mock_versioneq, mock_isfile):
        """Test08 UdockerTools._verify_version()."""
        mock_init.return_value = None
        mock_isfile.return_value = False
        utools = udocker.UdockerTools(None)
        mock_futil.return_value.mktmp.return_value = ""
        status = utools._verify_version("tarballfile")
        self.assertEqual(status, (False, ''))

        mock_msg.level = 0
        mock_call.return_value = 1
        mock_isfile.return_value = True
        status = utools._verify_version("tarballfile")
        self.assertEqual(status, (False, ''))

        mock_call.return_value = 0
        mock_versioneq.return_value = False
        mock_isfile.return_value = True
        status = utools._verify_version("tarballfile")
        # self.assertEqual(status, (False, ''))

        mock_call.return_value = 0
        mock_versioneq.return_value = True
        mock_isfile.return_value = True
        status = utools._verify_version("tarballfile")
        self.assertTrue(status)

    @mock.patch('udocker.FileUtil')
    @mock.patch('udocker.os.listdir')
    @mock.patch('udocker.LocalRepository')
    def test_09_purge(self, mock_localrepo, mock_listdir, mock_futil):
        """Test09 UdockerTools.purge()."""
        mock_listdir.return_value = []
        utools = udocker.UdockerTools(mock_localrepo)
        utools.purge()
        self.assertFalse(mock_futil.return_value.remove.called)

        mock_listdir.return_value = ["F1", "F2"]
        utools = udocker.UdockerTools(mock_localrepo)
        utools.purge()
        self.assertTrue(mock_futil.return_value.remove.called)

    @mock.patch('udocker.os.path.isfile')
    @mock.patch('udocker.UdockerTools._install')
    @mock.patch('udocker.UdockerTools._verify_version')
    @mock.patch('udocker.LocalRepository')
    @mock.patch('udocker.Msg')
    @mock.patch('udocker.subprocess.call')
    @mock.patch('udocker.UdockerTools.__init__')
    def test_10__install(self, mock_init, mock_call, mock_msg, mock_local,
                         mock_ver_version, mock_ins, mock_isfile):
        """Test10 UdockerTools._install()."""
        mock_init.return_value = None
        utools = udocker.UdockerTools(None)
        utools.localrepo = mock_local
        mock_local.bindir = ""
        mock_msg.level = 0
        mock_call.return_value = 1
        mock_ver_version.return_value = False
        mock_ins.return_value = False
        mock_isfile.return_value = False
        status = utools._install("tarballfile")
        self.assertFalse(status)

        mock_call.return_value = 0
        mock_ver_version.return_value = True
        mock_ins.return_value = True
        mock_isfile.return_value = True
        status = utools._install("tarballfile")
        self.assertTrue(status)

    @mock.patch('udocker.LocalRepository')
    @mock.patch('udocker.GetURL')
    def test_11__get_mirrors(self, mock_geturl, mock_localrepo):
        """Test11 UdockerTools._get_mirrors()."""
        mock_geturl.return_value = None
        mirrors = "https://download.ncg.ingrid.pt/udocker-1.1.3.tar.gz"
        utools = udocker.UdockerTools(mock_localrepo)
        status = utools._get_mirrors(mirrors)
        self.assertEqual(status, [mirrors])

    @mock.patch.object(udocker.UdockerTools, '_get_file')
    @mock.patch.object(udocker.UdockerTools, '_get_mirrors')
    @mock.patch('udocker.json.load')
    @mock.patch('udocker.LocalRepository')
    @mock.patch('udocker.GetURL')
    def test_12_get_installinfo(self, mock_geturl, mock_localrepo, mock_jload,
                                mock_getmirr, mock_getfile):
        """Test12 UdockerTools.get_installinfo()."""
        mock_geturl.return_value = None
        mirrors = "https://download.ncg.ingrid.pt/udocker-1.1.3.tar.gz"
        mock_getmirr.return_value = [mirrors]
        mock_getfile.return_value = "udocker-1.1.3.tar.gz"
        dictdata = {"architecture": "amd64",
                     "messages": {"AttachStderr": False}}
        json_data = json.dumps(dictdata)
        mock_jload.return_value = dictdata
        with mock.patch(BUILTINS + '.open',
                        mock.mock_open(read_data=json_data)):
            utools = udocker.UdockerTools(mock_localrepo)
            data = utools.get_installinfo()
            self.assertEqual(data, dictdata)

    @mock.patch.object(udocker.UdockerTools, '_install')
    @mock.patch.object(udocker.UdockerTools, '_verify_version')
    @mock.patch.object(udocker.UdockerTools, '_get_file')
    @mock.patch.object(udocker.UdockerTools, '_get_mirrors')
    @mock.patch('udocker.FileUtil.remove')
    @mock.patch('udocker.Msg')
    @mock.patch('udocker.LocalRepository')
    @mock.patch('udocker.GetURL')
    def test_13__install_logic(self, mock_geturl, mock_localrepo, mock_msg,
                               mock_futilrm, mock_getmirr, mock_getfile,
                               mock_ver, mock_inst):
        """Test13 UdockerTools._install_logic()."""
        mock_geturl.return_value = None
        mock_futilrm.return_value = None
        mirrors = "https://download.ncg.ingrid.pt/udocker-1.1.3.tar.gz"
        mock_getmirr.return_value = [mirrors]
        mock_getfile.return_value = "udocker-1.1.3.tar.gz"
        mock_ver.return_value = (True, "1.1.3")
        mock_inst.return_value = True
        utools = udocker.UdockerTools(mock_localrepo)
        status = utools._install_logic()
        self.assertTrue(mock_getmirr.called)
        self.assertEqual(mock_msg.call_count, 2)
        self.assertTrue(mock_getfile.called)
        self.assertTrue(mock_inst.called)
        self.assertTrue(status)

        mock_geturl.return_value = None
        mock_futilrm.return_value = None
        mirrors = "https://download.ncg.ingrid.pt/udocker-1.1.3.tar.gz"
        mock_getmirr.return_value = [mirrors]
        mock_getfile.return_value = "udocker-1.1.3.tar.gz"
        mock_ver.return_value = (False, "1.1.3")
        utools = udocker.UdockerTools(mock_localrepo)
        status = utools._install_logic()
        self.assertEqual(mock_msg.call_count, 4)
        self.assertFalse(status)

    @mock.patch('udocker.Config')
    @mock.patch('udocker.Msg')
    @mock.patch('udocker.LocalRepository')
    @mock.patch('udocker.GetURL')
    @mock.patch.object(udocker.UdockerTools, 'get_installinfo')
    @mock.patch.object(udocker.UdockerTools, '_install_logic')
    @mock.patch.object(udocker.UdockerTools, '_instructions')
    @mock.patch.object(udocker.UdockerTools, 'is_available')
    def test_14_install(self, mock_is, mock_instr, mock_install, mock_getinst,
                        mock_geturl, mock_localrepo, mock_msg, mock_config):
        """Test14 UdockerTools.install()"""
        # Is available no force
        mock_geturl.return_value = None
        mock_is.return_value = True
        utools = udocker.UdockerTools(mock_localrepo)
        status = utools.install()
        self.assertTrue(mock_is.called)
        self.assertTrue(status)

        # No autoinstall
        mock_geturl.return_value = None
        mock_is.return_value = False
        utools = udocker.UdockerTools(mock_localrepo)
        utools._autoinstall = False
        status = utools.install()
        self.assertTrue(mock_is.called)
        self.assertTrue(mock_msg().err.called)
        self.assertFalse(status)

        # No tarball
        mock_geturl.return_value = None
        mock_is.return_value = False
        mock_getinst.return_value = "JSONinstall"
        utools = udocker.UdockerTools(mock_localrepo)
        utools._autoinstall = True
        utools._tarball = ""
        status = utools.install()
        self.assertTrue(mock_is.called)
        self.assertTrue(mock_msg().err.called)
        self.assertTrue(mock_instr.called)
        self.assertTrue(mock_getinst.called)
        self.assertFalse(status)

        # Download ok
        mock_geturl.return_value = None
        mock_is.return_value = False
        mock_install.return_value = True
        mock_getinst.return_value = "JSONinstall"
        udocker.Config = mock_config
        udocker.Config.autoinstall = True
        udocker.Config.installretry = 1
        utools = udocker.UdockerTools(mock_localrepo)
        utools._tarball = "http://node.domain/filename.tgz"
        status = utools.install()
        self.assertTrue(mock_install.called)
        self.assertTrue(mock_msg().err.called)
        self.assertTrue(mock_getinst.called)
        self.assertTrue(status)


class ElfPatcherTestCase(unittest.TestCase):
    """Test ElfPatcher: Patch container executables."""

    @classmethod
    def setUpClass(cls):
        """Setup test."""
        set_env()

    @mock.patch('udocker.os.path.realpath')
    @mock.patch('udocker.LocalRepository')
    def test_01_init(self, mock_local, mock_rpath):
        """ Test01 ElfPatcher constructor."""
        mock_rpath.return_value = "/cont/ROOT"
        container_id = "SOME-RANDOM-ID"
        udocker.ElfPatcher(mock_local, container_id)
        self.assertTrue(mock_rpath.called)

    @mock.patch('udocker.sys.exit')
    @mock.patch('udocker.os.path.realpath')
    @mock.patch('udocker.Msg')
    @mock.patch('udocker.HostInfo.arch')
    @mock.patch('udocker.FileUtil')
    @mock.patch('udocker.LocalRepository')
    def test_02_select_patchelf(self, mock_local, mock_futil,
                                mock_arch, mock_msg, mock_rpath, mock_exit):
        """Test02 ElfPatcher().select_patchelf(). Set patchelf executable."""
        container_id = "SOME-RANDOM-ID"
        mock_arch.return_value = "amd64"
        mock_futil.return_value.find_file_in_dir.return_value = "patchelf-x86_64"
        mock_rpath.return_value = "/ROOT"
        elfp = udocker.ElfPatcher(mock_local, container_id)
        output = elfp.select_patchelf()
        self.assertEqual(output, "patchelf-x86_64")

        mock_futil.return_value.find_file_in_dir.return_value = ""
        mock_exit.return_value = None
        elfp = udocker.ElfPatcher(mock_local, container_id)
        elfp.select_patchelf()
        self.assertTrue(mock_msg.return_value.err.called)
        self.assertTrue(mock_exit.called)

    @mock.patch('udocker.os.path.realpath')
    @mock.patch('udocker.LocalRepository')
    def test_03__replace(self, mock_local, mock_rpath):
        """ Test03 ElfPatcher()._replace()."""
        container_id = "SOME-RANDOM-ID"
        cmd = ["#f", "-al"]
        path = "/bin/ls"
        mock_rpath.return_value = "/ROOT"
        elfp = udocker.ElfPatcher(mock_local, container_id)
        status = elfp._replace(cmd, path)
        self.assertEqual(status, ["/bin/ls", "-al"])

    @mock.patch('udocker.os.path.islink')
    @mock.patch('udocker.os.path.stat')
    @mock.patch('udocker.os.path')
    @mock.patch('udocker.os.walk')
    @mock.patch('udocker.os.access')
    @mock.patch('udocker.LocalRepository')
    def test_04__walk_fs(self, mock_local, mock_access, mock_walk,
                         mock_path, mock_stat, mock_islink):
        """Test04 ElfPatcher()._walk_fs()."""
        container_id = "SOME-RANDOM-ID"
        mock_walk.return_value = [('/tmp', ('dir',), ('file',)), ]
        mock_islink.return_value = False
        mock_stat.return_value.st_uid = ""
        elfp = udocker.ElfPatcher(mock_local, container_id)
        status = elfp._walk_fs("cmd", "/tmp", elfp.BIN)
        self.assertFalse(status)

    @mock.patch('udocker.os.path')
    @mock.patch('udocker.LocalRepository')
    @mock.patch('udocker.ElfPatcher._walk_fs')
    @mock.patch('udocker.ElfPatcher.select_patchelf')
    def test_05_guess_elf_loader(self, mock_spelf, mock_walk,
                                 mock_local, mock_path):
        """Test05 ElfPatcher().guess_elf_loader()."""
        container_id = "SOME-RANDOM-ID"
        mock_spelf.return_value = "ld.so"
        mock_walk.return_value = ""
        elfp = udocker.ElfPatcher(mock_local, container_id)
        self.assertEqual(elfp.guess_elf_loader(), "")

        mock_walk.return_value = "ld.so"
        elfp = udocker.ElfPatcher(mock_local, container_id)
        self.assertEqual(elfp.guess_elf_loader(), "ld.so")

    @mock.patch('udocker.os.path')
    @mock.patch('udocker.os.path.exists')
    @mock.patch('udocker.LocalRepository')
    @mock.patch('udocker.FileUtil.getdata')
    @mock.patch('udocker.ElfPatcher.guess_elf_loader')
    def test_06_get_original_loader(self, mock_guess, mock_futils,
                                    mock_local, mock_exists, mock_path):
        """Test06 ElfPatcher().get_original_loader()."""
        container_id = "SOME-RANDOM-ID"
        mock_exists.return_value = True
        mock_futils.return_value.strip.return_value = "ld.so"
        elfp = udocker.ElfPatcher(mock_local, container_id)
        self.assertEqual(elfp.get_original_loader(), "ld.so")

        mock_exists.return_value = False
        mock_guess.return_value = "ld.so"
        mock_futils.return_value.strip.return_value = "ld.so"
        elfp = udocker.ElfPatcher(mock_local, container_id)
        self.assertEqual(elfp.get_original_loader(), "ld.so")

    @mock.patch('udocker.os.path')
    @mock.patch('udocker.os.path.exists')
    @mock.patch('udocker.LocalRepository')
    @mock.patch('udocker.ElfPatcher.get_original_loader')
    def test_07_get_container_loader(self, mock_gol, mock_local,
                                     mock_exists, mock_path):
        """Test07 ElfPatcher().get_container_loader()."""
        container_id = "SOME-RANDOM-ID"
        mock_gol.return_value = ""
        elfp = udocker.ElfPatcher(mock_local, container_id)
        self.assertEqual(elfp.get_container_loader(), "")

        mock_exists.return_value = True
        mock_gol.return_value = "ld.so"
        elfp = udocker.ElfPatcher(mock_local, container_id)
        self.assertEqual(elfp.get_container_loader(),
                         elfp._container_root + "/" + "ld.so")

    @mock.patch('udocker.os.path')
    @mock.patch('udocker.os.path.exists')
    @mock.patch('udocker.LocalRepository')
    @mock.patch('udocker.FileUtil.getdata')
    def test_08_get_patch_last_path(self, mock_getdata, mock_local,
                                    mock_exists, mock_path):
        """Test08 ElfPatcher().get_patch_last_path()."""
        container_id = "SOME-RANDOM-ID"
        mock_getdata.return_value = ""
        elfp = udocker.ElfPatcher(mock_local, container_id)
        self.assertEqual(elfp.get_patch_last_path(), "")

        mock_getdata.return_value = "/tmp"
        elfp = udocker.ElfPatcher(mock_local, container_id)
        self.assertEqual(elfp.get_patch_last_path(), "/tmp")

    @mock.patch('udocker.os.path')
    @mock.patch('udocker.os.path.exists')
    @mock.patch('udocker.LocalRepository')
    @mock.patch('udocker.ElfPatcher.get_patch_last_path')
    @mock.patch('udocker.Msg')
    def test_09_check_container_path(self, mock_msg, mock_lpath,
                                     mock_local, mock_exists, mock_path):
        """Test09 ElfPatcher().check_container_path()."""
        container_id = "SOME-RANDOM-ID"
        mock_lpath.return_value = "/tmp"
        elfp = udocker.ElfPatcher(mock_local, container_id)
        status = elfp.check_container_path()
        self.assertFalse(status)

    @mock.patch('udocker.os.path')
    @mock.patch('udocker.os.path.exists')
    @mock.patch('udocker.LocalRepository')
    @mock.patch('udocker.FileUtil.getdata')
    def test_10_get_patch_last_time(self, mock_getdata, mock_local,
                                    mock_exists, mock_path):
        """Test10 ElfPatcher().get_patch_last_time()."""
        container_id = "SOME-RANDOM-ID"
        mock_getdata.return_value = "30"
        elfp = udocker.ElfPatcher(mock_local, container_id)
        self.assertEqual(elfp.get_patch_last_time(), "30")

    @mock.patch('udocker.os.path')
    @mock.patch('udocker.os.path.exists')
    @mock.patch('udocker.LocalRepository')
    @mock.patch('udocker.FileUtil.putdata')
    @mock.patch('udocker.ElfPatcher.guess_elf_loader')
    @mock.patch('udocker.ElfPatcher.select_patchelf')
    @mock.patch('udocker.ElfPatcher.get_container_loader')
    @mock.patch('udocker.ElfPatcher')
    def test_11_patch_binaries(self, mock_elfp, mock_gcl, mock_select,
                               mock_guess, mock_putdata, mock_local,
                               mock_exists, mock_path):
        """Test11 ElfPatcher().patch_binaries()."""
        container_id = "SOME-RANDOM-ID"
        mock_exists.return_value = True
        mock_gcl.return_value = "/usr/bin/ld"
        mock_select.return_value = "runc-arm"
        mock_putdata.side_effect = ["10", "/tmp"]
        mock_guess.return_value = "/usr/bin/ld"
        mock_elfp.return_value._container_root.return_value = "/tmp/ROOT"
        elfp = udocker.ElfPatcher(mock_local, container_id)
        self.assertTrue(elfp.patch_binaries())

    @mock.patch('udocker.os.path')
    @mock.patch('udocker.os.path.exists')
    @mock.patch('udocker.LocalRepository')
    @mock.patch('udocker.ElfPatcher.guess_elf_loader')
    @mock.patch('udocker.ElfPatcher.select_patchelf')
    @mock.patch('udocker.ElfPatcher.get_container_loader')
    @mock.patch('udocker.ElfPatcher')
    def test_12_restore_binaries(self, mock_elfp, mock_gcl, mock_select,
                                 mock_guess, mock_local,
                                 mock_exists, mock_path):
        """Test12 ElfPatcher().restore_binaries()."""
        container_id = "SOME-RANDOM-ID"
        mock_exists.return_value = True
        mock_gcl.return_value = "/usr/bin/ld"
        mock_select.return_value = "runc-arm"
        mock_guess.return_value = "/usr/bin/ld"
        mock_elfp.return_value._container_root.return_value = "/tmp/ROOT"
        elfp = udocker.ElfPatcher(mock_local, container_id)
        self.assertTrue(elfp.restore_binaries())

    @mock.patch('udocker.os.path')
    @mock.patch('udocker.os.path.exists')
    @mock.patch('udocker.LocalRepository')
    @mock.patch('udocker.ElfPatcher.get_container_loader')
    @mock.patch('udocker.FileUtil.size')
    @mock.patch('udocker.FileUtil.copyto')
    @mock.patch('udocker.FileUtil.getdata')
    def test_13_patch_ld(self, mock_getdata,
                         mock_copyto, mock_size,
                         mock_gcl, mock_local,
                         mock_exists, mock_path):
        """Test13 ElfPatcher().patch_ld(). Patch ld.so"""
        container_id = "SOME-RANDOM-ID"
        mock_size.return_value = -1
        elfp = udocker.ElfPatcher(mock_local, container_id)
        self.assertFalse(elfp.patch_ld())

        mock_size.return_value = 20
        mock_copyto.return_value = False
        elfp = udocker.ElfPatcher(mock_local, container_id)
        self.assertFalse(elfp.patch_ld())

        mock_size.return_value = 20
        mock_copyto.return_value = True
        mock_getdata.return_value = []
        elfp = udocker.ElfPatcher(mock_local, container_id)
        self.assertFalse(elfp.patch_ld())

        mock_size.return_value = 20
        mock_copyto.return_value = True
        mock_getdata.return_value = []
        elfp = udocker.ElfPatcher(mock_local, container_id)
        self.assertFalse(elfp.patch_ld("OUTPUT_ELF"))

    @mock.patch('udocker.Msg')
    @mock.patch('udocker.os.path')
    @mock.patch('udocker.os.path.exists')
    @mock.patch('udocker.LocalRepository')
    @mock.patch('udocker.ElfPatcher.get_container_loader')
    @mock.patch('udocker.FileUtil.size')
    @mock.patch('udocker.FileUtil.copyto')
    def test_14_restore_ld(self, mock_copyto, mock_size,
                           mock_gcl, mock_local,
                           mock_exists, mock_path, mock_msg):
        """Test14 ElfPatcher().restore_ld(). Restore ld.so"""
        container_id = "SOME-RANDOM-ID"
        mock_size.return_value = -1
        elfp = udocker.ElfPatcher(mock_local, container_id)
        self.assertFalse(elfp.restore_ld())

        mock_size.return_value = 20
        mock_copyto.return_value = True
        elfp = udocker.ElfPatcher(mock_local, container_id)
        self.assertTrue(elfp.restore_ld())

    @mock.patch('udocker.os.path')
    @mock.patch('udocker.os.path.exists')
    @mock.patch('udocker.LocalRepository')
    @mock.patch('udocker.Uprocess.get_output')
    def test_15__get_ld_config(self, mock_upout,
                               mock_local, mock_exists, mock_path):
        """Test15 ElfPatcher()._get_ld_config()."""
        container_id = "SOME-RANDOM-ID"
        mock_upout.return_value = []
        elfp = udocker.ElfPatcher(mock_local, container_id)
        status = elfp._get_ld_config()
        self.assertEqual(status, [])

        mock_upout.return_value = \
            "ld.so.cache => /tmp/ROOT/etc/ld.so.cache\n" \
            "ld.so.cache => /tmp/ROOT/etc/ld.so"
        elfp = udocker.ElfPatcher(mock_local, container_id)
        status = elfp._get_ld_config()
        self.assertIsInstance(status, list)

    @mock.patch('udocker.os.path.realpath')
    @mock.patch('udocker.os.path')
    @mock.patch('udocker.os.access')
    @mock.patch('udocker.os.walk')
    @mock.patch('udocker.os.path.isfile')
    @mock.patch('udocker.LocalRepository')
    def test_16__find_ld_libdirs(self, mock_local, mock_isfile, mock_walk,
                                 mock_access, mock_path, mock_rpath):
        """Test16 ElfPatcher()._find_ld_libdirs()."""
        container_id = "SOME-RANDOM-ID"
        mock_rpath.return_value = "/ROOT"
        elfp = udocker.ElfPatcher(mock_local, container_id)
        status = elfp._find_ld_libdirs()
        self.assertEqual(status, [])

        root_path = "/udocker/cont"
        mock_walk.return_value = [("/ROOT", ["ROOT"], ["ld-linux-x86-64.so.2"]), ]
        mock_access.return_value = True
        mock_isfile.return_value = True
        mock_rpath.return_value = "/ROOT"
        elfp = udocker.ElfPatcher(mock_local, container_id)
        status = elfp._find_ld_libdirs(root_path)
        # self.assertEqual(status, ['ROOT'])

    @mock.patch.object(udocker.ElfPatcher, '_find_ld_libdirs')
    @mock.patch('udocker.FileUtil.putdata')
    @mock.patch('udocker.os.path')
    @mock.patch('udocker.os.path.exists')
    @mock.patch('udocker.LocalRepository')
    def test_17_get_ld_libdirs(self, mock_local, mock_exists,
                               mock_path, mock_put, mock_find):
        """Test17 ElfPatcher().get_ld_libdirs(). Get ld library paths"""
        container_id = "SOME-RANDOM-ID"
        elfp = udocker.ElfPatcher(mock_local, container_id)
        status = elfp.get_ld_libdirs()
        self.assertEqual(status, [''])

        mock_exists.return_value = False
        mock_find.return_value = ['/lib', '/usr/lib']
        mock_put.return_value = '/lib:/usr/lib'
        elfp = udocker.ElfPatcher(mock_local, container_id)
        status = elfp.get_ld_libdirs(True)
        self.assertTrue(mock_find.called)
        self.assertTrue(mock_put.called)
        self.assertEqual(status, ['/lib', '/usr/lib'])

    @mock.patch.object(udocker.ElfPatcher, '_get_ld_config')
    @mock.patch('udocker.os.path')
    @mock.patch('udocker.os.path.exists')
    @mock.patch('udocker.LocalRepository')
    def test_18_get_ld_library_path(self, mock_local,
                                    mock_exists, mock_path, mock_get_ld):
        """Test18 ElfPatcher().get_ld_library_path(). Get ld library paths"""
        container_id = "SOME-RANDOM-ID"
        mock_get_ld.return_value = []
        elfp = udocker.ElfPatcher(mock_local, container_id)
        status = elfp.get_ld_library_path()
        self.assertEqual(status, '')

        mock_get_ld.return_value = ['/lib', '/usr/lib']
        elfp = udocker.ElfPatcher(mock_local, container_id)
        status = elfp.get_ld_library_path()
        self.assertEqual(status, '/lib:/usr/lib:')


class NixAuthenticationTestCase(unittest.TestCase):
    """Test NixAuthentication() *nix authentication portably."""

    @classmethod
    def setUpClass(cls):
        """Setup test."""
        set_env()

    def test_01_init(self):
        """Test01 NixAuthentication() constructor."""
        auth = udocker.NixAuthentication()
        self.assertEqual(auth.passwd_file, None)
        self.assertEqual(auth.group_file, None)

        auth = udocker.NixAuthentication("passwd", "group")
        self.assertEqual(auth.passwd_file, "passwd")
        self.assertEqual(auth.group_file, "group")

    def test_02__user_in_subid(self):
        """Test02 NixAuthentication()._user_in_subid()."""
        sfile = "/etc/subuid"
        auth = udocker.NixAuthentication()
        auth.passwd_file = ""
        subid_line = StringIO('root:296608:65536')
        with mock.patch(BUILTINS + '.open') as mopen:
            mopen.return_value.__iter__ = (
                lambda self: iter(subid_line.readline, ''))
            name = auth._user_in_subid(sfile, "root")
            self.assertEqual(name, [('296608', '65536')])

    @mock.patch('udocker.NixAuthentication._user_in_subid')
    def test_03_user_in_subuid(self, mock_usubid):
        """Test03 NixAuthentication().user_in_subuid()."""
        mock_usubid.return_value = [('296608', '65536')]
        subid_line = StringIO('root:296608:65536')
        auth = udocker.NixAuthentication()
        auth.passwd_file = ""
        status = auth.user_in_subuid("root")

    @mock.patch('udocker.NixAuthentication._user_in_subid')
    def test_04_user_in_subgid(self, mock_usubid):
        """Test04 NixAuthentication().user_in_subgid()."""
        mock_usubid.return_value = [('296618', '65536')]
        subid_line = StringIO('root:296618:65536')
        auth = udocker.NixAuthentication()
        auth.passwd_file = ""
        status = auth.user_in_subgid("root")

    @mock.patch('udocker.pwd')
    def test_05__get_user_from_host(self, mock_pwd):
        """Test05 NixAuthentication()._get_user_from_host()."""
        usr = pwd.struct_passwd(["root", "*", "0", "0", "root usr",
                                 "/root", "/bin/bash"])
        mock_pwd.getpwuid.return_value = usr
        auth = udocker.NixAuthentication()
        (name, uid, gid, gecos, _dir, shell) = auth._get_user_from_host(0)
        self.assertEqual(name, usr.pw_name)
        self.assertEqual(uid, usr.pw_uid)
        self.assertEqual(gid, str(usr.pw_gid))
        self.assertEqual(gecos, usr.pw_gecos)
        self.assertEqual(_dir, usr.pw_dir)
        self.assertEqual(shell, usr.pw_shell)

        mock_pwd.getpwnam.return_value = usr
        auth = udocker.NixAuthentication()
        (name, uid, gid, gecos, _dir, shell) = auth._get_user_from_host("root")
        self.assertEqual(name, usr.pw_name)
        self.assertEqual(uid, usr.pw_uid)
        self.assertEqual(gid, str(usr.pw_gid))
        self.assertEqual(gecos, usr.pw_gecos)
        self.assertEqual(_dir, usr.pw_dir)

    @mock.patch('udocker.pwd')
    def test_06__get_group_from_host(self, mock_pwd):
        """Test06 NixAuthentication()._get_group_from_host()."""
        hgr = grp.struct_group(["root", "*", "0", str([])])
        mock_pwd.getgrgid.return_value = hgr
        auth = udocker.NixAuthentication()
        (name, gid, mem) = auth._get_group_from_host(0)
        self.assertEqual(name, hgr.gr_name)
        self.assertEqual(gid, str(hgr.gr_gid))
        self.assertEqual(mem, hgr.gr_mem)

        mock_pwd.getgrnam.return_value = hgr
        auth = udocker.NixAuthentication()
        (name, gid, mem) = auth._get_group_from_host("root")
        self.assertEqual(name, hgr.gr_name)
        self.assertEqual(gid, str(hgr.gr_gid))
        self.assertEqual(mem, hgr.gr_mem)

    def test_07__get_user_from_file(self):
        """Test07 NixAuthentication()._get_user_from_file()."""
        auth = udocker.NixAuthentication()
        auth.passwd_file = "passwd"
        passwd_line = StringIO('root:x:0:0:root:/root:/bin/bash')
        with mock.patch(BUILTINS + '.open') as mopen:
            mopen.return_value.__iter__ = (
                lambda self: iter(passwd_line.readline, ''))
            (name, uid, gid,
             gecos, _dir, shell) = auth._get_user_from_file("root")
            self.assertEqual(name, "root")
            self.assertEqual(uid, "0")
            self.assertEqual(gid, "0")
            self.assertEqual(gecos, "root")
            self.assertEqual(_dir, "/root")
            self.assertEqual(shell, "/bin/bash")

        passwd_line = StringIO('root:x:0:0:root:/root:/bin/bash')
        with mock.patch(BUILTINS + '.open') as mopen:
            mopen.return_value.__iter__ = (
                lambda self: iter(passwd_line.readline, ''))
            (name, uid, gid,
             gecos, _dir, shell) = auth._get_user_from_file(0)
            self.assertEqual(name, "root")
            self.assertEqual(uid, "0")
            self.assertEqual(gid, "0")
            self.assertEqual(gecos, "root")
            self.assertEqual(_dir, "/root")
            self.assertEqual(shell, "/bin/bash")

    def test_08__get_group_from_file(self):
        """Test08 NixAuthentication()._get_group_from_file()."""
        auth = udocker.NixAuthentication()
        auth.passwd_file = "passwd"
        group_line = StringIO('root:x:0:a,b,c')
        with mock.patch(BUILTINS + '.open') as mopen:
            mopen.return_value.__iter__ = (
                lambda self: iter(group_line.readline, ''))
            (name, gid, mem) = auth._get_group_from_file("root")
            self.assertEqual(name, "root")
            self.assertEqual(gid, "0")
            self.assertEqual(mem, "a,b,c")

        group_line = StringIO('root:x:0:a,b,c')
        with mock.patch(BUILTINS + '.open') as mopen:
            mopen.return_value.__iter__ = (
                lambda self: iter(group_line.readline, ''))
            (name, gid, mem) = auth._get_group_from_file(0)
            self.assertEqual(name, "root")
            self.assertEqual(gid, "0")
            self.assertEqual(mem, "a,b,c")

    def test_09_add_user(self):
        """Test09 NixAuthentication().add_user()."""
        auth = udocker.NixAuthentication()
        with mock.patch(BUILTINS + '.open', mock.mock_open()):
            status = auth.add_user("root", "pw", 0, 0, "gecos",
                                   "/home", "/bin/bash")
            self.assertTrue(status)

    def test_10_add_group(self):
        """Test10 NixAuthentication().add_group()."""
        auth = udocker.NixAuthentication()
        with mock.patch(BUILTINS + '.open', mock.mock_open()):
            status = auth.add_group("root", 0)
            self.assertTrue(status)

    @mock.patch('udocker.NixAuthentication._get_user_from_host')
    @mock.patch('udocker.NixAuthentication._get_user_from_file')
    def test_11_get_user(self, mock_file, mock_host):
        """Test11 NixAuthentication().get_user()."""
        auth = udocker.NixAuthentication()
        auth.passwd_file = ""
        auth.get_user("user")
        self.assertTrue(mock_host.called)
        self.assertFalse(mock_file.called)

        mock_host.reset_mock()
        mock_file.reset_mock()
        auth.passwd_file = "passwd"
        auth.get_user("user")
        self.assertFalse(mock_host.called)
        self.assertTrue(mock_file.called)

    @mock.patch('udocker.NixAuthentication._get_group_from_host')
    @mock.patch('udocker.NixAuthentication._get_group_from_file')
    def test_12_get_group(self, mock_file, mock_host):
        """Test12 NixAuthentication().get_group()."""
        auth = udocker.NixAuthentication()
        auth.group_file = ""
        auth.get_group("group")
        self.assertTrue(mock_host.called)
        self.assertFalse(mock_file.called)

        mock_host.reset_mock()
        mock_file.reset_mock()
        auth.group_file = "group"
        auth.get_group("group")
        self.assertFalse(mock_host.called)
        self.assertTrue(mock_file.called)

    @mock.patch('udocker.NixAuthentication.get_user')
    def test_13_get_home(self, mock_getuser):
        """Test13 NixAuthentication().get_home()."""
        mock_getuser.return_value = ("user", "", "", "", "/home/user", "")
        auth = udocker.NixAuthentication()
        status = auth.get_home()
        self.assertTrue(mock_getuser.called)
        self.assertEqual(status, "/home/user")


class FileBindTestCase(unittest.TestCase):
    """Test FileBind()."""

    @classmethod
    def setUpClass(cls):
        """Setup test."""
        set_env()

    def _init(self):
        """Configure variables."""
        self.bind_dir = "/.bind_host_files"
        self.orig_dir = "/.bind_orig_files"

    @mock.patch('udocker.LocalRepository')
    @mock.patch('udocker.os.path.realpath')
    def test_01_init(self, mock_realpath, mock_local):
        """Test01 FileBind() constructor."""
        self._init()
        container_id = "CONTAINERID"
        mock_realpath.return_value = "/tmp"
        fbind = udocker.FileBind(mock_local, container_id)
        self.assertEqual(fbind.localrepo, mock_local)
        self.assertEqual(fbind.container_id, container_id)
        self.assertTrue(mock_realpath.called)
        self.assertTrue(fbind.container_root, fbind.container_dir + "/ROOT")
        self.assertTrue(
            fbind.container_bind_dir, fbind.container_root + self.bind_dir)
        self.assertTrue(
            fbind.container_orig_dir, fbind.container_dir + self.orig_dir)
        self.assertIsNone(fbind.host_bind_dir)

    @mock.patch('udocker.Msg')
    @mock.patch('udocker.LocalRepository')
    @mock.patch('udocker.os.path.isdir')
    @mock.patch('udocker.os.path.realpath')
    @mock.patch('udocker.FileUtil')
    def test_02_setup(self, mock_futil, mock_realpath, mock_isdir,
                      mock_local, mock_msg):
        """Test02 FileBind().setup()."""
        self._init()
        mock_msg.level = 0
        container_id = "CONTAINERID"
        mock_realpath.return_value = "/tmp"
        mock_isdir.return_value = True
        status = udocker.FileBind(mock_local, container_id).setup()
        self.assertTrue(mock_isdir.called)
        self.assertTrue(status)

        mock_isdir.return_value = False
        mock_futil.return_value.mkdir.return_value = False
        status = udocker.FileBind(mock_local, container_id).setup()
        self.assertFalse(status)

    @mock.patch('udocker.LocalRepository')
    @mock.patch('udocker.os.path.isdir')
    @mock.patch('udocker.os.path.islink')
    @mock.patch('udocker.os.path.isfile')
    @mock.patch('udocker.os.path.realpath')
    @mock.patch('udocker.Config')
    @mock.patch('udocker.os.listdir')
    @mock.patch('udocker.FileUtil')
    def test_03_restore(self, mock_futil, mock_listdir,
                        mock_config, mock_realpath, mock_isfile,
                        mock_islink, mock_isdir, mock_local):
        """Test03 FileBind().restore()."""
        self._init()
        container_id = "CONTAINERID"
        mock_realpath.return_value = "/tmp"
        mock_listdir.return_value = []
        mock_config.return_value.tmpdir.return_value = "/tmp"
        mock_futil.return_value.remove.return_value = True
        mock_isdir.return_value = False
        fbind = udocker.FileBind(mock_local, container_id)
        status = fbind.restore()
        self.assertFalse(mock_listdir.called)

        mock_isdir.return_value = True
        fbind = udocker.FileBind(mock_local, container_id)
        status = fbind.restore()
        self.assertTrue(mock_listdir.called)

        mock_listdir.return_value = ["is_file1", "is_dir", "is_file2"]
        mock_isfile.side_effect = [True, False, True]
        mock_islink.side_effect = [True, False, False]
        status = fbind.restore()
        self.assertTrue(mock_isfile.called)
        self.assertTrue(mock_islink.called)

    @mock.patch('udocker.LocalRepository')
    @mock.patch('udocker.FileUtil')
    @mock.patch('udocker.os.path.realpath')
    @mock.patch('udocker.os.path.isfile')
    @mock.patch('udocker.os.path.exists')
    def test_04_start(self, mock_exists, mock_isfile,
                      mock_realpath, mock_futil, mock_local):
        """Test04 FileBind().start()."""
        self._init()
        container_id = "CONTAINERID"
        mock_realpath.return_value = "/tmp"
        files_list = ["file1", "dir1", "file2"]
        mock_futil.return_value.mktmp.return_value = "tmpDir"
        fbind = udocker.FileBind(mock_local, container_id)
        fbind.start(files_list)
        self.assertTrue(mock_futil.called)

        mock_isfile.side_effect = [True, False, True]
        self.assertTrue(mock_isfile.called)
        self.assertTrue(mock_exists.called)
        self.assertIsInstance(fbind.start(files_list), tuple)

    @mock.patch('udocker.os.path.realpath')
    @mock.patch('udocker.FileBind.set_file')
    @mock.patch('udocker.LocalRepository')
    def test_05_set_list(self, mock_local, mock_setf, mock_realpath):
        """Test05 FileBind().set_list()."""
        self._init()
        container_id = "CONTAINERID"
        files_list = ["file1", "dir1", "file2"]
        mock_realpath.return_value = "/tmp"
        mock_setf.side_effect = [None, None, None]
        fbind = udocker.FileBind(mock_local, container_id)
        fbind.set_list(files_list)
        self.assertTrue(mock_setf.called, 3)

    @mock.patch('udocker.FileUtil')
    @mock.patch('udocker.os.path.exists')
    @mock.patch('udocker.os.path.isfile')
    @mock.patch('udocker.os.path.realpath')
    @mock.patch('udocker.LocalRepository')
    def test_06_set_file(self, mock_local, mock_realpath, mock_isfile,
                         mock_exist, mock_futil):
        """Test06 FileBind().set_file()."""
        self._init()
        container_id = "CONTAINERID"
        hfile = "/hfile"
        cfile = "#cfile"
        mock_realpath.return_value = "/tmp"
        mock_isfile.side_effect = [True, True]
        mock_exist.return_value = True
        mock_futil.return_value.copyto.return_value = None
        fbind = udocker.FileBind(mock_local, container_id)
        fbind.set_file(hfile, cfile)
        self.assertTrue(mock_futil.return_value.copyto.called)
        self.assertTrue(mock_isfile.called, 2)
        self.assertTrue(mock_exist.called)

    # @mock.patch('udocker.os.path.realpath')
    # @mock.patch('udocker.FileUtil')
    # @mock.patch('udocker.LocalRepository')
    # def test_07_add_file(self, mock_local, mock_futil, mock_realpath):
    #     """Test07 FileBind().add_file()."""
    #     self._init()
    #     container_id = "CONTAINERID"
    #     hfile = "/hfile"
    #     cfile = "#cfile"
    #     mock_realpath.return_value = "/tmp"
    #     mock_futil.return_value.remove.return_value = None
    #     mock_futil.return_value.copyto.return_value = None
    #     fbind = udocker.FileBind(mock_local, container_id)
    #     fbind.set_file(hfile, cfile)
    #     self.assertTrue(mock_futil.return_value.remove.called)
    #     self.assertTrue(mock_futil.return_value.copyto.called)

    @mock.patch('udocker.os.path.realpath')
    @mock.patch('udocker.LocalRepository')
    def test_08_get_path(self, mock_local, mock_realpath):
        """Test08 FileBind().get_path()."""
        self._init()
        container_id = "CONTAINERID"
        mock_realpath.return_value = "/tmp"
        container_file = "#container.file"
        fbind = udocker.FileBind(mock_local, container_id)
        fbind.host_bind_dir = "/tmp"
        status = fbind.get_path(container_file)
        self.assertEqual(status, "/tmp/#container.file")

    # @mock.patch('udocker.LocalRepository')
    # def test_09_finish(self, mock_local):
    #     """Test09 FileBind().finish()."""
    #     pass


class MountPointTestCase(unittest.TestCase):
    """Test MountPoint().
    """

    @classmethod
    def setUpClass(cls):
        """Setup test."""
        set_env()

    def _init(self):
        """Configure variables."""
        self.bind_dir = "/.bind_host_files"
        self.orig_dir = "/.bind_orig_files"

    @mock.patch('udocker.MountPoint.setup')
    @mock.patch('udocker.LocalRepository')
    @mock.patch('udocker.os.path.realpath')
    def test_01_init(self, mock_realpath, mock_local, mock_setup):
        """Test01 MountPoint() constructor."""
        self._init()
        container_id = "CONTAINERID"
        mock_realpath.return_value = "/tmp"
        mock_setup.return_value = True
        mpoint = udocker.MountPoint(mock_local, container_id)
        self.assertEqual(mpoint.localrepo, mock_local)
        self.assertEqual(mpoint.container_id, container_id)
        self.assertTrue(mock_realpath.called)
        self.assertTrue(mock_setup.called)

    @mock.patch('udocker.FileUtil')
    @mock.patch('udocker.os.path.isdir')
    @mock.patch('udocker.LocalRepository')
    @mock.patch('udocker.os.path.realpath')
    def test_02_setup(self, mock_realpath, mock_local, mock_isdir,
                      mock_futil):
        """Test02 MountPoint().setup()."""
        self._init()
        container_id = "CONTAINERID"
        mock_realpath.return_value = "/tmp"
        mock_isdir.return_value = True
        mpoint = udocker.MountPoint(mock_local, container_id)
        status = mpoint.setup()
        self.assertTrue(status)

        mock_isdir.return_value = False
        mock_futil.return_value.mkdir.return_value = True
        mpoint = udocker.MountPoint(mock_local, container_id)
        status = mpoint.setup()
        self.assertTrue(status)

        mock_isdir.return_value = False
        mock_futil.return_value.mkdir.return_value = False
        mpoint = udocker.MountPoint(mock_local, container_id)
        status = mpoint.setup()
        self.assertFalse(status)

    # def test_03_add(self):
    #     """Test03 MountPoint().add()."""
    #     pass

    # def test_04_delete(self):
    #     """Test04 MountPoint().delete()."""
    #     pass

    # def test_05_delete_all(self):
    #     """Test05 MountPoint().delete_all()."""
    #     pass

    # def test_06_create(self):
    #     """Test06 MountPoint().create()."""
    #     pass

    # def test_07_save(self):
    #     """Test07 MountPoint().save()."""
    #     pass

    # def test_08_save_all(self):
    #     """Test08 MountPoint().save_all()."""
    #     pass

    # def test_09_load_all(self):
    #     """Test09 MountPoint().load_all()."""
    #     pass

    # def test_10_restore(self):
    #     """Test10 MountPoint().restore()."""
    #     pass


class ExecutionEngineCommonTestCase(unittest.TestCase):
    """Test ExecutionEngineCommon().
    Parent class for containers execution.
    """

    @classmethod
    def setUpClass(cls):
        """Setup test."""
        set_env()

    def _init(self):
        """Configure variables."""
        udocker.Config = type('test', (object,), {})()
        udocker.Config.hostauth_list = ("/etc/passwd", "/etc/group")
        udocker.Config.cmd = "/bin/bash"
        udocker.Config.cpu_affinity_exec_tools = \
            (["numactl", "-C", "%s", "--", ], ["taskset", "-c", "%s", ])
        udocker.Config.location = ""
        udocker.Config.uid = 1000
        udocker.Config.sysdirs_list = ["/", ]
        udocker.Config.root_path = "/usr/sbin:/sbin:/usr/bin:/bin"
        udocker.Config.user_path = "/usr/bin:/bin:/usr/local/bin"

    @mock.patch('udocker.LocalRepository')
    def test_01_init(self, mock_local):
        """Test01 ExecutionEngineCommon() constructor."""
        self._init()
        ex_eng = udocker.ExecutionEngineCommon(mock_local)
        self.assertEqual(ex_eng.container_id, "")
        self.assertEqual(ex_eng.container_root, "")
        self.assertEqual(ex_eng.container_names, [])
        self.assertEqual(ex_eng.opt["nometa"], False)
        self.assertEqual(ex_eng.opt["nosysdirs"], False)
        self.assertEqual(ex_eng.opt["dri"], False)
        self.assertEqual(ex_eng.opt["bindhome"], False)
        self.assertEqual(ex_eng.opt["hostenv"], False)
        self.assertEqual(ex_eng.opt["hostauth"], False)
        self.assertEqual(ex_eng.opt["novol"], [])
        self.assertEqual(ex_eng.opt["env"], [])
        self.assertEqual(ex_eng.opt["vol"], [])
        self.assertEqual(ex_eng.opt["cpuset"], "")
        self.assertEqual(ex_eng.opt["user"], "")
        self.assertEqual(ex_eng.opt["cwd"], "")
        self.assertEqual(ex_eng.opt["entryp"], "")
        self.assertEqual(ex_eng.opt["cmd"], udocker.Config.cmd)
        self.assertEqual(ex_eng.opt["hostname"], "")
        self.assertEqual(ex_eng.opt["domain"], "")
        self.assertEqual(ex_eng.opt["volfrom"], [])

    @mock.patch('udocker.HostInfo.cmd_has_option')
    @mock.patch('udocker.LocalRepository')
    def test_02__has_option(self, mock_local, mock_hasopt):
        """Test02 ExecutionEngineCommon()._has_option()."""
        self._init()
        mock_hasopt.return_value = True
        ex_eng = udocker.ExecutionEngineCommon(mock_local)
        ex_eng.executable = "ls"
        status = ex_eng._has_option("-l")
        self.assertTrue(status)
        self.assertTrue(mock_hasopt.called)

    @mock.patch('udocker.LocalRepository')
    def test_03__get_portsmap(self, mock_local):
        """Test03 ExecutionEngineCommon()._get_portsmap()."""
        self._init()
        ex_eng = udocker.ExecutionEngineCommon(mock_local)
        ex_eng.opt["portsmap"] = ["8080:80", "8443:443"]
        status = ex_eng._get_portsmap()
        self.assertEqual(status, {80: 8080, 443: 8443})

        ex_eng = udocker.ExecutionEngineCommon(mock_local)
        ex_eng.opt["portsmap"] = ["8080:80", "8443:443"]
        status = ex_eng._get_portsmap(False)
        self.assertEqual(status, {8080: 80, 8443: 443})

    @mock.patch('udocker.Msg')
    @mock.patch('udocker.LocalRepository')
    def test_04__check_exposed_ports(self, mock_local, mock_msg):
        """Test04 ExecutionEngineCommon()._check_exposed_ports()."""
        self._init()
        mock_msg.level = 0
        ex_eng = udocker.ExecutionEngineCommon(mock_local)
        ex_eng.opt["portsexp"] = ("1024", "2048/tcp", "23000/udp")
        status = ex_eng._check_exposed_ports()
        self.assertTrue(status)

        ex_eng.opt["portsexp"] = ("1023", "2048/tcp", "23000/udp")
        status = ex_eng._check_exposed_ports()
        self.assertFalse(status)

        ex_eng.opt["portsexp"] = ("1024", "80/tcp", "23000/udp")
        status = ex_eng._check_exposed_ports()
        self.assertFalse(status)

        ex_eng.opt["portsexp"] = ("1024", "2048/tcp", "23/udp")
        status = ex_eng._check_exposed_ports()
        self.assertFalse(status)

    @mock.patch('udocker.FileUtil')
    @mock.patch('udocker.LocalRepository')
    def test_05__set_cpu_affinity(self, mock_local, mock_futil):
        """Test05 ExecutionEngineCommon()._set_cpu_affinity()."""
        self._init()
        ex_eng = udocker.ExecutionEngineCommon(mock_local)
        mock_futil.return_value.find_exec.return_value = ""
        status = ex_eng._set_cpu_affinity()
        self.assertEqual(status, [])

        mock_futil.return_value.find_exec.return_value = "taskset"
        status = ex_eng._set_cpu_affinity()
        self.assertEqual(status, [])

        mock_futil.return_value.find_exec.return_value = "numactl"
        ex_eng.opt["cpuset"] = "1-2"
        status = ex_eng._set_cpu_affinity()
        self.assertEqual(status, ["numactl", "-C", "1-2", "--"])

    @mock.patch('udocker.LocalRepository')
    def test_06__cleanpath(self, mock_local):
        """Test06 ExecutionEngineCommon()._cleanpath()."""
        self._init()
        ex_eng = udocker.ExecutionEngineCommon(mock_local)
        status = ex_eng._cleanpath("//somedir/file")
        self.assertEqual(status, "/somedir/file")

        ex_eng = udocker.ExecutionEngineCommon(mock_local)
        status = ex_eng._cleanpath("//somedir/file/")
        self.assertEqual(status, "/somedir/file")

    @mock.patch('udocker.LocalRepository')
    def test_07__vol_split(self, mock_local):
        """Test07 ExecutionEngineCommon()._vol_split()."""
        self._init()
        volum = "/host/home/user:/cont/home/user"
        ex_eng = udocker.ExecutionEngineCommon(mock_local)
        status = ex_eng._vol_split(volum)
        self.assertEqual(status, ("/host/home/user", "/cont/home/user"))

    @mock.patch('udocker.os.path.isdir')
    @mock.patch('udocker.LocalRepository')
    def test_08__cont2host(self, mock_local, mock_isdir):
        """Test08 ExecutionEngineCommon()._cont2host()."""
        self._init()
        mock_isdir.return_value = True
        ex_eng = udocker.ExecutionEngineCommon(mock_local)
        ex_eng.opt["vol"] = ("/opt/xxx:/mnt",)
        status = ex_eng._cont2host("/mnt")
        self.assertEqual(status, "/opt/xxx")

        ex_eng.opt["vol"] = ("/var/xxx:/mnt",)
        status = ex_eng._cont2host("/opt")
        self.assertTrue(status.endswith("/opt"))

        # change dir to volume (regression of #51)
        ex_eng.opt["vol"] = ("/var/xxx",)
        status = ex_eng._cont2host("/var/xxx/tt")
        self.assertEqual(status, "/var/xxx/tt")

        # change dir to volume (regression of #51)
        ex_eng.opt["vol"] = ("/var/xxx:/mnt",)
        status = ex_eng._cont2host("/mnt/tt")
        self.assertEqual(status, "/var/xxx/tt")

    @mock.patch('udocker.FileUtil')
    @mock.patch('udocker.LocalRepository')
    def test_09__create_mountpoint(self, mock_local, mock_futil):
        """Test09 ExecutionEngineCommon()._create_mountpoint()."""
        self._init()
        mock_futil.return_value.isdir.return_value = False
        exc = udocker.ExecutionEngineCommon(mock_local)
        status = exc._create_mountpoint("", "", True)
        self.assertTrue(status)

        # mock_isdir.return_value = True
        # exc = udocker.ExecutionEngineCommon(mock_local)
        # status = exc._create_mountpoint("", "")
        # self.assertTrue(status)

    @mock.patch('udocker.os.path.exists')
    @mock.patch('udocker.LocalRepository')
    def test_10__check_volumes(self, mock_local, mock_exists):
        """Test10 ExecutionEngineCommon()._check_volumes()."""
        self._init()
        exc = udocker.ExecutionEngineCommon(mock_local)
        exc.opt["vol"] = ()
        status = exc._check_volumes()
        self.assertTrue(status)

        mock_exists.return_value = False
        exc = udocker.ExecutionEngineCommon(mock_local)
        status = exc._check_volumes()
        self.assertTrue(status)

    @mock.patch('udocker.NixAuthentication')
    @mock.patch('udocker.LocalRepository')
    def test_11__get_bindhome(self, mock_local, mock_nixauth):
        """Test11 ExecutionEngineCommon()._get_bindhome()."""
        self._init()
        mock_nixauth.return_value.get_home.return_value = ""
        prex = udocker.ExecutionEngineCommon(mock_local)
        prex.opt["bindhome"] = False
        status = prex._get_bindhome()
        self.assertEqual(status, "")

        mock_nixauth.return_value.get_home.return_value = "/home/user"
        prex = udocker.ExecutionEngineCommon(mock_local)
        prex.opt["bindhome"] = True
        status = prex._get_bindhome()
        self.assertEqual(status, "/home/user")

        mock_nixauth.return_value.get_home.return_value = ""
        prex = udocker.ExecutionEngineCommon(mock_local)
        prex.opt["bindhome"] = True
        status = prex._get_bindhome()
        self.assertEqual(status, "")

    @mock.patch('udocker.LocalRepository')
    def test_12__is_volume(self, mock_local):
        """Test11 ExecutionEngineCommon()._is_volume()."""
        self._init()
        exc = udocker.ExecutionEngineCommon(mock_local)
        exc.opt["vol"] = ["/tmp"]
        status = exc._is_volume("/tmp")
        self.assertTrue(status)

        exc = udocker.ExecutionEngineCommon(mock_local)
        exc.opt["vol"] = [""]
        status = exc._is_volume("/tmp")
        self.assertFalse(status)

    # def test_13__is_mountpoint(self):
    #     """Test13 ExecutionEngineCommon()._is_mountpoint()."""
    #     pass

    # def test_14__set_volume_bindings(self):
    #     """Test14 ExecutionEngineCommon()._set_volume_bindings()."""
    #     pass

    @mock.patch('udocker.Msg')
    @mock.patch('udocker.os.path.isdir')
    @mock.patch('udocker.os.path.exists')
    @mock.patch('udocker.ExecutionEngineCommon._cont2host')
    @mock.patch('udocker.ExecutionEngineCommon._getenv')
    @mock.patch('udocker.LocalRepository')
    def test_15__check_paths(self, mock_local, mock_getenv, mock_isinvol,
                             mock_exists, mock_isdir, mock_msg):
        """Test15 ExecutionEngineCommon()._check_paths()."""
        self._init()
        mock_msg.level = 0
        ex_eng = udocker.ExecutionEngineCommon(mock_local)
        mock_getenv.return_value = ""
        mock_isinvol.return_value = False
        mock_exists.return_value = False
        mock_isdir.return_value = False
        ex_eng.opt["uid"] = "0"
        ex_eng.opt["cwd"] = ""
        ex_eng.opt["home"] = "/home/user"
        ex_eng.container_root = "/containers/123/ROOT"
        status = ex_eng._check_paths()
        self.assertFalse(status)
        self.assertEqual(ex_eng.opt["env"][-1],
                         "PATH=/usr/sbin:/sbin:/usr/bin:/bin")
        self.assertEqual(ex_eng.opt["cwd"], ex_eng.opt["home"])

        ex_eng.opt["uid"] = "1000"
        status = ex_eng._check_paths()
        self.assertFalse(status)
        self.assertEqual(ex_eng.opt["env"][-1],
                         "PATH=/usr/bin:/bin:/usr/local/bin")
        self.assertEqual(ex_eng.opt["cwd"], ex_eng.opt["home"])

        mock_exists.return_value = True
        mock_isdir.return_value = True
        status = ex_eng._check_paths()
        self.assertTrue(status)

    @mock.patch('udocker.Msg')
    @mock.patch('udocker.os.access')
    @mock.patch('udocker.os.readlink')
    @mock.patch('udocker.os.path.isfile')
    @mock.patch('udocker.ExecutionEngineCommon._getenv')
    @mock.patch('udocker.LocalRepository')
    def test_16__check_executable(self, mock_local, mock_getenv, mock_isfile,
                                  mock_readlink, mock_access, mock_msg):
        """Test16 ExecutionEngineCommon()._check_executable()."""
        self._init()
        mock_msg.level = 0
        ex_eng = udocker.ExecutionEngineCommon(mock_local)
        mock_getenv.return_value = ""
        ex_eng.opt["entryp"] = "/bin/shell -x -v"
        mock_isfile.return_value = False
        ex_eng.container_root = "/containers/123/ROOT"
        status = ex_eng._check_executable()
        self.assertFalse(status)

        mock_isfile.return_value = True
        mock_access.return_value = True
        status = ex_eng._check_executable()
        self.assertTrue(status)

        ex_eng.opt["entryp"] = ["/bin/shell", "-x", "-v"]
        ex_eng.opt["cmd"] = ""
        status = ex_eng._check_executable()
        self.assertEqual(ex_eng.opt["cmd"], ex_eng.opt["entryp"])

        ex_eng.opt["entryp"] = ["/bin/shell", ]
        ex_eng.opt["cmd"] = ["-x", "-v"]
        status = ex_eng._check_executable()
        self.assertEqual(ex_eng.opt["cmd"], ["/bin/shell", "-x", "-v"])

    @mock.patch('udocker.ContainerStructure')
    @mock.patch('udocker.ExecutionEngineCommon._check_exposed_ports')
    @mock.patch('udocker.ExecutionEngineCommon._getenv')
    @mock.patch('udocker.LocalRepository')
    def test_17__run_load_metadata(self, mock_local, mock_getenv,
                                   mock_chkports, mock_cstruct):
        """Test17 ExecutionEngineCommon()._run_load_metadata()."""
        self._init()
        ex_eng = udocker.ExecutionEngineCommon(mock_local)
        mock_getenv.return_value = ""
        udocker.Config.location = "/tmp/container"
        status = ex_eng._run_load_metadata("123")
        self.assertEqual(status, ("", []))

        udocker.Config.location = ""
        mock_cstruct.return_value.get_container_attr.return_value = ("", [])
        status = ex_eng._run_load_metadata("123")
        self.assertEqual(status, (None, None))

        udocker.Config.location = ""
        mock_cstruct.return_value.get_container_attr.return_value = ("/x", [])
        ex_eng.opt["nometa"] = True
        status = ex_eng._run_load_metadata("123")
        self.assertEqual(status, ("/x", []))

        udocker.Config.location = ""
        mock_cstruct.return_value.get_container_attr.return_value = ("/x", [])
        ex_eng.opt["nometa"] = False
        status = ex_eng._run_load_metadata("123")
        self.assertEqual(status, ("/x", []))

    @mock.patch('udocker.LocalRepository')
    def test_18__check_env(self, mock_local):
        """Test18 ExecutionEngineCommon()._check_env()."""
        self._init()
        ex_eng = udocker.ExecutionEngineCommon(mock_local)
        ex_eng.opt["env"] = ["HOME=/home/user", "PATH=/bin:/usr/bin"]
        status = ex_eng._check_env()
        self.assertTrue(status)

        ex_eng = udocker.ExecutionEngineCommon(mock_local)
        ex_eng.opt["env"] = ["HOME =", "PATH=/bin:/usr/bin"]
        status = ex_eng._check_env()
        self.assertFalse(status)

    @mock.patch('udocker.LocalRepository')
    def test_19__getenv(self, mock_local):
        """Test19 ExecutionEngineCommon()._getenv()."""
        self._init()
        ex_eng = udocker.ExecutionEngineCommon(mock_local)
        ex_eng.opt["env"] = ["HOME=/home/user", "PATH=/bin:/usr/bin"]
        status = ex_eng._getenv("")
        self.assertEqual(status, None)

        status = ex_eng._getenv("XXX")
        self.assertEqual(status, None)

        status = ex_eng._getenv("HOME")
        self.assertEqual(status, "/home/user")

        status = ex_eng._getenv("PATH")
        self.assertEqual(status, "/bin:/usr/bin")

    # def test_20__select_auth_files(self):
    #     """Test20 ExecutionEngineCommon()._select_auth_files()."""
    #     pass

    # def test_21__validate_user_str(self):
    #     """Test21 ExecutionEngineCommon()._validate_user_str()."""
    #     pass

    # def test_22__user_from_str(self):
    #     """Test22 ExecutionEngineCommon()._user_from_str()."""
    #     pass

    # @mock.patch('udocker.Msg')
    # @mock.patch('udocker.NixAuthentication')
    # @mock.patch('udocker.LocalRepository')
    # @mock.patch('udocker.ExecutionEngineCommon._create_user')
    # def test_23__setup_container_user(self, mock_cruser,
    #                                   mock_local, mock_nix, mock_msg):
    #     """Test23 ExecutionEngineCommon()._setup_container_user()."""
    #     self._init()
    #     mock_msg.level = 0
    #     ex_eng = udocker.ExecutionEngineCommon(mock_local)
    #     status = ex_eng._setup_container_user("0:0")
    #     self.assertFalse(status)

    #     ex_eng = udocker.ExecutionEngineCommon(mock_local)
    #     ex_eng.opt["vol"] = ""
    #     ex_eng.opt["hostauth"] = False
    #     mock_nix.return_value.get_user.return_value = ("", "", "",
    #                                                    "", "", "")
    #     status = ex_eng._setup_container_user("0:0")
    #     self.assertTrue(status)
    #     self.assertTrue(mock_cruser.called)

    #     ex_eng = udocker.ExecutionEngineCommon(mock_local)
    #     ex_eng.opt["vol"] = ""
    #     ex_eng.opt["hostauth"] = False
    #     mock_nix.return_value.get_user.return_value = ("root", 0, 0,
    #                                                    "", "", "")
    #     status = ex_eng._setup_container_user("0:0")
    #     self.assertTrue(status)
    #     self.assertTrue(mock_cruser.called)

    #     ex_eng = udocker.ExecutionEngineCommon(mock_local)
    #     ex_eng.opt["vol"] = ""
    #     ex_eng.opt["hostauth"] = True
    #     mock_nix.return_value.get_user.return_value = ("", "", "",
    #                                                    "", "", "")
    #     status = ex_eng._setup_container_user("0:0")
    #     self.assertFalse(status)

    #     ex_eng = udocker.ExecutionEngineCommon(mock_local)
    #     ex_eng.opt["vol"] = ""
    #     ex_eng.opt["hostauth"] = True
    #     mock_nix.return_value.get_user.return_value = ("root", 0, 0,
    #                                                    "", "", "")
    #     status = ex_eng._setup_container_user("0:0")
    #     self.assertTrue(status)
    #     self.assertTrue(mock_cruser.called)

    #     ex_eng = udocker.ExecutionEngineCommon(mock_local)
    #     ex_eng.opt["vol"] = ""
    #     ex_eng.opt["hostauth"] = False
    #     mock_nix.return_value.get_user.return_value = ("", "", "",
    #                                                    "", "", "")
    #     status = ex_eng._setup_container_user("")
    #     self.assertTrue(status)
    #     self.assertTrue(mock_cruser.called)

    #     ex_eng = udocker.ExecutionEngineCommon(mock_local)
    #     ex_eng.opt["vol"] = ""
    #     ex_eng.opt["hostauth"] = False
    #     mock_nix.return_value.get_user.return_value = ("root", 0, 0,
    #                                                    "", "", "")
    #     status = ex_eng._setup_container_user("")
    #     self.assertTrue(status)
    #     self.assertTrue(mock_cruser.called)

    #     ex_eng = udocker.ExecutionEngineCommon(mock_local)
    #     ex_eng.opt["vol"] = ""
    #     ex_eng.opt["hostauth"] = True
    #     mock_nix.return_value.get_user.return_value = ("", "", "",
    #                                                    "", "", "")
    #     status = ex_eng._setup_container_user("")
    #     self.assertFalse(status)

    #     ex_eng = udocker.ExecutionEngineCommon(mock_local)
    #     ex_eng.opt["vol"] = ""
    #     ex_eng.opt["hostauth"] = False
    #     mock_nix.return_value.get_user.return_value = ("", 100, 0,
    #                                                    "", "", "")
    #     status = ex_eng._setup_container_user("0:0")
    #     self.assertTrue(status)
    #     self.assertTrue(mock_cruser.called)
    #     self.assertEqual(ex_eng.opt["user"], "")

    # def test_24__setup_container_user_noroot(self):
    #     """Test24 ExecutionEngineCommon()._setup_container_user_noroot()."""
    #     pass

    # def test_25__fill_user(self):
    #     """Test25 ExecutionEngineCommon()._fill_user()."""
    #     pass

    # @mock.patch('udocker.os.getgroups')
    # @mock.patch('udocker.FileUtil')
    # @mock.patch('udocker.Msg')
    # @mock.patch('udocker.NixAuthentication')
    # @mock.patch('udocker.LocalRepository')
    # def test_26__create_user(self, mock_local, mock_nix, mock_msg,
    #                          mock_futil, mock_groups):
    #     """Test26 ExecutionEngineCommon()._create_user()."""
    #     self._init()
    #     mock_msg.level = 0
    #     container_auth = udocker.NixAuthentication("", "")
    #     container_auth.passwd_file = ""
    #     container_auth.group_file = ""
    #     host_auth = udocker.NixAuthentication("", "")
    #     udocker.Config.uid = 1000
    #     udocker.Config.gid = 1000
    #     mock_nix.return_value.add_user.return_value = False
    #     ex_eng = udocker.ExecutionEngineCommon(mock_local)
    #     ex_eng.opt["uid"] = ""
    #     ex_eng.opt["gid"] = ""
    #     ex_eng.opt["user"] = ""
    #     ex_eng.opt["home"] = ""
    #     ex_eng.opt["shell"] = ""
    #     ex_eng.opt["gecos"] = ""
    #     status = ex_eng._create_user(container_auth, host_auth)
    #     self.assertFalse(status)
    #     self.assertEqual(ex_eng.opt["uid"], "1000")
    #     self.assertEqual(ex_eng.opt["gid"], "1000")
    #     self.assertEqual(ex_eng.opt["user"], "udoc1000")
    #     self.assertEqual(ex_eng.opt["home"], "/home/udoc1000")
    #     self.assertEqual(ex_eng.opt["shell"], "/bin/sh")
    #     self.assertEqual(ex_eng.opt["gecos"], "*UDOCKER*")

    #     mock_nix.return_value.add_user.return_value = False
    #     ex_eng = udocker.ExecutionEngineCommon(mock_local)
    #     ex_eng.opt["uid"] = "60000"
    #     ex_eng.opt["gid"] = "60000"
    #     ex_eng.opt["user"] = "someuser"
    #     ex_eng.opt["home"] = ""
    #     ex_eng.opt["shell"] = "/bin/false"
    #     ex_eng.opt["gecos"] = "*XXX*"
    #     status = ex_eng._create_user(container_auth, host_auth)
    #     self.assertFalse(status)
    #     self.assertEqual(ex_eng.opt["uid"], "60000")
    #     self.assertEqual(ex_eng.opt["gid"], "60000")
    #     self.assertEqual(ex_eng.opt["user"], "someuser")
    #     self.assertEqual(ex_eng.opt["home"], "/home/someuser")
    #     self.assertEqual(ex_eng.opt["shell"], "/bin/false")
    #     self.assertEqual(ex_eng.opt["gecos"], "*XXX*")

    #     mock_nix.return_value.add_user.return_value = False
    #     ex_eng = udocker.ExecutionEngineCommon(mock_local)
    #     ex_eng.opt["uid"] = "60000"
    #     ex_eng.opt["gid"] = "60000"
    #     ex_eng.opt["user"] = "someuser"
    #     ex_eng.opt["home"] = "/home/batata"
    #     ex_eng.opt["shell"] = "/bin/false"
    #     ex_eng.opt["gecos"] = "*XXX*"
    #     status = ex_eng._create_user(container_auth, host_auth)
    #     self.assertFalse(status)
    #     self.assertEqual(ex_eng.opt["uid"], "60000")
    #     self.assertEqual(ex_eng.opt["gid"], "60000")
    #     self.assertEqual(ex_eng.opt["user"], "someuser")
    #     self.assertEqual(ex_eng.opt["home"], "/home/batata")
    #     self.assertEqual(ex_eng.opt["shell"], "/bin/false")
    #     self.assertEqual(ex_eng.opt["gecos"], "*XXX*")

    #     mock_nix.return_value.add_user.return_value = True
    #     mock_nix.return_value.get_group.return_value = ("", "", "")
    #     mock_nix.return_value.add_group.return_value = True
    #     mock_groups.return_value = ()
    #     ex_eng = udocker.ExecutionEngineCommon(mock_local)
    #     ex_eng.opt["uid"] = "60000"
    #     ex_eng.opt["gid"] = "60000"
    #     ex_eng.opt["user"] = "someuser"
    #     ex_eng.opt["home"] = "/home/batata"
    #     ex_eng.opt["shell"] = "/bin/false"
    #     ex_eng.opt["gecos"] = "*XXX*"
    #     status = ex_eng._create_user(container_auth, host_auth)
    #     self.assertTrue(status)
    #     self.assertEqual(ex_eng.opt["uid"], "60000")
    #     self.assertEqual(ex_eng.opt["gid"], "60000")
    #     self.assertEqual(ex_eng.opt["user"], "someuser")
    #     self.assertEqual(ex_eng.opt["home"], "/home/batata")
    #     self.assertEqual(ex_eng.opt["shell"], "/bin/false")
    #     self.assertEqual(ex_eng.opt["gecos"], "*XXX*")
    #     self.assertEqual(ex_eng.opt["hostauth"], True)
    #     mgroup = mock_nix.return_value.get_group
    #     self.assertTrue(mgroup.called_once_with("60000"))

    #     mock_nix.return_value.add_user.return_value = True
    #     mock_nix.return_value.get_group.return_value = ("", "", "")
    #     mock_nix.return_value.add_group.return_value = True
    #     mock_groups.return_value = (80000,)
    #     ex_eng = udocker.ExecutionEngineCommon(mock_local)
    #     ex_eng.opt["uid"] = "60000"
    #     ex_eng.opt["gid"] = "60000"
    #     ex_eng.opt["user"] = "someuser"
    #     ex_eng.opt["home"] = "/home/batata"
    #     ex_eng.opt["shell"] = "/bin/false"
    #     ex_eng.opt["gecos"] = "*XXX*"
    #     status = ex_eng._create_user(container_auth, host_auth)
    #     self.assertTrue(status)
    #     self.assertEqual(ex_eng.opt["uid"], "60000")
    #     self.assertEqual(ex_eng.opt["gid"], "60000")
    #     self.assertEqual(ex_eng.opt["user"], "someuser")
    #     self.assertEqual(ex_eng.opt["home"], "/home/batata")
    #     self.assertEqual(ex_eng.opt["shell"], "/bin/false")
    #     self.assertEqual(ex_eng.opt["gecos"], "*XXX*")
    #     self.assertEqual(ex_eng.opt["hostauth"], True)
    #     ggroup = mock_nix.return_value.get_group
    #     self.assertTrue(ggroup.called_once_with("60000"))
    #     agroup = mock_nix.return_value.add_group
    #     self.assertTrue(agroup.called_once_with("G80000", "80000"))

    @mock.patch('udocker.Msg')
    @mock.patch('udocker.os.path.basename')
    @mock.patch('udocker.LocalRepository')
    def test_27__run_banner(self, mock_local, mock_base, mock_msg):
        """Test27 ExecutionEngineCommon()._run_banner()."""
        self._init()
        mock_msg.level = 0
        ex_eng = udocker.ExecutionEngineCommon(mock_local)
        ex_eng._run_banner("/bin/bash")
        ex_eng.container_id = "CONTAINERID"
        self.assertTrue(mock_base.called_once_with("/bin/bash"))

    @mock.patch('udocker.Config')
    @mock.patch('udocker.os')
    @mock.patch('udocker.LocalRepository')
    def test_28__env_cleanup_dict(self, mock_local, mock_os, mock_config):
        """Test28 ExecutionEngineCommon()._env_cleanup()."""
        udocker.Config = mock_config
        udocker.Config.valid_host_env = ("HOME",)
        mock_os.environ = {'HOME': '/', 'USERNAME': 'user', }
        ex_eng = udocker.ExecutionEngineCommon(mock_local)
        ex_eng._run_env_cleanup_dict()
        self.assertEqual(mock_os.environ, {'HOME': '/', })

    @mock.patch('udocker.Config')
    @mock.patch('udocker.os')
    @mock.patch('udocker.LocalRepository')
    def test_29__run_env_cleanup_list(self, mock_local, mock_os, mock_config):
        """Test29 ExecutionEngineCommon()._run_env_cleanup_list()."""
        udocker.Config = mock_config
        udocker.Config.valid_host_env = ("HOME",)
        mock_os.environ = {'HOME': '/', 'USERNAME': 'user', }
        ex_eng = udocker.ExecutionEngineCommon(mock_local)
        ex_eng._run_env_cleanup_list()
        self.assertEqual(mock_os.environ, {'HOME': '/', 'USERNAME': 'user', })

    @mock.patch('udocker.Config')
    @mock.patch('udocker.LocalRepository')
    def test_30__run_env_get(self, mock_local, mock_config):
        """Test30 ExecutionEngineCommon()._run_env_get()."""
        udocker.Config = mock_config
        udocker.Config.valid_host_env = ("HOME",)
        ex_eng = udocker.ExecutionEngineCommon(mock_local)
        ex_eng.opt["env"] = ['HOME=/']
        status = ex_eng._run_env_get()
        self.assertEqual(status, {'HOME': '/'})

    @mock.patch('udocker.Config')
    @mock.patch('udocker.LocalRepository')
    def test_31__run_env_set(self, mock_local, mock_config):
        """Test31 ExecutionEngineCommon()._run_env_set()."""
        ex_eng = udocker.ExecutionEngineCommon(mock_local)
        ex_eng.opt["home"] = "/"
        ex_eng.opt["user"] = "user"
        ex_eng.opt["uid"] = "1000"
        ex_eng.container_root = "/croot"
        ex_eng.container_id = "2717add4-e6f6-397c-9019-74fa67be439f"
        ex_eng.container_names = ['cna[]me', ]
        ex_eng.exec_mode = mock.MagicMock()
        ex_eng.exec_mode.get_mode.return_value = "P1"
        ex_eng._run_env_set()
        self.assertTrue("HOME=" + ex_eng.opt["home"] in ex_eng.opt["env"])
        self.assertTrue("USER=" + ex_eng.opt["user"] in ex_eng.opt["env"])
        self.assertTrue("LOGNAME=" + ex_eng.opt["user"] in ex_eng.opt["env"])
        self.assertTrue("USERNAME=" + ex_eng.opt["user"] in ex_eng.opt["env"])
        self.assertTrue("SHLVL=0" in ex_eng.opt["env"])
        self.assertTrue("container_root=/croot" in ex_eng.opt["env"])

    # def test_32__run_env_cmdoptions(self):
    #     """Test32 ExecutionEngineCommon()._run_env_cmdoptions()."""
    #     pass

    # @mock.patch('udocker.os.path.realpath')
    # @mock.patch('udocker.Config')
    # @mock.patch('udocker.LocalRepository.get_container_name')
    # @mock.patch('udocker.ExecutionMode')
    # @mock.patch('udocker.ExecutionEngineCommon._run_env_cmdoptions')
    # @mock.patch('udocker.ExecutionEngineCommon._set_volume_bindings')
    # @mock.patch('udocker.ExecutionEngineCommon._check_executable')
    # @mock.patch('udocker.ExecutionEngineCommon._check_paths')
    # @mock.patch('udocker.ExecutionEngineCommon._setup_container_user')
    # @mock.patch('udocker.ExecutionEngineCommon._run_load_metadata')
    # @mock.patch('udocker.LocalRepository')
    # def test_33__run_init(self, mock_local, mock_loadmeta, mock_setupuser,
    #                       mock_chkpaths, mock_chkexec, mock_chkvol,
    #                       mock_cmdopt, mock_execmode, mock_contname,
    #                       mock_conf, mock_ospath):
    #     """Test33 ExecutionEngineCommon()._run_init()."""
    #     mock_conf.return_value.container.return_value = None
    #     mock_conf.location = False
    #     mock_local.get_container_name.return_value = "cname"
    #     mock_loadmeta.return_value = ("/container_dir", "dummy",)
    #     mock_contname.return_value = "2717add4-e6f6-397c-9019-74fa67be439f"
    #     mock_cmdopt.return_value = None
    #     mock_execmode.return_value = None
    #     mock_setupuser.return_value = True
    #     mock_chkpaths.return_value = True
    #     mock_chkexec.return_value = True
    #     mock_ospath.return_value = "/container_dir/ROOT"
    #     ex_eng = udocker.ExecutionEngineCommon(mock_local)
    #     status = ex_eng._run_init("2717add4-e6f6-397c-9019-74fa67be439f")
    #     self.assertTrue(status)
    #     self.assertEqual(ex_eng.container_root, "/container_dir/ROOT")

    #     mock_setupuser.return_value = False
    #     mock_chkpaths.return_value = True
    #     mock_chkexec.return_value = True
    #     mock_ospath.return_value = "/container_dir/ROOT"
    #     status = ex_eng._run_init("2717add4-e6f6-397c-9019-74fa67be439f")
    #     self.assertFalse(status)

    #     mock_setupuser.return_value = True
    #     mock_chkpaths.return_value = False
    #     mock_chkexec.return_value = True
    #     mock_ospath.return_value = "/container_dir/ROOT"
    #     status = ex_eng._run_init("2717add4-e6f6-397c-9019-74fa67be439f")
    #     self.assertFalse(status)

    #     mock_setupuser.return_value = True
    #     mock_chkpaths.return_value = True
    #     mock_chkexec.return_value = False
    #     mock_ospath.return_value = "/container_dir/ROOT"
    #     status = ex_eng._run_init("2717add4-e6f6-397c-9019-74fa67be439f")
    #     self.assertFalse(status)


class PRootEngineTestCase(unittest.TestCase):
    """Test PRootEngine() class for containers execution."""

    @classmethod
    def setUpClass(cls):
        """Setup test."""
        set_env()

    def _init(self):
        """Configure variables."""
        udocker.Config = mock.MagicMock()
        udocker.Config.hostauth_list = ("/etc/passwd", "/etc/group")
        udocker.Config.cmd = "/bin/bash"
        udocker.Config.cpu_affinity_exec_tools = \
            (["numactl", "-C", "%s", "--", ], ["taskset", "-c", "%s", ])
        udocker.Config.valid_host_env = "HOME"
        udocker.Config.return_value.username.return_value = "user"
        udocker.Config.return_value.userhome.return_value = "/"
        udocker.Config.return_value.oskernel.return_value = "4.8.13"
        udocker.Config.location = ""

    # @mock.patch('udocker.ExecutionEngineCommon')
    # @mock.patch('udocker.LocalRepository')
    # def test_01_init(self, mock_local, mock_exeng):
    #     """Test01 PRootEngine()."""
    #     self._init()
    #     prex = udocker.PRootEngine(mock_local)
    #     self.assertFalse(prex.proot_noseccomp)
    #     self.assertEqual(prex._kernel, "4.8.13")
    #     self.assertEqual(prex.proot_exec, None)

    # @mock.patch('udocker.Config')
    # @mock.patch('udocker.ExecutionMode')
    # @mock.patch('udocker.FileUtil.find_file_in_dir')
    # @mock.patch('udocker.LocalRepository')
    # def test_02_select_proot(self, mock_local, mock_fimage, mock_execmode,
    #                          mock_config):
    #     """Test02 PRootEngine().select_proot()."""
    #     self._init()
    #     udocker.Config.return_value.arch.return_value = "amd64"
    #     udocker.Config.return_value.oskernel_isgreater.return_value = False
    #     mock_fimage.return_value = "proot-4_8_0"
    #     mock_execmode.return_value.get_mode.return_value = ""
    #     udocker.Config.return_value.proot_noseccomp = None
    #     prex = udocker.PRootEngine(mock_local)
    #     prex.exec_mode = mock_execmode
    #     prex.select_proot()
    #     self.assertFalse(prex.proot_noseccomp)

    #     udocker.Config.return_value.oskernel_isgreater.return_value = True
    #     mock_fimage.return_value = "proot"
    #     prex = udocker.PRootEngine(mock_local)
    #     prex.exec_mode = mock_execmode
    #     udocker.Config.return_value.proot_noseccomp = True
    #     prex.select_proot()
    #     self.assertTrue(prex.proot_noseccomp)

    #     udocker.Config.return_value.oskernel_isgreater.return_value = True
    #     mock_fimage.return_value = "proot"
    #     prex = udocker.PRootEngine(mock_local)
    #     prex.exec_mode = mock_execmode
    #     udocker.Config.return_value.proot_noseccomp = False
    #     prex.select_proot()
    #     self.assertFalse(prex.proot_noseccomp)

    #     udocker.Config.return_value.oskernel_isgreater.return_value = True
    #     mock_fimage.return_value = "proot-x86_64-4_8_0"
    #     prex = udocker.PRootEngine(mock_local)
    #     prex.exec_mode = mock_execmode
    #     udocker.Config.return_value.proot_noseccomp = None
    #     prex.select_proot()
    #     self.assertFalse(prex.proot_noseccomp)

    #     udocker.Config.return_value.oskernel_isgreater.return_value = True
    #     mock_fimage.return_value = "proot-x86_64-4_8_0"
    #     prex = udocker.PRootEngine(mock_local)
    #     prex.exec_mode = mock_execmode
    #     udocker.Config.return_value.proot_noseccomp = False
    #     prex.select_proot()
    #     self.assertFalse(prex.proot_noseccomp)

    #     udocker.Config.return_value.oskernel_isgreater.return_value = True
    #     mock_fimage.return_value = "proot-x86_64-4_8_0"
    #     prex = udocker.PRootEngine(mock_local)
    #     prex.exec_mode = mock_execmode
    #     udocker.Config.return_value.proot_noseccomp = True
    #     prex.select_proot()
    #     self.assertTrue(prex.proot_noseccomp)

    @mock.patch('udocker.LocalRepository')
    def test_03__set_uid_map(self, mock_local):
        """Test03 PRootEngine()._set_uid_map()."""
        self._init()
        prex = udocker.PRootEngine(mock_local)
        prex.opt["uid"] = "0"
        status = prex._set_uid_map()
        self.assertEqual(status, ['-0'])

        prex = udocker.PRootEngine(mock_local)
        prex.opt["uid"] = "1000"
        prex.opt["gid"] = "1001"
        status = prex._set_uid_map()
        self.assertEqual(status, ['-i', '1000:1001'])

    @mock.patch('udocker.LocalRepository')
    def test_04__create_mountpoint(self, mock_local):
        """Test04 PRootEngine()._create_mountpoint()."""
        self._init()
        prex = udocker.PRootEngine(mock_local)
        status = prex._create_mountpoint("/host/file", "/cont/file")
        self.assertTrue(status)

    @mock.patch('udocker.LocalRepository')
    def test_05__get_volume_bindings(self, mock_local):
        """Test05 PRootEngine()._get_volume_bindings()."""
        self._init()
        prex = udocker.PRootEngine(mock_local)
        prex.opt["vol"] = ()
        status = prex._get_volume_bindings()
        self.assertEqual(status, [])
        #
        prex = udocker.PRootEngine(mock_local)
        prex.opt["vol"] = ("/tmp", "/bbb",)
        status = prex._get_volume_bindings()
        self.assertEqual(status, ['-b', '/tmp:/tmp', '-b', '/bbb:/bbb'])

    @mock.patch('udocker.ExecutionEngineCommon._get_portsmap')
    @mock.patch('udocker.LocalRepository')
    def test_07__get_network_map(self, mock_local, mock_portsmap):
        """Test07 PRootEngine()._get_network_map()."""
        self._init()
        mock_portsmap.return_value = {80: 8080, 443: 8443}
        prex = udocker.PRootEngine(mock_local)
        prex.opt["netcoop"] = None
        status = prex._get_network_map()
        self.assertEqual(status, ["-p", "80:8080 ", "-p", "443:8443 "])

    @mock.patch('udocker.subprocess.call')
    @mock.patch('udocker.PRootEngine._run_banner')
    @mock.patch('udocker.PRootEngine._run_env_cleanup_dict')
    @mock.patch('udocker.PRootEngine._set_uid_map')
    @mock.patch('udocker.PRootEngine._get_volume_bindings')
    @mock.patch('udocker.PRootEngine._set_cpu_affinity')
    @mock.patch('udocker.PRootEngine._check_env')
    @mock.patch('udocker.PRootEngine._run_env_set')
    @mock.patch('udocker.os.getenv')
    @mock.patch('udocker.PRootEngine.select_proot')
    @mock.patch('udocker.ExecutionEngineCommon._run_init')
    @mock.patch('udocker.LocalRepository')
    def test_08_run(self, mock_local, mock_run_init, mock_sel_proot,
                    mock_getenv, mock_run_env_set, mock_check_env,
                    mock_set_cpu_aff, mock_get_vol_bind, mock_set_uid_map,
                    mock_env_cleanup_dict, mock_run_banner, mock_call):
        """Test08 PRootEngine().run()."""
        mock_run_init.return_value = False
        self._init()
        prex = udocker.PRootEngine(mock_local)
        status = prex.run("CONTAINERID")
        self.assertEqual(status, 2)

        mock_run_init.return_value = True
        self._init()
        mock_check_env.return_value = False
        prex = udocker.PRootEngine(mock_local)
        prex.proot_noseccomp = False
        prex.opt = dict()
        prex.opt["env"] = []
        prex.opt["kernel"] = ""
        prex.opt["netcoop"] = False
        prex.opt["portsmap"] = []
        status = prex.run("CONTAINERID")
        self.assertEqual(status, 4)

        mock_run_init.return_value = True
        self._init()
        mock_check_env.return_value = True
        mock_set_cpu_aff.return_value = []
        mock_get_vol_bind.return_value = ""
        mock_set_uid_map.return_value = ""
        mock_call.return_value = 5
        prex = udocker.PRootEngine(mock_local)
        prex.proot_exec = "/.udocker/bin/proot"
        prex.proot_noseccomp = False
        prex.opt = dict()
        prex.opt["env"] = []
        prex.opt["kernel"] = ""
        prex.opt["netcoop"] = False
        prex.opt["portsmap"] = []
        prex.opt["hostenv"] = ""
        prex.opt["cwd"] = "/"
        prex.opt["cmd"] = "/bin/bash"
        prex._kernel = ""
        prex.container_root = ""
        status = prex.run("CONTAINERID")
        self.assertEqual(status, 5)


class RuncEngineTestCase(unittest.TestCase):
    """Test RuncEngine() containers execution with runC."""

    @classmethod
    def setUpClass(cls):
        """Setup test."""
        set_env()

    def _init(self):
        """Configure variables."""
        udocker.Config = mock.MagicMock()
        udocker.Config.hostauth_list = ("/etc/passwd", "/etc/group")
        udocker.Config.cmd = "/bin/bash"
        udocker.Config.cpu_affinity_exec_tools = \
            (["numactl", "-C", "%s", "--", ], ["taskset", "-c", "%s", ])
        udocker.Config.valid_host_env = "HOME"
        udocker.Config.return_value.username.return_value = "user"
        udocker.Config.return_value.userhome.return_value = "/"
        udocker.Config.return_value.oskernel.return_value = "4.8.13"
        udocker.Config.location = ""

    # @mock.patch('udocker.ExecutionEngineCommon')
    # @mock.patch('udocker.LocalRepository')
    # def test_01_init(self, mock_local, mock_exeng):
    #     """Test01 RuncEngine()."""
    #     self._init()
    #     rcex = udocker.RuncEngine(mock_local)
    #     self.assertEqual(rcex.runc_exec, None)

    # @mock.patch('udocker.Config')
    # @mock.patch('udocker.ExecutionMode')
    # @mock.patch('udocker.FileUtil')
    # @mock.patch('udocker.LocalRepository')
    # def test_02_select_runc(self, mock_local, mock_futil, mock_execmode,
    #                         mock_config):
    #     """Test02 RuncEngine().select_runc()."""
    #     self._init()
    #     udocker.Config.return_value.arch.return_value = "arm"
    #     udocker.Config.return_value.oskernel_isgreater.return_value = False
    #     mock_futil.return_value.find_file_in_dir.return_value = "runc-arm"
    #     mock_execmode.return_value.get_mode.return_value = ""
    #     rcex = udocker.RuncEngine(mock_local)
    #     rcex.exec_mode = mock_execmode
    #     rcex.select_runc()
    #     self.assertEqual(rcex.runc_exec, "runc-arm")

    @mock.patch('udocker.json.load')
    @mock.patch('udocker.subprocess.call')
    @mock.patch('udocker.os.path.realpath')
    @mock.patch('udocker.FileUtil')
    @mock.patch('udocker.LocalRepository')
    def test_03__load_spec(self, mock_local, mock_futil, mock_realpath,
                           mock_call, mock_jsonload):
        """Test03 RuncEngine()._load_spec()."""
        self._init()
        mock_futil.reset()
        mock_futil.return_value.size.return_value = 1
        rcex = udocker.RuncEngine(mock_local)
        rcex._load_spec(False)
        self.assertFalse(mock_futil.return_value.remove.called)

        mock_futil.reset()
        mock_futil.return_value.size.return_value = 1
        rcex = udocker.RuncEngine(mock_local)
        rcex._load_spec(True)
        self.assertTrue(mock_futil.return_value.remove.called)

        mock_futil.reset()
        mock_futil.return_value.size.return_value = -1
        mock_realpath.return_value = "/.udocker/containers/aaaaa"
        mock_call.return_value = True
        rcex = udocker.RuncEngine(mock_local)
        rcex.runc_exec = "runc"
        status = rcex._load_spec(False)
        self.assertFalse(status)

        mock_futil.reset()
        mock_futil.return_value.size.return_value = -1
        mock_realpath.return_value = "/.udocker/containers/aaaaa"
        mock_call.return_value = False  # ok
        mock_jsonload.return_value = "JSON"
        rcex = udocker.RuncEngine(mock_local)
        rcex.runc_exec = "runc"
        with mock.patch(BUILTINS + '.open', mock.mock_open()):
            status = rcex._load_spec(False)
        self.assertEqual(status, "JSON")

        mock_futil.reset()
        mock_futil.return_value.size.return_value = -1
        mock_realpath.return_value = "/.udocker/containers/aaaaa"
        mock_call.return_value = False  # ok
        mock_jsonload.return_value = "JSON"
        mock_jsonload.side_effect = OSError("reading json")
        rcex = udocker.RuncEngine(mock_local)
        rcex.runc_exec = "runc"
        with mock.patch(BUILTINS + '.open', mock.mock_open()):
            status = rcex._load_spec(False)
        self.assertEqual(status, None)

    @mock.patch('udocker.json.dump')
    @mock.patch('udocker.LocalRepository')
    def test_04__save_spec(self, mock_local, mock_jsondump):
        """Test04 RuncEngine()._save_spec()."""
        self._init()
        rcex = udocker.RuncEngine(mock_local)
        rcex._container_specjson = "JSON"
        with mock.patch(BUILTINS + '.open', mock.mock_open()):
            status = rcex._save_spec()
        self.assertTrue(status)

        mock_jsondump.side_effect = OSError("in open")
        rcex = udocker.RuncEngine(mock_local)
        rcex._container_specjson = "JSON"
        with mock.patch(BUILTINS + '.open', mock.mock_open()):
            status = rcex._save_spec()
        self.assertFalse(status)

    # def test_05__remove_quotes(self):
    #     """Test05 RuncEngine()._remove_quotes()."""
    #     pass

    @mock.patch('udocker.os.getgid')
    @mock.patch('udocker.os.getuid')
    @mock.patch('udocker.platform.node')
    @mock.patch('udocker.os.path.realpath')
    @mock.patch('udocker.LocalRepository')
    def test_06__set_spec(self, mock_local, mock_realpath, mock_node,
                          mock_getuid, mock_getgid):
        """Test06 RuncEngine()._set_spec()."""
        self._init()
        # rcex.opt["hostname"] has nodename
        mock_realpath.return_value = "/.udocker/containers/aaaaaa/ROOT"
        mock_node.return_value = "nodename.local"
        rcex = udocker.RuncEngine(mock_local)
        rcex.opt = dict()
        rcex._container_specjson = dict()
        rcex._container_specjson["root"] = dict()
        rcex._container_specjson["process"] = dict()
        rcex._container_specjson["linux"] = dict()
        rcex._container_specjson["linux"]["uidMappings"] = dict()
        rcex._container_specjson["linux"]["gidMappings"] = dict()
        rcex.opt["cwd"] = "/"
        rcex.opt["env"] = []
        rcex.opt["cmd"] = "bash"
        rcex.opt["hostname"] = "node.domain"
        json_obj = rcex._set_spec()
        self.assertEqual(json_obj["hostname"], "node.domain")

        # empty rcex.opt["hostname"]
        mock_realpath.return_value = "/.udocker/containers/aaaaaa/ROOT"
        mock_node.return_value = "nodename.local"
        rcex = udocker.RuncEngine(mock_local)
        rcex.opt = dict()
        rcex._container_specjson = dict()
        rcex._container_specjson["root"] = dict()
        rcex._container_specjson["process"] = dict()
        rcex._container_specjson["linux"] = dict()
        rcex._container_specjson["linux"]["uidMappings"] = dict()
        rcex._container_specjson["linux"]["gidMappings"] = dict()
        rcex.opt["cwd"] = "/"
        rcex.opt["env"] = []
        rcex.opt["cmd"] = "bash"
        rcex.opt["hostname"] = ""
        json_obj = rcex._set_spec()
        self.assertEqual(json_obj["hostname"], "nodename.local")

        # environment passes to container json
        mock_realpath.return_value = "/.udocker/containers/aaaaaa/ROOT"
        mock_node.return_value = "nodename.local"
        rcex = udocker.RuncEngine(mock_local)
        rcex.opt = dict()
        rcex._container_specjson = dict()
        rcex._container_specjson["root"] = dict()
        rcex._container_specjson["process"] = dict()
        rcex._container_specjson["linux"] = dict()
        rcex._container_specjson["linux"]["uidMappings"] = dict()
        rcex._container_specjson["linux"]["gidMappings"] = dict()
        rcex.opt["cwd"] = "/"
        rcex.opt["env"] = ["AA=aa", "BB=bb"]
        rcex.opt["cmd"] = "bash"
        rcex.opt["hostname"] = ""
        json_obj = rcex._set_spec()
        self.assertIn("AA=aa", json_obj["process"]["env"])

        # environment syntax error
        mock_realpath.return_value = "/.udocker/containers/aaaaaa/ROOT"
        mock_node.return_value = "nodename.local"
        rcex = udocker.RuncEngine(mock_local)
        rcex.opt = dict()
        rcex._container_specjson = dict()
        rcex._container_specjson["root"] = dict()
        rcex._container_specjson["process"] = dict()
        rcex._container_specjson["linux"] = dict()
        rcex._container_specjson["linux"]["uidMappings"] = dict()
        rcex._container_specjson["linux"]["gidMappings"] = dict()
        rcex.opt["cwd"] = "/"
        rcex.opt["env"] = ["=aa", "BB=bb"]
        rcex.opt["cmd"] = "bash"
        rcex.opt["hostname"] = ""
        json_obj = rcex._set_spec()
        self.assertNotIn("AA=aa", json_obj["process"]["env"])

        # uid and gid mappings
        mock_realpath.return_value = "/.udocker/containers/aaaaaa/ROOT"
        mock_node.return_value = "nodename.local"
        mock_getuid.return_value = 10000
        mock_getgid.return_value = 10000
        rcex = udocker.RuncEngine(mock_local)
        rcex.opt = dict()
        rcex._container_specjson = dict()
        rcex._container_specjson["root"] = dict()
        rcex._container_specjson["process"] = dict()
        rcex._container_specjson["linux"] = dict()
        rcex._container_specjson["linux"]["uidMappings"] = dict()
        rcex._container_specjson["linux"]["gidMappings"] = dict()
        rcex._container_specjson["linux"]["uidMappings"]["XXX"] = 0
        rcex._container_specjson["linux"]["gidMappings"]["XXX"] = 0
        rcex.opt["cwd"] = "/"
        rcex.opt["env"] = ["AA=aa", "BB=bb"]
        rcex.opt["cmd"] = "bash"
        rcex.opt["hostname"] = ""
        json_obj = rcex._set_spec()
        self.assertFalse(mock_getuid.called)
        self.assertFalse(mock_getgid.called)

    @mock.patch('udocker.Msg')
    @mock.patch('udocker.LocalRepository')
    def test_07__uid_check(self, mock_local, mock_msg):
        """Test07 RuncEngine()._uid_check()."""
        self._init()
        mock_msg.reset_mock()
        rcex = udocker.RuncEngine(mock_local)
        rcex.opt = dict()
        rcex._uid_check()
        self.assertFalse(mock_msg.called)

        mock_msg.reset_mock()
        rcex = udocker.RuncEngine(mock_local)
        rcex.opt = dict()
        rcex.opt["user"] = "root"
        rcex._uid_check()
        self.assertFalse(mock_msg.called)

        mock_msg.reset_mock()
        rcex = udocker.RuncEngine(mock_local)
        rcex.opt = dict()
        rcex.opt["user"] = "user01"
        rcex._uid_check()
        self.assertTrue(mock_msg.called)

    # def test_08__add_device_spec(self):
    #     """Test08 RuncEngine()._add_device_spec()."""
    #     pass

    # def test_09__add_devices(self):
    #     """Test09 RuncEngine()._add_devices()."""
    #     pass

    # @mock.patch('udocker.LocalRepository')
    # def test_10__create_mountpoint(self, mock_local):
    #     """Test10 RuncEngine()._create_mountpoint()."""
    #     self._init()
    #     rcex = udocker.RuncEngine(mock_local)
    #     status = rcex._create_mountpoint("HOSTPATH", "CONTPATH")
    #     self.assertTrue(status)

    @mock.patch('udocker.LocalRepository')
    def test_11__add_mount_spec(self, mock_local):
        """Test11 RuncEngine()._add_mount_spec()."""
        self._init()

        # ro
        rcex = udocker.RuncEngine(mock_local)
        rcex._container_specjson = dict()
        rcex._container_specjson["mounts"] = []
        status = rcex._add_mount_spec("/HOSTDIR", "/CONTDIR")
        mount = rcex._container_specjson["mounts"][0]
        self.assertEqual(mount["destination"], "/CONTDIR")
        self.assertEqual(mount["source"], "/HOSTDIR")
        self.assertIn("ro", mount["options"])

        # rw
        rcex = udocker.RuncEngine(mock_local)
        rcex._container_specjson = dict()
        rcex._container_specjson["mounts"] = []
        status = rcex._add_mount_spec("/HOSTDIR", "/CONTDIR", True)
        mount = rcex._container_specjson["mounts"][0]
        self.assertEqual(mount["destination"], "/CONTDIR")
        self.assertEqual(mount["source"], "/HOSTDIR")
        self.assertIn("rw", mount["options"])

    @mock.patch('udocker.LocalRepository')
    def test_12__del_mount_spec(self, mock_local):
        """Test12 RuncEngine()._del_mount_spec()."""
        self._init()
        rcex = udocker.RuncEngine(mock_local)
        rcex._container_specjson = dict()
        rcex._container_specjson["mounts"] = []
        mount = {"destination": "/CONTDIR",
                 "type": "none",
                 "source": "/HOSTDIR",
                 "options": ["rbind", "nosuid",
                             "noexec", "nodev",
                             "rw", ], }
        rcex._container_specjson["mounts"].append(mount)
        rcex._del_mount_spec("/HOSTDIR", "/CONTDIR")
        self.assertEqual(len(rcex._container_specjson["mounts"]), 1)

        rcex = udocker.RuncEngine(mock_local)
        rcex._container_specjson = dict()
        rcex._container_specjson["mounts"] = []
        mount = {"destination": "/XXXX",
                 "type": "none",
                 "source": "/HOSTDIR",
                 "options": ["rbind", "nosuid",
                             "noexec", "nodev",
                             "rw", ], }
        rcex._container_specjson["mounts"].append(mount)
        rcex._del_mount_spec("/HOSTDIR", "/CONTDIR")
        self.assertEqual(len(rcex._container_specjson["mounts"]), 1)

        rcex = udocker.RuncEngine(mock_local)
        rcex._container_specjson = dict()
        rcex._container_specjson["mounts"] = []
        mount = {"destination": "/CONTDIR",
                 "type": "none",
                 "source": "XXXX",
                 "options": ["rbind", "nosuid",
                             "noexec", "nodev",
                             "rw", ], }
        rcex._container_specjson["mounts"].append(mount)
        rcex._del_mount_spec("/HOSTDIR", "/CONTDIR")
        self.assertEqual(len(rcex._container_specjson["mounts"]), 1)

    @mock.patch('udocker.Msg')
    @mock.patch('udocker.os.path.isfile')
    @mock.patch('udocker.os.path.isdir')
    @mock.patch('udocker.RuncEngine._add_mount_spec')
    @mock.patch('udocker.FileBind')
    @mock.patch('udocker.LocalRepository')
    def test_13__add_volume_bindings(self, mock_local, mock_fbind,
                                     mock_add_mount_spec,
                                     mock_isdir, mock_isfile, mock_msg):
        """Test13 RuncEngine()._add_volume_bindings()."""
        self._init()
        mock_fbind.start.return_value = ("/HOSTDIR", "/CONTDIR")
        mock_isdir.reset_mock()
        rcex = udocker.RuncEngine(mock_local)
        rcex._filebind = mock_fbind
        rcex.opt["vol"] = dict()
        status = rcex._add_volume_bindings()
        self.assertFalse(mock_isdir.called)

        # isdir = False, isfile = False
        mock_fbind.start.return_value = ("/HOSTDIR", "/CONTDIR")
        mock_isdir.reset_mock()
        mock_isfile.reset_mock()
        mock_isdir.return_value = False
        mock_isfile.return_value = False
        rcex = udocker.RuncEngine(mock_local)
        rcex._filebind = mock_fbind
        rcex.opt["vol"] = []
        rcex.opt["vol"].append("/HOSTDIR:/CONTDIR")
        status = rcex._add_volume_bindings()
        self.assertTrue(mock_isdir.called)
        self.assertTrue(mock_isfile.called)

        # isdir = True
        mock_fbind.start.return_value = ("/HOSTDIR", "/CONTDIR")
        mock_isdir.reset_mock()
        mock_isfile.reset_mock()
        mock_add_mount_spec.reset_mock()
        mock_isdir.return_value = True
        mock_isfile.return_value = False
        rcex = udocker.RuncEngine(mock_local)
        rcex._filebind = mock_fbind
        rcex.opt["vol"] = []
        rcex.opt["vol"].append("/HOSTDIR:/CONTDIR")
        status = rcex._add_volume_bindings()
        self.assertTrue(mock_isdir.called)
        self.assertFalse(mock_isfile.called)
        self.assertTrue(mock_add_mount_spec.called)

        # isfile = True
        mock_fbind.start.return_value = ("/HOSTDIR", "/CONTDIR")
        mock_isdir.reset_mock()
        mock_isfile.reset_mock()
        mock_add_mount_spec.reset_mock()
        mock_fbind.reset_mock()
        mock_isdir.return_value = False
        mock_isfile.return_value = True
        udocker.Config.sysdirs_list = ["/CONTDIR"]
        rcex = udocker.RuncEngine(mock_local)
        rcex._filebind = mock_fbind
        rcex.opt["vol"] = []
        rcex.opt["vol"].append("/HOSTDIR:/CONTDIR")
        status = rcex._add_volume_bindings()
        self.assertTrue(mock_isdir.called)
        self.assertTrue(mock_isfile.called)
        # self.assertTrue(mock_fbind.add.called)

        # isfile = True
        mock_fbind.start.return_value = ("/HOSTDIR", "/CONTDIR")
        mock_isdir.reset_mock()
        mock_isfile.reset_mock()
        mock_add_mount_spec.reset_mock()
        mock_fbind.reset_mock()
        mock_isdir.return_value = False
        mock_isfile.return_value = True
        udocker.Config.sysdirs_list = [""]
        rcex = udocker.RuncEngine(mock_local)
        rcex._filebind = mock_fbind
        rcex.opt["vol"] = []
        rcex.opt["vol"].append("/HOSTDIR:/CONTDIR")
        status = rcex._add_volume_bindings()
        self.assertTrue(mock_isdir.called)
        self.assertTrue(mock_isfile.called)
        self.assertFalse(mock_fbind.add.called)

    @mock.patch('udocker.Msg')
    @mock.patch('udocker.os.getenv')
    @mock.patch('udocker.LocalRepository')
    def test_14__check_env(self, mock_local, mock_getenv, mock_msg):
        """Test14 RuncEngine()._check_env()."""
        self._init()
        rcex = udocker.RuncEngine(mock_local)
        rcex.opt["env"] = []
        status = rcex._check_env()
        self.assertTrue(status)

        mock_getenv.return_value = "aaaa"
        rcex = udocker.RuncEngine(mock_local)
        rcex.opt["env"] = ["", "HOME=/home/user01", "AAAA", ]
        status = rcex._check_env()
        self.assertTrue(status)
        self.assertNotIn("", rcex.opt["env"])
        self.assertIn("AAAA=aaaa", rcex.opt["env"])
        self.assertIn("HOME=/home/user01", rcex.opt["env"])

        rcex = udocker.RuncEngine(mock_local)
        rcex.opt["env"] = ["3WRONG=/home/user01", ]
        status = rcex._check_env()
        self.assertFalse(status)

        rcex = udocker.RuncEngine(mock_local)
        rcex.opt["env"] = ["WR ONG=/home/user01", ]
        status = rcex._check_env()
        self.assertFalse(status)

    # def test_15__run_invalid_options(self):
    #     """Test15 RuncEngine()._run_invalid_options()."""
    #     pass

    @mock.patch('udocker.subprocess.call')
    @mock.patch('udocker.Msg')
    @mock.patch('udocker.FileBind')
    @mock.patch('udocker.Unique')
    @mock.patch('udocker.RuncEngine._run_invalid_options')
    @mock.patch('udocker.RuncEngine._del_mount_spec')
    @mock.patch('udocker.RuncEngine._run_banner')
    @mock.patch('udocker.RuncEngine._save_spec')
    @mock.patch('udocker.RuncEngine._add_volume_bindings')
    @mock.patch('udocker.RuncEngine._set_spec')
    @mock.patch('udocker.RuncEngine._check_env')
    @mock.patch('udocker.RuncEngine._run_env_set')
    @mock.patch('udocker.RuncEngine._uid_check')
    @mock.patch('udocker.RuncEngine._run_env_cleanup_list')
    @mock.patch('udocker.RuncEngine._load_spec')
    @mock.patch('udocker.RuncEngine.select_runc')
    @mock.patch('udocker.RuncEngine._run_init')
    @mock.patch('udocker.LocalRepository')
    def test_16_run(self, mock_local, mock_run_init, mock_sel_runc,
                    mock_load_spec, mock_uid_check,
                    mock_run_env_cleanup_list, mock_env_set, mock_check_env,
                    mock_set_spec, mock_add_bindings, mock_save_spec,
                    mock_run_banner, mock_del_mount_spec, mock_inv_opt,
                    mock_unique, mock_fbind, mock_msg, mock_call):
        """Test16 RuncEngine().run()."""
        self._init()
        mock_run_init.return_value = False
        rcex = udocker.RuncEngine(mock_local)
        status = rcex.run("CONTAINERID")
        self.assertEqual(status, 2)

        mock_run_init.return_value = True
        mock_load_spec.return_value = False
        rcex = udocker.RuncEngine(mock_local)
        status = rcex.run("CONTAINERID")
        self.assertEqual(status, 4)

        mock_run_init.return_value = True
        mock_load_spec.return_value = True
        mock_check_env.return_value = False
        mock_run_env_cleanup_list.reset_mock()
        rcex = udocker.RuncEngine(mock_local)
        rcex.opt["hostenv"] = []
        status = rcex.run("CONTAINERID")
        self.assertTrue(mock_run_env_cleanup_list.called)
        self.assertEqual(status, 5)

        # mock_run_init.return_value = True
        # mock_load_spec.return_value = True
        # mock_check_env.return_value = True
        # mock_unique.return_value.uuid.return_value = "EXECUTION_ID"
        # mock_run_env_cleanup_list.reset_mock()
        # mock_call.reset_mock()
        # rcex = udocker.RuncEngine(mock_local)
        # rcex.runc_exec = "true"
        # rcex.container_dir = "/.udocker/containers/CONTAINER/ROOT"
        # rcex.opt["hostenv"] = []
        # status = rcex.run("CONTAINERID")
        # self.assertTrue(mock_run_env_cleanup_list.called)
        # self.assertTrue(mock_call.called)


class SingularityEngineTestCase(unittest.TestCase):
    """Docker container execution engine using Singularity"""

    @classmethod
    def setUpClass(cls):
        """Setup test."""
        set_env()

    def _init(self):
        """Configure variables."""
        udocker.Config = mock.MagicMock()
        udocker.Config.hostauth_list = ("/etc/passwd", "/etc/group")
        udocker.Config.location = ""
        udocker.Config.use_singularity_executable = "singularity"

    @mock.patch('udocker.LocalRepository')
    def test_01__init(self, mock_local):
        """Test01 SingularityEngine() constructor."""
        self._init()
        sing = udocker.SingularityEngine(mock_local)
        self.assertEqual(sing.executable, None)

    # @mock.patch('udocker.LocalRepository')
    # def test_02_select_singularity(self, mock_local):
    #     """Test02 SingularityEngine().select_singularity."""
    #     self._init()
    #     sing = udocker.SingularityEngine(mock_local)

    # @mock.patch('udocker.LocalRepository')
    # def test_03__get_volume_bindings(self, mock_local):
    #     """Test03 SingularityEngine()._get_volume_bindings."""
    #     self._init()
    #     sing = udocker.SingularityEngine(mock_local)

    # @mock.patch('udocker.LocalRepository')
    # def test_04__singularity_env_get(self, mock_local):
    #     """Test04 SingularityEngine()._singularity_env_get."""
    #     self._init()
    #     sing = udocker.SingularityEngine(mock_local)

    # @mock.patch('udocker.LocalRepository')
    # def test_05__make_container_directories(self, mock_local):
    #     """Test05 SingularityEngine()._make_container_directories."""
    #     self._init()
    #     sing = udocker.SingularityEngine(mock_local)

    # @mock.patch('udocker.LocalRepository')
    # def test_06__run_invalid_options(self, mock_local):
    #     """Test06 SingularityEngine()._run_invalid_options."""
    #     self._init()
    #     sing = udocker.SingularityEngine(mock_local)

    # @mock.patch('udocker.LocalRepository')
    # def test_07__run_as_root(self, mock_local):
    #     """Test07 SingularityEngine()._run_as_root."""
    #     self._init()
    #     sing = udocker.SingularityEngine(mock_local)

    # @mock.patch('udocker.LocalRepository')
    # def test_08__run_as_root(self, mock_local):
    #     """Test08 SingularityEngine()._run_as_root."""
    #     self._init()
    #     sing = udocker.SingularityEngine(mock_local)

class FakechrootEngineTestCase(unittest.TestCase):
    """Docker container execution engine using Fakechroot
    Provides a chroot like environment to run containers.
    Uses Fakechroot as chroot alternative.
    Inherits from ContainerEngine class
    """

    @classmethod
    def setUpClass(cls):
        """Setup test."""
        set_env()

    def _init(self):
        """Configure variables."""
        udocker.Config = mock.MagicMock()
        udocker.Config.hostauth_list = ("/etc/passwd", "/etc/group")
        udocker.Config.cmd = "/bin/bash"
        udocker.Config.cpu_affinity_exec_tools = \
            (["numactl", "-C", "%s", "--", ], ["taskset", "-c", "%s", ])
        udocker.Config.valid_host_env = "HOME"
        udocker.Config.return_value.username.return_value = "user"
        udocker.Config.return_value.userhome.return_value = "/"
        udocker.Config.return_value.oskernel.return_value = "4.8.13"
        udocker.Config.location = ""

    @mock.patch('udocker.LocalRepository')
    def test_01__init(self, mock_local):
        """Test01 FakechrootEngine() constructor."""
        self._init()
        ufake = udocker.FakechrootEngine(mock_local)
        self.assertEqual(ufake._fakechroot_so, "")
        self.assertIsNone(ufake._elfpatcher)

    # @mock.patch('udocker.Msg')
    # @mock.patch('udocker.os.path')
    # @mock.patch('udocker.Config')
    # @mock.patch('udocker.FileUtil')
    # @mock.patch('udocker.LocalRepository')
    # def test_02__select_fakechroot_so(self, mock_local, mock_futil,
    #                                   mock_config, mock_path, mock_msg):
    #     """Test02 FakechrootEngine()._select_fakechroot_so().
    #      Select fakechroot sharable object library."""
    #     self._init()
    #     ufake = udocker.FakechrootEngine(mock_local)
    #     out = ufake._select_fakechroot_so()
    #     self.assertTrue(mock_msg.return_value.err.called)

    @mock.patch('udocker.Msg')
    @mock.patch('udocker.LocalRepository')
    @mock.patch('udocker.NixAuthentication')
    @mock.patch('udocker.ExecutionEngineCommon')
    def test_03__setup_container_user(self, mock_eecom, mock_auth,
                                      mock_local, mock_msg):
        """Test03 FakechrootEngine()._setup_container_user()."""
        self._init()
        mock_eecom.return_value._uid_gid_from_str.side_effect = (None, None)
        ufake = udocker.FakechrootEngine(mock_local)
        status = ufake._setup_container_user(":lalves")
        self.assertFalse(status)

    @mock.patch('udocker.LocalRepository')
    def test_04__get_volume_bindings(self, mock_local):
        """Test04 FakechrootEngine()._get_volume_bindings()."""
        self._init()
        ufake = udocker.FakechrootEngine(mock_local)
        out = ufake._get_volume_bindings()
        self.assertEqual(out, ("", ""))

    @mock.patch('udocker.LocalRepository')
    def test_05__get_access_filesok(self, mock_local):
        """Test05 FakechrootEngine()._get_access_filesok()."""
        self._init()

        ufake = udocker.FakechrootEngine(mock_local)
        out = ufake._get_access_filesok()
        self.assertEqual(out, "")

    # @mock.patch('udocker.FileUtil')
    # @mock.patch('udocker.Msg')
    # @mock.patch('udocker.ContainerStructure')
    # @mock.patch('udocker.LocalRepository')
    # def test_06__fakechroot_env_set(self, mock_local, mock_struct,
    #                                 mock_msg, mock_futil):
    #     """Test06 FakechrootEngine()._fakechroot_env_set()."""
    #     self._init()
    #     mock_futil.return_value.find_file_in_dir.return_value = True
    #     ufake = udocker.FakechrootEngine(mock_local)
    #     ufake._fakechroot_env_set()
    #     self.assertTrue(mock_eecom.return_value.exec_mode.called)

    # def test_07__run_invalid_options(self):
    #     """Test07 FakechrootEngine()._run_invalid_options()."""

    # def test_08__run_add_script_support(self):
    #     """Test06 FakechrootEngine()._run_add_script_support()."""

    @mock.patch('udocker.Msg')
    @mock.patch('udocker.ContainerStructure')
    @mock.patch('udocker.LocalRepository')
    def test_09_run(self, mock_local, mock_struct, mock_msg):
        """Test09 FakechrootEngine().run()."""
        self._init()
        ufake = udocker.FakechrootEngine(mock_local)
        status = ufake.run("container_id")
        self.assertEqual(status, 2)


##
## NvidiaModeTestCase(unittest.TestCase)
##


class ExecutionModeTestCase(unittest.TestCase):
    """Test ExecutionMode()."""

    @classmethod
    def setUpClass(cls):
        """Setup test."""
        set_env()

    def _init(self):
        """Configure variables."""
        udocker.Config = mock.MagicMock()
        udocker.Config.hostauth_list = ("/etc/passwd", "/etc/group")
        udocker.Config.cmd = "/bin/bash"
        udocker.Config.cpu_affinity_exec_tools = \
            (["numactl", "-C", "%s", "--", ], ["taskset", "-c", "%s", ])
        udocker.Config.valid_host_env = "HOME"
        udocker.Config.return_value.username.return_value = "user"
        udocker.Config.return_value.userhome.return_value = "/"
        udocker.Config.return_value.oskernel.return_value = "4.8.13"
        udocker.Config.location = ""
        udocker.Config.keystore = "KEYSTORE"
        udocker.Config.return_value.osversion.return_value = "OSVERSION"
        udocker.Config.return_value.arch.return_value = "ARCH"
        udocker.Config.default_execution_mode = "P1"

    @mock.patch('udocker.os.path.realpath')
    @mock.patch('udocker.LocalRepository')
    def test_01_init(self, mock_local, mock_realpath):
        """Test01 ExecutionMode() constructor."""
        self._init()
        container_id = "CONTAINER_ID"
        modes = ("P1", "P2", "F1", "F2", "F3", "F4", "R1", "R2", "R3", "S1")
        mock_realpath.return_value = "/tmp"
        mock_local.cd_container.return_value = "/tmp"
        uexm = udocker.ExecutionMode(mock_local, container_id)
        self.assertEqual(uexm.localrepo, mock_local)
        self.assertEqual(uexm.container_id, "CONTAINER_ID")
        self.assertEqual(uexm.container_dir, "/tmp")
        self.assertEqual(uexm.container_root, "/tmp/ROOT")
        self.assertEqual(uexm.container_execmode, "/tmp/execmode")
        self.assertIsNone(uexm.exec_engine)
        self.assertEqual(uexm.valid_modes, modes)

    @mock.patch('udocker.os.path')
    @mock.patch('udocker.FileUtil')
    @mock.patch('udocker.LocalRepository')
    def test_02_get_mode(self, mock_local, mock_futil, mock_path):
        """Test02 ExecutionMode().get_mode()."""
        self._init()
        container_id = "CONTAINER_ID"
        mock_futil.return_value.getdata.return_value.strip.return_value = None
        uexm = udocker.ExecutionMode(mock_local, container_id)
        status = uexm.get_mode()
        self.assertEqual(status, "P1")

        mock_futil.return_value.getdata.return_value = "F3"
        uexm = udocker.ExecutionMode(mock_local, container_id)
        status = uexm.get_mode()
        self.assertEqual(status, "F3")

    @mock.patch('udocker.Msg')
    @mock.patch('udocker.ExecutionMode.get_mode')
    @mock.patch('udocker.os.path')
    @mock.patch('udocker.LocalRepository')
    @mock.patch('udocker.FileBind')
    @mock.patch('udocker.ElfPatcher')
    @mock.patch('udocker.FileUtil')
    @mock.patch('udocker.FileUtil.putdata')
    def test_03_set_mode(self, mock_putdata, mock_futil,
                         mock_elfp, mock_fbind, mock_local,
                         mock_path, mock_getmode, mock_msg):
        """Test03 ExecutionMode().set_mode()."""
        self._init()
        container_id = "CONTAINER_ID"
        mock_getmode.side_effect = \
            ["", "P1", "R1", "R1", "F4", "P1", "F3", "P2", "P2", "F4", "F4"]
        mock_putdata.return_value = True
        uexm = udocker.ExecutionMode(mock_local, container_id)
        status = uexm.set_mode("")
        self.assertFalse(status)

        status = uexm.set_mode("P1")
        self.assertTrue(status)

        uexm.set_mode("P1")
        self.assertTrue(mock_fbind.return_value.restore.called)

        uexm.set_mode("F1")
        self.assertTrue(mock_futil.return_value.links_conv.called)

        uexm.set_mode("P2")
        self.assertTrue(mock_elfp.return_value.restore_ld.called)

        uexm.set_mode("R1")
        self.assertTrue(mock_fbind.return_value.setup.called)

        uexm.set_mode("F2")
        self.assertTrue(mock_elfp.return_value.restore_binaries.called)

        uexm.set_mode("F2")
        self.assertTrue(mock_elfp.return_value.patch_ld.called)

        uexm.set_mode("F3")
        self.assertTrue(mock_elfp.return_value.patch_ld.called and
                        mock_elfp.return_value.patch_binaries.called)

        status = uexm.set_mode("F3")
        self.assertTrue(status)

        mock_putdata.return_value = False
        uexm.set_mode("F3")
        self.assertTrue(mock_msg.return_value.err.called)

    @mock.patch('udocker.ExecutionMode.get_mode')
    @mock.patch('udocker.os.path')
    @mock.patch('udocker.LocalRepository')
    def test_04_get_engine(self, mock_local, mock_path, mock_getmode):
        """Test04 ExecutionMode().get_engine()."""
        self._init()
        container_id = "CONTAINER_ID"
        mock_getmode.side_effect = ["R1", "F2", "P2"]
        uexm = udocker.ExecutionMode(mock_local, container_id)

        exec_engine = uexm.get_engine()
        self.assertIsInstance(exec_engine, udocker.RuncEngine)

        exec_engine = uexm.get_engine()
        self.assertIsInstance(exec_engine, udocker.FakechrootEngine)

        exec_engine = uexm.get_engine()
        self.assertIsInstance(exec_engine, udocker.PRootEngine)


class ContainerStructureTestCase(unittest.TestCase):
    """Test ContainerStructure() class for containers structure."""

    @classmethod
    def setUpClass(cls):
        """Setup test."""
        set_env()

    def _init(self):
        """Configure variables."""
        udocker.Config = mock.MagicMock()
        udocker.Config.hostauth_list = ("/etc/passwd", "/etc/group")
        udocker.Config.cmd = "/bin/bash"
        udocker.Config.cpu_affinity_exec_tools = \
            (["numactl", "-C", "%s", "--", ], ["taskset", "-c", "%s", ])
        udocker.Config.valid_host_env = "HOME"
        udocker.Config.return_value.username.return_value = "user"
        udocker.Config.return_value.userhome.return_value = "/"
        udocker.Config.location = ""
        udocker.Config.return_value.oskernel.return_value = "4.8.13"

    @mock.patch('udocker.LocalRepository')
    def test_01_init(self, mock_local):
        """Test01 ContainerStructure()."""
        self._init()
        prex = udocker.ContainerStructure(mock_local)
        self.assertEqual(prex.tag, "")
        self.assertEqual(prex.imagerepo, "")

        prex = udocker.ContainerStructure(mock_local, "123456")
        self.assertEqual(prex.tag, "")
        self.assertEqual(prex.imagerepo, "")
        self.assertEqual(prex.container_id, "123456")

    @mock.patch('udocker.Msg')
    @mock.patch('udocker.LocalRepository')
    def test_02_get_container_attr(self, mock_local, mock_msg):
        """Test02 ContainerStructure().get_container_attr()."""
        self._init()
        mock_msg.level = 0
        prex = udocker.ContainerStructure(mock_local)
        udocker.Config.location = "/"
        (container_dir, container_json) = prex.get_container_attr()
        self.assertEqual(container_dir, "")
        self.assertEqual(container_json, [])

        prex = udocker.ContainerStructure(mock_local)
        udocker.Config.location = ""
        mock_local.cd_container.return_value = ""
        (container_dir, container_json) = prex.get_container_attr()
        self.assertEqual(container_dir, False)
        self.assertEqual(container_json, False)

        prex = udocker.ContainerStructure(mock_local)
        udocker.Config.location = ""
        mock_local.cd_container.return_value = "/"
        mock_local.load_json.return_value = []
        (container_dir, container_json) = prex.get_container_attr()
        self.assertEqual(container_dir, False)
        self.assertEqual(container_json, False)

        prex = udocker.ContainerStructure(mock_local)
        udocker.Config.location = ""
        mock_local.cd_container.return_value = "/"
        mock_local.load_json.return_value = ["value", ]
        (container_dir, container_json) = prex.get_container_attr()
        self.assertEqual(container_dir, "/")
        self.assertEqual(container_json, ["value", ])

    # def test_03__chk_container_root(self):
    #     """Test03 ContainerStructure()._chk_container_root()."""
    #     pass

    @mock.patch('udocker.ContainerStructure._untar_layers')
    @mock.patch('udocker.Unique')
    @mock.patch('udocker.Msg')
    @mock.patch('udocker.LocalRepository')
    def test_04_create_fromimage(self, mock_local, mock_msg, mock_unique,
                                 mock_untar):
        """Test04 ContainerStructure().create_fromimage()."""
        self._init()
        mock_msg.level = 0
        prex = udocker.ContainerStructure(mock_local)
        mock_local.cd_imagerepo.return_value = ""
        status = prex.create_fromimage("imagerepo", "tag")
        self.assertFalse(status)

        prex = udocker.ContainerStructure(mock_local)
        mock_local.cd_imagerepo.return_value = "/"
        mock_local.get_image_attributes.return_value = ([], [])
        status = prex.create_fromimage("imagerepo", "tag")
        self.assertFalse(status)

        prex = udocker.ContainerStructure(mock_local)
        mock_local.cd_imagerepo.return_value = "/"
        mock_local.get_image_attributes.return_value = (["value", ], [])
        mock_local.setup_container.return_value = ""
        status = prex.create_fromimage("imagerepo", "tag")
        self.assertFalse(status)

        prex = udocker.ContainerStructure(mock_local)
        mock_local.cd_imagerepo.return_value = "/"
        mock_local.get_image_attributes.return_value = (["value", ], [])
        mock_local.setup_container.return_value = "/"
        mock_untar.return_value = False
        mock_unique.return_value.uuid.return_value = "123456"
        status = prex.create_fromimage("imagerepo", "tag")
        self.assertEqual(status, "123456")

    # def test_05_create_fromlayer(self):
    #     """Test05 ContainerStructure().create_fromlayer()."""
    #     pass

    # def test_06_clone_fromfile(self):
    #     """Test06 ContainerStructure().clone_fromfile()."""
    #     pass

    @mock.patch('udocker.Uprocess.get_output')
    @mock.patch('udocker.FileUtil')
    @mock.patch('udocker.Msg')
    @mock.patch('udocker.LocalRepository')
    def test_07__apply_whiteouts(self, mock_local, mock_msg,
                                 mock_futil, mock_upgetout):
        """Test07 ContainerStructure()._apply_whiteouts()."""
        self._init()
        mock_msg.level = 0
        mock_upgetout.return_value = ""
        prex = udocker.ContainerStructure(mock_local)
        with mock.patch.object(subprocess, 'Popen') as mock_popen:
            mock_popen.return_value.stdout.readline.side_effect = [
                "/aaa", "",
            ]
            status = prex._apply_whiteouts("tarball", "/tmp")
        self.assertEqual(status, None)
        self.assertFalse(mock_futil.called)

        mock_upgetout.return_value = "/a/.wh.x"
        prex = udocker.ContainerStructure(mock_local)
        with mock.patch.object(subprocess, 'Popen') as mock_popen:
            mock_popen.return_value.stdout.readline.side_effect = ["/a/.wh.x",
                                                                   "", ]
            status = prex._apply_whiteouts("tarball", "/tmp")
        self.assertTrue(mock_futil.called)

    @mock.patch('udocker.HostInfo.cmd_has_option')
    @mock.patch('udocker.subprocess.call')
    @mock.patch('udocker.ContainerStructure._apply_whiteouts')
    @mock.patch('udocker.Msg')
    @mock.patch('udocker.LocalRepository')
    def test_08__untar_layers(self, mock_local, mock_msg, mock_appwhite,
                              mock_call, mock_hasopt):
        """Test08 ContainerStructure()._untar_layers()."""
        self._init()
        mock_msg.level = 0
        tarfiles = ["a.tar", "b.tar", ]
        mock_call.return_value = False
        mock_hasopt.return_value = False
        prex = udocker.ContainerStructure(mock_local)
        status = prex._untar_layers(tarfiles, "/tmp")
        self.assertTrue(status)
        self.assertTrue(mock_call.called)

        mock_call.reset_mock()
        mock_call.return_value = True
        mock_hasopt.return_value = False
        prex = udocker.ContainerStructure(mock_local)
        status = prex._untar_layers(tarfiles, "/tmp")
        self.assertFalse(status)
        self.assertTrue(mock_call.called)

        mock_call.reset_mock()
        mock_call.return_value = True
        mock_hasopt.return_value = False
        prex = udocker.ContainerStructure(mock_local)
        status = prex._untar_layers([], "/tmp")
        self.assertFalse(status)
        self.assertFalse(mock_call.called)

    @mock.patch('udocker.Msg')
    @mock.patch('udocker.LocalRepository')
    def test_09_get_container_meta(self, mock_local, mock_msg):
        """Test09 ContainerStructure().get_container_meta()."""
        self._init()
        mock_msg.level = 0
        container_json = {
            "architecture": "amd64",
            "author": "https://github.com/CentOS/sig-cloud-instance-images",
            "config": {
                "AttachStderr": False,
                "AttachStdin": False,
                "AttachStdout": False,
                "Cmd": [
                    "/bin/bash"
                ],
                "Domainname": "",
                "Entrypoint": None,
                "Env": [
                    "PATH=\
                    /usr/local/sbin:\
                    /usr/local/bin:/usr/sbin:\
                    /usr/bin:/sbin:\
                    /bin"
                ],
                "Hostname": "9aac06993d69",
                "Image": "sha256:4f64745dd34556af8f644a7886fcf" +
                         "cb11c059f64e1b0a753cb41188656ec8b33",
                "Labels": {
                    "build-date": "20161102",
                    "license": "GPLv2",
                    "name": "CentOS Base Image",
                    "vendor": "CentOS"
                },
                "OnBuild": None,
                "OpenStdin": False,
                "StdinOnce": False,
                "Tty": False,
                "User": "",
                "Volumes": None,
                "WorkingDir": ""
            },
        }
        prex = udocker.ContainerStructure(mock_local)
        status = prex.get_container_meta("Cmd", "", container_json)
        self.assertEqual(status, "/bin/bash")

        prex = udocker.ContainerStructure(mock_local)
        status = prex.get_container_meta("XXX", "", container_json)
        self.assertEqual(status, "")

        prex = udocker.ContainerStructure(mock_local)
        status = prex.get_container_meta("Entrypoint", "BBB", container_json)
        self.assertEqual(status, "BBB")

    @mock.patch('udocker.Msg')
    @mock.patch('udocker.LocalRepository')
    def test_10__dict_to_str(self, mock_local, mock_msg):
        """Test10 ContainerStructure()._dict_to_str()."""
        self._init()
        mock_msg.level = 0
        prex = udocker.ContainerStructure(mock_local)
        status = prex._dict_to_str({'A': 1, 'B': 2})
        self.assertTrue(status in ("A:1 B:2 ", "B:2 A:1 ", ))

    @mock.patch('udocker.Msg')
    @mock.patch('udocker.LocalRepository')
    def test_11__dict_to_list(self, mock_local, mock_msg):
        """Test11 ContainerStructure()._dict_to_list()."""
        self._init()
        mock_msg.level = 0
        prex = udocker.ContainerStructure(mock_local)
        status = prex._dict_to_list({'A': 1, 'B': 2})
        self.assertEqual(sorted(status), sorted(["A:1", "B:2"]))

    # def test_12_export_tofile(self):
    #     """Test12 ContainerStructure().export_tofile()."""
    #     pass

    # def test_13_clone_tofile(self):
    #     """Test13 ContainerStructure().clone_tofile()."""
    #     pass

    # def test_14_clone(self):
    #     """Test14 ContainerStructure().clone()."""
    #     pass


class LocalRepositoryTestCase(unittest.TestCase):
    """Test LocalRepositoryTestCase().
    Management of local repository of container
    images and extracted containers
    Tests not yet implemented:
    _load_structure
    _find_top_layer_id
    _sorted_layers
    verify_image
    """

    def _localrepo(self, topdir):
        """Instantiate a local repository class."""
        topdir_path = os.getenv("HOME") + "/" + topdir
        udocker.Config = mock.patch('udocker.Config').start()
        udocker.Config.tmpdir = "/tmp"
        udocker.Config.homedir = "/tmp"
        udocker.Config.bindir = ""
        udocker.Config.libdir = ""
        udocker.Config.reposdir = ""
        udocker.Config.layersdir = ""
        udocker.Config.containersdir = ""
        udocker.FileUtil = mock.MagicMock()
        localrepo = udocker.LocalRepository(topdir_path)
        return localrepo

    @classmethod
    def setUpClass(cls):
        """Setup test."""
        set_env()

    def test_01_init(self):
        """Test01 LocalRepository() constructor."""
        localrepo = self._localrepo(UDOCKER_TOPDIR)
        self.assertTrue(localrepo.topdir)
        self.assertTrue(localrepo.reposdir)
        self.assertTrue(localrepo.layersdir)
        self.assertTrue(localrepo.containersdir)
        self.assertTrue(localrepo.bindir)
        self.assertTrue(localrepo.libdir)
        self.assertTrue(localrepo.homedir)
        self.assertEqual(localrepo.cur_repodir, "")
        self.assertEqual(localrepo.cur_tagdir, "")
        self.assertEqual(localrepo.cur_containerdir, "")

    def test_02_setup(self):
        """Test02 LocalRepository().setup()."""
        localrepo = self._localrepo("XXXX")
        self.assertEqual(os.path.basename(localrepo.topdir), "XXXX")
        localrepo.setup("YYYY")
        self.assertEqual(os.path.basename(localrepo.topdir), "YYYY")

    def test_03_create_repo(self):
        """Test03 LocalRepository().create_repo()."""
        localrepo = self._localrepo(UDOCKER_TOPDIR)
        subprocess.call(["/bin/rm", "-Rf", localrepo.topdir])
        self.assertFalse(os.path.exists(localrepo.topdir))
        localrepo.create_repo()
        self.assertTrue(os.path.exists(localrepo.topdir))
        self.assertTrue(os.path.exists(localrepo.reposdir))
        self.assertTrue(os.path.exists(localrepo.layersdir))
        self.assertTrue(os.path.exists(localrepo.containersdir))
        self.assertTrue(os.path.exists(localrepo.bindir))
        self.assertTrue(os.path.exists(localrepo.libdir))
        subprocess.call(["/bin/rm", "-Rf", localrepo.topdir])

    def test_04_is_repo(self):
        """Test04 LocalRepository().is_repo()."""
        localrepo = self._localrepo(UDOCKER_TOPDIR)
        subprocess.call(["/bin/rm", "-Rf", localrepo.topdir])
        localrepo.create_repo()
        self.assertTrue(localrepo.is_repo())
        subprocess.call(["/bin/rm", "-Rf", localrepo.topdir])

    def test_05_is_container_id(self):
        """Test05 LocalRepository().is_container_id."""
        localrepo = self._localrepo(UDOCKER_TOPDIR)
        self.assertTrue(localrepo.is_container_id(
            "10860ac1-6962-3a9b-a5f8-63bcfb67ce39"))
        self.assertFalse(localrepo.is_container_id(
            "10860ac1-6962-3a9b-a5f863bcfb67ce37"))
        self.assertFalse(localrepo.is_container_id(
            "10860ac1-6962--3a9b-a5f863bcfb67ce37"))
        self.assertFalse(localrepo.is_container_id(
            "-6962--3a9b-a5f863bcfb67ce37"))
        self.assertFalse(localrepo.is_container_id(
            12345678))

    def test_06_protect_container(self):
        """Test06 LocalRepository().protect_container()."""
        localrepo = self._localrepo(UDOCKER_TOPDIR)
        with mock.patch(BUILTINS + '.open', mock.mock_open()) as mopen:
            container_id = "d2578feb-acfc-37e0-8561-47335f85e46a"
            localrepo.protect_container(container_id)
            self.assertTrue(mopen.called)
            self.assertEqual(mopen.call_args, mock.call('/PROTECT', 'w'))

    @mock.patch('udocker.LocalRepository.cd_container')
    @mock.patch('udocker.LocalRepository._unprotect')
    def test_07_unprotect_container(self, mock_unprotect, mock_cdcont):
        """Test07 LocalRepository().unprotect_container()."""
        mock_cdcont.return_value = "/tmp"
        localrepo = self._localrepo(UDOCKER_TOPDIR)
        container_id = "d2578feb-acfc-37e0-8561-47335f85e46a"
        localrepo.unprotect_container(container_id)
        self.assertTrue(mock_unprotect.called)

    def test_08_isprotected_container(self):
        """Test08 LocalRepository().isprotected_container()."""
        localrepo = self._localrepo(UDOCKER_TOPDIR)
        with mock.patch('os.path.exists') as mexists:
            container_id = "d2578feb-acfc-37e0-8561-47335f85e46a"
            localrepo.isprotected_container(container_id)
            self.assertTrue(mexists.called)
            self.assertEqual(mexists.call_args, mock.call('/PROTECT'))

    @mock.patch('udocker.FileUtil')
    def test_09__protect(self, mock_futil):
        """Test09 LocalRepository()._protect().
        Set the protection mark in a container or image tag
        """
        localrepo = self._localrepo(UDOCKER_TOPDIR)
        mock_futil.return_value.isdir.return_value = True
        status = localrepo._protect
        self.assertTrue(status)

    @mock.patch('udocker.FileUtil')
    def test_10__unprotect(self, mock_futil):
        """Test10 LocalRepository()._unprotect().
        Remove protection mark from container or image tag.
        """
        localrepo = self._localrepo(UDOCKER_TOPDIR)
        mock_futil.return_value.isdir.return_value = True
        status = localrepo._unprotect("dir")
        self.assertTrue(status)

    @mock.patch('udocker.FileUtil')
    @mock.patch('udocker.os.path.exists')
    def test_11__isprotected(self, mock_exists, mock_futil):
        """Test11 LocalRepository()._isprotected().
        See if container or image tag are protected.
        """
        localrepo = self._localrepo(UDOCKER_TOPDIR)
        mock_futil.return_value.isdir.return_value = True
        mock_exists.return_value = True
        status = localrepo._isprotected("dir")
        self.assertTrue(status)

    @mock.patch('udocker.os.access')
    @mock.patch('udocker.os.path.isdir')
    @mock.patch('udocker.os.path.exists')
    @mock.patch.object(udocker.LocalRepository, 'cd_container')
    def test_12_iswriteable_container(self, mock_cd, mock_exists,
                                      mock_isdir, mock_access):
        """Test12 LocalRepository().iswriteable_container()."""
        localrepo = self._localrepo(UDOCKER_TOPDIR)
        container_id = "d2578feb-acfc-37e0-8561-47335f85e46a"
        mock_exists.return_value = False
        status = localrepo.iswriteable_container(container_id)
        self.assertEqual(status, 2)

        mock_exists.return_value = True
        mock_isdir.return_value = False
        status = localrepo.iswriteable_container(container_id)
        self.assertEqual(status, 3)

        mock_exists.return_value = True
        mock_isdir.return_value = True
        mock_access.return_value = True
        status = localrepo.iswriteable_container(container_id)
        self.assertEqual(status, 1)

        mock_exists.return_value = True
        mock_isdir.return_value = True
        mock_access.return_value = False
        status = localrepo.iswriteable_container(container_id)
        self.assertEqual(status, 0)

    @mock.patch('udocker.Uprocess.get_output')
    def test_13_get_size(self, mock_ugetout):
        """Test12 LocalRepository().get_size()."""
        localrepo = self._localrepo(UDOCKER_TOPDIR)
        container_id = "d2578feb-acfc-37e0-8561-47335f85e46a"
        mock_ugetout.return_value = "1024   ."
        status = localrepo.get_size(container_id)
        self.assertEqual(status, 1024)

    @mock.patch.object(udocker.LocalRepository, 'get_container_name')
    def test_14_get_containers_list(self, mock_getname):
        """Test14 LocalRepository().get_containers_list()."""
        localrepo = self._localrepo(UDOCKER_TOPDIR)
        mock_isdir = mock.patch('os.path.isdir').start()
        mock_isdir.return_value = True
        mock_listdir = mock.patch('os.listdir').start()
        mock_listdir.return_value = ['LINK']
        with mock.patch(BUILTINS + '.open',
                        mock.mock_open(read_data='REPONAME')):
            containers_list = localrepo.get_containers_list()
            self.assertEqual(os.path.basename(containers_list[0]), "LINK")

        mock_isdir = mock.patch('os.path.isdir').start()
        mock_isdir.return_value = True
        mock_listdir = mock.patch('os.listdir').start()
        mock_listdir.return_value = ['LINK']
        mock_islink = mock.patch('os.path.islink').start()
        mock_islink.return_value = False
        mock_getname.return_value = ["NAME1", "NAME2"]
        with mock.patch(BUILTINS + '.open',
                        mock.mock_open(read_data='REPONAME')):
            containers_list = localrepo.get_containers_list(False)
            self.assertEqual(os.path.basename(containers_list[0][1]),
                             "REPONAME")

    @mock.patch.object(udocker.LocalRepository, 'cd_container')
    @mock.patch.object(udocker.LocalRepository, 'get_containers_list')
    def test_15_del_container(self, mock_cdcont, mock_getcl):
        """Test15 LocalRepository().del_container()."""
        localrepo = self._localrepo(UDOCKER_TOPDIR)
        container_id = "d2578feb-acfc-37e0-8561-47335f85e46a"
        status = localrepo.del_container(container_id)
        self.assertTrue(mock_cdcont.called)
        self.assertFalse(status)

        mock_cdcont.return_value = ""
        mock_getcl.return_value = "tmp"
        status = localrepo.del_container(container_id)
        self.assertFalse(status)

        mock_cdcont.return_value = "/tmp"
        mock_getcl.return_value = "/tmp"
        status = localrepo.del_container(container_id)
        self.assertTrue(status)

    @mock.patch.object(udocker.LocalRepository, 'get_containers_list')
    def test_16_cd_container(self, mock_getlist):
        """Test16 LocalRepository().cd_container()."""
        localrepo = self._localrepo(UDOCKER_TOPDIR)
        mock_exists = mock.patch('os.path.exists').start()
        mock_exists.return_value = True
        mock_getlist.return_value = [localrepo.containersdir +
                                     "/CONTAINERNAME"]
        container_path = localrepo.cd_container("CONTAINERNAME")
        self.assertEqual(container_path, mock_getlist.return_value[0])

    @mock.patch('udocker.os.symlink')
    @mock.patch('udocker.os.path.exists')
    def test_17__symlink(self, mock_exists, mock_symlink):
        """Test17 LocalRepository()._symlink()."""
        localrepo = self._localrepo(UDOCKER_TOPDIR)
        mock_exists.return_value = True
        status = localrepo._symlink("EXISTINGFILE", "LINKFILE")
        self.assertFalse(status)

        mock_exists.return_value = False
        status = localrepo._symlink("EXISTINGFILE", "LINKFILE")
        self.assertTrue(status)

    def test_18__name_is_valid(self):
        """Test18 LocalRepository()._name_is_valid().
        Check name alias validity.
        """
        localrepo = self._localrepo(UDOCKER_TOPDIR)
        name = "lzskjghdlak"
        status = localrepo._name_is_valid(name)
        self.assertTrue(status)

        name = "lzskjghd/lak"
        status = localrepo._name_is_valid(name)
        self.assertFalse(status)

        name = ".lzsklak"
        status = localrepo._name_is_valid(name)
        self.assertFalse(status)

        name = "]lzsklak"
        status = localrepo._name_is_valid(name)
        self.assertFalse(status)

        name = "lzs[klak"
        status = localrepo._name_is_valid(name)
        self.assertFalse(status)

        name = "lzs klak"
        status = localrepo._name_is_valid(name)
        self.assertFalse(status)

        name = "x" * 2049
        status = localrepo._name_is_valid(name)
        self.assertFalse(status)

    @mock.patch('udocker.os.path.exists')
    @mock.patch.object(udocker.LocalRepository, '_symlink')
    @mock.patch.object(udocker.LocalRepository, 'cd_container')
    def test_19_set_container_name(self, mock_cd, mock_slink, mock_exists):
        """Test19 LocalRepository().set_container_name()."""
        localrepo = self._localrepo(UDOCKER_TOPDIR)
        container_id = "d2578feb-acfc-37e0-8561-47335f85e46a"
        status = localrepo.set_container_name(container_id, "WRONG[/")
        self.assertFalse(status)

        mock_cd.return_value = "CONTAINERDIR"
        mock_exists.return_value = True
        status = localrepo.set_container_name(container_id, "RIGHT")
        self.assertFalse(status)

        mock_cd.return_value = "CONTAINERDIR"
        mock_exists.return_value = False
        status = localrepo.set_container_name(container_id, "RIGHT")
        self.assertTrue(status)

    @mock.patch('udocker.LocalRepository._name_is_valid')
    @mock.patch('udocker.Msg')
    @mock.patch('udocker.os.path.exists')
    def test_20_del_container_name(self, mock_exists, mock_msg,
                                   mock_namevalid):
        """Test20 LocalRepository().del_container_name()."""
        localrepo = self._localrepo(UDOCKER_TOPDIR)
        mock_namevalid.return_value = False
        mock_exists.return_value = True
        udocker.FileUtil.return_value.remove.return_value = True
        status = localrepo.del_container_name("NAMEALIAS")
        self.assertFalse(status)

        mock_namevalid.return_value = True
        mock_exists.return_value = False
        udocker.FileUtil.return_value.remove.return_value = True
        status = localrepo.del_container_name("NAMEALIAS")
        self.assertFalse(status)

        mock_namevalid.return_value = True
        mock_exists.return_value = True
        udocker.FileUtil.return_value.remove.return_value = True
        status = localrepo.del_container_name("NAMEALIAS")
        # self.assertTrue(status)

        mock_namevalid.return_value = True
        mock_exists.return_value = True
        udocker.FileUtil.return_value.remove.return_value = False
        status = localrepo.del_container_name("NAMEALIAS")
        self.assertFalse(status)

    @mock.patch('udocker.os.readlink')
    @mock.patch('udocker.os.path.isdir')
    @mock.patch('udocker.os.path.islink')
    def test_21_get_container_id(self, mock_islink,
                                 mock_isdir, mock_readlink):
        """Test21 LocalRepository().get_container_id()."""
        localrepo = self._localrepo(UDOCKER_TOPDIR)
        status = localrepo.get_container_id(None)
        self.assertEqual(status, "")

        mock_islink.return_value = True
        mock_readlink.return_value = "BASENAME"
        status = localrepo.get_container_id("ALIASNAM")
        self.assertEqual(status, "BASENAME")

        mock_islink.return_value = False
        mock_isdir.return_value = False
        status = localrepo.get_container_id("ALIASNAM")
        self.assertEqual(status, "")

        mock_islink.return_value = False
        mock_isdir.return_value = True
        status = localrepo.get_container_id("ALIASNAM")
        self.assertEqual(status, "ALIASNAM")

    @mock.patch('udocker.os.readlink')
    @mock.patch('udocker.os.path.islink')
    @mock.patch('udocker.os.listdir')
    @mock.patch('udocker.os.path.isdir')
    def test_22_get_container_name(self, mock_isdir, mock_listdir,
                                   mock_islink, mock_readlink):
        """Test22 LocalRepository().get_container_name()."""
        localrepo = self._localrepo(UDOCKER_TOPDIR)
        mock_isdir.return_value = True
        mock_listdir.return_value = ['LINK']
        mock_islink.return_value = True
        mock_readlink.return_value = "/a/b/IMAGE:TAG"
        name_list = localrepo.get_container_name("IMAGE:TAG")
        self.assertEqual(name_list, ["LINK"])

    @mock.patch('udocker.os.makedirs')
    @mock.patch('udocker.os.path.exists')
    def test_23_setup_container(self, mock_exists, mock_makedirs):
        """Test23 LocalRepository().setup_container()."""
        localrepo = self._localrepo(UDOCKER_TOPDIR)
        mock_exists.return_value = True
        status = localrepo.setup_container("REPO", "TAG", "ID")
        self.assertEqual(status, "")

        mock_exists.return_value = False
        with mock.patch(BUILTINS + '.open', mock.mock_open()):
            status = localrepo.setup_container("REPO", "TAG", "ID")
            self.assertEqual(status, localrepo.containersdir + "/ID")
            self.assertEqual(localrepo.cur_containerdir,
                             localrepo.containersdir + "/ID")

    @mock.patch('udocker.FileUtil')
    @mock.patch('udocker.os.path.isfile')
    def test_24__is_tag(self, mock_isfile, mock_futil):
        """Test24 LocalRepository()._is_tag().
        Does this directory contain an image tag ?
        An image TAG indicates that this repo directory
        contains references to layers and metadata from
        which we can extract a container.
        """
        localrepo = self._localrepo(UDOCKER_TOPDIR)
        mock_isfile.return_value = True
        status = localrepo._is_tag("tagdir")
        self.assertTrue(status)

        mock_isfile.return_value = False
        status = localrepo._is_tag("tagdir")
        self.assertFalse(status)

    def test_25_protect_imagerepo(self):
        """Test25 LocalRepository().protect_imagerepo()."""
        localrepo = self._localrepo(UDOCKER_TOPDIR)
        with mock.patch(BUILTINS + '.open', mock.mock_open()) as mopen:
            localrepo.protect_imagerepo("IMAGE", "TAG")
            self.assertTrue(mopen.called)
            protect = localrepo.reposdir + "/IMAGE/TAG/PROTECT"
            self.assertEqual(mopen.call_args, mock.call(protect, 'w'))

    @mock.patch('udocker.LocalRepository._unprotect')
    def test_26_unprotect_imagerepo(self, mock_unprotect):
        """Test26 LocalRepository().unprotected_imagerepo()."""
        localrepo = self._localrepo(UDOCKER_TOPDIR)
        localrepo.unprotect_imagerepo("IMAGE", "TAG")
        self.assertTrue(mock_unprotect.called)

    def test_27_isprotected_imagerepo(self):
        """Test27 LocalRepository().isprotected_imagerepo()."""
        localrepo = self._localrepo(UDOCKER_TOPDIR)
        with mock.patch('os.path.exists') as mexists:
            localrepo.isprotected_imagerepo("IMAGE", "TAG")
            self.assertTrue(mexists.called)
            protect = localrepo.reposdir + "/IMAGE/TAG/PROTECT"
            self.assertEqual(mexists.call_args, mock.call(protect))

    @mock.patch('udocker.LocalRepository')
    def test_28_cd_imagerepo(self, mock_local):
        """Test28 LocalRepository().cd_imagerepo()."""
        localrepo = self._localrepo(UDOCKER_TOPDIR)
        localrepo.reposdir = "/tmp"
        out = localrepo.cd_imagerepo("IMAGE", "TAG")
        self.assertNotEqual(out, "")

    @mock.patch('udocker.FileUtil')
    @mock.patch('udocker.os.path.islink')
    @mock.patch('udocker.os.path.isdir')
    @mock.patch('udocker.os.listdir')
    def test_29__find(self, mock_listdir, mock_isdir, mock_islink, mock_futil):
        """Test29 LocalRepository()._find().
        is a specific layer filename referenced by another image TAG
        """
        localrepo = self._localrepo(UDOCKER_TOPDIR)
        mock_futil.return_value.isdir.return_value = True
        mock_listdir.return_value = ["file"]
        mock_islink.return_value = True
        filename = "file"
        folder = "/tmp"
        out = localrepo._find(filename, folder)
        self.assertEqual(out, ["/tmp/file"])

        mock_islink.return_value = False
        mock_isdir.return_value = False
        out = localrepo._find(filename, folder)
        self.assertEqual(out, [])

    @mock.patch('udocker.FileUtil')
    @mock.patch('udocker.os.path.islink')
    @mock.patch('udocker.os.path.isdir')
    @mock.patch('udocker.os.listdir')
    def test_30__inrepository(self, mock_listdir,
                              mock_isdir, mock_islink, mock_futil):
        """Test30 LocalRepository()._inrepository().
        Check if a given file is in the repository.
        """
        localrepo = self._localrepo(UDOCKER_TOPDIR)
        mock_futil.return_value.isdir.return_value = True
        mock_listdir.return_value = ["file"]
        mock_islink.return_value = True
        localrepo.reposdir = "/tmp"
        filename = "file"
        out = localrepo._inrepository(filename)
        self.assertEqual(out, ["/tmp/file"])

        mock_islink.return_value = False
        mock_isdir.return_value = False
        out = localrepo._inrepository(filename)
        self.assertEqual(out, [])

    @mock.patch('udocker.os.readlink')
    @mock.patch('udocker.os.path.islink')
    @mock.patch('udocker.os.listdir')
    @mock.patch.object(udocker.LocalRepository, '_inrepository')
    def test_31__remove_layers(self, mock_in,
                               mock_listdir, mock_islink, mock_readlink):
        """Test31 LocalRepository()._remove_layers()."""
        localrepo = self._localrepo(UDOCKER_TOPDIR)
        mock_listdir.return_value = []
        status = localrepo._remove_layers("TAG_DIR", False)
        self.assertTrue(status)

        mock_listdir.return_value = ["FILE1,", "FILE2"]
        mock_islink.return_value = False
        status = localrepo._remove_layers("TAG_DIR", False)
        self.assertTrue(status)

        mock_islink.return_value = True
        mock_readlink.return_value = "REALFILE"
        udocker.FileUtil.return_value.remove.return_value = False
        status = localrepo._remove_layers("TAG_DIR", False)
        self.assertFalse(status)

        udocker.FileUtil.return_value.remove.return_value = True
        status = localrepo._remove_layers("TAG_DIR", False)
        self.assertTrue(status)

        udocker.FileUtil.return_value.remove.return_value = True
        status = localrepo._remove_layers("TAG_DIR", True)
        self.assertTrue(status)

        udocker.FileUtil.return_value.remove.return_value = False
        mock_in.return_value = False
        status = localrepo._remove_layers("TAG_DIR", True)
        self.assertTrue(status)

        udocker.FileUtil.return_value.remove.return_value = False
        mock_in.return_value = False
        status = localrepo._remove_layers("TAG_DIR", False)
        self.assertFalse(status)

        udocker.FileUtil.return_value.remove.return_value = False
        mock_in.return_value = True
        status = localrepo._remove_layers("TAG_DIR", True)
        self.assertTrue(status)

    @mock.patch('udocker.FileUtil')
    @mock.patch.object(udocker.LocalRepository, '_remove_layers')
    @mock.patch.object(udocker.LocalRepository, 'cd_imagerepo')
    def test_32_del_imagerepo(self, mock_cd, mock_rmlayers, mock_futil):
        """Test32 LocalRepository()._del_imagerepo()."""
        localrepo = self._localrepo(UDOCKER_TOPDIR)
        mock_cd.return_value = False
        status = localrepo.del_imagerepo("IMAGE", "TAG", False)
        self.assertFalse(status)

        mock_cd.return_value = True
        status = localrepo.del_imagerepo("IMAGE", "TAG", False)
        self.assertTrue(status)

        localrepo.cur_repodir = "XXXX"
        localrepo.cur_tagdir = "XXXX"
        mock_futil.return_value.remove.return_value = True
        status = localrepo.del_imagerepo("IMAGE", "TAG", False)
        self.assertEqual(localrepo.cur_repodir, "")
        self.assertEqual(localrepo.cur_tagdir, "")
        self.assertTrue(status)

    def _sideffect_test_33(self, arg):
        """Side effect for isdir on test 33 _get_tags()."""
        if self.iter < 3:
            self.iter += 1
            return False
        return True

    @mock.patch('udocker.os.path.isdir')
    @mock.patch('udocker.os.listdir')
    @mock.patch('udocker.FileUtil')
    @mock.patch.object(udocker.LocalRepository, '_is_tag')
    def test_33__get_tags(self, mock_is, mock_futil,
                          mock_listdir, mock_isdir):
        """Test33 LocalRepository()._get_tags()."""
        localrepo = self._localrepo(UDOCKER_TOPDIR)
        mock_futil.return_value.isdir.return_value = False
        status = localrepo._get_tags("CONTAINERS_DIR")
        self.assertEqual(status, [])

        mock_futil.return_value.isdir.return_value = True
        mock_listdir.return_value = []
        status = localrepo._get_tags("CONTAINERS_DIR")
        self.assertEqual(status, [])

        mock_futil.return_value.isdir.return_value = True
        mock_listdir.return_value = ["FILE1", "FILE2"]
        mock_is.return_value = False
        mock_isdir.return_value = False
        status = localrepo._get_tags("CONTAINERS_DIR")
        self.assertEqual(status, [])

        mock_futil.return_value.isdir.return_value = True
        mock_listdir.return_value = ["FILE1", "FILE2"]
        mock_is.return_value = True
        status = localrepo._get_tags("CONTAINERS_DIR")
        expected_status = [('CONTAINERS_DIR', 'FILE1'),
                           ('CONTAINERS_DIR', 'FILE2')]
        self.assertEqual(status, expected_status)
        mock_futil.return_value.isdir.return_value = True
        mock_listdir.return_value = ["FILE1", "FILE2"]
        mock_is.return_value = False
        self.iter = 0
        mock_isdir.side_effect = self._sideffect_test_33
        status = localrepo._get_tags("CONTAINERS_DIR")
        expected_status = [('CONTAINERS_DIR', 'FILE1'),
                           ('CONTAINERS_DIR', 'FILE2')]
        self.assertEqual(self.iter, 2)
        self.assertEqual(status, [])

    @mock.patch.object(udocker.LocalRepository, '_get_tags')
    def test_34_get_imagerepos(self, mock_gtags):
        """Test34 LocalRepository().get_imagerepos()."""
        localrepo = self._localrepo(UDOCKER_TOPDIR)
        localrepo.get_imagerepos()
        self.assertTrue(mock_gtags.called)

    @mock.patch('udocker.LocalRepository')
    @mock.patch.object(udocker.LocalRepository, 'cd_container')
    def test_35_get_layers(self, mock_local, mock_cd):
        """Test35 LocalRepository().get_layers()."""
        localrepo = self._localrepo(UDOCKER_TOPDIR)
        localrepo.get_layers("IMAGE", "TAG")
        self.assertTrue(mock_cd.called)

    @mock.patch('udocker.os.path.islink')
    @mock.patch('udocker.os.path.exists')
    @mock.patch.object(udocker.LocalRepository, '_symlink')
    def test_36_add_image_layer(self, mock_slink, mock_exists, mock_islink):
        """Test36 LocalRepository().add_image_layer()."""
        localrepo = self._localrepo(UDOCKER_TOPDIR)
        localrepo.cur_repodir = ""
        localrepo.cur_tagdir = ""
        status = localrepo.add_image_layer("FILE")
        self.assertFalse(status)

        localrepo.cur_repodir = "IMAGE"
        localrepo.cur_tagdir = "TAG"
        status = localrepo.add_image_layer("FILE")
        self.assertTrue(status)

        mock_exists.return_value = False
        status = localrepo.add_image_layer("FILE")
        self.assertFalse(status)

        mock_exists.return_value = True
        mock_islink.return_value = True
        status = localrepo.add_image_layer("FILE")
        udocker.FileUtil.return_value.remove.return_value = True
        self.assertTrue(udocker.FileUtil.called)
        self.assertTrue(status)

        mock_exists.return_value = True
        mock_islink.return_value = False
        udocker.FileUtil.reset_mock()
        status = localrepo.add_image_layer("FILE")
        self.assertFalse(udocker.FileUtil.called)
        self.assertTrue(status)

    @mock.patch('udocker.os.makedirs')
    @mock.patch('udocker.os.path.exists')
    def test_37_setup_imagerepo(self, mock_exists, mock_makedirs):
        """Test37 LocalRepository().setup_imagerepo()."""
        localrepo = self._localrepo(UDOCKER_TOPDIR)
        status = localrepo.setup_imagerepo("")
        self.assertFalse(status)

        mock_exists.return_value = True
        status = localrepo.setup_imagerepo("IMAGE")
        expected_directory = localrepo.reposdir + "/IMAGE"
        self.assertEqual(localrepo.cur_repodir, expected_directory)
        self.assertFalse(status)

        mock_exists.return_value = False
        status = localrepo.setup_imagerepo("IMAGE")
        expected_directory = localrepo.reposdir + "/IMAGE"
        self.assertTrue(mock_makedirs.called)
        self.assertEqual(localrepo.cur_repodir, expected_directory)
        self.assertTrue(status)

    @mock.patch('udocker.os.makedirs')
    @mock.patch('udocker.os.path.exists')
    def test_38_setup_tag(self, mock_exists, mock_makedirs):
        """Test38 LocalRepository().setup_tag()."""
        localrepo = self._localrepo(UDOCKER_TOPDIR)
        mock_exists.return_value = False
        localrepo.cur_repodir = localrepo.reposdir + "/IMAGE"
        with mock.patch(BUILTINS + '.open', mock.mock_open()) as mopen:
            status = localrepo.setup_tag("NEWTAG")
            self.assertTrue(mock_makedirs.called)
            expected_directory = localrepo.reposdir + "/IMAGE/NEWTAG"
            self.assertEqual(localrepo.cur_tagdir, expected_directory)
            self.assertTrue(mopen.called)
            self.assertTrue(status)

    @mock.patch('udocker.os.listdir')
    @mock.patch('udocker.os.makedirs')
    @mock.patch('udocker.os.path.exists')
    def test_39_set_version(self, mock_exists, mock_makedirs, mock_listdir):
        """Test39 LocalRepository().set_version()."""
        localrepo = self._localrepo(UDOCKER_TOPDIR)
        status = localrepo.set_version("v1")
        self.assertFalse(mock_exists.called)
        self.assertFalse(status)

        localrepo.cur_repodir = localrepo.reposdir + "/IMAGE"
        localrepo.cur_tagdir = localrepo.cur_repodir + "/TAG"
        mock_exists.return_value = False
        status = localrepo.set_version("v1")
        self.assertFalse(mock_listdir.called)
        self.assertFalse(status)

        mock_exists.return_value = True
        with mock.patch(BUILTINS + '.open', mock.mock_open()) as mopen:
            status = localrepo.set_version("v1")
            self.assertTrue(mock_listdir.called)
            self.assertTrue(mopen.called)
            self.assertTrue(status)

    # Review complete test
    @mock.patch.object(udocker.LocalRepository, 'save_json')
    @mock.patch.object(udocker.LocalRepository, 'load_json')
    @mock.patch('udocker.os.path.exists')
    def test_40_get_image_attributes(self, mock_exists, mock_loadjson,
                                     mock_savejson):
        """Test40 LocalRepository().get_image_attributes()."""
        localrepo = self._localrepo(UDOCKER_TOPDIR)
        mock_exists.return_value = True
        mock_loadjson.return_value = None
        status = localrepo.get_image_attributes()
        self.assertEqual((None, None), status)

        mock_exists.side_effect = [True, False]
        mock_loadjson.side_effect = [("foolayername",), ]
        status = localrepo.get_image_attributes()
        self.assertEqual((None, None), status)

        # mock_exists.side_effect = [True, True, False]
        # mock_loadjson.side_effect = [("foolayername",), "foojson"]
        # status = localrepo.get_image_attributes()
        # self.assertEqual((None, None), status)

        mock_exists.side_effect = [True, True, True]
        mock_loadjson.side_effect = [("foolayername",), "foojson"]
        status = localrepo.get_image_attributes()
        self.assertEqual(('foojson', ['/foolayername.layer']), status)

        mock_exists.side_effect = [False, True]
        mock_loadjson.side_effect = [None, ]
        status = localrepo.get_image_attributes()
        self.assertEqual((None, None), status)

        mock_exists.side_effect = [False, True, False]
        manifest = {
            "fsLayers": ({"blobSum": "foolayername"},),
            "history": ({"v1Compatibility": '["foojsonstring"]'},)
        }
        mock_loadjson.side_effect = [manifest, ]
        status = localrepo.get_image_attributes()
        self.assertEqual((None, None), status)

        mock_exists.side_effect = [False, True, True]
        mock_loadjson.side_effect = [manifest, ]
        status = localrepo.get_image_attributes()
        self.assertEqual(([u'foojsonstring'], ['/foolayername']), status)

    @mock.patch('udocker.json.dump')
    @mock.patch('udocker.os.path.exists')
    def test_41_save_json(self, mock_exists, mock_jsondump):
        """Test41 LocalRepository().save_json()."""
        localrepo = self._localrepo(UDOCKER_TOPDIR)
        status = localrepo.save_json("filename", "data")
        self.assertFalse(mock_exists.called)
        self.assertFalse(status)

        localrepo.cur_repodir = localrepo.reposdir + "/IMAGE"
        localrepo.cur_tagdir = localrepo.cur_repodir + "/TAG"
        mock_exists.return_value = False
        status = localrepo.save_json("filename", "data")
        self.assertTrue(mock_exists.called)
        self.assertFalse(status)

        mock_exists.reset_mock()
        with mock.patch(BUILTINS + '.open', mock.mock_open()) as mopen:
            status = localrepo.save_json("/filename", "data")
            self.assertTrue(mopen.called)
            self.assertTrue(status)

        mock_exists.reset_mock()
        with mock.patch(BUILTINS + '.open', mock.mock_open()) as mopen:
            mopen.side_effect = IOError('foo')
            status = localrepo.save_json("/filename", "data")
            self.assertTrue(mopen.called)
            self.assertFalse(status)

    @mock.patch('udocker.json.load')
    @mock.patch('udocker.os.path.exists')
    def test_42_load_json(self, mock_exists, mock_jsonload):
        """Test42 LocalRepository().load_json()."""
        localrepo = self._localrepo(UDOCKER_TOPDIR)
        status = localrepo.load_json("filename")
        self.assertFalse(mock_exists.called)
        self.assertFalse(status)

        localrepo.cur_repodir = localrepo.reposdir + "/IMAGE"
        localrepo.cur_tagdir = localrepo.cur_repodir + "/TAG"
        mock_exists.return_value = False
        status = localrepo.load_json("filename")
        self.assertTrue(mock_exists.called)
        self.assertFalse(status)

        mock_exists.reset_mock()
        with mock.patch(BUILTINS + '.open', mock.mock_open()) as mopen:
            status = localrepo.load_json("/filename")
            self.assertTrue(mopen.called)
            self.assertTrue(status)

        mock_exists.reset_mock()
        with mock.patch(BUILTINS + '.open', mock.mock_open()) as mopen:
            mopen.side_effect = IOError('foo')
            status = localrepo.load_json("/filename")
            self.assertTrue(mopen.called)
            self.assertFalse(status)

    @mock.patch('udocker.FileUtil.isdir')
    @mock.patch('udocker.LocalRepository')
    @mock.patch('udocker.LocalRepository.load_json')
    @mock.patch('udocker.os.listdir')
    def test_43__load_structure(self, mock_listdir, mock_json,
                                mock_local, mock_isdir):
        """Test43 LocalRepository()._load_structure().
        Scan the repository structure of a given image tag.
        """
        localrepo = self._localrepo(UDOCKER_TOPDIR)
        mock_isdir.return_value = False
        structure = localrepo._load_structure("IMAGETAGDIR")
        self.assertTrue(structure["layers"])

        mock_isdir.return_value = True
        mock_listdir.return_value = ["ancestry"]
        localrepo.return_value = "JSON"
        structure = localrepo._load_structure("IMAGETAGDIR")
        # WIP
        # self.assertTrue("JSON" in structure["ancestry"])

    # def test_44__find_top_layer_id(self):
    #     """Test44 LocalRepository()._find_top_layer_id()."""
    #     pass

    # def test_45__sorted_layers(self):
    #     """Test45 LocalRepository()._sorted_layers()."""
    #     pass

    # def test_46__verify_layer_file(self):
    #     """Test46 LocalRepository()._verify_layer_file()."""
    #     pass

    @mock.patch('udocker.Msg')
    @mock.patch.object(udocker.LocalRepository, '_load_structure')
    def test_47_verify_image(self, mock_lstruct, mock_msg):
        """Test47 LocalRepository().verify_image()."""
        mock_msg.level = 0
        localrepo = self._localrepo(UDOCKER_TOPDIR)
        localrepo.verify_image()
        self.assertTrue(mock_lstruct.called)


class CurlHeaderTestCase(unittest.TestCase):
    """Test CurlHeader() http header parser."""

    @classmethod
    def setUpClass(cls):
        """Setup test."""
        set_env()

    def test_01_init(self):
        """Test01 CurlHeader() constructor."""
        curl_header = udocker.CurlHeader()
        self.assertFalse(curl_header.sizeonly)
        self.assertIsInstance(curl_header.data, dict)
        self.assertEqual("", curl_header.data["X-ND-HTTPSTATUS"])
        self.assertEqual("", curl_header.data["X-ND-CURLSTATUS"])

    def test_02_write(self):
        """Test02 CurlHeader().write()."""
        buff = ["HTTP/1.1 200 OK",
                "Content-Type: application/octet-stream",
                "Content-Length: 32", ]
        curl_header = udocker.CurlHeader()
        for line in buff:
            curl_header.write(line)
        self.assertEqual(curl_header.data["content-type"],
                         "application/octet-stream")
        self.assertEqual(curl_header.data["X-ND-HTTPSTATUS"],
                         "HTTP/1.1 200 OK")

        curl_header = udocker.CurlHeader()
        for line in buff:
            curl_header.write(line)
        buff_out = curl_header.getvalue()
        self.assertTrue("HTTP/1.1 200 OK" in buff_out)

        line = ""
        curl_header = udocker.CurlHeader()
        curl_header.sizeonly = True
        self.assertEqual(-1, curl_header.write(line))

    @mock.patch('udocker.CurlHeader.write')
    def test_03_setvalue_from_file(self, mock_write):
        """Test03 CurlHeader().setvalue_from_file()."""
        fakedata = StringIO('XXXX')
        with mock.patch(BUILTINS + '.open') as mopen:
            mopen.return_value.__iter__ = (
                lambda self: iter(fakedata.readline, ''))
            curl_header = udocker.CurlHeader()
            self.assertTrue(curl_header.setvalue_from_file("filename"))
            mock_write.assert_called_with('XXXX')

    def test_04_getvalue(self):
        """Test04 CurlHeader().getvalue()."""
        curl_header = udocker.CurlHeader()
        curl_header.data = "XXXX"
        self.assertEqual(curl_header.getvalue(), curl_header.data)


class GetURLTestCase(unittest.TestCase):
    """Test GetURL() perform http operations portably."""

    @classmethod
    def setUpClass(cls):
        """Setup test."""
        set_env()

    def _init(self):
        """Configure variables."""
        udocker.Config = mock.patch('udocker.Config').start()
        udocker.Config.timeout = 1
        udocker.Config.ctimeout = 1
        udocker.Config.download_timeout = 1
        udocker.Config.http_agent = ""
        udocker.Config.http_proxy = ""
        udocker.Config.http_insecure = 0
        udocker.Config.use_curl_executable = ""

    def _get(self, *args, **kwargs):
        """Mock for pycurl.get."""
        return args[0]

    @mock.patch('udocker.Msg')
    @mock.patch('udocker.GetURL._select_implementation')
    def test_01_init(self, mock_simplement, mock_msg):
        """Test01 GetURL() constructor."""
        self._init()
        mock_msg.level = 0
        geturl = udocker.GetURL()
        self.assertEqual(geturl.ctimeout, udocker.Config.ctimeout)
        self.assertEqual(geturl.insecure, udocker.Config.http_insecure)
        self.assertEqual(geturl.cache_support, False)

    @mock.patch('udocker.Msg')
    @mock.patch('udocker.GetURLexeCurl')
    @mock.patch('udocker.GetURLpyCurl')
    def test_02__select_implementation(self, mock_gupycurl, mock_guexecurl, mock_msg):
        """Test02 GetURL()._select_implementation()."""
        self._init()
        mock_msg.level = 0
        mock_gupycurl.return_value.is_available.return_value = True
        geturl = udocker.GetURL()
        geturl._select_implementation()
        self.assertEqual(geturl.cache_support, True)

        mock_gupycurl.return_value.is_available.return_value = False
        geturl = udocker.GetURL()
        geturl._select_implementation()
        self.assertEqual(geturl.cache_support, False)

        mock_guexecurl.return_value.is_available.return_value = False
        with self.assertRaises(NameError):
            udocker.GetURL()

    @mock.patch('udocker.GetURL._select_implementation')
    def test_03_get_content_length(self, mock_sel):
        """Test03 GetURL().get_content_length()."""
        self._init()
        geturl = udocker.GetURL()
        hdr = type('test', (object,), {})()
        hdr.data = {"content-length": 10, }
        self.assertEqual(geturl.get_content_length(hdr), 10)
        hdr.data = {"content-length": dict(), }
        self.assertEqual(geturl.get_content_length(hdr), -1)

    @mock.patch('udocker.GetURLpyCurl')
    def test_04_set_insecure(self, mock_gupycurl):
        """Test04 GetURL().set_insecure()."""
        self._init()
        mock_gupycurl.return_value.is_available.return_value = True
        geturl = udocker.GetURL()
        geturl.set_insecure()
        self.assertEqual(geturl.insecure, True)

        geturl.set_insecure(False)
        self.assertEqual(geturl.insecure, False)

    @mock.patch('udocker.GetURLpyCurl')
    def test_05_set_proxy(self, mock_gupycurl):
        """Test05 GetURL().set_proxy()."""
        self._init()
        mock_gupycurl.return_value.is_available.return_value = True
        geturl = udocker.GetURL()
        geturl.set_proxy("http://host")
        self.assertEqual(geturl.http_proxy, "http://host")

    @mock.patch('udocker.GetURL._select_implementation')
    def test_06_get(self, mock_sel):
        """Test06 GetURL().get() generic get."""
        self._init()
        geturl = udocker.GetURL()
        self.assertRaises(TypeError, geturl.get)
        #
        geturl = udocker.GetURL()
        geturl._geturl = type('test', (object,), {})()
        geturl._geturl.get = self._get
        self.assertEqual(geturl.get("http://host"), "http://host")

    @mock.patch('udocker.GetURL._select_implementation')
    def test_07_post(self, mock_sel):
        """Test07 GetURL().post() generic post."""
        self._init()
        geturl = udocker.GetURL()
        self.assertRaises(TypeError, geturl.post)
        self.assertRaises(TypeError, geturl.post, "http://host")
        #
        geturl = udocker.GetURL()
        geturl._geturl = type('test', (object,), {})()
        geturl._geturl.get = self._get
        self.assertEqual(geturl.post("http://host",
                                     {"DATA": 1, }), "http://host")

    # def test_08__get_status_code(self):
    #     """Test08 GetURL()._get_status_code()."""
    #     pass


class GetURLpyCurlTestCase(unittest.TestCase):
    """GetURLpyCurl TestCase."""

    @classmethod
    def setUpClass(cls):
        """Setup test."""
        set_env()

    def _init(self):
        """Configure variables."""
        udocker.Config = mock.patch('udocker.Config').start()
        udocker.Config.timeout = 1
        udocker.Config.ctimeout = 1
        udocker.Config.download_timeout = 1
        udocker.Config.http_agent = ""
        udocker.Config.http_proxy = ""
        udocker.Config.http_insecure = 0

    def _get(self, *args, **kwargs):
        """Mock for pycurl.get."""
        return args[0]

    # def test_01_init(self):
    #     """Test01 GetURLpyCurl() constructor."""
    #     pass

    @mock.patch('udocker.Msg')
    @mock.patch('udocker.GetURLpyCurl')
    def test_02_is_available(self, mock_gupycurl, mock_msg):
        """Test02 GetURLpyCurl()._is_available()."""
        self._init()
        mock_msg.level = 0
        geturl = udocker.GetURLpyCurl()
        geturl.is_available()
        mock_gupycurl.return_value.is_available.return_value = True
        self.assertTrue(geturl.is_available())

        mock_gupycurl.return_value.is_available.return_value = False
        self.assertFalse(geturl.is_available())

    # def test_03__select_implementation(self):
    #     """Test03 GetURLpyCurl()._select_implementation()."""
    #     pass

    @mock.patch('udocker.GetURLpyCurl._select_implementation')
    @mock.patch('udocker.Msg')
    @mock.patch('udocker.pycurl')
    @mock.patch('udocker.CurlHeader')
    def test_04__set_defaults(self, mock_hdr, mock_pyc, mock_msg, mock_sel):
        """Test04 GetURLpyCurl()._set_defaults()."""
        self._init()
        mock_sel.return_value.insecure.return_value = True
        geturl = udocker.GetURLpyCurl()
        geturl._set_defaults(mock_pyc, mock_hdr)
        self.assertTrue(mock_pyc.setopt.called)

        # when Msg.level >= Msg.DBG: AND insecure
        mock_msg.DBG.return_value = 3
        mock_msg.level.return_value = 3
        geturl._set_defaults(mock_pyc, mock_hdr)
        self.assertEqual(mock_pyc.setopt.call_count, 18)

        # when Msg.level < Msg.DBG: AND secure
        mock_sel.return_value.insecure.return_value = True
        mock_msg.DBG.return_value = 3
        mock_msg.level.return_value = 2
        geturl._set_defaults(mock_pyc, mock_hdr)
        self.assertEqual(mock_pyc.setopt.call_count, 27)

    @mock.patch('udocker.GetURLpyCurl._select_implementation')
    @mock.patch('udocker.Msg')
    @mock.patch('udocker.pycurl')
    @mock.patch('udocker.CurlHeader')
    def test_05__mkpycurl(self, mock_hdr, mock_pyc, mock_msg, mock_sel):
        """Test05 GetURL()._mkpycurl()."""
        self._init()
        mock_sel.return_value.insecure.return_value = True
        geturl = udocker.GetURLpyCurl()
        geturl._set_defaults(mock_pyc, mock_hdr)
        self.assertTrue(mock_pyc.setopt.called)

    @mock.patch('udocker.GetURLpyCurl._select_implementation')
    def test_06_get(self, mock_sel):
        """Test06 GetURLpyCurl().get() generic get."""
        self._init()
        geturl = udocker.GetURLpyCurl()
        geturl._geturl = type('test', (object,), {})()
        geturl.get = self._get
        self.assertEqual(geturl.get("http://host"), "http://host")


class GetURLexeCurlTestCase(unittest.TestCase):
    """GetURLexeCurl TestCase."""

    @classmethod
    def setUpClass(cls):
        """Setup test."""
        set_env()

    def _init(self):
        """Configure variables."""
        udocker.Config = mock.patch('udocker.Config').start()
        udocker.Config.timeout = 1
        udocker.Config.ctimeout = 1
        udocker.Config.download_timeout = 1
        udocker.Config.http_agent = ""
        udocker.Config.http_proxy = ""
        udocker.Config.http_insecure = 0

    def _get(self, *args, **kwargs):
        """Mock for pycurl.get."""
        return args[0]

    @mock.patch('udocker.Msg')
    @mock.patch('udocker.GetURL')
    def test_01_init(self, mock_gcurl, mock_msg):
        """Test01 GetURLexeCurl() constructor."""
        self._init()
        self.assertIsNone(udocker.GetURLexeCurl()._opts)
        self.assertIsNone(udocker.GetURLexeCurl()._files)

    @mock.patch('udocker.Msg')
    @mock.patch('udocker.FileUtil')
    @mock.patch('udocker.GetURLexeCurl._select_implementation')
    def test_02_is_available(self, mock_sel, mock_futil, mock_msg):
        """Test02 GetURLexeCurl()._is_available()."""
        self._init()
        mock_msg.level = 0
        geturl = udocker.GetURLexeCurl()
        mock_futil.return_value.find_exec.return_value = "/tmp"
        self.assertTrue(geturl.is_available())

        mock_futil.return_value.find_exec.return_value = ""
        self.assertFalse(geturl.is_available())

    # def test_03__select_implementation(self):
    #     """Test03 GetURLexeCurl()._select_implementation()."""
    #     pass

    @mock.patch('udocker.Msg')
    @mock.patch('udocker.GetURLexeCurl._select_implementation')
    @mock.patch('udocker.FileUtil')
    def test_04__set_defaults(self, mock_sel, mock_futil, mock_msg):
        """Test04 GetURLexeCurl()._set_defaults()."""
        self._init()
        geturl = udocker.GetURLexeCurl()
        geturl._set_defaults()
        self.assertEqual(geturl._opts["insecure"], list())

        geturl.insecure = True
        geturl._set_defaults()
        self.assertEqual(geturl._opts["insecure"], ["-k"])

        mock_msg.DBG = 0
        mock_msg.level = 1
        geturl._set_defaults()
        # self.assertEqual(geturl._opts["verbose"], "-v")
        self.assertEqual(geturl._files["url"], "")

    # def test_05__mkcurlcmd(self):
    #     """Test05 GetURLexeCurl()._mkcurlcmd()."""
    #     pass

    @mock.patch('udocker.GetURLexeCurl._select_implementation')
    def test_06_get(self, mock_sel):
        """Test06 GetURLexeCurl().get() generic get."""
        self._init()
        geturl = udocker.GetURLexeCurl()
        geturl._geturl = type('test', (object,), {})()
        geturl.get = self._get
        self.assertEqual(geturl.get("http://host"), "http://host")


class DockerIoAPITestCase(unittest.TestCase):
    """Test DockerIoAPITest().

    Class to encapsulate the access to the Docker Hub service.
    Allows to search and download images from Docker Hub.
    """

    @classmethod
    def setUpClass(cls):
        """Setup test."""
        set_env()

    def _init(self):
        """Configure variables."""
        udocker.Config = mock.MagicMock()
        # udocker.Config.http_proxy

    @mock.patch('udocker.GetURL')
    @mock.patch('udocker.LocalRepository')
    def test_01_init(self, mock_local, mock_geturl):
        """Test01 DockerIoAPI()."""
        self._init()
        mock_geturl.return_value = None
        uia = udocker.DockerIoAPI(mock_local)
        self.assertEqual(uia.index_url, udocker.Config.dockerio_index_url)
        self.assertEqual(uia.registry_url,
                         udocker.Config.dockerio_registry_url)
        self.assertEqual(uia.v1_auth_header, "")
        self.assertEqual(uia.v2_auth_header, "")
        self.assertEqual(uia.v2_auth_token, "")
        self.assertEqual(uia.localrepo, mock_local)
        self.assertTrue(uia.search_pause)
        self.assertEqual(uia.search_page, 0)
        self.assertFalse(uia.search_ended)
        self.assertTrue(mock_geturl.called)

    @mock.patch('udocker.GetURL')
    @mock.patch('udocker.LocalRepository')
    def test_02_set_proxy(self, mock_local, mock_geturl):
        """Test02 DockerIoAPI().set_proxy()."""
        self._init()
        uia = udocker.DockerIoAPI(mock_local)
        url = "socks5://user:pass@host:port"
        uia.set_proxy(url)
        self.assertTrue(mock_geturl.return_value.set_proxy.called_with(url))

    @mock.patch('udocker.GetURL')
    @mock.patch('udocker.LocalRepository')
    def test_03_set_registry(self, mock_local, mock_geturl):
        """Test03 DockerIoAPI().set_registry()."""
        self._init()
        uia = udocker.DockerIoAPI(mock_local)
        uia.set_registry("https://registry-1.docker.io")
        self.assertEqual(uia.registry_url, "https://registry-1.docker.io")

    @mock.patch('udocker.GetURL')
    @mock.patch('udocker.LocalRepository')
    def test_04_set_index(self, mock_local, mock_geturl):
        """Test04 DockerIoAPI().set_index()."""
        self._init()
        uia = udocker.DockerIoAPI(mock_local)
        uia.set_index("https://index.docker.io/v1")
        self.assertEqual(uia.index_url, "https://index.docker.io/v1")

    @mock.patch('udocker.GetURL')
    @mock.patch('udocker.Msg')
    @mock.patch('udocker.LocalRepository')
    def test_05_is_repo_name(self, mock_local, mock_msg, mock_geturl):
        """Test05 DockerIoAPI().is_repo_name()."""
        self._init()
        mock_msg.level = 0
        uia = udocker.DockerIoAPI(mock_local)
        self.assertFalse(uia.is_repo_name(""))
        self.assertFalse(uia.is_repo_name("socks5://user:pass@host:port"))
        self.assertFalse(uia.is_repo_name("/:"))
        self.assertTrue(uia.is_repo_name("1233/fasdfasdf:sdfasfd"))
        self.assertTrue(uia.is_repo_name("os-cli-centos7"))
        self.assertTrue(uia.is_repo_name("os-cli-centos7:latest"))
        self.assertTrue(uia.is_repo_name("lipcomputing/os-cli-centos7"))
        self.assertTrue(uia.is_repo_name("lipcomputing/os-cli-centos7:latest"))

    # @mock.patch('udocker.DockerIoAPI._get_url')
    # @mock.patch('udocker.GetURL')
    # @mock.patch('udocker.CurlHeader')
    # @mock.patch('udocker.Msg')
    # @mock.patch('udocker.LocalRepository')
    # def test_07__get_url(self, mock_local, mock_msg, mock_hdr,
    #                      mock_geturl, mock_dgu):
    #     """Test07 DockerIoAPI()._get_url()."""
    #     self._init()
    #     mock_dgu.return_value = (mock_hdr, [])
    #     doia = udocker.DockerIoAPI(mock_local)

    # @mock.patch('udocker.DockerIoAPI._get_url')
    # @mock.patch('udocker.GetURL')
    # @mock.patch('udocker.CurlHeader')
    # @mock.patch('udocker.Msg')
    # @mock.patch('udocker.LocalRepository')
    # def test_08__get_file(self, mock_local, mock_msg, mock_hdr,
    #                       mock_geturl, mock_dgu):
    #     """Test08 DockerIoAPI()._get_file()."""
    #     self._init()
    #     mock_dgu.return_value = (mock_hdr, [])
    #     doia = udocker.DockerIoAPI(mock_local)

    # def test_09__split_fields(self):
    #     """Test09 DockerIoAPI()._split_fields()."""
    #     pass

    # def test_10_is_v1(self):
    #     """Test10 DockerIoAPI().is_v1()."""
    #     pass

    # def test_11_has_search_v1(self):
    #     """Test11 DockerIoAPI().has_search_v1()."""
    #     pass

    @mock.patch('udocker.GetURL')
    @mock.patch('udocker.CurlHeader')
    @mock.patch('udocker.DockerIoAPI._get_url')
    @mock.patch('udocker.LocalRepository')
    def test_12_get_v1_repo(self, mock_local, mock_dgu, mock_hdr, mock_geturl):
        """Test12 DockerIoAPI().get_v1_repo()."""
        self._init()
        mock_dgu.return_value = (mock_hdr, [])
        imagerepo = "REPO"
        doia = udocker.DockerIoAPI(mock_local)
        doia.index_url = "docker.io"
        out = doia.get_v1_repo(imagerepo)
        self.assertIsInstance(out, tuple)

    @mock.patch('udocker.GetURL')
    @mock.patch('udocker.Msg')
    @mock.patch('udocker.LocalRepository')
    def test_13__get_v1_auth(self, mock_local, mock_msg, mock_geturl):
        """Test13 DockerIoAPI()._get_v1_auth()."""
        self._init()
        doia = udocker.DockerIoAPI(mock_local)
        doia.v1_auth_header = "Not Empty"

        www_authenticate = ['Other Stuff']
        out = doia._get_v1_auth(www_authenticate)
        self.assertEqual(out, "")

        www_authenticate = ['Token']
        out = doia._get_v1_auth(www_authenticate)
        self.assertEqual(out, "Not Empty")

    @mock.patch('udocker.GetURL')
    @mock.patch('udocker.CurlHeader')
    @mock.patch('udocker.DockerIoAPI._get_url')
    @mock.patch('udocker.LocalRepository')
    def test_14_get_v1_image_tags(self, mock_local, mock_dgu, mock_hdr, mock_geturl):
        """Test14 DockerIoAPI().get_v1_image_tags()."""
        self._init()
        mock_dgu.return_value = (mock_hdr, [])
        endpoint = "docker.io"
        imagerepo = "REPO"
        doia = udocker.DockerIoAPI(mock_local)
        out = doia.get_v1_image_tags(endpoint, imagerepo)
        # self.assertIsInstance(out, tuple)

    @mock.patch('udocker.GetURL')
    @mock.patch('udocker.CurlHeader')
    @mock.patch('udocker.DockerIoAPI._get_url')
    @mock.patch('udocker.LocalRepository')
    def test_15_get_v1_image_tag(self, mock_local, mock_dgu, mock_hdr, mock_geturl):
        """Test15 DockerIoAPI().get_v1_image_tag()."""
        self._init()
        mock_dgu.return_value = (mock_hdr, [])
        endpoint = "docker.io"
        imagerepo = "REPO"
        tag = "TAG"
        doia = udocker.DockerIoAPI(mock_local)
        out = doia.get_v1_image_tag(endpoint, imagerepo, tag)
        self.assertIsInstance(out, tuple)

    @mock.patch('udocker.GetURL')
    @mock.patch('udocker.CurlHeader')
    @mock.patch('udocker.DockerIoAPI._get_url')
    @mock.patch('udocker.LocalRepository')
    def test_16_get_v1_image_ancestry(self, mock_local, mock_dgu, mock_hdr, mock_geturl):
        """Test16 DockerIoAPI().get_v1_image_ancestry()."""
        self._init()
        mock_dgu.return_value = (mock_hdr, [])
        endpoint = "docker.io"
        image_id = "IMAGEID"
        doia = udocker.DockerIoAPI(mock_local)
        out = doia.get_v1_image_ancestry(endpoint, image_id)
        self.assertIsInstance(out, tuple)

    @mock.patch('udocker.GetURL')
    @mock.patch('udocker.DockerIoAPI._get_file')
    @mock.patch('udocker.LocalRepository')
    def test_17_get_v1_image_json(self, mock_local, mock_dgf, mock_geturl):
        """Test17 DockerIoAPI().get_v1_image_json()."""
        self._init()
        mock_dgf.return_value = True
        endpoint = "docker.io"
        layer_id = "LAYERID"
        doia = udocker.DockerIoAPI(mock_local)
        status = doia.get_v1_image_json(endpoint, layer_id)
        self.assertTrue(status)

        mock_dgf.return_value = False
        status = doia.get_v1_image_json(endpoint, layer_id)
        self.assertFalse(status)

    @mock.patch('udocker.GetURL')
    @mock.patch('udocker.DockerIoAPI._get_file')
    @mock.patch('udocker.LocalRepository')
    def test_18_get_v1_image_layer(self, mock_local, mock_dgf, mock_geturl):
        """Test18 DockerIoAPI().get_v1_image_layer()."""
        self._init()
        mock_dgf.return_value = True
        endpoint = "docker.io"
        layer_id = "LAYERID"
        doia = udocker.DockerIoAPI(mock_local)
        status = doia.get_v1_image_layer(endpoint, layer_id)
        self.assertTrue(status)

        mock_dgf.return_value = False
        status = doia.get_v1_image_layer(endpoint, layer_id)
        self.assertFalse(status)

    @mock.patch('udocker.GetURL')
    @mock.patch('udocker.Msg')
    @mock.patch('udocker.DockerIoAPI._get_file')
    @mock.patch('udocker.LocalRepository')
    def test_19_get_v1_layers_all(self, mock_local, mock_dgf, mock_msg, mock_geturl):
        """Test19 DockerIoAPI().get_v1_layers_all()."""
        self._init()
        mock_dgf.return_value = True
        endpoint = "docker.io"
        layer_list = []
        doia = udocker.DockerIoAPI(mock_local)
        out = doia.get_v1_layers_all(endpoint, layer_list)
        self.assertEqual(out, [])

        layer_list = ["a", "b"]
        doia = udocker.DockerIoAPI(mock_local)
        out = doia.get_v1_layers_all(endpoint, layer_list)
        self.assertEqual(out, ['b.json', 'b.layer', 'a.json', 'a.layer'])

    @mock.patch('udocker.DockerIoAPI._get_url')
    @mock.patch('udocker.CurlHeader')
    @mock.patch('udocker.json.loads')
    @mock.patch('udocker.GetURL')
    @mock.patch('udocker.Msg')
    @mock.patch('udocker.LocalRepository')
    def test_20__get_v2_auth(self, mock_local, mock_msg, mock_geturl,
                             mock_jloads, mock_hdr, mock_dgu):
        """Test20 DockerIoAPI()._get_v2_auth()."""
        self._init()
        fakedata = StringIO('token')
        mock_dgu.return_value = (mock_hdr, fakedata)
        mock_jloads.return_value = {'token': 'YYY'}
        doia = udocker.DockerIoAPI(mock_local)
        doia.v2_auth_header = "v2 Auth Header"
        doia.v2_auth_token = "v2 Auth Token"
        www_authenticate = 'Other Stuff'
        out = doia._get_v2_auth(www_authenticate, False)
        self.assertEqual(out, "")

        www_authenticate = "Bearer realm=REALM"
        out = doia._get_v2_auth(www_authenticate, False)
        self.assertEqual(out, "Authorization: Bearer YYY")

        www_authenticate = "BASIC realm=Sonatype Nexus Repository"
        out = doia._get_v2_auth(www_authenticate, False)
        self.assertEqual(out, "Authorization: Basic %s" %doia.v2_auth_token)

    @mock.patch('udocker.GetURL')
    @mock.patch('udocker.LocalRepository')
    def test_21_get_v2_login_token(self, mock_local, mock_geturl):
        """Test21 DockerIoAPI().get_v2_login_token()."""
        self._init()
        doia = udocker.DockerIoAPI(mock_local)
        out = doia.get_v2_login_token("username", "password")
        self.assertIsInstance(out, str)

        out = doia.get_v2_login_token("", "")
        self.assertEqual(out, "")

    @mock.patch('udocker.GetURL')
    @mock.patch('udocker.LocalRepository')
    def test_22_set_v2_login_token(self, mock_local, mock_geturl):
        """Test22 DockerIoAPI().set_v2_login_token()."""
        self._init()
        doia = udocker.DockerIoAPI(mock_local)
        doia.set_v2_login_token("BIG-FAT-TOKEN")
        self.assertEqual(doia.v2_auth_token, "BIG-FAT-TOKEN")

    @mock.patch('udocker.GetURL')
    @mock.patch('udocker.CurlHeader')
    @mock.patch('udocker.DockerIoAPI._get_url')
    @mock.patch('udocker.LocalRepository')
    def test_23_is_v2(self, mock_local, mock_dgu, mock_hdr, mock_geturl):
        """Test23 DockerIoAPI().is_v2()."""
        self._init()
        mock_dgu.return_value = (mock_hdr, [])
        doia = udocker.DockerIoAPI(mock_local)
        doia.registry_url = "http://www.docker.io"
        out = doia.is_v2()
        self.assertFalse(out)

        # needs auth to be working before
        doia.registry_url = "https://registry-1.docker.io"
        out = doia.is_v2()
        # self.assertTrue(out)

    # def test_24_has_search_v2(self):
    #     """Test24 DockerIoAPI().has_search_v2()."""
    #     pass

    @mock.patch('udocker.GetURL')
    @mock.patch('udocker.CurlHeader')
    @mock.patch('udocker.DockerIoAPI._get_url')
    @mock.patch('udocker.LocalRepository')
    def test_25_get_v2_image_manifest(self, mock_local, mock_dgu, mock_hdr, mock_geturl):
        """Test25 DockerIoAPI().get_v2_image_manifest()."""
        self._init()
        imagerepo = "REPO"
        tag = "TAG"
        mock_dgu.return_value = (mock_hdr, [])
        doia = udocker.DockerIoAPI(mock_local)
        doia.registry_url = "https://registry-1.docker.io"
        out = doia.get_v2_image_manifest(imagerepo, tag)
        self.assertIsInstance(out, tuple)

    @mock.patch('udocker.GetURL')
    @mock.patch('udocker.CurlHeader')
    @mock.patch('udocker.DockerIoAPI._get_file')
    @mock.patch('udocker.LocalRepository')
    def test_26_get_v2_image_layer(self, mock_local, mock_dgf, mock_hdr, mock_geturl):
        """Test26 DockerIoAPI().get_v2_image_layer()."""
        self._init()
        imagerepo = "REPO"
        layer_id = "LAYERID"
        doia = udocker.DockerIoAPI(mock_local)
        doia.registry_url = "https://registry-1.docker.io"

        mock_dgf.return_value = True
        out = doia.get_v2_image_layer(imagerepo, layer_id)
        self.assertTrue(out)

        mock_dgf.return_value = False
        out = doia.get_v2_image_layer(imagerepo, layer_id)
        self.assertFalse(out)

    @mock.patch('udocker.GetURL')
    @mock.patch('udocker.Msg')
    @mock.patch('udocker.DockerIoAPI.get_v2_image_layer')
    @mock.patch('udocker.LocalRepository')
    def test_27_get_v2_layers_all(self, mock_local, mock_v2img,
                                  mock_msg, mock_geturl):
        """Test27 DockerIoAPI().get_v2_layers_all()."""
        self._init()
        mock_v2img.return_value = False
        imagerepo = "docker.io"
        fslayers = []
        doia = udocker.DockerIoAPI(mock_local)
        out = doia.get_v2_layers_all(imagerepo, fslayers)
        self.assertEqual(out, [])

        # mock_v2img.return_value = True
        # imagerepo = "docker.io"
        # fslayers = ["a", "b"]
        # doia = udocker.DockerIoAPI(mock_local)
        # out = doia.get_v2_layers_all(imagerepo, fslayers)
        # self.assertEqual(out, ['b.json', 'b.layer', 'a.json', 'a.layer'])

    @mock.patch('udocker.GetURL')
    @mock.patch('udocker.CurlHeader')
    @mock.patch('udocker.Msg')
    @mock.patch('udocker.DockerIoAPI.get_v2_layers_all')
    @mock.patch('udocker.DockerIoAPI._get_url')
    @mock.patch('udocker.LocalRepository')
    def test_28_get_v2(self, mock_local, mock_dgu, mock_dgv2,
                       mock_msg, mock_hdr, mock_geturl):
        """Test28 DockerIoAPI().get_v2()."""
        self._init()
        mock_dgv2.return_value = []
        mock_dgu.return_value = (mock_hdr, [])
        imagerepo = "REPO"
        tag = "TAG"
        doia = udocker.DockerIoAPI(mock_local)
        doia.registry_url = "https://registry-1.docker.io"
        out = doia.get_v2(imagerepo, tag)
        self.assertEqual(out, [])

        # mock_dgv2.return_value = ["a", "b"]
        # out = doia.get_v2(imagerepo, tag)
        # self.assertEqual(out, [])

    # Test as well the private methods
    # _get_v1_id_from_tags _get_v1_id_from_images
    @mock.patch('udocker.GetURL')
    @mock.patch('udocker.CurlHeader')
    @mock.patch('udocker.Msg')
    @mock.patch('udocker.DockerIoAPI.get_v1_layers_all')
    @mock.patch('udocker.DockerIoAPI._get_url')
    @mock.patch('udocker.LocalRepository')
    def test_29_get_v1(self, mock_local, mock_dgu, mock_dgv1,
                       mock_msg, mock_hdr, mock_geturl):
        """Test29 DockerIoAPI().get_v1()."""
        self._init()
        mock_dgv1.return_value = []
        mock_dgu.return_value = (mock_hdr, [])
        imagerepo = "REPO"
        tag = "TAG"
        doia = udocker.DockerIoAPI(mock_local)
        doia.registry_url = "https://registry-1.docker.io"
        out = doia.get_v1(imagerepo, tag)
        self.assertEqual(out, [])

        # mock_dgv1.return_value = ["a", "b"]
        # out = doia.get_v1(imagerepo, tag)
        # self.assertEqual(out, [])

    # Test as well the private methods
    # _parse_imagerepo
    @mock.patch('udocker.DockerIoAPI._get_url')
    @mock.patch('udocker.GetURL')
    @mock.patch('udocker.CurlHeader')
    @mock.patch('udocker.Msg')
    @mock.patch('udocker.DockerIoAPI._parse_imagerepo')
    @mock.patch('udocker.LocalRepository')
    @mock.patch('udocker.LocalRepository.cd_imagerepo')
    def test_30_get(self, mock_cdir, mock_local, mock_parse,
                    mock_msg, mock_hdr, mock_geturl, mock_dgu):
        """Test30 DockerIoAPI().get()."""
        self._init()
        # mock_cdir.return_value = False
        # mock_parse.return_value = ()
        # mock_dgu.return_value = (mock_hdr, [])
        #
        # imagerepo = "REPO"
        # tag = "TAG"
        # doia = udocker.DockerIoAPI(mock_local)
        # doia.registry_url = "https://registry-1.docker.io"
        # out = doia.get(imagerepo, tag)
        # self.assertEqual(out, [])

    @mock.patch('udocker.GetURL')
    @mock.patch('udocker.LocalRepository')
    def test_31_search_init(self, mock_local, mock_geturl):
        """Test31 DockerIoAPI().search_init()."""
        self._init()
        doia = udocker.DockerIoAPI(mock_local)
        doia.search_init("PAUSE")
        self.assertEqual(doia.search_pause, "PAUSE")
        self.assertEqual(doia.search_page, 0)
        # self.assertEqual(doia.search_link, "")
        self.assertEqual(doia.search_ended, False)

    @mock.patch('udocker.DockerIoAPI._get_url')
    @mock.patch('udocker.GetURL')
    @mock.patch('udocker.CurlHeader')
    @mock.patch('udocker.Msg')
    @mock.patch('udocker.LocalRepository')
    def test_32_search_get_page_v1(self, mock_local, mock_msg, mock_hdr,
                                   mock_geturl, mock_dgu):
        """Test32 DockerIoAPI().search_get_page_v1()."""
        self._init()
        mock_dgu.return_value = (mock_hdr, [])

        doia = udocker.DockerIoAPI(mock_local)
        doia.set_index("index.docker.io")
        # out = doia.search_get_page_v1("SOMETHING")
        # self.assertEqual(out, [])

    # def test_33_search_get_page_v2(self):
    #     """Test33 DockerIoAPI().search_get_page_v2()."""
    #     pass

    @mock.patch('udocker.DockerIoAPI._get_url')
    @mock.patch('udocker.GetURL')
    @mock.patch('udocker.CurlHeader')
    @mock.patch('udocker.Msg')
    @mock.patch('udocker.LocalRepository')
    def test_34_search_get_page(self, mock_local, mock_msg, mock_hdr,
                                mock_geturl, mock_dgu):
        """Test34 DockerIoAPI().search_get_page()."""
        self._init()
        mock_dgu.return_value = (mock_hdr, [])
        doia = udocker.DockerIoAPI(mock_local)
        doia.set_index("index.docker.io")
        out = doia.search_get_page("SOMETHING")
        self.assertEqual(out, [])


##
## CommonLocalFileApiTestCase(unittest.TestCase)
##


class DockerLocalFileAPITestCase(unittest.TestCase):
    """Test DockerLocalFileAPI() manipulate Docker images."""

    @classmethod
    def setUpClass(cls):
        """Setup test."""
        set_env()

    def _init(self):
        """Configure variables."""
        udocker.Config = mock.MagicMock()
        udocker.Config.hostauth_list = ("/etc/passwd", "/etc/group")
        udocker.Config.cmd = "/bin/bash"
        udocker.Config.cpu_affinity_exec_tools = \
            (["numactl", "-C", "%s", "--", ], ["taskset", "-c", "%s", ])
        udocker.Config.valid_host_env = "HOME"
        udocker.Config.return_value.username.return_value = "user"
        udocker.Config.return_value.userhome.return_value = "/"
        udocker.Config.return_value.oskernel.return_value = "4.8.13"
        udocker.Config.location = ""
        udocker.Config.keystore = "KEYSTORE"
        udocker.Config.return_value.osversion.return_value = "OSVERSION"
        udocker.Config.return_value.arch.return_value = "ARCH"

    @mock.patch('udocker.LocalRepository')
    def test_01_init(self, mock_local):
        """Test01 DockerLocalFileAPI() constructor."""
        self._init()
        dlocapi = udocker.DockerLocalFileAPI(mock_local)
        self.assertEqual(dlocapi.localrepo, mock_local)

    @mock.patch('udocker.os.listdir')
    @mock.patch('udocker.FileUtil')
    @mock.patch('udocker.LocalRepository')
    def test_02__load_structure(self, mock_local, mock_futil, mock_ldir):
        """Test02 DockerLocalFileAPI()._load_structure()."""
        self._init()
        dlocapi = udocker.DockerLocalFileAPI(mock_local)
        mock_futil.return_value.isdir.return_value = False
        structure = dlocapi._load_structure("/tmp")
        self.assertEqual(structure, {'repolayers': {}, 'repoconfigs': {}})

        dlocapi = udocker.DockerLocalFileAPI(mock_local)
        mock_futil.return_value.isdir.return_value = True
        mock_ldir.return_value = ["repositories", ]
        mock_local.load_json.return_value = {"REPO": "", }
        structure = dlocapi._load_structure("/tmp")
        expected = {'repolayers': {}, 'repoconfigs': {},
                    'repositories': {'REPO': ''}}
        self.assertEqual(structure, expected)

        dlocapi = udocker.DockerLocalFileAPI(mock_local)
        mock_futil.return_value.isdir.return_value = True
        mock_ldir.return_value = ["manifest.json", ]
        structure = dlocapi._load_structure("/tmp")
        expected = {'repolayers': {}, 'repoconfigs': {},
                    'manifest': {'REPO': ''}}
        self.assertEqual(structure, expected)

        # dlocapi = udocker.DockerLocalFileAPI(mock_local)
        # mock_futil.return_value.isdir.return_value = True
        # mock_ldir.return_value = ["x" * 64 + ".json", ]
        # structure = dlocapi._load_structure("/tmp")
        # expected = {'repolayers': {}, 'repoconfigs': {"x" * 64},
        #             'repositories': {'REPO': ''}}
        # self.assertEqual(structure, expected)

        # dlocapi = udocker.DockerLocalFileAPI(mock_local)
        # mock_futil.return_value.isdir.return_value = True
        # mock_ldir.side_effect = [["x" * 64, ], ["VERSION", ], ]
        # mock_local.load_json.return_value = {"X": "", }
        # structure = dlocapi._load_structure("/tmp")
        # expected = {'layers': {"x" * 64: {'VERSION': {'X': ''}}}}
        # self.assertEqual(structure, expected)

        # dlocapi = udocker.DockerLocalFileAPI(mock_local)
        # mock_futil.return_value.isdir.return_value = True
        # mock_ldir.side_effect = [["x" * 64, ], ["json", ], ]
        # mock_local.load_json.return_value = {"X": "", }
        # structure = dlocapi._load_structure("/tmp")
        # expected = {'layers': {"x" * 64: {'json': {'X': ''},
        #                                   'json_f': '/tmp/' + "x" * 64 + '/json'}}}
        # self.assertEqual(structure, expected)

        # dlocapi = udocker.DockerLocalFileAPI(mock_local)
        # mock_futil.return_value.isdir.return_value = True
        # mock_ldir.side_effect = [["x" * 64, ], ["layer", ], ]
        # mock_local.load_json.return_value = {"X": "", }
        # structure = dlocapi._load_structure("/tmp")
        # expected = {'layers': {"x" * 64: {
        #     'layer_f': '/tmp/' + "x" * 64 + '/layer'}}}
        # self.assertEqual(structure, expected)

    @mock.patch('udocker.LocalRepository')
    def test_03__find_top_layer_id(self, mock_local):
        """Test03 DockerLocalFileAPI()._find_top_layer_id()."""
        self._init()
        dlocapi = udocker.DockerLocalFileAPI(mock_local)
        structure = {}
        status = dlocapi._find_top_layer_id(structure)
        self.assertFalse(status)

        # dlocapi = udocker.DockerLocalFileAPI(mock_local)
        # structure = {'layers': {"repolayers": {"json": {}, }, }, }
        # status = dlocapi._find_top_layer_id(structure)
        # self.assertEqual(status, "repolayers")

        # dlocapi = udocker.DockerLocalFileAPI(mock_local)
        # structure = {'layers': {"repolayers": {"json": {"parent": "x", }, }, }, }
        # status = dlocapi._find_top_layer_id(structure)
        # self.assertEqual(status, "repolayers")

    @mock.patch('udocker.LocalRepository')
    def test_04__sorted_layers(self, mock_local):
        """Test04 DockerLocalFileAPI()._sorted_layers()."""
        self._init()
        dlocapi = udocker.DockerLocalFileAPI(mock_local)
        structure = {}
        status = dlocapi._sorted_layers(structure, "")
        self.assertFalse(status)

        # dlocapi = udocker.DockerLocalFileAPI(mock_local)
        # structure = {'layers': {"repolayers": {"json": {"parent": {}, }, }, }, }
        # status = dlocapi._sorted_layers(structure, "repolayers")
        # self.assertEqual(status, ["repolayers"])

    # @mock.patch('udocker.os.rename')
    # @mock.patch('udocker.LocalRepository')
    # def test_05__copy_layer_to_repo(self, mock_local, mock_rename):
    #     """Test05 DockerLocalFileAPI()._copy_layer_to_repo()."""
    #     self._init()
    #     mock_local.layersdir = ""
    #     dlocapi = udocker.DockerLocalFileAPI(mock_local)
    #     status = dlocapi._copy_layer_to_repo("/", "repolayers")
    #     self.assertFalse(status)

    #     dlocapi = udocker.DockerLocalFileAPI(mock_local)
    #     status = dlocapi._copy_layer_to_repo("/xxx.json", "repolayers")
    #     self.assertTrue(status)

    # @mock.patch('udocker.DockerLocalFileAPI._copy_layer_to_repo')
    # @mock.patch('udocker.DockerLocalFileAPI._sorted_layers')
    # @mock.patch('udocker.DockerLocalFileAPI._find_top_layer_id')
    # @mock.patch('udocker.Msg')
    # @mock.patch('udocker.LocalRepository')
    # def test_06__load_image(self, mock_local, mock_msg, mock_findtop,
    #                         mock_slayers, mock_copylayer):
    #     """Test06 DockerLocalFileAPI()._load_image()."""
    #     self._init()
    #     mock_msg.level = 0
    #     dlocapi = udocker.DockerLocalFileAPI(mock_local)
    #     mock_local.cd_imagerepo.return_value = True
    #     structure = {}
    #     status = dlocapi._load_image(structure, "IMAGE", "TAG")
    #     self.assertFalse(status)

    #     dlocapi = udocker.DockerLocalFileAPI(mock_local)
    #     mock_local.cd_imagerepo.return_value = False
    #     mock_local.setup_tag.return_value = ""
    #     structure = {}
    #     status = dlocapi._load_image(structure, "IMAGE", "TAG")
    #     self.assertFalse(status)

    #     dlocapi = udocker.DockerLocalFileAPI(mock_local)
    #     mock_local.cd_imagerepo.return_value = False
    #     mock_local.setup_tag.return_value = "/dir"
    #     mock_local.set_version.return_value = False
    #     structure = {}
    #     status = dlocapi._load_image(structure, "IMAGE", "TAG")
    #     self.assertFalse(status)

    #     dlocapi = udocker.DockerLocalFileAPI(mock_local)
    #     mock_local.cd_imagerepo.return_value = False
    #     mock_local.setup_tag.return_value = "/dir"
    #     mock_local.set_version.return_value = True
    #     mock_findtop.return_value = "TLID"
    #     mock_slayers.return_value = []
    #     structure = {}
    #     status = dlocapi._load_image(structure, "IMAGE", "TAG")
    #     self.assertEqual(status, ['IMAGE:TAG'])

        # dlocapi = udocker.DockerLocalFileAPI(mock_local)
        # mock_local.cd_imagerepo.return_value = False
        # mock_local.setup_tag.return_value = "/dir"
        # mock_local.set_version.return_value = True
        # mock_findtop.return_value = "TLID"
        # mock_slayers.return_value = ["LID", ]
        # mock_copylayer.return_value = False
        # structure = {'layers': {'LID': {'VERSION': "1.0",
        #                                 'json_f': "f1",
        #                                 'layer_f': "f1", }, }, }
        # status = dlocapi._load_image(structure, "IMAGE", "TAG")
        # self.assertFalse(status)

        # dlocapi = udocker.DockerLocalFileAPI(mock_local)
        # mock_local.cd_imagerepo.return_value = False
        # mock_local.setup_tag.return_value = "/dir"
        # mock_local.set_version.return_value = True
        # mock_findtop.return_value = "TLID"
        # mock_slayers.return_value = ["repolayers", ]
        # mock_copylayer.return_value = True
        # structure = {'layers': {'repolayers': {'VERSION': "1.0",
        #                                        'json_f': "f1",
        #                                        'layer_f': "f1", }, }, }
        # status = dlocapi._load_image(structure, "IMAGE", "TAG")
        # self.assertEqual(status, ['IMAGE:TAG'])

    # @mock.patch('udocker.DockerLocalFileAPI._load_image')
    # @mock.patch('udocker.Msg')
    # @mock.patch('udocker.LocalRepository')
    # def test_07__load_repositories(self, mock_local, mock_msg, mock_loadi):
    #     """Test07 DockerLocalFileAPI()._load_repositories()."""
    #     self._init()
    #     mock_msg.level = 0
    #     dlocapi = udocker.DockerLocalFileAPI(mock_local)
    #     structure = {}
    #     status = dlocapi._load_repositories(structure)
    #     self.assertFalse(status)

    #     dlocapi = udocker.DockerLocalFileAPI(mock_local)
    #     structure = {'repositories': {'IMAGE': {'TAG': "tag", }, }, }
    #     mock_loadi.return_value = False
    #     status = dlocapi._load_repositories(structure)
    #     self.assertFalse(status)

    #     dlocapi = udocker.DockerLocalFileAPI(mock_local)
    #     structure = {'repositories': {'IMAGE': {'TAG': "tag", }, }, }
    #     mock_loadi.return_value = True
    #     status = dlocapi._load_repositories(structure)
    #     self.assertTrue(status)

    @mock.patch('udocker.Uprocess.call')
    @mock.patch('udocker.Msg')
    @mock.patch('udocker.LocalRepository')
    def test_08__untar_saved_container(self, mock_local, mock_msg, mock_call):
        """Test08 DockerLocalFileAPI()._untar_saved_container()."""
        self._init()
        mock_msg.level = 0
        mock_call.return_value = True
        dlocapi = udocker.DockerLocalFileAPI(mock_local)
        status = dlocapi._untar_saved_container("TARFILE", "DESTDIR")
        self.assertFalse(status)

        mock_call.return_value = False
        dlocapi = udocker.DockerLocalFileAPI(mock_local)
        status = dlocapi._untar_saved_container("TARFILE", "DESTDIR")
        self.assertTrue(mock_call.called)
        self.assertTrue(status)

    @mock.patch('udocker.DockerLocalFileAPI._load_repositories')
    @mock.patch('udocker.DockerLocalFileAPI._load_structure')
    @mock.patch('udocker.DockerLocalFileAPI._untar_saved_container')
    @mock.patch('udocker.os.makedirs')
    @mock.patch('udocker.FileUtil')
    @mock.patch('udocker.os.path.exists')
    @mock.patch('udocker.Msg')
    @mock.patch('udocker.LocalRepository')
    def test_09_load(self, mock_local, mock_msg, mock_exists, mock_futil,
                     mock_makedirs, mock_untar, mock_lstruct, mock_lrepo):
        """Test09 DockerLocalFileAPI().load()."""
        self._init()
        mock_msg.level = 0
        dlocapi = udocker.DockerLocalFileAPI(mock_local)
        mock_exists.return_value = False
        mock_futil.return_value.mktmp.return_value = "tmpfile"
        status = dlocapi.load("IMAGEFILE")
        self.assertFalse(status)

        dlocapi = udocker.DockerLocalFileAPI(mock_local)
        mock_exists.return_value = True
        mock_futil.return_value.mktmp.return_value = "tmpfile"
        mock_untar.return_value = False
        status = dlocapi.load("IMAGEFILE")
        self.assertFalse(status)

        dlocapi = udocker.DockerLocalFileAPI(mock_local)
        mock_exists.return_value = True
        mock_futil.return_value.mktmp.return_value = "tmpfile"
        mock_untar.return_value = True
        structure = {}
        mock_lstruct.return_value = structure
        status = dlocapi.load("IMAGEFILE")
        self.assertFalse(status)

        dlocapi = udocker.DockerLocalFileAPI(mock_local)
        mock_exists.return_value = True
        mock_futil.return_value.mktmp.return_value = "tmpfile"
        mock_untar.return_value = True
        structure = {'repositories': {'IMAGE': {'TAG': "tag", }, }, }
        mock_lstruct.return_value = structure
        mock_lrepo.return_value = ["R1", "R2", ]
        status = dlocapi.load("IMAGEFILE")
        self.assertEqual(status, ["R1", "R2", ])

    # @mock.patch('udocker.time.strftime')
    # @mock.patch('udocker.FileUtil')
    # @mock.patch('udocker.Msg')
    # @mock.patch('udocker.LocalRepository')
    # def test_10_create_container_meta(self, mock_local, mock_msg, mock_futil,
    #                                   mock_stime):
    #     """Test10 DockerLocalFileAPI().create_container_meta()."""
    #     self._init()
    #     mock_msg.level = 0
    #     dlocapi = udocker.DockerLocalFileAPI(mock_local)
    #     mock_futil.return_value.size.return_value = 123
    #     mock_stime.return_value = "DATE"
    #     status = dlocapi.create_container_meta("LID")
    #     meta = {'comment': 'created by udocker',
    #             'created': 'DATE',
    #             'config': {'Env': None, 'Hostname': '', 'Entrypoint': None,
    #                        'PortSpecs': None, 'Memory': 0, 'OnBuild': None,
    #                        'OpenStdin': False, 'MacAddress': '', 'Cpuset': '',
    #                        'NetworkDisable': False, 'User': '',
    #                        'AttachStderr': False, 'AttachStdout': False,
    #                        'Cmd': None, 'StdinOnce': False, 'CpusShares': 0,
    #                        'WorkingDir': '', 'AttachStdin': False,
    #                        'Volumes': None, 'MemorySwap': 0, 'Tty': False,
    #                        'Domainname': '', 'Image': '', 'Labels': None,
    #                        'ExposedPorts': None},
    #             'container_config': {'Env': None, 'Hostname': '',
    #                                  'Entrypoint': None, 'PortSpecs': None,
    #                                  'Memory': 0, 'OnBuild': None,
    #                                  'OpenStdin': False, 'MacAddress': '',
    #                                  'Cpuset': '', 'NetworkDisable': False,
    #                                  'User': '', 'AttachStderr': False,
    #                                  'AttachStdout': False, 'Cmd': None,
    #                                  'StdinOnce': False, 'CpusShares': 0,
    #                                  'WorkingDir': '', 'AttachStdin': False,
    #                                  'Volumes': None, 'MemorySwap': 0,
    #                                  'Tty': False, 'Domainname': '',
    #                                  'Image': '', 'Labels': None,
    #                                  'ExposedPorts': None},
    #             'architecture': 'ARCH', 'os': 'OSVERSION',
    #             'id': 'LID', 'size': 123}
    #     self.assertEqual(status, meta)

    @mock.patch('udocker.Unique')
    @mock.patch('udocker.os.rename')
    @mock.patch('udocker.FileUtil')
    @mock.patch('udocker.os.path.exists')
    @mock.patch('udocker.Msg')
    @mock.patch('udocker.LocalRepository')
    def test_11_import_toimage(self, mock_local, mock_msg, mock_exists,
                               mock_futil, mock_rename, mock_unique):
        """Test11 DockerLocalFileAPI().import_toimage()."""
        self._init()
        mock_msg.level = 0
        dlocapi = udocker.DockerLocalFileAPI(mock_local)
        mock_exists.return_value = False
        status = dlocapi.import_toimage("TARFILE", "IMAGE", "TAG")
        self.assertFalse(status)

        dlocapi = udocker.DockerLocalFileAPI(mock_local)
        mock_exists.return_value = True
        mock_local.cd_imagerepo.return_value = "TAGDIR"
        status = dlocapi.import_toimage("TARFILE", "IMAGE", "TAG")
        self.assertFalse(status)

        dlocapi = udocker.DockerLocalFileAPI(mock_local)
        mock_exists.return_value = True
        mock_local.cd_imagerepo.return_value = ""
        mock_local.setup_tag.return_value = ""
        status = dlocapi.import_toimage("TARFILE", "IMAGE", "TAG")
        self.assertFalse(status)

        dlocapi = udocker.DockerLocalFileAPI(mock_local)
        mock_exists.return_value = True
        mock_local.cd_imagerepo.return_value = ""
        mock_local.setup_tag.return_value = "TAGDIR"
        mock_local.set_version.return_value = False
        status = dlocapi.import_toimage("TARFILE", "IMAGE", "TAG")
        self.assertFalse(status)

        dlocapi = udocker.DockerLocalFileAPI(mock_local)
        mock_exists.return_value = True
        mock_local.cd_imagerepo.return_value = ""
        mock_local.setup_tag.return_value = "TAGDIR"
        mock_local.set_version.return_value = True
        mock_unique.return_value.layer_v1.return_value = "LAYERID"
        status = dlocapi.import_toimage("TARFILE", "IMAGE", "TAG")
        self.assertEqual(status, "LAYERID")
        self.assertTrue(mock_rename.called)

        mock_rename.reset_mock()
        dlocapi = udocker.DockerLocalFileAPI(mock_local)
        mock_exists.return_value = True
        mock_local.cd_imagerepo.return_value = ""
        mock_local.setup_tag.return_value = "TAGDIR"
        mock_local.set_version.return_value = True
        mock_unique.return_value.layer_v1.return_value = "LAYERID"
        status = dlocapi.import_toimage("TARFILE", "IMAGE", "TAG", False)
        self.assertEqual(status, "LAYERID")
        self.assertFalse(mock_rename.called)

    # def test_12_import_tocontainer(self):
    #     """Test12 DockerLocalFileAPI().import_tocontainer()."""
    #     pass

    # def test_13_import_clone(self):
    #     """Test13 DockerLocalFileAPI().import_clone()."""
    #     pass

    # def test_14_clone_container(self):
    #     """Test14 DockerLocalFileAPI().clone_container()."""
    #     pass


##
## OciLocalFileAPITestCase
##


##
## LocalFileAPITestCase
##


class UdockerTestCase(unittest.TestCase):
    """Test UdockerTestCase() command line interface."""

    def _init(self):
        """Configure variables."""
        udocker.Config = mock.MagicMock()
        udocker.Config.hostauth_list = ("/etc/passwd", "/etc/group")
        udocker.Config.cmd = "/bin/bash"
        udocker.Config.cpu_affinity_exec_tools = \
            (["numactl", "-C", "%s", "--", ], ["taskset", "-c", "%s", ])
        udocker.Config.valid_host_env = "HOME"
        udocker.Config.return_value.username.return_value = "user"
        udocker.Config.return_value.userhome.return_value = "/"
        udocker.Config.return_value.oskernel.return_value = "4.8.13"
        udocker.Config.location = ""
        udocker.Config.keystore = "KEYSTORE"

    @classmethod
    def setUpClass(cls):
        """Setup test."""
        set_env()

    @mock.patch('udocker.KeyStore')
    @mock.patch('udocker.LocalFileAPI')
    @mock.patch('udocker.DockerIoAPI')
    @mock.patch('udocker.LocalRepository')
    def test_01_init(self, mock_local, mock_dioapi, mock_locapi, mock_ks):
        """Test01 Udocker() constructor."""
        self._init()
        mock_local.homedir = "/h/u/.udocker"
        mock_ks.return_value = 123
        mock_dioapi.return_value = 456
        mock_locapi.return_value = 789

        udoc = udocker.Udocker(mock_local)
        self.assertEqual(udoc.keystore, 123)
        self.assertEqual(udoc.dockerioapi, 456)
        self.assertEqual(udoc.dockerlocalfileapi, 789)

    @mock.patch('udocker.FileUtil')
    @mock.patch('udocker.CmdParser')
    @mock.patch('udocker.KeyStore')
    @mock.patch('udocker.DockerLocalFileAPI')
    @mock.patch('udocker.DockerIoAPI')
    @mock.patch('udocker.LocalRepository')
    def test_02__cdrepo(self, mock_local, mock_dioapi, mock_dlocapi, mock_ks,
                        mock_cmdp, mock_futil):
        """Test02 Udocker()._cdrepo()."""
        self._init()
        mock_local.homedir = "/h/u/.udocker"
        mock_ks.return_value = 123
        mock_dioapi.return_value = 456
        mock_dlocapi.return_value = 789
        mock_cmdp.get.return_value = "/u/containers/AAAA"
        mock_cmdp.missing_options.return_value = True
        udoc = udocker.Udocker(mock_local)
        status = udoc._cdrepo(mock_cmdp)
        self.assertFalse(status)

        mock_cmdp.get.return_value = "/u/containers/AAAA"
        mock_cmdp.missing_options.return_value = False
        mock_futil.return_value.isdir.return_value = False
        udoc = udocker.Udocker(mock_local)
        status = udoc._cdrepo(mock_cmdp)
        self.assertFalse(status)

        mock_cmdp.get.return_value = "/u/containers/AAAA"
        mock_cmdp.missing_options.return_value = False
        mock_futil.return_value.isdir.return_value = True
        udoc = udocker.Udocker(mock_local)
        status = udoc._cdrepo(mock_cmdp)
        self.assertTrue(status)

    @mock.patch('udocker.CmdParser')
    @mock.patch('udocker.KeyStore')
    @mock.patch('udocker.DockerLocalFileAPI')
    @mock.patch('udocker.DockerIoAPI')
    @mock.patch('udocker.Msg')
    @mock.patch('udocker.LocalRepository')
    def test_03__check_imagespec(self, mock_local, mock_msg, mock_dioapi,
                                 mock_dlocapi, mock_ks, mock_cmdp):
        """Test03 Udocker()._check_imagespec()."""
        self._init()
        mock_msg.level = 0
        mock_dioapi.is_repo_name = False
        udoc = udocker.Udocker(mock_local)
        status = udoc._check_imagespec("")
        self.assertEqual(status, (None, None))

        mock_dioapi.is_repo_name = False
        udoc = udocker.Udocker(mock_local)
        status = udoc._check_imagespec("AAA")
        self.assertEqual(status, ("AAA", "latest"))

        mock_dioapi.is_repo_name = False
        udoc = udocker.Udocker(mock_local)
        status = udoc._check_imagespec("AAA:45")
        self.assertEqual(status, ("AAA", "45"))

    @mock.patch('udocker.os.path.exists')
    @mock.patch('udocker.CmdParser')
    @mock.patch('udocker.KeyStore')
    @mock.patch('udocker.DockerLocalFileAPI')
    @mock.patch('udocker.DockerIoAPI')
    @mock.patch('udocker.Msg')
    @mock.patch('udocker.LocalRepository')
    def test_04_do_mkrepo(self, mock_local, mock_msg, mock_dioapi,
                          mock_dlocapi, mock_ks, mock_cmdp, mock_exists):
        """Test04 Udocker().do_mkrepo()."""
        self._init()
        mock_msg.level = 0
        mock_cmdp.get.return_value = "/"
        mock_exists.return_value = True
        mock_dlocapi.create_repo.return_value = True
        udoc = udocker.Udocker(mock_local)
        status = udoc.do_mkrepo(mock_cmdp)
        self.assertFalse(status)

        mock_cmdp.get.return_value = ""
        mock_exists.return_value = True
        mock_dlocapi.create_repo.return_value = True
        udoc = udocker.Udocker(mock_local)
        status = udoc.do_mkrepo(mock_cmdp)
        # self.assertTrue(status)

        mock_cmdp.get.return_value = "/"
        mock_exists.return_value = True
        mock_dlocapi.create_repo.return_value = False
        udoc = udocker.Udocker(mock_local)
        status = udoc.do_mkrepo(mock_cmdp)
        self.assertFalse(status)

    # @mock.patch('udocker.raw_input')
    # @mock.patch('udocker.CmdParser')
    # @mock.patch('udocker.KeyStore')
    # @mock.patch('udocker.DockerLocalFileAPI')
    # @mock.patch('udocker.DockerIoAPI')
    # @mock.patch('udocker.DockerIoAPI.search_get_page')
    # @mock.patch('udocker.Msg')
    # @mock.patch('udocker.LocalRepository')
    # def test_05_do_search(self, mock_local, mock_msg, mock_diosearch,
    #                       mock_dio, mock_dlocapi, mock_ks,
    #                       mock_cmdp, mock_rinput):
    #     """Test05 Udocker().do_search()."""
    #     self._init()
    #     mock_msg.level = 0
    #     mock_cmdp.get.side_effect = ["", "", "" "", "", ]
    #     mock_cmdp.missing_options.return_value = True
    #     udoc = udocker.Udocker(mock_local)
    #     status = udoc.do_search(mock_cmdp)
    #     self.assertFalse(status)

        # mock_cmdp.get.side_effect = ["", "", "" "", "", ]
        # mock_cmdp.missing_options.return_value = False
        # mock_diosearch.return_value = None
        # udoc = udocker.Udocker(mock_local)
        # status = udoc.do_search(mock_cmdp)
        # self.assertTrue(status)

        # mock_cmdp.get.side_effect = ["", "", "" "", "", ]
        # mock_cmdp.missing_options.return_value = False
        # mock_diosearch.side_effect = (
        #     [["results", ], ["repositories", ], [], ])
        # udoc = udocker.Udocker(mock_local)
        # status = udoc.do_search(mock_cmdp)
        # self.assertTrue(status)

        # mock_cmdp.get.side_effect = ["", "", "" "", "", ]
        # mock_cmdp.missing_options.return_value = False
        # mock_diosearch.side_effect = (
        #     [["zzz", ], ["repositories", ], [], ])
        # udoc = udocker.Udocker(mock_local)
        # status = udoc.do_search(mock_cmdp)
        # self.assertTrue(status)

        # mock_cmdp.get.side_effect = ["", "", "" "", "", ]
        # mock_cmdp.missing_options.return_value = False
        # mock_rinput.return_value = "q"
        # mock_dio.return_value.search_end = False
        # mock_diosearch.side_effect = (
        #     [["zzz", ], ["repositories", ], [], ])
        # udoc = udocker.Udocker(mock_local)
        # status = udoc.do_search(mock_cmdp)
        # self.assertTrue(status)

    @mock.patch('udocker.CmdParser')
    @mock.patch('udocker.KeyStore')
    @mock.patch('udocker.DockerLocalFileAPI')
    @mock.patch('udocker.DockerIoAPI')
    @mock.patch('udocker.Msg')
    @mock.patch('udocker.LocalRepository')
    def test_06_do_load(self, mock_local, mock_msg, mock_dioapi,
                        mock_dlocapi, mock_ks, mock_cmdp):
        """Test06 Udocker().do_load()."""
        self._init()
        mock_msg.level = 0
        udoc = udocker.Udocker(mock_local)
        mock_cmdp.get.side_effect = ["", "", "" "", "", ]
        mock_cmdp.missing_options.return_value = True
        status = udoc.do_load(mock_cmdp)
        self.assertFalse(status)

        # udoc = udocker.Udocker(mock_local)
        # mock_cmdp.get.side_effect = ["", "", "" "", "", ]
        # mock_cmdp.missing_options.return_value = False
        # status = udoc.do_load(mock_cmdp)
        # self.assertTrue(status)

        # udoc = udocker.Udocker(mock_local)
        # mock_cmdp.get.side_effect = ["INFILE", "", "" "", "", ]
        # mock_cmdp.missing_options.return_value = False
        # mock_dlocapi.return_value.load.return_value = []
        # status = udoc.do_load(mock_cmdp)
        # self.assertFalse(status)

        # udoc = udocker.Udocker(mock_local)
        # mock_cmdp.get.side_effect = ["INFILE", "", "" "", "", ]
        # mock_cmdp.missing_options.return_value = False
        # mock_dlocapi.return_value.load.return_value = ["REPO", ]
        # status = udoc.do_load(mock_cmdp)
        # self.assertTrue(status)

    @mock.patch('udocker.Udocker._check_imagespec')
    @mock.patch('udocker.CmdParser')
    @mock.patch('udocker.KeyStore')
    @mock.patch('udocker.DockerLocalFileAPI')
    @mock.patch('udocker.DockerIoAPI')
    @mock.patch('udocker.Msg')
    @mock.patch('udocker.LocalRepository')
    def test_07_do_import(self, mock_local, mock_msg, mock_dioapi,
                          mock_dlocapi, mock_ks, mock_cmdp, mock_chkimg):
        """Test07 Udocker().do_import()."""
        self._init()
        mock_msg.level = 0
        cmd_options = [False, False, "", False,
                       "INFILE", "IMAGE", "" "", "", ]
        udoc = udocker.Udocker(mock_local)
        mock_cmdp.get.side_effect = ["", "", "", "", "", "", "", "", "", ]
        status = udoc.do_import(mock_cmdp)
        self.assertFalse(status)

        mock_cmdp.reset_mock()
        udoc = udocker.Udocker(mock_local)
        mock_cmdp.get.side_effect = cmd_options
        mock_chkimg.return_value = ("", "")
        mock_cmdp.missing_options.return_value = False
        status = udoc.do_import(mock_cmdp)
        self.assertFalse(status)

        mock_cmdp.reset_mock()
        udoc = udocker.Udocker(mock_local)
        mock_cmdp.get.side_effect = cmd_options
        mock_chkimg.return_value = ("IMAGE", "")
        mock_cmdp.missing_options.return_value = True
        status = udoc.do_import(mock_cmdp)
        self.assertFalse(status)

        mock_cmdp.reset_mock()
        udoc = udocker.Udocker(mock_local)
        mock_cmdp.get.side_effect = cmd_options
        mock_chkimg.return_value = ("IMAGE", "TAG")
        mock_cmdp.missing_options.return_value = False
        mock_dlocapi.return_value.import_toimage.return_value = False
        status = udoc.do_import(mock_cmdp)
        self.assertFalse(status)

        mock_cmdp.reset_mock()
        udoc = udocker.Udocker(mock_local)
        mock_cmdp.get.side_effect = cmd_options
        mock_chkimg.return_value = ("IMAGE", "TAG")
        mock_cmdp.missing_options.return_value = False
        mock_dlocapi.return_value.import_toimage.return_value = True
        status = udoc.do_import(mock_cmdp)
        # self.assertTrue(status)

    # def test_08_do_export(self):
    #     """Test08 Udocker().do_export()."""
    #     self._init()
    #     mock_msg.level = 0

    # def test_09_do_clone(self):
    #     """Test09 Udocker().do_clone()."""
    #     self._init()
    #     mock_msg.level = 0

    @mock.patch('udocker.getpass')
    @mock.patch('udocker.raw_input')
    @mock.patch('udocker.CmdParser')
    @mock.patch('udocker.KeyStore')
    @mock.patch('udocker.DockerLocalFileAPI')
    @mock.patch('udocker.DockerIoAPI')
    @mock.patch('udocker.Msg')
    @mock.patch('udocker.LocalRepository')
    def test_10_do_login(self, mock_local, mock_msg, mock_dioapi,
                         mock_dlocapi, mock_ks, mock_cmdp,
                         mock_rinput, mock_gpass):
        """Test10 Udocker().do_login()."""
        self._init()
        mock_msg.level = 0
        udoc = udocker.Udocker(mock_local)
        mock_cmdp.get.side_effect = ["user", "pass", "" "", "", ]
        mock_rinput.return_value = "user"
        mock_gpass.return_value = "pass"
        mock_ks.return_value.put.return_value = False
        status = udoc.do_login(mock_cmdp)
        self.assertFalse(status)
        self.assertFalse(mock_rinput.called)
        self.assertFalse(mock_gpass.called)

        mock_rinput.reset_mock()
        mock_gpass.reset_mock()
        udoc = udocker.Udocker(mock_local)
        mock_cmdp.get.side_effect = ["", "", "" "", "", ]
        mock_rinput.return_value = "user"
        mock_gpass.return_value = "pass"
        mock_ks.return_value.put.return_value = False
        status = udoc.do_login(mock_cmdp)
        self.assertFalse(status)
        # self.assertTrue(mock_rinput.called)
        # self.assertTrue(mock_gpass.called)

        udoc = udocker.Udocker(mock_local)
        mock_cmdp.get.side_effect = ["", "", "" "", "", ]
        mock_rinput.return_value = "user"
        mock_gpass.return_value = "pass"
        mock_ks.return_value.put.return_value = True
        status = udoc.do_login(mock_cmdp)
        # self.assertTrue(status)

    @mock.patch('udocker.CmdParser')
    @mock.patch('udocker.KeyStore')
    @mock.patch('udocker.DockerLocalFileAPI')
    @mock.patch('udocker.DockerIoAPI')
    @mock.patch('udocker.Msg')
    @mock.patch('udocker.LocalRepository')
    def test_11_do_logout(self, mock_local, mock_msg, mock_dioapi,
                          mock_dlocapi, mock_ks, mock_cmdp):
        """Test11 Udocker().do_logout()."""
        self._init()
        mock_msg.level = 0
        udoc = udocker.Udocker(mock_local)
        mock_cmdp.get.side_effect = ["", "", "" "", "", ]
        mock_ks.return_value.delete.return_value = False
        status = udoc.do_logout(mock_cmdp)
        self.assertFalse(status)

        udoc = udocker.Udocker(mock_local)
        mock_cmdp.get.side_effect = ["ALL", "", "" "", "", ]
        mock_ks.return_value.delete.return_value = False
        mock_ks.return_value.erase.return_value = True
        status = udoc.do_logout(mock_cmdp)
        # self.assertTrue(status)
        # self.assertTrue(mock_ks.return_value.erase.called)

        udoc = udocker.Udocker(mock_local)
        mock_cmdp.get.side_effect = ["", "", "" "", "", ]
        mock_ks.return_value.delete.return_value = True
        status = udoc.do_logout(mock_cmdp)
        # self.assertTrue(status)
        # self.assertTrue(mock_ks.return_value.delete.called)

    @mock.patch('udocker.Udocker._check_imagespec')
    @mock.patch('udocker.CmdParser')
    @mock.patch('udocker.KeyStore')
    @mock.patch('udocker.DockerLocalFileAPI')
    @mock.patch('udocker.DockerIoAPI')
    @mock.patch('udocker.Msg')
    @mock.patch('udocker.LocalRepository')
    def test_12_do_pull(self, mock_local, mock_msg, mock_dioapi,
                        mock_dlocapi, mock_ks, mock_cmdp, mock_chkimg):
        """Test12 Udocker().do_pull()."""
        self._init()
        mock_msg.level = 0
        udoc = udocker.Udocker(mock_local)
        mock_cmdp.get.side_effect = ["", "", "" "", "", ]
        mock_chkimg.return_value = ("", "TAG")
        status = udoc.do_pull(mock_cmdp)
        self.assertFalse(status)

        udoc = udocker.Udocker(mock_local)
        mock_cmdp.get.side_effect = ["", "", "" "", "", ]
        mock_chkimg.return_value = ("IMAGE", "TAG")
        mock_cmdp.missing_options.return_value = True
        status = udoc.do_pull(mock_cmdp)
        self.assertFalse(status)

        udoc = udocker.Udocker(mock_local)
        mock_cmdp.get.side_effect = ["", "", "" "", "", ]
        mock_chkimg.return_value = ("IMAGE", "TAG")
        mock_cmdp.missing_options.return_value = False
        mock_dioapi.return_value.get.return_value = []
        status = udoc.do_pull(mock_cmdp)
        self.assertFalse(status)

        udoc = udocker.Udocker(mock_local)
        mock_cmdp.get.side_effect = ["", "", "" "", "", ]
        mock_chkimg.return_value = ("IMAGE", "TAG")
        mock_cmdp.missing_options.return_value = False
        mock_dioapi.return_value.get.return_value = ["F1", "F2", ]
        status = udoc.do_pull(mock_cmdp)
        self.assertTrue(status)

    @mock.patch('udocker.Udocker._create')
    @mock.patch('udocker.CmdParser')
    @mock.patch('udocker.KeyStore')
    @mock.patch('udocker.DockerLocalFileAPI')
    @mock.patch('udocker.DockerIoAPI')
    @mock.patch('udocker.Msg')
    @mock.patch('udocker.LocalRepository')
    def test_13_do_create(self, mock_local, mock_msg, mock_dioapi,
                          mock_dlocapi, mock_ks, mock_cmdp, mock_create):
        """Test13 Udocker().do_create()."""
        self._init()
        mock_msg.level = 0
        udoc = udocker.Udocker(mock_local)
        mock_cmdp.missing_options.return_value = True
        mock_cmdp.get.side_effect = ["", "", "" "", "", ]
        mock_create.return_value = ""
        status = udoc.do_create(mock_cmdp)
        self.assertFalse(status)

        udoc = udocker.Udocker(mock_local)
        mock_cmdp.missing_options.return_value = False
        mock_cmdp.get.side_effect = ["", "", "" "", "", ]
        mock_create.return_value = ""
        status = udoc.do_create(mock_cmdp)
        self.assertFalse(status)

        udoc = udocker.Udocker(mock_local)
        mock_cmdp.missing_options.return_value = False
        mock_cmdp.get.side_effect = ["", "", "" "", "", ]
        mock_create.return_value = "CONTAINER_ID"
        status = udoc.do_create(mock_cmdp)
        self.assertTrue(status)

    @mock.patch('udocker.ContainerStructure')
    @mock.patch('udocker.Udocker._check_imagespec')
    @mock.patch('udocker.DockerIoAPI')
    @mock.patch('udocker.Msg')
    @mock.patch('udocker.LocalRepository')
    def test_14__create(self, mock_local, mock_msg, mock_dioapi, mock_chkimg,
                        mock_cstruct):
        """Test14 Udocker()._create()."""
        self._init()
        mock_msg.level = 0
        udoc = udocker.Udocker(mock_local)
        mock_dioapi.return_value.is_repo_name.return_value = False
        status = udoc._create("IMAGE:TAG")
        self.assertFalse(status)

        udoc = udocker.Udocker(mock_local)
        mock_dioapi.return_value.is_repo_name.return_value = True
        mock_chkimg.return_value = ("", "TAG")
        mock_cstruct.return_value.create.return_value = True
        status = udoc._create("IMAGE:TAG")
        self.assertFalse(status)

        udoc = udocker.Udocker(mock_local)
        mock_dioapi.return_value.is_repo_name.return_value = True
        mock_chkimg.return_value = ("IMAGE", "TAG")
        mock_cstruct.return_value.create.return_value = True
        status = udoc._create("IMAGE:TAG")
        self.assertTrue(status)

    # @mock.patch('udocker.CmdParser')
    # @mock.patch('udocker.LocalRepository')
    # def test_15__get_run_options(self, mock_local, mock_cmdp):
    #     """Test15 Udocker()._get_run_options()"""
    #     self._init()
    #     udocker.PRootEngine = mock.MagicMock()
    #     udocker.PRootEngine.opt = dict()
    #     udocker.PRootEngine.opt["vol"] = []
    #     udocker.PRootEngine.opt["env"] = []
    #     mock_cmdp.get.return_value = "VALUE"
    #     udoc = udocker.Udocker(mock_local)
    #     udoc._get_run_options(mock_cmdp, udocker.PRootEngine)
    #     self.assertEqual(udocker.PRootEngine.opt["dns"], "VALUE")

    @mock.patch('udocker.Udocker._get_run_options')
    @mock.patch('udocker.PRootEngine')
    @mock.patch('udocker.CmdParser')
    @mock.patch('udocker.KeyStore')
    @mock.patch('udocker.DockerLocalFileAPI')
    @mock.patch('udocker.DockerIoAPI')
    @mock.patch('udocker.Msg')
    @mock.patch('udocker.LocalRepository')
    @mock.patch('udocker.LocalRepository.del_container')
    @mock.patch('udocker.os.path.realpath')
    def test_16_do_run(self, mock_realpath, mock_del, mock_local,
                       mock_msg, mock_dioapi, mock_dlocapi,
                       mock_ks, mock_cmdp, mock_eng, mock_getopt):
        """Test16 Udocker().do_run()."""
        self._init()
        mock_msg.level = 0
        mock_realpath.return_value = "/tmp"
        mock_cmdp.return_value.missing_options.return_value = True
        mock_cmdp.return_value.get.side_effect = ["", "", "" "", "", ]
        udoc = udocker.Udocker(mock_local)
        status = udoc.do_run(mock_cmdp)
        self.assertFalse(status)

        mock_local.reset_mock()
        mock_cmdp.reset_mock()
        mock_eng.reset_mock()
        mock_cmdp.return_value.missing_options.return_value = False
        mock_cmdp.return_value.get.side_effect = ["", "", "" "", "", ]
        udocker.Config.location = "/"
        mock_eng.return_value.run.return_value = True
        udoc = udocker.Udocker(mock_local)
        status = udoc.do_run(mock_cmdp)
        self.assertFalse(status)

        mock_local.reset_mock()
        mock_cmdp.reset_mock()
        mock_eng.reset_mock()
        mock_cmdp.return_value.missing_options.return_value = False
        mock_cmdp.return_value.get.side_effect = ["", "", "" "", "", ]
        udocker.Config.location = "/"
        mock_eng.return_value.run.return_value = False
        udoc = udocker.Udocker(mock_local)
        status = udoc.do_run(mock_cmdp)
        self.assertFalse(status)

        mock_local.reset_mock()
        mock_cmdp.reset_mock()
        mock_eng.reset_mock()
        mock_del.reset_mock()
        mock_cmdp.return_value.missing_options.return_value = False
        mock_cmdp.return_value.get.side_effect = ["", "", "--rm" "", "", ]
        udocker.Config.location = "/"
        mock_eng.return_value.run.return_value = False
        mock_local.return_value.isprotected_container.return_value = True
        mock_del.return_value = True
        udoc = udocker.Udocker(mock_local)
        status = udoc.do_run(mock_cmdp)
        self.assertFalse(mock_del.called)
        self.assertFalse(status)

        mock_local.reset_mock()
        mock_cmdp.reset_mock()
        mock_eng.reset_mock()
        mock_del.reset_mock()
        mock_cmdp.return_value.missing_options.return_value = False
        mock_cmdp.return_value.get.side_effect = ["", "", "--rm" "", "", ]
        udocker.Config.location = "/"
        mock_eng.return_value.run.return_value = False
        mock_local.return_value.isprotected_container.return_value = False
        mock_del.return_value = True
        udoc = udocker.Udocker(mock_local)
        status = udoc.do_run(mock_cmdp)
        # self.assertTrue(mock_del.called)
        self.assertFalse(status)

        mock_local.reset_mock()
        mock_cmdp.reset_mock()
        mock_eng.reset_mock()
        mock_cmdp.return_value.missing_options.return_value = False
        mock_cmdp.return_value.get.side_effect = ["", "", "" "", "", ]
        udocker.Config.location = ""
        mock_local.return_value.get_container_id.return_value = ""
        mock_eng.return_value.run.return_value = True
        udoc = udocker.Udocker(mock_local)
        status = udoc.do_run(mock_cmdp)
        self.assertFalse(status)

        mock_local.reset_mock()
        mock_cmdp.reset_mock()
        mock_eng.reset_mock()
        mock_cmdp.return_value.missing_options.return_value = False
        mock_cmdp.return_value.get.side_effect = ["", "", "" "", "", ]
        udocker.Config.location = ""
        mock_local.return_value.get_container_id.return_value = "CONTAINER_ID"
        mock_eng.return_value.run.return_value = True
        udoc = udocker.Udocker(mock_local)
        status = udoc.do_run(mock_cmdp)
        # self.assertTrue(status)

        mock_local.reset_mock()
        mock_cmdp.reset_mock()
        mock_eng.reset_mock()
        mock_cmdp.return_value.missing_options.return_value = False
        mock_cmdp.return_value.get.side_effect = ["", "", "" "", "NAME", ]
        udocker.Config.location = ""
        mock_local.return_value.get_container_id.return_value = "CONTAINER_ID"
        mock_eng.return_value.run.return_value = True
        mock_local.return_value.set_container_name.return_value = True
        udoc = udocker.Udocker(mock_local)
        status = udoc.do_run(mock_cmdp)
        # self.assertTrue(status)

        mock_local.reset_mock()
        mock_cmdp.reset_mock()
        mock_eng.reset_mock()
        mock_cmdp.return_value.missing_options.return_value = False
        mock_cmdp.return_value.get.side_effect = ["", "", "" "", "NAME", ]
        udocker.Config.location = ""
        mock_local.return_value.get_container_id.return_value = "CONTAINER_ID"
        mock_eng.return_value.run.return_value = True
        mock_local.return_value.set_container_name.return_value = False
        udoc = udocker.Udocker(mock_local)
        status = udoc.do_run(mock_cmdp)
        self.assertFalse(status)

    @mock.patch('udocker.CmdParser')
    @mock.patch('udocker.KeyStore')
    @mock.patch('udocker.DockerLocalFileAPI')
    @mock.patch('udocker.DockerIoAPI')
    @mock.patch('udocker.Msg')
    @mock.patch('udocker.LocalRepository')
    def test_17_do_images(self, mock_local, mock_msg, mock_dioapi,
                          mock_dlocapi, mock_ks, mock_cmdp):
        """Test17 Udocker().do_images()."""
        self._init()
        mock_msg.level = 0
        udoc = udocker.Udocker(mock_local)
        mock_cmdp.missing_options.return_value = True
        mock_cmdp.get.side_effect = ["", "", "" "", "", ]
        status = udoc.do_images(mock_cmdp)
        self.assertFalse(status)

        udoc = udocker.Udocker(mock_local)
        mock_cmdp.missing_options.return_value = False
        mock_cmdp.get.side_effect = ["", "", "" "", "", ]
        mock_local.get_imagerepos.return_values = []
        status = udoc.do_images(mock_cmdp)
        self.assertTrue(status)

        udoc = udocker.Udocker(mock_local)
        mock_cmdp.missing_options.return_value = False
        mock_cmdp.get.side_effect = ["", "", "" "", "", ]
        mock_local.get_imagerepos.return_value = [("I1", "T1"), ("I2", "T2"), ]
        mock_local.isprotected_imagerepo.return_value = True
        status = udoc.do_images(mock_cmdp)
        self.assertTrue(status)
        self.assertTrue(mock_local.isprotected_imagerepo.called)

        udoc = udocker.Udocker(mock_local)
        mock_cmdp.missing_options.return_value = False
        mock_cmdp.get.side_effect = ["LONG", "", "" "", "", ]
        mock_local.get_imagerepos.return_value = [("I1", "T1"), ("I2", "T2"), ]
        mock_local.isprotected_imagerepo.return_value = True
        mock_local.get_layers.return_value = []
        status = udoc.do_images(mock_cmdp)
        self.assertTrue(status)
        self.assertTrue(mock_local.get_layers.called)

    @mock.patch('udocker.CmdParser')
    @mock.patch('udocker.KeyStore')
    @mock.patch('udocker.DockerLocalFileAPI')
    @mock.patch('udocker.DockerIoAPI')
    @mock.patch('udocker.Msg')
    @mock.patch('udocker.LocalRepository')
    def test_18_do_ps(self, mock_local, mock_msg, mock_dioapi,
                      mock_dlocapi, mock_ks, mock_cmdp):
        """Test18 Udocker().do_ps()."""
        self._init()
        mock_msg.level = 0
        udoc = udocker.Udocker(mock_local)
        mock_cmdp.missing_options.return_value = True
        mock_cmdp.get.side_effect = ["", "", "" "", "", ]
        status = udoc.do_ps(mock_cmdp)
        self.assertFalse(status)

        udoc = udocker.Udocker(mock_local)
        mock_cmdp.missing_options.return_value = False
        mock_cmdp.get.side_effect = ["", "", "" "", "", ]
        mock_local.get_containers_list.return_value = []
        udoc.do_ps(mock_cmdp)
        self.assertTrue(mock_local.get_containers_list.called)

        udoc = udocker.Udocker(mock_local)
        mock_cmdp.missing_options.return_value = False
        mock_cmdp.get.side_effect = ["", "", "" "", "", ]
        mock_local.get_containers_list.return_value = [("ID", "NAME", ""), ]
        mock_local.isprotected_container.return_value = True
        mock_local.iswriteable_container.return_value = True
        udoc.do_ps(mock_cmdp)
        self.assertTrue(mock_local.isprotected_container.called)

    @mock.patch('udocker.CmdParser')
    @mock.patch('udocker.KeyStore')
    @mock.patch('udocker.DockerLocalFileAPI')
    @mock.patch('udocker.DockerIoAPI')
    @mock.patch('udocker.Msg')
    @mock.patch('udocker.LocalRepository')
    def test_19_do_rm(self, mock_local, mock_msg, mock_dioapi,
                      mock_dlocapi, mock_ks, mock_cmdp):
        """Test19 Udocker().do_rm()."""
        self._init()
        mock_msg.level = 0
        udoc = udocker.Udocker(mock_local)
        mock_cmdp.missing_options.return_value = True
        mock_cmdp.get.side_effect = ["", "", "" "", "", ]
        status = udoc.do_rm(mock_cmdp)
        self.assertFalse(status)

        udoc = udocker.Udocker(mock_local)
        mock_cmdp.missing_options.return_value = False
        mock_cmdp.get.side_effect = ["", "", "" "", "", ]
        status = udoc.do_rm(mock_cmdp)
        self.assertFalse(status)

        udoc = udocker.Udocker(mock_local)
        mock_cmdp.missing_options.return_value = False
        mock_cmdp.get.side_effect = ["X", "12", "" "", "", ]
        mock_local.get_container_id.return_value = ""
        status = udoc.do_rm(mock_cmdp)
        self.assertTrue(status)

        udoc = udocker.Udocker(mock_local)
        mock_cmdp.missing_options.return_value = False
        mock_cmdp.get.side_effect = ["X", "1", "" "", "", ]
        mock_local.get_container_id.return_value = "1"
        mock_local.isprotected_container.return_value = True
        status = udoc.do_rm(mock_cmdp)
        self.assertTrue(status)

        udoc = udocker.Udocker(mock_local)
        mock_cmdp.missing_options.return_value = False
        mock_cmdp.get.side_effect = ["X", "1", "" "", "", ]
        mock_local.get_container_id.return_value = "1"
        mock_local.isprotected_container.return_value = False
        status = udoc.do_rm(mock_cmdp)
        self.assertTrue(status)

    @mock.patch('udocker.Udocker._check_imagespec')
    @mock.patch('udocker.CmdParser')
    @mock.patch('udocker.KeyStore')
    @mock.patch('udocker.DockerLocalFileAPI')
    @mock.patch('udocker.DockerIoAPI')
    @mock.patch('udocker.Msg')
    @mock.patch('udocker.LocalRepository')
    def test_20_do_rmi(self, mock_local, mock_msg, mock_dioapi,
                       mock_dlocapi, mock_ks, mock_cmdp, mock_chkimg):
        """Test20 Udocker().do_rmi()."""
        self._init()
        mock_msg.level = 0
        udoc = udocker.Udocker(mock_local)
        mock_cmdp.missing_options.return_value = True
        mock_cmdp.get.side_effect = ["", "", "" "", "", ]
        mock_chkimg.return_value = ("IMAGE", "TAG")
        status = udoc.do_rmi(mock_cmdp)
        self.assertFalse(status)

        udoc = udocker.Udocker(mock_local)
        mock_cmdp.missing_options.return_value = False
        mock_cmdp.get.side_effect = ["", "", "" "", "", ]
        mock_chkimg.return_value = ("", "TAG")
        status = udoc.do_rmi(mock_cmdp)
        self.assertFalse(status)

        udoc = udocker.Udocker(mock_local)
        mock_cmdp.missing_options.return_value = False
        mock_cmdp.get.side_effect = ["", "", "" "", "", ]
        mock_chkimg.return_value = ("IMAGE", "TAG")
        mock_local.isprotected_imagerepo.return_value = True
        status = udoc.do_rmi(mock_cmdp)
        self.assertFalse(status)

        udoc = udocker.Udocker(mock_local)
        mock_cmdp.missing_options.return_value = False
        mock_cmdp.get.side_effect = ["", "", "" "", "", ]
        mock_chkimg.return_value = ("IMAGE", "TAG")
        mock_local.isprotected_imagerepo.return_value = False
        status = udoc.do_rmi(mock_cmdp)
        self.assertTrue(status)

    @mock.patch('udocker.Udocker._check_imagespec')
    @mock.patch('udocker.CmdParser')
    @mock.patch('udocker.KeyStore')
    @mock.patch('udocker.DockerLocalFileAPI')
    @mock.patch('udocker.DockerIoAPI')
    @mock.patch('udocker.Msg')
    @mock.patch('udocker.LocalRepository')
    def test_21_do_protect(self, mock_local, mock_msg, mock_dioapi,
                           mock_dlocapi, mock_ks, mock_cmdp, mock_chkimg):
        """Test21 Udocker().do_protect()."""
        self._init()
        mock_msg.level = 0
        udoc = udocker.Udocker(mock_local)
        mock_cmdp.missing_options.return_value = True
        mock_cmdp.get.side_effect = ["", "", "" "", "", ]
        mock_chkimg.return_value = ("IMAGE", "TAG")
        status = udoc.do_protect(mock_cmdp)
        self.assertFalse(status)

        udoc = udocker.Udocker(mock_local)
        mock_cmdp.missing_options.return_value = False
        mock_cmdp.get.side_effect = ["", "", "" "", "", ]
        mock_chkimg.return_value = ("IMAGE", "TAG")
        mock_local.get_container_id.return_value = "123"
        mock_local.protect_container.return_value = False
        status = udoc.do_protect(mock_cmdp)
        self.assertFalse(status)

        udoc = udocker.Udocker(mock_local)
        mock_cmdp.missing_options.return_value = False
        mock_cmdp.get.side_effect = ["", "", "" "", "", ]
        mock_chkimg.return_value = ("IMAGE", "TAG")
        mock_local.get_container_id.return_value = "123"
        mock_local.protect_container.return_value = True
        status = udoc.do_protect(mock_cmdp)
        self.assertTrue(status)

        udoc = udocker.Udocker(mock_local)
        mock_cmdp.missing_options.return_value = False
        mock_cmdp.get.side_effect = ["", "", "" "", "", ]
        mock_chkimg.return_value = ("", "TAG")
        mock_local.get_container_id.return_value = ""
        mock_local.protect_imagerepo.return_value = True
        status = udoc.do_protect(mock_cmdp)
        self.assertFalse(status)

        udoc = udocker.Udocker(mock_local)
        mock_cmdp.missing_options.return_value = False
        mock_cmdp.get.side_effect = ["", "", "" "", "", ]
        mock_chkimg.return_value = ("IMAGE", "TAG")
        mock_local.get_container_id.return_value = ""
        mock_local.protect_imagerepo.return_value = True
        status = udoc.do_protect(mock_cmdp)
        self.assertTrue(status)

    @mock.patch('udocker.Udocker._check_imagespec')
    @mock.patch('udocker.CmdParser')
    @mock.patch('udocker.KeyStore')
    @mock.patch('udocker.DockerLocalFileAPI')
    @mock.patch('udocker.DockerIoAPI')
    @mock.patch('udocker.Msg')
    @mock.patch('udocker.LocalRepository')
    def test_22_do_unprotect(self, mock_local, mock_msg, mock_dioapi,
                             mock_dlocapi, mock_ks, mock_cmdp, mock_chkimg):
        """Test22 Udocker().do_unprotect()."""
        self._init()
        mock_msg.level = 0
        udoc = udocker.Udocker(mock_local)
        mock_cmdp.missing_options.return_value = True
        mock_cmdp.get.side_effect = ["", "", "" "", "", ]
        mock_chkimg.return_value = ("IMAGE", "TAG")
        status = udoc.do_unprotect(mock_cmdp)
        self.assertFalse(status)

        udoc = udocker.Udocker(mock_local)
        mock_cmdp.missing_options.return_value = False
        mock_cmdp.get.side_effect = ["", "", "" "", "", ]
        mock_chkimg.return_value = ("IMAGE", "TAG")
        mock_local.get_container_id.return_value = "123"
        mock_local.unprotect_container.return_value = False
        status = udoc.do_unprotect(mock_cmdp)
        self.assertFalse(status)

        udoc = udocker.Udocker(mock_local)
        mock_cmdp.missing_options.return_value = False
        mock_cmdp.get.side_effect = ["", "", "" "", "", ]
        mock_chkimg.return_value = ("IMAGE", "TAG")
        mock_local.get_container_id.return_value = "123"
        mock_local.unprotect_container.return_value = True
        status = udoc.do_unprotect(mock_cmdp)
        self.assertTrue(status)

        udoc = udocker.Udocker(mock_local)
        mock_cmdp.missing_options.return_value = False
        mock_cmdp.get.side_effect = ["", "", "" "", "", ]
        mock_chkimg.return_value = ("IMAGE", "TAG")
        mock_local.get_container_id.return_value = ""
        mock_local.unprotect_imagerepo.return_value = True
        status = udoc.do_unprotect(mock_cmdp)
        self.assertTrue(status)
        self.assertTrue(mock_local.unprotect_imagerepo.called)

    @mock.patch('udocker.Udocker._check_imagespec')
    @mock.patch('udocker.CmdParser')
    @mock.patch('udocker.KeyStore')
    @mock.patch('udocker.DockerLocalFileAPI')
    @mock.patch('udocker.DockerIoAPI')
    @mock.patch('udocker.Msg')
    @mock.patch('udocker.LocalRepository')
    def test_23_do_name(self, mock_local, mock_msg, mock_dioapi,
                        mock_dlocapi, mock_ks, mock_cmdp, mock_chkimg):
        """Test23 Udocker().do_name()."""
        self._init()
        mock_msg.level = 0
        udoc = udocker.Udocker(mock_local)
        mock_cmdp.missing_options.return_value = True
        mock_cmdp.get.side_effect = ["", "", "" "", "", ]
        mock_chkimg.return_value = ("IMAGE", "TAG")
        status = udoc.do_name(mock_cmdp)
        self.assertFalse(status)

        udoc = udocker.Udocker(mock_local)
        mock_cmdp.missing_options.return_value = False
        mock_cmdp.get.side_effect = ["", "NAME", "" "", "", ]
        mock_chkimg.return_value = ("IMAGE", "TAG")
        mock_local.get_container_id.return_value = ""
        status = udoc.do_name(mock_cmdp)
        self.assertFalse(status)

        udoc = udocker.Udocker(mock_local)
        mock_cmdp.missing_options.return_value = False
        mock_cmdp.get.side_effect = ["", "NAME", "" "", "", ]
        mock_chkimg.return_value = ("IMAGE", "TAG")
        mock_local.get_container_id.return_value = "123"
        mock_local.set_container_name.return_value = False
        status = udoc.do_name(mock_cmdp)
        self.assertFalse(status)

        udoc = udocker.Udocker(mock_local)
        mock_cmdp.missing_options.return_value = False
        mock_cmdp.get.side_effect = ["", "NAME", "" "", "", ]
        mock_chkimg.return_value = ("IMAGE", "TAG")
        mock_local.get_container_id.return_value = "123"
        mock_local.set_container_name.return_value = True
        status = udoc.do_name(mock_cmdp)
        self.assertTrue(status)

    @mock.patch('udocker.Udocker._check_imagespec')
    @mock.patch('udocker.CmdParser')
    @mock.patch('udocker.KeyStore')
    @mock.patch('udocker.DockerLocalFileAPI')
    @mock.patch('udocker.DockerIoAPI')
    @mock.patch('udocker.Msg')
    @mock.patch('udocker.LocalRepository')
    def test_24_do_rmname(self, mock_local, mock_msg, mock_dioapi,
                          mock_dlocapi, mock_ks, mock_cmdp, mock_chkimg):
        """Test24 Udocker().do_rmname()."""
        self._init()
        mock_msg.level = 0
        udoc = udocker.Udocker(mock_local)
        mock_cmdp.missing_options.return_value = True
        mock_cmdp.get.side_effect = ["", "", "" "", "", ]
        mock_chkimg.return_value = ("IMAGE", "TAG")
        status = udoc.do_rmname(mock_cmdp)
        self.assertFalse(status)

        udoc = udocker.Udocker(mock_local)
        mock_cmdp.missing_options.return_value = False
        mock_cmdp.get.side_effect = ["NAME", "", "" "", "", ]
        mock_chkimg.return_value = ("IMAGE", "TAG")
        mock_local.del_container_name.return_value = False
        status = udoc.do_rmname(mock_cmdp)
        self.assertFalse(status)

        udoc = udocker.Udocker(mock_local)
        mock_cmdp.missing_options.return_value = False
        mock_cmdp.get.side_effect = ["NAME", "", "" "", "", ]
        mock_chkimg.return_value = ("IMAGE", "TAG")
        mock_local.del_container_name.return_value = True
        status = udoc.do_rmname(mock_cmdp)
        self.assertTrue(status)

    @mock.patch('udocker.json')
    @mock.patch('udocker.ContainerStructure')
    @mock.patch('udocker.Udocker._check_imagespec')
    @mock.patch('udocker.CmdParser')
    @mock.patch('udocker.KeyStore')
    @mock.patch('udocker.DockerLocalFileAPI')
    @mock.patch('udocker.DockerIoAPI')
    @mock.patch('udocker.Msg')
    @mock.patch('udocker.LocalRepository')
    def test_25_do_inspect(self, mock_local, mock_msg, mock_dioapi,
                           mock_dlocapi, mock_ks, mock_cmdp, mock_chkimg,
                           mock_cstruct, mock_json):
        """Test25 Udocker().do_inspect()."""
        self._init()
        mock_msg.level = 0
        udoc = udocker.Udocker(mock_local)
        mock_cmdp.missing_options.return_value = True
        mock_cmdp.get.side_effect = ["", "", "" "", "", ]
        mock_chkimg.return_value = ("IMAGE", "TAG")
        status = udoc.do_inspect(mock_cmdp)
        self.assertFalse(status)

        udoc = udocker.Udocker(mock_local)
        mock_cmdp.missing_options.return_value = False
        mock_cmdp.get.side_effect = ["", "", "" "", "", ]
        mock_chkimg.return_value = ("IMAGE", "TAG")
        mock_local.get_container_id.return_value = "123"
        mock_cstruct.return_value.get_container_attr.return_value = ("", "")
        status = udoc.do_inspect(mock_cmdp)
        self.assertFalse(status)

        udoc = udocker.Udocker(mock_local)
        mock_cmdp.missing_options.return_value = False
        mock_cmdp.get.side_effect = ["", "PRINT", "" "", "", ]
        mock_chkimg.return_value = ("IMAGE", "TAG")
        mock_local.get_container_id.return_value = "123"
        mock_cstruct.return_value.get_container_attr.return_value = ("DIR", "")
        status = udoc.do_inspect(mock_cmdp)
        self.assertTrue(status)

        udoc = udocker.Udocker(mock_local)
        mock_cmdp.missing_options.return_value = False
        mock_cmdp.get.side_effect = ["", "", "" "", "", ]
        mock_chkimg.return_value = ("IMAGE", "TAG")
        mock_local.get_container_id.return_value = "123"
        mock_cstruct.return_value.get_container_attr.return_value = (
            "", "JSON")
        status = udoc.do_inspect(mock_cmdp)
        self.assertTrue(status)

    @mock.patch('udocker.Udocker._check_imagespec')
    @mock.patch('udocker.CmdParser')
    @mock.patch('udocker.KeyStore')
    @mock.patch('udocker.DockerLocalFileAPI')
    @mock.patch('udocker.DockerIoAPI')
    @mock.patch('udocker.Msg')
    @mock.patch('udocker.LocalRepository')
    def test_26_do_verify(self, mock_local, mock_msg, mock_dioapi,
                          mock_dlocapi, mock_ks, mock_cmdp, mock_chkimg):
        """Test26 Udocker().do_verify()."""
        self._init()
        mock_msg.level = 0
        udoc = udocker.Udocker(mock_local)
        mock_cmdp.missing_options.return_value = True
        mock_cmdp.get.side_effect = ["", "", "" "", "", ]
        mock_chkimg.return_value = ("IMAGE", "TAG")
        status = udoc.do_verify(mock_cmdp)
        self.assertFalse(status)

        udoc = udocker.Udocker(mock_local)
        mock_cmdp.missing_options.return_value = False
        mock_cmdp.get.side_effect = ["", "", "" "", "", ]
        mock_chkimg.return_value = ("", "")
        status = udoc.do_verify(mock_cmdp)
        self.assertFalse(status)

        udoc = udocker.Udocker(mock_local)
        mock_cmdp.missing_options.return_value = False
        mock_cmdp.get.side_effect = ["", "", "" "", "", ]
        mock_chkimg.return_value = ("IMAGE", "TAG")
        mock_local.cd_imagerepo.return_value = False
        status = udoc.do_verify(mock_cmdp)
        self.assertFalse(status)

        udoc = udocker.Udocker(mock_local)
        mock_cmdp.missing_options.return_value = False
        mock_cmdp.get.side_effect = ["", "", "" "", "", ]
        mock_chkimg.return_value = ("IMAGE", "TAG")
        mock_local.cd_imagerepo.return_value = True
        mock_local.verify_image.return_value = True
        status = udoc.do_verify(mock_cmdp)
        self.assertTrue(status)

    # @mock.patch('udocker.ExecutionMode')
    # @mock.patch('udocker.CmdParser')
    # @mock.patch('udocker.KeyStore')
    # @mock.patch('udocker.DockerLocalFileAPI')
    # @mock.patch('udocker.DockerIoAPI')
    # @mock.patch('udocker.Msg')
    # @mock.patch('udocker.LocalRepository')
    # def test_27_do_setup(self, mock_local, mock_msg, mock_dioapi,
    #                      mock_dlocapi, mock_ks, mock_cmdp, mock_exec):
    #     """Test27 Udocker().do_setup()."""
    #     self._init()
    #     mock_msg.level = 0
    #     udoc = udocker.Udocker(mock_local)
    #     mock_cmdp.missing_options.return_value = True
    #     mock_cmdp.get.side_effect = ["", "", "" "", "", ]
    #     mock_local.cd_container.return_value = False
    #     status = udoc.do_setup(mock_cmdp)
    #     self.assertFalse(status)

    #     udoc = udocker.Udocker(mock_local)
    #     mock_cmdp.missing_options.return_value = True
    #     mock_cmdp.get.side_effect = ["", "", "" "", "", ]
    #     mock_local.cd_container.return_value = True
    #     mock_exec.set_mode.return_value = False
    #     status = udoc.do_setup(mock_cmdp)
    #     self.assertFalse(status)

    #     udoc = udocker.Udocker(mock_local)
    #     mock_cmdp.missing_options.return_value = True
    #     mock_cmdp.get.side_effect = ["", "", "" "", "", ]
    #     mock_local.cd_container.return_value = True
    #     mock_exec.set_mode.return_value = True
    #     status = udoc.do_setup(mock_cmdp)
    #     self.assertFalse(status)

    #     udoc = udocker.Udocker(mock_local)
    #     mock_cmdp.missing_options.return_value = True
    #     mock_cmdp.get.side_effect = ["", "P1", "" "", "", ]
    #     mock_local.cd_container.return_value = True
    #     mock_local.isprotected_container.return_value = True
    #     mock_exec.set_mode.return_value = True
    #     status = udoc.do_setup(mock_cmdp)
    #     self.assertFalse(status)

    #     udoc = udocker.Udocker(mock_local)
    #     mock_cmdp.missing_options.return_value = True
    #     mock_cmdp.get.side_effect = ["", "P1", "" "", "", ]
    #     mock_local.cd_container.return_value = True
    #     mock_local.isprotected_container.return_value = False
    #     mock_exec.set_mode.return_value = True
    #     status = udoc.do_setup(mock_cmdp)
    #     self.assertFalse(status)

    @mock.patch('udocker.UdockerTools')
    @mock.patch('udocker.CmdParser')
    @mock.patch('udocker.Msg')
    @mock.patch('udocker.LocalRepository')
    def test_28_do_install(self, mock_local, mock_msg, mock_cmdp,
                           mock_utools):
        """Test28 Udocker().do_install()."""
        self._init()
        mock_msg.level = 0
        udoc = udocker.Udocker(mock_local)
        mock_cmdp.missing_options.return_value = True
        mock_cmdp.get.side_effect = ["", "", "" "", "", ]
        status = udoc.do_install(mock_cmdp)
        self.assertFalse(mock_utools.return_value.purge.called)
        # self.assertTrue(mock_utools.return_value.install.called)

        udoc = udocker.Udocker(mock_local)
        mock_cmdp.missing_options.return_value = True
        mock_cmdp.get.side_effect = ["", "--purge", "" "", "", ]
        mock_utools.reset_mock()
        mock_cmdp.reset_mock()
        status = udoc.do_install(mock_cmdp)
        # self.assertTrue(mock_utools.return_value.purge.called)
        self.assertTrue(mock_utools.return_value.install.called_with(False))

        udoc = udocker.Udocker(mock_local)
        mock_cmdp.missing_options.return_value = True
        mock_cmdp.get.side_effect = ["", "--purge", "--force" "", "", ]
        mock_utools.reset_mock()
        mock_cmdp.reset_mock()
        status = udoc.do_install(mock_cmdp)
        # self.assertTrue(mock_utools.return_value.purge.called)
        self.assertTrue(mock_utools.return_value.install.called_with(True))

        udoc = udocker.Udocker(mock_local)
        mock_cmdp.missing_options.return_value = True
        mock_cmdp.get.side_effect = ["", "", "--force" "", "", ]
        mock_utools.reset_mock()
        mock_cmdp.reset_mock()
        status = udoc.do_install(mock_cmdp)
        # self.assertFalse(mock_utools.return_value.purge.called)
        self.assertTrue(mock_utools.return_value.install.called_with(True))

    @mock.patch('udocker.Msg.out')
    @mock.patch('udocker.CmdParser')
    @mock.patch('udocker.LocalRepository')
    def test_29_do_help(self, mock_local, mock_cmdp, mock_msgout):
        """Test29 Udocker().do_help()."""
        self._init()
        udoc = udocker.Udocker(mock_local)
        mock_cmdp.get.side_effect = ["run", "help", "" "", "", ]
        udoc.do_help(mock_cmdp)
        self.assertTrue(mock_msgout.called)

    @mock.patch('udocker.CmdParser')
    @mock.patch('udocker.LocalRepository')
    def test_30_do_version(self, mock_local, mock_cmdp):
        """Test30 Udocker().do_version()."""
        self._init()
        udoc = udocker.Udocker(mock_local)
        mock_cmdp.get.side_effect = ["run", "", "" "", "", ]
        version = udoc.do_version(mock_cmdp)
        self.assertIsNotNone(version)


class CmdParserTestCase(unittest.TestCase):
    """Test CmdParserTestCase() command line interface."""

    @classmethod
    def setUpClass(cls):
        """Setup test."""
        set_env()

    def test_01__init(self):
        """Test01 CmdParser() Constructor."""
        cmdp = udocker.CmdParser()
        self.assertEqual(cmdp._argv, "")
        self.assertIsInstance(cmdp._argv_split, dict)
        self.assertIsInstance(cmdp._argv_consumed_options, dict)
        self.assertIsInstance(cmdp._argv_consumed_params, dict)
        self.assertEqual(cmdp._argv_split['CMD'], "")
        self.assertEqual(cmdp._argv_split['GEN_OPT'], [])
        self.assertEqual(cmdp._argv_split['CMD_OPT'], [])
        self.assertEqual(cmdp._argv_consumed_options['GEN_OPT'], [])
        self.assertEqual(cmdp._argv_consumed_options['CMD_OPT'], [])
        self.assertEqual(cmdp._argv_consumed_params['GEN_OPT'], [])
        self.assertEqual(cmdp._argv_consumed_params['CMD_OPT'], [])

    def test_02_parse(self):
        """Test02 CmdParser().parse()."""
        cmdp = udocker.CmdParser()
        status = cmdp.parse("udocker run --bindhome "
                            "--hostauth --hostenv -v /sys"
                            " -v /proc -v /var/run -v /dev"
                            " --user=jorge --dri myfed  firefox")
        self.assertTrue(status)

    def test_03_missing_options(self):
        """Test03 CmdParser().missing_options()."""
        cmdp = udocker.CmdParser()
        cmdp.parse("udocker run --bindhome "
                   "--hostauth --hostenv -v /sys"
                   " -v /proc -v /var/run -v /dev"
                   " --user=jorge --dri myfed  firefox")
        out = cmdp.missing_options()
        self.assertIsInstance(out, list)

    def test_04_get(self):
        """Test04 CmdParser().get()."""
        cmdp = udocker.CmdParser()
        cmdp.declare_options("-v= -e= -w= -u= -i -t -a")
        cmdp.parse("udocker run --bindhome "
                   "--hostauth --hostenv -v /sys"
                   " -v /proc -v /var/run -v /dev --debug"
                   " -u=jorge --dri myfed  firefox")
        out = cmdp.get("xyz")
        self.assertIsNone(out)

        # out = cmdp.get("--user=")
        # self.assertEqual(out, "jorge")

        # out = cmdp.get("--debug", "GEN_OPT")
        # self.assertTrue(out)

    # def test_05_declare_options(self):
    #     """Test05 CmdParser().declare_options()."""
    #     pass

    # def test_06__get_options(self):
    #     """Test06 CmdParser()._get_options()."""
    #     pass

    # def test_07__get_params(self):
    #     """Test07 CmdParser()._get_params()."""
    #     pass


class MainTestCase(unittest.TestCase):
    """Test Main() class main udocker program."""

    @classmethod
    def setUpClass(cls):
        """Setup test."""
        set_env()

    def _init(self):
        """Configure variables."""
        udocker.Config = mock.MagicMock()
        udocker.Config.hostauth_list = ("/etc/passwd", "/etc/group")
        udocker.Config.cmd = "/bin/bash"
        #udocker.Config.cpu_affinity_exec_tools = (["numactl", "-C", "%s", "--", ],
        #                       ["taskset", "-c", "%s", ])
        udocker.Config.cpu_affinity_exec_tools = ("taskset -c ", "numactl -C ")
        udocker.Config.valid_host_env = "HOME"
        udocker.Config.username.return_value = "user"
        udocker.Config.userhome.return_value = "/"
        udocker.Config.location = ""
        udocker.Config.oskernel.return_value = "4.8.13"
        udocker.Config.verbose_level = 3
        udocker.Config.http_insecure = False
        udocker.Config.topdir = "/.udocker"

    @mock.patch('udocker.Msg')
    @mock.patch('udocker.CmdParser')
    def test_01_init(self, mock_cmdp, mock_msg):
        """Test01 Main() constructor."""
        self._init()
        mock_cmdp.return_value.parse.return_value = False
        with self.assertRaises(SystemExit) as mainexpt:
            udocker.Main()
        self.assertEqual(mainexpt.exception.code, 0)

    @mock.patch('udocker.LocalRepository')
    @mock.patch('udocker.Udocker')
    @mock.patch('udocker.Config.user_init')
    @mock.patch('udocker.Msg')
    @mock.patch('udocker.CmdParser')
    def test_02_init(self, mock_cmdp, mock_msg, mock_conf_init, mock_udocker,
                     mock_localrepo):
        """Test02 Main() constructor."""
        self._init()
        mock_cmdp.return_value.parse.return_value = True
        mock_cmdp.return_value.get.side_effect = [False, False, False, False,
                                                  False, False, False, False,
                                                  False]
        udocker.Main()
        self.assertEqual(udocker.Config.verbose_level, 3)

        # --debug
        mock_cmdp.return_value.parse.return_value = True
        mock_cmdp.return_value.get.side_effect = [False, False, True, False,
                                                  False, False, False, False,
                                                  False]
        udocker.Main()
        self.assertNotEqual(udocker.Config.verbose_level, 3)

        # -D
        mock_cmdp.return_value.parse.return_value = True
        mock_cmdp.return_value.get.side_effect = [False, False, False, True,
                                                  False, False, False, False,
                                                  False]
        udocker.Main()
        self.assertNotEqual(udocker.Config.verbose_level, 3)

        # --quiet
        mock_cmdp.return_value.parse.return_value = True
        mock_cmdp.return_value.get.side_effect = [False, False, False, False,
                                                  True, False, False, False,
                                                  False]
        udocker.Main()
        self.assertNotEqual(udocker.Config.verbose_level, 3)

        # -q
        mock_cmdp.return_value.parse.return_value = True
        mock_cmdp.return_value.get.side_effect = [False, False, False, False,
                                                  False, True, False, False,
                                                  False]
        udocker.Main()
        self.assertNotEqual(udocker.Config.verbose_level, 3)

        # --insecure
        mock_cmdp.return_value.parse.return_value = True
        mock_cmdp.return_value.get.side_effect = [False, False, False, False,
                                                  False, False, True, False,
                                                  False, False]
        udocker.Main()
        self.assertTrue(udocker.Config.http_insecure)

        # --repo=
        mock_localrepo.return_value.is_repo.return_value = True
        mock_cmdp.return_value.parse.return_value = True
        mock_cmdp.return_value.get.side_effect = [False, False, False, False,
                                                  False, False, False, True,
                                                  "/TOPDIR"]
        with self.assertRaises(SystemExit) as mainexpt:
            udocker.Main()
        self.assertEqual(mainexpt.exception.code, 0)

    @mock.patch('udocker.Main.__init__')
    @mock.patch('udocker.LocalRepository')
    @mock.patch('udocker.Udocker')
    @mock.patch('udocker.Msg')
    @mock.patch('udocker.CmdParser')
    def test_03_execute(self, mock_cmdp, mock_msg, mock_udocker,
                        mock_localrepo, mock_main_init):
        """Test03 Main().execute()."""
        self._init()
        mock_main_init.return_value = None
        mock_cmdp.return_value.get.side_effect = [True, False, False, False,
                                                  False, False, False, False]
        umain = udocker.Main()
        umain.udocker = mock_udocker
        umain.cmdp = mock_cmdp
        status = umain.execute()
        self.assertEqual(status, 0)

        mock_main_init.return_value = None
        mock_cmdp.return_value.get.side_effect = [False, True, False, False,
                                                  False, False, False, False]
        umain = udocker.Main()
        umain.udocker = mock_udocker
        umain.cmdp = mock_cmdp
        status = umain.execute()
        self.assertEqual(status, 0)

        mock_main_init.return_value = None
        mock_cmdp.return_value.get.side_effect = [False, False, "ERR", False,
                                                  False, False, False, False]
        umain = udocker.Main()
        umain.udocker = mock_udocker
        umain.cmdp = mock_cmdp
        umain.cmdp.reset_mock()
        status = umain.execute()
        self.assertTrue(umain.udocker.do_help.called)

        mock_main_init.return_value = None
        mock_cmdp.return_value.get.side_effect = [False, False, "run", True,
                                                  False, False, False, False]
        umain = udocker.Main()
        umain.udocker = mock_udocker
        umain.cmdp = mock_cmdp
        umain.cmdp.reset_mock()
        status = umain.execute()
        self.assertTrue(umain.udocker.do_help.called)

    @mock.patch('udocker.Main.__init__')
    @mock.patch('udocker.Main.execute')
    @mock.patch('udocker.FileUtil')
    @mock.patch('udocker.Msg')
    def test_04_start(self, mock_msg, mock_futil, mock_main_execute,
                      mock_main_init):
        """Test04 Main().start()."""
        self._init()
        mock_main_init.return_value = None
        mock_main_execute.return_value = 2
        umain = udocker.Main()
        status = umain.start()
        self.assertEqual(status, 2)

        self._init()
        mock_main_init.return_value = None
        mock_main_execute.return_value = 2
        mock_main_execute.side_effect = KeyboardInterrupt("CTRLC")
        umain = udocker.Main()
        status = umain.start()
        self.assertEqual(status, 1)


if __name__ == '__main__':
    unittest.main()
