#!/usr/bin/env python

# -*- coding: utf-8 -*-
"""
udocker unit tests: ContainerStructure
"""
import logging
import os
import random
import subprocess

import pytest

from udocker.config import Config
from udocker.container.structure import ContainerStructure
from udocker.helper.hostinfo import HostInfo
from udocker.helper.unique import Unique
from udocker.utils.fileutil import FileUtil
from udocker.utils.uprocess import Uprocess


@pytest.fixture
def container_id():
    return str(random.randint(1, 1000))


@pytest.fixture
def lrepo(mocker, container_id):
    mock_lrepo = mocker.patch('udocker.container.localrepo.LocalRepository')
    mock_lrepo._container_id = container_id
    return mock_lrepo


@pytest.fixture
def container_struct(lrepo, container_id):
    return ContainerStructure(lrepo, container_id)


@pytest.fixture
def logger(mocker):
    return mocker.patch('udocker.container.structure.LOG')


@pytest.mark.parametrize("container_id", ["123456", "", None, ], ids=[
    "container id is valid",
    "container id is empty",
    "container id is None",
])
def test_01_init(container_struct, lrepo, container_id):
    """Test01 ContainerStructure()."""
    assert container_struct.localrepo == lrepo
    assert container_struct.container_id == container_id
    assert container_struct.tag == ""
    assert container_struct.imagerepo == ""


@pytest.mark.parametrize("location_set,cd_container_return,load_json_return,logmsg,expected", [
    ("/", None, None, False, ("", [])),
    ("", "/path/to/container", {"some": "data"}, False, ("/path/to/container", {"some": "data"})),
    ("", None, None, "container id or name not found", (False, False)),
    ("", "/path/to/container", None, "invalid container json metadata", (False, False)),
], ids=[
    "location is set in config",
    "container directory found, valid JSON",
    "container directory not found",
    "Invalid container JSON metadata",
])
def test_02_get_container_attr(mocker, container_struct, logger, location_set, cd_container_return, load_json_return,
                               logmsg, expected):
    """Test02 ContainerStructure().get_container_attr()."""
    mocker.patch.object(Config, 'conf', {'location': location_set})
    mocker.patch.object(container_struct.localrepo, 'cd_container', return_value=cd_container_return)
    mocker.patch.object(container_struct.localrepo, 'load_json', return_value=load_json_return)

    get_container_attr = container_struct.get_container_attr()

    assert get_container_attr == expected
    logger.error.assert_called_with(logmsg) if logmsg else logger.error.assert_not_called()


@pytest.mark.parametrize("manifest_json, expected_output", [
    ({"architecture": "x86_64", "os": "linux", "variant": "v8"}, "linux/x86_64/v8"),
    ({"architecture": "x86_64", "os": "linux"}, "linux/x86_64"),
    ({"architecture": "x86_64"}, "unknown/x86_64"),
    ({"os": "linux"}, "linux/unknown"),
    ({}, "unknown/unknown"),
    (None, "unknown/unknown"),
])
def test_03_get_container_platform_fmt(mocker, container_struct, manifest_json, expected_output):
    """Test03 ContainerStructure().get_container_platform_fmt()."""
    mocker.patch.object(container_struct, 'get_container_attr', return_value=(None, manifest_json))
    result = container_struct.get_container_platform_fmt()
    assert result == expected_output


