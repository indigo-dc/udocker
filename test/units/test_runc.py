#!/usr/bin/env python
"""
udocker unit tests: RuncEngine
"""
import logging
import random
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
    return mocker.patch('udocker.container.localrepo.LocalRepository')


@pytest.mark.parametrize('xmode', XMODE)
def mock_exec_mode(localrepo, container_id, xmode):
    mocker_exec_mode = ExecutionMode(localrepo, container_id)
    mocker_exec_mode.force_mode = xmode
    return mocker_exec_mode


@pytest.fixture
def runc(localrepo, container_id):
    mock_runc = RuncEngine(localrepo, mock_exec_mode)
    runc.container_id = container_id
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


@pytest.fixture
def mocker_os_exists(mocker):
    return mocker.patch('udocker.engine.runc.os.path.exists')


@pytest.fixture
def mocker_os_basename(mocker):
    return mocker.patch('udocker.engine.runc.os.path.basename')


@pytest.fixture
def mocker_fileutil(mocker):
    return mocker.patch('udocker.engine.runc.FileUtil', autospec=True)


@pytest.fixture
def mock_realpath(mocker):
    return mocker.patch('udocker.engine.runc.os.path.realpath')


# @pytest.fixture
# def mock_plat_node(mocker):
#     return mocker.patch('udocker.engine.runc.platform.node')


# BUILTINS = "builtins"
# BOPEN = BUILTINS + '.open'
#
#
# class RuncEngineTestCase(TestCase):
#     """Test RuncEngine() containers execution with runC."""
#
#     def setUp(self):
#         LOG.setLevel(100)
#         Config().getconf()
#         Config().conf['hostauth_list'] = ("/etc/passwd", "/etc/group")
#         Config().conf['cmd'] = "/bin/bash"
#         Config().conf['cpu_affinity_exec_tools'] = (["numactl", "-C", "%s", "--", ],
#                                                     ["taskset", "-c", "%s", ])
#         Config().conf['runc_capabilities'] = [
#             "CAP_KILL", "CAP_NET_BIND_SERVICE", "CAP_CHOWN", "CAP_DAC_OVERRIDE",
#             "CAP_FOWNER", "CAP_FSETID", "CAP_KILL", "CAP_SETGID", "CAP_SETUID",
#             "CAP_SETPCAP", "CAP_NET_BIND_SERVICE", "CAP_NET_RAW",
#             "CAP_SYS_CHROOT", "CAP_MKNOD", "CAP_AUDIT_WRITE", "CAP_SETFCAP",
#         ]
#         Config().conf['valid_host_env'] = "HOME"
#         Config().conf['username'] = "user"
#         Config().conf['userhome'] = "/"
#         Config().conf['oskernel'] = "4.8.13"
#         Config().conf['location'] = ""
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

@pytest.mark.parametrize('xmode', XMODE)
def test_01_init(runc):
    """Test01 RuncEngine() constructor."""
    assert runc.executable is None
    assert runc._cont_specjson is None
    assert runc._cont_specfile is None
    assert runc._cont_specdir == ''  # FIXME: maybe init this
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
def test_02_select_runc(mocker, runc, logger, mocker_os_exists, mocker_os_basename, conf, runc_path, crun_path, arch,
                        find_file, os_exists, error, expected_exec, expected_type):
    """Test02 RuncEngine().select_runc()."""

    mocker.patch.object(runc, 'executable', conf)
    mocker.patch('udocker.engine.runc.FileUtil.find_exec', side_effect=[runc_path, crun_path])
    mocker.patch('udocker.engine.runc.HostInfo.arch', return_value=arch)
    mocker.patch('udocker.engine.runc.FileUtil.find_file_in_dir', return_value=find_file)

    mocker_os_exists.return_value = os_exists
    mocker_os_basename.return_value = expected_exec

    with error:
        runc.select_runc()
        assert runc.executable == expected_exec
        assert runc.engine_type == expected_type


