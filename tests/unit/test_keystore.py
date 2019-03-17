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

sys.path.append('../../')

from udocker.helper.keystore import KeyStore

if sys.version_info[0] >= 3:
    BUILTINS = "builtins"
else:
    BUILTINS = "__builtin__"


def set_env():
    """Set environment variables."""
    if not os.getenv("HOME"):
        os.environ["HOME"] = os.getcwd()

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
        kstore = KeyStore("filename")
        self.assertEqual(kstore.keystore_file, "filename")

    @mock.patch('json.load')
    def test_02__read_all(self, mock_jload):
        """Test KeyStore()._read_all() read credentials."""
        self._init()
        mock_jload.return_value = self.credentials
        with mock.patch(BUILTINS + '.open', mock.mock_open()):
            kstore = KeyStore("filename")
            self.assertEqual(self.credentials, kstore._read_all())

    @mock.patch('udocker.helper.keystore.KeyStore._verify_keystore')
    @mock.patch('udocker.config.Config')
    def test_03__shred(self, mock_config, mock_verks):
        """Test KeyStore()._shred() erase file content."""
        Config = mock_config
        Config.tmpdir = "/tmp"
        with mock.patch(BUILTINS + '.open', mock.mock_open()):
            kstore = KeyStore("filename")
            self.assertFalse(kstore._shred())

    @mock.patch('udocker.helper.keystore.KeyStore._verify_keystore')
    @mock.patch('udocker.config.Config')
    @mock.patch('os.stat')
    def test_04__shred(self, mock_stat, mock_config, mock_verks):
        """Test KeyStore()._shred() erase file content."""
        Config = mock_config
        Config.tmpdir = "/tmp"
        mock_stat.return_value.st_size = 123
        with mock.patch(BUILTINS + '.open', mock.mock_open()):
            kstore = KeyStore("filename")
            self.assertTrue(kstore._shred())

    @mock.patch('udocker.config.Config')
    @mock.patch('json.dump')
    @mock.patch('os.umask')
    def test_05__write_all(self, mock_umask, mock_jdump, mock_config):
        """Test KeyStore()._write_all() write all credentials to file."""
        self._init()
        Config = mock_config
        Config.tmpdir = "/tmp"
        mock_umask.return_value = 0o77
        mock_jdump.side_effect = IOError('json dump')
        with mock.patch(BUILTINS + '.open', mock.mock_open()):
            kstore = KeyStore("filename")
            self.assertFalse(kstore._write_all(self.credentials))

    @mock.patch('udocker.config.Config')
    @mock.patch('udocker.helper.keystore.KeyStore._read_all')
    def test_06_get(self, mock_readall, mock_config):
        """Test KeyStore().get() get credential for url from file."""
        self._init()
        Config = mock_config
        Config.tmpdir = "/tmp"
        mock_readall.return_value = self.credentials
        kstore = KeyStore("filename")
        self.assertTrue(kstore.get(self.url))
        self.assertFalse(kstore.get("NOT EXISTING ENTRY"))

    @mock.patch('udocker.config.Config')
    @mock.patch('udocker.helper.keystore.KeyStore._write_all')
    @mock.patch('udocker.helper.keystore.KeyStore._read_all')
    def test_07_put(self, mock_readall, mock_writeall, mock_config):
        """Test KeyStore().put() put credential for url to file."""
        self._init()
        Config = mock_config
        Config.tmpdir = "/tmp"
        kstore = KeyStore("filename")
        self.assertFalse(kstore.put("", "", ""))
        mock_readall.return_value = dict()
        kstore.put(self.url, self.auth, self.email)
        mock_writeall.assert_called_once_with(self.credentials)

    @mock.patch('udocker.config.Config')
    @mock.patch('udocker.helper.keystore.KeyStore._verify_keystore')
    @mock.patch('udocker.helper.keystore.KeyStore._shred')
    @mock.patch('udocker.helper.keystore.KeyStore._write_all')
    @mock.patch('udocker.helper.keystore.KeyStore._read_all')
    def test_08_delete(self, mock_readall, mock_writeall, mock_shred,
                       mock_verks, mock_config):
        """Test KeyStore().delete() delete credential for url from file."""
        self._init()
        Config = mock_config
        Config.tmpdir = "/tmp"
        mock_readall.return_value = self.credentials
        kstore = KeyStore("filename")
        kstore.delete(self.url)
        mock_writeall.assert_called_once_with({})
        mock_verks.side_effect = KeyError
        self.assertFalse(kstore.delete(self.url))

    @mock.patch('udocker.helper.keystore.KeyStore._verify_keystore')
    @mock.patch('udocker.config.Config')
    @mock.patch('os.unlink')
    @mock.patch('udocker.helper.keystore.KeyStore._shred')
    def test_09_erase(self, mock_shred, mock_unlink,
                      mock_config, mock_verks):
        """Test KeyStore().erase() erase credentials file."""
        self._init()
        Config = mock_config
        Config.tmpdir = "/tmp"
        kstore = KeyStore("filename")
        self.assertTrue(kstore.erase())
        mock_unlink.assert_called_once_with("filename")

        mock_unlink.side_effect = IOError
        self.assertFalse(kstore.erase())

