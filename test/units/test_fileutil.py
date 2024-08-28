#!/usr/bin/env python
"""
udocker unit tests: FileUtil
"""
import os
import sys
from io import BytesIO

import pytest
from udocker.utils.fileutil import FileUtil

STDOUT = sys.stdout
STDERR = sys.stderr
UDOCKER_TOPDIR = "test_topdir"
BUILTINS = "builtins"


def find_str(self, find_exp, where):
    """Find string in test output messages."""
    found = False
    for item in where:
        if find_exp in str(item):
            self.assertTrue(True)
            found = True
            break
    if not found:
        self.assertTrue(False)


def is_writable_file(obj):
    """Check if obj is a file."""
    try:
        obj.write("")
    except (AttributeError, OSError, IOError):
        return False
    else:
        return True


@pytest.fixture
def futil():
    file_util = FileUtil('somefile')
    file_util.filename = '/dir/somefile'
    file_util.basename = 'somefile'
    file_util._register_prefix('/dir')
    return file_util


@pytest.fixture
def logger(mocker):
    return mocker.patch('udocker.utils.fileutil.LOG')


def test_01_init(mocker):
    """Test01 FileUtil() constructor."""
    mock_absp = mocker.patch('udocker.utils.fileutil.os.path.abspath', return_value='/dir/somefile')
    mock_base = mocker.patch('udocker.utils.fileutil.os.path.basename', return_value='somefile')
    mock_regpre = mocker.patch.object(FileUtil, '_register_prefix')
    fileutil = FileUtil('somefile')
    assert fileutil.filename == '/dir/somefile'
    mock_absp.assert_called()
    mock_base.assert_called()
    mock_regpre.assert_called()


def test_02_init(mocker):
    """Test02 FileUtil() constructor."""
    mock_absp = mocker.patch('udocker.utils.fileutil.os.path.abspath')
    mock_base = mocker.patch('udocker.utils.fileutil.os.path.basename')
    mock_regpre = mocker.patch.object(FileUtil, '_register_prefix')
    fileutil = FileUtil('-')
    assert fileutil.filename == '-'
    mock_absp.assert_not_called()
    mock_base.assert_not_called()
    mock_regpre.assert_not_called()


# data_regp = (('/dir1', '/dir1', ['/dir1', '/dir1', '/dir1', '/dir1'], True, False,
#               ['/tmp/', '/tmp/', '/tmp/', '/tmp/', '/some_contdir', '/some_contdir',
#                '/home/.udocker/containers/123', '/home/.udocker/containers/123', '/dir1/',
#                '/dir1/', '/dir1/', '/dir1/']),
#              ('file1', '/dir1/file1', ['/dir1/file1', '/dir1/file1', '/dir1/file1', '/dir1/file1'],
#               False, False,
#               ['/tmp/', '/tmp/', '/tmp/', '/tmp/', '/some_contdir', '/some_contdir',
#                '/home/.udocker/containers/123', '/home/.udocker/containers/123', '/dir1/',
#                '/dir1/', '/dir1/', '/dir1/', '/dir1/file1', '/dir1/file1']))


# @pytest.mark.parametrize("ftype,abspath,rpathsd,risdir,rislink,expected", data_regp)
# def test_03_register_prefix(mocker, ftype, abspath, rpathsd, risdir, rislink, expected):
#     """Test03 FileUtil.register_prefix()."""
#     mock_absp = mocker.patch('udocker.utils.fileutil.os.path.abspath', return_value=abspath)
#     mock_base = mocker.patch('udocker.utils.fileutil.os.path.basename', return_value=ftype)
#     mock_rpath = mocker.patch('udocker.utils.fileutil.os.path.realpath', side_effect=rpathsd)
#     mock_isdir = mocker.patch('udocker.utils.fileutil.os.path.isdir', return_value=risdir)
#     mock_islink = mocker.patch('udocker.utils.fileutil.os.path.islink', return_value=rislink)
#     fileutil = FileUtil(ftype)
#     fileutil.register_prefix()
#     assert fileutil.safe_prefixes == expected
#     mock_absp.assert_called()
#     mock_base.assert_called()
#     mock_rpath.assert_called()
#     mock_isdir.assert_called()
#     mock_islink.assert_called()


def test_04_umask(futil, mocker):
    """Test04 FileUtil.umask()."""
    mock_umask = mocker.patch('udocker.utils.fileutil.os.umask', return_value=0)
    resout = futil.umask()
    assert resout
    mock_umask.assert_called()


def test_05_umask(futil, mocker):
    """Test05 FileUtil.umask()."""
    mock_umask = mocker.patch('udocker.utils.fileutil.os.umask', return_value=1)
    resout = futil.umask(1)
    assert resout
    assert futil.orig_umask == 1
    mock_umask.assert_called()


def test_06_umask(futil, mocker):
    """Test06 FileUtil.umask()."""
    mock_umask = mocker.patch('udocker.utils.fileutil.os.umask', side_effect=TypeError('fail'))
    resout = futil.umask()
    assert not resout
    mock_umask.assert_called()


def test_07_umask(futil, mocker):
    """Test07 FileUtil.umask()."""
    mock_umask = mocker.patch('udocker.utils.fileutil.os.umask', side_effect=TypeError('fail'))
    resout = futil.umask(1)
    assert not resout
    mock_umask.assert_called()


