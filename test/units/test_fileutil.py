#!/usr/bin/env python
"""
udocker unit tests: FileUtil
"""
import sys
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
def futil(mocker):
    mock_absp = mocker.patch('os.path.abspath', return_value='/dir/somefile')
    mock_base = mocker.patch('os.path.basename', return_value='somefile')
    mock_regpre = mocker.patch.object(FileUtil, '_register_prefix')
    return FileUtil('somefile')


def test_01_init(mocker):
    """Test01 FileUtil() constructor."""
    mock_absp = mocker.patch('os.path.abspath', return_value='/dir/somefile')
    mock_base = mocker.patch('os.path.basename', return_value='somefile')
    mock_regpre = mocker.patch.object(FileUtil, '_register_prefix')
    fileutil = FileUtil('somefile')
    assert fileutil.filename == '/dir/somefile'
    mock_absp.assert_called()
    mock_base.assert_called()
    mock_regpre.assert_called()


def test_02_init(mocker):
    """Test02 FileUtil() constructor."""
    mock_absp = mocker.patch('os.path.abspath')
    mock_base = mocker.patch('os.path.basename')
    mock_regpre = mocker.patch.object(FileUtil, '_register_prefix')
    fileutil = FileUtil('-')
    assert fileutil.filename == '-'
    mock_absp.assert_not_called()
    mock_base.assert_not_called()
    mock_regpre.assert_not_called()


data_regp = (('/dir1', '/dir1', ['/dir1', '/dir1', '/dir1', '/dir1'], True, False,
              ['/tmp/', '/tmp/', '/tmp/', '/tmp/', '/some_contdir', '/some_contdir',
               '/home/.udocker/containers/123', '/home/.udocker/containers/123', '/dir1/',
               '/dir1/', '/dir1/', '/dir1/']),
             ('file1', '/dir1/file1', ['/dir1/file1', '/dir1/file1', '/dir1/file1', '/dir1/file1'],
              False, False,
              ['/tmp/', '/tmp/', '/tmp/', '/tmp/', '/some_contdir', '/some_contdir',
               '/home/.udocker/containers/123', '/home/.udocker/containers/123', '/dir1/',
               '/dir1/', '/dir1/', '/dir1/', '/dir1/file1', '/dir1/file1']))


@pytest.mark.parametrize("ftype,abspath,rpathsd,risdir,rislink,expected", data_regp)
def test_03_register_prefix(mocker, ftype, abspath, rpathsd, risdir, rislink, expected):
    """Test03 FileUtil.register_prefix()."""
    mock_absp = mocker.patch('os.path.abspath', return_value=abspath)
    mock_base = mocker.patch('os.path.basename', return_value=ftype)
    mock_rpath = mocker.patch('os.path.realpath', side_effect=rpathsd)
    mock_isdir = mocker.patch('os.path.isdir', return_value=risdir)
    mock_islink = mocker.patch('os.path.islink', return_value=rislink)
    fileutil = FileUtil(ftype)
    fileutil.register_prefix()
    assert fileutil.safe_prefixes == expected
    mock_absp.assert_called()
    mock_base.assert_called()
    mock_rpath.assert_called()
    mock_isdir.assert_called()
    mock_islink.assert_called()


def test_04_umask(futil, mocker):
    """Test04 FileUtil.umask()."""
    mock_umask = mocker.patch('os.umask', return_value=0)
    resout = futil.umask()
    assert resout
    mock_umask.assert_called()


def test_05_umask(futil, mocker):
    """Test05 FileUtil.umask()."""
    mock_umask = mocker.patch('os.umask', return_value=1)
    resout = futil.umask(1)
    assert resout
    assert futil.orig_umask == 1
    mock_umask.assert_called()


def test_06_umask(futil, mocker):
    """Test06 FileUtil.umask()."""
    mock_umask = mocker.patch('os.umask', side_effect=TypeError('fail'))
    resout = futil.umask()
    assert not resout
    mock_umask.assert_called()


def test_07_umask(futil, mocker):
    """Test07 FileUtil.umask()."""
    mock_umask = mocker.patch('os.umask', side_effect=TypeError('fail'))
    resout = futil.umask(1)
    assert not resout
    mock_umask.assert_called()


def test_08_mktmp(futil, mocker):
    """Test08 FileUtil.mktmp()."""
    mock_uniqf = mocker.patch('udocker.utils.fileutil.Unique.filename', return_value='fname213')
    mock_exists = mocker.patch('os.path.exists', return_value=False)
    resout = futil.mktmp()
    assert resout == '/tmp/fname213'
    assert futil.tmptrash['/tmp/fname213']
    mock_uniqf.assert_called()
    mock_exists.assert_called()


