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
    BUILTINS = "builtins"
else:
    BUILTINS = "__builtin__"

BOPEN = BUILTINS + '.open'


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

    def tearDown(self):
        pass

    def test_01_init(self):
        """Test RuncEngine() constructor."""
        rcex = RuncEngine(self.conf, self.local, self.xmode)
        self.assertEqual(rcex.runc_exec, None)

    @patch('udocker.engine.runc.ExecutionEngineCommon._oskernel_isgreater')
    @patch('udocker.engine.runc.ExecutionEngineCommon')
    @patch('udocker.engine.runc.FileUtil.find_file_in_dir')
    def test_02__select_runc(self, mock_find, mock_execmode, mock_isgreater):
        """Test RuncEngine()._select_runc()."""
        self.conf['arch'] = "arm"
        mock_isgreater.return_value = False
        mock_find.return_value = "runc-arm"
        mock_execmode.return_value.get_mode.return_value = ""
        rcex = RuncEngine(self.conf, self.local, self.xmode)
        rcex.exec_mode = mock_execmode
        rcex._select_runc()
        self.assertEqual(rcex.runc_exec, "runc-arm")

    @patch('udocker.engine.runc.FileUtil.size.remove')
    @patch('udocker.engine.runc.FileUtil.size')
    @patch('udocker.engine.runc.subprocess.call')
    @patch('udocker.engine.runc.os.path.realpath')
    @patch('udocker.engine.runc.FileUtil')
    def test_03__load_spec(self, mock_futil, mock_realpath,
                           mock_call, mock_size, mock_rm):
        """Test RuncEngine()._load_spec()."""
        mock_futil.reset()
        mock_size.return_value = 1
        rcex = RuncEngine(self.conf, self.local, self.xmode)
        rcex._load_spec(False)
        self.assertFalse(mock_rm.called)

        mock_futil.reset()
        mock_size.return_value = 1
        rcex = RuncEngine(self.conf, self.local, self.xmode)
        rcex._load_spec(True)
        # self.assertTrue(mock_rm.called)

        mock_futil.reset()
        mock_size.return_value = -1
        mock_realpath.return_value = "/.udocker/containers/aaaaa"
        mock_call.return_value = True
        rcex = RuncEngine(self.conf, self.local, self.xmode)
        rcex.runc_exec = "runc"
        status = rcex._load_spec(False)
        self.assertFalse(status)

        mock_futil.reset()
        mock_size.return_value = -1
        mock_realpath.return_value = "/.udocker/containers/aaaaa"
        mock_call.return_value = False  # ok
        mock_jsonload.return_value = "JSON"
        rcex = RuncEngine(self.conf, self.local, self.xmode)
        rcex.runc_exec = "runc"
        with patch(BOPEN, mock_open()):
            status = rcex._load_spec(False)
        self.assertEqual(status, "JSON")

        mock_futil.reset()
        mock_size.return_value = -1
        mock_realpath.return_value = "/.udocker/containers/aaaaa"
        mock_call.return_value = False  # ok
        mock_jsonload.return_value = "JSON"
        mock_jsonload.side_effect = OSError("reading json")
        rcex = RuncEngine(self.conf, self.local, self.xmode)
        rcex.runc_exec = "runc"
        with patch(BOPEN, mock_open()):
            status = rcex._load_spec(False)
        self.assertEqual(status, None)

    def test_05__remove_quotes(self):
        """Test RuncEngine()._remove_quotes()."""
        pass

    @patch('udocker.engine.runc.os.getgid')
    @patch('udocker.engine.runc.os.getuid')
    @patch('udocker.engine.runc.platform.node')
    @patch('udocker.engine.runc.os.path.realpath')
    def test_06__set_spec(self, mock_realpath, mock_node,
                          mock_getuid, mock_getgid):
        """Test RuncEngine()._set_spec()."""
        # rcex.opt["hostname"] has nodename
        mock_realpath.return_value = "/.udocker/containers/aaaaaa/ROOT"
        mock_node.return_value = "nodename.local"
        rcex = RuncEngine(self.conf, self.local, self.xmode)
        rcex.opt = dict()
        rcex._container_specjson = dict()
        rcex._container_specjson["root"] = dict()
        rcex._container_specjson["process"] = dict()
        rcex._container_specjson["linux"] = dict()
        rcex._container_specjson["linux"]["uidMappings"] = dict()
        rcex._container_specjson["linux"]["gidMappings"] = dict()
        rcex.opt["cwd"] = "/"
        rcex.opt["env"] = []
        rcex.opt["cmd"] = "bash"
        rcex.opt["hostname"] = "node.domain"
        json_obj = rcex._set_spec()
        self.assertEqual(json_obj["hostname"], "node.domain")

        # empty rcex.opt["hostname"]
        mock_realpath.return_value = "/.udocker/containers/aaaaaa/ROOT"
        mock_node.return_value = "nodename.local"
        rcex = RuncEngine(self.conf, self.local, self.xmode)
        rcex.opt = dict()
        rcex._container_specjson = dict()
        rcex._container_specjson["root"] = dict()
        rcex._container_specjson["process"] = dict()
        rcex._container_specjson["linux"] = dict()
        rcex._container_specjson["linux"]["uidMappings"] = dict()
        rcex._container_specjson["linux"]["gidMappings"] = dict()
        rcex.opt["cwd"] = "/"
        rcex.opt["env"] = []
        rcex.opt["cmd"] = "bash"
        rcex.opt["hostname"] = ""
        json_obj = rcex._set_spec()
        self.assertEqual(json_obj["hostname"], "nodename.local")

        # environment passes to container json
        mock_realpath.return_value = "/.udocker/containers/aaaaaa/ROOT"
        mock_node.return_value = "nodename.local"
        rcex = RuncEngine(self.conf, self.local, self.xmode)
        rcex.opt = dict()
        rcex._container_specjson = dict()
        rcex._container_specjson["root"] = dict()
        rcex._container_specjson["process"] = dict()
        rcex._container_specjson["linux"] = dict()
        rcex._container_specjson["linux"]["uidMappings"] = dict()
        rcex._container_specjson["linux"]["gidMappings"] = dict()
        rcex.opt["cwd"] = "/"
        rcex.opt["env"] = ["AA=aa", "BB=bb"]
        rcex.opt["cmd"] = "bash"
        rcex.opt["hostname"] = ""
        json_obj = rcex._set_spec()
        self.assertIn("AA=aa", json_obj["process"]["env"])

        # environment syntax error
        mock_realpath.return_value = "/.udocker/containers/aaaaaa/ROOT"
        mock_node.return_value = "nodename.local"
        rcex = RuncEngine(self.conf, self.local, self.xmode)
        rcex.opt = dict()
        rcex._container_specjson = dict()
        rcex._container_specjson["root"] = dict()
        rcex._container_specjson["process"] = dict()
        rcex._container_specjson["linux"] = dict()
        rcex._container_specjson["linux"]["uidMappings"] = dict()
        rcex._container_specjson["linux"]["gidMappings"] = dict()
        rcex.opt["cwd"] = "/"
        rcex.opt["env"] = ["=aa", "BB=bb"]
        rcex.opt["cmd"] = "bash"
        rcex.opt["hostname"] = ""
        json_obj = rcex._set_spec()
        self.assertNotIn("AA=aa", json_obj["process"]["env"])

        # uid and gid mappings
        mock_realpath.return_value = "/.udocker/containers/aaaaaa/ROOT"
        mock_node.return_value = "nodename.local"
        mock_getuid.return_value = 10000
        mock_getgid.return_value = 10000
        rcex = RuncEngine(self.conf, self.local, self.xmode)
        rcex.opt = dict()
        rcex._container_specjson = dict()
        rcex._container_specjson["root"] = dict()
        rcex._container_specjson["process"] = dict()
        rcex._container_specjson["linux"] = dict()
        rcex._container_specjson["linux"]["uidMappings"] = dict()
        rcex._container_specjson["linux"]["gidMappings"] = dict()
        rcex._container_specjson["linux"]["uidMappings"]["XXX"] = 0
        rcex._container_specjson["linux"]["gidMappings"]["XXX"] = 0
        rcex.opt["cwd"] = "/"
        rcex.opt["env"] = ["AA=aa", "BB=bb"]
        rcex.opt["cmd"] = "bash"
        rcex.opt["hostname"] = ""
        json_obj = rcex._set_spec()
        self.assertFalse(mock_getuid.called)
        self.assertFalse(mock_getgid.called)

    @patch('udocker.engine.runc.Msg')
    def test_07__uid_check(self, mock_msg):
        """Test RuncEngine()._uid_check()."""
        rcex = RuncEngine(self.conf, self.local, self.xmode)
        rcex.opt = dict()
        rcex._uid_check()
        self.assertFalse(mock_msg.called)

        rcex = RuncEngine(self.conf, self.local, self.xmode)
        rcex.opt = dict()
        rcex.opt["user"] = "root"
        rcex._uid_check()
        self.assertFalse(mock_msg.called)

        rcex = RuncEngine(self.conf, self.local, self.xmode)
        rcex.opt = dict()
        rcex.opt["user"] = "user01"
        rcex._uid_check()
        # self.assertTrue(mock_msg.called)

    def test_08__add_device_spec(self):
        """Test RuncEngine()._add_device_spec()."""
        pass

    def test_09__add_devices(self):
        """Test RuncEngine()._add_device_spec()."""
        pass

    def test_10__create_mountpoint(self):
        """Test RuncEngine()._create_mountpoint()."""
        rcex = RuncEngine(self.conf, self.local, self.xmode)
        status = rcex._create_mountpoint("HOSTPATH", "CONTPATH")
        self.assertTrue(status)

    def test_11__add_mount_spec(self):
        """Test RuncEngine()._add_mount_spec()."""
        rcex = RuncEngine(self.conf, self.local, self.xmode)
        rcex._container_specjson = dict()
        rcex._container_specjson["mounts"] = []
        status = rcex._add_mount_spec("/HOSTDIR", "/CONTDIR")
        mount = rcex._container_specjson["mounts"][0]
        self.assertEqual(mount["destination"], "/CONTDIR")
        self.assertEqual(mount["source"], "/HOSTDIR")
        self.assertIn("ro", mount["options"])

        # rw
        rcex = RuncEngine(self.conf, self.local, self.xmode)
        rcex._container_specjson = dict()
        rcex._container_specjson["mounts"] = []
        status = rcex._add_mount_spec("/HOSTDIR", "/CONTDIR", True)
        mount = rcex._container_specjson["mounts"][0]
        self.assertEqual(mount["destination"], "/CONTDIR")
        self.assertEqual(mount["source"], "/HOSTDIR")
        self.assertIn("rw", mount["options"])

    def test_12__del_mount_spec(self):
        """Test RuncEngine()._del_mount_spec()."""
        rcex = RuncEngine(self.conf, self.local, self.xmode)
        rcex._container_specjson = dict()
        rcex._container_specjson["mounts"] = []
        mount = {"destination": "/CONTDIR",
                 "type": "none",
                 "source": "/HOSTDIR",
                 "options": ["rbind", "nosuid",
                             "noexec", "nodev",
                             "rw", ], }
        rcex._container_specjson["mounts"].append(mount)
        rcex._del_mount_spec("/HOSTDIR", "/CONTDIR")
        self.assertEqual(len(rcex._container_specjson["mounts"]), 0)

        rcex = RuncEngine(self.conf, self.local, self.xmode)
        rcex._container_specjson = dict()
        rcex._container_specjson["mounts"] = []
        mount = {"destination": "/XXXX",
                 "type": "none",
                 "source": "/HOSTDIR",
                 "options": ["rbind", "nosuid",
                             "noexec", "nodev",
                             "rw", ], }
        rcex._container_specjson["mounts"].append(mount)
        rcex._del_mount_spec("/HOSTDIR", "/CONTDIR")
        self.assertEqual(len(rcex._container_specjson["mounts"]), 1)

        rcex = RuncEngine(self.conf, self.local, self.xmode)
        rcex._container_specjson = dict()
        rcex._container_specjson["mounts"] = []
        mount = {"destination": "/CONTDIR",
                 "type": "none",
                 "source": "XXXX",
                 "options": ["rbind", "nosuid",
                             "noexec", "nodev",
                             "rw", ], }
        rcex._container_specjson["mounts"].append(mount)
        rcex._del_mount_spec("/HOSTDIR", "/CONTDIR")
        self.assertEqual(len(rcex._container_specjson["mounts"]), 1)

    @patch('udocker.engine.runc.FileBind.add')
    @patch('udocker.engine.runc.Msg')
    @patch('udocker.engine.runc.os.path.isfile')
    @patch('udocker.engine.runc.os.path.isdir')
    @patch.object(RuncEngine, '_add_mount_spec')
    @patch('udocker.engine.runc.FileBind')
    def test_13__add_volume_bindings(self, mock_fbind,
                                     mock_add_mount_spec,
                                     mock_isdir, mock_isfile, mock_msg,
                                     mock_fbadd):
        """Test RuncEngine()._add_volume_bindings()."""
        mock_fbind.start.return_value = ("/HOSTDIR", "/CONTDIR")
        mock_isdir.reset_mock()
        rcex = RuncEngine(self.conf, self.local, self.xmode)
        rcex._filebind = mock_fbind
        rcex.opt["vol"] = dict()
        status = rcex._add_volume_bindings()
        self.assertFalse(mock_isdir.called)

        # isdir = False, isfile = False
        mock_fbind.start.return_value = ("/HOSTDIR", "/CONTDIR")
        mock_isdir.reset_mock()
        mock_isfile.reset_mock()
        mock_isdir.return_value = False
        mock_isfile.return_value = False
        rcex = RuncEngine(self.conf, self.local, self.xmode)
        rcex._filebind = mock_fbind
        rcex.opt["vol"] = []
        rcex.opt["vol"].append("/HOSTDIR:/CONTDIR")
        status = rcex._add_volume_bindings()
        self.assertTrue(mock_isdir.called)
        self.assertTrue(mock_isfile.called)

        # isdir = True
        mock_fbind.start.return_value = ("/HOSTDIR", "/CONTDIR")
        mock_isdir.reset_mock()
        mock_isfile.reset_mock()
        mock_add_mount_spec.reset_mock()
        mock_isdir.return_value = True
        mock_isfile.return_value = False
        rcex = RuncEngine(self.conf, self.local, self.xmode)
        rcex._filebind = mock_fbind
        rcex.opt["vol"] = []
        rcex.opt["vol"].append("/HOSTDIR:/CONTDIR")
        status = rcex._add_volume_bindings()
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
        self.conf['sysdirs_list'] = ["/CONTDIR"]
        rcex = RuncEngine(self.conf, self.local, self.xmode)
        rcex._filebind = mock_fbind
        rcex.opt["vol"] = []
        rcex.opt["vol"].append("/HOSTDIR:/CONTDIR")
        status = rcex._add_volume_bindings()
        self.assertTrue(mock_isdir.called)
        self.assertTrue(mock_isfile.called)
        self.assertTrue(mock_fbadd.called)

        # isfile = True
        mock_fbind.start.return_value = ("/HOSTDIR", "/CONTDIR")
        mock_isdir.reset_mock()
        mock_isfile.reset_mock()
        mock_add_mount_spec.reset_mock()
        mock_fbind.reset_mock()
        mock_isdir.return_value = False
        mock_isfile.return_value = True
        self.conf['sysdirs_list'] = [""]
        rcex = RuncEngine(self.conf, self.local, self.xmode)
        rcex._filebind = mock_fbind
        rcex.opt["vol"] = []
        rcex.opt["vol"].append("/HOSTDIR:/CONTDIR")
        status = rcex._add_volume_bindings()
        self.assertTrue(mock_isdir.called)
        self.assertTrue(mock_isfile.called)
        # self.assertFalse(mock_fbadd.called)

    @patch('udocker.engine.runc.Msg')
    @patch('udocker.engine.runc.os.getenv')
    def test_14__check_env(self, mock_getenv, mock_msg):
        """Test RuncEngine()._check_env()."""
        rcex = RuncEngine(self.conf, self.local, self.xmode)
        rcex.opt["env"] = []
        status = rcex._check_env()
        self.assertTrue(status)

        mock_getenv.return_value = "aaaa"
        rcex = RuncEngine(self.conf, self.local, self.xmode)
        rcex.opt["env"] = ["", "HOME=/home/user01", "AAAA", ]
        status = rcex._check_env()
        self.assertTrue(status)
        self.assertNotIn("", rcex.opt["env"])
        self.assertIn("AAAA=aaaa", rcex.opt["env"])
        self.assertIn("HOME=/home/user01", rcex.opt["env"])

        rcex = RuncEngine(self.conf, self.local, self.xmode)
        rcex.opt["env"] = ["3WRONG=/home/user01", ]
        status = rcex._check_env()
        self.assertFalse(status)

        rcex = RuncEngine(self.conf, self.local, self.xmode)
        rcex.opt["env"] = ["WR ONG=/home/user01", ]
        status = rcex._check_env()
        self.assertFalse(status)

    def test_15__run_invalid_options(self):
        """Test RuncEngine()._run_invalid_options()."""
        pass

    @patch('udocker.engine.runc.subprocess.call')
    @patch('udocker.engine.runc.Msg')
    @patch('udocker.engine.runc.FileBind')
    @patch('udocker.engine.runc.Unique')
    @patch.object(RuncEngine, '_run_invalid_options')
    @patch.object(RuncEngine, '_del_mount_spec')
    @patch.object(RuncEngine, '_run_banner')
    @patch.object(RuncEngine, '_save_spec')
    @patch.object(RuncEngine, '_add_volume_bindings')
    @patch.object(RuncEngine, '_set_spec')
    @patch.object(RuncEngine, '_check_env')
    @patch.object(RuncEngine, '_run_env_set')
    @patch.object(RuncEngine, '_uid_check')
    @patch.object(RuncEngine, '_run_env_cleanup_list')
    @patch.object(RuncEngine, '_load_spec')
    @patch.object(RuncEngine, '_select_runc')
    @patch.object(RuncEngine, '_run_init')
    def test_16_run(self, mock_run_init, mock_sel_runc,
                    mock_load_spec, mock_uid_check,
                    mock_run_env_cleanup_list, mock_env_set, mock_check_env,
                    mock_set_spec, mock_add_bindings, mock_save_spec,
                    mock_run_banner, mock_del_mount_spec, mock_inv_opt,
                    mock_unique, mock_fbind, mock_msg, mock_call):
        """Test RuncEngine().run()."""
        mock_run_init.return_value = False
        rcex = RuncEngine(self.conf, self.local, self.xmode)
        status = rcex.run("CONTAINERID")
        self.assertEqual(status, 2)

        mock_run_init.return_value = True
        mock_load_spec.return_value = False
        rcex = RuncEngine(self.conf, self.local, self.xmode)
        status = rcex.run("CONTAINERID")
        self.assertEqual(status, 4)

        mock_run_init.return_value = True
        mock_load_spec.return_value = True
        mock_check_env.return_value = False
        mock_run_env_cleanup_list.reset_mock()
        rcex = RuncEngine(self.conf, self.local, self.xmode)
        rcex.opt["hostenv"] = []
        status = rcex.run("CONTAINERID")
        self.assertTrue(mock_run_env_cleanup_list.called)
        self.assertEqual(status, 5)

        mock_run_init.return_value = True
        mock_load_spec.return_value = True
        mock_check_env.return_value = True
        mock_unique.return_value.uuid.return_value = "EXECUTION_ID"
        mock_run_env_cleanup_list.reset_mock()
        mock_call.reset_mock()
        rcex = RuncEngine(self.conf, self.local, self.xmode)
        rcex.runc_exec = "true"
        rcex.container_dir = "/.udocker/containers/CONTAINER/ROOT"
        rcex.opt["hostenv"] = []
        # status = rcex.run("CONTAINERID")
        # self.assertTrue(mock_run_env_cleanup_list.called)
        # self.assertTrue(mock_call.called)

    def test_17_run_pty(self):
        """Test RuncEngine().run_pty()."""
        pass

    def test_18_run_nopty(self):
        """Test RuncEngine().run_nopty()."""
        pass


if __name__ == '__main__':
    main()
