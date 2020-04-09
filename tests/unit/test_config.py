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
        """Test01 Config() constructor."""
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
        # self.assertIsInstance(self.config.conf['cmd'], list)
        self.assertIsInstance(self.config.conf['sysdirs_list'], tuple)
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

    # private methods
    #@patch('udocker.config.os.getenv')
    #def test_02__file_override(self, mock_getenv):
    #    """Test02 Config()._file_override"""
    #    mock_getenv.return_value = "5"
    #    self.Config._file_override()
    #    self.assertEqual(self.Config.conf['verbose_level'], 5)

    # private methods
    #@patch('udocker.config.os.getenv')
    #def test_03__env_override(self, mock_getenv):
    #    """Test03 Config()._env_override"""
    #    mock_getenv.return_value = "5"
    #    self.Config._env_override()
    #    self.assertEqual(self.Config.conf['verbose_level'], 5)

    @patch.object(Config, '_env_override')
    @patch.object(Config, '_file_override')
    @patch('udocker.config.Config')
    def test_04_getconf(self, mock_conf, mock_fileover, mock_envover):
        """Test04 Config.getconf()."""
        mock_conf.return_value.conf["topdir"] = "/.udocker"
        self.config.getconf()
        self.assertTrue(mock_fileover.called)
        self.assertTrue(mock_envover.called)

    @patch.object(Config, '_file_override')
    @patch('udocker.config.Config')
    def test_05_container(self, mock_conf, mock_fileover):
        """Test05 Config.container()."""
        mock_conf.return_value.conf["topdir"] = "/.udocker"
        self.config.container()
        self.assertTrue(mock_fileover.called)

if __name__ == '__main__':
    main()
