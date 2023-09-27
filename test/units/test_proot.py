#!/usr/bin/env python
"""
udocker unit tests: PRootEngine
"""
import os
import pytest
import random

from udocker.config import Config
from udocker.engine.execmode import ExecutionMode
from udocker.engine.proot import PRootEngine
from contextlib import nullcontext as does_not_raise

KERNEL_VERSIONS = ["4.8.13", "4.8.0", "4.5.0"]
EXECUTABLE = ["UDOCKER", "proot", "proot-x86_64-4_8_13", "proot-x86_64-4_8_0", "proot-x86_64-4_5_0"]
XMODE = ["P1", "P2"]


@pytest.fixture
def container_id():
    return str(random.randint(1, 1000))


@pytest.fixture
def localrepo(mocker, container_id):
    mocker_localrepo = mocker.patch('udocker.container.localrepo.LocalRepository')
    mocker_localrepo._container_id = container_id
    mocker_localrepo.bindir = "proot"  # TODO: check if this is correct
    return mocker_localrepo


@pytest.fixture(autouse=True)
def mock_hostinfo_oskernel(mocker, kernel):
    mocker_hostinfo_kernel = mocker.patch('udocker.engine.proot.HostInfo.oskernel', return_value=kernel)
    return mocker_hostinfo_kernel


@pytest.fixture(autouse=True)
@pytest.mark.parametrize('xmode', XMODE)
def mock_exec_mode(localrepo, container_id, xmode):
    mocker_exec_mode = ExecutionMode(localrepo, container_id)
    mocker_exec_mode.force_mode = xmode
    return mocker_exec_mode


@pytest.fixture(autouse=True)
def mock_proot(localrepo, mock_exec_mode):
    mocker_proot = PRootEngine(localrepo, mock_exec_mode)
    return mocker_proot


@pytest.fixture(autouse=True)
def mock_os_exists(mocker):
    mocker_os_exists = mocker.patch('udocker.engine.proot.os.path.exists')
    return mocker_os_exists


@pytest.fixture
def logger(mocker):
    mocker_logger = mocker.patch('udocker.engine.proot.LOG')
    return mocker_logger


@pytest.fixture(autouse=True)
def mock_hostinfo_oskernel_isgreater(mocker):
    mocker_hostinfo = mocker.patch('udocker.helper.hostinfo.HostInfo')
    mocker_hostinfo.return_value.oskernel_isgreater.return_value = False
    return mocker_hostinfo


# @pytest.fixture
# def mock_fileutil(mocker):
#     mocker_fileutil = mocker.patch('udocker.engine.proot.FileUtil.__init__')
#     return mocker_fileutil


@pytest.fixture
def mock_fileutil_find_file_in_dir(mocker):
    mocker_fileutil_find_file_in_dir = mocker.patch('udocker.engine.proot.FileUtil.find_file_in_dir',
                                                    return_value="/some/path/proot")
    return mocker_fileutil_find_file_in_dir


# @pytest.fixture
# def mock_fileutil_find_exec(mocker):
#     mocker_fileutil_find_exec = mocker.patch('udocker.engine.proot.FileUtil.find_exec',
#                                              return_value="/some/executable/proot")
#     return mocker_fileutil_find_exec


# @pytest.fixture
# def mock_is_seccomp_patched(mocker):
#     return mocker.patch('udocker.engine.proot.PRootEngine._is_seccomp_patched')


@pytest.fixture
def mock_get_saved_osenv(mocker):
    mocker_hostinfo_get_saved_osenv = mocker.patch('udocker.engine.proot.PRootEngine._get_saved_osenv')
    return mocker_hostinfo_get_saved_osenv


@pytest.fixture
def mock_get_output(mocker):
    return mocker.patch('udocker.engine.proot.Uprocess.get_output')


@pytest.mark.parametrize('kernel', KERNEL_VERSIONS)
@pytest.mark.parametrize('xmode', ['P1', 'P2'])
def test_01_init(mock_proot, mock_hostinfo_oskernel, kernel):
    """Test01 PRootEngine() constructor."""
    assert mock_proot.executable is None
    assert mock_proot.proot_noseccomp is False
    assert mock_proot.proot_newseccomp is False
    assert mock_proot._kernel == kernel