@pytest.mark.parametrize("config,param,default,expected", [
    (False, "Cmd", "", "/bin/bash"),
    (True, "Cmd", "", "/bin/bash"),
    (True, "NonExistent", "", ""),
    (True, "NonExistentList", [], []),
    (True, "NonExistentDict", {}, {}),
    (True, "Entrypoint", "DefaultString", "DefaultString"),
    (False, "Env", [], ["PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:bin"]),
    (True, "Labels", {},
     {"build-date": "20161102", "license": "GPLv2", "name": "CentOS Base Image", "vendor": "CentOS"}),  # Dict default
    (True, "SplitParam", "default_string", "split value"),
    (True, "DictToList", [], ["key1:value1", "key2:value2"]),
    (True, "DictItem", "default_string", "key1:value1 key2:value2 "),
    (False, "DirectParam", ["default"], ["direct_value"]),
    (True, "Hostname", "default_hostname", "9aac06993d69"),
    (False, "Tty", "default_tty", False),
    (True, "Volumes", "default_volumes", "default_volumes"),
    (True, "OnBuild", None, None),
    (True, "architecture", "", "amd64"),
], ids=[
    "cmd in config, default str",
    "cmd in container_config, default str",
    "non-existent key, default str",
    "non-existent key, default list",
    "non-existent key, default dict",
    "entrypoint is None, default str",
    "env list, default list",
    "labels dict, default dict",
    "string to list transformation",
    "dict to list transformation",
    "dict to str transformation",
    "direct param, root level",
    "hostname in config, default str",
    "tty in config, default str",
    "volumes in config, default str",
    "onbuild in config, default None",
    "architecture as direct param"
])
def test_04__get_container_meta(container_struct, config, param, default, expected):
    """Test04 ContainerStructure().get_container_meta()."""
    container_json = {
        "architecture": "amd64",
        "author": "https://github.com/CentOS/sig-cloud-instance-images",
        "config": {
            "AttachStderr": False,
            "AttachStdin": False,
            "AttachStdout": False,
            "Cmd": [
                "/bin/bash"
            ],
            "Domainname": "",
            "Entrypoint": None,
            "Env": [
                "PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:bin"
            ],
            "Hostname": "9aac06993d69",
            "Image": "sha256:4f64745dd34556af8f644a7886fcf" +
                     "cb11c059f64e1b0a753cb41188656ec8b33",
            "Labels": {
                "build-date": "20161102",
                "license": "GPLv2",
                "name": "CentOS Base Image",
                "vendor": "CentOS"
            },
            "OnBuild": None,
            "OpenStdin": False,
            "StdinOnce": False,
            "Tty": False,
            "User": "",
            "Volumes": None,
            "WorkingDir": "",
            "DirectParam": "direct_value",
            "SplitParam": "split value",
            "DictToList": {"key1": "value1", "key2": "value2"},
            "DictItem": {"key1": "value1", "key2": "value2"},
        },
    }
    container_json['container_config'] = container_json.pop('config') if not config else None
    result = container_struct._get_container_meta(param, default, container_json)
    assert result == expected


@pytest.mark.parametrize("param, default, expected", [
    ("Cmd", "default_cmd", "/bin/bash"),
    ("Env", "default_env", "PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:bin"),
    ("NonExistent", "", ""),
    ("Missing", "default_value", "default_value"),
    ("DictItem", "default_value", "key1:value1 key2:value2 "),
    ("SplitParam", "default_value", "split value"),
])
def test_05_get_container_meta(container_struct, param, default, expected):
    """Test05 ContainerStructure().get_container_meta()."""
    container_json2 = {
        "architecture": "amd64",
        "author": "https://github.com/CentOS/sig-cloud-instance-images",
        "config": {
            "Cmd": [
                "/bin/bash"
            ],
            "Domainname": "",
            "Entrypoint": None,
            "Env": [
                "PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:bin"
            ],
            "Hostname": "9aac06993d69",
            "WorkingDir": "",
            "DirectParam": "direct_value",
            "SplitParam": "split value",
            "DictToList": {"key1": "value1", "key2": "value2"},
            "DictItem": {"key1": "value1", "key2": "value2"},
        },
    }

    result = container_struct.get_container_meta(param, default, container_json2)
    assert result == expected