def test_09_mkdir(futil, mocker):
    """Test09 FileUtil.mkdir()"""
    mock_mkdirs = mocker.patch('os.makedirs')
    resout = futil.mkdir()
    assert resout
    mock_mkdirs.assert_called()


def test_10_mkdir(futil, mocker):
    """Test10 FileUtil.mkdir()"""
    mock_mkdirs = mocker.patch('os.makedirs', side_effect=OSError('fail'))
    resout = futil.mkdir()
    assert not resout
    mock_mkdirs.assert_called()


def test_11_rmdir(futil, mocker):
    """Test11 FileUtil.rmdir()"""
    mock_rmdir = mocker.patch('os.rmdir')
    resout = futil.rmdir()
    assert resout
    mock_rmdir.assert_called()


def test_12_rmdir(futil, mocker):
    """Test12 FileUtil.rmdir()"""
    mock_rmdir = mocker.patch('os.rmdir', side_effect=OSError('fail'))
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
    mock_lstat = mocker.patch('os.lstat')
    mock_lstat.return_value.st_uid = 1234
    resout = futil.uid()
    assert resout == 1234
    mock_lstat.assert_called()


def test_15_uid(futil, mocker):
    """Test15 FileUtil.uid()."""
    mock_lstat = mocker.patch('os.lstat', side_effect=OSError('fail'))
    resout = futil.uid()
    assert resout == -1


data_spref = (('/bin', ['/bin'], ['/bin', '/bin'], True, False, True),
              ('ls', ['/bin/ls'], ['/bin/ls', '/bin/ls'], False, False, True),
              ('link', ['/bin/link'], ['/bin/link', '/bin/link'], False, True, True))


@pytest.mark.parametrize("fname,safep,rpathsd,risdir,rislink,expected", data_spref)
def test_16__is_safe_prefix(futil, mocker, fname, safep, rpathsd, risdir, rislink, expected):
    """Test16 FileUtil._is_safe_prefix()."""
    mock_base = mocker.patch('os.path.basename', return_value=fname)
    mock_rpath = mocker.patch('os.path.realpath', side_effect=rpathsd)
    mock_isdir = mocker.patch('os.path.isdir', return_value=risdir)
    mock_islink = mocker.patch('os.path.islink', return_value=rislink)
    futil.safe_prefixes = safep
    resout = futil._is_safe_prefix(fname)
    assert resout == expected
    mock_rpath.assert_called()
    mock_isdir.assert_called()
    mock_islink.assert_called()


def test_17_chown(futil, mocker):
    """Test17 FileUtil.chown()."""
    mock_lchown = mocker.patch('os.lchown')
    resout = futil.chown(0, 0, False)
    assert resout
    mock_lchown.assert_called()


def test_18_chown(futil, mocker):
    """Test18 FileUtil.chown()."""
    mock_lchown = mocker.patch('os.lchown', side_effect=[None, None, None, None])
    mock_walk = mocker.patch('os.walk', return_value=[("/tmp", ["dir"], ["file"]), ])
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


# def test_21__chmod(futil, mocker):
#     """Test21 FileUtil._chmod()."""
#     mock_lstat = mocker.patch('os.lstat')
#     mock_stat = mocker.patch('stat')
#     mock_chmod = mocker.patch('os.chmod')
#     mock_lstat.return_value.st_mode = 33277
#     mock_stat.return_value.S_ISREG = True
#     mock_stat.return_value.S_ISDIR = False
#     mock_stat.return_value.S_ISLNK = False
#     mock_stat.return_value.S_IMODE = 509
#     futil._chmod("somefile")
#     mock_lstat.assert_called()
#     mock_stat.S_ISREG.assert_called()
#     mock_stat.S_IMODE.assert_called()


def test_22__chmod(futil, mocker):
    """Test22 FileUtil._chmod()."""
    mock_lstat = mocker.patch('os.lstat', side_effect=OSError('fail'))
    futil._chmod("somefile")
    mock_lstat.assert_called()


def test23_chmod(futil, mocker):
    """Test23 FileUtil.chmod()."""
    mock_walk = mocker.patch('os.walk', return_value=[("/tmp", ["dir"], ["file"]), ])
    mock_fuchmod = mocker.patch.object(FileUtil, '_chmod', side_effect=[None, None, None, None])
    futil.safe_prefixes = ["/tmp"]
    resout = futil.chmod(0o600, 0o700, 0o755, True)
    assert resout
    mock_fuchmod.assert_called()
    mock_walk.assert_called()


