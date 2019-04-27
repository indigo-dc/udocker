#!/usr/bin/env python
"""
udocker unit tests: RuncEngine
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
from udocker.engine.runc import RuncEngine

if sys.version_info[0] >= 3:
    BOPEN = "builtins" + '.open'
else:
    BOPEN = "__builtin__" + '.open'


class RuncEngineTestCase(TestCase):
    """Test RuncEngine() containers execution with runC."""

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
        self.xmode = "R1"
        self.rcex = RuncEngine(self.conf, self.local, self.xmode)

    def tearDown(self):
        pass

    @patch('udocker.engine.base.ExecutionEngineCommon')
    @patch('udocker.container.localrepo.LocalRepository')
    def test_01_init(self, mock_local, mock_exeng):
        """Test RuncEngine()."""
        self.assertEqual(self.rcex.runc_exec, None)

    @patch('udocker.config.Config.oskernel_isgreater')
    @patch('udocker.engine.base.ExecutionEngineCommon')
    @patch('udocker.utils.fileutil.FileUtil.find_file_in_dir')
    @patch('udocker.container.localrepo.LocalRepository')
    def test_03__select_runc(self, mock_local, mock_find, mock_execmode,
                             mock_isgreater):
        """Test RuncEngine()._select_runc()."""
        self.conf['arch'] = "arm"
        mock_isgreater.return_value = False
        mock_find.return_value = "runc-arm"
        mock_execmode.return_value.get_mode.return_value = ""
        self.rcex.exec_mode = mock_execmode
        self.rcex._select_runc()
        self.assertEqual(self.rcex.runc_exec, "runc-arm")

    @patch('udocker.utils.fileutil.FileUtil.size.remove')
    @patch('udocker.utils.fileutil.FileUtil.size')
    @patch('udocker.engine.runc.json.load')
    @patch('udocker.engine.runc.subprocess.call')
    @patch('udocker.engine.runc.os.path.realpath')
    @patch('udocker.utils.fileutil.FileUtil')
    @patch('udocker.container.localrepo.LocalRepository')
    def test_04__load_spec(self, mock_local, mock_futil, mock_realpath,
                           mock_call, mock_jsonload, mock_size, mock_rm):
        """Test RuncEngine()._load_spec()."""
        mock_futil.reset()
        mock_size.return_value = 1
        self.rcex._load_spec(False)
        self.assertFalse(mock_rm.called)
        #
        mock_futil.reset()
        mock_size.return_value = 1
        self.rcex._load_spec(True)
        # self.assertTrue(mock_rm.called)
        #
        mock_futil.reset()
        mock_size.return_value = -1
        mock_realpath.return_value = "/.udocker/containers/aaaaa"
        mock_call.return_value = True
        self.rcex.runc_exec = "runc"
        status = self.rcex._load_spec(False)
        self.assertFalse(status)
        #
        mock_futil.reset()
        mock_size.return_value = -1
        mock_realpath.return_value = "/.udocker/containers/aaaaa"
        mock_call.return_value = False  # ok
        mock_jsonload.return_value = "JSON"
        self.rcex.runc_exec = "runc"
        with patch(BOPEN, mock_open()):
            status = self.rcex._load_spec(False)
        self.assertEqual(status, "JSON")
        #
        mock_futil.reset()
        mock_size.return_value = -1
        mock_realpath.return_value = "/.udocker/containers/aaaaa"
        mock_call.return_value = False  # ok
        mock_jsonload.return_value = "JSON"
        mock_jsonload.side_effect = OSError("reading json")
        self.rcex.runc_exec = "runc"
        with patch(BOPEN, mock_open()):
            status = self.rcex._load_spec(False)
        self.assertEqual(status, None)

    @patch('udocker.engine.runc.json.dump')
    @patch('udocker.container.localrepo.LocalRepository')
    def test_05__save_spec(self, mock_local, mock_jsondump):
        """Test RuncEngine()._save_spec()."""
        self.rcex._container_specjson = "JSON"
        with patch(BOPEN, mock_open()):
            status = self.rcex._save_spec()
        self.assertTrue(status)
        #
        mock_jsondump.side_effect = OSError("in open")
        self.rcex._container_specjson = "JSON"
        with patch(BOPEN, mock_open()):
            status = self.rcex._save_spec()
        self.assertFalse(status)

    @patch('udocker.engine.runc.os.getgid')
    @patch('udocker.engine.runc.os.getuid')
    @patch('udocker.engine.runc.platform.node')
    @patch('udocker.engine.runc.os.path.realpath')
    @patch('udocker.container.localrepo.LocalRepository')
    def test_06__set_spec(self, mock_local, mock_realpath, mock_node,
                          mock_getuid, mock_getgid):
        """Test RuncEngine()._set_spec()."""
        # self.rcex.opt["hostname"] has nodename
        mock_realpath.return_value = "/.udocker/containers/aaaaaa/ROOT"
        mock_node.return_value = "nodename.local"
        self.rcex.opt = dict()
        self.rcex._container_specjson = dict()
        self.rcex._container_specjson["root"] = dict()
        self.rcex._container_specjson["process"] = dict()
        self.rcex._container_specjson["linux"] = dict()
        self.rcex._container_specjson["linux"]["uidMappings"] = dict()
        self.rcex._container_specjson["linux"]["gidMappings"] = dict()
        self.rcex.opt["cwd"] = "/"
        self.rcex.opt["env"] = []
        self.rcex.opt["cmd"] = "bash"
        self.rcex.opt["hostname"] = "node.domain"
        json_obj = self.rcex._set_spec()
        self.assertEqual(json_obj["hostname"], "node.domain")
        # empty self.rcex.opt["hostname"]
        mock_realpath.return_value = "/.udocker/containers/aaaaaa/ROOT"
        mock_node.return_value = "nodename.local"
        self.rcex.opt = dict()
        self.rcex._container_specjson = dict()
        self.rcex._container_specjson["root"] = dict()
        self.rcex._container_specjson["process"] = dict()
        self.rcex._container_specjson["linux"] = dict()
        self.rcex._container_specjson["linux"]["uidMappings"] = dict()
        self.rcex._container_specjson["linux"]["gidMappings"] = dict()
        self.rcex.opt["cwd"] = "/"
        self.rcex.opt["env"] = []
        self.rcex.opt["cmd"] = "bash"
        self.rcex.opt["hostname"] = ""
        json_obj = self.rcex._set_spec()
        self.assertEqual(json_obj["hostname"], "nodename.local")
        # environment passes to container json
        mock_realpath.return_value = "/.udocker/containers/aaaaaa/ROOT"
        mock_node.return_value = "nodename.local"
        self.rcex.opt = dict()
        self.rcex._container_specjson = dict()
        self.rcex._container_specjson["root"] = dict()
        self.rcex._container_specjson["process"] = dict()
        self.rcex._container_specjson["linux"] = dict()
        self.rcex._container_specjson["linux"]["uidMappings"] = dict()
        self.rcex._container_specjson["linux"]["gidMappings"] = dict()
        self.rcex.opt["cwd"] = "/"
        self.rcex.opt["env"] = ["AA=aa", "BB=bb"]
        self.rcex.opt["cmd"] = "bash"
        self.rcex.opt["hostname"] = ""
        json_obj = self.rcex._set_spec()
        self.assertIn("AA=aa", json_obj["process"]["env"])
        # environment syntax error
        mock_realpath.return_value = "/.udocker/containers/aaaaaa/ROOT"
        mock_node.return_value = "nodename.local"
        self.rcex.opt = dict()
        self.rcex._container_specjson = dict()
        self.rcex._container_specjson["root"] = dict()
        self.rcex._container_specjson["process"] = dict()
        self.rcex._container_specjson["linux"] = dict()
        self.rcex._container_specjson["linux"]["uidMappings"] = dict()
        self.rcex._container_specjson["linux"]["gidMappings"] = dict()
        self.rcex.opt["cwd"] = "/"
        self.rcex.opt["env"] = ["=aa", "BB=bb"]
        self.rcex.opt["cmd"] = "bash"
        self.rcex.opt["hostname"] = ""
        json_obj = self.rcex._set_spec()
        self.assertNotIn("AA=aa", json_obj["process"]["env"])
        # uid and gid mappings
        mock_realpath.return_value = "/.udocker/containers/aaaaaa/ROOT"
        mock_node.return_value = "nodename.local"
        mock_getuid.return_value = 10000
        mock_getgid.return_value = 10000
        self.rcex.opt = dict()
        self.rcex._container_specjson = dict()
        self.rcex._container_specjson["root"] = dict()
        self.rcex._container_specjson["process"] = dict()
        self.rcex._container_specjson["linux"] = dict()
        self.rcex._container_specjson["linux"]["uidMappings"] = dict()
        self.rcex._container_specjson["linux"]["gidMappings"] = dict()
        self.rcex._container_specjson["linux"]["uidMappings"]["XXX"] = 0
        self.rcex._container_specjson["linux"]["gidMappings"]["XXX"] = 0
        self.rcex.opt["cwd"] = "/"
        self.rcex.opt["env"] = ["AA=aa", "BB=bb"]
        self.rcex.opt["cmd"] = "bash"
        self.rcex.opt["hostname"] = ""
        json_obj = self.rcex._set_spec()
        self.assertFalse(mock_getuid.called)
        self.assertFalse(mock_getgid.called)

    @patch('udocker.msg.Msg')
    @patch('udocker.container.localrepo.LocalRepository')
    def test_07__uid_check(self, mock_local, mock_msg):
        """Test RuncEngine()._uid_check()."""
        mock_msg.reset_mock()
        self.rcex.opt = dict()
        self.rcex._uid_check()
        self.assertFalse(mock_msg.called)
        #
        mock_msg.reset_mock()
        self.rcex.opt = dict()
        self.rcex.opt["user"] = "root"
        self.rcex._uid_check()
        self.assertFalse(mock_msg.called)
        #
        mock_msg.reset_mock()
        self.rcex.opt = dict()
        self.rcex.opt["user"] = "user01"
        self.rcex._uid_check()
        # self.assertTrue(mock_msg.called)

    @patch('udocker.container.localrepo.LocalRepository')
    def test_08__create_mountpoint(self, mock_local):
        """Test RuncEngine()._create_mountpoint()."""
        status = self.rcex._create_mountpoint("HOSTPATH", "CONTPATH")
        self.assertTrue(status)

    @patch('udocker.container.localrepo.LocalRepository')
    def test_09__add_mount_spec(self, mock_local):
        """Test RuncEngine()._add_mount_spec()."""
        self.rcex._container_specjson = dict()
        self.rcex._container_specjson["mounts"] = []
        status = self.rcex._add_mount_spec("/HOSTDIR", "/CONTDIR")
        mount = self.rcex._container_specjson["mounts"][0]
        self.assertEqual(mount["destination"], "/CONTDIR")
        self.assertEqual(mount["source"], "/HOSTDIR")
        self.assertIn("ro", mount["options"])
        # rw
        self.rcex._container_specjson = dict()
        self.rcex._container_specjson["mounts"] = []
        status = self.rcex._add_mount_spec("/HOSTDIR", "/CONTDIR", True)
        mount = self.rcex._container_specjson["mounts"][0]
        self.assertEqual(mount["destination"], "/CONTDIR")
        self.assertEqual(mount["source"], "/HOSTDIR")
        self.assertIn("rw", mount["options"])

    @patch('udocker.container.localrepo.LocalRepository')
    def test_10__del_mount_spec(self, mock_local):
        """Test RuncEngine()._del_mount_spec()."""
        self.rcex._container_specjson = dict()
        self.rcex._container_specjson["mounts"] = []
        mount = {"destination": "/CONTDIR",
                 "type": "none",
                 "source": "/HOSTDIR",
                 "options": ["rbind", "nosuid",
                             "noexec", "nodev",
                             "rw", ], }
        self.rcex._container_specjson["mounts"].append(mount)
        self.rcex._del_mount_spec("/HOSTDIR", "/CONTDIR")
        self.assertEqual(len(self.rcex._container_specjson["mounts"]), 0)
        #
        self.rcex._container_specjson = dict()
        self.rcex._container_specjson["mounts"] = []
        mount = {"destination": "/XXXX",
                 "type": "none",
                 "source": "/HOSTDIR",
                 "options": ["rbind", "nosuid",
                             "noexec", "nodev",
                             "rw", ], }
        self.rcex._container_specjson["mounts"].append(mount)
        self.rcex._del_mount_spec("/HOSTDIR", "/CONTDIR")
        self.assertEqual(len(self.rcex._container_specjson["mounts"]), 1)
        #
        self.rcex._container_specjson = dict()
        self.rcex._container_specjson["mounts"] = []
        mount = {"destination": "/CONTDIR",
                 "type": "none",
                 "source": "XXXX",
                 "options": ["rbind", "nosuid",
                             "noexec", "nodev",
                             "rw", ], }
        self.rcex._container_specjson["mounts"].append(mount)
        self.rcex._del_mount_spec("/HOSTDIR", "/CONTDIR")
        self.assertEqual(len(self.rcex._container_specjson["mounts"]), 1)

    @patch('udocker.utils.filebind.FileBind.add')
    @patch('udocker.msg.Msg')
    @patch('udocker.engine.runc.os.path.isfile')
    @patch('udocker.engine.runc.os.path.isdir')
    @patch('udocker.engine.runc.RuncEngine._add_mount_spec')
    @patch('udocker.utils.filebind.FileBind')
    @patch('udocker.container.localrepo.LocalRepository')
    def test_11__add_volume_bindings(self, mock_local, mock_fbind,
                                     mock_add_mount_spec,
                                     mock_isdir, mock_isfile, mock_msg,
                                     mock_fbadd):
        """Test RuncEngine()._add_volume_bindings()."""
        mock_fbind.start.return_value = ("/HOSTDIR", "/CONTDIR")
        mock_isdir.reset_mock()
        self.rcex._filebind = mock_fbind
        self.rcex.opt["vol"] = dict()
        status = self.rcex._add_volume_bindings()
        self.assertFalse(mock_isdir.called)
        # isdir = False, isfile = False
        mock_fbind.start.return_value = ("/HOSTDIR", "/CONTDIR")
        mock_isdir.reset_mock()
        mock_isfile.reset_mock()
        mock_isdir.return_value = False
        mock_isfile.return_value = False
        self.rcex._filebind = mock_fbind
        self.rcex.opt["vol"] = []
        self.rcex.opt["vol"].append("/HOSTDIR:/CONTDIR")
        status = self.rcex._add_volume_bindings()
        self.assertTrue(mock_isdir.called)
        self.assertTrue(mock_isfile.called)
        # isdir = True
        mock_fbind.start.return_value = ("/HOSTDIR", "/CONTDIR")
        mock_isdir.reset_mock()
        mock_isfile.reset_mock()
        mock_add_mount_spec.reset_mock()
        mock_isdir.return_value = True
        mock_isfile.return_value = False
        self.rcex._filebind = mock_fbind
        self.rcex.opt["vol"] = []
        self.rcex.opt["vol"].append("/HOSTDIR:/CONTDIR")
        status = self.rcex._add_volume_bindings()
        self.assertTrue(mock_isdir.called)
        self.assertFalse(mock_isfile.called)
        self.assertTrue(mock_add_mount_spec.called)
        # isfile = True
        mock_fbind.start.return_value = ("/HOSTDIR", "/CONTDIR")
        mock_isdir.reset_mock()
        mock_isfile.reset_mock()
        mock_add_mount_spec.reset_mock()
        mock_fbind.reset_mock()
        mock_isdir.return_value = False
        mock_isfile.return_value = True
        Config.sysdirs_list = ["/CONTDIR"]
        self.rcex._filebind = mock_fbind
        self.rcex.opt["vol"] = []
        self.rcex.opt["vol"].append("/HOSTDIR:/CONTDIR")
        status = self.rcex._add_volume_bindings()
        self.assertTrue(mock_isdir.called)
        self.assertTrue(mock_isfile.called)
        # self.assertTrue(mock_fbadd.called)
        # isfile = True
        mock_fbind.start.return_value = ("/HOSTDIR", "/CONTDIR")
        mock_isdir.reset_mock()
        mock_isfile.reset_mock()
        mock_add_mount_spec.reset_mock()
        mock_fbind.reset_mock()
        mock_isdir.return_value = False
        mock_isfile.return_value = True
        Config.sysdirs_list = [""]
        self.rcex._filebind = mock_fbind
        self.rcex.opt["vol"] = []
        self.rcex.opt["vol"].append("/HOSTDIR:/CONTDIR")
        status = self.rcex._add_volume_bindings()
        self.assertTrue(mock_isdir.called)
        self.assertTrue(mock_isfile.called)
        self.assertFalse(mock_fbadd.called)

    @patch('udocker.msg.Msg')
    @patch('udocker.engine.runc.os.getenv')
    @patch('udocker.container.localrepo.LocalRepository')
    def test_12__check_env(self, mock_local, mock_getenv, mock_msg):
        """Test RuncEngine()._check_env()."""
        self.rcex.opt["env"] = []
        status = self.rcex._check_env()
        self.assertTrue(status)
        #
        mock_getenv.return_value = "aaaa"
        self.rcex.opt["env"] = ["", "HOME=/home/user01", "AAAA", ]
        status = self.rcex._check_env()
        self.assertTrue(status)
        self.assertNotIn("", self.rcex.opt["env"])
        self.assertIn("AAAA=aaaa", self.rcex.opt["env"])
        self.assertIn("HOME=/home/user01", self.rcex.opt["env"])
        #
        self.rcex.opt["env"] = ["3WRONG=/home/user01", ]
        status = self.rcex._check_env()
        self.assertFalse(status)
        #
        self.rcex.opt["env"] = ["WR ONG=/home/user01", ]
        status = self.rcex._check_env()
        self.assertFalse(status)

    @patch('udocker.engine.runc.subprocess.call')
    @patch('udocker.msg.Msg')
    @patch('udocker.utils.filebind.FileBind')
    @patch('udocker.helper.unique.Unique')
    @patch('udocker.engine.runc.RuncEngine._run_invalid_options')
    @patch('udocker.engine.runc.RuncEngine._del_mount_spec')
    @patch('udocker.engine.runc.RuncEngine._run_banner')
    @patch('udocker.engine.runc.RuncEngine._save_spec')
    @patch('udocker.engine.runc.RuncEngine._add_volume_bindings')
    @patch('udocker.engine.runc.RuncEngine._set_spec')
    @patch('udocker.engine.runc.RuncEngine._check_env')
    @patch('udocker.engine.runc.RuncEngine._run_env_set')
    @patch('udocker.engine.runc.RuncEngine._uid_check')
    @patch('udocker.engine.runc.RuncEngine._run_env_cleanup_list')
    @patch('udocker.engine.runc.RuncEngine._load_spec')
    @patch('udocker.engine.runc.RuncEngine._select_runc')
    @patch('udocker.engine.runc.RuncEngine._run_init')
    @patch('udocker.container.localrepo.LocalRepository')
    def test_16_run(self, mock_local, mock_run_init, mock_sel_runc,
                    mock_load_spec, mock_uid_check,
                    mock_run_env_cleanup_list, mock_env_set, mock_check_env,
                    mock_set_spec, mock_add_bindings, mock_save_spec,
                    mock_run_banner, mock_del_mount_spec, mock_inv_opt,
                    mock_unique, mock_fbind, mock_msg, mock_call):
        """Test RuncEngine().run()."""
        mock_run_init.return_value = False
        status = self.rcex.run("CONTAINERID")
        self.assertEqual(status, 2)
        #
        mock_run_init.return_value = True
        mock_load_spec.return_value = False
        status = self.rcex.run("CONTAINERID")
        self.assertEqual(status, 4)
        #
        mock_run_init.return_value = True
        mock_load_spec.return_value = True
        mock_check_env.return_value = False
        mock_run_env_cleanup_list.reset_mock()
        self.rcex.opt["hostenv"] = []
        status = self.rcex.run("CONTAINERID")
        self.assertTrue(mock_run_env_cleanup_list.called)
        self.assertEqual(status, 5)
        #
        mock_run_init.return_value = True
        mock_load_spec.return_value = True
        mock_check_env.return_value = True
        mock_unique.return_value.uuid.return_value = "EXECUTION_ID"
        mock_run_env_cleanup_list.reset_mock()
        mock_call.reset_mock()
        self.rcex.runc_exec = "true"
        self.rcex.container_dir = "/.udocker/containers/CONTAINER/ROOT"
        self.rcex.opt["hostenv"] = []
        # status = self.rcex.run("CONTAINERID")
        # self.assertTrue(mock_run_env_cleanup_list.called)
        # self.assertTrue(mock_call.called)


if __name__ == '__main__':
    main()
