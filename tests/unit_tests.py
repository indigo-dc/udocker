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
__version__ = "0.0.2-1"
__date__ = "2016"

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


class UprocessTestCase(unittest.TestCase):
    """Test case for the Uprocess class."""

    @classmethod
    def setUpClass(cls):
        """Setup test."""
        set_env()

    @mock.patch('udocker.subprocess.Popen')
    def test_01__check_output(self, mock_popen):
        """Test _check_output()."""
        mock_popen.return_value.communicate.return_value = ("OUTPUT", None)
        mock_popen.return_value.poll.return_value = 0
        uproc = udocker.Uprocess()
        status = uproc._check_output("CMD")
        self.assertEqual(status, "OUTPUT")
        #
        mock_popen.return_value.communicate.return_value = ("OUTPUT", None)
        mock_popen.return_value.poll.return_value = 1
        uproc = udocker.Uprocess()
        self.assertRaises(subprocess.CalledProcessError,
                          uproc._check_output, "CMD")

    @mock.patch('udocker.Uprocess._check_output')
    @mock.patch('udocker.subprocess.check_output')
    def test_02_check_output(self, mock_subp_chkout, mock_uproc_chkout):
        """Test check_output()."""
        uproc = udocker.Uprocess()
        uproc.check_output("CMD")
        # udocker.PY_VER = "%d.%d" % (sys.version_info[0], sys.version_info[1])
        # if udocker.PY_VER >= "2.7":
        #     self.assertTrue(mock_subp_chkout.called)
        # else:
        #     self.assertTrue(mock_uproc_chkout.called)

        # Making sure we cover both cases
        udocker.PY_VER = "3.5"
        uproc.check_output("CMD")
        self.assertTrue(mock_subp_chkout.called)
        udocker.PY_VER = "2.6"
        uproc.check_output("CMD")
        self.assertTrue(mock_uproc_chkout.called)

    @mock.patch('udocker.Uprocess.check_output')
    def test_03_get_output(self, mock_uproc_chkout):
        """Test get_output()."""
        mock_uproc_chkout.return_value = "OUTPUT"
        uproc = udocker.Uprocess()
        self.assertEqual("OUTPUT", uproc.get_output("CMD"))

    def test_04_get_output(self):
        """Test get_output()."""
        uproc = udocker.Uprocess()
        self.assertRaises(subprocess.CalledProcessError,
                          uproc.get_output("/bin/false"))


class ConfigTestCase(unittest.TestCase):
    """Test case for the udocker configuration."""

    @classmethod
    def setUpClass(cls):
        """Setup test."""
        set_env()

    def _verify_config(self, conf):
        """Verify config parameters."""
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
        self.assertIsInstance(conf.hostauth_list, tuple)
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
        """Test Config() constructor."""
        conf = udocker.Config()
        self._verify_config(conf)

    @mock.patch('udocker.platform')
    def test_02_platform(self, mock_platform):
        """Test Config.platform()."""
        conf = udocker.Config()
        mock_platform.machine.return_value = "x86_64"
        arch = conf.arch()
        self.assertEqual("amd64", arch, "Config._sysarch x86_64")
        mock_platform.machine.return_value = "i586"
        arch = conf.arch()
        self.assertEqual("i386", arch, "Config._sysarchi i586")
        mock_platform.machine.return_value = "xpto"
        arch = conf.arch()
        self.assertEqual("", arch, "Config._sysarchi i586")
        #
        mock_platform.system.return_value = "linux"
        osver = conf.osversion()
        self.assertEqual(osver, "linux")
        #
        mock_platform.release.return_value = "release"
        osver = conf.oskernel()
        self.assertEqual(osver, "release")

    @mock.patch('udocker.Config._verify_config')
    @mock.patch('udocker.Config._override_config')
    @mock.patch('udocker.Config._read_config')
    @mock.patch('udocker.Msg')
    @mock.patch('udocker.FileUtil')
    def test_03_user_init_good(self, mock_fileutil, mock_msg,
                               mock_readc, mock_overrride, mock_verify):
        """Test Config.user_init() with good data."""
        udocker.Msg = mock_msg
        conf = udocker.Config()
        conf_data = '# comment\nverbose_level = 100\n'
        conf_data += 'tmpdir = "/xpto"\ncmd = ["/bin/ls", "-l"]\n'
        mock_readc.return_value = conf_data
        status = conf.user_init("filename.conf")
        self.assertFalse(mock_verify.called)

    @mock.patch('udocker.Msg')
    @mock.patch('udocker.FileUtil')
    @mock.patch('udocker.sys.exit')
    def test_04_user_init_bad(self, mock_exit, mock_fileutil, mock_msg):
        """Test Config.user_init() with bad config data."""
        udocker.Msg = mock_msg
        conf = udocker.Config()
        conf_data = 'hh +=* ffhdklfh\n'
        mock_fileutil.return_value.size.return_value = 10
        mock_fileutil.return_value.getdata.return_value = conf_data
        conf.user_init("filename.conf")
        self.assertTrue(mock_exit.called)

    @mock.patch('udocker.Msg')
    def test_05_username(self, mock_msg):
        """Test Config._username()."""
        udocker.Msg = mock_msg
        conf = udocker.Config()
        user = conf.username()
        self.assertEqual(user, pwd.getpwuid(os.getuid()).pw_name)

    @mock.patch('udocker.Config.oskernel')
    @mock.patch('udocker.Msg')
    def test_06_oskernel_isgreater(self, mock_msg, mock_oskern):
        """Test Config.oskernel_isgreater()."""
        udocker.Msg = mock_msg
        conf = udocker.Config()
        #
        mock_oskern.return_value = "1.1.2-"
        status = conf.oskernel_isgreater([1, 1, 1])
        self.assertTrue(status)
        #
        mock_oskern.return_value = "1.2.1-"
        status = conf.oskernel_isgreater([1, 1, 1])
        self.assertTrue(status)
        #
        mock_oskern.return_value = "1.0.1-"
        status = conf.oskernel_isgreater([1, 1, 1])
        self.assertFalse(status)

    @mock.patch('udocker.FileUtil')
    def test_07__read_config(self, mock_futil):
        """Test Config._read_config()."""
        conf = udocker.Config()
        mock_futil.return_value.size.return_value = -1
        status = conf._read_config(conf)
        self.assertFalse(status)

    @mock.patch('udocker.Config.__init__')
    @mock.patch('udocker.Msg')
    def test_00__verify_config(self, mock_msg, mock_conf_init):
        """Test Config._verify_config()."""
        mock_conf_init.return_value = None
        udocker.Config.topdir = "/.udocker"
        conf = udocker.Config()
        conf._verify_config()
        self.assertFalse(mock_msg.return_value.err.called)
        #
        mock_conf_init.return_value = None
        udocker.Config.topdir = ""
        conf = udocker.Config()
        with self.assertRaises(SystemExit) as confexpt:
            conf._verify_config()
        self.assertEqual(confexpt.exception.code, 1)

    @mock.patch('udocker.Config.__init__')
    @mock.patch('udocker.platform.architecture')
    @mock.patch('udocker.platform.machine')
    def test_00_arch(self, mock_machine, mock_architecture, mock_conf_init):
        """Test Config.arch()."""
        mock_conf_init.return_value = None
        mock_machine.return_value = "x86_64"
        mock_architecture.return_value = ["32bit", ]
        conf = udocker.Config()
        status = conf.arch()
        self.assertEqual(status, "i386")
        #
        mock_conf_init.return_value = None
        mock_machine.return_value = "x86_64"
        mock_architecture.return_value = ["", ]
        conf = udocker.Config()
        status = conf.arch()
        self.assertEqual(status, "amd64")
        #
        mock_conf_init.return_value = None
        mock_machine.return_value = "i686"
        mock_architecture.return_value = ["", ]
        conf = udocker.Config()
        status = conf.arch()
        self.assertEqual(status, "i386")
        #
        mock_conf_init.return_value = None
        mock_machine.return_value = "armXX"
        mock_architecture.return_value = ["32bit", ]
        conf = udocker.Config()
        status = conf.arch()
        self.assertEqual(status, "arm")
        #
        mock_conf_init.return_value = None
        mock_machine.return_value = "armXX"
        mock_architecture.return_value = ["", ]
        conf = udocker.Config()
        status = conf.arch()
        self.assertEqual(status, "arm64")

    @mock.patch('udocker.Config.__init__')
    @mock.patch('udocker.platform.system')
    def test_00_osversion(self, mock_system, mock_conf_init):
        """Test Config.osversion()."""
        mock_conf_init.return_value = None
        mock_system.return_value = "Linux"
        conf = udocker.Config()
        status = conf.osversion()
        self.assertEqual(status, "linux")
        #
        mock_conf_init.return_value = None
        mock_system.return_value = "Linux"
        mock_system.side_effect = NameError('platform system')
        conf = udocker.Config()
        status = conf.osversion()
        self.assertEqual(status, "")

    @mock.patch('udocker.Config.__init__')
    @mock.patch('udocker.platform.linux_distribution')
    def test_00_osdistribution(self, mock_distribution, mock_conf_init):
        """Test Config.osdistribution()."""
        mock_conf_init.return_value = None
        mock_distribution.return_value = ("DISTRO XX", "1.0", "DUMMY")
        conf = udocker.Config()
        status = conf.osdistribution()
        self.assertEqual(status, ("DISTRO", "1"))

    @mock.patch('udocker.Config.__init__')
    @mock.patch('udocker.platform.release')
    def test_00_oskernel(self, mock_release, mock_conf_init):
        """Test Config.oskernel()."""
        mock_conf_init.return_value = None
        mock_release.return_value = "1.2.3"
        conf = udocker.Config()
        status = conf.oskernel()
        self.assertEqual(status, "1.2.3")
        #
        mock_conf_init.return_value = None
        mock_release.return_value = "1.2.3"
        mock_release.side_effect = NameError('platform release')
        conf = udocker.Config()
        status = conf.oskernel()
        self.assertEqual(status, "3.2.1")


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
        self.osdist = ("Ubuntu", "16.04")
        self.noosdist = ("", "xx")

    def test_01_init(self):
        """Test GuestInfo() constructor."""
        self._init()
        ginfo = udocker.GuestInfo(self.rootdir)
        self.assertEqual(ginfo._root_dir, self.rootdir)

    @mock.patch('udocker.Uprocess.get_output')
    @mock.patch('udocker.os.path.isfile')
    def test_02_get_filetype(self, mock_isfile, mock_getout):
        """Test GuestInfo.get_filetype(filename)"""
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

#    @mock.patch('udocker.Uprocess.get_output')
#    @mock.patch('udocker.GuestInfo')
#    @mock.patch('udocker.GuestInfo._binarylist')
#    def test_03_arch(self, mock_binlist, mock_gi, mock_getout):
#        """Test GuestInfo.arch()"""
#        self._init()
#        # arch is x86_64
#        mock_binlist.return_value = ["/bin/bash", "/bin/ls"]
#        mock_getout.return_value.get_filetype.side_effect = [self.ftype, self.ftype]
#        ginfo = udocker.GuestInfo(self.rootdir)
#        self.assertEqual(ginfo.arch(), "amd64")

    # @mock.patch('udocker.os.path.exists')
    # @mock.patch('udocker.FileUtil.match')
    # @mock.patch('udocker.FileUtil.getdata')
    # def test_04_osdistribution(self, mock_gdata, mock_match, mock_exists):
    #     """Test GuestInfo.osdistribution()"""
    #     self._init()
    #     # has osdistro
    #     self.lsbdata = "DISTRIB_ID=Ubuntu\n" \
    #                    "DISTRIB_RELEASE=16.04\n" \
    #                    "DISTRIB_CODENAME=xenial\n" \
    #                    "DISTRIB_DESCRIPTION=Ubuntu 16.04.5 LTS\n"
    #     mock_match.return_value = ["/etc/lsb-release"]
    #     mock_exists.return_value = True
    #     mock_gdata.return_value = self.lsbdata
    #     ginfo = udocker.GuestInfo(self.rootdir)
    #     self.assertEqual(ginfo.osdistribution(), self.osdist)

    @mock.patch('udocker.GuestInfo.osdistribution')
    def test_05_osversion(self, mock_osdist):
        """Test GuestInfo.osversion()"""
        self._init()
        # has osdistro
        mock_osdist.return_value = self.osdist
        ginfo = udocker.GuestInfo(self.rootdir)
        self.assertEqual(ginfo.osversion(), "linux")
        # has no osdistro
        mock_osdist.return_value = self.noosdist
        ginfo = udocker.GuestInfo(self.rootdir)
        self.assertEqual(ginfo.osversion(), "")


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
        """Test Msg() constructor."""
        msg = udocker.Msg(0)
        self._verify_descriptors(msg)
        self.assertEqual(msg.level, 0)

    def test_02_setlevel(self):
        """Test Msg.setlevel() change of log level."""
        msg = udocker.Msg(5)
        self._verify_descriptors(msg)
        self.assertEqual(msg.level, 5)
        msg = udocker.Msg(0)
        msg.setlevel(7)
        self._verify_descriptors(msg)
        self.assertEqual(msg.level, 7)

    @mock.patch('udocker.sys.stdout', new_callable=StringIO)
    def test_03_out(self, mock_stdout):
        """Test Msg.out() screen messages."""
        msg = udocker.Msg(udocker.Msg.MSG)
        msg.out("111", "222", "333", 444, ('555'))
        self.assertEqual("111 222 333 444 555\n", mock_stdout.getvalue())
        sys.stdout = STDOUT
        sys.stderr = STDERR

    @mock.patch('udocker.sys.stderr', new_callable=StringIO)
    def test_04_err(self, mock_stderr):
        """Test Msg.err() screen messages."""
        msg = udocker.Msg(udocker.Msg.ERR)
        msg.err("111", "222", "333", 444, ('555'))
        self.assertEqual("111 222 333 444 555\n", mock_stderr.getvalue())
        sys.stdout = STDOUT
        sys.stderr = STDERR


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
        """Test KeyStore() constructor."""
        kstore = udocker.KeyStore("filename")
        self.assertEqual(kstore.keystore_file, "filename")

    @mock.patch('udocker.json.load')
    def test_02__read_all(self, mock_jload):
        """Test KeyStore()._read_all() read credentials."""
        self._init()
        mock_jload.return_value = self.credentials
        with mock.patch(BUILTINS + '.open', mock.mock_open()):
            kstore = udocker.KeyStore("filename")
            self.assertEqual(self.credentials, kstore._read_all())

    @mock.patch('udocker.Config')
    @mock.patch('udocker.KeyStore._verify_keystore')
    def test_02__shred(self, mock_config, mock_verks):
        """Test KeyStore()._shred() erase file content."""
        udocker.Config = mock_config
        udocker.Config.tmpdir = "/tmp"
        with mock.patch(BUILTINS + '.open', mock.mock_open()):
            kstore = udocker.KeyStore("filename")
            self.assertFalse(kstore._shred())

    @mock.patch('udocker.Config')
    @mock.patch('udocker.KeyStore._verify_keystore')
    @mock.patch('udocker.os.stat')
    def test_03__shred(self, mock_stat, mock_config, mock_verks):
        """Test KeyStore()._shred() erase file content."""
        udocker.Config = mock_config
        udocker.Config.tmpdir = "/tmp"
        mock_stat.return_value.st_size = 123
        with mock.patch(BUILTINS + '.open', mock.mock_open()):
            kstore = udocker.KeyStore("filename")
            self.assertTrue(kstore._shred())

    @mock.patch('udocker.Config')
    @mock.patch('udocker.KeyStore._verify_keystore')
    @mock.patch('udocker.json.dump')
    @mock.patch('udocker.os.umask')
    def test_04__write_all(self, mock_umask, mock_jdump,
                           mock_config, mock_verks):
        """Test KeyStore()._write_all() write all credentials to file."""
        self._init()
        udocker.Config = mock_config
        udocker.Config.tmpdir = "/tmp"
        mock_umask.return_value = 0o77
        mock_jdump.side_effect = IOError('json dump')
        with mock.patch(BUILTINS + '.open', mock.mock_open()):
            kstore = udocker.KeyStore("filename")
            self.assertFalse(kstore._write_all(self.credentials))

    @mock.patch('udocker.Config')
    @mock.patch('udocker.KeyStore._verify_keystore')
    @mock.patch('udocker.KeyStore._read_all')
    def test_05_get(self, mock_readall, mock_config, mock_verks):
        """Test KeyStore().get() get credential for url from file."""
        self._init()
        udocker.Config = mock_config
        udocker.Config.tmpdir = "/tmp"
        mock_readall.return_value = self.credentials
        kstore = udocker.KeyStore("filename")
        self.assertTrue(kstore.get(self.url))
        self.assertFalse(kstore.get("NOT EXISTING ENTRY"))

    @mock.patch('udocker.Config')
    @mock.patch('udocker.KeyStore._verify_keystore')
    @mock.patch('udocker.KeyStore._shred')
    @mock.patch('udocker.KeyStore._write_all')
    @mock.patch('udocker.KeyStore._read_all')
    def test_06_put(self, mock_readall, mock_writeall, mock_shred,
                    mock_config, mock_verks):
        """Test KeyStore().put() put credential for url to file."""
        self._init()
        udocker.Config = mock_config
        udocker.Config.tmpdir = "/tmp"
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
    def test_07_delete(self, mock_readall, mock_writeall, mock_shred,
                       mock_config, mock_verks):
        """Test KeyStore().delete() delete credential for url from file."""
        self._init()
        udocker.Config = mock_config
        udocker.Config.tmpdir = "/tmp"
        mock_readall.return_value = self.credentials
        kstore = udocker.KeyStore("filename")
        kstore.delete(self.url)
        mock_writeall.assert_called_once_with({})

        mock_verks.side_effect = KeyError
        self.assertFalse(kstore.delete(self.url))

    @mock.patch('udocker.Config')
    @mock.patch('udocker.KeyStore._verify_keystore')
    @mock.patch('udocker.os.unlink')
    @mock.patch('udocker.KeyStore._shred')
    def test_07_erase(self, mock_shred, mock_unlink,
                      mock_config, mock_verks):
        """Test KeyStore().erase() erase credentials file."""
        self._init()
        udocker.Config = mock_config
        udocker.Config.tmpdir = "/tmp"
        kstore = udocker.KeyStore("filename")
        self.assertTrue(kstore.erase())
        mock_unlink.assert_called_once_with("filename")

        mock_unlink.side_effect = IOError
        self.assertFalse(kstore.erase())


class UniqueTestCase(unittest.TestCase):
    """Test Unique() class."""

    @classmethod
    def setUpClass(cls):
        """Setup test."""
        set_env()

    def test_01_init(self):
        """Test Unique() constructor."""
        uniq = udocker.Unique()
        self.assertEqual(uniq.def_name, "udocker")

    def test_02__rnd(self):
        """Test Unique._rnd()."""
        uniq = udocker.Unique()
        rand = uniq._rnd(64)
        self.assertIsInstance(rand, str)
        self.assertEqual(len(rand), 64)

    def test_03_uuid(self):
        """Test Unique.uuid()."""
        uniq = udocker.Unique()
        rand = uniq.uuid("zxcvbnm")
        self.assertEqual(len(rand), 36)
        rand = uniq.uuid(789)
        self.assertEqual(len(rand), 36)

    def test_04_imagename(self):
        """Test Unique.imagename()."""
        uniq = udocker.Unique()
        rand = uniq.imagename()
        self.assertEqual(len(rand), 16)

    def test_05_layer_v1(self):
        """Test Unique.layer_v1()."""
        uniq = udocker.Unique()
        rand = uniq.layer_v1()
        self.assertEqual(len(rand), 64)

    def test_06_filename(self):
        """Test Unique.filename()."""
        uniq = udocker.Unique()
        rand = uniq.filename("zxcvbnmasdf")
        self.assertTrue(rand.endswith("zxcvbnmasdf"))
        self.assertTrue(rand.startswith("udocker"))
        self.assertGreater(len(rand.strip()), 56)
        rand = uniq.filename(12345)
        self.assertTrue(rand.endswith("12345"))
        self.assertTrue(rand.startswith("udocker"))
        self.assertGreater(len(rand.strip()), 50)


