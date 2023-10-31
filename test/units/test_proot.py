#!/usr/bin/env python
"""
udocker unit tests: PRootEngine
"""
import logging
import os
import random
import subprocess
from contextlib import nullcontext as does_not_raise

import pytest

from udocker.config import Config
from udocker.engine.execmode import ExecutionMode
from udocker.engine.proot import PRootEngine
from udocker.helper.hostinfo import HostInfo
from udocker.utils.fileutil import FileUtil
from udocker.utils.uenv import Uenv
from udocker.utils.uprocess import Uprocess

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


@pytest.fixture
def logger(mocker):
    mocker_logger = mocker.patch('udocker.engine.proot.LOG')
    return mocker_logger


@pytest.mark.parametrize('kernel', KERNEL_VERSIONS)
@pytest.mark.parametrize('xmode', ['P1', 'P2'])
def test_01_init(proot, kernel):
    """Test01 PRootEngine() constructor."""
    assert proot.executable is None
    assert proot.proot_noseccomp is False
    assert proot.proot_newseccomp is False
    assert proot._kernel == kernel


@pytest.mark.parametrize('pathexists, logcount, msg,error, conf, pathexec, kernel, is_seccomp_patched, expected', [
    (True, 0, "", does_not_raise(), {'use_proot_executable': 'UDOCKER', 'proot_noseccomp': None, 'tmpdir': 'tmp'},
     "/some/path/proot",
     KERNEL_VERSIONS, False, ("/some/path/proot", False)),
    (True, 0, "", does_not_raise(), {'use_proot_executable': None, 'proot_noseccomp': None, 'tmpdir': 'tmp'},
     "/some/path/proot",
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
@pytest.mark.parametrize('is_greater', (True, False))
@pytest.mark.parametrize('xmode', XMODE)
def test_02_select_proot(mocker, proot, logger, is_greater, xmode, pathexists, logcount, msg, error, conf, pathexec,
                         kernel, is_seccomp_patched, expected):
    """Test02 PRootEngine().select_proot()."""
    mocker.patch.object(Config, 'conf', conf)
    mocker.patch.object(os.path, 'exists', return_value=pathexists)
    mocker.patch.object(FileUtil, 'find_file_in_dir', return_value=pathexec)
    mocker.patch.object(HostInfo, 'arch', return_value='amd64')
    mocker.patch.object(HostInfo, 'oskernel_isgreater', return_value=is_greater)
    mocker.patch.object(FileUtil, 'find_exec', return_value=pathexec)
    mocker.patch.object(proot, '_is_seccomp_patched', return_value=is_seccomp_patched, autospec=True)

    with error:
        proot.select_proot()
        assert proot.executable == expected[0]
        assert proot.proot_noseccomp == (expected[1] if xmode != 'P2' else True)
        assert proot.proot_newseccomp == (True if is_seccomp_patched is True else False)
        assert logger.error.called == logcount


@pytest.mark.parametrize('os_env, saved_os, kernel, output, expected', [
    ({'PROOT_NEW_SECCOMP': '1'}, {}, "4.8.0", [], True),
    ({'PROOT_NO_SECCOMP': '1'}, {}, "4.8.0", [], False),
    (None, {}, "4.8.0", [], False),
    (None, {"PROOT_NEW_SECCOMP": "1"}, "4.8.0", [], False),
    (None, {"PROOT_NEW_SECCOMP": "1"}, "4.1.0", [], True),
    (None, {"NOT_PROOT": "1"}, "4.1.0", [], False),
    (None, {}, "4.1.0", ["proot", ""], False),
    (None, {}, "4.1.0", ["", "proot"], True),
])
@pytest.mark.parametrize('xmode', XMODE)
def test_03__is_seccomp_patched(mocker, proot, os_env, saved_os, kernel, output, expected):
    """Test03 PRootEngine()._is_seccomp_patched()."""
    mocker.patch.object(Uprocess, 'get_output', side_effect=output, autospec=True)
    mocker.patch.object(proot, '_get_saved_osenv', return_value=saved_os, autospec=True)
    mocker.patch.dict(os.environ, os_env) if os_env else None

    is_seccomp_patched = proot._is_seccomp_patched("proot")

    assert is_seccomp_patched == expected


@pytest.mark.parametrize('uid, gid, expected', [
    ("0", "1001", ['-0']),
    ("1001", "0", ['-i', '1001:0']),
    ("1000", "1001", ['-i', '1000:1001']),
])
@pytest.mark.parametrize('xmode', ['P1', 'P2'])
@pytest.mark.parametrize('kernel', ['4.8.13'])
def test_03__set_uid_map(mocker, proot, uid, gid, expected):
    """Test03 PRootEngine()._set_uid_map()."""
    mocker.patch.object(proot, 'opt', {'uid': uid, 'gid': gid})

    set_uid_map = proot._set_uid_map()

    assert set_uid_map == expected


@pytest.mark.parametrize('kernel', KERNEL_VERSIONS)
@pytest.mark.parametrize('xmode', ['P1', 'P2'])
def test_04__create_mountpoint(proot):
    """Test04 PRootEngine()._create_mountpoint()."""
    create_mountpoint = proot._create_mountpoint("", "")

    assert create_mountpoint is True


@pytest.mark.parametrize("vol, expected", [
    ((), []),
    (("/tmp", "/bbb",), ['-b', '/tmp:/tmp', '-b', '/bbb:/bbb']),
    (("/tmp",), ['-b', '/tmp:/tmp']),
])
@pytest.mark.parametrize('xmode', ['P1'])
@pytest.mark.parametrize('kernel', ['4.8.13'])
def test_05__get_volume_bindings(mocker, proot, vol, expected):
    """Test05 PRootEngine()._get_volume_bindings()."""
    mocker.patch.object(proot, 'opt', {'vol': vol})

    get_volume_bindings = proot._get_volume_bindings()

    assert get_volume_bindings == expected


@pytest.mark.parametrize("netcoop, portsmap, expected", [
    (None, {}, []),
    (None, {80: 8080}, ["-p", "80:8080"]),
    (None, {80: 8080, 443: 8443}, ["-p", "80:8080", "-p", "443:8443"]),
    (True, {80: 8080, 443: 8443, 53: 53}, ["-p", "80:8080", "-p", "443:8443", "-p", "53:53", "-n"]),
])
@pytest.mark.parametrize('xmode', ['P1'])
@pytest.mark.parametrize('kernel', ['4.8.13'])
def test_06__get_network_map(mocker, proot, netcoop, portsmap, expected):
    """Test06 PRootEngine()._get_network_map()."""
    mocker.patch.object(proot, 'opt', {'netcoop': netcoop})
    mocker.patch.object(proot, '_get_portsmap', return_value=portsmap)

    assert proot._get_network_map() == expected


@pytest.mark.parametrize("qemu_return, expected", [
    ("qemu-x86_64", ["-q", "qemu-x86_64"]),
    (None, []),
    ("", []),
])
@pytest.mark.parametrize('kernel', ['4.8.13'])
@pytest.mark.parametrize('xmode', ['P1', 'P2'])
def test_07__get_qemu_string(mocker, proot, qemu_return, kernel, xmode, expected):
    mocker.patch.object(proot, '_get_qemu', return_value=qemu_return)

    result = proot._get_qemu_string()

    assert result == expected


@pytest.mark.parametrize('run_init, env_keys, opt_dict, oskernel_isgreater, loglevel, proot_killonexit, expected', [
    (False, {}, {'cmd': [''], 'cwd': [], 'env': {}}, False, logging.DEBUG, False, 2),
    (True, {"PROOT_NO_SECCOMP": '1', "PROOT_NEW_SECCOMP": '1'}, {'cmd': 'cmd', 'cwd': 'pwd', 'env': {}},
     True, logging.DEBUG, True, 1),
    (True, {"PROOT_NO_SECCOMP": '1', "PROOT_NEW_SECCOMP": '1'}, {'cmd': 'cmd', 'cwd': 'pwd', 'env': {}},
     True, logging.NOTSET, False, 1),
    (True, {}, {'cmd': [''], 'cwd': [], 'env': {}}, False, logging.NOTSET, False, 1),
])
@pytest.mark.parametrize('kernel', ['4.8.13'])
@pytest.mark.parametrize('xmode', XMODE)
def test_08_run(mocker, proot, container_id, kernel, run_init, env_keys, opt_dict, oskernel_isgreater, loglevel,
                proot_killonexit, expected):
    """Test07 PRootEngine().run()."""
    uenv_instance = Uenv()
    for key, value in env_keys.items():
        uenv_instance.append(f"{key}={value}")

    mocker.patch.object(proot, 'opt', {
        "env": uenv_instance,
        "cmd": opt_dict['cmd'],
        "cwd": opt_dict['cwd'],
        'kernel': kernel
    })

    mocker.patch.object(HostInfo, 'oskernel_isgreater', return_value=oskernel_isgreater)
    mocker.patch.object(subprocess, 'call', return_value=expected)
    mocker.patch.object(Config, 'conf', {'verbose_level': loglevel, 'proot_killonexit': proot_killonexit})
    mocker.patch.object(os, 'getenv', side_effect=lambda key: env_keys.get(key, None))
    mocker.patch.object(proot, '_run_init', return_value=run_init)
    mocker.patch.object(proot, 'select_proot')
    mocker.patch.object(proot, '_run_env_set')
    mocker.patch.object(proot, '_set_cpu_affinity', return_value=[])
    mocker.patch.object(proot, '_get_qemu_string', return_value=[])
    mocker.patch.object(proot, '_get_volume_bindings', return_value=[])
    mocker.patch.object(proot, '_set_uid_map', return_value=[])
    mocker.patch.object(proot, '_get_network_map', return_value=[])
    mocker.patch.object(proot, '_run_banner', return_value=[])
    mocker.patch.object(proot, '_run_env_cleanup_dict', return_value=None)
    mocker.patch.object(proot, '_has_option', return_value=True)

    with mocker.patch('subprocess.call', return_value=expected):
        status = proot.run(container_id=container_id)
        assert proot.opt.get('env').env == env_keys
        assert proot._kernel == kernel if oskernel_isgreater else "6.0.0"
        assert status == expected