def test24_chmod(futil, mocker):
    """Test24 FileUtil.chmod()."""
    mock_walk = mocker.patch('os.walk', return_value=[("/tmp", ["dir"], ["file"]), ])
    mock_fuchmod = mocker.patch.object(FileUtil, '_chmod', return_value=None)
    futil.safe_prefixes = ["/tmp"]
    resout = futil.chmod(0o600, 0o700, 0o755, False)
    assert resout
    mock_fuchmod.assert_called()
    mock_walk.assert_not_called()


def test25_chmod(futil, mocker):
    """Test25 FileUtil.chmod()."""
    mock_fuchmod = mocker.patch.object(FileUtil, '_chmod', side_effect=OSError('fail'))
    resout = futil.chmod()
    assert not resout


def test26_rchmod(futil, mocker):
    """Test26 FileUtil.rchmod()."""
    mock_fuchmod = mocker.patch.object(FileUtil, 'chmod', return_value=True)
    futil.rchmod()
    mock_fuchmod.assert_called()


def test_27__removedir(futil, mocker):
    """Test27 FileUtil._removedir()."""
    mock_walk = mocker.patch('os.walk', return_value=[("/tmp", ["dir"], ["file"]), ])
    mock_islink = mocker.patch('os.path.islink', side_effect=[False, True, True, True])
    mock_chmod = mocker.patch('os.chmod', side_effect=[None, None, None, None])
    mock_unlink = mocker.patch('os.unlink', side_effect=[None, None, None, None])
    mock_rmdir = mocker.patch('os.rmdir', side_effect=[None, None, None, None])
    resout = futil._removedir()
    assert resout
    mock_walk.assert_called()
    mock_islink.assert_called()
    mock_chmod.assert_called()
    mock_rmdir.assert_called()


def test_28__removedir(futil, mocker):
    """Test28 FileUtil._removedir()."""
    mock_walk = mocker.patch('os.walk', side_effect=OSError('fail'))
    resout = futil._removedir()
    assert not resout


#           force, recursive, mhinfo, muid, msafe, mfile, mdir,  mrmd,  fname,     expected
data_rm = ((False, False,     100,    100,  False, False, False, False, '/f4',     False),
           (False, False,     100,    101,  False, False, False, False, '/dir/f4', False),
           (False, False,     100,    100,  False, True,  False, False, '/dir/f4', False),
           (True,  False,     100,    100,  True,  True,  False, False, '/dir/f4', True),
           (False, True,      100,    100,  True,  False, True,  True,  '/dir/f4', True),
           (False, False,     100,    100,  True,  False, True,  True,  '/dir/f4', True),
           (False, False,     100,    100,  True,  False, True,  False, '/dir/f4', False),
           )


@pytest.mark.parametrize('force,recursive,mhinfo,muid,msafe,mfile,mdir,mrmd,fname,expected', data_rm)
def test_29_remove(futil, mocker, force, recursive, mhinfo, muid, msafe, mfile, mdir, mrmd, fname,
                   expected):
    """Test29 FileUtil.remove()."""
    mock_exists = mocker.patch('os.path.lexists', return_value=True)
    mock_hinfo = mocker.patch('udocker.utils.fileutil.HostInfo')
    mock_hinfo.uid = mhinfo
    mock_uid = mocker.patch.object(FileUtil, 'uid', return_value=muid)
    mock_safe = mocker.patch.object(FileUtil, '_is_safe_prefix', return_value=msafe)
    mock_isfile = mocker.patch('os.path.isfile', return_value=mfile)
    mock_islink = mocker.patch('os.path.islink', return_value=mfile)
    mock_isdir = mocker.patch('os.path.isdir', return_value=mdir)
    mock_remove = mocker.patch('os.remove')
    mock_furmdir = mocker.patch.object(FileUtil, '_removedir', return_value=mrmd)
    mock_furmd = mocker.patch.object(FileUtil, 'rmdir', return_value=mrmd)
    futil.filename = fname
    futil.tmptrash = {}
    resout = futil.remove(force, recursive)
    assert resout == expected


def test_30_remove(futil, mocker):
    """Test30 FileUtil.remove()."""
    mock_exists = mocker.patch('os.path.lexists', return_value=True)
    mock_hinfo = mocker.patch('udocker.utils.fileutil.HostInfo')
    mock_hinfo.uid = 100
    mock_uid = mocker.patch.object(FileUtil, 'uid', return_value=100)
    mock_safe = mocker.patch.object(FileUtil, '_is_safe_prefix', return_value=False)
    mock_isfile = mocker.patch('os.path.isfile', return_value=True)
    mock_islink = mocker.patch('os.path.islink', return_value=True)
    mock_remove = mocker.patch('os.remove', side_effect=OSError('fail'))
    futil.filename = '/dir/f4'
    resout = futil.remove()
    assert not resout


