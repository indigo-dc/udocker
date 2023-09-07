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
    mock_realpath = mocker.patch('udocker.utils.mountpoint.os.path.realpath',
                                 return_value='/home/.udocker/containers/123')
    return MountPoint(lrepo, '123')


data_setup = ((True, False, True, 0),
              (False, True, True, 1),
              (False, False, False, 1)
              )


@pytest.mark.parametrize('isdir,ismkdir,expected,mkdircall', data_setup)
def test_01_setup(mpoint, mocker, isdir, ismkdir, mkdircall, expected):
    """Test01 MountPoint().setup()."""
    mock_isdir = mocker.patch('udocker.utils.mountpoint.os.path.isdir', return_value=isdir)
    mock_mkdir = mocker.patch('udocker.utils.mountpoint.FileUtil.mkdir', return_value=ismkdir)
    resout = mpoint.setup()
    assert resout == expected
    mock_isdir.assert_called()
    assert mock_mkdir.call_count == mkdircall


data_add = (('/.udocker/123/ROOT/mycpath', 'mycpath', '/.udocker/123/ROOT/mycpath'),)


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
    mock_rpath = mocker.patch('udocker.utils.mountpoint.os.path.realpath', return_value='/tmp')
    mock_npath = mocker.patch('udocker.utils.mountpoint.os.path.normpath',
                              side_effect=['/controot/cont_path', '/controot/cont_path'])
    mock_dirname = mocker.patch('udocker.utils.mountpoint.os.path.dirname',
                                return_value='/ROOT/tmp')
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
    mock_rpath = mocker.patch('udocker.utils.mountpoint.os.path.realpath', return_value='/tmp')
    mock_npath = mocker.patch('udocker.utils.mountpoint.os.path.normpath',
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
    mock_exists = mocker.patch('udocker.utils.mountpoint.os.path.exists', return_value=False)
    mock_add = mocker.patch.object(MountPoint, 'add', return_value=None)
    mock_isfile = mocker.patch('udocker.utils.mountpoint.os.path.isfile', side_effect=[True, True])
    mock_mkdir = mocker.patch('udocker.utils.mountpoint.FileUtil.mkdir', return_value=None)
    mock_putdata = mocker.patch('udocker.utils.mountpoint.FileUtil.putdata', return_value=None)
    mock_islink = mocker.patch('udocker.utils.mountpoint.os.path.islink', return_value=True)
    mock_isdir = mocker.patch('udocker.utils.mountpoint.os.path.isdir', return_value=False)
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
    mock_exists = mocker.patch('udocker.utils.mountpoint.os.path.exists', return_value=False)
    mock_add = mocker.patch.object(MountPoint, 'add', return_value=None)
    mock_isfile = mocker.patch('udocker.utils.mountpoint.os.path.isfile', side_effect=[True, False])
    mock_mkdir = mocker.patch('udocker.utils.mountpoint.FileUtil.mkdir', return_value=None)
    mock_putdata = mocker.patch('udocker.utils.mountpoint.FileUtil.putdata', return_value=None)
    mock_islink = mocker.patch('udocker.utils.mountpoint.os.path.islink', return_value=False)
    mock_isdir = mocker.patch('udocker.utils.mountpoint.os.path.isdir', return_value=False)
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
    mock_exists = mocker.patch('udocker.utils.mountpoint.os.path.exists', return_value=False)
    mock_add = mocker.patch.object(MountPoint, 'add', return_value=None)
    mock_isfile = mocker.patch('udocker.utils.mountpoint.os.path.isfile', return_value=False)
    mock_mkdir = mocker.patch('udocker.utils.mountpoint.FileUtil.mkdir', return_value=True)
    mock_putdata = mocker.patch('udocker.utils.mountpoint.FileUtil.putdata', return_value=None)
    mock_islink = mocker.patch('udocker.utils.mountpoint.os.path.islink', return_value=None)
    mock_isdir = mocker.patch('udocker.utils.mountpoint.os.path.isdir', return_value=True)
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


def test_10_save(mpoint):
    """Test10 MountPoint().save()."""
    mpoint.mountpoints = {'some_path': '/cont/bin'}
    resout = mpoint.save('cont_path')
    assert resout


def test_11_save(mpoint, mocker):
    """Test11 MountPoint().save()."""
    mock_exists = mocker.patch('udocker.utils.mountpoint.os.path.exists', return_value=False)
    mock_symlink = mocker.patch('udocker.utils.mountpoint.os.symlink', return_value=None)
    mpoint.mountpoints = {'cont_path': '/cont/bin'}
    resout = mpoint.save('cont_path')
    assert resout
    mock_exists.assert_called()
    mock_symlink.assert_called()


def test_12_save(mpoint, mocker):
    """Test12 MountPoint().save()."""
    mock_exists = mocker.patch('udocker.utils.mountpoint.os.path.exists',
                               side_effect=OSError("fail"))
    mock_symlink = mocker.patch('udocker.utils.mountpoint.os.symlink', return_value=None)
    mpoint.mountpoints = {'cont_path': '/cont/bin'}
    resout = mpoint.save('cont_path')
    assert not resout
    mock_exists.assert_called()
    mock_symlink.assert_not_called()


def test_13_save_all(mpoint, mocker):
    """Test13 MountPoint().save_all()."""
    mock_save = mocker.patch.object(MountPoint, 'save', return_value=True)
    mpoint.mountpoints = {'some_path': '/cont/bin'}
    mpoint.save_all()
    mock_save.assert_called()


def test_14_load_all(mpoint, mocker):
    """Test14 MountPoint().load_all()."""
    result = {'/dir1': '/dir1', '/dir2': '/dir2'}
    mock_ldir = mocker.patch('udocker.utils.mountpoint.os.listdir', return_value=['/dir1', '/dir2'])
    mock_readl = mocker.patch('udocker.utils.mountpoint.os.readlink',
                              side_effect=['/dir1', '/dir2'])
    mpoint.load_all()
    assert mpoint.mountpoints == result
    mock_ldir.assert_called()
    assert mock_readl.call_count == 2


def test_15_restore(mpoint, mocker):
    """Test15 MountPoint().restore()."""
    mock_save = mocker.patch.object(MountPoint, 'save_all', return_value=None)
    mock_load = mocker.patch.object(MountPoint, 'load_all', return_value=None)
    mock_del = mocker.patch.object(MountPoint, 'delete_all', return_value=None)
    mock_rm = mocker.patch('udocker.utils.mountpoint.FileUtil.remove', return_value=None)
    mpoint.restore()
    mock_save.assert_called()
    mock_load.assert_called()
    mock_del.assert_called()
    mock_rm.assert_called()