@pytest.mark.parametrize("input_dict,expected", [
    ({}, ""),
    ({"A": "1"}, "A:1 "),
    ({"A": "1", "B": "2"}, "A:1 B:2 "),
    ({"A": 123, "B": [1, 2, 3]}, "A:123 B:[1, 2, 3] "),
    ({"A": {"B": "1"}}, "A:{'B': '1'} "),
], ids=[
    "Empty dictionary",
    "Single key-value pair",
    "Multiple key-value pairs",
    "Different data types as values",
    "Nested dictionary",
])
def test_06__dict_to_str(container_struct, input_dict, expected):
    """Test06 ContainerStructure()._dict_to_str()."""
    assert container_struct._dict_to_str(input_dict) == expected


@pytest.mark.parametrize("test_input,expected", [
    ({"A": 1, "B": "two"}, ["A:1", "B:two"]),
    ({}, []),
    ({"A": 123, "B": [1, 2, 3], "C": "value"}, ['A:123', 'B:[1, 2, 3]', 'C:value']),
    ({"A": {"B": "1"}}, ["A:{'B': '1'}"]),
])
def test_07__dict_to_list(container_struct, test_input, expected):
    """Test07 ContainerStructure()._dict_to_list()."""
    assert container_struct._dict_to_list(test_input) == expected


@pytest.mark.parametrize("container_id,container_dir,expected,existing_paths", [
    (None, "/fake/container/dir", 5, ["/lib", "/bin", "/etc", "/tmp", "/var"]),
    (12345, "/fake/container/dir", 3, ["/usr", "/sys", "/dev"]),
    (12345, None, 0, ["/usr", "/sys", "/dev"]),
    (12345, "", 0, ["/usr", "/sys", "/dev"]),
    ("invalid_id", "/fake/container/dir", 0, []),
])
def test_08__chk_container_root(mocker, container_struct, container_id, container_dir, expected, existing_paths):
    """Test08 ContainerStructure()._chk_container_root()."""
    mocker.patch.object(container_struct.localrepo, "cd_container", return_value=container_dir)
    mocker.patch("os.path.exists",
                 side_effect=lambda path: any(path == container_dir + "/ROOT" + ep for ep in existing_paths))
    assert container_struct._chk_container_root(container_id) == expected


@pytest.mark.parametrize(
    "container_id, image_dir, log_error, log_warn, img_attributes, setup_container, untar, chk_container, expected",
    [
        ("123456", False, "create container: imagerepo is invalid", "", (None, None), False, False, False, False),
        ("123456", True, "create container: getting layers or json", "", (None, None), False, False, False, False),
        ("123456", True, "create container: setting up container", "", (["value", "value"], ["value2", "layer2"]),
         False, False, False, False),
        ("123456", True, "creating container: %s", "", (["value", "value"], ["value2", "layer2"]), True, False, False,
         "123456"),
        ("123456", True, "", "check container content: %s", (["value", "value"], ["value2", "layer2"]), True, True,
         False, "123456"),
        ("123456", True, "", "", (["value", "value"], ["value2", "layer2"]), True, True, False, "123456"),
        (None, True, "", "", (["value", "value"], ["value2", "layer2"]), True, True, False, "123456"),
    ], ids=[
        "image repo invalid",
        "getting layers or json fails",
        "setting up container fails",
        "untar layers fails",
        "check container content fails",
        "success scenario",
        "success scenario, no container id"
    ])
def test_09_create_fromimage(mocker, container_struct, container_id, logger, image_dir, log_error, log_warn,
                             img_attributes, setup_container, untar, chk_container, expected):
    """Test09 ContainerStructure().create_fromimage()."""
    mocker.patch.object(container_struct.localrepo, 'cd_imagerepo', return_value="/" if image_dir else None)
    mocker.patch.object(container_struct.localrepo, 'get_image_attributes', return_value=img_attributes)
    mocker.patch.object(container_struct.localrepo, 'setup_container',
                        return_value="/ROOT" if setup_container else None)
    mocker.patch.object(container_struct.localrepo, 'save_json', return_value="/ROOT" if setup_container else None)
    mocker.patch.object(container_struct, '_untar_layers', return_value=untar)
    mocker.patch.object(container_struct, '_chk_container_root', return_value=chk_container)

    mocker.patch.object(os.path, 'basename', return_value="fake_basename")
    mocker.patch.object(Unique, 'uuid', return_value="123456")

    result = container_struct.create_fromimage("imagerepo", "tag")
    assert result == expected

    if log_error:
        assert mocker.call(log_error) in logger.error.call_args_list or \
               mocker.call(log_error, mocker.ANY) in logger.error.call_args_list

    if log_warn:
        logger.warning.assert_called_with(log_warn, mocker.ANY)


