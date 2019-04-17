#!/usr/bin/env python2
"""
udocker unit tests: FileBind
"""

import sys
from unittest import TestCase, main
try:
    from unittest.mock import Mock, MagicMock, patch, mock_open
except ImportError:
    from mock import Mock, MagicMock, patch, mock_open

sys.path.append('.')

from udocker.utils.filebind import FileBind
from udocker.config import Config


class FileBindTestCase(TestCase):
    """Test FileBind()."""

    def setUp(self):
        self.conf = Config().getconf()
        self.bind_dir = "/.bind_host_files"
        self.orig_dir = "/.bind_orig_files"

    def tearDown(self):
        pass

    @patch('udocker.container.localrepo.LocalRepository')
    @patch('udocker.utils.filebind.os.path.realpath')
    def test_01_init(self, mock_realpath, mock_local):
        """Test FileBind() constructor"""
        container_id = "CONTAINERID"
        mock_realpath.return_value = "/tmp"
        fbind = FileBind(self.conf, mock_local, container_id)
        self.assertEqual(fbind.localrepo, mock_local)
        self.assertEqual(fbind.container_id, container_id)
        self.assertTrue(mock_realpath.called)
        self.assertTrue(fbind.container_root, fbind.container_dir + "/ROOT")
        self.assertTrue(
            fbind.container_bind_dir, fbind.container_root + self.bind_dir)
        self.assertTrue(
            fbind.container_orig_dir, fbind.container_dir + self.orig_dir)
        self.assertIsNone(fbind.host_bind_dir)

    @patch('udocker.msg.Msg')
    @patch('udocker.container.localrepo.LocalRepository')
    @patch('udocker.utils.filebind.os.path.isdir')
    @patch('udocker.utils.filebind.os.path.realpath')
    @patch('udocker.utils.fileutil.FileUtil')
    def test_02_setup(self, mock_futil, mock_realpath, mock_isdir,
                      mock_local, mock_msg):
        """Test FileBind().setup().
        Prepare container for FileBind.
        """
        mock_msg.level = 0
        container_id = "CONTAINERID"
        mock_realpath.return_value = "/tmp"
        mock_isdir.return_value = True
        status = FileBind(self.conf, mock_local, container_id).setup()
        self.assertTrue(mock_isdir.called)
        self.assertTrue(status)

        mock_isdir.return_value = False
        mock_futil.return_value.mkdir.return_value = False
        status = FileBind(self.conf, mock_local, container_id).setup()
        self.assertFalse(status)

    @patch('udocker.container.localrepo.LocalRepository')
    @patch('udocker.utils.filebind.os.path.isdir')
    @patch('udocker.utils.filebind.os.path.islink')
    @patch('udocker.utils.filebind.os.path.isfile')
    @patch('udocker.utils.filebind.os.path.realpath')
    @patch('udocker.utils.filebind.os.listdir')
    @patch('udocker.utils.fileutil.FileUtil')
    def test_03_restore(self, mock_futil, mock_listdir,
                        mock_realpath, mock_isfile,
                        mock_islink, mock_isdir, mock_local):
        """Test FileBind().restore().
        Restore container files after FileBind
        """
        container_id = "CONTAINERID"
        mock_realpath.return_value = "/tmp"
        mock_listdir.return_value = []
        mock_futil.return_value.remove.return_value = True

        mock_isdir.return_value = False
        fbind = FileBind(self.conf, mock_local, container_id)
        status = fbind.restore()
        self.assertFalse(mock_listdir.called)

        mock_isdir.return_value = True
        fbind = FileBind(self.conf, mock_local, container_id)
        status = fbind.restore()
        self.assertTrue(mock_listdir.called)

        mock_listdir.return_value = ["is_file1", "is_dir", "is_file2"]
        mock_isfile.side_effect = [True, False, True]
        mock_islink.side_effect = [True, False, False]
        status = fbind.restore()
        self.assertTrue(mock_isfile.called)
        self.assertTrue(mock_islink.called)

    @patch('udocker.container.localrepo.LocalRepository')
    @patch('udocker.utils.fileutil.FileUtil.mktmp')
    @patch('udocker.utils.filebind.os.path.realpath')
    @patch('udocker.utils.filebind.os.path.isfile')
    @patch('udocker.utils.filebind.os.path.exists')
    def test_04_start(self, mock_exists, mock_isfile,
                      mock_realpath, mock_mktmp, mock_local):
        """Test FileBind().start().
        Prepare to run.
        """
        container_id = "CONTAINERID"
        mock_realpath.return_value = "/tmp"
        files_list = ["file1", "dir1", "file2"]
        mock_mktmp.return_value = "tmpDir"
        fbind = FileBind(self.conf, mock_local, container_id)
        fbind.start(files_list)
        self.assertTrue(mock_mktmp.called)

        mock_isfile.side_effect = [True, False, True]
        self.assertTrue(mock_isfile.called)
        self.assertTrue(mock_exists.called)
        self.assertIsInstance(fbind.start(files_list), tuple)

    @patch('udocker.container.localrepo.LocalRepository')
    def test_05_finish(self, mock_local):
        """Test FileBind().finish().
        Cleanup after run.
        """
        pass

    @patch('udocker.container.localrepo.LocalRepository')
    @patch('udocker.utils.fileutil.FileUtil.remove')
    @patch('udocker.utils.fileutil.FileUtil.copyto')
    @patch('udocker.utils.filebind.os.path.realpath')
    def test_06_add(self, mock_realpath, mock_futilcp,
                    mock_futilrm, mock_local):
        """Test FileBind().add().
        Add file to be made available inside container.
        """
        container_id = "CONTAINERID"
        mock_realpath.return_value = "/tmp"
        host_file = "host.file"
        container_file = "#container.file"
        fbind = FileBind(self.conf, mock_local, container_id)
        fbind.host_bind_dir = "/tmp"
        fbind.add(host_file, container_file)
        self.assertTrue(mock_futilrm.called)
        self.assertTrue(mock_futilcp.called)


if __name__ == '__main__':
    main()