def test_08_mktmp(futil, mocker):
    """Test08 FileUtil.mktmp()."""
    mock_uniqf = mocker.patch('udocker.utils.fileutil.Unique.filename', return_value='fname213')
    mock_exists = mocker.patch('udocker.utils.fileutil.os.path.exists', return_value=False)
    resout = futil.mktmp()
    assert resout == '/tmp/fname213'
    assert futil.tmptrash['/tmp/fname213']
    mock_uniqf.assert_called()
    mock_exists.assert_called()


def test_09_mkdir(futil, mocker):
    """Test09 FileUtil.mkdir()"""
    mock_mkdirs = mocker.patch('udocker.utils.fileutil.os.makedirs')
    resout = futil.mkdir()
    assert resout
    mock_mkdirs.assert_called()


def test_10_mkdir(futil, mocker):
    """Test10 FileUtil.mkdir()"""
    mock_mkdirs = mocker.patch('udocker.utils.fileutil.os.makedirs', side_effect=OSError('fail'))
    resout = futil.mkdir()
    assert not resout
    mock_mkdirs.assert_called()


def test_11_rmdir(futil, mocker):
    """Test11 FileUtil.rmdir()"""
    mock_rmdir = mocker.patch('udocker.utils.fileutil.os.rmdir')
    resout = futil.rmdir()
    assert resout
    mock_rmdir.assert_called()


def test_12_rmdir(futil, mocker):
    """Test12 FileUtil.rmdir()"""
    mock_rmdir = mocker.patch('udocker.utils.fileutil.os.rmdir', side_effect=OSError('fail'))
    resout = futil.rmdir()
    assert not resout
    mock_rmdir.assert_called()


data_mk = ((True, 'somedir'),
           (False, None))


@pytest.mark.parametrize("rmkdir,expected", data_mk)
def test_13_mktmpdir(futil, mocker, rmkdir, expected):
    """Test13 FileUtil.mktmpdir()."""
    mock_mkdir = mocker.patch.object(FileUtil, 'mkdir', return_value=rmkdir)
    mock_mktmp = mocker.patch.object(FileUtil, 'mktmp', return_value='somedir')
    resout = futil.mktmpdir()
    assert resout == expected
    mock_mkdir.assert_called()
    mock_mktmp.assert_called()


def test_14_uid(futil, mocker):
    """Test14 FileUtil.uid()."""
    mock_lstat = mocker.patch('udocker.utils.fileutil.os.lstat')
    mock_lstat.return_value.st_uid = 1234
    resout = futil.uid()
    assert resout == 1234
    mock_lstat.assert_called()


def test_15_uid(futil, mocker):
    """Test15 FileUtil.uid()."""
    mock_lstat = mocker.patch('udocker.utils.fileutil.os.lstat', side_effect=OSError('fail'))
    resout = futil.uid()
    assert resout == -1


data_spref = (('/bin', ['/bin'], ['/bin', '/bin'], True, False, True),
              ('ls', ['/bin/ls'], ['/bin/ls', '/bin/ls'], False, False, True),
              ('link', ['/bin/link'], ['/bin/link', '/bin/link'], False, True, True))


@pytest.mark.parametrize("fname,safep,rpathsd,risdir,rislink,expected", data_spref)
def test_16__is_safe_prefix(futil, mocker, fname, safep, rpathsd, risdir, rislink, expected):
    """Test16 FileUtil._is_safe_prefix()."""
    mock_base = mocker.patch('udocker.utils.fileutil.os.path.basename', return_value=fname)
    mock_rpath = mocker.patch('udocker.utils.fileutil.os.path.realpath', side_effect=rpathsd)
    mock_isdir = mocker.patch('udocker.utils.fileutil.os.path.isdir', return_value=risdir)
    mock_islink = mocker.patch('udocker.utils.fileutil.os.path.islink', return_value=rislink)
    futil.safe_prefixes = safep
    resout = futil._is_safe_prefix(fname)
    assert resout == expected
    mock_rpath.assert_called()
    mock_isdir.assert_called()
    mock_islink.assert_called()


def test_17_chown(futil, mocker):
    """Test17 FileUtil.chown()."""
    mock_lchown = mocker.patch('udocker.utils.fileutil.os.lchown')
    resout = futil.chown(0, 0, False)
    assert resout
    mock_lchown.assert_called()


def test_18_chown(futil, mocker):
    """Test18 FileUtil.chown()."""
    mock_lchown = mocker.patch('udocker.utils.fileutil.os.lchown',
                               side_effect=[None, None, None, None])
    mock_walk = mocker.patch('udocker.utils.fileutil.os.walk',
                             return_value=[("/tmp", ["dir"], ["file"]), ])
    resout = futil.chown(0, 0, True)
    assert resout
    mock_lchown.assert_called()
    mock_walk.assert_called()


def test_19_chown(futil, mocker):
    """Test19 FileUtil.chown()."""
    mock_lchown = mocker.patch('os.lchown', side_effect=OSError("fail"))
    resout = futil.chown(0, 0, False)
    assert not resout
    mock_lchown.assert_called()


def test_20_rchown(futil, mocker):
    """Test20 FileUtil.rchown()."""
    mock_fuchown = mocker.patch.object(FileUtil, 'chown', return_value=True)
    assert futil.rchown()
    mock_fuchown.assert_called()


