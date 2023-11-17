#!/usr/bin/env python
"""
udocker unit tests: RuncEngine
"""
import copy
import logging
import os
import platform
import random
import select
import stat
import subprocess
import sys
from contextlib import nullcontext as does_not_raise

import pytest

from udocker.config import Config
from udocker.engine.execmode import ExecutionMode
from udocker.engine.nvidia import NvidiaMode
from udocker.engine.runc import RuncEngine
from udocker.helper.hostinfo import HostInfo
from udocker.utils.filebind import FileBind
from udocker.utils.fileutil import FileUtil

XMODE = ["P1", "P2"]


@pytest.fixture
def container_id():
    return str(random.randint(1, 1000))


@pytest.fixture
def localrepo(mocker, container_id):
    mocker_local_repo = mocker.patch('udocker.container.localrepo.LocalRepository')
    mocker_local_repo.container_id = container_id
    mocker_local_repo.container_dir.return_value = "/.udocker/containers/" + container_id
    return mocker_local_repo


@pytest.mark.parametrize('xmode', XMODE)
def mock_exec_mode(localrepo, container_id, xmode):
    mocker_exec_mode = ExecutionMode(localrepo, container_id)
    mocker_exec_mode.force_mode = xmode
    return mocker_exec_mode


@pytest.fixture
def runc(localrepo, container_id):
    mock_runc = RuncEngine(localrepo, mock_exec_mode)
    mock_runc.container_id = container_id
    mock_runc._cont_specdir = localrepo.container_dir.return_value
    return mock_runc


@pytest.fixture
def logger(mocker):
    return mocker.patch('udocker.engine.runc.LOG')


@pytest.fixture(autouse=True)
@pytest.mark.parametrize('xmode', XMODE)
def mock_exec_mode(localrepo, container_id, xmode):
    mocker_exec_mode = ExecutionMode(localrepo, container_id)
    mocker_exec_mode.force_mode = xmode
    return mocker_exec_mode


@pytest.fixture(scope='function')
def fresh_runc(runc):
    new_runc = copy.deepcopy(runc)
    new_runc._cont_specjson = {"mounts": []}
    return new_runc


@pytest.mark.parametrize('xmode', XMODE)
def test_01_init(runc, localrepo):
    """Test01 RuncEngine() constructor."""
    assert runc.executable is None
    assert runc._cont_specjson is None
    assert runc._cont_specfile is None
    assert runc._cont_specdir == localrepo.container_dir.return_value
    assert runc._filebind is None
    assert runc.execution_id is None
    assert runc.engine_type == ""


@pytest.mark.parametrize(
    "conf, runc_path, crun_path, arch, find_file, os_exists, error, expected_exec, expected_type",
    [
        ("UDOCKER", None, None, "x86_64", None, False, pytest.raises(SystemExit), None, None),
        (None, "/bin/runc-arm", None, "x86_64", None, True, does_not_raise(), "/bin/runc-arm", "runc"),
        (None, None, "/bin/crun-arm", "x86_64", None, True, does_not_raise(), "/bin/crun-arm", "crun"),
        (None, None, None, "x86_64", "/bin/crun-arm-x86_64", True, does_not_raise(), "/bin/crun-arm-x86_64", "crun"),
        (None, None, None, "x86_64", "/bin/runc-arm-x86_64", True, does_not_raise(), "/bin/runc-arm-x86_64", "runc"),
        (None, None, None, "x86_64", "/bin/runc-arm-x86_64", False, pytest.raises(SystemExit), "/path/to/runc-x86",
         "runc"),
        (None, "runc-x86_64", None, "x86_64", "/path/to/runc-x86", True, does_not_raise(), "runc-x86_64", "runc"),
    ]
)
@pytest.mark.parametrize('xmode', XMODE)
def test_02_select_runc(mocker, runc, logger, conf, runc_path, crun_path, arch,
                        find_file, os_exists, error, expected_exec, expected_type):
    """Test02 RuncEngine().select_runc()."""
    mocker.patch.object(runc, 'executable', conf)
    mocker.patch.object(FileUtil, 'find_exec', side_effect=[runc_path, crun_path])
    mocker.patch.object(HostInfo, 'arch', return_value=arch)
    mocker.patch.object(FileUtil, 'find_file_in_dir', return_value=find_file)
    mocker.patch.object(os.path, 'exists', return_value=os_exists)
    mocker.patch.object(os.path, 'basename', return_value=expected_exec)

    with error:
        runc.select_runc()
        logger.error.assert_called_once_with(
            "runc/crun executable not found") if not os_exists else logger.error.assert_not_called()
        assert runc.executable == expected_exec
        assert runc.engine_type == expected_type