#
#     @patch('udocker.engine.runc.json.load')
#     @patch('udocker.engine.runc.FileUtil.register_prefix')
#     @patch('udocker.engine.runc.FileUtil.remove')
#     @patch('udocker.engine.runc.FileUtil.size')
#     @patch('udocker.engine.runc.subprocess.call')
#     @patch('udocker.engine.runc.os.path.realpath')
@pytest.mark.parametrize("verbose,new,file_exists,subprocess,read_json,error,expected", [
    (logging.NOTSET, False, False, 0, True, does_not_raise(), {}),
    (logging.NOTSET, False, True, 0, True, does_not_raise(), {}),
    (logging.NOTSET, True, True, 0, True, does_not_raise(), {}),
    (logging.NOTSET, True, False, 0, True, does_not_raise(), {}),
    (logging.NOTSET, True, False, 1, True, does_not_raise(), False),
    (logging.DEBUG, True, False, 1, True, does_not_raise(), False),
    # (logging.NOTSET, True, False, 0, False, pytest.raises(SystemError), None), #FIXME: this test fails
])
@pytest.mark.parametrize('xmode', XMODE)
def test_03__load_spec(mocker, runc, mocker_fileutil, verbose, new, file_exists, subprocess, read_json, error,
                       expected):
    """Test03 RuncEngine()._load_spec()."""

    mocker.patch.object(Config, 'conf', {'verbose_level': verbose})

    size_mock = mocker.patch("udocker.engine.runc.FileUtil.size")
    size_mock.side_effect = [0 if file_exists else -1, 0] # FIXME: this is not working as intended

    mocker.patch("subprocess.call", return_value=subprocess)
    mocker.patch.object(runc, '_cont_specjson')

    mocker_fileutil.return_value.size.return_value = -1
    mocker_fileutil.return_value.register_prefix.return_value = None
    mocker_fileutil.return_value.remove.return_value = None

    if read_json:
        mocker.patch("builtins.open", mocker.mock_open(read_data='{}'))
    else:
        mocker.patch("builtins.open", side_effect=OSError)

    with error:
        assert runc._load_spec(new) == expected


#         mock_size.side_effect = [-1, -1]
#         mock_rpath.return_value = "/container/ROOT"
#         mock_call.return_value = 1
#         mock_rm.return_value = None
#         mock_reg.return_value = None
#         rcex = RuncEngine(self.local, self.xmode)
#         status = rcex._load_spec(False)
#         self.assertFalse(mock_rm.called)
#         self.assertFalse(mock_reg.called)
#         self.assertTrue(mock_call.called)
#         self.assertTrue(mock_rpath.called)
#         self.assertFalse(status)
#
#         jload = {
#             "container": "cxxx", "parent": "dyyy",
#             "created": "2020-05-05T21:20:07.182447994Z",
#             "os": "linux",
#             "container_config": {"Tty": "false", "Cmd": ["/bin/sh"]},
#             "Image": "sha256:aa"
#             }
#
#         mock_size.side_effect = [100, 100]
#         mock_rpath.return_value = "/container/ROOT"
#         mock_call.return_value = 0
#         mock_rm.return_value = None
#         mock_reg.return_value = None
#         mock_jload.return_value = jload
#         with patch(BOPEN, mock_open()) as mopen:
#             rcex = RuncEngine(self.local, self.xmode)
#             status = rcex._load_spec(True)
#             self.assertTrue(mopen.called)
#             self.assertEqual(status, jload)
#             self.assertTrue(mock_rm.called)
#             self.assertTrue(mock_reg.called)
#
#     @patch('udocker.engine.runc.json.dump')

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


#
#     @patch('udocker.engine.runc.os.getgid')
#     @patch('udocker.engine.runc.os.getuid')
#     @patch('udocker.engine.runc.platform.node')
#     @patch('udocker.engine.runc.os.path.realpath')
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
    mocker.patch.object(runc, 'opt' , opt)

    set_spec_json = runc._set_spec()

    for key, value in expected.items():
        if type(value) is dict:
            for subkey, subvalue in value.items():
                assert set_spec_json[key][subkey] == subvalue
        else:
            assert set_spec_json[key] == value


