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


# @patch('udocker.helper.elfpatcher.os.path.realpath')
# @patch.object(ElfPatcher, '_walk_fs')
# @patch.object(ElfPatcher, 'select_patchelf')
# def test_05_guess_elf_loader(self, mock_spelf, mock_walk, mock_path):
#     """Test05 ElfPatcher().guess_elf_loader()."""
#     mock_spelf.return_value = "ld.so"
#     mock_walk.return_value = ""
#     mock_path.return_value = "/some_contdir"
#     elfp = ElfPatcher(self.local, self.contid)
#     self.assertEqual(elfp.guess_elf_loader(), "")

#     mock_walk.return_value = "ld.so"
#     mock_path.return_value = "/some_contdir"
#     elfp = ElfPatcher(self.local, self.contid)
#     self.assertEqual(elfp.guess_elf_loader(), "ld.so")

# @patch('udocker.helper.elfpatcher.os.path.realpath')
# @patch('udocker.helper.elfpatcher.os.path.exists')
# @patch('udocker.helper.elfpatcher.FileUtil.getdata')
# @patch('udocker.helper.elfpatcher.FileUtil.putdata')
# @patch.object(ElfPatcher, 'guess_elf_loader')
# def test_06_get_original_loader(self, mock_guess, mock_getdata,
#                                 mock_putdata, mock_exists, mock_path):
#     """Test06 ElfPatcher().get_original_loader()."""
#     mock_path.return_value = "/some_contdir"
#     mock_exists.return_value = False
#     mock_guess.return_value = "ld.so"
#     mock_getdata.return_value.strip.return_value = "ld.so"
#     mock_putdata.return_value = "ld.so"
#     elfp = ElfPatcher(self.local, self.contid)
#     status = elfp.get_original_loader()
#     self.assertEqual(status, "ld.so")

# @patch('udocker.helper.elfpatcher.os.path.realpath')
# @patch('udocker.helper.elfpatcher.os.path.exists')
# @patch.object(ElfPatcher, 'get_original_loader')
# def test_07_get_container_loader(self, mock_gol, mock_exists, mock_path):
#     """Test07 ElfPatcher().get_container_loader().
#     Get an absolute pathname to the container ld.so"""
#     mock_gol.return_value = ""
#     mock_path.return_value = "/some_contdir"
#     elfp = ElfPatcher(self.local, self.contid)
#     self.assertEqual(elfp.get_container_loader(), "")

#     mock_exists.return_value = True
#     mock_gol.return_value = "ld.so"
#     mock_path.return_value = "/some_contdir"
#     elfp = ElfPatcher(self.local, self.contid)
#     self.assertEqual(elfp.get_container_loader(), elfp._container_root + "/" + "ld.so")

# @patch('udocker.helper.elfpatcher.os.path.realpath')
# @patch('udocker.helper.elfpatcher.FileUtil.getdata')
# def test_08_get_patch_last_path(self, mock_getdata, mock_path):
#     """Test08 ElfPatcher().get_patch_last_path()."""
#     mock_getdata.return_value = ""
#     mock_path.return_value = "/some_contdir"
#     elfp = ElfPatcher(self.local, self.contid)
#     self.assertEqual(elfp.get_patch_last_path(), "")

#     mock_getdata.return_value = "/tmp"
#     mock_path.return_value = "/some_contdir"
#     elfp = ElfPatcher(self.local, self.contid)
#     self.assertEqual(elfp.get_patch_last_path(), "/tmp")

# @patch('udocker.helper.elfpatcher.os.path.realpath')
# @patch.object(ElfPatcher, 'get_patch_last_path')
# def test_09_check_container_path(self, mock_lpath, mock_path):
#     """Test09 ElfPatcher().check_container_path()."""
#     mock_lpath.return_value = ""
#     mock_path.return_value = "/some_contdir"
#     elfp = ElfPatcher(self.local, self.contid)
#     status = elfp.check_container_path()
#     self.assertTrue(status)

#     mock_lpath.return_value = "xxx"
#     mock_path.return_value = "/some_contdir"
#     elfp = ElfPatcher(self.local, self.contid)
#     status = elfp.check_container_path()
#     self.assertFalse(status)

# @patch('udocker.helper.elfpatcher.os.path.realpath')
# @patch('udocker.helper.elfpatcher.FileUtil.getdata')
# def test_10_get_patch_last_time(self, mock_getdata, mock_path):
#     """Test10 ElfPatcher().patch_last_time()."""
#     mock_getdata.return_value = "30"
#     mock_path.return_value = "/some_contdir"
#     elfp = ElfPatcher(self.local, self.contid)
#     self.assertEqual(elfp.get_patch_last_time(), "30")

