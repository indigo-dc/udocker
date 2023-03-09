#!/usr/bin/env python
"""
udocker unit tests: Keystore
"""
import pytest
from udocker.helper.keystore import KeyStore


@pytest.fixture
def kstore():
    return KeyStore("ksfile")


def test_01__verify_keystore(mocker, kstore):
    """Test01 KeyStore()._verify_keystore()."""
    mock_fu_uid = mocker.patch('udocker.helper.keystore.FileUtil.uid', return_value=1001)
    mock_hi_uid = mocker.patch('udocker.helper.keystore.HostInfo.uid', return_value=10)
    mock_pdir = mocker.patch('os.path.dirname')

    pytest.raises(OSError, kstore._verify_keystore)
    assert mock_fu_uid.call_count == 1
    assert mock_hi_uid.call_count == 0
    assert mock_pdir.call_count == 0


def test_02__verify_keystore(mocker, kstore):
    """Test02 KeyStore()._verify_keystore()."""
    mock_fu_uid = mocker.patch('udocker.helper.keystore.FileUtil.uid', side_effect=[10, 1001])
    mock_hi = mocker.patch('udocker.helper.keystore.HostInfo')
    mock_hi.return_value.uid = 10
    mock_pdir = mocker.patch('os.path.dirname', return_value="somedir/filename")

    pytest.raises(OSError, kstore._verify_keystore)
    assert mock_fu_uid.call_count == 2
    mock_hi.return_value.uid.assert_called()
    assert mock_pdir.call_count == 1


# data_verks = (([1001, 1001], 1, 10, 0, 0, False, 0),
#               ([10, 1001], 1, 10, 1, 1, 0o077, 0))

# @pytest.mark.parametrize("se_fuuid,cnt_fuuid,ret_hiuid,cnt_hiuid,cnt_pdir,ret_stat,cnt_stat",
#                          data_verks)
# def test_01__verify_keystore(mocker, kstore, se_fuuid, cnt_fuuid, ret_hiuid, cnt_hiuid,
#                              cnt_pdir, ret_stat, cnt_stat):
#     """Test01 KeyStore()._verify_keystore()."""
#     mock_fu_uid = mocker.patch('udocker.helper.keystore.FileUtil.uid', side_effect=se_fuuid)
#     mock_hi_uid = mocker.patch('udocker.helper.keystore.HostInfo.uid', return_value=ret_hiuid)
#     mock_pdir = mocker.patch('udocker.helper.keystore.os.path.dirname',
#                              return_value="somedir/filename")
#     mock_stat = mocker.patch('udocker.helper.keystore.os.stat')
#     mock_stat.return_value.st_mode = ret_stat

#     pytest.raises(OSError, kstore._verify_keystore)
#     assert mock_fu_uid.call_count == cnt_fuuid
#     assert mock_hi_uid.call_count == cnt_hiuid
#     assert mock_pdir.call_count == cnt_pdir
#     assert mock_stat.call_count == cnt_stat



# BUILTINS = "builtins"
# @patch('udocker.helper.keystore.os.path.dirname')
# @patch('udocker.helper.keystore.HostInfo')
# @patch('udocker.helper.keystore.FileUtil')
# def test_02__verify_keystore(self, mock_futil, mock_hinfo, mock_pdir):
#     """Test02 KeyStore()._verify_keystore()."""
#     mock_futil.return_value.uid.return_value = 1001
#     mock_hinfo.return_value.uid.return_value = 0
#     kstore = KeyStore("filename")
#     self.assertRaises(IOError, kstore._verify_keystore)

#     mock_futil.return_value.uid.side_effect = [1001, 1000]
#     mock_hinfo.return_value.uid.return_value = 1001
#     mock_pdir.return_value = "somedir/filename"
#     kstore = KeyStore("filename")
#     self.assertRaises(IOError, kstore._verify_keystore)

# @patch('udocker.helper.keystore.json.load')
# def test_03__read_all(self, mock_jload):
#     """Test03 KeyStore()._read_all()."""
#     url = u'https://xxx'
#     email = u'user@domain'
#     auth = u'xxx'
#     credentials = {url: {u'email': email, u'auth': auth}}
#     mock_jload.return_value = credentials
#     with patch(BUILTINS + '.open', mock_open()):
#         kstore = KeyStore("filename")
#         status = kstore._read_all()
#         self.assertEqual(status, credentials)

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
