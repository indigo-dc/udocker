#!/usr/bin/env python
"""
udocker unit tests: NVIDIA mode
"""
from unittest import TestCase, main
from udocker.config import Config
from udocker.container.localrepo import LocalRepository
from udocker.engine.nvidia import NvidiaMode
try:
    from unittest.mock import patch
except ImportError:
    from mock import patch


class NvidiaModeTestCase(TestCase):
    """Test PRootEngine() class for containers execution."""

    def setUp(self):
        self.conf = Config().getconf()
        self.local = LocalRepository(self.conf)
        self.cont_id = "12345a"

    def tearDown(self):
        pass

    @patch('udocker.container.localrepo.LocalRepository.cd_container', autospec=True)
    def test_01_init(self, mock_cd):
        """Test NvidiaMode() constructor."""
        mock_cd.return_value = "/" + self.cont_id
        nvmode = NvidiaMode(self.conf, self.local, self.cont_id)
        self.assertTrue(mock_cd.called)
        self.assertEqual(nvmode.container_dir, "/" + self.cont_id)
        self.assertEqual(nvmode.container_root, "/" + self.cont_id + "/ROOT")
        self.assertEqual(nvmode._container_nvidia_set, 
                         "/" + self.cont_id + "/nvidia")

    @patch.object(NvidiaMode, '_copy_files')
    @patch.object(NvidiaMode, '_get_nvidia_libs')
    @patch.object(NvidiaMode, '_installation_exists')
    @patch.object(NvidiaMode, '_find_cont_dir')
    @patch.object(NvidiaMode, '_find_host_dir')
    @patch('udocker.engine.nvidia.os.mknod')
    @patch('udocker.engine.nvidia.Msg')
    @patch('udocker.container.localrepo.LocalRepository.cd_container', autospec=True)
    def test_02_set_nvidia(self, mock_cd, mock_msg, mock_mknod, mock_findhdir,
                           mock_findcdir, mock_instexist, mock_nvlibs,
                           mock_cpfiles):
        """Test NvidiaMode.set_nvidia()."""
        mock_cd.return_value = "/" + self.cont_id
        mock_msg.return_value.level.return_value = 0
        nvmode = NvidiaMode(self.conf, self.local, self.cont_id)
        status = nvmode.set_nvidia()
        self.assertTrue(mock_msg().err.called)

        mock_mknod.return_value = None
        mock_findhdir.return_value = set()
        mock_findcdir.return_value = ""
        nvmode = NvidiaMode(self.conf, self.local, self.cont_id)
        nvmode.container_dir = "/" + self.cont_id
        status = nvmode.set_nvidia()
        self.assertTrue(mock_msg().err.called)

        mock_mknod.return_value = None
        mock_findhdir.return_value = {"/usr/lib"}
        mock_findcdir.return_value = "/ROOT/usr/lib"
        mock_instexist.return_value = True
        mock_nvlibs.return_value = ["a", "b"]
        mock_cpfiles.return_value = None
        nvmode = NvidiaMode(self.conf, self.local, self.cont_id)
        nvmode.container_dir = ""
        status = nvmode.set_nvidia()
        self.assertTrue(mock_msg().err.called)
        #self.assertTrue(mock_mknod.called)
        self.assertTrue(mock_findhdir.called)
        self.assertTrue(mock_findcdir.called)
        self.assertTrue(mock_instexist.called)
        #self.assertTrue(mock_nvlibs.called)
        #self.assertTrue(mock_cpfiles.called)

    @patch('udocker.engine.nvidia.os.path.exists')
    @patch('udocker.container.localrepo.LocalRepository.cd_container', autospec=True)
    def test_03_get_nvidia(self, mock_cd, mock_path):
        """Test NvidiaMode.get_nvidia()."""
        mock_cd.return_value = "/" + self.cont_id
        mock_path.return_value = True
        nvmode = NvidiaMode(self.conf, self.local, self.cont_id)
        status = nvmode.get_nvidia()
        self.assertTrue(mock_path.called)

    @patch('udocker.container.localrepo.LocalRepository.cd_container', autospec=True)
    def test_04_get_devices(self, mock_cd):
        """Test NvidiaMode.get_devices()."""
        mock_cd.return_value = "/" + self.cont_id
        nvmode = NvidiaMode(self.conf, self.local, self.cont_id)
        status = nvmode.get_devices()
        #self.assertEqual(status, self.conf['nvi_dev_list'])


if __name__ == '__main__':
    main()
