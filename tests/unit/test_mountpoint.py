#!/usr/bin/env python
"""
udocker unit tests: MountPoint
"""

import sys
from unittest import TestCase, main
from udocker.utils.mountpoint import MountPoint
from udocker.config import Config
try:
    from unittest.mock import Mock, MagicMock, patch, mock_open
except ImportError:
    from mock import Mock, MagicMock, patch, mock_open

sys.path.append('.')


class MountPointTestCase(TestCase):
    """Test MountPoint()."""

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

    @patch.object(MountPoint, 'setup')
    @patch('udocker.utils.mountpoint.os.path.realpath')
    def test_01_init(self, mock_realpath, mock_setup):
        """Test01 MountPoint() constructor"""
        container_id = "CONTAINERID"
        mock_realpath.return_value = "/tmp"
        mpoint = MountPoint(self.local, container_id)
        self.assertEqual(mpoint.localrepo, self.local)
        self.assertEqual(mpoint.container_id, container_id)
        self.assertTrue(mock_realpath.called)
        self.assertTrue(mpoint.container_root, mpoint.container_dir + "/ROOT")
        self.assertTrue(mock_setup.called)

    @patch('udocker.utils.mountpoint.Msg.err')
    @patch('udocker.utils.mountpoint.FileUtil.mkdir')
    @patch('udocker.utils.mountpoint.os.path.isdir')
    @patch('udocker.utils.mountpoint.os.path.realpath')
    def test_02_setup(self, mock_realpath, mock_isdir, mock_mkdir, mock_msg):
        """Test02 MountPoint().setup()."""
        container_id = "CONTAINERID"
        mock_realpath.return_value = "/tmp"
        mock_isdir.return_value = True
        mpoint = MountPoint(self.local, container_id)
        status = mpoint.setup()
        self.assertTrue(mock_isdir.called)
        self.assertTrue(status)

        mock_isdir.return_value = False
        mock_mkdir.return_value = True
        mpoint = MountPoint(self.local, container_id)
        status = mpoint.setup()
        self.assertTrue(mock_mkdir.called)
        self.assertTrue(status)

        mock_isdir.return_value = False
        mock_mkdir.return_value = False
        mpoint = MountPoint(self.local, container_id)
        status = mpoint.setup()
        self.assertTrue(mock_msg.called)
        self.assertFalse(status)

    @patch('udocker.utils.mountpoint.FileUtil.getvalid_path')
    @patch.object(MountPoint, 'setup')
    @patch('udocker.utils.mountpoint.os.path.realpath')
    def test_03_add(self, mock_realpath, mock_setup, mock_valid):
        """Test03 MountPoint().add()."""
        container_id = "CONTAINERID"
        mock_realpath.return_value = "/tmp"
        cpath = 'cont_path'
        mock_setup.return_value = True
        mock_valid.return_value = "/ROOT/dir1"
        mpoint = MountPoint(self.local, container_id)
        mpoint.add(cpath)
        self.assertEqual(mpoint.mountpoints[cpath], "/ROOT/dir1")

    # @patch.object(MountPoint, 'setup')
    # @patch('udocker.utils.mountpoint.os.path.realpath')
    # # def test_04_delete(self, mock_realpath, mock_setup):
    # #     """Test04 MountPoint().delete()."""

    # @patch.object(MountPoint, 'setup')
    # @patch('udocker.utils.mountpoint.os.path.realpath')
    # # def test_05_delete_all(self, mock_realpath, mock_setup):
    # #     """Test05 MountPoint().delete_all()."""

    @patch.object(MountPoint, 'delete')
    @patch.object(MountPoint, 'add')
    @patch('udocker.utils.mountpoint.Msg.err')
    @patch('udocker.utils.mountpoint.os.path.isdir')
    @patch('udocker.utils.mountpoint.os.path.islink')
    @patch('udocker.utils.mountpoint.FileUtil.putdata')
    @patch('udocker.utils.mountpoint.FileUtil.mkdir')
    @patch('udocker.utils.mountpoint.os.path.isfile')
    @patch('udocker.utils.mountpoint.os.path.exists')
    @patch.object(MountPoint, 'setup')
    @patch('udocker.utils.mountpoint.os.path.realpath')
    def test_06_create(self, mock_realpath, mock_setup, mock_exists, mock_isfile,
                       mock_mkdir, mock_putdata, mock_islink, mock_isdir, mock_msg,
                       mock_add, mock_del):
        """Test06 MountPoint().create()."""
        container_id = "CONTAINERID"
        mock_realpath.return_value = "/tmp"
        mock_setup.return_value = True
        mock_exists.return_value = False
        hpath = '/bin'
        cpath = '/ROOT/bin'
        mock_add.return_value = None
        mock_del.return_value = True
        mock_isfile.side_effect = [True, True]
        mock_mkdir.return_value = False
        mock_putdata.return_value = None
        mock_islink.return_value = True
        mock_isdir.return_value = False
        mpoint = MountPoint(self.local, container_id)
        status = mpoint.create(hpath, cpath)
        self.assertTrue(mock_add.called)
        self.assertTrue(mock_isfile.called)
        self.assertTrue(mock_mkdir.called)
        self.assertTrue(mock_putdata.called)
        self.assertFalse(mock_del.called)
        self.assertTrue(status)

        mock_exists.return_value = False
        mock_add.return_value = None
        mock_del.return_value = True
        mock_isfile.side_effect = [False, False]
        mock_mkdir.return_value = True
        mock_putdata.return_value = None
        mock_islink.return_value = True
        mock_isdir.return_value = True
        mpoint = MountPoint(self.local, container_id)
        status = mpoint.create(hpath, cpath)
        self.assertTrue(mock_mkdir.called)
        self.assertFalse(mock_msg.called)
        self.assertTrue(status)

        mock_exists.return_value = False
        mock_add.return_value = None
        mock_del.return_value = True
        mock_isfile.side_effect = [False, False]
        mock_mkdir.return_value = False
        mock_putdata.return_value = None
        mock_islink.return_value = True
        mock_isdir.return_value = True
        mpoint = MountPoint(self.local, container_id)
        status = mpoint.create(hpath, cpath)
        self.assertTrue(mock_mkdir.called)
        self.assertTrue(mock_msg.called)
        self.assertTrue(mock_del.called)
        self.assertFalse(status)

    # @patch.object(MountPoint, 'setup')
    # @patch('udocker.utils.mountpoint.os.path.realpath')
    # # def test_07_save(self, mock_realpath, mock_setup):
    # #     """Test07 MountPoint().save()."""

    # @patch.object(MountPoint, 'setup')
    # @patch('udocker.utils.mountpoint.os.path.realpath')
    # # def test_08_save_all(self, mock_realpath, mock_setup):
    # #     """Test08 MountPoint().save_all()."""

    # @patch.object(MountPoint, 'setup')
    # @patch('udocker.utils.mountpoint.os.path.realpath')
    # # def test_09_load_all(self, mock_realpath, mock_setup):
    # #     """Test09 MountPoint().load_all()."""

    # @patch.object(MountPoint, 'setup')
    # @patch('udocker.utils.mountpoint.os.path.realpath')
    # # def test_10_restore(self, mock_realpath, mock_setup):
    # #     """Test10 MountPoint().restore()."""


if __name__ == '__main__':
    main()