data_tarver = ((True, False, True), (True, True, False), (False, False, False))


@pytest.mark.parametrize('misfile,boolcal,expected', data_tarver)
def test_31_verify_tar(futil, mocker, misfile, boolcal, expected):
    """Test31 FileUtil.verify_tar()."""
    mock_isfile = mocker.patch('os.path.isfile', return_value=misfile)
    mock_stderr = mocker.patch('udocker.utils.fileutil.Uprocess.get_stderr', return_value='stder')
    mock_call = mocker.patch('udocker.utils.fileutil.Uprocess.call', return_value=boolcal)
    resout = futil.verify_tar()
    assert resout == expected
    mock_isfile.assert_called()


data_tar = ((False, True), (True, False))


@pytest.mark.parametrize('boolcal,expected', data_tar)
def test_32_tar(futil, mocker, boolcal, expected):
    """Test32 FileUtil.tar()."""
    mock_stderr = mocker.patch('udocker.utils.fileutil.Uprocess.get_stderr', return_value='stder')
    mock_call = mocker.patch('udocker.utils.fileutil.Uprocess.call', return_value=boolcal)
    resout = futil.tar('t.tar')
    assert resout == expected
    mock_stderr.assert_called()
    mock_call.assert_called()


data_cpdir = ((True, True), (False, False))


@pytest.mark.parametrize('mpipe,expected', data_cpdir)
def test_33_copydir(futil, mocker, mpipe, expected):
    """Test33 FileUtil.copydir()."""
    mock_pipe = mocker.patch('udocker.utils.fileutil.Uprocess.pipe', return_value=mpipe)
    resout = futil.copydir('/dir')
    assert resout == expected
    mock_pipe.assert_called()


def test_34_cleanup(futil, mocker):
    """Test34 FileUtil.cleanup()."""
    mock_remove = mocker.patch.object(FileUtil, 'remove')
    futil.tmptrash = {'file1.txt': None, 'file2.txt': None}
    futil.cleanup()
    mock_remove.assert_called()


@pytest.mark.parametrize('misdir,expected', data_cpdir)
def test_35_isdir(futil, mocker, misdir, expected):
    """Test35 FileUtil.isdir()."""
    mock_isdir = mocker.patch('os.path.isdir', return_value=misdir)
    resout = futil.isdir()
    assert resout == expected
    mock_isdir.assert_called()


@pytest.mark.parametrize('misfile,expected', data_cpdir)
def test_36_isfile(futil, mocker, misfile, expected):
    """Test36 FileUtil.isfile()."""
    mock_isfile = mocker.patch('os.path.isfile', return_value=misfile)
    resout = futil.isfile()
    assert resout == expected
    mock_isfile.assert_called()


def test_37_size(futil, mocker):
    """Test37 FileUtil.size()."""
    mock_stat = mocker.patch('os.stat')
    mock_stat.return_value.st_size = 4321
    size = futil.size()
    assert size == 4321
    mock_stat.assert_called()


def test_38_size(futil, mocker):
    """Test38 FileUtil.size()."""
    mock_stat = mocker.patch('os.stat', side_effect = OSError('fail'))
    size = futil.size()
    assert size == -1


def test_39_getdata(futil, mocker):
    """Test39 FileUtil.getdata()."""
    mock_file = mocker.mock_open(read_data='qwerty')
    mocker.patch("builtins.open", mock_file)
    resout = futil.getdata()
    assert resout == 'qwerty'
    mock_file.assert_called()


def test_40_getdata(futil, mocker):
    """Test40 FileUtil.getdata()."""
    mock_file = mocker.mock_open()
    mock_file.side_effect = OSError     
    resout = futil.getdata()
    assert resout == ''


def test_41_get1stline(futil, mocker):
    """Test41 FileUtil.get1stline()."""
    mock_file = mocker.mock_open(read_data='qwerty')
    mocker.patch("builtins.open", mock_file)
    resout = futil.get1stline()
    assert resout == 'qwerty'
    mock_file.assert_called()


def test_42_get1stline(futil, mocker):
    """Test42 FileUtil.get1stline()."""
    mock_file = mocker.mock_open()
    mock_file.side_effect = OSError     
    resout = futil.get1stline()
    assert resout == ''


