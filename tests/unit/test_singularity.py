#!/usr/bin/env python
"""
udocker unit tests: SingularityEngine
"""

from unittest import TestCase, main
from unittest.mock import Mock, patch
from udocker.config import Config
from udocker.engine.singularity import SingularityEngine


class SingularityEngineTestCase(TestCase):
    """Test SingularityEngine() class for containers execution."""

    def setUp(self):
        Config().getconf()

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

    def test_01_init(self):
        """Test01 SingularityEngine() constructor."""
        sing = SingularityEngine(self.local, self.xmode)
        self.assertEqual(sing.executable, None)
        self.assertEqual(sing.execution_id, None)

    @patch('udocker.helper.elfpatcher.os.path.exists')
    @patch('udocker.engine.singularity.HostInfo.arch')
    @patch('udocker.engine.singularity.FileUtil.find_file_in_dir')
    @patch('udocker.engine.singularity.FileUtil.find_exec')
    def test_02_select_singularity(self, mock_findexe, mock_find,
                                   mock_arch, mock_exists):
        """Test02 SingularityEngine().select_singularity()."""
        Config.conf['use_singularity_executable'] = ""
        mock_findexe.return_value = "/bin/runc-arm"
        mock_exists.return_value = True
        sing = SingularityEngine(self.local, self.xmode)
        sing.select_singularity()
        self.assertTrue(mock_findexe.called)

        Config.conf['use_singularity_executable'] = "UDOCKER"
        mock_arch.return_value = "amd64"
        mock_find.return_value = "singularity-x86_64"
        mock_exists.return_value = True
        sing = SingularityEngine(self.local, self.xmode)
        sing.select_singularity()
        self.assertTrue(mock_arch.called)
        self.assertTrue(mock_find.called)

        Config.conf['use_singularity_executable'] = "UDOCKER"
        mock_arch.return_value = "i386"
        mock_find.return_value = "singularity-x86"
        mock_exists.return_value = True
        sing = SingularityEngine(self.local, self.xmode)
        sing.select_singularity()
        self.assertTrue(mock_arch.called)
        self.assertTrue(mock_find.called)

    @patch('udocker.engine.singularity.NixAuthentication.get_home')
    @patch('udocker.engine.singularity.os.path.isdir')
    def test_03__get_volume_bindings(self, mock_isdir, mock_gethome):
        """Test03 SingularityEngine()._get_volume_bindings()."""
        res_exp = ['-B', '/dir1:/dir1',
                   '-B', '/home/user:/home/user',
                   '-B', '/tmp:/tmp',
                   '-B', '/var/tmp:/var/tmp']
        mock_gethome.return_value = "/home/user"
        mock_isdir.side_effect = [True, True]
        sing = SingularityEngine(self.local, self.xmode)
        sing.opt = dict()
        sing.opt["vol"] = ["/dir1", "/home/user"]
        status = sing._get_volume_bindings()
        self.assertEqual(status, res_exp)
        self.assertTrue(mock_gethome.called)
        self.assertTrue(mock_isdir.call_count, 2)

        res_exp = ['-B', '/home/user:/home/user',
                   '-B', '/tmp:/tmp',
                   '-B', '/var/tmp:/var/tmp']
        mock_gethome.return_value = "/home/user"
        mock_isdir.side_effect = [True, True, True]
        sing = SingularityEngine(self.local, self.xmode)
        sing.opt = dict()
        sing.opt["vol"] = ["/home/user", "/tmp", "/var/tmp"]
        status = sing._get_volume_bindings()
        self.assertEqual(status, res_exp)
        self.assertTrue(mock_gethome.called)
        self.assertTrue(mock_isdir.call_count, 3)

    def test_04__singularity_env_get(self):
        """Test04 SingularityEngine()._singularity_env_get()."""
        res_exp = {"SINGULARITYENV_AA": "aa", "SINGULARITYENV_BB": "bb"}
        sing = SingularityEngine(self.local, self.xmode)
        sing.opt = dict()
        sing.opt["env"] = [("AA", "aa"), ("BB", "bb")]
        status = sing._singularity_env_get()
        self.assertEqual(status, res_exp)

    @patch('udocker.engine.singularity.FileUtil.mkdir')
    def test_05__make_container_dirs(self, mock_mkdir):
        """Test05 SingularityEngine()._make_container_directories()."""
        mock_mkdir.side_effect = [None, None, None, None, None, None]
        sing = SingularityEngine(self.local, self.xmode)
        sing._make_container_directories()
        self.assertTrue(mock_mkdir.call_count, 6)

    @patch('udocker.engine.singularity.Msg')
    def test_06__run_invalid_options(self, mock_msg):
        """Test06 SingularityEngine()._run_invalid_options()."""
        mock_msg.level = 0
        sing = SingularityEngine(self.local, self.xmode)
        sing.opt['netcoop'] = False
        sing.opt['portsmap'] = True
        sing._run_invalid_options()
        self.assertTrue(mock_msg.called)

    @patch.object(SingularityEngine, '_has_option')
    @patch('udocker.engine.singularity.NixAuthentication')
    @patch('udocker.engine.singularity.HostInfo.username')
    @patch('udocker.engine.singularity.Msg')
    def test_07__run_as_root(self, mock_msg, mock_uname,
                             mock_nixauth, mock_hasopt):
        """Test07 SingularityEngine()._run_as_root()."""
        mock_msg.level = 0
        mock_uname.return_value = "u1"
        sing = SingularityEngine(self.local, self.xmode)
        sing.opt = dict()
        status = sing._run_as_root()
        self.assertFalse(status)
        self.assertTrue(mock_uname.called)

        mock_msg.level = 0
        mock_uname.return_value = "u1"
        sing = SingularityEngine(self.local, self.xmode)
        sing.opt = dict()
        sing.opt["user"] = "u1"
        status = sing._run_as_root()
        self.assertFalse(status)
        self.assertTrue(mock_uname.called)

        mock_msg.level = 0
        mock_uname.return_value = "u1"
        sing = SingularityEngine(self.local, self.xmode)
        sing.opt = dict()
        sing.opt["user"] = "u2"
        sing.opt["uid"] = "1000"
        status = sing._run_as_root()
        self.assertFalse(status)
        self.assertTrue(mock_uname.called)

        mock_msg.level = 0
        mock_uname.return_value = "u1"
        mock_hasopt.return_value = True
        mock_nixauth.return_value.user_in_subuid.return_value = True
        mock_nixauth.return_value.user_in_subgid.return_value = True
        sing = SingularityEngine(self.local, self.xmode)
        sing.opt = dict()
        sing.opt["user"] = "root"
        sing.opt["uid"] = "0"
        status = sing._run_as_root()
        self.assertTrue(status)
        self.assertTrue(mock_hasopt.called)
        self.assertTrue(mock_nixauth.return_value.user_in_subuid.called)
        self.assertTrue(mock_nixauth.return_value.user_in_subgid.called)

    @patch.object(SingularityEngine, '_run_banner')
    @patch.object(SingularityEngine, '_run_env_cleanup_dict')
    @patch.object(SingularityEngine, '_get_volume_bindings')
    @patch.object(SingularityEngine, '_run_env_set')
    @patch.object(SingularityEngine, '_run_as_root')
    @patch.object(SingularityEngine, 'select_singularity')
    @patch.object(SingularityEngine, '_make_container_directories')
    @patch.object(SingularityEngine, '_run_invalid_options')
    @patch.object(SingularityEngine, '_run_init')
    @patch('udocker.engine.singularity.subprocess.call')
    @patch('udocker.engine.singularity.Unique.uuid')
    @patch('udocker.engine.singularity.FileBind')
    @patch('udocker.engine.singularity.os.path.isdir')
    def test_08_run(self, mock_isdir, mock_fbind, mock_uuid, mock_call,
                    mock_rinit, mock_rinvopt, mock_mkcontdir,
                    mock_selsing, mock_runroot, mock_renvset, mock_getvolbind,
                    mock_renvclean, mock_rbann):
        """Test08 SingularityEngine().run()."""
        mock_isdir.return_value = True
        mock_fbind.return_value.container_orig_dir.return_value = "/d1"
        mock_fbind.return_value.restore.return_value = None
        mock_rinit.return_value = False
        sing = SingularityEngine(self.local, self.xmode)
        status = sing.run("CONTAINERID")
        self.assertEqual(status, 2)

        mock_isdir.return_value = True
        mock_fbind.return_value.container_orig_dir.return_value = "/d1"
        mock_fbind.return_value.restore.return_value = None
        mock_rinit.return_value = "/cont/"
        mock_rinvopt.return_value = None
        mock_mkcontdir.return_value = None
        mock_selsing.return_value = None
        mock_runroot.return_value = None
        mock_renvset.return_value = None
        self.local.bindir = "/cont/bin"
        mock_getvolbind.return_value = ['-B', '/home/user:/home/user',
                                        '-B', '/tmp:/tmp',
                                        '-B', '/var/tmp:/var/tmp']
        mock_uuid.return_value = "EXECUTION_ID"
        mock_renvclean.return_value = None
        mock_rbann.return_value = None
        mock_call.return_value = 0
        sing = SingularityEngine(self.local, self.xmode)
        sing.executable = "/bin/sing"
        status = sing.run("CONTAINERID")
        self.assertEqual(status, 0)

if __name__ == '__main__':
    main()
