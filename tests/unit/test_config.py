#!/usr/bin/env python2
"""
udocker unit tests: Config
"""

import os
import sys
import pwd
from unittest import TestCase, main
try:
    from unittest.mock import Mock, MagicMock, patch, mock_open
except ImportError:
    from mock import Mock, MagicMock, patch, mock_open

sys.path.append('.')

from udocker.config import Config


class ConfigTestCase(TestCase):
    """Test case for the udocker configuration."""

    def test_01_init(self):
        """Test Config() constructor."""
        conf = Config().getconf()
        self.assertIsInstance(conf['verbose_level'], int)
        self.assertIsInstance(conf['topdir'], str)
        self.assertIs(conf['bindir'], None)
        self.assertIs(conf['libdir'], None)
        self.assertIs(conf['reposdir'], None)
        self.assertIs(conf['layersdir'], None)
        self.assertIs(conf['containersdir'], None)
        self.assertIsInstance(conf['homedir'], str)
        self.assertIsInstance(conf['config'], str)
        self.assertIsInstance(conf['keystore'], str)
        self.assertIsInstance(conf['tmpdir'], str)
        self.assertIsInstance(conf['tarball'], str)
        self.assertIsInstance(conf['cmd'], list)
        self.assertIsInstance(conf['sysdirs_list'], tuple)
        self.assertIsInstance(conf['hostauth_list'], tuple)
        self.assertIsInstance(conf['dri_list'], tuple)
        self.assertIsInstance(conf['cpu_affinity_exec_tools'], tuple)
        self.assertIsInstance(conf['location'], str)
        self.assertIsInstance(conf['http_proxy'], str)
        self.assertIsInstance(conf['timeout'], int)
        self.assertIsInstance(conf['download_timeout'], int)
        self.assertIsInstance(conf['ctimeout'], int)
        self.assertIsInstance(conf['http_agent'], str)
        self.assertIsInstance(conf['http_insecure'], bool)
        self.assertIsInstance(conf['dockerio_index_url'], str)
        self.assertIsInstance(conf['dockerio_registry_url'], str)

    def test_02_file_override(self):
        """Test Config()._file_override"""
        pass

    def test_03_env_override(self):
        """Test Config()._env_override"""
        pass

    @patch('udocker.msg.Msg')
    def test_04_username(self, mock_msg):
        """Test Config._username()."""
        Msg = mock_msg
        conf = Config().getconf()
        user = conf['username']
        self.assertEqual(user, pwd.getpwuid(os.getuid()).pw_name)

    @patch('udocker.config.platform.architecture')
    @patch('udocker.config.platform.machine')
    def test_05_arch(self, mock_machine, mock_architecture):
        """Test Config._arch()."""
        mock_machine.return_value = "x86_64"
        mock_architecture.return_value = ["32bit", ]
        conf = Config().getconf()
        status = conf['arch']
        self.assertEqual(status, "i386")
        #
        mock_machine.return_value = "x86_64"
        mock_architecture.return_value = ["", ]
        conf = Config().getconf()
        status = conf['arch']
        self.assertEqual(status, "amd64")
        #
        mock_machine.return_value = "i686"
        mock_architecture.return_value = ["", ]
        conf = Config().getconf()
        status = conf['arch']
        self.assertEqual(status, "i386")
        #
        mock_machine.return_value = "armXX"
        mock_architecture.return_value = ["32bit", ]
        conf = Config().getconf()
        status = conf['arch']
        self.assertEqual(status, "arm")
        #
        mock_machine.return_value = "armXX"
        mock_architecture.return_value = ["", ]
        conf = Config().getconf()
        status = conf['arch']
        self.assertEqual(status, "arm64")

    @patch('udocker.config.platform.system')
    def test_06_osversion(self, mock_system):
        """Test Config._osversion()."""
        mock_system.return_value = "Linux"
        conf = Config().getconf()
        status = conf['osversion']
        self.assertEqual(status, "linux")
        #
        mock_system.return_value = "Linux"
        mock_system.side_effect = NameError('platform system')
        conf = Config().getconf()
        status = conf['osversion']
        self.assertEqual(status, "")

    @patch('udocker.config.platform.linux_distribution')
    def test_07_osdistribution(self, mock_distribution):
        """Test Config._osdistribution()."""
        mock_distribution.return_value = ("DISTRO XX", "1.0", "DUMMY")
        conf = Config().getconf()
        status = conf['osdistribution']
        self.assertEqual(status, ("DISTRO", "1"))

    @patch('udocker.config.platform.release')
    def test_08_oskernel(self, mock_release):
        """Test Config._oskernel()."""
        mock_release.return_value = "1.2.3"
        conf = Config().getconf()
        status = conf['oskernel']
        self.assertEqual(status, "1.2.3")
        #
        mock_release.return_value = "1.2.3"
        mock_release.side_effect = NameError('platform release')
        conf = Config().getconf()
        status = conf['oskernel']
        self.assertEqual(status, "3.2.1")

    @patch('udocker.msg.Msg')
    def test_09_oskernel_isgreater(self, mock_msg):
        """Test Config.oskernel_isgreater()."""
        Msg = mock_msg
        conf = Config().getconf()
        #
        conf['oskernel'] = "1.1.2-"
        status = Config().oskernel_isgreater([1, 1, 1])
        self.assertTrue(status)
        #
        conf['oskernel'] = "1.2.1-"
        status = Config().oskernel_isgreater([1, 1, 1])
        self.assertTrue(status)

        # TODO: recheck this test
        #conf['oskernel'] = "1.0.0-"
        #status = Config().oskernel_isgreater([1, 1, 1])
        #self.assertFalse(status)

    @patch('udocker.msg.Msg')
    def test_10_getconf(self, mock_msg):
        """Test Config.getconf()."""
        conf = Config().getconf()
        conf['topdir'] = "/.udocker"
        self.assertFalse(mock_msg.return_value.err.called)

        # TODO: Test raise no topdir
        #conf = Config().getconf()
        #conf['topdir'] = ""
        #with self.assertRaises(SystemExit) as confexpt:
        #    conf._verify_config()
        #self.assertEqual(confexpt.exception.code, 1)


if __name__ == '__main__':
    main()
