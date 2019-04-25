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
        self._init()
        prex = PRootEngine(mock_local)
        self.assertFalse(prex.proot_noseccomp)
        self.assertEqual(prex._kernel, "4.8.13")
        self.assertEqual(prex.proot_exec, None)

    @patch('udocker.config.Config')
    @patch('udocker.engine.base.ExecutionMode')
    @patch('udocker.utils.fileutil.FileUtil.find_file_in_dir')
    @patch('udocker.container.localrepo.LocalRepository')
    def test_03__select_proot(self, mock_local, mock_fimage, mock_execmode,
                              mock_config):
        """Test PRootEngine()._select_proot()."""
        self._init()
        Config.return_value.arch.return_value = "amd64"
        Config.return_value.oskernel_isgreater.return_value = False
        mock_fimage.return_value = "proot-4_8_0"
        mock_execmode.return_value.get_mode.return_value = ""
        Config.return_value.proot_noseccomp = None
        prex = PRootEngine(mock_local)
        prex.exec_mode = mock_execmode
        prex._select_proot()
        self.assertFalse(prex.proot_noseccomp)
        #
        Config.return_value.oskernel_isgreater.return_value = True
        mock_fimage.return_value = "proot"
        prex = PRootEngine(mock_local)
        prex.exec_mode = mock_execmode
        Config.return_value.proot_noseccomp = True
        prex._select_proot()
        self.assertTrue(prex.proot_noseccomp)
        #
        Config.return_value.oskernel_isgreater.return_value = True
        mock_fimage.return_value = "proot"
        prex = PRootEngine(mock_local)
        prex.exec_mode = mock_execmode
        Config.return_value.proot_noseccomp = False
        prex._select_proot()
        self.assertFalse(prex.proot_noseccomp)
        #
        Config.return_value.oskernel_isgreater.return_value = True
        mock_fimage.return_value = "proot-x86_64-4_8_0"
        prex = PRootEngine(mock_local)
        prex.exec_mode = mock_execmode
        Config.return_value.proot_noseccomp = None
        prex._select_proot()
        self.assertFalse(prex.proot_noseccomp)
        #
        Config.return_value.oskernel_isgreater.return_value = True
        mock_fimage.return_value = "proot-x86_64-4_8_0"
        prex = PRootEngine(mock_local)
        prex.exec_mode = mock_execmode
        Config.return_value.proot_noseccomp = False
        prex._select_proot()
        self.assertFalse(prex.proot_noseccomp)
        #
        Config.return_value.oskernel_isgreater.return_value = True
        mock_fimage.return_value = "proot-x86_64-4_8_0"
        prex = PRootEngine(mock_local)
        prex.exec_mode = mock_execmode
        Config.return_value.proot_noseccomp = True
        prex._select_proot()
        self.assertTrue(prex.proot_noseccomp)

    @patch('udocker.container.localrepo.LocalRepository')
    def test_04__set_uid_map(self, mock_local):
        """Test PRootEngine()._set_uid_map()."""
        self._init()
        prex = PRootEngine(mock_local)
        prex.opt["uid"] = "0"
        status = prex._set_uid_map()
        self.assertEqual(status, ['-0'])
        #
        prex = PRootEngine(mock_local)
        prex.opt["uid"] = "1000"
        prex.opt["gid"] = "1001"
        status = prex._set_uid_map()
        self.assertEqual(status, ['-i', '1000:1001'])

    @patch('udocker.container.localrepo.LocalRepository')
    def test_05__get_volume_bindings(self, mock_local):
        """Test PRootEngine()._get_volume_bindings()."""
        self._init()
        prex = PRootEngine(mock_local)
        prex.opt["vol"] = ()
        status = prex._get_volume_bindings()
        self.assertEqual(status, [])
        #
        prex = PRootEngine(mock_local)
        prex.opt["vol"] = ("/tmp", "/bbb",)
        status = prex._get_volume_bindings()
        self.assertEqual(status, ['-b', '/tmp:/tmp', '-b', '/bbb:/bbb'])

    @patch('udocker.container.localrepo.LocalRepository')
    def test_06__create_mountpoint(self, mock_local):
        """Test PRootEngine()._create_mountpoint()."""
        self._init()
        prex = PRootEngine(mock_local)
        status = prex._create_mountpoint("", "")
        self.assertTrue(status)

    @patch('subprocess.call')
    @patch('udocker.engine.proot.PRootEngine._run_banner')
    @patch('udocker.engine.proot.PRootEngine._run_env_cleanup_dict')
    @patch('udocker.engine.proot.PRootEngine._set_uid_map')
    @patch('udocker.engine.proot.PRootEngine._get_volume_bindings')
    @patch('udocker.engine.proot.PRootEngine._set_cpu_affinity')
    @patch('udocker.engine.proot.PRootEngine._check_env')
    @patch('udocker.engine.proot.PRootEngine._run_env_set')
    @patch('os.getenv')
    @patch('udocker.engine.proot.PRootEngine._select_proot')
    @patch('udocker.engine.base.ExecutionEngineCommon._run_init')
    @patch('udocker.container.localrepo.LocalRepository')
    def test_07_run(self, mock_local, mock_run_init, mock_sel_proot,
                    mock_getenv, mock_run_env_set, mock_check_env,
                    mock_set_cpu_aff, mock_get_vol_bind, mock_set_uid_map,
                    mock_env_cleanup_dict, mock_run_banner, mock_call):
        """Test PRootEngine().run()."""
        mock_run_init.return_value = False
        self._init()
        prex = PRootEngine(mock_local)
        status = prex.run("CONTAINERID")
        self.assertEqual(status, 2)
        #
        mock_run_init.return_value = True
        self._init()
        mock_check_env.return_value = False
        prex = PRootEngine(mock_local)
        prex.proot_noseccomp = False
        prex.opt = dict()
        prex.opt["env"] = []
        prex.opt["kernel"] = ""
        prex.opt["netcoop"] = False
        prex.opt["portsmap"] = []
        status = prex.run("CONTAINERID")
        self.assertEqual(status, 4)
        #
        mock_run_init.return_value = True
        self._init()
        mock_check_env.return_value = True
        mock_set_cpu_aff.return_value = []
        mock_get_vol_bind.return_value = ""
        mock_set_uid_map.return_value = ""
        mock_call.return_value = 5
        prex = PRootEngine(mock_local)
        prex.proot_exec = "/.udocker/bin/proot"
        prex.proot_noseccomp = False
        prex.opt = dict()
        prex.opt["env"] = []
        prex.opt["kernel"] = ""
        prex.opt["netcoop"] = False
        prex.opt["portsmap"] = []
        prex.opt["hostenv"] = ""
        prex.opt["cwd"] = "/"
        prex.opt["cmd"] = "/bin/bash"
        prex._kernel = ""
        prex.container_root = ""
        status = prex.run("CONTAINERID")
        self.assertEqual(status, 5)


if __name__ == '__main__':
    main()
