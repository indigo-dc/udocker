#!/usr/bin/env python
"""
udocker unit tests: ElfPatcher
"""

from unittest import TestCase, main
from unittest.mock import patch, Mock
from udocker.helper.elfpatcher import ElfPatcher
from udocker.config import Config


class ElfPatcherTestCase(TestCase):
    """Test ElfPatcher"""

    def setUp(self):
        self.contid = "12345"
        Config().getconf()
        str_local = 'udocker.container.localrepo.LocalRepository'
        self.lrepo = patch(str_local)
        self.local = self.lrepo.start()
        self.mock_lrepo = Mock()
        self.local.return_value = self.mock_lrepo

    def tearDown(self):
        self.lrepo.stop()

    @patch('udocker.helper.elfpatcher.HostInfo')
    @patch('udocker.helper.elfpatcher.os.path.realpath')
    def test_01__init(self, mock_path, mock_hinfo):
        """Test01 ElfPatcher() constructor."""
        mock_path.return_value = "/some_contdir"
        mock_hinfo.uid = "1000"
        elfp = ElfPatcher(self.local, self.contid)
        self.assertTrue(mock_path.callled)
        self.assertEqual(elfp._uid, "1000")

    @patch('udocker.helper.elfpatcher.Msg')
    @patch('udocker.helper.elfpatcher.os.path.exists')
    @patch('udocker.helper.elfpatcher.HostInfo.arch')
    @patch('udocker.helper.elfpatcher.FileUtil.find_file_in_dir')
    @patch('udocker.helper.elfpatcher.os.path.realpath')
    def test_02_select_patchelf(self, mock_path, mock_find,
                                mock_arch, mock_exists, mock_msg):
        """Test02 ElfPatcher().select_patchelf()."""
        mock_msg.level = 0
        mock_path.return_value = "/some_contdir"
        mock_arch.return_value = "arm"
        mock_find.return_value = "runc-arm"
        mock_exists.return_value = True
        elfp = ElfPatcher(self.local, self.contid)
        output = elfp.select_patchelf()
        self.assertEqual(output, "runc-arm")

        mock_path.return_value = "/some_contdir"
        mock_arch.return_value = "arm"
        mock_find.return_value = ""
        mock_exists.return_value = False
        with self.assertRaises(SystemExit) as epexpt:
            elfp = ElfPatcher(self.local, self.contid)
            elfp.select_patchelf()
            self.assertEqual(epexpt.exception.code, 1)

    @patch('udocker.helper.elfpatcher.os.path.realpath')
    def test_03__replace(self, mock_path):
        """Test03 ElfPatcher()._replace."""
        mock_path.return_value = "/some_contdir"
        cmd = ("#f", "ls")
        path = "/bin/"
        elfp = ElfPatcher(self.local, self.contid)
        output = elfp._replace(cmd, path)
        self.assertEqual(output, ["/bin/", "ls"])

    # Needs reviewing
    @patch('udocker.helper.elfpatcher.Uprocess.get_output')
    @patch('udocker.helper.elfpatcher.os.path.islink')
    @patch('udocker.helper.elfpatcher.os.stat')
    @patch('udocker.helper.elfpatcher.os.walk')
    @patch('udocker.helper.elfpatcher.os.access')
    @patch('udocker.helper.elfpatcher.os.path.realpath')
    def test_04__walk_fs(self, mock_path, mock_access, mock_walk,
                         mock_stat, mock_islink, mock_uprocout):
        """Test04 ElfPatcher()._walk_fs()."""
        mock_path.return_value = "/some_contdir"
        mock_walk.return_value = [("/tmp", ["dir"], ["file"]), ]
        mock_islink.return_value = False
        mock_access.return_value = False
        mock_stat.return_value.st_uid = 1000
        elfp = ElfPatcher(self.local, self.contid)
        elfp._uid = 0
        status = elfp._walk_fs("cmd", "/tmp", elfp.ABORT_ON_ERROR)
        self.assertEqual(status, "")

        mock_path.return_value = "/some_contdir"
        mock_walk.return_value = [("/tmp", ["dir"], ["file"]), ]
        mock_islink.return_value = False
        mock_access.return_value = True
        mock_stat.return_value.st_uid = 0
        mock_uprocout.return_value = "some output"
        elfp = ElfPatcher(self.local, self.contid)
        elfp._uid = 0
        status = elfp._walk_fs("cmd", "/tmp", elfp.BIN)
        self.assertTrue(mock_uprocout.called)
        self.assertEqual(status, "some output")

    @patch('udocker.helper.elfpatcher.os.path.realpath')
    @patch.object(ElfPatcher, '_walk_fs')
    @patch.object(ElfPatcher, 'select_patchelf')
    def test_05_guess_elf_loader(self, mock_spelf, mock_walk,
                                 mock_path):
        """Test05 ElfPatcher().guess_elf_loader()."""
        mock_spelf.return_value = "ld.so"
        mock_walk.return_value = ""
        mock_path.return_value = "/some_contdir"
        elfp = ElfPatcher(self.local, self.contid)
        self.assertEqual(elfp.guess_elf_loader(), "")

        mock_walk.return_value = "ld.so"
        mock_path.return_value = "/some_contdir"
        elfp = ElfPatcher(self.local, self.contid)
        self.assertEqual(elfp.guess_elf_loader(), "ld.so")

    @patch('udocker.helper.elfpatcher.os.path.realpath')
    @patch('udocker.helper.elfpatcher.os.path.exists')
    @patch('udocker.helper.elfpatcher.FileUtil.getdata')
    @patch('udocker.helper.elfpatcher.FileUtil.putdata')
    @patch.object(ElfPatcher, 'guess_elf_loader')
    def test_06_get_original_loader(self, mock_guess, mock_getdata,
                                    mock_putdata, mock_exists, mock_path):
        """Test06 ElfPatcher().get_original_loader()."""
        mock_path.return_value = "/some_contdir"
        mock_exists.return_value = False
        mock_guess.return_value = "ld.so"
        mock_getdata.return_value.strip.return_value = "ld.so"
        mock_putdata.return_value = "ld.so"
        elfp = ElfPatcher(self.local, self.contid)
        status = elfp.get_original_loader()
        self.assertEqual(status, "ld.so")

    @patch('udocker.helper.elfpatcher.os.path.realpath')
    @patch('udocker.helper.elfpatcher.os.path.exists')
    @patch.object(ElfPatcher, 'get_original_loader')
    def test_07_get_container_loader(self, mock_gol, mock_exists, mock_path):
        """Test07 ElfPatcher().get_container_loader().

        Get an absolute pathname to the container ld.so"""
        mock_gol.return_value = ""
        mock_path.return_value = "/some_contdir"
        elfp = ElfPatcher(self.local, self.contid)
        self.assertEqual(elfp.get_container_loader(), "")

        mock_exists.return_value = True
        mock_gol.return_value = "ld.so"
        mock_path.return_value = "/some_contdir"
        elfp = ElfPatcher(self.local, self.contid)
        self.assertEqual(elfp.get_container_loader(),
                         elfp._container_root + "/" + "ld.so")

    @patch('udocker.helper.elfpatcher.os.path.realpath')
    @patch('udocker.helper.elfpatcher.FileUtil.getdata')
    def test_08_get_patch_last_path(self, mock_getdata,
                                    mock_path):
        """Test08 ElfPatcher().get_patch_last_path()."""
        mock_getdata.return_value = ""
        mock_path.return_value = "/some_contdir"
        elfp = ElfPatcher(self.local, self.contid)
        self.assertEqual(elfp.get_patch_last_path(), "")

        mock_getdata.return_value = "/tmp"
        mock_path.return_value = "/some_contdir"
        elfp = ElfPatcher(self.local, self.contid)
        self.assertEqual(elfp.get_patch_last_path(), "/tmp")

    @patch('udocker.helper.elfpatcher.os.path.realpath')
    @patch.object(ElfPatcher, 'get_patch_last_path')
    def test_09_check_container_path(self, mock_lpath, mock_path):
        """Test09 ElfPatcher().check_container_path()."""
        mock_lpath.return_value = ""
        mock_path.return_value = "/some_contdir"
        elfp = ElfPatcher(self.local, self.contid)
        status = elfp.check_container_path()
        self.assertTrue(status)

        mock_lpath.return_value = "xxx"
        mock_path.return_value = "/some_contdir"
        elfp = ElfPatcher(self.local, self.contid)
        status = elfp.check_container_path()
        self.assertFalse(status)

    @patch('udocker.helper.elfpatcher.os.path.realpath')
    @patch('udocker.helper.elfpatcher.FileUtil.getdata')
    def test_10_get_patch_last_time(self, mock_getdata, mock_path):
        """Test10 ElfPatcher().patch_last_time()."""
        mock_getdata.return_value = "30"
        mock_path.return_value = "/some_contdir"
        elfp = ElfPatcher(self.local, self.contid)
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
        mock_exists.return_value = True
        mock_chkcont.return_value = True
        mock_walk.return_value = True
        mock_gcl.return_value = "/usr/bin/ld"
        mock_select.return_value = "runc-arm"
        mock_putdata.side_effect = ["10", "/tmp"]
        mock_guess.return_value = "/usr/bin/ld"
        mock_path.return_value = "/some_contdir"
        elfp = ElfPatcher(self.local, self.contid)
        elfp._container_root = "/tmp/ROOT"
        self.assertTrue(elfp.patch_binaries())

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
        mock_select.return_value = "runc-arm"
        mock_gol.return_value = "ld.so"
        mock_lpath.return_value = "xxx"
        mock_walk.return_value = ""
        mock_guess.return_value = "ld.so"
        mock_rm.return_value = True
        mock_path.return_value = "/some_contdir"
        elfp = ElfPatcher(self.local, self.contid)
        elfp._container_root = "/tmp/ROOT"
        self.assertTrue(elfp.restore_binaries())
        self.assertTrue(mock_rm.called)

    @patch.object(ElfPatcher, 'get_container_loader')
    @patch('udocker.helper.elfpatcher.os.path.realpath')
    @patch('udocker.helper.elfpatcher.FileUtil.size')
    @patch('udocker.helper.elfpatcher.FileUtil.copyto')
    @patch('udocker.helper.elfpatcher.FileUtil.getdata')
    @patch('udocker.helper.elfpatcher.FileUtil.putdata')
    def test_13_patch_ld(self, mock_putdata, mock_getdata,
                         mock_copyto, mock_size, mock_path, mock_gcl):
        """Test13 ElfPatcher().patch_ld()."""
        mock_size.return_value = -1
        mock_putdata.return_value = False
        mock_path.return_value = "/some_contdir"
        mock_gcl.return_value = ""
        elfp = ElfPatcher(self.local, self.contid)
        self.assertFalse(elfp.patch_ld())

        mock_size.return_value = 20
        mock_copyto.return_value = False
        mock_path.return_value = "/some_contdir"
        mock_gcl.return_value = ""
        elfp = ElfPatcher(self.local, self.contid)
        self.assertFalse(elfp.patch_ld())

        mock_size.return_value = 20
        mock_copyto.return_value = True
        mock_getdata.return_value = []
        mock_path.return_value = "/some_contdir"
        mock_gcl.return_value = ""
        elfp = ElfPatcher(self.local, self.contid)
        self.assertFalse(elfp.patch_ld())

        mock_size.return_value = 20
        mock_copyto.return_value = True
        mock_getdata.return_value = []
        mock_path.return_value = "/some_contdir"
        mock_gcl.return_value = ""
        elfp = ElfPatcher(self.local, self.contid)
        self.assertFalse(elfp.patch_ld("OUTPUT_ELF"))

    @patch('udocker.helper.elfpatcher.Msg')
    @patch.object(ElfPatcher, 'get_container_loader')
    @patch('udocker.helper.elfpatcher.os.path.realpath')
    @patch('udocker.helper.elfpatcher.FileUtil.size')
    @patch('udocker.helper.elfpatcher.FileUtil.copyto')
    def test_14_restore_ld(self, mock_copyto, mock_size, mock_path,
                           mock_gcl, mock_msg):
        """Test14 ElfPatcher().restore_ld()."""
        mock_msg.level = 0
        mock_size.return_value = -1
        mock_path.return_value = "/some_contdir"
        mock_gcl.return_value = ""
        elfp = ElfPatcher(self.local, self.contid)
        self.assertFalse(elfp.restore_ld())

        mock_size.return_value = 20
        mock_copyto.return_value = True
        mock_path.return_value = "/some_contdir"
        mock_gcl.return_value = ""
        elfp = ElfPatcher(self.local, self.contid)
        self.assertTrue(elfp.restore_ld())

    @patch('udocker.helper.elfpatcher.os.path.realpath')
    @patch('udocker.helper.elfpatcher.os.path.dirname')
    @patch('udocker.helper.elfpatcher.Uprocess.get_output')
    def test_15__get_ld_config(self, mock_upout, mock_dir, mock_path):
        """Test15 ElfPatcher().get_ld_config()."""
        mock_upout.return_value = []
        mock_path.return_value = "/some_contdir"
        elfp = ElfPatcher(self.local, self.contid)
        status = elfp._get_ld_config()
        self.assertEqual(status, [])

        mock_upout.return_value = \
            "ld.so.cache => /tmp/ROOT/etc/ld.so.cache\n" \
            "ld.so.cache => /tmp/ROOT/etc/ld.so"
        mock_dir.side_effect = ['/ld.so.cache', '/ld.so']
        mock_path.return_value = "/some_contdir"
        elfp = ElfPatcher(self.local, self.contid)
        status = elfp._get_ld_config()
        self.assertIsInstance(status, list)

    @patch('udocker.helper.elfpatcher.os.path.isfile')
    @patch('udocker.helper.elfpatcher.os.path.realpath')
    @patch('udocker.helper.elfpatcher.os.access')
    @patch('udocker.helper.elfpatcher.os.walk')
    def test_16__find_ld_libdirs(self, mock_walk, mock_access,
                                 mock_path, mock_isfile):
        """Test16 ElfPatcher()._find_ld_libdirs().
        search for library directories in container"""
        mock_path.return_value = "/some_contdir"
        elfp = ElfPatcher(self.local, self.contid)
        status = elfp._find_ld_libdirs()
        self.assertEqual(status, [])

        mock_path.return_value = "/some_contdir"
        mock_walk.return_value = [("libsome.so.0", ["dir"], ["libsome.so.0"]), ]
        mock_access.return_value = True
        mock_isfile.return_value = True
        elfp = ElfPatcher(self.local, self.contid)
        status = elfp._find_ld_libdirs()
        self.assertEqual(status, ["libsome.so.0"])

    @patch('udocker.helper.elfpatcher.os.path.realpath')
    @patch.object(ElfPatcher, '_find_ld_libdirs')
    @patch('udocker.helper.elfpatcher.FileUtil.putdata')
    @patch('udocker.helper.elfpatcher.FileUtil.getdata')
    @patch('udocker.helper.elfpatcher.os.path.exists')
    def test_17_get_ld_libdirs(self, mock_exists, mock_getdata,
                               mock_pudata, mock_findlib, mock_path):
        """Test17 ElfPatcher().get_ld_libdirs()."""
        mock_exists.return_value = True
        mock_getdata.return_value = '/lib:/usr/lib'
        mock_path.return_value = "/some_contdir"
        elfp = ElfPatcher(self.local, self.contid)
        status = elfp.get_ld_libdirs(False)
        self.assertEqual(status, ['/lib', '/usr/lib'])

        mock_exists.return_value = False
        mock_pudata.return_value = '/lib:/usr/lib'
        mock_findlib.return_value = ['/lib', '/usr/lib']
        mock_path.return_value = "/some_contdir"
        elfp = ElfPatcher(self.local, self.contid)
        status = elfp.get_ld_libdirs(True)
        self.assertEqual(status, ['/lib', '/usr/lib'])

    @patch('udocker.helper.elfpatcher.os.path.realpath')
    @patch.object(ElfPatcher, 'get_ld_libdirs')
    @patch.object(ElfPatcher, '_get_ld_config')
    def test_18_get_ld_library_path(self, mock_ldconf,
                                    mock_ldlib, mock_path):
        """Test18 ElfPatcher().get_ld_library_path()."""
        Config().conf['lib_dirs_list_essential'] = ""
        mock_ldconf.return_value = ["/lib"]
        mock_ldlib.return_value = ["/usr/lib"]
        mock_path.return_value = "/some_contdir"
        elfp = ElfPatcher(self.local, self.contid)
        status = elfp.get_ld_library_path()
        self.assertEqual(status, "/lib:/usr/lib:.")


if __name__ == '__main__':
    main()