def test_43_putdata(futil, mocker):
    """Test43 FileUtil.putdata()."""
    mock_file = mocker.mock_open()
    mocker.patch("builtins.open", mock_file)
    resout = futil.putdata('qwerty')
    assert resout == 'qwerty'
    mock_file.assert_called()


def test_44_putdata(futil, mocker):
    """Test44 FileUtil.putdata()."""
    mock_file = mocker.mock_open()
    mock_file.side_effect = OSError
    resout = futil.putdata('qwerty')
    assert resout == ''


def test_45_getvalid_path(futil, mocker):
    """Test45 FileUtil.getvalid_path()."""
    mock_exists = mocker.patch('os.path.exists', return_value=True)
    resout = futil.getvalid_path()
    assert resout == '/dir/somefile'
    mock_exists.assert_called()


def test_46_getvalid_path(futil, mocker):
    """Test46 FileUtil.getvalid_path()."""
    mock_exists = mocker.patch('os.path.exists', side_effect=[False, True])
    mock_split = mocker.patch('os.path.split', return_value=('somefile', '/dir'))
    resout = futil.getvalid_path()
    assert resout == 'somefile'
    assert mock_exists.call_count == 2
    mock_split.assert_called()


def test_47__cont2host(futil, mocker):
    """Test47 FileUtil._cont2host()."""
    resout = futil._cont2host('', '/ROOT')
    assert resout == ''


def test_48__cont2host(futil, mocker):
    """Test48 FileUtil._cont2host()."""
    resout = futil._cont2host('/usr/bin', '/ROOT/usr/bin')
    assert resout == '/dir/somefile'


def test_49__cont2host(futil, mocker):
    """Test49 FileUtil._cont2host()."""
    vol = ['/home/user:/ROOT/home/user']   # var - volume
    mock_rpath = mocker.patch('os.path.realpath', return_value='/ROOT/usr/bin')
    mock_normp = mocker.patch('os.path.normpath', return_value='/ROOT/usr/bin')
    mock_islink = mocker.patch('os.path.islink', return_value=False)
    resout = futil._cont2host('/usr/bin', '/ROOT/usr/bin', vol)
    assert resout == '/ROOT/usr/bin'
    mock_rpath.assert_called()
    mock_normp.assert_called()
    mock_islink.assert_called()


# def test_50__cont2host(futil, mocker):
#     """Test50 FileUtil._cont2host()."""
#     mock_rpath = mocker.patch('os.path.realpath', side_effect=['/ROOT/usr/bin', '/ROOT/link'])
#     mock_normp = mocker.patch('os.path.normpath', return_value='/ROOT/usr/bin')
#     mock_islink = mocker.patch('os.path.islink', side_effect=[True, False])
#     mock_readlnk = mocker.patch('os.readlink', return_value='/ROOT/link')
#     resout = futil._cont2host('/usr/bin', '/ROOT/usr/bin')
#     assert resout == '/ROOT/link'
#     mock_rpath.assert_called()
#     mock_normp.assert_called()
#     mock_islink.assert_called()
#     mock_readlnk.assert_called()


def test_51_cont2host(futil, mocker):
    """Test51 FileUtil.cont2host()."""
    mock_c2h = mocker.patch.object(FileUtil, '_cont2host', return_value='/ROOT/dir')
    resout = futil.cont2host('/ROOT/dir')
    assert resout == '/ROOT/dir'
    mock_c2h.assert_called()


def test_52__find_exec(futil, mocker):
    """Test52 FileUtil._find_exec()."""
    resout = futil._find_exec('')
    assert resout == ''


def test_53__find_exec(futil, mocker):
    """Test53 FileUtil._find_exec()."""
    mock_c2h = mocker.patch.object(FileUtil, '_cont2host',
                                   side_effect=['/ROOT/usr/bin', '/ROOT', '/ROOT'])
    mock_isfile = mocker.patch('os.path.isfile', side_effect=[False, False, True])
    mock_access = mocker.patch('os.access', side_effect=[True, True, True])
    resout = futil._find_exec(['/usr/bin', '.', '..'], '/ROOT')
    assert resout == '../somefile'
    assert mock_isfile.call_count == 3
    assert mock_access.call_count == 1


def test_54_find_exec(futil, mocker):
    """Test54 FileUtil.find_exec()."""
    mock_findexe = mocker.patch.object(FileUtil, '_find_exec', return_value='/bin/ls')
    resout = futil.find_exec("/bin", "", "", ".", False)
    assert resout == '/bin/ls'
    mock_findexe.assert_called()