#         # rcex.opt["hostname"] has nodename
#         mock_realpath.return_value = "/.udocker/containers/aaaaaa/ROOT"
#         mock_node.return_value = "nodename.local"
#         rcex = RuncEngine(self.local, self.xmode)
#         rcex.opt = dict()
#         rcex._container_specjson = dict()
#         rcex._container_specjson["root"] = dict()
#         rcex._container_specjson["process"] = dict()
#         rcex._container_specjson["linux"] = dict()
#         rcex._container_specjson["linux"]["uidMappings"] = dict()
#         rcex._container_specjson["linux"]["gidMappings"] = dict()
#         rcex.opt["cwd"] = "/"
#         rcex.opt["env"] = []
#         rcex.opt["cmd"] = "bash"
#         rcex.opt["hostname"] = "node.domain"
#         json_obj = rcex._set_spec()
#         self.assertEqual(json_obj["hostname"], "node.domain")
#
#         # empty rcex.opt["hostname"]
#         mock_realpath.return_value = "/.udocker/containers/aaaaaa/ROOT"
#         mock_node.return_value = "nodename.local"
#         rcex = RuncEngine(self.local, self.xmode)
#         rcex.opt = dict()
#         rcex._container_specjson = dict()
#         rcex._container_specjson["root"] = dict()
#         rcex._container_specjson["process"] = dict()
#         rcex._container_specjson["linux"] = dict()
#         rcex._container_specjson["linux"]["uidMappings"] = dict()
#         rcex._container_specjson["linux"]["gidMappings"] = dict()
#         rcex.opt["cwd"] = "/"
#         rcex.opt["env"] = []
#         rcex.opt["cmd"] = "bash"
#         rcex.opt["hostname"] = ""
#         json_obj = rcex._set_spec()
#         self.assertEqual(json_obj["hostname"], "nodename.local")
#
#         # environment passes to container json
#         mock_realpath.return_value = "/.udocker/containers/aaaaaa/ROOT"
#         mock_node.return_value = "nodename.local"
#         rcex = RuncEngine(self.local, self.xmode)
#         rcex.opt = dict()
#         rcex._container_specjson = dict()
#         rcex._container_specjson["root"] = dict()
#         rcex._container_specjson["process"] = dict()
#         rcex._container_specjson["linux"] = dict()
#         rcex._container_specjson["linux"]["uidMappings"] = dict()
#         rcex._container_specjson["linux"]["gidMappings"] = dict()
#         rcex.opt["cwd"] = "/"
#         rcex.opt["env"] = [("AA", "aa"), ("BB", "bb")]
#         rcex.opt["cmd"] = "bash"
#         rcex.opt["hostname"] = ""
#         json_obj = rcex._set_spec()
#         self.assertIn("AA=aa", json_obj["process"]["env"])
#
#         # environment syntax error
#         mock_realpath.return_value = "/.udocker/containers/aaaaaa/ROOT"
#         mock_node.return_value = "nodename.local"
#         rcex = RuncEngine(self.local, self.xmode)
#         rcex.opt = dict()
#         rcex._container_specjson = dict()
#         rcex._container_specjson["root"] = dict()
#         rcex._container_specjson["process"] = dict()
#         rcex._container_specjson["linux"] = dict()
#         rcex._container_specjson["linux"]["uidMappings"] = dict()
#         rcex._container_specjson["linux"]["gidMappings"] = dict()
#         rcex.opt["cwd"] = "/"
#         rcex.opt["env"] = [("BB", "bb")]
#         rcex.opt["cmd"] = "bash"
#         rcex.opt["hostname"] = ""
#         json_obj = rcex._set_spec()
#         self.assertNotIn("AA=aa", json_obj["process"]["env"])
#
#         # uid and gid mappings
#         mock_realpath.return_value = "/.udocker/containers/aaaaaa/ROOT"
#         mock_node.return_value = "nodename.local"
#         mock_getuid.return_value = 10000
#         mock_getgid.return_value = 10000
#         rcex = RuncEngine(self.local, self.xmode)
#         rcex.opt = dict()
#         rcex._container_specjson = dict()
#         rcex._container_specjson["root"] = dict()
#         rcex._container_specjson["process"] = dict()
#         rcex._container_specjson["linux"] = dict()
#         rcex._container_specjson["linux"]["uidMappings"] = dict()
#         rcex._container_specjson["linux"]["gidMappings"] = dict()
#         rcex._container_specjson["linux"]["uidMappings"]["XXX"] = 0
#         rcex._container_specjson["linux"]["gidMappings"]["XXX"] = 0
#         rcex.opt["cwd"] = "/"
#         rcex.opt["env"] = [("AA", "aa"), ("BB", "bb")]
#         rcex.opt["cmd"] = "bash"
#         rcex.opt["hostname"] = ""
#         json_obj = rcex._set_spec()
#         self.assertFalse(mock_getuid.called)
#         self.assertFalse(mock_getgid.called)
#
#     @patch('udocker.engine.runc.HostInfo')
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