# @patch('udocker.helper.elfpatcher.os.path.realpath')
# @patch('udocker.helper.elfpatcher.os.path.exists')
# @patch('udocker.helper.elfpatcher.FileUtil.putdata')
# @patch.object(ElfPatcher, '_walk_fs')
# @patch.object(ElfPatcher, 'guess_elf_loader')
# @patch.object(ElfPatcher, 'select_patchelf')
# @patch.object(ElfPatcher, 'get_container_loader')
# @patch.object(ElfPatcher, 'check_container_path')
# def test_11_patch_binaries(self, mock_chkcont, mock_gcl, mock_select, mock_guess, mock_walk,
#                             mock_putdata, mock_exists, mock_path):
#     """Test11 ElfPatcher().patch_binaries()."""
#     mock_exists.return_value = True
#     mock_chkcont.return_value = True
#     mock_walk.return_value = True
#     mock_gcl.return_value = "/usr/bin/ld"
#     mock_select.return_value = "runc-arm"
#     mock_putdata.side_effect = ["10", "/tmp"]
#     mock_guess.return_value = "/usr/bin/ld"
#     mock_path.return_value = "/some_contdir"
#     elfp = ElfPatcher(self.local, self.contid)
#     elfp._container_root = "/tmp/ROOT"
#     self.assertTrue(elfp.patch_binaries())

# @patch('udocker.helper.elfpatcher.os.path.realpath')
# @patch('udocker.helper.elfpatcher.FileUtil.remove')
# @patch.object(ElfPatcher, 'guess_elf_loader')
# @patch.object(ElfPatcher, '_walk_fs')
# @patch.object(ElfPatcher, 'get_patch_last_path')
# @patch.object(ElfPatcher, 'get_original_loader')
# @patch.object(ElfPatcher, 'select_patchelf')
# def test_12_restore_binaries(self, mock_select, mock_gol, mock_lpath, mock_walk, mock_guess,
#                                 mock_rm, mock_path):
#     """Test12 ElfPatcher().restore_binaries()."""
#     mock_select.return_value = "runc-arm"
#     mock_gol.return_value = "ld.so"
#     mock_lpath.return_value = "xxx"
#     mock_walk.return_value = ""
#     mock_guess.return_value = "ld.so"
#     mock_rm.return_value = True
#     mock_path.return_value = "/some_contdir"
#     elfp = ElfPatcher(self.local, self.contid)
#     elfp._container_root = "/tmp/ROOT"
#     self.assertTrue(elfp.restore_binaries())
#     self.assertTrue(mock_rm.called)

# @patch.object(ElfPatcher, 'get_container_loader')
# @patch('udocker.helper.elfpatcher.os.path.realpath')
# @patch('udocker.helper.elfpatcher.FileUtil.size')
# @patch('udocker.helper.elfpatcher.FileUtil.copyto')
# @patch('udocker.helper.elfpatcher.FileUtil.getdata')
# @patch('udocker.helper.elfpatcher.FileUtil.putdata')
# def test_13_patch_ld(self, mock_putdata, mock_getdata,
#                         mock_copyto, mock_size, mock_path, mock_gcl):
#     """Test13 ElfPatcher().patch_ld()."""
#     mock_size.return_value = -1
#     mock_putdata.return_value = False
#     mock_path.return_value = "/some_contdir"
#     mock_gcl.return_value = ""
#     elfp = ElfPatcher(self.local, self.contid)
#     self.assertFalse(elfp.patch_ld())

#     mock_size.return_value = 20
#     mock_copyto.return_value = False
#     mock_path.return_value = "/some_contdir"
#     mock_gcl.return_value = ""
#     elfp = ElfPatcher(self.local, self.contid)
#     self.assertFalse(elfp.patch_ld())

#     mock_size.return_value = 20
#     mock_copyto.return_value = True
#     mock_getdata.return_value = []
#     mock_path.return_value = "/some_contdir"
#     mock_gcl.return_value = ""
#     elfp = ElfPatcher(self.local, self.contid)
#     self.assertFalse(elfp.patch_ld())

#     mock_size.return_value = 20
#     mock_copyto.return_value = True
#     mock_getdata.return_value = []
#     mock_path.return_value = "/some_contdir"
#     mock_gcl.return_value = ""
#     elfp = ElfPatcher(self.local, self.contid)
#     self.assertFalse(elfp.patch_ld("OUTPUT_ELF"))

# @patch.object(ElfPatcher, 'get_container_loader')
# @patch('udocker.helper.elfpatcher.os.path.realpath')
# @patch('udocker.helper.elfpatcher.FileUtil.size')
# @patch('udocker.helper.elfpatcher.FileUtil.copyto')
# def test_14_restore_ld(self, mock_copyto, mock_size, mock_path, mock_gcl):
#     """Test14 ElfPatcher().restore_ld()."""
#     mock_size.return_value = -1
#     mock_path.return_value = "/some_contdir"
#     mock_gcl.return_value = ""
#     elfp = ElfPatcher(self.local, self.contid)
#     self.assertFalse(elfp.restore_ld())

