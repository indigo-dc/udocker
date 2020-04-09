#!/usr/bin/env python
"""
udocker unit tests: ElfPatcher
"""
from unittest import TestCase, main
from udocker.helper.elfpatcher import ElfPatcher
from udocker.config import Config
from udocker.container.localrepo import LocalRepository
try:
    from unittest.mock import patch
except ImportError:
    from mock import patch


class ElfPatcherTestCase(TestCase):
    """Test ElfPatcher"""

    def setUp(self):
        Config().getconf()
        self.local = LocalRepository()

    def tearDown(self):
        pass

    # @patch('udocker.helper.elfpatcher.os.path.realpath')
    # def test_01__init(self, mock_path):
    #     """Test01 ElfPatcher() constructor."""

    @patch('udocker.helper.elfpatcher.Msg')
    @patch('udocker.helper.elfpatcher.os.path.realpath')
    @patch('udocker.helper.elfpatcher.FileUtil.find_file_in_dir')
    def test_02_select_patchelf(self, mock_find, mock_path, mock_msg):
        """Test02 ElfPatcher().select_patchelf()."""

        container_id = "SOME-RANDOM-ID"
        # mock_arch.side_effect = ["arm", "amd64", "i386", "arm64"]
        Config().conf["arch"] = "arm"
        mock_find.return_value = "runc-arm"
        mock_path.return_value = "/some_contdir"
        elfp = ElfPatcher(self.local, container_id)
        output = elfp.select_patchelf()
        self.assertEqual(output, "runc-arm")

        mock_find.return_value = ""
        mock_path.return_value = "/some_contdir"
        with self.assertRaises(SystemExit) as epexpt:
            elfp = ElfPatcher(self.local, container_id)
            elfp.select_patchelf()
        self.assertEqual(epexpt.exception.code, 1)

    # @patch('udocker.helper.elfpatcher.os.path.realpath')
    # def test_03__replace(self, mock_path):
    #     """Test03 ElfPatcher()._replace."""

    # Needs reviewing
    # @patch('udocker.helper.elfpatcher.os.path.realpath')
    # @patch('udocker.helper.elfpatcher.os.path.islink')
    # @patch('udocker.helper.elfpatcher.os.stat')
    # @patch('udocker.helper.elfpatcher.os.walk')
    # @patch('udocker.helper.elfpatcher.os.access')
    # def test_04__walk_fs(self, mock_access, mock_walk,
    #                      mock_stat, mock_islink, mock_path):
    #     """Test04 ElfPatcher()._walk_fs()."""
    #     container_id = "SOME-RANDOM-ID"
    #     mock_walk.return_value = [("/tmp", ["dir"], ["file"]), ]
    #     mock_islink.return_value = False
    #     mock_access.return_value = False
    #     mock_path.return_value = "/some_contdir"
    #     mock_stat.st_uid = ""
    #     elfp = ElfPatcher(self.local, container_id)
    #     status = elfp._walk_fs("cmd", "/tmp", elfp.BIN)
    #     self.assertFalse(status)

    @patch('udocker.helper.elfpatcher.os.path.realpath')
    @patch.object(ElfPatcher, '_walk_fs')
    @patch.object(ElfPatcher, 'select_patchelf')
    def test_05_guess_elf_loader(self, mock_spelf, mock_walk,
                                 mock_path):
        """Test05 ElfPatcher().guess_elf_loader()."""
        container_id = "SOME-RANDOM-ID"
        mock_spelf.return_value = "ld.so"
        mock_walk.return_value = ""
        mock_path.return_value = "/some_contdir"
        elfp = ElfPatcher(self.local, container_id)
        self.assertEqual(elfp.guess_elf_loader(), "")

        mock_walk.return_value = "ld.so"
        mock_path.return_value = "/some_contdir"
        elfp = ElfPatcher(self.local, container_id)
        self.assertEqual(elfp.guess_elf_loader(), "ld.so")

    @patch('udocker.helper.elfpatcher.os.path.realpath')
    @patch('udocker.helper.elfpatcher.os.path.exists')
    @patch('udocker.helper.elfpatcher.FileUtil.getdata')
    @patch('udocker.helper.elfpatcher.FileUtil.putdata')
    @patch.object(ElfPatcher, 'guess_elf_loader')
    def test_06_get_original_loader(self, mock_guess, mock_getdata,
                                    mock_putdata, mock_exists, mock_path):
        """Test06 ElfPatcher().get_original_loader()."""
        container_id = "SOME-RANDOM-ID"
        mock_path.return_value = "/some_contdir"
        #mock_exists.return_value = True
        #mock_getdata.return_value.strip.return_value = "ld.so"
        #elfp = ElfPatcher(self.local, container_id)
        #self.assertEqual(elfp.get_original_loader(), "ld.so")

        mock_path.return_value = "/some_contdir"
        mock_exists.return_value = False
        mock_guess.return_value = "ld.so"
        mock_getdata.return_value.strip.return_value = "ld.so"
        mock_putdata.return_value = "ld.so"
        elfp = ElfPatcher(self.local, container_id)
        self.assertEqual(elfp.get_original_loader(), "ld.so")

    @patch('udocker.helper.elfpatcher.os.path.realpath')
    @patch('udocker.helper.elfpatcher.os.path.exists')
    @patch.object(ElfPatcher, 'get_original_loader')
    def test_07_get_container_loader(self, mock_gol, mock_exists, mock_path):
        """Test07 ElfPatcher().get_container_loader().

        Get an absolute pathname to the container ld.so"""
        container_id = "SOME-RANDOM-ID"
        mock_gol.return_value = ""
        mock_path.return_value = "/some_contdir"
        elfp = ElfPatcher(self.local, container_id)
        self.assertEqual(elfp.get_container_loader(), "")

        mock_exists.return_value = True
        mock_gol.return_value = "ld.so"
        mock_path.return_value = "/some_contdir"
        elfp = ElfPatcher(self.local, container_id)
        self.assertEqual(elfp.get_container_loader(),
                         elfp._container_root + "/" + "ld.so")

    @patch('udocker.helper.elfpatcher.os.path.realpath')
    @patch('udocker.helper.elfpatcher.os.path.exists')
    @patch('udocker.helper.elfpatcher.FileUtil.getdata')
    def test_08_get_patch_last_path(self, mock_getdata, mock_exists,
                                    mock_path):
        """Test08 ElfPatcher().get_patch_last_path()."""
        container_id = "SOME-RANDOM-ID"
        mock_getdata.return_value = ""
        mock_path.return_value = "/some_contdir"
        elfp = ElfPatcher(self.local, container_id)
        self.assertEqual(elfp.get_patch_last_path(), "")

        mock_getdata.return_value = "/tmp"
        mock_path.return_value = "/some_contdir"
        elfp = ElfPatcher(self.local, container_id)
        self.assertEqual(elfp.get_patch_last_path(), "/tmp")

    @patch('udocker.helper.elfpatcher.os.path.realpath')
    @patch('udocker.helper.elfpatcher.os.path.exists')
    @patch.object(ElfPatcher, 'get_patch_last_path')
    @patch('udocker.helper.elfpatcher.Msg')
    def test_09_check_container_path(self, mock_msg, mock_lpath, mock_exists,
                                     mock_path):
        """Test09 ElfPatcher().check_container_path()."""
        container_id = "SOME-RANDOM-ID"
        mock_lpath.return_value = ""
        mock_path.return_value = "/some_contdir"
        elfp = ElfPatcher(self.local, container_id)
        status = elfp.check_container_path()
        self.assertTrue(status)

        mock_lpath.return_value = "xxx"
        mock_path.return_value = "/some_contdir"
        elfp = ElfPatcher(self.local, container_id)
        status = elfp.check_container_path()
        self.assertFalse(status)

    @patch('udocker.helper.elfpatcher.os.path.realpath')
    @patch('udocker.helper.elfpatcher.os.path.exists')
    @patch('udocker.helper.elfpatcher.FileUtil.getdata')
    def test_10_get_patch_last_time(self, mock_getdata,
                                    mock_exists, mock_path):
        """Test10 ElfPatcher().patch_last_time()."""
        container_id = "SOME-RANDOM-ID"
        mock_getdata.return_value = "30"
        mock_path.return_value = "/some_contdir"
        elfp = ElfPatcher(self.local, container_id)
        self.assertEqual(elfp.get_patch_last_time(), "30")

    @patch('udocker.helper.elfpatcher.os.path.realpath')
    @patch('udocker.helper.elfpatcher.os.path.exists')
    @patch('udocker.helper.elfpatcher.FileUtil.putdata')
    @patch.object(ElfPatcher, '_walk_fs')
    @patch.object(ElfPatcher, 'guess_elf_loader')
    @patch.object(ElfPatcher, 'select_patchelf')
    @patch.object(ElfPatcher, 'get_container_loader')
    @patch.object(ElfPatcher, 'check_container_path')
    def test_11_patch_binaries(self, mock_chkcont, mock_gcl, mock_select,
                               mock_guess, mock_walk, mock_putdata,
                               mock_exists, mock_path):
        """Test11 ElfPatcher().patch_binaries()."""
        container_id = "SOME-RANDOM-ID"
        mock_exists.return_value = True
        mock_chkcont.return_value = True
        mock_walk.return_value = True
        mock_gcl.return_value = "/usr/bin/ld"
        mock_select.return_value = "runc-arm"
        mock_putdata.side_effect = ["10", "/tmp"]
        mock_guess.return_value = "/usr/bin/ld"
        mock_path.return_value = "/some_contdir"
        elfp = ElfPatcher(self.local, container_id)
        elfp._container_root = "/tmp/ROOT"
        self.assertTrue(elfp.patch_binaries())

    # TODO: review this test
    @patch('udocker.helper.elfpatcher.os.path.realpath')
    @patch('udocker.helper.elfpatcher.FileUtil.remove')
    @patch.object(ElfPatcher, 'guess_elf_loader')
    @patch.object(ElfPatcher, '_walk_fs')
    @patch.object(ElfPatcher, 'get_patch_last_path')
    @patch.object(ElfPatcher, 'get_original_loader')
    @patch.object(ElfPatcher, 'select_patchelf')
    def test_12_restore_binaries(self, mock_select, mock_gol,
                                 mock_lpath, mock_walk, mock_guess,
                                 mock_rm, mock_path):
        """Test12 ElfPatcher().restore_binaries()."""
        container_id = "SOME-RANDOM-ID"
        mock_select.return_value = "runc-arm"
        mock_gol.return_value = "ld.so"
        mock_lpath.return_value = "xxx"
        mock_walk.return_value = ""
        mock_guess.return_value = "ld.so"
        mock_rm.return_value = True
        mock_path.return_value = "/some_contdir"
        elfp = ElfPatcher(self.local, container_id)
        elfp._container_root = "/tmp/ROOT"
        self.assertTrue(elfp.restore_binaries())
        self.assertTrue(mock_rm.called)

    @patch('udocker.helper.elfpatcher.os.path.realpath')
    @patch('udocker.helper.elfpatcher.os.path.exists')
    @patch.object(ElfPatcher, 'get_container_loader')
    @patch('udocker.helper.elfpatcher.FileUtil.size')
    @patch('udocker.helper.elfpatcher.FileUtil.copyto')
    @patch('udocker.helper.elfpatcher.FileUtil.getdata')
    @patch('udocker.helper.elfpatcher.FileUtil.putdata')
    def test_13_patch_ld(self, mock_putdata, mock_getdata,
                         mock_copyto, mock_size,
                         mock_gcl,
                         mock_exists, mock_path):
        """Test13 ElfPatcher().patch_ld()."""
        container_id = "SOME-RANDOM-ID"
        mock_size.return_value = -1
        mock_putdata.return_value = False
        mock_path.return_value = "/some_contdir"
        elfp = ElfPatcher(self.local, container_id)
        self.assertFalse(elfp.patch_ld())

        mock_size.return_value = 20
        mock_copyto.return_value = False
        mock_path.return_value = "/some_contdir"
        elfp = ElfPatcher(self.local, container_id)
        self.assertFalse(elfp.patch_ld())

        mock_size.return_value = 20
        mock_copyto.return_value = True
        mock_getdata.return_value = []
        mock_path.return_value = "/some_contdir"
        elfp = ElfPatcher(self.local, container_id)
        self.assertFalse(elfp.patch_ld())

        mock_size.return_value = 20
        mock_copyto.return_value = True
        mock_getdata.return_value = []
        mock_path.return_value = "/some_contdir"
        elfp = ElfPatcher(self.local, container_id)
        self.assertFalse(elfp.patch_ld("OUTPUT_ELF"))

    @patch('udocker.helper.elfpatcher.Msg')
    @patch('udocker.helper.elfpatcher.os.path.realpath')
    @patch('udocker.helper.elfpatcher.os.path.exists')
    @patch.object(ElfPatcher, 'get_container_loader')
    @patch('udocker.helper.elfpatcher.FileUtil.size')
    @patch('udocker.helper.elfpatcher.FileUtil.copyto')
    def test_14_restore_ld(self, mock_copyto, mock_size,
                           mock_gcl,
                           mock_exists, mock_path, mock_msg):
        """Test14 ElfPatcher().restore_ld()."""
        container_id = "SOME-RANDOM-ID"
        mock_size.return_value = -1
        mock_path.return_value = "/some_contdir"
        elfp = ElfPatcher(self.local, container_id)
        self.assertFalse(elfp.restore_ld())

        mock_size.return_value = 20
        mock_copyto.return_value = True
        mock_path.return_value = "/some_contdir"
        elfp = ElfPatcher(self.local, container_id)
        self.assertTrue(elfp.restore_ld())

    @patch('udocker.helper.elfpatcher.os.path.realpath')
    @patch('udocker.helper.elfpatcher.os.path.dirname')
    @patch('udocker.helper.elfpatcher.os.path.exists')
    @patch('udocker.helper.elfpatcher.Uprocess.get_output')
    def test_15__get_ld_config(self, mock_upout,
                               mock_exists, mock_dir, mock_path):
        """Test15 ElfPatcher().get_ld_config()."""
        container_id = "SOME-RANDOM-ID"
        mock_upout.return_value = []
        mock_path.return_value = "/some_contdir"
        elfp = ElfPatcher(self.local, container_id)
        status = elfp._get_ld_config()
        self.assertEqual(status, [])

        mock_upout.return_value = \
            "ld.so.cache => /tmp/ROOT/etc/ld.so.cache\n" \
            "ld.so.cache => /tmp/ROOT/etc/ld.so"
        mock_dir.side_effect = ['/ld.so.cache', '/ld.so']
        mock_path.return_value = "/some_contdir"
        elfp = ElfPatcher(self.local, container_id)
        status = elfp._get_ld_config()
        self.assertIsInstance(status, list)

    @patch('udocker.helper.elfpatcher.os.path.realpath')
    @patch('udocker.helper.elfpatcher.os.access')
    @patch('udocker.helper.elfpatcher.os.walk')
    @patch('udocker.helper.elfpatcher.os.path.exists')
    def test_16__find_ld_libdirs(self, mock_exists,
                                 mock_walk, mock_access, mock_path):
        """Test16 ElfPatcher()._find_ld_libdirs().
        search for library directories in container"""
        container_id = "SOME-RANDOM-ID"
        mock_path.return_value = "/some_contdir"
        elfp = ElfPatcher(self.local, container_id)
        status = elfp._find_ld_libdirs()
        self.assertEqual(status, [])

    @patch('udocker.helper.elfpatcher.os.path.realpath')
    @patch.object(ElfPatcher, '_find_ld_libdirs')
    @patch('udocker.helper.elfpatcher.FileUtil.putdata')
    @patch('udocker.helper.elfpatcher.FileUtil.getdata')
    @patch('udocker.helper.elfpatcher.os.path.exists')
    def test_17_get_ld_libdirs(self, mock_exists, mock_getdata,
                               mock_pudata, mock_findlib, mock_path):
        """Test17 ElfPatcher().get_ld_libdirs()."""
        container_id = "SOME-RANDOM-ID"
        mock_exists.return_value = True
        mock_getdata.return_value = '/lib:/usr/lib'
        mock_path.return_value = "/some_contdir"
        elfp = ElfPatcher(self.local, container_id)
        status = elfp.get_ld_libdirs(False)
        self.assertEqual(status, ['/lib', '/usr/lib'])

        mock_exists.return_value = False
        mock_pudata.return_value = '/lib:/usr/lib'
        mock_findlib.return_value = ['/lib', '/usr/lib']
        mock_path.return_value = "/some_contdir"
        elfp = ElfPatcher(self.local, container_id)
        status = elfp.get_ld_libdirs(True)
        self.assertEqual(status, ['/lib', '/usr/lib'])

    @patch('udocker.helper.elfpatcher.os.path.realpath')
    @patch.object(ElfPatcher, 'get_ld_libdirs')
    @patch.object(ElfPatcher, '_get_ld_config')
    def test_18_get_ld_library_path(self, mock_ldconf,
                                    mock_ldlib, mock_path):
        """Test18 ElfPatcher().get_ld_library_path()."""
        container_id = "SOME-RANDOM-ID"
        Config().conf['lib_dirs_list_essential'] = ""
        mock_ldconf.return_value = ["/lib"]
        mock_ldlib.return_value = ["/usr/lib"]
        mock_path.return_value = "/some_contdir"
        elfp = ElfPatcher(self.local, container_id)
        status = elfp.get_ld_library_path()
        self.assertEqual(status, "/lib:/usr/lib:.")


if __name__ == '__main__':
    main()
