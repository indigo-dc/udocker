#!/usr/bin/env python
"""
udocker unit tests: MountPoint
"""
import pytest
from udocker.utils.mountpoint import MountPoint


@pytest.fixture
def lrepo(mocker):
    mock_lrepo = mocker.patch('udocker.container.localrepo.LocalRepository')
    return mock_lrepo


@pytest.fixture
def mpoint(mocker, lrepo):
    return MountPoint(lrepo, 'contID123')


data_setup = ((True, False, True, 0),
              (False, True, True, 1),
              (False, False, False, 1)
              )


@pytest.mark.parametrize('isdir,ismkdir,expected,mkdircall', data_setup)
def test_01_setup(mpoint, mocker, isdir, ismkdir, mkdircall, expected):
    """Test01 MountPoint().setup()."""
    mock_isdir = mocker.patch('os.path.isdir', return_value=isdir)
    mock_mkdir = mocker.patch('udocker.utils.mountpoint.FileUtil.mkdir', return_value=ismkdir)
    resout = mpoint.setup()
    assert resout == expected
    mock_isdir.assert_called()
    assert mock_mkdir.call_count == mkdircall


data_add = (('/.udocker/contID123/ROOT/mycpath', 'mycpath', '/.udocker/contID123/ROOT/mycpath'),)


@pytest.mark.parametrize('vpath,cpath,expected', data_add)
def test_02_add(mpoint, mocker, vpath, cpath, expected):
    """Test02 MountPoint().add()."""
    mock_validpath = mocker.patch('udocker.utils.mountpoint.FileUtil.getvalid_path',
                                  return_value=vpath)
    mpointattr = mpoint.mountpoints
    mpoint.add(cpath)
    assert mpointattr == {cpath: expected}
    mock_validpath.assert_called()


def test_03_delete(mpoint, mocker):
    """Test03 MountPoint().delete()."""
    mock_rpath = mocker.patch('os.path.realpath', return_value='/tmp')
    mock_npath = mocker.patch('os.path.normpath',
                              side_effect=['/controot/cont_path', '/controot/cont_path'])
    mock_dirname = mocker.patch('os.path.dirname', return_value='/ROOT/tmp')
    mock_furm = mocker.patch('udocker.utils.mountpoint.FileUtil.remove', return_value=True)
    mpoint.mountpoints = {'cont_path': '/cont/bin'}
    resout = mpoint.delete('cont_path')
    assert resout
    assert mpoint.mountpoints == {}
    mock_rpath.assert_called()
    assert mock_npath.call_count == 2


def test_04_delete(mpoint, mocker):
    """Test04 MountPoint().delete()."""
    mpoint.mountpoints = {'some_path': '/cont/bin'}
    resout = mpoint.delete('cont_path')
    assert not resout


def test_05_delete_all(mpoint, mocker):
    """Test05 MountPoint().delete_all()."""
    mock_rpath = mocker.patch('os.path.realpath', return_value='/tmp')
    mock_npath = mocker.patch('os.path.normpath',
                              side_effect=['/controot/cont_path', '/controot/cont_path'])
    mpoint.mountpoints = {'cont_path': '/cont/bin'}
    mpoint.delete_all()
    assert mpoint.mountpoints == {}
    mock_rpath.assert_called()
    assert mock_npath.call_count == 2


# data_create1 = (([32768, 32768], True),
#                 ([0, 32768], False),
#                 )


# @pytest.mark.parametrize('ret_isf,expected', data_create1)
# def test_06_create(mpoint, mocker, ret_isf, expected):
#     """Test06 MountPoint().create()."""
#     mock_exists = mocker.patch('os.path.exists', return_value=True)
#     mock_add = mocker.patch.object(MountPoint, 'add', return_value=None)
#     mock_stmode = mocker.patch('os.stat.st_mode', side_effect=ret_isf)
#     mock_ifmt = mocker.patch('stat.S_IFMT', side_effect=ret_isf)
    
#     resout = mpoint.create('/bin', '/ROOT/bin')
#     assert resout == expected
#     mock_exists.assert_called()
#     mock_add.assert_not_called()
#     assert mock_stmode.call_count == 2


def test_07_create(mpoint, mocker):
    """Test07 MountPoint().create()."""
    mock_exists = mocker.patch('os.path.exists', return_value=False)
    mock_add = mocker.patch.object(MountPoint, 'add', return_value=None)
    mock_isfile = mocker.patch('os.path.isfile', side_effect=[True, True])
    mock_mkdir = mocker.patch('udocker.utils.mountpoint.FileUtil.mkdir', return_value=None)
    mock_putdata = mocker.patch('udocker.utils.mountpoint.FileUtil.putdata', return_value=None)
    mock_islink = mocker.patch('os.path.islink', return_value=True)
    mock_isdir = mocker.patch('os.path.isdir', return_value=False)
    mock_del = mocker.patch.object(MountPoint, 'delete', return_value=True)
    resout = mpoint.create('/bin', '/ROOT/bin')
    assert resout
    mock_exists.assert_called()
    mock_add.assert_called()
    assert mock_isfile.call_count == 2
    mock_mkdir.assert_called()
    mock_putdata.assert_called()
    mock_islink.assert_called()
    mock_isdir.assert_called()
    mock_del.assert_not_called()


