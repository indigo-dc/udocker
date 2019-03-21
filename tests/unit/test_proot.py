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
import unittest
import mock

from udocker.engine.proot import PRootEngine
from udocker.config import Config


def set_env():
    """Set environment variables."""
    if not os.getenv("HOME"):
        os.environ["HOME"] = os.getcwd()


class PRootEngineTestCase(unittest.TestCase):
    """Test PRootEngine() class for containers execution."""

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
        """Test PRootEngine()."""
        self._init()
        prex = PRootEngine(mock_local)
        self.assertFalse(prex.proot_noseccomp)
        self.assertEqual(prex._kernel, "4.8.13")
        self.assertEqual(prex.proot_exec, None)

    @mock.patch('udocker.config.Config')
    @mock.patch('udocker.engine.base.ExecutionMode')
    @mock.patch('udocker.utils.fileutil.FileUtil.find_file_in_dir')
    @mock.patch('udocker.container.localrepo.LocalRepository')
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

    @mock.patch('udocker.container.localrepo.LocalRepository')
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

    @mock.patch('udocker.container.localrepo.LocalRepository')
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

    @mock.patch('udocker.container.localrepo.LocalRepository')
    def test_06__create_mountpoint(self, mock_local):
        """Test PRootEngine()._create_mountpoint()."""
        self._init()
        prex = PRootEngine(mock_local)
        status = prex._create_mountpoint("", "")
        self.assertTrue(status)

    @mock.patch('subprocess.call')
    @mock.patch('udocker.engine.proot.PRootEngine._run_banner')
    @mock.patch('udocker.engine.proot.PRootEngine._run_env_cleanup_dict')
    @mock.patch('udocker.engine.proot.PRootEngine._set_uid_map')
    @mock.patch('udocker.engine.proot.PRootEngine._get_volume_bindings')
    @mock.patch('udocker.engine.proot.PRootEngine._set_cpu_affinity')
    @mock.patch('udocker.engine.proot.PRootEngine._check_env')
    @mock.patch('udocker.engine.proot.PRootEngine._run_env_set')
    @mock.patch('os.getenv')
    @mock.patch('udocker.engine.proot.PRootEngine._select_proot')
    @mock.patch('udocker.engine.base.ExecutionEngineCommon._run_init')
    @mock.patch('udocker.container.localrepo.LocalRepository')
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
