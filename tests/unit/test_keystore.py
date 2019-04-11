#!/usr/bin/env python2
"""
udocker unit tests: Keystore
"""
import sys
from unittest import TestCase, main
try:
    from unittest.mock import Mock, MagicMock, patch, mock_open
except ImportError:
    from mock import Mock, MagicMock, patch, mock_open

sys.path.append('.')

from udocker.helper.keystore import KeyStore
from udocker.config import Config

if sys.version_info[0] >= 3:
    BUILTINS = "builtins"
else:
    BUILTINS = "__builtin__"


class KeyStoreTestCase(TestCase):
    """Test KeyStore() local basic credentials storage."""

    def _init(self):
        """Common variables."""
        self.conf = Config().getconf()
        self.url = u'https://xxx'
        self.email = u'user@domain'
        self.auth = u'xxx'
        self.credentials = {self.url: {u'email': self.email,
                                       u'auth': self.auth}}

    def test_01_init(self):
        """Test KeyStore() constructor."""
        self._init()
        kstore = KeyStore(self.conf, "filename")
        self.assertEqual(kstore.keystore_file, "filename")

    @patch('udocker.helper.keystore.json.load')
    def test_02__read_all(self, mock_jload):
        """Test KeyStore()._read_all() read credentials."""
        self._init()
        mock_jload.return_value = self.credentials
        with patch(BUILTINS + '.open', mock_open()):
            kstore = KeyStore(self.conf, "filename")
            self.assertEqual(self.credentials, kstore._read_all())

    @patch('udocker.helper.keystore.KeyStore._verify_keystore')
    def test_03__shred(self, mock_verks):
        """Test KeyStore()._shred() erase file content."""
        self._init()
        self.conf['tmpdir'] = "/tmp"
        with patch(BUILTINS + '.open', mock_open()):
            kstore = KeyStore(self.conf, "filename")
            self.assertEqual(kstore._shred(), 1)

    @patch('udocker.helper.keystore.KeyStore._verify_keystore')
    @patch('udocker.helper.keystore.os.stat')
    def test_04__shred(self, mock_stat, mock_verks):
        """Test KeyStore()._shred() erase file content."""
        self._init()
        self.conf['tmpdir'] = "/tmp"
        mock_stat.return_value.st_size = 123
        with patch(BUILTINS + '.open', mock_open()):
            kstore = KeyStore(self.conf, "filename")
            self.assertTrue(kstore._shred())

    @patch('udocker.helper.keystore.json.dump')
    @patch('udocker.helper.keystore.os.umask')
    def test_05__write_all(self, mock_umask, mock_jdump):
        """Test KeyStore()._write_all() write all credentials to file."""
        self._init()
        self.conf['tmpdir'] = "/tmp"
        mock_umask.return_value = 0o77
        mock_jdump.side_effect = IOError('json dump')
        with patch(BUILTINS + '.open', mock_open()):
            kstore = KeyStore(self.conf, "filename")
            self.assertFalse(kstore._write_all(self.credentials))

    @patch('udocker.helper.keystore.KeyStore._read_all')
    def test_06_get(self, mock_readall):
        """Test KeyStore().get() get credential for url from file."""
        self._init()
        self.conf['tmpdir'] = "/tmp"
        mock_readall.return_value = self.credentials
        kstore = KeyStore(self.conf, "filename")
        self.assertTrue(kstore.get(self.url))
        self.assertFalse(kstore.get("NOT EXISTING ENTRY"))

    @patch('udocker.helper.keystore.KeyStore._write_all')
    @patch('udocker.helper.keystore.KeyStore._read_all')
    def test_07_put(self, mock_readall, mock_writeall):
        """Test KeyStore().put() put credential for url to file."""
        self._init()
        self.conf['tmpdir'] = "/tmp"
        kstore = KeyStore(self.conf, "filename")
        self.assertFalse(kstore.put("", "", ""))
        mock_readall.return_value = dict()
        kstore.put(self.url, self.auth, self.email)
        mock_writeall.assert_called_once_with(self.credentials)

    @patch('udocker.helper.keystore.KeyStore._verify_keystore')
    @patch('udocker.helper.keystore.KeyStore._shred')
    @patch('udocker.helper.keystore.KeyStore._write_all')
    @patch('udocker.helper.keystore.KeyStore._read_all')
    def test_08_delete(self, mock_readall, mock_writeall, mock_shred,
                       mock_verks):
        """Test KeyStore().delete() delete credential for url from file."""
        self._init()
        self.conf['tmpdir'] = "/tmp"
        mock_readall.return_value = self.credentials
        kstore = KeyStore(self.conf, "filename")
        kstore.delete(self.url)
        mock_writeall.assert_called_once_with({})
        mock_verks.side_effect = KeyError
        self.assertFalse(kstore.delete(self.url))

    @patch('udocker.helper.keystore.KeyStore._verify_keystore')
    @patch('udocker.helper.keystore.os.unlink')
    @patch('udocker.helper.keystore.KeyStore._shred')
    def test_09_erase(self, mock_shred, mock_unlink, mock_verks):
        """Test KeyStore().erase() erase credentials file."""
        self._init()
        self.conf['tmpdir'] = "/tmp"
        kstore = KeyStore(self.conf, "filename")
        self.assertEqual(kstore.erase(), 0)
        mock_unlink.assert_called_once_with("filename")

        mock_unlink.side_effect = IOError
        self.assertEqual(kstore.erase(), 1)


if __name__ == '__main__':
    main()
