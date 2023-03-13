#!/usr/bin/env python
"""
udocker unit tests: ElfPatcher
"""
import pytest
from udocker.helper.elfpatcher import ElfPatcher
from udocker.config import Config


@pytest.fixture
def lrepo(mocker):
    mock_lrepo = mocker.patch('udocker.container.localrepo.LocalRepository')
    return mock_lrepo


@pytest.fixture
def hinfo(mocker):
    mock_hinfo = mocker.patch('udocker.helper.elfpatcher.HostInfo')
    return mock_hinfo


@pytest.fixture
def elfp(mocker, lrepo, hinfo):
    mock_path = mocker.patch('os.path.realpath', return_value='/some_contdir')
    hinfo.return_value.uid = '1000'
    return ElfPatcher(lrepo, '12345')


data_pelf = (('amd64', 'patchelf-x86_64'),
           ('i386', 'patchelf-x86'),
           ('arm64', 'patchelf-arm64'),
           ('arm', 'patchelf-arm'))


@pytest.mark.parametrize("parch,pexec", data_pelf)
def test_01_select_patchelf(mocker, elfp, hinfo, parch, pexec):
    """Test01 ElfPatcher().select_patchelf(). path elf exist"""
    hinfo.return_value.arch.return_value = parch
    mock_futil = mocker.patch('udocker.helper.elfpatcher.FileUtil')
    mock_futil.return_value.find_file_in_dir.return_value = pexec
    mock_exists = mocker.patch('os.path.exists', return_value=True)

    output = elfp.select_patchelf()
    assert output == pexec
    hinfo.return_value.arch.assert_called()
    mock_futil.assert_called()
    mock_futil.return_value.find_file_in_dir.assert_called()
    mock_exists.assert_called()


def test_02_select_patchelf(mocker, elfp, hinfo):
    """Test02 ElfPatcher().select_patchelf(). path elf not exist"""
    hinfo.return_value.arch.return_value = 'amd64'
    mock_futil = mocker.patch('udocker.helper.elfpatcher.FileUtil')
    mock_futil.return_value.find_file_in_dir.return_value = ''
    mock_exists = mocker.patch('os.path.exists', return_value=False)
    mock_logerr = mocker.patch('udocker.LOG.error')
    mock_sysexit = mocker.patch('sys.exit', return_value=1)

    output = elfp.select_patchelf()
    assert output == ''
    hinfo.return_value.arch.assert_called()
    mock_futil.assert_called()
    mock_futil.return_value.find_file_in_dir.assert_called()
    mock_exists.assert_called()
    mock_logerr.assert_called()
    mock_sysexit.assert_called()


def test_03__replace(elfp):
    """Test03 ElfPatcher()._replace."""
    output = elfp._replace(("#f", "ls"), "/bin/")
    assert output == ["/bin/", "ls"]


def test_04__walk_fs(mocker, elfp):
    """Test04 ElfPatcher()._walk_fs()."""
    mock_walk = mocker.patch('os.walk', return_value=[("/tmp", [], ["f1"])])
    elfp._uid = 0
    mock_islink = mocker.patch('os.path.islink', return_value=False)
    mock_stat = mocker.patch('os.stat')
    mock_stat.return_value.st_uid = 1000

    status = elfp._walk_fs("cmd", "/tmp", elfp.ABORT_ON_ERROR)
    assert status == ''
    mock_walk.assert_called()
    assert mock_islink.call_count == 1
    mock_stat.assert_called()


def test_05__walk_fs(mocker, elfp):
    """Test05 ElfPatcher()._walk_fs()."""
    mock_walk = mocker.patch('os.walk', return_value=[("/tmp", [], ["f1"])])
    elfp._uid = 1000
    mock_islink = mocker.patch('os.path.islink', return_value=False)
    mock_stat = mocker.patch('os.stat')
    mock_stat.return_value.st_uid = 1000
    mock_access = mocker.patch('os.access', return_value=True)
    mock_uprocout = mocker.patch('udocker.helper.elfpatcher.Uprocess.get_output',
                                 return_value='someout')

    status = elfp._walk_fs("cmd", "/tmp", elfp.BIN)
    assert status == 'someout'
    mock_walk.assert_called()
    mock_islink.assert_called()
    mock_stat.assert_called()
    mock_access.assert_called()
    mock_uprocout.assert_called()