select_proot_data = (
    (True, 0, "", does_not_raise(), "UDOCKER", "/some/path/proot", KERNEL_VERSIONS),
    (True, 0, "", does_not_raise(), "PROOT", "PROOT", KERNEL_VERSIONS),
    (True, 0, "", does_not_raise(), "", "/some/path/proot", KERNEL_VERSIONS),
    (True, 0, "", does_not_raise(), None, "/some/path/proot", KERNEL_VERSIONS),
    (False, 0, "", pytest.raises(SystemExit), "PROOT", "/some/path/proot", KERNEL_VERSIONS),
    (False, 1, "proot executable not found", pytest.raises(SystemExit), "PROOT", "/some/path/proot", KERNEL_VERSIONS),
)


# @pytest.mark.parametrize('xmode', XMODE)
# @pytest.mark.parametrize('pathexists,logcount,msg,error,exec,pathexec,kernel', select_proot_data)
# def test_02_select_proot(mock_proot, mock_os_exists, mock_hostinfo_oskernel_isgreater,
#                          mock_exec_mode, mock_fileutil_find_file_in_dir,
#                          logger,
#                          pathexists, logcount, msg, error, exec, pathexec, xmode, kernel):
#     """Test02 PRootEngine().select_proot()."""
#     Config.conf['use_proot_executable'] = exec
#     mock_os_exists.return_value = pathexists
#     mock_fileutil.return_value = "proot"
#     mock_fileutil_find_file_in_dir.return_value = "/some/path/proot"

#     logger.reset_mock()
#     with error:
#         mock_proot.select_proot()
#         assert pathexec == mock_proot.executable
#         assert logger.error.called == logcount
#         if xmode == 'P2':
#             assert mock_proot.proot_noseccomp is True
#         else:
#             assert mock_proot.proot_noseccomp is False


is_seccomp_patched_data = (
    #('PROOT_NEW_SECCOMP', {}, "4.8.0", [], True),
    #('PROOT_NO_SECCOMP', {}, "4.8.0", [], False),
    #(None, {}, "4.8.0", [], False),
    #(None, {"PROOT_NEW_SECCOMP": "1"}, "4.8.0", [], False),
    (None, {"PROOT_NEW_SECCOMP": "1"}, "4.1.0", [], True),
    (None, {"NOT_PROOT": "1"}, "4.1.0", [], False),
    (None, {}, "4.1.0", ["proot", ""], False),
    (None, {}, "4.1.0", ["", "proot"], True),
)


@pytest.mark.parametrize('xmode', XMODE)
@pytest.mark.parametrize('os_env,saved_os,kernel,output,expected', is_seccomp_patched_data)
def test_03__is_seccomp_patched(mock_proot, mock_hostinfo_oskernel_isgreater, mock_get_saved_osenv, mock_get_output,
                                expected, os_env, saved_os, kernel, output):
    """Test03 PRootEngine()._is_seccomp_patched()."""

    # cleanup environment
    os.environ.pop('PROOT_NEW_SECCOMP', None)
    os.environ.pop('PROOT_NO_SECCOMP', None)

    mock_get_output.side_effect = output
    mock_get_saved_osenv.return_value = saved_os

    # set additional variable to environment
    if os_env:
        os.environ[os_env] = os_env

    assert mock_proot._is_seccomp_patched("/bin/sec") == expected


set_uid_map_data = (
    ("0", "1001", ['-0']),
    ("1001", "0", ['-i', '1001:0']),
    ("1000", "1001", ['-i', '1000:1001']),
)


@pytest.mark.parametrize('xmode', ['P1', 'P2'])
@pytest.mark.parametrize('kernel', ['4.8.13'])
@pytest.mark.parametrize('uid,gid,expected', set_uid_map_data)
def test_03__set_uid_map(mock_proot, uid, gid, expected):
    """Test03 PRootEngine()._set_uid_map()."""
    mock_proot.opt['uid'] = uid
    mock_proot.opt["gid"] = gid
    assert mock_proot._set_uid_map() == expected


@pytest.mark.parametrize('kernel', KERNEL_VERSIONS)
@pytest.mark.parametrize('xmode', ['P1', 'P2'])
def test_04__create_mountpoint(mock_proot):
    """Test04 PRootEngine()._create_mountpoint()."""
    assert mock_proot._create_mountpoint("", "") is True


get_volume_bindings_data = (
    ((), []),
    (("/tmp", "/bbb",), ['-b', '/tmp:/tmp', '-b', '/bbb:/bbb']),
    (("/tmp",), ['-b', '/tmp:/tmp']),
)