class FileUtilTestCase(unittest.TestCase):
    """Test FileUtil() file manipulation methods."""

    @classmethod
    def setUpClass(cls):
        """Setup test."""
        set_env()

    @mock.patch('udocker.Config')
    def test_01_init(self, mock_config):
        """Test FileUtil() constructor."""
        udocker.Config = mock_config
        udocker.Config.tmpdir = "/tmp"
        futil = udocker.FileUtil("filename.txt")
        self.assertEqual(futil.filename, os.path.abspath("filename.txt"))
        self.assertTrue(udocker.Config.tmpdir)

        mock_config.side_effect = AttributeError("abc")
        futil = udocker.FileUtil()
        self.assertEqual(futil.filename, None)

    def test_02_mktmp(self):
        """Test FileUtil.mktmp()."""
        udocker.Config.tmpdir = "/somewhere"
        tmp_file = udocker.FileUtil("filename2.txt").mktmp()
        self.assertTrue(tmp_file.endswith("-filename2.txt"))
        self.assertTrue(tmp_file.startswith("/somewhere/udocker-"))
        self.assertGreater(len(tmp_file.strip()), 68)

    @mock.patch('udocker.os.stat')
    def test_03_uid(self, mock_stat):
        """Test FileUtil.uid()."""
        mock_stat.return_value.st_uid = 1234
        uid = udocker.FileUtil("filename3.txt").uid()
        self.assertEqual(uid, 1234)

    @mock.patch('udocker.Config')
    @mock.patch('udocker.os.path.realpath')
    @mock.patch('udocker.os.path.exists')
    @mock.patch('udocker.Msg')
    @mock.patch('udocker.os.remove')
    @mock.patch('udocker.os.path.islink')
    @mock.patch('udocker.os.path.isfile')
    @mock.patch('udocker.os.path.isdir')
    @mock.patch('udocker.FileUtil.uid')
    @mock.patch('udocker.FileUtil._is_safe_prefix')
    def test_04_remove_file(self, mock_safe, mock_uid, mock_isdir,
                            mock_isfile, mock_islink, mock_remove, mock_msg,
                            mock_exists, mock_realpath, mock_config):
        """Test FileUtil.remove() with plain files."""
        mock_uid.return_value = os.getuid()
        # file does not exist (regression of #50)
        mock_isdir.return_value = True
        mock_isfile.return_value = True
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
    @mock.patch('udocker.Msg')
    @mock.patch('udocker.subprocess.call')
    @mock.patch('udocker.os.path.isdir')
    @mock.patch('udocker.os.path.islink')
    @mock.patch('udocker.os.path.isfile')
    @mock.patch('udocker.FileUtil.uid')
    @mock.patch('udocker.FileUtil._is_safe_prefix')
    def test_05_remove_dir(self, mock_safe, mock_uid, mock_isfile,
                           mock_islink, mock_isdir, mock_call,
                           mock_msg, mock_exists, mock_config):
        """Test FileUtil.remove() with directories."""
        mock_uid.return_value = os.getuid()
        mock_isfile.return_value = False
        mock_islink.return_value = False
        mock_isdir.return_value = True
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
        mock_call.return_value = 1
        futil = udocker.FileUtil("/tmp/directory")
        status = futil.remove()
        self.assertFalse(status)

    @mock.patch('udocker.Msg')
    @mock.patch('udocker.subprocess.call')
    @mock.patch('udocker.os.path.isfile')
    def test_06_verify_tar01(self, mock_isfile, mock_call, mock_msg):
        """Test FileUtil.verify_tar() check tar file."""
        mock_msg.level = 0
        mock_isfile.return_value = False
        mock_call.return_value = 0
        status = udocker.FileUtil("tarball.tar").verify_tar()
        self.assertFalse(status)

    @mock.patch('udocker.Msg')
    @mock.patch('udocker.subprocess.call')
    @mock.patch('udocker.os.path.isfile')
    def test_07_verify_tar02(self, mock_isfile, mock_call, mock_msg):
        """Test FileUtil.verify_tar() check tar file."""
        mock_msg.level = 0
        mock_isfile.return_value = True
        mock_call.return_value = 0
        status = udocker.FileUtil("tarball.tar").verify_tar()
        self.assertTrue(status)

    @mock.patch('udocker.Msg')
    @mock.patch('udocker.subprocess.call')
    @mock.patch('udocker.os.path.isfile')
    def test_08_verify_tar03(self, mock_isfile, mock_call, mock_msg):
        """Test FileUtil.verify_tar() check tar file."""
        mock_msg.level = 0
        mock_isfile.return_value = True
        mock_call.return_value = 1
        status = udocker.FileUtil("tarball.tar").verify_tar()
        self.assertFalse(status)

    @mock.patch('udocker.Config')
    @mock.patch('udocker.FileUtil.remove')
    def test_09_cleanup(self, mock_remove, mock_config):
        """Test FileUtil.cleanup() delete tmp files."""
        udocker.Config = mock_config
        udocker.Config.tmpdir = "/tmp"
        udocker.FileUtil.tmptrash = {'file1.txt': None, 'file2.txt': None}
        udocker.FileUtil("").cleanup()
        self.assertEqual(mock_remove.call_count, 2)

    @mock.patch('udocker.os.path.isdir')
    def test_10_isdir(self, mock_isdir):
        """Test FileUtil.isdir()."""
        mock_isdir.return_value = True
        status = udocker.FileUtil("somedir").isdir()
        self.assertTrue(status)
        mock_isdir.return_value = False
        status = udocker.FileUtil("somedir").isdir()
        self.assertFalse(status)

    @mock.patch('udocker.os.stat')
    def test_11_size(self, mock_stat):
        """Test FileUtil.size() get file size."""
        mock_stat.return_value.st_size = 4321
        size = udocker.FileUtil("somefile").size()
        self.assertEqual(size, 4321)

    def test_12_getdata(self):
        """Test FileUtil.size() get file content."""
        with mock.patch(BUILTINS + '.open',
                        mock.mock_open(read_data='qwerty')):
            data = udocker.FileUtil("somefile").getdata()
            self.assertEqual(data, 'qwerty')

    @mock.patch('udocker.Uprocess')
    def test_13_find_exec(self, mock_call):
        """Test FileUtil.find_exec() find executable."""
        mock_call.return_value.get_output.return_value = None
        filename = udocker.FileUtil("executable").find_exec()
        self.assertEqual(filename, "")
        #
        mock_call.return_value.get_output.return_value = "/bin/ls"
        filename = udocker.FileUtil("executable").find_exec()
        self.assertEqual(filename, "/bin/ls")
        #
        mock_call.return_value.get_output.return_value = "not found"
        filename = udocker.FileUtil("executable").find_exec()
        self.assertEqual(filename, "")

    @mock.patch('udocker.os.path.lexists')
    def test_14_find_inpath(self, mock_exists):
        """Test FileUtil.find_inpath() file is in a path."""
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

    def test_15_copyto(self):
        """Test FileUtil.copyto() file copy."""
        with mock.patch(BUILTINS + '.open', mock.mock_open()):
            status = udocker.FileUtil("source").copyto("dest")
            self.assertTrue(status)
            status = udocker.FileUtil("source").copyto("dest", "w")
            self.assertTrue(status)
            status = udocker.FileUtil("source").copyto("dest", "a")
            self.assertTrue(status)

    @mock.patch('udocker.os.makedirs')
    @mock.patch('udocker.FileUtil')
    def test_16_mkdir(self, mock_mkdirs, mock_futil):
        """Create directory"""
        mock_mkdirs.return_value = True
        status = mock_futil.mkdir()
        self.assertTrue(status)

        mock_mkdirs.side_effect = OSError("fail")
        status = mock_futil.mkdir()
        self.assertTrue(status)

    @mock.patch('udocker.os.umask')
    def test_17_umask(self, mock_umask):
        """Test FileUtil.umask()."""
        mock_umask.return_value = 0
        futil = udocker.FileUtil("somedir")
        status = futil.umask()
        self.assertTrue(status)
        #
        mock_umask.return_value = 0
        futil = udocker.FileUtil("somedir")
        udocker.FileUtil.orig_umask = 0
        status = futil.umask(1)
        self.assertTrue(status)
        self.assertEqual(udocker.FileUtil.orig_umask, 0)
        #
        mock_umask.return_value = 0
        futil = udocker.FileUtil("somedir")
        udocker.FileUtil.orig_umask = None
        status = futil.umask(1)
        self.assertTrue(status)
        self.assertEqual(udocker.FileUtil.orig_umask, 0)

    @mock.patch('udocker.FileUtil.mktmp')
    @mock.patch('udocker.FileUtil.mkdir')
    def test_18_mktmpdir(self, mock_umkdir, mock_umktmp):
        """Test FileUtil.mktmpdir()."""
        mock_umktmp.return_value = "/dir"
        mock_umkdir.return_value = True
        futil = udocker.FileUtil("somedir")
        status = futil.mktmpdir()
        self.assertEqual(status, "/dir")
        #
        mock_umktmp.return_value = "/dir"
        mock_umkdir.return_value = False
        futil = udocker.FileUtil("somedir")
        status = futil.mktmpdir()
        self.assertEqual(status, None)

    @mock.patch('udocker.FileUtil.mktmp')
    @mock.patch('udocker.FileUtil.mkdir')
    def test_19__is_safe_prefix(self, mock_umkdir, mock_umktmp):
        """Test FileUtil._is_safe_prefix()."""
        futil = udocker.FileUtil("somedir")
        udocker.FileUtil.safe_prefixes = []
        status = futil._is_safe_prefix("/AAA")
        self.assertFalse(status)
        #
        futil = udocker.FileUtil("somedir")
        udocker.FileUtil.safe_prefixes = ["/AAA", ]
        status = futil._is_safe_prefix("/AAA")
        self.assertTrue(status)

    def test_20_putdata(self):
        """Test FileUtil.putdata()"""
        futil = udocker.FileUtil("somefile")
        futil.filename = ""
        data = futil.putdata("qwerty")
        self.assertFalse(data)
        #
        with mock.patch(BUILTINS + '.open',
                        mock.mock_open()):
            data = udocker.FileUtil("somefile").putdata("qwerty")
            self.assertEqual(data, 'qwerty')

    @mock.patch('udocker.os.rename')
    def test_21_rename(self, mock_rename):
        """Test FileUtil.rename()."""
        status = udocker.FileUtil("somefile").rename("otherfile")
        self.assertTrue(status)

    @mock.patch('udocker.os.path.exists')
    def test_22_find_file_in_dir(self, mock_exists):
        """Test FileUtil.find_file_in_dir()."""
        file_list = []
        status = udocker.FileUtil("/dir").find_file_in_dir(file_list)
        self.assertEqual(status, "")
        #
        file_list = ["F1", "F2"]
        mock_exists.side_effect = [False, False]
        status = udocker.FileUtil("/dir").find_file_in_dir(file_list)
        self.assertEqual(status, "")
        #
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
    def test_23__link_change_apply(self, mock_readlink,
                                   mock_realpath, mock_dirname,
                                   mock_access, mock_chmod, mock_stat,
                                   mock_remove, mock_symlink):
        """Actually apply the link convertion."""
        mock_readlink.return_value = "/HOST/DIR"
        mock_realpath.return_value = "/HOST/DIR"
        mock_access.return_value = True
        udocker.FileUtil("/con").\
            _link_change_apply("/con/lnk_new", "/con/lnk", False)
        self.assertTrue(mock_remove.called)
        self.assertTrue(mock_symlink.called)

        mock_access.return_value = False
        mock_remove.reset_mock()
        mock_symlink.reset_mock()
        udocker.FileUtil("/con").\
            _link_change_apply("/con/lnk_new", "/con/lnk", True)
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
    def test_24__link_set(self, mock_readlink, mock_realpath, mock_dirname,
                          mock_access, mock_chmod, mock_stat, mock_remove,
                          mock_symlink):
        """Test FileUtil._link_set()."""
        mock_readlink.return_value = "X"
        status = udocker.FileUtil("/con")._link_set("/con/lnk", "", "/con", False)
        self.assertFalse(status)
        #
        mock_readlink.return_value = "/con"
        status = udocker.FileUtil("/con")._link_set("/con/lnk", "", "/con", False)
        self.assertFalse(status)
        #
        mock_readlink.return_value = "/HOST/DIR"
        mock_realpath.return_value = "/HOST/DIR"
        mock_remove.reset_mock()
        mock_symlink.reset_mock()
        mock_chmod.reset_mock()
        status = udocker.FileUtil("/con")._link_set("/con/lnk", "", "/con", False)
        self.assertTrue(mock_remove.called)
        self.assertTrue(mock_symlink.called)
        self.assertFalse(mock_chmod.called)
        self.assertTrue(status)
        #
        mock_readlink.return_value = "/HOST/DIR"
        mock_realpath.return_value = "/HOST/DIR"
        mock_access.return_value = True
        mock_remove.reset_mock()
        mock_symlink.reset_mock()
        mock_chmod.reset_mock()
        status = udocker.FileUtil("/con")._link_set("/con/lnk", "", "/con", True)
        self.assertTrue(mock_remove.called)
        self.assertTrue(mock_symlink.called)
        self.assertFalse(mock_chmod.called)
        self.assertTrue(status)
        #
        mock_readlink.return_value = "/HOST/DIR"
        mock_realpath.return_value = "/HOST/DIR"
        mock_access.return_value = False
        mock_remove.reset_mock()
        mock_symlink.reset_mock()
        mock_chmod.reset_mock()
        status = udocker.FileUtil("/con")._link_set("/con/lnk", "", "/con", True)
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
    def test_25__link_restore(self, mock_readlink, mock_realpath, mock_dirname,
                              mock_access, mock_chmod, mock_stat, mock_remove,
                              mock_symlink):
        """Test FileUtil._link_restore()."""
        mock_readlink.return_value = "/con/AAA"
        status = udocker.FileUtil("/con")._link_restore("/con/lnk", "/con",
                                                        "/root", False)
        self.assertTrue(status)
        #
        mock_readlink.return_value = "/con/AAA"
        mock_symlink.reset_mock()
        mock_chmod.reset_mock()
        status = udocker.FileUtil("/con")._link_restore("/con/lnk", "/con",
                                                        "/root", False)
        self.assertTrue(status)
        self.assertTrue(mock_symlink.called_with("/con/lnk", "/AAA"))
        #
        mock_readlink.return_value = "/root/BBB"
        mock_symlink.reset_mock()
        mock_chmod.reset_mock()
        status = udocker.FileUtil("/con")._link_restore("/con/lnk", "/con",
                                                        "/root", False)
        self.assertTrue(status)
        self.assertTrue(mock_symlink.called_with("/con/lnk", "/BBB"))
        #
        mock_readlink.return_value = "/XXX"
        status = udocker.FileUtil("/con")._link_restore("/con/lnk", "/con",
                                                        "/root", False)
        self.assertFalse(status)
        #
        mock_readlink.return_value = "/root/BBB"
        mock_symlink.reset_mock()
        mock_chmod.reset_mock()
        status = udocker.FileUtil("/con")._link_restore("/con/lnk", "/con",
                                                        "/root", True)
        self.assertTrue(status)
        self.assertTrue(mock_symlink.called_with("/con/lnk", "/BBB"))
        self.assertFalse(mock_chmod.called)
        #
        mock_readlink.return_value = "/root/BBB"
        mock_access.return_value = False
        mock_symlink.reset_mock()
        mock_chmod.reset_mock()
        status = udocker.FileUtil("/con")._link_restore("/con/lnk", "",
                                                        "/root", True)
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
    def test_26_links_conv(self, mock_realpath, mock_walk, mock_islink,
                           mock_lstat, mock_is_safe_prefix, mock_msg,
                           mock_link_set, mock_link_restore):
        """Test FileUtil.links_conv()."""
        mock_realpath.return_value = "/ROOT"
        mock_is_safe_prefix.return_value = False
        status = udocker.FileUtil("/ROOT").links_conv(False, True, "")
        self.assertEqual(status, None)
        #
        mock_realpath.return_value = "/ROOT"
        mock_is_safe_prefix.return_value = True
        mock_walk.return_value = []
        status = udocker.FileUtil("/ROOT").links_conv(False, True, "")
        self.assertEqual(status, [])
        #
        mock_realpath.return_value = "/ROOT"
        mock_is_safe_prefix.return_value = True
        mock_walk.return_value = [("/", [], []), ]
        status = udocker.FileUtil("/ROOT").links_conv(False, True, "")
        self.assertEqual(status, [])
        #
        mock_realpath.return_value = "/ROOT"
        mock_is_safe_prefix.return_value = True
        mock_islink = False
        mock_walk.return_value = [("/", [], ["F1", "F2"]), ]
        status = udocker.FileUtil("/ROOT").links_conv(False, True, "")
        self.assertEqual(status, [])
        #
        mock_realpath.return_value = "/ROOT"
        mock_is_safe_prefix.return_value = True
        mock_islink = True
        mock_lstat.return_value.st_uid = 1
        udocker.Config.uid = 0
        mock_walk.return_value = [("/", [], ["F1", "F2"]), ]
        status = udocker.FileUtil("/ROOT").links_conv(False, True, "")
        self.assertEqual(status, [])
        #
        mock_realpath.return_value = "/ROOT"
        mock_is_safe_prefix.return_value = True
        mock_islink = True
        mock_lstat.return_value.st_uid = 1
        mock_link_set.reset_mock()
        mock_link_restore.reset_mock()
        udocker.Config.uid = 1
        mock_walk.return_value = [("/", [], ["F1", "F2"]), ]
        status = udocker.FileUtil("/ROOT").links_conv(False, True, "")
        self.assertTrue(mock_link_set.called)
        self.assertFalse(mock_link_restore.called)
        #
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
        self.assertTrue(mock_link_restore.called)


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
        """Test UdockerTools() constructor."""
        udocker.Config = mock_config
        udocker.Config.tmpdir = "/tmp"
        udocker.Config.tarball = "/tmp/xxx"
        udocker.Config.installinfo = "/tmp/xxx"
        udocker.Config._tarball_release = "0.0.0"
        localrepo = mock_localrepo
        localrepo.bindir = "/bindir"
        utools = udocker.UdockerTools(localrepo)
        self.assertEqual(utools.localrepo, localrepo)

    @mock.patch('udocker.LocalRepository')
    @mock.patch('udocker.FileUtil')
    def test_02__version_isequal(self, futil, mock_localrepo):
        """Test UdockerTools._version_isequal()."""
        futil.return_value.getdata.return_value = "0.0.0"
        utools = udocker.UdockerTools(mock_localrepo)
        utools._tarball_release = "0.0.0"
        status = utools._version_isequal("versionfile")
        self.assertTrue(status)
        #
        futil.return_value.getdata.return_value = "0.0.0"
        utools = udocker.UdockerTools(mock_localrepo)
        utools._tarball_release = "1.1.1"
        status = utools._version_isequal("versionfile")
        self.assertFalse(status)

    @mock.patch('udocker.UdockerTools._version_isequal')
    @mock.patch('udocker.LocalRepository')
    def test_02_is_available(self, mock_localrepo, mock_version_isequal):
        """Test UdockerTools.is_available()."""
        mock_version_isequal.return_value = False
        utools = udocker.UdockerTools(mock_localrepo)
        status = utools.is_available()
        self.assertFalse(status)
        #
        mock_version_isequal.return_value = True
        utools = udocker.UdockerTools(mock_localrepo)
        status = utools.is_available()
        self.assertTrue(status)

    @mock.patch('udocker.os.path.isfile')
    @mock.patch('udocker.os.path.exists')
    @mock.patch('udocker.Msg')
    @mock.patch('udocker.LocalRepository')
    @mock.patch('udocker.UdockerTools.__init__')
    @mock.patch('udocker.FileUtil')
    @mock.patch('udocker.GetURL')
    @mock.patch.object(udocker.UdockerTools, '_install')
    @mock.patch.object(udocker.UdockerTools, '_verify_version')
    @mock.patch.object(udocker.UdockerTools, '_instructions')
    @mock.patch.object(udocker.UdockerTools, '_download')
    @mock.patch.object(udocker.UdockerTools, 'is_available')
    def test_03__install(self, mock_is, mock_down, mock_instr, mock_ver,
                         mock_install, mock_geturl, mock_futil, mock_init,
                         mock_localrepo, mock_msg, mock_exists, mock_isfile):
        """Test UdockerTools.install()"""
        mock_msg.level = 0
        mock_futil.return_value.mktmp.return_value = "filename_tmp"
        mock_init.return_value = None
        utools = udocker.UdockerTools(mock_localrepo)
        utools.localrepo = mock_localrepo
        utools.curl = mock_geturl
        utools.localrepo.topdir = "/home/user/.udocker"
        udocker.CurlHeader()
        # IS AVAILABLE NO DOWNLOAD
        mock_is.return_value = True
        status = utools.install()
        self.assertTrue(status)
        # NO AUTOINSTALL
        mock_is.return_value = False
        utools._tarball = "http://node.domain/filename.tgz"
        utools._tarball_release = udocker.Config.tarball_version
        utools._autoinstall = False
        status = utools.install()
        self.assertEqual(status, None)
        # NO TARBALL
        mock_is.return_value = False
        utools._tarball = ""
        utools._autoinstall = True
        status = utools.install()
        self.assertFalse(status)
        # _download fails
        mock_instr.reset_mock()
        mock_is.return_value = False
        utools._tarball = "http://node.domain/filename.tgz"
        utools._tarball_release = udocker.Config.tarball_version
        mock_down.return_value = ""
        status = utools.install()
        self.assertTrue(mock_instr.called)
        self.assertFalse(status)
        # _download ok _verify_version fails
        mock_instr.reset_mock()
        mock_is.return_value = False
        utools._tarball = "http://node.domain/filename.tgz"
        utools._tarball_release = udocker.Config.tarball_version
        mock_down.return_value = "filename.tgz"
        mock_ver.return_value = False
        mock_isfile.return_value = False
        status = utools.install()
        #self.assertTrue(mock_instr.called)
        #self.assertTrue(mock_futil.return_value.remove.called)
        self.assertFalse(status)
        # _download ok _verify_version ok install ok
        mock_instr.reset_mock()
        mock_is.return_value = False
        utools._tarball = "http://node.domain/filename.tgz"
        utools._tarball_release = udocker.Config.tarball_version
        utools._installinfo = "installinfo.txt"
        utools._install_json = dict()
        mock_down.return_value = "filename.tgz"
        mock_ver.return_value = True
        mock_install.return_value = True
        mock_isfile.return_value = True
        status = utools.install()
        self.assertTrue(mock_install.called)
        self.assertTrue(status)
        # _download ok _verify_version ok install fail
        mock_instr.reset_mock()
        mock_is.return_value = False
        utools._tarball = "http://node.domain/filename.tgz"
        utools._tarball_release = udocker.Config.tarball_version
        utools._installinfo = "installinfo.txt"
        utools._install_json = dict()
        mock_down.return_value = "filename.tgz"
        mock_ver.return_value = True
        mock_install.return_value = False
        status = utools.install()
        self.assertTrue(mock_install.called)
        self.assertTrue(mock_instr.called)
        self.assertTrue(mock_futil.return_value.remove.called)
        self.assertFalse(status)
        # file not exists no download
        mock_instr.reset_mock()
        mock_is.return_value = False
        mock_exists.return_value = False
        utools._install_json = dict()
        utools._tarball = "filename.tgz"
        utools._tarball_release = udocker.Config.tarball_version
        utools._installinfo = "installinfo.txt"
        utools._tarball_file = ""
        status = utools.install()
        self.assertTrue(mock_instr.called)
        self.assertFalse(mock_futil.remove.called)
        self.assertFalse(status)

    @mock.patch('udocker.GetURL')
    @mock.patch('udocker.FileUtil')
    @mock.patch('udocker.UdockerTools.__init__')
    def test_04__download(self, mock_init, mock_futil, mock_gurl):
        """Test UdockerTools.download()."""
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
        #
        hdr.data["X-ND-HTTPSTATUS"] = "400"
        hdr.data["X-ND-CURLSTATUS"] = 1
        status = utools._download(utools._tarball)
        self.assertEqual(status, "")

    @mock.patch('udocker.os.path.isfile')
    @mock.patch('udocker.UdockerTools._version_isequal')
    @mock.patch('udocker.Msg')
    @mock.patch('udocker.subprocess.call')
    @mock.patch('udocker.FileUtil')
    @mock.patch('udocker.UdockerTools.__init__')
    def test_04__verify_version(self, mock_init, mock_futil, mock_call,
                                mock_msg, mock_versioneq, mock_isfile):
        """Test UdockerTools._verify_version()."""
        mock_init.return_value = None
        mock_isfile.return_value = False
        utools = udocker.UdockerTools(None)
        mock_futil.return_value.mktmp.return_value = ""
        status = utools._verify_version("tarballfile")
        self.assertFalse(status)
        #
        mock_msg.level = 0
        mock_call.return_value = 1
        mock_isfile.return_value = True
        status = utools._verify_version("tarballfile")
        self.assertFalse(status)
        #
        mock_call.return_value = 0
        mock_versioneq.return_value = False
        mock_isfile.return_value = True
        status = utools._verify_version("tarballfile")
        self.assertFalse(status)
        #
        mock_call.return_value = 0
        mock_versioneq.return_value = True
        mock_isfile.return_value = True
        status = utools._verify_version("tarballfile")
        self.assertTrue(status)

    @mock.patch('udocker.os.path.isfile')
    @mock.patch('udocker.UdockerTools._install')
    @mock.patch('udocker.UdockerTools._verify_version')
    @mock.patch('udocker.LocalRepository')
    @mock.patch('udocker.Msg')
    @mock.patch('udocker.subprocess.call')
    @mock.patch('udocker.UdockerTools.__init__')
    def test_04__install(self, mock_init, mock_call, mock_msg, mock_local,
                         mock_ver_version, mock_ins, mock_isfile):
        """Test UdockerTools._install()."""
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
        #
        mock_call.return_value = 0
        mock_ver_version.return_value = True
        mock_ins.return_value = True
        mock_isfile.return_value = True
        status = utools._install("tarballfile")
        self.assertTrue(status)

    @mock.patch('udocker.FileUtil')
    @mock.patch('udocker.os.listdir')
    @mock.patch('udocker.LocalRepository')
    def test_05_purge(self, mock_localrepo, mock_listdir, mock_futil):
        """Test UdockerTools.purge()."""
        mock_listdir.return_value = []
        utools = udocker.UdockerTools(mock_localrepo)
        utools.purge()
        self.assertFalse(mock_futil.return_value.remove.called)
        #
        mock_listdir.return_value = ["F1", "F2"]
        utools = udocker.UdockerTools(mock_localrepo)
        utools.purge()
        self.assertTrue(mock_futil.return_value.remove.called)

    @mock.patch('udocker.Msg')
    @mock.patch('udocker.LocalRepository')
    def test_06__instructions(self, mock_localrepo, mock_msg):
        """Test UdockerTools._instructions()."""
        utools = udocker.UdockerTools(mock_localrepo)
        utools._instructions()
        self.assertTrue(mock_msg.return_value.out.called)


