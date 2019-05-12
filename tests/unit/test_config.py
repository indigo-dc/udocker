#!/usr/bin/env python

# -*- coding: utf-8 -*-
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

    def setUp(self):
        self.Config = Config()

    def tearDown(self):
        pass

    def test_01_init(self):
        """Test Config() constructor."""
        self.assertIsInstance(self.Config.conf['verbose_level'], int)
        self.assertIsInstance(self.Config.conf['topdir'], str)
        self.assertIs(self.Config.conf['bindir'], None)
        self.assertIs(self.Config.conf['libdir'], None)
        self.assertIs(self.Config.conf['reposdir'], None)
        self.assertIs(self.Config.conf['layersdir'], None)
        self.assertIs(self.Config.conf['containersdir'], None)
        self.assertIsInstance(self.Config.conf['homedir'], str)
        self.assertIsInstance(self.Config.conf['config'], str)
        self.assertIsInstance(self.Config.conf['keystore'], str)
        self.assertIsInstance(self.Config.conf['tmpdir'], str)
        self.assertIsInstance(self.Config.conf['tarball'], str)
        self.assertIsInstance(self.Config.conf['cmd'], list)
        self.assertIsInstance(self.Config.conf['sysdirs_list'], tuple)
        self.assertIsInstance(self.Config.conf['hostauth_list'], tuple)
        self.assertIsInstance(self.Config.conf['dri_list'], tuple)
        self.assertIsInstance(self.Config.conf['cpu_affinity_exec_tools'], tuple)
        self.assertIsInstance(self.Config.conf['location'], str)
        self.assertIsInstance(self.Config.conf['http_proxy'], str)
        self.assertIsInstance(self.Config.conf['timeout'], int)
        self.assertIsInstance(self.Config.conf['download_timeout'], int)
        self.assertIsInstance(self.Config.conf['ctimeout'], int)
        self.assertIsInstance(self.Config.conf['http_agent'], str)
        self.assertIsInstance(self.Config.conf['http_insecure'], bool)
        self.assertIsInstance(self.Config.conf['dockerio_index_url'], str)
        self.assertIsInstance(self.Config.conf['dockerio_registry_url'], str)

    # TODO: need to be implemented
    # def test_02_file_override(self):
    #     """Test Config()._file_override"""
    #     pass

    # TODO: this test needs further work
    @patch('udocker.config.os.getenv')
    def test_03_env_override(self, mock_getenv):
        """Test Config()._env_override"""
        mock_getenv.return_value = "5"
        self.Config._env_override()
        self.assertEqual(self.Config.conf['verbose_level'], 5)


    def test_04_username(self):
        """Test Config._username()."""
        self.Config.conf['uid'] = os.getuid()
        user = self.Config._username()
        self.assertEqual(user, pwd.getpwuid(os.getuid()).pw_name)

        self.Config.conf['uid'] = 20000000
        user = self.Config._username()
        self.assertEqual(user, "")

    @patch('udocker.config.platform.architecture')
    @patch('udocker.config.platform.machine')
    def test_05_arch(self, mock_machine, mock_architecture):
        """Test Config._arch()."""

        mock_machine.return_value = "x86_64"
        mock_architecture.return_value = ["32bit", ]
        status = self.Config._arch()
        self.assertEqual(status, "i386")

        mock_machine.return_value = "x86_64"
        mock_architecture.return_value = ["", ]
        status = self.Config._arch()
        self.assertEqual(status, "amd64")

        mock_machine.return_value = "i686"
        mock_architecture.return_value = ["", ]
        status = self.Config._arch()
        self.assertEqual(status, "i386")

        mock_machine.return_value = "armXX"
        mock_architecture.return_value = ["32bit", ]
        status = self.Config._arch()
        self.assertEqual(status, "arm")

        mock_machine.return_value = "armXX"
        mock_architecture.return_value = ["", ]
        status = self.Config._arch()
        self.assertEqual(status, "arm64")

    @patch('udocker.config.platform.system')
    def test_06_osversion(self, mock_system):
        """Test Config._osversion()."""

        mock_system.return_value = "Linux"
        status = self.Config._osversion()
        self.assertEqual(status, "linux")

        mock_system.return_value = "Linux"
        mock_system.side_effect = NameError('platform system')
        status = self.Config._osversion()
        self.assertEqual(status, "")

    @patch('udocker.config.platform.linux_distribution')
    def test_07_osdistribution(self, mock_distribution):
        """Test Config._osdistribution()."""

        mock_distribution.return_value = ("DISTRO XX", "1.0", "DUMMY")
        status = self.Config._osdistribution()
        self.assertEqual(status, ("DISTRO", "1"))

    @patch('udocker.config.platform.release')
    def test_08_oskernel(self, mock_release):
        """Test Config._oskernel()."""

        mock_release.return_value = "1.2.3"
        status = self.Config._oskernel()
        self.assertEqual(status, "1.2.3")

        mock_release.return_value = "1.2.3"
        mock_release.side_effect = NameError('platform release')
        status = self.Config._oskernel()
        self.assertEqual(status, "3.2.1")

    @patch.object(Config, '_oskernel')
    @patch.object(Config, '_osdistribution')
    @patch.object(Config, '_osversion')
    @patch.object(Config, '_arch')
    @patch.object(Config, '_username')
    @patch('udocker.config.Config')
    def test_10_getconf(self, mock_conf, mock_user, mock_arch, mock_osver,
                        mock_osdistr, mock_oskern):
        """Test Config.getconf()."""
        mock_user.return_value = os.getuid()
        mock_arch.return_value = "i386"
        mock_osver.return_value = "linux"
        mock_osdistr.return_value = ("DISTRO", "1")
        mock_oskern.return_value = "1.1.2-"
        mock_conf.return_value.conf['topdir'] = "/.udocker"
        status = self.Config.getconf()
        self.assertTrue(mock_user.called)
        self.assertTrue(mock_arch.called)
        self.assertTrue(mock_osver.called)
        self.assertTrue(mock_osdistr.called)
        self.assertTrue(mock_oskern.called)

if __name__ == '__main__':
    main()