def test_06__walk_fs(mocker, elfp):
    """Test06 ElfPatcher()._walk_fs()."""
    mock_walk = mocker.patch('os.walk', return_value=[("/tmp", [], ["f1"])])
    elfp._uid = 1000
    mock_islink = mocker.patch('os.path.islink', return_value=False)
    mock_stat = mocker.patch('os.stat')
    mock_stat.return_value.st_uid = 1000

    status = elfp._walk_fs("cmd", "/tmp", elfp.ABORT_ON_ERROR)
    assert status == ''
    mock_walk.assert_called()
    mock_islink.assert_called()
    mock_stat.assert_called()


def test_07__walk_fs(mocker, elfp):
    """Test07 ElfPatcher()._walk_fs()."""
    mock_walk = mocker.patch('os.walk', return_value=[("/tmp", [], ["f1"])])
    elfp._uid = 1000
    mock_islink = mocker.patch('os.path.islink', return_value=False)
    mock_stat = mocker.patch('os.stat')
    mock_stat.return_value.st_uid = 1000

    status = elfp._walk_fs("cmd", "/tmp", elfp.ONE_SUCCESS)
    assert status == ''
    mock_walk.assert_called()
    mock_islink.assert_called()
    mock_stat.assert_called()


def test_08__walk_fs(mocker, elfp):
    """Test08 ElfPatcher()._walk_fs()."""
    mock_walk = mocker.patch('os.walk', return_value=[("/tmp", [], ["f1"])])
    elfp._uid = 1000
    mock_islink = mocker.patch('os.path.islink', return_value=False)
    mock_stat = mocker.patch('os.stat')
    mock_stat.return_value.st_uid = 1000

    status = elfp._walk_fs("cmd", "/tmp", elfp.ONE_OUTPUT)
    assert status == ''
    mock_walk.assert_called()
    mock_islink.assert_called()
    mock_stat.assert_called()


data_guess = (('', ''),
              ('ld.so', 'ld.so'))


@pytest.mark.parametrize("pwalk,pout", data_guess)
def test_09_guess_elf_loader(mocker, elfp, pwalk, pout):
    """Test09 ElfPatcher().guess_elf_loader()."""
    mock_spelf = mocker.patch.object(ElfPatcher, 'select_patchelf', return_value="ld.so")
    mock_walk = mocker.patch.object(ElfPatcher, '_walk_fs', return_value=pwalk)

    out = elfp.guess_elf_loader()
    assert out == pout
    mock_spelf.assert_called()
    mock_walk.assert_called()


# Tuple is (os.path.exists, <return value AND expected output>,
#           call count FileUtil.getdata, call count of guess_elf_loader, call count of putdata)
data_get_load = ((True, 'ld.so', 1, 0, 0),
                 (False, 'ld.so', 0, 1, 1))


@pytest.mark.parametrize("pexists,expected,getdata_count,guess_count,put_count", data_get_load)
def test_10_get_original_loader(mocker, elfp, pexists, expected, getdata_count,
                                guess_count, put_count):
    """Test06 ElfPatcher().get_original_loader()."""
    mock_exists = mocker.patch('os.path.exists', return_value=pexists)
    mock_getdata = mocker.patch('udocker.helper.elfpatcher.FileUtil.getdata', return_value=expected)
    mock_guess = mocker.patch.object(ElfPatcher, 'guess_elf_loader', return_value=expected)
    mock_putdata = mocker.patch('udocker.helper.elfpatcher.FileUtil.putdata', return_value=expected)

    out = elfp.get_original_loader()
    assert out == expected
    mock_exists.assert_called()
    assert mock_getdata.call_count == getdata_count
    assert mock_guess.call_count == guess_count
    assert mock_putdata.call_count == put_count


# Tuple is (get_original_loader, expected output, return value path.exist, call count path.exists)
data_get_load = (('', '', False, 0),
                 ('ld.so', '', False, 1),
                 ('ld.so', '/some_contdir/ROOT/ld.so', True, 1))


