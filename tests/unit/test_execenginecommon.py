#!/usr/bin/env python
"""
udocker unit tests: ExecutionEngineCommon
"""

from unittest import TestCase, main
from unittest.mock import Mock, patch
from udocker.engine.base import ExecutionEngineCommon
from udocker.utils.uenv import Uenv
from udocker.config import Config


class ExecutionEngineCommonTestCase(TestCase):
    """Test ExecutionEngineCommon().
    Parent class for containers execution.
    """

    def setUp(self):
        Config().getconf()
        Config().conf['hostauth_list'] = ("/etc/passwd", "/etc/group")
        Config().conf['cmd'] = "/bin/bash"
        Config().conf['cpu_affinity_exec_tools'] = \
            (["numactl", "-C", "%s", "--", ], ["taskset", "-c", "%s", ])
        Config().conf['location'] = ""
        Config().conf['uid'] = 1000
        Config().conf['sysdirs_list'] = ["/", ]
        Config().conf['root_path'] = "/usr/sbin:/sbin:/usr/bin:/bin"
        Config().conf['user_path'] = "/usr/bin:/bin:/usr/local/bin"
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
        """Test01 ExecutionEngineCommon() constructor"""
        ex_eng = ExecutionEngineCommon(self.local, self.xmode)
        self.assertEqual(ex_eng.container_id, "")
        self.assertEqual(ex_eng.container_root, "")
        self.assertEqual(ex_eng.container_names, [])
        self.assertEqual(ex_eng.localrepo, self.local)
        self.assertEqual(ex_eng.exec_mode, self.xmode)
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
        self.assertEqual(ex_eng.opt["hostname"], "")
        self.assertEqual(ex_eng.opt["domain"], "")
        self.assertEqual(ex_eng.opt["volfrom"], [])

    @patch('udocker.engine.base.HostInfo.cmd_has_option')
    def test_02__has_option(self, mock_hinfocmd):
        """Test02 ExecutionEngineCommon()._has_option()."""
        mock_hinfocmd.return_value = True
        ex_eng = ExecutionEngineCommon(self.local, self.xmode)
        status = ex_eng._has_option("opt1")
        self.assertTrue(status)
        self.assertTrue(mock_hinfocmd.called)

    def test_03__get_portsmap(self):
        """Test03 ExecutionEngineCommon()._get_portsmap()."""
        ex_eng = ExecutionEngineCommon(self.local, self.xmode)
        ex_eng.opt["portsmap"] = ["1024:1024", "2048:2048"]
        status = ex_eng._get_portsmap()
        self.assertEqual(status, {1024: 1024, 2048: 2048})

    @patch('udocker.engine.base.Msg')
    @patch('udocker.engine.base.HostInfo')
    @patch.object(ExecutionEngineCommon, '_get_portsmap')
    def test_04__check_exposed_ports(self, mock_getports, mock_hinfo, mock_msg):
        """Test04 ExecutionEngineCommon()._check_exposed_ports()."""
        mock_msg.level = 0
        mock_getports.return_value = {22: 22, 2048: 2048}
        mock_hinfo.uid = 1000
        ex_eng = ExecutionEngineCommon(self.local, self.xmode)
        ex_eng.opt["portsexp"] = ("22", "2048/tcp")
        status = ex_eng._check_exposed_ports()
        self.assertFalse(status)

        mock_getports.return_value = {22: 22, 2048: 2048}
        mock_hinfo.uid = 0
        ex_eng = ExecutionEngineCommon(self.local, self.xmode)
        ex_eng.opt["portsexp"] = ("22", "2048/tcp")
        status = ex_eng._check_exposed_ports()
        self.assertTrue(status)

    @patch('udocker.engine.base.FileUtil.find_exec')
    def test_05__set_cpu_affinity(self, mock_findexec):
        """Test05 ExecutionEngineCommon()._set_cpu_affinity()."""
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

    @patch('udocker.engine.base.MountPoint')
    @patch('udocker.engine.base.FileUtil.isdir')
    def test_06__create_mountpoint(self, mock_isdir, mock_mpoint):
        """Test06 ExecutionEngineCommon()._create_mountpoint()."""
        hpath = "/bin"
        cpath = "/ROOT/bin"
        mock_isdir.return_value = False
        ex_eng = ExecutionEngineCommon(self.local, self.xmode)
        status = ex_eng._create_mountpoint(hpath, cpath, True)
        self.assertTrue(status)
        self.assertTrue(mock_isdir.called)

        hpath = "/bin"
        cpath = "/ROOT/bin"
        mock_isdir.return_value = True
        ex_eng = ExecutionEngineCommon(self.local, self.xmode)
        ex_eng.mountp = mock_mpoint
        ex_eng.mountp.create.return_value = True
        ex_eng.mountp.save.return_value = None
        status = ex_eng._create_mountpoint(hpath, cpath, True)
        self.assertTrue(status)
        self.assertTrue(ex_eng.mountp.save.called)

        hpath = "/bin"
        cpath = "/ROOT/bin"
        mock_isdir.return_value = True
        ex_eng = ExecutionEngineCommon(self.local, self.xmode)
        ex_eng.mountp = mock_mpoint
        ex_eng.mountp.create.return_value = False
        ex_eng.mountp.save.return_value = None
        status = ex_eng._create_mountpoint(hpath, cpath, True)
        self.assertFalse(status)

    @patch('udocker.engine.base.Msg')
    @patch.object(ExecutionEngineCommon, '_create_mountpoint')
    @patch('udocker.engine.base.os.path.exists')
    @patch('udocker.engine.base.Uvolume.split')
    def test_07__check_volumes(self, mock_uvolsplit, mock_exists,
                               mock_crmpoint, mock_msg):
        """Test07 ExecutionEngineCommon()._check_volumes()."""
        mock_msg.level = 0
        mock_uvolsplit.return_value = ("HOSTDIR", "CONTDIR")
        ex_eng = ExecutionEngineCommon(self.local, self.xmode)
        ex_eng.opt["vol"] = list()
        ex_eng.opt["vol"].append("HOSTDIR:CONTDIR")
        status = ex_eng._check_volumes()
        self.assertFalse(status)
        self.assertTrue(mock_uvolsplit.called)

        mock_uvolsplit.return_value = ("/HOSTDIR", "CONTDIR")
        ex_eng = ExecutionEngineCommon(self.local, self.xmode)
        ex_eng.opt["vol"] = list()
        ex_eng.opt["vol"].append("/HOSTDIR:CONTDIR")
        status = ex_eng._check_volumes()
        self.assertFalse(status)

        Config.conf['sysdirs_list'] = ["/HOSTDIR"]
        mock_exists.return_value = False
        mock_uvolsplit.return_value = ("/HOSTDIR", "/CONTDIR")
        mock_crmpoint.return_value = False
        ex_eng = ExecutionEngineCommon(self.local, self.xmode)
        ex_eng.opt["vol"] = list()
        ex_eng.opt["vol"].append("/HOSTDIR:/CONTDIR")
        status = ex_eng._check_volumes()
        self.assertTrue(status)
        self.assertEqual(ex_eng.opt["vol"], list())
        self.assertTrue(mock_exists.called)

        Config.conf['sysdirs_list'] = ["/sys"]
        mock_exists.return_value = False
        mock_uvolsplit.return_value = ("/HOSTDIR", "/CONTDIR")
        mock_crmpoint.return_value = False
        ex_eng = ExecutionEngineCommon(self.local, self.xmode)
        ex_eng.opt["vol"] = list()
        ex_eng.opt["vol"].append("/HOSTDIR:/CONTDIR")
        status = ex_eng._check_volumes()
        self.assertFalse(status)
        self.assertTrue(mock_exists.called)

        Config.conf['sysdirs_list'] = ["/sys"]
        mock_exists.return_value = True
        mock_uvolsplit.return_value = ("/HOSTDIR", "/CONTDIR")
        mock_crmpoint.return_value = True
        ex_eng = ExecutionEngineCommon(self.local, self.xmode)
        ex_eng.opt["vol"] = list()
        ex_eng.opt["vol"].append("/HOSTDIR:/CONTDIR")
        status = ex_eng._check_volumes()
        self.assertTrue(status)

    @patch('udocker.engine.base.NixAuthentication.get_home')
    def test_08__get_bindhome(self, mock_gethome):
        """Test08 ExecutionEngineCommon()._get_bindhome()."""
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
        self.assertTrue(mock_gethome.called)

    @patch('udocker.engine.base.Uvolume.cleanpath')
    @patch('udocker.engine.base.Uvolume.split')
    def test_09__is_volume(self, mock_uvolsplit, mock_uvolclean):
        """Test09 ExecutionEngineCommon()._is_volume()."""
        ex_eng = ExecutionEngineCommon(self.local, self.xmode)
        ex_eng.opt["vol"] = list()
        status = ex_eng._is_volume("/tmp")
        self.assertEqual(status, "")

        mock_uvolsplit.return_value = ("/tmp", "/CONTDIR")
        mock_uvolclean.return_value = "/tmp"
        ex_eng = ExecutionEngineCommon(self.local, self.xmode)
        ex_eng.opt["vol"] = list()
        ex_eng.opt["vol"].append("/tmp:/CONTDIR")
        status = ex_eng._is_volume("/tmp")
        self.assertEqual(status, "/CONTDIR")

    @patch('udocker.engine.base.Uvolume.cleanpath')
    @patch('udocker.engine.base.Uvolume.split')
    def test_10__is_mountpoint(self, mock_uvolsplit, mock_uvolclean):
        """Test10 ExecutionEngineCommon()._is_mountpoint()."""
        ex_eng = ExecutionEngineCommon(self.local, self.xmode)
        ex_eng.opt["vol"] = list()
        status = ex_eng._is_mountpoint("/tmp")
        self.assertEqual(status, "")

        mock_uvolsplit.return_value = ("/tmp", "/CONTDIR")
        mock_uvolclean.return_value = "/CONTDIR"
        ex_eng = ExecutionEngineCommon(self.local, self.xmode)
        ex_eng.opt["vol"] = list()
        ex_eng.opt["vol"].append("/tmp:/CONTDIR")
        status = ex_eng._is_mountpoint("/tmp")
        self.assertEqual(status, "/tmp")

    @patch.object(ExecutionEngineCommon, '_check_volumes')
    @patch.object(ExecutionEngineCommon, '_get_bindhome')
    def test_11__set_volume_bindings(self, mock_bindhome, mock_chkvol):
        """Test11 ExecutionEngineCommon()._set_volume_bindings()."""
        Config.conf['sysdirs_list'] = ["/sys"]
        Config.conf['dri_list'] = ["/dri"]
        mock_bindhome.return_value = "/home/user"
        mock_chkvol.return_value = False
        ex_eng = ExecutionEngineCommon(self.local, self.xmode)
        ex_eng.opt["vol"] = list()
        ex_eng.opt["hostauth"] = "/etc/passwd"
        ex_eng.opt["nosysdirs"] = False
        ex_eng.opt["dri"] = True
        ex_eng.opt["novol"] = list()
        status = ex_eng._set_volume_bindings()
        self.assertFalse(status)
        self.assertTrue(mock_bindhome.called)
        self.assertTrue(mock_chkvol.called)

        Config.conf['sysdirs_list'] = ["/sys"]
        Config.conf['dri_list'] = ["/dri"]
        mock_bindhome.return_value = "/home/user"
        mock_chkvol.return_value = True
        ex_eng = ExecutionEngineCommon(self.local, self.xmode)
        ex_eng.opt["vol"] = list()
        ex_eng.opt["hostauth"] = "/etc/passwd"
        ex_eng.opt["nosysdirs"] = False
        ex_eng.opt["dri"] = True
        ex_eng.opt["novol"] = ["/sys", "/dri", "/home/user"]
        status = ex_eng._set_volume_bindings()
        self.assertTrue(status)

    @patch('udocker.engine.base.Msg')
    @patch('udocker.engine.base.Uenv')
    @patch('udocker.engine.base.os.path.isdir')
    @patch('udocker.engine.base.FileUtil.cont2host')
    def test_12__check_paths(self, mock_fuc2h, mock_isdir, mock_uenv,
                             mock_msg):
        """Test12 ExecutionEngineCommon()._check_paths()."""
        Config.conf['root_path'] = "/sbin"
        Config.conf['user_path'] = "/bin"
        mock_msg.level = 0
        mock_fuc2h.return_value = "/container/bin"
        mock_isdir.return_value = False
        ex_eng = ExecutionEngineCommon(self.local, self.xmode)
        ex_eng.opt["uid"] = "0"
        ex_eng.opt["cwd"] = ""
        ex_eng.opt["home"] = "/home/user"
        ex_eng.opt["env"] = mock_uenv
        ex_eng.opt["env"].getenv.return_value = "/sbin"
        status = ex_eng._check_paths()
        self.assertFalse(status)
        self.assertEqual(ex_eng.opt["cwd"], ex_eng.opt["home"])

        Config.conf['root_path'] = "/sbin"
        Config.conf['user_path'] = "/bin"
        mock_fuc2h.return_value = "/container/bin"
        mock_isdir.return_value = True
        ex_eng = ExecutionEngineCommon(self.local, self.xmode)
        ex_eng.opt["uid"] = "0"
        ex_eng.opt["cwd"] = "/home/user"
        ex_eng.opt["home"] = "/home/user"
        ex_eng.opt["env"] = mock_uenv
        ex_eng.opt["env"].getenv.return_value = ""
        status = ex_eng._check_paths()
        self.assertTrue(status)
        self.assertTrue(mock_fuc2h.called)
        self.assertTrue(mock_isdir.called)

    @patch('udocker.engine.base.Msg')
    @patch('udocker.engine.base.FileUtil.find_exec')
    @patch('udocker.engine.base.Uenv')
    def test_13__check_executable(self, mock_uenv, mock_fufindexe, mock_msg):
        """Test13 ExecutionEngineCommon()._check_executable()."""
        Config.conf['cmd'] = "/bin/ls"
        mock_msg.level = 0
        mock_fufindexe.return_value = ""
        ex_eng = ExecutionEngineCommon(self.local, self.xmode)
        ex_eng.opt["env"] = mock_uenv
        ex_eng.opt["env"].getenv.return_value = ""
        ex_eng.opt["entryp"] = "/bin/ls -a -l"
        ex_eng.container_root = "/containers/123/ROOT"
        status = ex_eng._check_executable()
        self.assertEqual(status, "")
        self.assertTrue(mock_fufindexe.called)

        Config.conf['cmd'] = "/bin/ls"
        mock_fufindexe.return_value = "/bin/ls"
        ex_eng = ExecutionEngineCommon(self.local, self.xmode)
        ex_eng.opt["env"] = mock_uenv
        ex_eng.opt["env"].getenv.return_value = ""
        ex_eng.opt["entryp"] = "/bin/ls -a -l"
        ex_eng.container_root = "/containers/123/ROOT"
        status = ex_eng._check_executable()
        self.assertEqual(status, "/containers/123/ROOT//bin/ls")

        Config.conf['cmd'] = "/bin/ls"
        mock_fufindexe.return_value = "/bin/ls"
        ex_eng = ExecutionEngineCommon(self.local, self.xmode)
        ex_eng.opt["env"] = mock_uenv
        ex_eng.opt["env"].getenv.return_value = ""
        ex_eng.opt["entryp"] = ["/bin/ls", "-a", "-l"]
        ex_eng.container_root = "/containers/123/ROOT"
        status = ex_eng._check_executable()
        self.assertEqual(status, "/containers/123/ROOT//bin/ls")

    @patch('udocker.engine.base.ContainerStructure.get_container_meta')
    @patch('udocker.engine.base.ContainerStructure.get_container_attr')
    def test_14__run_load_metadata(self, mock_attr, mock_meta):
        """Test14 ExecutionEngineCommon()._run_load_metadata()."""
        Config().conf['location'] = "/tmp/container"
        ex_eng = ExecutionEngineCommon(self.local, self.xmode)
        status = ex_eng._run_load_metadata("123")
        self.assertEqual(status, ("", []))

        Config().conf['location'] = ""
        mock_attr.return_value = (None, None)
        ex_eng = ExecutionEngineCommon(self.local, self.xmode)
        status = ex_eng._run_load_metadata("123")
        self.assertEqual(status, (None, None))
        self.assertTrue(mock_attr.called)

        Config().conf['location'] = ""
        mock_attr.return_value = ("/x", [])
        ex_eng = ExecutionEngineCommon(self.local, self.xmode)
        ex_eng.opt["nometa"] = True
        status = ex_eng._run_load_metadata("123")
        self.assertEqual(status, ("/x", []))

        Config().conf['location'] = ""
        mock_attr.return_value = ("/x", [])
        mock_meta.side_effects = ["user1", "cont/ROOT", "host1", "mydomain",
                                  "ls", "/bin/sh", "vol1", "8443", None]
        ex_eng = ExecutionEngineCommon(self.local, self.xmode)
        ex_eng.opt["nometa"] = False
        ex_eng.opt["portsexp"] = list()
        status = ex_eng._run_load_metadata("123")
        self.assertEqual(status, ("/x", []))
        self.assertTrue(mock_meta.call_count, 9)

    @patch('udocker.engine.base.os.path.isfile')
    @patch('udocker.engine.base.os.path.islink')
    @patch('udocker.engine.base.FileBind')
    @patch.object(ExecutionEngineCommon, '_is_mountpoint')
    def test_15__select_auth_files(self, mock_ismpoint, mock_fbind, mock_islink,
                                   mock_isfile):
        """Test15 ExecutionEngineCommon()._select_auth_files()."""
        resp = "/fbdir/#etc#passwd"
        resg = "/fbdir/#etc#group"
        mock_fbind.return_value.orig_dir = "/fbdir"
        mock_islink.side_effect = [True, True]
        mock_isfile.side_effect = [True, True]
        mock_ismpoint.side_effect = ["", "", "", ""]
        ex_eng = ExecutionEngineCommon(self.local, self.xmode)
        status = ex_eng._select_auth_files()
        self.assertTrue(mock_islink.call_count, 2)
        self.assertTrue(mock_isfile.call_count, 2)
        self.assertTrue(mock_ismpoint.call_count, 2)
        # self.assertEqual(status, resp)

        resp = "/etc/passwd"
        resg = "/etc/group"
        mock_fbind.orig_dir.side_effect = ["/fbdir", "/fbdir"]
        mock_islink.side_effect = [False, False]
        mock_isfile.side_effect = [False, False]
        mock_ismpoint.side_effect = ["", "", "", ""]
        ex_eng = ExecutionEngineCommon(self.local, self.xmode)
        status = ex_eng._select_auth_files()
        self.assertEqual(status, (resp, resg))

        resp = "/d/etc/passwd"
        resg = "/d/etc/group"
        mock_fbind.orig_dir.side_effect = ["/fbdir", "/fbdir"]
        mock_islink.side_effect = [False, False]
        mock_isfile.side_effect = [False, False]
        mock_ismpoint.side_effect = ["/d/etc/passwd", "/d/etc/passwd",
                                     "/d/etc/group", "/d/etc/group"]
        ex_eng = ExecutionEngineCommon(self.local, self.xmode)
        status = ex_eng._select_auth_files()
        self.assertTrue(mock_ismpoint.call_count, 4)
        self.assertEqual(status, (resp, resg))

    def test_16__validate_user_str(self):
        """Test16 ExecutionEngineCommon()._validate_user_str()."""
        userstr = ""
        ex_eng = ExecutionEngineCommon(self.local, self.xmode)
        status = ex_eng._validate_user_str(userstr)
        self.assertEqual(status, dict())

        userstr = "user1"
        res = {"user": userstr}
        ex_eng = ExecutionEngineCommon(self.local, self.xmode)
        status = ex_eng._validate_user_str(userstr)
        self.assertEqual(status, res)

        userstr = "1000:1000"
        res = {"uid": "1000", "gid": "1000"}
        ex_eng = ExecutionEngineCommon(self.local, self.xmode)
        status = ex_eng._validate_user_str(userstr)
        self.assertEqual(status, res)

    def test_17__user_from_str(self):
        """Test17 ExecutionEngineCommon()._user_from_str()."""
        userstr = ""
        ex_eng = ExecutionEngineCommon(self.local, self.xmode)
        status = ex_eng._user_from_str(userstr)
        self.assertEqual(status, (False, dict()))

        userstr = "user1"
        res = {"user": userstr}
        str_exmode = 'udocker.helper.nixauth.NixAuthentication'
        nixauth = patch(str_exmode)
        auth = nixauth.start()
        mock_auth = Mock()
        auth.return_value = mock_auth
        ex_eng = ExecutionEngineCommon(self.local, self.xmode)
        ex_eng.opt["hostauth"] = True
        auth.get_user.return_value = ("user1", "1000", "1000", "usr",
                                      "/home/user", "/bin/bash")
        status = ex_eng._user_from_str(userstr, host_auth=auth)
        self.assertEqual(status, (True, res))
        auth = nixauth.stop()

        userstr = "user1"
        res = {"user": userstr}
        str_exmode = 'udocker.helper.nixauth.NixAuthentication'
        nixauth = patch(str_exmode)
        auth = nixauth.start()
        mock_auth = Mock()
        auth.return_value = mock_auth
        ex_eng = ExecutionEngineCommon(self.local, self.xmode)
        ex_eng.opt["hostauth"] = False
        auth.get_user.return_value = ("user1", "1000", "1000", "usr",
                                      "/home/user", "/bin/bash")
        status = ex_eng._user_from_str(userstr, container_auth=auth)
        self.assertEqual(status, (True, res))
        auth = nixauth.stop()

        userstr = "1000:1000"
        res = {"uid": "1000", "gid": "1000"}
        str_exmode = 'udocker.helper.nixauth.NixAuthentication'
        nixauth = patch(str_exmode)
        auth = nixauth.start()
        mock_auth = Mock()
        auth.return_value = mock_auth
        ex_eng = ExecutionEngineCommon(self.local, self.xmode)
        ex_eng.opt["hostauth"] = True
        auth.get_user.return_value = ("user1", "1000", "1000", "usr",
                                      "/home/user", "/bin/bash")
        status = ex_eng._user_from_str(userstr, host_auth=auth)
        self.assertEqual(status, (True, res))
        auth = nixauth.stop()

    @patch('udocker.engine.base.Msg')
    @patch('udocker.engine.base.HostInfo')
    @patch('udocker.engine.base.NixAuthentication')
    @patch.object(ExecutionEngineCommon, '_create_user')
    @patch.object(ExecutionEngineCommon, '_is_mountpoint')
    @patch.object(ExecutionEngineCommon, '_user_from_str')
    @patch.object(ExecutionEngineCommon, '_select_auth_files')
    def test_18__setup_container_user(self, mock_selauth, mock_ustr,
                                      mock_ismpoint, mock_cruser, mock_auth,
                                      mock_hinfo, mock_msg):
        """Test18 ExecutionEngineCommon()._setup_container_user()."""
        user = "invuser"
        mock_msg.level = 0
        mock_selauth.return_value = ("/etc/passwd", "/etc/group")
        mock_ustr.return_value = (False, {"uid": "100", "gid": "50"})
        mock_auth.side_effect = [None, None]
        ex_eng = ExecutionEngineCommon(self.local, self.xmode)
        status = ex_eng._setup_container_user(user)
        self.assertFalse(status)

        user = ""
        mock_selauth.return_value = ("/etc/passwd", "/etc/group")
        mock_ustr.return_value = (True, {"uid": "0", "gid": "0"})
        mock_auth.side_effect = [None, None]
        mock_hinfo.return_value.username.return_value = "root"
        mock_hinfo.uid = 0
        mock_hinfo.gid = 0
        mock_ismpoint.side_effect = [True, True]
        ex_eng = ExecutionEngineCommon(self.local, self.xmode)
        status = ex_eng._setup_container_user(user)
        self.assertTrue(status)

        user = ""
        mock_selauth.return_value = ("/etc/passwd", "/etc/group")
        mock_ustr.return_value = (True, {"uid": "0", "gid": "0"})
        mock_auth.side_effect = [None, None]
        mock_hinfo.return_value.username.return_value = "root"
        mock_hinfo.uid = 0
        mock_hinfo.gid = 0
        mock_ismpoint.side_effect = [False, False]
        mock_cruser.return_value = None
        ex_eng = ExecutionEngineCommon(self.local, self.xmode)
        ex_eng.opt["user"] = ""
        ex_eng.opt["hostauth"] = True
        status = ex_eng._setup_container_user(user)
        self.assertFalse(status)
        self.assertFalse(mock_cruser.called)

        user = ""
        mock_selauth.return_value = ("/etc/passwd", "/etc/group")
        mock_ustr.return_value = (True, {"uid": "0", "gid": "0"})
        mock_auth.side_effect = [None, None]
        mock_hinfo.return_value.username.return_value = "root"
        mock_hinfo.uid = 0
        mock_hinfo.gid = 0
        mock_ismpoint.side_effect = [False, False]
        mock_cruser.return_value = None
        ex_eng = ExecutionEngineCommon(self.local, self.xmode)
        ex_eng.opt["user"] = ""
        ex_eng.opt["hostauth"] = False
        ex_eng.opt["containerauth"] = False
        status = ex_eng._setup_container_user(user)
        self.assertTrue(status)
        self.assertTrue(mock_cruser.called)

    @patch('udocker.engine.base.Msg')
    @patch('udocker.engine.base.HostInfo')
    @patch('udocker.engine.base.NixAuthentication')
    @patch.object(ExecutionEngineCommon, '_create_user')
    @patch.object(ExecutionEngineCommon, '_is_mountpoint')
    @patch.object(ExecutionEngineCommon, '_user_from_str')
    @patch.object(ExecutionEngineCommon, '_select_auth_files')
    def test_19__set_cont_user_noroot(self, mock_selauth, mock_ustr,
                                      mock_ismpoint, mock_cruser, mock_auth,
                                      mock_hinfo, mock_msg):
        """Test19 ExecutionEngineCommon()._setup_container_user_noroot()."""
        user = "invuser"
        mock_msg.level = 0
        mock_selauth.return_value = ("/etc/passwd", "/etc/group")
        mock_ustr.return_value = (False, {"uid": "100", "gid": "50"})
        mock_auth.side_effect = [None, None]
        ex_eng = ExecutionEngineCommon(self.local, self.xmode)
        status = ex_eng._setup_container_user_noroot(user)
        self.assertFalse(status)

        user = ""
        mock_selauth.return_value = ("/etc/passwd", "/etc/group")
        mock_ustr.return_value = (True, {"uid": "1000", "gid": "1000"})
        mock_auth.side_effect = [None, None]
        mock_hinfo.return_value.username.return_value = "u1"
        mock_hinfo.uid = 0
        mock_hinfo.gid = 0
        mock_ismpoint.side_effect = [True, True]
        ex_eng = ExecutionEngineCommon(self.local, self.xmode)
        status = ex_eng._setup_container_user_noroot(user)
        self.assertTrue(status)

        user = ""
        mock_selauth.return_value = ("/etc/passwd", "/etc/group")
        mock_ustr.return_value = (True, {"uid": "1000", "gid": "1000"})
        mock_auth.side_effect = [None, None]
        mock_hinfo.return_value.username.return_value = "u1"
        mock_hinfo.uid = 0
        mock_hinfo.gid = 0
        mock_ismpoint.side_effect = [False, False]
        mock_cruser.return_value = None
        ex_eng = ExecutionEngineCommon(self.local, self.xmode)
        ex_eng.opt["user"] = ""
        ex_eng.opt["hostauth"] = True
        status = ex_eng._setup_container_user_noroot(user)
        self.assertFalse(status)
        self.assertFalse(mock_cruser.called)

        user = ""
        mock_selauth.return_value = ("/etc/passwd", "/etc/group")
        mock_ustr.return_value = (True, {"uid": "1000", "gid": "1000"})
        mock_auth.side_effect = [None, None]
        mock_hinfo.return_value.username.return_value = "u1"
        mock_hinfo.uid = 0
        mock_hinfo.gid = 0
        mock_ismpoint.side_effect = [False, False]
        mock_cruser.return_value = None
        ex_eng = ExecutionEngineCommon(self.local, self.xmode)
        ex_eng.opt["user"] = ""
        ex_eng.opt["hostauth"] = False
        ex_eng.opt["containerauth"] = False
        status = ex_eng._setup_container_user_noroot(user)
        self.assertTrue(status)
        self.assertTrue(mock_cruser.called)

    @patch('udocker.engine.base.HostInfo')
    @patch('udocker.engine.base.NixAuthentication')
    def test_20__fill_user(self, mock_auth, mock_hinfo):
        """Test20 ExecutionEngineCommon()._fill_user()."""
        mock_auth.return_value.get_home.return_value = "/home/u1"
        mock_hinfo.uid = 1000
        mock_hinfo.gid = 1000
        ex_eng = ExecutionEngineCommon(self.local, self.xmode)
        ex_eng.opt["user"] = ""
        ex_eng.opt["uid"] = ""
        ex_eng.opt["gid"] = ""
        ex_eng.opt["bindhome"] = True
        ex_eng.opt["shell"] = ""
        ex_eng.opt["gecos"] = ""
        ex_eng._fill_user()
        self.assertEqual(ex_eng.opt["user"], "udoc1000")
        self.assertEqual(ex_eng.opt["uid"], "1000")
        self.assertEqual(ex_eng.opt["gid"], "1000")
        self.assertEqual(ex_eng.opt["shell"], "/bin/sh")
        self.assertEqual(ex_eng.opt["gecos"], "*UDOCKER*")

    @patch.object(ExecutionEngineCommon, '_fill_user')
    @patch('udocker.engine.base.os.getgroups')
    @patch('udocker.engine.base.FileUtil.copyto')
    @patch('udocker.engine.base.FileUtil.mktmp')
    @patch('udocker.engine.base.FileUtil.umask')
    @patch('udocker.engine.base.NixAuthentication')
    def test_21__create_user(self, mock_nix, mock_umask, mock_mktmp,
                             mock_cpto, mock_getgrp, mock_fillu):
        """Test21 ExecutionEngineCommon()._create_user()."""
        cont_auth = mock_nix
        host_auth = mock_nix
        cont_auth.passwd_file.return_value = "/c/etc/passwd"
        cont_auth.group_file.return_value = "/c/etc/grpup"
        ex_eng = ExecutionEngineCommon(self.local, self.xmode)
        ex_eng.opt["containerauth"] = True
        status = ex_eng._create_user(cont_auth, host_auth)
        self.assertTrue(status)
        self.assertFalse(ex_eng.opt["hostauth"])

        cont_auth = mock_nix
        host_auth = mock_nix
        res = ("/tmp/passwd:/etc/passwd","/tmp/group:/etc/group")
        cont_auth.passwd_file.return_value = "/c/etc/passwd"
        cont_auth.group_file.return_value = "/c/etc/group"
        mock_umask.side_effect = [None, None]
        mock_mktmp.side_effect = ["/tmp/passwd", "/tmp/group"]
        mock_cpto.side_effect = [None, None]
        ex_eng = ExecutionEngineCommon(self.local, self.xmode)
        ex_eng.opt["containerauth"] = False
        ex_eng.opt["hostauth"] = True
        status = ex_eng._create_user(cont_auth, host_auth)
        self.assertTrue(status)
        self.assertTrue(ex_eng.opt["hostauth"])
        self.assertEqual(ex_eng.hostauth_list, res)

        cont_auth = mock_nix
        host_auth = mock_nix
        res = ("/tmp/passwd:/etc/passwd","/tmp/group:/etc/group")
        cont_auth.passwd_file.return_value = "/c/etc/passwd"
        cont_auth.group_file.return_value = "/c/etc/group"
        mock_umask.side_effect = [None, None]
        mock_mktmp.side_effect = ["/tmp/passwd", "/tmp/group"]
        mock_cpto.side_effect = [None, None]
        mock_fillu.return_value = None
        mock_nix.add_user.return_value = None
        host_auth.get_group.return_value = ("", "x1", "x2")
        mock_nix.add_group.return_value = None
        mock_getgrp.return_value = [1000]
        ex_eng = ExecutionEngineCommon(self.local, self.xmode)
        ex_eng.opt["containerauth"] = False
        ex_eng.opt["hostauth"] = False
        status = ex_eng._create_user(cont_auth, host_auth)
        self.assertTrue(status)
        self.assertTrue(ex_eng.opt["hostauth"])
        self.assertEqual(ex_eng.hostauth_list, res)

    @patch('udocker.engine.base.Msg')
    @patch('udocker.engine.base.os.path.basename')
    def test_22__run_banner(self, mock_base, mock_msg):
        """Test22 ExecutionEngineCommon()._run_banner()."""
        mock_base.return_value = "ls"
        ex_eng = ExecutionEngineCommon(self.local, self.xmode)
        ex_eng._run_banner("/bin/bash")
        ex_eng.container_id = "CONTAINERID"
        self.assertTrue(mock_msg.called)
        self.assertTrue(mock_base.called_once_with("/bin/bash"))

    @patch('udocker.engine.base.os.environ.copy')
    @patch('udocker.engine.base.os.environ')
    def test_23__run_env_cleanup_dict(self, mock_osenv, mock_osenvcp):
        """Test23 ExecutionEngineCommon()._run_env_cleanup_dict()."""
        res = {'HOME': '/', }
        Config.conf['valid_host_env'] = ("HOME",)
        Config.conf['invalid_host_env'] = ("USERNAME",)
        mock_osenvcp.return_value = {'HOME': '/', 'USERNAME': 'user', }
        mock_osenv.return_value = {'HOME': '/', }
        ex_eng = ExecutionEngineCommon(self.local, self.xmode)
        ex_eng.opt["hostenv"] = {'HOME': '/', }
        ex_eng._run_env_cleanup_dict()
        self.assertEqual(mock_osenv.return_value, res)

    @patch('udocker.engine.base.os.environ')
    def test_24__run_env_cleanup_list(self, mock_osenv):
        """Test24 ExecutionEngineCommon()._run_env_cleanup_list()."""
        Config.conf['valid_host_env'] = ("HOME",)
        Config.conf['invalid_host_env'] = ("USERNAME",)
        mock_osenv.return_value = {'HOME': '/', 'USERNAME': 'user', }
        ex_eng = ExecutionEngineCommon(self.local, self.xmode)
        ex_eng.opt["hostenv"] = "HOME"
        ex_eng.opt["env"] = Uenv()
        ex_eng._run_env_cleanup_list()
        self.assertEqual(ex_eng.opt["env"].env, dict())

    @patch('udocker.engine.base.HostInfo.username')
    def test_25__run_env_set(self, mock_hiuname):
        """Test25 ExecutionEngineCommon()._run_env_set()."""
        mock_hiuname.return_value = "user1"
        ex_eng = ExecutionEngineCommon(self.local, self.xmode)
        ex_eng.opt["home"] = "/"
        ex_eng.opt["user"] = "user1"
        ex_eng.opt["uid"] = "1000"
        ex_eng.container_root = "/croot"
        ex_eng.container_id = "2717add4-e6f6-397c-9019-74fa67be439f"
        ex_eng.container_names = ['cna[]me', ]
        self.xmode.get_mode.return_value = "P1"
        ex_eng._run_env_set()
        self.assertEqual(ex_eng.opt["env"].env["USER"], "user1")
        self.assertEqual(ex_eng.opt["env"].env["LOGNAME"], "user1")
        self.assertEqual(ex_eng.opt["env"].env["USERNAME"], "user1")
        self.assertEqual(ex_eng.opt["env"].env["SHLVL"], "0")

    @patch('udocker.engine.base.FileUtil.getdata')
    def test_26__run_env_cmdoptions(self, mock_getdata):
        """Test26 ExecutionEngineCommon()._run_env_cmdoptions()."""
        mock_getdata.return_value = "USER=user1\nSHLVL=0"
        ex_eng = ExecutionEngineCommon(self.local, self.xmode)
        ex_eng.opt["envfile"] = ["/dir/env"]
        ex_eng.opt["env"] = Uenv()
        ex_eng._run_env_cmdoptions()
        self.assertEqual(ex_eng.opt["env"].env["USER"], "user1")

    @patch('udocker.engine.base.MountPoint')
    @patch.object(ExecutionEngineCommon, '_check_exposed_ports')
    @patch.object(ExecutionEngineCommon, '_set_volume_bindings')
    @patch.object(ExecutionEngineCommon, '_check_executable')
    @patch.object(ExecutionEngineCommon, '_check_paths')
    @patch.object(ExecutionEngineCommon, '_setup_container_user')
    @patch.object(ExecutionEngineCommon, '_run_env_cmdoptions')
    @patch.object(ExecutionEngineCommon, '_run_load_metadata')
    def test_27__run_init(self, mock_loadmeta, mock_envcmd,
                          mock_setupuser,
                          mock_chkpaths, mock_chkexec, mock_setvol,
                          mock_chkports, mock_mpoint):
        """Test27 ExecutionEngineCommon()._run_init()."""
        # mock_getcname.return_value = "cname"
        Config.conf['location'] = ""
        mock_loadmeta.return_value = ("", "dummy",)
        ex_eng = ExecutionEngineCommon(self.local, self.xmode)
        status = ex_eng._run_init("2717add4-e6f6-397c-9019-74fa67be439f")
        self.assertEqual(status, "")
        self.assertTrue(mock_loadmeta.called)

        Config.conf['location'] = "/container_dir"
        mock_loadmeta.return_value = ("/container_dir", "dummy",)
        mock_envcmd.return_value = None
        mock_chkports.return_value = None
        mock_setupuser.return_value = False
        self.local.get_container_name.return_value = "cont_name"
        ex_eng = ExecutionEngineCommon(self.local, self.xmode)
        status = ex_eng._run_init("2717add4-e6f6-397c-9019-74fa67be439f")
        self.assertEqual(status, "")
        self.assertTrue(mock_envcmd.called)
        self.assertTrue(self.local.get_container_name.called)
        self.assertTrue(mock_chkports.called)

        Config.conf['location'] = "/container_dir"
        mock_loadmeta.return_value = ("/container_dir", "dummy",)
        mock_envcmd.return_value = None
        mock_chkports.return_value = None
        mock_setupuser.return_value = True
        mock_mpoint.return_value = None
        mock_setvol.return_value = False
        self.local.get_container_name.return_value = "cont_name"
        ex_eng = ExecutionEngineCommon(self.local, self.xmode)
        status = ex_eng._run_init("2717add4-e6f6-397c-9019-74fa67be439f")
        self.assertEqual(status, "")
        self.assertTrue(mock_chkports.called)
        self.assertTrue(mock_mpoint.called)
        self.assertTrue(mock_setvol.called)

        Config.conf['location'] = "/container_dir"
        mock_loadmeta.return_value = ("/container_dir", "dummy",)
        mock_envcmd.return_value = None
        mock_chkports.return_value = None
        mock_setupuser.return_value = True
        mock_mpoint.return_value = None
        mock_setvol.return_value = True
        mock_chkpaths.return_value = False
        self.local.get_container_name.return_value = "cont_name"
        ex_eng = ExecutionEngineCommon(self.local, self.xmode)
        status = ex_eng._run_init("2717add4-e6f6-397c-9019-74fa67be439f")
        self.assertEqual(status, "")
        self.assertTrue(mock_chkpaths.called)

        Config.conf['location'] = "/container_dir"
        mock_loadmeta.return_value = ("/container_dir", "dummy",)
        mock_envcmd.return_value = None
        mock_chkports.return_value = None
        mock_setupuser.return_value = True
        mock_mpoint.return_value = None
        mock_setvol.return_value = True
        mock_chkpaths.return_value = True
        mock_chkexec.return_value = "/bin/ls"
        self.local.get_container_name.return_value = "cont_name"
        ex_eng = ExecutionEngineCommon(self.local, self.xmode)
        status = ex_eng._run_init("2717add4-e6f6-397c-9019-74fa67be439f")
        self.assertEqual(status, "/bin/ls")
        self.assertTrue(mock_chkexec.called)


if __name__ == '__main__':
    main()