@pytest.mark.parametrize("verbose, new,size, subprocess, read_json, error, expected", [
    (logging.DEBUG, None, 0, 0, True, does_not_raise(), {'container': 'cxxx', 'parent': 'dyyy'}),
    (logging.NOTSET, False, -1, None, True, does_not_raise(), {"container": "cxxx", "parent": "dyyy"}),
    (logging.NOTSET, False, 0, 0, True, does_not_raise(), {"container": "cxxx", "parent": "dyyy"}),
    (logging.NOTSET, True, 0, 0, True, does_not_raise(), {"container": "cxxx", "parent": "dyyy"}),
    (logging.NOTSET, True, -1, 0, True, does_not_raise(), {"container": "cxxx", "parent": "dyyy"}),
    (logging.NOTSET, True, -1, 1, True, does_not_raise(), False),
    (logging.DEBUG, True, -1, 1, True, does_not_raise(), False),
    (logging.DEBUG, True, 0, 0, True, does_not_raise(), {"container": "cxxx", "parent": "dyyy"}),
    (logging.DEBUG, True, -1, 0, False, does_not_raise(), None),
    (logging.DEBUG, True, -1, 0, None, does_not_raise(), None)
])
@pytest.mark.parametrize('xmode', XMODE)
def test_03__load_spec(mocker, runc, verbose, new, size, subprocess, read_json, error, expected):
    """Test03 RuncEngine()._load_spec()."""

    mocker.patch.object(Config, 'conf', {'verbose_level': verbose, 'tmpdir': '/tmp'})
    mocker.patch.object(FileUtil, 'size', return_value=size)
    mocker.patch("subprocess.call", return_value=subprocess)
    mocker.patch.object(runc, '_cont_specjson')
    mocker.patch.object(FileUtil, 'register_prefix')
    mocker.patch.object(FileUtil, 'remove')

    jload = '{"container": "cxxx", "parent": "dyyy"}'
    mocker.patch("builtins.open", mocker.mock_open(read_data=jload)) if read_json else (
        mocker.patch("builtins.open", side_effect=OSError))

    with error:
        load_spec = runc._load_spec(new)
        assert load_spec == expected


@pytest.mark.parametrize("error,exception,expected", [
    (does_not_raise(), None, True),
    (does_not_raise(), OSError("fail"), False),
    (does_not_raise(), AttributeError("fail"), False),
])
@pytest.mark.parametrize('xmode', XMODE)
def test_04__save_spec(mocker, runc, error, exception, expected):
    """Test04 RuncEngine()._save_spec()."""
    mock_open = mocker.mock_open()
    mocker.patch("builtins.open", mock_open)
    mocker.patch("json.dump", side_effect=exception)

    with error:
        save_spec = runc._save_spec()
        assert save_spec == expected


@pytest.mark.parametrize("engine_type, isatty, opt, expected", [
    ("crun", True, {"hostname": "node.domain", "cwd": "/", "env": [], "cmd": "bash"},
     {'hostname': 'node.domain', 'process': {'args': 'bash', 'cwd': '/', 'env': [], 'terminal': False},
      'root': {'path': '/.udocker/containers/aaaaaa/ROOT', 'readonly': False}}),

    ("crun", True, {"hostname": "", "cwd": "/", "env": [], "cmd": "bash"},
     {'hostname': 'nodename.local', 'process': {'args': 'bash', 'cwd': '/', 'env': [], 'terminal': False},
      'root': {'path': '/.udocker/containers/aaaaaa/ROOT', 'readonly': False}}),

    ("crun", True, {"hostname": "", "cwd": "/", "env": [("AA", "aa"), ("BB", "bb")], "cmd": "bash"},
     {'hostname': 'nodename.local',
      'process': {'args': 'bash', 'cwd': '/', 'env': ['AA=aa', 'BB=bb'], 'terminal': False},
      'root': {'path': '/.udocker/containers/aaaaaa/ROOT', 'readonly': False}}),

    ("run", True, {"hostname": "", "cwd": "/", "env": [("AA", "aa"), ("BB", "bb")], "cmd": "bash"},
     {'hostname': 'nodename.local',
      'process': {'args': 'bash', 'cwd': '/', 'env': ['AA=aa', 'BB=bb'], 'terminal': True},
      'root': {'path': '/.udocker/containers/aaaaaa/ROOT', 'readonly': False}}),
])
@pytest.mark.parametrize('xmode', XMODE)
def test_05__set_spec(mocker, runc, engine_type, isatty, opt, expected):
    """Test05 RuncEngine()._set_spec()."""
    mocker.patch.object(os.path, 'realpath', return_value="/.udocker/containers/aaaaaa/ROOT")
    mocker.patch.object(platform, 'node', return_value="nodename.local")
    mocker.patch.object(sys.stdout, 'isatty', return_value=isatty)
    mocker.patch.object(runc, 'engine_type', engine_type)
    mocker.patch.object(runc, '_cont_specjson', {
        "root": {},
        "hostname": "",
        "process": {"cwd": "/", "terminal": "bash", "env": [], "args": []}
    })
    mocker.patch.object(runc, 'opt', opt)

    set_spec_json = runc._set_spec()

    assert set_spec_json == expected


