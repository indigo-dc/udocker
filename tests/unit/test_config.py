#!/usr/bin/env python

# -*- coding: utf-8 -*-
"""
udocker unit tests: Config
"""

from unittest import TestCase, main
from udocker.config import Config

try:
    from unittest.mock import patch
except ImportError:
    from mock import patch



class ConfigTestCase(TestCase):
    """Test case for the udocker configuration."""

    def setUp(self):
        self.config = Config()

    def tearDown(self):
        pass

    def test_01_init(self):
        """Test Config() constructor."""
        self.assertIsInstance(self.config.conf['verbose_level'], int)
        self.assertIsInstance(self.config.conf['topdir'], str)
        self.assertIs(self.config.conf['bindir'], None)
        self.assertIs(self.config.conf['libdir'], None)
        self.assertIs(self.config.conf['reposdir'], None)
        self.assertIs(self.config.conf['layersdir'], None)
        self.assertIs(self.config.conf['containersdir'], None)
        self.assertIsInstance(self.config.conf['homedir'], str)
        self.assertIsInstance(self.config.conf['config'], str)
        self.assertIsInstance(self.config.conf['keystore'], str)
        self.assertIsInstance(self.config.conf['tmpdir'], str)
        self.assertIsInstance(self.config.conf['tarball'], str)
        self.assertIsInstance(self.config.conf['cmd'], list)
        self.assertIsInstance(self.config.conf['sysdirs_list'], tuple)
        self.assertIsInstance(self.config.conf['hostauth_list'], tuple)
        self.assertIsInstance(self.config.conf['dri_list'], tuple)
        self.assertIsInstance(self.config.conf['location'], str)
        self.assertIsInstance(self.config.conf['http_proxy'], str)
        self.assertIsInstance(self.config.conf['timeout'], int)
        self.assertIsInstance(self.config.conf['download_timeout'], int)
        self.assertIsInstance(self.config.conf['ctimeout'], int)
        self.assertIsInstance(self.config.conf['http_agent'], str)
        self.assertIsInstance(self.config.conf['http_insecure'], bool)
        self.assertIsInstance(self.config.conf['dockerio_index_url'], str)
        self.assertIsInstance(self.config.conf['dockerio_registry_url'], str)

    @patch.object(Config, '_env_override')
    @patch.object(Config, '_file_override')
    @patch('udocker.config.OSInfo.osdistribution')
    @patch('udocker.config.OSInfo.osversion')
    @patch('udocker.config.OSInfo.arch')
    @patch('udocker.config.platform.release')
    @patch('udocker.config.pwd.getpwuid')
    @patch('udocker.config.os.getgid')
    @patch('udocker.config.os.getuid')
    @patch('udocker.config.Config')
    def test_02_getconf(self, mock_conf, mock_uid, mock_gid,
                        mock_uname, mock_platrel, mock_arch, mock_version,
                        mock_distribution, mock_fileover, mock_envover):
        """Test Config.getconf()."""
        mock_conf.return_value.conf["topdir"] = "/.udocker"
        mock_uid.return_value = "500"
        mock_gid.return_value = "500"
        mock_uname.return_value.pw_name.return_value = "username"
        mock_platrel.return_value = "1.1.2-"
        mock_arch.return_value = "i386"
        mock_version.return_value = "linux"
        mock_distribution.return_value = ("DISTRO", "1")
        self.config.getconf()
        self.assertTrue(mock_uid.called)
        self.assertTrue(mock_gid.called)
        self.assertTrue(mock_platrel.called)
        self.assertTrue(mock_arch.called)
        self.assertTrue(mock_version.called)
        self.assertTrue(mock_distribution.called)
        self.assertTrue(mock_fileover.called)
        self.assertTrue(mock_envover.called)
        self.assertEqual(self.config.conf["arch"], "i386")

    # private methods
    #@patch('udocker.config.os.getenv')
    #def test_03__env_override(self, mock_getenv):
    #    """Test Config()._env_override"""
    #    mock_getenv.return_value = "5"
    #    self.Config._env_override()
    #    self.assertEqual(self.Config.conf['verbose_level'], 5)

if __name__ == '__main__':
    main()