def test_55_rename(futil, mocker):
    """Test55 FileUtil.rename()."""
    mock_rename = mocker.patch('os.rename')
    resout = futil.rename("somefile")
    assert resout
    mock_rename.assert_called()


def test_56_rename(futil, mocker):
    """Test56 FileUtil.rename()."""
    mock_rename = mocker.patch('os.rename', side_effect=OSError('fail'))
    resout = futil.rename("somefile")
    assert not resout
    mock_rename.assert_called()



# # def test_33__stream2file(self):
# #     """Test33 FileUtil._stream2file()."""

# # def test_34__file2stream(self):
# #     """Test34 FileUtil._file2stream()."""

# # def test_35__file2file(self):
# #     """Test35 FileUtil._file2file()."""

# @patch('udocker.utils.fileutil.os.path.abspath')
# @patch('udocker.utils.fileutil.os.path.basename')
# @patch.object(FileUtil, '_register_prefix')
# def test_36_copyto(self, mock_regpre, mock_base, mock_absp):
#     """Test36 FileUtil.copyto()."""
#     mock_regpre.return_value = None
#     mock_base.return_value = 'filename.txt'
#     mock_absp.return_value = '/tmp/filename.txt'
#     with patch(BUILTINS + '.open', mock_open()):
#         status = FileUtil("source").copyto("dest")
#         self.assertTrue(status)

#         status = FileUtil("source").copyto("dest", "w")
#         self.assertTrue(status)

#         status = FileUtil("source").copyto("dest", "a")
#         self.assertTrue(status)

# @patch('udocker.utils.fileutil.os.path.exists')
# @patch('udocker.utils.fileutil.os.path.abspath')
# @patch('udocker.utils.fileutil.os.path.basename')
# @patch.object(FileUtil, '_register_prefix')
# def test_37_find_file_in_dir(self, mock_regpre, mock_base, mock_absp, mock_exists):
#     """Test37 FileUtil.find_file_in_dir()."""
#     mock_regpre.return_value = None
#     mock_base.return_value = 'filename.txt'
#     mock_absp.return_value = '/dir'
#     file_list = []
#     status = FileUtil("/dir").find_file_in_dir(file_list)
#     self.assertEqual(status, "")

#     file_list = ["F1", "F2"]
#     mock_exists.side_effect = [False, False]
#     status = FileUtil("/dir").find_file_in_dir(file_list)
#     self.assertEqual(status, "")

#     file_list = ["F1", "F2"]
#     mock_exists.side_effect = [False, True]
#     status = FileUtil("/dir").find_file_in_dir(file_list)
#     self.assertEqual(status, "/dir/F2")

# @patch('udocker.utils.fileutil.stat')
# @patch('udocker.utils.fileutil.os.stat')
# @patch('udocker.utils.fileutil.os.symlink')
# @patch('udocker.utils.fileutil.os.remove')
# @patch('udocker.utils.fileutil.os.chmod')
# @patch('udocker.utils.fileutil.os.access')
# @patch('udocker.utils.fileutil.os.path.realpath')
# @patch('udocker.utils.fileutil.os.path.abspath')
# @patch('udocker.utils.fileutil.os.path.basename')
# @patch.object(FileUtil, '_register_prefix')
# def test_38__link_change_apply(self, mock_regpre, mock_base, mock_absp, mock_realpath,
#                                 mock_access, mock_chmod, mock_remove, mock_symlink,
#                                 mock_osstat, mock_stat):
#     """Test38 FileUtil._link_change_apply()."""
#     mock_regpre.return_value = None
#     mock_chmod.return_value = None
#     mock_base.return_value = 'filename.txt'
#     mock_absp.return_value = '/tmp/filename.txt'
#     mock_realpath.return_value = "/HOST/DIR"
#     mock_access.return_value = True
#     futil = FileUtil("/con")
#     futil._link_change_apply("/con/lnk_new", "/con/lnk", False)
#     self.assertTrue(mock_remove.called)
#     self.assertTrue(mock_symlink.called)

#     mock_regpre.return_value = None
#     mock_base.return_value = 'filename.txt'
#     mock_absp.return_value = '/tmp/filename.txt'
#     mock_realpath.return_value = "/HOST/DIR"
#     mock_access.return_value = False
#     mock_chmod.side_effect = [None, None]
#     mock_remove.return_value = None
#     mock_symlink.return_value = None
#     mock_osstat.return_value.st_mode = None
#     mock_stat.return_value = None
#     mock_realpath.return_value = "/HOST/DIR"
#     futil = FileUtil("/con")
#     futil._link_change_apply("/con/lnk_new", "/con/lnk", True)
#     self.assertTrue(mock_chmod.call_count, 2)
#     self.assertTrue(mock_remove.called)
#     self.assertTrue(mock_symlink.called)