#         mock_hinfo.return_value.uid = 1001
#         mock_hinfo.return_value.gid = 1001
#         rcex = RuncEngine(self.local, self.xmode)
#         rcex._container_specjson = {"linux":
#                                       {"uidMappings": [{"containerID": 0, "hostID": 1001}],
#                                        "gidMappings": [{"containerID": 0, "hostID": 1001}]}
#                                     }
#         rcex._set_id_mappings()
#         self.assertTrue(mock_hinfo.return_value.called_count, 2)
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

    #         rcex = RuncEngine(self.local, self.xmode)
    #         Config.conf['runc_capabilities'] = ""
    #         self.assertEqual(rcex._add_capabilities_spec(), None)
    #
    #         rcex = RuncEngine(self.local, self.xmode)
    #         Config.conf['runc_capabilities'] = ["CAP_KILL", "CAP_NET_BIND_SERVICE", "CAP_CHOWN"]
    #         rcex._container_specjson = dict()
    #         rcex._container_specjson["process"] = dict()
    #         rcex._container_specjson["process"]["capabilities"] = dict()
    #         rcex._container_specjson["process"]["capabilities"]["ambient"] = dict()
    #         rcex._add_capabilities_spec()
    #         res = rcex._container_specjson["process"]["capabilities"]["ambient"]
    #         self.assertEqual(res, Config.conf['runc_capabilities'])
    #
    #     @patch('udocker.engine.runc.HostInfo')
    #     @patch('udocker.engine.runc.os.minor')
    #     @patch('udocker.engine.runc.os.major')
    #     @patch('udocker.engine.runc.stat.S_ISCHR')
    #     @patch('udocker.engine.runc.stat.S_ISBLK')
    #     @patch('udocker.engine.runc.os.path.exists')


def test_10__add_device_spec(self, mock_exists, mock_blk, mock_chr, mock_osmaj,
                             mock_osmin, mock_hi):
    """Test10 RuncEngine()._add_device_spec()."""


#         mock_exists.return_value = False
#         rcex = RuncEngine(self.local, self.xmode)
#         status = rcex._add_device_spec("/dev/zero")
#         self.assertFalse(status)
#
#         mock_exists.return_value = True
#         mock_blk.return_value = False
#         mock_chr.return_value = False
#         rcex = RuncEngine(self.local, self.xmode)
#         status = rcex._add_device_spec("/dev/zero")
#         self.assertFalse(status)
#
#         mock_exists.return_value = True
#         mock_blk.return_value = True
#         mock_chr.return_value = False
#         mock_osmaj.return_value = 0
#         mock_osmin.return_value = 6
#         mock_hi.uid = 0
#         mock_hi.gid = 0
#         rcex = RuncEngine(self.local, self.xmode)
#         rcex._container_specjson = dict()
#         rcex._container_specjson["linux"] = dict()
#         rcex._container_specjson["linux"]["devices"] = list()
#         status = rcex._add_device_spec("/dev/zero")
#         self.assertTrue(status)
#         self.assertTrue(mock_osmaj.called)
#         self.assertTrue(mock_osmin.called)
#
#     @patch('udocker.engine.runc.NvidiaMode')
#     @patch.object(RuncEngine, '_add_device_spec')
def test_11__add_devices(self, mock_adddecspec, mock_nv):
    """Test11 RuncEngine()._add_devices()."""


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
def test_12__add_mount_spec(self):
    """Test12 RuncEngine()._add_mount_spec()."""


