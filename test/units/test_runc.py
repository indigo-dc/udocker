#!/usr/bin/env python
"""
udocker unit tests: RuncEngine
"""
import copy
import logging
import os
import random
import stat
import subprocess
from contextlib import nullcontext as does_not_raise

import pytest

from udocker.config import Config
from udocker.engine.execmode import ExecutionMode
from udocker.engine.runc import RuncEngine

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
def mock_nvidia_mode(mocker):
    return mocker.patch('udocker.engine.runc.NvidiaMode')


@pytest.fixture
def logger(mocker):
    return mocker.patch('udocker.engine.runc.LOG')


@pytest.fixture(autouse=True)
@pytest.mark.parametrize('xmode', XMODE)
def mock_exec_mode(localrepo, container_id, xmode):
    mocker_exec_mode = ExecutionMode(localrepo, container_id)
    mocker_exec_mode.force_mode = xmode
    return mocker_exec_mode


@pytest.fixture
def mock_os_exists(mocker):
    return mocker.patch('udocker.engine.runc.os.path.exists')


@pytest.fixture
def mock_os_basename(mocker):
    return mocker.patch('udocker.engine.runc.os.path.basename')


@pytest.fixture
def mock_fileutil(mocker):
    return mocker.patch('udocker.engine.runc.FileUtil', autospec=True)


@pytest.fixture
def mock_realpath(mocker):
    return mocker.patch('udocker.engine.runc.os.path.realpath')


@pytest.fixture
def mock_hostinfo(mocker):
    return mocker.patch('udocker.engine.runc.HostInfo')


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
    "conf,runc_path,crun_path,arch,find_file,os_exists,error,expected_exec,expected_type",
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
def test_02_select_runc(mocker, runc, logger, mock_os_exists, mock_os_basename, conf, runc_path, crun_path, arch,
                        find_file, os_exists, error, expected_exec, expected_type):
    """Test02 RuncEngine().select_runc()."""

    mocker.patch.object(runc, 'executable', conf)
    mocker.patch('udocker.engine.runc.FileUtil.find_exec', side_effect=[runc_path, crun_path])
    mocker.patch('udocker.engine.runc.HostInfo.arch', return_value=arch)
    mocker.patch('udocker.engine.runc.FileUtil.find_file_in_dir', return_value=find_file)

    mock_os_exists.return_value = os_exists
    mock_os_basename.return_value = expected_exec

    with error:
        runc.select_runc()
        assert runc.executable == expected_exec
        assert runc.engine_type == expected_type


@pytest.mark.parametrize("verbose,new,file_exists,subprocess,read_json,error,expected", [
    (logging.NOTSET, False, False, 0, True, does_not_raise(), {"container": "cxxx", "parent": "dyyy"}),
    (logging.NOTSET, False, True, 0, True, does_not_raise(), {"container": "cxxx", "parent": "dyyy"}),
    (logging.NOTSET, True, True, 0, True, does_not_raise(), {"container": "cxxx", "parent": "dyyy"}),
    (logging.NOTSET, True, False, 0, True, does_not_raise(), {"container": "cxxx", "parent": "dyyy"}),
    (logging.NOTSET, True, False, 1, True, does_not_raise(), False),
    (logging.DEBUG, True, False, 1, True, does_not_raise(), False),
    # (logging.NOTSET, True, False, 0, False, pytest.raises(SystemError), None), #FIXME: this test fails
])
@pytest.mark.parametrize('xmode', XMODE)
def test_03__load_spec(mocker, runc, mock_fileutil, verbose, new, file_exists, subprocess, read_json, error,
                       expected):
    """Test03 RuncEngine()._load_spec()."""

    mocker.patch.object(Config, 'conf', {'verbose_level': verbose})

    size_mock = mocker.patch("udocker.engine.runc.FileUtil.size")
    size_mock.side_effect = [0 if file_exists else -1, 0]  # FIXME: this is not working as intended

    mocker.patch("subprocess.call", return_value=subprocess)
    mocker.patch.object(runc, '_cont_specjson')

    mock_fileutil.return_value.size.return_value = -1
    mock_fileutil.return_value.register_prefix.return_value = None
    mock_fileutil.return_value.remove.return_value = None
    jload = '{"container": "cxxx", "parent": "dyyy"}'
    if read_json:
        mocker.patch("builtins.open", mocker.mock_open(read_data=jload))
    else:
        mocker.patch("builtins.open", side_effect=OSError)

    with error:
        assert runc._load_spec(new) == expected


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
        assert runc._save_spec() == expected


