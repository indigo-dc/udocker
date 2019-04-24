#!/usr/bin/env python
"""
udocker unit tests: ExecutionEngineCommon
"""

import sys
from unittest import TestCase, main
try:
    from unittest.mock import Mock, patch, MagicMock, mock_open
except ImportError:
    from mock import Mock, patch, MagicMock, mock_open

sys.path.append('.')

from udocker.engine.base import ExecutionEngineCommon
from udocker.config import Config
from udocker.container.localrepo import LocalRepository
from udocker.helper.nixauth import NixAuthentication


class ExecutionEngineCommonTestCase(TestCase):
    """Test ExecutionEngineCommon().
    Parent class for containers execution.
    """

    def setUp(self):
        self.conf = Config().getconf()

        self.conf['hostauth_list'] = ("/etc/passwd", "/etc/group")
        self.conf['cmd'] = "/bin/bash"
        self.conf['cpu_affinity_exec_tools'] = (["numactl", "-C", "%s", "--", ],
                                                ["taskset", "-c", "%s", ])
        self.conf['location'] = ""
        self.conf['uid'] = 1000
        self.conf['sysdirs_list'] = ["/", ]
        self.conf['root_path'] = "/usr/sbin:/sbin:/usr/bin:/bin"
        self.conf['user_path'] = "/usr/bin:/bin:/usr/local/bin"
        self.xmode = "P1"
        self.local = LocalRepository(self.conf)
        self.ex_eng = ExecutionEngineCommon(self.conf, self.local, self.xmode)

    def tearDown(self):
        pass

    @patch('udocker.container.localrepo.LocalRepository')
    def test_01_init(self, mock_local):
        """Test ExecutionEngineCommon() constructor"""
        self.assertEqual(self.ex_eng.container_id, "")
        self.assertEqual(self.ex_eng.container_root, "")
        self.assertEqual(self.ex_eng.container_names, [])
        self.assertEqual(self.ex_eng.opt["nometa"], False)
        self.assertEqual(self.ex_eng.opt["nosysdirs"], False)
        self.assertEqual(self.ex_eng.opt["dri"], False)
        self.assertEqual(self.ex_eng.opt["bindhome"], False)
        self.assertEqual(self.ex_eng.opt["hostenv"], False)
        self.assertEqual(self.ex_eng.opt["hostauth"], False)
        self.assertEqual(self.ex_eng.opt["novol"], [])
        self.assertEqual(self.ex_eng.opt["env"], [])
        self.assertEqual(self.ex_eng.opt["vol"], [])
        self.assertEqual(self.ex_eng.opt["cpuset"], "")
        self.assertEqual(self.ex_eng.opt["user"], "")
        self.assertEqual(self.ex_eng.opt["cwd"], "")
        self.assertEqual(self.ex_eng.opt["entryp"], "")
        self.assertEqual(self.ex_eng.opt["cmd"], self.conf['cmd'])
        self.assertEqual(self.ex_eng.opt["hostname"], "")
        self.assertEqual(self.ex_eng.opt["domain"], "")
        self.assertEqual(self.ex_eng.opt["volfrom"], [])

    @patch('udocker.msg.Msg')
    @patch('udocker.container.localrepo.LocalRepository')
    def test_02__check_exposed_ports(self, mock_local, mock_msg):
        """Test ExecutionEngineCommon()._check_exposed_ports()."""
        self.ex_eng.opt["portsexp"] = ("1024", "2048/tcp", "23000/udp")
        status = self.ex_eng._check_exposed_ports()
        self.assertTrue(status)
        #
        self.ex_eng.opt["portsexp"] = ("1023", "2048/tcp", "23000/udp")
        status = self.ex_eng._check_exposed_ports()
        self.assertFalse(status)
        #
        self.ex_eng.opt["portsexp"] = ("1024", "80/tcp", "23000/udp")
        status = self.ex_eng._check_exposed_ports()
        self.assertFalse(status)
        #
        self.ex_eng.opt["portsexp"] = ("1024", "2048/tcp", "23/udp")
        status = self.ex_eng._check_exposed_ports()
        self.assertFalse(status)

    @patch('udocker.utils.fileutil.FileUtil.find_exec')
    @patch('udocker.container.localrepo.LocalRepository')
    def test_03__set_cpu_affinity(self, mock_local, mock_findexec):
        """Test ExecutionEngineCommon()._set_cpu_affinity()."""
        mock_findexec.return_value = ""
        status = self.ex_eng._set_cpu_affinity()
        self.assertEqual(status, [])
        #
        mock_findexec.return_value = "taskset"
        status = self.ex_eng._set_cpu_affinity()
        self.assertEqual(status, [])
        #
        mock_findexec.return_value = "numactl"
        self.ex_eng.opt["cpuset"] = "1-2"
        status = self.ex_eng._set_cpu_affinity()
        self.assertEqual(status, ["numactl", "-C", "1-2", "--"])

    @patch('udocker.engine.base.os.path.isdir')
    @patch('udocker.container.localrepo.LocalRepository')
    def test_04__cont2host(self, mock_local, mock_isdir):
        """Test ExecutionEngine()._cont2host()."""
        mock_isdir.return_value = True
        self.ex_eng.opt["vol"] = ("/opt/xxx:/mnt",)
        status = self.ex_eng._cont2host("/mnt")
        self.assertEqual(status, "/opt/xxx")
        #
        self.ex_eng.opt["vol"] = ("/var/xxx:/mnt",)
        status = self.ex_eng._cont2host("/opt")
        self.assertTrue(status.endswith("/opt"))
        # change dir to volume (regression of #51)
        self.ex_eng.opt["vol"] = ("/var/xxx",)
        status = self.ex_eng._cont2host("/var/xxx/tt")
        self.assertEqual(status, "/var/xxx/tt")
        # change dir to volume (regression of #51)
        self.ex_eng.opt["vol"] = ("/var/xxx:/mnt",)
        status = self.ex_eng._cont2host("/mnt/tt")
        self.assertEqual(status, "/var/xxx/tt")

    @patch('udocker.msg.Msg')
    @patch('udocker.engine.base.os.path.isdir')
    @patch('udocker.engine.base.os.path.exists')
    @patch('udocker.engine.base.ExecutionEngineCommon._cont2host')
    @patch('udocker.engine.base.ExecutionEngineCommon._getenv')
    @patch('udocker.container.localrepo.LocalRepository')
    def test_05__check_paths(self, mock_local, mock_getenv, mock_isinvol,
                             mock_exists, mock_isdir, mock_msg):
        """Test ExecutionEngineCommon()._check_paths()."""
        mock_getenv.return_value = ""
        mock_isinvol.return_value = False
        mock_exists.return_value = False
        mock_isdir.return_value = False
        self.ex_eng.opt["uid"] = "0"
        self.ex_eng.opt["cwd"] = ""
        self.ex_eng.opt["home"] = "/home/user"
        self.ex_eng.container_root = "/containers/123/ROOT"
        status = self.ex_eng._check_paths()
        self.assertFalse(status)
        self.assertEqual(self.ex_eng.opt["env"][-1],
                         "PATH=/usr/sbin:/sbin:/usr/bin:/bin")
        self.assertEqual(self.ex_eng.opt["cwd"], self.ex_eng.opt["home"])
        #
        self.ex_eng.opt["uid"] = "1000"
        status = self.ex_eng._check_paths()
        self.assertFalse(status)
        self.assertEqual(self.ex_eng.opt["env"][-1],
                         "PATH=/usr/bin:/bin:/usr/local/bin")
        self.assertEqual(self.ex_eng.opt["cwd"], self.ex_eng.opt["home"])
        #
        mock_exists.return_value = True
        mock_isdir.return_value = True
        status = self.ex_eng._check_paths()
        self.assertTrue(status)

    @patch('udocker.msg.Msg')
    @patch('udocker.engine.base.os.access')
    @patch('udocker.engine.base.os.readlink')
    @patch('udocker.engine.base.os.path.isfile')
    @patch('udocker.engine.base.ExecutionEngineCommon._getenv')
    @patch('udocker.container.localrepo.LocalRepository')
    def test_06__check_executable(self, mock_local, mock_getenv, mock_isfile,
                                  mock_readlink, mock_access, mock_msg):
        """Test ExecutionEngineCommon()._check_executable()."""
        mock_getenv.return_value = ""
        self.ex_eng.opt["entryp"] = "/bin/shell -x -v"
        mock_isfile.return_value = False
        self.ex_eng.container_root = "/containers/123/ROOT"
        status = self.ex_eng._check_executable()
        self.assertFalse(status)
        #
        mock_isfile.return_value = True
        mock_access.return_value = True
        status = self.ex_eng._check_executable()
        self.assertTrue(status)
        #
        self.ex_eng.opt["entryp"] = ["/bin/shell", "-x", "-v"]
        self.ex_eng.opt["cmd"] = ""
        status = self.ex_eng._check_executable()
        self.assertEqual(self.ex_eng.opt["cmd"], self.ex_eng.opt["entryp"])
        #
        self.ex_eng.opt["entryp"] = ["/bin/shell", ]
        self.ex_eng.opt["cmd"] = ["-x", "-v"]
        status = self.ex_eng._check_executable()
        self.assertEqual(self.ex_eng.opt["cmd"], ["/bin/shell", "-x", "-v"])

    @patch('udocker.container.structure.ContainerStructure.get_container_attr')
    @patch('udocker.engine.base.ExecutionEngineCommon._check_exposed_ports')
    @patch('udocker.engine.base.ExecutionEngineCommon._getenv')
    @patch('udocker.container.localrepo.LocalRepository')
    def test_07__run_load_metadata(self, mock_local, mock_getenv,
                                   mock_chkports, mock_cattr):
        """Test ExecutionEngineCommon()._run_load_metadata()."""
        mock_getenv.return_value = ""
        self.conf['location'] = "/tmp/container"
        status = self.ex_eng._run_load_metadata("123")
        self.assertEqual(status, ("", []))
        #
        self.conf['location'] = ""
        mock_cattr.return_value = ("", [])
        status = self.ex_eng._run_load_metadata("123")
        self.assertEqual(status, (None, None))
        #
        self.conf['location'] = ""
        mock_cattr.return_value = ("/x", [])
        self.ex_eng.opt["nometa"] = True
        status = self.ex_eng._run_load_metadata("123")
        self.assertEqual(status, ("/x", []))
        #
        # self.conf['location'] = ""
        # mock_cattr.return_value = ("/x", [])
        # self.ex_eng.opt["nometa"] = False
        # status = self.ex_eng._run_load_metadata("123")
        # self.assertEqual(status, ("/x", []))

    @patch('udocker.container.localrepo.LocalRepository')
    def test_08__getenv(self, mock_local):
        """Test ExecutionEngineCommon()._getenv()."""
        self.ex_eng.opt["env"] = ["HOME=/home/user", "PATH=/bin:/usr/bin"]
        status = self.ex_eng._getenv("")
        self.assertEqual(status, None)
        #
        status = self.ex_eng._getenv("XXX")
        self.assertEqual(status, None)
        #
        status = self.ex_eng._getenv("HOME")
        self.assertEqual(status, "/home/user")
        #
        status = self.ex_eng._getenv("PATH")
        self.assertEqual(status, "/bin:/usr/bin")

    @patch('udocker.msg.Msg')
    @patch('udocker.container.localrepo.LocalRepository')
    def test_09__uid_gid_from_str(self, mock_local, mock_msg):
        """Test ExecutionEngineCommon()._uid_gid_from_str()."""
        status = self.ex_eng._uid_gid_from_str("")
        self.assertEqual(status, (None, None))
        #
        status = self.ex_eng._uid_gid_from_str("0:0")
        self.assertEqual(status, ('0', '0'))
        #
        status = self.ex_eng._uid_gid_from_str("100:100")
        self.assertEqual(status, ('100', '100'))

    @patch('udocker.msg.Msg')
    @patch('udocker.helper.nixauth.NixAuthentication.get_user')
    @patch('udocker.container.localrepo.LocalRepository')
    @patch('udocker.engine.base.ExecutionEngineCommon._create_user')
    @patch('udocker.engine.base.ExecutionEngineCommon._uid_gid_from_str')
    def test_10__setup_container_user(self, mock_ugfs, mock_cruser,
                                      mock_local, mock_getuser, mock_msg):
        """Test ExecutionEngineCommon()._setup_container_user()."""
        mock_ugfs.return_value = (None, None)
        status = self.ex_eng._setup_container_user("0:0")
        self.assertFalse(status)
        self.assertTrue(mock_ugfs.called_once_with("root"))
        #
        self.ex_eng.opt["vol"] = ""
        self.ex_eng.opt["hostauth"] = False
        mock_getuser.return_value = ("", "", "", "", "", "")
        mock_ugfs.return_value = ("0", "0")
        status = self.ex_eng._setup_container_user("0:0")
        self.assertTrue(status)
        self.assertTrue(mock_cruser.called)
        #
        self.ex_eng.opt["vol"] = ""
        self.ex_eng.opt["hostauth"] = False
        mock_getuser.return_value = ("root", 0, 0, "", "", "")
        mock_ugfs.return_value = ("0", "0")
        status = self.ex_eng._setup_container_user("0:0")
        self.assertTrue(status)
        self.assertTrue(mock_cruser.called)
        #
        self.ex_eng.opt["vol"] = ""
        self.ex_eng.opt["hostauth"] = True
        mock_getuser.return_value = ("", "", "", "", "", "")
        mock_ugfs.return_value = ("0", "0")
        status = self.ex_eng._setup_container_user("0:0")
        self.assertFalse(status)
        #
        self.ex_eng.opt["vol"] = ""
        self.ex_eng.opt["hostauth"] = True
        mock_getuser.return_value = ("root", 0, 0, "", "", "")
        mock_ugfs.return_value = ("0", "0")
        status = self.ex_eng._setup_container_user("0:0")
        self.assertTrue(status)
        self.assertTrue(mock_cruser.called)
        #
        self.ex_eng.opt["vol"] = ""
        self.ex_eng.opt["hostauth"] = False
        mock_getuser.return_value = ("", "", "", "", "", "")
        status = self.ex_eng._setup_container_user("")
        self.assertTrue(status)
        self.assertTrue(mock_cruser.called)
        #
        self.ex_eng.opt["vol"] = ""
        self.ex_eng.opt["hostauth"] = False
        mock_getuser.return_value = ("root", 0, 0, "", "", "")
        status = self.ex_eng._setup_container_user("")
        self.assertTrue(status)
        self.assertTrue(mock_cruser.called)
        #
        self.ex_eng.opt["vol"] = ""
        self.ex_eng.opt["hostauth"] = True
        mock_getuser.return_value = ("", "", "", "", "", "")
        status = self.ex_eng._setup_container_user("")
        self.assertFalse(status)
        #
        self.ex_eng.opt["vol"] = ""
        self.ex_eng.opt["hostauth"] = False
        mock_getuser.return_value = ("", 100, 0, "", "", "")
        mock_ugfs.return_value = ("0", "0")
        status = self.ex_eng._setup_container_user("0:0")
        self.assertTrue(status)
        self.assertTrue(mock_cruser.called)
        self.assertEqual(self.ex_eng.opt["user"], "")

    @patch('udocker.helper.nixauth.NixAuthentication.get_group')
    @patch('udocker.helper.nixauth.NixAuthentication.add_group')
    @patch('udocker.helper.nixauth.NixAuthentication.add_user')
    @patch('udocker.engine.base.os.getgroups')
    @patch('udocker.utils.fileutil.FileUtil')
    @patch('udocker.msg.Msg')
    @patch('udocker.helper.nixauth.NixAuthentication')
    @patch('udocker.container.localrepo.LocalRepository')
    def test_11__create_user(self, mock_local, mock_nix, mock_msg,
                             mock_futil, mock_groups, mock_adduser,
                             mock_addgroup, mock_getgroup):
        """Test ExecutionEngineCommon()._create_user()."""
        container_auth = NixAuthentication("", "")
        container_auth.passwd_file = ""
        container_auth.group_file = ""
        host_auth = NixAuthentication("", "")
        #
        self.conf['uid'] = 1000
        self.conf['gid'] = 1000
        mock_adduser.return_value = False
        self.ex_eng.opt["uid"] = ""
        self.ex_eng.opt["gid"] = ""
        self.ex_eng.opt["user"] = ""
        self.ex_eng.opt["home"] = ""
        self.ex_eng.opt["shell"] = ""
        self.ex_eng.opt["gecos"] = ""
        status = self.ex_eng._create_user(container_auth, host_auth)
        # self.assertFalse(status)
        self.assertEqual(self.ex_eng.opt["uid"], "1000")
        self.assertEqual(self.ex_eng.opt["gid"], "1000")
        self.assertEqual(self.ex_eng.opt["user"], "udoc1000")
        self.assertEqual(self.ex_eng.opt["home"], "/home/udoc1000")
        self.assertEqual(self.ex_eng.opt["shell"], "/bin/sh")
        self.assertEqual(self.ex_eng.opt["gecos"], "*UDOCKER*")
        #
        mock_adduser.return_value = False
        self.ex_eng.opt["uid"] = "60000"
        self.ex_eng.opt["gid"] = "60000"
        self.ex_eng.opt["user"] = "someuser"
        self.ex_eng.opt["home"] = ""
        self.ex_eng.opt["shell"] = "/bin/false"
        self.ex_eng.opt["gecos"] = "*XXX*"
        status = self.ex_eng._create_user(container_auth, host_auth)
        # self.assertFalse(status)
        self.assertEqual(self.ex_eng.opt["uid"], "60000")
        self.assertEqual(self.ex_eng.opt["gid"], "60000")
        self.assertEqual(self.ex_eng.opt["user"], "someuser")
        self.assertEqual(self.ex_eng.opt["home"], "/home/someuser")
        self.assertEqual(self.ex_eng.opt["shell"], "/bin/false")
        self.assertEqual(self.ex_eng.opt["gecos"], "*XXX*")
        #
        mock_adduser.return_value = False
        self.ex_eng.opt["uid"] = "60000"
        self.ex_eng.opt["gid"] = "60000"
        self.ex_eng.opt["user"] = "someuser"
        self.ex_eng.opt["home"] = "/home/batata"
        self.ex_eng.opt["shell"] = "/bin/false"
        self.ex_eng.opt["gecos"] = "*XXX*"
        status = self.ex_eng._create_user(container_auth, host_auth)
        # self.assertFalse(status)
        self.assertEqual(self.ex_eng.opt["uid"], "60000")
        self.assertEqual(self.ex_eng.opt["gid"], "60000")
        self.assertEqual(self.ex_eng.opt["user"], "someuser")
        self.assertEqual(self.ex_eng.opt["home"], "/home/batata")
        self.assertEqual(self.ex_eng.opt["shell"], "/bin/false")
        self.assertEqual(self.ex_eng.opt["gecos"], "*XXX*")
        #
        mock_adduser.return_value = True
        mock_getgroup.return_value = ("", "", "")
        mock_addgroup.return_value = True
        mock_groups.return_value = ()
        self.ex_eng.opt["uid"] = "60000"
        self.ex_eng.opt["gid"] = "60000"
        self.ex_eng.opt["user"] = "someuser"
        self.ex_eng.opt["home"] = "/home/batata"
        self.ex_eng.opt["shell"] = "/bin/false"
        self.ex_eng.opt["gecos"] = "*XXX*"
        status = self.ex_eng._create_user(container_auth, host_auth)
        self.assertTrue(status)
        self.assertEqual(self.ex_eng.opt["uid"], "60000")
        self.assertEqual(self.ex_eng.opt["gid"], "60000")
        self.assertEqual(self.ex_eng.opt["user"], "someuser")
        self.assertEqual(self.ex_eng.opt["home"], "/home/batata")
        self.assertEqual(self.ex_eng.opt["shell"], "/bin/false")
        self.assertEqual(self.ex_eng.opt["gecos"], "*XXX*")
        self.assertEqual(self.ex_eng.opt["hostauth"], True)
        mgroup = mock_nix.return_value.get_group
        self.assertTrue(mgroup.called_once_with("60000"))
        #
        mock_adduser.return_value = True
        mock_getgroup.return_value = ("", "", "")
        mock_addgroup.return_value = True
        mock_groups.return_value = (80000,)
        self.ex_eng.opt["uid"] = "60000"
        self.ex_eng.opt["gid"] = "60000"
        self.ex_eng.opt["user"] = "someuser"
        self.ex_eng.opt["home"] = "/home/batata"
        self.ex_eng.opt["shell"] = "/bin/false"
        self.ex_eng.opt["gecos"] = "*XXX*"
        status = self.ex_eng._create_user(container_auth, host_auth)
        self.assertTrue(status)
        self.assertEqual(self.ex_eng.opt["uid"], "60000")
        self.assertEqual(self.ex_eng.opt["gid"], "60000")
        self.assertEqual(self.ex_eng.opt["user"], "someuser")
        self.assertEqual(self.ex_eng.opt["home"], "/home/batata")
        self.assertEqual(self.ex_eng.opt["shell"], "/bin/false")
        self.assertEqual(self.ex_eng.opt["gecos"], "*XXX*")
        self.assertEqual(self.ex_eng.opt["hostauth"], True)
        ggroup = mock_getgroup
        self.assertTrue(ggroup.called_once_with("60000"))
        agroup = mock_addgroup
        self.assertTrue(agroup.called_once_with("G80000", "80000"))

    @patch('udocker.msg.Msg')
    @patch('udocker.engine.base.os.path.basename')
    @patch('udocker.container.localrepo.LocalRepository')
    def test_12__run_banner(self, mock_local, mock_base, mock_msg):
        """Test ExecutionEngineCommon()._run_banner()."""
        self.ex_eng._run_banner("/bin/bash")
        self.ex_eng.container_id = "CONTAINERID"
        self.assertTrue(mock_base.called_once_with("/bin/bash"))

    # @patch('udocker.engine.base.os.environ')
    # @patch('udocker.container.localrepo.LocalRepository')
    # def test_14__env_cleanup_dict(self, mock_local, mock_osenv):
    #     """Test ExecutionEngineCommon()._env_cleanup()."""
    #     # self._init()
    #     self.conf['valid_host_env'] = ("HOME",)
    #     mock_osenv.return_value = {'HOME': '/', 'USERNAME': 'user', }
    #     self.ex_eng._run_env_cleanup_dict()
    #     self.assertEqual(mock_osenv, {'HOME': '/', })

    @patch('udocker.config.Config')
    @patch('udocker.container.localrepo.LocalRepository')
    def test_15__run_env_set(self, mock_local, mock_config):
        """Test ExecutionEngineCommon()._run_env_set()."""
        # self._init()
        self.ex_eng.opt["home"] = "/"
        self.ex_eng.opt["user"] = "user"
        self.ex_eng.opt["uid"] = "1000"
        self.ex_eng.container_root = "/croot"
        self.ex_eng.container_id = "2717add4-e6f6-397c-9019-74fa67be439f"
        self.ex_eng.container_names = ['cna[]me', ]
        self.ex_eng.exec_mode = MagicMock()
        self.ex_eng.exec_mode.get_mode.return_value = "P1"
        self.ex_eng._run_env_set()
        self.assertTrue("HOME=" + self.ex_eng.opt["home"] in self.ex_eng.opt["env"])
        self.assertTrue("USER=" + self.ex_eng.opt["user"] in self.ex_eng.opt["env"])
        self.assertTrue("LOGNAME=" + self.ex_eng.opt["user"] in self.ex_eng.opt["env"])
        self.assertTrue("USERNAME=" + self.ex_eng.opt["user"] in self.ex_eng.opt["env"])
        self.assertTrue("SHLVL=0" in self.ex_eng.opt["env"])
        self.assertTrue("container_root=/croot" in self.ex_eng.opt["env"])

    @patch('udocker.engine.execmode.ExecutionMode')
    @patch('udocker.engine.base.ExecutionEngineCommon._set_volume_bindings')
    @patch('udocker.engine.base.ExecutionEngineCommon._check_executable')
    @patch('udocker.engine.base.ExecutionEngineCommon._check_paths')
    @patch('udocker.engine.base.ExecutionEngineCommon._setup_container_user')
    @patch('udocker.engine.base.ExecutionEngineCommon._run_load_metadata')
    @patch('udocker.container.localrepo.LocalRepository.get_container_name')
    def test_16__run_init(self, mock_getcname, mock_loadmeta, mock_setupuser,
                          mock_chkpaths, mock_chkexec, mock_chkvol,
                          mock_execmode):
        """Test ExecutionEngineCommon()._run_init()."""
        mock_getcname.return_value = "cname"
        mock_loadmeta.return_value = ("/container_dir", "dummy",)
        mock_setupuser.return_value = True
        mock_chkpaths.return_value = True
        mock_chkexec.return_value = True
        status = self.ex_eng._run_init("2717add4-e6f6-397c-9019-74fa67be439f")
        self.assertTrue(status)
        self.assertEqual(self.ex_eng.container_root, "/container_dir/ROOT")
        #
        mock_setupuser.return_value = False
        mock_chkpaths.return_value = True
        mock_chkexec.return_value = True
        status = self.ex_eng._run_init("2717add4-e6f6-397c-9019-74fa67be439f")
        self.assertFalse(status)
        #
        mock_setupuser.return_value = True
        mock_chkpaths.return_value = False
        mock_chkexec.return_value = True
        status = self.ex_eng._run_init("2717add4-e6f6-397c-9019-74fa67be439f")
        self.assertFalse(status)
        #
        mock_setupuser.return_value = True
        mock_chkpaths.return_value = True
        mock_chkexec.return_value = False
        status = self.ex_eng._run_init("2717add4-e6f6-397c-9019-74fa67be439f")
        self.assertFalse(status)

    @patch('udocker.helper.nixauth.NixAuthentication.get_home')
    @patch('udocker.container.localrepo.LocalRepository')
    def test_17__get_bindhome(self, mock_local, mock_gethome):
        """Test ExecutionEngine()._get_bindhome()."""
        mock_gethome.return_value = ""
        self.ex_eng.opt["bindhome"] = False
        status = self.ex_eng._get_bindhome()
        self.assertEqual(status, "")
        #
        mock_gethome.return_value = "/home/user"
        self.ex_eng.opt["bindhome"] = True
        status = self.ex_eng._get_bindhome()
        self.assertEqual(status, "/home/user")
        #
        mock_gethome.return_value = ""
        self.ex_eng.opt["bindhome"] = True
        status = self.ex_eng._get_bindhome()
        self.assertEqual(status, "")

    @patch('udocker.engine.base.os.path.exists')
    @patch('udocker.container.localrepo.LocalRepository')
    def test_18__create_mountpoint(self, mock_local, mock_exists):
        """Test ExecutionEngine()._create_mountpoint()."""
        mock_exists.return_value = False
        status = self.ex_eng._create_mountpoint("", "")
        self.assertFalse(status)

        mock_exists.return_value = True
        status = self.ex_eng._create_mountpoint("", "")
        self.assertTrue(status)

    @patch('udocker.engine.base.os.path.exists')
    @patch('udocker.container.localrepo.LocalRepository')
    def test_19__check_volumes(self, mock_local, mock_exists):
        """."""
        self.ex_eng.opt["vol"] = ()
        status = self.ex_eng._check_volumes()
        self.assertTrue(status)

        mock_exists.return_value = False
        status = self.ex_eng._check_volumes()
        self.assertTrue(status)

    @patch('udocker.container.localrepo.LocalRepository')
    def test_19__is_volume(self, mock_local):
        """."""
        self.ex_eng.opt["vol"] = ["/tmp"]
        status = self.ex_eng._is_volume("/tmp")
        self.assertTrue(status)

        self.ex_eng.opt["vol"] = [""]
        status = self.ex_eng._is_volume("/tmp")
        self.assertFalse(status)


if __name__ == '__main__':
    main()