#         rcex = RuncEngine(self.local, self.xmode)
#         rcex._container_specjson = dict()
#         rcex._container_specjson["mounts"] = []
#         rcex._add_mount_spec("/HOSTDIR", "/CONTDIR")
#         mount = rcex._container_specjson["mounts"][0]
#         self.assertEqual(mount["destination"], "/CONTDIR")
#         self.assertEqual(mount["source"], "/HOSTDIR")
#         self.assertIn("ro", mount["options"])
#
#         # rw
#         rcex = RuncEngine(self.local, self.xmode)
#         rcex._container_specjson = dict()
#         rcex._container_specjson["mounts"] = []
#         rcex._add_mount_spec("/HOSTDIR", "/CONTDIR", True)
#         mount = rcex._container_specjson["mounts"][0]
#         self.assertEqual(mount["destination"], "/CONTDIR")
#         self.assertEqual(mount["source"], "/HOSTDIR")
#         self.assertIn("rw", mount["options"])
#
def test_13__del_mount_spec(self):
    """Test13 RuncEngine()._del_mount_spec()."""


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
def test_14__sel_mount_spec(self):
    """Test14 RuncEngine()._sel_mount_spec()."""


#         rcex = RuncEngine(self.local, self.xmode)
#         rcex._container_specjson = dict()
#         rcex._container_specjson["mounts"] = []
#         mount = {"destination": "/CONTDIR",
#                  "type": "none",
#                  "source": "xxx",
#                  "options": ["rbind", "nosuid",
#                              "noexec", "nodev",
#                              "rw", ], }
#         rcex._container_specjson["mounts"].append(mount)
#         status = rcex._sel_mount_spec("/HOSTDIR", "/CONTDIR")
#         self.assertEqual(status, None)
#
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
#         status = rcex._sel_mount_spec("/HOSTDIR", "/CONTDIR")
#         self.assertEqual(status, 0)
#
#     @patch.object(RuncEngine, '_sel_mount_spec')
def test_15__mod_mount_spec(self, mock_selmount):
    """Test15 RuncEngine()._mod_mount_spec()."""


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
def test_16__add_volume_bindings(self, mock_fbind, mock_add_mnt_spec, mock_isdir, mock_isfile):
    """Test16 RuncEngine()._add_volume_bindings()."""


