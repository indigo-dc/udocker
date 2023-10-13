#!/usr/bin/env python
"""
udocker unit tests: PRootEngine
"""
import os
import random
from contextlib import nullcontext as does_not_raise

import pytest

from udocker.config import Config
from udocker.engine.execmode import ExecutionMode
from udocker.engine.proot import PRootEngine

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
    mocker_localrepo.bindir = "proot"
    return mocker_localrepo


@pytest.fixture
def mock_hostinfo(mocker):
    return mocker.patch('udocker.engine.proot.HostInfo')


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
def proot(localrepo, mock_exec_mode):
    mocker_proot = PRootEngine(localrepo, mock_exec_mode)
    return mocker_proot


@pytest.fixture(autouse=True)
def mock_os_exists(mocker):
    return mocker.patch('udocker.engine.proot.os.path.exists')


@pytest.fixture
def logger(mocker):
    mocker_logger = mocker.patch('udocker.engine.proot.LOG')
    return mocker_logger


@pytest.fixture
def mock_fileutil(mocker):
    return mocker.patch('udocker.engine.proot.FileUtil')


@pytest.fixture
def mock_get_output(mocker):
    return mocker.patch('udocker.engine.proot.Uprocess.get_output')


@pytest.mark.parametrize('kernel', KERNEL_VERSIONS)
@pytest.mark.parametrize('xmode', ['P1', 'P2'])
def test_01_init(proot, kernel):
    """Test01 PRootEngine() constructor."""
    assert proot.executable is None
    assert proot.proot_noseccomp is False
    assert proot.proot_newseccomp is False
    assert proot._kernel == kernel


@pytest.mark.parametrize('is_greater', (True, False))
@pytest.mark.parametrize('pathexists,logcount,msg,error,conf,pathexec,kernel,is_seccomp_patched,expected', [
    (True, 0, "", does_not_raise(), {'use_proot_executable': 'UDOCKER', 'proot_noseccomp': None}, "/some/path/proot",
     KERNEL_VERSIONS, False, ("/some/path/proot", False)),
    (True, 0, "", does_not_raise(), {'use_proot_executable': None, 'proot_noseccomp': None}, "/some/path/proot",
     KERNEL_VERSIONS, False, ('/some/path/proot', False)),
    (True, 0, "", does_not_raise(), {'use_proot_executable': "PROOT", 'proot_noseccomp': None}, "/some/path/proot",
     KERNEL_VERSIONS, True, ('PROOT', False)),
    (True, 0, "", does_not_raise(), {'use_proot_executable': "PROOT", 'proot_noseccomp': None}, "/some/path/proot",
     KERNEL_VERSIONS, True, ('PROOT', False)),
    (False, 1, "", pytest.raises(SystemExit), {'use_proot_executable': "PROOT", 'proot_noseccomp': None},
     "/some/path/proot", KERNEL_VERSIONS, False, ('PROOT', False)),
    (True, 0, "", does_not_raise(), {'use_proot_executable': "PROOT", 'proot_noseccomp': True},
     "/some/path/proot", KERNEL_VERSIONS, True, ('PROOT', True)),
])
@pytest.mark.parametrize('xmode', XMODE)
def test_02_select_proot(mocker, proot, mock_os_exists, mock_hostinfo, mock_fileutil, is_greater,
                         pathexists, is_seccomp_patched,
                         logger, logcount, msg, error, conf, pathexec, xmode, kernel, expected):
    """Test02 PRootEngine().select_proot()."""

    mocker.patch.object(Config, 'conf', conf)

    mock_os_exists.return_value = pathexists
    mock_fileutil.return_value.find_file_in_dir.return_value = pathexec
    mock_hostinfo.return_value.arch.return_value = 'amd64'
    mock_hostinfo.return_value.oskernel_isgreater.return_value = is_greater
    mock_fileutil.return_value.find_exec.return_value = pathexec

    mocker.patch.object(proot, '_is_seccomp_patched', return_value=is_seccomp_patched, autospec=True)

    with error:
        proot.select_proot()
        assert proot.executable == expected[0]
        assert proot.proot_noseccomp == (expected[1] if xmode != 'P2' else True)
        assert proot.proot_newseccomp == (True if is_seccomp_patched is True else False)
        assert logger.error.called == logcount


@pytest.mark.parametrize('xmode', XMODE)
@pytest.mark.parametrize('os_env,saved_os,kernel,output,expected', [
    ({'PROOT_NEW_SECCOMP': '1'}, {}, "4.8.0", [], True),
    ({'PROOT_NO_SECCOMP': '1'}, {}, "4.8.0", [], False),
    (None, {}, "4.8.0", [], False),
    (None, {"PROOT_NEW_SECCOMP": "1"}, "4.8.0", [], False),
    (None, {"PROOT_NEW_SECCOMP": "1"}, "4.1.0", [], True),
    (None, {"NOT_PROOT": "1"}, "4.1.0", [], False),
    (None, {}, "4.1.0", ["proot", ""], False),
    (None, {}, "4.1.0", ["", "proot"], True),
])
def test_03__is_seccomp_patched(mocker, proot, mock_get_output,
                                expected, os_env, saved_os, kernel, output):
    """Test03 PRootEngine()._is_seccomp_patched()."""
    mock_get_output.side_effect = output
    mocker.patch.object(proot, '_get_saved_osenv', return_value=saved_os, autospec=True)

    if os_env:
        mocker.patch.dict(os.environ, os_env)

    assert proot._is_seccomp_patched("/bin/sec") == expected


