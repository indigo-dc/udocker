#!/usr/bin/env python
"""
udocker unit tests: NVIDIA mode
"""

from unittest import TestCase, main
from unittest.mock import patch, Mock
from udocker.config import Config
from udocker.engine.nvidia import NvidiaMode


class NvidiaModeTestCase(TestCase):
    """Test PRootEngine() class for containers execution."""

    def setUp(self):
        Config().getconf()
        Config().conf['nvi_dev_list'] = ['/dev/nvidia']
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

    @patch('udocker.engine.nvidia.os.path.exists')
    def test_02__files_exist(self, mock_exists):
        """Test02 NvidiaMode._files_exist."""
        cont_dst_dir = "/home/.udocker/container"
        files_list = ["a", "b"]
        mock_exists.return_value = False
        nvmode = NvidiaMode(self.local, self.cont_id)
        nvmode._files_exist(cont_dst_dir, files_list)
        self.assertTrue(mock_exists.called)

    @patch('udocker.engine.nvidia.Msg')
    @patch('udocker.engine.nvidia.os.access')
    @patch('udocker.engine.nvidia.stat')
    @patch('udocker.engine.nvidia.shutil.copy2')
    @patch('udocker.engine.nvidia.os.symlink')
    @patch('udocker.engine.nvidia.os.readlink')
    @patch('udocker.engine.nvidia.os.chmod')
    @patch('udocker.engine.nvidia.os.makedirs')
    @patch('udocker.engine.nvidia.os.path.isdir')
    @patch('udocker.engine.nvidia.os.path.dirname')
    @patch('udocker.engine.nvidia.os.remove')
    @patch('udocker.engine.nvidia.os.path.islink')
    @patch('udocker.engine.nvidia.os.path.isfile')
    def test_03__copy_files(self, mock_isfile, mock_islink, mock_rm,
                            mock_dirname, mock_isdir, mock_mkdir, mock_chmod,
                            mock_readln, mock_symln, mock_copy2, mock_stat,
                            mock_access, mock_msg):
        """Test03 NvidiaMode._copy_files."""
        hsrc_dir = "/usr/lib"
        cdst_dir = "/hone/.udocker/cont/ROOT/usr/lib"
        flist = ["a"]
        force = False
        mock_msg.level = 0
        mock_isfile.side_effect = [True, False]
        mock_islink.side_effect = [True, False]
        mock_rm.return_value = None
        nvmode = NvidiaMode(self.local, self.cont_id)
        status = nvmode._copy_files(hsrc_dir, cdst_dir, flist, force)
        self.assertFalse(status)
        self.assertTrue(mock_isfile.called)

        force = True
        mock_msg.level = 0
        mock_isfile.side_effect = [True, True]
        mock_islink.side_effect = [True, False]
        mock_dirname.side_effect = [None, None]
        mock_rm.return_value = None
        mock_isdir.return_value = True
        mock_mkdir.return_value = None
        mock_chmod.side_effect = [644, 755]
        mock_readln.return_value = "/usr/xxx"
        mock_symln.return_value = None
        mock_copy2.return_value = None
        mock_stat.side_effect = [444, 222, 111, 111]
        mock_access.return_value = False
        nvmode = NvidiaMode(self.local, self.cont_id)
        status = nvmode._copy_files(hsrc_dir, cdst_dir, flist, force)
        self.assertTrue(status)
        self.assertTrue(mock_isfile.called)
        self.assertTrue(mock_rm.called)

    @patch('udocker.engine.nvidia.glob.glob')
    def test_04__get_nvidia_libs(self, mock_glob):
        """Test04 NvidiaMode._get_nvidia_libs."""
        host_dir = "/usr/lib"
        Config.conf['nvi_lib_list'] = ['/lib/libnvidia.so']
        mock_glob.return_value = ['/lib/libnvidia.so']
        nvmode = NvidiaMode(self.local, self.cont_id)
        status = nvmode._get_nvidia_libs(host_dir)
        self.assertEqual(status, Config.conf['nvi_lib_list'])

    # @patch('udocker.engine.nvidia.os.path.realpath')
    # @patch('udocker.engine.nvidia.Uprocess.get_output')
    # def test_05__find_host_dir_ldconfig(self, mock_uproc, mock_realp):
    #     """Test05 NvidiaMode._find_host_dir_ldconfig."""
    #     res_set = set()
    #     mock_uproc.return_value = \
    #       "libnvidia-cfg.so.1 (libc6,x86-64) => \
    #       /lib/x86_64-linux-gnu/libnvidia-cfg.so.1"
    #     mock_realp.return_value = "/lib/x86_64-linux-gnu/libnvidia-cfg.so.1"
    #     res_set.add("/lib/x86_64-linux-gnu/")
    #     nvmode = NvidiaMode(self.local, self.cont_id)
    #     status = nvmode._find_host_dir_ldconfig()
    #     self.assertEqual(status, res_set)

    # def test_06__find_host_dir_ldpath(self):
    #     """Test06 NvidiaMode._find_host_dir_ldpath."""

    @patch.object(NvidiaMode, '_find_host_dir_ldconfig')
    @patch.object(NvidiaMode, '_find_host_dir_ldpath')
    @patch('udocker.engine.nvidia.Msg')
    def test_07__find_host_dir(self, mock_msg, mock_ldpath, mock_ldconf):
        """Test07 NvidiaMode._find_host_dir."""
        res = set()
        mock_msg.return_value.level.return_value = 0
        mock_ldpath.side_effect = [res, res]
        mock_ldconf.return_value = res
        nvmode = NvidiaMode(self.local, self.cont_id)
        status = nvmode._find_host_dir()
        self.assertEqual(status, res)
        self.assertTrue(mock_ldpath.called)
        self.assertTrue(mock_ldconf.called)

        res = set()
        res.add("/lib/x86_64-linux-gnu/")
        mock_msg.return_value.level.return_value = 0
        mock_ldpath.side_effect = [set(), set()]
        mock_ldconf.return_value = res
        nvmode = NvidiaMode(self.local, self.cont_id)
        status = nvmode._find_host_dir()
        self.assertEqual(status, res)

    @patch('udocker.engine.nvidia.os.path.isdir')
    @patch('udocker.engine.nvidia.Msg')
    def test_08__find_cont_dir(self, mock_msg, mock_isdir):
        """Test08 NvidiaMode._find_cont_dir."""
        cdir = ""
        mock_msg.return_value.level.return_value = 0
        mock_isdir.side_effect = [False, False]
        nvmode = NvidiaMode(self.local, self.cont_id)
        status = nvmode._find_cont_dir()
        self.assertEqual(status, cdir)

        cdir = "/usr/lib/x86_64-linux-gnu"
        mock_msg.return_value.level.return_value = 0
        mock_isdir.side_effect = [True, False]
        nvmode = NvidiaMode(self.local, self.cont_id)
        status = nvmode._find_cont_dir()
        self.assertEqual(status, cdir)

    @patch.object(NvidiaMode, '_get_nvidia_libs')
    @patch.object(NvidiaMode, '_find_host_dir_ldconfig')
    @patch('udocker.engine.nvidia.Msg')
    def test_09__installation_exists(self, mock_msg, mock_ldconf,
                                     mock_libs):
        """Test09 NvidiaMode._installation_exists."""
        host_dir = "/usr/lib"
        cont_dir = "/home/.udocker/cont/usr/lib"
        mock_msg.return_value.level.return_value = 0
        mock_ldconf.side_effect = [set(), set(), set()]
        mock_libs.return_value = ['/lib/libnvidia.so']
        nvmode = NvidiaMode(self.local, self.cont_id)
        status = nvmode._installation_exists(host_dir, cont_dir)
        self.assertFalse(status)

    @patch('udocker.engine.nvidia.FileUtil.putdata')
    @patch.object(NvidiaMode, '_copy_files')
    @patch.object(NvidiaMode, '_get_nvidia_libs')
    @patch.object(NvidiaMode, '_installation_exists')
    @patch.object(NvidiaMode, '_find_cont_dir')
    @patch.object(NvidiaMode, '_find_host_dir')
    @patch('udocker.engine.nvidia.Msg')
    def test_10_set_mode(self, mock_msg, mock_findhdir,
                         mock_findcdir, mock_instexist, mock_libs,
                         mock_cpfiles, mock_futilput):
        """Test10 NvidiaMode.set_mode()."""
        mock_msg.return_value.level.return_value = 0
        self.mock_cdcont.return_value = ""
        nvmode = NvidiaMode(self.local, self.cont_id)
        status = nvmode.set_mode()
        self.assertTrue(mock_msg().err.called)
        self.assertFalse(status)

        self.mock_cdcont.return_value = "/home/.udocker/cont"
        mock_findhdir.return_value = set()
        mock_findcdir.return_value = "/usr/lib/x86_64-linux-gnu"
        nvmode = NvidiaMode(self.local, self.cont_id)
        nvmode.container_dir = "/" + self.cont_id
        status = nvmode.set_mode()
        self.assertTrue(mock_msg().err.called)
        self.assertFalse(status)

        self.mock_cdcont.return_value = "/home/.udocker/cont"
        host_dir = set()
        mock_findhdir.return_value = host_dir.update("/usr/lib")
        mock_findcdir.return_value = ""
        nvmode = NvidiaMode(self.local, self.cont_id)
        nvmode.container_dir = "/" + self.cont_id
        status = nvmode.set_mode()
        self.assertTrue(mock_msg().err.called)
        self.assertFalse(status)

        # TODO: need work
        self.mock_cdcont.return_value = "/home/.udocker/cont"
        host_dir = set()
        host_dir.add("/usr/lib")
        mock_findhdir.return_value = host_dir
        mock_findcdir.return_value = "/usr/lib/x86_64-linux-gnu"
        mock_libs.return_value = ['/lib/libnvidia.so']
        mock_instexist.return_value = False
        mock_cpfiles.side_effect = [True, True, True]
        mock_futilput.return_value = None
        nvmode = NvidiaMode(self.local, self.cont_id)
        nvmode.container_dir = "/" + self.cont_id
        status = nvmode.set_mode(True)
        self.assertTrue(mock_findhdir.called)
        self.assertTrue(mock_findcdir.called)
        # self.assertTrue(mock_instexist.called)
        # self.assertTrue(mock_futilput.called)
        # self.assertTrue(status)

    @patch('udocker.engine.nvidia.os.path.exists')
    def test_11_get_mode(self, mock_exists):
        """Test11 NvidiaMode.get_mode()."""
        mock_exists.return_value = True
        nvmode = NvidiaMode(self.local, self.cont_id)
        status = nvmode.get_mode()
        self.assertTrue(mock_exists.called)
        self.assertTrue(status)

    @patch('udocker.engine.nvidia.glob.glob')
    def test_12_get_devices(self, mock_glob):
        """Test12 NvidiaMode.get_devices()."""
        mock_glob.return_value = ['/dev/nvidia']
        nvmode = NvidiaMode(self.local, self.cont_id)
        status = nvmode.get_devices()
        self.assertEqual(status, Config().conf['nvi_dev_list'])


if __name__ == '__main__':
    main()
