#!/usr/bin/env python
"""
udocker unit tests: ExecutionEngineCommon
"""
import logging
import os
import random
from contextlib import nullcontext as does_not_raise

import pytest

from udocker import MSG
from udocker.config import Config
from udocker.container.structure import ContainerStructure
from udocker.engine.base import ExecutionEngineCommon
from udocker.helper.hostinfo import HostInfo
from udocker.helper.nixauth import NixAuthentication
from udocker.helper.osinfo import OSInfo
from udocker.utils.filebind import FileBind
from udocker.utils.fileutil import FileUtil
from udocker.utils.uenv import Uenv
from udocker.utils.uvolume import Uvolume


@pytest.fixture
def container_id():
    return str(random.randint(1, 1000))


@pytest.fixture
def localrepo(mocker, container_id):
    mock_localrepo = mocker.patch('udocker.container.localrepo.LocalRepository')
    mock_localrepo.return_value.cd_imagerepo.return_value = "/ROOT"
    return mock_localrepo


@pytest.fixture
def engine(localrepo, container_id, xmode):
    mocker_exec_mode = ExecutionEngineCommon(localrepo, xmode)
    return mocker_exec_mode


@pytest.fixture
def logger(mocker):
    return mocker.patch('udocker.engine.base.LOG')


def mocker_msg(mocker):
    return mocker.patch.object(MSG, 'info')


@pytest.fixture
def mocker_nixauth(mocker):
    return mocker.patch('udocker.engine.base.NixAuthentication', return_value=mocker.Mock())