def test_21__chmod(futil, mocker):
    """Test21 FileUtil._chmod()."""
    mock_lstat = mocker.patch('udocker.utils.fileutil.os.lstat')
    mock_stat = mocker.patch('udocker.utils.fileutil.stat')
    mock_chmod = mocker.patch('udocker.utils.fileutil.os.chmod')
    mock_lstat.return_value.st_mode = 33277
    mock_stat.return_value.S_ISREG = True
    mock_stat.return_value.S_ISDIR = False
    mock_stat.return_value.S_ISLNK = False
    mock_stat.return_value.S_IMODE = 509
    futil._chmod("somefile")
    mock_lstat.assert_called()
    mock_stat.S_ISREG.assert_called()
    mock_stat.S_IMODE.assert_called()


def test_22__chmod(futil, mocker, logger):
    """Test22 FileUtil._chmod()."""
    mock_lstat = mocker.patch('udocker.utils.fileutil.os.lstat', side_effect=OSError('fail'))
    futil._chmod("somefile")
    mock_lstat.assert_called()
    logger.error.assert_called_with('changing permissions of: %s', 'somefile')


@pytest.mark.parametrize("st_mode, is_reg, is_dir, is_lnk, filemode, dirmode, mask, expected_chmod_mode", [
    (33277, True, False, False, 0o600, 0o700, 0o755, 0o755),
    (16877, False, True, False, 0o600, 0o700, 0o755, 0o755),
    (41453, False, False, True, 0o600, 0o700, 0o755, None),
    (33277, False, False, False, 0o600, None, 0o755, 0o755),
])
def test_23__chmod(futil, mocker, st_mode, is_reg, is_dir, is_lnk, filemode, dirmode, mask, expected_chmod_mode):
    """Test23 FileUtil._chmod()."""
    mock_lstat = mocker.patch('udocker.utils.fileutil.os.lstat')
    mock_chmod = mocker.patch('udocker.utils.fileutil.os.chmod')
    mock_stat = mocker.patch('udocker.utils.fileutil.stat')

    mock_lstat.return_value.st_mode = st_mode
    mock_stat.S_ISREG.return_value = is_reg
    mock_stat.S_ISDIR.return_value = is_dir
    mock_stat.S_ISLNK.return_value = is_lnk

    mock_stat.S_IMODE.side_effect = lambda mode: mode & 0o777

    futil._chmod("somefile", filemode=filemode, dirmode=dirmode, mask=mask)

    if expected_chmod_mode is not None:
        mock_chmod.assert_called_with("somefile", expected_chmod_mode)
    else:
        mock_chmod.assert_not_called()


def test_24_chmod(futil, mocker):
    """Test24 FileUtil.chmod()."""
    mock_walk = mocker.patch('udocker.utils.fileutil.os.walk',
                             return_value=[("/tmp", ["dir"], ["file"]), ])
    mock_fuchmod = mocker.patch.object(FileUtil, '_chmod', side_effect=[None, None, None, None])
    futil.safe_prefixes = ["/tmp"]
    resout = futil.chmod(0o600, 0o700, 0o755, True)
    assert resout
    mock_fuchmod.assert_called()
    mock_walk.assert_called()


def test_25_chmod(futil, mocker):
    """Test25 FileUtil.chmod()."""
    mock_walk = mocker.patch('udocker.utils.fileutil.os.walk',
                             return_value=[("/tmp", ["dir"], ["file"]), ])
    mock_fuchmod = mocker.patch.object(FileUtil, '_chmod', return_value=None)
    futil.safe_prefixes = ["/tmp"]
    resout = futil.chmod(0o600, 0o700, 0o755, False)
    assert resout
    mock_fuchmod.assert_called()
    mock_walk.assert_not_called()


def test_26_chmod(futil, mocker):
    """Test26 FileUtil.chmod()."""
    mock_fuchmod = mocker.patch.object(FileUtil, '_chmod', side_effect=OSError('fail'))
    resout = futil.chmod()
    assert not resout
    mock_fuchmod.assert_called()


def test_27_rchmod(futil, mocker):
    """Test27 FileUtil.rchmod()."""
    mock_fuchmod = mocker.patch.object(FileUtil, 'chmod', return_value=True)
    futil.rchmod()
    mock_fuchmod.assert_called()


def test_28__removedir(futil, mocker):
    """Test28 FileUtil._removedir()."""
    mock_walk = mocker.patch('udocker.utils.fileutil.os.walk',
                             return_value=[("/tmp", ["dir"], ["file"]), ])
    mock_islink = mocker.patch('udocker.utils.fileutil.os.path.islink',
                               side_effect=[False, True, True, True])
    mock_chmod = mocker.patch('udocker.utils.fileutil.os.chmod',
                              side_effect=[None, None, None, None])
    mock_unlink = mocker.patch('udocker.utils.fileutil.os.unlink',
                               side_effect=[None, None, None, None])
    mock_rmdir = mocker.patch('udocker.utils.fileutil.os.rmdir',
                              side_effect=[None, None, None, None])
    resout = futil._removedir()
    assert resout
    mock_walk.assert_called()
    mock_islink.assert_called()
    mock_chmod.assert_called()
    mock_rmdir.assert_called()


def test_29__removedir(futil, mocker):
    """Test29 FileUtil._removedir()."""
    mock_walk = mocker.patch('udocker.utils.fileutil.os.walk', side_effect=OSError('fail'))
    resout = futil._removedir()
    assert not resout