@pytest.mark.parametrize('xmode', ['P1'])
@pytest.mark.parametrize('kernel', ['4.8.13'])
@pytest.mark.parametrize("vol,expected", get_volume_bindings_data)
def test_05__get_volume_bindings(mock_proot, vol, expected):
    """Test05 PRootEngine()._get_volume_bindings()."""
    mock_proot.opt["vol"] = vol
    assert mock_proot._get_volume_bindings() == expected


get_network_map_data = (
    (None, {}, []),
    (None, {80: 8080}, ["-p", "80:8080"]),
    (None, {80: 8080, 443: 8443}, ["-p", "80:8080", "-p", "443:8443"]),
    (True, {80: 8080, 443: 8443, 53: 53}, ["-p", "80:8080", "-p", "443:8443", "-p", "53:53", "-n"]),
)


@pytest.mark.parametrize('xmode', ['P1'])
@pytest.mark.parametrize('kernel', ['4.8.13'])
@pytest.mark.parametrize("netcoop,portsmap,expected", get_network_map_data)
def test_06__get_network_map(mock_proot, netcoop, portsmap, expected):
    """Test06 PRootEngine()._get_network_map()."""
    mock_proot.opt["netcoop"] = netcoop
    mock_proot._get_portsmap = lambda: portsmap
    assert mock_proot._get_network_map() == expected

run_data = (
    (None, None, None, None, None, None, None, None, None, None, None, None, None, None, None),
)


@pytest.mark.parametrize('xmode', XMODE)
@pytest.mark.parametrize('kernel', KERNEL_VERSIONS)
def test_07_run(mocker, mock_proot, container_id):
    """Test07 PRootEngine().run()."""

    mock_proot._set_uid_map = lambda: []
    mocker.patch('udocker.engine.proot.Uprocess.get_output', return_value="output")
    mock_proot._run_init = lambda: True

    mock_proot.run(container_id=container_id)