@pytest.mark.parametrize(
    "container_id, cntjson_exists, logmsg_error, logmsg_warning, setup_cont, untar_status, chk_root_status, expected",
    [
        ("123456", False, "create container: getting json", None, None, False, False, False),
        ("123456", True, "create container: setting up", None, None, False, False, False),
        ("123456", True, "creating container: %s", None, "/ROOT", False, False, "123456"),
        ("123456", True, None, "check container content: %s", "/ROOT", True, False, "123456"),
        ("123456", True, None, None, "/ROOT", True, True, "123456"),
        (None, True, None, None, "/ROOT", True, True, "123456"),
    ], ids=[
        "container json not provided",
        "setup container fails",
        "setting up fails",
        "check container root fails",
        "success scenario",
        "success scenario, no container id"
    ])
def test_10_create_fromlayer(mocker, container_struct, logger, container_id, cntjson_exists, logmsg_error,
                             logmsg_warning, setup_cont, untar_status, chk_root_status, expected):
    """Test10 ContainerStructure().create_fromlayer()."""
    mocker.patch.object(container_struct.localrepo, 'setup_container', return_value=setup_cont)
    mocker.patch.object(container_struct.localrepo, 'save_json')
    mocker.patch.object(container_struct, '_untar_layers', return_value=untar_status)
    mocker.patch.object(container_struct, '_chk_container_root', return_value=chk_root_status)
    mocker.patch.object(os.path, 'basename', return_value="fake_basename")
    mocker.patch.object(Unique, 'uuid', return_value="123456")

    cont_json = {
        "architecture": "amd64",
        "author": "https://github.com/CentOS/sig-cloud-instance-images",
        "config": {
            "AttachStderr": False,
            "AttachStdin": False,
            "AttachStdout": False,
            "Cmd": [
                "/bin/bash"
            ],
            "Domainname": "",
            "Entrypoint": None,
            "Env": [
                "PATH=\
                /usr/local/sbin:\
                /usr/local/bin:/usr/sbin:\
                /usr/bin:/sbin:\
                /bin"
            ],
            "Hostname": "9aac06993d69",
            "Image": "sha256:4f64745dd34556af8f644a7886fcf" +
                     "cb11c059f64e1b0a753cb41188656ec8b33",
            "Labels": {
                "build-date": "20161102",
                "license": "GPLv2",
                "name": "CentOS Base Image",
                "vendor": "CentOS"
            },
            "OnBuild": None,
            "OpenStdin": False,
            "StdinOnce": False,
            "Tty": False,
            "User": "",
            "Volumes": None,
            "WorkingDir": ""
        },
    }
    cntjson = cont_json if cntjson_exists else None

    result = container_struct.create_fromlayer("dummy_repo", "dummy_tag", "dummy_layer_file", cntjson)

    assert result == expected
    if logmsg_error:
        assert mocker.call(logmsg_error) in logger.error.call_args_list or \
               mocker.call(logmsg_error, mocker.ANY) in logger.error.call_args_list

    if logmsg_warning:
        logger.warning.assert_called_with(logmsg_warning, mocker.ANY)