#           force, recursive, mhinfo, muid, msafe, mfile, mdir,  mrmd,  fname,     expected
data_rm = ((False, False, 100, 100, False, False, False, False, '/f4', False),
           (False, False, 100, 101, False, False, False, False, '/dir/f4', False),
           (False, False, 100, 100, False, True, False, False, '/dir/f4', False),
           (True, False, 100, 100, True, True, False, False, '/dir/f4', True),
           (False, True, 100, 100, True, False, True, True, '/dir/f4', True),
           (False, False, 100, 100, True, False, True, True, '/dir/f4', True),
           (False, False, 100, 100, True, False, True, False, '/dir/f4', False),
           )


@pytest.mark.parametrize('force,recursive,mhinfo,muid,msafe,mfile,mdir,mrmd,fname,expected', data_rm)
def test_30_remove(futil, mocker, logger, force, recursive, mhinfo, muid, msafe, mfile, mdir, mrmd, fname,
                   expected):
    """Test30 FileUtil.remove()."""
    mock_exists = mocker.patch('udocker.utils.fileutil.os.path.lexists', return_value=True)
    mock_hinfo = mocker.patch('udocker.utils.fileutil.HostInfo')
    mock_hinfo.uid = mhinfo
    mock_uid = mocker.patch.object(FileUtil, 'uid', return_value=muid)
    mock_safe = mocker.patch.object(FileUtil, '_is_safe_prefix', return_value=msafe)
    mock_isfile = mocker.patch('udocker.utils.fileutil.os.path.isfile', return_value=mfile)
    mock_islink = mocker.patch('udocker.utils.fileutil.os.path.islink', return_value=mfile)
    mock_isdir = mocker.patch('udocker.utils.fileutil.os.path.isdir', return_value=mdir)
    mock_remove = mocker.patch('udocker.utils.fileutil.os.remove')
    mock_furmdir = mocker.patch.object(FileUtil, '_removedir', return_value=mrmd)
    mock_furmd = mocker.patch.object(FileUtil, 'rmdir', return_value=mrmd)
    futil.filename = fname
    futil.tmptrash = {}
    resout = futil.remove(force, recursive)
    assert resout == expected

    if not expected:
        assert logger.error.call_count == 1


def test_31_remove(futil, mocker, logger):
    """Test31 FileUtil.remove()."""
    mock_exists = mocker.patch('udocker.utils.fileutil.os.path.lexists', return_value=True)
    mock_hinfo = mocker.patch('udocker.utils.fileutil.HostInfo')
    mock_hinfo.uid = 100
    mock_uid = mocker.patch.object(FileUtil, 'uid', return_value=100)
    mock_safe = mocker.patch.object(FileUtil, '_is_safe_prefix', return_value=False)
    mock_isfile = mocker.patch('udocker.utils.fileutil.os.path.isfile', return_value=True)
    mock_islink = mocker.patch('udocker.utils.fileutil.os.path.islink', return_value=True)
    mock_remove = mocker.patch('udocker.utils.fileutil.os.remove', side_effect=OSError('fail'))
    futil.filename = '/dir/f4'
    resout = futil.remove()
    assert not resout
    assert logger.error.call_count == 1
    logger.error.assert_called_with('delete outside of directory tree: %s', '/dir/f4')


data_tarver = ((True, False, True), (True, True, False), (False, False, False))


@pytest.mark.parametrize('misfile,boolcal,expected', data_tarver)
def test_32_verify_tar(futil, mocker, misfile, boolcal, expected):
    """Test32 FileUtil.verify_tar()."""
    mock_isfile = mocker.patch('udocker.utils.fileutil.os.path.isfile', return_value=misfile)
    mock_stderr = mocker.patch('udocker.utils.fileutil.Uprocess.get_stderr', return_value='stder')
    mock_call = mocker.patch('udocker.utils.fileutil.Uprocess.call', return_value=boolcal)
    resout = futil.verify_tar()
    assert resout == expected
    mock_isfile.assert_called()


data_tar = ((False, True), (True, False))


@pytest.mark.parametrize('boolcal,expected', data_tar)
def test_33_tar(futil, mocker, logger, boolcal, expected):
    """Test33 FileUtil.tar()."""
    mock_stderr = mocker.patch('udocker.utils.fileutil.Uprocess.get_stderr', return_value='stder')
    mock_call = mocker.patch('udocker.utils.fileutil.Uprocess.call', return_value=boolcal)
    resout = futil.tar('t.tar')
    assert resout == expected
    mock_stderr.assert_called()
    mock_call.assert_called()
    if not expected:
        logger.error.assert_called_with('creating tar file: %s', 't.tar')


data_cpdir = ((True, True), (False, False))


@pytest.mark.parametrize('mpipe,expected', data_cpdir)
def test_34_copydir(futil, mocker, mpipe, expected):
    """Test34 FileUtil.copydir()."""
    mock_pipe = mocker.patch('udocker.utils.fileutil.Uprocess.pipe', return_value=mpipe)
    resout = futil.copydir('/dir')
    assert resout == expected
    mock_pipe.assert_called()


def test_35_cleanup(futil, mocker):
    """Test35 FileUtil.cleanup()."""
    mock_remove = mocker.patch.object(FileUtil, 'remove')
    futil.tmptrash = {'file1.txt': None, 'file2.txt': None}
    futil.cleanup()
    mock_remove.assert_called()


