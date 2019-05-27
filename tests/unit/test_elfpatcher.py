#!/usr/bin/env python
"""
udocker unit tests: ElfPatcher
"""
import sys
from unittest import TestCase, main
try:
    from unittest.mock import Mock, MagicMock, patch, mock_open
except ImportError:
    from mock import Mock, MagicMock, patch, mock_open

sys.path.append('.')

from udocker.helper.elfpatcher import ElfPatcher
from udocker.config import Config
from udocker.container.localrepo import LocalRepository


class ElfPatcherTestCase(TestCase):
    """Test ElfPatcher"""

    def setUp(self):
        self.conf = Config().getconf()
        self.local = LocalRepository(self.conf)

    def tearDown(self):
        pass

    @patch('udocker.helper.elfpatcher.Msg')
    @patch('udocker.helper.elfpatcher.os.path')
    @patch('udocker.helper.elfpatcher.FileUtil.find_file_in_dir')
    def test_02_select_patchelf(self, mock_find, mock_path, mock_msg):
        """Test ElfPatcher().select_patchelf().

        Set patchelf executable."""

        container_id = "SOME-RANDOM-ID"
        # mock_arch.side_effect = ["arm", "amd64", "i386", "arm64"]
        self.conf["arch"] = "arm"
        mock_find.return_value = "runc-arm"
        elfp = ElfPatcher(self.conf, self.local, container_id)
        output = elfp.select_patchelf()
        self.assertEqual(output, "runc-arm")

        mock_find.return_value = ""
        with self.assertRaises(SystemExit) as epexpt:
            elfp = ElfPatcher(self.conf, self.local, container_id)
            elfp.select_patchelf()
        self.assertEqual(epexpt.exception.code, 1)

    # @patch('udocker.helper.elfpatcher.os.path.realpath')
    @patch('udocker.helper.elfpatcher.os.path.islink')
    @patch('udocker.helper.elfpatcher.os.stat')
    @patch('udocker.helper.elfpatcher.os.walk')
    @patch('udocker.helper.elfpatcher.os.access')
    def test_03__walk_fs(self, mock_access, mock_walk,
                         mock_stat, mock_islink):
        """Test ElfPatcher()._walk_fs().

        Execute a shell command over each executable file in a given dir_path.
        Action can be ABORT_ON_ERROR, return upon first success
        ONE_SUCCESS, or return upon the first non empty output. #f is the
        placeholder for the filename.
        """
        container_id = "SOME-RANDOM-ID"
        # mock_rpath.return_value = '/some/' + container_id
        mock_walk.return_value = [("/tmp", ["dir"], ["file"]), ]
        mock_islink.return_value = False
        mock_access.return_value = False
        mock_stat.st_uid = ""
        elfp = ElfPatcher(self.conf, self.local, container_id)
        status = elfp._walk_fs("cmd", "/tmp", elfp.BIN)
        self.assertFalse(status)

    @patch('udocker.helper.elfpatcher.os.path')
    @patch.object(ElfPatcher, '_walk_fs')
    @patch.object(ElfPatcher, 'select_patchelf')
    def test_04_guess_elf_loader(self, mock_spelf, mock_walk,
                                 mock_path):
        """Test ElfPatcher().guess_elf_loader().

        Search for executables and try to read the ld.so pathname."""
        container_id = "SOME-RANDOM-ID"
        mock_spelf.return_value = "ld.so"
        mock_walk.return_value = ""
        elfp = ElfPatcher(self.conf, self.local, container_id)
        self.assertEqual(elfp.guess_elf_loader(), "")

        mock_walk.return_value = "ld.so"
        elfp = ElfPatcher(self.conf, self.local, container_id)
        self.assertEqual(elfp.guess_elf_loader(), "ld.so")

    @patch('udocker.helper.elfpatcher.os.path')
    @patch('udocker.helper.elfpatcher.os.path.exists')
    @patch('udocker.helper.elfpatcher.FileUtil.getdata')
    @patch.object(ElfPatcher, 'guess_elf_loader')
    def test_05_get_original_loader(self, mock_guess, mock_futils,
                                    mock_exists, mock_path):
        """Test ElfPatcher().get_original_loader().

        Get the pathname of the original ld.so.
        """
        container_id = "SOME-RANDOM-ID"
        mock_exists.return_value = True
        mock_futils.return_value.strip.return_value = "ld.so"
        elfp = ElfPatcher(self.conf, self.local, container_id)
        self.assertEqual(elfp.get_original_loader(), "ld.so")

        mock_exists.return_value = False
        mock_guess.return_value = "ld.so"
        mock_futils.return_value.strip.return_value = "ld.so"
        elfp = ElfPatcher(self.conf, self.local, container_id)
        self.assertEqual(elfp.get_original_loader(), "ld.so")

    @patch('udocker.helper.elfpatcher.os.path')
    @patch('udocker.helper.elfpatcher.os.path.exists')
    @patch.object(ElfPatcher, 'get_original_loader')
    def test_06_get_container_loader(self, mock_gol, mock_exists, mock_path):
        """Test ElfPatcher().get_container_loader().

        Get an absolute pathname to the container ld.so"""
        container_id = "SOME-RANDOM-ID"
        mock_gol.return_value = ""
        elfp = ElfPatcher(self.conf, self.local, container_id)
        self.assertEqual(elfp.get_container_loader(), "")

        mock_exists.return_value = True
        mock_gol.return_value = "ld.so"
        elfp = ElfPatcher(self.conf, self.local, container_id)
        self.assertEqual(elfp.get_container_loader(),
                         elfp._container_root + "/" + "ld.so")

    @patch('udocker.helper.elfpatcher.os.path')
    @patch('udocker.helper.elfpatcher.os.path.exists')
    @patch('udocker.helper.elfpatcher.FileUtil.getdata')
    def test_07_get_patch_last_path(self, mock_getdata, mock_exists, mock_path):
        """Test ElfPatcher().get_patch_last_path().

        get last host pathname to the patched container."""
        container_id = "SOME-RANDOM-ID"
        mock_getdata.return_value = ""
        elfp = ElfPatcher(self.conf, self.local, container_id)
        self.assertEqual(elfp.get_patch_last_path(), "")

        mock_getdata.return_value = "/tmp"
        elfp = ElfPatcher(self.conf, self.local, container_id)
        self.assertEqual(elfp.get_patch_last_path(), "/tmp")

    @patch('udocker.helper.elfpatcher.os.path')
    @patch('udocker.helper.elfpatcher.os.path.exists')
    @patch.object(ElfPatcher, 'get_patch_last_path')
    @patch('udocker.helper.elfpatcher.Msg')
    def test_08_check_container_path(self, mock_msg, mock_lpath, mock_exists,
                                     mock_path):
        """Test ElfPatcher().check_container_path().

        verify if path to container is ok"""
        container_id = "SOME-RANDOM-ID"
        mock_lpath.return_value = ""
        elfp = ElfPatcher(self.conf, self.local, container_id)
        status = elfp.check_container_path()
        self.assertTrue(status)

        mock_lpath.return_value = "xxx"
        elfp = ElfPatcher(self.conf, self.local, container_id)
        status = elfp.check_container_path()
        self.assertFalse(status)

    @patch('udocker.helper.elfpatcher.os.path')
    @patch('udocker.helper.elfpatcher.os.path.exists')
    @patch('udocker.helper.elfpatcher.FileUtil.getdata')
    def test_09_get_patch_last_time(self, mock_getdata,
                                    mock_exists, mock_path):
        """Test ElfPatcher().patch_last_time().

        get time in seconds of last full patch of container"""
        container_id = "SOME-RANDOM-ID"
        mock_getdata.return_value = "30"
        elfp = ElfPatcher(self.conf, self.local, container_id)
        self.assertEqual(elfp.get_patch_last_time(), "30")

    @patch('udocker.helper.elfpatcher.os.path')
    @patch('udocker.helper.elfpatcher.os.path.exists')
    @patch('udocker.helper.elfpatcher.FileUtil.putdata')
    @patch.object(ElfPatcher, '_walk_fs')
    @patch.object(ElfPatcher, 'guess_elf_loader')
    @patch.object(ElfPatcher, 'select_patchelf')
    @patch.object(ElfPatcher, 'get_container_loader')
    @patch.object(ElfPatcher, 'check_container_path')
    def test_10_patch_binaries(self, mock_chkcont, mock_gcl, mock_select,
                               mock_guess, mock_walk, mock_putdata,
                               mock_exists, mock_path):
        """Test ElfPatcher().patch_binaries().

        Set all executables and libs to the ld.so absolute pathname"""
        container_id = "SOME-RANDOM-ID"
        mock_exists.return_value = True
        mock_chkcont.return_value = True
        mock_walk.return_value = True
        mock_gcl.return_value = "/usr/bin/ld"
        mock_select.return_value = "runc-arm"
        mock_putdata.side_effect = ["10", "/tmp"]
        mock_guess.return_value = "/usr/bin/ld"
        elfp = ElfPatcher(self.conf, self.local, container_id)
        elfp._container_root = "/tmp/ROOT"
        self.assertTrue(elfp.patch_binaries())

    # TODO: review this test
    # @patch('udocker.helper.elfpatcher.os.path')
    # @patch('udocker.helper.elfpatcher.os.path.exists')
    # @patch.object(ElfPatcher, 'guess_elf_loader')
    # @patch.object(ElfPatcher, 'select_patchelf')
    # @patch.object(ElfPatcher, 'get_container_loader')
    # def test_11_restore_binaries(self, mock_gcl, mock_select, mock_guess,
    #                              mock_exists, mock_path):
    #     """Test ElfPatcher().restore_binaries().
    #
    #     Restore all executables and libs to the original ld.so pathname"""
    #     container_id = "SOME-RANDOM-ID"
    #     mock_exists.return_value = True
    #     mock_gcl.return_value = "/usr/bin/ld"
    #     mock_select.return_value = "runc-arm"
    #     mock_guess.return_value = "/usr/bin/ld"
    #     elfp = ElfPatcher(self.conf, self.local, container_id)
    #     elfp._container_root = "/tmp/ROOT"
    #     self.assertTrue(elfp.restore_binaries())

    @patch('udocker.helper.elfpatcher.os.path')
    @patch('udocker.helper.elfpatcher.os.path.exists')
    @patch.object(ElfPatcher, 'get_container_loader')
    @patch('udocker.helper.elfpatcher.FileUtil.size')
    @patch('udocker.helper.elfpatcher.FileUtil.copyto')
    @patch('udocker.helper.elfpatcher.FileUtil.getdata')
    @patch('udocker.helper.elfpatcher.FileUtil.putdata')
    def test_12_patch_ld(self, mock_putdata, mock_getdata,
                         mock_copyto, mock_size,
                         mock_gcl,
                         mock_exists, mock_path):
        """Test ElfPatcher().patch_ld().

        Patch ld.so"""
        container_id = "SOME-RANDOM-ID"
        mock_size.return_value = -1
        mock_putdata.return_value = False
        elfp = ElfPatcher(self.conf, self.local, container_id)
        self.assertFalse(elfp.patch_ld())

        mock_size.return_value = 20
        mock_copyto.return_value = False
        elfp = ElfPatcher(self.conf, self.local, container_id)
        self.assertFalse(elfp.patch_ld())

        mock_size.return_value = 20
        mock_copyto.return_value = True
        mock_getdata.return_value = []
        elfp = ElfPatcher(self.conf, self.local, container_id)
        self.assertFalse(elfp.patch_ld())

        mock_size.return_value = 20
        mock_copyto.return_value = True
        mock_getdata.return_value = []
        elfp = ElfPatcher(self.conf, self.local, container_id)
        self.assertFalse(elfp.patch_ld("OUTPUT_ELF"))

    @patch('udocker.helper.elfpatcher.Msg')
    @patch('udocker.helper.elfpatcher.os.path')
    @patch('udocker.helper.elfpatcher.os.path.exists')
    @patch.object(ElfPatcher, 'get_container_loader')
    @patch('udocker.helper.elfpatcher.FileUtil.size')
    @patch('udocker.helper.elfpatcher.FileUtil.copyto')
    def test_13_restore_ld(self, mock_copyto, mock_size,
                           mock_gcl,
                           mock_exists, mock_path, mock_msg):
        """Test ElfPatcher().restore_ld().

        Restore ld.so"""
        container_id = "SOME-RANDOM-ID"
        mock_size.return_value = -1
        elfp = ElfPatcher(self.conf, self.local, container_id)
        self.assertFalse(elfp.restore_ld())

        mock_size.return_value = 20
        mock_copyto.return_value = True
        elfp = ElfPatcher(self.conf, self.local, container_id)
        self.assertTrue(elfp.restore_ld())

    @patch('udocker.helper.elfpatcher.os.path.dirname')
    @patch('udocker.helper.elfpatcher.os.path.exists')
    @patch('udocker.helper.elfpatcher.Uprocess.get_output')
    def test_14__get_ld_config(self, mock_upout,
                               mock_exists, mock_dir):
        """Test ElfPatcher().get_ld_config().

        Get get directories from container ld.so.cache"""
        container_id = "SOME-RANDOM-ID"
        mock_upout.return_value = []
        elfp = ElfPatcher(self.conf, self.local, container_id)
        status = elfp._get_ld_config()
        self.assertEqual(status, [])

        mock_upout.return_value = \
            "ld.so.cache => /tmp/ROOT/etc/ld.so.cache\n" \
            "ld.so.cache => /tmp/ROOT/etc/ld.so"
        mock_dir.side_effect = ['/ld.so.cache', '/ld.so']
        elfp = ElfPatcher(self.conf, self.local, container_id)
        status = elfp._get_ld_config()
        self.assertIsInstance(status, list)

    @patch('udocker.helper.elfpatcher.os.path')
    @patch('udocker.helper.elfpatcher.os.access')
    @patch('udocker.helper.elfpatcher.os.walk')
    @patch('udocker.helper.elfpatcher.os.path.exists')
    def test_15__find_ld_libdirs(self, mock_exists,
                                 mock_walk, mock_access, mock_path):
        """Test ElfPatcher()._find_ld_libdirs().
        search for library directories in container"""
        container_id = "SOME-RANDOM-ID"
        elfp = ElfPatcher(self.conf, self.local, container_id)
        status = elfp._find_ld_libdirs()
        self.assertEqual(status, [])

    @patch.object(ElfPatcher, '_find_ld_libdirs')
    @patch('udocker.helper.elfpatcher.FileUtil.putdata')
    @patch('udocker.helper.elfpatcher.FileUtil.getdata')
    @patch('udocker.helper.elfpatcher.os.path.exists')
    def test_16_get_ld_libdirs(self, mock_exists, mock_getdata,
                               mock_pudata, mock_findlib):
        """Test ElfPatcher().get_ld_libdirs().
        Get ld library paths"""
        container_id = "SOME-RANDOM-ID"
        mock_exists.return_value = True
        mock_getdata.return_value = '/lib:/usr/lib'
        elfp = ElfPatcher(self.conf, self.local, container_id)
        status = elfp.get_ld_libdirs(False)
        self.assertEqual(status, ['/lib', '/usr/lib'])

        mock_exists.return_value = False
        mock_pudata.return_value = '/lib:/usr/lib'
        mock_findlib.return_value = ['/lib', '/usr/lib']
        elfp = ElfPatcher(self.conf, self.local, container_id)
        status = elfp.get_ld_libdirs(True)
        self.assertEqual(status, ['/lib', '/usr/lib'])

    @patch.object(ElfPatcher, 'get_ld_libdirs')
    @patch.object(ElfPatcher, '_get_ld_config')
    def test_17_get_ld_library_path(self, mock_ldconf, mock_ldlib):
        """Test ElfPatcher().get_ld_library_path().
        Get ld library paths"""
        container_id = "SOME-RANDOM-ID"
        self.conf['lib_dirs_list_essential'] = ""
        mock_ldconf.return_value = ["/lib"]
        mock_ldlib.return_value = ["/usr/lib"]
        elfp = ElfPatcher(self.conf, self.local, container_id)
        status = elfp.get_ld_library_path()
        self.assertEqual(status, "/lib:/usr/lib:.")


if __name__ == '__main__':
    main()