@pytest.mark.parametrize(
    "setup_container_return, logmsg_error, logmsg_warning, container_id, untar_status, chk_root_status, expected",
    [
        (None, "", "", "123456", False, False, False),
        ("/ROOT", "creating container clone: %s", "", "123456", False, False, "123456"),
        ("/ROOT", "", "", None, False, False, "1234"),
        ("/ROOT", "", "check container content: %s", "123456", True, False, "123456"),
        ("/ROOT", "", "", "123456", True, True, "123456"),
    ], ids=[
        "setup container fails",
        "untar layers fails",
        "no container_id provided",
        "check container root fails",
        "success scenario",
    ])
def test_11_clone_fromfile(mocker, container_struct, logger, container_id, setup_container_return, logmsg_error,
                           logmsg_warning, untar_status, chk_root_status, expected):
    """Test11 ContainerStructure().clone_fromfile()."""
    mocker.patch.object(container_struct.localrepo, 'setup_container', return_value=setup_container_return)
    mocker.patch.object(container_struct, '_untar_layers', return_value=untar_status)
    mocker.patch.object(container_struct, '_chk_container_root', return_value=chk_root_status)
    mocker.patch.object(os.path, 'basename', return_value="fake_basename")
    mocker.patch.object(Unique, 'uuid', return_value="1234")

    result = container_struct.clone_fromfile("dummy_clone_file")
    assert result == expected

    if logmsg_error:
        logger.error.assert_called_with(logmsg_error, mocker.ANY)

    if logmsg_warning:
        logger.warning.assert_called_with(logmsg_warning, mocker.ANY)


@pytest.mark.parametrize("verbose_level, logmsg, has_wildcards, tar_output, is_dir, list_dir, expected_calls", [
    (logging.DEBUG, "applying whiteouts: %s", True, "path/.wh.file\n", False, None, ["/tmp/path/file"]),
    (logging.DEBUG, "applying whiteouts: %s", True, None, False, None, []),
    (logging.NOTSET, None, True, "path/.wh..wh..opq\ninner/file", False, None, []),
    (logging.NOTSET, None, True, "path/.wh..wh..opq\ninner/file", True, [".wh.aa", ".wh.bb"],
     ['/tmp/path/.wh.aa', '/tmp/path/.wh.bb']),
    (logging.NOTSET, None, False, "path/.wh.file\n", False, None, ["/tmp/path/file"]),
])
def test_12__apply_whiteouts(mocker, container_struct, logger, verbose_level, logmsg, has_wildcards, is_dir, tar_output,
                             list_dir, expected_calls):
    """Test12 ContainerStructure()._apply_whiteouts()."""
    mocker.patch.object(Config, 'conf', {'verbose_level': verbose_level, 'tmpdir': "/tmp"})
    mocker.patch.object(HostInfo, 'cmd_has_option', return_value=has_wildcards)
    mocker.patch.object(Uprocess, 'get_output', return_value=tar_output)
    mocker.patch.object(os.path, 'isdir', return_value=is_dir)
    mocker.patch.object(os, 'listdir', return_value=list_dir)
    mock_remove = mocker.patch('udocker.container.structure.FileUtil')

    container_struct._apply_whiteouts("tarball", "/tmp")

    if verbose_level == logging.DEBUG:
        logger.debug.assert_called_with(logmsg, "tarball")
    actual_calls = [call.args[0] for call in mock_remove.call_args_list]
    assert actual_calls == expected_calls


@pytest.mark.parametrize("verbose_level, has_options, tarfiles, cmd_success, expected_status", [
    (logging.DEBUG, True, ["a.tar", "b.tar"], True, True),
    (logging.INFO, False, ["a.tar"], False, False),
    (logging.ERROR, True, [], True, False),
])
def test_13__untar_layers(mocker, container_struct, verbose_level, has_options, tarfiles, cmd_success, expected_status):
    """Test13 ContainerStructure()._untar_layers()."""
    mocker.patch.object(Config, 'conf', {'verbose_level': verbose_level})
    mocker.patch.object(HostInfo, 'cmd_has_option', return_value=has_options)
    mocker.patch.object(HostInfo, 'gid', return_value='1000')
    mocker.patch.object(subprocess, 'call', return_value=(0 if cmd_success else 1))
    mock_apply_whiteouts = mocker.patch.object(container_struct, '_apply_whiteouts')

    result = container_struct._untar_layers(tarfiles, '/dest/dir')

    assert result == expected_status
    if tarfiles:
        assert mock_apply_whiteouts.call_count == len(tarfiles)
    else:
        mock_apply_whiteouts.assert_not_called()