class ElfPatcherTestCase(unittest.TestCase):
    """."""

    @classmethod
    def setUpClass(cls):
        """Setup test."""
        set_env()

    def _init(self):
        """."""
        pass

    @mock.patch('udocker.Msg')
    @mock.patch('udocker.os.path')
    @mock.patch('udocker.Config')
    @mock.patch('udocker.FileUtil')
    @mock.patch('udocker.LocalRepository')
    def test_02_select_patchelf(self, mock_local, mock_futil,
                                mock_conf, mock_path, mock_msg):
        """Test ElfPatcher().select_patchelf().

        Set patchelf executable."""
        container_id = "SOME-RANDOM-ID"
        self._init()

        mock_conf.return_value.arch.side_effect = ["arm", "amd64", "i386", "arm64"]
        mock_futil.return_value.find_file_in_dir.return_value = "runc-arm"
        elfp = udocker.ElfPatcher(mock_local, container_id)
        output = elfp.select_patchelf()
        self.assertEqual(output, "runc-arm")

        mock_futil.return_value.find_file_in_dir.return_value = ""
        elfp = udocker.ElfPatcher(mock_local, container_id)
        with self.assertRaises(SystemExit) as epexpt:
            elfp.select_patchelf()
        self.assertEqual(epexpt.exception.code, 1)

    @mock.patch('udocker.os.path.islink')
    @mock.patch('udocker.os.path.stat')
    @mock.patch('udocker.os.path')
    @mock.patch('udocker.os.walk')
    @mock.patch('udocker.os.access')
    @mock.patch('udocker.LocalRepository')
    def test_03__walk_fs(self, mock_local, mock_access, mock_walk,
                         mock_path, mock_stat, mock_islink):
        """Test ElfPatcher()._walk_fs().

        Execute a shell command over each executable file in a given dir_path.
        Action can be ABORT_ON_ERROR, return upon first success
        ONE_SUCCESS, or return upon the first non empty output. #f is the
        placeholder for the filename.
        """
        # self._init()
        # container_id = "SOME-RANDOM-ID"
        # elfp = udocker.ElfPatcher(mock_local, container_id)
        #
        # mock_walk.return_value = ("/tmp", ["dir"], ["file"]);
        # mock_islink.return_value = False
        # mock_stat.return_value.st_uid = ""
        # status = elfp._walk_fs("cmd", "/tmp", elfp.BIN)
        # self.assertIsNone(status)
        pass

    @mock.patch('udocker.os.path')
    @mock.patch('udocker.LocalRepository')
    @mock.patch('udocker.ElfPatcher._walk_fs')
    @mock.patch('udocker.ElfPatcher.select_patchelf')
    def test_04_guess_elf_loader(self, mock_spelf, mock_walk,
                                 mock_local, mock_path):
        """Test ElfPatcher().guess_elf_loader().

        Search for executables and try to read the ld.so pathname."""
        self._init()
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
    def test_05_get_original_loader(self, mock_guess, mock_futils,
                                    mock_local, mock_exists, mock_path):
        """Test ElfPatcher().get_original_loader().

        Get the pathname of the original ld.so.
        """
        self._init()
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
    def test_06_get_container_loader(self, mock_gol, mock_local,
                                     mock_exists, mock_path):
        """Test ElfPatcher().get_container_loader().

        Get an absolute pathname to the container ld.so"""
        self._init()
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
    def test_07_get_patch_last_path(self, mock_getdata, mock_local,
                                    mock_exists, mock_path):
        """Test ElfPatcher().get_patch_last_path().

        get last host pathname to the patched container."""
        self._init()
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
    def test_08_check_container(self, mock_msg, mock_lpath,
                                mock_local, mock_exists, mock_path):
        """Test ElfPatcher().check_container().

        verify if path to container is ok"""
        self._init()
        container_id = "SOME-RANDOM-ID"
        mock_lpath.return_value = "/tmp"
        elfp = udocker.ElfPatcher(mock_local, container_id)
        # with self.assertRaises(SystemExit) as epexpt:
        #     elfp.check_container()
        # self.assertEqual(epexpt.exception.code, 1)

    @mock.patch('udocker.os.path')
    @mock.patch('udocker.os.path.exists')
    @mock.patch('udocker.LocalRepository')
    @mock.patch('udocker.FileUtil.getdata')
    def test_09_get_patch_last_time(self, mock_getdata, mock_local,
                                    mock_exists, mock_path):
        """Test ElfPatcher().patch_last_time().

        get time in seconds of last full patch of container"""
        self._init()
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
    def test_10_patch_binaries(self, mock_elfp, mock_gcl, mock_select,
                               mock_guess, mock_putdata, mock_local,
                               mock_exists, mock_path):
        """Test ElfPatcher().patch_binaries().

        Set all executables and libs to the ld.so absolute pathname"""
        self._init()
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
    def test_11_restore_binaries(self, mock_elfp, mock_gcl, mock_select,
                                 mock_guess, mock_local,
                                 mock_exists, mock_path):
        """Test ElfPatcher().restore_binaries().

        Restore all executables and libs to the original ld.so pathname"""
        self._init()
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
    def test_12_patch_ld(self, mock_getdata,
                         mock_copyto, mock_size,
                         mock_gcl, mock_local,
                         mock_exists, mock_path):
        """Test ElfPatcher().patch_ld().

        Patch ld.so"""
        self._init()
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
    def test_13_restore_ld(self, mock_copyto, mock_size,
                           mock_gcl, mock_local,
                           mock_exists, mock_path, mock_msg):
        """Test ElfPatcher().restore_ld().

        Restore ld.so"""
        self._init()
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
    def test_14__get_ld_config(self, mock_upout,
                               mock_local, mock_exists, mock_path):
        """Test ElfPatcher().get_ld_config().

        Get get directories from container ld.so.cache"""
        self._init()
        container_id = "SOME-RANDOM-ID"
        mock_upout.return_value = []
        elfp = udocker.ElfPatcher(mock_local, container_id)
        status = elfp._get_ld_config()
        self.assertEqual(status, [])

        # mock_upout.return_value = \
        #     "ld.so.cache => /tmp/ROOT/etc/ld.so.cache\n" \
        #     "ld.so.cache => /tmp/ROOT/etc/ld.so"
        # elfp = udocker.ElfPatcher(mock_local, container_id)
        # status = elfp._get_ld_config()
        # self.assertIsInstance(status, list)

    @mock.patch('udocker.os.path')
    @mock.patch('udocker.os.access')
    @mock.patch('udocker.os.walk')
    @mock.patch('udocker.os.path.exists')
    @mock.patch('udocker.LocalRepository')
    def test_15__find_ld_libdirs(self, mock_local, mock_exists,
                                 mock_walk, mock_access, mock_path):
        """Test ElfPatcher()._find_ld_libdirs().

        search for library directories in container"""
        self._init()
        container_id = "SOME-RANDOM-ID"

        elfp = udocker.ElfPatcher(mock_local, container_id)
        status = elfp._find_ld_libdirs()
        self.assertEqual(status, [])

    @mock.patch('udocker.os.path')
    @mock.patch('udocker.os.path.exists')
    @mock.patch('udocker.LocalRepository')
    def test_16_get_ld_libdirs(self, mock_local,
                               mock_exists, mock_path):
        """Test ElfPatcher().get_ld_libdirs().

        Get ld library paths"""
        self._init()
        container_id = "SOME-RANDOM-ID"

        elfp = udocker.ElfPatcher(mock_local, container_id)
        status = elfp.get_ld_libdirs()
        self.assertEqual(status, [''])

    @mock.patch('udocker.os.path')
    @mock.patch('udocker.os.path.exists')
    @mock.patch('udocker.LocalRepository')
    def test_17_get_ld_library_path(self, mock_local,
                                    mock_exists, mock_path):
        """Test ElfPatcher().get_ld_library_path().

        Get ld library paths"""
        self._init()
        container_id = "SOME-RANDOM-ID"

        elfp = udocker.ElfPatcher(mock_local, container_id)
        # status = elfp.get_ld_library_path()
        # self.assertEqual(status, [''])


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
        """Test LocalRepository() constructor."""
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
        """Test LocalRepository().setup()."""
        localrepo = self._localrepo("XXXX")
        self.assertEqual(os.path.basename(localrepo.topdir), "XXXX")
        localrepo.setup("YYYY")
        self.assertEqual(os.path.basename(localrepo.topdir), "YYYY")

    def test_03_create_repo(self):
        """Test LocalRepository().create_repo()."""
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
        """Test LocalRepository().is_repo()."""
        localrepo = self._localrepo(UDOCKER_TOPDIR)
        subprocess.call(["/bin/rm", "-Rf", localrepo.topdir])
        localrepo.create_repo()
        self.assertTrue(localrepo.is_repo())
        subprocess.call(["/bin/rm", "-Rf", localrepo.topdir])

    def test_05_is_container_id(self):
        """Test LocalRepository().is_container_id."""
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

    def test_06_get_container_name(self):
        """Test LocalRepository().get_container_name()."""
        localrepo = self._localrepo(UDOCKER_TOPDIR)
        mock_isdir = mock.patch('os.path.isdir').start()
        mock_isdir.return_value = True
        mock_listdir = mock.patch('os.listdir').start()
        mock_listdir.return_value = ['LINK']
        mock_islink = mock.patch('os.path.islink').start()
        mock_islink.return_value = True
        mock_readlink = mock.patch('os.readlink').start()
        mock_readlink.return_value = "/a/b/IMAGE:TAG"
        name_list = localrepo.get_container_name("IMAGE:TAG")
        self.assertEqual(name_list, ["LINK"])

    def test_07a_get_containers_list(self):
        """Test LocalRepository().get_containers_list()."""
        localrepo = self._localrepo(UDOCKER_TOPDIR)
        mock_isdir = mock.patch('os.path.isdir').start()
        mock_isdir.return_value = True
        mock_listdir = mock.patch('os.listdir').start()
        mock_listdir.return_value = ['LINK']
        with mock.patch(BUILTINS + '.open',
                        mock.mock_open(read_data='REPONAME')):
            containers_list = localrepo.get_containers_list()
            self.assertEqual(os.path.basename(containers_list[0]), "LINK")

    @mock.patch.object(udocker.LocalRepository, 'get_container_name')
    def test_07b_get_containers_list(self, mock_getname):
        """Test LocalRepository().get_containers_list()."""
        localrepo = self._localrepo(UDOCKER_TOPDIR)
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

    @mock.patch.object(udocker.LocalRepository, 'get_containers_list')
    def test_08_cd_container(self, mock_getlist):
        """Test LocalRepository().cd_container()."""
        localrepo = self._localrepo(UDOCKER_TOPDIR)
        mock_exists = mock.patch('os.path.exists').start()
        mock_exists.return_value = True
        mock_getlist.return_value = [localrepo.containersdir +
                                     "/CONTAINERNAME"]
        container_path = localrepo.cd_container("CONTAINERNAME")
        self.assertEqual(container_path, mock_getlist.return_value[0])

    def test_09_protect_container(self):
        """Test LocalRepository().protect_container()."""
        localrepo = self._localrepo(UDOCKER_TOPDIR)
        with mock.patch(BUILTINS + '.open', mock.mock_open()) as mopen:
            container_id = "d2578feb-acfc-37e0-8561-47335f85e46a"
            localrepo.protect_container(container_id)
            self.assertTrue(mopen.called)
            self.assertEqual(mopen.call_args, mock.call('/PROTECT', 'w'))

    def test_10_isprotected_container(self):
        """Test LocalRepository().isprotected_container()."""
        localrepo = self._localrepo(UDOCKER_TOPDIR)
        with mock.patch('os.path.exists') as mexists:
            container_id = "d2578feb-acfc-37e0-8561-47335f85e46a"
            localrepo.isprotected_container(container_id)
            self.assertTrue(mexists.called)
            self.assertEqual(mexists.call_args, mock.call('/PROTECT'))

    @mock.patch('udocker.LocalRepository.cd_container')
    @mock.patch('udocker.LocalRepository._unprotect')
    def test_11_unprotect_container(self, mock_unprotect, mock_cdcont):
        """Test LocalRepository().isprotected_container()."""
        mock_cdcont.return_value = "/tmp"
        localrepo = self._localrepo(UDOCKER_TOPDIR)
        container_id = "d2578feb-acfc-37e0-8561-47335f85e46a"
        localrepo.unprotect_container(container_id)
        self.assertTrue(mock_unprotect.called)

    def test_12_protect_imagerepo(self):
        """Test LocalRepository().protect_imagerepo()."""
        localrepo = self._localrepo(UDOCKER_TOPDIR)
        with mock.patch(BUILTINS + '.open', mock.mock_open()) as mopen:
            localrepo.protect_imagerepo("IMAGE", "TAG")
            self.assertTrue(mopen.called)
            protect = localrepo.reposdir + "/IMAGE/TAG/PROTECT"
            self.assertEqual(mopen.call_args, mock.call(protect, 'w'))

    def test_13_isprotected_imagerepo(self):
        """Test LocalRepository().isprotected_imagerepo()."""
        localrepo = self._localrepo(UDOCKER_TOPDIR)
        with mock.patch('os.path.exists') as mexists:
            localrepo.isprotected_imagerepo("IMAGE", "TAG")
            self.assertTrue(mexists.called)
            protect = localrepo.reposdir + "/IMAGE/TAG/PROTECT"
            self.assertEqual(mexists.call_args, mock.call(protect))

    @mock.patch('udocker.LocalRepository._unprotect')
    def test_14_unprotect_imagerepo(self, mock_unprotect):
        """Test LocalRepository().unprotected_imagerepo()."""
        localrepo = self._localrepo(UDOCKER_TOPDIR)
        localrepo.unprotect_imagerepo("IMAGE", "TAG")
        self.assertTrue(mock_unprotect.called)

    @mock.patch('udocker.os.access')
    @mock.patch('udocker.os.path.isdir')
    @mock.patch('udocker.os.path.exists')
    @mock.patch.object(udocker.LocalRepository, 'cd_container')
    def test_15_iswriteable_container(self, mock_cd, mock_exists,
                                      mock_isdir, mock_access):
        """Test LocalRepository().iswriteable_container()."""
        localrepo = self._localrepo(UDOCKER_TOPDIR)
        container_id = "d2578feb-acfc-37e0-8561-47335f85e46a"
        mock_exists.return_value = False
        status = localrepo.iswriteable_container(container_id)
        self.assertEqual(status, 2)
        #
        mock_exists.return_value = True
        mock_isdir.return_value = False
        status = localrepo.iswriteable_container(container_id)
        self.assertEqual(status, 3)
        #
        mock_exists.return_value = True
        mock_isdir.return_value = True
        mock_access.return_value = True
        status = localrepo.iswriteable_container(container_id)
        self.assertEqual(status, 1)
        #
        mock_exists.return_value = True
        mock_isdir.return_value = True
        mock_access.return_value = False
        status = localrepo.iswriteable_container(container_id)
        self.assertEqual(status, 0)

    @mock.patch('udocker.LocalRepository._name_is_valid')
    @mock.patch('udocker.Msg')
    @mock.patch('udocker.os.path.exists')
    def test_16_del_container_name(self, mock_exists, mock_msg,
                                   mock_namevalid):
        """Test LocalRepository().del_container_name()."""
        localrepo = self._localrepo(UDOCKER_TOPDIR)
        #
        mock_namevalid.return_value = False
        mock_exists.return_value = True
        udocker.FileUtil.return_value.remove.return_value = True
        status = localrepo.del_container_name("NAMEALIAS")
        self.assertFalse(status)
        #
        mock_namevalid.return_value = True
        mock_exists.return_value = False
        udocker.FileUtil.return_value.remove.return_value = True
        status = localrepo.del_container_name("NAMEALIAS")
        self.assertFalse(status)
        #
        mock_namevalid.return_value = True
        mock_exists.return_value = True
        udocker.FileUtil.return_value.remove.return_value = True
        status = localrepo.del_container_name("NAMEALIAS")
        self.assertTrue(status)
        #
        mock_namevalid.return_value = True
        mock_exists.return_value = True
        udocker.FileUtil.return_value.remove.return_value = False
        status = localrepo.del_container_name("NAMEALIAS")
        self.assertFalse(status)

    @mock.patch('udocker.os.symlink')
    @mock.patch('udocker.os.path.exists')
    def test_17__symlink(self, mock_exists, mock_symlink):
        """Test LocalRepository()._symlink()."""
        localrepo = self._localrepo(UDOCKER_TOPDIR)
        mock_exists.return_value = True
        status = localrepo._symlink("EXISTINGFILE", "LINKFILE")
        self.assertFalse(status)
        #
        mock_exists.return_value = False
        status = localrepo._symlink("EXISTINGFILE", "LINKFILE")
        self.assertTrue(status)

    @mock.patch('udocker.os.path.exists')
    @mock.patch.object(udocker.LocalRepository, '_symlink')
    @mock.patch.object(udocker.LocalRepository, 'cd_container')
    def test_18_set_container_name(self, mock_cd, mock_slink, mock_exists):
        """Test LocalRepository().set_container_name()."""
        localrepo = self._localrepo(UDOCKER_TOPDIR)
        container_id = "d2578feb-acfc-37e0-8561-47335f85e46a"
        status = localrepo.set_container_name(container_id, "WRONG[/")
        self.assertFalse(status)
        #
        mock_cd.return_value = "CONTAINERDIR"
        mock_exists.return_value = True
        status = localrepo.set_container_name(container_id, "RIGHT")
        self.assertFalse(status)
        #
        mock_cd.return_value = "CONTAINERDIR"
        mock_exists.return_value = False
        status = localrepo.set_container_name(container_id, "RIGHT")
        self.assertTrue(status)

    @mock.patch('udocker.os.readlink')
    @mock.patch('udocker.os.path.isdir')
    @mock.patch('udocker.os.path.islink')
    def test_19_get_container_id(self, mock_islink,
                                 mock_isdir, mock_readlink):
        """Test LocalRepository().get_container_id()."""
        localrepo = self._localrepo(UDOCKER_TOPDIR)
        status = localrepo.get_container_id(None)
        self.assertEqual(status, "")
        #
        mock_islink.return_value = True
        mock_readlink.return_value = "BASENAME"
        status = localrepo.get_container_id("ALIASNAM")
        self.assertEqual(status, "BASENAME")
        #
        mock_islink.return_value = False
        mock_isdir.return_value = False
        status = localrepo.get_container_id("ALIASNAM")
        self.assertEqual(status, "")
        #
        mock_islink.return_value = False
        mock_isdir.return_value = True
        status = localrepo.get_container_id("ALIASNAM")
        self.assertEqual(status, "ALIASNAM")

    @mock.patch('udocker.os.makedirs')
    @mock.patch('udocker.os.path.exists')
    def test_20_setup_container(self, mock_exists, mock_makedirs):
        """Test LocalRepository().setup_container()."""
        localrepo = self._localrepo(UDOCKER_TOPDIR)
        mock_exists.return_value = True
        status = localrepo.setup_container("REPO", "TAG", "ID")
        self.assertEqual(status, "")
        #
        mock_exists.return_value = False
        with mock.patch(BUILTINS + '.open', mock.mock_open()):
            status = localrepo.setup_container("REPO", "TAG", "ID")
            self.assertEqual(status, localrepo.containersdir + "/ID")
            self.assertEqual(localrepo.cur_containerdir,
                             localrepo.containersdir + "/ID")

    @mock.patch('udocker.os.readlink')
    @mock.patch('udocker.os.path.islink')
    @mock.patch('udocker.os.listdir')
    @mock.patch.object(udocker.LocalRepository, '_inrepository')
    def test_21__remove_layers(self, mock_in,
                               mock_listdir, mock_islink, mock_readlink):
        """Test LocalRepository()._remove_layers()."""
        localrepo = self._localrepo(UDOCKER_TOPDIR)
        #
        mock_listdir.return_value = []
        status = localrepo._remove_layers("TAG_DIR", False)
        self.assertTrue(status)
        #
        mock_listdir.return_value = ["FILE1,", "FILE2"]
        mock_islink.return_value = False
        status = localrepo._remove_layers("TAG_DIR", False)
        self.assertTrue(status)
        #
        mock_islink.return_value = True
        mock_readlink.return_value = "REALFILE"
        udocker.FileUtil.return_value.remove.return_value = False
        status = localrepo._remove_layers("TAG_DIR", False)
        self.assertFalse(status)
        #
        udocker.FileUtil.return_value.remove.return_value = True
        status = localrepo._remove_layers("TAG_DIR", False)
        self.assertTrue(status)
        #
        udocker.FileUtil.return_value.remove.return_value = True
        status = localrepo._remove_layers("TAG_DIR", True)
        self.assertTrue(status)
        #
        udocker.FileUtil.return_value.remove.return_value = False
        mock_in.return_value = False
        status = localrepo._remove_layers("TAG_DIR", True)
        self.assertTrue(status)
        #
        udocker.FileUtil.return_value.remove.return_value = False
        mock_in.return_value = False
        status = localrepo._remove_layers("TAG_DIR", False)
        self.assertFalse(status)
        #
        udocker.FileUtil.return_value.remove.return_value = False
        mock_in.return_value = True
        status = localrepo._remove_layers("TAG_DIR", True)
        self.assertTrue(status)

    @mock.patch('udocker.FileUtil')
    @mock.patch.object(udocker.LocalRepository, '_remove_layers')
    @mock.patch.object(udocker.LocalRepository, 'cd_imagerepo')
    def test_22_del_imagerepo(self, mock_cd, mock_rmlayers, mock_futil):
        """Test LocalRepository()._del_imagerepo()."""
        localrepo = self._localrepo(UDOCKER_TOPDIR)
        #
        mock_cd.return_value = False
        status = localrepo.del_imagerepo("IMAGE", "TAG", False)
        self.assertFalse(status)
        #
        mock_cd.return_value = True
        status = localrepo.del_imagerepo("IMAGE", "TAG", False)
        self.assertTrue(status)
        #
        localrepo.cur_repodir = "XXXX"
        localrepo.cur_tagdir = "XXXX"
        mock_futil.return_value.remove.return_value = True
        status = localrepo.del_imagerepo("IMAGE", "TAG", False)
        self.assertEqual(localrepo.cur_repodir, "")
        self.assertEqual(localrepo.cur_tagdir, "")
        self.assertTrue(status)

    def _sideffect_test_23(self, arg):
        """Side effect for isdir on test 23 _get_tags()."""
        if self.iter < 3:
            self.iter += 1
            return False
        else:
            return True

    @mock.patch('udocker.os.path.isdir')
    @mock.patch('udocker.os.listdir')
    @mock.patch('udocker.FileUtil')
    @mock.patch.object(udocker.LocalRepository, '_is_tag')
    def test_23__get_tags(self, mock_is, mock_futil,
                          mock_listdir, mock_isdir):
        """Test LocalRepository()._get_tags()."""
        localrepo = self._localrepo(UDOCKER_TOPDIR)
        #
        mock_futil.return_value.isdir.return_value = False
        status = localrepo._get_tags("CONTAINERS_DIR")
        self.assertEqual(status, [])
        #
        mock_futil.return_value.isdir.return_value = True
        mock_listdir.return_value = []
        status = localrepo._get_tags("CONTAINERS_DIR")
        self.assertEqual(status, [])
        #
        mock_futil.return_value.isdir.return_value = True
        mock_listdir.return_value = ["FILE1", "FILE2"]
        mock_is.return_value = False
        mock_isdir.return_value = False
        status = localrepo._get_tags("CONTAINERS_DIR")
        self.assertEqual(status, [])
        #
        mock_futil.return_value.isdir.return_value = True
        mock_listdir.return_value = ["FILE1", "FILE2"]
        mock_is.return_value = True
        status = localrepo._get_tags("CONTAINERS_DIR")
        expected_status = [('CONTAINERS_DIR', 'FILE1'),
                           ('CONTAINERS_DIR', 'FILE2')]
        self.assertEqual(status, expected_status)
        #
        mock_futil.return_value.isdir.return_value = True
        mock_listdir.return_value = ["FILE1", "FILE2"]
        mock_is.return_value = False
        self.iter = 0
        mock_isdir.side_effect = self._sideffect_test_23
        status = localrepo._get_tags("CONTAINERS_DIR")
        expected_status = [('CONTAINERS_DIR', 'FILE1'),
                           ('CONTAINERS_DIR', 'FILE2')]
        self.assertEqual(self.iter, 2)
        self.assertEqual(status, [])

    @mock.patch('udocker.os.path.islink')
    @mock.patch('udocker.os.path.exists')
    @mock.patch.object(udocker.LocalRepository, '_symlink')
    def test_24_add_image_layer(self, mock_slink, mock_exists, mock_islink):
        """Test LocalRepository().add_image_layer()."""
        localrepo = self._localrepo(UDOCKER_TOPDIR)
        #
        localrepo.cur_repodir = ""
        localrepo.cur_tagdir = ""
        status = localrepo.add_image_layer("FILE")
        self.assertFalse(status)
        #
        localrepo.cur_repodir = "IMAGE"
        localrepo.cur_tagdir = "TAG"
        status = localrepo.add_image_layer("FILE")
        self.assertTrue(status)
        #
        mock_exists.return_value = False
        status = localrepo.add_image_layer("FILE")
        self.assertFalse(status)
        #
        mock_exists.return_value = True
        mock_islink.return_value = True
        status = localrepo.add_image_layer("FILE")
        udocker.FileUtil.return_value.remove.return_value = True
        self.assertTrue(udocker.FileUtil.called)
        self.assertTrue(status)
        #
        mock_exists.return_value = True
        mock_islink.return_value = False
        udocker.FileUtil.reset_mock()
        status = localrepo.add_image_layer("FILE")
        self.assertFalse(udocker.FileUtil.called)
        self.assertTrue(status)

    @mock.patch('udocker.os.makedirs')
    @mock.patch('udocker.os.path.exists')
    def test_25_setup_imagerepo(self, mock_exists, mock_makedirs):
        """Test LocalRepository().setup_imagerepo()."""
        localrepo = self._localrepo(UDOCKER_TOPDIR)
        #
        status = localrepo.setup_imagerepo("")
        self.assertFalse(status)
        #
        mock_exists.return_value = True
        status = localrepo.setup_imagerepo("IMAGE")
        expected_directory = localrepo.reposdir + "/IMAGE"
        self.assertEqual(localrepo.cur_repodir, expected_directory)
        self.assertFalse(status)
        #
        mock_exists.return_value = False
        status = localrepo.setup_imagerepo("IMAGE")
        expected_directory = localrepo.reposdir + "/IMAGE"
        self.assertTrue(mock_makedirs.called)
        self.assertEqual(localrepo.cur_repodir, expected_directory)
        self.assertTrue(status)

    @mock.patch('udocker.os.makedirs')
    @mock.patch('udocker.os.path.exists')
    def test_26_setup_tag(self, mock_exists, mock_makedirs):
        """Test LocalRepository().setup_tag()."""
        localrepo = self._localrepo(UDOCKER_TOPDIR)
        #
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
    def test_27_set_version(self, mock_exists, mock_makedirs, mock_listdir):
        """Test LocalRepository().set_version()."""
        localrepo = self._localrepo(UDOCKER_TOPDIR)
        #
        status = localrepo.set_version("v1")
        self.assertFalse(mock_exists.called)
        self.assertFalse(status)
        #
        localrepo.cur_repodir = localrepo.reposdir + "/IMAGE"
        localrepo.cur_tagdir = localrepo.cur_repodir + "/TAG"
        mock_exists.return_value = False
        status = localrepo.set_version("v1")
        self.assertFalse(mock_listdir.called)
        self.assertFalse(status)
        #
        mock_exists.return_value = True
        with mock.patch(BUILTINS + '.open', mock.mock_open()) as mopen:
            status = localrepo.set_version("v1")
            self.assertTrue(mock_listdir.called)
            self.assertTrue(mopen.called)
            self.assertTrue(status)

    @mock.patch.object(udocker.LocalRepository, 'save_json')
    @mock.patch.object(udocker.LocalRepository, 'load_json')
    @mock.patch('udocker.os.path.exists')
    def test_28_get_image_attributes(self, mock_exists, mock_loadjson,
                                     mock_savejson):
        """Test LocalRepository().get_image_attributes()."""
        localrepo = self._localrepo(UDOCKER_TOPDIR)
        #
        mock_exists.return_value = True
        mock_loadjson.return_value = None
        status = localrepo.get_image_attributes()
        self.assertEqual((None, None), status)
        #
        mock_exists.side_effect = [True, False]
        mock_loadjson.side_effect = [("foolayername",), ]
        status = localrepo.get_image_attributes()
        self.assertEqual((None, None), status)
        #
        mock_exists.side_effect = [True, True, False]
        mock_loadjson.side_effect = [("foolayername",), "foojson"]
        status = localrepo.get_image_attributes()
        self.assertEqual((None, None), status)
        #
        mock_exists.side_effect = [True, True, True]
        mock_loadjson.side_effect = [("foolayername",), "foojson"]
        status = localrepo.get_image_attributes()
        self.assertEqual(('foojson', ['/foolayername.layer']), status)
        #
        mock_exists.side_effect = [False, True]
        mock_loadjson.side_effect = [None, ]
        status = localrepo.get_image_attributes()
        self.assertEqual((None, None), status)
        #
        mock_exists.side_effect = [False, True, False]
        manifest = {
            "fsLayers": ({"blobSum": "foolayername"},),
            "history": ({"v1Compatibility": '["foojsonstring"]'},)
        }
        mock_loadjson.side_effect = [manifest, ]
        status = localrepo.get_image_attributes()
        self.assertEqual((None, None), status)
        #
        mock_exists.side_effect = [False, True, True]
        mock_loadjson.side_effect = [manifest, ]
        status = localrepo.get_image_attributes()
        self.assertEqual(([u'foojsonstring'], ['/foolayername']), status)

    @mock.patch('udocker.json.dump')
    @mock.patch('udocker.os.path.exists')
    def test_29_save_json(self, mock_exists, mock_jsondump):
        """Test LocalRepository().save_json()."""
        localrepo = self._localrepo(UDOCKER_TOPDIR)
        #
        status = localrepo.save_json("filename", "data")
        self.assertFalse(mock_exists.called)
        self.assertFalse(status)
        #
        localrepo.cur_repodir = localrepo.reposdir + "/IMAGE"
        localrepo.cur_tagdir = localrepo.cur_repodir + "/TAG"
        mock_exists.return_value = False
        status = localrepo.save_json("filename", "data")
        self.assertTrue(mock_exists.called)
        self.assertFalse(status)
        #
        mock_exists.reset_mock()
        with mock.patch(BUILTINS + '.open', mock.mock_open()) as mopen:
            status = localrepo.save_json("/filename", "data")
            self.assertTrue(mopen.called)
            self.assertTrue(status)
        #
        mock_exists.reset_mock()
        with mock.patch(BUILTINS + '.open', mock.mock_open()) as mopen:
            mopen.side_effect = IOError('foo')
            status = localrepo.save_json("/filename", "data")
            self.assertTrue(mopen.called)
            self.assertFalse(status)

    @mock.patch('udocker.json.load')
    @mock.patch('udocker.os.path.exists')
    def test_30_load_json(self, mock_exists, mock_jsonload):
        """Test LocalRepository().load_json()."""
        localrepo = self._localrepo(UDOCKER_TOPDIR)
        #
        status = localrepo.load_json("filename")
        self.assertFalse(mock_exists.called)
        self.assertFalse(status)
        #
        localrepo.cur_repodir = localrepo.reposdir + "/IMAGE"
        localrepo.cur_tagdir = localrepo.cur_repodir + "/TAG"
        mock_exists.return_value = False
        status = localrepo.load_json("filename")
        self.assertTrue(mock_exists.called)
        self.assertFalse(status)
        #
        mock_exists.reset_mock()
        with mock.patch(BUILTINS + '.open', mock.mock_open()) as mopen:
            status = localrepo.load_json("/filename")
            self.assertTrue(mopen.called)
            self.assertTrue(status)
        #
        mock_exists.reset_mock()
        with mock.patch(BUILTINS + '.open', mock.mock_open()) as mopen:
            mopen.side_effect = IOError('foo')
            status = localrepo.load_json("/filename")
            self.assertTrue(mopen.called)
            self.assertFalse(status)

    @mock.patch('udocker.FileUtil')
    def test_31__protect(self, mock_futil):
        """Test LocalRepository()._protect().

        Set the protection mark in a container or image tag
        """
        localrepo = self._localrepo(UDOCKER_TOPDIR)
        mock_futil.return_value.isdir.return_value = True
        status = localrepo._protect
        self.assertTrue(status)

    @mock.patch('udocker.FileUtil')
    def test_32__unprotect(self, mock_futil):
        """Test LocalRepository()._unprotect().

        Remove protection mark from container or image tag.
        """
        localrepo = self._localrepo(UDOCKER_TOPDIR)
        mock_futil.return_value.isdir.return_value = True
        status = localrepo._unprotect("dir")
        self.assertTrue(status)

    @mock.patch('udocker.FileUtil')
    @mock.patch('udocker.os.path.exists')
    def test_33__isprotected(self, mock_exists, mock_futil):
        """Test LocalRepository()._isprotected().

        See if container or image tag are protected.
        """
        localrepo = self._localrepo(UDOCKER_TOPDIR)
        mock_futil.return_value.isdir.return_value = True
        mock_exists.return_value = True
        status = localrepo._isprotected("dir")
        self.assertTrue(status)

    @mock.patch.object(udocker.LocalRepository, 'cd_container')
    @mock.patch.object(udocker.LocalRepository, 'get_containers_list')
    def test_34_del_container(self, mock_cdcont, mock_getcl):
        """Test LocalRepository().del_container()."""
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

    def test_35__relpath(self):
        """Test LocalRepository()._relpath()."""
        pass

    def test_36__name_is_valid(self):
        """Test LocalRepository()._name_is_valid().

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

    @mock.patch('udocker.FileUtil')
    @mock.patch('udocker.os.path.isfile')
    def test_37__is_tag(self, mock_isfile, mock_futil):
        """Test LocalRepository()._is_tag().

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

    @mock.patch('udocker.LocalRepository')
    def test_38_cd_imagerepo(self, mock_local):
        """Test LocalRepository().cd_imagerepo()."""
        localrepo = self._localrepo(UDOCKER_TOPDIR)
        localrepo.reposdir = "/tmp"
        out = localrepo.cd_imagerepo("IMAGE", "TAG")
        self.assertNotEqual(out, "")

    @mock.patch('udocker.FileUtil')
    @mock.patch('udocker.os.path.islink')
    @mock.patch('udocker.os.path.isdir')
    @mock.patch('udocker.os.listdir')
    def test_39__find(self, mock_listdir, mock_isdir, mock_islink, mock_futil):
        """Test LocalRepository()._find().

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
    def test_40__inrepository(self, mock_listdir,
                              mock_isdir, mock_islink, mock_futil):
        """Test LocalRepository()._inrepository().

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

    @mock.patch('udocker.FileUtil')
    @mock.patch('udocker.os.path.islink')
    @mock.patch('udocker.os.readlink')
    @mock.patch('udocker.os.listdir')
    @mock.patch('udocker.os.path.realpath')
    def test_41__remove_layers(self, mock_realpath, mock_listdir,
                               mock_readlink, mock_islink, mock_futil):
        """Test LocalRepository()._remove_layers().

        Remove link to image layer and corresponding layer
        if not being used by other images.
        """
        localrepo = self._localrepo(UDOCKER_TOPDIR)
        localrepo.reposdir = "/tmp"
        mock_realpath.return_value = "/tmp"
        mock_listdir.return_value = "file"
        mock_islink.return_value = True
        mock_readlink.return_value = "file"
        tag_dir = "TAGDIR"

        mock_futil.return_value.remove.return_value = False
        status = localrepo._remove_layers(tag_dir, True)
        self.assertTrue(status)

        mock_futil.return_value.remove.return_value = False
        status = localrepo._remove_layers(tag_dir, False)
        # (FIXME lalves): This is not OK, it should be False. Review this test.
        self.assertTrue(status)

    @mock.patch.object(udocker.LocalRepository, '_get_tags')
    def test_42_get_imagerepos(self, mock_gtags):
        """Test LocalRepository().get_imagerepos()."""
        localrepo = self._localrepo(UDOCKER_TOPDIR)
        localrepo.get_imagerepos()
        self.assertTrue(mock_gtags.called)

    @mock.patch('udocker.LocalRepository')
    @mock.patch.object(udocker.LocalRepository, 'cd_container')
    def test_43_get_layers(self, mock_local, mock_cd):
        """Test LocalRepository().get_layers()."""
        localrepo = self._localrepo(UDOCKER_TOPDIR)
        localrepo.get_layers("IMAGE", "TAG")
        self.assertTrue(mock_cd.called)

    @mock.patch('udocker.FileUtil.isdir')
    @mock.patch('udocker.LocalRepository')
    @mock.patch('udocker.LocalRepository.load_json')
    @mock.patch('udocker.os.listdir')
    def test_44__load_structure(self, mock_listdir, mock_json,
                                mock_local, mock_isdir):
        """Test LocalRepository()._load_structure().

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


    def test_45__find_top_layer_id(self):
        """Test."""
        pass

    def test_46__sorted_layers(self):
        """Test."""
        pass

    def test_47__verify_layer_file(self):
        """Test."""
        pass

    @mock.patch('udocker.Msg')
    @mock.patch.object(udocker.LocalRepository, '_load_structure')
    def test_48_verify_image(self, mock_lstruct, mock_msg):
        """Test LocalRepository().verify_image()."""
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
        """Test CurlHeader() constructor."""
        curl_header = udocker.CurlHeader()
        self.assertFalse(curl_header.sizeonly)
        self.assertIsInstance(curl_header.data, dict)
        self.assertEqual("", curl_header.data["X-ND-HTTPSTATUS"])
        self.assertEqual("", curl_header.data["X-ND-CURLSTATUS"])

    def test_02_write(self):
        """Test CurlHeader().write()."""
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
        #
        curl_header = udocker.CurlHeader()
        for line in buff:
            curl_header.write(line)
        buff_out = curl_header.getvalue()
        self.assertTrue("HTTP/1.1 200 OK" in buff_out)
        #
        line = ""
        curl_header = udocker.CurlHeader()
        curl_header.sizeonly = True
        self.assertEqual(-1, curl_header.write(line))

    @mock.patch('udocker.CurlHeader.write')
    def test_03_setvalue_from_file(self, mock_write):
        """Test CurlHeader().setvalue_from_file()."""
        fakedata = StringIO('XXXX')
        with mock.patch(BUILTINS + '.open') as mopen:
            mopen.return_value.__iter__ = (
                lambda self: iter(fakedata.readline, ''))
            curl_header = udocker.CurlHeader()
            self.assertTrue(curl_header.setvalue_from_file("filename"))
            mock_write.assert_called_with('XXXX')

    def test_04_getvalue(self):
        """Test CurlHeader().getvalue()."""
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
        """Test GetURL() constructor."""
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
        """Test GetURL()._select_implementation()."""
        self._init()
        mock_msg.level = 0
        mock_gupycurl.return_value.is_available.return_value = True
        geturl = udocker.GetURL()
        geturl._select_implementation()
        self.assertEqual(geturl.cache_support, True)
        #
        mock_gupycurl.return_value.is_available.return_value = False
        geturl = udocker.GetURL()
        geturl._select_implementation()
        self.assertEqual(geturl.cache_support, False)
        #
        mock_guexecurl.return_value.is_available.return_value = False
        with self.assertRaises(NameError):
            udocker.GetURL()

    @mock.patch('udocker.GetURL._select_implementation')
    def test_03_get_content_length(self, mock_sel):
        """Test GetURL().get_content_length()."""
        self._init()
        geturl = udocker.GetURL()
        hdr = type('test', (object,), {})()
        hdr.data = {"content-length": 10, }
        self.assertEqual(geturl.get_content_length(hdr), 10)
        hdr.data = {"content-length": dict(), }
        self.assertEqual(geturl.get_content_length(hdr), -1)

    @mock.patch('udocker.GetURLpyCurl')
    def test_04_set_insecure(self, mock_gupycurl):
        """Test GetURL().set_insecure()."""
        self._init()
        mock_gupycurl.return_value.is_available.return_value = True
        geturl = udocker.GetURL()
        geturl.set_insecure()
        self.assertEqual(geturl.insecure, True)
        #
        geturl.set_insecure(False)
        self.assertEqual(geturl.insecure, False)

    @mock.patch('udocker.GetURLpyCurl')
    def test_05_set_proxy(self, mock_gupycurl):
        """Test GetURL().set_proxy()."""
        self._init()
        mock_gupycurl.return_value.is_available.return_value = True
        geturl = udocker.GetURL()
        geturl.set_proxy("http://host")
        self.assertEqual(geturl.http_proxy, "http://host")

    @mock.patch('udocker.GetURL._select_implementation')
    def test_06_get(self, mock_sel):
        """Test GetURL().get() generic get."""
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
        """Test GetURL().post() generic post."""
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

    @mock.patch('udocker.Msg')
    @mock.patch('udocker.GetURLpyCurl')
    def test_01_is_available(self, mock_gupycurl, mock_msg):
        """Test GetURLpyCurl()._is_available()."""
        self._init()
        mock_msg.level = 0
        geturl = udocker.GetURLpyCurl()
        geturl.is_available()
        mock_gupycurl.return_value.is_available.return_value = True
        self.assertTrue(geturl.is_available())

        mock_gupycurl.return_value.is_available.return_value = False
        self.assertFalse(geturl.is_available())

    def test_02__select_implementation(self):
        """Test GetURLpyCurl()._select_implementation()."""
        pass

    #    @mock.patch('udocker.GetURLpyCurl._select_implementation')
    #    @mock.patch('udocker.Msg')
    #    @mock.patch('udocker.pycurl')
    #    @mock.patch('udocker.CurlHeader')
    #    def test_03__set_defaults(self, mock_hdr, mock_pyc, mock_msg, mock_sel):
    #        """Test GetURLpyCurl()._set_defaults()."""
    #        self._init()
    #        mock_sel.return_value.insecure.return_value = True
    #        geturl = udocker.GetURLpyCurl()
    #        geturl._set_defaults(mock_pyc, mock_hdr)
    #        self.assertTrue(mock_pyc.setopt.called)
    #
    #        # when Msg.level >= Msg.DBG: AND insecure
    #        mock_msg.DBG.return_value = 3
    #        mock_msg.level.return_value = 3
    #        geturl._set_defaults(mock_pyc, mock_hdr)
    #        self.assertEqual(mock_pyc.setopt.call_count, 18)
    #
    #        mock_sel.return_value.insecure.return_value = True
    #
    #        # when Msg.level < Msg.DBG: AND secure
    #        mock_msg.DBG.return_value = 3
    #        mock_msg.level.return_value = 2
    #        geturl._set_defaults(mock_pyc, mock_hdr)
    #        self.assertEqual(mock_pyc.setopt.call_count, 27)
    #
    #    @mock.patch('udocker.GetURLpyCurl._select_implementation')
    #    @mock.patch('udocker.Msg')
    #    @mock.patch('udocker.pycurl')
    #    @mock.patch('udocker.CurlHeader')
    #    def test_04__mkpycurl(self, mock_hdr, mock_pyc, mock_msg, mock_sel):
    #        """Test GetURL()._mkpycurl()."""
    #        self._init()
    #        mock_sel.return_value.insecure.return_value = True
    #        geturl = udocker.GetURLpyCurl()
    #        geturl._set_defaults(mock_pyc, mock_hdr)
    #        self.assertTrue(mock_pyc.setopt.called)
    #
    #        # WIP(...)

    @mock.patch('udocker.GetURLpyCurl._select_implementation')
    def test_05_get(self, mock_sel):
        """Test GetURLpyCurl().get() generic get."""
        self._init()
        #
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
        """Test GetURLexeCurl().__init__()."""
        self._init()
        self.assertIsNone(udocker.GetURLexeCurl()._opts)
        self.assertIsNone(udocker.GetURLexeCurl()._files)

    @mock.patch('udocker.Msg')
    @mock.patch('udocker.FileUtil')
    @mock.patch('udocker.GetURLexeCurl._select_implementation')
    def test_02_is_available(self, mock_sel, mock_futil, mock_msg):
        """Test GetURLexeCurl()._is_available()."""
        self._init()
        mock_msg.level = 0
        geturl = udocker.GetURLexeCurl()
        mock_futil.return_value.find_exec.return_value = "/tmp"
        self.assertTrue(geturl.is_available())

        mock_futil.return_value.find_exec.return_value = ""
        self.assertFalse(geturl.is_available())

    def test_03__select_implementation(self):
        """Test GetURLexeCurl()._select_implementation()."""
        pass

    @mock.patch('udocker.Msg')
    @mock.patch('udocker.GetURLexeCurl._select_implementation')
    @mock.patch('udocker.FileUtil')
    def test_04__set_defaults(self, mock_sel, mock_futil, mock_msg):
        """Set defaults for curl command line options"""
        self._init()
        geturl = udocker.GetURLexeCurl()
        geturl._set_defaults()
        self.assertEqual(geturl._opts["insecure"], "")

        geturl.insecure = True
        geturl._set_defaults()
        self.assertEqual(geturl._opts["insecure"], "-k")

        mock_msg.DBG = 0
        mock_msg.level = 1
        geturl._set_defaults()
        # self.assertEqual(geturl._opts["verbose"], "-v")

        self.assertEqual(geturl._files["url"], "")

    def test_05__mkcurlcmd(self):
        """Test GetURLexeCurl()._mkcurlcmd()."""
        pass

    @mock.patch('udocker.GetURLexeCurl._select_implementation')
    def test_06_get(self, mock_sel):
        """Test GetURLexeCurl().get() generic get."""
        self._init()
        #
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
        """Test DockerIoAPI()."""
        self._init()
        #
        uia = udocker.DockerIoAPI(mock_local)
        self.assertEqual(uia.index_url, udocker.Config.dockerio_index_url)
        self.assertEqual(uia.registry_url,
                         udocker.Config.dockerio_registry_url)
        self.assertEqual(uia.v1_auth_header, "")
        self.assertEqual(uia.v2_auth_header, "")
        self.assertEqual(uia.v2_auth_token, "")
        self.assertEqual(uia.localrepo, mock_local)
        self.assertEqual(uia.docker_registry_domain, "docker.io")
        self.assertEqual(uia.search_link, "")
        self.assertTrue(uia.search_pause)
        self.assertEqual(uia.search_page, 0)
        self.assertEqual(uia.search_lines, 25)
        self.assertEqual(uia.search_link, "")
        self.assertFalse(uia.search_ended)
        self.assertTrue(mock_geturl.called)

    @mock.patch('udocker.GetURL')
    @mock.patch('udocker.LocalRepository')
    def test_02_set_proxy(self, mock_local, mock_geturl):
        """Test DockerIoAPI().set_proxy()."""
        self._init()
        #
        uia = udocker.DockerIoAPI(mock_local)
        url = "socks5://user:pass@host:port"
        uia.set_proxy(url)
        self.assertTrue(mock_geturl.return_value.set_proxy.called_with(url))

    @mock.patch('udocker.GetURL')
    @mock.patch('udocker.LocalRepository')
    def test_03_set_registry(self, mock_local, mock_geturl):
        """Test DockerIoAPI().set_registry()."""
        self._init()
        #
        uia = udocker.DockerIoAPI(mock_local)
        uia.set_registry("https://registry-1.docker.io")
        self.assertEqual(uia.registry_url, "https://registry-1.docker.io")

    @mock.patch('udocker.GetURL')
    @mock.patch('udocker.LocalRepository')
    def test_04_set_index(self, mock_local, mock_geturl):
        """Test DockerIoAPI().set_index()."""
        self._init()
        #
        uia = udocker.DockerIoAPI(mock_local)
        uia.set_index("https://index.docker.io/v1")
        self.assertEqual(uia.index_url, "https://index.docker.io/v1")

    @mock.patch('udocker.GetURL')
    @mock.patch('udocker.Msg')
    @mock.patch('udocker.LocalRepository')
    def test_05_is_repo_name(self, mock_local, mock_msg, mock_geturl):
        """Test DockerIoAPI().is_repo_name()."""
        self._init()
        mock_msg.level = 0
        #
        uia = udocker.DockerIoAPI(mock_local)
        self.assertFalse(uia.is_repo_name(""))
        self.assertFalse(uia.is_repo_name("socks5://user:pass@host:port"))
        self.assertFalse(uia.is_repo_name("/:"))
        self.assertTrue(uia.is_repo_name("1233/fasdfasdf:sdfasfd"))
        self.assertTrue(uia.is_repo_name("os-cli-centos7"))
        self.assertTrue(uia.is_repo_name("os-cli-centos7:latest"))
        self.assertTrue(uia.is_repo_name("lipcomputing/os-cli-centos7"))
        self.assertTrue(uia.is_repo_name("lipcomputing/os-cli-centos7:latest"))

    @mock.patch('udocker.GetURL')
    @mock.patch('udocker.LocalRepository')
    def test_06__is_docker_registry(self, mock_local, mock_geturl):
        """Test DockerIoAPI().is_docker_registry()."""
        self._init()
        #
        uia = udocker.DockerIoAPI(mock_local)
        uia.set_registry("https://registry-1.docker.io")
        self.assertTrue(uia._is_docker_registry())
        #
        uia.set_registry("")
        self.assertFalse(uia._is_docker_registry())
        #
        uia.set_registry("https://registry-1.docker.pt")
        self.assertFalse(uia._is_docker_registry())
        #
        uia.set_registry("docker.io")
        self.assertTrue(uia._is_docker_registry())

    @mock.patch('udocker.GetURL')
    @mock.patch('udocker.CurlHeader')
    @mock.patch('udocker.DockerIoAPI._get_url')
    @mock.patch('udocker.LocalRepository')
    def test_07_get_v1_repo(self, mock_local, mock_dgu, mock_hdr, mock_geturl):
        """Test."""
        self._init()

        mock_dgu.return_value = (mock_hdr, [])
        imagerepo = "REPO"
        doia = udocker.DockerIoAPI(mock_local)
        doia.index_url = "docker.io"
        out = doia.get_v1_repo(imagerepo)
        self.assertIsInstance(out, tuple)

    @mock.patch('udocker.GetURL')
    @mock.patch('udocker.CurlHeader')
    @mock.patch('udocker.DockerIoAPI._get_url')
    @mock.patch('udocker.LocalRepository')
    def test_08_get_v1_image_tags(self, mock_local, mock_dgu, mock_hdr, mock_geturl):
        """Test."""
        self._init()

        mock_dgu.return_value = (mock_hdr, [])
        endpoint = "docker.io"
        imagerepo = "REPO"
        doia = udocker.DockerIoAPI(mock_local)
        out = doia.get_v1_image_tags(endpoint, imagerepo)
        self.assertIsInstance(out, tuple)

    @mock.patch('udocker.GetURL')
    @mock.patch('udocker.CurlHeader')
    @mock.patch('udocker.DockerIoAPI._get_url')
    @mock.patch('udocker.LocalRepository')
    def test_09_get_v1_image_tag(self, mock_local, mock_dgu, mock_hdr, mock_geturl):
        """Test."""
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
    def test_10_get_v1_image_ancestry(self, mock_local, mock_dgu, mock_hdr, mock_geturl):
        """Test."""
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
    def test_11_get_v1_image_json(self, mock_local, mock_dgf, mock_geturl):
        """Test."""
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
    def test_12_get_v1_image_layer(self, mock_local, mock_dgf, mock_geturl):
        """Test."""
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
    def test_13_get_v1_layers_all(self, mock_local, mock_dgf, mock_msg, mock_geturl):
        """Test."""
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

    @mock.patch('udocker.GetURL')
    @mock.patch('udocker.LocalRepository')
    def test_14_get_v2_login_token(self, mock_local, mock_geturl):
        """Test."""
        self._init()

        doia = udocker.DockerIoAPI(mock_local)
        out = doia.get_v2_login_token("username", "password")
        self.assertIsInstance(out, str)

        out = doia.get_v2_login_token("", "")
        self.assertEqual(out, "")

    @mock.patch('udocker.GetURL')
    @mock.patch('udocker.LocalRepository')
    def test_15_set_v2_login_token(self, mock_local, mock_geturl):
        """Test."""
        self._init()

        doia = udocker.DockerIoAPI(mock_local)
        doia.set_v2_login_token("BIG-FAT-TOKEN")
        self.assertEqual(doia.v2_auth_token, "BIG-FAT-TOKEN")

    @mock.patch('udocker.GetURL')
    @mock.patch('udocker.CurlHeader')
    @mock.patch('udocker.DockerIoAPI._get_url')
    @mock.patch('udocker.LocalRepository')
    def test_16_is_v2(self, mock_local, mock_dgu, mock_hdr, mock_geturl):
        """Test."""
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

    @mock.patch('udocker.GetURL')
    @mock.patch('udocker.CurlHeader')
    @mock.patch('udocker.DockerIoAPI._get_url')
    @mock.patch('udocker.LocalRepository')
    def test_17_get_v2_image_manifest(self, mock_local, mock_dgu, mock_hdr, mock_geturl):
        """Test."""
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
    def test_18_get_v2_image_layer(self, mock_local, mock_dgf, mock_hdr, mock_geturl):
        """Test."""
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
    @mock.patch('udocker.DockerIoAPI._get_file')
    @mock.patch('udocker.LocalRepository')
    def test_19_get_v2_layers_all(self, mock_local, mock_dgf, mock_msg, mock_geturl):
        """Test."""
        self._init()

        mock_dgf.return_value = True
        endpoint = "docker.io"
        fslayers = []
        doia = udocker.DockerIoAPI(mock_local)
        out = doia.get_v2_layers_all(endpoint, fslayers)
        self.assertEqual(out, [])

        # fslayers = ["a", "b"]
        # doia = udocker.DockerIoAPI(mock_local)
        # out = doia.get_v2_layers_all(endpoint, fslayers)
        # self.assertEqual(out, ['b.json', 'b.layer', 'a.json', 'a.layer'])

    @mock.patch('udocker.GetURL')
    @mock.patch('udocker.CurlHeader')
    @mock.patch('udocker.Msg')
    @mock.patch('udocker.DockerIoAPI.get_v2_layers_all')
    @mock.patch('udocker.DockerIoAPI._get_url')
    @mock.patch('udocker.LocalRepository')
    def test_20_get_v2(self, mock_local, mock_dgu, mock_dgv2,
                       mock_msg, mock_hdr, mock_geturl):
        """Test."""
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

    @mock.patch('udocker.GetURL')
    @mock.patch('udocker.CurlHeader')
    @mock.patch('udocker.Msg')
    @mock.patch('udocker.DockerIoAPI.get_v1_layers_all')
    @mock.patch('udocker.DockerIoAPI._get_url')
    @mock.patch('udocker.LocalRepository')
    def test_21_get_v1(self, mock_local, mock_dgu, mock_dgv1,
                       mock_msg, mock_hdr, mock_geturl):
        """Test."""
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

    @mock.patch('udocker.DockerIoAPI._get_url')
    @mock.patch('udocker.GetURL')
    @mock.patch('udocker.CurlHeader')
    @mock.patch('udocker.Msg')
    @mock.patch('udocker.DockerIoAPI._parse_imagerepo')
    @mock.patch('udocker.LocalRepository')
    @mock.patch('udocker.LocalRepository.cd_imagerepo')
    def test_22_get(self, mock_cdir, mock_local, mock_parse,
                    mock_msg, mock_hdr, mock_geturl, mock_dgu):
        """Test."""
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
    def test_23_search_init(self, mock_local, mock_geturl):
        """Test."""
        self._init()

        doia = udocker.DockerIoAPI(mock_local)
        doia.search_init("PAUSE")
        self.assertEqual(doia.search_pause, "PAUSE")
        self.assertEqual(doia.search_page, 0)
        self.assertEqual(doia.search_link, "")
        self.assertEqual(doia.search_ended, False)

    @mock.patch('udocker.DockerIoAPI._get_url')
    @mock.patch('udocker.GetURL')
    @mock.patch('udocker.CurlHeader')
    @mock.patch('udocker.Msg')
    @mock.patch('udocker.LocalRepository')
    def test_24_search_get_page_v1(self, mock_local, mock_msg, mock_hdr,
                                   mock_geturl, mock_dgu):
        """Test."""
        self._init()

        mock_dgu.return_value = (mock_hdr, [])

        doia = udocker.DockerIoAPI(mock_local)
        doia.set_index("index.docker.io")
        out = doia.search_get_page_v1("SOMETHING")
        self.assertEqual(out, [])

    @mock.patch('udocker.DockerIoAPI._get_url')
    @mock.patch('udocker.GetURL')
    @mock.patch('udocker.CurlHeader')
    @mock.patch('udocker.Msg')
    @mock.patch('udocker.LocalRepository')
    def test_25_catalog_get_page_v2(self, mock_local, mock_msg, mock_hdr,
                                    mock_geturl, mock_dgu):
        """Test."""
        self._init()

        # mock_dgu.return_value = (mock_hdr, [])
        #
        # doia = udocker.DockerIoAPI(mock_local)
        # doia.set_index("index.docker.io")
        # out = doia.catalog_get_page_v2("lines")
        # self.assertEqual(out, [])

    @mock.patch('udocker.DockerIoAPI._get_url')
    @mock.patch('udocker.GetURL')
    @mock.patch('udocker.CurlHeader')
    @mock.patch('udocker.Msg')
    @mock.patch('udocker.LocalRepository')
    def test_26_search_get_page(self, mock_local, mock_msg, mock_hdr,
                                mock_geturl, mock_dgu):
        """Test."""
        self._init()

        mock_dgu.return_value = (mock_hdr, [])

        doia = udocker.DockerIoAPI(mock_local)
        doia.set_index("index.docker.io")
        out = doia.search_get_page("SOMETHING")
        self.assertEqual(out, [])

    @mock.patch('udocker.DockerIoAPI._get_url')
    @mock.patch('udocker.GetURL')
    @mock.patch('udocker.CurlHeader')
    @mock.patch('udocker.Msg')
    @mock.patch('udocker.LocalRepository')
    def test_27__get_url(self, mock_local, mock_msg, mock_hdr,
                         mock_geturl, mock_dgu):
        """."""
        self._init()

        mock_dgu.return_value = (mock_hdr, [])

        doia = udocker.DockerIoAPI(mock_local)

    @mock.patch('udocker.DockerIoAPI._get_url')
    @mock.patch('udocker.GetURL')
    @mock.patch('udocker.CurlHeader')
    @mock.patch('udocker.Msg')
    @mock.patch('udocker.LocalRepository')
    def test_28__get_file(self, mock_local, mock_msg, mock_hdr,
                          mock_geturl, mock_dgu):
        """."""
        self._init()

        mock_dgu.return_value = (mock_hdr, [])

        doia = udocker.DockerIoAPI(mock_local)


    @mock.patch('udocker.GetURL')
    @mock.patch('udocker.Msg')
    @mock.patch('udocker.LocalRepository')
    def test_29__get_v1_auth(self, mock_local, mock_msg, mock_geturl):
        """."""
        self._init()

        doia = udocker.DockerIoAPI(mock_local)
        doia.v1_auth_header = "Not Empty"

        www_authenticate = ['Other Stuff']
        out = doia._get_v1_auth(www_authenticate)
        self.assertEqual(out, "")

        www_authenticate = ['Token']
        out = doia._get_v1_auth(www_authenticate)
        self.assertEqual(out, "Not Empty")

    @mock.patch('udocker.DockerIoAPI._get_url')
    @mock.patch('udocker.CurlHeader')
    @mock.patch('udocker.json.loads')
    @mock.patch('udocker.GetURL')
    @mock.patch('udocker.Msg')
    @mock.patch('udocker.LocalRepository')
    def test_30__get_v2_auth(self, mock_local, mock_msg, mock_geturl,
                             mock_jloads, mock_hdr, mock_dgu):
        """."""
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

class ChkSUMTestCase(unittest.TestCase):
    """Test ChkSUM() performs checksums portably."""

    @classmethod
    def setUpClass(cls):
        """Setup test."""
        set_env()

    def _init(self):
        """Configure variables."""
        pass

    @mock.patch('udocker.hashlib.sha256')
    def test_01_init(self, mock_hashlib_sha):
        """Test ChkSUM() constructor."""
        self._init()
        mock_hashlib_sha.return_value = True
        cksum = udocker.ChkSUM()
        self.assertEqual(cksum._sha256_call, cksum._hashlib_sha256)

    def test_02_sha256(self):
        """Test ChkSUM().sha256()."""
        self._init()
        mock_call = mock.MagicMock()
        cksum = udocker.ChkSUM()
        #
        mock_call.return_value = True
        cksum._sha256_call = mock_call
        status = cksum.sha256("filename")
        self.assertTrue(status)
        #
        mock_call.return_value = False
        cksum._sha256_call = mock_call
        status = cksum.sha256("filename")
        self.assertFalse(status)

    def test_03__hashlib_sha256(self):
        """Test ChkSUM()._hashlib_sha256()."""
        sha256sum = (
            "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855")
        self._init()
        cksum = udocker.ChkSUM()
        file_data = StringIO("qwerty")
        with mock.patch(BUILTINS + '.open', mock.mock_open()) as mopen:
            mopen.return_value.__iter__ = (
                lambda self: iter(file_data.readline, ''))
            status = cksum._hashlib_sha256("filename")
            self.assertEqual(status, sha256sum)

    @mock.patch('udocker.Uprocess.get_output')
    @mock.patch('udocker.Msg')
    def test_04__openssl_sha256(self, mock_msg, mock_subproc):
        """Test ChkSUM()._openssl_sha256()."""
        self._init()
        udocker.Msg = mock_msg
        udocker.Msg.return_value.chlderr = open("/dev/null", "w")
        udocker.Msg.chlderr = open("/dev/null", "w")
        mock_subproc.return_value = "123456 "
        cksum = udocker.ChkSUM()
        status = cksum._openssl_sha256("filename")
        self.assertEqual(status, "123456")


class NixAuthenticationTestCase(unittest.TestCase):
    """Test NixAuthentication() *nix authentication portably."""

    @classmethod
    def setUpClass(cls):
        """Setup test."""
        set_env()

    def _init(self):
        """Configure variables."""
        pass

    def test_01_init(self):
        """Test NixAuthentication() constructor."""
        self._init()
        auth = udocker.NixAuthentication()
        self.assertEqual(auth.passwd_file, None)
        self.assertEqual(auth.group_file, None)
        #
        auth = udocker.NixAuthentication("passwd", "group")
        self.assertEqual(auth.passwd_file, "passwd")
        self.assertEqual(auth.group_file, "group")

    @mock.patch('udocker.pwd')
    def test_01__get_user_from_host(self, mock_pwd):
        """Test NixAuthentication()._get_user_from_host()."""
        self._init()
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
        #
        mock_pwd.getpwnam.return_value = usr
        auth = udocker.NixAuthentication()
        (name, uid, gid, gecos, _dir, shell) = auth._get_user_from_host("root")
        self.assertEqual(name, usr.pw_name)
        self.assertEqual(uid, usr.pw_uid)
        self.assertEqual(gid, str(usr.pw_gid))
        self.assertEqual(gecos, usr.pw_gecos)
        self.assertEqual(_dir, usr.pw_dir)

    @mock.patch('udocker.pwd')
    def test_02__get_group_from_host(self, mock_pwd):
        """Test NixAuthentication()._get_group_from_host()."""
        self._init()
        hgr = grp.struct_group(["root", "*", "0", str([])])
        mock_pwd.getgrgid.return_value = hgr
        auth = udocker.NixAuthentication()
        (name, gid, mem) = auth._get_group_from_host(0)
        self.assertEqual(name, hgr.gr_name)
        self.assertEqual(gid, str(hgr.gr_gid))
        self.assertEqual(mem, hgr.gr_mem)
        #
        mock_pwd.getgrnam.return_value = hgr
        auth = udocker.NixAuthentication()
        (name, gid, mem) = auth._get_group_from_host("root")
        self.assertEqual(name, hgr.gr_name)
        self.assertEqual(gid, str(hgr.gr_gid))
        self.assertEqual(mem, hgr.gr_mem)

    def test_03__get_user_from_file(self):
        """Test NixAuthentication()._get_user_from_file()."""
        self._init()
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
            #
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

    def test_04__get_group_from_file(self):
        """Test NixAuthentication()._get_group_from_file()."""
        self._init()
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
            #
        group_line = StringIO('root:x:0:a,b,c')
        with mock.patch(BUILTINS + '.open') as mopen:
            mopen.return_value.__iter__ = (
                lambda self: iter(group_line.readline, ''))
            (name, gid, mem) = auth._get_group_from_file(0)
            self.assertEqual(name, "root")
            self.assertEqual(gid, "0")
            self.assertEqual(mem, "a,b,c")

    def test_05_add_user(self):
        """Test NixAuthentication().add_user()."""
        self._init()
        auth = udocker.NixAuthentication()
        with mock.patch(BUILTINS + '.open', mock.mock_open()):
            status = auth.add_user("root", "pw", 0, 0, "gecos",
                                   "/home", "/bin/bash")
            self.assertTrue(status)

    def test_06_add_group(self):
        """Test NixAuthentication().add_group()."""
        self._init()
        auth = udocker.NixAuthentication()
        with mock.patch(BUILTINS + '.open', mock.mock_open()):
            status = auth.add_group("root", 0)
            self.assertTrue(status)

    @mock.patch('udocker.NixAuthentication._get_user_from_host')
    @mock.patch('udocker.NixAuthentication._get_user_from_file')
    def test_07_get_user(self, mock_file, mock_host):
        """Test NixAuthentication().get_user()."""
        self._init()
        auth = udocker.NixAuthentication()
        auth.passwd_file = ""
        auth.get_user("user")
        self.assertTrue(mock_host.called)
        self.assertFalse(mock_file.called)
        #
        mock_host.reset_mock()
        mock_file.reset_mock()
        auth.passwd_file = "passwd"
        auth.get_user("user")
        self.assertFalse(mock_host.called)
        self.assertTrue(mock_file.called)

    @mock.patch('udocker.NixAuthentication._get_group_from_host')
    @mock.patch('udocker.NixAuthentication._get_group_from_file')
    def test_08_get_group(self, mock_file, mock_host):
        """Test NixAuthentication().get_group()."""
        self._init()
        auth = udocker.NixAuthentication()
        auth.group_file = ""
        auth.get_group("group")
        self.assertTrue(mock_host.called)
        self.assertFalse(mock_file.called)
        #
        mock_host.reset_mock()
        mock_file.reset_mock()
        auth.group_file = "group"
        auth.get_group("group")
        self.assertFalse(mock_host.called)
        self.assertTrue(mock_file.called)


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
        """Test FileBind()."""
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
        """Test FileBind().setup().

        Prepare container for FileBind.
        """
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
        """Test FileBind().restore().

        Restore container files after FileBind
        """
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
        """Test FileBind().start().

        Prepare to run.
        """
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

    @mock.patch('udocker.LocalRepository')
    def test_05_finish(self, mock_local):
        """Test FileBind().finish().

        Cleanup after run.
        """
        pass

    @mock.patch('udocker.LocalRepository')
    @mock.patch('udocker.FileUtil')
    @mock.patch('udocker.os.path.realpath')
    def test_06_add(self, mock_realpath, mock_futil, mock_local):
        """Test FileBind().add().

        Add file to be made available inside container.
        """
        self._init()

        container_id = "CONTAINERID"
        mock_realpath.return_value = "/tmp"
        host_file = "host.file"
        container_file = "#container.file"

        fbind = udocker.FileBind(mock_local, container_id)
        fbind.host_bind_dir = "/tmp"
        fbind.add(host_file, container_file)
        self.assertTrue(mock_futil.return_value.remove.called)
        self.assertTrue(mock_futil.return_value.copyto.called)


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
        udocker.Config.cpu_affinity_exec_tools = (["numactl", "-C", "%s", "--", ], ["taskset", "-c", "%s", ])
        udocker.Config.location = ""
        udocker.Config.uid = 1000
        udocker.Config.sysdirs_list = ["/", ]
        udocker.Config.root_path = "/usr/sbin:/sbin:/usr/bin:/bin"
        udocker.Config.user_path = "/usr/bin:/bin:/usr/local/bin"

    @mock.patch('udocker.LocalRepository')
    def test_01_init(self, mock_local):
        """Test ExecutionEngineCommon()."""
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

    @mock.patch('udocker.Msg')
    @mock.patch('udocker.LocalRepository')
    def test_02__check_exposed_ports(self, mock_local, mock_msg):
        """Test ExecutionEngineCommon()._check_exposed_ports()."""
        self._init()
        mock_msg.level = 0
        ex_eng = udocker.ExecutionEngineCommon(mock_local)
        ex_eng.opt["portsexp"] = ("1024", "2048/tcp", "23000/udp")
        status = ex_eng._check_exposed_ports()
        self.assertTrue(status)
        #
        ex_eng.opt["portsexp"] = ("1023", "2048/tcp", "23000/udp")
        status = ex_eng._check_exposed_ports()
        self.assertFalse(status)
        #
        ex_eng.opt["portsexp"] = ("1024", "80/tcp", "23000/udp")
        status = ex_eng._check_exposed_ports()
        self.assertFalse(status)
        #
        ex_eng.opt["portsexp"] = ("1024", "2048/tcp", "23/udp")
        status = ex_eng._check_exposed_ports()
        self.assertFalse(status)

    @mock.patch('udocker.FileUtil')
    @mock.patch('udocker.LocalRepository')
    def test_03__set_cpu_affinity(self, mock_local, mock_futil):
        """Test ExecutionEngineCommon()._set_cpu_affinity()."""
        self._init()
        ex_eng = udocker.ExecutionEngineCommon(mock_local)
        mock_futil.return_value.find_exec.return_value = ""
        status = ex_eng._set_cpu_affinity()
        self.assertEqual(status, [])
        #
        mock_futil.return_value.find_exec.return_value = "taskset"
        status = ex_eng._set_cpu_affinity()
        self.assertEqual(status, [])
        #
        mock_futil.return_value.find_exec.return_value = "numactl"
        ex_eng.opt["cpuset"] = "1-2"
        status = ex_eng._set_cpu_affinity()
        self.assertEqual(status, ["numactl", "-C", "1-2", "--"])

    @mock.patch('udocker.os.path.isdir')
    @mock.patch('udocker.LocalRepository')
    def test_04__cont2host(self, mock_local, mock_isdir):
        """Test ExecutionEngine()._cont2host()."""
        self._init()
        mock_isdir.return_value = True
        #
        ex_eng = udocker.ExecutionEngineCommon(mock_local)
        ex_eng.opt["vol"] = ("/opt/xxx:/mnt",)
        status = ex_eng._cont2host("/mnt")
        self.assertEqual(status, "/opt/xxx")
        #
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

    @mock.patch('udocker.Msg')
    @mock.patch('udocker.os.path.isdir')
    @mock.patch('udocker.os.path.exists')
    @mock.patch('udocker.ExecutionEngineCommon._cont2host')
    @mock.patch('udocker.ExecutionEngineCommon._getenv')
    @mock.patch('udocker.LocalRepository')
    def test_05__check_paths(self, mock_local, mock_getenv, mock_isinvol,
                             mock_exists, mock_isdir, mock_msg):
        """Test ExecutionEngineCommon()._check_paths()."""
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
        #
        ex_eng.opt["uid"] = "1000"
        status = ex_eng._check_paths()
        self.assertFalse(status)
        self.assertEqual(ex_eng.opt["env"][-1],
                         "PATH=/usr/bin:/bin:/usr/local/bin")
        self.assertEqual(ex_eng.opt["cwd"], ex_eng.opt["home"])
        #
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
    def test_06__check_executable(self, mock_local, mock_getenv, mock_isfile,
                                  mock_readlink, mock_access, mock_msg):
        """Test ExecutionEngineCommon()._check_executable()."""
        self._init()
        mock_msg.level = 0
        ex_eng = udocker.ExecutionEngineCommon(mock_local)
        mock_getenv.return_value = ""
        ex_eng.opt["entryp"] = "/bin/shell -x -v"
        mock_isfile.return_value = False
        ex_eng.container_root = "/containers/123/ROOT"
        status = ex_eng._check_executable()
        self.assertFalse(status)
        #
        mock_isfile.return_value = True
        mock_access.return_value = True
        status = ex_eng._check_executable()
        self.assertTrue(status)
        #
        ex_eng.opt["entryp"] = ["/bin/shell", "-x", "-v"]
        ex_eng.opt["cmd"] = ""
        status = ex_eng._check_executable()
        self.assertEqual(ex_eng.opt["cmd"], ex_eng.opt["entryp"])
        #
        ex_eng.opt["entryp"] = ["/bin/shell", ]
        ex_eng.opt["cmd"] = ["-x", "-v"]
        status = ex_eng._check_executable()
        self.assertEqual(ex_eng.opt["cmd"], ["/bin/shell", "-x", "-v"])

    @mock.patch('udocker.ContainerStructure')
    @mock.patch('udocker.ExecutionEngineCommon._check_exposed_ports')
    @mock.patch('udocker.ExecutionEngineCommon._getenv')
    @mock.patch('udocker.LocalRepository')
    def test_07__run_load_metadata(self, mock_local, mock_getenv,
                                   mock_chkports, mock_cstruct):
        """Test ExecutionEngineCommon()._run_load_metadata()."""
        self._init()
        ex_eng = udocker.ExecutionEngineCommon(mock_local)
        mock_getenv.return_value = ""
        udocker.Config.location = "/tmp/container"
        status = ex_eng._run_load_metadata("123")
        self.assertEqual(status, ("", []))
        #
        udocker.Config.location = ""
        mock_cstruct.return_value.get_container_attr.return_value = ("", [])
        status = ex_eng._run_load_metadata("123")
        self.assertEqual(status, (None, None))
        #
        udocker.Config.location = ""
        mock_cstruct.return_value.get_container_attr.return_value = ("/x", [])
        ex_eng.opt["nometa"] = True
        status = ex_eng._run_load_metadata("123")
        self.assertEqual(status, ("/x", []))
        #
        udocker.Config.location = ""
        mock_cstruct.return_value.get_container_attr.return_value = ("/x", [])
        ex_eng.opt["nometa"] = False
        status = ex_eng._run_load_metadata("123")
        self.assertEqual(status, ("/x", []))

    @mock.patch('udocker.LocalRepository')
    def test_08__getenv(self, mock_local):
        """Test ExecutionEngineCommon()._getenv()."""
        self._init()
        ex_eng = udocker.ExecutionEngineCommon(mock_local)
        ex_eng.opt["env"] = ["HOME=/home/user", "PATH=/bin:/usr/bin"]
        status = ex_eng._getenv("")
        self.assertEqual(status, None)
        #
        status = ex_eng._getenv("XXX")
        self.assertEqual(status, None)
        #
        status = ex_eng._getenv("HOME")
        self.assertEqual(status, "/home/user")
        #
        status = ex_eng._getenv("PATH")
        self.assertEqual(status, "/bin:/usr/bin")

    @mock.patch('udocker.Msg')
    @mock.patch('udocker.LocalRepository')
    def test_09__uid_gid_from_str(self, mock_local, mock_msg):
        """Test ExecutionEngineCommon()._uid_gid_from_str()."""
        self._init()
        mock_msg.level = 0
        ex_eng = udocker.ExecutionEngineCommon(mock_local)
        status = ex_eng._uid_gid_from_str("")
        self.assertEqual(status, (None, None))
        #
        status = ex_eng._uid_gid_from_str("0:0")
        self.assertEqual(status, ('0', '0'))
        #
        status = ex_eng._uid_gid_from_str("100:100")
        self.assertEqual(status, ('100', '100'))

    @mock.patch('udocker.Msg')
    @mock.patch('udocker.NixAuthentication')
    @mock.patch('udocker.LocalRepository')
    @mock.patch('udocker.ExecutionEngineCommon._create_user')
    @mock.patch('udocker.ExecutionEngineCommon._uid_gid_from_str')
    def test_10__setup_container_user(self, mock_ugfs, mock_cruser,
                                      mock_local, mock_nix, mock_msg):
        """Test ExecutionEngineCommon()._setup_container_user()."""
        self._init()
        mock_msg.level = 0
        ex_eng = udocker.ExecutionEngineCommon(mock_local)
        mock_ugfs.return_value = (None, None)
        status = ex_eng._setup_container_user("0:0")
        self.assertFalse(status)
        self.assertTrue(mock_ugfs.called_once_with("root"))
        #
        ex_eng = udocker.ExecutionEngineCommon(mock_local)
        ex_eng.opt["vol"] = ""
        ex_eng.opt["hostauth"] = False
        mock_nix.return_value.get_user.return_value = ("", "", "",
                                                       "", "", "")
        mock_ugfs.return_value = ("0", "0")
        status = ex_eng._setup_container_user("0:0")
        self.assertTrue(status)
        self.assertTrue(mock_cruser.called)
        #
        ex_eng = udocker.ExecutionEngineCommon(mock_local)
        ex_eng.opt["vol"] = ""
        ex_eng.opt["hostauth"] = False
        mock_nix.return_value.get_user.return_value = ("root", 0, 0,
                                                       "", "", "")
        mock_ugfs.return_value = ("0", "0")
        status = ex_eng._setup_container_user("0:0")
        self.assertTrue(status)
        self.assertTrue(mock_cruser.called)
        #
        ex_eng = udocker.ExecutionEngineCommon(mock_local)
        ex_eng.opt["vol"] = ""
        ex_eng.opt["hostauth"] = True
        mock_nix.return_value.get_user.return_value = ("", "", "",
                                                       "", "", "")
        mock_ugfs.return_value = ("0", "0")
        status = ex_eng._setup_container_user("0:0")
        self.assertFalse(status)
        #
        ex_eng = udocker.ExecutionEngineCommon(mock_local)
        ex_eng.opt["vol"] = ""
        ex_eng.opt["hostauth"] = True
        mock_nix.return_value.get_user.return_value = ("root", 0, 0,
                                                       "", "", "")
        mock_ugfs.return_value = ("0", "0")
        status = ex_eng._setup_container_user("0:0")
        self.assertTrue(status)
        self.assertTrue(mock_cruser.called)
        #
        ex_eng = udocker.ExecutionEngineCommon(mock_local)
        ex_eng.opt["vol"] = ""
        ex_eng.opt["hostauth"] = False
        mock_nix.return_value.get_user.return_value = ("", "", "",
                                                       "", "", "")
        status = ex_eng._setup_container_user("")
        self.assertTrue(status)
        self.assertTrue(mock_cruser.called)
        #
        ex_eng = udocker.ExecutionEngineCommon(mock_local)
        ex_eng.opt["vol"] = ""
        ex_eng.opt["hostauth"] = False
        mock_nix.return_value.get_user.return_value = ("root", 0, 0,
                                                       "", "", "")
        status = ex_eng._setup_container_user("")
        self.assertTrue(status)
        self.assertTrue(mock_cruser.called)
        #
        ex_eng = udocker.ExecutionEngineCommon(mock_local)
        ex_eng.opt["vol"] = ""
        ex_eng.opt["hostauth"] = True
        mock_nix.return_value.get_user.return_value = ("", "", "",
                                                       "", "", "")
        status = ex_eng._setup_container_user("")
        self.assertFalse(status)
        #
        ex_eng = udocker.ExecutionEngineCommon(mock_local)
        ex_eng.opt["vol"] = ""
        ex_eng.opt["hostauth"] = False
        mock_nix.return_value.get_user.return_value = ("", 100, 0,
                                                       "", "", "")
        mock_ugfs.return_value = ("0", "0")
        status = ex_eng._setup_container_user("0:0")
        self.assertTrue(status)
        self.assertTrue(mock_cruser.called)
        self.assertEqual(ex_eng.opt["user"], "")

    @mock.patch('udocker.os.getgroups')
    @mock.patch('udocker.FileUtil')
    @mock.patch('udocker.Msg')
    @mock.patch('udocker.NixAuthentication')
    @mock.patch('udocker.LocalRepository')
    def test_11__create_user(self, mock_local, mock_nix, mock_msg,
                             mock_futil, mock_groups):
        """Test ExecutionEngineCommon()._create_user()."""
        self._init()
        mock_msg.level = 0
        container_auth = udocker.NixAuthentication("", "")
        container_auth.passwd_file = ""
        container_auth.group_file = ""
        host_auth = udocker.NixAuthentication("", "")
        #
        udocker.Config.uid = 1000
        udocker.Config.gid = 1000
        mock_nix.return_value.add_user.return_value = False
        ex_eng = udocker.ExecutionEngineCommon(mock_local)
        ex_eng.opt["uid"] = ""
        ex_eng.opt["gid"] = ""
        ex_eng.opt["user"] = ""
        ex_eng.opt["home"] = ""
        ex_eng.opt["shell"] = ""
        ex_eng.opt["gecos"] = ""
        status = ex_eng._create_user(container_auth, host_auth)
        self.assertFalse(status)
        self.assertEqual(ex_eng.opt["uid"], "1000")
        self.assertEqual(ex_eng.opt["gid"], "1000")
        self.assertEqual(ex_eng.opt["user"], "udoc1000")
        self.assertEqual(ex_eng.opt["home"], "/home/udoc1000")
        self.assertEqual(ex_eng.opt["shell"], "/bin/sh")
        self.assertEqual(ex_eng.opt["gecos"], "*UDOCKER*")
        #
        mock_nix.return_value.add_user.return_value = False
        ex_eng = udocker.ExecutionEngineCommon(mock_local)
        ex_eng.opt["uid"] = "60000"
        ex_eng.opt["gid"] = "60000"
        ex_eng.opt["user"] = "someuser"
        ex_eng.opt["home"] = ""
        ex_eng.opt["shell"] = "/bin/false"
        ex_eng.opt["gecos"] = "*XXX*"
        status = ex_eng._create_user(container_auth, host_auth)
        self.assertFalse(status)
        self.assertEqual(ex_eng.opt["uid"], "60000")
        self.assertEqual(ex_eng.opt["gid"], "60000")
        self.assertEqual(ex_eng.opt["user"], "someuser")
        self.assertEqual(ex_eng.opt["home"], "/home/someuser")
        self.assertEqual(ex_eng.opt["shell"], "/bin/false")
        self.assertEqual(ex_eng.opt["gecos"], "*XXX*")
        #
        mock_nix.return_value.add_user.return_value = False
        ex_eng = udocker.ExecutionEngineCommon(mock_local)
        ex_eng.opt["uid"] = "60000"
        ex_eng.opt["gid"] = "60000"
        ex_eng.opt["user"] = "someuser"
        ex_eng.opt["home"] = "/home/batata"
        ex_eng.opt["shell"] = "/bin/false"
        ex_eng.opt["gecos"] = "*XXX*"
        status = ex_eng._create_user(container_auth, host_auth)
        self.assertFalse(status)
        self.assertEqual(ex_eng.opt["uid"], "60000")
        self.assertEqual(ex_eng.opt["gid"], "60000")
        self.assertEqual(ex_eng.opt["user"], "someuser")
        self.assertEqual(ex_eng.opt["home"], "/home/batata")
        self.assertEqual(ex_eng.opt["shell"], "/bin/false")
        self.assertEqual(ex_eng.opt["gecos"], "*XXX*")
        #
        mock_nix.return_value.add_user.return_value = True
        mock_nix.return_value.get_group.return_value = ("", "", "")
        mock_nix.return_value.add_group.return_value = True
        mock_groups.return_value = ()
        ex_eng = udocker.ExecutionEngineCommon(mock_local)
        ex_eng.opt["uid"] = "60000"
        ex_eng.opt["gid"] = "60000"
        ex_eng.opt["user"] = "someuser"
        ex_eng.opt["home"] = "/home/batata"
        ex_eng.opt["shell"] = "/bin/false"
        ex_eng.opt["gecos"] = "*XXX*"
        status = ex_eng._create_user(container_auth, host_auth)
        self.assertTrue(status)
        self.assertEqual(ex_eng.opt["uid"], "60000")
        self.assertEqual(ex_eng.opt["gid"], "60000")
        self.assertEqual(ex_eng.opt["user"], "someuser")
        self.assertEqual(ex_eng.opt["home"], "/home/batata")
        self.assertEqual(ex_eng.opt["shell"], "/bin/false")
        self.assertEqual(ex_eng.opt["gecos"], "*XXX*")
        self.assertEqual(ex_eng.opt["hostauth"], True)
        mgroup = mock_nix.return_value.get_group
        self.assertTrue(mgroup.called_once_with("60000"))
        #
        mock_nix.return_value.add_user.return_value = True
        mock_nix.return_value.get_group.return_value = ("", "", "")
        mock_nix.return_value.add_group.return_value = True
        mock_groups.return_value = (80000,)
        ex_eng = udocker.ExecutionEngineCommon(mock_local)
        ex_eng.opt["uid"] = "60000"
        ex_eng.opt["gid"] = "60000"
        ex_eng.opt["user"] = "someuser"
        ex_eng.opt["home"] = "/home/batata"
        ex_eng.opt["shell"] = "/bin/false"
        ex_eng.opt["gecos"] = "*XXX*"
        status = ex_eng._create_user(container_auth, host_auth)
        self.assertTrue(status)
        self.assertEqual(ex_eng.opt["uid"], "60000")
        self.assertEqual(ex_eng.opt["gid"], "60000")
        self.assertEqual(ex_eng.opt["user"], "someuser")
        self.assertEqual(ex_eng.opt["home"], "/home/batata")
        self.assertEqual(ex_eng.opt["shell"], "/bin/false")
        self.assertEqual(ex_eng.opt["gecos"], "*XXX*")
        self.assertEqual(ex_eng.opt["hostauth"], True)
        ggroup = mock_nix.return_value.get_group
        self.assertTrue(ggroup.called_once_with("60000"))
        agroup = mock_nix.return_value.add_group
        self.assertTrue(agroup.called_once_with("G80000", "80000"))

    @mock.patch('udocker.Msg')
    @mock.patch('udocker.os.path.basename')
    @mock.patch('udocker.LocalRepository')
    def test_12__run_banner(self, mock_local, mock_base, mock_msg):
        """Test ExecutionEngineCommon()._run_banner()."""
        self._init()
        mock_msg.level = 0
        ex_eng = udocker.ExecutionEngineCommon(mock_local)
        ex_eng._run_banner("/bin/bash")
        ex_eng.container_id = "CONTAINERID"
        self.assertTrue(mock_base.called_once_with("/bin/bash"))

    @mock.patch('udocker.Config')
    @mock.patch('udocker.os')
    @mock.patch('udocker.LocalRepository')
    def test_14__env_cleanup_dict(self, mock_local, mock_os, mock_config):
        """Test ExecutionEngineCommon()._env_cleanup()."""
        # self._init()
        udocker.Config = mock_config
        udocker.Config.valid_host_env = ("HOME",)
        mock_os.environ = {'HOME': '/', 'USERNAME': 'user', }
        ex_eng = udocker.ExecutionEngineCommon(mock_local)
        ex_eng._run_env_cleanup_dict()
        self.assertEqual(mock_os.environ, {'HOME': '/', })

    @mock.patch('udocker.Config')
    @mock.patch('udocker.LocalRepository')
    def test_15__run_env_set(self, mock_local, mock_config):
        """Test ExecutionEngineCommon()._run_env_set()."""
        # self._init()
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

    @mock.patch('udocker.ExecutionMode')
    @mock.patch('udocker.ExecutionEngineCommon._set_volume_bindings')
    @mock.patch('udocker.ExecutionEngineCommon._check_executable')
    @mock.patch('udocker.ExecutionEngineCommon._check_paths')
    @mock.patch('udocker.ExecutionEngineCommon._setup_container_user')
    @mock.patch('udocker.ExecutionEngineCommon._run_load_metadata')
    @mock.patch('udocker.LocalRepository')
    def test_16__run_init(self, mock_local, mock_loadmeta, mock_setupuser,
                          mock_chkpaths, mock_chkexec, mock_chkvol,
                          mock_execmode):
        """Test ExecutionEngineCommon()._run_init()."""
        self._init()
        mock_local.get_container_name.return_value = "cname"
        mock_loadmeta.return_value = ("/container_dir", "dummy",)
        mock_setupuser.return_value = True
        mock_chkpaths.return_value = True
        mock_chkexec.return_value = True
        ex_eng = udocker.ExecutionEngineCommon(mock_local)
        status = ex_eng._run_init("2717add4-e6f6-397c-9019-74fa67be439f")
        self.assertTrue(status)
        self.assertEqual(ex_eng.container_root, "/container_dir/ROOT")
        #
        mock_setupuser.return_value = False
        mock_chkpaths.return_value = True
        mock_chkexec.return_value = True
        status = ex_eng._run_init("2717add4-e6f6-397c-9019-74fa67be439f")
        self.assertFalse(status)
        #
        mock_setupuser.return_value = True
        mock_chkpaths.return_value = False
        mock_chkexec.return_value = True
        status = ex_eng._run_init("2717add4-e6f6-397c-9019-74fa67be439f")
        self.assertFalse(status)
        #
        mock_setupuser.return_value = True
        mock_chkpaths.return_value = True
        mock_chkexec.return_value = False
        status = ex_eng._run_init("2717add4-e6f6-397c-9019-74fa67be439f")
        self.assertFalse(status)

    @mock.patch('udocker.NixAuthentication')
    @mock.patch('udocker.LocalRepository')
    def test_17__get_bindhome(self, mock_local, mock_nixauth):
        """Test ExecutionEngine()._get_bindhome()."""
        self._init()
        #
        mock_nixauth.return_value.get_home.return_value = ""
        prex = udocker.ExecutionEngineCommon(mock_local)
        prex.opt["bindhome"] = False
        status = prex._get_bindhome()
        self.assertEqual(status, "")
        #
        mock_nixauth.return_value.get_home.return_value = "/home/user"
        prex = udocker.ExecutionEngineCommon(mock_local)
        prex.opt["bindhome"] = True
        status = prex._get_bindhome()
        self.assertEqual(status, "/home/user")
        #
        mock_nixauth.return_value.get_home.return_value = ""
        prex = udocker.ExecutionEngineCommon(mock_local)
        prex.opt["bindhome"] = True
        status = prex._get_bindhome()
        self.assertEqual(status, "")

    @mock.patch('udocker.os.path.exists')
    @mock.patch('udocker.LocalRepository')
    def test_18__create_mountpoint(self, mock_local, mock_exists):
        """Test ExecutionEngine()._create_mountpoint()."""
        self._init()
        mock_exists.return_value = False
        exc = udocker.ExecutionEngineCommon(mock_local)
        status = exc._create_mountpoint("", "")
        self.assertFalse(status)

        mock_exists.return_value = True
        exc = udocker.ExecutionEngineCommon(mock_local)
        status = exc._create_mountpoint("", "")
        self.assertTrue(status)

    @mock.patch('udocker.os.path.exists')
    @mock.patch('udocker.LocalRepository')
    def test_19__check_volumes(self, mock_local, mock_exists):
        """."""
        self._init()

        exc = udocker.ExecutionEngineCommon(mock_local)
        exc.opt["vol"] = ()
        status = exc._check_volumes()
        self.assertTrue(status)

        mock_exists.return_value = False
        exc = udocker.ExecutionEngineCommon(mock_local)
        status = exc._check_volumes()
        self.assertTrue(status)

    @mock.patch('udocker.LocalRepository')
    def test_19__is_volume(self, mock_local):
        """."""
        self._init()

        exc = udocker.ExecutionEngineCommon(mock_local)
        exc.opt["vol"] = ["/tmp"]
        status = exc._is_volume("/tmp")
        self.assertTrue(status)

        exc = udocker.ExecutionEngineCommon(mock_local)
        exc.opt["vol"] = [""]
        status = exc._is_volume("/tmp")
        self.assertFalse(status)


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
        udocker.Config.cpu_affinity_exec_tools = (["numactl", "-C", "%s", "--", ],
                               ["taskset", "-c", "%s", ])
        udocker.Config.valid_host_env = "HOME"
        udocker.Config.return_value.username.return_value = "user"
        udocker.Config.return_value.userhome.return_value = "/"
        udocker.Config.return_value.oskernel.return_value = "4.8.13"
        udocker.Config.location = ""

    @mock.patch('udocker.ExecutionEngineCommon')
    @mock.patch('udocker.LocalRepository')
    def test_01_init(self, mock_local, mock_exeng):
        """Test PRootEngine()."""
        self._init()
        prex = udocker.PRootEngine(mock_local)
        self.assertFalse(prex.proot_noseccomp)
        self.assertEqual(prex._kernel, "4.8.13")
        self.assertEqual(prex.proot_exec, None)

    @mock.patch('udocker.Config')
    @mock.patch('udocker.ExecutionMode')
    @mock.patch('udocker.FileUtil.find_file_in_dir')
    @mock.patch('udocker.LocalRepository')
    def test_03__select_proot(self, mock_local, mock_fimage, mock_execmode,
                              mock_config):
        """Test PRootEngine()._select_proot()."""
        self._init()
        udocker.Config.return_value.arch.return_value = "amd64"
        udocker.Config.return_value.oskernel_isgreater.return_value = False
        mock_fimage.return_value = "proot-4_8_0"
        mock_execmode.return_value.get_mode.return_value = ""
        udocker.Config.return_value.proot_noseccomp = None
        prex = udocker.PRootEngine(mock_local)
        prex.exec_mode = mock_execmode
        prex._select_proot()
        self.assertFalse(prex.proot_noseccomp)
        #
        udocker.Config.return_value.oskernel_isgreater.return_value = True
        mock_fimage.return_value = "proot"
        prex = udocker.PRootEngine(mock_local)
        prex.exec_mode = mock_execmode
        udocker.Config.return_value.proot_noseccomp = True
        prex._select_proot()
        self.assertTrue(prex.proot_noseccomp)
        #
        udocker.Config.return_value.oskernel_isgreater.return_value = True
        mock_fimage.return_value = "proot"
        prex = udocker.PRootEngine(mock_local)
        prex.exec_mode = mock_execmode
        udocker.Config.return_value.proot_noseccomp = False
        prex._select_proot()
        self.assertFalse(prex.proot_noseccomp)
        #
        udocker.Config.return_value.oskernel_isgreater.return_value = True
        mock_fimage.return_value = "proot-x86_64-4_8_0"
        prex = udocker.PRootEngine(mock_local)
        prex.exec_mode = mock_execmode
        udocker.Config.return_value.proot_noseccomp = None
        prex._select_proot()
        self.assertFalse(prex.proot_noseccomp)
        #
        udocker.Config.return_value.oskernel_isgreater.return_value = True
        mock_fimage.return_value = "proot-x86_64-4_8_0"
        prex = udocker.PRootEngine(mock_local)
        prex.exec_mode = mock_execmode
        udocker.Config.return_value.proot_noseccomp = False
        prex._select_proot()
        self.assertFalse(prex.proot_noseccomp)
        #
        udocker.Config.return_value.oskernel_isgreater.return_value = True
        mock_fimage.return_value = "proot-x86_64-4_8_0"
        prex = udocker.PRootEngine(mock_local)
        prex.exec_mode = mock_execmode
        udocker.Config.return_value.proot_noseccomp = True
        prex._select_proot()
        self.assertTrue(prex.proot_noseccomp)

    @mock.patch('udocker.LocalRepository')
    def test_04__set_uid_map(self, mock_local):
        """Test PRootEngine()._set_uid_map()."""
        self._init()
        prex = udocker.PRootEngine(mock_local)
        prex.opt["uid"] = "0"
        status = prex._set_uid_map()
        self.assertEqual(status, ['-0'])
        #
        prex = udocker.PRootEngine(mock_local)
        prex.opt["uid"] = "1000"
        prex.opt["gid"] = "1001"
        status = prex._set_uid_map()
        self.assertEqual(status, ['-i', '1000:1001'])

    @mock.patch('udocker.LocalRepository')
    def test_05__get_volume_bindings(self, mock_local):
        """Test PRootEngine()._get_volume_bindings()."""
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

    @mock.patch('udocker.LocalRepository')
    def test_06__create_mountpoint(self, mock_local):
        """Test PRootEngine()._create_mountpoint()."""
        self._init()
        prex = udocker.PRootEngine(mock_local)
        status = prex._create_mountpoint("", "")
        self.assertTrue(status)

    @mock.patch('udocker.subprocess.call')
    @mock.patch('udocker.PRootEngine._run_banner')
    @mock.patch('udocker.PRootEngine._run_env_cleanup_dict')
    @mock.patch('udocker.PRootEngine._set_uid_map')
    @mock.patch('udocker.PRootEngine._get_volume_bindings')
    @mock.patch('udocker.PRootEngine._set_cpu_affinity')
    @mock.patch('udocker.PRootEngine._check_env')
    @mock.patch('udocker.PRootEngine._run_env_set')
    @mock.patch('udocker.os.getenv')
    @mock.patch('udocker.PRootEngine._select_proot')
    @mock.patch('udocker.ExecutionEngineCommon._run_init')
    @mock.patch('udocker.LocalRepository')
    def test_07_run(self, mock_local, mock_run_init, mock_sel_proot,
                    mock_getenv, mock_run_env_set, mock_check_env,
                    mock_set_cpu_aff, mock_get_vol_bind, mock_set_uid_map,
                    mock_env_cleanup_dict, mock_run_banner, mock_call):
        """Test PRootEngine().run()."""
        mock_run_init.return_value = False
        self._init()
        prex = udocker.PRootEngine(mock_local)
        status = prex.run("CONTAINERID")
        self.assertEqual(status, 2)
        #
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
        #
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
        udocker.Config.cpu_affinity_exec_tools = (["numactl", "-C", "%s", "--", ],
                               ["taskset", "-c", "%s", ])
        udocker.Config.valid_host_env = "HOME"
        udocker.Config.return_value.username.return_value = "user"
        udocker.Config.return_value.userhome.return_value = "/"
        udocker.Config.return_value.oskernel.return_value = "4.8.13"
        udocker.Config.location = ""

    @mock.patch('udocker.ExecutionEngineCommon')
    @mock.patch('udocker.LocalRepository')
    def test_01_init(self, mock_local, mock_exeng):
        """Test RuncEngine()."""
        self._init()
        rcex = udocker.RuncEngine(mock_local)
        self.assertEqual(rcex.runc_exec, None)

    @mock.patch('udocker.Config')
    @mock.patch('udocker.ExecutionMode')
    @mock.patch('udocker.FileUtil')
    @mock.patch('udocker.LocalRepository')
    def test_03__select_runc(self, mock_local, mock_futil, mock_execmode,
                             mock_config):
        """Test RuncEngine()._select_runc()."""
        self._init()
        udocker.Config.return_value.arch.return_value = "arm"
        udocker.Config.return_value.oskernel_isgreater.return_value = False
        mock_futil.return_value.find_file_in_dir.return_value = "runc-arm"
        mock_execmode.return_value.get_mode.return_value = ""
        rcex = udocker.RuncEngine(mock_local)
        rcex.exec_mode = mock_execmode
        rcex._select_runc()
        self.assertEqual(rcex.runc_exec, "runc-arm")

    @mock.patch('udocker.json.load')
    @mock.patch('udocker.subprocess.call')
    @mock.patch('udocker.os.path.realpath')
    @mock.patch('udocker.FileUtil')
    @mock.patch('udocker.LocalRepository')
    def test_04__load_spec(self, mock_local, mock_futil, mock_realpath,
                           mock_call, mock_jsonload):
        """Test RuncEngine()._load_spec()."""
        self._init()
        mock_futil.reset()
        mock_futil.return_value.size.return_value = 1
        rcex = udocker.RuncEngine(mock_local)
        rcex._load_spec(False)
        self.assertFalse(mock_futil.return_value.remove.called)
        #
        mock_futil.reset()
        mock_futil.return_value.size.return_value = 1
        rcex = udocker.RuncEngine(mock_local)
        rcex._load_spec(True)
        self.assertTrue(mock_futil.return_value.remove.called)
        #
        mock_futil.reset()
        mock_futil.return_value.size.return_value = -1
        mock_realpath.return_value = "/.udocker/containers/aaaaa"
        mock_call.return_value = True
        rcex = udocker.RuncEngine(mock_local)
        rcex.runc_exec = "runc"
        status = rcex._load_spec(False)
        self.assertFalse(status)
        #
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
        #
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
    def test_05__save_spec(self, mock_local, mock_jsondump):
        """Test RuncEngine()._save_spec()."""
        self._init()
        rcex = udocker.RuncEngine(mock_local)
        rcex._container_specjson = "JSON"
        with mock.patch(BUILTINS + '.open', mock.mock_open()):
            status = rcex._save_spec()
        self.assertTrue(status)
        #
        mock_jsondump.side_effect = OSError("in open")
        rcex = udocker.RuncEngine(mock_local)
        rcex._container_specjson = "JSON"
        with mock.patch(BUILTINS + '.open', mock.mock_open()):
            status = rcex._save_spec()
        self.assertFalse(status)

    @mock.patch('udocker.os.getgid')
    @mock.patch('udocker.os.getuid')
    @mock.patch('udocker.platform.node')
    @mock.patch('udocker.os.path.realpath')
    @mock.patch('udocker.LocalRepository')
    def test_06__set_spec(self, mock_local, mock_realpath, mock_node,
                          mock_getuid, mock_getgid):
        """Test RuncEngine()._set_spec()."""
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
        """Test RuncEngine()._uid_check()."""
        self._init()
        #
        mock_msg.reset_mock()
        rcex = udocker.RuncEngine(mock_local)
        rcex.opt = dict()
        rcex._uid_check()
        self.assertFalse(mock_msg.called)
        #
        mock_msg.reset_mock()
        rcex = udocker.RuncEngine(mock_local)
        rcex.opt = dict()
        rcex.opt["user"] = "root"
        rcex._uid_check()
        self.assertFalse(mock_msg.called)
        #
        mock_msg.reset_mock()
        rcex = udocker.RuncEngine(mock_local)
        rcex.opt = dict()
        rcex.opt["user"] = "user01"
        rcex._uid_check()
        self.assertTrue(mock_msg.called)

    @mock.patch('udocker.LocalRepository')
    def test_08__create_mountpoint(self, mock_local):
        """Test RuncEngine()._create_mountpoint()."""
        self._init()
        rcex = udocker.RuncEngine(mock_local)
        status = rcex._create_mountpoint("HOSTPATH", "CONTPATH")
        self.assertTrue(status)

    @mock.patch('udocker.LocalRepository')
    def test_09__add_mount_spec(self, mock_local):
        """Test RuncEngine()._add_mount_spec()."""
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
    def test_10__del_mount_spec(self, mock_local):
        """Test RuncEngine()._del_mount_spec()."""
        self._init()
        #
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
        self.assertEqual(len(rcex._container_specjson["mounts"]), 0)
        #
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
        #
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
    def test_11__add_volume_bindings(self, mock_local, mock_fbind,
                                     mock_add_mount_spec,
                                     mock_isdir, mock_isfile, mock_msg):
        """Test RuncEngine()._add_volume_bindings()."""
        self._init()
        #
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
        self.assertTrue(mock_fbind.add.called)
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
    def test_12__check_env(self, mock_local, mock_getenv, mock_msg):
        """Test RuncEngine()._check_env()."""
        self._init()
        #
        rcex = udocker.RuncEngine(mock_local)
        rcex.opt["env"] = []
        status = rcex._check_env()
        self.assertTrue(status)
        #
        mock_getenv.return_value = "aaaa"
        rcex = udocker.RuncEngine(mock_local)
        rcex.opt["env"] = ["", "HOME=/home/user01", "AAAA", ]
        status = rcex._check_env()
        self.assertTrue(status)
        self.assertNotIn("", rcex.opt["env"])
        self.assertIn("AAAA=aaaa", rcex.opt["env"])
        self.assertIn("HOME=/home/user01", rcex.opt["env"])
        #
        rcex = udocker.RuncEngine(mock_local)
        rcex.opt["env"] = ["3WRONG=/home/user01", ]
        status = rcex._check_env()
        self.assertFalse(status)
        #
        rcex = udocker.RuncEngine(mock_local)
        rcex.opt["env"] = ["WR ONG=/home/user01", ]
        status = rcex._check_env()
        self.assertFalse(status)

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
    @mock.patch('udocker.RuncEngine._select_runc')
    @mock.patch('udocker.RuncEngine._run_init')
    @mock.patch('udocker.LocalRepository')
    def test_16_run(self, mock_local, mock_run_init, mock_sel_runc,
                    mock_load_spec, mock_uid_check,
                    mock_run_env_cleanup_list, mock_env_set, mock_check_env,
                    mock_set_spec, mock_add_bindings, mock_save_spec,
                    mock_run_banner, mock_del_mount_spec, mock_inv_opt,
                    mock_unique, mock_fbind, mock_msg, mock_call):
        """Test RuncEngine().run()."""
        self._init()
        #
        mock_run_init.return_value = False
        rcex = udocker.RuncEngine(mock_local)
        status = rcex.run("CONTAINERID")
        self.assertEqual(status, 2)
        #
        mock_run_init.return_value = True
        mock_load_spec.return_value = False
        rcex = udocker.RuncEngine(mock_local)
        status = rcex.run("CONTAINERID")
        self.assertEqual(status, 4)
        #
        mock_run_init.return_value = True
        mock_load_spec.return_value = True
        mock_check_env.return_value = False
        mock_run_env_cleanup_list.reset_mock()
        rcex = udocker.RuncEngine(mock_local)
        rcex.opt["hostenv"] = []
        status = rcex.run("CONTAINERID")
        self.assertTrue(mock_run_env_cleanup_list.called)
        self.assertEqual(status, 5)
        #
        mock_run_init.return_value = True
        mock_load_spec.return_value = True
        mock_check_env.return_value = True
        mock_unique.return_value.uuid.return_value = "EXECUTION_ID"
        mock_run_env_cleanup_list.reset_mock()
        mock_call.reset_mock()
        rcex = udocker.RuncEngine(mock_local)
        rcex.runc_exec = "true"
        rcex.container_dir = "/.udocker/containers/CONTAINER/ROOT"
        rcex.opt["hostenv"] = []
        status = rcex.run("CONTAINERID")
        self.assertTrue(mock_run_env_cleanup_list.called)
        #self.assertTrue(mock_call.called)


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
        udocker.Config.cpu_affinity_exec_tools = (["numactl", "-C", "%s", "--", ],
                               ["taskset", "-c", "%s", ])
        udocker.Config.valid_host_env = "HOME"
        udocker.Config.return_value.username.return_value = "user"
        udocker.Config.return_value.userhome.return_value = "/"
        udocker.Config.return_value.oskernel.return_value = "4.8.13"
        udocker.Config.location = ""

    @mock.patch('udocker.LocalRepository')
    def test_01__init(self, mock_local):
        """Test FakechrootEngine Constructor."""
        self._init()

        ufake = udocker.FakechrootEngine(mock_local)
        self.assertEqual(ufake._fakechroot_so, "")
        self.assertIsNone(ufake._elfpatcher)

    @mock.patch('udocker.Msg')
    @mock.patch('udocker.os.path')
    @mock.patch('udocker.Config')
    @mock.patch('udocker.FileUtil')
    @mock.patch('udocker.LocalRepository')
    def test_02__select_fakechroot_so(self, mock_local, mock_futil,
                                      mock_config, mock_path, mock_msg):
        """Select fakechroot sharable object library."""

        self._init()

        #ufake = udocker.FakechrootEngine(mock_local)
        #out = ufake._select_fakechroot_so()
        #self.assertTrue(mock_msg.return_value.err.called)


    @mock.patch('udocker.Msg')
    @mock.patch('udocker.LocalRepository')
    def test_03__uid_check(self, mock_local, mock_msg):
        """Set the uid_map string for container run command"""
        self._init()

        ufake = udocker.FakechrootEngine(mock_local)
        ufake.opt["user"] = "root"
        ufake._uid_check_noroot()
        self.assertTrue(mock_msg.return_value.err.called)

    @mock.patch('udocker.Msg')
    @mock.patch('udocker.LocalRepository')
    @mock.patch('udocker.NixAuthentication')
    @mock.patch('udocker.ExecutionEngineCommon')
    def test_04__setup_container_user(self, mock_eecom, mock_auth,
                                      mock_local, mock_msg):
        """ Override method ExecutionEngineCommon._setup_container_user()."""
        self._init()

        mock_eecom.return_value._uid_gid_from_str.side_effect = (None, None)
        ufake = udocker.FakechrootEngine(mock_local)
        status = ufake._setup_container_user(":lalves")
        self.assertFalse(status)

    @mock.patch('udocker.LocalRepository')
    def test_05__get_volume_bindings(self, mock_local):
        """Get the volume bindings string for fakechroot run."""
        self._init()

        ufake = udocker.FakechrootEngine(mock_local)
        out = ufake._get_volume_bindings()
        self.assertEqual(out, ("", ""))

    @mock.patch('udocker.LocalRepository')
    def test_06__get_access_filesok(self, mock_local):
        """Circumvent mpi init issues when calling access().

        A list of certain existing files is provided
        """
        self._init()

        ufake = udocker.FakechrootEngine(mock_local)
        out = ufake._get_access_filesok()
        self.assertEqual(out, "")

    @mock.patch('udocker.FileUtil')
    @mock.patch('udocker.Msg')
    @mock.patch('udocker.ContainerStructure')
    @mock.patch('udocker.LocalRepository')
    def test_07__fakechroot_env_set(self, mock_local, mock_struct,
                                    mock_msg, mock_futil):
        """fakechroot environment variables to set."""
        self._init()

        # mock_futil.return_value.find_file_in_dir.return_value = True
        # ufake = udocker.FakechrootEngine(mock_local)
        #
        # ufake._fakechroot_env_set()
        # self.assertTrue(mock_eecom.return_value.exec_mode.called)

    @mock.patch('udocker.Msg')
    @mock.patch('udocker.ContainerStructure')
    @mock.patch('udocker.LocalRepository')
    def test_08_run(self, mock_local, mock_struct, mock_msg):
        """Execute a Docker container using Fakechroot.

        This is the main
        method invoked to run the a container with Fakechroot.
          * argument: container_id or name
          * options:  many via self.opt see the help
        """
        self._init()

        ufake = udocker.FakechrootEngine(mock_local)
        status = ufake.run("container_id")
        self.assertEqual(status, 2)


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
        udocker.Config.cpu_affinity_exec_tools = (["numactl", "-C", "%s", "--", ],
                               ["taskset", "-c", "%s", ])
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
        """Test __init__()."""

        self._init()
        container_id = "CONTAINER_ID"
        mock_realpath.return_value = "/tmp"
        mock_local.cd_container.return_value = "/tmp"
        uexm = udocker.ExecutionMode(mock_local, container_id)

        self.assertEqual(uexm.localrepo, mock_local)
        self.assertEqual(uexm.container_id, "CONTAINER_ID")
        self.assertEqual(uexm.container_dir, "/tmp")
        self.assertEqual(uexm.container_root, "/tmp/ROOT")
        self.assertEqual(uexm.container_execmode, "/tmp/execmode")
        self.assertIsNone(uexm.exec_engine)
        self.assertEqual(uexm.valid_modes,
                         ("P1", "P2", "F1", "F2", "F3", "F4", "R1", "S1"))

    @mock.patch('udocker.os.path')
    @mock.patch('udocker.FileUtil')
    @mock.patch('udocker.LocalRepository')
    def test_02_get_mode(self, mock_local, mock_futil, mock_path):
        """Get execution mode"""

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
        """Set execution mode."""

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
        """get execution engine instance"""

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
        udocker.Config.cpu_affinity_exec_tools = (["numactl", "-C", "%s", "--", ],
                               ["taskset", "-c", "%s", ])
        udocker.Config.valid_host_env = "HOME"
        udocker.Config.return_value.username.return_value = "user"
        udocker.Config.return_value.userhome.return_value = "/"
        udocker.Config.location = ""
        udocker.Config.return_value.oskernel.return_value = "4.8.13"

    @mock.patch('udocker.LocalRepository')
    def test_01_init(self, mock_local):
        """Test ContainerStructure()."""
        self._init()
        #
        prex = udocker.ContainerStructure(mock_local)
        self.assertEqual(prex.tag, "")
        self.assertEqual(prex.imagerepo, "")
        #
        prex = udocker.ContainerStructure(mock_local, "123456")
        self.assertEqual(prex.tag, "")
        self.assertEqual(prex.imagerepo, "")
        self.assertEqual(prex.container_id, "123456")

    @mock.patch('udocker.Msg')
    @mock.patch('udocker.LocalRepository')
    def test_02_get_container_attr(self, mock_local, mock_msg):
        """Test ContainerStructure().get_container_attr()."""
        self._init()
        mock_msg.level = 0
        #
        prex = udocker.ContainerStructure(mock_local)
        udocker.Config.location = "/"
        (container_dir, container_json) = prex.get_container_attr()
        self.assertEqual(container_dir, "")
        self.assertEqual(container_json, [])
        #
        prex = udocker.ContainerStructure(mock_local)
        udocker.Config.location = ""
        mock_local.cd_container.return_value = ""
        (container_dir, container_json) = prex.get_container_attr()
        self.assertEqual(container_dir, False)
        self.assertEqual(container_json, False)
        #
        prex = udocker.ContainerStructure(mock_local)
        udocker.Config.location = ""
        mock_local.cd_container.return_value = "/"
        mock_local.load_json.return_value = []
        (container_dir, container_json) = prex.get_container_attr()
        self.assertEqual(container_dir, False)
        self.assertEqual(container_json, False)
        #
        prex = udocker.ContainerStructure(mock_local)
        udocker.Config.location = ""
        mock_local.cd_container.return_value = "/"
        mock_local.load_json.return_value = ["value", ]
        (container_dir, container_json) = prex.get_container_attr()
        self.assertEqual(container_dir, "/")
        self.assertEqual(container_json, ["value", ])

    @mock.patch('udocker.ContainerStructure._untar_layers')
    @mock.patch('udocker.Unique')
    @mock.patch('udocker.Msg')
    @mock.patch('udocker.LocalRepository')
    def test_03_create(self, mock_local, mock_msg, mock_unique,
                       mock_untar):
        """Test ContainerStructure().create()."""
        self._init()
        mock_msg.level = 0
        #
        prex = udocker.ContainerStructure(mock_local)
        mock_local.cd_imagerepo.return_value = ""
        status = prex.create_fromimage("imagerepo", "tag")
        self.assertFalse(status)
        #
        prex = udocker.ContainerStructure(mock_local)
        mock_local.cd_imagerepo.return_value = "/"
        mock_local.get_image_attributes.return_value = ([], [])
        status = prex.create_fromimage("imagerepo", "tag")
        self.assertFalse(status)
        #
        prex = udocker.ContainerStructure(mock_local)
        mock_local.cd_imagerepo.return_value = "/"
        mock_local.get_image_attributes.return_value = (["value", ], [])
        mock_local.setup_container.return_value = ""
        status = prex.create_fromimage("imagerepo", "tag")
        self.assertFalse(status)
        #
        prex = udocker.ContainerStructure(mock_local)
        mock_local.cd_imagerepo.return_value = "/"
        mock_local.get_image_attributes.return_value = (["value", ], [])
        mock_local.setup_container.return_value = "/"
        mock_untar.return_value = False
        mock_unique.return_value.uuid.return_value = "123456"
        status = prex.create_fromimage("imagerepo", "tag")
        self.assertEqual(status, "123456")

    @mock.patch('udocker.FileUtil')
    @mock.patch('udocker.Msg')
    @mock.patch('udocker.LocalRepository')
    def test_04__apply_whiteouts(self, mock_local, mock_msg, mock_futil):
        """Test ContainerStructure()._apply_whiteouts()."""
        self._init()
        mock_msg.level = 0
        #
        prex = udocker.ContainerStructure(mock_local)
        with mock.patch.object(subprocess, 'Popen') as mock_popen:
            mock_popen.return_value.stdout.readline.side_effect = [
                "/aaa", "",
            ]
            status = prex._apply_whiteouts("tarball", "/tmp")
        self.assertTrue(status)
        self.assertFalse(mock_futil.called)
        #
        prex = udocker.ContainerStructure(mock_local)
        with mock.patch.object(subprocess, 'Popen') as mock_popen:
            mock_popen.return_value.stdout.readline.side_effect = ["/a/.wh.x",
                                                                   "", ]
            status = prex._apply_whiteouts("tarball", "/tmp")
        self.assertTrue(status)
        self.assertTrue(mock_futil.called)

    @mock.patch('udocker.subprocess.call')
    @mock.patch('udocker.ContainerStructure._apply_whiteouts')
    @mock.patch('udocker.Msg')
    @mock.patch('udocker.LocalRepository')
    def test_05__untar_layers(self, mock_local, mock_msg, mock_appwhite,
                              mock_call):
        """Test ContainerStructure()._untar_layers()."""
        self._init()
        mock_msg.level = 0
        tarfiles = ["a.tar", "b.tar", ]
        #
        mock_call.return_value = False
        prex = udocker.ContainerStructure(mock_local)
        status = prex._untar_layers(tarfiles, "/tmp")
        self.assertTrue(status)
        self.assertTrue(mock_call.called)
        #
        mock_call.reset_mock()
        mock_call.return_value = True
        prex = udocker.ContainerStructure(mock_local)
        status = prex._untar_layers(tarfiles, "/tmp")
        self.assertFalse(status)
        self.assertTrue(mock_call.called)
        #
        mock_call.reset_mock()
        mock_call.return_value = True
        prex = udocker.ContainerStructure(mock_local)
        status = prex._untar_layers([], "/tmp")
        self.assertFalse(status)
        self.assertFalse(mock_call.called)

    @mock.patch('udocker.Msg')
    @mock.patch('udocker.LocalRepository')
    def test_06_get_container_meta(self, mock_local, mock_msg):
        """Test ContainerStructure().get_container_meta()."""
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
        #
        prex = udocker.ContainerStructure(mock_local)
        status = prex.get_container_meta("Cmd", "", container_json)
        self.assertEqual(status, "/bin/bash")
        #
        status = prex.get_container_meta("XXX", "", container_json)
        self.assertEqual(status, "")
        #self.assertEqual(status, None)
        #
        status = prex.get_container_meta("Entrypoint", "BBB", container_json)
        self.assertEqual(status, "BBB")

    @mock.patch('udocker.Msg')
    @mock.patch('udocker.LocalRepository')
    def test_07__dict_to_str(self, mock_local, mock_msg):
        """Test ContainerStructure()._dict_to_str()."""
        self._init()
        mock_msg.level = 0
        #
        prex = udocker.ContainerStructure(mock_local)
        status = prex._dict_to_str({'A': 1, 'B': 2})
        self.assertTrue(status in ("A:1 B:2 ", "B:2 A:1 ", ))
        #self.assertEqual(status, "A:1 B:2 ")

    @mock.patch('udocker.Msg')
    @mock.patch('udocker.LocalRepository')
    def test_08__dict_to_list(self, mock_local, mock_msg):
        """Test ContainerStructure()._dict_to_list()."""
        self._init()
        mock_msg.level = 0
        #
        prex = udocker.ContainerStructure(mock_local)
        status = prex._dict_to_list({'A': 1, 'B': 2})
        self.assertEqual(sorted(status), sorted(["A:1", "B:2"]))


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
        udocker.Config.cpu_affinity_exec_tools = (["numactl", "-C", "%s", "--", ],
                               ["taskset", "-c", "%s", ])
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
        """Test DockerLocalFileAPI() constructor."""
        self._init()
        dlocapi = udocker.DockerLocalFileAPI(mock_local)
        self.assertEqual(dlocapi.localrepo, mock_local)

    @mock.patch('udocker.os.listdir')
    @mock.patch('udocker.FileUtil')
    @mock.patch('udocker.LocalRepository')
    def test_02__load_structure(self, mock_local, mock_futil, mock_ldir):
        """Test DockerLocalFileAPI()._load_structure()."""
        self._init()
        #
        dlocapi = udocker.DockerLocalFileAPI(mock_local)
        mock_futil.return_value.isdir.return_value = False
        structure = dlocapi._load_structure("/tmp")
        self.assertEqual(structure, {'layers': {}})
        #
        dlocapi = udocker.DockerLocalFileAPI(mock_local)
        mock_futil.return_value.isdir.return_value = True
        mock_ldir.return_value = ["repositories", ]
        mock_local.load_json.return_value = {"REPO": "", }
        structure = dlocapi._load_structure("/tmp")
        expected = {'layers': {}, 'repositories': {'REPO': ''}}
        self.assertEqual(structure, expected)
        #
        dlocapi = udocker.DockerLocalFileAPI(mock_local)
        mock_futil.return_value.isdir.return_value = True
        mock_ldir.return_value = ["manifest.json", ]
        structure = dlocapi._load_structure("/tmp")
        expected = {'layers': {}}
        self.assertEqual(structure, expected)
        #
        dlocapi = udocker.DockerLocalFileAPI(mock_local)
        mock_futil.return_value.isdir.return_value = True
        mock_ldir.return_value = ["x" * 64 + ".json", ]
        structure = dlocapi._load_structure("/tmp")
        expected = {'layers': {}}
        self.assertEqual(structure, expected)
        #
        dlocapi = udocker.DockerLocalFileAPI(mock_local)
        mock_futil.return_value.isdir.return_value = True
        mock_ldir.side_effect = [["x" * 64, ], ["VERSION", ], ]
        mock_local.load_json.return_value = {"X": "", }
        structure = dlocapi._load_structure("/tmp")
        expected = {'layers': {"x" * 64: {'VERSION': {'X': ''}}}}
        self.assertEqual(structure, expected)
        #
        dlocapi = udocker.DockerLocalFileAPI(mock_local)
        mock_futil.return_value.isdir.return_value = True
        mock_ldir.side_effect = [["x" * 64, ], ["json", ], ]
        mock_local.load_json.return_value = {"X": "", }
        structure = dlocapi._load_structure("/tmp")
        expected = {'layers': {"x" * 64: {'json': {'X': ''},
                                          'json_f': '/tmp/' + "x" * 64 + '/json'}}}
        self.assertEqual(structure, expected)
        #
        dlocapi = udocker.DockerLocalFileAPI(mock_local)
        mock_futil.return_value.isdir.return_value = True
        mock_ldir.side_effect = [["x" * 64, ], ["layer", ], ]
        mock_local.load_json.return_value = {"X": "", }
        structure = dlocapi._load_structure("/tmp")
        expected = {'layers': {"x" * 64: {
            'layer_f': '/tmp/' + "x" * 64 + '/layer'}}}
        self.assertEqual(structure, expected)

    @mock.patch('udocker.LocalRepository')
    def test_03__find_top_layer_id(self, mock_local):
        """Test DockerLocalFileAPI()._find_top_layer_id()."""
        self._init()
        #
        dlocapi = udocker.DockerLocalFileAPI(mock_local)
        structure = {}
        status = dlocapi._find_top_layer_id(structure)
        self.assertFalse(status)
        #
        dlocapi = udocker.DockerLocalFileAPI(mock_local)
        structure = {'layers': {"LID": {"json": {}, }, }, }
        status = dlocapi._find_top_layer_id(structure)
        self.assertEqual(status, "LID")
        #
        dlocapi = udocker.DockerLocalFileAPI(mock_local)
        structure = {'layers': {"LID": {"json": {"parent": "x", }, }, }, }
        status = dlocapi._find_top_layer_id(structure)
        self.assertEqual(status, "LID")

    @mock.patch('udocker.LocalRepository')
    def test_04__sorted_layers(self, mock_local):
        """Test DockerLocalFileAPI()._sorted_layers()."""
        self._init()
        #
        dlocapi = udocker.DockerLocalFileAPI(mock_local)
        structure = {}
        status = dlocapi._sorted_layers(structure, "")
        self.assertFalse(status)
        #
        dlocapi = udocker.DockerLocalFileAPI(mock_local)
        structure = {'layers': {"LID": {"json": {"parent": {}, }, }, }, }
        status = dlocapi._sorted_layers(structure, "LID")
        self.assertEqual(status, ["LID"])

    @mock.patch('udocker.os.rename')
    @mock.patch('udocker.LocalRepository')
    def test_05__copy_layer_to_repo(self, mock_local, mock_rename):
        """Test DockerLocalFileAPI()._copy_layer_to_repo()."""
        self._init()
        mock_local.layersdir = ""
        #
        dlocapi = udocker.DockerLocalFileAPI(mock_local)
        status = dlocapi._copy_layer_to_repo("/", "LID")
        self.assertFalse(status)
        #
        dlocapi = udocker.DockerLocalFileAPI(mock_local)
        status = dlocapi._copy_layer_to_repo("/xxx.json", "LID")
        self.assertTrue(status)

    @mock.patch('udocker.DockerLocalFileAPI._copy_layer_to_repo')
    @mock.patch('udocker.DockerLocalFileAPI._sorted_layers')
    @mock.patch('udocker.DockerLocalFileAPI._find_top_layer_id')
    @mock.patch('udocker.Msg')
    @mock.patch('udocker.LocalRepository')
    def test_06__load_image(self, mock_local, mock_msg, mock_findtop,
                            mock_slayers, mock_copylayer):
        """Test DockerLocalFileAPI()._load_image()."""
        self._init()
        mock_msg.level = 0
        #
        dlocapi = udocker.DockerLocalFileAPI(mock_local)
        mock_local.cd_imagerepo.return_value = True
        structure = {}
        status = dlocapi._load_image(structure, "IMAGE", "TAG")
        self.assertFalse(status)
        #
        dlocapi = udocker.DockerLocalFileAPI(mock_local)
        mock_local.cd_imagerepo.return_value = False
        mock_local.setup_tag.return_value = ""
        structure = {}
        status = dlocapi._load_image(structure, "IMAGE", "TAG")
        self.assertFalse(status)
        #
        dlocapi = udocker.DockerLocalFileAPI(mock_local)
        mock_local.cd_imagerepo.return_value = False
        mock_local.setup_tag.return_value = "/dir"
        mock_local.set_version.return_value = False
        structure = {}
        status = dlocapi._load_image(structure, "IMAGE", "TAG")
        self.assertFalse(status)
        #
        dlocapi = udocker.DockerLocalFileAPI(mock_local)
        mock_local.cd_imagerepo.return_value = False
        mock_local.setup_tag.return_value = "/dir"
        mock_local.set_version.return_value = True
        mock_findtop.return_value = "TLID"
        mock_slayers.return_value = []
        structure = {}
        status = dlocapi._load_image(structure, "IMAGE", "TAG")
        self.assertEqual(status, ['IMAGE:TAG'])
        #
        dlocapi = udocker.DockerLocalFileAPI(mock_local)
        mock_local.cd_imagerepo.return_value = False
        mock_local.setup_tag.return_value = "/dir"
        mock_local.set_version.return_value = True
        mock_findtop.return_value = "TLID"
        mock_slayers.return_value = ["LID", ]
        mock_copylayer.return_value = False
        structure = {'layers': {'LID': {'VERSION': "1.0",
                                        'json_f': "f1",
                                        'layer_f': "f1", }, }, }
        status = dlocapi._load_image(structure, "IMAGE", "TAG")
        self.assertFalse(status)
        #
        dlocapi = udocker.DockerLocalFileAPI(mock_local)
        mock_local.cd_imagerepo.return_value = False
        mock_local.setup_tag.return_value = "/dir"
        mock_local.set_version.return_value = True
        mock_findtop.return_value = "TLID"
        mock_slayers.return_value = ["LID", ]
        mock_copylayer.return_value = True
        structure = {'layers': {'LID': {'VERSION': "1.0",
                                        'json_f': "f1",
                                        'layer_f': "f1", }, }, }
        status = dlocapi._load_image(structure, "IMAGE", "TAG")
        self.assertEqual(status, ['IMAGE:TAG'])

    @mock.patch('udocker.DockerLocalFileAPI._load_image')
    @mock.patch('udocker.Msg')
    @mock.patch('udocker.LocalRepository')
    def test_07__load_repositories(self, mock_local, mock_msg, mock_loadi):
        """Test DockerLocalFileAPI()._load_repositories()."""
        self._init()
        mock_msg.level = 0
        #
        dlocapi = udocker.DockerLocalFileAPI(mock_local)
        structure = {}
        status = dlocapi._load_repositories(structure)
        self.assertFalse(status)
        #
        dlocapi = udocker.DockerLocalFileAPI(mock_local)
        structure = {'repositories': {'IMAGE': {'TAG': "tag", }, }, }
        mock_loadi.return_value = False
        status = dlocapi._load_repositories(structure)
        self.assertFalse(status)
        #
        dlocapi = udocker.DockerLocalFileAPI(mock_local)
        structure = {'repositories': {'IMAGE': {'TAG': "tag", }, }, }
        mock_loadi.return_value = True
        status = dlocapi._load_repositories(structure)
        self.assertTrue(status)

    @mock.patch('udocker.subprocess.call')
    @mock.patch('udocker.Msg')
    @mock.patch('udocker.LocalRepository')
    def test_08__untar_saved_container(self, mock_local, mock_msg, mock_call):
        """Test DockerLocalFileAPI()._untar_saved_container()."""
        self._init()
        mock_msg.level = 0
        #
        dlocapi = udocker.DockerLocalFileAPI(mock_local)
        mock_call.return_value = True
        status = dlocapi._untar_saved_container("TARFILE", "DESTDIR")
        self.assertFalse(status)
        #
        dlocapi = udocker.DockerLocalFileAPI(mock_local)
        mock_call.return_value = False
        status = dlocapi._untar_saved_container("TARFILE", "DESTDIR")
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
        """Test DockerLocalFileAPI().load()."""
        self._init()
        mock_msg.level = 0
        #
        dlocapi = udocker.DockerLocalFileAPI(mock_local)
        mock_exists.return_value = False
        mock_futil.return_value.mktmp.return_value = "tmpfile"
        status = dlocapi.load("IMAGEFILE")
        self.assertFalse(status)
        #
        dlocapi = udocker.DockerLocalFileAPI(mock_local)
        mock_exists.return_value = True
        mock_futil.return_value.mktmp.return_value = "tmpfile"
        mock_untar.return_value = False
        status = dlocapi.load("IMAGEFILE")
        self.assertFalse(status)
        #
        dlocapi = udocker.DockerLocalFileAPI(mock_local)
        mock_exists.return_value = True
        mock_futil.return_value.mktmp.return_value = "tmpfile"
        mock_untar.return_value = True
        structure = {}
        mock_lstruct.return_value = structure
        status = dlocapi.load("IMAGEFILE")
        self.assertFalse(status)
        #
        dlocapi = udocker.DockerLocalFileAPI(mock_local)
        mock_exists.return_value = True
        mock_futil.return_value.mktmp.return_value = "tmpfile"
        mock_untar.return_value = True
        structure = {'repositories': {'IMAGE': {'TAG': "tag", }, }, }
        mock_lstruct.return_value = structure
        mock_lrepo.return_value = ["R1", "R2", ]
        status = dlocapi.load("IMAGEFILE")
        self.assertEqual(status, ["R1", "R2", ])

    @mock.patch('udocker.time.strftime')
    @mock.patch('udocker.FileUtil')
    @mock.patch('udocker.Msg')
    @mock.patch('udocker.LocalRepository')
    def test_10_create_container_meta(self, mock_local, mock_msg, mock_futil,
                                      mock_stime):
        """Test DockerLocalFileAPI().create_container_meta()."""
        self._init()
        mock_msg.level = 0
        #
        dlocapi = udocker.DockerLocalFileAPI(mock_local)
        mock_futil.return_value.size.return_value = 123
        mock_stime.return_value = "DATE"
        status = dlocapi.create_container_meta("LID")
        meta = {'comment': 'created by udocker',
                'created': 'DATE',
                'config': {'Env': None, 'Hostname': '', 'Entrypoint': None,
                           'PortSpecs': None, 'Memory': 0, 'OnBuild': None,
                           'OpenStdin': False, 'MacAddress': '', 'Cpuset': '',
                           'NetworkDisable': False, 'User': '',
                           'AttachStderr': False, 'AttachStdout': False,
                           'Cmd': None, 'StdinOnce': False, 'CpusShares': 0,
                           'WorkingDir': '', 'AttachStdin': False,
                           'Volumes': None, 'MemorySwap': 0, 'Tty': False,
                           'Domainname': '', 'Image': '', 'Labels': None,
                           'ExposedPorts': None},
                'container_config': {'Env': None, 'Hostname': '',
                                     'Entrypoint': None, 'PortSpecs': None,
                                     'Memory': 0, 'OnBuild': None,
                                     'OpenStdin': False, 'MacAddress': '',
                                     'Cpuset': '', 'NetworkDisable': False,
                                     'User': '', 'AttachStderr': False,
                                     'AttachStdout': False, 'Cmd': None,
                                     'StdinOnce': False, 'CpusShares': 0,
                                     'WorkingDir': '', 'AttachStdin': False,
                                     'Volumes': None, 'MemorySwap': 0,
                                     'Tty': False, 'Domainname': '',
                                     'Image': '', 'Labels': None,
                                     'ExposedPorts': None},
                'architecture': 'ARCH', 'os': 'OSVERSION',
                'id': 'LID', 'size': 123}
        self.assertEqual(status, meta)

    @mock.patch('udocker.Unique')
    @mock.patch('udocker.os.rename')
    @mock.patch('udocker.FileUtil')
    @mock.patch('udocker.os.path.exists')
    @mock.patch('udocker.Msg')
    @mock.patch('udocker.LocalRepository')
    def test_11_import_toimage(self, mock_local, mock_msg, mock_exists,
                               mock_futil, mock_rename, mock_unique):
        """Test DockerLocalFileAPI().import_toimage()."""
        self._init()
        mock_msg.level = 0
        #
        dlocapi = udocker.DockerLocalFileAPI(mock_local)
        mock_exists.return_value = False
        status = dlocapi.import_toimage("TARFILE", "IMAGE", "TAG")
        self.assertFalse(status)
        #
        dlocapi = udocker.DockerLocalFileAPI(mock_local)
        mock_exists.return_value = True
        mock_local.cd_imagerepo.return_value = "TAGDIR"
        status = dlocapi.import_toimage("TARFILE", "IMAGE", "TAG")
        self.assertFalse(status)
        #
        dlocapi = udocker.DockerLocalFileAPI(mock_local)
        mock_exists.return_value = True
        mock_local.cd_imagerepo.return_value = ""
        mock_local.setup_tag.return_value = ""
        status = dlocapi.import_toimage("TARFILE", "IMAGE", "TAG")
        self.assertFalse(status)
        #
        dlocapi = udocker.DockerLocalFileAPI(mock_local)
        mock_exists.return_value = True
        mock_local.cd_imagerepo.return_value = ""
        mock_local.setup_tag.return_value = "TAGDIR"
        mock_local.set_version.return_value = False
        status = dlocapi.import_toimage("TARFILE", "IMAGE", "TAG")
        self.assertFalse(status)
        #
        dlocapi = udocker.DockerLocalFileAPI(mock_local)
        mock_exists.return_value = True
        mock_local.cd_imagerepo.return_value = ""
        mock_local.setup_tag.return_value = "TAGDIR"
        mock_local.set_version.return_value = True
        mock_unique.return_value.layer_v1.return_value = "LAYERID"
        status = dlocapi.import_toimage("TARFILE", "IMAGE", "TAG")
        self.assertEqual(status, "LAYERID")
        self.assertTrue(mock_rename.called)
        #
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


class UdockerTestCase(unittest.TestCase):
    """Test UdockerTestCase() command line interface."""

    def _init(self):
        """Configure variables."""
        udocker.Config = mock.MagicMock()
        udocker.Config.hostauth_list = ("/etc/passwd", "/etc/group")
        udocker.Config.cmd = "/bin/bash"
        udocker.Config.cpu_affinity_exec_tools = (["numactl", "-C", "%s", "--", ],
                               ["taskset", "-c", "%s", ])
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
    @mock.patch('udocker.DockerLocalFileAPI')
    @mock.patch('udocker.DockerIoAPI')
    @mock.patch('udocker.LocalRepository')
    def test_01_init(self, mock_local, mock_dioapi, mock_dlocapi, mock_ks):
        """Test Udocker() constructor."""
        self._init()
        mock_local.homedir = "/h/u/.udocker"
        mock_ks.return_value = 123
        mock_dioapi.return_value = 456
        mock_dlocapi.return_value = 789
        #
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
        """Test Udocker()._cdrepo()."""
        self._init()
        mock_local.homedir = "/h/u/.udocker"
        mock_ks.return_value = 123
        mock_dioapi.return_value = 456
        mock_dlocapi.return_value = 789
        #
        mock_cmdp.get.return_value = "/u/containers/AAAA"
        mock_cmdp.missing_options.return_value = True
        udoc = udocker.Udocker(mock_local)
        status = udoc._cdrepo(mock_cmdp)
        self.assertFalse(status)
        #
        mock_cmdp.get.return_value = "/u/containers/AAAA"
        mock_cmdp.missing_options.return_value = False
        mock_futil.return_value.isdir.return_value = False
        udoc = udocker.Udocker(mock_local)
        status = udoc._cdrepo(mock_cmdp)
        self.assertFalse(status)
        #
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
        """Test Udocker()._check_imagespec()."""
        self._init()
        mock_msg.level = 0
        #
        mock_dioapi.is_repo_name = False
        udoc = udocker.Udocker(mock_local)
        status = udoc._check_imagespec("")
        self.assertEqual(status, (None, None))
        #
        mock_dioapi.is_repo_name = False
        udoc = udocker.Udocker(mock_local)
        status = udoc._check_imagespec("AAA")
        self.assertEqual(status, ("AAA", "latest"))
        #
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
        """Test Udocker().do_mkrepo()."""
        self._init()
        mock_msg.level = 0
        #
        mock_cmdp.get.return_value = "/"
        mock_exists.return_value = True
        mock_dlocapi.create_repo.return_value = True
        udoc = udocker.Udocker(mock_local)
        status = udoc.do_mkrepo(mock_cmdp)
        self.assertFalse(status)
        #
        mock_cmdp.get.return_value = ""
        mock_exists.return_value = True
        mock_dlocapi.create_repo.return_value = True
        udoc = udocker.Udocker(mock_local)
        status = udoc.do_mkrepo(mock_cmdp)
        self.assertTrue(status)
        #
        mock_cmdp.get.return_value = "/"
        mock_exists.return_value = True
        mock_dlocapi.create_repo.return_value = False
        udoc = udocker.Udocker(mock_local)
        status = udoc.do_mkrepo(mock_cmdp)
        self.assertFalse(status)

    @mock.patch('udocker.raw_input')
    @mock.patch('udocker.Udocker._search_print_v2')
    @mock.patch('udocker.Udocker._search_print_v1')
    @mock.patch('udocker.CmdParser')
    @mock.patch('udocker.KeyStore')
    @mock.patch('udocker.DockerLocalFileAPI')
    @mock.patch('udocker.DockerIoAPI')
    @mock.patch('udocker.Msg')
    @mock.patch('udocker.LocalRepository')
    def test_05_do_search(self, mock_local, mock_msg, mock_dioapi,
                          mock_dlocapi, mock_ks, mock_cmdp,
                          mock_print1, mock_print2, mock_rinput):
        """Test Udocker().do_search()."""
        self._init()
        mock_msg.level = 0
        #
        udoc = udocker.Udocker(mock_local)
        mock_cmdp.get.side_effect = ["", "", "" "", "", ]
        mock_cmdp.missing_options.return_value = True
        status = udoc.do_search(mock_cmdp)
        self.assertFalse(status)
        #
        udoc = udocker.Udocker(mock_local)
        mock_cmdp.get.side_effect = ["", "", "" "", "", ]
        mock_cmdp.missing_options.return_value = False
        mock_dioapi.return_value.search_get_page.return_value = None
        status = udoc.do_search(mock_cmdp)
        self.assertTrue(status)
        #
        udoc = udocker.Udocker(mock_local)
        mock_cmdp.get.side_effect = ["", "", "" "", "", ]
        mock_cmdp.missing_options.return_value = False
        mock_dioapi.return_value.search_get_page.side_effect = (
            [["results", ], ["repositories", ], [], ])
        status = udoc.do_search(mock_cmdp)
        self.assertTrue(status)
        self.assertTrue(mock_print1.called)
        self.assertTrue(mock_print2.called)
        #
        mock_print1.reset_mock()
        mock_print2.reset_mock()
        udoc = udocker.Udocker(mock_local)
        mock_cmdp.get.side_effect = ["", "", "" "", "", ]
        mock_cmdp.missing_options.return_value = False
        mock_dioapi.return_value.search_get_page.side_effect = (
            [["zzz", ], ["repositories", ], [], ])
        status = udoc.do_search(mock_cmdp)
        self.assertTrue(status)
        self.assertFalse(mock_print1.called)
        self.assertTrue(mock_print2.called)
        #
        mock_print1.reset_mock()
        mock_print2.reset_mock()
        udoc = udocker.Udocker(mock_local)
        mock_cmdp.get.side_effect = ["", "", "" "", "", ]
        mock_cmdp.missing_options.return_value = False
        mock_rinput.return_value = "q"
        mock_dioapi.return_value.search_ended = False
        mock_dioapi.return_value.search_get_page.side_effect = (
            [["zzz", ], ["repositories", ], [], ])
        status = udoc.do_search(mock_cmdp)
        self.assertTrue(status)
        self.assertFalse(mock_print1.called)
        self.assertFalse(mock_print2.called)

    @mock.patch('udocker.CmdParser')
    @mock.patch('udocker.KeyStore')
    @mock.patch('udocker.DockerLocalFileAPI')
    @mock.patch('udocker.DockerIoAPI')
    @mock.patch('udocker.Msg')
    @mock.patch('udocker.LocalRepository')
    def test_06_do_load(self, mock_local, mock_msg, mock_dioapi,
                        mock_dlocapi, mock_ks, mock_cmdp):
        """Test Udocker().do_load()."""
        self._init()
        mock_msg.level = 0
        #
        udoc = udocker.Udocker(mock_local)
        mock_cmdp.get.side_effect = ["", "", "" "", "", ]
        mock_cmdp.missing_options.return_value = True
        status = udoc.do_load(mock_cmdp)
        self.assertFalse(status)
        #
        udoc = udocker.Udocker(mock_local)
        mock_cmdp.get.side_effect = ["", "", "" "", "", ]
        mock_cmdp.missing_options.return_value = False
        status = udoc.do_load(mock_cmdp)
        self.assertFalse(status)
        #
        udoc = udocker.Udocker(mock_local)
        mock_cmdp.get.side_effect = ["INFILE", "", "" "", "", ]
        mock_cmdp.missing_options.return_value = False
        mock_dlocapi.return_value.load.return_value = []
        status = udoc.do_load(mock_cmdp)
        self.assertFalse(status)
        #
        udoc = udocker.Udocker(mock_local)
        mock_cmdp.get.side_effect = ["INFILE", "", "" "", "", ]
        mock_cmdp.missing_options.return_value = False
        mock_dlocapi.return_value.load.return_value = ["REPO", ]
        status = udoc.do_load(mock_cmdp)
        self.assertTrue(status)

    @mock.patch('udocker.Udocker._check_imagespec')
    @mock.patch('udocker.CmdParser')
    @mock.patch('udocker.KeyStore')
    @mock.patch('udocker.DockerLocalFileAPI')
    @mock.patch('udocker.DockerIoAPI')
    @mock.patch('udocker.Msg')
    @mock.patch('udocker.LocalRepository')
    def test_07_do_import(self, mock_local, mock_msg, mock_dioapi,
                          mock_dlocapi, mock_ks, mock_cmdp, mock_chkimg):
        """Test Udocker().do_import()."""
        self._init()
        mock_msg.level = 0
        cmd_options = [False, False, "", False,
                       "INFILE", "IMAGE", "" "", "", ]
        #
        udoc = udocker.Udocker(mock_local)
        mock_cmdp.get.side_effect = ["", "", "", "", "", "", "", "", "", ]
        status = udoc.do_import(mock_cmdp)
        self.assertFalse(status)
        #
        mock_cmdp.reset_mock()
        udoc = udocker.Udocker(mock_local)
        mock_cmdp.get.side_effect = cmd_options
        mock_chkimg.return_value = ("", "")
        mock_cmdp.missing_options.return_value = False
        status = udoc.do_import(mock_cmdp)
        self.assertFalse(status)
        #
        mock_cmdp.reset_mock()
        udoc = udocker.Udocker(mock_local)
        mock_cmdp.get.side_effect = cmd_options
        mock_chkimg.return_value = ("IMAGE", "")
        mock_cmdp.missing_options.return_value = True
        status = udoc.do_import(mock_cmdp)
        self.assertFalse(status)
        #
        mock_cmdp.reset_mock()
        udoc = udocker.Udocker(mock_local)
        mock_cmdp.get.side_effect = cmd_options
        mock_chkimg.return_value = ("IMAGE", "TAG")
        mock_cmdp.missing_options.return_value = False
        mock_dlocapi.return_value.import_toimage.return_value = False
        status = udoc.do_import(mock_cmdp)
        self.assertFalse(status)
        #
        mock_cmdp.reset_mock()
        udoc = udocker.Udocker(mock_local)
        mock_cmdp.get.side_effect = cmd_options
        mock_chkimg.return_value = ("IMAGE", "TAG")
        mock_cmdp.missing_options.return_value = False
        mock_dlocapi.return_value.import_toimage.return_value = True
        status = udoc.do_import(mock_cmdp)
        self.assertTrue(status)

    @mock.patch('udocker.getpass')
    @mock.patch('udocker.raw_input')
    @mock.patch('udocker.CmdParser')
    @mock.patch('udocker.KeyStore')
    @mock.patch('udocker.DockerLocalFileAPI')
    @mock.patch('udocker.DockerIoAPI')
    @mock.patch('udocker.Msg')
    @mock.patch('udocker.LocalRepository')
    def test_08_do_login(self, mock_local, mock_msg, mock_dioapi,
                         mock_dlocapi, mock_ks, mock_cmdp,
                         mock_rinput, mock_gpass):
        """Test Udocker().do_login()."""
        self._init()
        mock_msg.level = 0
        #
        udoc = udocker.Udocker(mock_local)
        mock_cmdp.get.side_effect = ["user", "pass", "" "", "", ]
        mock_rinput.return_value = "user"
        mock_gpass.return_value = "pass"
        mock_ks.return_value.put.return_value = False
        status = udoc.do_login(mock_cmdp)
        self.assertFalse(status)
        self.assertFalse(mock_rinput.called)
        self.assertFalse(mock_gpass.called)
        #
        mock_rinput.reset_mock()
        mock_gpass.reset_mock()
        udoc = udocker.Udocker(mock_local)
        mock_cmdp.get.side_effect = ["", "", "" "", "", ]
        mock_rinput.return_value = "user"
        mock_gpass.return_value = "pass"
        mock_ks.return_value.put.return_value = False
        status = udoc.do_login(mock_cmdp)
        self.assertFalse(status)
        self.assertTrue(mock_rinput.called)
        self.assertTrue(mock_gpass.called)
        #
        udoc = udocker.Udocker(mock_local)
        mock_cmdp.get.side_effect = ["", "", "" "", "", ]
        mock_rinput.return_value = "user"
        mock_gpass.return_value = "pass"
        mock_ks.return_value.put.return_value = True
        status = udoc.do_login(mock_cmdp)
        self.assertTrue(status)

    @mock.patch('udocker.CmdParser')
    @mock.patch('udocker.KeyStore')
    @mock.patch('udocker.DockerLocalFileAPI')
    @mock.patch('udocker.DockerIoAPI')
    @mock.patch('udocker.Msg')
    @mock.patch('udocker.LocalRepository')
    def test_09_do_logout(self, mock_local, mock_msg, mock_dioapi,
                          mock_dlocapi, mock_ks, mock_cmdp):
        """Test Udocker().do_logout()."""
        self._init()
        mock_msg.level = 0
        #
        udoc = udocker.Udocker(mock_local)
        mock_cmdp.get.side_effect = ["", "", "" "", "", ]
        mock_ks.return_value.delete.return_value = False
        status = udoc.do_logout(mock_cmdp)
        self.assertFalse(status)
        #
        udoc = udocker.Udocker(mock_local)
        mock_cmdp.get.side_effect = ["ALL", "", "" "", "", ]
        mock_ks.return_value.delete.return_value = False
        mock_ks.return_value.erase.return_value = True
        status = udoc.do_logout(mock_cmdp)
        self.assertTrue(status)
        self.assertTrue(mock_ks.return_value.erase.called)
        #
        udoc = udocker.Udocker(mock_local)
        mock_cmdp.get.side_effect = ["", "", "" "", "", ]
        mock_ks.return_value.delete.return_value = True
        status = udoc.do_logout(mock_cmdp)
        self.assertTrue(status)
        self.assertTrue(mock_ks.return_value.delete.called)

    @mock.patch('udocker.Udocker._check_imagespec')
    @mock.patch('udocker.CmdParser')
    @mock.patch('udocker.KeyStore')
    @mock.patch('udocker.DockerLocalFileAPI')
    @mock.patch('udocker.DockerIoAPI')
    @mock.patch('udocker.Msg')
    @mock.patch('udocker.LocalRepository')
    def test_10_do_pull(self, mock_local, mock_msg, mock_dioapi,
                        mock_dlocapi, mock_ks, mock_cmdp, mock_chkimg):
        """Test Udocker().do_pull()."""
        self._init()
        mock_msg.level = 0
        #
        udoc = udocker.Udocker(mock_local)
        mock_cmdp.get.side_effect = ["", "", "" "", "", ]
        mock_chkimg.return_value = ("", "TAG")
        status = udoc.do_pull(mock_cmdp)
        self.assertFalse(status)
        #
        udoc = udocker.Udocker(mock_local)
        mock_cmdp.get.side_effect = ["", "", "" "", "", ]
        mock_chkimg.return_value = ("IMAGE", "TAG")
        mock_cmdp.missing_options.return_value = True
        status = udoc.do_pull(mock_cmdp)
        self.assertFalse(status)
        #
        udoc = udocker.Udocker(mock_local)
        mock_cmdp.get.side_effect = ["", "", "" "", "", ]
        mock_chkimg.return_value = ("IMAGE", "TAG")
        mock_cmdp.missing_options.return_value = False
        mock_dioapi.return_value.get.return_value = []
        status = udoc.do_pull(mock_cmdp)
        self.assertFalse(status)
        #
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
    def test_11_do_create(self, mock_local, mock_msg, mock_dioapi,
                          mock_dlocapi, mock_ks, mock_cmdp, mock_create):
        """Test Udocker().do_create()."""
        self._init()
        mock_msg.level = 0
        #
        udoc = udocker.Udocker(mock_local)
        mock_cmdp.missing_options.return_value = True
        mock_cmdp.get.side_effect = ["", "", "" "", "", ]
        mock_create.return_value = ""
        status = udoc.do_create(mock_cmdp)
        self.assertFalse(status)
        #
        udoc = udocker.Udocker(mock_local)
        mock_cmdp.missing_options.return_value = False
        mock_cmdp.get.side_effect = ["", "", "" "", "", ]
        mock_create.return_value = ""
        status = udoc.do_create(mock_cmdp)
        self.assertFalse(status)
        #
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
    def test_12__create(self, mock_local, mock_msg, mock_dioapi, mock_chkimg,
                        mock_cstruct):
        """Test Udocker()._create()."""
        self._init()
        mock_msg.level = 0
        #
        udoc = udocker.Udocker(mock_local)
        mock_dioapi.return_value.is_repo_name.return_value = False
        status = udoc._create("IMAGE:TAG")
        self.assertFalse(status)
        #
        udoc = udocker.Udocker(mock_local)
        mock_dioapi.return_value.is_repo_name.return_value = True
        mock_chkimg.return_value = ("", "TAG")
        mock_cstruct.return_value.create.return_value = True
        status = udoc._create("IMAGE:TAG")
        self.assertFalse(status)
        #
        udoc = udocker.Udocker(mock_local)
        mock_dioapi.return_value.is_repo_name.return_value = True
        mock_chkimg.return_value = ("IMAGE", "TAG")
        mock_cstruct.return_value.create.return_value = True
        status = udoc._create("IMAGE:TAG")
        self.assertTrue(status)

    #    @mock.patch('udocker.CmdParser')
    #    @mock.patch('udocker.LocalRepository')
    #    def test_14__get_run_options(self, mock_local, mock_cmdp):
    #        """Test Udocker()._get_run_options()"""
    #        self._init()
    #        #
    #        udoc = udocker.Udocker(mock_local)
    #        udocker.PRootEngine = mock.MagicMock()
    #        udocker.PRootEngine.opt = dict()
    #        udocker.PRootEngine.opt["vol"] = []
    #        udocker.PRootEngine.opt["env"] = []
    #        mock_cmdp.get.return_value = "VALUE"
    #        udoc._get_run_options(mock_cmdp, udocker.PRootEngine)
    #        self.assertEqual(udocker.PRootEngine.opt["dns"], "VALUE")

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
    def test_15_do_run(self, mock_realpath, mock_del, mock_local,
                       mock_msg, mock_dioapi, mock_dlocapi,
                       mock_ks, mock_cmdp, mock_eng, mock_getopt):
        """Test Udocker().do_run()."""
        self._init()
        mock_msg.level = 0
        mock_realpath.return_value = "/tmp"
        #
        udoc = udocker.Udocker(mock_local)
        mock_cmdp.return_value.missing_options.return_value = True
        mock_cmdp.return_value.get.side_effect = ["", "", "" "", "", ]
        status = udoc.do_run(mock_cmdp)
        self.assertFalse(status)

        mock_local.reset_mock()
        mock_cmdp.reset_mock()
        mock_eng.reset_mock()
        udoc = udocker.Udocker(mock_local)
        mock_cmdp.return_value.missing_options.return_value = False
        mock_cmdp.return_value.get.side_effect = ["", "", "" "", "", ]
        udocker.Config.location = "/"
        mock_eng.return_value.run.return_value = True
        status = udoc.do_run(mock_cmdp)
        self.assertFalse(status)

        # mock_local.reset_mock()
        # mock_cmdp.reset_mock()
        # mock_eng.reset_mock()
        # udoc = udocker.Udocker(mock_local)
        # mock_cmdp.return_value.missing_options.return_value = False
        # mock_cmdp.return_value.get.side_effect = ["", "", "" "", "", ]
        # udocker.Config.location = "/"
        # mock_eng.return_value.run.return_value = False
        # status = udoc.do_run(mock_cmdp)
        # self.assertFalse(status)
        #
        # mock_local.reset_mock()
        # mock_cmdp.reset_mock()
        # mock_eng.reset_mock()
        # mock_del.reset_mock()
        # udoc = udocker.Udocker(mock_local)
        # mock_cmdp.return_value.missing_options.return_value = False
        # mock_cmdp.return_value.get.side_effect = ["", "", "--rm" "", "", ]
        # udocker.Config.location = "/"
        # mock_eng.return_value.run.return_value = False
        # mock_local.return_value.isprotected_container.return_value = True
        # mock_del.return_value = True
        # status = udoc.do_run(mock_cmdp)
        # self.assertFalse(mock_del.called)
        # self.assertFalse(status)
        #
        # mock_local.reset_mock()
        # mock_cmdp.reset_mock()
        # mock_eng.reset_mock()
        # mock_del.reset_mock()
        # udoc = udocker.Udocker(mock_local)
        # mock_cmdp.return_value.missing_options.return_value = False
        # mock_cmdp.return_value.get.side_effect = ["", "", "--rm" "", "", ]
        # udocker.Config.location = "/"
        # mock_eng.return_value.run.return_value = False
        # mock_local.return_value.isprotected_container.return_value = False
        # mock_del.return_value = True
        # status = udoc.do_run(mock_cmdp)
        # # self.assertTrue(mock_del.called)
        # self.assertFalse(status)
        #
        # mock_local.reset_mock()
        # mock_cmdp.reset_mock()
        # mock_eng.reset_mock()
        # udoc = udocker.Udocker(mock_local)
        # mock_cmdp.return_value.missing_options.return_value = False
        # mock_cmdp.return_value.get.side_effect = ["", "", "" "", "", ]
        # udocker.Config.location = ""
        # mock_local.return_value.get_container_id.return_value = ""
        # mock_eng.return_value.run.return_value = True
        # status = udoc.do_run(mock_cmdp)
        # self.assertFalse(status)
        #
        # mock_local.reset_mock()
        # mock_cmdp.reset_mock()
        # mock_eng.reset_mock()
        # udoc = udocker.Udocker(mock_local)
        # mock_cmdp.return_value.missing_options.return_value = False
        # mock_cmdp.return_value.get.side_effect = ["", "", "" "", "", ]
        # udocker.Config.location = ""
        # mock_local.return_value.get_container_id.return_value = "CONTAINER_ID"
        # mock_eng.return_value.run.return_value = True
        # status = udoc.do_run(mock_cmdp)
        # self.assertTrue(status)
        #
        # mock_local.reset_mock()
        # mock_cmdp.reset_mock()
        # mock_eng.reset_mock()
        # udoc = udocker.Udocker(mock_local)
        # mock_cmdp.return_value.missing_options.return_value = False
        # mock_cmdp.return_value.get.side_effect = ["", "", "" "", "NAME", ]
        # udocker.Config.location = ""
        # mock_local.return_value.get_container_id.return_value = "CONTAINER_ID"
        # mock_eng.return_value.run.return_value = True
        # mock_local.return_value.set_container_name.return_value = True
        # status = udoc.do_run(mock_cmdp)
        # self.assertTrue(status)
        #
        # mock_local.reset_mock()
        # mock_cmdp.reset_mock()
        # mock_eng.reset_mock()
        # udoc = udocker.Udocker(mock_local)
        # mock_cmdp.return_value.missing_options.return_value = False
        # mock_cmdp.return_value.get.side_effect = ["", "", "" "", "NAME", ]
        # udocker.Config.location = ""
        # mock_local.return_value.get_container_id.return_value = "CONTAINER_ID"
        # mock_eng.return_value.run.return_value = True
        # mock_local.return_value.set_container_name.return_value = False
        # status = udoc.do_run(mock_cmdp)
        # self.assertFalse(status)

    @mock.patch('udocker.CmdParser')
    @mock.patch('udocker.KeyStore')
    @mock.patch('udocker.DockerLocalFileAPI')
    @mock.patch('udocker.DockerIoAPI')
    @mock.patch('udocker.Msg')
    @mock.patch('udocker.LocalRepository')
    def test_16_do_images(self, mock_local, mock_msg, mock_dioapi,
                          mock_dlocapi, mock_ks, mock_cmdp):
        """Test Udocker().do_images()."""
        self._init()
        mock_msg.level = 0
        #
        udoc = udocker.Udocker(mock_local)
        mock_cmdp.missing_options.return_value = True
        mock_cmdp.get.side_effect = ["", "", "" "", "", ]
        status = udoc.do_images(mock_cmdp)
        self.assertFalse(status)
        #
        udoc = udocker.Udocker(mock_local)
        mock_cmdp.missing_options.return_value = False
        mock_cmdp.get.side_effect = ["", "", "" "", "", ]
        mock_local.get_imagerepos.return_values = []
        status = udoc.do_images(mock_cmdp)
        self.assertTrue(status)
        #
        udoc = udocker.Udocker(mock_local)
        mock_cmdp.missing_options.return_value = False
        mock_cmdp.get.side_effect = ["", "", "" "", "", ]
        mock_local.get_imagerepos.return_value = [("I1", "T1"), ("I2", "T2"), ]
        mock_local.isprotected_imagerepo.return_value = True
        status = udoc.do_images(mock_cmdp)
        self.assertTrue(status)
        self.assertTrue(mock_local.isprotected_imagerepo.called)
        #
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
    def test_17_do_ps(self, mock_local, mock_msg, mock_dioapi,
                      mock_dlocapi, mock_ks, mock_cmdp):
        """Test Udocker().do_ps()."""
        self._init()
        mock_msg.level = 0
        #
        udoc = udocker.Udocker(mock_local)
        mock_cmdp.missing_options.return_value = True
        mock_cmdp.get.side_effect = ["", "", "" "", "", ]
        status = udoc.do_ps(mock_cmdp)
        self.assertFalse(status)
        #
        udoc = udocker.Udocker(mock_local)
        mock_cmdp.missing_options.return_value = False
        mock_cmdp.get.side_effect = ["", "", "" "", "", ]
        mock_local.get_containers_list.return_value = []
        udoc.do_ps(mock_cmdp)
        self.assertTrue(mock_local.get_containers_list.called)
        #
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
    def test_18_do_rm(self, mock_local, mock_msg, mock_dioapi,
                      mock_dlocapi, mock_ks, mock_cmdp):
        """Test Udocker().do_rm()."""
        self._init()
        mock_msg.level = 0
        #
        udoc = udocker.Udocker(mock_local)
        mock_cmdp.missing_options.return_value = True
        mock_cmdp.get.side_effect = ["", "", "" "", "", ]
        status = udoc.do_rm(mock_cmdp)
        self.assertFalse(status)
        #
        udoc = udocker.Udocker(mock_local)
        mock_cmdp.missing_options.return_value = False
        mock_cmdp.get.side_effect = ["", "", "" "", "", ]
        status = udoc.do_rm(mock_cmdp)
        self.assertFalse(status)
        #
        udoc = udocker.Udocker(mock_local)
        mock_cmdp.missing_options.return_value = False
        mock_cmdp.get.side_effect = ["X", "12", "" "", "", ]
        mock_local.get_container_id.return_value = ""
        status = udoc.do_rm(mock_cmdp)
        self.assertFalse(status)
        #
        udoc = udocker.Udocker(mock_local)
        mock_cmdp.missing_options.return_value = False
        mock_cmdp.get.side_effect = ["X", "1", "" "", "", ]
        mock_local.get_container_id.return_value = "1"
        mock_local.isprotected_container.return_value = True
        status = udoc.do_rm(mock_cmdp)
        self.assertFalse(status)
        #
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
    def test_19_do_rmi(self, mock_local, mock_msg, mock_dioapi,
                       mock_dlocapi, mock_ks, mock_cmdp, mock_chkimg):
        """Test Udocker().do_rmi()."""
        self._init()
        mock_msg.level = 0
        #
        udoc = udocker.Udocker(mock_local)
        mock_cmdp.missing_options.return_value = True
        mock_cmdp.get.side_effect = ["", "", "" "", "", ]
        mock_chkimg.return_value = ("IMAGE", "TAG")
        status = udoc.do_rmi(mock_cmdp)
        self.assertFalse(status)
        #
        udoc = udocker.Udocker(mock_local)
        mock_cmdp.missing_options.return_value = False
        mock_cmdp.get.side_effect = ["", "", "" "", "", ]
        mock_chkimg.return_value = ("", "TAG")
        status = udoc.do_rmi(mock_cmdp)
        self.assertFalse(status)
        #
        udoc = udocker.Udocker(mock_local)
        mock_cmdp.missing_options.return_value = False
        mock_cmdp.get.side_effect = ["", "", "" "", "", ]
        mock_chkimg.return_value = ("IMAGE", "TAG")
        mock_local.isprotected_imagerepo.return_value = True
        status = udoc.do_rmi(mock_cmdp)
        self.assertFalse(status)
        #
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
    def test_20_do_protect(self, mock_local, mock_msg, mock_dioapi,
                           mock_dlocapi, mock_ks, mock_cmdp, mock_chkimg):
        """Test Udocker().do_protect()."""
        self._init()
        mock_msg.level = 0
        #
        udoc = udocker.Udocker(mock_local)
        mock_cmdp.missing_options.return_value = True
        mock_cmdp.get.side_effect = ["", "", "" "", "", ]
        mock_chkimg.return_value = ("IMAGE", "TAG")
        status = udoc.do_protect(mock_cmdp)
        self.assertFalse(status)
        #
        udoc = udocker.Udocker(mock_local)
        mock_cmdp.missing_options.return_value = False
        mock_cmdp.get.side_effect = ["", "", "" "", "", ]
        mock_chkimg.return_value = ("IMAGE", "TAG")
        mock_local.get_container_id.return_value = "123"
        mock_local.protect_container.return_value = False
        status = udoc.do_protect(mock_cmdp)
        self.assertFalse(status)
        #
        udoc = udocker.Udocker(mock_local)
        mock_cmdp.missing_options.return_value = False
        mock_cmdp.get.side_effect = ["", "", "" "", "", ]
        mock_chkimg.return_value = ("IMAGE", "TAG")
        mock_local.get_container_id.return_value = "123"
        mock_local.protect_container.return_value = True
        status = udoc.do_protect(mock_cmdp)
        self.assertTrue(status)
        #
        udoc = udocker.Udocker(mock_local)
        mock_cmdp.missing_options.return_value = False
        mock_cmdp.get.side_effect = ["", "", "" "", "", ]
        mock_chkimg.return_value = ("", "TAG")
        mock_local.get_container_id.return_value = ""
        mock_local.protect_imagerepo.return_value = True
        status = udoc.do_protect(mock_cmdp)
        self.assertFalse(status)
        #
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
    def test_21_do_unprotect(self, mock_local, mock_msg, mock_dioapi,
                             mock_dlocapi, mock_ks, mock_cmdp, mock_chkimg):
        """Test Udocker().do_unprotect()."""
        self._init()
        mock_msg.level = 0
        #
        udoc = udocker.Udocker(mock_local)
        mock_cmdp.missing_options.return_value = True
        mock_cmdp.get.side_effect = ["", "", "" "", "", ]
        mock_chkimg.return_value = ("IMAGE", "TAG")
        status = udoc.do_unprotect(mock_cmdp)
        self.assertFalse(status)
        #
        udoc = udocker.Udocker(mock_local)
        mock_cmdp.missing_options.return_value = False
        mock_cmdp.get.side_effect = ["", "", "" "", "", ]
        mock_chkimg.return_value = ("IMAGE", "TAG")
        mock_local.get_container_id.return_value = "123"
        mock_local.unprotect_container.return_value = False
        status = udoc.do_unprotect(mock_cmdp)
        self.assertFalse(status)
        #
        udoc = udocker.Udocker(mock_local)
        mock_cmdp.missing_options.return_value = False
        mock_cmdp.get.side_effect = ["", "", "" "", "", ]
        mock_chkimg.return_value = ("IMAGE", "TAG")
        mock_local.get_container_id.return_value = "123"
        mock_local.unprotect_container.return_value = True
        status = udoc.do_unprotect(mock_cmdp)
        self.assertTrue(status)
        #
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
    def test_22_do_name(self, mock_local, mock_msg, mock_dioapi,
                        mock_dlocapi, mock_ks, mock_cmdp, mock_chkimg):
        """Test Udocker().do_name()."""
        self._init()
        mock_msg.level = 0
        #
        udoc = udocker.Udocker(mock_local)
        mock_cmdp.missing_options.return_value = True
        mock_cmdp.get.side_effect = ["", "", "" "", "", ]
        mock_chkimg.return_value = ("IMAGE", "TAG")
        status = udoc.do_name(mock_cmdp)
        self.assertFalse(status)
        #
        udoc = udocker.Udocker(mock_local)
        mock_cmdp.missing_options.return_value = False
        mock_cmdp.get.side_effect = ["", "NAME", "" "", "", ]
        mock_chkimg.return_value = ("IMAGE", "TAG")
        mock_local.get_container_id.return_value = ""
        status = udoc.do_name(mock_cmdp)
        self.assertFalse(status)
        #
        udoc = udocker.Udocker(mock_local)
        mock_cmdp.missing_options.return_value = False
        mock_cmdp.get.side_effect = ["", "NAME", "" "", "", ]
        mock_chkimg.return_value = ("IMAGE", "TAG")
        mock_local.get_container_id.return_value = "123"
        mock_local.set_container_name.return_value = False
        status = udoc.do_name(mock_cmdp)
        self.assertFalse(status)
        #
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
    def test_23_do_rmname(self, mock_local, mock_msg, mock_dioapi,
                          mock_dlocapi, mock_ks, mock_cmdp, mock_chkimg):
        """Test Udocker().do_rmname()."""
        self._init()
        mock_msg.level = 0
        #
        udoc = udocker.Udocker(mock_local)
        mock_cmdp.missing_options.return_value = True
        mock_cmdp.get.side_effect = ["", "", "" "", "", ]
        mock_chkimg.return_value = ("IMAGE", "TAG")
        status = udoc.do_rmname(mock_cmdp)
        self.assertFalse(status)
        #
        udoc = udocker.Udocker(mock_local)
        mock_cmdp.missing_options.return_value = False
        mock_cmdp.get.side_effect = ["NAME", "", "" "", "", ]
        mock_chkimg.return_value = ("IMAGE", "TAG")
        mock_local.del_container_name.return_value = False
        status = udoc.do_rmname(mock_cmdp)
        self.assertFalse(status)
        #
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
    def test_24_do_inspect(self, mock_local, mock_msg, mock_dioapi,
                           mock_dlocapi, mock_ks, mock_cmdp, mock_chkimg,
                           mock_cstruct, mock_json):
        """Test Udocker().do_inspect()."""
        self._init()
        mock_msg.level = 0
        #
        udoc = udocker.Udocker(mock_local)
        mock_cmdp.missing_options.return_value = True
        mock_cmdp.get.side_effect = ["", "", "" "", "", ]
        mock_chkimg.return_value = ("IMAGE", "TAG")
        status = udoc.do_inspect(mock_cmdp)
        self.assertFalse(status)
        #
        udoc = udocker.Udocker(mock_local)
        mock_cmdp.missing_options.return_value = False
        mock_cmdp.get.side_effect = ["", "", "" "", "", ]
        mock_chkimg.return_value = ("IMAGE", "TAG")
        mock_local.get_container_id.return_value = "123"
        mock_cstruct.return_value.get_container_attr.return_value = ("", "")
        status = udoc.do_inspect(mock_cmdp)
        self.assertFalse(status)
        #
        udoc = udocker.Udocker(mock_local)
        mock_cmdp.missing_options.return_value = False
        mock_cmdp.get.side_effect = ["", "PRINT", "" "", "", ]
        mock_chkimg.return_value = ("IMAGE", "TAG")
        mock_local.get_container_id.return_value = "123"
        mock_cstruct.return_value.get_container_attr.return_value = ("DIR", "")
        status = udoc.do_inspect(mock_cmdp)
        self.assertTrue(status)
        #
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
    def test_25_do_verify(self, mock_local, mock_msg, mock_dioapi,
                          mock_dlocapi, mock_ks, mock_cmdp, mock_chkimg):
        """Test Udocker().do_verify()."""
        self._init()
        mock_msg.level = 0
        #
        udoc = udocker.Udocker(mock_local)
        mock_cmdp.missing_options.return_value = True
        mock_cmdp.get.side_effect = ["", "", "" "", "", ]
        mock_chkimg.return_value = ("IMAGE", "TAG")
        status = udoc.do_verify(mock_cmdp)
        self.assertFalse(status)
        #
        udoc = udocker.Udocker(mock_local)
        mock_cmdp.missing_options.return_value = False
        mock_cmdp.get.side_effect = ["", "", "" "", "", ]
        mock_chkimg.return_value = ("", "")
        status = udoc.do_verify(mock_cmdp)
        self.assertFalse(status)
        #
        udoc = udocker.Udocker(mock_local)
        mock_cmdp.missing_options.return_value = False
        mock_cmdp.get.side_effect = ["", "", "" "", "", ]
        mock_chkimg.return_value = ("IMAGE", "TAG")
        mock_local.cd_imagerepo.return_value = False
        status = udoc.do_verify(mock_cmdp)
        self.assertFalse(status)
        #
        udoc = udocker.Udocker(mock_local)
        mock_cmdp.missing_options.return_value = False
        mock_cmdp.get.side_effect = ["", "", "" "", "", ]
        mock_chkimg.return_value = ("IMAGE", "TAG")
        mock_local.cd_imagerepo.return_value = True
        mock_local.verify_image.return_value = True
        status = udoc.do_verify(mock_cmdp)
        self.assertTrue(status)

    #@mock.patch('udocker.CmdParser')
    #@mock.patch('udocker.LocalRepository')
    #def test_25_do_version(self, mock_local, mock_cmdp):
    #    """Test Udocker().do_version()."""
    #    self._init()
    #   udoc = udocker.Udocker(mock_local)
    #   mock_cmdp.get.side_effect = ["run", "", "" "", "", ]
    #   version = udoc.do_version(mock_cmdp)
    #   self.assertIsNotNone(version)

    @mock.patch('udocker.Msg.out')
    @mock.patch('udocker.CmdParser')
    @mock.patch('udocker.LocalRepository')
    def test_26_do_help(self, mock_local, mock_cmdp, mock_msgout):
        """Test Udocker().do_help()."""
        self._init()

        udoc = udocker.Udocker(mock_local)
        mock_cmdp.get.side_effect = ["run", "help", "" "", "", ]
        udoc.do_help(mock_cmdp)
        self.assertTrue(mock_msgout.called)

    @mock.patch('udocker.UdockerTools')
    @mock.patch('udocker.CmdParser')
    @mock.patch('udocker.Msg')
    @mock.patch('udocker.LocalRepository')
    def test_27_do_install(self, mock_local, mock_msg, mock_cmdp,
                           mock_utools):
        """Test Udocker().do_install()."""
        self._init()
        mock_msg.level = 0
        #
        udoc = udocker.Udocker(mock_local)
        mock_cmdp.missing_options.return_value = True
        mock_cmdp.get.side_effect = ["", "", "" "", "", ]
        status = udoc.do_install(mock_cmdp)
        self.assertFalse(mock_utools.return_value.purge.called)
        self.assertTrue(mock_utools.return_value.install.called)
        #
        udoc = udocker.Udocker(mock_local)
        mock_cmdp.missing_options.return_value = True
        mock_cmdp.get.side_effect = ["", "--purge", "" "", "", ]
        mock_utools.reset_mock()
        mock_cmdp.reset_mock()
        status = udoc.do_install(mock_cmdp)
        self.assertTrue(mock_utools.return_value.purge.called)
        self.assertTrue(mock_utools.return_value.install.called_with(False))
        #
        udoc = udocker.Udocker(mock_local)
        mock_cmdp.missing_options.return_value = True
        mock_cmdp.get.side_effect = ["", "--purge", "--force" "", "", ]
        mock_utools.reset_mock()
        mock_cmdp.reset_mock()
        status = udoc.do_install(mock_cmdp)
        self.assertTrue(mock_utools.return_value.purge.called)
        self.assertTrue(mock_utools.return_value.install.called_with(True))
        #
        udoc = udocker.Udocker(mock_local)
        mock_cmdp.missing_options.return_value = True
        mock_cmdp.get.side_effect = ["", "", "--force" "", "", ]
        mock_utools.reset_mock()
        mock_cmdp.reset_mock()
        status = udoc.do_install(mock_cmdp)
        self.assertFalse(mock_utools.return_value.purge.called)
        self.assertTrue(mock_utools.return_value.install.called_with(True))

    @mock.patch('udocker.ExecutionMode')
    @mock.patch('udocker.CmdParser')
    @mock.patch('udocker.KeyStore')
    @mock.patch('udocker.DockerLocalFileAPI')
    @mock.patch('udocker.DockerIoAPI')
    @mock.patch('udocker.Msg')
    @mock.patch('udocker.LocalRepository')
    def test_28_do_setup(self, mock_local, mock_msg, mock_dioapi,
                         mock_dlocapi, mock_ks, mock_cmdp, mock_exec):
        """Test Udocker().do_setup()."""
        self._init()
        mock_msg.level = 0
        #
        udoc = udocker.Udocker(mock_local)
        mock_cmdp.missing_options.return_value = True
        mock_cmdp.get.side_effect = ["", "", "" "", "", ]
        mock_local.cd_container.return_value = False
        status = udoc.do_setup(mock_cmdp)
        self.assertFalse(status)
        #
        udoc = udocker.Udocker(mock_local)
        mock_cmdp.missing_options.return_value = True
        mock_cmdp.get.side_effect = ["", "", "" "", "", ]
        mock_local.cd_container.return_value = True
        mock_exec.set_mode.return_value = False
        status = udoc.do_setup(mock_cmdp)
        self.assertFalse(status)
        #
        udoc = udocker.Udocker(mock_local)
        mock_cmdp.missing_options.return_value = True
        mock_cmdp.get.side_effect = ["", "", "" "", "", ]
        mock_local.cd_container.return_value = True
        mock_exec.set_mode.return_value = True
        status = udoc.do_setup(mock_cmdp)
        self.assertFalse(status)
        #
        udoc = udocker.Udocker(mock_local)
        mock_cmdp.missing_options.return_value = True
        mock_cmdp.get.side_effect = ["", "P1", "" "", "", ]
        mock_local.cd_container.return_value = True
        mock_local.isprotected_container.return_value = True
        mock_exec.set_mode.return_value = True
        status = udoc.do_setup(mock_cmdp)
        self.assertFalse(status)
        #
        udoc = udocker.Udocker(mock_local)
        mock_cmdp.missing_options.return_value = True
        mock_cmdp.get.side_effect = ["", "P1", "" "", "", ]
        mock_local.cd_container.return_value = True
        mock_local.isprotected_container.return_value = False
        mock_exec.set_mode.return_value = True
        status = udoc.do_setup(mock_cmdp)
        self.assertFalse(status)


class CmdParserTestCase(unittest.TestCase):
    """Test CmdParserTestCase() command line interface."""

    @classmethod
    def setUpClass(cls):
        """Setup test."""
        set_env()

    def test_01__init(self):
        """Test CmdParser() Constructor."""

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
        """Test CmdParser().parse()."""

        cmdp = udocker.CmdParser()
        status = cmdp.parse("udocker run --bindhome "
                            "--hostauth --hostenv -v /sys"
                            " -v /proc -v /var/run -v /dev"
                            " --user=jorge --dri myfed  firefox")
        self.assertTrue(status)

    def test_03_missing_options(self):
        """Test CmdParser().missing_options()."""

        cmdp = udocker.CmdParser()
        cmdp.parse("udocker run --bindhome "
                   "--hostauth --hostenv -v /sys"
                   " -v /proc -v /var/run -v /dev"
                   " --user=jorge --dri myfed  firefox")
        out = cmdp.missing_options()
        self.assertIsInstance(out, list)

    def test_04_get(self):
        """Test CmdParser().get()."""

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

    def test_05_declare_options(self):
        """Test CmdParser().declare_options()."""
        pass

    def test_06__get_options(self):
        """Test CmdParser()._get_options()."""
        pass

    def test_07__get_params(self):
        """Test CmdParser()._get_params()."""
        pass


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
        """Test Main() constructor."""
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
        """Test Main() constructor."""
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
        """Test Main().execute()."""
        self._init()
        mock_main_init.return_value = None
        mock_cmdp.return_value.get.side_effect = [True, False, False, False,
                                                  False, False, False, False]
        umain = udocker.Main()
        umain.udocker = mock_udocker
        umain.cmdp = mock_cmdp
        status = umain.execute()
        self.assertEqual(status, 0)
        #
        mock_main_init.return_value = None
        mock_cmdp.return_value.get.side_effect = [False, True, False, False,
                                                  False, False, False, False]
        umain = udocker.Main()
        umain.udocker = mock_udocker
        umain.cmdp = mock_cmdp
        status = umain.execute()
        self.assertEqual(status, 0)
        #
        mock_main_init.return_value = None
        mock_cmdp.return_value.get.side_effect = [False, False, "ERR", False,
                                                  False, False, False, False]
        umain = udocker.Main()
        umain.udocker = mock_udocker
        umain.cmdp = mock_cmdp
        umain.cmdp.reset_mock()
        status = umain.execute()
        self.assertTrue(umain.udocker.do_help.called)
        #
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
        """Test Main().start()."""
        self._init()
        mock_main_init.return_value = None
        mock_main_execute.return_value = 2
        umain = udocker.Main()
        status = umain.start()
        self.assertEqual(status, 2)
        #
        self._init()
        mock_main_init.return_value = None
        mock_main_execute.return_value = 2
        mock_main_execute.side_effect = KeyboardInterrupt("CTRLC")
        umain = udocker.Main()
        status = umain.start()
        self.assertEqual(status, 1)


if __name__ == '__main__':
    unittest.main()