@pytest.mark.parametrize('xmode', ['P1', 'P2'])
@pytest.mark.parametrize('kernel', ['4.8.13'])
@pytest.mark.parametrize('uid,gid,expected', [
    ("0", "1001", ['-0']),
    ("1001", "0", ['-i', '1001:0']),
    ("1000", "1001", ['-i', '1000:1001']),
])
def test_03__set_uid_map(proot, uid, gid, expected):
    """Test03 PRootEngine()._set_uid_map()."""
    proot.opt['uid'] = uid
    proot.opt["gid"] = gid
    assert proot._set_uid_map() == expected


@pytest.mark.parametrize('kernel', KERNEL_VERSIONS)
@pytest.mark.parametrize('xmode', ['P1', 'P2'])
def test_04__create_mountpoint(proot):
    """Test04 PRootEngine()._create_mountpoint()."""
    assert proot._create_mountpoint("", "") is True


@pytest.mark.parametrize('xmode', ['P1'])
@pytest.mark.parametrize('kernel', ['4.8.13'])
@pytest.mark.parametrize("vol,expected", [
    ((), []),
    (("/tmp", "/bbb",), ['-b', '/tmp:/tmp', '-b', '/bbb:/bbb']),
    (("/tmp",), ['-b', '/tmp:/tmp']),
])
def test_05__get_volume_bindings(mocker, proot, vol, expected):
    """Test05 PRootEngine()._get_volume_bindings()."""
    mocker.patch.object(proot, 'opt', {'vol': vol})
    assert proot._get_volume_bindings() == expected


@pytest.mark.parametrize('xmode', ['P1'])
@pytest.mark.parametrize('kernel', ['4.8.13'])
@pytest.mark.parametrize("netcoop,portsmap,expected", [
    (None, {}, []),
    (None, {80: 8080}, ["-p", "80:8080"]),
    (None, {80: 8080, 443: 8443}, ["-p", "80:8080", "-p", "443:8443"]),
    (True, {80: 8080, 443: 8443, 53: 53}, ["-p", "80:8080", "-p", "443:8443", "-p", "53:53", "-n"]),
])
def test_06__get_network_map(mocker, proot, netcoop, portsmap, expected):
    """Test06 PRootEngine()._get_network_map()."""
    mocker.patch.object(proot, 'opt', {'netcoop': netcoop})
    mocker.patch.object(proot, '_get_portsmap', return_value=portsmap)
    assert proot._get_network_map() == expected

# FIXME: this test comment since needs change in the src code to pass

# @pytest.mark.parametrize('xmode', XMODE)
# @pytest.mark.parametrize('kernel', ['4.8.13'])
# @pytest.mark.parametrize('run_init,env_keys,opt_dict,oskernel_isgreater,loglevel,expected', [
#     (False, {}, {'cmd': [''], 'cwd': [], 'env': {}}, False, {'verbose_level': logging.DEBUG}, 2),
#     (True, {"PROOT_NO_SECCOMP": 1, "PROOT_NEW_SECCOMP": 1}, {'cmd': 'cmd', 'cwd': 'pwd', 'env': {}},
#      {'verbose_level': logging.DEBUG}, True, 1),
#     (True, {}, {'cmd': [''], 'cwd': [], 'env': {}}, False, {}, 1),
# ])
# def test_07_run(mocker, proot, container_id, run_init, expected, kernel, opt_dict, oskernel_isgreater, env_keys,
#                 loglevel):
#     """Test07 PRootEngine().run()."""
#
#     opt_dict.update({'kernel': kernel})
#     mocker.patch.object(proot, 'opt', opt_dict)
#
#     mocker.patch('udocker.engine.proot.HostInfo.oskernel_isgreater', return_value=oskernel_isgreater)
#     mocker.patch('udocker.engine.proot.subprocess.call', return_value=expected)
#     mocker.patch.dict('udocker.engine.proot.Config.conf', {'verbose_level': logging.DEBUG, 'proot_killonexit': False})
#     mocker.patch('udocker.engine.proot.os.getenv', side_effect=lambda key: env_keys.get(key, None))
#     mocker.patch('udocker.engine.proot.os.environ.update')
#
#     mocker.patch.object(proot, '_run_init', return_value=run_init)
#     mocker.patch.object(proot, 'select_proot')
#     mocker.patch.object(proot, '_run_env_set')
#     mocker.patch.object(proot, '_set_cpu_affinity', return_value=[])
#     mocker.patch.object(proot, '_get_qemu_string', return_value=[])
#     mocker.patch.object(proot, '_get_volume_bindings', return_value=[])
#     mocker.patch.object(proot, '_set_uid_map', return_value=[])
#     mocker.patch.object(proot, '_get_network_map', return_value=[])
#     mocker.patch.object(proot, '_run_banner', return_value=[])
#     mocker.patch.object(proot, '_run_env_cleanup_dict', return_value=None)
#
#     with mocker.patch('subprocess.call', return_value=expected):
#         status = proot.run(container_id=container_id)
#         assert proot.opt.get('env').get('PROOT_NO_SECCOMP') == (1 if env_keys.get("PROOT_NO_SECCOMP") else None)
#         assert proot.opt.get('env').get('PROOT_NEW_SECCOMP') == (1 if env_keys.get("PROOT_NEW_SECCOMP") else None)
#         assert proot._kernel == kernel if oskernel_isgreater else "6.0.0"
#         assert status == expected
