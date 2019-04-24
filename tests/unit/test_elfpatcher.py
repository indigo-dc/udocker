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
        container_id = "SOME-RANDOM-ID"
        self.elfp = ElfPatcher(self.conf, self.local, container_id)

    def tearDown(self):
        pass

    @patch('udocker.msg.Msg')
    @patch('udocker.helper.elfpatcher.os.path')
    @patch('udocker.config.Config')
    @patch('udocker.utils.fileutil.FileUtil.find_file_in_dir')
    @patch('udocker.container.localrepo.LocalRepository')
    def test_02_select_patchelf(self, mock_local, mock_find,
                                mock_conf, mock_path, mock_msg):
        """Test ElfPatcher().select_patchelf().

        Set patchelf executable."""

        mock_conf.return_value.arch.side_effect = ["arm", "amd64", "i386", "arm64"]
        mock_find.return_value = "runc-arm"
        output = self.elfp.select_patchelf()
        self.assertEqual(output, "runc-arm")

        mock_find.return_value = ""
        with self.assertRaises(SystemExit) as epexpt:
            self.elfp.select_patchelf()
        self.assertEqual(epexpt.exception.code, 1)

    # @patch('udocker.helper.elfpatcher.os.path.islink')
    # @patch('udocker.helper.elfpatcher.os.path.stat')
    # @patch('udocker.helper.elfpatcher.os.path')
    # @patch('udocker.helper.elfpatcher.os.walk')
    # @patch('udocker.helper.elfpatcher.os.access')
    # @patch('udocker.container.localrepo.LocalRepository')
    # def test_03__walk_fs(self, mock_local, mock_access, mock_walk,
    #                      mock_path, mock_stat, mock_islink):
    #     """Test ElfPatcher()._walk_fs().
    #
    #     Execute a shell command over each executable file in a given dir_path.
    #     Action can be ABORT_ON_ERROR, return upon first success
    #     ONE_SUCCESS, or return upon the first non empty output. #f is the
    #     placeholder for the filename.
    #     """
    #     mock_walk.return_value = ("/tmp", ["dir"], ["file"]);
    #     mock_islink.return_value = False
    #     mock_stat.return_value.st_uid = ""
    #     status = self.elfp._walk_fs("cmd", "/tmp", self.elfp.BIN)
    #     self.assertIsNone(status)

    @patch('udocker.helper.elfpatcher.os.path')
    @patch('udocker.container.localrepo.LocalRepository')
    @patch('udocker.helper.elfpatcher.ElfPatcher._walk_fs')
    @patch('udocker.helper.elfpatcher.ElfPatcher.select_patchelf')
    def test_04_guess_elf_loader(self, mock_spelf, mock_walk,
                                 mock_local, mock_path):
        """Test ElfPatcher().guess_elf_loader().

        Search for executables and try to read the ld.so pathname."""
        mock_spelf.return_value = "ld.so"
        mock_walk.return_value = ""
        self.assertEqual(self.elfp.guess_elf_loader(), "")

        mock_walk.return_value = "ld.so"
        self.assertEqual(self.elfp.guess_elf_loader(), "ld.so")

    @patch('udocker.helper.elfpatcher.os.path')
    @patch('udocker.helper.elfpatcher.os.path.exists')
    @patch('udocker.container.localrepo.LocalRepository')
    @patch('udocker.utils.fileutil.FileUtil.getdata')
    @patch('udocker.helper.elfpatcher.ElfPatcher.guess_elf_loader')
    def test_05_get_original_loader(self, mock_guess, mock_futils,
                                    mock_local, mock_exists, mock_path):
        """Test ElfPatcher().get_original_loader().

        Get the pathname of the original ld.so.
        """
        mock_exists.return_value = True
        mock_futils.return_value.strip.return_value = "ld.so"
        self.assertEqual(self.elfp.get_original_loader(), "ld.so")

        mock_exists.return_value = False
        mock_guess.return_value = "ld.so"
        mock_futils.return_value.strip.return_value = "ld.so"
        self.assertEqual(self.elfp.get_original_loader(), "ld.so")

    @patch('udocker.helper.elfpatcher.os.path')
    @patch('udocker.helper.elfpatcher.os.path.exists')
    @patch('udocker.container.localrepo.LocalRepository')
    @patch('udocker.helper.elfpatcher.ElfPatcher.get_original_loader')
    def test_06_get_container_loader(self, mock_gol, mock_local,
                                     mock_exists, mock_path):
        """Test ElfPatcher().get_container_loader().

        Get an absolute pathname to the container ld.so"""
        mock_gol.return_value = ""
        self.assertEqual(self.elfp.get_container_loader(), "")

        mock_exists.return_value = True
        mock_gol.return_value = "ld.so"
        self.assertEqual(self.elfp.get_container_loader(),
                         self.elfp._container_root + "/" + "ld.so")

    @patch('udocker.helper.elfpatcher.os.path')
    @patch('udocker.helper.elfpatcher.os.path.exists')
    @patch('udocker.container.localrepo.LocalRepository')
    @patch('udocker.utils.fileutil.FileUtil.getdata')
    def test_07_get_patch_last_path(self, mock_getdata, mock_local,
                                    mock_exists, mock_path):
        """Test ElfPatcher().get_patch_last_path().

        get last host pathname to the patched container."""
        mock_getdata.return_value = ""
        self.assertEqual(self.elfp.get_patch_last_path(), "")

        mock_getdata.return_value = "/tmp"
        self.assertEqual(self.elfp.get_patch_last_path(), "/tmp")

    # @patch('udocker.helper.elfpatcher.os.path')
    # @patch('udocker.helper.elfpatcher.os.path.exists')
    # @patch('udocker.container.localrepo.LocalRepository')
    # @patch('udocker.helper.elfpatcher.ElfPatcher.get_patch_last_path')
    # @patch('udocker.msg.Msg')
    # def test_08_check_container_path(self, mock_msg, mock_lpath,
    #                             mock_local, mock_exists, mock_path):
    #     """Test ElfPatcher().check_container_path().
    #
    #     verify if path to container is ok"""
    #     mock_lpath.return_value = "/tmp"
    #     with self.assertRaises(SystemExit) as epexpt:
    #         self.elfp.check_container_path()
    #     self.assertEqual(epexpt.exception.code, 1)

    @patch('udocker.helper.elfpatcher.os.path')
    @patch('udocker.helper.elfpatcher.os.path.exists')
    @patch('udocker.container.localrepo.LocalRepository')
    @patch('udocker.utils.fileutil.FileUtil.getdata')
    def test_09_get_patch_last_time(self, mock_getdata, mock_local,
                                    mock_exists, mock_path):
        """Test ElfPatcher().patch_last_time().

        get time in seconds of last full patch of container"""
        mock_getdata.return_value = "30"
        self.assertEqual(self.elfp.get_patch_last_time(), "30")

    @patch('udocker.helper.elfpatcher.os.path')
    @patch('udocker.helper.elfpatcher.os.path.exists')
    @patch('udocker.container.localrepo.LocalRepository')
    @patch('udocker.utils.fileutil.FileUtil.putdata')
    @patch('udocker.helper.elfpatcher.ElfPatcher.guess_elf_loader')
    @patch('udocker.helper.elfpatcher.ElfPatcher.select_patchelf')
    @patch('udocker.helper.elfpatcher.ElfPatcher.get_container_loader')
    @patch('udocker.helper.elfpatcher.ElfPatcher')
    def test_10_patch_binaries(self, mock_elfp, mock_gcl, mock_select,
                               mock_guess, mock_putdata, mock_local,
                               mock_exists, mock_path):
        """Test ElfPatcher().patch_binaries().

        Set all executables and libs to the ld.so absolute pathname"""
        mock_exists.return_value = True
        mock_gcl.return_value = "/usr/bin/ld"
        mock_select.return_value = "runc-arm"
        mock_putdata.side_effect = ["10", "/tmp"]
        mock_guess.return_value = "/usr/bin/ld"
        mock_elfp.return_value._container_root.return_value = "/tmp/ROOT"
        self.assertTrue(self.elfp.patch_binaries())

    # @patch('udocker.helper.elfpatcher.os.path')
    # @patch('udocker.helper.elfpatcher.os.path.exists')
    # @patch('udocker.container.localrepo.LocalRepository')
    # @patch('udocker.helper.elfpatcher.ElfPatcher.guess_elf_loader')
    # @patch('udocker.helper.elfpatcher.ElfPatcher.select_patchelf')
    # @patch('udocker.helper.elfpatcher.ElfPatcher.get_container_loader')
    # @patch('udocker.helper.elfpatcher.ElfPatcher')
    # def test_11_restore_binaries(self, mock_elfp, mock_gcl, mock_select,
    #                              mock_guess, mock_local,
    #                              mock_exists, mock_path):
    #     """Test ElfPatcher().restore_binaries().
    #
    #     Restore all executables and libs to the original ld.so pathname"""
    #     mock_exists.return_value = True
    #     mock_gcl.return_value = "/usr/bin/ld"
    #     mock_select.return_value = "runc-arm"
    #     mock_guess.return_value = "/usr/bin/ld"
    #     mock_elfp.return_value._container_root.return_value = "/tmp/ROOT"
    #     self.assertTrue(self.elfp.restore_binaries())

    @patch('udocker.helper.elfpatcher.os.path')
    @patch('udocker.helper.elfpatcher.os.path.exists')
    @patch('udocker.container.localrepo.LocalRepository')
    @patch('udocker.helper.elfpatcher.ElfPatcher.get_container_loader')
    @patch('udocker.utils.fileutil.FileUtil.size')
    @patch('udocker.utils.fileutil.FileUtil.copyto')
    @patch('udocker.utils.fileutil.FileUtil.getdata')
    def test_12_patch_ld(self, mock_getdata,
                         mock_copyto, mock_size,
                         mock_gcl, mock_local,
                         mock_exists, mock_path):
        """Test ElfPatcher().patch_ld().

        Patch ld.so"""
        mock_size.return_value = -1
        self.assertFalse(self.elfp.patch_ld())

        mock_size.return_value = 20
        mock_copyto.return_value = False
        self.assertFalse(self.elfp.patch_ld())

        mock_size.return_value = 20
        mock_copyto.return_value = True
        mock_getdata.return_value = []
        self.assertFalse(self.elfp.patch_ld())

        mock_size.return_value = 20
        mock_copyto.return_value = True
        mock_getdata.return_value = []
        self.assertFalse(self.elfp.patch_ld("OUTPUT_ELF"))

    @patch('udocker.msg.Msg')
    @patch('udocker.helper.elfpatcher.os.path')
    @patch('udocker.helper.elfpatcher.os.path.exists')
    @patch('udocker.container.localrepo.LocalRepository')
    @patch('udocker.helper.elfpatcher.ElfPatcher.get_container_loader')
    @patch('udocker.utils.fileutil.FileUtil.size')
    @patch('udocker.utils.fileutil.FileUtil.copyto')
    def test_13_restore_ld(self, mock_copyto, mock_size,
                           mock_gcl, mock_local,
                           mock_exists, mock_path, mock_msg):
        """Test ElfPatcher().restore_ld().

        Restore ld.so"""
        mock_size.return_value = -1
        self.assertFalse(self.elfp.restore_ld())

        mock_size.return_value = 20
        mock_copyto.return_value = True
        self.assertTrue(self.elfp.restore_ld())

    @patch('udocker.helper.elfpatcher.os.path')
    @patch('udocker.helper.elfpatcher.os.path.exists')
    @patch('udocker.container.localrepo.LocalRepository')
    @patch('udocker.utils.uprocess.Uprocess.get_output')
    def test_14__get_ld_config(self, mock_upout,
                               mock_local, mock_exists, mock_path):
        """Test ElfPatcher().get_ld_config().

        Get get directories from container ld.so.cache"""
        mock_upout.return_value = []
        status = self.elfp._get_ld_config()
        self.assertEqual(status, [])

        mock_upout.return_value = \
            "ld.so.cache => /tmp/ROOT/etc/ld.so.cache\n" \
            "ld.so.cache => /tmp/ROOT/etc/ld.so"
        status = self.elfp._get_ld_config()
        self.assertIsInstance(status, list)

    @patch('udocker.helper.elfpatcher.os.path')
    @patch('udocker.helper.elfpatcher.os.access')
    @patch('udocker.helper.elfpatcher.os.walk')
    @patch('udocker.helper.elfpatcher.os.path.exists')
    @patch('udocker.container.localrepo.LocalRepository')
    def test_15__find_ld_libdirs(self, mock_local, mock_exists,
                                 mock_walk, mock_access, mock_path):
        """Test ElfPatcher()._find_ld_libdirs().

        search for library directories in container"""
        status = self.elfp._find_ld_libdirs()
        self.assertEqual(status, [])

    @patch('udocker.helper.elfpatcher.os.path')
    @patch('udocker.helper.elfpatcher.os.path.exists')
    @patch('udocker.container.localrepo.LocalRepository')
    def test_16_get_ld_libdirs(self, mock_local,
                               mock_exists, mock_path):
        """Test ElfPatcher().get_ld_libdirs().

        Get ld library paths"""
        status = self.elfp.get_ld_libdirs()
        self.assertEqual(status, [''])

    # @patch('udocker.helper.elfpatcher.os.path')
    # @patch('udocker.helper.elfpatcher.os.path.exists')
    # @patch('udocker.container.localrepo.LocalRepository')
    # def test_17_get_ld_library_path(self, mock_local,
    #                                 mock_exists, mock_path):
    #     """Test ElfPatcher().get_ld_library_path().
    #
    #     Get ld library paths"""
    #     status = self.elfp.get_ld_library_path()
    #     self.assertEqual(status, [''])


if __name__ == '__main__':
    main()