@pytest.mark.parametrize("specjson, expected", [
    ({"linux": {}}, {"linux": {"uidMappings": [{"containerID": 0, "hostID": 1000, "size": 1}],
                               "gidMappings": [{"containerID": 0, "hostID": 1001, "size": 1}]}}),
    ({"linux": {"uidMappings": [{"containerID": 0, "size": 1}]}}, {
        "linux": {"uidMappings": [{"containerID": 0, "size": 1}],
                  "gidMappings": [{"containerID": 0, "hostID": 1001, "size": 1}]}}),
    ({"linux": {"uidMappings": [{"containerID": 0, "hostID": 999, "size": 1}]}}, {
        "linux": {"uidMappings": [{"containerID": 0, "hostID": 1000, "size": 1}],
                  "gidMappings": [{"containerID": 0, "hostID": 1001, "size": 1}]}}),
    ({"linux": {"uidMappings": [{"containerID": 0, "hostID": 999, "size": 1}],
                "gidMappings": [{"containerID": 0, "hostID": 999, "size": 1}]}}, {
         "linux": {"uidMappings": [{"containerID": 0, "hostID": 1000, "size": 1}],
                   "gidMappings": [{"containerID": 0, "hostID": 1001, "size": 1}]}}),
])
@pytest.mark.parametrize('xmode', XMODE)
def test_06__set_id_mappings(mocker, runc, specjson, expected):
    """Test06 RuncEngine()._set_id_mappings()."""
    mocker.patch.object(HostInfo, 'uid', 1000)
    mocker.patch.object(HostInfo, 'gid', 1001)
    mocker.patch.object(runc, '_cont_specjson', specjson)

    runc._set_id_mappings()

    assert runc._cont_specjson == expected


@pytest.mark.parametrize("initial_specjson, namespace_to_remove, error, expected", [
    ({"linux": {"namespaces": [{"type": "network"}, {"type": "docker"}]}}, "network", does_not_raise(),
     {"linux": {"namespaces": [{"type": "docker"}]}}),
    ({"linux": {"namespaces": [{"type": "network"}]}}, "docker", does_not_raise(),
     {"linux": {"namespaces": [{"type": "network"}]}}),
    ({"linux": {"namespaces": []}}, "network", does_not_raise(), {"linux": {"namespaces": []}}),
])
@pytest.mark.parametrize('xmode', XMODE)
def test_07__del_namespace_spec(runc, initial_specjson, namespace_to_remove, error, expected):
    """Test07 RuncEngine()._del_namespace_spec()."""
    runc._cont_specjson = initial_specjson
    runc._del_namespace_spec(namespace_to_remove)

    with error:
        assert runc._cont_specjson == expected


@pytest.mark.parametrize("opts, log_warning", [
    ({'user': "1000"}, True),
    ({'user': "0"}, False),
    ({'user': "root"}, False),
    ({}, False),
])
@pytest.mark.parametrize('xmode', XMODE)
def test_08__uid_check(mocker, runc, logger, opts, log_warning):
    """Test08 RuncEngine()._uid_check()."""
    mocker.patch.object(runc, 'opt', opts)

    runc._uid_check()

    logger.warning.assert_called_once_with(
        "this engine only supports execution as root") if log_warning else logger.warning.assert_not_called()


