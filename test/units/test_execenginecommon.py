#!/usr/bin/env python
"""
udocker unit tests: ExecutionEngineCommon
"""
import random
import pytest

from udocker.config import Config
from udocker.engine.base import ExecutionEngineCommon
from contextlib import nullcontext as does_not_raise


@pytest.fixture
def container_id():
    return str(random.randint(1, 1000))


@pytest.fixture
def localrepo(mocker, container_id):
    return mocker.patch('udocker.container.localrepo.LocalRepository')


@pytest.fixture
def engine(localrepo, container_id, xmode):
    mocker_exec_mode = ExecutionEngineCommon(localrepo, xmode)
    return mocker_exec_mode


@pytest.fixture
def logger(mocker):
    return mocker.patch('udocker.engine.base.LOG')


@pytest.fixture
def mocker_hostinfo(mocker):
    return mocker.patch('udocker.engine.base.HostInfo')


@pytest.fixture
def mocker_fileutil(mocker):
    return mocker.patch('udocker.engine.base.FileUtil')


# class ExecutionEngineCommonTestCase(TestCase):
#     """Test ExecutionEngineCommon().
#     Parent class for containers execution.
#     """
#
#     def setUp(self):
#         LOG.setLevel(100)
#         Config().getconf()
#         Config().conf['hostauth_list'] = ("/etc/passwd", "/etc/group")
#         Config().conf['cmd'] = "/bin/bash"
#         Config().conf['cpu_affinity_exec_tools'] = (["numactl", "-C", "%s", "--", ],
#                                                     ["taskset", "-c", "%s", ])
#         Config().conf['location'] = ""
#         Config().conf['uid'] = 1000
#         Config().conf['sysdirs_list'] = ["/", ]
#         Config().conf['root_path'] = "/usr/sbin:/sbin:/usr/bin:/bin"
#         Config().conf['user_path'] = "/usr/bin:/bin:/usr/local/bin"
#         str_local = 'udocker.container.localrepo.LocalRepository'
#         self.lrepo = patch(str_local)
#         self.local = self.lrepo.start()
#         self.mock_lrepo = Mock()
#         self.local.return_value = self.mock_lrepo
#
#         str_exmode = 'udocker.engine.execmode.ExecutionMode'
#         self.execmode = patch(str_exmode)
#         self.xmode = self.execmode.start()
#         self.mock_execmode = Mock()
#         self.xmode.return_value = self.mock_execmode
#
#     def tearDown(self):
#         self.lrepo.stop()
#         self.execmode.stop()
@pytest.mark.parametrize("opts", [
    {'nometa': False, 'nosysdirs': False, 'dri': False, 'bindhome': False, 'hostenv': False, 'hostauth': False,
     'novol': [], 'vol': [], 'cpuset': '', 'user': '', 'cwd': '', 'entryp': '', 'hostname': '', 'domain': '',
     'volfrom': [], 'portsmap': [], 'portsexp': [], 'portsexp': [], 'devices': [], 'nobanner': False}
])
@pytest.mark.parametrize("xmode", ["P1", "P2", "F1", "F2"])
def test_01_init(engine, localrepo, container_id, xmode, opts):
    """Test01 ExecutionEngineCommon() constructor"""
    assert engine.container_id == ""
    assert engine.container_root == ""
    assert engine.container_names == []
    assert engine.localrepo == localrepo
    assert engine.exec_mode == xmode
    assert opts.items() <= engine.opt.items()


@pytest.mark.parametrize("has_option", [True, False])
@pytest.mark.parametrize("xmode", ["P1", "P2", "F1", "F2"])
def test_02__has_option(mocker, engine, xmode, has_option):
    """Test02 ExecutionEngineCommon()._has_option()."""
    mock_has_option = mocker.patch('udocker.engine.base.HostInfo.cmd_has_option', return_value=has_option)
    assert engine._has_option("opt1") == has_option
    assert mock_has_option.called


@pytest.mark.parametrize("by_container", [True, False])
@pytest.mark.parametrize("portsmap,error,expected", [
    (['1024:1024', '2048:2048'], (does_not_raise(), does_not_raise()), {1024: 1024, 2048: 2048}),
    ([':1024', '2048:2048'], (pytest.raises(IndexError), does_not_raise()), {1024: 1024, 2048: 2048}),
    (['INVALID', '2048:2048', '1024:1024'], (pytest.raises(IndexError), does_not_raise()), {1024: 1024, 2048: 2048}),
    (['INVALID', 'INVALID', 'INVALID'],
     (pytest.raises(IndexError), pytest.raises(ValueError), pytest.raises(ValueError)), {}),

])
@pytest.mark.parametrize("xmode", ["P1", "P2", "F1", "F2"])
def test_03__get_portsmap(mocker, engine, xmode, by_container, portsmap, error, expected):
    """Test03 ExecutionEngineCommon()._get_portsmap()."""
    mocker.patch.object(engine, 'opt', {'portsmap': portsmap})

    # FIXME: this does not test the second try
    with error[0]:
        with error[1]:
            ports = engine._get_portsmap(by_container)
            assert ports == expected


@pytest.mark.parametrize("xmode", ["P1", "P2", "F1", "F2"])
@pytest.mark.parametrize("ports,portsexp,uid,error,count_error,count_warning,expected", [
    # ({22: 22, 2048: 2048}, ("22", "2048/tcp"), 1000, does_not_raise(), 1, 0, False),
    # ({22: 22, 2048: 2048}, ("22", "2048/tcp"), 0, does_not_raise(), 0, 1, True),
    ({22: 22, 2048: 2048}, ("22", "2048/tcp"), 0, pytest.raises(ValueError), 0, 1, True),

])
def test_04__check_exposed_ports(mocker, engine, xmode, logger, ports, portsexp, uid, error, count_error,
                                 count_warning, expected):
    """Test04 ExecutionEngineCommon()._check_exposed_ports()."""
    mocker.patch.object(engine, '_get_portsmap', return_value=ports)
    mocker.patch.object(engine, 'opt', {'portsexp': portsexp})
    mocker.patch('udocker.engine.base.HostInfo.uid', uid)

    exposed_port = engine._check_exposed_ports()
    assert exposed_port == expected

    assert logger.error.call_count == count_error
    assert logger.warning.call_count == count_warning

    if count_error == 1:
        assert logger.error.call_args_list == [mocker.call('this container exposes privileged TCP/IP ports')]

    if count_warning == 1:
        assert logger.warning.call_args_list == [mocker.call('this container exposes TCP/IP ports')]

    # FIXME: needs to launch the error, it's not launching the exception

    # @patch('udocker.engine.base.FileUtil.find_exec')