#         mock_add_mnt_spec.side_effect = [None, None]
#         rcex = RuncEngine(self.local, self.xmode)
#         rcex._filebind = mock_fbind
#         rcex._filebind.start.return_value = ("/HOSTDIR", "/CONTDIR")
#         rcex.opt["vol"] = list()
#         rcex._add_volume_bindings()
#         self.assertTrue(mock_add_mnt_spec.called)
#         self.assertFalse(mock_isdir.called)
#
#         mock_add_mnt_spec.side_effect = [None, None]
#         mock_isdir.return_value = False
#         mock_isfile.return_value = False
#         rcex = RuncEngine(self.local, self.xmode)
#         rcex._filebind = mock_fbind
#         rcex._filebind.start.return_value = ("/HOSTDIR", "/CONTDIR")
#         rcex.opt["vol"] = list()
#         rcex.opt["vol"].append("/HOSTDIR:/CONTDIR")
#         rcex._add_volume_bindings()
#         self.assertTrue(mock_isdir.called)
#         self.assertTrue(mock_isfile.called)
#
#         mock_add_mnt_spec.side_effect = [None, None]
#         mock_isdir.return_value = True
#         mock_isfile.return_value = False
#         rcex = RuncEngine(self.local, self.xmode)
#         rcex._filebind = mock_fbind
#         rcex._filebind.start.return_value = ("/HOSTDIR", "/CONTDIR")
#         rcex.opt["vol"] = list()
#         rcex.opt["vol"].append("/HOSTDIR:/CONTDIR")
#         rcex._add_volume_bindings()
#         self.assertTrue(mock_isdir.called)
#         self.assertTrue(mock_isfile.called)
#         self.assertTrue(mock_add_mnt_spec.call_count, 2)
#
#         mock_add_mnt_spec.side_effect = [None, None]
#         mock_isdir.return_value = False
#         mock_isfile.return_value = True
#         rcex = RuncEngine(self.local, self.xmode)
#         Config.conf['sysdirs_list'] = ["/HOSTDIR"]
#         rcex._filebind = mock_fbind
#         rcex._filebind.start.return_value = ("/HOSTDIR", "/CONTDIR")
#         rcex._filebind.set_file.return_value = None
#         rcex._filebind.add_file.return_value = None
#         rcex.opt["vol"] = list()
#         rcex.opt["vol"].append("/HOSTDIR:/CONTDIR")
#         rcex._add_volume_bindings()
#         self.assertTrue(mock_isdir.called)
#         self.assertTrue(mock_isfile.called)
#         self.assertTrue(mock_add_mount_spec.call_count, 1)
#         # self.assertTrue(rcex._filebind.set_file.called)
#         self.assertTrue(rcex._filebind.add_file.called)
#
#     @patch('udocker.engine.runc.LOG.warning')
def test_17__run_invalid_options(self, mock_warn):
    """Test17 RuncEngine()._run_invalid_options()."""


#         rcex = RuncEngine(self.local, self.xmode)
#         rcex.opt['netcoop'] = False
#         rcex.opt['portsmap'] = True
#         rcex._run_invalid_options()
#         self.assertTrue(mock_warn.called)
#
#         rcex = RuncEngine(self.local, self.xmode)
#         rcex.opt['netcoop'] = True
#         rcex.opt['portsmap'] = True
#         rcex._run_invalid_options()
#         self.assertTrue(mock_warn.called_count, 2)
#
#     @patch.object(RuncEngine, '_create_mountpoint')
#     @patch('udocker.engine.runc.stat')
#     @patch('udocker.engine.runc.FileUtil.chmod')
#     @patch('udocker.engine.runc.FileBind')
#     @patch('udocker.engine.runc.os.path.basename')
#     @patch('udocker.engine.runc.PRootEngine')
def test_18__proot_overlay(self, mock_proot, mock_base, mock_fbind,
                           mock_chmod, mock_stat, mock_crmpoint):
    """Test18 RuncEngine()._proot_overlay()."""


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
#     @patch('udocker.engine.runc.FileBind')
#     @patch('udocker.engine.runc.Unique')
#     @patch.object(RuncEngine, '_set_id_mappings')
#     @patch.object(RuncEngine, '_del_namespace_spec')
#     @patch.object(RuncEngine, '_del_mount_spec')
#     @patch.object(RuncEngine, 'run_nopty')
#     @patch.object(RuncEngine, 'run_pty')
#     @patch.object(RuncEngine, '_run_invalid_options')
#     @patch.object(RuncEngine, '_del_mount_spec')
#     @patch.object(RuncEngine, '_run_banner')
#     @patch.object(RuncEngine, '_add_devices')
#     @patch.object(RuncEngine, '_add_volume_bindings')
#     @patch.object(RuncEngine, '_set_spec')
#     @patch.object(RuncEngine, '_save_spec')
#     @patch.object(RuncEngine, '_proot_overlay')
#     @patch.object(RuncEngine, '_run_env_set')
#     @patch.object(RuncEngine, '_mod_mount_spec')
#     @patch.object(RuncEngine, '_add_capabilities_spec')
#     @patch.object(RuncEngine, '_uid_check')
#     @patch.object(RuncEngine, '_run_env_cleanup_list')
#     @patch.object(RuncEngine, '_load_spec')
#     @patch.object(RuncEngine, 'select_runc')
#     @patch.object(RuncEngine, '_run_init')
def test_19_run(self, mock_run_init, mock_sel_runc, mock_load_spec, mock_run_env_cleanup_list,
                mock_uid_check, mock_addspecs, mock_modms, mock_env_set, mock_prooto,
                mock_savespec, mock_set_spec, mock_add_bindings, mock_add_dev, mock_run_banner,
                mock_del_mount_spec, mock_inv_opt, mock_pty, mock_nopty, mock_delmnt,
                mock_delns, mock_setid, mock_unique, mock_fbind):
    """Test19 RuncEngine().run()."""


