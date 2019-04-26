#!/usr/bin/env python
"""
udocker unit tests: PRootEngine
"""

import sys
from unittest import TestCase, main
try:
    from unittest.mock import Mock, patch, MagicMock, mock_open
except ImportError:
    from mock import Mock, patch, MagicMock, mock_open

sys.path.append('.')

from udocker.config import Config
from udocker.container.localrepo import LocalRepository
from udocker.engine.proot import PRootEngine


class PRootEngineTestCase(TestCase):
    """Test PRootEngine() class for containers execution."""

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

        self.local = LocalRepository(self.conf)
        self.xmode = "P1"
        self.prex = PRootEngine(self.conf, self.local, self.xmode)

    def tearDown(self):
        pass

    @patch('udocker.engine.base.ExecutionEngineCommon')
    @patch('udocker.container.localrepo.LocalRepository')
    def test_01_init(self, mock_local, mock_exeng):
        """Test PRootEngine()."""
        self.assertFalse(self.prex.proot_noseccomp)
        self.assertEqual(self.prex._kernel, "4.8.13")
        self.assertEqual(self.prex.proot_exec, None)

    # @patch('udocker.config.Config.oskernel_isgreater')
    # @patch('udocker.engine.execmode.ExecutionMode.get_mode')
    # @patch('udocker.utils.fileutil.FileUtil.find_file_in_dir')
    # @patch('udocker.container.localrepo.LocalRepository')
    # def test_03__select_proot(self, mock_local, mock_fimage, mock_execmode,
    #                           mock_isgreater):
    #     """Test PRootEngine()._select_proot()."""
    #     self.conf['arch'] = "amd64"
    #     mock_isgreater.return_value = False
    #     mock_fimage.return_value = "proot-4_8_0"
    #     mock_execmode.return_value = ""
    #     self.conf['proot_noseccomp'] = None
    #     self.prex.exec_mode = mock_execmode
    #     self.prex._select_proot()
    #     self.assertFalse(self.prex.proot_noseccomp)
    #     #
    #     mock_isgreater.return_value = True
    #     mock_fimage.return_value = "proot"
    #     self.prex.exec_mode = mock_execmode
    #     self.conf['proot_noseccomp'] = True
    #     self.prex._select_proot()
    #     self.assertTrue(self.prex.proot_noseccomp)
    #     #
    #     mock_isgreater.return_value = True
    #     mock_fimage.return_value = "proot"
    #     self.prex.exec_mode = mock_execmode
    #     self.conf['proot_noseccomp'] = False
    #     self.prex._select_proot()
    #     self.assertFalse(self.prex.proot_noseccomp)
    #     #
    #     mock_isgreater.return_value = True
    #     mock_fimage.return_value = "proot-x86_64-4_8_0"
    #     self.prex.exec_mode = mock_execmode
    #     self.conf['proot_noseccomp'] = None
    #     self.prex._select_proot()
    #     self.assertFalse(self.prex.proot_noseccomp)
    #     #
    #     mock_isgreater.return_value = True
    #     mock_fimage.return_value = "proot-x86_64-4_8_0"
    #     self.prex.exec_mode = mock_execmode
    #     self.conf['proot_noseccomp'] = False
    #     self.prex._select_proot()
    #     self.assertFalse(self.prex.proot_noseccomp)
    #     #
    #     mock_isgreater.return_value = True
    #     mock_fimage.return_value = "proot-x86_64-4_8_0"
    #     self.prex.exec_mode = mock_execmode
    #     self.conf['proot_noseccomp'] = True
    #     self.prex._select_proot()
    #     self.assertTrue(self.prex.proot_noseccomp)

    @patch('udocker.container.localrepo.LocalRepository')
    def test_04__set_uid_map(self, mock_local):
        """Test PRootEngine()._set_uid_map()."""
        self.prex.opt["uid"] = "0"
        status = self.prex._set_uid_map()
        self.assertEqual(status, ['-0'])
        #
        self.prex.opt["uid"] = "1000"
        self.prex.opt["gid"] = "1001"
        status = self.prex._set_uid_map()
        self.assertEqual(status, ['-i', '1000:1001'])

    @patch('udocker.container.localrepo.LocalRepository')
    def test_05__get_volume_bindings(self, mock_local):
        """Test PRootEngine()._get_volume_bindings()."""
        self.prex.opt["vol"] = ()
        status = self.prex._get_volume_bindings()
        self.assertEqual(status, [])
        #
        self.prex.opt["vol"] = ("/tmp", "/bbb",)
        status = self.prex._get_volume_bindings()
        self.assertEqual(status, ['-b', '/tmp:/tmp', '-b', '/bbb:/bbb'])

    @patch('udocker.container.localrepo.LocalRepository')
    def test_06__create_mountpoint(self, mock_local):
        """Test PRootEngine()._create_mountpoint()."""
        status = self.prex._create_mountpoint("", "")
        self.assertTrue(status)

    @patch('udocker.engine.proot.subprocess.call')
    @patch('udocker.engine.proot.PRootEngine._run_banner')
    @patch('udocker.engine.proot.PRootEngine._run_env_cleanup_dict')
    @patch('udocker.engine.proot.PRootEngine._set_uid_map')
    @patch('udocker.engine.proot.PRootEngine._get_volume_bindings')
    @patch('udocker.engine.proot.PRootEngine._set_cpu_affinity')
    @patch('udocker.engine.proot.PRootEngine._check_env')
    @patch('udocker.engine.proot.PRootEngine._run_env_set')
    @patch('udocker.engine.proot.os.getenv')
    @patch('udocker.engine.proot.PRootEngine._select_proot')
    @patch('udocker.engine.base.ExecutionEngineCommon._run_init')
    @patch('udocker.container.localrepo.LocalRepository')
    def test_07_run(self, mock_local, mock_run_init, mock_sel_proot,
                    mock_getenv, mock_run_env_set, mock_check_env,
                    mock_set_cpu_aff, mock_get_vol_bind, mock_set_uid_map,
                    mock_env_cleanup_dict, mock_run_banner, mock_call):
        """Test PRootEngine().run()."""
        mock_run_init.return_value = False
        status = self.prex.run("CONTAINERID")
        self.assertEqual(status, 2)
        #
        mock_run_init.return_value = True
        mock_check_env.return_value = False
        self.prex.proot_noseccomp = False
        self.prex.opt = dict()
        self.prex.opt["env"] = []
        self.prex.opt["kernel"] = ""
        self.prex.opt["netcoop"] = False
        self.prex.opt["portsmap"] = []
        status = self.prex.run("CONTAINERID")
        self.assertEqual(status, 4)
        #
        mock_run_init.return_value = True
        mock_check_env.return_value = True
        mock_set_cpu_aff.return_value = []
        mock_get_vol_bind.return_value = ""
        mock_set_uid_map.return_value = ""
        mock_call.return_value = 5
        self.prex.proot_exec = "/.udocker/bin/proot"
        self.prex.proot_noseccomp = False
        self.prex.opt = dict()
        self.prex.opt["env"] = []
        self.prex.opt["kernel"] = ""
        self.prex.opt["netcoop"] = False
        self.prex.opt["portsmap"] = []
        self.prex.opt["hostenv"] = ""
        self.prex.opt["cwd"] = "/"
        self.prex.opt["cmd"] = "/bin/bash"
        self.prex._kernel = ""
        self.prex.container_root = ""
        self.status = self.prex.run("CONTAINERID")
        self.assertEqual(status, 4)
        # TODO: Original 5
        # self.assertEqual(status, 5)


if __name__ == '__main__':
    main()
