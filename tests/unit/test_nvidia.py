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
        Config().getconf()
        self.local = LocalRepository()
        self.cont_id = "12345a"

    def tearDown(self):
        pass

    @patch('udocker.container.localrepo.LocalRepository.cd_container', autospec=True)
    def test_01_init(self, mock_cd):
        """Test01 NvidiaMode() constructor."""
        mock_cd.return_value = "/" + self.cont_id
        nvmode = NvidiaMode(self.local, self.cont_id)
        self.assertTrue(mock_cd.called)
        self.assertEqual(nvmode.container_dir, "/" + self.cont_id)
        self.assertEqual(nvmode.container_root, "/" + self.cont_id + "/ROOT")
        self.assertEqual(nvmode._container_nvidia_set, 
                         "/" + self.cont_id + "/nvidia")

    # def test_02__files_exist(self):
    #     """Test02 NvidiaMode._files_exist."""

    # def test_03__copy_files(self):
    #     """Test03 NvidiaMode._copy_files."""

    # def test_04__get_nvidia_libs(self):
    #     """Test04 NvidiaMode._get_nvidia_libs."""

    # def test_05__find_host_dir_ldconfig(self):
    #     """Test05 NvidiaMode._find_host_dir_ldconfig."""

    # def test_06__find_host_dir_ldpath(self):
    #     """Test06 NvidiaMode._find_host_dir_ldpath."""

    # def test_07__find_host_dir(self):
    #     """Test07 NvidiaMode._find_host_dir."""

    # def test_08__find_cont_dir(self):
    #     """Test08 NvidiaMode._find_cont_dir."""

    # def test_09__installation_exists(self):
    #     """Test09 NvidiaMode._installation_exists."""

    @patch.object(NvidiaMode, '_copy_files')
    @patch.object(NvidiaMode, '_get_nvidia_libs')
    @patch.object(NvidiaMode, '_installation_exists')
    @patch.object(NvidiaMode, '_find_cont_dir')
    @patch.object(NvidiaMode, '_find_host_dir')
    @patch('udocker.engine.nvidia.os.mknod')
    @patch('udocker.engine.nvidia.Msg')
    @patch('udocker.container.localrepo.LocalRepository.cd_container', autospec=True)
    def test_10_set_mode(self, mock_cd, mock_msg, mock_mknod, mock_findhdir,
                         mock_findcdir, mock_instexist, mock_nvlibs,
                         mock_cpfiles):
        """Test10 NvidiaMode.set_mode()."""
        mock_cd.return_value = "/" + self.cont_id
        mock_msg.return_value.level.return_value = 0
        nvmode = NvidiaMode(self.local, self.cont_id)
        status = nvmode.set_mode()
        self.assertTrue(mock_msg().err.called)

        mock_mknod.return_value = None
        mock_findhdir.return_value = set()
        mock_findcdir.return_value = ""
        nvmode = NvidiaMode(self.local, self.cont_id)
        nvmode.container_dir = "/" + self.cont_id
        status = nvmode.set_mode()
        self.assertTrue(mock_msg().err.called)

        mock_mknod.return_value = None
        mock_findhdir.return_value = {"/usr/lib"}
        mock_findcdir.return_value = "/ROOT/usr/lib"
        mock_instexist.return_value = True
        mock_nvlibs.return_value = ["a", "b"]
        mock_cpfiles.return_value = None
        nvmode = NvidiaMode(self.local, self.cont_id)
        nvmode.container_dir = ""
        status = nvmode.set_mode()
        self.assertTrue(mock_msg().err.called)
        #self.assertTrue(mock_mknod.called)
        self.assertTrue(mock_findhdir.called)
        self.assertTrue(mock_findcdir.called)
        self.assertTrue(mock_instexist.called)
        #self.assertTrue(mock_nvlibs.called)
        #self.assertTrue(mock_cpfiles.called)

    @patch('udocker.engine.nvidia.os.path.exists')
    @patch('udocker.container.localrepo.LocalRepository.cd_container', autospec=True)
    def test_11_get_mode(self, mock_cd, mock_path):
        """Test11 NvidiaMode.get_mode()."""
        mock_cd.return_value = "/" + self.cont_id
        mock_path.return_value = True
        nvmode = NvidiaMode(self.local, self.cont_id)
        status = nvmode.get_mode()
        self.assertTrue(mock_path.called)

    @patch('udocker.container.localrepo.LocalRepository.cd_container', autospec=True)
    def test_12_get_devices(self, mock_cd):
        """Test12 NvidiaMode.get_devices()."""
        mock_cd.return_value = "/" + self.cont_id
        nvmode = NvidiaMode(self.local, self.cont_id)
        status = nvmode.get_devices()
        #self.assertEqual(status, self.conf['nvi_dev_list'])


if __name__ == '__main__':
    main()
