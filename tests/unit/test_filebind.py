#!/usr/bin/env python
"""
udocker unit tests: FileBind
"""

from unittest import TestCase, main
from unittest.mock import Mock, patch
from udocker.utils.filebind import FileBind
from udocker.config import Config


class FileBindTestCase(TestCase):
    """Test FileBind()."""

    def setUp(self):
        Config().getconf()
        self.bind_dir = "/.bind_host_files"
        self.orig_dir = "/.bind_orig_files"
        str_local = 'udocker.container.localrepo.LocalRepository'
        self.lrepo = patch(str_local)
        self.local = self.lrepo.start()
        self.mock_lrepo = Mock()
        self.local.return_value = self.mock_lrepo

    def tearDown(self):
        self.lrepo.stop()

    @patch('udocker.utils.filebind.os.path.realpath')
    def test_01_init(self, mock_realpath):
        """Test01 FileBind() constructor"""
        container_id = "CONTAINERID"
        mock_realpath.return_value = "/tmp"
        fbind = FileBind(self.local, container_id)
        self.assertEqual(fbind.localrepo, self.local)
        self.assertEqual(fbind.container_id, container_id)
        self.assertTrue(mock_realpath.called)
        self.assertTrue(fbind.container_root, fbind.container_dir + "/ROOT")
        self.assertTrue(
            fbind.container_bind_dir, fbind.container_root + self.bind_dir)
        self.assertTrue(
            fbind.container_orig_dir, fbind.container_dir + self.orig_dir)
        self.assertIsNone(fbind.host_bind_dir)

    @patch('udocker.utils.filebind.Msg')
    @patch('udocker.utils.filebind.os.path.isdir')
    @patch('udocker.utils.filebind.os.path.realpath')
    @patch('udocker.utils.filebind.FileUtil')
    def test_02_setup(self, mock_futil, mock_realpath, mock_isdir,
                      mock_msg):
        """Test02 FileBind().setup()."""
        mock_msg.level = 0
        container_id = "CONTAINERID"
        mock_realpath.return_value = "/tmp"
        mock_isdir.side_effect = [True, True]
        status = FileBind(self.local, container_id).setup()
        self.assertTrue(mock_isdir.called)
        self.assertTrue(status)

        mock_isdir.side_effect = [False, True]
        mock_futil.return_value.mkdir.return_value = False
        status = FileBind(self.local, container_id).setup()
        self.assertFalse(status)

        mock_isdir.side_effect = [True, False]
        mock_futil.return_value.mkdir.return_value = False
        status = FileBind(self.local, container_id).setup()
        self.assertFalse(status)

    @patch('udocker.utils.filebind.os.path.isdir')
    @patch('udocker.utils.filebind.os.path.islink')
    @patch('udocker.utils.filebind.os.path.isfile')
    @patch('udocker.utils.filebind.os.path.realpath')
    @patch('udocker.utils.filebind.os.listdir')
    @patch('udocker.utils.filebind.FileUtil')
    def test_03_restore(self, mock_futil, mock_listdir,
                        mock_realpath, mock_isfile,
                        mock_islink, mock_isdir):
        """Test03 FileBind().restore()."""
        container_id = "CONTAINERID"
        mock_realpath.return_value = "/tmp"
        mock_listdir.return_value = []
        mock_futil.return_value.remove.return_value = True

        mock_isdir.return_value = False
        fbind = FileBind(self.local, container_id)
        fbind.restore()
        self.assertFalse(mock_listdir.called)

        mock_isdir.return_value = True
        fbind = FileBind(self.local, container_id)
        fbind.restore()
        self.assertTrue(mock_listdir.called)

        mock_listdir.return_value = ["is_file1", "is_dir", "is_file2"]
        mock_isfile.side_effect = [True, False, True]
        mock_islink.side_effect = [True, False, False]
        fbind = FileBind(self.local, container_id)
        fbind.restore()
        self.assertTrue(mock_isfile.called)
        self.assertTrue(mock_islink.called)

    @patch.object(FileBind, 'setup')
    @patch('udocker.utils.filebind.FileUtil.mktmpdir')
    @patch('udocker.utils.filebind.os.path.realpath')
    @patch('udocker.utils.filebind.os.path.isfile')
    @patch('udocker.utils.filebind.os.path.exists')
    def test_04_start(self, mock_exists, mock_isfile,
                      mock_realpath, mock_mktmp, mock_setup):
        """Test04 FileBind().start()."""
        container_id = "CONTAINERID"
        mock_realpath.return_value = "/tmp"
        mock_setup.return_value = None
        files_list = ["file1", "dir1", "file2"]
        mock_mktmp.return_value = "tmpDir"
        fbind = FileBind(self.local, container_id)
        fbind.start(files_list)
        self.assertTrue(mock_mktmp.called)

        mock_isfile.side_effect = [True, False, True]
        mock_setup.return_value = None
        fbind = FileBind(self.local, container_id)
        self.assertTrue(mock_isfile.called)
        self.assertTrue(mock_exists.called)
        self.assertIsInstance(fbind.start(files_list), tuple)

    @patch('udocker.utils.filebind.os.path.realpath')
    @patch.object(FileBind, 'set_file')
    def test_05_set_list(self, mock_setfile, mock_realpath):
        """Test05 FileBind().set_list()."""
        container_id = "CONTAINERID"
        flist = ['f1', 'f2']
        mock_realpath.return_value = "/tmp"
        mock_setfile.side_effect = [None, None]
        FileBind(self.local, container_id).set_list(flist)
        self.assertTrue(mock_setfile.called)

    @patch('udocker.utils.filebind.FileUtil.copyto')
    @patch('udocker.utils.filebind.os.symlink')
    @patch('udocker.utils.filebind.os.rename')
    @patch('udocker.utils.filebind.os.path.exists')
    @patch('udocker.utils.filebind.os.path.isfile')
    @patch('udocker.utils.filebind.os.path.realpath')
    def test_06_set_file(self, mock_realpath, mock_isfile,
                         mock_exists, mock_rename, mock_sym,
                         mock_futilcopy):
        """Test06 FileBind().set_file()."""
        hfile = 'host_file'
        cfile = 'cont_file'
        container_id = "CONTAINERID"
        mock_realpath.return_value = "/tmp"
        mock_isfile.return_value = False
        mock_exists.return_value = False
        fbind = FileBind(self.local, container_id)
        fbind.set_file(hfile, cfile)
        self.assertFalse(mock_futilcopy.called)

        mock_realpath.return_value = "/tmp"
        mock_isfile.return_value = True
        mock_exists.return_value = False
        fbind = FileBind(self.local, container_id)
        fbind.set_file(hfile, cfile)
        self.assertTrue(mock_rename.called)
        self.assertTrue(mock_sym.called)

        mock_realpath.return_value = "/tmp"
        mock_isfile.return_value = True
        mock_exists.return_value = True
        fbind = FileBind(self.local, container_id)
        fbind.set_file(hfile, cfile)
        self.assertTrue(mock_futilcopy.called)

    @patch('udocker.utils.filebind.FileUtil.remove')
    @patch('udocker.utils.filebind.FileUtil.copyto')
    @patch('udocker.utils.filebind.os.path.realpath')
    def test_07_add_file(self, mock_realpath, mock_futilcp,
                         mock_futilrm):
        """Test07 FileBind().add_file()."""
        container_id = "CONTAINERID"
        mock_realpath.return_value = "/tmp"
        host_file = "host.file"
        container_file = "#container.file"
        fbind = FileBind(self.local, container_id)
        fbind.host_bind_dir = "/tmp"
        fbind.add_file(host_file, container_file)
        self.assertTrue(mock_futilrm.called)
        self.assertTrue(mock_futilcp.called)

    @patch('udocker.utils.filebind.os.path.realpath')
    def test_08_get_path(self, mock_realpath):
        """Test08 FileBind().get_path()."""
        container_id = 'CONTAINERID'
        cont_file = '/dir1/file'
        mock_realpath.return_value = "/tmp"
        fbind = FileBind(self.local, container_id)
        fbind.host_bind_dir = '/dir0'
        status = fbind.get_path(cont_file)
        self.assertEqual(status, '/dir0/#dir1#file')

    # def test_09_finish(self):
    #     """Test09 FileBind().finish()."""


if __name__ == '__main__':
    main()
