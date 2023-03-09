#!/usr/bin/env python
"""
udocker unit tests: Keystore
"""
import pytest
from io import StringIO
from udocker.helper.keystore import KeyStore


@pytest.fixture
def kstore():
    return KeyStore("ksfile")


def test_01__verify_keystore(mocker, kstore):
    """Test01 KeyStore()._verify_keystore()."""
    mock_fu_uid = mocker.patch('udocker.helper.keystore.FileUtil.uid', return_value=1001)
    mock_hi = mocker.patch('udocker.helper.keystore.HostInfo')
    mock_pdir = mocker.patch('os.path.dirname')

    pytest.raises(OSError, kstore._verify_keystore)
    assert mock_fu_uid.call_count == 1
    mock_hi.assert_not_called()
    mock_pdir.assert_not_called()


def test_02__verify_keystore(mocker, kstore):
    """Test02 KeyStore()._verify_keystore()."""
    mock_fu = mocker.patch('udocker.helper.keystore.FileUtil')
    mock_fu.return_value.uid.side_effect = [10, 1001]
    mock_hi = mocker.patch('udocker.helper.keystore.HostInfo')
    mock_hi.uid = 10
    mock_pdir = mocker.patch('os.path.dirname', return_value="somedir/filename")
    mock_stat = mocker.patch('udocker.helper.keystore.os.stat')

    pytest.raises(OSError, kstore._verify_keystore)
    assert mock_fu.return_value.uid.call_count == 2
    mock_pdir.assert_called()
    mock_stat.assert_not_called()


def test_03__verify_keystore(mocker, kstore):
    """Test03 KeyStore()._verify_keystore()."""
    mock_fu_uid = mocker.patch('udocker.helper.keystore.FileUtil.uid', side_effect=[10, 10])
    mock_hi = mocker.patch('udocker.helper.keystore.HostInfo')
    mock_hi.uid = 10
    mock_pdir = mocker.patch('os.path.dirname', return_value="somedir/filename")
    mock_stat = mocker.patch('udocker.helper.keystore.os.stat')
    mock_stat.return_value.st_mode = 0o077

    pytest.raises(OSError, kstore._verify_keystore)
    assert mock_fu_uid.call_count == 2
    mock_pdir.assert_called()
    mock_stat.assert_called()


def test_04__read_all(mocker, kstore):
    """Test04 KeyStore()._read_all()."""
    url = 'https://xxx'
    email = 'user@domain'
    auth = 'xxx'
    credentials = {url: {'email': email, 'auth': auth}}
    mock_jload = mocker.patch('json.load', return_value=credentials)
    mock_jfile = mocker.mock_open(read_data=str(credentials))
    mocker.patch("builtins.open", mock_jfile)
    mock_loginfo = mocker.patch('udocker.helper.keystore.LOG.info')

    out = kstore._read_all()
    assert out == credentials
    mock_jload.assert_called()
    mock_loginfo.assert_called()


def test_05__read_all(mocker, kstore):
    """Test05 KeyStore()._read_all()."""
    mock_jload = mocker.patch('json.load')
    mock_jfile = mocker.mock_open()
    mock_jfile.side_effect = OSError
    mock_loginfo = mocker.patch('udocker.helper.keystore.LOG.info')

    out = kstore._read_all()
    assert out == {}
    mock_jload.assert_not_called()
    mock_loginfo.assert_not_called()



# @patch.object(KeyStore, '_verify_keystore')
# @patch('udocker.helper.keystore.FileUtil.size')
# def test_04__shred(self, mock_size, mock_verks):
#     """Test04 KeyStore()._shred()."""
#     mock_verks.return_value = None
#     with patch(BUILTINS + '.open', mock_open()):
#         kstore = KeyStore("filename")
#         status = kstore._shred()
#         self.assertEqual(status, 0)

#     mock_size.return_value = 123
#     mock_verks.return_value = None
#     with patch(BUILTINS + '.open', mock_open()):
#         kstore = KeyStore("filename")
#         status = kstore._shred()
#         self.assertEqual(status, 0)

