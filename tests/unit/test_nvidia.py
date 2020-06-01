#!/usr/bin/env python
"""
udocker unit tests: NVIDIA mode
"""
from unittest import TestCase, main
from udocker.config import Config
from udocker.engine.nvidia import NvidiaMode
try:
    from unittest.mock import patch, Mock
except ImportError:
    from mock import patch, Mock


class NvidiaModeTestCase(TestCase):
    """Test PRootEngine() class for containers execution."""

    def setUp(self):
        self.cont_id = "12345a"
        str_local = 'udocker.container.localrepo.LocalRepository'
        self.lrepo = patch(str_local)
        self.local = self.lrepo.start()
        self.mock_lrepo = Mock()
        self.local.return_value = self.mock_lrepo
        str_cd = str_local + '.cd_container'
        self.cdcont = patch(str_cd, return_value="/" + self.cont_id)
        self.mock_cdcont = self.cdcont.start()

    def tearDown(self):
        self.lrepo.stop()
        self.cdcont.stop()

    def test_01_init(self):
        """Test01 NvidiaMode() constructor."""
        cdir = "/" + self.cont_id
        nvmode = NvidiaMode(self.local, self.cont_id)
        self.assertTrue(self.mock_cdcont.called)
        self.assertEqual(nvmode.container_dir, cdir)
        self.assertEqual(nvmode.container_root, cdir + "/ROOT")
        self.assertEqual(nvmode._container_nvidia_set, cdir + "/nvidia")

    # def test_02__files_exist(self):
    #     """Test02 NvidiaMode._files_exist."""

    # def test_03__copy_files(self):
    #     """Test03 NvidiaMode._copy_files."""

    # def test_04__get_nvidia_libs(self):
    #     """Test04 NvidiaMode._get_nvidia_libs."""
    #     Config().getconf()
    #     host_dir = "/usr/lib"
    #     nvmode = NvidiaMode(self.local, self.cont_id)
    #     status = nvmode._get_nvidia_libs(host_dir)
    #     self.assertEqual(status, Config.conf['nvi_lib_list'])

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
    def test_10_set_mode(self, mock_msg, mock_mknod, mock_findhdir,
                         mock_findcdir, mock_instexist, mock_nvlibs,
                         mock_cpfiles):
        """Test10 NvidiaMode.set_mode()."""
        mock_msg.return_value.level.return_value = 0
        nvmode = NvidiaMode(self.local, self.cont_id)
        nvmode.set_mode()
        self.assertTrue(mock_msg().err.called)

        mock_mknod.return_value = None
        mock_findhdir.return_value = set()
        mock_findcdir.return_value = ""
        nvmode = NvidiaMode(self.local, self.cont_id)
        nvmode.container_dir = "/" + self.cont_id
        nvmode.set_mode()
        self.assertTrue(mock_msg().err.called)

        mock_mknod.return_value = None
        mock_findhdir.return_value = {"/usr/lib"}
        mock_findcdir.return_value = "/ROOT/usr/lib"
        mock_instexist.return_value = True
        mock_nvlibs.return_value = ["a", "b"]
        mock_cpfiles.return_value = None
        nvmode = NvidiaMode(self.local, self.cont_id)
        nvmode.container_dir = ""
        nvmode.set_mode()
        self.assertTrue(mock_msg().err.called)
        #self.assertTrue(mock_mknod.called)
        self.assertTrue(mock_findhdir.called)
        self.assertTrue(mock_findcdir.called)
        self.assertTrue(mock_instexist.called)
        #self.assertTrue(mock_nvlibs.called)
        #self.assertTrue(mock_cpfiles.called)

    @patch('udocker.engine.nvidia.os.path.exists')
    def test_11_get_mode(self, mock_path):
        """Test11 NvidiaMode.get_mode()."""
        mock_path.return_value = True
        nvmode = NvidiaMode(self.local, self.cont_id)
        status = nvmode.get_mode()
        self.assertTrue(mock_path.called)
        self.assertTrue(status)

    def test_12_get_devices(self):
        """Test12 NvidiaMode.get_devices()."""
        nvmode = NvidiaMode(self.local, self.cont_id)
        Config.conf['nvi_dev_list'] = ['/dev/nvidia', ]
        status = nvmode.get_devices()
        # self.assertEqual(status, ['/dev/nvidia', ])


if __name__ == '__main__':
    main()
