#!/usr/bin/env python
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

sys.path.append('.')

from udocker.engine.base import ExecutionEngineCommon
from udocker.config import Config
from udocker.helper.nixauth import NixAuthentication


def set_env():
    """Set environment variables."""
    if not os.getenv("HOME"):
        os.environ["HOME"] = os.getcwd()


class ExecutionEngineCommonTestCase(unittest.TestCase):
    """Test ExecutionEngineCommon().

    Parent class for containers execution.
    """

    @classmethod
    def setUpClass(cls):
        """Setup test."""
        set_env()

    def _init(self):
        """Configure variables."""
        Config = type('test', (object,), {})()
        Config.hostauth_list = ("/etc/passwd", "/etc/group")
        Config.cmd = "/bin/bash"
        Config.cpu_affinity_exec_tools = (["numactl", "-C", "%s", "--", ],
                                          ["taskset", "-c", "%s", ])
        Config.location = ""
        Config.uid = 1000
        Config.sysdirs_list = ["/", ]
        Config.root_path = "/usr/sbin:/sbin:/usr/bin:/bin"
        Config.user_path = "/usr/bin:/bin:/usr/local/bin"
        self.xmode = "P1"

    @mock.patch('udocker.container.localrepo.LocalRepository')
    def test_01_init(self, mock_local):
        """Test ExecutionEngineCommon() constructor"""
        self._init()
        ex_eng = ExecutionEngineCommon(mock_local, self.xmode)
        self.assertEqual(ex_eng.container_id, "")
        self.assertEqual(ex_eng.container_root, "")
        self.assertEqual(ex_eng.container_names, [])
        self.assertEqual(ex_eng.opt["nometa"], False)
        self.assertEqual(ex_eng.opt["nosysdirs"], False)
        self.assertEqual(ex_eng.opt["dri"], False)
        self.assertEqual(ex_eng.opt["bindhome"], False)
        self.assertEqual(ex_eng.opt["hostenv"], False)
        self.assertEqual(ex_eng.opt["hostauth"], False)
        self.assertEqual(ex_eng.opt["novol"], [])
        self.assertEqual(ex_eng.opt["env"], [])
        self.assertEqual(ex_eng.opt["vol"], [])
        self.assertEqual(ex_eng.opt["cpuset"], "")
        self.assertEqual(ex_eng.opt["user"], "")
        self.assertEqual(ex_eng.opt["cwd"], "")
        self.assertEqual(ex_eng.opt["entryp"], "")
        self.assertEqual(ex_eng.opt["cmd"], Config.cmd)
        self.assertEqual(ex_eng.opt["hostname"], "")
        self.assertEqual(ex_eng.opt["domain"], "")
        self.assertEqual(ex_eng.opt["volfrom"], [])

    @mock.patch('udocker.msg.Msg')
    @mock.patch('udocker.container.localrepo.LocalRepository')
    def test_02__check_exposed_ports(self, mock_local, mock_msg):
        """Test ExecutionEngineCommon()._check_exposed_ports()."""
        self._init()
        mock_msg.level = 0
        ex_eng = ExecutionEngineCommon(mock_local, self.xmode)
        ex_eng.opt["portsexp"] = ("1024", "2048/tcp", "23000/udp")
        status = ex_eng._check_exposed_ports()
        self.assertTrue(status)
        #
        ex_eng.opt["portsexp"] = ("1023", "2048/tcp", "23000/udp")
        status = ex_eng._check_exposed_ports()
        self.assertFalse(status)
        #
        ex_eng.opt["portsexp"] = ("1024", "80/tcp", "23000/udp")
        status = ex_eng._check_exposed_ports()
        self.assertFalse(status)
        #
        ex_eng.opt["portsexp"] = ("1024", "2048/tcp", "23/udp")
        status = ex_eng._check_exposed_ports()
        self.assertFalse(status)

    @mock.patch('udocker.utils.fileutil.FileUtil.find_exec')
    @mock.patch('udocker.container.localrepo.LocalRepository')
    def test_03__set_cpu_affinity(self, mock_local, mock_findexec):
        """Test ExecutionEngineCommon()._set_cpu_affinity()."""
        self._init()
        ex_eng = ExecutionEngineCommon(mock_local, self.xmode)
        mock_findexec.return_value = ""
        status = ex_eng._set_cpu_affinity()
        self.assertEqual(status, [])
        #
        mock_findexec.return_value = "taskset"
        status = ex_eng._set_cpu_affinity()
        self.assertEqual(status, [])
        #
        mock_findexec.return_value = "numactl"
        ex_eng.opt["cpuset"] = "1-2"
        status = ex_eng._set_cpu_affinity()
        self.assertEqual(status, ["numactl", "-C", "1-2", "--"])

    @mock.patch('udocker.engine.base.os.path.isdir')
    @mock.patch('udocker.container.localrepo.LocalRepository')
    def test_04__cont2host(self, mock_local, mock_isdir):
        """Test ExecutionEngine()._cont2host()."""
        self._init()
        mock_isdir.return_value = True
        #
        ex_eng = ExecutionEngineCommon(mock_local, self.xmode)
        ex_eng.opt["vol"] = ("/opt/xxx:/mnt",)
        status = ex_eng._cont2host("/mnt")
        self.assertEqual(status, "/opt/xxx")
        #
        ex_eng.opt["vol"] = ("/var/xxx:/mnt",)
        status = ex_eng._cont2host("/opt")
        self.assertTrue(status.endswith("/opt"))
        # change dir to volume (regression of #51)
        ex_eng.opt["vol"] = ("/var/xxx",)
        status = ex_eng._cont2host("/var/xxx/tt")
        self.assertEqual(status, "/var/xxx/tt")
        # change dir to volume (regression of #51)
        ex_eng.opt["vol"] = ("/var/xxx:/mnt",)
        status = ex_eng._cont2host("/mnt/tt")
        self.assertEqual(status, "/var/xxx/tt")

    @mock.patch('udocker.msg.Msg')
    @mock.patch('udocker.engine.base.os.path.isdir')
    @mock.patch('udocker.engine.base.os.path.exists')
    @mock.patch('udocker.engine.base.ExecutionEngineCommon._cont2host')
    @mock.patch('udocker.engine.base.ExecutionEngineCommon._getenv')
    @mock.patch('udocker.container.localrepo.LocalRepository')
    def test_05__check_paths(self, mock_local, mock_getenv, mock_isinvol,
                             mock_exists, mock_isdir, mock_msg):
        """Test ExecutionEngineCommon()._check_paths()."""
        self._init()
        mock_msg.level = 0
        ex_eng = ExecutionEngineCommon(mock_local, self.xmode)
        mock_getenv.return_value = ""
        mock_isinvol.return_value = False
        mock_exists.return_value = False
        mock_isdir.return_value = False
        ex_eng.opt["uid"] = "0"
        ex_eng.opt["cwd"] = ""
        ex_eng.opt["home"] = "/home/user"
        ex_eng.container_root = "/containers/123/ROOT"
        status = ex_eng._check_paths()
        self.assertFalse(status)
        self.assertEqual(ex_eng.opt["env"][-1],
                         "PATH=/usr/sbin:/sbin:/usr/bin:/bin")
        self.assertEqual(ex_eng.opt["cwd"], ex_eng.opt["home"])
        #
        ex_eng.opt["uid"] = "1000"
        status = ex_eng._check_paths()
        self.assertFalse(status)
        self.assertEqual(ex_eng.opt["env"][-1],
                         "PATH=/usr/bin:/bin:/usr/local/bin")
        self.assertEqual(ex_eng.opt["cwd"], ex_eng.opt["home"])
        #
        mock_exists.return_value = True
        mock_isdir.return_value = True
        status = ex_eng._check_paths()
        self.assertTrue(status)

    @mock.patch('udocker.msg.Msg')
    @mock.patch('udocker.engine.base.os.access')
    @mock.patch('udocker.engine.base.os.readlink')
    @mock.patch('udocker.engine.base.os.path.isfile')
    @mock.patch('udocker.engine.base.ExecutionEngineCommon._getenv')
    @mock.patch('udocker.container.localrepo.LocalRepository')
    def test_06__check_executable(self, mock_local, mock_getenv, mock_isfile,
                                  mock_readlink, mock_access, mock_msg):
        """Test ExecutionEngineCommon()._check_executable()."""
        self._init()
        mock_msg.level = 0
        ex_eng = ExecutionEngineCommon(mock_local, self.xmode)
        mock_getenv.return_value = ""
        ex_eng.opt["entryp"] = "/bin/shell -x -v"
        mock_isfile.return_value = False
        ex_eng.container_root = "/containers/123/ROOT"
        status = ex_eng._check_executable()
        self.assertFalse(status)
        #
        mock_isfile.return_value = True
        mock_access.return_value = True
        status = ex_eng._check_executable()
        self.assertTrue(status)
        #
        ex_eng.opt["entryp"] = ["/bin/shell", "-x", "-v"]
        ex_eng.opt["cmd"] = ""
        status = ex_eng._check_executable()
        self.assertEqual(ex_eng.opt["cmd"], ex_eng.opt["entryp"])
        #
        ex_eng.opt["entryp"] = ["/bin/shell", ]
        ex_eng.opt["cmd"] = ["-x", "-v"]
        status = ex_eng._check_executable()
        self.assertEqual(ex_eng.opt["cmd"], ["/bin/shell", "-x", "-v"])

    @mock.patch('udocker.container.structure.ContainerStructure')
    @mock.patch('udocker.engine.base.ExecutionEngineCommon._check_exposed_ports')
    @mock.patch('udocker.engine.base.ExecutionEngineCommon._getenv')
    @mock.patch('udocker.container.localrepo.LocalRepository')
    def test_07__run_load_metadata(self, mock_local, mock_getenv,
                                   mock_chkports, mock_cstruct):
        """Test ExecutionEngineCommon()._run_load_metadata()."""
        self._init()
        ex_eng = ExecutionEngineCommon(mock_local, self.xmode)
        mock_getenv.return_value = ""
        Config.location = "/tmp/container"
        status = ex_eng._run_load_metadata("123")
        self.assertEqual(status, ("", []))
        #
        Config.location = ""
        mock_cstruct.return_value.get_container_attr.return_value = ("", [])
        status = ex_eng._run_load_metadata("123")
        self.assertEqual(status, (None, None))
        #
        Config.location = ""
        mock_cstruct.return_value.get_container_attr.return_value = ("/x", [])
        ex_eng.opt["nometa"] = True
        status = ex_eng._run_load_metadata("123")
        self.assertEqual(status, ("/x", []))
        #
        Config.location = ""
        mock_cstruct.return_value.get_container_attr.return_value = ("/x", [])
        ex_eng.opt["nometa"] = False
        status = ex_eng._run_load_metadata("123")
        self.assertEqual(status, ("/x", []))

    @mock.patch('udocker.container.localrepo.LocalRepository')
    def test_08__getenv(self, mock_local):
        """Test ExecutionEngineCommon()._getenv()."""
        self._init()
        ex_eng = ExecutionEngineCommon(mock_local, self.xmode)
        ex_eng.opt["env"] = ["HOME=/home/user", "PATH=/bin:/usr/bin"]
        status = ex_eng._getenv("")
        self.assertEqual(status, None)
        #
        status = ex_eng._getenv("XXX")
        self.assertEqual(status, None)
        #
        status = ex_eng._getenv("HOME")
        self.assertEqual(status, "/home/user")
        #
        status = ex_eng._getenv("PATH")
        self.assertEqual(status, "/bin:/usr/bin")

    @mock.patch('udocker.msg.Msg')
    @mock.patch('udocker.container.localrepo.LocalRepository')
    def test_09__uid_gid_from_str(self, mock_local, mock_msg):
        """Test ExecutionEngineCommon()._uid_gid_from_str()."""
        self._init()
        mock_msg.level = 0
        ex_eng = ExecutionEngineCommon(mock_local, self.xmode)
        status = ex_eng._uid_gid_from_str("")
        self.assertEqual(status, (None, None))
        #
        status = ex_eng._uid_gid_from_str("0:0")
        self.assertEqual(status, ('0', '0'))
        #
        status = ex_eng._uid_gid_from_str("100:100")
        self.assertEqual(status, ('100', '100'))

    @mock.patch('udocker.msg.Msg')
    @mock.patch('udocker.helper.nixauth.NixAuthentication')
    @mock.patch('udocker.container.localrepo.LocalRepository')
    @mock.patch('udocker.engine.base.ExecutionEngineCommon._create_user')
    @mock.patch('udocker.engine.base.ExecutionEngineCommon._uid_gid_from_str')
    def test_10__setup_container_user(self, mock_ugfs, mock_cruser,
                                      mock_local, mock_nix, mock_msg):
        """Test ExecutionEngineCommon()._setup_container_user()."""
        self._init()
        mock_msg.level = 0
        ex_eng = ExecutionEngineCommon(mock_local, self.xmode)
        mock_ugfs.return_value = (None, None)
        status = ex_eng._setup_container_user("0:0")
        self.assertFalse(status)
        self.assertTrue(mock_ugfs.called_once_with("root"))
        #
        ex_eng = ExecutionEngineCommon(mock_local, self.xmode)
        ex_eng.opt["vol"] = ""
        ex_eng.opt["hostauth"] = False
        mock_nix.return_value.get_user.return_value = ("", "", "",
                                                       "", "", "")
        mock_ugfs.return_value = ("0", "0")
        status = ex_eng._setup_container_user("0:0")
        self.assertTrue(status)
        self.assertTrue(mock_cruser.called)
        #
        ex_eng = ExecutionEngineCommon(mock_local, self.xmode)
        ex_eng.opt["vol"] = ""
        ex_eng.opt["hostauth"] = False
        mock_nix.return_value.get_user.return_value = ("root", 0, 0,
                                                       "", "", "")
        mock_ugfs.return_value = ("0", "0")
        status = ex_eng._setup_container_user("0:0")
        self.assertTrue(status)
        self.assertTrue(mock_cruser.called)
        #
        ex_eng = ExecutionEngineCommon(mock_local, self.xmode)
        ex_eng.opt["vol"] = ""
        ex_eng.opt["hostauth"] = True
        mock_nix.return_value.get_user.return_value = ("", "", "",
                                                       "", "", "")
        mock_ugfs.return_value = ("0", "0")
        status = ex_eng._setup_container_user("0:0")
        self.assertFalse(status)
        #
        ex_eng = ExecutionEngineCommon(mock_local, self.xmode)
        ex_eng.opt["vol"] = ""
        ex_eng.opt["hostauth"] = True
        mock_nix.return_value.get_user.return_value = ("root", 0, 0,
                                                       "", "", "")
        mock_ugfs.return_value = ("0", "0")
        status = ex_eng._setup_container_user("0:0")
        self.assertTrue(status)
        self.assertTrue(mock_cruser.called)
        #
        ex_eng = ExecutionEngineCommon(mock_local, self.xmode)
        ex_eng.opt["vol"] = ""
        ex_eng.opt["hostauth"] = False
        mock_nix.return_value.get_user.return_value = ("", "", "",
                                                       "", "", "")
        status = ex_eng._setup_container_user("")
        self.assertTrue(status)
        self.assertTrue(mock_cruser.called)
        #
        ex_eng = ExecutionEngineCommon(mock_local, self.xmode)
        ex_eng.opt["vol"] = ""
        ex_eng.opt["hostauth"] = False
        mock_nix.return_value.get_user.return_value = ("root", 0, 0,
                                                       "", "", "")
        status = ex_eng._setup_container_user("")
        self.assertTrue(status)
        self.assertTrue(mock_cruser.called)
        #
        ex_eng = ExecutionEngineCommon(mock_local, self.xmode)
        ex_eng.opt["vol"] = ""
        ex_eng.opt["hostauth"] = True
        mock_nix.return_value.get_user.return_value = ("", "", "",
                                                       "", "", "")
        status = ex_eng._setup_container_user("")
        self.assertFalse(status)
        #
        ex_eng = ExecutionEngineCommon(mock_local, self.xmode)
        ex_eng.opt["vol"] = ""
        ex_eng.opt["hostauth"] = False
        mock_nix.return_value.get_user.return_value = ("", 100, 0,
                                                       "", "", "")
        mock_ugfs.return_value = ("0", "0")
        status = ex_eng._setup_container_user("0:0")
        self.assertTrue(status)
        self.assertTrue(mock_cruser.called)
        self.assertEqual(ex_eng.opt["user"], "")

    @mock.patch('udocker.engine.base.os.getgroups')
    @mock.patch('udocker.utils.fileutil.FileUtil')
    @mock.patch('udocker.msg.Msg')
    @mock.patch('udocker.helper.nixauth.NixAuthentication')
    @mock.patch('udocker.container.localrepo.LocalRepository')
    def test_11__create_user(self, mock_local, mock_nix, mock_msg,
                             mock_futil, mock_groups):
        """Test ExecutionEngineCommon()._create_user()."""
        self._init()
        mock_msg.level = 0
        container_auth = NixAuthentication("", "")
        container_auth.passwd_file = ""
        container_auth.group_file = ""
        host_auth = NixAuthentication("", "")
        #
        Config.uid = 1000
        Config.gid = 1000
        mock_nix.return_value.add_user.return_value = False
        ex_eng = ExecutionEngineCommon(mock_local, self.xmode)
        ex_eng.opt["uid"] = ""
        ex_eng.opt["gid"] = ""
        ex_eng.opt["user"] = ""
        ex_eng.opt["home"] = ""
        ex_eng.opt["shell"] = ""
        ex_eng.opt["gecos"] = ""
        status = ex_eng._create_user(container_auth, host_auth)
        self.assertFalse(status)
        self.assertEqual(ex_eng.opt["uid"], "1000")
        self.assertEqual(ex_eng.opt["gid"], "1000")
        self.assertEqual(ex_eng.opt["user"], "udoc1000")
        self.assertEqual(ex_eng.opt["home"], "/home/udoc1000")
        self.assertEqual(ex_eng.opt["shell"], "/bin/sh")
        self.assertEqual(ex_eng.opt["gecos"], "*UDOCKER*")
        #
        mock_nix.return_value.add_user.return_value = False
        ex_eng = ExecutionEngineCommon(mock_local, self.xmode)
        ex_eng.opt["uid"] = "60000"
        ex_eng.opt["gid"] = "60000"
        ex_eng.opt["user"] = "someuser"
        ex_eng.opt["home"] = ""
        ex_eng.opt["shell"] = "/bin/false"
        ex_eng.opt["gecos"] = "*XXX*"
        status = ex_eng._create_user(container_auth, host_auth)
        self.assertFalse(status)
        self.assertEqual(ex_eng.opt["uid"], "60000")
        self.assertEqual(ex_eng.opt["gid"], "60000")
        self.assertEqual(ex_eng.opt["user"], "someuser")
        self.assertEqual(ex_eng.opt["home"], "/home/someuser")
        self.assertEqual(ex_eng.opt["shell"], "/bin/false")
        self.assertEqual(ex_eng.opt["gecos"], "*XXX*")
        #
        mock_nix.return_value.add_user.return_value = False
        ex_eng = ExecutionEngineCommon(mock_local, self.xmode)
        ex_eng.opt["uid"] = "60000"
        ex_eng.opt["gid"] = "60000"
        ex_eng.opt["user"] = "someuser"
        ex_eng.opt["home"] = "/home/batata"
        ex_eng.opt["shell"] = "/bin/false"
        ex_eng.opt["gecos"] = "*XXX*"
        status = ex_eng._create_user(container_auth, host_auth)
        self.assertFalse(status)
        self.assertEqual(ex_eng.opt["uid"], "60000")
        self.assertEqual(ex_eng.opt["gid"], "60000")
        self.assertEqual(ex_eng.opt["user"], "someuser")
        self.assertEqual(ex_eng.opt["home"], "/home/batata")
        self.assertEqual(ex_eng.opt["shell"], "/bin/false")
        self.assertEqual(ex_eng.opt["gecos"], "*XXX*")
        #
        mock_nix.return_value.add_user.return_value = True
        mock_nix.return_value.get_group.return_value = ("", "", "")
        mock_nix.return_value.add_group.return_value = True
        mock_groups.return_value = ()
        ex_eng = ExecutionEngineCommon(mock_local, self.xmode)
        ex_eng.opt["uid"] = "60000"
        ex_eng.opt["gid"] = "60000"
        ex_eng.opt["user"] = "someuser"
        ex_eng.opt["home"] = "/home/batata"
        ex_eng.opt["shell"] = "/bin/false"
        ex_eng.opt["gecos"] = "*XXX*"
        status = ex_eng._create_user(container_auth, host_auth)
        self.assertTrue(status)
        self.assertEqual(ex_eng.opt["uid"], "60000")
        self.assertEqual(ex_eng.opt["gid"], "60000")
        self.assertEqual(ex_eng.opt["user"], "someuser")
        self.assertEqual(ex_eng.opt["home"], "/home/batata")
        self.assertEqual(ex_eng.opt["shell"], "/bin/false")
        self.assertEqual(ex_eng.opt["gecos"], "*XXX*")
        self.assertEqual(ex_eng.opt["hostauth"], True)
        mgroup = mock_nix.return_value.get_group
        self.assertTrue(mgroup.called_once_with("60000"))
        #
        mock_nix.return_value.add_user.return_value = True
        mock_nix.return_value.get_group.return_value = ("", "", "")
        mock_nix.return_value.add_group.return_value = True
        mock_groups.return_value = (80000,)
        ex_eng = ExecutionEngineCommon(mock_local, self.xmode)
        ex_eng.opt["uid"] = "60000"
        ex_eng.opt["gid"] = "60000"
        ex_eng.opt["user"] = "someuser"
        ex_eng.opt["home"] = "/home/batata"
        ex_eng.opt["shell"] = "/bin/false"
        ex_eng.opt["gecos"] = "*XXX*"
        status = ex_eng._create_user(container_auth, host_auth)
        self.assertTrue(status)
        self.assertEqual(ex_eng.opt["uid"], "60000")
        self.assertEqual(ex_eng.opt["gid"], "60000")
        self.assertEqual(ex_eng.opt["user"], "someuser")
        self.assertEqual(ex_eng.opt["home"], "/home/batata")
        self.assertEqual(ex_eng.opt["shell"], "/bin/false")
        self.assertEqual(ex_eng.opt["gecos"], "*XXX*")
        self.assertEqual(ex_eng.opt["hostauth"], True)
        ggroup = mock_nix.return_value.get_group
        self.assertTrue(ggroup.called_once_with("60000"))
        agroup = mock_nix.return_value.add_group
        self.assertTrue(agroup.called_once_with("G80000", "80000"))

    @mock.patch('udocker.msg.Msg')
    @mock.patch('udocker.engine.base.os.path.basename')
    @mock.patch('udocker.container.localrepo.LocalRepository')
    def test_12__run_banner(self, mock_local, mock_base, mock_msg):
        """Test ExecutionEngineCommon()._run_banner()."""
        self._init()
        mock_msg.level = 0
        ex_eng = ExecutionEngineCommon(mock_local, self.xmode)
        ex_eng._run_banner("/bin/bash")
        ex_eng.container_id = "CONTAINERID"
        self.assertTrue(mock_base.called_once_with("/bin/bash"))

    @mock.patch('udocker.config.Config')
    @mock.patch('udocker.engine.base.os.environ')
    @mock.patch('udocker.container.localrepo.LocalRepository')
    def test_14__env_cleanup_dict(self, mock_local, mock_osenv, mock_config):
        """Test ExecutionEngineCommon()._env_cleanup()."""
        # self._init()
        Config = mock_config
        Config.valid_host_env = ("HOME",)
        mock_osenv.return_value = {'HOME': '/', 'USERNAME': 'user', }
        ex_eng = ExecutionEngineCommon(mock_local, self.xmode)
        ex_eng._run_env_cleanup_dict()
        self.assertEqual(mock_osenv, {'HOME': '/', })

    @mock.patch('udocker.config.Config')
    @mock.patch('udocker.container.localrepo.LocalRepository')
    def test_15__run_env_set(self, mock_local, mock_config):
        """Test ExecutionEngineCommon()._run_env_set()."""
        # self._init()
        ex_eng = ExecutionEngineCommon(mock_local, self.xmode)
        ex_eng.opt["home"] = "/"
        ex_eng.opt["user"] = "user"
        ex_eng.opt["uid"] = "1000"
        ex_eng.container_root = "/croot"
        ex_eng.container_id = "2717add4-e6f6-397c-9019-74fa67be439f"
        ex_eng.container_names = ['cna[]me', ]
        ex_eng.exec_mode = mock.MagicMock()
        ex_eng.exec_mode.get_mode.return_value = "P1"
        ex_eng._run_env_set()
        self.assertTrue("HOME=" + ex_eng.opt["home"] in ex_eng.opt["env"])
        self.assertTrue("USER=" + ex_eng.opt["user"] in ex_eng.opt["env"])
        self.assertTrue("LOGNAME=" + ex_eng.opt["user"] in ex_eng.opt["env"])
        self.assertTrue("USERNAME=" + ex_eng.opt["user"] in ex_eng.opt["env"])
        self.assertTrue("SHLVL=0" in ex_eng.opt["env"])
        self.assertTrue("container_root=/croot" in ex_eng.opt["env"])

    @mock.patch('udocker.engine.execmode.ExecutionMode')
    @mock.patch('udocker.engine.base.ExecutionEngineCommon._set_volume_bindings')
    @mock.patch('udocker.engine.base.ExecutionEngineCommon._check_executable')
    @mock.patch('udocker.engine.base.ExecutionEngineCommon._check_paths')
    @mock.patch('udocker.engine.base.ExecutionEngineCommon._setup_container_user')
    @mock.patch('udocker.engine.base.ExecutionEngineCommon._run_load_metadata')
    @mock.patch('udocker.container.localrepo.LocalRepository')
    def test_16__run_init(self, mock_local, mock_loadmeta, mock_setupuser,
                          mock_chkpaths, mock_chkexec, mock_chkvol,
                          mock_execmode):
        """Test ExecutionEngineCommon()._run_init()."""
        self._init()
        mock_local.get_container_name.return_value = "cname"
        mock_loadmeta.return_value = ("/container_dir", "dummy",)
        mock_setupuser.return_value = True
        mock_chkpaths.return_value = True
        mock_chkexec.return_value = True
        ex_eng = ExecutionEngineCommon(mock_local, self.xmode)
        status = ex_eng._run_init("2717add4-e6f6-397c-9019-74fa67be439f")
        self.assertTrue(status)
        self.assertEqual(ex_eng.container_root, "/container_dir/ROOT")
        #
        mock_setupuser.return_value = False
        mock_chkpaths.return_value = True
        mock_chkexec.return_value = True
        status = ex_eng._run_init("2717add4-e6f6-397c-9019-74fa67be439f")
        self.assertFalse(status)
        #
        mock_setupuser.return_value = True
        mock_chkpaths.return_value = False
        mock_chkexec.return_value = True
        status = ex_eng._run_init("2717add4-e6f6-397c-9019-74fa67be439f")
        self.assertFalse(status)
        #
        mock_setupuser.return_value = True
        mock_chkpaths.return_value = True
        mock_chkexec.return_value = False
        status = ex_eng._run_init("2717add4-e6f6-397c-9019-74fa67be439f")
        self.assertFalse(status)

    @mock.patch('udocker.helper.nixauth.NixAuthentication')
    @mock.patch('udocker.container.localrepo.LocalRepository')
    def test_17__get_bindhome(self, mock_local, mock_nixauth):
        """Test ExecutionEngine()._get_bindhome()."""
        self._init()
        #
        mock_nixauth.return_value.get_home.return_value = ""
        prex = ExecutionEngineCommon(mock_local, self.xmode)
        prex.opt["bindhome"] = False
        status = prex._get_bindhome()
        self.assertEqual(status, "")
        #
        mock_nixauth.return_value.get_home.return_value = "/home/user"
        prex = ExecutionEngineCommon(mock_local, self.xmode)
        prex.opt["bindhome"] = True
        status = prex._get_bindhome()
        self.assertEqual(status, "/home/user")
        #
        mock_nixauth.return_value.get_home.return_value = ""
        prex = ExecutionEngineCommon(mock_local, self.xmode)
        prex.opt["bindhome"] = True
        status = prex._get_bindhome()
        self.assertEqual(status, "")

    @mock.patch('udocker.engine.base.os.path.exists')
    @mock.patch('udocker.container.localrepo.LocalRepository')
    def test_18__create_mountpoint(self, mock_local, mock_exists):
        """Test ExecutionEngine()._create_mountpoint()."""
        self._init()
        mock_exists.return_value = False
        exc = ExecutionEngineCommon(mock_local, self.xmode)
        status = exc._create_mountpoint("", "")
        self.assertFalse(status)

        mock_exists.return_value = True
        exc = ExecutionEngineCommon(mock_local, self.xmode)
        status = exc._create_mountpoint("", "")
        self.assertTrue(status)

    @mock.patch('udocker.engine.base.os.path.exists')
    @mock.patch('udocker.container.localrepo.LocalRepository')
    def test_19__check_volumes(self, mock_local, mock_exists):
        """."""
        self._init()

        exc = ExecutionEngineCommon(mock_local, self.xmode)
        exc.opt["vol"] = ()
        status = exc._check_volumes()
        self.assertTrue(status)

        mock_exists.return_value = False
        exc = ExecutionEngineCommon(mock_local, self.xmode)
        status = exc._check_volumes()
        self.assertTrue(status)

    @mock.patch('udocker.container.localrepo.LocalRepository')
    def test_19__is_volume(self, mock_local):
        """."""
        self._init()

        exc = ExecutionEngineCommon(mock_local, self.xmode)
        exc.opt["vol"] = ["/tmp"]
        status = exc._is_volume("/tmp")
        self.assertTrue(status)

        exc = ExecutionEngineCommon(mock_local, self.xmode)
        exc.opt["vol"] = [""]
        status = exc._is_volume("/tmp")
        self.assertFalse(status)


if __name__ == '__main__':
    unittest.main()