#         mock_run_init.return_value = False
#         mock_delmnt.return_value = None
#         mock_delns.return_value = None
#         mock_setid.return_value = None
#         mock_env_set.return_value = None
#         rcex = RuncEngine(self.local, self.xmode)
#         status = rcex.run("CONTAINERID")
#         self.assertEqual(status, 2)
#
#         mock_run_init.return_value = True
#         mock_inv_opt.return_value = None
#         mock_load_spec.return_value = False
#         mock_sel_runc.return_value = None
#         mock_load_spec.return_value = False
#         mock_delmnt.return_value = None
#         mock_delns.return_value = None
#         mock_setid.return_value = None
#         rcex = RuncEngine(self.local, self.xmode)
#         rcex.container_dir = "/container/ROOT"
#         rcex._filebind = mock_fbind
#         rcex._filebind.setup.return_value = None
#         status = rcex.run("CONTAINERID")
#         self.assertEqual(status, 4)
#
#         jload = {
#             "container": "cxxx", "parent": "dyyy",
#             "created": "2020-05-05T21:20:07.182447994Z",
#             "os": "linux",
#             "container_config": {"Tty": "false", "Cmd": ["/bin/sh"]},
#             "Image": "sha256:aa"
#         }
#         mock_run_init.return_value = True
#         mock_inv_opt.return_value = None
#         mock_load_spec.return_value = False
#         mock_sel_runc.return_value = None
#         mock_load_spec.return_value = jload
#         mock_uid_check.return_value = None
#         mock_run_env_cleanup_list.return_value = None
#         mock_set_spec.return_value = None
#         mock_del_mount_spec.return_value = None
#         mock_add_bindings.return_value = None
#         mock_add_dev.return_value = None
#         mock_addspecs.return_value = None
#         mock_modms.return_value = None
#         mock_prooto.return_value = None
#         mock_savespec.return_value = None
#         mock_unique.return_value.uuid.return_value = "EXECUTION_ID"
#         mock_run_banner.return_value = None
#         mock_pty.return_value = 0
#         mock_nopty.return_value = 0
#         mock_delmnt.return_value = None
#         mock_delns.return_value = None
#         mock_setid.return_value = None
#         rcex = RuncEngine(self.local, self.xmode)
#         rcex.opt["cmd"] = ["/bin/ls"]
#         rcex.container_dir = "/container/ROOT"
#         rcex._filebind = mock_fbind
#         rcex._filebind.setup.return_value = None
#         rcex.opt["cmd"] = [""]
#         status = rcex.run("CONTAINERID")
#         self.assertEqual(status, 0)
#
#     @patch('udocker.engine.runc.FileBind')
#     @patch('udocker.engine.runc.subprocess.call')
def test_20_run_pty(self, mock_call, mock_fbind):
    """Test20 RuncEngine().run_pty()."""


#         mock_call.return_value = 0
#         rcex = RuncEngine(self.local, self.xmode)
#         rcex.container_dir = "/container/ROOT"
#         rcex._filebind = mock_fbind
#         rcex._filebind.finish.return_value = None
#         status = rcex.run_pty("CONTAINERID")
#         self.assertEqual(status, 0)
#
def test_21_run_nopty(self):
    """Test21 RuncEngine().run_nopty()."""
#     #     pass
#
#
# if __name__ == '__main__':
#     main()