# @patch('udocker.utils.fileutil.os.readlink')
# @patch.object(FileUtil, '_link_change_apply', return_value=None)
# @patch('udocker.utils.fileutil.os.path.abspath')
# @patch('udocker.utils.fileutil.os.path.basename')
# @patch.object(FileUtil, '_register_prefix')
# def test_39__link_set(self, mock_regpre, mock_base, mock_absp, mock_lnchange, mock_readlink):
#     """Test39 FileUtil._link_set()."""
#     mock_regpre.return_value = None
#     mock_base.return_value = 'filename.txt'
#     mock_absp.return_value = '/tmp/filename.txt'
#     mock_readlink.return_value = "X"
#     futil = FileUtil("/con")
#     status = futil._link_set("/con/lnk", "", "/con", False)
#     self.assertFalse(status)

#     mock_readlink.return_value = "/con"
#     futil = FileUtil("/con")
#     status = futil._link_set("/con/lnk", "", "/con", False)
#     self.assertFalse(status)

#     mock_readlink.return_value = "/HOST/DIR"
#     futil = FileUtil("/con")
#     status = futil._link_set("/con/lnk", "", "/con", False)
#     self.assertTrue(mock_lnchange.called)
#     self.assertTrue(status)

#     mock_readlink.return_value = "/HOST/DIR"
#     futil = FileUtil("/con")
#     status = futil._link_set("/con/lnk", "", "/con", True)
#     self.assertTrue(mock_lnchange.called)
#     self.assertTrue(status)

#     mock_readlink.return_value = "/HOST/DIR"
#     futil = FileUtil("/con")
#     status = futil._link_set("/con/lnk", "", "/con", True)
#     self.assertTrue(mock_lnchange.called)
#     self.assertTrue(status)

# @patch('udocker.utils.fileutil.os.readlink')
# @patch.object(FileUtil, '_link_change_apply', return_value=None)
# @patch('udocker.utils.fileutil.os.path.abspath')
# @patch('udocker.utils.fileutil.os.path.basename')
# @patch.object(FileUtil, '_register_prefix')
# def test_40__link_restore(self, mock_regpre, mock_base, mock_absp, mock_lnchange, mock_rlink):
#     """Test40 FileUtil._link_restore()."""
#     mock_regpre.return_value = None
#     mock_base.return_value = 'filename.txt'
#     mock_absp.return_value = '/tmp/filename.txt'
#     mock_rlink.return_value = "/con/AAA"
#     futil = FileUtil("/con")
#     status = futil._link_restore("/con/lnk", "/con", "/root", False)
#     self.assertTrue(status)

#     mock_rlink.return_value = "/con/AAA"
#     futil = FileUtil("/con")
#     status = futil._link_restore("/con/lnk", "/con", "/root", False)
#     self.assertTrue(mock_lnchange.called)
#     self.assertTrue(status)

#     mock_rlink.return_value = "/root/BBB"
#     futil = FileUtil("/con")
#     status = futil._link_restore("/con/lnk", "/con", "/root", False)
#     self.assertTrue(mock_lnchange.called)
#     self.assertTrue(status)

#     mock_rlink.return_value = "/XXX"
#     futil = FileUtil("/con")
#     status = futil._link_restore("/con/lnk", "/con", "/root", False)
#     self.assertTrue(mock_lnchange.called)
#     self.assertFalse(status)

#     mock_rlink.return_value = "/root/BBB"
#     futil = FileUtil("/con")
#     status = futil._link_restore("/con/lnk", "/con", "/root", True)
#     self.assertTrue(mock_lnchange.called)
#     self.assertTrue(status)

#     mock_rlink.return_value = "/root/BBB"
#     futil = FileUtil("/con")
#     status = futil._link_restore("/con/lnk", "", "/root", True)
#     self.assertTrue(mock_lnchange.called)
#     self.assertTrue(status)

