#!/usr/bin/env python
"""
udocker unit tests: ExecutionMode
"""

from unittest import TestCase, main
from unittest.mock import Mock, patch
from udocker.engine.execmode import ExecutionMode
from udocker.engine.proot import PRootEngine
from udocker.engine.runc import RuncEngine
from udocker.engine.fakechroot import FakechrootEngine
from udocker.engine.singularity import SingularityEngine
from udocker.config import Config


class ExecutionModeTestCase(TestCase):
    """Test ExecutionMode()."""

    def setUp(self):
        Config().getconf()
        Config().conf['hostauth_list'] = ("/etc/passwd", "/etc/group")
        Config().conf['cmd'] = "/bin/bash"
        Config().conf['cpu_affinity_exec_tools'] = \
            (["numactl", "-C", "%s", "--", ], ["taskset", "-c", "%s", ])
        Config().conf['valid_host_env'] = "HOME"
        Config().conf['username'] = "user"
        Config().conf['userhome'] = "/"
        Config().conf['oskernel'] = "4.8.13"
        Config().conf['location'] = ""
        Config().conf['keystore'] = "KEYSTORE"
        Config().conf['osversion'] = "OSVERSION"
        Config().conf['arch'] = "ARCH"
        Config().conf['default_execution_mode'] = "P1"
        self.container_id = "CONTAINER_ID"

        str_local = 'udocker.container.localrepo.LocalRepository'
        self.lrepo = patch(str_local)
        self.local = self.lrepo.start()
        self.mock_lrepo = Mock()
        self.local.return_value = self.mock_lrepo

        str_cd = str_local + '.cd_container'
        self.cdcont = patch(str_cd, return_value="/tmp")
        self.mock_cdcont = self.cdcont.start()

    def tearDown(self):
        self.lrepo.stop()
        self.cdcont.stop()

    def test_01_init(self):
        """Test01 ExecutionMode() constructor."""
        uexm = ExecutionMode(self.local, self.container_id)
        self.assertEqual(uexm.localrepo, self.local)
        self.assertEqual(uexm.container_id, "CONTAINER_ID")
        self.assertEqual(uexm.container_dir, "/tmp")
        self.assertEqual(uexm.container_root, "/tmp/ROOT")
        self.assertEqual(uexm.container_execmode, "/tmp/execmode")
        self.assertIsNone(uexm.exec_engine)
        self.assertEqual(uexm.valid_modes,
                         ("P1", "P2", "F1", "F2",
                          "F3", "F4", "R1", "R2", "R3", "S1"))

    @patch('udocker.engine.execmode.FileUtil.getdata')
    def test_02_get_mode(self, mock_getdata):
        """Test02 ExecutionMode().get_mode."""
        mock_getdata.return_value.strip.return_value = None
        uexm = ExecutionMode(self.local, self.container_id)
        status = uexm.get_mode()
        self.assertEqual(status, "P1")

        mock_getdata.return_value = "F3"
        uexm = ExecutionMode(self.local, self.container_id)
        status = uexm.get_mode()
        self.assertEqual(status, "F3")

    @patch('udocker.engine.execmode.Msg')
    @patch('udocker.engine.execmode.os.path')
    @patch('udocker.engine.execmode.FileUtil.putdata')
    @patch('udocker.engine.execmode.FileBind.setup')
    @patch('udocker.engine.execmode.ElfPatcher.get_ld_libdirs')
    @patch('udocker.engine.execmode.FileUtil.links_conv')
    @patch('udocker.engine.execmode.FileBind.restore')
    @patch('udocker.engine.execmode.FileUtil.getdata')
    @patch('udocker.engine.execmode.FileUtil')
    @patch('udocker.engine.execmode.FileBind')
    @patch('udocker.engine.execmode.ElfPatcher')
    @patch.object(ExecutionMode, 'get_mode')
    def test_03_set_mode(self, mock_getmode, mock_elfp, mock_fbind,
                         mock_futil, mock_getdata, mock_restore, mock_links,
                         mock_getld, mock_fbset, mock_putdata, mock_path,
                         mock_msg):
        """Test03 ExecutionMode().set_mode."""
        mock_msg.level = 0
        mock_getmode.side_effect = \
            ["", "P1", "R1", "R1", "F4", "P1", "F3", "P2", "P2", "F4", "F4"]
        mock_getdata.return_value = "F3"
        mock_restore.return_value = None
        mock_fbset.return_value = None
        uexm = ExecutionMode(self.local, self.container_id)
        status = uexm.set_mode("")
        self.assertTrue(mock_getmode.called)
        self.assertTrue(mock_elfp.called)
        self.assertTrue(mock_fbind.called)
        self.assertTrue(mock_futil.called)
        self.assertFalse(status)

        mock_restore.return_value = None
        mock_fbset.return_value = None
        uexm = ExecutionMode(self.local, self.container_id)
        status = uexm.set_mode("P1")
        self.assertTrue(status)

        mock_restore.return_value = None
        mock_fbset.return_value = None
        mock_links.return_value = True
        mock_getld.return_value = True
        uexm = ExecutionMode(self.local, self.container_id)
        status = uexm.set_mode("F1", True)
        self.assertTrue(status)

        mock_restore.return_value = None
        mock_fbset.return_value = None
        mock_putdata.return_value = True
        mock_path.return_value = "/tmp"
        uexm = ExecutionMode(self.local, self.container_id)
        status = uexm.set_mode("P1")
        self.assertTrue(status)

        mock_restore.return_value = None
        mock_fbset.return_value = None
        uexm = ExecutionMode(self.local, self.container_id)
        uexm.set_mode("F1")
        self.assertTrue(mock_futil.return_value.links_conv.called)

        mock_restore.return_value = None
        mock_fbset.return_value = None
        uexm = ExecutionMode(self.local, self.container_id)
        uexm.set_mode("P2")
        self.assertTrue(mock_elfp.return_value.restore_ld.called)

        mock_restore.return_value = None
        mock_fbset.return_value = None
        uexm = ExecutionMode(self.local, self.container_id)
        uexm.set_mode("F2")
        self.assertTrue(mock_elfp.return_value.restore_binaries.called)

        mock_restore.return_value = None
        mock_fbset.return_value = None
        uexm = ExecutionMode(self.local, self.container_id)
        uexm.set_mode("F2")
        self.assertTrue(mock_elfp.return_value.patch_ld.called)

        mock_restore.return_value = None
        mock_fbset.return_value = None
        uexm = ExecutionMode(self.local, self.container_id)
        uexm.set_mode("F3")
        self.assertTrue(mock_elfp.return_value.patch_ld.called and
                        mock_elfp.return_value.patch_binaries.called)

        mock_restore.return_value = None
        mock_fbset.return_value = None
        uexm = ExecutionMode(self.local, self.container_id)
        status = uexm.set_mode("F3")
        self.assertTrue(status)

    @patch.object(ExecutionMode, 'get_mode')
    def test_04_get_engine(self, mock_getmode):
        """Test04 ExecutionMode().get_engine."""
        mock_getmode.side_effect = ["R1", "F2", "P2", "S1"]
        uexm = ExecutionMode(self.local, self.container_id)
        exec_engine = uexm.get_engine()
        self.assertIsInstance(exec_engine, RuncEngine)

        uexm = ExecutionMode(self.local, self.container_id)
        exec_engine = uexm.get_engine()
        self.assertIsInstance(exec_engine, FakechrootEngine)

        uexm = ExecutionMode(self.local, self.container_id)
        exec_engine = uexm.get_engine()
        self.assertIsInstance(exec_engine, PRootEngine)

        uexm = ExecutionMode(self.local, self.container_id)
        exec_engine = uexm.get_engine()
        self.assertIsInstance(exec_engine, SingularityEngine)


if __name__ == '__main__':
    main()