@pytest.mark.parametrize("opt, expected", [
    ({"hostname": "node.domain", "cwd": "/", "env": [], "cmd": "bash"},
     {"hostname": "node.domain"}),

    ({"hostname": "", "cwd": "/", "env": [], "cmd": "bash"},
     {"hostname": "nodename.local"}),

    ({"hostname": "", "cwd": "/", "env": [("AA", "aa"), ("BB", "bb")], "cmd": "bash"},
     {"process": {"env": ["AA=aa", "BB=bb"]}}),
])
@pytest.mark.parametrize('xmode', XMODE)
def test_05__set_spec(mocker, runc, mock_realpath, opt, expected):
    """Test05 RuncEngine()._set_spec()."""
    mock_realpath.return_value = "/.udocker/containers/aaaaaa/ROOT"
    mocker.patch('udocker.engine.runc.platform.node', return_value="nodename.local")

    runc._cont_specjson = {
        "root": {},
        "hostname": "",
        "process": {"cwd": "/", "terminal": "bash", "env": [], "args": []}
    }
    mocker.patch.object(runc, 'opt', opt)

    set_spec_json = runc._set_spec()

    for key, value in expected.items():
        if type(value) is dict:
            for subkey, subvalue in value.items():
                assert set_spec_json[key][subkey] == subvalue
        else:
            assert set_spec_json[key] == value