#     mock_size.return_value = 20
#     mock_copyto.return_value = True
#     mock_path.return_value = "/some_contdir"
#     mock_gcl.return_value = ""
#     elfp = ElfPatcher(self.local, self.contid)
#     self.assertTrue(elfp.restore_ld())

# @patch('udocker.helper.elfpatcher.os.path.realpath')
# @patch('udocker.helper.elfpatcher.os.path.dirname')
# @patch('udocker.helper.elfpatcher.Uprocess.get_output')
# def test_15__get_ld_config(self, mock_upout, mock_dir, mock_path):
#     """Test15 ElfPatcher().get_ld_config()."""
#     mock_upout.return_value = []
#     mock_path.return_value = "/some_contdir"
#     elfp = ElfPatcher(self.local, self.contid)
#     status = elfp._get_ld_config()
#     self.assertEqual(status, [])

#     mock_upout.return_value = \
#         "ld.so.cache => /tmp/ROOT/etc/ld.so.cache\n" \
#         "ld.so.cache => /tmp/ROOT/etc/ld.so"
#     mock_dir.side_effect = ['/ld.so.cache', '/ld.so']
#     mock_path.return_value = "/some_contdir"
#     elfp = ElfPatcher(self.local, self.contid)
#     status = elfp._get_ld_config()
#     self.assertIsInstance(status, list)

# @patch('udocker.helper.elfpatcher.os.path.isfile')
# @patch('udocker.helper.elfpatcher.os.path.realpath')
# @patch('udocker.helper.elfpatcher.os.access')
# @patch('udocker.helper.elfpatcher.os.walk')
# def test_16__find_ld_libdirs(self, mock_walk, mock_access, mock_path, mock_isfile):
#     """Test16 ElfPatcher()._find_ld_libdirs().
#     search for library directories in container"""
#     mock_path.return_value = "/some_contdir"
#     elfp = ElfPatcher(self.local, self.contid)
#     status = elfp._find_ld_libdirs()
#     self.assertEqual(status, [])

#     mock_path.return_value = "/some_contdir"
#     mock_walk.return_value = [("libsome.so.0", ["dir"], ["libsome.so.0"]), ]
#     mock_access.return_value = True
#     mock_isfile.return_value = True
#     elfp = ElfPatcher(self.local, self.contid)
#     status = elfp._find_ld_libdirs()
#     self.assertEqual(status, ["libsome.so.0"])

# @patch('udocker.helper.elfpatcher.os.path.realpath')
# @patch.object(ElfPatcher, '_find_ld_libdirs')
# @patch('udocker.helper.elfpatcher.FileUtil.putdata')
# @patch('udocker.helper.elfpatcher.FileUtil.getdata')
# @patch('udocker.helper.elfpatcher.os.path.exists')
# def test_17_get_ld_libdirs(self, mock_exists, mock_getd, mock_pudata, mock_findlib, mock_path):
#     """Test17 ElfPatcher().get_ld_libdirs()."""
#     mock_exists.return_value = True
#     mock_getd.return_value = '/lib:/usr/lib'
#     mock_path.return_value = "/some_contdir"
#     elfp = ElfPatcher(self.local, self.contid)
#     status = elfp.get_ld_libdirs(False)
#     self.assertEqual(status, ['/lib', '/usr/lib'])

#     mock_exists.return_value = False
#     mock_pudata.return_value = '/lib:/usr/lib'
#     mock_findlib.return_value = ['/lib', '/usr/lib']
#     mock_path.return_value = "/some_contdir"
#     elfp = ElfPatcher(self.local, self.contid)
#     status = elfp.get_ld_libdirs(True)
#     self.assertEqual(status, ['/lib', '/usr/lib'])

# @patch('udocker.helper.elfpatcher.os.path.realpath')
# @patch.object(ElfPatcher, 'get_ld_libdirs')
# @patch.object(ElfPatcher, '_get_ld_config')
# def test_18_get_ld_library_path(self, mock_ldconf, mock_ldlib, mock_path):
#     """Test18 ElfPatcher().get_ld_library_path()."""
#     Config().conf['lib_dirs_list_essential'] = ""
#     mock_ldconf.return_value = ["/lib"]
#     mock_ldlib.return_value = ["/usr/lib"]
#     mock_path.return_value = "/some_contdir"
#     elfp = ElfPatcher(self.local, self.contid)
#     status = elfp.get_ld_library_path()
#     self.assertEqual(status, "/lib:/usr/lib:.")
