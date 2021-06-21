#!/usr/bin/env python
"""
udocker unit tests: PRootEngine
"""

from unittest import TestCase, main
from unittest.mock import Mock, patch
from udocker.config import Config
from udocker.engine.proot import PRootEngine


class PRootEngineTestCase(TestCase):
    """Test PRootEngine() class for containers execution."""

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

        str_local = 'udocker.container.localrepo.LocalRepository'
        self.lrepo = patch(str_local)
        self.local = self.lrepo.start()
        self.mock_lrepo = Mock()
        self.local.return_value = self.mock_lrepo

        str_exmode = 'udocker.engine.execmode.ExecutionMode'
        self.execmode = patch(str_exmode)
        self.xmode = self.execmode.start()
        self.mock_execmode = Mock()
        self.xmode.return_value = self.mock_execmode

    def tearDown(self):
        self.lrepo.stop()
        self.execmode.stop()

    @patch('udocker.engine.proot.HostInfo.oskernel')
    def test_01_init(self, mock_kernel):
        """Test01 PRootEngine() constructor."""
        mock_kernel.return_value = "4.8.13"
        prex = PRootEngine(self.local, self.xmode)
        self.assertFalse(prex.proot_noseccomp)
        self.assertEqual(prex._kernel, "4.8.13")

    @patch.object(PRootEngine, '_is_seccomp_patched')
    @patch('udocker.engine.proot.HostInfo.oskernel_isgreater')
    @patch('udocker.engine.proot.FileUtil.find_file_in_dir')
    @patch('udocker.helper.elfpatcher.os.path.exists')
    def test_02_select_proot(self, mock_exists, mock_fimage,
                             mock_isgreater, mock_issecomp):
        """Test02 PRootEngine().select_proot()."""
        Config().conf['arch'] = "amd64"
        Config().conf['proot_noseccomp'] = None
        mock_isgreater.return_value = False
        mock_fimage.return_value = "proot-4_8_0"
        mock_issecomp.return_value = False
        mock_exists.return_value = True
        prex = PRootEngine(self.local, self.xmode)
        prex.select_proot()
        self.assertFalse(prex.proot_noseccomp)

        Config().conf['proot_noseccomp'] = True
        mock_isgreater.return_value = True
        mock_fimage.return_value = "proot"
        mock_issecomp.return_value = False
        mock_exists.return_value = True
        prex = PRootEngine(self.local, self.xmode)
        prex.select_proot()
        self.assertTrue(prex.proot_noseccomp)

        Config().conf['proot_noseccomp'] = False
        mock_isgreater.return_value = True
        mock_fimage.return_value = "proot"
        mock_issecomp.return_value = False
        mock_exists.return_value = True
        prex = PRootEngine(self.local, self.xmode)
        prex.select_proot()
        self.assertFalse(prex.proot_noseccomp)

        Config().conf['proot_noseccomp'] = None
        mock_isgreater.return_value = True
        mock_fimage.return_value = "proot-x86_64-4_8_0"
        mock_issecomp.return_value = False
        mock_exists.return_value = True
        prex = PRootEngine(self.local, self.xmode)
        prex.select_proot()
        self.assertFalse(prex.proot_noseccomp)

        Config().conf['proot_noseccomp'] = False
        mock_isgreater.return_value = True
        mock_fimage.return_value = "proot-x86_64-4_8_0"
        mock_issecomp.return_value = False
        mock_exists.return_value = True
        prex = PRootEngine(self.local, self.xmode)
        prex.select_proot()
        self.assertFalse(prex.proot_noseccomp)

        Config().conf['proot_noseccomp'] = True
        mock_isgreater.return_value = True
        mock_fimage.return_value = "proot-x86_64-4_8_0"
        mock_issecomp.return_value = False
        mock_exists.return_value = True
        prex = PRootEngine(self.local, self.xmode)
        prex.select_proot()
        self.assertTrue(prex.proot_noseccomp)

    def test_03__set_uid_map(self):
        """Test03 PRootEngine()._set_uid_map()."""
        prex = PRootEngine(self.local, self.xmode)
        prex.opt["uid"] = "0"
        status = prex._set_uid_map()
        self.assertEqual(status, ['-0'])

        prex = PRootEngine(self.local, self.xmode)
        prex.opt["uid"] = "1000"
        prex.opt["gid"] = "1001"
        status = prex._set_uid_map()
        self.assertEqual(status, ['-i', '1000:1001'])

    def test_04__create_mountpoint(self):
        """Test04 PRootEngine()._create_mountpoint()."""
        prex = PRootEngine(self.local, self.xmode)
        status = prex._create_mountpoint("", "")
        self.assertTrue(status)

    def test_05__get_volume_bindings(self):
        """Test05 PRootEngine()._get_volume_bindings()."""
        prex = PRootEngine(self.local, self.xmode)
        prex.opt["vol"] = ()
        status = prex._get_volume_bindings()
        self.assertEqual(status, [])

        prex = PRootEngine(self.local, self.xmode)
        prex.opt["vol"] = ("/tmp", "/bbb",)
        status = prex._get_volume_bindings()
        self.assertEqual(status, ['-b', '/tmp:/tmp', '-b', '/bbb:/bbb'])

    @patch('udocker.engine.proot.ExecutionEngineCommon._get_portsmap')
    def test_06__get_network_map(self, mock_pmap):
        """Test06 PRootEngine()._get_network_map()."""
        mock_pmap.return_value = {}
        prex = PRootEngine(self.local, self.xmode)
        prex.opt['netcoop'] = False
        status = prex._get_network_map()
        self.assertEqual(status, [])

        mock_pmap.return_value = {}
        prex = PRootEngine(self.local, self.xmode)
        prex.opt['netcoop'] = True
        status = prex._get_network_map()
        self.assertEqual(status, ['-n'])

        mock_pmap.return_value = {80: 8080, 443: 8443}
        prex = PRootEngine(self.local, self.xmode)
        prex.opt['netcoop'] = True
        status = prex._get_network_map()
        self.assertEqual(status, ['-p', '80:8080', '-p', '443:8443', '-n'])

    @patch('udocker.engine.proot.os.environ.update')
    @patch.object(PRootEngine, '_get_network_map')
    @patch('udocker.engine.nvidia.Msg')
    @patch('udocker.engine.proot.HostInfo.oskernel_isgreater')
    @patch.object(PRootEngine, '_run_banner')
    @patch.object(PRootEngine, '_run_env_cleanup_dict')
    @patch.object(PRootEngine, '_set_uid_map')
    @patch.object(PRootEngine, '_get_volume_bindings')
    @patch.object(PRootEngine, '_set_cpu_affinity')
    @patch.object(PRootEngine, '_run_env_set')
    @patch.object(PRootEngine, 'select_proot')
    @patch('udocker.engine.proot.os.getenv')
    @patch('udocker.engine.proot.subprocess.call')
    @patch('udocker.engine.proot.ExecutionEngineCommon._run_init')
    def test_07_run(self, mock_run_init, mock_call, mock_getenv, mock_sel_proot,
                    mock_run_env_set,
                    mock_set_cpu_aff, mock_get_vol_bind, mock_set_uid_map,
                    mock_env_cleanup_dict, mock_run_banner, mock_isgreater,
                    mock_msg, mock_netmap, mock_envupd):
        """Test07 PRootEngine().run()."""
        mock_run_init.return_value = False
        prex = PRootEngine(self.local, self.xmode)
        status = prex.run("CONTAINERID")
        self.assertEqual(status, 2)

        Config().conf['proot_killonexit'] = False
        mock_run_init.return_value = True
        mock_sel_proot.return_value = None
        mock_isgreater.return_value = "2.9.0"
        mock_run_env_set.return_value = None
        mock_msg.level = 5
        mock_set_cpu_aff.return_value = []
        mock_get_vol_bind.return_value = ['-b', '/tmp:/tmp']
        mock_set_uid_map.return_value = ['-i', '1000:1001']
        mock_netmap.return_value = ['-p', '80:8080', '-n']
        mock_env_cleanup_dict.return_value = None
        mock_run_banner.return_value = None
        mock_call.return_value = 5
        mock_getenv.return_value = False
        mock_envupd.return_value = None
        prex = PRootEngine(self.local, self.xmode)
        prex.opt["kernel"] = "5.4.0"
        status = prex.run("CONTAINERID")
        self.assertEqual(status, 5)
        self.assertTrue(mock_run_init.called)
        self.assertTrue(mock_call.called)
        self.assertTrue(mock_envupd.called)


if __name__ == '__main__':
    main()
