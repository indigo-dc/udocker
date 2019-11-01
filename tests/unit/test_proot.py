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

    def tearDown(self):
        pass

    def test_01_init(self):
        """Test PRootEngine() constructor."""
        prex = PRootEngine(self.conf, self.local, self.xmode)
        self.assertFalse(prex.proot_noseccomp)
        self.assertEqual(prex._kernel, "4.8.13")
        self.assertEqual(prex.proot_exec, None)

    @patch('udocker.engine.proot.ExecutionEngineCommon._oskernel_isgreater')
    @patch('udocker.engine.proot.FileUtil.find_file_in_dir')
    def test_02__select_proot(self, mock_fimage, mock_isgreater):
        """Test PRootEngine()._select_proot()."""
        self.conf['arch'] = "amd64"
        self.conf['proot_noseccomp'] = None
        mock_isgreater.return_value = False
        mock_fimage.return_value = "proot-4_8_0"
        prex = PRootEngine(self.conf, self.local, self.xmode)
        prex._select_proot()
        self.assertFalse(prex.proot_noseccomp)

        self.conf['proot_noseccomp'] = True
        mock_isgreater.return_value = True
        mock_fimage.return_value = "proot"
        prex = PRootEngine(self.conf, self.local, self.xmode)
        prex._select_proot()
        self.assertTrue(prex.proot_noseccomp)

        self.conf['proot_noseccomp'] = False
        mock_isgreater.return_value = True
        mock_fimage.return_value = "proot"
        prex = PRootEngine(self.conf, self.local, self.xmode)
        prex._select_proot()
        self.assertFalse(prex.proot_noseccomp)

        self.conf['proot_noseccomp'] = None
        mock_isgreater.return_value = True
        mock_fimage.return_value = "proot-x86_64-4_8_0"
        prex = PRootEngine(self.conf, self.local, self.xmode)
        prex._select_proot()
        self.assertFalse(prex.proot_noseccomp)

        self.conf['proot_noseccomp'] = False
        mock_isgreater.return_value = True
        mock_fimage.return_value = "proot-x86_64-4_8_0"
        prex = PRootEngine(self.conf, self.local, self.xmode)
        prex._select_proot()
        self.assertFalse(prex.proot_noseccomp)

        self.conf['proot_noseccomp'] = True
        mock_isgreater.return_value = True
        mock_fimage.return_value = "proot-x86_64-4_8_0"
        prex = PRootEngine(self.conf, self.local, self.xmode)
        prex._select_proot()
        self.assertTrue(prex.proot_noseccomp)

    def test_03__set_uid_map(self):
        """Test PRootEngine()._set_uid_map()."""
        prex = PRootEngine(self.conf, self.local, self.xmode)
        prex.opt["uid"] = "0"
        status = prex._set_uid_map()
        self.assertEqual(status, ['-0'])

        prex = PRootEngine(self.conf, self.local, self.xmode)
        prex.opt["uid"] = "1000"
        prex.opt["gid"] = "1001"
        status = prex._set_uid_map()
        self.assertEqual(status, ['-i', '1000:1001'])

    def test_04__create_mountpoint(self):
        """Test PRootEngine()._create_mountpoint()."""
        prex = PRootEngine(self.conf, self.local, self.xmode)
        status = prex._create_mountpoint("", "")
        self.assertTrue(status)

    def test_05__get_volume_bindings(self):
        """Test PRootEngine()._get_volume_bindings()."""
        prex = PRootEngine(self.conf, self.local, self.xmode)
        prex.opt["vol"] = ()
        status = prex._get_volume_bindings()
        self.assertEqual(status, [])

        prex = PRootEngine(self.conf, self.local, self.xmode)
        prex.opt["vol"] = ("/tmp", "/bbb",)
        status = prex._get_volume_bindings()
        self.assertEqual(status, ['-b', '/tmp:/tmp', '-b', '/bbb:/bbb'])

    @patch('udocker.engine.proot.ExecutionEngineCommon._get_portsmap')
    def test_06__get_network_map(self, mock_pmap):
        """Test PRootEngine()._get_network_map()."""
        mock_pmap.return_value = {}
        prex = PRootEngine(self.conf, self.local, self.xmode)
        prex.opt['netcoop'] = False
        status = prex._get_network_map()
        self.assertEqual(status, [])

        mock_pmap.return_value = {}
        prex = PRootEngine(self.conf, self.local, self.xmode)
        prex.opt['netcoop'] = True
        status = prex._get_network_map()
        self.assertEqual(status, ['-n'])

        mock_pmap.return_value = {80: 8080, 443: 8443}
        prex = PRootEngine(self.conf, self.local, self.xmode)
        prex.opt['netcoop'] = True
        status = prex._get_network_map()
        self.assertEqual(status, ['-p', '80:8080', '-p', '443:8443', '-n'])

    @patch.object(PRootEngine, '_run_banner')
    @patch.object(PRootEngine, '_run_env_cleanup_dict')
    @patch.object(PRootEngine, '_set_uid_map')
    @patch.object(PRootEngine, '_get_volume_bindings')
    @patch.object(PRootEngine, '_set_cpu_affinity')
    @patch.object(PRootEngine, '_check_env')
    @patch.object(PRootEngine, '_run_env_set')
    @patch.object(PRootEngine, '_select_proot')
    @patch('udocker.engine.proot.os.getenv')
    @patch('udocker.engine.proot.subprocess.call')
    @patch('udocker.engine.proot.ExecutionEngineCommon._run_init')
    def test_07_run(self, mock_run_init, mock_call, mock_getenv, mock_sel_proot,
                    mock_run_env_set, mock_check_env,
                    mock_set_cpu_aff, mock_get_vol_bind, mock_set_uid_map,
                    mock_env_cleanup_dict, mock_run_banner):
        """Test PRootEngine().run()."""
        mock_run_init.return_value = False
        prex = PRootEngine(self.conf, self.local, self.xmode)
        status = prex.run("CONTAINERID")
        self.assertEqual(status, 2)

        mock_run_init.return_value = True
        mock_check_env.return_value = False
        prex = PRootEngine(self.conf, self.local, self.xmode)
        prex.proot_noseccomp = False
        prex.opt = dict()
        prex.opt["env"] = []
        prex.opt["kernel"] = ""
        prex.opt["netcoop"] = False
        prex.opt["portsmap"] = []
        status = prex.run("CONTAINERID")
        self.assertEqual(status, 4)

        mock_run_init.return_value = True
        mock_check_env.return_value = True
        mock_set_cpu_aff.return_value = []
        mock_get_vol_bind.return_value = ""
        mock_set_uid_map.return_value = ""
        mock_call.return_value = 5
        prex = PRootEngine(self.conf, self.local, self.xmode)
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
