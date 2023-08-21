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


def test_06__shred(mocker, kstore):
    """Test06 KeyStore()._shred()."""
    mock_verks = mocker.patch.object(KeyStore, '_verify_keystore')
    mock_size = mocker.patch('udocker.helper.keystore.FileUtil.size', return_value=123)
    mock_file = mocker.mock_open()
    mocker.patch("builtins.open", mock_file)
    out = kstore._shred()
    assert out == 0
    mock_verks.assert_called()
    mock_size.assert_called()
    mock_file.assert_called()


def test_07__shred(mocker, kstore):
    """Test07 KeyStore()._shred()."""
    mock_verks = mocker.patch.object(KeyStore, '_verify_keystore')
    mock_size = mocker.patch('udocker.helper.keystore.FileUtil.size', side_effect=OSError('fail'))
    mock_file = mocker.mock_open()
    mocker.patch("builtins.open", mock_file)
    out = kstore._shred()
    assert out == 1
    mock_verks.assert_called()
    mock_size.assert_called()
    mock_file.assert_not_called()


def test_08__write_all(mocker, kstore):
    """Test08 KeyStore()._write_all()."""
    mock_verks = mocker.patch.object(KeyStore, '_verify_keystore')
    mock_umask = mocker.patch('os.umask', side_effect=[0o77, 0o77])
    mock_jdump = mocker.patch('json.dump')
    mock_file = mocker.mock_open()
    mocker.patch("builtins.open", mock_file)
    out = kstore._write_all('{auth}')
    assert out == 0
    mock_verks.assert_called()
    assert mock_umask.call_count == 2
    mock_jdump.assert_called()
    mock_file.assert_called()


def test_09__write_all(mocker, kstore):
    """Test09 KeyStore()._write_all()."""
    mock_verks = mocker.patch.object(KeyStore, '_verify_keystore')
    mock_umask = mocker.patch('os.umask', side_effect=[0o77, 0o77])
    mock_jdump = mocker.patch('json.dump')
    mock_file = mocker.mock_open()
    mopen = mocker.patch("builtins.open", mock_file)
    mopen.side_effect = OSError
    out = kstore._write_all('{auth}')
    assert out == 1
    mock_verks.assert_called()
    assert mock_umask.call_count == 2
    mock_jdump.assert_not_called()
    mock_file.assert_called()


def test_10_get(mocker, kstore):
    """Test10 KeyStore().get()."""
    url = 'https://xxx'
    email = 'user@domain'
    auth = 'xxx'
    credentials = {url: {'email': email, 'auth': auth}}
    mock_readall = mocker.patch.object(KeyStore, '_read_all', return_value=credentials)
    out = kstore.get(url)
    assert out == auth
    mock_readall.assert_called()


def test_11_get(mocker, kstore):
    """Test11 KeyStore().get()."""
    mock_readall = mocker.patch.object(KeyStore, '_read_all', return_value={})
    out = kstore.get('')
    assert out == ''
    mock_readall.assert_called()


def test_12_put(mocker, kstore):
    """Test12 KeyStore().put()."""
    mock_readall = mocker.patch.object(KeyStore, '_read_all')
    out = kstore.put("", "", "")
    assert out == 1
    mock_readall.assert_not_called()


def test_13_put(mocker, kstore):
    """Test13 KeyStore().put()."""
    url = u'https://xxx'
    email = u'user@domain'
    auth = u'xxx'
    credentials = {url: {u'email': email, u'auth': auth}}
    mock_readall = mocker.patch.object(KeyStore, '_read_all', return_value=credentials)
    mock_loginfo = mocker.patch('udocker.helper.keystore.LOG.info')
    mock_shred = mocker.patch.object(KeyStore, '_shred', return_value=0)
    mock_writeall = mocker.patch.object(KeyStore, '_write_all', return_value=0)
    out = kstore.put(url, auth, email)
    assert out == 0
    mock_readall.assert_called()
    mock_loginfo.assert_called()
    mock_shred.assert_called()
    mock_writeall.assert_called()


def test_14_delete(mocker, kstore):
    """Test14 KeyStore().delete()."""
    url = 'https://xxx'
    email = 'user@domain'
    auth = 'xxx'
    credentials = {url: {'email': email, 'auth': auth}}
    mock_verks = mocker.patch.object(KeyStore, '_verify_keystore')
    mock_readall = mocker.patch.object(KeyStore, '_read_all', return_value=credentials)
    mock_loginfo = mocker.patch('udocker.helper.keystore.LOG.info')
    mock_shred = mocker.patch.object(KeyStore, '_shred', return_value=0)
    mock_writeall = mocker.patch.object(KeyStore, '_write_all', return_value=0)
    out = kstore.delete(url)
    assert out == 0
    mock_verks.assert_called()
    mock_readall.assert_called()
    mock_loginfo.assert_called()
    mock_shred.assert_called()
    mock_writeall.assert_called()


def test_15_delete(mocker, kstore):
    """Test15 KeyStore().delete()."""
    mock_verks = mocker.patch.object(KeyStore, '_verify_keystore')
    mock_readall = mocker.patch.object(KeyStore, '_read_all', return_value={})
    mock_loginfo = mocker.patch('udocker.helper.keystore.LOG.info')
    mock_shred = mocker.patch.object(KeyStore, '_shred')
    mock_writeall = mocker.patch.object(KeyStore, '_write_all')
    out = kstore.delete('')
    assert out == 1
    mock_verks.assert_called()
    mock_readall.assert_called()
    mock_loginfo.assert_not_called()
    mock_shred.assert_not_called()
    mock_writeall.assert_not_called()


def test_16_erase(mocker, kstore):
    """Test16 KeyStore().erase()."""
    mock_verks = mocker.patch.object(KeyStore, '_verify_keystore')
    mock_loginfo = mocker.patch('udocker.helper.keystore.LOG.info')
    mock_shred = mocker.patch.object(KeyStore, '_shred', return_value=0)
    mock_unlink = mocker.patch('os.unlink')
    out = kstore.erase()
    assert out == 0
    mock_verks.assert_called()
    mock_loginfo.assert_called()
    mock_shred.assert_called()
    mock_unlink.assert_called()


def test_17_erase(mocker, kstore):
    """Test17 KeyStore().erase()."""
    mock_verks = mocker.patch.object(KeyStore, '_verify_keystore')
    mock_loginfo = mocker.patch('udocker.helper.keystore.LOG.info')
    mock_shred = mocker.patch.object(KeyStore, '_shred', return_value=0)
    mock_unlink = mocker.patch('os.unlink', side_effect=OSError)
    out = kstore.erase()
    assert out == 1
    mock_verks.assert_called()
    mock_loginfo.assert_not_called()
    mock_shred.assert_called()
    mock_unlink.assert_called()