@pytest.mark.parametrize("executable, error, result", [
    (True, False, True),
    (True, True, False),
    (False, True, False),
    (False, False, False),
])
def test_36_isexectutable(futil, mocker, error, executable, result):
    """Test36 FileUtil.isexectutable()."""
    mock_access_executable = mocker.patch.object(os, 'access', return_value=executable)
    if error:
        mock_access_executable.side_effect = OSError('fail')
    is_exec = futil.isexecutable()
    assert is_exec == result
    mock_access_executable.assert_called()


@pytest.mark.parametrize("writable, error, result", [
    (True, False, True),
    (True, True, False),
    (False, True, False),
    (False, False, False),
])
def test_37_iswriteable(futil, mocker, error, writable, result):
    """Test37 FileUtil.isexectutable()."""
    mock_access_writable = mocker.patch.object(os, 'access', return_value=writable)
    if error:
        mock_access_writable.side_effect = OSError('fail')
    is_exec = futil.iswriteable()
    assert is_exec == result
    mock_access_writable.assert_called()


@pytest.mark.parametrize('misdir,expected', data_cpdir)
def test_38_isdir(futil, mocker, misdir, expected):
    """Test38 FileUtil.isdir()."""
    mock_isdir = mocker.patch('udocker.utils.fileutil.os.path.isdir', return_value=misdir)
    resout = futil.isdir()
    assert resout == expected
    mock_isdir.assert_called()


@pytest.mark.parametrize('misfile,expected', data_cpdir)
def test_39_isfile(futil, mocker, misfile, expected):
    """Test39 FileUtil.isfile()."""
    mock_isfile = mocker.patch('udocker.utils.fileutil.os.path.isfile', return_value=misfile)
    resout = futil.isfile()
    assert resout == expected
    mock_isfile.assert_called()


def test_40_size(futil, mocker):
    """Test40 FileUtil.size()."""
    mock_stat = mocker.patch('udocker.utils.fileutil.os.stat')
    mock_stat.return_value.st_size = 4321
    size = futil.size()
    assert size == 4321
    mock_stat.assert_called()


def test_41_size(futil, mocker):
    """Test41 FileUtil.size()."""
    mock_stat = mocker.patch('udocker.utils.fileutil.os.stat', side_effect=OSError('fail'))
    size = futil.size()
    assert size == -1


def test_42_getdata(futil, mocker):
    """Test42 FileUtil.getdata()."""
    mock_file = mocker.mock_open(read_data='qwerty')
    mocker.patch("builtins.open", mock_file)
    resout = futil.getdata()
    assert resout == 'qwerty'
    mock_file.assert_called()


def test_43_getdata(futil, mocker):
    """Test43 FileUtil.getdata()."""
    mock_file = mocker.mock_open()
    mock_file.side_effect = OSError
    resout = futil.getdata()
    assert resout == ''


def test_44_get1stline(futil, mocker):
    """Test44 FileUtil.get1stline()."""
    mock_file = mocker.mock_open(read_data='qwerty')
    mocker.patch("builtins.open", mock_file)
    resout = futil.get1stline()
    assert resout == 'qwerty'
    mock_file.assert_called()


def test_45_get1stline(futil, mocker):
    """Test45 FileUtil.get1stline()."""
    mock_file = mocker.mock_open()
    mock_file.side_effect = OSError
    resout = futil.get1stline()
    assert resout == ''


def test_46_putdata(futil, mocker):
    """Test46 FileUtil.putdata()."""
    mock_file = mocker.mock_open()
    mocker.patch("builtins.open", mock_file)
    resout = futil.putdata('qwerty')
    assert resout == 'qwerty'
    mock_file.assert_called()


def test_47_putdata(futil, mocker):
    """Test47 FileUtil.putdata()."""
    mock_file = mocker.mock_open()
    mock_file.side_effect = OSError
    resout = futil.putdata('qwerty')
    assert resout == ''


def test_48_getvalid_path(futil, mocker):
    """Test48 FileUtil.getvalid_path()."""
    mock_exists = mocker.patch('udocker.utils.fileutil.os.path.exists', return_value=True)
    resout = futil.getvalid_path()
    assert resout == '/dir/somefile'
    mock_exists.assert_called()


def test_49_getvalid_path(futil, mocker):
    """Test49 FileUtil.getvalid_path()."""
    mock_exists = mocker.patch('udocker.utils.fileutil.os.path.exists', side_effect=[False, True])
    mock_split = mocker.patch('udocker.utils.fileutil.os.path.split',
                              return_value=('somefile', '/dir'))
    resout = futil.getvalid_path()
    assert resout == 'somefile'
    assert mock_exists.call_count == 2
    mock_split.assert_called()


def test_50__cont2host(futil, mocker):
    """Test50 FileUtil._cont2host()."""
    resout = futil._cont2host('', '/ROOT')
    assert resout == ''


def test_51__cont2host(futil, mocker):
    """Test51 FileUtil._cont2host()."""
    resout = futil._cont2host('/usr/bin', '/ROOT/usr/bin')
    assert resout == '/ROOT/usr/bin/usr/bin'


