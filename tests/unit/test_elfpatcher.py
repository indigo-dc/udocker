#!/usr/bin/env python2
"""
udocker unit tests.
Unit tests for udocker, a wrapper to execute basic docker containers
without using docker.
Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at
http://www.apache.org/licenses/LICENSE-2.0
Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""

import os
import sys
import unittest
import mock

sys.path.append('.')

from udocker.helper.elfpatcher import ElfPatcher


def set_env():
    """Set environment variables."""
    if not os.getenv("HOME"):
        os.environ["HOME"] = os.getcwd()


class ElfPatcherTestCase(unittest.TestCase):
    """."""

    @classmethod
    def setUpClass(cls):
        """Setup test."""
        set_env()

    def _init(self):
        """."""
        pass

    @mock.patch('udocker.msg.Msg')
    @mock.patch('os.path')
    @mock.patch('udocker.config.Config')
    @mock.patch('udocker.utils.fileutil.FileUtil')
    @mock.patch('udocker.container.localrepo.LocalRepository')
    def test_02_select_patchelf(self, mock_local, mock_futil,
                                mock_conf, mock_path, mock_msg):
        """Test ElfPatcher().select_patchelf().

        Set patchelf executable."""
        container_id = "SOME-RANDOM-ID"
        self._init()

        mock_conf.return_value.arch.side_effect = ["arm", "amd64", "i386", "arm64"]
        mock_futil.return_value.find_file_in_dir.return_value = "runc-arm"
        elfp = ElfPatcher(mock_local, container_id)
        output = elfp.select_patchelf()
        self.assertEqual(output, "runc-arm")

        mock_futil.return_value.find_file_in_dir.return_value = ""
        elfp = ElfPatcher(mock_local, container_id)
        with self.assertRaises(SystemExit) as epexpt:
            elfp.select_patchelf()
        self.assertEqual(epexpt.exception.code, 1)

    @mock.patch('os.path.islink')
    @mock.patch('os.path.stat')
    @mock.patch('os.path')
    @mock.patch('os.walk')
    @mock.patch('os.access')
    @mock.patch('udocker.container.localrepo.LocalRepository')
    def test_03__walk_fs(self, mock_local, mock_access, mock_walk,
                         mock_path, mock_stat, mock_islink):
        """Test ElfPatcher()._walk_fs().

        Execute a shell command over each executable file in a given dir_path.
        Action can be ABORT_ON_ERROR, return upon first success
        ONE_SUCCESS, or return upon the first non empty output. #f is the
        placeholder for the filename.
        """
        # self._init()
        # container_id = "SOME-RANDOM-ID"
        # elfp = udocker.ElfPatcher(mock_local, container_id)
        #
        # mock_walk.return_value = ("/tmp", ["dir"], ["file"]);
        # mock_islink.return_value = False
        # mock_stat.return_value.st_uid = ""
        # status = elfp._walk_fs("cmd", "/tmp", elfp.BIN)
        # self.assertIsNone(status)
        pass

    @mock.patch('os.path')
    @mock.patch('udocker.container.localrepo.LocalRepository')
    @mock.patch('udocker.helper.elfpatcher.ElfPatcher._walk_fs')
    @mock.patch('udocker.helper.elfpatcher.ElfPatcher.select_patchelf')
    def test_04_guess_elf_loader(self, mock_spelf, mock_walk,
                                 mock_local, mock_path):
        """Test ElfPatcher().guess_elf_loader().

        Search for executables and try to read the ld.so pathname."""
        self._init()
        container_id = "SOME-RANDOM-ID"
        mock_spelf.return_value = "ld.so"
        mock_walk.return_value = ""
        elfp = ElfPatcher(mock_local, container_id)
        self.assertEqual(elfp.guess_elf_loader(), "")

        mock_walk.return_value = "ld.so"
        elfp = ElfPatcher(mock_local, container_id)
        self.assertEqual(elfp.guess_elf_loader(), "ld.so")

    @mock.patch('os.path')
    @mock.patch('os.path.exists')
    @mock.patch('udocker.container.localrepo.LocalRepository')
    @mock.patch('udocker.utils.fileutil.FileUtil.getdata')
    @mock.patch('udocker.helper.elfpatcher.ElfPatcher.guess_elf_loader')
    def test_05_get_original_loader(self, mock_guess, mock_futils,
                                    mock_local, mock_exists, mock_path):
        """Test ElfPatcher().get_original_loader().

        Get the pathname of the original ld.so.
        """
        self._init()
        container_id = "SOME-RANDOM-ID"
        mock_exists.return_value = True
        mock_futils.return_value.strip.return_value = "ld.so"
        elfp = ElfPatcher(mock_local, container_id)
        self.assertEqual(elfp.get_original_loader(), "ld.so")

        mock_exists.return_value = False
        mock_guess.return_value = "ld.so"
        mock_futils.return_value.strip.return_value = "ld.so"
        elfp = ElfPatcher(mock_local, container_id)
        self.assertEqual(elfp.get_original_loader(), "ld.so")

    @mock.patch('os.path')
    @mock.patch('os.path.exists')
    @mock.patch('udocker.container.localrepo.LocalRepository')
    @mock.patch('udocker.helper.elfpatcher.ElfPatcher.get_original_loader')
    def test_06_get_container_loader(self, mock_gol, mock_local,
                                     mock_exists, mock_path):
        """Test ElfPatcher().get_container_loader().

        Get an absolute pathname to the container ld.so"""
        self._init()
        container_id = "SOME-RANDOM-ID"
        mock_gol.return_value = ""
        elfp = ElfPatcher(mock_local, container_id)
        self.assertEqual(elfp.get_container_loader(), "")

        mock_exists.return_value = True
        mock_gol.return_value = "ld.so"
        elfp = ElfPatcher(mock_local, container_id)
        self.assertEqual(elfp.get_container_loader(),
                         elfp._container_root + "/" + "ld.so")

    @mock.patch('os.path')
    @mock.patch('os.path.exists')
    @mock.patch('udocker.container.localrepo.LocalRepository')
    @mock.patch('udocker.utils.fileutil.FileUtil.getdata')
    def test_07_get_patch_last_path(self, mock_getdata, mock_local,
                                    mock_exists, mock_path):
        """Test ElfPatcher().get_patch_last_path().

        get last host pathname to the patched container."""
        self._init()
        container_id = "SOME-RANDOM-ID"
        mock_getdata.return_value = ""
        elfp = ElfPatcher(mock_local, container_id)
        self.assertEqual(elfp.get_patch_last_path(), "")

        mock_getdata.return_value = "/tmp"
        elfp = ElfPatcher(mock_local, container_id)
        self.assertEqual(elfp.get_patch_last_path(), "/tmp")

    @mock.patch('os.path')
    @mock.patch('os.path.exists')
    @mock.patch('udocker.container.localrepo.LocalRepository')
    @mock.patch('udocker.helper.elfpatcher.ElfPatcher.get_patch_last_path')
    @mock.patch('udocker.msg.Msg')
    def test_08_check_container(self, mock_msg, mock_lpath,
                                mock_local, mock_exists, mock_path):
        """Test ElfPatcher().check_container().

        verify if path to container is ok"""
        self._init()
        container_id = "SOME-RANDOM-ID"
        mock_lpath.return_value = "/tmp"
        elfp = ElfPatcher(mock_local, container_id)
        # with self.assertRaises(SystemExit) as epexpt:
        #     elfp.check_container()
        # self.assertEqual(epexpt.exception.code, 1)

    @mock.patch('os.path')
    @mock.patch('os.path.exists')
    @mock.patch('udocker.container.localrepo.LocalRepository')
    @mock.patch('udocker.utils.fileutil.FileUtil.getdata')
    def test_09_get_patch_last_time(self, mock_getdata, mock_local,
                                    mock_exists, mock_path):
        """Test ElfPatcher().patch_last_time().

        get time in seconds of last full patch of container"""
        self._init()
        container_id = "SOME-RANDOM-ID"
        mock_getdata.return_value = "30"
        elfp = ElfPatcher(mock_local, container_id)
        self.assertEqual(elfp.get_patch_last_time(), "30")

    @mock.patch('os.path')
    @mock.patch('os.path.exists')
    @mock.patch('udocker.container.localrepo.LocalRepository')
    @mock.patch('udocker.utils.fileutil.FileUtil.putdata')
    @mock.patch('udocker.helper.elfpatcher.ElfPatcher.guess_elf_loader')
    @mock.patch('udocker.helper.elfpatcher.ElfPatcher.select_patchelf')
    @mock.patch('udocker.helper.elfpatcher.ElfPatcher.get_container_loader')
    @mock.patch('udocker.helper.elfpatcher.ElfPatcher')
    def test_10_patch_binaries(self, mock_elfp, mock_gcl, mock_select,
                               mock_guess, mock_putdata, mock_local,
                               mock_exists, mock_path):
        """Test ElfPatcher().patch_binaries().

        Set all executables and libs to the ld.so absolute pathname"""
        self._init()
        container_id = "SOME-RANDOM-ID"
        mock_exists.return_value = True
        mock_gcl.return_value = "/usr/bin/ld"
        mock_select.return_value = "runc-arm"
        mock_putdata.side_effect = ["10", "/tmp"]
        mock_guess.return_value = "/usr/bin/ld"
        mock_elfp.return_value._container_root.return_value = "/tmp/ROOT"
        elfp = ElfPatcher(mock_local, container_id)
        self.assertTrue(elfp.patch_binaries())

    @mock.patch('os.path')
    @mock.patch('os.path.exists')
    @mock.patch('udocker.container.localrepo.LocalRepository')
    @mock.patch('udocker.helper.elfpatcher.ElfPatcher.guess_elf_loader')
    @mock.patch('udocker.helper.elfpatcher.ElfPatcher.select_patchelf')
    @mock.patch('udocker.helper.elfpatcher.ElfPatcher.get_container_loader')
    @mock.patch('udocker.helper.elfpatcher.ElfPatcher')
    def test_11_restore_binaries(self, mock_elfp, mock_gcl, mock_select,
                                 mock_guess, mock_local,
                                 mock_exists, mock_path):
        """Test ElfPatcher().restore_binaries().

        Restore all executables and libs to the original ld.so pathname"""
        self._init()
        container_id = "SOME-RANDOM-ID"
        mock_exists.return_value = True
        mock_gcl.return_value = "/usr/bin/ld"
        mock_select.return_value = "runc-arm"
        mock_guess.return_value = "/usr/bin/ld"
        mock_elfp.return_value._container_root.return_value = "/tmp/ROOT"
        elfp = ElfPatcher(mock_local, container_id)
        self.assertTrue(elfp.restore_binaries())

    @mock.patch('os.path')
    @mock.patch('os.path.exists')
    @mock.patch('udocker.container.localrepo.LocalRepository')
    @mock.patch('udocker.helper.elfpatcher.ElfPatcher.get_container_loader')
    @mock.patch('udocker.utils.fileutil.FileUtil.size')
    @mock.patch('udocker.utils.fileutil.FileUtil.copyto')
    @mock.patch('udocker.utils.fileutil.FileUtil.getdata')
    def test_12_patch_ld(self, mock_getdata,
                         mock_copyto, mock_size,
                         mock_gcl, mock_local,
                         mock_exists, mock_path):
        """Test ElfPatcher().patch_ld().

        Patch ld.so"""
        self._init()
        container_id = "SOME-RANDOM-ID"
        mock_size.return_value = -1
        elfp = ElfPatcher(mock_local, container_id)
        self.assertFalse(elfp.patch_ld())

        mock_size.return_value = 20
        mock_copyto.return_value = False
        elfp = ElfPatcher(mock_local, container_id)
        self.assertFalse(elfp.patch_ld())

        mock_size.return_value = 20
        mock_copyto.return_value = True
        mock_getdata.return_value = []
        elfp = ElfPatcher(mock_local, container_id)
        self.assertFalse(elfp.patch_ld())

        mock_size.return_value = 20
        mock_copyto.return_value = True
        mock_getdata.return_value = []
        elfp = ElfPatcher(mock_local, container_id)
        self.assertFalse(elfp.patch_ld("OUTPUT_ELF"))

    @mock.patch('udocker.msg.Msg')
    @mock.patch('os.path')
    @mock.patch('os.path.exists')
    @mock.patch('udocker.container.localrepo.LocalRepository')
    @mock.patch('udocker.helper.elfpatcher.ElfPatcher.get_container_loader')
    @mock.patch('udocker.utils.fileutil.FileUtil.size')
    @mock.patch('udocker.utils.fileutil.FileUtil.copyto')
    def test_13_restore_ld(self, mock_copyto, mock_size,
                           mock_gcl, mock_local,
                           mock_exists, mock_path, mock_msg):
        """Test ElfPatcher().restore_ld().

        Restore ld.so"""
        self._init()
        container_id = "SOME-RANDOM-ID"
        mock_size.return_value = -1
        elfp = ElfPatcher(mock_local, container_id)
        self.assertFalse(elfp.restore_ld())

        mock_size.return_value = 20
        mock_copyto.return_value = True
        elfp = ElfPatcher(mock_local, container_id)
        self.assertTrue(elfp.restore_ld())

    @mock.patch('os.path')
    @mock.patch('os.path.exists')
    @mock.patch('udocker.container.localrepo.LocalRepository')
    @mock.patch('udocker.utils.uprocess.Uprocess.get_output')
    def test_14__get_ld_config(self, mock_upout,
                               mock_local, mock_exists, mock_path):
        """Test ElfPatcher().get_ld_config().

        Get get directories from container ld.so.cache"""
        self._init()
        container_id = "SOME-RANDOM-ID"
        mock_upout.return_value = []
        elfp = ElfPatcher(mock_local, container_id)
        status = elfp._get_ld_config()
        self.assertEqual(status, [])

        # mock_upout.return_value = \
        #     "ld.so.cache => /tmp/ROOT/etc/ld.so.cache\n" \
        #     "ld.so.cache => /tmp/ROOT/etc/ld.so"
        # elfp = udocker.ElfPatcher(mock_local, container_id)
        # status = elfp._get_ld_config()
        # self.assertIsInstance(status, list)

    @mock.patch('os.path')
    @mock.patch('os.access')
    @mock.patch('os.walk')
    @mock.patch('os.path.exists')
    @mock.patch('udocker.container.localrepo.LocalRepository')
    def test_15__find_ld_libdirs(self, mock_local, mock_exists,
                                 mock_walk, mock_access, mock_path):
        """Test ElfPatcher()._find_ld_libdirs().

        search for library directories in container"""
        self._init()
        container_id = "SOME-RANDOM-ID"

        elfp = ElfPatcher(mock_local, container_id)
        status = elfp._find_ld_libdirs()
        self.assertEqual(status, [])

    @mock.patch('os.path')
    @mock.patch('os.path.exists')
    @mock.patch('udocker.container.localrepo.LocalRepository')
    def test_16_get_ld_libdirs(self, mock_local,
                               mock_exists, mock_path):
        """Test ElfPatcher().get_ld_libdirs().

        Get ld library paths"""
        self._init()
        container_id = "SOME-RANDOM-ID"

        elfp = ElfPatcher(mock_local, container_id)
        status = elfp.get_ld_libdirs()
        self.assertEqual(status, [''])

    @mock.patch('os.path')
    @mock.patch('os.path.exists')
    @mock.patch('udocker.container.localrepo.LocalRepository')
    def test_17_get_ld_library_path(self, mock_local,
                                    mock_exists, mock_path):
        """Test ElfPatcher().get_ld_library_path().

        Get ld library paths"""
        self._init()
        container_id = "SOME-RANDOM-ID"

        elfp = ElfPatcher(mock_local, container_id)
        # status = elfp.get_ld_library_path()
        # self.assertEqual(status, [''])


if __name__ == '__main__':
    unittest.main()
