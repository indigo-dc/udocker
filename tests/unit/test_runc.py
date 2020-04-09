#!/usr/bin/env python
"""
udocker unit tests: RuncEngine
"""

import sys
from unittest import TestCase, main
from udocker.config import Config
from udocker.container.localrepo import LocalRepository
from udocker.engine.execmode import ExecutionMode
from udocker.engine.runc import RuncEngine
try:
    from unittest.mock import Mock, patch, MagicMock, mock_open
except ImportError:
    from mock import Mock, patch, MagicMock, mock_open

if sys.version_info[0] >= 3:
    BUILTINS = "builtins"
else:
    BUILTINS = "__builtin__"

BOPEN = BUILTINS + '.open'


class RuncEngineTestCase(TestCase):
    """Test RuncEngine() containers execution with runC."""

    def setUp(self):
        Config().getconf()
        Config().conf['hostauth_list'] = ("/etc/passwd", "/etc/group")
        Config().conf['cmd'] = "/bin/bash"
        Config().conf['cpu_affinity_exec_tools'] = (["numactl", "-C", "%s", "--", ],
                                                    ["taskset", "-c", "%s", ])
        Config().conf['runc_capabilities'] = [
            "CAP_KILL", "CAP_NET_BIND_SERVICE", "CAP_CHOWN", "CAP_DAC_OVERRIDE",
            "CAP_FOWNER", "CAP_FSETID", "CAP_KILL", "CAP_SETGID", "CAP_SETUID",
            "CAP_SETPCAP", "CAP_NET_BIND_SERVICE", "CAP_NET_RAW",
            "CAP_SYS_CHROOT", "CAP_MKNOD", "CAP_AUDIT_WRITE", "CAP_SETFCAP",
        ]
        Config().conf['valid_host_env'] = "HOME"
        Config().conf['username'] = "user"
        Config().conf['userhome'] = "/"
        Config().conf['oskernel'] = "4.8.13"
        Config().conf['location'] = ""
        self.local = LocalRepository()
        self.xmode = ExecutionMode(self.local, "12345")

    def tearDown(self):
        pass

    # def test_01_init(self):
    #     """Test01 RuncEngine() constructor."""
    #     rcex = RuncEngine(self.local, self.xmode)

    @patch('udocker.engine.runc.ExecutionEngineCommon._oskernel_isgreater')
    @patch('udocker.engine.runc.ExecutionEngineCommon')
    @patch('udocker.engine.runc.FileUtil.find_file_in_dir')
    def test_02_select_runc(self, mock_find, mock_execmode, mock_isgreater):
        """Test02 RuncEngine().select_runc()."""
        Config().conf['arch'] = "arm"
        mock_isgreater.return_value = False
        mock_find.return_value = "runc-arm"
        mock_execmode.return_value.get_mode.return_value = ""
        rcex = RuncEngine(self.local, self.xmode)
        rcex.exec_mode = mock_execmode
        # rcex.select_runc()

    @patch('udocker.engine.runc.FileUtil.remove')
    @patch('udocker.engine.runc.FileUtil.size')
    @patch('udocker.engine.runc.subprocess.call')
    @patch('udocker.engine.runc.os.path.realpath')
    @patch('udocker.engine.runc.FileUtil')
    def test_03__load_spec(self, mock_futil, mock_realpath,
                           mock_call, mock_size, mock_rm):
        """Test03 RuncEngine()._load_spec()."""
        mock_futil.reset()
        mock_size.return_value = 1
        rcex = RuncEngine(self.local, self.xmode)
        rcex._container_specfile = "/config.json"
        rcex._load_spec(True)
        self.assertFalse(mock_rm.called)

        # mock_futil.reset()
        # mock_size.return_value = 1
        # rcex = RuncEngine(self.conf, self.local, self.xmode)
        # rcex._container_specfile = "/config.json"
        # rcex._load_spec(True)
        # # self.assertTrue(mock_rm.called)

        mock_futil.reset()
        mock_size.return_value = -1
        mock_realpath.return_value = "/.udocker/containers/aaaaa"
        mock_call.return_value = True
        rcex = RuncEngine(self.local, self.xmode)
        rcex.runc_exec = "runc"
        status = rcex._load_spec(False)
        self.assertFalse(status)

        # mock_futil.reset()
        # mock_size.return_value = -1
        # mock_realpath.return_value = "/.udocker/containers/aaaaa"
        # mock_call.return_value = False  # ok
        # self.local.load_json = "JSON"
        # rcex = RuncEngine(self.conf, self.local, self.xmode)
        # rcex.runc_exec = "runc"
        # with patch(BOPEN, mock_open()):
        #     status = rcex._load_spec(False)
        # self.assertEqual(status, "JSON")

        # mock_futil.reset()
        # mock_size.return_value = -1
        # mock_realpath.return_value = "/.udocker/containers/aaaaa"
        # mock_call.return_value = False  # ok
        # self.local.load_json = "JSON"
        # rcex = RuncEngine(self.conf, self.local, self.xmode)
        # rcex.runc_exec = "runc"
        # with patch(BOPEN, mock_open()):
        #     status = rcex._load_spec(False)
        # self.assertEqual(status, None)

    # def test_04__save_spec(self):
    #     """Test04 RuncEngine()._save_spec()."""
    #     pass

    @patch('udocker.engine.runc.os.getgid')
    @patch('udocker.engine.runc.os.getuid')
    @patch('udocker.engine.runc.platform.node')
    @patch('udocker.engine.runc.os.path.realpath')
    def test_05__set_spec(self, mock_realpath, mock_node,
                          mock_getuid, mock_getgid):
        """Test05 RuncEngine()._set_spec()."""
        # rcex.opt["hostname"] has nodename
        mock_realpath.return_value = "/.udocker/containers/aaaaaa/ROOT"
        mock_node.return_value = "nodename.local"
        rcex = RuncEngine(self.local, self.xmode)
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
        rcex = RuncEngine(self.local, self.xmode)
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
        rcex = RuncEngine(self.local, self.xmode)
        rcex.opt = dict()
        rcex._container_specjson = dict()
        rcex._container_specjson["root"] = dict()
        rcex._container_specjson["process"] = dict()
        rcex._container_specjson["linux"] = dict()
        rcex._container_specjson["linux"]["uidMappings"] = dict()
        rcex._container_specjson["linux"]["gidMappings"] = dict()
        rcex.opt["cwd"] = "/"
        rcex.opt["env"] = [("AA", "aa"), ("BB", "bb")]
        rcex.opt["cmd"] = "bash"
        rcex.opt["hostname"] = ""
        json_obj = rcex._set_spec()
        self.assertIn("AA=aa", json_obj["process"]["env"])

        # environment syntax error
        mock_realpath.return_value = "/.udocker/containers/aaaaaa/ROOT"
        mock_node.return_value = "nodename.local"
        rcex = RuncEngine(self.local, self.xmode)
        rcex.opt = dict()
        rcex._container_specjson = dict()
        rcex._container_specjson["root"] = dict()
        rcex._container_specjson["process"] = dict()
        rcex._container_specjson["linux"] = dict()
        rcex._container_specjson["linux"]["uidMappings"] = dict()
        rcex._container_specjson["linux"]["gidMappings"] = dict()
        rcex.opt["cwd"] = "/"
        rcex.opt["env"] = [("AA", "aa"), ("BB", "bb")]
        rcex.opt["cmd"] = "bash"
        rcex.opt["hostname"] = ""
        json_obj = rcex._set_spec()
        # self.assertNotIn("AA=aa", json_obj["process"]["env"])

        # uid and gid mappings
        mock_realpath.return_value = "/.udocker/containers/aaaaaa/ROOT"
        mock_node.return_value = "nodename.local"
        mock_getuid.return_value = 10000
        mock_getgid.return_value = 10000
        rcex = RuncEngine(self.local, self.xmode)
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
        rcex.opt["env"] = [("AA", "aa"), ("BB", "bb")]
        rcex.opt["cmd"] = "bash"
        rcex.opt["hostname"] = ""
        json_obj = rcex._set_spec()
        self.assertFalse(mock_getuid.called)
        self.assertFalse(mock_getgid.called)

    @patch('udocker.engine.runc.Msg')
    def test_06__uid_check(self, mock_msg):
        """Test06 RuncEngine()._uid_check()."""
        rcex = RuncEngine(self.local, self.xmode)
        rcex.opt = dict()
        rcex._uid_check()
        self.assertFalse(mock_msg.called)

        rcex = RuncEngine(self.local, self.xmode)
        rcex.opt = dict()
        rcex.opt["user"] = "root"
        rcex._uid_check()
        self.assertFalse(mock_msg.called)

        rcex = RuncEngine(self.local, self.xmode)
        rcex.opt = dict()
        rcex.opt["user"] = "user01"
        rcex._uid_check()
        # self.assertTrue(mock_msg.called)

    # def test_07__add_capabilities_spec(self):
    #     """Test07 RuncEngine()._add_capabilities_spec()."""
    #     pass

    # def test_08__add_device_spec(self):
    #     """Test08 RuncEngine()._add_device_spec()."""
    #     pass

    # def test_09__add_devices(self):
    #     """Test09 RuncEngine()._add_device_spec()."""
    #     pass

    def test_10__add_mount_spec(self):
        """Test10 RuncEngine()._add_mount_spec()."""
        rcex = RuncEngine(self.local, self.xmode)
        rcex._container_specjson = dict()
        rcex._container_specjson["mounts"] = []
        status = rcex._add_mount_spec("/HOSTDIR", "/CONTDIR")
        mount = rcex._container_specjson["mounts"][0]
        self.assertEqual(mount["destination"], "/CONTDIR")
        self.assertEqual(mount["source"], "/HOSTDIR")
        self.assertIn("ro", mount["options"])

        # rw
        rcex = RuncEngine(self.local, self.xmode)
        rcex._container_specjson = dict()
        rcex._container_specjson["mounts"] = []
        status = rcex._add_mount_spec("/HOSTDIR", "/CONTDIR", True)
        mount = rcex._container_specjson["mounts"][0]
        self.assertEqual(mount["destination"], "/CONTDIR")
        self.assertEqual(mount["source"], "/HOSTDIR")
        self.assertIn("rw", mount["options"])

    def test_11__del_mount_spec(self):
        """Test11 RuncEngine()._del_mount_spec()."""
        rcex = RuncEngine(self.local, self.xmode)
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
        # self.assertEqual(len(rcex._container_specjson["mounts"]), 0)

        rcex = RuncEngine(self.local, self.xmode)
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

        rcex = RuncEngine(self.local, self.xmode)
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

    # def test_12__sel_mount_spec(self):
    #     """Test12 RuncEngine()._sel_mount_spec()."""
    #     pass

    # def test_13__mod_mount_spec(self):
    #     """Test13 RuncEngine()._mod_mount_spec()."""
    #     pass

    @patch('udocker.engine.runc.FileBind.add')
    @patch('udocker.engine.runc.Msg')
    @patch('udocker.engine.runc.os.path.isfile')
    @patch('udocker.engine.runc.os.path.isdir')
    @patch.object(RuncEngine, '_add_mount_spec')
    @patch('udocker.engine.runc.FileBind')
    def test_14__add_volume_bindings(self, mock_fbind,
                                     mock_add_mount_spec,
                                     mock_isdir, mock_isfile, mock_msg,
                                     mock_fbadd):
        """Test14 RuncEngine()._add_volume_bindings()."""
        mock_fbind.start.return_value = ("/HOSTDIR", "/CONTDIR")
        mock_isdir.reset_mock()
        rcex = RuncEngine(self.local, self.xmode)
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
        rcex = RuncEngine(self.local, self.xmode)
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
        rcex = RuncEngine(self.local, self.xmode)
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
        Config().conf['sysdirs_list'] = ["/CONTDIR"]
        rcex = RuncEngine(self.local, self.xmode)
        rcex._filebind = mock_fbind
        rcex.opt["vol"] = []
        rcex.opt["vol"].append("/HOSTDIR:/CONTDIR")
        status = rcex._add_volume_bindings()
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
        Config().conf['sysdirs_list'] = [""]
        rcex = RuncEngine(self.local, self.xmode)
        rcex._filebind = mock_fbind
        rcex.opt["vol"] = []
        rcex.opt["vol"].append("/HOSTDIR:/CONTDIR")
        status = rcex._add_volume_bindings()
        self.assertTrue(mock_isdir.called)
        self.assertTrue(mock_isfile.called)
        # self.assertFalse(mock_fbadd.called)

    # def test_15__run_invalid_options(self):
    #     """Test15 RuncEngine()._run_invalid_options()."""
    #     pass

    # def test_16__proot_overlay(self):
    #     """Test16 RuncEngine()._proot_overlay()."""
    #     pass

    @patch('udocker.engine.runc.subprocess.call')
    @patch('udocker.engine.runc.Msg')
    @patch('udocker.engine.runc.FileBind')
    @patch('udocker.engine.runc.Unique')
    @patch.object(RuncEngine, '_run_invalid_options')
    @patch.object(RuncEngine, '_del_mount_spec')
    @patch.object(RuncEngine, '_run_banner')
    @patch.object(RuncEngine, '_add_volume_bindings')
    @patch.object(RuncEngine, '_set_spec')
    @patch.object(RuncEngine, '_run_env_set')
    @patch.object(RuncEngine, '_uid_check')
    @patch.object(RuncEngine, '_run_env_cleanup_list')
    @patch.object(RuncEngine, '_load_spec')
    @patch.object(RuncEngine, 'select_runc')
    @patch.object(RuncEngine, '_run_init')
    def test_17_run(self, mock_run_init, mock_sel_runc,
                    mock_load_spec, mock_uid_check,
                    mock_run_env_cleanup_list, mock_env_set,
                    mock_set_spec, mock_add_bindings,
                    mock_run_banner, mock_del_mount_spec, mock_inv_opt,
                    mock_unique, mock_fbind, mock_msg, mock_call):
        """Test17 RuncEngine().run()."""
        mock_run_init.return_value = False
        rcex = RuncEngine(self.local, self.xmode)
        status = rcex.run("CONTAINERID")
        self.assertEqual(status, 2)

        mock_run_init.return_value = True
        mock_load_spec.return_value = False
        rcex = RuncEngine(self.local, self.xmode)
        status = rcex.run("CONTAINERID")
        self.assertEqual(status, 4)

        mock_run_init.return_value = True
        mock_load_spec.return_value = True
        mock_run_env_cleanup_list.reset_mock()
        Config().conf['runc_capabilities'] = []
        # rcex = RuncEngine(self.local, self.xmode)
        # rcex.opt["hostenv"] = []
        # status = rcex.run("CONTAINERID")
        # self.assertTrue(mock_run_env_cleanup_list.called)
        # self.assertEqual(status, 5)

        mock_run_init.return_value = True
        mock_load_spec.return_value = True
        mock_unique.return_value.uuid.return_value = "EXECUTION_ID"
        mock_run_env_cleanup_list.reset_mock()
        mock_call.reset_mock()
        rcex = RuncEngine(self.local, self.xmode)
        rcex.runc_exec = "true"
        rcex.container_dir = "/.udocker/containers/CONTAINER/ROOT"
        rcex.opt["hostenv"] = []
        # status = rcex.run("CONTAINERID")
        # self.assertTrue(mock_run_env_cleanup_list.called)
        # self.assertTrue(mock_call.called)

    # def test_18_run_pty(self):
    #     """Test18 RuncEngine().run_pty()."""
    #     pass

    # def test_19_run_nopty(self):
    #     """Test19 RuncEngine().run_nopty()."""
    #     pass


if __name__ == '__main__':
    main()