@pytest.mark.parametrize("opts", [
    {'nometa': False, 'nosysdirs': False, 'dri': False, 'bindhome': False, 'hostenv': False, 'hostauth': False,
     'novol': [], 'vol': [], 'cpuset': '', 'user': '', 'cwd': '', 'entryp': '', 'hostname': '', 'domain': '',
     'volfrom': [], 'portsmap': [], 'portsexp': [], 'devices': [], 'nobanner': False}
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
    mock_has_option = mocker.patch.object(HostInfo, 'cmd_has_option', return_value=has_option)
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

    with error[0]:
        with error[1]:
            ports = engine._get_portsmap(by_container)
            assert ports == expected


@pytest.mark.parametrize("xmode", ["P1", "P2", "F1", "F2"])
@pytest.mark.parametrize("ports,portsexp,uid,error,count_error,count_warning,expected", [
    ({22: 22, 2048: 2048}, ("22", "2048/tcp"), 1000, does_not_raise(), 1, 0, False),
    ({22: 22, 2048: 2048}, ("22", "2048/tcp"), 0, does_not_raise(), 0, 1, True),
    ({22: 22, 2048: 2048}, ("invalid", "2048/tcp"), 1000, does_not_raise(), 0, 1, True),
])
def test_04__check_exposed_ports(mocker, engine, xmode, logger, ports, portsexp, uid, error, count_error,
                                 count_warning, expected):
    """Test04 ExecutionEngineCommon()._check_exposed_ports()."""
    mocker.patch.object(engine, '_get_portsmap', return_value=ports)
    mocker.patch.object(engine, 'opt', {'portsexp': portsexp})
    mocker.patch.object(HostInfo, 'uid', uid)

    with error:
        exposed_port = engine._check_exposed_ports()
        assert exposed_port == expected


    assert logger.error.call_count == count_error
    assert logger.warning.call_count == count_warning

    if count_error == 1:
        assert logger.error.call_args_list == [mocker.call('this container exposes privileged TCP/IP ports')]

    if count_warning == 1:
        assert logger.warning.call_args_list == [mocker.call('this container exposes TCP/IP ports')]


@pytest.mark.parametrize("xmode", ["P1", "P2", "F1", "F2"])
@pytest.mark.parametrize("opts,conf,exec_name,expected", [
    ({'cpuset': []}, {'cpu_affinity_exec_tools': [[], ], 'tmpdir': '/tmp'}, '/bin', []),
    ({'cpuset': '1-2'}, {'cpu_affinity_exec_tools': [["numactl", "-C", "%s", "--", ], ], 'tmpdir': '/tmp'}, 'numactl',
     ['numactl', '-C', '1-2', '--']),
    ({'cpuset': '1-2'},
     {'cpu_affinity_exec_tools': [["", "-C", "%s", "--", ], ["taskset", "-c", "%s", ]], 'tmpdir': '/tmp'},
     None, []),
])
def test_05__set_cpu_affinity(mocker, engine, xmode, logger, opts, conf, exec_name, expected):
    """Test05 ExecutionEngineCommon()._set_cpu_affinity()."""
    mocker.patch.object(FileUtil, 'find_exec', return_value=exec_name)
    mocker.patch.object(engine, 'opt', opts)
    mocker.patch.object(Config, 'conf', conf)

    cpu_affinity = engine._set_cpu_affinity()

    assert cpu_affinity == expected


@pytest.mark.parametrize("xmode", ["P1", "F1"])
@pytest.mark.parametrize("dirs_only,is_dir,create,expected", [
    (False, False, None, False),
    (False, True, None, False),
    (True, False, None, True),
    (True, True, False, False),
    (True, True, True, True),
])
def test_06__create_mountpoint(mocker, engine, logger, dirs_only, is_dir, create, expected):
    """Test06 ExecutionEngineCommon()._create_mountpoint()."""
    cont_path = "/ROOT/bin"
    host_path = "/bin"

    mocker.patch.object(FileUtil, 'isdir', return_value=is_dir)
    mocker.patch.object(engine, 'mountp', return_value='/home/user/')
    mocker.patch.object(engine.mountp, 'create', return_value=create)

    mountpoint = engine._create_mountpoint(host_path, cont_path, dirs_only)
    assert mountpoint == expected

    if not dirs_only or is_dir:
        engine.mountp.create.assert_called_once_with(host_path, cont_path)
    else:
        engine.mountp.create.assert_not_called()

    if create and (not dirs_only or is_dir):
        engine.mountp.save.assert_called_once_with(cont_path)
    else:
        engine.mountp.save.assert_not_called()


# , "F1"

@pytest.mark.parametrize("vol,dri_list,sysdirs_list,os_exists,create,log,expected", [
    (["invalid_host:/cont"], [], [], [False], [True], (1, "invalid host volume path: %s"), False),
    (["/host:/"], [], [], True, True, (1, 'invalid container volume path: %s'), False),  # Invalid container volume path
    (["/nonexistent_host:/cont"], [], [], [False], [True], (1, 'invalid host volume path: %s'), False),
    (["/host_in_dri:/cont"], ["/host_in_dri"], [], [False], [True], (0, None), True),  # Non-existent but in dri_list
    (["/host:/cont"], [], [], [True], [False], (1, 'creating mountpoint: %s:%s'), False),  # create_mountpoint fails
    (["/existing_host:/cont"], [], [], [True], [True], (0, None), True),
])
@pytest.mark.parametrize("xmode", ["P1"])
def test_07__check_volumes(mocker, engine, logger, vol, dri_list, sysdirs_list, os_exists, create, log, expected):
    """Test07 ExecutionEngineCommon()._check_volumes()."""
    mocker.patch.object(os.path, 'exists', side_effect=os_exists)
    mocker.patch.object(engine, '_create_mountpoint', side_effect=create)
    mocker.patch.object(Config, 'conf', {'dri_list': dri_list, 'sysdirs_list': sysdirs_list})
    mocker.patch.object(engine, 'opt', {'vol': vol})

    check_volumes = engine._check_volumes()
    assert check_volumes == expected
    assert logger.error.call_count == log[0]

    if log[0] == 1:
        log_message = logger.error.call_args_list[0][0][0]
        assert log_message == log[1]


@pytest.mark.parametrize("opt,count_called,nix_home,expected", [
    ({"bindhome": True}, 1, "/home/user", "/home/user"),
    ({"bindhome": True}, 1, "/root", "/root"),
    ({"bindhome": False}, 0, "/home/user", ""),
    ({"bindhome": False}, 0, "/root", "")
])
@pytest.mark.parametrize("xmode", ["P1", "F1"])
def test_08__get_bindhome(mocker, engine, opt, count_called, nix_home, expected):
    """Test08 ExecutionEngineCommon()._get_bindhome()."""
    mocker.patch.object(engine, 'opt', opt)
    mocker_ngix_auth = mocker.patch.object(NixAuthentication, 'get_home', return_value=nix_home)
    assert engine._get_bindhome() == expected
    assert mocker_ngix_auth.call_count == count_called


@pytest.mark.parametrize("path,vol,expected", [
    ("/home/user", ["/home/user:/cont1"], "/cont1"),
    ("/root", ["/home/user:/cont1", "/root:/cont2"], "/cont2"),
    ("/nonexistent", ["/home/user:/cont1", "/root:/cont2"], ""),
    ("/home/user", [], ""),  # No volumes defined
])
@pytest.mark.parametrize("xmode", ["P1", "F1"])
def test_09__is_volume(mocker, engine, path, vol, expected):
    """Test09 ExecutionEngineCommon()._is_volume()."""
    mocker.patch.object(engine, 'opt', {"vol": vol})
    mocker.patch.object(Uvolume, 'cleanpath', side_effect=lambda x: x)
    assert engine._is_volume(path) == expected


@pytest.mark.parametrize("path,vol,expected", [
    ("/cont1", ["/home/user:/cont1"], "/home/user"),  # cont_path exists
    ("/cont2", ["/home/user:/cont1", "/root:/cont2"], "/root"),  # Multiple paths, cont_path exists
    ("/nonexistent", ["/home/user:/cont1", "/root:/cont2"], ""),  # cont_path doesn't exist
    ("/cont1", [], ""),  # No volumes defined
])
@pytest.mark.parametrize("xmode", ["P1", "F1"])
def test_10__is_mountpoint(mocker, engine, path, vol, expected):
    """Test10 ExecutionEngineCommon()._is_mountpoint()."""
    mocker.patch.object(engine, 'opt', {"vol": vol})
    mocker.patch.object(Uvolume, 'cleanpath', side_effect=lambda x: x)

    is_mountpoint = engine._is_mountpoint(path)

    assert is_mountpoint == expected


@pytest.mark.parametrize("opts,bindhome,expected_vol,log_count,expected", [
    ({'vol': list(), 'nosysdirs': False, 'hostauth': "/etc/passwd", 'dri': ["/dri"], 'novol': list()}, "/home/user",
     ['/sys', '/dri', '/home/user'], 0, True),
    ({'vol': list(), 'nosysdirs': False, 'hostauth': "/etc/passwd", 'dri': ["/dri"],
      'novol': ["/sys", "/dri", "/home/user"]}, "/home/user",
     [], 0, True),
    ({'vol': list(), 'nosysdirs': False, 'hostauth': "/etc/passwd", 'dri': ["/dri"],
      'novol': ["/bin", "/dri", "/home/user"]}, "/home/user",
     ['/sys'], 1, False),
])
@pytest.mark.parametrize("xmode", ["F1", "P1"])
def test_11__set_volume_bindings(mocker, engine, logger, opts, bindhome, expected_vol, log_count, expected):
    """Test11 ExecutionEngineCommon()._set_volume_bindings()."""
    mocker.patch.object(engine, 'opt', opts)
    mocker.patch.object(Config, 'conf', {'sysdirs_list': ["/sys"], 'dri_list': ["/dri"]})
    mocker.patch.object(engine, '_get_bindhome', return_value=bindhome)
    mocker.patch.object(engine, '_check_volumes', return_value=expected)

    assert engine._set_volume_bindings() == expected
    assert engine.opt['vol'] == expected_vol
    assert logger.warning.call_count == log_count

    if log_count == 1:
        assert logger.warning.call_args_list == [mocker.call('--novol %s not in volumes list', mocker.ANY)]

    # clean
    engine.opt['vol'] = list()


@pytest.mark.parametrize("env,uid,config_paths,cwd,isdir,expected", [
    (None, "0", {'root_path': '/sbin', 'user_path': '/bin', 'tmpdir': '/tmp'}, False, True, True),
    ("/some/path", "0", {'root_path': '/sbin', 'user_path': '/bin', 'tmpdir': '/tmp'}, True, True, True),
    (None, "1000", {'root_path': '/sbin', 'user_path': '/bin', 'tmpdir': '/tmp'}, True, False, False),
])
@pytest.mark.parametrize("xmode", ["F1", "P1"])
def test_12__check_paths(mocker, engine, logger, env, uid, config_paths, cwd, isdir, expected):
    """Test12 ExecutionEngineCommon()._check_paths()."""
    mocker.patch.object(engine, 'opt', {'uid': uid,
                                        'cwd': "/some/cwd" if cwd else None,
                                        'env': mocker.Mock(),
                                        'home': '/home/user',
                                        'vol': list()})
    mocker.patch.object(engine.opt["env"], 'getenv', return_value=env)
    mocker.patch.object(Config, 'conf', config_paths)
    mocker.patch.object(os.path, 'isdir', return_value=isdir)
    mocker.patch.object(FileUtil, 'cont2host', return_value="/container/bin")

    assert engine._check_paths() == expected

    if not expected:
        assert logger.error.call_args_list == [mocker.call('invalid working directory: %s', mocker.ANY)]


@pytest.mark.parametrize("entryp,cmd,exec_name,path,find_exec_path,expected", [
    (None, ["/bin/ls"], "ls", "/user/bin", "bin", "/container_dir/bin"),
    ("/bin/ls -a -l", None, "ls", "/user/bin", "bin", "/container_dir/bin"),
    (["/bin/ls -a -l"], None, "ls", "/user/bin", "bin", "/container_dir/bin"),
    (["bin/ls -a -l"], ["/bin/ls"], "ls", "/user/bin", "bin", "/container_dir/bin"),
    (None, None, "default_cmd", "/user/bin", "default_path", "/container_dir/default_path"),
    (None, ["./bin/ls"], "ls", "/user/bin", "bin", "/container_dir/bin"),
    (None, ["../bin/ls"], "ls", "/user/bin", "bin", "/container_dir/bin"),
    (None, ["/bin/ls"], "ls", "/user/bin", None, ""),
])
@pytest.mark.parametrize("xmode", ["F1", "P1"])
def test_13__check_executable(mocker, engine, logger, entryp, cmd, exec_name, path, find_exec_path, expected):
    """Test13 ExecutionEngineCommon()._check_executable()."""
    mocker.patch.object(engine, 'container_root', "/container_dir")
    mocker.patch.object(engine, 'opt', {"entryp": entryp, "cmd": cmd,
                                        "env": mocker.Mock(), "cwd": "some_cwd", "vol": list()})
    mocker.patch.object(FileUtil, 'find_exec', return_value=find_exec_path)

    assert engine._check_executable() == expected
    if not exec_name:
        assert logger.error.call_args_list == [mocker.call('command not found/no execute bit set: %s', mocker.ANY)]


@pytest.mark.parametrize("location,cont_dir,opts,cntjson,expected", [
    (True, "",
     {"nometa": False, "user": None, "cwd": None, "hostname": None, "domain": None, "entryp": False, "cmd": None}, [],
     ("", [])),
    (False, None,
     {"nometa": False, "user": None, "cwd": None, "hostname": None, "domain": None, "entryp": False, "cmd": None}, [],
     (None, None)),
    (False, "cont_dir",
     {"nometa": False, "user": None, "cwd": None, "hostname": None, "domain": None, "entryp": False, "cmd": None,
      'portsexp': [], 'Volumes': None}, [],
     ('cont_dir', [])),
    (False, "cont_dir",
     {"nometa": False, "user": None, "cwd": None, "hostname": None, "domain": None, "entryp": "", "cmd": None,
      'portsexp': [], 'Volumes': None}, [],
     ('cont_dir', [])),
    (False, "cont_dir",
     {"nometa": False, "user": None, "cwd": None, "hostname": None, "domain": None, "entryp": "ls", "cmd": None,
      'portsexp': [], 'Volumes': None}, [],
     ('cont_dir', [])),
])
@pytest.mark.parametrize("xmode", ["F1", "P1"])
def test_14__run_load_metadata(mocker, engine, location, cont_dir, opts, cntjson, expected):
    """Test14 ExecutionEngineCommon()._run_load_metadata()."""
    mocker.patch.object(Config, 'conf', {"location": location})
    mocker.patch.object(engine, 'opt', {"nometa": opts.get("nometa", False), "user": opts.get("user", None),
                                        "cwd": opts.get("cwd", None), "hostname": opts.get("hostname", None),
                                        "domain": opts.get("domain", None), "entryp": opts.get("entryp", False),
                                        "cmd": opts.get("cmd", None), 'portsexp': opts.get('portsexp', []),
                                        'Volumes': opts.get('Volumes', None), 'env': mocker.Mock(), })

    mocker.patch.object(ContainerStructure, 'get_container_attr', return_value=(cont_dir, cntjson))
    mocker.patch.object(ContainerStructure, 'get_container_meta',
                        side_effect=lambda *args: cntjson.get(args[0], args[1]) if isinstance(args[2], dict) else args[
                            1])

    result = engine._run_load_metadata(container_id)
    assert result == expected


@pytest.mark.parametrize(
    "passwd_islink,passwd_isfile,group_islink,group_isfile,passwd_mount,group_mount,ismount,expected", [
        (False, False, False, False, False, False, ["", ""],
         ('container/ROOT/etc/passwd', 'container/ROOT/etc/group')),
        (True, False, False, False, False, False, ["", ""],
         ('container/ROOT/etc/passwd', 'container/ROOT/etc/group')),
        (True, True, False, False, False, False, ["", ""],
         ('container/.orig_dir/#etc#passwd', 'container/ROOT/etc/group')),
        (False, False, True, False, False, False, ["", ""],
         ('container/ROOT/etc/passwd', 'container/ROOT/etc/group')),
        (False, False, True, True, False, False, ["", ""],
         ('container/ROOT/etc/passwd', 'container/.orig_dir/#etc#group')),
        (False, False, False, False, True, False, ["mounted_path", "mounted_path", False],
         ('mounted_path', 'container/ROOT/etc/group')),
        (False, False, False, False, False, True, [False, "mounted_path", "mounted_path"],
         ('container/ROOT/etc/passwd', 'mounted_path')),
        (False, False, False, False, True, True, ["mounted_path"] * 4,
         ('mounted_path', 'mounted_path')),
    ])
@pytest.mark.parametrize("xmode", ["F1", "P1"])
def test_15__select_auth_files(mocker, engine, passwd_islink, passwd_isfile, group_islink,
                               group_isfile, passwd_mount, group_mount, ismount, expected):
    """Test15 ExecutionEngineCommon()._select_auth_files()."""

    mocker.patch.object(FileBind, 'bind_dir', new_callable=mocker.PropertyMock, return_value='/.bind_dir')
    mocker.patch.object(FileBind, 'orig_dir', new_callable=mocker.PropertyMock, return_value='/.orig_dir')

    mocker.patch.object(engine, 'container_root', "container/ROOT")
    mocker.patch.object(engine, 'container_dir', "container")

    mocker.patch.object(os.path, 'islink', side_effect=lambda x: (x.endswith('passwd') and passwd_islink) or (
            x.endswith('group') and group_islink))
    mocker.patch.object(os.path, 'isfile', side_effect=lambda x: (x.endswith('passwd') and passwd_isfile) or (
            x.endswith('group') and group_isfile))

    mocker.patch.object(engine, '_is_mountpoint', side_effect=ismount)

    assert engine._select_auth_files() == expected


@pytest.mark.parametrize("user_input,expected_output", [
    (None, {}),
    ("123:", {}),
    (":123", {}),
    ("user@name", {}),
    ("123user", {}),
    ("username", {"user": "username"}),
    ("user_name", {"user": "user_name"}),
    ("123:456", {"uid": "123", "gid": "456"}),
    ("123", {"uid": "123"}),
])
@pytest.mark.parametrize("xmode", ["F1", "P1"])
def test_16__validate_user_str(engine, user_input, expected_output):
    """Test16 ExecutionEngineCommon()._validate_user_str()."""
    result = engine._validate_user_str(user_input)
    assert result == expected_output


@pytest.mark.parametrize("user,hostauth_return,container_auth_return,opt_hostauth,expected_validity,expected", [
    ("123:", None, None, False, False, (False, {})),
    ("user1", ("user1", "1000", "1000", "gecos1", "/home/user1", "/bin/bash"), None, True,
     {"user": "user1", "uid": "1000", "gid": "1000", "gecos": "gecos1", "home": "/home/user1", "shell": "/bin/bash"},
     (True, {'user': 'user1'})),
    ("user2", None, ("user2", "2000", "2000", "gecos2", "/home/user2", "/bin/bash"), False,
     {"user": "user2", "uid": "2000", "gid": "2000", "gecos": "gecos2", "home": "/home/user2", "shell": "/bin/bash"},
     (True, {'user': 'user2'})),
])
@pytest.mark.parametrize("xmode", ["F1", "P1"])
def test_17__user_from_str(mocker, engine, user, hostauth_return, container_auth_return, opt_hostauth,
                           expected_validity, expected):
    """Test16 ExecutionEngineCommon()._validate_user_str()."""
    mock_nixauth_instance = mocker.Mock()
    mocker.patch.object(engine, 'opt', {"hostauth": opt_hostauth})

    if hostauth_return:
        mock_nixauth_instance.get_user.return_value = hostauth_return
        assert engine._user_from_str(user, host_auth=mock_nixauth_instance) == expected

    if container_auth_return:
        mock_nixauth_instance.get_user.return_value = container_auth_return
        assert engine._user_from_str(user, container_auth=mock_nixauth_instance) == expected

    if not hostauth_return and not container_auth_return:
        assert engine._user_from_str(user) == expected

    if expected_validity:
        assert engine.opt["user"] == expected_validity["user"]
        assert engine.opt["uid"] == expected_validity["uid"]
        assert engine.opt["gid"] == expected_validity["gid"]
        assert engine.opt["gecos"] == expected_validity["gecos"]
        assert engine.opt["home"] == expected_validity["home"]
        assert engine.opt["shell"] == expected_validity["shell"]


@pytest.mark.parametrize(
    "user_input,validity,uid,gid,username,expected_username,ismountpoint,hostauth,containerauth,not_found,"
    "expected_uid,expected_gid,expected",
    [
        (None, True, "1001", "1001", "username", "username", False, True, True, False, "1001", "1001", True),
        ("invuser", False, "100", "50", "username", "username", False, False, False, False, "100", "50", False),
        ("root", True, "0", "0", "root", "root", False, True, True, False, "0", "0", True),
        ("u1", True, "1001", "1001", "u1", "u1", True, True, True, False, "1001", "1001", True),
        ("", True, "1001", "1001", "", "root", False, False, False, False, "", "", True),
        (None, True, "1001", "1001", None, None, False, True, False, True, "1001", "1001", False),
        (None, True, "1002", "1002", None, "root", False, False, False, False, "", "", True),
    ]
)
@pytest.mark.parametrize("xmode", ["F1", "P1"])
def test_18__setup_container_user(mocker, engine, logger, user_input, validity, uid, gid, username, expected_username,
                                  ismountpoint, hostauth, containerauth, not_found, expected_uid, expected_gid,
                                  expected):
    """Test18 ExecutionEngineCommon()._setup_container_user()."""
    mocker.patch.object(HostInfo, "username", return_value=user_input)
    mocker.patch.object(HostInfo, "uid", uid)
    mocker.patch.object(HostInfo, "gid", gid)
    mocker.patch.object(engine, '_user_from_str', return_value=(validity, uid))
    mocker.patch.object(engine, '_is_mountpoint', return_value=ismountpoint)
    mocker.patch.object(engine, '_create_user')
    mocker.patch.object(engine, 'opt', {
        "user": username,
        "hostauth": hostauth,
        "containerauth": containerauth,
        "vol": list(),
        'bindhome': False,
        'home': '/home/user',
        'shell': '/bin/sh',
        'gecos': '*udocker*',
        'uid': uid,
        'gid': gid,
    })

    assert engine._setup_container_user(user_input) == expected
    assert engine.opt["user"] == expected_username
    assert engine.opt["uid"] == expected_uid
    assert engine.opt["gid"] == expected_gid
    # assert engine.opt["hostauth"] == hostauth
    # assert engine.opt["containerauth"] == containerauth
    # FIXME: asserts for hostauth and containerauth depends on the _create_user if mocked can be done otherwhise
    #       hostauth and containerauth can be changed inside the function - need further debugging

    if not validity:
        assert logger.error.call_args_list == [
            mocker.call('invalid syntax for user; %s', mocker.ANY)]  # FIXME: this should be changed :

    if not_found:
        assert logger.error.call_args_list == [mocker.call('user not found')]


@pytest.mark.parametrize(
    "user_input, validity, uid, gid, username, expected_username, ismountpoint, hostauth, containerauth, not_found, "
    "expected",
    [
        (None, True, "1001", "1001", "username", "username", False, True, True, False, True),
        ("invuser", False, "100", "50", "username", "username", False, False, False, False, False),
        ("root", True, "0", "0", "root", "root", False, True, True, False, True),
        ("u1", True, "1001", "1001", "u1", "u1", True, True, True, False, True),
        ("", True, "1001", "1001", "", "udoc1001", False, False, False, False, True),
        (None, True, "1001", "1001", None, None, False, True, False, True, False),
        (None, True, "1002", "1002", None, "udoc1002", False, False, False, False, True),
    ], ids=[
        "default_user_valid_uidgid_nomount",
        "invalid_user",
        "root_user",
        "custom_user_mount",
        "empty_user",
        "null_user_existing_uidgid",
        "null_user_nonexisting_uidgid",
    ])
@pytest.mark.parametrize("xmode", ["F1", "P1"])
def test_19__set_cont_user_noroot(mocker, engine, logger, mocker_nixauth, user_input, validity, uid, gid, username,
                                  expected_username,
                                  ismountpoint, hostauth, containerauth, not_found, expected):
    """Test19 ExecutionEngineCommon()._setup_container_user_noroot()."""
    host_auth_mock = mocker.Mock(spec=NixAuthentication)
    container_auth_mock = mocker.Mock(spec=NixAuthentication)
    mocker_nixauth.side_effect = [host_auth_mock, container_auth_mock]

    mocker.patch.object(HostInfo, "username", return_value=username if user_input is None else user_input)
    mocker.patch.object(HostInfo, "uid", uid)
    mocker.patch.object(HostInfo, "gid", gid)
    mocker.patch.object(engine, '_user_from_str',
                        return_value=(validity, {"user": expected_username, "uid": uid, "gid": gid}))
    mocker.patch.object(engine, '_is_mountpoint', return_value=ismountpoint)
    create_user_mock = mocker.patch.object(engine, '_create_user')

    mocker.patch.object(engine, 'opt', {
        "user": username,
        "hostauth": hostauth,
        "containerauth": containerauth,
        "vol": list(),
        'bindhome': False,
        'home': '/home/user',
        'shell': '/bin/sh',
        'gecos': '*udocker*',
        'uid': uid,
        'gid': gid,
    })

    set_cont_user_noroot = engine._setup_container_user_noroot(user_input)
    assert set_cont_user_noroot == expected
    assert engine.opt["user"] == expected_username
    assert engine.opt["uid"] == uid
    assert engine.opt["gid"] == gid
    assert engine.opt["hostauth"] == (not ismountpoint and hostauth)
    assert engine.opt["containerauth"] == (not ismountpoint and containerauth)

    if validity and not ismountpoint and not not_found:
        create_user_mock.assert_called_once_with(container_auth_mock, host_auth_mock)
    else:
        create_user_mock.assert_not_called()

    if not validity:
        assert logger.error.call_args_list == [mocker.call('invalid syntax for user: %s', mocker.ANY)]

    if not_found:
        assert logger.error.call_args_list == [mocker.call('user not found on host')]


@pytest.mark.parametrize("initial_opts, expected_opts", [
    ({'uid': None, 'gid': None, 'user': None, 'home': None, 'shell': None, 'gecos': None, 'bindhome': True},
     {'uid': '0', 'gid': '0', 'user': 'udoc0', 'home': '/home/user', 'shell': '/bin/sh', 'gecos': '*udocker*',
      'bindhome': True}),
    ({'uid': None, 'gid': None, 'user': None, 'home': None, 'shell': None, 'gecos': None, 'bindhome': False},
     {'uid': '0', 'gid': '0', 'user': 'udoc0', 'home': '/', 'shell': '/bin/sh', 'gecos': '*udocker*',
      'bindhome': False}),
    ({'uid': '0', 'gid': '0', 'user': 'udoc0', 'home': '/', 'shell': '/bin/sh', 'gecos': '*udocker*',
      'bindhome': False},
     {'uid': '0', 'gid': '0', 'user': 'udoc0', 'home': '/', 'shell': '/bin/sh', 'gecos': '*udocker*',
      'bindhome': False}),
])
@pytest.mark.parametrize("xmode", ["F1", "P1"])
def test_20__fill_user(mocker, engine, initial_opts, expected_opts):
    """Test20 ExecutionEngineCommon()._fill_user()."""
    mocker.patch.object(HostInfo, 'uid', expected_opts['uid'])
    mocker.patch.object(HostInfo, 'gid', expected_opts['gid'])
    mocker.patch.object(NixAuthentication, 'get_home', side_effect=['/home/user'])

    mocker.patch.object(engine, 'opt', initial_opts)
    engine._fill_user()

    assert engine.opt == expected_opts


@pytest.mark.parametrize("containerauth, hostauth, expected_hostauth, log_warning, passwd_exists, group_exists", [
    (True, True, False, False, True, True),
    (True, False, False, False, True, True),
    (False, True, True, False, True, True),
    (False, False, True, True, False, False),
])
@pytest.mark.parametrize("xmode", ["F1", "P1"])
def test_21__create_user(mocker, engine, logger, mocker_nixauth, containerauth, hostauth, expected_hostauth,
                         log_warning, passwd_exists,
                         group_exists):
    """Test21 ExecutionEngineCommon()._create_user()."""
    mocker.patch.object(FileUtil, 'umask')
    mocker.patch.object(FileUtil, 'mktmp', return_value="/tmp/passwd")
    mocker.patch.object(FileUtil, 'copyto')
    mocker.patch.object(os, 'getgroups', return_value=[1001, 1002])

    mock_nix_auth_instance = mocker_nixauth.return_value
    mocker.patch.object(mock_nix_auth_instance, 'add_user', return_value=True)
    mocker.patch.object(mock_nix_auth_instance, 'add_group', return_value=True)
    mocker.patch.object(mock_nix_auth_instance, 'passwd_file', return_value="/c/etc/passwd")
    mocker.patch.object(mock_nix_auth_instance, 'group_file', return_value="/c/etc/group")

    mock_host_auth = mocker.Mock()
    mock_host_auth.get_group.return_value = ("", "x1", "x2")

    mocker.patch.object(engine, 'opt', {
        "containerauth": containerauth,
        "hostauth": hostauth,
        'uid': 1001,
        'gid': 1001,
        'user': 'user',
        'bindhome': True,
        'home': '/home/user',
        'shell': '/bin/sh',
        'gecos': '*udocker*',
    })

    assert engine._create_user(mock_nix_auth_instance, mock_host_auth) is True
    assert engine.opt["hostauth"] == expected_hostauth
    assert logger.warning.called == log_warning

    if not containerauth:
        FileUtil.mktmp.assert_called()
        assert engine.hostauth_list == ('/tmp/passwd:/etc/passwd', '/tmp/passwd:/etc/group')


@pytest.mark.parametrize("cmd,container_id,nobanner,expected", [
    ("/bin/ls", "container1234", False,
     '############################################################################\n'
     '|                                                                          '
     '|\n'
     '|                          starting container1234                          '
     '|\n'
     '|                                                                          '
     '|\n'
     '############################################################################\n'
     '\n'
     'executing: ls\n'
     '____________________________________________________________________________\n',),
    ("/bin/ls", "container1234", True, None),
])
@pytest.mark.parametrize("xmode", ["F1", "P1"])
def test_22__run_banner(mocker, engine, cmd, container_id, nobanner, expected):
    """Test22 ExecutionEngineCommon()._run_banner()."""

    mock_msg_info = mocker.patch('udocker.engine.base.MSG.info')
    engine.container_id = container_id
    engine.opt = {"nobanner": nobanner}

    engine._run_banner(cmd)

    if not nobanner:
        mock_msg_info.assert_called_once_with(expected)
    else:
        assert not mock_msg_info.called


@pytest.mark.parametrize("initial_env,invalid_host_env,valid_host_env,hostenv_opt,expected", [
    ({'HOME': '/', 'USERNAME': 'user', }, ("USERNAME",), ("HOME",), False, {'HOME': '/'}),
    ({'HOME': '/', 'USERNAME': 'user', }, ("USERNAME", "HOME",), (), False, {}),
])
@pytest.mark.parametrize("xmode", ["F1", "P1"])
def test_23__run_env_cleanup_dict(mocker, engine, initial_env, invalid_host_env, valid_host_env, hostenv_opt, expected):
    """Test23 ExecutionEngineCommon()._run_env_cleanup_dict()."""

    mocker.patch.dict(os.environ, initial_env)
    mocker.patch.object(Config, 'conf', {'invalid_host_env': invalid_host_env, 'valid_host_env': valid_host_env})
    engine.opt = {"hostenv": hostenv_opt}

    engine._run_env_cleanup_dict()

    assert os.environ == expected


@pytest.mark.parametrize("initial_env,invalid_host_env,valid_host_env,container_env,hostenv_opt,expected", [
    ({'HOME': '/', 'USERNAME': 'user', }, ("USERNAME",), ("HOME",), {'PATH': '/usr/bin'}, False,
     {'HOME': '/', 'USERNAME': 'user'}),
    ({'HOME': '/', 'USERNAME': 'user', 'PATH': '/user/bin'}, ("USERNAME",), ("HOME",), {'PATH': '/usr/bin'}, True,
     {'HOME': '/', 'USERNAME': 'user', 'PATH': '/user/bin', }),
])
@pytest.mark.parametrize("xmode", ["F1", "P1"])
def test_24__run_env_cleanup_list(mocker, engine, initial_env, invalid_host_env, valid_host_env, container_env,
                                  hostenv_opt, expected):
    """Test24 ExecutionEngineCommon()._run_env_cleanup_list()."""
    uenv_instance = Uenv()  # this can be done with magickmock
    for key, value in initial_env.items():
        uenv_instance.append(f"{key}={value}")

    mocker.patch.object(Config, 'conf', {
        'invalid_host_env': invalid_host_env,
        'valid_host_env': valid_host_env
    })

    mocker.patch.object(os.environ, 'items', return_value=initial_env.items())
    mocker.patch.dict('os.environ', initial_env)

    engine.opt = {
        "env": uenv_instance,
        "hostenv": hostenv_opt
    }

    engine._run_env_cleanup_list()

    assert engine.opt["env"].dict() == expected


#
@pytest.mark.parametrize("username,uid,expected_ps1", [
    ("root", "0", "2717add4 #"),
    ("user1", "1000", "2717add4 \\$"),
])
@pytest.mark.parametrize("xmode", ["F1", "P1"])
def test_25__run_env_set(mocker, engine, xmode, username, uid, expected_ps1):
    """Test25 ExecutionEngineCommon()._run_env_set()."""
    uenv_instance = Uenv()
    mocker.patch.object(uenv_instance, 'appendif', side_effect=uenv_instance.appendif)
    mocker.patch.object(uenv_instance, 'append', side_effect=uenv_instance.append)
    mocker.patch.object(HostInfo, 'username', return_value=username)
    mocker.patch.object(engine, 'opt', {
        "env": uenv_instance,
        "home": f"/home/{username}",
        "user": username,
        "uid": uid
    })
    mocker.patch.object(engine, 'container_id', "2717add4-e6f6-397c-9019-74fa67be439f")
    mocker.patch.object(engine, 'container_root', "/mocked/container/root")
    mocker.patch.object(engine, 'container_names', ['cna[]me', ])

    mock_exec_mode = mocker.Mock()
    mocker.patch.object(mock_exec_mode, 'get_mode', return_value=xmode)
    mocker.patch.object(engine, 'exec_mode', mock_exec_mode)

    expected = [
        "home=" + f"/home/{username}",
        "user=" + username,
        "logname=" + username,
        "username=" + username,
        "ps1=" + expected_ps1,
        "shlvl=0",
        "container_ruser=" + username,
        "container_root=/mocked/container/root",
        "container_uuid=2717add4-e6f6-397c-9019-74fa67be439f",
        "container_execmode=" + xmode,
        "container_names=cname",
    ]

    engine._run_env_set()
    assert set(uenv_instance.list()) == set(expected)


@pytest.mark.parametrize("envfile_content, expected", [
    ("", set()),
    ("HOME=/home/user\nUSERNAME=user\nSHLVL=0", {"HOME=/home/user", "USERNAME=user", "SHLVL=0"}),
])
@pytest.mark.parametrize("xmode", ["F1", "P1"])
def test_26__run_env_cmdoptions(mocker, engine, envfile_content, expected):
    """Test26 ExecutionEngineCommon()._run_env_cmdoptions()."""
    uenv_instance = Uenv()
    mocker.patch.object(uenv_instance, 'appendif', side_effect=uenv_instance.appendif)
    mocker.patch.object(FileUtil, 'getdata', return_value=envfile_content)
    mocker.patch.object(engine, 'opt', {"envfile": ["/dir/env"], "env": uenv_instance})
    engine._run_env_cmdoptions()

    assert set(uenv_instance.list()) == expected


@pytest.mark.parametrize(
    "container_os, container_arch, container_variant, host_platform, log_warning",
    [
        (None, "arm64", "glibc", "linux/x86_64/glibc", False),
        ("linux", "x86_64", "glibc", "linux/x86_64/glibc", False),
        ("linux", "x86_64", "musl", "linux/x86_64/glibc", True),
        ("windows", "x86_64", "", "linux/x86_64/glibc", True),
        ("linux", "arm64", "glibc", "linux/x86_64/glibc", True),
    ])
@pytest.mark.parametrize("xmode", ["F1", "P1"])
def test_27__check_platform(mocker, engine, logger, container_os, container_arch, container_variant, host_platform,
                            log_warning):
    """Test27 ExecutionEngineCommon()._check_platform()."""
    mocker.patch.object(engine, 'container_os', container_os)
    mocker.patch.object(engine, 'container_architecture', container_arch)
    mocker.patch.object(engine, 'container_variant', container_variant)

    mocker.patch.object(HostInfo, "platform_to_str",
                        return_value=f"{container_os}/{container_arch}/{container_variant}" if container_os else None)
    mocker.patch.object(HostInfo, "is_same_platform", side_effect=lambda platform: platform == host_platform)
    mocker.patch.object(HostInfo, "platform", return_value=host_platform)

    engine._check_platform()

    logger.warning.assert_called_once_with(
        "container platform (%s) does not match host platform (%s)", mocker.ANY, mocker.ANY) if log_warning else \
        logger.warning.assert_not_called()


@pytest.mark.parametrize(
    "error,container_dir,config_location,setup_result,volume,paths,executable,expected",
    [
        (ValueError, None, None, True, True, True, "/bin/exec", ""),
        (None, None, None, True, True, True, "/bin/exec", ""),
        (None, "/path/to/container", None, True, True, True, "/bin/exec", "/path/to/container/exec"),
        (None, "/another/container/path", None, False, True, True, "/bin/exec", ""),
        (None, "/yet/another/path", None, True, False, True, "/bin/exec", ""),
        (None, "/some/path", None, True, True, False, "/bin/exec", ""),
        (None, "/final/path", None, True, True, True, "/bin/exec", "/final/path/exec"),
        (None, "/final/path", "/ROOT", True, True, True, "/bin/exec", "/final/path/exec"),
    ])
@pytest.mark.parametrize("xmode", ["F1", "P1"])
def test_28__run_init(mocker, engine, error, container_dir, config_location, setup_result, volume, paths, executable,
                      expected):
    """Test28 ExecutionEngineCommon()._run_init()."""
    mocker.patch.object(engine.localrepo, 'cd_container', return_value="/path/to/container")
    if error:
        mocker.patch.object(engine, '_run_load_metadata', side_effect=error)
    else:
        mocker.patch.object(engine, '_run_load_metadata', return_value=(container_dir, None))
    mocker.patch.object(engine, '_check_platform')
    mocker.patch.object(engine, '_run_env_cmdoptions')
    mocker.patch.object(engine, '_check_exposed_ports')
    mocker.patch.object(engine, '_setup_container_user', return_value=setup_result)
    mocker.patch.object(engine, '_set_volume_bindings', return_value=volume)
    mocker.patch.object(engine, '_check_paths', return_value=paths)
    mocker.patch.object(engine, '_check_executable',
                        return_value=container_dir + '/' + 'exec' if container_dir else executable)

    mocker.patch.object(Config, 'conf', {'location': config_location, 'tmpdir': '/tmp', })

    result = engine._run_init("2717add4-e6f6-397c-9019-74fa67be439f")
    assert result == expected


@pytest.mark.parametrize("file_content, expected", [
    ('{"key": "value"}', {"key": "value"}),  # Valid JSON
    ('', {}),  # Empty file
    ('invalid json', {}),  # Invalid JSON
    (pytest.raises(IOError), {}),  # IOError exception
    (pytest.raises(OSError), {}),  # OSError exception
    (pytest.raises(ValueError), {}),  # ValueError exception
    (pytest.raises(TypeError), {}),  # TypeError exception
], ids=[
    "valid_json",
    "empty_file",
    "invalid_json",
    "ioerror",
    "oserror",
    "valueerror",
    "typeerror",
])
@pytest.mark.parametrize("xmode", ["F1", "P1"])
def test_29__get_saved_osenv(mocker, engine, file_content, expected):
    """ Test29 ExecutionEngineCommon()._get_saved_osenv()."""
    mock_getdata = mocker.patch.object(FileUtil, 'getdata')
    if isinstance(file_content, Exception):
        mock_getdata.side_effect = file_content
    else:
        mock_getdata.return_value = file_content

    result = engine._get_saved_osenv('some_file.json')

    assert result == expected


@pytest.mark.parametrize("file_contents,osversion,oskernel,arch,osdistribution,error,expected", [
    ('{}', "", "", "", "", does_not_raise(), {}),
    ('not_a_valid_json', "", "", "", "", does_not_raise(), {}),
    ('{"osversion": "linux", "oskernel": "", "arch": ""}', "linux", "3.2.1", "amd64", "ubuntu", does_not_raise(), {}),
    ('{"osversion": "linux", "oskernel": "3.2.1", "arch": "amd64", "osdistribution": "ubuntu"}', "linux", "3.2.1",
     "amd64", "ubuntu", does_not_raise(),
     {'arch': 'amd64', 'osdistribution': 'ubuntu', 'oskernel': '3.2.1', 'osversion': 'linux'}),
])
@pytest.mark.parametrize("xmode", ["F1", "P1"])
def test_30__is_same_osenv(mocker, engine, file_contents, osversion, oskernel, arch, osdistribution, error, expected):
    """Test30 ExecutionEngineCommon()._is_same_osenv()."""
    mocker.patch.object(HostInfo, 'osversion', side_effect=[osversion])
    mocker.patch.object(HostInfo, 'oskernel', return_value=oskernel)
    mocker.patch.object(HostInfo, 'arch', return_value=arch)
    mocker.patch.object(OSInfo, 'osdistribution', return_value=osdistribution)
    mocker.patch.object(FileUtil, 'getdata', return_value=file_contents)

    with error:
        result = engine._is_same_osenv("dummy_filename")
        assert result == expected


@pytest.mark.parametrize("osversion,oskernel,arch,osdistribution,putdata_return,error,expected", [
    ("linux", "3.2.1", "amd64", "ubuntu", True, False, True),
    ("linux", "3.2.1", "amd64", "ubuntu", False, False, False),
    (ValueError("Error"), "3.2.1", "amd64", "ubuntu", True, True, False),
    (None, "3.2.1", "amd64", "ubuntu", False, False, False),
    (None, "3.2.1", "amd64", "ubuntu", False, False, False),
])
@pytest.mark.parametrize("xmode", ["F1", "P1"])
def test_31__save_osenv(mocker, engine, osversion, oskernel, arch, osdistribution, putdata_return, error, expected):
    """Test31 ExecutionEngineCommon()._save_osenv()."""
    mocker.patch.object(HostInfo, 'osversion', side_effect=[osversion])
    mocker.patch.object(HostInfo, 'oskernel', return_value=oskernel)
    mocker.patch.object(HostInfo, 'arch', return_value=arch)
    mocker.patch.object(OSInfo, 'osdistribution', return_value=osdistribution)
    mocker.patch.object(FileUtil, 'putdata', return_value=putdata_return)

    save = dict()
    engine._save_osenv("dummy_filename", save) == expected

    if not error:
        assert save["osversion"] == osversion
        assert save["oskernel"] == oskernel
        assert save["arch"] == arch
        assert save["osdistribution"] == osdistribution


@pytest.mark.parametrize("is_same_arch, fail, expected_result, expected_log", [
    (True, False, True, None),
    (True, True, True, None),
    (False, False, True, logging.warning),
    (False, True, False, logging.error),
], ids=[
    "arch_match_no_fail",
    "arch_match_fail",
    "arch_mismatch_no_fail",
    "arch_mismatch_fail",
])
@pytest.mark.parametrize("xmode", ["F1", "P1"])
def test_32__check_arch(mocker, engine, logger, is_same_arch, fail, expected_result, expected_log):
    """ Test32 ExecutionEngineCommon()._check_arch()."""
    mocker.patch.object(OSInfo, 'is_same_arch', return_value=is_same_arch)

    result = engine._check_arch(fail)
    assert result == expected_result

    if expected_log == logging.warning:
        logger.warning.assert_called_once_with("host and container architectures mismatch")
    elif expected_log == logging.error:
        logger.error.assert_called_once_with("host and container architectures mismatch")
    else:
        logger.warning.assert_not_called()
        logger.error.assert_not_called()


@pytest.mark.parametrize("arch, qemu_exec_found, return_path, expected_result, expected_log", [
    ([None, "x86_64"], False, False, "", None),
    (["arm", None], False, False, "", None),
    (["x86_64", "x86_64"], False, False, "", None),
    (["arm", "x86_64"], False, False, "", "error"),
    (["arm", "x86_64"], True, False, "qemu-arm", None),
    (["arm", "x86_64"], True, True, "/path/to/qemu-arm", None),
], ids=[
    "no_container_qemu",
    "no_host_qemu",
    "matching_arch",
    "mismatched_arch_no_qemu",
    "mismatched_arch_qemu_found_filename",
    "mismatched_arch_qemu_found_path",
])
@pytest.mark.parametrize("xmode", ["F1", "P1"])
def test_33__get_qemu(mocker, engine, logger, arch, qemu_exec_found, return_path, expected_result, expected_log):
    """ Test33 ExecutionEngineCommon()._get_qemu()."""
    mocker.patch.object(OSInfo, 'arch', side_effect=arch)
    mocker.patch.object(FileUtil, 'find_exec', return_value="/path/to/qemu-arm" if qemu_exec_found else None)

    result = engine._get_qemu(return_path)
    assert result == expected_result

    logger.error.assert_called_once_with(
        "qemu required but not available") if expected_log else logger.error.assert_not_called()