def test_08_create(mpoint, mocker):
    """Test08 MountPoint().create()."""
    mock_exists = mocker.patch('os.path.exists', return_value=False)
    mock_add = mocker.patch.object(MountPoint, 'add', return_value=None)
    mock_isfile = mocker.patch('os.path.isfile', side_effect=[True, False])
    mock_mkdir = mocker.patch('udocker.utils.mountpoint.FileUtil.mkdir', return_value=None)
    mock_putdata = mocker.patch('udocker.utils.mountpoint.FileUtil.putdata', return_value=None)
    mock_islink = mocker.patch('os.path.islink', return_value=False)
    mock_isdir = mocker.patch('os.path.isdir', return_value=False)
    mock_del = mocker.patch.object(MountPoint, 'delete', return_value=True)
    resout = mpoint.create('/bin', '/ROOT/bin')
    assert not resout
    mock_exists.assert_called()
    mock_add.assert_called()
    assert mock_isfile.call_count == 2
    mock_mkdir.assert_called()
    mock_putdata.assert_called()
    mock_islink.assert_called()
    mock_isdir.assert_not_called()
    mock_del.assert_called()


def test_09_create(mpoint, mocker):
    """Test09 MountPoint().create()."""
    mock_exists = mocker.patch('os.path.exists', return_value=False)
    mock_add = mocker.patch.object(MountPoint, 'add', return_value=None)
    mock_isfile = mocker.patch('os.path.isfile', return_value=False)
    mock_mkdir = mocker.patch('udocker.utils.mountpoint.FileUtil.mkdir', return_value=True)
    mock_putdata = mocker.patch('udocker.utils.mountpoint.FileUtil.putdata', return_value=None)
    mock_islink = mocker.patch('os.path.islink', return_value=None)
    mock_isdir = mocker.patch('os.path.isdir', return_value=True)
    mock_del = mocker.patch.object(MountPoint, 'delete', return_value=True)
    resout = mpoint.create('/bin', '/ROOT/bin')
    assert resout
    mock_exists.assert_called()
    mock_add.assert_called()
    mock_isfile.assert_called()
    mock_mkdir.assert_called()
    mock_putdata.assert_not_called()
    mock_islink.assert_called()
    mock_isdir.assert_called()
    mock_del.assert_not_called()



# @patch('udocker.utils.mountpoint.os.path.realpath')
# @patch('udocker.utils.mountpoint.os.symlink')
# @patch('udocker.utils.mountpoint.os.path.exists')
# def test_07_save(self, mock_exists, mock_syml, mock_realpath):
#     """Test07 MountPoint().save()."""
#     container_id = "CONTAINERID"
#     cpath = 'cont_path'
#     mock_realpath.return_value = "/tmp"
#     mpoint = MountPoint(self.local, container_id)
#     mpoint.mountpoints = {'some_path': '/cont/bin'}
#     status = mpoint.save(cpath)
#     self.assertTrue(status)

#     mock_exists.return_value = False
#     mock_syml.return_value = None
#     mock_realpath.return_value = "/tmp"
#     mpoint = MountPoint(self.local, container_id)
#     mpoint.mountpoints = {'cont_path': '/cont/bin'}
#     status = mpoint.save(cpath)
#     self.assertTrue(status)
#     self.assertTrue(mock_exists.called)
#     self.assertTrue(mock_syml.called)

#     mock_realpath.return_value = "/tmp"
#     mock_exists.side_effect = IOError("fail")
#     mpoint = MountPoint(self.local, container_id)
#     mpoint.mountpoints = {'cont_path': '/cont/bin'}
#     status = mpoint.save(cpath)
#     self.assertFalse(status)

# @patch.object(MountPoint, 'save')
# @patch.object(MountPoint, 'setup')
# @patch('udocker.utils.mountpoint.os.path.realpath')
# def test_08_save_all(self, mock_realpath, mock_setup, mock_save):
#     """Test08 MountPoint().save_all()."""
#     container_id = "CONTAINERID"
#     mock_realpath.return_value = "/tmp"
#     mock_setup.return_value = True
#     mock_save.return_value = None
#     mpoint = MountPoint(self.local, container_id)
#     mpoint.mountpoints = {'cont_path': '/cont/bin'}
#     mpoint.save_all()
#     self.assertTrue(mock_save.called)

# @patch('udocker.utils.mountpoint.os.readlink')
# @patch('udocker.utils.mountpoint.os.listdir')
# @patch.object(MountPoint, 'setup')
# @patch('udocker.utils.mountpoint.os.path.realpath')
# def test_09_load_all(self, mock_realpath, mock_setup, mock_ldir, mock_readl):
#     """Test09 MountPoint().load_all()."""
#     container_id = "CONTAINERID"
#     result = {'/dir1': '/dir1', '/dir2': '/dir2'}
#     mock_realpath.return_value = "/tmp"
#     mock_setup.return_value = True
#     mock_ldir.return_value = ['/dir1', '/dir2']
#     mock_readl.side_effect = ['/dir1', '/dir2']
#     mpoint = MountPoint(self.local, container_id)
#     mpoint.load_all()
#     self.assertEqual(mpoint.mountpoints, result)

# @patch('udocker.utils.mountpoint.FileUtil.remove')
# @patch.object(MountPoint, 'delete_all')
# @patch.object(MountPoint, 'load_all')
# @patch.object(MountPoint, 'save_all')
# @patch.object(MountPoint, 'setup')
# @patch('udocker.utils.mountpoint.os.path.realpath')
# def test_10_restore(self, mock_realpath, mock_setup, mock_save, mock_load, mock_del, mock_rm):
#     """Test10 MountPoint().restore()."""
#     container_id = "CONTAINERID"
#     mock_realpath.return_value = "/tmp"
#     mock_setup.return_value = True
#     mock_save.return_value = None
#     mock_load.return_value = None
#     mock_del.return_value = None
#     mock_rm.return_value = None
#     mpoint = MountPoint(self.local, container_id)
#     mpoint.restore()
#     self.assertTrue(mock_save.called)
#     self.assertTrue(mock_load.called)
#     self.assertTrue(mock_del.called)
#     self.assertTrue(mock_rm.called)