# @patch.object(FileUtil, '_link_restore')
# @patch.object(FileUtil, '_link_set')
# @patch.object(FileUtil, '_is_safe_prefix')
# @patch('udocker.utils.fileutil.os.lstat')
# @patch('udocker.utils.fileutil.os.path.islink')
# @patch('udocker.utils.fileutil.os.walk')
# @patch('udocker.utils.fileutil.os.path.realpath')
# @patch('udocker.utils.fileutil.os.path.abspath')
# @patch('udocker.utils.fileutil.os.path.basename')
# @patch.object(FileUtil, '_register_prefix')
# def test_41_links_conv(self, mock_regpre, mock_base, mock_absp, mock_realpath, mock_walk,
#                         mock_islink, mock_lstat, mock_is_safe_prefix, mock_link_set,
#                         mock_link_restore):
#     """Test41 FileUtil.links_conv()."""
#     mock_regpre.return_value = None
#     mock_base.return_value = 'filename.txt'
#     mock_absp.return_value = '/tmp/filename.txt'
#     mock_realpath.return_value = "/ROOT"
#     mock_is_safe_prefix.return_value = False
#     futil = FileUtil("/ROOT")
#     status = futil.links_conv(False, True, "")
#     self.assertEqual(status, None)

#     mock_realpath.return_value = "/ROOT"
#     mock_is_safe_prefix.return_value = True
#     mock_walk.return_value = []
#     mock_islink.return_value = True
#     futil = FileUtil("/ROOT")
#     status = futil.links_conv(False, True, "")
#     self.assertEqual(status, [])

#     mock_realpath.return_value = "/ROOT"
#     mock_is_safe_prefix.return_value = True
#     mock_walk.return_value = [("/", [], []), ]
#     futil = FileUtil("/ROOT")
#     status = futil.links_conv(False, True, "")
#     self.assertEqual(status, [])

#     mock_realpath.return_value = "/ROOT"
#     mock_is_safe_prefix.return_value = True
#     mock_islink = False
#     mock_walk.return_value = [("/", [], ["F1", "F2"]), ]
#     futil = FileUtil("/ROOT")
#     status = futil.links_conv(False, True, "")
#     self.assertEqual(status, [])

#     mock_realpath.return_value = "/ROOT"
#     mock_is_safe_prefix.return_value = True
#     mock_islink = True
#     mock_lstat.return_value.st_uid = 1
#     Config().conf['uid'] = 0
#     mock_walk.return_value = [("/", [], ["F1", "F2"]), ]
#     futil = FileUtil("/ROOT")
#     status = futil.links_conv(False, True, "")
#     self.assertEqual(status, [])

#     mock_realpath.return_value = "/ROOT"
#     mock_is_safe_prefix.return_value = True
#     mock_islink = True
#     mock_lstat.return_value.st_uid = 1
#     mock_link_set.reset_mock()
#     mock_link_restore.reset_mock()
#     Config().conf['uid'] = 1
#     mock_walk.return_value = [("/", [], ["F1", "F2"]), ]
#     futil = FileUtil("/ROOT")
#     status = futil.links_conv(False, True, "")
#     self.assertFalse(mock_link_restore.called)

#     mock_realpath.return_value = "/ROOT"
#     mock_is_safe_prefix.return_value = True
#     mock_islink = True
#     mock_lstat.return_value.st_uid = 1
#     mock_link_set.reset_mock()
#     mock_link_restore.reset_mock()
#     Config().conf['uid'] = 1
#     mock_walk.return_value = [("/", [], ["F1", "F2"]), ]
#     futil = FileUtil("/ROOT")
#     status = futil.links_conv(False, False, "")
#     self.assertFalse(mock_link_set.called)

# @patch('udocker.utils.fileutil.os.path.isdir')
# @patch('udocker.utils.fileutil.os.listdir')
# @patch('udocker.utils.fileutil.os.path.dirname')
# @patch('udocker.utils.fileutil.os.path.abspath')
# @patch('udocker.utils.fileutil.os.path.basename')
# @patch.object(FileUtil, '_register_prefix')
# def test_42_match(self, mock_regpre, mock_base, mock_absp, mock_dname, mock_lsdir, mock_isdir):
#     """Test42 FileUtil.match()."""
#     mock_regpre.return_value = None
#     mock_base.return_value = "/con/filename.txt"
#     mock_absp.return_value = "/con/filename.txt"
#     mock_dname.return_value = "/con/fil*"
#     mock_isdir.return_value = False
#     mock_lsdir.return_value = list()
#     futil = FileUtil("/con/filename.txt")
#     status = futil.match()
#     self.assertEqual(status, [])

#     mock_regpre.return_value = None
#     mock_base.return_value = "fil*"
#     mock_absp.return_value = "/con/filename*"
#     mock_dname.return_value = "/con"
#     mock_isdir.return_value = True
#     mock_lsdir.return_value = ["filename1", "filename2"]
#     futil = FileUtil("/con/filename*")
#     status = futil.match()
#     self.assertEqual(status, ["/con/filename1", "/con/filename2"])