def test_52__cont2host(futil, mocker):
    """Test52 FileUtil._cont2host()."""
    vol = ['/home/user:/ROOT/home/user']  # var - volume
    mock_rpath = mocker.patch('udocker.utils.fileutil.os.path.realpath', return_value='/ROOT/usr/bin')
    mock_normp = mocker.patch('udocker.utils.fileutil.os.path.normpath', return_value='/ROOT/usr/bin')
    mock_islink = mocker.patch('udocker.utils.fileutil.os.path.islink', return_value=False)
    resout = futil._cont2host('/usr/bin', '/ROOT/usr/bin', vol)
    assert resout == '/ROOT/usr/bin'
    mock_rpath.assert_called()
    mock_normp.assert_called()
    mock_islink.assert_called()


# def test_53__cont2host(futil, mocker):
#     """Test53 FileUtil._cont2host()."""
#     mock_rpath = mocker.patch('udocker.utils.fileutil.os.path.realpath', side_effect=['/ROOT/usr/bin', '/ROOT/link'])
#     mock_normp = mocker.patch('udocker.utils.fileutil.os.path.normpath', return_value='/ROOT/usr/bin')
#     mock_islink = mocker.patch('udocker.utils.fileutil.os.path.islink', side_effect=[True, False])
#     mock_readlnk = mocker.patch('udocker.utils.fileutil.os.readlink', return_value='/ROOT/link')
#     resout = futil._cont2host('/usr/bin', '/ROOT/usr/bin')
#     assert resout == '/ROOT/link'
#     mock_rpath.assert_called()
#     mock_normp.assert_called()
#     mock_islink.assert_called()
#     mock_readlnk.assert_called()


def test_54_cont2host(futil, mocker):
    """Test54 FileUtil.cont2host()."""
    mock_c2h = mocker.patch.object(FileUtil, '_cont2host', return_value='/ROOT/dir')
    resout = futil.cont2host('/ROOT/dir')
    assert resout == '/ROOT/dir'
    mock_c2h.assert_called()


def test_55__find_exec(futil, mocker):
    """Test55 FileUtil._find_exec()."""
    resout = futil._find_exec('')
    assert resout == ''


def test_56__find_exec(futil, mocker):
    """Test56 FileUtil._find_exec()."""
    mock_c2h = mocker.patch.object(FileUtil, '_cont2host',
                                   side_effect=['/ROOT/usr/bin', '/ROOT', '/ROOT'])
    mock_isfile = mocker.patch('udocker.utils.fileutil.os.path.isfile',
                               side_effect=[False, False, True])
    mock_access = mocker.patch('udocker.utils.fileutil.os.access', side_effect=[True, True, True])
    resout = futil._find_exec(['/usr/bin', '.', '..'], '/ROOT')
    assert resout == '../somefile'
    assert mock_isfile.call_count == 3
    assert mock_access.call_count == 1


def test_57_find_exec(futil, mocker):
    """Test57 FileUtil.find_exec()."""
    mock_findexe = mocker.patch.object(FileUtil, '_find_exec', return_value='/bin/ls')
    resout = futil.find_exec("/bin", "", "", ".", False)
    assert resout == '/bin/ls'
    mock_findexe.assert_called()


def test_58_rename(futil, mocker):
    """Test58 FileUtil.rename()."""
    mock_rename = mocker.patch('udocker.utils.fileutil.os.rename')
    resout = futil.rename("somefile")
    assert resout
    mock_rename.assert_called()


def test_59_rename(futil, mocker):
    """Test59 FileUtil.rename()."""
    mock_rename = mocker.patch('udocker.utils.fileutil.os.rename', side_effect=OSError('fail'))
    resout = futil.rename("somefile")
    assert not resout
    mock_rename.assert_called()


@pytest.mark.parametrize('input_data, expected_output, mode, raises_error', [
    (b"streaming udocker", b"streaming udocker", "w", False),
    (b"streaming udocker", b"streaming udocker", "w", True),
    (b"", b"", "w", False),
])
def test_60__stream2file(mocker, futil, tmp_path, input_data, expected_output, mode, raises_error):
    """Test60 FileUtil._stream2file()."""
    dest_filename = tmp_path / "output.txt"
    futil.filename = str(dest_filename)
    mocker.patch("sys.stdin.buffer.read", side_effect=[input_data, None])

    if raises_error:
        mocker.patch('builtins.open', side_effect=OSError)

    result = futil._stream2file(str(dest_filename), mode)
    assert result == (not raises_error)


def test_61__file2stream(futil, mocker):
    """Test61 FileUtil._file2stream()."""
    mock_file = mocker.mock_open(read_data='qwerty')
    mocker.patch("builtins.open", mock_file)
    mock_stdout = mocker.patch('udocker.utils.fileutil.sys.stdout.write')
    resout = futil._file2stream()
    assert resout
    mock_file.assert_called()
    mock_stdout.assert_called()


def test_62__file2stream(futil, mocker):
    """Test62 FileUtil._file2stream()."""
    mock_file = mocker.mock_open()
    mock_file.side_effect = OSError
    resout = futil._file2stream()
    assert not resout


@pytest.mark.parametrize("src_open_success, dst_open_success, expected_result, expected_open_calls", [
    (True, True, True, 2),
    (False, True, False, 1),
    (True, False, False, 2),
])
def test_63__file2file(futil, mocker, src_open_success, dst_open_success, expected_result, expected_open_calls):
    """Test63 FileUtil._file2file()."""

    mock_open = mocker.mock_open(read_data='content of the source file')
    mocker.patch("builtins.open", mock_open)

    side_effects = []
    if not src_open_success:
        side_effects.append(OSError())
    else:
        side_effects.append(mocker.DEFAULT)

    if not dst_open_success:
        side_effects.append(OSError())
    else:
        side_effects.append(mocker.DEFAULT)

    mock_open.side_effect = side_effects

    resout = futil._file2file('dstfile')
    assert resout == expected_result
    assert mock_open.call_count == expected_open_calls