@pytest.mark.parametrize("get_loader,expected,pexist,pexist_count", data_get_load)
def test_11_get_container_loader(mocker, elfp, get_loader, expected, pexist, pexist_count):
    """Test1 ElfPatcher().get_container_loader()."""
    mock_gol = mocker.patch.object(ElfPatcher, 'get_original_loader', return_value=get_loader)
    mock_exists = mocker.patch('os.path.exists', return_value=pexist)

    out = elfp.get_container_loader()
    assert out == expected
    mock_gol.assert_called()
    assert mock_exists.call_count == pexist_count


# Tuple is (FileUtil.getdata return value, expected output)
data_lpath = (('', ''),
              ('  withspaces', 'withspaces'),
              ('nospaces', 'nospaces'))


@pytest.mark.parametrize("getdata,expected", data_lpath)
def test_12_get_patch_last_path(mocker, elfp, getdata, expected):
    """Test12 ElfPatcher().get_patch_last_path()."""
    mock_getdata = mocker.patch('udocker.helper.elfpatcher.FileUtil.getdata', return_value=getdata)

    out = elfp.get_patch_last_path()
    assert out == expected
    assert mock_getdata.call_count == 1


# Tuple is (get_patch_last_path return value, expected output)
data_contpath = (('', True),
                 ('lastpath', False))


@pytest.mark.parametrize("getlpath,expected", data_contpath)
def test_13_get_patch_last_path(mocker, elfp, getlpath, expected):
    """Test13 ElfPatcher().check_container_path()."""
    mock_lpath = mocker.patch.object(ElfPatcher, 'get_patch_last_path', return_value=getlpath)

    out = elfp.check_container_path()
    assert out == expected
    mock_lpath.assert_called()


data_ltime = (('30', '30'),
              ('aa', '0'))


@pytest.mark.parametrize("getdata,expected", data_ltime)
def test_14_get_patch_last_time(mocker, elfp, getdata, expected):
    """Test14 ElfPatcher().get_patch_last_time()."""
    mock_getdata = mocker.patch('udocker.helper.elfpatcher.FileUtil.getdata', return_value=getdata)

    out = elfp.get_patch_last_time()
    assert out == expected
    mock_getdata.assert_called()


def test_15_patch_binaries(mocker, elfp):
    """Test15 ElfPatcher().patch_binaries()."""
    mock_chkcont = mocker.patch.object(ElfPatcher, 'check_container_path', return_value=False)
    mock_restbin = mocker.patch.object(ElfPatcher, 'restore_binaries')
    mock_select = mocker.patch.object(ElfPatcher, 'select_patchelf', return_value="patchelf-arm")
    mock_gcl = mocker.patch.object(ElfPatcher, 'get_container_loader', return_value="/usr/bin/ld")
    mock_walk = mocker.patch.object(ElfPatcher, '_walk_fs', return_value=True)
    mock_guess = mocker.patch.object(ElfPatcher, 'guess_elf_loader', return_value="/usr/bin/ld")
    mock_time = mocker.patch('time.time')
    mock_putdata = mocker.patch('udocker.helper.elfpatcher.FileUtil.putdata',
                                side_effect=["10", "/tmp"])

    assert elfp.patch_binaries()
    mock_chkcont.assert_called()
    mock_restbin.assert_called()
    mock_select.assert_called()
    mock_gcl.assert_called()
    mock_walk.assert_called()
    mock_guess.assert_called()
    mock_time.assert_called()
    assert mock_putdata.call_count == 2


def test_16_patch_binaries(mocker, elfp):
    """Test16 ElfPatcher().patch_binaries()."""
    mock_chkcont = mocker.patch.object(ElfPatcher, 'check_container_path', return_value=False)
    mock_restbin = mocker.patch.object(ElfPatcher, 'restore_binaries')
    mock_select = mocker.patch.object(ElfPatcher, 'select_patchelf', return_value="patchelf-arm")
    mock_gcl = mocker.patch.object(ElfPatcher, 'get_container_loader', return_value="/usr/bin/ld1")
    mock_walk = mocker.patch.object(ElfPatcher, '_walk_fs', return_value=True)
    mock_guess = mocker.patch.object(ElfPatcher, 'guess_elf_loader', return_value="/usr/bin/ld2")
    mock_time = mocker.patch('time.time')
    mock_putdata = mocker.patch('udocker.helper.elfpatcher.FileUtil.putdata')

    assert not elfp.patch_binaries()
    mock_chkcont.assert_called()
    mock_restbin.assert_called()
    mock_select.assert_called()
    mock_gcl.assert_called()
    mock_walk.assert_called()
    mock_guess.assert_called()
    mock_time.assert_not_called()
    mock_putdata.assert_not_called()