@pytest.mark.parametrize("capabilities, expected", [
    (["CAP_KILL", "CAP_NET_BIND_SERVICE", "CAP_CHOWN"], ["CAP_KILL", "CAP_NET_BIND_SERVICE", "CAP_CHOWN"]),
    (None, None),
])
@pytest.mark.parametrize('xmode', XMODE)
def test_09__add_capabilities_spec(mocker, runc, capabilities, expected):
    """Test09 RuncEngine()._add_capabilities_spec()."""
    mocker.patch.object(Config, "conf", {"runc_capabilities": capabilities})
    mocker.patch.object(runc, '_cont_specjson', {"process": {
        "capabilities": {
            "ambient": [],
            "bounding": [],
            "effective": [],
            "inheritable": [],
            "permitted": [],
        }
    }})

    runc._add_capabilities_spec()

    for capability_type in ["ambient", "bounding", "effective", "inheritable", "permitted"]:
        if expected:
            assert runc._cont_specjson["process"]["capabilities"][capability_type] == expected
        else:
            assert not runc._cont_specjson["process"]["capabilities"][capability_type]


@pytest.mark.parametrize("dev_path, os_exists, logger_msg, st_mode, mode, expected_filemode, expected_return", [
    ("/fakepath", False, ["device not found: %s"], stat.S_IFREG, "r", None, False),
    ("/fakepath/notdev/", True, ["device not found: %s"], stat.S_IFREG, "r", None, False),
    ("/dev/zero", True, ["not a device: %s"], stat.S_IFREG, "r", None, False),
    ("/dev/zero", True, [], stat.S_IFCHR, "r", 0o444, True),
    ("/dev/zeroblock", True, [], stat.S_IFBLK, "r", 0o444, True),
    ("/dev/zero", True, [], stat.S_IFCHR, "w", 0o222, True),
    ("/dev/zero", True, [], stat.S_IFCHR, "", 0o666, True),
])
@pytest.mark.parametrize('xmode', XMODE)
def test_10__add_device_spec(mocker, runc, logger, dev_path, os_exists, logger_msg, st_mode, mode, expected_filemode,
                             expected_return):
    """Test10 RuncEngine()._add_device_spec()."""
    mocker.patch.object(os.path, 'exists', return_value=os_exists)
    mocker.patch.object(os, 'minor', return_value=0)
    mocker.patch.object(os, 'major', return_value=6)
    mocked_stat = os.stat_result((st_mode, 0, 0, 0, 0, 0, 0, 0, 0, 0))
    mocker.patch.object(os, 'stat', return_value=mocked_stat)
    mocker.patch.object(runc, '_cont_specjson', {"linux": {"mocked_field": []}})
    mocker.patch.object(HostInfo, 'uid', 1000)
    mocker.patch.object(HostInfo, 'gid', 0)

    assert runc._add_device_spec(dev_path, mode) == expected_return

    if expected_return:
        expected_result = {"path": dev_path, "type": "c" if st_mode == stat.S_IFCHR else "b", "major": 6, "minor": 0,
                           "fileMode": expected_filemode, "uid": 1000, "gid": 0}
        assert runc._cont_specjson["linux"]["devices"][0] == expected_result
        logger.error.assert_not_called()
    else:
        logger.error.assert_called_once_with(logger_msg[0], dev_path)


@pytest.mark.parametrize("devices, nvidia_mode_return, nvidia_devices, expected_added", [
    ({'devices': ["/dev/open-mx", "/dev/myri0"]}, False, [], ["/dev/open-mx", "/dev/myri0"]),
    ({'devices': []}, True, ["/dev/nvidia"], ["/dev/nvidia"]),
    ({'devices': ["/dev/nvidia"]}, True, ["/dev/myri0", "/dev/open-mx"], ["/dev/myri0", "/dev/open-mx"]),
    ({'devices': ["/dev/nvidiactl"]}, True, ["/dev/open-mx", "/dev/myri0"], []),
])
@pytest.mark.parametrize('xmode', XMODE)
def test_11__add_devices(mocker, runc, devices, nvidia_mode_return, nvidia_devices, expected_added):
    """Test11 RuncEngine()._add_devices()."""
    add_device_spec = mocker.patch.object(runc, "_add_device_spec", return_value=True)
    mocker.patch.object(runc, 'opt', devices)
    mocker.patch.object(NvidiaMode, 'get_mode', return_value=nvidia_mode_return)
    mocker.patch.object(NvidiaMode, 'get_devices', return_value=nvidia_devices)

    runc._add_devices()

    calls = [mocker.call(device) for device in expected_added]
    add_device_spec.assert_has_calls(calls, any_order=True)