def test_64__file2file(futil, mocker):
    """Test64 FileUtil._file2file()."""
    mock_file = mocker.mock_open()
    mock_file.side_effect = OSError
    resout = futil._file2file('dstfile')
    assert not resout


data_cpto = (('-', 'dstfile', 1, 0, 0, True),
             ('srcfile', '-', 0, 1, 0, True),
             ('srcfile', 'dstfile', 0, 0, 1, True),
             ('-', '-', 0, 0, 0, False))


@pytest.mark.parametrize('srcfname,dstfname,cnts2f,cntf2s,cntf2f,expected', data_cpto)
def test_65_copyto(futil, mocker, srcfname, dstfname, cnts2f, cntf2s, cntf2f, expected):
    """Test65 FileUtil.copyto()."""
    mock_s2f = mocker.patch.object(FileUtil, '_stream2file', return_value=True)
    mock_f2s = mocker.patch.object(FileUtil, '_file2stream', return_value=True)
    mock_f2f = mocker.patch.object(FileUtil, '_file2file', return_value=True)
    futil.filename = srcfname
    resout = futil.copyto(dstfname)
    assert resout == expected
    assert mock_s2f.call_count == cnts2f
    assert mock_f2s.call_count == cntf2s
    assert mock_f2f.call_count == cntf2f


def test_66_find_file_in_dir(futil, mocker):
    """Test66 FileUtil.find_file_in_dir()."""
    mock_exists = mocker.patch('udocker.utils.fileutil.os.path.exists', side_effect=[False, True])
    resout = futil.find_file_in_dir(['F1', 'F2'])
    assert resout == '/dir/somefile/F2'
    assert mock_exists.call_count == 2


def test_67_find_file_in_dir(futil, mocker):
    """Test67 FileUtil.find_file_in_dir()."""
    mock_exists = mocker.patch('udocker.utils.fileutil.os.path.exists')
    resout = futil.find_file_in_dir([])
    assert resout == ''
    mock_exists.assert_not_called()


def test_68__link_change_apply(futil, mocker):
    """Test68 FileUtil._link_change_apply()."""
    mock_realpath = mocker.patch('udocker.utils.fileutil.os.path.realpath', return_value="/HOST/DIR")
    mock_access = mocker.patch('udocker.utils.fileutil.os.access', return_value=False)
    mock_chmod = mocker.patch('udocker.utils.fileutil.os.chmod', side_effect=[None, None])
    mock_remove = mocker.patch('udocker.utils.fileutil.os.remove')
    mock_symlink = mocker.patch('udocker.utils.fileutil.os.symlink')
    mock_osstat = mocker.patch('udocker.utils.fileutil.os.stat')
    mock_stat = mocker.patch('udocker.utils.fileutil.stat')
    mock_stat.return_value.S_IWUSR = 128
    futil._link_change_apply("/con/lnk_new", "/con/lnk", True)
    mock_realpath.assert_called()
    mock_access.assert_called()
    mock_chmod.assert_called()
    mock_remove.assert_called()
    mock_symlink.assert_called()
    mock_osstat.assert_called()


def test_69__link_change_apply(futil, mocker):
    """Test69 FileUtil._link_change_apply()."""
    mock_realpath = mocker.patch('udocker.utils.fileutil.os.path.realpath', return_value="/HOST/DIR")
    mock_access = mocker.patch('udocker.utils.fileutil.os.access')
    mock_chmod = mocker.patch('udocker.utils.fileutil.os.chmod')
    mock_remove = mocker.patch('udocker.utils.fileutil.os.remove')
    mock_symlink = mocker.patch('udocker.utils.fileutil.os.symlink')
    mock_osstat = mocker.patch('udocker.utils.fileutil.os.stat')
    futil._link_change_apply("/con/lnk_new", "/con/lnk", False)
    mock_realpath.assert_called()
    mock_access.assert_not_called()
    mock_chmod.assert_not_called()
    mock_remove.assert_called()
    mock_symlink.assert_called()


data_lnkset = (('X', False, False),
               ('/con', False, False),
               ('/HOST/DIR', False, True),
               ('/HOST/DIR', True, True))


@pytest.mark.parametrize('mrlnk,force,expected', data_lnkset)
def test_70__link_set(futil, mocker, mrlnk, force, expected):
    """Test70 FileUtil._link_set()."""
    mock_readlink = mocker.patch('udocker.utils.fileutil.os.readlink', return_value=mrlnk)
    mock_lnchange = mocker.patch.object(FileUtil, '_link_change_apply')
    futil.filename = '/con'
    resout = futil._link_set('/con/lnk', '', '/con', force)
    assert resout == expected
    mock_readlink.assert_called()


data_lnkrest = (('/con/AAA', '/con', False, True),
                ('/con/BBB', '/con', False, True),
                ('/XXX', '/con', False, False),
                ('/root/BBB', '/con', True, True),
                ('BBB', '/con', True, False),
                ('/dir/containers/ROOT', '', True, False))


