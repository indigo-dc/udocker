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



# @patch('udocker.utils.filebind.FileUtil.copyto')
# @patch('udocker.utils.filebind.os.symlink')
# @patch('udocker.utils.filebind.os.rename')
# @patch('udocker.utils.filebind.os.path.exists')
# @patch('udocker.utils.filebind.os.path.isfile')
# @patch('udocker.utils.filebind.os.path.realpath')
# def test_06_set_file(self, mock_realpath, mock_isfile,
#                         mock_exists, mock_rename, mock_sym,
#                         mock_futilcopy):
#     """Test06 FileBind().set_file()."""
#     hfile = 'host_file'
#     cfile = 'cont_file'
#     container_id = "CONTAINERID"
#     mock_realpath.return_value = "/tmp"
#     mock_isfile.return_value = False
#     mock_exists.return_value = False
#     fbind = FileBind(self.local, container_id)
#     fbind.set_file(hfile, cfile)
#     self.assertFalse(mock_futilcopy.called)

#     mock_realpath.return_value = "/tmp"
#     mock_isfile.return_value = True
#     mock_exists.return_value = False
#     fbind = FileBind(self.local, container_id)
#     fbind.set_file(hfile, cfile)
#     self.assertTrue(mock_rename.called)
#     self.assertTrue(mock_sym.called)

#     mock_realpath.return_value = "/tmp"
#     mock_isfile.return_value = True
#     mock_exists.return_value = True
#     fbind = FileBind(self.local, container_id)
#     fbind.set_file(hfile, cfile)
#     self.assertTrue(mock_futilcopy.called)

# @patch('udocker.utils.filebind.FileUtil.remove')
# @patch('udocker.utils.filebind.FileUtil.copyto')
# @patch('udocker.utils.filebind.os.path.realpath')
# def test_07_add_file(self, mock_realpath, mock_futilcp,
#                         mock_futilrm):
#     """Test07 FileBind().add_file()."""
#     container_id = "CONTAINERID"
#     mock_realpath.return_value = "/tmp"
#     host_file = "host.file"
#     container_file = "#container.file"
#     fbind = FileBind(self.local, container_id)
#     fbind.host_bind_dir = "/tmp"
#     fbind.add_file(host_file, container_file)
#     self.assertTrue(mock_futilrm.called)
#     self.assertTrue(mock_futilcp.called)

# @patch('udocker.utils.filebind.os.path.realpath')
# def test_08_get_path(self, mock_realpath):
#     """Test08 FileBind().get_path()."""
#     container_id = 'CONTAINERID'
#     cont_file = '/dir1/file'
#     mock_realpath.return_value = "/tmp"
#     fbind = FileBind(self.local, container_id)
#     fbind.host_bind_dir = '/dir0'
#     status = fbind.get_path(cont_file)
#     self.assertEqual(status, '/dir0/#dir1#file')

# # def test_09_finish(self):
# #     """Test09 FileBind().finish()."""
