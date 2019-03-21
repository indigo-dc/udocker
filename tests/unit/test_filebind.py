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
import unittest
import mock

from udocker.utils.filebind import FileBind


def set_env():
    """Set environment variables."""
    if not os.getenv("HOME"):
        os.environ["HOME"] = os.getcwd()


class FileBindTestCase(unittest.TestCase):
    """Test FileBind()."""

    @classmethod
    def setUpClass(cls):
        """Setup test."""
        set_env()

    def _init(self):
        """Configure variables."""
        self.bind_dir = "/.bind_host_files"
        self.orig_dir = "/.bind_orig_files"

    @mock.patch('udocker.container.localrepo.LocalRepository')
    @mock.patch('os.path.realpath')
    def test_01_init(self, mock_realpath, mock_local):
        """Test FileBind()."""
        self._init()

        container_id = "CONTAINERID"
        mock_realpath.return_value = "/tmp"
        fbind = FileBind(mock_local, container_id)
        self.assertEqual(fbind.localrepo, mock_local)
        self.assertEqual(fbind.container_id, container_id)
        self.assertTrue(mock_realpath.called)
        self.assertTrue(fbind.container_root, fbind.container_dir + "/ROOT")
        self.assertTrue(
            fbind.container_bind_dir, fbind.container_root + self.bind_dir)
        self.assertTrue(
            fbind.container_orig_dir, fbind.container_dir + self.orig_dir)
        self.assertIsNone(fbind.host_bind_dir)

    @mock.patch('udocker.msg.Msg')
    @mock.patch('udocker.container.localrepo.LocalRepository')
    @mock.patch('os.path.isdir')
    @mock.patch('os.path.realpath')
    @mock.patch('udocker.utils.fileutil.FileUtil')
    def test_02_setup(self, mock_futil, mock_realpath, mock_isdir,
                      mock_local, mock_msg):
        """Test FileBind().setup().

        Prepare container for FileBind.
        """
        self._init()
        mock_msg.level = 0

        container_id = "CONTAINERID"
        mock_realpath.return_value = "/tmp"

        mock_isdir.return_value = True
        status = FileBind(mock_local, container_id).setup()
        self.assertTrue(mock_isdir.called)
        self.assertTrue(status)

        mock_isdir.return_value = False
        mock_futil.return_value.mkdir.return_value = False
        status = FileBind(mock_local, container_id).setup()
        self.assertFalse(status)

    @mock.patch('udocker.container.localrepo.LocalRepository')
    @mock.patch('os.path.isdir')
    @mock.patch('os.path.islink')
    @mock.patch('os.path.isfile')
    @mock.patch('os.path.realpath')
    @mock.patch('udocker.config.Config')
    @mock.patch('os.listdir')
    @mock.patch('udocker.utils.fileutil.FileUtil')
    def test_03_restore(self, mock_futil, mock_listdir,
                        mock_config, mock_realpath, mock_isfile,
                        mock_islink, mock_isdir, mock_local):
        """Test FileBind().restore().

        Restore container files after FileBind
        """
        self._init()

        container_id = "CONTAINERID"
        mock_realpath.return_value = "/tmp"
        mock_listdir.return_value = []
        mock_config.return_value.tmpdir.return_value = "/tmp"
        mock_futil.return_value.remove.return_value = True

        mock_isdir.return_value = False
        fbind = FileBind(mock_local, container_id)
        status = fbind.restore()
        self.assertFalse(mock_listdir.called)

        mock_isdir.return_value = True
        fbind = FileBind(mock_local, container_id)
        status = fbind.restore()
        self.assertTrue(mock_listdir.called)

        mock_listdir.return_value = ["is_file1", "is_dir", "is_file2"]
        mock_isfile.side_effect = [True, False, True]
        mock_islink.side_effect = [True, False, False]
        status = fbind.restore()
        self.assertTrue(mock_isfile.called)
        self.assertTrue(mock_islink.called)

    @mock.patch('udocker.container.localrepo.LocalRepository')
    @mock.patch('udocker.utils.fileutil.FileUtil')
    @mock.patch('os.path.realpath')
    @mock.patch('os.path.isfile')
    @mock.patch('os.path.exists')
    def test_04_start(self, mock_exists, mock_isfile,
                      mock_realpath, mock_futil, mock_local):
        """Test FileBind().start().

        Prepare to run.
        """
        self._init()

        container_id = "CONTAINERID"
        mock_realpath.return_value = "/tmp"
        files_list = ["file1", "dir1", "file2"]

        mock_futil.return_value.mktmp.return_value = "tmpDir"
        fbind = FileBind(mock_local, container_id)
        fbind.start(files_list)
        self.assertTrue(mock_futil.called)

        mock_isfile.side_effect = [True, False, True]
        self.assertTrue(mock_isfile.called)
        self.assertTrue(mock_exists.called)

        self.assertIsInstance(fbind.start(files_list), tuple)

    @mock.patch('udocker.container.localrepo.LocalRepository')
    def test_05_finish(self, mock_local):
        """Test FileBind().finish().

        Cleanup after run.
        """
        pass

    @mock.patch('udocker.container.localrepo.LocalRepository')
    @mock.patch('udocker.utils.fileutil.FileUtil')
    @mock.patch('os.path.realpath')
    def test_06_add(self, mock_realpath, mock_futil, mock_local):
        """Test FileBind().add().

        Add file to be made available inside container.
        """
        self._init()

        container_id = "CONTAINERID"
        mock_realpath.return_value = "/tmp"
        host_file = "host.file"
        container_file = "#container.file"

        fbind = FileBind(mock_local, container_id)
        fbind.host_bind_dir = "/tmp"
        fbind.add(host_file, container_file)
        self.assertTrue(mock_futil.return_value.remove.called)
        self.assertTrue(mock_futil.return_value.copyto.called)