@pytest.mark.parametrize('mrlnk,orig_path,force,expected', data_lnkrest)
def test_71__link_restore(futil, mocker, mrlnk, orig_path, force, expected):
    """Test71 FileUtil._link_restore()."""
    mock_readlink = mocker.patch('udocker.utils.fileutil.os.readlink', return_value=mrlnk)
    mock_lnchange = mocker.patch.object(FileUtil, '_link_change_apply')
    futil.filename = '/con'
    resout = futil._link_restore('/con/lnk', orig_path, '/root', force)
    assert resout == expected
    mock_readlink.assert_called()


def test_72_links_conv(futil, mocker, logger):
    """Test72 FileUtil.links_conv()."""
    mock_is_safe_prefix = mocker.patch.object(FileUtil, '_is_safe_prefix', return_value=False)
    mock_walk = mocker.patch('udocker.utils.fileutil.os.walk')
    mock_realpath = mocker.patch('udocker.utils.fileutil.os.path.realpath', return_value='/ROOT')
    futil.filename = '/ROOT'
    resout = futil.links_conv()
    assert resout == []
    mock_realpath.assert_called()
    mock_is_safe_prefix.assert_called()
    mock_walk.assert_not_called()
    logger.error.assert_called_with('links conversion outside of dir tree: %s', '/ROOT')


def test_73_links_conv(futil, mocker):
    """Test73 FileUtil.links_conv()."""
    mock_link_restore = mocker.patch.object(FileUtil, '_link_restore', side_effect=[False, False])
    mock_link_set = mocker.patch.object(FileUtil, '_link_set', side_effect=[False, True])
    mock_is_safe_prefix = mocker.patch.object(FileUtil, '_is_safe_prefix', return_value=True)
    mock_lstat = mocker.patch('udocker.utils.fileutil.os.lstat')
    mock_lstat.return_value.st_uid = 1234
    mock_hinfo = mocker.patch('udocker.utils.fileutil.HostInfo')
    mock_hinfo.uid = 1234
    mock_islink = mocker.patch('udocker.utils.fileutil.os.path.islink', side_effect=[False, True])
    mock_walk = mocker.patch('udocker.utils.fileutil.os.walk',
                             return_value=[('/ROOT', [], ["F1", "L2"]), ])
    mock_realpath = mocker.patch('udocker.utils.fileutil.os.path.realpath', return_value='/ROOT')
    futil.filename = '/ROOT'
    resout = futil.links_conv()
    assert resout == []
    mock_realpath.assert_called()
    mock_is_safe_prefix.assert_called()
    mock_walk.assert_called()
    mock_link_restore.assert_not_called()
    mock_link_set.assert_called()
    mock_islink.assert_called()


def test_74_match(futil, mocker):
    """Test74 FileUtil.match()."""
    mock_isdir = mocker.patch('udocker.utils.fileutil.os.path.isdir', return_value=False)
    mock_lsdir = mocker.patch('udocker.utils.fileutil.os.listdir', return_value=[])
    mock_dname = mocker.patch('udocker.utils.fileutil.os.path.dirname', return_value='/con/fil*')
    mock_base = mocker.patch('udocker.utils.fileutil.os.path.basename', return_value='/con/filet')
    futil.filename = '/con/filename.txt'
    resout = futil.match()
    assert resout == []
    mock_isdir.assert_called()
    mock_lsdir.assert_not_called()
    mock_dname.assert_called()
    mock_base.assert_called()


def test_75_match(futil, mocker):
    """Test75 FileUtil.match()."""
    mock_isdir = mocker.patch('udocker.utils.fileutil.os.path.isdir', return_value=True)
    mock_lsdir = mocker.patch('udocker.utils.fileutil.os.listdir', return_value=['file1', 'file2'])
    mock_dname = mocker.patch('udocker.utils.fileutil.os.path.dirname', return_value='/con')
    mock_base = mocker.patch('udocker.utils.fileutil.os.path.basename', return_value='fil*')
    futil.filename = '/con/fil*'
    resout = futil.match()
    assert resout == ['/con/file1', '/con/file2']
    mock_isdir.assert_called()
    mock_lsdir.assert_called()
    mock_dname.assert_called()
    mock_base.assert_called()


@pytest.mark.parametrize('file_pattern, expected_count, exists, include_symlinks', [
    (r".*\.txt$", 2, True, False),
    (r".*\.md$", 0, True, False),
    (r".*", 3, True, False),
    (r".*", 0, False, False),
    (r".*", 2, True, True)
])
def test_76_match_recursive(mocker, futil, tmp_path, file_pattern, expected_count, exists, include_symlinks):
    """Test76 FileUtil.match_recursive()."""
    base_path = tmp_path / "testdir"

    if exists:
        base_path.mkdir()
        (base_path / "file1.txt").write_text("content1")
        (base_path / "file2.txt").write_text("content2")
        (base_path / "directory1").mkdir()
        if include_symlinks:
            (base_path / "symlink").symlink_to("file1.txt")

    futil.filename = str(base_path / file_pattern)

    side_effect_symlinks = [True, True, False, False, False]
    if include_symlinks:
        mocker.patch.object(os.path, 'islink', side_effect=side_effect_symlinks)

    filetype = 'FD'
    matching_files = futil.match_recursive(filetype=filetype)

    assert (len(matching_files) if not include_symlinks else side_effect_symlinks.count(True)) == expected_count
