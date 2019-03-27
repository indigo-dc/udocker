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

from udocker.engine.execmode import ExecutionMode
from udocker.engine.runc import RuncEngine
from udocker.engine.proot import PRootEngine
from udocker.engine.fakechroot import FakechrootEngine


def set_env():
    """Set environment variables."""
    if not os.getenv("HOME"):
        os.environ["HOME"] = os.getcwd()


class ExecutionModeTestCase(unittest.TestCase):
    """Test ExecutionMode()."""

    @classmethod
    def setUpClass(cls):
        """Setup test."""
        set_env()

    def _init(self):
        """Configure variables."""
        Config = mock.MagicMock()
        Config.hostauth_list = ("/etc/passwd", "/etc/group")
        Config.cmd = "/bin/bash"
        Config.cpu_affinity_exec_tools = (["numactl", "-C", "%s", "--", ],
                                          ["taskset", "-c", "%s", ])
        Config.valid_host_env = "HOME"
        Config.return_value.username.return_value = "user"
        Config.return_value.userhome.return_value = "/"
        Config.return_value.oskernel.return_value = "4.8.13"
        Config.location = ""
        Config.keystore = "KEYSTORE"
        Config.return_value.osversion.return_value = "OSVERSION"
        Config.return_value.arch.return_value = "ARCH"
        Config.default_execution_mode = "P1"

    @mock.patch('udocker.engine.execmode.os.path.realpath')
    @mock.patch('udocker.container.localrepo.LocalRepository')
    def test_01_init(self, mock_local, mock_realpath):
        """Test __init__()."""

        self._init()
        container_id = "CONTAINER_ID"
        mock_realpath.return_value = "/tmp"
        mock_local.cd_container.return_value = "/tmp"
        uexm = ExecutionMode(mock_local, container_id)

        self.assertEqual(uexm.localrepo, mock_local)
        self.assertEqual(uexm.container_id, "CONTAINER_ID")
        self.assertEqual(uexm.container_dir, "/tmp")
        self.assertEqual(uexm.container_root, "/tmp/ROOT")
        self.assertEqual(uexm.container_execmode, "/tmp/execmode")
        self.assertIsNone(uexm.exec_engine)
        self.assertEqual(uexm.valid_modes,
                         ("P1", "P2", "F1", "F2", "F3", "F4", "R1", "S1"))

    @mock.patch('udocker.engine.execmode.os.path')
    @mock.patch('udocker.utils.fileutil.FileUtil.getdata')
    @mock.patch('udocker.container.localrepo.LocalRepository')
    def test_02_get_mode(self, mock_local, mock_getdata, mock_path):
        """Get execution mode"""

        self._init()
        container_id = "CONTAINER_ID"
        mock_getdata.return_value.strip.return_value = None
        uexm = ExecutionMode(mock_local, container_id)
        status = uexm.get_mode()
        self.assertEqual(status, "P1")

        mock_getdata.return_value = "F3"
        uexm = ExecutionMode(mock_local, container_id)
        status = uexm.get_mode()
        self.assertEqual(status, "F3")

    @mock.patch('udocker.utils.filebind.FileBind.setup')
    @mock.patch('udocker.utils.filebind.FileBind.restore')
    @mock.patch('udocker.msg.Msg')
    @mock.patch('udocker.engine.execmode.ExecutionMode.get_mode')
    @mock.patch('udocker.engine.execmode.os.path')
    @mock.patch('udocker.container.localrepo.LocalRepository')
    @mock.patch('udocker.utils.filebind.FileBind')
    @mock.patch('udocker.helper.elfpatcher.ElfPatcher')
    @mock.patch('udocker.utils.fileutil.FileUtil')
    @mock.patch('udocker.utils.fileutil.FileUtil.putdata')
    def test_03_set_mode(self, mock_putdata, mock_futil,
                         mock_elfp, mock_fbind, mock_local,
                         mock_path, mock_getmode, mock_msg,
                         mock_restore, mock_setup):
        """Set execution mode."""

        self._init()
        container_id = "CONTAINER_ID"
        mock_getmode.side_effect = \
            ["", "P1", "R1", "R1", "F4", "P1", "F3", "P2", "P2", "F4", "F4"]
        mock_putdata.return_value = True

        uexm = ExecutionMode(mock_local, container_id)
        status = uexm.set_mode("")
        self.assertFalse(status)

        status = uexm.set_mode("P1")
        self.assertTrue(status)

        uexm.set_mode("P1")
        self.assertTrue(mock_restore.called)

        uexm.set_mode("F1")
        self.assertTrue(mock_futil.return_value.links_conv.called)

        uexm.set_mode("P2")
        self.assertTrue(mock_elfp.return_value.restore_ld.called)

        uexm.set_mode("R1")
        self.assertTrue(mock_setup.called)

        uexm.set_mode("F2")
        self.assertTrue(mock_elfp.return_value.restore_binaries.called)

        uexm.set_mode("F2")
        self.assertTrue(mock_elfp.return_value.patch_ld.called)

        uexm.set_mode("F3")
        self.assertTrue(mock_elfp.return_value.patch_ld.called and
                        mock_elfp.return_value.patch_binaries.called)

        status = uexm.set_mode("F3")
        self.assertTrue(status)

        mock_putdata.return_value = False
        uexm.set_mode("F3")
        self.assertTrue(mock_msg.return_value.err.called)

    @mock.patch('udocker.engine.execmode.ExecutionMode.get_mode')
    @mock.patch('udocker.engine.execmode.os.path')
    @mock.patch('udocker.container.localrepo.LocalRepository')
    def test_04_get_engine(self, mock_local, mock_path, mock_getmode):
        """get execution engine instance"""

        self._init()
        container_id = "CONTAINER_ID"
        mock_getmode.side_effect = ["R1", "F2", "P2"]
        uexm = ExecutionMode(mock_local, container_id)

        exec_engine = uexm.get_engine()
        self.assertIsInstance(exec_engine, RuncEngine)

        exec_engine = uexm.get_engine()
        self.assertIsInstance(exec_engine, FakechrootEngine)

        exec_engine = uexm.get_engine()
        self.assertIsInstance(exec_engine, PRootEngine)


if __name__ == '__main__':
    unittest.main()