@pytest.mark.parametrize("xmode", ["P1", "P2", "F1", "F2"])
@pytest.mark.parametrize("opts,conf,exec_name,expected", [
    ({'cpuset': []}, {'cpu_affinity_exec_tools': [[], ]}, '/bin', []),
    ({'cpuset': '1-2'}, {'cpu_affinity_exec_tools': [["numactl", "-C", "%s", "--", ], ]}, 'numactl',
     ['numactl', '-C', '1-2', '--']),
    ({'cpuset': '1-2'}, {'cpu_affinity_exec_tools': [["", "-C", "%s", "--", ], ["taskset", "-c", "%s", ]]},
     None, []),
])
def test_05__set_cpu_affinity(mocker, engine, mocker_fileutil, xmode, logger, opts, conf, exec_name, expected):
    """Test05 ExecutionEngineCommon()._set_cpu_affinity()."""
    mocker_fileutil.return_value.find_exec.return_value = exec_name
    mocker.patch.object(engine, 'opt', opts)
    mocker.patch.object(Config, 'conf', conf)
    cpu_affinity = engine._set_cpu_affinity()
    assert cpu_affinity == expected

# @pytest.mark.parametrize("xmode", ["P1", "P2", "F1", "F2"])
# @pytest.mark.parametrize("dirs_only,is_dir,expected", [
#     (False, []),
#     (True, []),
# ])
# def test_06__create_mountpoint(mocker, engine, logger):
#     """Test06 ExecutionEngineCommon()._create_mountpoint()."""
#     # TODO: complete this test
#     pass
#     # engine._create_mountpoint("/bin", "/ROOT/bin", True)



