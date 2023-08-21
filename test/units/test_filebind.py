#!/usr/bin/env python
"""
udocker unit tests: FileBind
"""
import pytest
from udocker.utils.filebind import FileBind


@pytest.fixture
def lrepo(mocker):
    mock_lrepo = mocker.patch('udocker.container.localrepo.LocalRepository')
    return mock_lrepo


@pytest.fixture
def fbind(mocker, lrepo):
    mock_realpath = mocker.patch('os.path.realpath', return_value='/home/.udocker/containers/123')
    return FileBind(lrepo, '123')


def test_01_setup(fbind, mocker):
    """Test01 FileBind().setup()."""
    mock_isdir = mocker.patch('os.path.isdir', side_effect=[True, True])
    resout = fbind.setup()
    assert resout
    assert mock_isdir.call_count == 2


def test_02_setup(fbind, mocker):
    """Test02 FileBind().setup()."""
    mock_isdir = mocker.patch('os.path.isdir', side_effect=[False, True])
    mock_futil = mocker.patch('udocker.utils.filebind.FileUtil')
    mock_futil.return_value.mkdir.return_value = False
    resout = fbind.setup()
    assert not resout
    mock_isdir.assert_called()
    mock_futil.assert_called()


def test_03_setup(fbind, mocker):
    """Test03 FileBind().setup()."""
    mock_isdir = mocker.patch('os.path.isdir', side_effect=[True, False])
    mock_futil = mocker.patch('udocker.utils.filebind.FileUtil')
    mock_futil.return_value.mkdir.side_effect = [False, False]
    resout = fbind.setup()
    assert not resout
    mock_isdir.assert_called()
    mock_futil.assert_called()


def test_04_restore(fbind, mocker):
    """Test04 FileBind().restore()."""
    mock_isdir = mocker.patch('os.path.isdir', return_value=False)
    fbind.restore()
    mock_isdir.assert_called()


def test_05_restore(fbind, mocker):
    """Test05 FileBind().restore()."""
    mock_isdir = mocker.patch('os.path.isdir', return_value=True)
    mock_listdir = mocker.patch('os.listdir', return_value=["is_file1", "is_dir", "is_file2"])
    mock_isfile = mocker.patch('os.path.isfile', side_effect=[True, False, True])
    mock_islink = mocker.patch('os.path.islink', side_effect=[True, False, False])
    mock_futil = mocker.patch('udocker.utils.filebind.FileUtil')
    mock_futil.return_value.register_prefix.side_effect = [None, None, None]
    mock_futil.return_value.remove.side_effect = [None, None, None, None, None]
    mock_futil.return_value.rename.side_effect = [True, False, False]
    fbind.restore()
    mock_isdir.assert_called()
    mock_listdir.assert_called()
    mock_islink.assert_called()
    mock_isfile.assert_called()
    mock_futil.return_value.register_prefix.assert_called()
    assert mock_futil.return_value.rename.call_count == 2


def test_06_start(fbind, mocker):
    """Test06 FileBind().start()."""
    mock_setup = mocker.patch.object(FileBind, 'setup', return_value=None)
    mock_setl = mocker.patch.object(FileBind, 'set_list', return_value=None)
    files_list = ["file1", "dir1", "file2"]
    mock_futil = mocker.patch('udocker.utils.filebind.FileUtil')
    mock_futil.return_value.mktmpdir.return_value = 'tmpDir'
    resout = fbind.start(files_list)
    assert resout == ('tmpDir', '/.bind_host_files')
    mock_setup.assert_called()
    mock_setl.assert_called()
    mock_futil.return_value.mktmpdir.assert_called()


def test_07_set_list(fbind, mocker):
    """Test07 FileBind().set_list()."""
    flist = ['f1', 'f2']
    mock_setfile = mocker.patch.object(FileBind, 'set_file', side_effect=[None, None])
    fbind.set_list(flist)
    assert mock_setfile.call_count == 2


def test_08_set_file(fbind, mocker):
    """Test08 FileBind().set_file()."""
    mock_isfile = mocker.patch('os.path.isfile', return_value=False)
    resout = fbind.set_file('host_file', 'cont_file')
    assert resout is None
    mock_isfile.assert_called()


def test_09_set_file(fbind, mocker):
    """Test09 FileBind().set_file()."""
    mock_isfile = mocker.patch('os.path.isfile', side_effect=[True, False])
    mock_exists = mocker.patch('os.path.exists', return_value=False)
    mock_rename = mocker.patch('os.rename')
    resout = fbind.set_file('host_file', 'cont_file')
    assert resout is None
    mock_isfile.assert_called()
    mock_exists.assert_called()
    mock_rename.assert_not_called()


def test_10_set_file(fbind, mocker):
    """Test10 FileBind().set_file()."""
    mock_isfile = mocker.patch('os.path.isfile', side_effect=[True, True])
    mock_exists = mocker.patch('os.path.exists', return_value=False)
    mock_rename = mocker.patch('os.rename')
    mock_sym = mocker.patch('os.symlink')
    mock_futilcopy = mocker.patch('udocker.utils.filebind.FileUtil.copyto')
    fbind.set_file('host_file', 'cont_file')
    mock_isfile.assert_called()
    mock_exists.assert_called()
    mock_rename.assert_called()
    mock_sym.assert_called()
    mock_futilcopy.assert_called()


def test_11_add_file(fbind, mocker):
    """Test11 FileBind().add_file()."""
    host_file = "host.file"
    container_file = "#container.file"
    mock_futilcp = mocker.patch('udocker.utils.filebind.FileUtil.copyto')
    mock_futilrm = mocker.patch('udocker.utils.filebind.FileUtil.remove')
    fbind.host_bind_dir = "/tmp"
    fbind.add_file(host_file, container_file)
    mock_futilcp.assert_called()
    mock_futilrm.assert_called()


def test_12_get_path(fbind):
    """Test12 FileBind().get_path()."""
    cont_file = '/dir1/file'
    fbind.host_bind_dir = '/dir0'
    resout = fbind.get_path(cont_file)
    assert resout == '/dir0/#dir1#file'


def test_13_finish(fbind):
    """Test13 FileBind().finish()."""
    assert fbind.finish() is None