data_restbin = (('ld1', '', 'ld1', 2, True),
                ('ld1', '/lib', 'ld1', 2, True),
                ('ld1', '/lib', 'ld2', 0, False))


@pytest.mark.parametrize("gol,lpath,gelfload,count_futilrm,expected", data_restbin)
def test_17_restore_binaries(mocker, elfp, gol, lpath, gelfload, count_futilrm, expected):
    """Test17 ElfPatcher().restore_binaries()."""
    mock_select = mocker.patch.object(ElfPatcher, 'select_patchelf', return_value="patchelf-arm")
    mock_gol = mocker.patch.object(ElfPatcher, 'get_original_loader', return_value=gol)
    mock_lpath = mocker.patch.object(ElfPatcher, 'get_patch_last_path', return_value=lpath)
    mock_walk = mocker.patch.object(ElfPatcher, '_walk_fs')
    mock_guess = mocker.patch.object(ElfPatcher, 'guess_elf_loader', return_value=gelfload)
    mock_rm = mocker.patch('udocker.helper.elfpatcher.FileUtil.remove', side_effect=[True, True])

    out = elfp.restore_binaries()
    assert out == expected
    mock_select.assert_called()
    mock_gol.assert_called()
    mock_lpath.assert_called()
    mock_walk.assert_called()
    mock_guess.assert_called()
    assert mock_rm.call_count == count_futilrm


USRENC = "\x00/usr".encode()
LIBENC = "\x00/lib".encode()
data_pld = ((-1, False, 1, [USRENC, LIBENC], 0, False, 0, None, False),
            (-1, True, 1, [False, False], 2, False, 0, None, False),
            (10, False, 0, [USRENC, LIBENC], 1, True, 1, None, True),
            (10, False, 0, [USRENC, LIBENC], 1, True, 1, 'patchelf-amd64', True))


@pytest.mark.parametrize("retsize,retcp,cnt_call,side_get,cnt_get,retput,cnt_put,out_elf,expected",
                         data_pld)
def test_18_patch_ld(mocker, elfp, retsize, retcp, cnt_call, side_get, cnt_get, retput, cnt_put,
                     out_elf, expected):
    """Test18 ElfPatcher().patch_ld()."""
    mock_gcl = mocker.patch.object(ElfPatcher, 'get_container_loader')
    mock_size = mocker.patch('udocker.helper.elfpatcher.FileUtil.size', return_value=retsize)
    mock_copyto = mocker.patch('udocker.helper.elfpatcher.FileUtil.copyto', return_value=retcp)
    mock_getdata = mocker.patch('udocker.helper.elfpatcher.FileUtil.getdata', side_effect=side_get)
    mock_putdata = mocker.patch('udocker.helper.elfpatcher.FileUtil.putdata', return_value=retput)

    out = elfp.patch_ld(out_elf)
    assert out == expected
    mock_gcl.assert_called()
    mock_size.assert_called()
    assert mock_copyto.call_count == cnt_call
    assert mock_getdata.call_count == cnt_get
    assert mock_putdata.call_count == cnt_put


data_restld = ((-1, False, 0, 1, False),
               (10, False, 1, 1, False),
               (10, True, 1, 0, True))


@pytest.mark.parametrize("retsize,retcp,cnt_cp,cnt_log,expected", data_restld)
def test_19_restore_ld(mocker, elfp, retsize, retcp, cnt_cp, cnt_log, expected):
    """Test19 ElfPatcher().restore_ld()."""
    mock_gcl = mocker.patch.object(ElfPatcher, 'get_container_loader')
    mock_size = mocker.patch('udocker.helper.elfpatcher.FileUtil.size', return_value=retsize)
    mock_copyto = mocker.patch('udocker.helper.elfpatcher.FileUtil.copyto', return_value=retcp)
    mock_logerr = mocker.patch('udocker.helper.elfpatcher.LOG.error')

    out = elfp.restore_ld()
    assert out == expected
    mock_gcl.assert_called()
    mock_size.assert_called()
    assert mock_copyto.call_count == cnt_cp
    assert mock_logerr.call_count == cnt_log


