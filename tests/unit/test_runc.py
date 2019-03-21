#!/usr/bin/env python2
"""
udocker unit tests.
Unit tests for udocker, a wrapper to execute basic docker containers
without using docker.
Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at
http://www.apache.org/licenses/LICENSE-2.0
Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""

import os
import sys
import unittest
import mock

from udocker.engine.runc import RuncEngine
from udocker.config import Config

if sys.version_info[0] >= 3:
    BUILTINS = "builtins"
else:
    BUILTINS = "__builtin__"


def set_env():
    """Set environment variables."""
    if not os.getenv("HOME"):
        os.environ["HOME"] = os.getcwd()


class RuncEngineTestCase(unittest.TestCase):
    """Test RuncEngine() containers execution with runC."""

    @classmethod
    def setUpClass(cls):
        """Setup test."""
        set_env()

    def _init(self):
        """Configure variables."""
        Config = mock.MagicMock()
        Config.hostauth_list = ("/etc/passwd", "/etc/group")
        Config.cmd = "/bin/bash"
        Config.cpu_affinity_exec_tools = (["numactl", "-C", "%s", "--", ],
                                          ["taskset", "-c", "%s", ])
        Config.valid_host_env = "HOME"
        Config.return_value.username.return_value = "user"
        Config.return_value.userhome.return_value = "/"
        Config.return_value.oskernel.return_value = "4.8.13"
        Config.location = ""

    @mock.patch('udocker.engine.base.ExecutionEngineCommon')
    @mock.patch('udocker.container.localrepo.LocalRepository')
    def test_01_init(self, mock_local, mock_exeng):
        """Test RuncEngine()."""
        self._init()
        rcex = RuncEngine(mock_local)
        self.assertEqual(rcex.runc_exec, None)

    @mock.patch('udocker.config.Config')
    @mock.patch('udocker.engine.base.ExecutionEngineCommon')
    @mock.patch('udocker.utils.fileutil.FileUtil')
    @mock.patch('udocker.container.localrepo.LocalRepository')
    def test_03__select_runc(self, mock_local, mock_futil, mock_execmode,
                             mock_config):
        """Test RuncEngine()._select_runc()."""
        self._init()
        Config.return_value.arch.return_value = "arm"
        Config.return_value.oskernel_isgreater.return_value = False
        mock_futil.return_value.find_file_in_dir.return_value = "runc-arm"
        mock_execmode.return_value.get_mode.return_value = ""
        rcex = RuncEngine(mock_local)
        rcex.exec_mode = mock_execmode
        rcex._select_runc()
        self.assertEqual(rcex.runc_exec, "runc-arm")

    @mock.patch('json.load')
    @mock.patch('subprocess.call')
    @mock.patch('os.path.realpath')
    @mock.patch('udocker.utils.fileutil.FileUtil')
    @mock.patch('udocker.container.localrepo.LocalRepository')
    def test_04__load_spec(self, mock_local, mock_futil, mock_realpath,
                           mock_call, mock_jsonload):
        """Test RuncEngine()._load_spec()."""
        self._init()
        mock_futil.reset()
        mock_futil.return_value.size.return_value = 1
        rcex = RuncEngine(mock_local)
        rcex._load_spec(False)
        self.assertFalse(mock_futil.return_value.remove.called)
        #
        mock_futil.reset()
        mock_futil.return_value.size.return_value = 1
        rcex = RuncEngine(mock_local)
        rcex._load_spec(True)
        self.assertTrue(mock_futil.return_value.remove.called)
        #
        mock_futil.reset()
        mock_futil.return_value.size.return_value = -1
        mock_realpath.return_value = "/.udocker/containers/aaaaa"
        mock_call.return_value = True
        rcex = RuncEngine(mock_local)
        rcex.runc_exec = "runc"
        status = rcex._load_spec(False)
        self.assertFalse(status)
        #
        mock_futil.reset()
        mock_futil.return_value.size.return_value = -1
        mock_realpath.return_value = "/.udocker/containers/aaaaa"
        mock_call.return_value = False  # ok
        mock_jsonload.return_value = "JSON"
        rcex = RuncEngine(mock_local)
        rcex.runc_exec = "runc"
        with mock.patch(BUILTINS + '.open', mock.mock_open()):
            status = rcex._load_spec(False)
        self.assertEqual(status, "JSON")
        #
        mock_futil.reset()
        mock_futil.return_value.size.return_value = -1
        mock_realpath.return_value = "/.udocker/containers/aaaaa"
        mock_call.return_value = False  # ok
        mock_jsonload.return_value = "JSON"
        mock_jsonload.side_effect = OSError("reading json")
        rcex = RuncEngine(mock_local)
        rcex.runc_exec = "runc"
        with mock.patch(BUILTINS + '.open', mock.mock_open()):
            status = rcex._load_spec(False)
        self.assertEqual(status, None)

    @mock.patch('json.dump')
    @mock.patch('udocker.container.localrepo.LocalRepository')
    def test_05__save_spec(self, mock_local, mock_jsondump):
        """Test RuncEngine()._save_spec()."""
        self._init()
        rcex = RuncEngine(mock_local)
        rcex._container_specjson = "JSON"
        with mock.patch(BUILTINS + '.open', mock.mock_open()):
            status = rcex._save_spec()
        self.assertTrue(status)
        #
        mock_jsondump.side_effect = OSError("in open")
        rcex = RuncEngine(mock_local)
        rcex._container_specjson = "JSON"
        with mock.patch(BUILTINS + '.open', mock.mock_open()):
            status = rcex._save_spec()
        self.assertFalse(status)

    @mock.patch('os.getgid')
    @mock.patch('os.getuid')
    @mock.patch('platform.node')
    @mock.patch('os.path.realpath')
    @mock.patch('udocker.container.localrepo.LocalRepository')
    def test_06__set_spec(self, mock_local, mock_realpath, mock_node,
                          mock_getuid, mock_getgid):
        """Test RuncEngine()._set_spec()."""
        self._init()
        # rcex.opt["hostname"] has nodename
        mock_realpath.return_value = "/.udocker/containers/aaaaaa/ROOT"
        mock_node.return_value = "nodename.local"
        rcex = RuncEngine(mock_local)
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
        rcex = RuncEngine(mock_local)
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
        rcex = RuncEngine(mock_local)
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
        rcex = RuncEngine(mock_local)
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
        rcex = RuncEngine(mock_local)
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

    @mock.patch('udocker.msg.Msg')
    @mock.patch('udocker.container.localrepo.LocalRepository')
    def test_07__uid_check(self, mock_local, mock_msg):
        """Test RuncEngine()._uid_check()."""
        self._init()
        #
        mock_msg.reset_mock()
        rcex = RuncEngine(mock_local)
        rcex.opt = dict()
        rcex._uid_check()
        self.assertFalse(mock_msg.called)
        #
        mock_msg.reset_mock()
        rcex = RuncEngine(mock_local)
        rcex.opt = dict()
        rcex.opt["user"] = "root"
        rcex._uid_check()
        self.assertFalse(mock_msg.called)
        #
        mock_msg.reset_mock()
        rcex = RuncEngine(mock_local)
        rcex.opt = dict()
        rcex.opt["user"] = "user01"
        rcex._uid_check()
        self.assertTrue(mock_msg.called)

    @mock.patch('udocker.container.localrepo.LocalRepository')
    def test_08__create_mountpoint(self, mock_local):
        """Test RuncEngine()._create_mountpoint()."""
        self._init()
        rcex = RuncEngine(mock_local)
        status = rcex._create_mountpoint("HOSTPATH", "CONTPATH")
        self.assertTrue(status)

    @mock.patch('udocker.container.localrepo.LocalRepository')
    def test_09__add_mount_spec(self, mock_local):
        """Test RuncEngine()._add_mount_spec()."""
        self._init()
        # ro
        rcex = RuncEngine(mock_local)
        rcex._container_specjson = dict()
        rcex._container_specjson["mounts"] = []
        status = rcex._add_mount_spec("/HOSTDIR", "/CONTDIR")
        mount = rcex._container_specjson["mounts"][0]
        self.assertEqual(mount["destination"], "/CONTDIR")
        self.assertEqual(mount["source"], "/HOSTDIR")
        self.assertIn("ro", mount["options"])
        # rw
        rcex = RuncEngine(mock_local)
        rcex._container_specjson = dict()
        rcex._container_specjson["mounts"] = []
        status = rcex._add_mount_spec("/HOSTDIR", "/CONTDIR", True)
        mount = rcex._container_specjson["mounts"][0]
        self.assertEqual(mount["destination"], "/CONTDIR")
        self.assertEqual(mount["source"], "/HOSTDIR")
        self.assertIn("rw", mount["options"])

    @mock.patch('udocker.container.localrepo.LocalRepository')
    def test_10__del_mount_spec(self, mock_local):
        """Test RuncEngine()._del_mount_spec()."""
        self._init()
        #
        rcex = RuncEngine(mock_local)
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
        #
        rcex = RuncEngine(mock_local)
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
        #
        rcex = RuncEngine(mock_local)
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

    @mock.patch('udocker.msg.Msg')
    @mock.patch('os.path.isfile')
    @mock.patch('os.path.isdir')
    @mock.patch('udocker.engine.runc.RuncEngine._add_mount_spec')
    @mock.patch('udocker.utils.filebind.FileBind')
    @mock.patch('udocker.container.localrepo.LocalRepository')
    def test_11__add_volume_bindings(self, mock_local, mock_fbind,
                                     mock_add_mount_spec,
                                     mock_isdir, mock_isfile, mock_msg):
        """Test RuncEngine()._add_volume_bindings()."""
        self._init()
        #
        mock_fbind.start.return_value = ("/HOSTDIR", "/CONTDIR")
        mock_isdir.reset_mock()
        rcex = RuncEngine(mock_local)
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
        rcex = RuncEngine(mock_local)
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
        rcex = RuncEngine(mock_local)
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
        Config.sysdirs_list = ["/CONTDIR"]
        rcex = RuncEngine(mock_local)
        rcex._filebind = mock_fbind
        rcex.opt["vol"] = []
        rcex.opt["vol"].append("/HOSTDIR:/CONTDIR")
        status = rcex._add_volume_bindings()
        self.assertTrue(mock_isdir.called)
        self.assertTrue(mock_isfile.called)
        self.assertTrue(mock_fbind.add.called)
        # isfile = True
        mock_fbind.start.return_value = ("/HOSTDIR", "/CONTDIR")
        mock_isdir.reset_mock()
        mock_isfile.reset_mock()
        mock_add_mount_spec.reset_mock()
        mock_fbind.reset_mock()
        mock_isdir.return_value = False
        mock_isfile.return_value = True
        Config.sysdirs_list = [""]
        rcex = RuncEngine(mock_local)
        rcex._filebind = mock_fbind
        rcex.opt["vol"] = []
        rcex.opt["vol"].append("/HOSTDIR:/CONTDIR")
        status = rcex._add_volume_bindings()
        self.assertTrue(mock_isdir.called)
        self.assertTrue(mock_isfile.called)
        self.assertFalse(mock_fbind.add.called)

    @mock.patch('udocker.msg.Msg')
    @mock.patch('os.getenv')
    @mock.patch('udocker.container.localrepo.LocalRepository')
    def test_12__check_env(self, mock_local, mock_getenv, mock_msg):
        """Test RuncEngine()._check_env()."""
        self._init()
        #
        rcex = RuncEngine(mock_local)
        rcex.opt["env"] = []
        status = rcex._check_env()
        self.assertTrue(status)
        #
        mock_getenv.return_value = "aaaa"
        rcex = RuncEngine(mock_local)
        rcex.opt["env"] = ["", "HOME=/home/user01", "AAAA", ]
        status = rcex._check_env()
        self.assertTrue(status)
        self.assertNotIn("", rcex.opt["env"])
        self.assertIn("AAAA=aaaa", rcex.opt["env"])
        self.assertIn("HOME=/home/user01", rcex.opt["env"])
        #
        rcex = RuncEngine(mock_local)
        rcex.opt["env"] = ["3WRONG=/home/user01", ]
        status = rcex._check_env()
        self.assertFalse(status)
        #
        rcex = RuncEngine(mock_local)
        rcex.opt["env"] = ["WR ONG=/home/user01", ]
        status = rcex._check_env()
        self.assertFalse(status)

    @mock.patch('subprocess.call')
    @mock.patch('udocker.msg.Msg')
    @mock.patch('udocker.utils.filebind.FileBind')
    @mock.patch('udocker.helper.unique.Unique')
    @mock.patch('udocker.engine.runc.RuncEngine._run_invalid_options')
    @mock.patch('udocker.engine.runc.RuncEngine._del_mount_spec')
    @mock.patch('udocker.engine.runc.RuncEngine._run_banner')
    @mock.patch('udocker.engine.runc.RuncEngine._save_spec')
    @mock.patch('udocker.engine.runc.RuncEngine._add_volume_bindings')
    @mock.patch('udocker.engine.runc.RuncEngine._set_spec')
    @mock.patch('udocker.engine.runc.RuncEngine._check_env')
    @mock.patch('udocker.engine.runc.RuncEngine._run_env_set')
    @mock.patch('udocker.engine.runc.RuncEngine._uid_check')
    @mock.patch('udocker.engine.runc.RuncEngine._run_env_cleanup_list')
    @mock.patch('udocker.engine.runc.RuncEngine._load_spec')
    @mock.patch('udocker.engine.runc.RuncEngine._select_runc')
    @mock.patch('udocker.engine.runc.RuncEngine._run_init')
    @mock.patch('udocker.container.localrepo.LocalRepository')
    def test_16_run(self, mock_local, mock_run_init, mock_sel_runc,
                    mock_load_spec, mock_uid_check,
                    mock_run_env_cleanup_list, mock_env_set, mock_check_env,
                    mock_set_spec, mock_add_bindings, mock_save_spec,
                    mock_run_banner, mock_del_mount_spec, mock_inv_opt,
                    mock_unique, mock_fbind, mock_msg, mock_call):
        """Test RuncEngine().run()."""
        self._init()
        #
        mock_run_init.return_value = False
        rcex = RuncEngine(mock_local)
        status = rcex.run("CONTAINERID")
        self.assertEqual(status, 2)
        #
        mock_run_init.return_value = True
        mock_load_spec.return_value = False
        rcex = RuncEngine(mock_local)
        status = rcex.run("CONTAINERID")
        self.assertEqual(status, 4)
        #
        mock_run_init.return_value = True
        mock_load_spec.return_value = True
        mock_check_env.return_value = False
        mock_run_env_cleanup_list.reset_mock()
        rcex = RuncEngine(mock_local)
        rcex.opt["hostenv"] = []
        status = rcex.run("CONTAINERID")
        self.assertTrue(mock_run_env_cleanup_list.called)
        self.assertEqual(status, 5)
        #
        mock_run_init.return_value = True
        mock_load_spec.return_value = True
        mock_check_env.return_value = True
        mock_unique.return_value.uuid.return_value = "EXECUTION_ID"
        mock_run_env_cleanup_list.reset_mock()
        mock_call.reset_mock()
        rcex = RuncEngine(mock_local)
        rcex.runc_exec = "true"
        rcex.container_dir = "/.udocker/containers/CONTAINER/ROOT"
        rcex.opt["hostenv"] = []
        status = rcex.run("CONTAINERID")
        self.assertTrue(mock_run_env_cleanup_list.called)
        #self.assertTrue(mock_call.called)
