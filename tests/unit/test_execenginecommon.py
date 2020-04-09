#!/usr/bin/env python
"""
udocker unit tests: ExecutionEngineCommon
"""

import sys
from udocker.engine.base import ExecutionEngineCommon
from udocker.config import Config
from udocker.container.localrepo import LocalRepository
from unittest import TestCase, main
try:
    from unittest.mock import Mock, patch, MagicMock, mock_open
except ImportError:
    from mock import Mock, patch, MagicMock, mock_open

sys.path.append('.')


class ExecutionEngineCommonTestCase(TestCase):
    """Test ExecutionEngineCommon().
    Parent class for containers execution.
    """

    def setUp(self):
        Config().getconf()
        Config().conf['hostauth_list'] = ("/etc/passwd", "/etc/group")
        Config().conf['cmd'] = "/bin/bash"
        Config().conf['cpu_affinity_exec_tools'] = (["numactl", "-C", "%s", "--", ],
                                                    ["taskset", "-c", "%s", ])
        Config().conf['location'] = ""
        Config().conf['uid'] = 1000
        Config().conf['sysdirs_list'] = ["/", ]
        Config().conf['root_path'] = "/usr/sbin:/sbin:/usr/bin:/bin"
        Config().conf['user_path'] = "/usr/bin:/bin:/usr/local/bin"
        self.xmode = "P1"
        self.local = LocalRepository()

    def tearDown(self):
        pass

    def test_01_init(self):
        """Test ExecutionEngineCommon() constructor"""
        ex_eng = ExecutionEngineCommon(self.local, self.xmode)
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
        self.assertEqual(ex_eng.opt["vol"], [])
        self.assertEqual(ex_eng.opt["cpuset"], "")
        self.assertEqual(ex_eng.opt["user"], "")
        self.assertEqual(ex_eng.opt["cwd"], "")
        self.assertEqual(ex_eng.opt["entryp"], "")
        # self.assertEqual(ex_eng.opt["cmd"], Config().conf['cmd'])
        self.assertEqual(ex_eng.opt["hostname"], "")
        self.assertEqual(ex_eng.opt["domain"], "")
        self.assertEqual(ex_eng.opt["volfrom"], [])

    # def test_03__get_portsmap(self):
    #     """Test ExecutionEngineCommon()._get_portsmap()."""
    #     pass

    @patch('udocker.engine.base.Msg')
    def test_04__check_exposed_ports(self, mock_msg):
        """Test ExecutionEngineCommon()._check_exposed_ports()."""
        ex_eng = ExecutionEngineCommon(self.local, self.xmode)
        ex_eng.opt["portsexp"] = ("1024", "2048/tcp", "23000/udp")
        status = ex_eng._check_exposed_ports()
        self.assertTrue(status)

        ex_eng = ExecutionEngineCommon(self.local, self.xmode)
        ex_eng.opt["portsexp"] = ("1023", "2048/tcp", "23000/udp")
        status = ex_eng._check_exposed_ports()
        self.assertFalse(status)

        ex_eng = ExecutionEngineCommon(self.local, self.xmode)
        ex_eng.opt["portsexp"] = ("1024", "80/tcp", "23000/udp")
        status = ex_eng._check_exposed_ports()
        self.assertFalse(status)

        ex_eng = ExecutionEngineCommon(self.local, self.xmode)
        ex_eng.opt["portsexp"] = ("1024", "2048/tcp", "23/udp")
        status = ex_eng._check_exposed_ports()
        self.assertFalse(status)

    @patch('udocker.engine.base.FileUtil.find_exec')
    def test_05__set_cpu_affinity(self, mock_findexec):
        """Test ExecutionEngineCommon()._set_cpu_affinity()."""
        mock_findexec.return_value = ""
        ex_eng = ExecutionEngineCommon(self.local, self.xmode)
        status = ex_eng._set_cpu_affinity()
        self.assertEqual(status, [])

        mock_findexec.return_value = "taskset"
        ex_eng = ExecutionEngineCommon(self.local, self.xmode)
        status = ex_eng._set_cpu_affinity()
        self.assertEqual(status, [])

        mock_findexec.return_value = "numactl"
        ex_eng = ExecutionEngineCommon(self.local, self.xmode)
        ex_eng.opt["cpuset"] = "1-2"
        status = ex_eng._set_cpu_affinity()
        self.assertEqual(status, ["numactl", "-C", "1-2", "--"])

    # def test_06__cleanpath(self):
    #     """Test ExecutionEngineCommon()._cleanpath()."""
    #     pass

    # def test_07__vol_split(self):
    #     """Test ExecutionEngineCommon()._vol_split()."""
    #     pass

    # @patch('udocker.engine.base.os.path.exists')
    # def test_09__create_mountpoint(self, mock_exists):
    #     """Test ExecutionEngine()._create_mountpoint()."""
    #     mock_exists.return_value = False
    #     ex_eng = ExecutionEngineCommon(self.local, self.xmode)
    #     status = ex_eng._create_mountpoint("", "")
    #     self.assertFalse(status)

    #     mock_exists.return_value = True
    #     ex_eng = ExecutionEngineCommon(self.local, self.xmode)
    #     status = ex_eng._create_mountpoint("", "")
    #     self.assertTrue(status)

    @patch('udocker.engine.base.os.path.exists')
    def test_10__check_volumes(self, mock_exists):
        """Test ExecutionEngine()._check_volumes()."""
        ex_eng = ExecutionEngineCommon(self.local, self.xmode)
        ex_eng.opt["vol"] = ()
        status = ex_eng._check_volumes()
        self.assertTrue(status)

        mock_exists.return_value = False
        ex_eng = ExecutionEngineCommon(self.local, self.xmode)
        status = ex_eng._check_volumes()
        self.assertTrue(status)

    @patch('udocker.engine.base.NixAuthentication.get_home')
    def test_11__get_bindhome(self, mock_gethome):
        """Test ExecutionEngine()._get_bindhome()."""
        mock_gethome.return_value = ""
        ex_eng = ExecutionEngineCommon(self.local, self.xmode)
        ex_eng.opt["bindhome"] = False
        status = ex_eng._get_bindhome()
        self.assertEqual(status, "")

        mock_gethome.return_value = "/home/user"
        ex_eng = ExecutionEngineCommon(self.local, self.xmode)
        ex_eng.opt["bindhome"] = True
        status = ex_eng._get_bindhome()
        self.assertEqual(status, "/home/user")

        mock_gethome.return_value = ""
        ex_eng = ExecutionEngineCommon(self.local, self.xmode)
        ex_eng.opt["bindhome"] = True
        status = ex_eng._get_bindhome()
        self.assertEqual(status, "")

    def test_12__is_volume(self):
        """Test ExecutionEngineCommon()._is_volume()."""
        ex_eng = ExecutionEngineCommon(self.local, self.xmode)
        ex_eng.opt["vol"] = ["/tmp"]
        status = ex_eng._is_volume("/tmp")
        self.assertTrue(status)

        ex_eng = ExecutionEngineCommon(self.local, self.xmode)
        ex_eng.opt["vol"] = [""]
        status = ex_eng._is_volume("/tmp")
        self.assertFalse(status)

    # TODO: to be implemented
    def test_13__set_volume_bindings(self):
        """Test ExecutionEngineCommon()._set_volume_bindings()."""
        pass

    @patch('udocker.engine.base.Msg')
    @patch('udocker.engine.base.os.path.isdir')
    @patch('udocker.engine.base.Uenv.getenv')
    def test_14__check_paths(self, mock_getenv, mock_isdir, mock_msg):
        """Test ExecutionEngineCommon()._check_paths()."""
        mock_getenv.return_value = ""
        mock_isdir.return_value = False
        ex_eng = ExecutionEngineCommon(self.local, self.xmode)
        ex_eng.opt["uid"] = "0"
        ex_eng.opt["cwd"] = ""
        ex_eng.opt["home"] = "/home/user"
        ex_eng.container_root = "/containers/123/ROOT"
        status = ex_eng._check_paths()
        self.assertFalse(status)
        # self.assertEqual(ex_eng.opt["env"][-1],
        #                  "PATH=/usr/sbin:/sbin:/usr/bin:/bin")
        self.assertEqual(ex_eng.opt["cwd"], ex_eng.opt["home"])

        ex_eng = ExecutionEngineCommon(self.local, self.xmode)
        ex_eng.opt["uid"] = "1000"
        ex_eng.opt["cwd"] = ""
        ex_eng.opt["home"] = "/home/user"
        ex_eng.container_root = "/containers/123/ROOT"
        status = ex_eng._check_paths()
        self.assertFalse(status)
        # self.assertEqual(ex_eng.opt["env"][-1],
        #                  "PATH=/usr/bin:/bin:/usr/local/bin")
        self.assertEqual(ex_eng.opt["cwd"], ex_eng.opt["home"])

        mock_getenv.return_value = "PATH"
        mock_isdir.return_value = True
        ex_eng = ExecutionEngineCommon(self.local, self.xmode)
        ex_eng.opt["cwd"] = "/tmp"
        status = ex_eng._check_paths()
        self.assertTrue(status)

    @patch('udocker.engine.base.Msg')
    @patch('udocker.engine.base.os.access')
    @patch('udocker.engine.base.os.readlink')
    @patch('udocker.engine.base.os.path.isfile')
    @patch('udocker.engine.base.Uenv.getenv')
    def test_15__check_executable(self, mock_getenv, mock_isfile,
                                  mock_readlink, mock_access,
                                  mock_msg):
        """Test ExecutionEngineCommon()._check_executable()."""
        mock_getenv.return_value = ""
        mock_isfile.return_value = False
        ex_eng = ExecutionEngineCommon(self.local, self.xmode)
        ex_eng.opt["entryp"] = "/bin/shell -x -v"
        ex_eng.container_root = "/containers/123/ROOT"
        status = ex_eng._check_executable()
        self.assertFalse(status)

        mock_isfile.return_value = True
        mock_access.return_value = True
        ex_eng = ExecutionEngineCommon(self.local, self.xmode)
        status = ex_eng._check_executable()
        self.assertTrue(status)

        mock_getenv.return_value = ""
        mock_isfile.return_value = True
        mock_access.return_value = True
        ex_eng = ExecutionEngineCommon(self.local, self.xmode)
        ex_eng.opt["entryp"] = ["/bin/shell", "-x", "-v"]
        ex_eng.opt["cmd"] = ""
        status = ex_eng._check_executable()
        self.assertEqual(ex_eng.opt["cmd"], ex_eng.opt["entryp"])

        mock_getenv.return_value = ""
        mock_isfile.return_value = True
        mock_access.return_value = True
        ex_eng = ExecutionEngineCommon(self.local, self.xmode)
        ex_eng.opt["entryp"] = ["/bin/shell", ]
        ex_eng.opt["cmd"] = ["-x", "-v"]
        status = ex_eng._check_executable()
        self.assertEqual(ex_eng.opt["cmd"], ["/bin/shell", "-x", "-v"])

    @patch('udocker.engine.base.ContainerStructure.get_container_meta')
    @patch('udocker.engine.base.ContainerStructure.get_container_attr')
    @patch.object(ExecutionEngineCommon, '_check_exposed_ports')
    @patch('udocker.engine.base.Uenv.getenv')
    def test_16__run_load_metadata(self, mock_getenv, mock_chkports,
                                   mock_attr, mock_meta):
        """Test ExecutionEngineCommon()._run_load_metadata()."""
        mock_getenv.return_value = ""
        Config().conf['location'] = "/tmp/container"
        ex_eng = ExecutionEngineCommon(self.local, self.xmode)
        status = ex_eng._run_load_metadata("123")
        self.assertEqual(status, ("", []))

        Config().conf['location'] = ""
        mock_attr.return_value = ("", [])
        ex_eng = ExecutionEngineCommon(self.local, self.xmode)
        status = ex_eng._run_load_metadata("123")
        self.assertEqual(status, (None, None))

        Config().conf['location'] = ""
        mock_attr.return_value = ("/x", [])
        ex_eng = ExecutionEngineCommon(self.local, self.xmode)
        ex_eng.opt["nometa"] = True
        status = ex_eng._run_load_metadata("123")
        self.assertEqual(status, ("/x", []))

        # TODO: need to implement mock_meta with side_effects
        # self.conf['location'] = ""
        # mock_attr.return_value = ("/x", [])
        # ex_eng = ExecutionEngineCommon(self.local, self.xmode)
        # ex_eng.opt["nometa"] = False
        # status = ex_eng._run_load_metadata("123")
        # self.assertEqual(status, ("/x", []))

    # def test_17__check_env(self):
    #     """Test ExecutionEngineCommon()._check_env()."""
    #     pass

    # def test_20__select_auth_files(self):
    #     """Test ExecutionEngineCommon()._select_auth_files()."""
    #     pass

    # @patch('udocker.engine.base.Msg')
    # @patch('udocker.engine.base.NixAuthentication.get_user')
    # @patch.object(ExecutionEngineCommon, '_create_user')
    # def test_21__setup_container_user(self, mock_cruser,
    #                                   mock_getuser, mock_msg):
    #     """Test ExecutionEngineCommon()._setup_container_user()."""
    #     ex_eng = ExecutionEngineCommon(self.local, self.xmode)
    #     status = ex_eng._setup_container_user("0:0")
    #     self.assertFalse(status)

    #     mock_getuser.return_value = ("", "", "", "", "", "")
    #     ex_eng = ExecutionEngineCommon(self.local, self.xmode)
    #     ex_eng.opt["vol"] = ""
    #     ex_eng.opt["hostauth"] = False
    #     status = ex_eng._setup_container_user("0:0")
    #     self.assertTrue(status)
    #     self.assertTrue(mock_cruser.called)

    #     mock_getuser.return_value = ("root", 0, 0, "", "", "")
    #     ex_eng = ExecutionEngineCommon(self.local, self.xmode)
    #     ex_eng.opt["vol"] = ""
    #     ex_eng.opt["hostauth"] = False
    #     status = ex_eng._setup_container_user("0:0")
    #     self.assertTrue(status)
    #     self.assertTrue(mock_cruser.called)

    #     mock_getuser.return_value = ("", "", "", "", "", "")
    #     ex_eng = ExecutionEngineCommon(self.local, self.xmode)
    #     ex_eng.opt["vol"] = ""
    #     ex_eng.opt["hostauth"] = True
    #     status = ex_eng._setup_container_user("0:0")
    #     self.assertFalse(status)

    #     mock_getuser.return_value = ("root", 0, 0, "", "", "")
    #     ex_eng = ExecutionEngineCommon(self.local, self.xmode)
    #     ex_eng.opt["vol"] = ""
    #     ex_eng.opt["hostauth"] = True
    #     status = ex_eng._setup_container_user("0:0")
    #     self.assertTrue(status)
    #     self.assertTrue(mock_cruser.called)

    #     mock_getuser.return_value = ("", "", "", "", "", "")
    #     ex_eng = ExecutionEngineCommon(self.local, self.xmode)
    #     ex_eng.opt["vol"] = ""
    #     ex_eng.opt["hostauth"] = False
    #     status = ex_eng._setup_container_user("")
    #     self.assertTrue(status)
    #     self.assertTrue(mock_cruser.called)

    #     mock_getuser.return_value = ("root", 0, 0, "", "", "")
    #     ex_eng = ExecutionEngineCommon(self.local, self.xmode)
    #     ex_eng.opt["vol"] = ""
    #     ex_eng.opt["hostauth"] = False
    #     status = ex_eng._setup_container_user("")
    #     self.assertTrue(status)
    #     self.assertTrue(mock_cruser.called)

    #     mock_getuser.return_value = ("", "", "", "", "", "")
    #     ex_eng = ExecutionEngineCommon(self.local, self.xmode)
    #     ex_eng.opt["vol"] = ""
    #     ex_eng.opt["hostauth"] = True
    #     status = ex_eng._setup_container_user("")
    #     self.assertFalse(status)

    #     mock_getuser.return_value = ("", 100, 0, "", "", "")
    #     ex_eng = ExecutionEngineCommon(self.local, self.xmode)
    #     ex_eng.opt["vol"] = ""
    #     ex_eng.opt["hostauth"] = False
    #     status = ex_eng._setup_container_user("0:0")
    #     self.assertTrue(status)
    #     self.assertTrue(mock_cruser.called)
    #     self.assertEqual(ex_eng.opt["user"], 'root')

    # @patch('udocker.engine.base.NixAuthentication.get_group')
    # @patch('udocker.engine.base.NixAuthentication.add_group')
    # @patch('udocker.engine.base.NixAuthentication.add_user')
    # @patch('udocker.engine.base.os.getgroups')
    # @patch('udocker.engine.base.FileUtil')
    # @patch('udocker.engine.base.Msg')
    # @patch('udocker.engine.base.NixAuthentication')
    # def test_22__create_user(self, mock_nix, mock_msg,
    #                          mock_futil, mock_groups, mock_adduser,
    #                          mock_addgroup, mock_getgroup):
    #     """Test ExecutionEngineCommon()._create_user()."""
    #     container_auth = NixAuthentication("", "")
    #     container_auth.passwd_file = ""
    #     container_auth.group_file = ""
    #     host_auth = NixAuthentication("", "")
    #     self.conf['uid'] = 1000
    #     self.conf['gid'] = 1000
    #
    #     mock_adduser.return_value = False
    #     ex_eng = ExecutionEngineCommon(self.local, self.xmode)
    #     ex_eng.opt["uid"] = ""
    #     ex_eng.opt["gid"] = ""
    #     ex_eng.opt["user"] = ""
    #     ex_eng.opt["home"] = ""
    #     ex_eng.opt["shell"] = ""
    #     ex_eng.opt["gecos"] = ""
    #     status = ex_eng._create_user(container_auth, host_auth)
    #     # self.assertFalse(status)
    #     self.assertEqual(ex_eng.opt["uid"], "1000")
    #     self.assertEqual(ex_eng.opt["gid"], "1000")
    #     self.assertEqual(ex_eng.opt["user"], "udoc1000")
    #     self.assertEqual(ex_eng.opt["home"], "/home/udoc1000")
    #     self.assertEqual(ex_eng.opt["shell"], "/bin/sh")
    #     self.assertEqual(ex_eng.opt["gecos"], "*UDOCKER*")
    #
    #     mock_adduser.return_value = False
    #     ex_eng = ExecutionEngineCommon(self.local, self.xmode)
    #     ex_eng.opt["uid"] = "60000"
    #     ex_eng.opt["gid"] = "60000"
    #     ex_eng.opt["user"] = "someuser"
    #     ex_eng.opt["home"] = ""
    #     ex_eng.opt["shell"] = "/bin/false"
    #     ex_eng.opt["gecos"] = "*XXX*"
    #     status = ex_eng._create_user(container_auth, host_auth)
    #     # self.assertFalse(status)
    #     self.assertEqual(ex_eng.opt["uid"], "60000")
    #     self.assertEqual(ex_eng.opt["gid"], "60000")
    #     self.assertEqual(ex_eng.opt["user"], "someuser")
    #     self.assertEqual(ex_eng.opt["home"], "/home/someuser")
    #     self.assertEqual(ex_eng.opt["shell"], "/bin/false")
    #     self.assertEqual(ex_eng.opt["gecos"], "*XXX*")
    #
    #     mock_adduser.return_value = False
    #     ex_eng = ExecutionEngineCommon(self.local, self.xmode)
    #     ex_eng.opt["uid"] = "60000"
    #     ex_eng.opt["gid"] = "60000"
    #     ex_eng.opt["user"] = "someuser"
    #     ex_eng.opt["home"] = "/home/batata"
    #     ex_eng.opt["shell"] = "/bin/false"
    #     ex_eng.opt["gecos"] = "*XXX*"
    #     status = ex_eng._create_user(container_auth, host_auth)
    #     # self.assertFalse(status)
    #     self.assertEqual(ex_eng.opt["uid"], "60000")
    #     self.assertEqual(ex_eng.opt["gid"], "60000")
    #     self.assertEqual(ex_eng.opt["user"], "someuser")
    #     self.assertEqual(ex_eng.opt["home"], "/home/batata")
    #     self.assertEqual(ex_eng.opt["shell"], "/bin/false")
    #     self.assertEqual(ex_eng.opt["gecos"], "*XXX*")
    #
    #     mock_adduser.return_value = True
    #     mock_getgroup.return_value = ("", "", "")
    #     mock_addgroup.return_value = True
    #     mock_groups.return_valueUE = ()
    #     ex_eng = ExecutionEngineCommon(self.local, self.xmode)
    #     ex_eng.opt["uid"] = "60000"
    #     ex_eng.opt["gid"] = "60000"
    #     ex_eng.opt["user"] = "someuser"
    #     ex_eng.opt["home"] = "/home/batata"
    #     ex_eng.opt["shell"] = "/bin/false"
    #     ex_eng.opt["gecos"] = "*XXX*"
    #     status = ex_eng._create_user(container_auth, host_auth)
    #     self.assertTrue(status)
    #     self.assertEqual(ex_eng.opt["uid"], "60000")
    #     self.assertEqual(ex_eng.opt["gid"], "60000")
    #     self.assertEqual(ex_eng.opt["user"], "someuser")
    #     self.assertEqual(ex_eng.opt["home"], "/home/batata")
    #     self.assertEqual(ex_eng.opt["shell"], "/bin/false")
    #     self.assertEqual(ex_eng.opt["gecos"], "*XXX*")
    #     self.assertEqual(ex_eng.opt["hostauth"], True)
    #     mgroup = mock_nix.return_value.get_group
    #     self.assertTrue(mgroup.called_once_with("60000"))
    #
    #     mock_adduser.return_value = True
    #     mock_getgroup.return_value = ("", "", "")
    #     mock_addgroup.return_value = True
    #     mock_groups.return_value = (80000,)
    #     ex_eng = ExecutionEngineCommon(self.local, self.xmode)
    #     ex_eng.opt["uid"] = "60000"
    #     ex_eng.opt["gid"] = "60000"
    #     ex_eng.opt["user"] = "someuser"
    #     ex_eng.opt["home"] = "/home/batata"
    #     ex_eng.opt["shell"] = "/bin/false"
    #     ex_eng.opt["gecos"] = "*XXX*"
    #     status = ex_eng._create_user(container_auth, host_auth)
    #     self.assertTrue(status)
    #     self.assertEqual(ex_eng.opt["uid"], "60000")
    #     self.assertEqual(ex_eng.opt["gid"], "60000")
    #     self.assertEqual(ex_eng.opt["user"], "someuser")
    #     self.assertEqual(ex_eng.opt["home"], "/home/batata")
    #     self.assertEqual(ex_eng.opt["shell"], "/bin/false")
    #     self.assertEqual(ex_eng.opt["gecos"], "*XXX*")
    #     self.assertEqual(ex_eng.opt["hostauth"], True)
    #     ggroup = mock_getgroup
    #     self.assertTrue(ggroup.called_once_with("60000"))
    #     agroup = mock_addgroup
    #     self.assertTrue(agroup.called_once_with("G80000", "80000"))

    # TODO: to be implemented
    def test_23__uid_check_noroot(self):
        """Test ExecutionEngineCommon()._uid_check_noroot()."""
        pass

    # TODO: to be implemented
    def test_24__setup_container_user_noroot(self):
        """Test ExecutionEngineCommon()._setup_container_user_noroot()."""
        pass

    @patch('udocker.engine.base.Msg')
    @patch('udocker.engine.base.os.path.basename')
    def test_25__run_banner(self, mock_base, mock_msg):
        """Test ExecutionEngineCommon()._run_banner()."""
        ex_eng = ExecutionEngineCommon(self.local, self.xmode)
        ex_eng._run_banner("/bin/bash")
        ex_eng.container_id = "CONTAINERID"
        self.assertTrue(mock_base.called_once_with("/bin/bash"))

    # @patch('udocker.engine.base.os')
    # def test_26__run_env_cleanup_dict(self, mock_os):
    #     """Test ExecutionEngineCommon()._run_env_cleanup_dict()."""
    #     self.conf['valid_host_env'] = ("HOME",)
    #     mock_os.return_value.environ.return_value = {'HOME': '/', 'USERNAME': 'user', }
    #     ex_eng = ExecutionEngineCommon(self.local, self.xmode)
    #     ex_eng._run_env_cleanup_dict()
    #     self.assertEqual(mock_os.return_value.environ.return_value, {'HOME': '/', })

    # @patch('udocker.engine.base.os.environ')
    # def test_27__run_env_cleanup_list(self, mock_osenv):
    #     """Test ExecutionEngineCommon()._run_env_cleanup_list()."""
    #     self.conf['valid_host_env'] = ("HOME",)
    #     mock_osenv.return_value = {'HOME': '/', 'USERNAME': 'user', }
    #     ex_eng = ExecutionEngineCommon(self.local, self.xmode)
    #     ex_eng._run_env_cleanup_list()
    #     self.assertEqual(mock_osenv, {'HOME': '/', })

    # TODO: to be implemented
    def test_28__run_env_get(self):
        """Test ExecutionEngineCommon()._run_env_get()."""
        pass

    def test_29__run_env_set(self):
        """Test ExecutionEngineCommon()._run_env_set()."""
        # self._init()
        ex_eng = ExecutionEngineCommon(self.local, self.xmode)
        ex_eng.opt["home"] = "/"
        ex_eng.opt["user"] = "user"
        ex_eng.opt["uid"] = "1000"
        ex_eng.container_root = "/croot"
        ex_eng.container_id = "2717add4-e6f6-397c-9019-74fa67be439f"
        ex_eng.container_names = ['cna[]me', ]
        ex_eng.exec_mode = MagicMock()
        ex_eng.exec_mode.get_mode.return_value = "P1"
        ex_eng._run_env_set()
        # self.assertTrue("USER=" + ex_eng.opt["user"] in ex_eng.opt["env"])
        # self.assertTrue("LOGNAME=" + ex_eng.opt["user"] in ex_eng.opt["env"])
        # self.assertTrue("USERNAME=" + ex_eng.opt["user"] in ex_eng.opt["env"])
        # self.assertTrue("SHLVL=0" in ex_eng.opt["env"])
        # self.assertTrue("container_root=/croot" in ex_eng.opt["env"])

    @patch.object(ExecutionEngineCommon, '_check_exposed_ports')
    @patch.object(ExecutionEngineCommon, '_set_volume_bindings')
    @patch.object(ExecutionEngineCommon, '_check_executable')
    @patch.object(ExecutionEngineCommon, '_check_paths')
    @patch.object(ExecutionEngineCommon, '_setup_container_user')
    @patch.object(ExecutionEngineCommon, '_run_load_metadata')
    @patch('udocker.container.localrepo.LocalRepository.get_container_name', autospec=True)
    def test_30__run_init(self, mock_getcname, mock_loadmeta, mock_setupuser,
                          mock_chkpaths, mock_chkexec, mock_setvol, mock_chkports):
        """Test ExecutionEngineCommon()._run_init()."""
        mock_getcname.return_value = "cname"
        mock_loadmeta.return_value = ("/container_dir", "dummy",)
        mock_setupuser.return_value = True
        mock_chkpaths.return_value = True
        mock_chkexec.return_value = True
        ex_eng = ExecutionEngineCommon(self.local, self.xmode)
        status = ex_eng._run_init("2717add4-e6f6-397c-9019-74fa67be439f")
        self.assertTrue(status)
        self.assertEqual(ex_eng.container_root, "/container_dir/ROOT")

        mock_setupuser.return_value = False
        mock_chkpaths.return_value = True
        mock_chkexec.return_value = True
        ex_eng = ExecutionEngineCommon(self.local, self.xmode)
        status = ex_eng._run_init("2717add4-e6f6-397c-9019-74fa67be439f")
        self.assertFalse(status)

        mock_setupuser.return_value = True
        mock_chkpaths.return_value = False
        mock_chkexec.return_value = True
        ex_eng = ExecutionEngineCommon(self.local, self.xmode)
        status = ex_eng._run_init("2717add4-e6f6-397c-9019-74fa67be439f")
        self.assertFalse(status)

        mock_setupuser.return_value = True
        mock_chkpaths.return_value = True
        mock_chkexec.return_value = False
        ex_eng = ExecutionEngineCommon(self.local, self.xmode)
        status = ex_eng._run_init("2717add4-e6f6-397c-9019-74fa67be439f")
        self.assertFalse(status)


    #### Removed or moved to another class
    # @patch('udocker.engine.base.os.path.isdir')
    # def test_08__cont2host(self, mock_isdir):
    #     """Test ExecutionEngine()._cont2host()."""
    #     mock_isdir.return_value = True
    #     ex_eng = ExecutionEngineCommon(self.local, self.xmode)
    #     ex_eng.opt["vol"] = ("/opt/xxx:/mnt",)
    #     status = ex_eng._cont2host("/mnt")
    #     self.assertEqual(status, "/opt/xxx")

    #     ex_eng = ExecutionEngineCommon(self.local, self.xmode)
    #     ex_eng.opt["vol"] = ("/var/xxx:/mnt",)
    #     status = ex_eng._cont2host("/opt")
    #     self.assertTrue(status.endswith("/opt"))

    #     # change dir to volume (regression of #51)
    #     ex_eng = ExecutionEngineCommon(self.local, self.xmode)
    #     ex_eng.opt["vol"] = ("/var/xxx",)
    #     status = ex_eng._cont2host("/var/xxx/tt")
    #     self.assertEqual(status, "/var/xxx/tt")

    #     # change dir to volume (regression of #51)
    #     ex_eng = ExecutionEngineCommon(self.local, self.xmode)
    #     ex_eng.opt["vol"] = ("/var/xxx:/mnt",)
    #     status = ex_eng._cont2host("/mnt/tt")
    #     self.assertEqual(status, "/var/xxx/tt")

    # def test_02_oskernel_isgreater(self):
    #     """Test Config.oskernel_isgreater()."""
    #     Config().conf['oskernel'] = "1.1.2-"
    #     ex_eng = ExecutionEngineCommon(self.local, self.xmode)
    #     status = ex_eng._oskernel_isgreater([1, 1, 1])
    #     self.assertTrue(status)

    #     Config().conf['oskernel'] = "1.2.1-"
    #     status = ex_eng._oskernel_isgreater([1, 1, 1])
    #     self.assertTrue(status)

    #     Config().conf['oskernel'] = "1.0.0-"
    #     status = ex_eng._oskernel_isgreater([1, 1, 1])
    #     self.assertFalse(status)

    # def test_18__getenv(self):
    #     """Test ExecutionEngineCommon()._getenv()."""
    #     ex_eng = ExecutionEngineCommon(self.local, self.xmode)
    #     ex_eng.opt["env"] = ["HOME=/home/user", "PATH=/bin:/usr/bin"]
    #     status = ex_eng._getenv("")
    #     self.assertEqual(status, None)

    #     ex_eng = ExecutionEngineCommon(self.local, self.xmode)
    #     ex_eng.opt["env"] = ["HOME=/home/user", "PATH=/bin:/usr/bin"]
    #     status = ex_eng._getenv("XXX")
    #     self.assertEqual(status, None)

    #     ex_eng = ExecutionEngineCommon(self.local, self.xmode)
    #     ex_eng.opt["env"] = ["HOME=/home/user", "PATH=/bin:/usr/bin"]
    #     status = ex_eng._getenv("HOME")
    #     self.assertEqual(status, "/home/user")

    #     ex_eng = ExecutionEngineCommon(self.local, self.xmode)
    #     ex_eng.opt["env"] = ["HOME=/home/user", "PATH=/bin:/usr/bin"]
    #     status = ex_eng._getenv("PATH")
    #     self.assertEqual(status, "/bin:/usr/bin")

    # @patch('udocker.engine.base.Msg')
    # def test_19__uid_gid_from_str(self, mock_msg):
    #     """Test ExecutionEngineCommon()._uid_gid_from_str()."""
    #     ex_eng = ExecutionEngineCommon(self.local, self.xmode)
    #     status = ex_eng._uid_gid_from_str("")
    #     self.assertEqual(status, (None, None))

    #     ex_eng = ExecutionEngineCommon(self.local, self.xmode)
    #     status = ex_eng._uid_gid_from_str("0:0")
    #     self.assertEqual(status, ('0', '0'))

    #     ex_eng = ExecutionEngineCommon(self.local, self.xmode)
    #     status = ex_eng._uid_gid_from_str("100:100")
    #     self.assertEqual(status, ('100', '100'))


if __name__ == '__main__':
    main()