@pytest.mark.parametrize("rwmode, options, expected", [
    (True, None, {'destination': '/CONTDIR', 'options': ['rbind', 'nosuid', 'nodev', 'rw'], 'source': '/HOSTDIR',
                  'type': 'fstype'}),
    (False, None, {'destination': '/CONTDIR', 'options': ['rbind', 'nosuid', 'nodev', 'ro'], 'source': '/HOSTDIR',
                   'type': 'fstype'}),
    (True, ["option1", ], {'destination': '/CONTDIR', 'options': ['option1'], 'source': '/HOSTDIR', 'type': 'fstype'}),
    (False, ["option1", ],
     {'destination': '/CONTDIR', 'options': ['option1'], 'source': '/HOSTDIR', 'type': 'fstype'}),
    (None, ["option1", ],
     {'destination': '/CONTDIR', 'options': ['rbind', 'nosuid', 'nodev', 'ro'], 'source': '/HOSTDIR', 'type': 'none'}),
])
@pytest.mark.parametrize('xmode', XMODE)
def test_12__add_mount_spec(mocker, runc, rwmode, options, expected):
    """Test12 RuncEngine()._add_mount_spec()."""
    mocker.patch.object(runc, '_cont_specjson', {"mounts": []})
    host_source = "/HOSTDIR"
    cont_dest = "/CONTDIR"
    fstype = 'fstype'

    runc._add_mount_spec(host_source, cont_dest) if rwmode is None else runc._add_mount_spec(
        host_source, cont_dest, rwmode=rwmode, fstype=fstype, options=options)

    add_mount_spec = runc._cont_specjson["mounts"][0]
    assert add_mount_spec == expected


@pytest.mark.parametrize("index,initial_mount,host_source,cont_dest,expected", [
    # (0, [{"destination": "/CONTDIR", "source": "/HOSTDIR"}, ], "/HOSTDIR", "/CONTDIR", 0), #FIXME: this test fails need some changes in the code
    (None, [{"destination": "/XXXX", "source": "/HOSTDIR"}, ], "/HOSTDIR", "/CONTDIR", 1),
    (None, [{"destination": "/CONTDIR", "source": "XXXX"}, ], "/HOSTDIR", "/CONTDIR", 1),
    (1, [{"destination": "/CONTDIR", "source": "XXXX"}, {"destination": "/CONTDIR", "source": "/HOSTDIR"}],
     "/HOSTDIR", "/CONTDIR", 1),
])
@pytest.mark.parametrize('xmode', ["P1"])
def test_13__del_mount_spec(mocker, runc, index, initial_mount, host_source, cont_dest, expected):
    """Test13 RuncEngine()._del_mount_spec()."""
    mocker.patch.object(runc, '_cont_specjson', {"mounts": initial_mount})
    mocker.patch.object(runc, '_sel_mount_spec', return_value=index)
    runc._del_mount_spec(host_source, cont_dest)
    assert len(runc._cont_specjson["mounts"]) == expected
    # FIXME: this test needs changes in the code, also using more than one mode is affecting the results


@pytest.mark.parametrize("mount, host_source, cont_dest, expected", [
    ([{"destination": "/CONTDIR", "type": "none", "source": "/XXX"}], "/HOSTDIR", "/CONTDIR", None),
    ([{"destination": "/CONTDIR", "type": "none", "source": "/HOSTDIR"}, ], "/HOSTDIR", "/CONTDIR", 0),
    ([{"destination": "/CONTDIR", "type": "none", "source": "/XXXX"},
      {"destination": "/CONTDIR", "type": "none", "source": "/HOSTDIR"}], "/HOSTDIR", "/CONTDIR", 1),
])
@pytest.mark.parametrize('xmode', XMODE)
def test_14__sel_mount_spec(mocker, runc, mount, host_source, cont_dest, expected):
    """Test14 RuncEngine()._sel_mount_spec()."""
    mocker.patch.object(runc, '_cont_specjson', {"mounts": mount})
    sel_mount_spec = runc._sel_mount_spec(host_source, cont_dest)
    assert sel_mount_spec == expected


