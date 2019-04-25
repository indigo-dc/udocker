#!/usr/bin/env python
"""
udocker unit tests: ExecutionMode
"""

import sys
from unittest import TestCase, main
try:
    from unittest.mock import Mock, MagicMock, patch, mock_open
except ImportError:
    from mock import Mock, MagicMock, patch, mock_open

sys.path.append('.')

from udocker.engine.execmode import ExecutionMode
from udocker.config import Config
from udocker.container.localrepo import LocalRepository
from udocker.engine.runc import RuncEngine
from udocker.engine.proot import PRootEngine
from udocker.engine.fakechroot import FakechrootEngine


class ExecutionModeTestCase(TestCase):
    """Test ExecutionMode()."""

    def setUp(self):
        self.conf = Config().getconf()
        self.conf['hostauth_list'] = ("/etc/passwd", "/etc/group")
        self.conf['cmd'] = "/bin/bash"
        self.conf['cpu_affinity_exec_tools'] = (["numactl", "-C", "%s", "--", ],
                                                ["taskset", "-c", "%s", ])
        self.conf['valid_host_env'] = "HOME"
        self.conf['username'] = "user"
        self.conf['userhome'] = "/"
        self.conf['oskernel'] = "4.8.13"
        self.conf['location'] = ""
        self.conf['keystore'] = "KEYSTORE"
        self.conf['osversion'] = "OSVERSION"
        self.conf['arch'] = "ARCH"
        self.conf['default_execution_mode'] = "P1"

        container_id = "CONTAINER_ID"
        self.local = LocalRepository(self.conf)
        self.uexm = ExecutionMode(self.conf, self.local, container_id)

    def tearDown(self):
        pass

    @patch('udocker.engine.execmode.os.path.realpath')
    @patch('udocker.container.localrepo.LocalRepository.cd_container')
    def test_01_init(self, mock_cdcont, mock_realpath):
        """Test __init__()."""
        mock_realpath.return_value = "/tmp"
        mock_cdcont.return_value = "/tmp"

        self.assertEqual(self.uexm.localrepo, self.local)
        self.assertEqual(self.uexm.container_id, "CONTAINER_ID")
        # self.assertEqual(self.uexm.container_dir, "/tmp")
        # self.assertEqual(self.uexm.container_root, "/tmp/ROOT")
        # self.assertEqual(self.uexm.container_execmode, "/tmp/execmode")
        self.assertIsNone(self.uexm.exec_engine)
        self.assertEqual(self.uexm.valid_modes,
                         ("P1", "P2", "F1", "F2", "F3", "F4", "R1", "S1"))

    @patch('udocker.engine.execmode.os.path')
    @patch('udocker.utils.fileutil.FileUtil.getdata')
    @patch('udocker.container.localrepo.LocalRepository')
    def test_02_get_mode(self, mock_local, mock_getdata, mock_path):
        """Get execution mode"""
        mock_getdata.return_value.strip.return_value = None
        status = self.uexm.get_mode()
        self.assertEqual(status, "P1")

        mock_getdata.return_value = "F3"
        status = self.uexm.get_mode()
        self.assertEqual(status, "F3")

    # @patch('udocker.utils.filebind.FileBind.setup')
    # @patch('udocker.utils.filebind.FileBind.restore')
    # @patch('udocker.msg.Msg')
    # @patch('udocker.engine.execmode.ExecutionMode.get_mode')
    # @patch('udocker.engine.execmode.os.path')
    # @patch('udocker.container.localrepo.LocalRepository')
    # @patch('udocker.utils.filebind.FileBind')
    # @patch('udocker.helper.elfpatcher.ElfPatcher')
    # @patch('udocker.utils.fileutil.FileUtil')
    # @patch('udocker.utils.fileutil.FileUtil.putdata')
    # def test_03_set_mode(self, mock_putdata, mock_futil,
    #                      mock_elfp, mock_fbind, mock_local,
    #                      mock_path, mock_getmode, mock_msg,
    #                      mock_restore, mock_setup):
    #     """Set execution mode."""
    #     mock_getmode.side_effect = \
    #         ["", "P1", "R1", "R1", "F4", "P1", "F3", "P2", "P2", "F4", "F4"]
    #     mock_putdata.return_value = True
    #     mock_path.return_value = "/tmp"
    #     status = self.uexm.set_mode("")
    #     self.assertFalse(status)
    #
    #     status = self.uexm.set_mode("P1")
    #     self.assertTrue(status)
    #
    #     self.uexm.set_mode("P1")
    #     self.assertTrue(mock_restore.called)
    #
    #     self.uexm.set_mode("F1")
    #     self.assertTrue(mock_futil.return_value.links_conv.called)
    #
    #     self.uexm.set_mode("P2")
    #     self.assertTrue(mock_elfp.return_value.restore_ld.called)
    #
    #     self.uexm.set_mode("R1")
    #     self.assertTrue(mock_setup.called)
    #
    #     self.uexm.set_mode("F2")
    #     self.assertTrue(mock_elfp.return_value.restore_binaries.called)
    #
    #     self.uexm.set_mode("F2")
    #     self.assertTrue(mock_elfp.return_value.patch_ld.called)
    #
    #     self.uexm.set_mode("F3")
    #     self.assertTrue(mock_elfp.return_value.patch_ld.called and
    #                     mock_elfp.return_value.patch_binaries.called)
    #
    #     status = self.uexm.set_mode("F3")
    #     self.assertTrue(status)
    #
    #     mock_putdata.return_value = False
    #     self.uexm.set_mode("F3")
    #     self.assertTrue(mock_msg.return_value.err.called)

    @patch('udocker.engine.execmode.ExecutionMode.get_mode')
    @patch('udocker.engine.execmode.os.path')
    @patch('udocker.container.localrepo.LocalRepository')
    def test_04_get_engine(self, mock_local, mock_path, mock_getmode):
        """get execution engine instance"""
        mock_getmode.side_effect = ["R1", "F2", "P2"]
        exec_engine = self.uexm.get_engine()
        self.assertIsInstance(exec_engine, RuncEngine)

        exec_engine = self.uexm.get_engine()
        self.assertIsInstance(exec_engine, FakechrootEngine)

        exec_engine = self.uexm.get_engine()
        self.assertIsInstance(exec_engine, PRootEngine)


if __name__ == '__main__':
    main()