UPOUT = ("ld.so.cache => /tmp/ROOT/etc/ld.so.cache\n"
         "ld.so.cache => /tmp/ROOT/etc/ld.so")

data_ldconf = (([], ['/ld.so.cache', '/ld.so'], 0, []),
               (UPOUT, ['/ld.so.cache', '/ld.so'], 2,
                ['/some_contdir/ROOT/ld.so.cache', '/some_contdir/ROOT/ld.so']))


@pytest.mark.parametrize("upout,side_dir,cnt_dir,expected", data_ldconf)
def test_20__get_ld_config(mocker, elfp, upout, side_dir, cnt_dir, expected):
    """Test20 ElfPatcher()._get_ld_config()."""
    mock_upout = mocker.patch('udocker.helper.elfpatcher.Uprocess.get_output', return_value=upout)
    mock_dir = mocker.patch('udocker.helper.elfpatcher.os.path.dirname', side_effect=side_dir)

    out = elfp._get_ld_config()
    assert out == expected
    mock_upout.assert_called()
    assert mock_dir.call_count == cnt_dir


def test_21__find_ld_libdirs(mocker, elfp):
    """Test21 ElfPatcher()._find_ld_libdirs(). search for library directories in container"""
    mock_walk = mocker.patch('udocker.helper.elfpatcher.os.walk',
                             return_value=[("/lib", ["dir"], ["lib1.so.0", "lib2.so.0"]), ])
    mock_access = mocker.patch('udocker.helper.elfpatcher.os.access', side_effect=[False, True])
    mock_isfile = mocker.patch('udocker.helper.elfpatcher.os.path.isfile', return_value=True)

    out = elfp._find_ld_libdirs()
    assert out == ["/lib"]
    mock_walk.assert_called()
    assert mock_access.call_count == 2
    mock_isfile.assert_called()


data_ldlib = ((False, True, 1, 0, 0, 1, ['/lib', '/usr/lib']),
              (True, True, 0, 1, 1, 0, ['/lib', '/usr/lib']),
              (False, False, 1, 1, 1, 0, ['/lib', '/usr/lib']))


@pytest.mark.parametrize("pin,retexist,cnt_exist,cnt_find,cnt_put,cnt_get,expected", data_ldlib)
def test_22_get_ld_libdirs(mocker, elfp, pin, retexist, cnt_exist, cnt_find,
                           cnt_put, cnt_get, expected):
    """Test22 ElfPatcher().get_ld_libdirs()."""
    mock_exists = mocker.patch('udocker.helper.elfpatcher.os.path.exists', return_value=retexist)
    mock_findlib = mocker.patch.object(ElfPatcher, '_find_ld_libdirs',
                                       return_value=['/lib', '/usr/lib'])
    mock_pudata = mocker.patch('udocker.helper.elfpatcher.FileUtil.putdata')
    mock_getdata = mocker.patch('udocker.helper.elfpatcher.FileUtil.getdata', 
                                return_value='/lib:/usr/lib')

    out = elfp.get_ld_libdirs(pin)
    assert out == expected
    assert mock_exists.call_count == cnt_exist
    assert mock_findlib.call_count == cnt_find
    assert mock_pudata.call_count == cnt_put
    assert mock_getdata.call_count == cnt_get


def test_23_get_ld_library_path(mocker, elfp):
    """Test23 ElfPatcher().get_ld_library_path()."""
    Config().conf['lib_dirs_list_essential'] = ("/lib64", )
    mock_ldconf = mocker.patch.object(ElfPatcher, '_get_ld_config',
                                      return_value=["/some_contdir/ROOT/lib"])
    mock_ldlib = mocker.patch.object(ElfPatcher, 'get_ld_libdirs',
                                     return_value=["/some_contdir/ROOT/usr/lib"])

    out = elfp.get_ld_library_path()
    assert out == "/some_contdir/ROOT//lib64:/some_contdir/ROOT/lib:/some_contdir/ROOT/usr/lib:."
    mock_ldconf.assert_called()
    mock_ldlib.assert_called()