#     @patch('udocker.engine.base.MountPoint')
#     @patch('udocker.engine.base.FileUtil.isdir')
#     def test_06__create_mountpoint(self, mock_isdir, mock_mpoint):
#         """Test06 ExecutionEngineCommon()._create_mountpoint()."""
#         hpath = "/bin"
#         cpath = "/ROOT/bin"
#         mock_isdir.return_value = False
#         ex_eng = ExecutionEngineCommon(self.local, self.xmode)
#         status = ex_eng._create_mountpoint(hpath, cpath, True)
#         self.assertTrue(status)
#         self.assertTrue(mock_isdir.called)
#
#         hpath = "/bin"
#         cpath = "/ROOT/bin"
#         mock_isdir.return_value = True
#         ex_eng = ExecutionEngineCommon(self.local, self.xmode)
#         ex_eng.mountp = mock_mpoint
#         ex_eng.mountp.create.return_value = True
#         ex_eng.mountp.save.return_value = None
#         status = ex_eng._create_mountpoint(hpath, cpath, True)
#         self.assertTrue(status)
#         self.assertTrue(ex_eng.mountp.save.called)
#
#         hpath = "/bin"
#         cpath = "/ROOT/bin"
#         mock_isdir.return_value = True
#         ex_eng = ExecutionEngineCommon(self.local, self.xmode)
#         ex_eng.mountp = mock_mpoint
#         ex_eng.mountp.create.return_value = False
#         ex_eng.mountp.save.return_value = None
#         status = ex_eng._create_mountpoint(hpath, cpath, True)
#         self.assertFalse(status)
#
#     @patch.object(ExecutionEngineCommon, '_create_mountpoint')
#     @patch('udocker.engine.base.os.path.exists')
#     @patch('udocker.engine.base.Uvolume.split')
#     def test_07__check_volumes(self, mock_uvolsplit, mock_exists, mock_crmpoint):
#         """Test07 ExecutionEngineCommon()._check_volumes()."""
#         mock_uvolsplit.return_value = ("HOSTDIR", "CONTDIR")
#         ex_eng = ExecutionEngineCommon(self.local, self.xmode)
#         ex_eng.opt["vol"] = list()
#         ex_eng.opt["vol"].append("HOSTDIR:CONTDIR")
#         status = ex_eng._check_volumes()
#         self.assertFalse(status)
#         self.assertTrue(mock_uvolsplit.called)
#
#         mock_uvolsplit.return_value = ("/HOSTDIR", "CONTDIR")
#         ex_eng = ExecutionEngineCommon(self.local, self.xmode)
#         ex_eng.opt["vol"] = list()
#         ex_eng.opt["vol"].append("/HOSTDIR:CONTDIR")
#         status = ex_eng._check_volumes()
#         self.assertFalse(status)
#
#         Config.conf['sysdirs_list'] = ["/HOSTDIR"]
#         mock_exists.return_value = False
#         mock_uvolsplit.return_value = ("/HOSTDIR", "/CONTDIR")
#         mock_crmpoint.return_value = False
#         ex_eng = ExecutionEngineCommon(self.local, self.xmode)
#         ex_eng.opt["vol"] = list()
#         ex_eng.opt["vol"].append("/HOSTDIR:/CONTDIR")
#         status = ex_eng._check_volumes()
#         self.assertTrue(status)
#         self.assertEqual(ex_eng.opt["vol"], list())
#         self.assertTrue(mock_exists.called)
#
#         Config.conf['sysdirs_list'] = ["/sys"]
#         mock_exists.return_value = False
#         mock_uvolsplit.return_value = ("/HOSTDIR", "/CONTDIR")
#         mock_crmpoint.return_value = False
#         ex_eng = ExecutionEngineCommon(self.local, self.xmode)
#         ex_eng.opt["vol"] = list()
#         ex_eng.opt["vol"].append("/HOSTDIR:/CONTDIR")
#         status = ex_eng._check_volumes()
#         self.assertFalse(status)
#         self.assertTrue(mock_exists.called)
#
#         Config.conf['sysdirs_list'] = ["/sys"]
#         mock_exists.return_value = True
#         mock_uvolsplit.return_value = ("/HOSTDIR", "/CONTDIR")
#         mock_crmpoint.return_value = True
#         ex_eng = ExecutionEngineCommon(self.local, self.xmode)
#         ex_eng.opt["vol"] = list()
#         ex_eng.opt["vol"].append("/HOSTDIR:/CONTDIR")
#         status = ex_eng._check_volumes()
#         self.assertTrue(status)
#
#     @patch('udocker.engine.base.NixAuthentication.get_home')
#     def test_08__get_bindhome(self, mock_gethome):
#         """Test08 ExecutionEngineCommon()._get_bindhome()."""
#         mock_gethome.return_value = ""
#         ex_eng = ExecutionEngineCommon(self.local, self.xmode)
#         ex_eng.opt["bindhome"] = False
#         status = ex_eng._get_bindhome()
#         self.assertEqual(status, "")
#
#         mock_gethome.return_value = "/home/user"
#         ex_eng = ExecutionEngineCommon(self.local, self.xmode)
#         ex_eng.opt["bindhome"] = True
#         status = ex_eng._get_bindhome()
#         self.assertEqual(status, "/home/user")
#         self.assertTrue(mock_gethome.called)
#
#     @patch('udocker.engine.base.Uvolume.cleanpath')
#     @patch('udocker.engine.base.Uvolume.split')
#     def test_09__is_volume(self, mock_uvolsplit, mock_uvolclean):
#         """Test09 ExecutionEngineCommon()._is_volume()."""
#         ex_eng = ExecutionEngineCommon(self.local, self.xmode)
#         ex_eng.opt["vol"] = list()
#         status = ex_eng._is_volume("/tmp")
#         self.assertEqual(status, "")
#
#         mock_uvolsplit.return_value = ("/tmp", "/CONTDIR")
#         mock_uvolclean.return_value = "/tmp"
#         ex_eng = ExecutionEngineCommon(self.local, self.xmode)
#         ex_eng.opt["vol"] = list()
#         ex_eng.opt["vol"].append("/tmp:/CONTDIR")
#         status = ex_eng._is_volume("/tmp")
#         self.assertEqual(status, "/CONTDIR")
#
#     @patch('udocker.engine.base.Uvolume.cleanpath')
#     @patch('udocker.engine.base.Uvolume.split')
#     def test_10__is_mountpoint(self, mock_uvolsplit, mock_uvolclean):
#         """Test10 ExecutionEngineCommon()._is_mountpoint()."""
#         ex_eng = ExecutionEngineCommon(self.local, self.xmode)
#         ex_eng.opt["vol"] = list()
#         status = ex_eng._is_mountpoint("/tmp")
#         self.assertEqual(status, "")
#
#         mock_uvolsplit.return_value = ("/tmp", "/CONTDIR")
#         mock_uvolclean.return_value = "/CONTDIR"
#         ex_eng = ExecutionEngineCommon(self.local, self.xmode)
#         ex_eng.opt["vol"] = list()
#         ex_eng.opt["vol"].append("/tmp:/CONTDIR")
#         status = ex_eng._is_mountpoint("/tmp")
#         self.assertEqual(status, "/tmp")
#
#     @patch.object(ExecutionEngineCommon, '_check_volumes')
#     @patch.object(ExecutionEngineCommon, '_get_bindhome')
#     def test_11__set_volume_bindings(self, mock_bindhome, mock_chkvol):
#         """Test11 ExecutionEngineCommon()._set_volume_bindings()."""
#         Config.conf['sysdirs_list'] = ["/sys"]
#         Config.conf['dri_list'] = ["/dri"]
#         mock_bindhome.return_value = "/home/user"
#         mock_chkvol.return_value = False
#         ex_eng = ExecutionEngineCommon(self.local, self.xmode)
#         ex_eng.opt["vol"] = list()
#         ex_eng.opt["hostauth"] = "/etc/passwd"
#         ex_eng.opt["nosysdirs"] = False
#         ex_eng.opt["dri"] = True
#         ex_eng.opt["novol"] = list()
#         status = ex_eng._set_volume_bindings()
#         self.assertFalse(status)
#         self.assertTrue(mock_bindhome.called)
#         self.assertTrue(mock_chkvol.called)
#
#         Config.conf['sysdirs_list'] = ["/sys"]
#         Config.conf['dri_list'] = ["/dri"]
#         mock_bindhome.return_value = "/home/user"
#         mock_chkvol.return_value = True
#         ex_eng = ExecutionEngineCommon(self.local, self.xmode)
#         ex_eng.opt["vol"] = list()
#         ex_eng.opt["hostauth"] = "/etc/passwd"
#         ex_eng.opt["nosysdirs"] = False
#         ex_eng.opt["dri"] = True
#         ex_eng.opt["novol"] = ["/sys", "/dri", "/home/user"]
#         status = ex_eng._set_volume_bindings()
#         self.assertTrue(status)
#
#     @patch('udocker.engine.base.Uenv')
#     @patch('udocker.engine.base.os.path.isdir')
#     @patch('udocker.engine.base.FileUtil.cont2host')
#     def test_12__check_paths(self, mock_fuc2h, mock_isdir, mock_uenv):
#         """Test12 ExecutionEngineCommon()._check_paths()."""
#         Config.conf['root_path'] = "/sbin"
#         Config.conf['user_path'] = "/bin"
#         mock_fuc2h.return_value = "/container/bin"
#         mock_isdir.return_value = False
#         ex_eng = ExecutionEngineCommon(self.local, self.xmode)
#         ex_eng.opt["uid"] = "0"
#         ex_eng.opt["cwd"] = ""
#         ex_eng.opt["home"] = "/home/user"
#         ex_eng.opt["env"] = mock_uenv
#         ex_eng.opt["env"].getenv.return_value = "/sbin"
#         status = ex_eng._check_paths()
#         self.assertFalse(status)
#         self.assertEqual(ex_eng.opt["cwd"], ex_eng.opt["home"])
#
#         Config.conf['root_path'] = "/sbin"
#         Config.conf['user_path'] = "/bin"
#         mock_fuc2h.return_value = "/container/bin"
#         mock_isdir.return_value = True
#         ex_eng = ExecutionEngineCommon(self.local, self.xmode)
#         ex_eng.opt["uid"] = "0"
#         ex_eng.opt["cwd"] = "/home/user"
#         ex_eng.opt["home"] = "/home/user"
#         ex_eng.opt["env"] = mock_uenv
#         ex_eng.opt["env"].getenv.return_value = ""
#         status = ex_eng._check_paths()
#         self.assertTrue(status)
#         self.assertTrue(mock_fuc2h.called)
#         self.assertTrue(mock_isdir.called)
#
#     @patch('udocker.engine.base.FileUtil.find_exec')
#     @patch('udocker.engine.base.Uenv')
#     def test_13__check_executable(self, mock_uenv, mock_fufindexe):
#         """Test13 ExecutionEngineCommon()._check_executable()."""
#         Config.conf['cmd'] = "/bin/ls"
#         mock_fufindexe.return_value = ""
#         ex_eng = ExecutionEngineCommon(self.local, self.xmode)
#         ex_eng.opt["env"] = mock_uenv
#         ex_eng.opt["env"].getenv.return_value = ""
#         ex_eng.opt["entryp"] = "/bin/ls -a -l"
#         ex_eng.container_root = "/containers/123/ROOT"
#         status = ex_eng._check_executable()
#         self.assertEqual(status, "")
#         self.assertTrue(mock_fufindexe.called)
#
#         Config.conf['cmd'] = "/bin/ls"
#         mock_fufindexe.return_value = "/bin/ls"
#         ex_eng = ExecutionEngineCommon(self.local, self.xmode)
#         ex_eng.opt["env"] = mock_uenv
#         ex_eng.opt["env"].getenv.return_value = ""
#         ex_eng.opt["entryp"] = "/bin/ls -a -l"
#         ex_eng.container_root = "/containers/123/ROOT"
#         status = ex_eng._check_executable()
#         self.assertEqual(status, "/containers/123/ROOT//bin/ls")
#
#         Config.conf['cmd'] = "/bin/ls"
#         mock_fufindexe.return_value = "/bin/ls"
#         ex_eng = ExecutionEngineCommon(self.local, self.xmode)
#         ex_eng.opt["env"] = mock_uenv
#         ex_eng.opt["env"].getenv.return_value = ""
#         ex_eng.opt["entryp"] = ["/bin/ls", "-a", "-l"]
#         ex_eng.container_root = "/containers/123/ROOT"
#         status = ex_eng._check_executable()
#         self.assertEqual(status, "/containers/123/ROOT//bin/ls")
#
#     @patch('udocker.engine.base.ContainerStructure.get_container_meta')
#     @patch('udocker.engine.base.ContainerStructure.get_container_attr')
#     def test_14__run_load_metadata(self, mock_attr, mock_meta):
#         """Test14 ExecutionEngineCommon()._run_load_metadata()."""
#         Config().conf['location'] = "/tmp/container"
#         ex_eng = ExecutionEngineCommon(self.local, self.xmode)
#         status = ex_eng._run_load_metadata("123")
#         self.assertEqual(status, ("", []))
#
#         Config().conf['location'] = ""
#         mock_attr.return_value = (None, None)
#         ex_eng = ExecutionEngineCommon(self.local, self.xmode)
#         status = ex_eng._run_load_metadata("123")
#         self.assertEqual(status, (None, None))
#         self.assertTrue(mock_attr.called)
#
#         Config().conf['location'] = ""
#         mock_attr.return_value = ("/x", [])
#         ex_eng = ExecutionEngineCommon(self.local, self.xmode)
#         ex_eng.opt["nometa"] = True
#         status = ex_eng._run_load_metadata("123")
#         self.assertEqual(status, ("/x", []))
#
#         Config().conf['location'] = ""
#         mock_attr.return_value = ("/x", [])
#         mock_meta.side_effects = ["user1", "cont/ROOT", "host1", "mydomain",
#                                   "ls", "/bin/sh", "vol1", "8443", None]
#         ex_eng = ExecutionEngineCommon(self.local, self.xmode)
#         ex_eng.opt["nometa"] = False
#         ex_eng.opt["portsexp"] = list()
#         status = ex_eng._run_load_metadata("123")
#         self.assertEqual(status, ("/x", []))
#         self.assertTrue(mock_meta.call_count, 9)
#
#     @patch('udocker.engine.base.os.path.isfile')
#     @patch('udocker.engine.base.os.path.islink')
#     @patch('udocker.engine.base.FileBind')
#     @patch.object(ExecutionEngineCommon, '_is_mountpoint')
#     def test_15__select_auth_files(self, mock_ismpoint, mock_fbind, mock_islink, mock_isfile):
#         """Test15 ExecutionEngineCommon()._select_auth_files()."""
#         resp = "/fbdir/#etc#passwd"
#         resg = "/fbdir/#etc#group"
#         mock_fbind.return_value.orig_dir = "/fbdir"
#         mock_islink.side_effect = [True, True]
#         mock_isfile.side_effect = [True, True]
#         mock_ismpoint.side_effect = ["", "", "", ""]
#         ex_eng = ExecutionEngineCommon(self.local, self.xmode)
#         status = ex_eng._select_auth_files()
#         self.assertTrue(mock_islink.call_count, 2)
#         self.assertTrue(mock_isfile.call_count, 2)
#         self.assertTrue(mock_ismpoint.call_count, 2)
#         # self.assertEqual(status, resp)
#
#         resp = "/etc/passwd"
#         resg = "/etc/group"
#         mock_fbind.orig_dir.side_effect = ["/fbdir", "/fbdir"]
#         mock_islink.side_effect = [False, False]
#         mock_isfile.side_effect = [False, False]
#         mock_ismpoint.side_effect = ["", "", "", ""]
#         ex_eng = ExecutionEngineCommon(self.local, self.xmode)
#         status = ex_eng._select_auth_files()
#         self.assertEqual(status, (resp, resg))
#
#         resp = "/d/etc/passwd"
#         resg = "/d/etc/group"
#         mock_fbind.orig_dir.side_effect = ["/fbdir", "/fbdir"]
#         mock_islink.side_effect = [False, False]
#         mock_isfile.side_effect = [False, False]
#         mock_ismpoint.side_effect = ["/d/etc/passwd", "/d/etc/passwd",
#                                      "/d/etc/group", "/d/etc/group"]
#         ex_eng = ExecutionEngineCommon(self.local, self.xmode)
#         status = ex_eng._select_auth_files()
#         self.assertTrue(mock_ismpoint.call_count, 4)
#         self.assertEqual(status, (resp, resg))
#
#     def test_16__validate_user_str(self):
#         """Test16 ExecutionEngineCommon()._validate_user_str()."""
#         userstr = ""
#         ex_eng = ExecutionEngineCommon(self.local, self.xmode)
#         status = ex_eng._validate_user_str(userstr)
#         self.assertEqual(status, dict())
#
#         userstr = "user1"
#         res = {"user": userstr}
#         ex_eng = ExecutionEngineCommon(self.local, self.xmode)
#         status = ex_eng._validate_user_str(userstr)
#         self.assertEqual(status, res)
#
#         userstr = "1000:1000"
#         res = {"uid": "1000", "gid": "1000"}
#         ex_eng = ExecutionEngineCommon(self.local, self.xmode)
#         status = ex_eng._validate_user_str(userstr)
#         self.assertEqual(status, res)
#
#     def test_17__user_from_str(self):
#         """Test17 ExecutionEngineCommon()._user_from_str()."""
#         userstr = ""
#         ex_eng = ExecutionEngineCommon(self.local, self.xmode)
#         status = ex_eng._user_from_str(userstr)
#         self.assertEqual(status, (False, dict()))
#
#         userstr = "user1"
#         res = {"user": userstr}
#         str_exmode = 'udocker.helper.nixauth.NixAuthentication'
#         nixauth = patch(str_exmode)
#         auth = nixauth.start()
#         mock_auth = Mock()
#         auth.return_value = mock_auth
#         ex_eng = ExecutionEngineCommon(self.local, self.xmode)
#         ex_eng.opt["hostauth"] = True
#         auth.get_user.return_value = ("user1", "1000", "1000", "usr", "/home/user", "/bin/bash")
#         status = ex_eng._user_from_str(userstr, host_auth=auth)
#         self.assertEqual(status, (True, res))
#         auth = nixauth.stop()
#
#         userstr = "user1"
#         res = {"user": userstr}
#         str_exmode = 'udocker.helper.nixauth.NixAuthentication'
#         nixauth = patch(str_exmode)
#         auth = nixauth.start()
#         mock_auth = Mock()
#         auth.return_value = mock_auth
#         ex_eng = ExecutionEngineCommon(self.local, self.xmode)
#         ex_eng.opt["hostauth"] = False
#         auth.get_user.return_value = ("user1", "1000", "1000", "usr", "/home/user", "/bin/bash")
#         status = ex_eng._user_from_str(userstr, container_auth=auth)
#         self.assertEqual(status, (True, res))
#         auth = nixauth.stop()
#
#         userstr = "1000:1000"
#         res = {"uid": "1000", "gid": "1000"}
#         str_exmode = 'udocker.helper.nixauth.NixAuthentication'
#         nixauth = patch(str_exmode)
#         auth = nixauth.start()
#         mock_auth = Mock()
#         auth.return_value = mock_auth
#         ex_eng = ExecutionEngineCommon(self.local, self.xmode)
#         ex_eng.opt["hostauth"] = True
#         auth.get_user.return_value = ("user1", "1000", "1000", "usr", "/home/user", "/bin/bash")
#         status = ex_eng._user_from_str(userstr, host_auth=auth)
#         self.assertEqual(status, (True, res))
#         auth = nixauth.stop()
#
#     @patch('udocker.engine.base.HostInfo')
#     @patch('udocker.engine.base.NixAuthentication')
#     @patch.object(ExecutionEngineCommon, '_create_user')
#     @patch.object(ExecutionEngineCommon, '_is_mountpoint')
#     @patch.object(ExecutionEngineCommon, '_user_from_str')
#     @patch.object(ExecutionEngineCommon, '_select_auth_files')
#     def test_18__setup_container_user(self, mock_selauth, mock_ustr, mock_ismpoint, mock_cruser,
#                                       mock_auth, mock_hinfo):
#         """Test18 ExecutionEngineCommon()._setup_container_user()."""
#         user = "invuser"
#         mock_selauth.return_value = ("/etc/passwd", "/etc/group")
#         mock_ustr.return_value = (False, {"uid": "100", "gid": "50"})
#         mock_auth.side_effect = [None, None]
#         ex_eng = ExecutionEngineCommon(self.local, self.xmode)
#         status = ex_eng._setup_container_user(user)
#         self.assertFalse(status)
#
#         user = ""
#         mock_selauth.return_value = ("/etc/passwd", "/etc/group")
#         mock_ustr.return_value = (True, {"uid": "0", "gid": "0"})
#         mock_auth.side_effect = [None, None]
#         mock_hinfo.return_value.username.return_value = "root"
#         mock_hinfo.uid = 0
#         mock_hinfo.gid = 0
#         mock_ismpoint.side_effect = [True, True]
#         ex_eng = ExecutionEngineCommon(self.local, self.xmode)
#         status = ex_eng._setup_container_user(user)
#         self.assertTrue(status)
#
#         user = ""
#         mock_selauth.return_value = ("/etc/passwd", "/etc/group")
#         mock_ustr.return_value = (True, {"uid": "0", "gid": "0"})
#         mock_auth.side_effect = [None, None]
#         mock_hinfo.return_value.username.return_value = "root"
#         mock_hinfo.uid = 0
#         mock_hinfo.gid = 0
#         mock_ismpoint.side_effect = [False, False]
#         mock_cruser.return_value = None
#         ex_eng = ExecutionEngineCommon(self.local, self.xmode)
#         ex_eng.opt["user"] = ""
#         ex_eng.opt["hostauth"] = True
#         status = ex_eng._setup_container_user(user)
#         self.assertFalse(status)
#         self.assertFalse(mock_cruser.called)
#
#         user = ""
#         mock_selauth.return_value = ("/etc/passwd", "/etc/group")
#         mock_ustr.return_value = (True, {"uid": "0", "gid": "0"})
#         mock_auth.side_effect = [None, None]
#         mock_hinfo.return_value.username.return_value = "root"
#         mock_hinfo.uid = 0
#         mock_hinfo.gid = 0
#         mock_ismpoint.side_effect = [False, False]
#         mock_cruser.return_value = None
#         ex_eng = ExecutionEngineCommon(self.local, self.xmode)
#         ex_eng.opt["user"] = ""
#         ex_eng.opt["hostauth"] = False
#         ex_eng.opt["containerauth"] = False
#         status = ex_eng._setup_container_user(user)
#         self.assertTrue(status)
#         self.assertTrue(mock_cruser.called)
#
#     @patch('udocker.engine.base.HostInfo')
#     @patch('udocker.engine.base.NixAuthentication')
#     @patch.object(ExecutionEngineCommon, '_create_user')
#     @patch.object(ExecutionEngineCommon, '_is_mountpoint')
#     @patch.object(ExecutionEngineCommon, '_user_from_str')
#     @patch.object(ExecutionEngineCommon, '_select_auth_files')
#     def test_19__set_cont_user_noroot(self, mock_selauth, mock_ustr, mock_ismpoint, mock_cruser,
#                                       mock_auth, mock_hinfo):
#         """Test19 ExecutionEngineCommon()._setup_container_user_noroot()."""
#         user = "invuser"
#         mock_selauth.return_value = ("/etc/passwd", "/etc/group")
#         mock_ustr.return_value = (False, {"uid": "100", "gid": "50"})
#         mock_auth.side_effect = [None, None]
#         ex_eng = ExecutionEngineCommon(self.local, self.xmode)
#         status = ex_eng._setup_container_user_noroot(user)
#         self.assertFalse(status)
#
#         user = ""
#         mock_selauth.return_value = ("/etc/passwd", "/etc/group")
#         mock_ustr.return_value = (True, {"uid": "1000", "gid": "1000"})
#         mock_auth.side_effect = [None, None]
#         mock_hinfo.return_value.username.return_value = "u1"
#         mock_hinfo.uid = 0
#         mock_hinfo.gid = 0
#         mock_ismpoint.side_effect = [True, True]
#         ex_eng = ExecutionEngineCommon(self.local, self.xmode)
#         status = ex_eng._setup_container_user_noroot(user)
#         self.assertTrue(status)
#
#         user = ""
#         mock_selauth.return_value = ("/etc/passwd", "/etc/group")
#         mock_ustr.return_value = (True, {"uid": "1000", "gid": "1000"})
#         mock_auth.side_effect = [None, None]
#         mock_hinfo.return_value.username.return_value = "u1"
#         mock_hinfo.uid = 0
#         mock_hinfo.gid = 0
#         mock_ismpoint.side_effect = [False, False]
#         mock_cruser.return_value = None
#         ex_eng = ExecutionEngineCommon(self.local, self.xmode)
#         ex_eng.opt["user"] = ""
#         ex_eng.opt["hostauth"] = True
#         status = ex_eng._setup_container_user_noroot(user)
#         self.assertFalse(status)
#         self.assertFalse(mock_cruser.called)
#
#         user = ""
#         mock_selauth.return_value = ("/etc/passwd", "/etc/group")
#         mock_ustr.return_value = (True, {"uid": "1000", "gid": "1000"})
#         mock_auth.side_effect = [None, None]
#         mock_hinfo.return_value.username.return_value = "u1"
#         mock_hinfo.uid = 0
#         mock_hinfo.gid = 0
#         mock_ismpoint.side_effect = [False, False]
#         mock_cruser.return_value = None
#         ex_eng = ExecutionEngineCommon(self.local, self.xmode)
#         ex_eng.opt["user"] = ""
#         ex_eng.opt["hostauth"] = False
#         ex_eng.opt["containerauth"] = False
#         status = ex_eng._setup_container_user_noroot(user)
#         self.assertTrue(status)
#         self.assertTrue(mock_cruser.called)
#
#     @patch('udocker.engine.base.HostInfo')
#     @patch('udocker.engine.base.NixAuthentication')
#     def test_20__fill_user(self, mock_auth, mock_hinfo):
#         """Test20 ExecutionEngineCommon()._fill_user()."""
#         mock_auth.return_value.get_home.return_value = "/home/u1"
#         mock_hinfo.uid = 1000
#         mock_hinfo.gid = 1000
#         ex_eng = ExecutionEngineCommon(self.local, self.xmode)
#         ex_eng.opt["user"] = ""
#         ex_eng.opt["uid"] = ""
#         ex_eng.opt["gid"] = ""
#         ex_eng.opt["bindhome"] = True
#         ex_eng.opt["shell"] = ""
#         ex_eng.opt["gecos"] = ""
#         ex_eng._fill_user()
#         self.assertEqual(ex_eng.opt["user"], "udoc1000")
#         self.assertEqual(ex_eng.opt["uid"], "1000")
#         self.assertEqual(ex_eng.opt["gid"], "1000")
#         self.assertEqual(ex_eng.opt["shell"], "/bin/sh")
#         self.assertEqual(ex_eng.opt["gecos"], "*UDOCKER*")
#
#     @patch.object(ExecutionEngineCommon, '_fill_user')
#     @patch('udocker.engine.base.os.getgroups')
#     @patch('udocker.engine.base.FileUtil.copyto')
#     @patch('udocker.engine.base.FileUtil.mktmp')
#     @patch('udocker.engine.base.FileUtil.umask')
#     @patch('udocker.engine.base.NixAuthentication')
#     def test_21__create_user(self, mock_nix, mock_umask, mock_mktmp,
#                              mock_cpto, mock_getgrp, mock_fillu):
#         """Test21 ExecutionEngineCommon()._create_user()."""
#         cont_auth = mock_nix
#         host_auth = mock_nix
#         cont_auth.passwd_file.return_value = "/c/etc/passwd"
#         cont_auth.group_file.return_value = "/c/etc/grpup"
#         ex_eng = ExecutionEngineCommon(self.local, self.xmode)
#         ex_eng.opt["containerauth"] = True
#         status = ex_eng._create_user(cont_auth, host_auth)
#         self.assertTrue(status)
#         self.assertFalse(ex_eng.opt["hostauth"])
#
#         cont_auth = mock_nix
#         host_auth = mock_nix
#         res = ("/tmp/passwd:/etc/passwd", "/tmp/group:/etc/group")
#         cont_auth.passwd_file.return_value = "/c/etc/passwd"
#         cont_auth.group_file.return_value = "/c/etc/group"
#         mock_umask.side_effect = [None, None]
#         mock_mktmp.side_effect = ["/tmp/passwd", "/tmp/group"]
#         mock_cpto.side_effect = [None, None]
#         ex_eng = ExecutionEngineCommon(self.local, self.xmode)
#         ex_eng.opt["containerauth"] = False
#         ex_eng.opt["hostauth"] = True
#         status = ex_eng._create_user(cont_auth, host_auth)
#         self.assertTrue(status)
#         self.assertTrue(ex_eng.opt["hostauth"])
#         self.assertEqual(ex_eng.hostauth_list, res)
#
#         cont_auth = mock_nix
#         host_auth = mock_nix
#         res = ("/tmp/passwd:/etc/passwd", "/tmp/group:/etc/group")
#         cont_auth.passwd_file.return_value = "/c/etc/passwd"
#         cont_auth.group_file.return_value = "/c/etc/group"
#         mock_umask.side_effect = [None, None]
#         mock_mktmp.side_effect = ["/tmp/passwd", "/tmp/group"]
#         mock_cpto.side_effect = [None, None]
#         mock_fillu.return_value = None
#         mock_nix.add_user.return_value = None
#         host_auth.get_group.return_value = ("", "x1", "x2")
#         mock_nix.add_group.return_value = None
#         mock_getgrp.return_value = [1000]
#         ex_eng = ExecutionEngineCommon(self.local, self.xmode)
#         ex_eng.opt["containerauth"] = False
#         ex_eng.opt["hostauth"] = False
#         status = ex_eng._create_user(cont_auth, host_auth)
#         self.assertTrue(status)
#         self.assertTrue(ex_eng.opt["hostauth"])
#         self.assertEqual(ex_eng.hostauth_list, res)
#
#     @patch('udocker.engine.base.os.path.basename')
#     def test_22__run_banner(self, mock_base):
#         """Test22 ExecutionEngineCommon()._run_banner()."""
#         mock_base.return_value = "ls"
#         ex_eng = ExecutionEngineCommon(self.local, self.xmode)
#         ex_eng._run_banner("/bin/bash")
#         ex_eng.container_id = "CONTAINERID"
#         self.assertTrue(mock_base.called_once_with("/bin/bash"))
#
#     @patch('udocker.engine.base.os.environ.copy')
#     @patch('udocker.engine.base.os.environ')
#     def test_23__run_env_cleanup_dict(self, mock_osenv, mock_osenvcp):
#         """Test23 ExecutionEngineCommon()._run_env_cleanup_dict()."""
#         res = {'HOME': '/', }
#         Config.conf['valid_host_env'] = ("HOME",)
#         Config.conf['invalid_host_env'] = ("USERNAME",)
#         mock_osenvcp.return_value = {'HOME': '/', 'USERNAME': 'user', }
#         mock_osenv.return_value = {'HOME': '/', }
#         ex_eng = ExecutionEngineCommon(self.local, self.xmode)
#         ex_eng.opt["hostenv"] = {'HOME': '/', }
#         ex_eng._run_env_cleanup_dict()
#         self.assertEqual(mock_osenv.return_value, res)
#
#     @patch('udocker.engine.base.os.environ')
#     def test_24__run_env_cleanup_list(self, mock_osenv):
#         """Test24 ExecutionEngineCommon()._run_env_cleanup_list()."""
#         Config.conf['valid_host_env'] = ("HOME",)
#         Config.conf['invalid_host_env'] = ("USERNAME",)
#         mock_osenv.return_value = {'HOME': '/', 'USERNAME': 'user', }
#         ex_eng = ExecutionEngineCommon(self.local, self.xmode)
#         ex_eng.opt["hostenv"] = "HOME"
#         ex_eng.opt["env"] = Uenv()
#         ex_eng._run_env_cleanup_list()
#         self.assertEqual(ex_eng.opt["env"].env, dict())
#
#     @patch('udocker.engine.base.HostInfo.username')
#     def test_25__run_env_set(self, mock_hiuname):
#         """Test25 ExecutionEngineCommon()._run_env_set()."""
#         mock_hiuname.return_value = "user1"
#         ex_eng = ExecutionEngineCommon(self.local, self.xmode)
#         ex_eng.opt["home"] = "/"
#         ex_eng.opt["user"] = "user1"
#         ex_eng.opt["uid"] = "1000"
#         ex_eng.container_root = "/croot"
#         ex_eng.container_id = "2717add4-e6f6-397c-9019-74fa67be439f"
#         ex_eng.container_names = ['cna[]me', ]
#         self.xmode.get_mode.return_value = "P1"
#         ex_eng._run_env_set()
#         self.assertEqual(ex_eng.opt["env"].env["USER"], "user1")
#         self.assertEqual(ex_eng.opt["env"].env["LOGNAME"], "user1")
#         self.assertEqual(ex_eng.opt["env"].env["USERNAME"], "user1")
#         self.assertEqual(ex_eng.opt["env"].env["SHLVL"], "0")
#
#     @patch('udocker.engine.base.FileUtil.getdata')
#     def test_26__run_env_cmdoptions(self, mock_getdata):
#         """Test26 ExecutionEngineCommon()._run_env_cmdoptions()."""
#         mock_getdata.return_value = "USER=user1\nSHLVL=0"
#         ex_eng = ExecutionEngineCommon(self.local, self.xmode)
#         ex_eng.opt["envfile"] = ["/dir/env"]
#         ex_eng.opt["env"] = Uenv()
#         ex_eng._run_env_cmdoptions()
#         self.assertEqual(ex_eng.opt["env"].env["USER"], "user1")
#
#     @patch('udocker.engine.base.MountPoint')
#     @patch.object(ExecutionEngineCommon, '_check_exposed_ports')
#     @patch.object(ExecutionEngineCommon, '_set_volume_bindings')
#     @patch.object(ExecutionEngineCommon, '_check_executable')
#     @patch.object(ExecutionEngineCommon, '_check_paths')
#     @patch.object(ExecutionEngineCommon, '_setup_container_user')
#     @patch.object(ExecutionEngineCommon, '_run_env_cmdoptions')
#     @patch.object(ExecutionEngineCommon, '_run_load_metadata')
#     def test_27__run_init(self, mock_loadmeta, mock_envcmd, mock_setupuser, mock_chkpaths,
#                           mock_chkexec, mock_setvol, mock_chkports, mock_mpoint):
#         """Test27 ExecutionEngineCommon()._run_init()."""
#         # mock_getcname.return_value = "cname"
#         Config.conf['location'] = ""
#         mock_loadmeta.return_value = ("", "dummy",)
#         ex_eng = ExecutionEngineCommon(self.local, self.xmode)
#         status = ex_eng._run_init("2717add4-e6f6-397c-9019-74fa67be439f")
#         self.assertEqual(status, "")
#         self.assertTrue(mock_loadmeta.called)
#
#         Config.conf['location'] = "/container_dir"
#         mock_loadmeta.return_value = ("/container_dir", "dummy",)
#         mock_envcmd.return_value = None
#         mock_chkports.return_value = None
#         mock_setupuser.return_value = False
#         self.local.get_container_name.return_value = "cont_name"
#         ex_eng = ExecutionEngineCommon(self.local, self.xmode)
#         status = ex_eng._run_init("2717add4-e6f6-397c-9019-74fa67be439f")
#         self.assertEqual(status, "")
#         self.assertTrue(mock_envcmd.called)
#         self.assertTrue(self.local.get_container_name.called)
#         self.assertTrue(mock_chkports.called)
#
#         Config.conf['location'] = "/container_dir"
#         mock_loadmeta.return_value = ("/container_dir", "dummy",)
#         mock_envcmd.return_value = None
#         mock_chkports.return_value = None
#         mock_setupuser.return_value = True
#         mock_mpoint.return_value = None
#         mock_setvol.return_value = False
#         self.local.get_container_name.return_value = "cont_name"
#         ex_eng = ExecutionEngineCommon(self.local, self.xmode)
#         status = ex_eng._run_init("2717add4-e6f6-397c-9019-74fa67be439f")
#         self.assertEqual(status, "")
#         self.assertTrue(mock_chkports.called)
#         self.assertTrue(mock_mpoint.called)
#         self.assertTrue(mock_setvol.called)
#
#         Config.conf['location'] = "/container_dir"
#         mock_loadmeta.return_value = ("/container_dir", "dummy",)
#         mock_envcmd.return_value = None
#         mock_chkports.return_value = None
#         mock_setupuser.return_value = True
#         mock_mpoint.return_value = None
#         mock_setvol.return_value = True
#         mock_chkpaths.return_value = False
#         self.local.get_container_name.return_value = "cont_name"
#         ex_eng = ExecutionEngineCommon(self.local, self.xmode)
#         status = ex_eng._run_init("2717add4-e6f6-397c-9019-74fa67be439f")
#         self.assertEqual(status, "")
#         self.assertTrue(mock_chkpaths.called)
#
#         Config.conf['location'] = "/container_dir"
#         mock_loadmeta.return_value = ("/container_dir", "dummy",)
#         mock_envcmd.return_value = None
#         mock_chkports.return_value = None
#         mock_setupuser.return_value = True
#         mock_mpoint.return_value = None
#         mock_setvol.return_value = True
#         mock_chkpaths.return_value = True
#         mock_chkexec.return_value = "/bin/ls"
#         self.local.get_container_name.return_value = "cont_name"
#         ex_eng = ExecutionEngineCommon(self.local, self.xmode)
#         status = ex_eng._run_init("2717add4-e6f6-397c-9019-74fa67be439f")
#         self.assertEqual(status, "/bin/ls")
#         self.assertTrue(mock_chkexec.called)
#
#     @patch('udocker.engine.base.HostInfo')
#     @patch('udocker.engine.base.json.loads')
#     @patch('udocker.engine.base.FileUtil.getdata')
#     def test_28__is_same_osenv(self, mock_getdata, mock_jload, mock_hinfo):
#         """Test28 ExecutionEngineCommon()._is_same_osenv()."""
#         mock_getdata.return_value = dict()
#         mock_jload.return_value = dict()
#         ex_eng = ExecutionEngineCommon(self.local, self.xmode)
#         status = ex_eng._is_same_osenv("somefile")
#         self.assertEqual(status, dict())
#
#         mock_getdata.return_value = {"osversion": "linux", "oskernel": "3.2.1", "arch": "amd64"}
#         mock_jload.return_value = {"osversion": "linux", "oskernel": "3.2.1", "arch": "amd64"}
#         mock_hinfo.return_value.osversion.return_value = "linux"
#         mock_hinfo.return_value.oskernel.return_value = "3.2.1"
#         mock_hinfo.return_value.arch.return_value = "amd64"
#         ex_eng = ExecutionEngineCommon(self.local, self.xmode)
#         status = ex_eng._is_same_osenv("somefile")
#         self.assertEqual(status, {"osversion": "linux", "oskernel": "3.2.1", "arch": "amd64"})
#
#     @patch('udocker.engine.base.HostInfo')
#     @patch('udocker.engine.base.json.dumps')
#     @patch('udocker.engine.base.FileUtil.putdata')
#     def test_29__save_osenv(self, mock_putdata, mock_jdump, mock_hinfo):
#         """Test29 ExecutionEngineCommon()._save_osenv()."""
#         mock_putdata.return_value = {"osversion": "linux", "oskernel": "3.2.1", "arch": "amd64"}
#         mock_jdump.return_value = {"osversion": "linux", "oskernel": "3.2.1", "arch": "amd64"}
#         mock_hinfo.return_value.osversion.return_value = "linux"
#         mock_hinfo.return_value.oskernel.return_value = "3.2.1"
#         mock_hinfo.return_value.arch.return_value = "amd64"
#         ex_eng = ExecutionEngineCommon(self.local, self.xmode)
#         status = ex_eng._save_osenv("somefile")
#         self.assertTrue(status)
#
#
# if __name__ == '__main__':
#     main()
