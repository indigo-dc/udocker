#!/usr/bin/env python
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

    def setUp(self):
        self.conf = Config().getconf()

    def tearDown(self):
        pass

    def test_01_init(self):
        """Test KeyStore() constructor."""
        kstore = KeyStore(self.conf, "filename")
        status = kstore.keystore_file
        self.assertEqual(status, "filename")

    def test_02__verify_keystore(self):
        """Test KeyStore()._verify_keystore()."""
        pass

    @patch('udocker.helper.keystore.json.load')
    def test_03__read_all(self, mock_jload):
        """Test KeyStore()._read_all() read credentials."""
        url = u'https://xxx'
        email = u'user@domain'
        auth = u'xxx'
        credentials = {url: {u'email': email, u'auth': auth}}
        mock_jload.return_value = credentials
        with patch(BUILTINS + '.open', mock_open()):
            kstore = KeyStore(self.conf, "filename")
            status = kstore._read_all()
            self.assertEqual(status, credentials)

    @patch.object(KeyStore, '_verify_keystore')
    @patch('udocker.helper.keystore.os.stat')
    def test_04__shred(self, mock_stat, mock_verks):
        """Test KeyStore()._shred() erase file content."""
        with patch(BUILTINS + '.open', mock_open()):
            kstore = KeyStore(self.conf, "filename")
            status = kstore._shred()
            self.assertEqual(status, 0)

        mock_stat.return_value.st_size = 123
        with patch(BUILTINS + '.open', mock_open()):
            kstore = KeyStore(self.conf, "filename")
            status = kstore._shred()
            self.assertEqual(status, 0)

    @patch('udocker.helper.keystore.json.dump')
    @patch('udocker.helper.keystore.os.umask')
    def test_05__write_all(self, mock_umask, mock_jdump):
        """Test KeyStore()._write_all() write all credentials to file."""
        url = u'https://xxx'
        email = u'user@domain'
        auth = u'xxx'
        credentials = {url: {u'email': email, u'auth': auth}}
        mock_umask.return_value = 0o77
        mock_jdump.side_effect = IOError('json dump')
        with patch(BUILTINS + '.open', mock_open()):
            kstore = KeyStore(self.conf, "filename")
            status = kstore._write_all(credentials)
            self.assertEqual(status, 1)

    @patch.object(KeyStore, '_read_all')
    def test_06_get(self, mock_readall):
        """Test KeyStore().get() get credential for url from file."""
        url = u'https://xxx'
        email = u'user@domain'
        auth = u'xxx'
        credentials = {url: {u'email': email, u'auth': auth}}
        mock_readall.return_value = credentials
        kstore = KeyStore(self.conf, "filename")
        self.assertTrue(kstore.get(url))
        self.assertFalse(kstore.get("NOT EXISTING ENTRY"))

    @patch.object(KeyStore, '_write_all')
    @patch.object(KeyStore, '_read_all')
    def test_07_put(self, mock_readall, mock_writeall):
        """Test KeyStore().put() put credential for url to file."""
        url = u'https://xxx'
        email = u'user@domain'
        auth = u'xxx'
        credentials = {url: {u'email': email, u'auth': auth}}
        kstore = KeyStore(self.conf, "filename")
        self.assertFalse(kstore.put("", "", ""))

        mock_readall.return_value = dict()
        kstore = KeyStore(self.conf, "filename")
        kstore.put(url, auth, email)
        mock_writeall.assert_called_once_with(credentials)

    @patch.object(KeyStore, '_verify_keystore')
    @patch.object(KeyStore, '_shred')
    @patch.object(KeyStore, '_write_all')
    @patch.object(KeyStore, '_read_all')
    def test_08_delete(self, mock_readall, mock_writeall, mock_shred,
                       mock_verks):
        """Test KeyStore().delete() delete credential for url from file."""
        url = u'https://xxx'
        email = u'user@domain'
        auth = u'xxx'
        credentials = {url: {u'email': email, u'auth': auth}}
        mock_readall.return_value = credentials
        mock_writeall.return_value = 0
        kstore = KeyStore(self.conf, "filename")
        status = kstore.delete(url)
        mock_writeall.assert_called_once_with({})
        self.assertEqual(status, 0)

    @patch('udocker.helper.keystore.os.unlink')
    @patch.object(KeyStore, '_verify_keystore')
    @patch.object(KeyStore, '_shred')
    def test_09_erase(self, mock_shred, mock_verks, mock_unlink):
        """Test KeyStore().erase() erase credentials file."""
        kstore = KeyStore(self.conf, "filename")
        self.assertEqual(kstore.erase(), 0)
        mock_unlink.assert_called_once_with("filename")

        mock_unlink.side_effect = IOError
        kstore = KeyStore(self.conf, "filename")
        self.assertEqual(kstore.erase(), 1)


if __name__ == '__main__':
    main()
