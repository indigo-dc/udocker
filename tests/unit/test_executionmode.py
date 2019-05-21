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
from udocker.engine.proot import PRootEngine
from udocker.engine.runc import RuncEngine
from udocker.engine.fakechroot import FakechrootEngine
from udocker.engine.singularity import SingularityEngine
from udocker.config import Config
from udocker.container.localrepo import LocalRepository


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

        self.container_id = "CONTAINER_ID"
        self.local = LocalRepository(self.conf)

    def tearDown(self):
        pass

    @patch('udocker.engine.execmode.os.path.realpath')
    @patch('udocker.container.localrepo.LocalRepository.cd_container', autospec=True)
    def test_01_init(self, mock_cdcont, mock_realpath):
        """Test __init__()."""
        mock_realpath.return_value = "/tmp"
        mock_cdcont.return_value = "/tmp"
        uexm = ExecutionMode(self.conf, self.local, self.container_id)
        self.assertEqual(uexm.localrepo, self.local)
        self.assertEqual(uexm.container_id, "CONTAINER_ID")
        # self.assertEqual(uexm.container_dir, "/tmp")
        # self.assertEqual(uexm.container_root, "/tmp/ROOT")
        # self.assertEqual(uexm.container_execmode, "/tmp/execmode")
        self.assertIsNone(uexm.exec_engine)
        self.assertEqual(uexm.valid_modes,
                         ("P1", "P2", "F1", "F2", "F3", "F4", "R1", "S1"))

    @patch('udocker.engine.execmode.os.path')
    @patch('udocker.engine.execmode.FileUtil.getdata')
    def test_02_get_mode(self, mock_getdata, mock_path):
        """Get execution mode"""
        mock_getdata.return_value.strip.return_value = None
        uexm = ExecutionMode(self.conf, self.local, self.container_id)
        status = uexm.get_mode()
        self.assertEqual(status, "P1")

        mock_getdata.return_value = "F3"
        uexm = ExecutionMode(self.conf, self.local, self.container_id)
        status = uexm.get_mode()
        self.assertEqual(status, "F3")

    @patch('udocker.engine.execmode.FileBind.setup')
    @patch('udocker.engine.execmode.FileBind.restore')
    @patch('udocker.engine.execmode.Msg')
    @patch('udocker.engine.execmode.ExecutionMode.get_mode')
    @patch('udocker.engine.execmode.os.path')
    @patch('udocker.engine.execmode.FileBind')
    @patch('udocker.engine.execmode.ElfPatcher')
    @patch('udocker.engine.execmode.FileUtil')
    @patch('udocker.engine.execmode.FileUtil.putdata')
    def test_03_set_mode(self, mock_putdata, mock_futil,
                         mock_elfp, mock_fbind,
                         mock_path, mock_getmode, mock_msg,
                         mock_restore, mock_setup):
        """Set execution mode."""
        mock_getmode.side_effect = \
            ["", "P1", "R1", "R1", "F4", "P1", "F3", "P2", "P2", "F4", "F4"]
        mock_putdata.return_value = True
        mock_path.return_value = "/tmp"
        uexm = ExecutionMode(self.conf, self.local, self.container_id)
        status = uexm.set_mode("")
        self.assertFalse(status)

        uexm = ExecutionMode(self.conf, self.local, self.container_id)
        status = uexm.set_mode("P1")
        self.assertTrue(status)

        uexm = ExecutionMode(self.conf, self.local, self.container_id)
        uexm.set_mode("P1")
        #self.assertTrue(mock_restore.called)

        uexm = ExecutionMode(self.conf, self.local, self.container_id)
        uexm.set_mode("F1")
        self.assertTrue(mock_futil.return_value.links_conv.called)

        uexm = ExecutionMode(self.conf, self.local, self.container_id)
        uexm.set_mode("P2")
        self.assertTrue(mock_elfp.return_value.restore_ld.called)

        uexm = ExecutionMode(self.conf, self.local, self.container_id)
        uexm.set_mode("R1")
        #self.assertTrue(mock_setup.called)

        uexm = ExecutionMode(self.conf, self.local, self.container_id)
        uexm.set_mode("F2")
        self.assertTrue(mock_elfp.return_value.restore_binaries.called)

        uexm = ExecutionMode(self.conf, self.local, self.container_id)
        uexm.set_mode("F2")
        self.assertTrue(mock_elfp.return_value.patch_ld.called)

        uexm = ExecutionMode(self.conf, self.local, self.container_id)
        uexm.set_mode("F3")
        self.assertTrue(mock_elfp.return_value.patch_ld.called and
                        mock_elfp.return_value.patch_binaries.called)

        uexm = ExecutionMode(self.conf, self.local, self.container_id)
        status = uexm.set_mode("F3")
        self.assertTrue(status)

        mock_putdata.return_value = False
        uexm = ExecutionMode(self.conf, self.local, self.container_id)
        uexm.set_mode("F3")
        self.assertTrue(mock_msg.return_value.err.called)

    @patch.object(ExecutionMode, 'get_mode')
    def test_04_get_engine(self, mock_getmode):
        """get execution engine instance"""
        mock_getmode.side_effect = ["R1", "F2", "P2", "S1"]
        uexm = ExecutionMode(self.conf, self.local, self.container_id)
        exec_engine = uexm.get_engine()
        self.assertIsInstance(exec_engine, RuncEngine)

        uexm = ExecutionMode(self.conf, self.local, self.container_id)
        exec_engine = uexm.get_engine()
        self.assertIsInstance(exec_engine, FakechrootEngine)

        uexm = ExecutionMode(self.conf, self.local, self.container_id)
        exec_engine = uexm.get_engine()
        self.assertIsInstance(exec_engine, PRootEngine)

        uexm = ExecutionMode(self.conf, self.local, self.container_id)
        exec_engine = uexm.get_engine()
        self.assertIsInstance(exec_engine, SingularityEngine)


if __name__ == '__main__':
    main()