#     mock_size.side_effect = IOError("fail")
#     kstore = KeyStore("filename")
#     status = kstore._shred()
#     self.assertEqual(status, 1)

# @patch.object(KeyStore, '_verify_keystore')
# @patch('udocker.helper.keystore.json.dump')
# @patch('udocker.helper.keystore.os.umask')
# def test_05__write_all(self, mock_umask, mock_jdump, mock_verks):
#     """Test05 KeyStore()._write_all()."""
#     url = u'https://xxx'
#     email = u'user@domain'
#     auth = u'xxx'
#     credentials = {url: {u'email': email, u'auth': auth}}
#     mock_umask.return_value = 0o77
#     mock_jdump.side_effect = IOError('json dump')
#     mock_verks.return_value = None
#     with patch(BUILTINS + '.open', mock_open()):
#         kstore = KeyStore("filename")
#         status = kstore._write_all(credentials)
#         self.assertEqual(status, 1)

#     mock_umask.side_effect = IOError("fail")
#     kstore = KeyStore("filename")
#     status = kstore._write_all(credentials)
#     self.assertEqual(status, 1)

# @patch.object(KeyStore, '_read_all')
# def test_06_get(self, mock_readall):
#     """Test06 KeyStore().get()."""
#     url = u'https://xxx'
#     email = u'user@domain'
#     auth = u'xxx'
#     credentials = {url: {u'email': email, u'auth': auth}}
#     mock_readall.return_value = credentials
#     kstore = KeyStore("filename")
#     self.assertTrue(kstore.get(url))
#     self.assertFalse(kstore.get("NOT EXISTING ENTRY"))

# @patch.object(KeyStore, '_shred')
# @patch.object(KeyStore, '_write_all')
# @patch.object(KeyStore, '_read_all')
# def test_07_put(self, mock_readall, mock_writeall, mock_shred):
#     """Test07 KeyStore().put()."""
#     url = u'https://xxx'
#     email = u'user@domain'
#     auth = u'xxx'
#     credentials = {url: {u'email': email, u'auth': auth}}
#     mock_shred.return_value = None
#     kstore = KeyStore("filename")
#     status = kstore.put("", "", "")
#     self.assertEqual(status, 1)

#     mock_shred.return_value = None
#     mock_readall.return_value = dict()
#     kstore = KeyStore("filename")
#     status = kstore.put(url, auth, email)
#     mock_writeall.assert_called_once_with(credentials)

# @patch.object(KeyStore, '_verify_keystore')
# @patch.object(KeyStore, '_shred')
# @patch.object(KeyStore, '_write_all')
# @patch.object(KeyStore, '_read_all')
# def test_08_delete(self, mock_readall, mock_writeall, mock_shred, mock_verks):
#     """Test08 KeyStore().delete()."""
#     url = u'https://xxx'
#     email = u'user@domain'
#     auth = u'xxx'
#     credentials = {url: {u'email': email, u'auth': auth}}
#     mock_readall.return_value = credentials
#     mock_writeall.return_value = 0
#     mock_shred.return_value = 0
#     mock_verks.return_value = None
#     kstore = KeyStore("filename")
#     status = kstore.delete(url)
#     mock_writeall.assert_called_once_with({})
#     self.assertEqual(status, 0)

# @patch('udocker.helper.keystore.os.unlink')
# @patch.object(KeyStore, '_verify_keystore')
# @patch.object(KeyStore, '_shred')
# def test_09_erase(self, mock_shred, mock_verks, mock_unlink):
#     """Test09 KeyStore().erase()."""
#     mock_verks.return_value = None
#     mock_shred.return_value = None
#     kstore = KeyStore("filename")
#     self.assertEqual(kstore.erase(), 0)
#     mock_unlink.assert_called_once_with("filename")

#     mock_verks.return_value = None
#     mock_shred.return_value = None
#     mock_unlink.side_effect = IOError
#     kstore = KeyStore("filename")
#     self.assertEqual(kstore.erase(), 1)