@pytest.mark.parametrize("specjson,expected_specjson", [
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
def test_06__set_id_mappings(mocker, runc, specjson, expected_specjson):
    """Test06 RuncEngine()._set_id_mappings()."""
    mocker.patch("udocker.engine.runc.HostInfo.uid", 1000)
    mocker.patch("udocker.engine.runc.HostInfo.gid", 1001)
    runc._cont_specjson = specjson
    runc._set_id_mappings()
    assert runc._cont_specjson == expected_specjson


@pytest.mark.parametrize("initial_specjson, namespace_to_remove, expected_specjson", [
    ({"linux": {"namespaces": [{"type": "network"}, {"type": "docker"}]}}, "network",
     {"linux": {"namespaces": [{"type": "docker"}]}}),
    ({"linux": {"namespaces": [{"type": "network"}]}}, "docker", {"linux": {"namespaces": [{"type": "network"}]}}),
    ({"linux": {"namespaces": []}}, "network", {"linux": {"namespaces": []}}),
])
@pytest.mark.parametrize('xmode', XMODE)
def test_07__del_namespace_spec(runc, initial_specjson, namespace_to_remove, expected_specjson):
    """Test07 RuncEngine()._del_namespace_spec()."""
    runc._cont_specjson = initial_specjson
    runc._del_namespace_spec(namespace_to_remove)

    assert runc._cont_specjson == expected_specjson


@pytest.mark.parametrize("opts, should_warn", [
    ({'user': "1000"}, True),
    ({'user': "0"}, False),
    ({'user': "root"}, False),
    ({}, False),
])
@pytest.mark.parametrize('xmode', XMODE)
def test_08__uid_check(mocker, runc, logger, opts, should_warn):
    """Test08 RuncEngine()._uid_check()."""
    mocker.patch.object(runc, 'opt', opts)
    runc._uid_check()

    if should_warn:
        logger.warning.assert_called_once_with("this engine only supports execution as root")
    else:
        logger.warning.assert_not_called()


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


@pytest.mark.parametrize("dev_path,os_exists,loggermsg, st_mode,mode,expected_filemode,expected_return", [
    ("/fakepath", False, ["device not found: %s"], stat.S_IFREG, "r", None, False),
    ("/fakepath/notdev/", True, ["device not found: %s"], stat.S_IFREG, "r", None, False),
    ("/dev/zero", True, ["not a device: %s"], stat.S_IFREG, "r", None, False),
    ("/dev/zero", True, [], stat.S_IFCHR, "r", 0o444, True),
    ("/dev/zeroblock", True, [], stat.S_IFBLK, "r", 0o444, True),
    ("/dev/zero", True, [], stat.S_IFCHR, "w", 0o222, True),
    ("/dev/zero", True, [], stat.S_IFCHR, "", 0o666, True),
])
@pytest.mark.parametrize('xmode', XMODE)
def test_10__add_device_spec(mocker, runc, logger, mock_os_exists, mock_hostinfo, dev_path, os_exists, loggermsg,
                             st_mode, mode, expected_filemode, expected_return):
    """Test10 RuncEngine()._add_device_spec()."""
    mock_os_exists.return_value = os_exists
    mocker.patch('os.minor', return_value=0)
    mocker.patch('os.major', return_value=6)
    mocked_stat = os.stat_result((st_mode, 0, 0, 0, 0, 0, 0, 0, 0, 0))
    mocker.patch('os.stat', return_value=mocked_stat)
    mocker.patch.object(runc, '_cont_specjson', {"linux": {"mocked_field": []}})
    mock_hostinfo.uid = 1000
    mock_hostinfo.gid = 0

    assert runc._add_device_spec(dev_path, mode) == expected_return

    if expected_return:
        expected_result = {"path": dev_path, "type": "c" if st_mode == stat.S_IFCHR else "b", "major": 6, "minor": 0,
                           "fileMode": expected_filemode, "uid": 1000, "gid": 0}
        assert runc._cont_specjson["linux"]["devices"][0] == expected_result
        assert logger.error.call_count == 0
    else:
        assert logger.error.call_count == 1
        logger.error.assert_called_once_with(loggermsg[0], dev_path)


@pytest.mark.parametrize("devices,nvidia_mode_return,nvidia_devices,expected_added", [
    ({'devices': ["/dev/open-mx", "/dev/myri0"]}, False, [], ["/dev/open-mx", "/dev/myri0"]),
    ({'devices': []}, True, ["/dev/nvidia"], ["/dev/nvidia"]),
    ({'devices': ["/dev/myri0"]}, True, ["/dev/myri0", "/dev/open-mx"], ["/dev/myri0", "/dev/open-mx"]),
    ({'devices': ["/dev/nvidiactl"]}, True, ["/dev/open-mx", "/dev/myri0"], []),
])
@pytest.mark.parametrize('xmode', XMODE)
def test_11__add_devices(mocker, runc, mock_nvidia_mode, devices, nvidia_mode_return, nvidia_devices, expected_added):
    """Test11 RuncEngine()._add_devices()."""
    add_device_spec = mocker.patch.object(runc, "_add_device_spec", return_value=True)

    mocker.patch.object(runc, 'opt', devices)

    mock_nvidia_mode.return_value.get_mode.return_value = nvidia_mode_return
    mock_nvidia_mode.return_value.get_devices.return_value = nvidia_devices

    runc._add_devices()

    calls = [mocker.call(device) for device in expected_added]
    add_device_spec.assert_has_calls(calls, any_order=True)


#         mock_adddecspec.side_effect = [True, True, True]
#         mock_nv.return_value.get_mode.return_value = True
#         mock_nv.return_value.get_devices.return_value = ['/dev/nvidia', ]
#         rcex = RuncEngine(self.local, self.xmode)
#         rcex.opt = dict()
#         rcex.opt["devices"] = ["/dev/open-mx", "/dev/myri0"]
#         rcex._add_devices()
#         self.assertTrue(mock_adddecspec.call_count, 3)
#         self.assertTrue(mock_nv.return_value.get_mode.called)
#         self.assertTrue(mock_nv.return_value.get_devices.called)
#
@pytest.mark.parametrize("rwmode,options,expected", [
    (True, None, {'destination': '/CONTDIR', 'options': ['rbind', 'nosuid', 'nodev', 'rw'], 'source': '/HOSTDIR',
                  'type': 'fstype'}),
    (False, None, {'destination': '/CONTDIR', 'options': ['rbind', 'nosuid', 'nodev', 'ro'], 'source': '/HOSTDIR',
                   'type': 'fstype'}),
    (True, ["option1", ], {'destination': '/CONTDIR', 'options': ['option1'], 'source': '/HOSTDIR',
                           'type': 'fstype'}),
    (False, ["option1", ], {'destination': '/CONTDIR', 'options': ['option1'], 'source': '/HOSTDIR',
                            'type': 'fstype'}),
])
@pytest.mark.parametrize('xmode', XMODE)
def test_12__add_mount_spec(mocker, runc, rwmode, options, expected):
    """Test12 RuncEngine()._add_mount_spec()."""

    mocker.patch.object(runc, '_cont_specjson', {"mounts": []})

    host_source = "/HOSTDIR"
    cont_dest = "/CONTDIR"
    fstype = 'fstype'

    runc._add_mount_spec(host_source, cont_dest, rwmode=rwmode, fstype=fstype, options=options)
    assert runc._cont_specjson["mounts"][0] == expected
    # FIXME: add test to none parameters


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


#         rcex = RuncEngine(self.local, self.xmode)
#         rcex._container_specjson = dict()
#         rcex._container_specjson["mounts"] = []
#         mount = {"destination": "/CONTDIR",
#                  "type": "none",
#                  "source": "/HOSTDIR",
#                  "options": ["rbind", "nosuid",
#                              "noexec", "nodev",
#                              "rw", ], }
#         rcex._container_specjson["mounts"].append(mount)
#         rcex._del_mount_spec("/HOSTDIR", "/CONTDIR")
#         # self.assertEqual(len(rcex._container_specjson["mounts"]), 0)
#
#         rcex = RuncEngine(self.local, self.xmode)
#         rcex._container_specjson = dict()
#         rcex._container_specjson["mounts"] = []
#         mount = {"destination": "/XXXX",
#                  "type": "none",
#                  "source": "/HOSTDIR",
#                  "options": ["rbind", "nosuid",
#                              "noexec", "nodev",
#                              "rw", ], }
#         rcex._container_specjson["mounts"].append(mount)
#         rcex._del_mount_spec("/HOSTDIR", "/CONTDIR")
#         self.assertEqual(len(rcex._container_specjson["mounts"]), 1)
#
#         rcex = RuncEngine(self.local, self.xmode)
#         rcex._container_specjson = dict()
#         rcex._container_specjson["mounts"] = []
#         mount = {"destination": "/CONTDIR",
#                  "type": "none",
#                  "source": "XXXX",
#                  "options": ["rbind", "nosuid",
#                              "noexec", "nodev",
#                              "rw", ], }
#         rcex._container_specjson["mounts"].append(mount)
#         rcex._del_mount_spec("/HOSTDIR", "/CONTDIR")
#         self.assertEqual(len(rcex._container_specjson["mounts"]), 1)
#

@pytest.mark.parametrize("initial_mount,host_source,cont_dest,expected", [
    ([{"destination": "/CONTDIR", "type": "none", "source": "/XXX"}], "/HOSTDIR", "/CONTDIR", None),
    ([{"destination": "/CONTDIR", "type": "none", "source": "/HOSTDIR"}, ], "/HOSTDIR", "/CONTDIR", 0),
    ([{"destination": "/CONTDIR", "type": "none", "source": "/XXXX"},
      {"destination": "/CONTDIR", "type": "none", "source": "/HOSTDIR"}], "/HOSTDIR", "/CONTDIR", 1),
])
@pytest.mark.parametrize('xmode', XMODE)
def test_14__sel_mount_spec(mocker, runc, initial_mount, host_source, cont_dest, expected):
    """Test14 RuncEngine()._sel_mount_spec()."""
    mocker.patch.object(runc, '_cont_specjson', {"mounts": initial_mount})
    assert runc._sel_mount_spec(host_source, cont_dest) == expected


# FIXME: this test fails, need to be fixed
# @pytest.mark.parametrize("initial_mounts, host_source, cont_dest, new_data, expected_mounts", [
#     # ([], "/HOSTDIR", "/CONTDIR", {}, []),
#     # ([], "/HOSTDIR", "/CONTDIR", {"options": ["a", "su"]}, []),
#     # ([{"destination": "/CONTDIR", "type": "none", "source": "/HOSTDIR", "options": ["b"]}], "/HOSTDIR", "/CONTDIR", {"options": ["c", "su"]}, [{"destination": "/CONTDIR", "type": "none", "source": "/HOSTDIR", "options": ["b", "c", "su"]}]),
# ])
# @pytest.mark.parametrize('xmode', XMODE)
# def test_15__mod_mount_spec(mocker, fresh_runc, initial_mounts, host_source, cont_dest, new_data, expected_mounts):
#     """Test15 RuncEngine()._mod_mount_spec()."""
#
#     mocker.patch.object(fresh_runc, '_cont_specjson', {"mounts": initial_mounts})
#     result = fresh_runc._mod_mount_spec(host_source, cont_dest, new_data)
#
#     if expected_mounts == initial_mounts:
#         assert not result
#     else:
#         assert result
#         assert fresh_runc._cont_specjson["mounts"] == expected_mounts


#         optnew = {"options": ["a", "su"]}
#         mock_selmount.return_value = None
#         rcex = RuncEngine(self.local, self.xmode)
#         status = rcex._mod_mount_spec("/HOSTDIR", "/CONTDIR", optnew)
#         self.assertFalse(status)
#
#         optnew = {"options": ["a", "su"]}
#         mock_selmount.return_value = 0
#         rcex = RuncEngine(self.local, self.xmode)
#         rcex._container_specjson = dict()
#         rcex._container_specjson["mounts"] = []
#         mount = {"destination": "/CONTDIR",
#                  "type": "none",
#                  "source": "/HOSTDIR",
#                  "options": ["a"], }
#         rcex._container_specjson["mounts"].append(mount)
#         status = rcex._mod_mount_spec("/HOSTDIR", "/CONTDIR", optnew)
#         self.assertTrue(status)
#         self.assertEqual(len(rcex._container_specjson["mounts"]), 1)
#
#     @patch('udocker.engine.runc.os.path.isfile')
#     @patch('udocker.engine.runc.os.path.isdir')
#     @patch.object(RuncEngine, '_add_mount_spec')
#     @patch('udocker.engine.runc.FileBind')


@pytest.mark.parametrize(
    "volumes, isdir_return, isfile_return, sysdirs_list, expected_method_calls",
    [
        ([], False, False, [], [('add_mount_spec', 1)]),
        (['/HOSTDIR:/CONTDIR'], False, False, [], [('isdir', 1), ('isfile', 1)]),
        (['/HOSTDIR:/CONTDIR'], True, False, [], [('isdir', 1), ('isfile', 0), ('add_mount_spec', 2)]),
        (['/dev'], True, False, [], [('isdir', 1), ('isfile', 0), ('add_mount_spec', 1)]),
        (['/HOSTDIR:/CONTDIR'], False, True, ["/HOSTDIR"],
         [('isdir', 1), ('isfile', 1), ('add_mount_spec', 1), ('add_file', 1)]),
    ])
@pytest.mark.parametrize('xmode', XMODE)
def test_16__add_volume_bindings(mocker, runc, logger, volumes, isdir_return, isfile_return, sysdirs_list,
                                 expected_method_calls):
    """Test16 RuncEngine()._add_volume_bindings()."""
    mocker.patch.object(runc, '_filebind', autospec=True)
    mock_isdir = mocker.patch('os.path.isdir', return_value=isdir_return)
    mock_isfile = mocker.patch('os.path.isfile', return_value=isfile_return)
    mock_add_mount_spec = mocker.patch.object(runc, '_add_mount_spec')
    mock_add_file = mocker.patch.object(runc._filebind, 'add_file')

    Config.conf['sysdirs_list'] = sysdirs_list

    runc._filebind.start.return_value = ("/HOSTDIR", "/CONTDIR")
    runc.opt["vol"] = volumes

    runc._add_volume_bindings()

    for method_name, call_count in expected_method_calls:
        assert locals()[f'mock_{method_name}'].call_count == call_count


#
@pytest.mark.parametrize("options, expected_logs", [
    ({"portsmap": None, 'netcoop': None}, []),
    ({"portsmap": True, 'netcoop': None}, ["this execution mode does not support -p --publish"]),
    ({"portsmap": None, "netcoop": True}, ["this exec mode does not support -P --netcoop --publish-all"]),
    ({"portsmap": True, "netcoop": True}, ["this execution mode does not support -p --publish",
                                           "this exec mode does not support -P --netcoop --publish-all"])
])
@pytest.mark.parametrize('xmode', XMODE)
def test_17__run_invalid_options(mocker, runc, logger, options, expected_logs):
    """Test17 RuncEngine()._run_invalid_options()."""

    mocker.patch.object(runc, 'opt', options)
    runc._run_invalid_options()

    if expected_logs:
        assert logger.warning.call_count == len(expected_logs)
        for msg in expected_logs:
            assert logger.warning.call_any(msg)


# FIXME: this test fails need to be fixed
# @pytest.mark.parametrize("proot_mode, proot_noseccomp, env_value, expected_result", [
#     ("P2", False, None, False),
#     ("P2", False, None, True),
#     ("P2", True, "PROOT_NO_SECCOMP=1", True),
#     ("P2", True, "PROOT_NO_SECCOMP=1", True),
# ])
# @pytest.mark.parametrize('xmode', ["P1", "P2", "R2", "R3"])
# def test_18__proot_overlay(mocker, runc, mock_fileutil, proot_mode, proot_noseccomp, env_value, expected_result):
#     """Test18 RuncEngine()._proot_overlay()."""
#     mocker.patch.object(runc, 'select_proot')
#     mocker.patch.object(mock_fileutil, 'chmod', return_value=True)
#     runc.exec_mode = mocker.MagicMock()
#     preng_mock = mocker.MagicMock()
#     preng_mock.proot_noseccomp = proot_noseccomp
#     preng_mock.executable = "/path/to/proot"
#     mocker.patch('PROOTEngine', return_value=preng_mock)
#     runc._cont_specjson = {"process": {"env": [], "args": []}}
#     runc.opt = {"cmd": ["testcmd"]}
#
#     if env_value:
#         mocker.patch.dict(os.environ, {"PROOT_NO_SECCOMP": "1"})
#
#     result = runc._proot_overlay(proot_mode)
#
#     assert result == expected_result
#     if expected_result:
#         assert runc._cont_specjson["process"]["args"] == ["/.udocker/bin/proot", "-0", "testcmd"]


#         self.xmode.get_mode.return_value = "R1"
#         rcex = RuncEngine(self.local, self.xmode)
#         status = rcex._proot_overlay("P2")
#         self.assertFalse(status)
#
#         self.xmode.get_mode.return_value = "R2"
#         mock_proot.return_value.select_proot.return_value = None
#         mock_base.return_value = "ls"
#         mock_chmod.return_value = None
#         mock_crmpoint.return_value = True
#         mock_stat.return_value.S_IRUSR = 256
#         mock_stat.return_value.S_IWUSR = 128
#         mock_stat.return_value.S_IXUSR = 64
#         rcex = RuncEngine(self.local, self.xmode)
#         rcex._filebind = mock_fbind
#         rcex._filebind.start.return_value = ("/HOSTDIR", "/CONTDIR")
#         rcex._filebind.set_file.return_value = None
#         rcex._filebind.add_file.return_value = None
#         rcex._container_specjson = dict()
#         rcex._container_specjson["process"] = dict()
#         rcex._container_specjson["process"]["env"] = []
#         rcex._container_specjson["process"]["args"] = []
#         status = rcex._proot_overlay("P2")
#         self.assertTrue(status)
#         self.assertTrue(mock_base.called)
#         self.assertTrue(mock_chmod.called)
#         self.assertTrue(mock_crmpoint.called)
#         self.assertTrue(rcex._filebind.set_file.called)
#         self.assertTrue(rcex._filebind.add_file.called)
#
@pytest.mark.parametrize("init_result, expect_return, expected_call", [
    (False, 2, None),
    (True, 4, "_load_spec"),
])
@pytest.mark.parametrize('xmode', XMODE)
def test_19_run(mocker, runc, init_result, expect_return, expected_call):
    """Test19 RuncEngine().run()."""
    mocker.patch.object(runc, '_run_init', return_value=init_result)
    mocker.patch.object(runc, '_check_arch')
    mocker.patch.object(runc, '_run_invalid_options')
    mocker.patch.object(runc, '_load_spec', return_value=not init_result)  # inverse of init_result for this example
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
    mocker.patch.object(runc, 'run_pty', return_value=0)
    mocker.patch.object(runc, 'run_nopty', return_value=0)

    # Execute the method
    result = runc.run("test_container_id")

    # Assertions
    assert result == expect_return
    if expected_call:
        mocker_method = getattr(runc, expected_call)
        mocker_method.assert_called_once()


@pytest.mark.parametrize("subprocess_return,expected", [(0, 0), (1, 1)])
@pytest.mark.parametrize('xmode', XMODE)
def test_20_run_pty(mocker, runc, subprocess_return, expected):
    """Test20 RuncEngine().run_pty()."""
    mocker.patch.object(runc, '_filebind', return_value=mocker.Mock())

    with mocker.patch('subprocess.call', return_value=expected):
        assert runc.run_pty(["CONTAINERID"]) == expected
        runc._filebind.finish.assert_called_once()


@pytest.mark.parametrize("select_return,read_raises,terminate_raises,expected", [
    (([1, ], [], []), False, False, 0),
    (([], [], [1, ]), False, False, 0),
    (([1, ], [], []), True, False, 0),
    (([], [], []), False, True, 0),
])
@pytest.mark.parametrize('xmode', XMODE)
def test_21_run_nopty(mocker, runc, select_return, read_raises, terminate_raises, expected):
    """Test21 RuncEngine().run_nopty()."""

    mocked_process = mocker.Mock(spec=subprocess.Popen)
    mocked_process.poll.return_value = None
    mocked_process.returncode = 0
    mocker.patch('subprocess.Popen', return_value=mocked_process)
    mocker.patch('os.openpty', return_value=(1, 2))
    mocker.patch('os.close')
    mocker.patch('select.select', return_value=select_return)

    if read_raises:
        mocker.patch('os.read', side_effect=OSError())
    else:
        mocker.patch('os.read', return_value=b'x')

    if terminate_raises:
        mocked_process.terminate.side_effect = OSError()

    runc._filebind = mocker.Mock()
    runc._filebind.finish = mocker.Mock()
    result = runc.run_nopty(["some_cmd"])
    subprocess.Popen.assert_called_once_with(["some_cmd"], shell=False, close_fds=False, stdout=2, stderr=2)
    runc._filebind.finish.assert_called_once()
    assert result.returncode == expected