# FIXME: this test fails, need to be fixed
@pytest.mark.parametrize("mount,host_source,cont_dest,new_data,expected_mounts,expected", [
    ([], "/HOSTDIR", "/CONTDIR", {}, [], False),
    ([], "/HOSTDIR", "/CONTDIR", {"options": ["a", "su"]}, [], False),
    # ([{"destination": "/CONTDIR", "type": "none", "source": "/HOSTDIR", "options": ["b"]}], "/HOSTDIR", "/CONTDIR",
    #  {"options": ["c", "su"]},
    #  [{"destination": "/CONTDIR", "type": "none", "source": "/HOSTDIR", "options": ["b", "c", "su"]}], True), # FIXME: this test fails may need some changes in the code if the scenarios is correctly defined
])
@pytest.mark.parametrize('xmode', XMODE)
def test_15__mod_mount_spec(mocker, fresh_runc, mount, host_source, cont_dest, new_data, expected_mounts, expected):
    """Test15 RuncEngine()._mod_mount_spec()."""

    mocker.patch.object(fresh_runc, '_cont_specjson', {"mounts": mount})
    result = fresh_runc._mod_mount_spec(host_source, cont_dest, new_data)

    assert result == expected
    assert fresh_runc._cont_specjson["mounts"] == expected_mounts
    # FIXME: this test fails, need to be fixed


@pytest.mark.parametrize(
    "volumes, isdir, isfile, sysdirs_list, log_warning, log_error, expected_method_calls", [
        ([], False, False, [], (0, ""), (0, ""),
         [('add_mount_spec', 1)]),
        (['/HOSTDIR:/CONTDIR'], False, False, [], (0, ""), (0, ""), [('isdir', 1), ('isfile', 1)]),
        (
                ['/HOSTDIR:/CONTDIR'], True, False, [], (0, ""), (0, ""),
                [('isdir', 1), ('isfile', 0), ('add_mount_spec', 2)]),
        (['/dev'], True, False, [], (1, 'engine does not support -v %s'), (0, ""),
         [('isdir', 1), ('isfile', 0), ('add_mount_spec', 1)]),
        (['/HOSTDIR:/CONTDIR'], False, True, ["/HOSTDIR"], (0, ""), (0, ""),
         [('isdir', 1), ('isfile', 1), ('add_mount_spec', 1), ('add_file', 1)]),
        (['/HOSTDIR:/CONTDIR'], False, True, ["/HOSTDIR"], (0, ""), (0, ""),
         [('isdir', 1), ('isfile', 1), ('add_mount_spec', 1), ('add_file', 1)]),
        (['/dev:/CONTDIR'], True, False, ["/HOSTDIR"], (1, 'engine does not support -v %s'),
         (0, ""),
         [('isdir', 1), ('isfile', 0), ('add_mount_spec', 1), ('add_file', 0)]),
        (['/dev:/CONTDIR'], False, True, ["/HOSTDIR"], (0, ""),
         (1, 'engine does not support file mounting: %s'),
         [('isdir', 1), ('isfile', 1), ('add_mount_spec', 1), ('add_file', 0)]),
    ])
@pytest.mark.parametrize('xmode', XMODE)
def test_16__add_volume_bindings(mocker, runc, logger, volumes, isdir, isfile, sysdirs_list, log_warning, log_error,
                                 expected_method_calls):
    """Test16 RuncEngine()._add_volume_bindings()."""
    mocker.patch.object(runc, '_filebind', autospec=True)
    mock_isdir = mocker.patch('os.path.isdir', return_value=isdir)
    mock_isfile = mocker.patch('os.path.isfile', return_value=isfile)
    mock_add_mount_spec = mocker.patch.object(runc, '_add_mount_spec')
    mock_add_file = mocker.patch.object(runc._filebind, 'add_file')
    mocker.patch.object(Config, 'conf', {'sysdirs_list': sysdirs_list, 'mountpoint_prefixes': []})
    mocker.patch.object(runc, 'opt', {'vol': volumes})
    mocker.patch.object(runc._filebind, 'start', return_value=("/HOSTDIR", "/CONTDIR"))

    runc._add_volume_bindings()

    logger.warning.assert_called_once_with(
        log_warning[1], mocker.ANY) if log_warning[0] > 0 else logger.warning.assert_not_called()

    logger.error.assert_called_once_with(
        log_error[1], mocker.ANY) if log_error[0] > 0 else logger.error.assert_not_called()

    for method_name, call_count in expected_method_calls:
        assert locals()[f'mock_{method_name}'].call_count == call_count


#
@pytest.mark.parametrize("options, expected_logs", [
    ({"portsmap": None, 'netcoop': None}, []),
    ({"portsmap": True, 'netcoop': None}, ['this execution mode does not support -p --publish']),
    ({"portsmap": None, "netcoop": True}, ['this exec mode does not support -P --netcoop --publish-all']),
    ({"portsmap": True, "netcoop": True}, ['this execution mode does not support -p --publish',
                                           'this exec mode does not support -P --netcoop --publish-all'])
])
@pytest.mark.parametrize('xmode', XMODE)
def test_17__run_invalid_options(mocker, runc, logger, options, expected_logs):
    """Test17 RuncEngine()._run_invalid_options()."""
    mocker.patch.object(runc, 'opt', options)

    runc._run_invalid_options()

    assert logger.warning.call_count == len(expected_logs)
    assert all(logger.warning.call_any(msg) for msg in expected_logs)


