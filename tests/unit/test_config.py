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

import os
import sys
import unittest
import mock
import platform
import pwd

sys.path.append('../../')

try:
    from StringIO import StringIO
except ImportError:
    from io import StringIO

from udocker.config import Config

__author__ = "udocker@lip.pt"
__credits__ = ["PRoot http://proot.me"]
__license__ = "Licensed under the Apache License, Version 2.0"
__version__ = "0.0.3"
__date__ = "2016"

if sys.version_info[0] >= 3:
    BUILTINS = "builtins"
else:
    BUILTINS = "__builtin__"


def set_env():
    """Set environment variables."""
    if not os.getenv("HOME"):
        os.environ["HOME"] = os.getcwd()


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
        conf = Config()
        self._verify_config(conf)


    @mock.patch('platform.release')
    @mock.patch('platform.system')
    @mock.patch('platform.machine')
    def test_02_platform(self, mock_machine, mock_system, mock_release):
        """Test Config.platform()."""
        conf = Config()
        mock_machine.return_value = "x86_64"
        arch = conf.arch()
        self.assertEqual("amd64", arch, "Config._sysarch x86_64")
        mock_machine.return_value = "i586"
        arch = conf.arch()
        self.assertEqual("i386", arch, "Config._sysarchi i586")
        mock_machine.return_value = "xpto"
        arch = conf.arch()
        self.assertEqual("", arch, "Config._sysarchi i586")
        #
        mock_system.return_value = "linux"
        osver = conf.osversion()
        self.assertEqual(osver, "linux")
        #
        mock_release.return_value = "release"
        osver = conf.oskernel()
        self.assertEqual(osver, "release")

    @mock.patch('udocker.config.Config._verify_config')
    @mock.patch('udocker.config.Config._override_config')
    @mock.patch('udocker.config.Config._read_config')
    @mock.patch('udocker.msg.Msg')
    @mock.patch('udocker.utils.fileutil.FileUtil')
    def test_03_user_init_good(self, mock_fileutil, mock_msg,
                               mock_readc, mock_overrride, mock_verify):
        """Test Config.user_init() with good data."""
        Msg = mock_msg
        conf = Config()
        conf_data = '# comment\nverbose_level = 100\n'
        conf_data += 'tmpdir = "/xpto"\ncmd = ["/bin/ls", "-l"]\n'
        mock_readc.return_value = conf_data
        status = conf.user_init("filename.conf")
        self.assertFalse(mock_verify.called)

    @mock.patch('udocker.msg.Msg')
    @mock.patch('udocker.utils.fileutil.FileUtil')
    @mock.patch('sys.exit')
    def test_04_user_init_bad(self, mock_exit, mock_fileutil, mock_msg):
        """Test Config.user_init() with bad config data."""
        Msg = mock_msg
        conf = Config()
        conf_data = 'hh +=* ffhdklfh\n'
        mock_fileutil.return_value.size.return_value = 10
        mock_fileutil.return_value.getdata.return_value = conf_data
        conf.user_init("filename.conf")
        self.assertTrue(mock_exit.called)

    @mock.patch('udocker.msg.Msg')
    def test_05_username(self, mock_msg):
        """Test Config._username()."""
        Msg = mock_msg
        conf = Config()
        user = conf.username()
        self.assertEqual(user, pwd.getpwuid(os.getuid()).pw_name)

    @mock.patch('udocker.config.Config.oskernel')
    @mock.patch('udocker.msg.Msg')
    def test_06_oskernel_isgreater(self, mock_msg, mock_oskern):
        """Test Config.oskernel_isgreater()."""
        Msg = mock_msg
        conf = Config()
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

    @mock.patch('udocker.utils.fileutil.FileUtil')
    def test_07__read_config(self, mock_futil):
        """Test Config._read_config()."""
        conf = Config()
        mock_futil.return_value.size.return_value = -1
        status = conf._read_config(conf)
        self.assertFalse(status)

    @mock.patch('udocker.config.Config.__init__')
    @mock.patch('udocker.msg.Msg')
    def test_08__verify_config(self, mock_msg, mock_conf_init):
        """Test Config._verify_config()."""
        mock_conf_init.return_value = None
        Config.topdir = "/.udocker"
        conf = Config()
        conf._verify_config()
        self.assertFalse(mock_msg.return_value.err.called)
        #
        mock_conf_init.return_value = None
        Config.topdir = ""
        conf = Config()
        with self.assertRaises(SystemExit) as confexpt:
            conf._verify_config()
        self.assertEqual(confexpt.exception.code, 1)

    @mock.patch('udocker.config.Config.__init__')
    @mock.patch('platform.architecture')
    @mock.patch('platform.machine')
    def test_08_arch(self, mock_machine, mock_architecture, mock_conf_init):
        """Test Config.arch()."""
        mock_conf_init.return_value = None
        mock_machine.return_value = "x86_64"
        mock_architecture.return_value = ["32bit", ]
        conf = Config()
        status = conf.arch()
        self.assertEqual(status, "i386")
        #
        mock_conf_init.return_value = None
        mock_machine.return_value = "x86_64"
        mock_architecture.return_value = ["", ]
        conf = Config()
        status = conf.arch()
        self.assertEqual(status, "amd64")
        #
        mock_conf_init.return_value = None
        mock_machine.return_value = "i686"
        mock_architecture.return_value = ["", ]
        conf = Config()
        status = conf.arch()
        self.assertEqual(status, "i386")
        #
        mock_conf_init.return_value = None
        mock_machine.return_value = "armXX"
        mock_architecture.return_value = ["32bit", ]
        conf = Config()
        status = conf.arch()
        self.assertEqual(status, "arm")
        #
        mock_conf_init.return_value = None
        mock_machine.return_value = "armXX"
        mock_architecture.return_value = ["", ]
        conf = Config()
        status = conf.arch()
        self.assertEqual(status, "arm64")

    @mock.patch('udocker.config.Config.__init__')
    @mock.patch('platform.system')
    def test_10_osversion(self, mock_system, mock_conf_init):
        """Test Config.osversion()."""
        mock_conf_init.return_value = None
        mock_system.return_value = "Linux"
        conf = Config()
        status = conf.osversion()
        self.assertEqual(status, "linux")
        #
        mock_conf_init.return_value = None
        mock_system.return_value = "Linux"
        mock_system.side_effect = NameError('platform system')
        conf = Config()
        status = conf.osversion()
        self.assertEqual(status, "")

    @mock.patch('udocker.config.Config.__init__')
    @mock.patch('platform.linux_distribution')
    def test_11_osdistribution(self, mock_distribution, mock_conf_init):
        """Test Config.osdistribution()."""
        mock_conf_init.return_value = None
        mock_distribution.return_value = ("DISTRO XX", "1.0", "DUMMY")
        conf = Config()
        status = conf.osdistribution()
        self.assertEqual(status, ("DISTRO", "1"))

    @mock.patch('udocker.config.Config.__init__')
    @mock.patch('platform.release')
    def test_12_oskernel(self, mock_release, mock_conf_init):
        """Test Config.oskernel()."""
        mock_conf_init.return_value = None
        mock_release.return_value = "1.2.3"
        conf = Config()
        status = conf.oskernel()
        self.assertEqual(status, "1.2.3")
        #
        mock_conf_init.return_value = None
        mock_release.return_value = "1.2.3"
        mock_release.side_effect = NameError('platform release')
        conf = Config()
        status = conf.oskernel()
        self.assertEqual(status, "3.2.1")