@pytest.mark.parametrize("container_exists, tar_status, log_error, expected", [
    (True, True, False, '123456'),
    (True, False, "export container as clone: %s", "123456"),
    (False, True, "container not found: %s", False),
    (False, False, "container not found: %s", False),
])
def test_14_export_tofile(mocker, container_struct, container_exists, tar_status, log_error, expected):
    """Test14 ContainerStructure().export_tofile()."""
    mocker.patch.object(container_struct, 'container_id', '123456')
    mocker.patch.object(container_struct.localrepo, 'cd_container',
                        return_value=(None if not container_exists else '/ROOT'))

    mocker.patch.object(FileUtil, 'tar', return_value=tar_status)

    result = container_struct.export_tofile('/path_to/clone_file.tar')

    assert result == expected


@pytest.mark.parametrize("container_exists, tar_status, log_error, expected", [
    (True, True, False, '123456'),
    (True, False, "export container as clone: %s", "123456"),
    (False, True, "container not found: %s", False),
    (False, False, "container not found: %s", False),
], ids=[
    "Success scenario",
    "Untar layers fails",
    "Container not found",
    "Container not found",
])
def test_15_clone_tofile(mocker, container_struct, logger, container_exists, tar_status, log_error, expected):
    """Test15 ContainerStructure().clone_tofile()."""
    mocker.patch.object(container_struct, 'container_id', '123456')
    mocker.patch.object(container_struct.localrepo, 'cd_container',
                        return_value=(None if not container_exists else '/ROOT'))
    mocker.patch.object(FileUtil, 'tar', return_value=tar_status)

    result = container_struct.clone_tofile('/path_to/clone_file.tar')

    assert result == expected
    logger.error.called_once_with(log_error, mocker.ANY) if log_error else logger.error.assert_not_called()


@pytest.mark.parametrize("source_exists,dest_setup,copydir,log_warning,log_error,root_check,expected", [
    (True, True, True, True, False, False, '123456'),
    (True, True, True, False, False, "check container content: %s", '123456'),
    (True, True, False, False, "creating container: %s", True, False),
    (True, False, True, False, "create destination container: setting up", True, False),
    (False, True, True, False, "source container not found: %s", True, False),
], ids=[
    "Success scenario",
    "Check container root fails",
    "Untar layers fails",
    "Setting up destination container fails",
    "Setting up source container fails",
])
def test_16_clone(mocker, container_struct, logger, source_exists, dest_setup, copydir, log_warning, log_error,
                  root_check, expected):
    """Test16 ContainerStructure().clone()."""
    mocker.patch.object(container_struct, 'container_id', 'source_container_id')
    mocker.patch.object(container_struct, 'imagerepo', 'imagerepo')
    mocker.patch.object(container_struct.localrepo, 'cd_container', return_value='/ROOT/src' if source_exists else None)
    mocker.patch.object(container_struct.localrepo, 'setup_container', return_value='/ROOT/dst' if dest_setup else None)
    mocker.patch.object(Unique, 'uuid', return_value='123456')
    mocker.patch.object(FileUtil, 'copydir', return_value=copydir)
    mocker.patch.object(container_struct, '_chk_container_root', return_value=root_check)

    result = container_struct.clone()

    assert result == expected
    logger.warning.called_once_with(log_warning, mocker.ANY) if log_warning else logger.warning.assert_not_called()
    logger.error.called_once_with(log_error, mocker.ANY) if log_error else logger.error.assert_not_called()