@pytest.mark.parametrize("xmode, executable, proot_noseccomp, expected_env, expected_cont_specjson, expected", [
    ("P1", "", False, None, [], False),
    ("P2", "", False, None, [], False),
    ("R2", "/bin/exec", False, [], ['/.udocker/bin/custom_folder', '-0', 'ls -la'], True),
    ("R3", "/bin/exec", False, ['PROOT_NO_SECCOMP=1'], ['/.udocker/bin/custom_folder', '-0', 'ls -la'], True),
    ("P1", "", True, None, [], False),
    ("P2", "", True, None, [], False),
    ("R2", "/bin/exec", True, [], ['/.udocker/bin/custom_folder', '-0', 'ls -la'], True),
    ("R3", "/bin/exec", True, ['PROOT_NO_SECCOMP=1'], ['/.udocker/bin/custom_folder', '-0', 'ls -la'], True),
])
def test_18__proot_overlay(mocker, runc, xmode, executable, proot_noseccomp, expected_env, expected_cont_specjson,
                           expected):
    """Test18 RuncEngine()._proot_overlay()."""
    runc.exec_mode.get_mode = mocker.Mock(return_value=xmode)
    mocker.patch.object(os.path, 'basename', return_value="custom_folder")
    mocker.patch('udocker.engine.runc.PRootEngine', return_value=mocker.Mock())
    mocker.patch.object(FileUtil, 'chmod', return_value=True)
    mocker.patch.object(runc, '_cont_specjson', {"process": {"env": [], "args": []}})
    mocker.patch.object(runc, 'opt', {"cmd": ["ls -la"]})
    mocker.patch.object(runc, '_create_mountpoint')
    mocker.patch.object(runc, '_filebind')

    result = runc._proot_overlay()
    assert result == expected

    if expected:
        runc_cont_specjson = runc._cont_specjson
        assert runc_cont_specjson["process"]["args"] == expected_cont_specjson
        assert runc_cont_specjson["process"]["env"] == expected_env
        assert runc._filebind.set_file.call_count == 1
        assert runc._filebind.add_file.call_count == 1
        assert runc._create_mountpoint.call_count == 1


@pytest.mark.parametrize(
    "log_level, init_result, load_spec, load_spec_new, container_dir, iswriteable_container, is_tty, expected, call",
    [
        (logging.NOTSET, False, True, False, None, True, False, 2, []),
        (logging.NOTSET, True, True, True, True, True, False, 0, ["_load_spec"]),
        (logging.NOTSET, True, True, False, "/.udocker/containers/aaaaaa", True, False, 4, []),
        (logging.NOTSET, False, True, False, "/.udocker/containers/aaaaaa", True, False, 2, []),
        (logging.NOTSET, False, True, False, None, False, False, 2, []),
        (logging.NOTSET, True, True, True, None, False, False, 0, ["_load_spec"]),
        (logging.NOTSET, False, True, True, "/.udocker/containers/aaaaaa", False, False, 2, []),
        (logging.NOTSET, True, True, True, "/.udocker/containers/aaaaaa", False, False, 0, ["_load_spec"]),
        (logging.DEBUG, True, True, True, "/.udocker/containers/aaaaaa", True, False, 0, ["_load_spec"]),
        (logging.NOTSET, True, True, True, "/.udocker/containers/aaaaaa", True, False, 0, ["_load_spec"]),
        (logging.NOTSET, True, True, True, "/.udocker/containers/aaaaaa", True, True, 0, ["_load_spec", "run_pty"]),
    ])