# from unittest import TestCase, main
# from unittest.mock import Mock, patch
# from udocker.config import Config
# from udocker.engine.proot import PRootEngine, LOG
# import collections
# collections.Callable = collections.abc.Callable
#
#
# class PRootEngineTestCase(TestCase):
#     """Test PRootEngine() class for containers execution."""
#
#     def setUp(self):
#         LOG.setLevel(100)
#         Config().getconf()
#         Config().conf['hostauth_list'] = ("/etc/passwd", "/etc/group")
#         Config().conf['cmd'] = "/bin/bash"
#         Config().conf['cpu_affinity_exec_tools'] = (["numactl", "-C", "%s", "--", ],
#                                                     ["taskset", "-c", "%s", ])
#         Config().conf['valid_host_env'] = "HOME"
#         Config().conf['username'] = "user"
#         Config().conf['userhome'] = "/"
#         Config().conf['oskernel'] = "4.8.13"
#         Config().conf['location'] = ""
#
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
#
#     @patch('udocker.engine.proot.HostInfo.oskernel')
#     def test_01_init(self, mock_kernel):
#         """Test01 PRootEngine() constructor."""
#         mock_kernel.return_value = "4.8.13"
#         prex = PRootEngine(self.local, self.xmode)
#         self.assertFalse(prex.proot_noseccomp)
#         self.assertEqual(prex._kernel, "4.8.13")
#
#     @patch.object(PRootEngine, '_is_seccomp_patched')
#     @patch('udocker.engine.proot.HostInfo.oskernel_isgreater')
#     @patch('udocker.engine.proot.FileUtil.find_file_in_dir')
#     @patch('udocker.helper.elfpatcher.os.path.exists')
#     def test_02_select_proot(self, mock_exists, mock_fimage, mock_isgreater, mock_issecomp):
#         """Test02 PRootEngine().select_proot()."""
#         Config().conf['arch'] = "amd64"
#         Config().conf['proot_noseccomp'] = None
#         mock_isgreater.return_value = False
#         mock_fimage.return_value = "proot-4_8_0"
#         mock_issecomp.return_value = False
#         mock_exists.return_value = True
#         prex = PRootEngine(self.local, self.xmode)
#         prex.select_proot()
#         self.assertFalse(prex.proot_noseccomp)
#
#         Config().conf['proot_noseccomp'] = True
#         mock_isgreater.return_value = True
#         mock_fimage.return_value = "proot"
#         mock_issecomp.return_value = False
#         mock_exists.return_value = True
#         prex = PRootEngine(self.local, self.xmode)
#         prex.select_proot()
#         self.assertTrue(prex.proot_noseccomp)
#
#         Config().conf['proot_noseccomp'] = False
#         mock_isgreater.return_value = True
#         mock_fimage.return_value = "proot"
#         mock_issecomp.return_value = False
#         mock_exists.return_value = True
#         prex = PRootEngine(self.local, self.xmode)
#         prex.select_proot()
#         self.assertFalse(prex.proot_noseccomp)
#
#         Config().conf['proot_noseccomp'] = None
#         mock_isgreater.return_value = True
#         mock_fimage.return_value = "proot-x86_64-4_8_0"
#         mock_issecomp.return_value = False
#         mock_exists.return_value = True
#         prex = PRootEngine(self.local, self.xmode)
#         prex.select_proot()
#         self.assertFalse(prex.proot_noseccomp)
#
#         Config().conf['proot_noseccomp'] = False
#         mock_isgreater.return_value = True
#         mock_fimage.return_value = "proot-x86_64-4_8_0"
#         mock_issecomp.return_value = False
#         mock_exists.return_value = True
#         prex = PRootEngine(self.local, self.xmode)
#         prex.select_proot()
#         self.assertFalse(prex.proot_noseccomp)
#
#         Config().conf['proot_noseccomp'] = True
#         mock_isgreater.return_value = True
#         mock_fimage.return_value = "proot-x86_64-4_8_0"
#         mock_issecomp.return_value = False
#         mock_exists.return_value = True
#         prex = PRootEngine(self.local, self.xmode)
#         prex.select_proot()
#         self.assertTrue(prex.proot_noseccomp)
#
#     @patch('udocker.engine.proot.ExecutionEngineCommon._save_osenv')
#     @patch('udocker.engine.proot.Uprocess.get_output')
#     @patch('udocker.engine.proot.ExecutionEngineCommon._is_same_osenv')
#     @patch('udocker.engine.proot.HostInfo.oskernel_isgreater')
#     @patch('udocker.engine.proot.os.environ')
#     def test_03__is_seccomp_patched(self, mock_env, mock_isgrt, mock_sameenv, mock_out, mock_save):
#         """Test03 PRootEngine()._is_seccomp_patched()."""
#         mock_env.return_value = {"PROOT_NEW_SECCOMP": "/bin/sec", }
#         prex = PRootEngine(self.local, self.xmode)
#         status = prex._is_seccomp_patched("/bin/sec")
#         self.assertFalse(status)
#
#         Config().conf['proot_noseccomp'] = True
#         mock_env.return_value = {"PROOT_NEW_SECCOMP": "/bin/sec", }
#         mock_isgrt.return_value = True
#         prex = PRootEngine(self.local, self.xmode)
#         status = prex._is_seccomp_patched("/bin/sec")
#         self.assertFalse(status)
#
#         Config().conf['proot_noseccomp'] = None
#         mock_env.return_value = dict()
#         mock_isgrt.return_value = False
#         mock_sameenv.return_value = {"PROOT_NEW_SECCOMP": "/bin/sec", }
#         prex = PRootEngine(self.local, self.xmode)
#         status = prex._is_seccomp_patched("/bin/sec")
#         self.assertTrue(status)
#
#         Config().conf['proot_noseccomp'] = None
#         mock_env.return_value = dict()
#         mock_isgrt.return_value = False
#         mock_sameenv.return_value = dict()
#         prex = PRootEngine(self.local, self.xmode)
#         status = prex._is_seccomp_patched("/bin/sec")
#         self.assertFalse(status)
#
#         Config().conf['proot_noseccomp'] = None
#         mock_env.return_value = dict()
#         mock_isgrt.return_value = False
#         mock_sameenv.return_value = None
#         mock_out.side_effect = [False, True]
#         prex = PRootEngine(self.local, self.xmode)
#         status = prex._is_seccomp_patched("/bin/sec")
#         self.assertTrue(status)
#
#         Config().conf['proot_noseccomp'] = None
#         mock_env.return_value = dict()
#         mock_isgrt.return_value = False
#         mock_sameenv.return_value = None
#         mock_out.side_effect = [True, False]
#         mock_save.return_value = None
#         prex = PRootEngine(self.local, self.xmode)
#         status = prex._is_seccomp_patched("/bin/sec")
#         self.assertFalse(status)
#
#     def test_03__set_uid_map(self):
#         """Test03 PRootEngine()._set_uid_map()."""
#         prex = PRootEngine(self.local, self.xmode)
#         prex.opt["uid"] = "0"
#         status = prex._set_uid_map()
#         self.assertEqual(status, ['-0'])
#
#         prex = PRootEngine(self.local, self.xmode)
#         prex.opt["uid"] = "1000"
#         prex.opt["gid"] = "1001"
#         status = prex._set_uid_map()
#         self.assertEqual(status, ['-i', '1000:1001'])
#
#     def test_04__create_mountpoint(self):
#         """Test04 PRootEngine()._create_mountpoint()."""
#         prex = PRootEngine(self.local, self.xmode)
#         status = prex._create_mountpoint("", "")
#         self.assertTrue(status)
#
#     def test_05__get_volume_bindings(self):
#         """Test05 PRootEngine()._get_volume_bindings()."""
#         prex = PRootEngine(self.local, self.xmode)
#         prex.opt["vol"] = ()
#         status = prex._get_volume_bindings()
#         self.assertEqual(status, [])
#
#         prex = PRootEngine(self.local, self.xmode)
#         prex.opt["vol"] = ("/tmp", "/bbb",)
#         status = prex._get_volume_bindings()
#         self.assertEqual(status, ['-b', '/tmp:/tmp', '-b', '/bbb:/bbb'])
#
#     @patch('udocker.engine.proot.ExecutionEngineCommon._get_portsmap')
#     def test_06__get_network_map(self, mock_pmap):
#         """Test06 PRootEngine()._get_network_map()."""
#         mock_pmap.return_value = {}
#         prex = PRootEngine(self.local, self.xmode)
#         prex.opt['netcoop'] = False
#         status = prex._get_network_map()
#         self.assertEqual(status, [])
#
#         mock_pmap.return_value = {}
#         prex = PRootEngine(self.local, self.xmode)
#         prex.opt['netcoop'] = True
#         status = prex._get_network_map()
#         self.assertEqual(status, ['-n'])
#
#         mock_pmap.return_value = {80: 8080, 443: 8443}
#         prex = PRootEngine(self.local, self.xmode)
#         prex.opt['netcoop'] = True
#         status = prex._get_network_map()
#         self.assertEqual(status, ['-p', '80:8080', '-p', '443:8443', '-n'])
#
#     @patch('udocker.engine.proot.os.environ.update')
#     @patch.object(PRootEngine, '_get_network_map')
#     @patch('udocker.engine.proot.HostInfo.oskernel_isgreater')
#     @patch.object(PRootEngine, '_run_banner')
#     @patch.object(PRootEngine, '_run_env_cleanup_dict')
#     @patch.object(PRootEngine, '_set_uid_map')
#     @patch.object(PRootEngine, '_get_volume_bindings')
#     @patch.object(PRootEngine, '_set_cpu_affinity')
#     @patch.object(PRootEngine, '_run_env_set')
#     @patch.object(PRootEngine, 'select_proot')
#     @patch('udocker.engine.proot.os.getenv')
#     @patch('udocker.engine.proot.subprocess.call')
#     @patch('udocker.engine.proot.ExecutionEngineCommon._run_init')
#     def test_07_run(self, mock_run_init, mock_call, mock_getenv, mock_sel_proot, mock_run_env_set,
#                     mock_set_cpu_aff, mock_get_vol_bind, mock_set_uid_map, mock_env_cleanup_dict,
#                     mock_run_banner, mock_isgreater, mock_netmap, mock_envupd):
#         """Test07 PRootEngine().run()."""
#         mock_run_init.return_value = False
#         prex = PRootEngine(self.local, self.xmode)
#         status = prex.run("CONTAINERID")
#         self.assertEqual(status, 2)
#
#         Config().conf['proot_killonexit'] = False
#         mock_run_init.return_value = True
#         mock_sel_proot.return_value = None
#         mock_isgreater.return_value = "2.9.0"
#         mock_run_env_set.return_value = None
#         mock_set_cpu_aff.return_value = []
#         mock_get_vol_bind.return_value = ['-b', '/tmp:/tmp']
#         mock_set_uid_map.return_value = ['-i', '1000:1001']
#         mock_netmap.return_value = ['-p', '80:8080', '-n']
#         mock_env_cleanup_dict.return_value = None
#         mock_run_banner.return_value = None
#         mock_call.return_value = 5
#         mock_getenv.return_value = False
#         mock_envupd.return_value = None
#         prex = PRootEngine(self.local, self.xmode)
#         prex.opt["kernel"] = "5.4.0"
#         prex.opt["cmd"] = [""]
#         status = prex.run("CONTAINERID")
#         self.assertEqual(status, 5)
#         self.assertTrue(mock_run_init.called)
#         self.assertTrue(mock_call.called)
#         self.assertTrue(mock_envupd.called)
#
#
# if __name__ == '__main__':
#     main()