@pytest.mark.parametrize('xmode', XMODE)
def test_19_run(mocker, runc, log_level, init_result, load_spec, load_spec_new, container_dir,
                iswriteable_container, is_tty, expected, call):
    """Test19 RuncEngine().run()."""
    mocker.patch.object(runc.localrepo, 'cd_container', return_value=container_dir)
    mocker.patch.object(runc, '_run_init', return_value=init_result)
    mocker.patch.object(runc, '_check_arch')
    mocker.patch.object(runc, '_run_invalid_options')
    mocker.patch.object(runc, '_load_spec', side_effect=lambda new: load_spec_new if new else load_spec)
    mocker.patch.object(runc, '_run_env_cleanup_list')
    mocker.patch.object(runc, '_run_env_set')
    mocker.patch.object(runc, '_set_spec')
    mocker.patch.object(runc, '_del_mount_spec')
    mocker.patch.object(runc, '_del_namespace_spec')
    mocker.patch.object(runc, '_set_id_mappings')
    mocker.patch.object(runc, '_add_volume_bindings')
    mocker.patch.object(runc, '_add_devices')
    mocker.patch.object(runc, '_add_capabilities_spec')
    mocker.patch.object(runc, '_mod_mount_spec')
    mocker.patch.object(runc, '_proot_overlay')
    mocker.patch.object(runc, '_save_spec')
    mocker.patch.object(sys.stdout, 'isatty', return_value=is_tty)
    mocker.patch.object(runc, 'run_pty', return_value=0)
    mocker.patch.object(runc, 'run_nopty', return_value=0)
    mocker.patch.object(runc, '_uid_check')
    mocker.patch.object(runc, 'select_runc')
    mocker.patch.object(runc, '_run_banner')
    mocker.patch.object(runc, '_set_cpu_affinity', return_value=[0, ])
    mocker.patch.object(os.path, 'realpath', return_value='/path/to/docker')

    mocker.patch.object(runc, 'opt', {'cmd': ['ls', '-la']})
    mocker.patch.object(Config, 'conf', {'runc_nomqueue': True, 'tmpdir': '/tmp', 'use_runc_executable': True,
                                         'verbose_level': log_level})

    mocker.patch.object(runc.localrepo, 'iswriteable_container', return_value=iswriteable_container)
    mocker.patch.object(runc, 'container_dir', return_value="/.udocker/containers/aaaaaa")

    result = runc.run("acdea16-8264a08-f9aaca0d-fc82ff34")
    assert result == expected

    for expected_call in call:
        mocker_method = getattr(runc, expected_call)
        mocker_method.assert_called_once()


@pytest.mark.parametrize("subprocess_return,expected", [(0, 0), (1, 1)])
@pytest.mark.parametrize('xmode', XMODE)
def test_20_run_pty(mocker, runc, subprocess_return, expected):
    """Test20 RuncEngine().run_pty()."""
    mocker.patch.object(runc, '_filebind', return_value=mocker.Mock())
    mocker.patch.object(subprocess, 'call', return_value=subprocess_return)

    assert runc.run_pty(["CONTAINERID"]) == expected
    runc._filebind.finish.assert_called_once()


@pytest.mark.parametrize("poll_return, select_return, read_raises, terminate_raises, expected", [
    (0, ([1, ], [], []), False, False, 0),
    (0, ([1, ], [], []), False, True, 0),
    (None, ([], [], [1, ]), False, False, None),
    (None, ([1, ], [], []), True, False, None),
], ids=[
    "process ends normally, data read without any errors",
    "process termination throws an exception,returns normal code",
    "process is ongoing without any data to read and no errors",
    "process is running, data is available, but an error occurs when attempting to read it",
])
@pytest.mark.parametrize('xmode', XMODE)
def test_21_run_nopty(mocker, runc, poll_return, select_return, read_raises, terminate_raises, expected):
    """Test21 RuncEngine().run_nopty()."""

    mocked_process = mocker.Mock(spec=subprocess.Popen)
    mocked_process.poll.return_value = [poll_return, 0]
    mocked_process.terminate.side_effect = [2]
    mocked_process.returncode = poll_return
    mocker.patch.object(subprocess, 'Popen', return_value=mocked_process)
    mocker.patch.object(os, 'openpty', return_value=(1, 2))
    mocker.patch.object(os, 'close')
    mocker.patch.object(select, 'select', return_value=select_return)
    mocker.patch.object(os, 'read', side_effect=OSError()) if read_raises else mocker.patch.object(
        os, 'read', return_value=b'x')
    mocker.patch.object(runc, '_filebind', return_value=mocker.Mock())
    mocker.patch.object(runc._filebind, 'finish', return_value=mocker.Mock())

    if terminate_raises:
        mocked_process.terminate.side_effect = OSError()

    result = runc.run_nopty(["some_cmd"])
    subprocess.Popen.assert_called_once_with(["some_cmd"], shell=False, close_fds=False, stdout=2, stderr=2)
    runc._filebind.finish.assert_called_once()
    assert result.returncode == expected
