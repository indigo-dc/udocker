#!/usr/bin/env python

# -*- coding: utf-8 -*-
"""
udocker unit tests: ContainerStructure
"""
import logging
import os
import random

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


# from unittest import TestCase, main
# from unittest.mock import patch, Mock

# from udocker.config import Config
# import collections
# collections.Callable = collections.abc.Callable
#
#
# class ContainerStructureTestCase(TestCase):
#     """Test ContainerStructure() class for containers structure."""
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
#         Config().conf['location'] = ""
#         Config().conf['oskernel'] = "4.8.13"
#
#         str_local = 'udocker.container.localrepo.LocalRepository'
#         self.lrepo = patch(str_local)
#         self.local = self.lrepo.start()
#         self.mock_lrepo = Mock()
#         self.local.return_value = self.mock_lrepo
#
#     def tearDown(self):
#         self.lrepo.stop()
#
def test_01_init(container_struct, lrepo, container_id):
    """Test01 ContainerStructure()."""
    assert container_struct.localrepo == lrepo
    assert container_struct.container_id == container_id
    assert container_struct.tag == ""
    assert container_struct.imagerepo == ""


#         prex = ContainerStructure(self.local)
#         self.assertEqual(prex.tag, "")
#         self.assertEqual(prex.imagerepo, "")
#         self.assertEqual(prex.localrepo, self.local)
#
#         prex = ContainerStructure(self.local, "123456")
#         self.assertEqual(prex.tag, "")
#         self.assertEqual(prex.imagerepo, "")
#         self.assertEqual(prex.container_id, "123456")
#

@pytest.mark.parametrize("location_set,cd_container_return,load_json_return,logmsg,expected", [
    ("/", None, None, False, ("", [])),
    ("", "/path/to/container", {"some": "data"}, False, ("/path/to/container", {"some": "data"})),
    ("", None, None, "container id or name not found", (False, False)),
    ("", "/path/to/container", None, "invalid container json metadata", (False, False)),
], ids=[
    "location is set in config",
    "Container directory found, valid JSON",
    "Container directory not found",
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


#         Config().conf['location'] = "/"
#         prex = ContainerStructure(self.local)
#         (container_dir, container_json) = prex.get_container_attr()
#         self.assertEqual(container_dir, "")
#         self.assertEqual(container_json, [])
#
#         Config().conf['location'] = ""
#         self.local.cd_container.return_value = ""
#         prex = ContainerStructure(self.local)
#         (container_dir, container_json) = prex.get_container_attr()
#         self.assertEqual(container_dir, False)
#         self.assertEqual(container_json, False)
#
#         Config().conf['location'] = ""
#         self.local.cd_container.return_value = "/"
#         self.local.load_json.return_value = []
#         prex = ContainerStructure(self.local)
#         (container_dir, container_json) = prex.get_container_attr()
#         self.assertEqual(container_dir, False)
#         self.assertEqual(container_json, False)
#
#         Config().conf['location'] = ""
#         self.local.cd_container.return_value = "/"
#         self.local.load_json.return_value = ["value", ]
#         prex = ContainerStructure(self.local)
#         (container_dir, container_json) = prex.get_container_attr()
#         self.assertEqual(container_dir, "/")
#         self.assertEqual(container_json, ["value", ])
#

@pytest.mark.parametrize("config,param,default,expected", [
    (False, "Cmd", "", "/bin/bash"),
    (True, "Cmd", "", "/bin/bash"),
    (True, "XXX", "", ""),
    (True, "Entrypoint", "BBB", "BBB"),
], ids=[
    "Cmd is present, config present",
    "Cmd is present, container_config is present",
    "Non-existent key 'XXX', default is empty string",
    "'Entrypoint' is None, default is 'BBB'",
])
def test_03_get_container_meta(container_struct, config, param, default, expected):
    """Test03 ContainerStructure().get_container_meta()."""
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

    container_json['container_config'] = container_json.pop('config') if not config else None
    result = container_struct._get_container_meta(param, default, container_json)
    assert result == expected


#         prex = ContainerStructure(self.local)
#         status = prex.get_container_meta("Cmd", "", container_json)
#         self.assertEqual(status, "/bin/bash")
#
#         prex = ContainerStructure(self.local)
#         status = prex.get_container_meta("XXX", "", container_json)
#         self.assertEqual(status, "")
#
#         prex = ContainerStructure(self.local)
#         status = prex.get_container_meta("Entrypoint", "BBB", container_json)
#         self.assertEqual(status, "BBB")
#
@pytest.mark.parametrize("input_dict,expected", [
    ({}, ""),  # Testing with an empty dictionary
    ({"A": "1"}, "A:1 "),  # Testing with a single key-value pair
    ({"A": "1", "B": "2"}, "A:1 B:2 "),  # Testing with multiple key-value pairs
    ({"A": 123, "B": [1, 2, 3]}, "A:123 B:[1, 2, 3] "),  # Testing with different data types as values
    ({"A": {"B": "1"}}, "A:{'B': '1'} "),
    # Testing with nested dictionary (considering it converts only the first layer)
], ids=[
    "Empty dictionary",
    "Single key-value pair",
    "Multiple key-value pairs",
    "Different data types as values",
    "Nested dictionary",
])
def test_04__dict_to_str(container_struct, input_dict, expected):
    """Test04 ContainerStructure()._dict_to_str()."""
    assert container_struct._dict_to_str(input_dict) == expected


#         prex = ContainerStructure(self.local)
#         status = prex._dict_to_str({'A': 1, 'B': 2})
#         self.assertTrue(status in ("A:1 B:2 ", "B:2 A:1 ", ))
#         self.assertEqual(status, "A:1 B:2 ")
#

@pytest.mark.parametrize("test_input,expected", [
    ({"A": 1, "B": "two"}, ["A:1", "B:two"]),
    ({}, []),
    ({"A": 123, "B": [1, 2, 3], "C": "value"}, ['A:123', 'B:[1, 2, 3]', 'C:value']),
    ({"A": {"B": "1"}}, ["A:{'B': '1'}"]),
])
def test_05__dict_to_list(container_struct, test_input, expected):
    """Test05 ContainerStructure()._dict_to_list()."""
    assert container_struct._dict_to_list(test_input) == expected


#         prex = ContainerStructure(self.local)
#         status = prex._dict_to_list({'A': 1, 'B': 2})
#         self.assertEqual(sorted(status), sorted(["A:1", "B:2"]))
#
# @patch('udocker.container.structure.os.path.exists')

@pytest.mark.parametrize("container_id,container_dir,expected,existing_paths", [
    (None, "/fake/container/dir", 5, ["/lib", "/bin", "/etc", "/tmp", "/var"]),
    (12345, "/fake/container/dir", 3, ["/usr", "/sys", "/dev"]),
    (12345, None, 0, ["/usr", "/sys", "/dev"]),
    (12345, "", 0, ["/usr", "/sys", "/dev"]),
    ("invalid_id", "/fake/container/dir", 0, []),
])
def test_06__chk_container_root(mocker, container_struct, container_id, container_dir, expected, existing_paths):
    """Test06 ContainerStructure()._chk_container_root()."""
    mocker.patch.object(container_struct.localrepo, "cd_container", return_value=container_dir)
    mocker.patch("os.path.exists",
                 side_effect=lambda path: any(path == container_dir + "/ROOT" + ep for ep in existing_paths))
    assert container_struct._chk_container_root(container_id) == expected


#         self.local.cd_container.return_value = ""
#         prex = ContainerStructure(self.local)
#         status = prex._chk_container_root("12345")
#         self.assertEqual(status, 0)
#
#         self.local.cd_container.return_value = "/ROOT"
#         mock_exists.side_effect = [True, True, False, True, True, False, False, False,
#                                    True, False, True, True, False]
#         prex = ContainerStructure(self.local)
#         status = prex._chk_container_root()
#         self.assertEqual(status, 7)
#
#     @patch.object(ContainerStructure, '_untar_layers')
#     @patch('udocker.container.structure.Unique.uuid')

@pytest.mark.parametrize(
    "container_id,image_dir,logmsg_error,logmsg_warn,img_attributes,setup_container,untar,chk_container,expected",
    [
        ("123456", False, "create container: imagerepo is invalid", "", (None, None), False, False, False, False),
        # Image repo invalid
        ("123456", True, "create container: getting layers or json", "", (None, None), False, False, False, False),
        # Getting layers or json fails
        ("123456", True, "create container: setting up container", "", (["value", "value"], ["value2", "layer2"]),
         False, False, False, False),
        # Setting up container fails
        ("123456", True, "creating container: %s", "", (["value", "value"], ["value2", "layer2"]), True, False, False,
         "123456"),
        # # Untar layers fails
        ("123456", True, "", "check container content: %s", (["value", "value"], ["value2", "layer2"]), True, True,
         False, "123456"),
        # _chk_container_root
        ("123456", True, "", "", (["value", "value"], ["value2", "layer2"]), True, True, False, "123456"),
        # Success scenario
        (None, True, "", "", (["value", "value"], ["value2", "layer2"]), True, True, False, "123456"),
        # Success scenario, no container id
    ])
def test_07_create_fromimage(mocker, container_struct, logger, image_dir, logmsg_error, logmsg_warn, img_attributes,
                             setup_container, untar, chk_container, expected):
    """Test07 ContainerStructure().create_fromimage()."""
    mocker.patch.object(container_struct.localrepo, 'cd_imagerepo', return_value="/" if image_dir else None)
    mocker.patch.object(container_struct.localrepo, 'get_image_attributes', return_value=img_attributes)
    mocker.patch.object(container_struct.localrepo, 'setup_container',
                        return_value="/ROOT" if setup_container else None)

    mocker.patch.object(container_struct.localrepo, 'save_json')
    mocker.patch.object(container_struct, '_untar_layers', return_value=untar)
    mocker.patch.object(container_struct, '_chk_container_root', return_value=chk_container)

    mocker.patch.object(os.path, 'basename', return_value="fake_basename")
    mocker.patch.object(Unique, 'uuid', return_value="123456")

    result = container_struct.create_fromimage("imagerepo", "tag")
    assert result == expected

    if logmsg_error:
        assert mocker.call(logmsg_error) in logger.error.call_args_list or \
               mocker.call(logmsg_error, mocker.ANY) in logger.error.call_args_list

    if logmsg_warn:
        logger.warning.assert_called_with(logmsg_warn, mocker.ANY)

    logger.reset_mock()


#         self.local.cd_imagerepo.return_value = ""
#         prex = ContainerStructure(self.local)
#         status = prex.create_fromimage("imagerepo", "tag")
#         self.assertFalse(status)
#
#         self.local.cd_imagerepo.return_value = "/"
#         self.local.get_image_attributes.return_value = ([], [])
#         prex = ContainerStructure(self.local)
#         status = prex.create_fromimage("imagerepo", "tag")
#         self.assertFalse(status)
#
#         self.local.cd_imagerepo.return_value = "/"
#         self.local.get_image_attributes.return_value = (["value", ], [])
#         self.local.setup_container.return_value = ""
#         prex = ContainerStructure(self.local)
#         status = prex.create_fromimage("imagerepo", "tag")
#         self.assertFalse(status)
#
#         self.local.cd_imagerepo.return_value = "/"
#         self.local.get_image_attributes.return_value = (["value", ], [])
#         self.local.setup_container.return_value = "/"
#         mock_untar.return_value = False
#         mock_uuid.return_value = "123456"
#         prex = ContainerStructure(self.local)
#         status = prex.create_fromimage("imagerepo", "tag")
#         self.assertEqual(status, "123456")
#
#     @patch.object(ContainerStructure, '_chk_container_root')
#     @patch.object(ContainerStructure, '_untar_layers')
#     @patch('udocker.container.structure.Unique.uuid')

@pytest.mark.parametrize(
    "container_id, cntjson_exists, logmsg_error, logmsg_warning, setup_container_return, untar_status, chk_root_status, expected_result",
    [
        ("123456", False, "create container: getting json", None, None, False, False, False),  # JSON not provided
        ("123456", True, "create container: setting up", None, None, False, False, False),  # setup container fails
        ("123456", True, "creating container: %s", None, "/ROOT", False, False, "123456"),  # setting up fails
        ("123456", True, None, "check container content: %s", "/ROOT", True, False, "123456"),
        # Check container root fails
        ("123456", True, None, None, "/ROOT", True, True, "123456"),  # Success scenario
        (None, True, None, None, "/ROOT", True, True, "123456"),  # Success scenario, no container id
    ])
def test_08_create_fromlayer(mocker, container_struct, container_id, logger, logmsg_error, cntjson_exists,
                             setup_container_return,
                             untar_status, chk_root_status, expected_result, logmsg_warning):
    """Test08 ContainerStructure().create_fromlayer()."""
    mocker.patch.object(container_struct.localrepo, 'setup_container', return_value=setup_container_return)
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

    if logmsg_error:
        assert mocker.call(logmsg_error) in logger.error.call_args_list or \
               mocker.call(logmsg_error, mocker.ANY) in logger.error.call_args_list

    if logmsg_warning:
        logger.warning.assert_called_with(logmsg_warning, mocker.ANY)

    assert result == expected_result


#         # Empty container_json
#         cont_json = dict()
#         mock_uuid.return_value = "123456"
#         prex = ContainerStructure(self.local)
#         status = prex.create_fromlayer("imagerepo", "tag", "layer", cont_json)
#         self.assertFalse(status)
#
#         # Non-empty container_json, empty cont dir
#         cont_json = {
#             "architecture": "amd64",
#             "author": "https://github.com/CentOS/sig-cloud-instance-images",
#             "config": {
#                 "AttachStderr": False,
#                 "AttachStdin": False,
#                 "AttachStdout": False,
#                 "Cmd": [
#                     "/bin/bash"
#                 ],
#                 "Domainname": "",
#                 "Entrypoint": None,
#                 "Env": [
#                     "PATH=\
#                     /usr/local/sbin:\
#                     /usr/local/bin:/usr/sbin:\
#                     /usr/bin:/sbin:\
#                     /bin"
#                 ],
#                 "Hostname": "9aac06993d69",
#                 "Image": "sha256:4f64745dd34556af8f644a7886fcf" +
#                          "cb11c059f64e1b0a753cb41188656ec8b33",
#                 "Labels": {
#                     "build-date": "20161102",
#                     "license": "GPLv2",
#                     "name": "CentOS Base Image",
#                     "vendor": "CentOS"
#                 },
#                 "OnBuild": None,
#                 "OpenStdin": False,
#                 "StdinOnce": False,
#                 "Tty": False,
#                 "User": "",
#                 "Volumes": None,
#                 "WorkingDir": ""
#             },
#         }
#         mock_uuid.return_value = "123456"
#         self.local.setup_container.return_value = ""
#         prex = ContainerStructure(self.local)
#         status = prex.create_fromlayer("imagerepo", "tag", "layer", cont_json)
#         self.assertFalse(status)
#
#         # Non-empty container_json, non empty cont dir
#         mock_uuid.return_value = "123456"
#         self.local.setup_container.return_value = "/ROOT"
#         self.local.save_json.return_value = True
#         mock_untar.return_value = True
#         mock_chkcont.return_value = 3
#         prex = ContainerStructure(self.local)
#         status = prex.create_fromlayer("imagerepo", "tag", "layer", cont_json)
#         self.assertEqual(status, "123456")
#
#     @patch.object(ContainerStructure, '_chk_container_root')
#     @patch.object(ContainerStructure, '_untar_layers')
#     @patch('udocker.container.structure.Unique.uuid')
@pytest.mark.parametrize(
    "setup_container_return,logmsg_error,logmsg_warning,container_id,untar_status,chk_root_status,expected",
    [
        (None, "", "", "123456", False, False, False),  # Setup container fails
        ("/ROOT", "creating container clone: %s", "", "123456", False, False, "123456"),  # Untar layers fails
        ("/ROOT", "", "", None, False, False, "1234"),  # No container_id provided
        ("/ROOT", "", "check container content: %s", "123456", True, False, "123456"),  # Check container root fails
        ("/ROOT", "", "", "123456", True, True, "123456"),  # Success scenario
    ])
def test_09_clone_fromfile(mocker, container_struct, logger, container_id, setup_container_return, logmsg_error,
                           logmsg_warning, untar_status, chk_root_status, expected):
    """Test09 ContainerStructure().clone_fromfile()."""
    mocker.patch.object(container_struct.localrepo, 'setup_container', return_value=setup_container_return)
    mocker.patch.object(container_struct, '_untar_layers', return_value=untar_status)
    mocker.patch.object(container_struct, '_chk_container_root', return_value=chk_root_status)
    mocker.patch('os.path.basename', return_value="fake_basename")
    mocker.patch('udocker.container.structure.Unique.uuid', return_value="1234")

    result = container_struct.clone_fromfile("dummy_clone_file")
    assert result == expected

    if logmsg_error:
        logger.error.assert_called_with(logmsg_error, mocker.ANY)

    if logmsg_warning:
        logger.warning.assert_called_with(logmsg_warning, mocker.ANY)


#         # Empty container_dir
#         self.local.setup_container.return_value = ""
#         mock_uuid.return_value = "123456"
#         prex = ContainerStructure(self.local)
#         status = prex.clone_fromfile("clone_file")
#         self.assertFalse(status)
#
#         # Non-empty container_dir
#         self.local.setup_container.return_value = "/ROOT"
#         mock_uuid.return_value = "123456"
#         mock_untar.return_value = True
#         mock_chkcont.return_value = 3
#         prex = ContainerStructure(self.local)
#         status = prex.clone_fromfile("clone_file")
#         self.assertEqual(status, "123456")
#
#     @patch('udocker.container.structure.os.listdir')
#     @patch('udocker.container.structure.os.path.isdir')
#     @patch('udocker.container.structure.os.path.dirname')
#     @patch('udocker.container.structure.os.path.basename')
#     @patch('udocker.container.structure.Uprocess.get_output')
#     @patch('udocker.container.structure.HostInfo.cmd_has_option')
#     @patch('udocker.container.structure.FileUtil.remove')

@pytest.mark.parametrize("verbose_level, logmsg, has_wildcards, tar_output, is_dir, list_dir, expected_calls", [
    (logging.DEBUG, "applying whiteouts: %s", True, "path/.wh.file\n", False, None, ["/tmp/path/file"]),
    (logging.DEBUG, "applying whiteouts: %s", True, None, False, None, []),
    (logging.NOTSET, None, True, "path/.wh..wh..opq\ninner/file", False, None, []),
    (logging.NOTSET, None, True, "path/.wh..wh..opq\ninner/file", True, [".wh.aa", ".wh.bb"],
     ['/tmp/path/.wh.aa', '/tmp/path/.wh.bb']),
    (logging.NOTSET, None, False, "path/.wh.file\n", False, None, ["/tmp/path/file"]),
])
def test_10__apply_whiteouts(mocker, container_struct, logger, verbose_level, logmsg, has_wildcards, is_dir, tar_output,
                             list_dir, expected_calls):
    """Test10 ContainerStructure()._apply_whiteouts()."""
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


#         mock_hinfocmd.return_value = False
#         mock_uprocget.return_value = ""
#         prex = ContainerStructure(self.local)
#         prex._apply_whiteouts("tarball", "/tmp")
#         self.assertTrue(mock_hinfocmd.called)
#         self.assertTrue(mock_uprocget.called)
#
#         mock_hinfocmd.return_value = False
#         mock_uprocget.return_value = "/d1/.wh.aa\n/d1/.wh.bb\n"
#         mock_base.side_effect = [".wh.aa", ".wh.bb", ".wh.aa", ".wh.bb"]
#         mock_dir.side_effect = ["/d1", "/d2"]
#         mock_isdir.side_effect = [True, True]
#         mock_lsdir.side_effect = [".wh.aa", ".wh.bb"]
#         mock_furm.side_effect = [None, None]
#         prex = ContainerStructure(self.local)
#         prex._apply_whiteouts("tarball", "/tmp")
#         self.assertTrue(mock_hinfocmd.called)
#         self.assertTrue(mock_uprocget.called)
#         self.assertTrue(mock_base.called)
#         self.assertTrue(mock_dir.called)
#         self.assertTrue(mock_furm.called)
#
#     @patch('udocker.container.structure.HostInfo')
#     @patch('udocker.container.structure.subprocess.call')
#     @patch.object(ContainerStructure, '_apply_whiteouts')

@pytest.mark.parametrize("verbose_level, has_options, tarfiles, cmd_success, expected_status", [
    (logging.DEBUG, True, ["layer1.tar", "layer2.tar"], True, True),
    (logging.INFO, False, ["layer1.tar"], False, False),
    (logging.ERROR, True, [], True, False),
    # Add more scenarios as needed
])
def test_11__untar_layers(mocker, container_struct, verbose_level, has_options, tarfiles, cmd_success, expected_status):
    """Test11 ContainerStructure()._untar_layers()."""

    mocker.patch.object(Config, 'conf', {'verbose_level': verbose_level})
    mocker.patch('udocker.container.structure.HostInfo.cmd_has_option', return_value=has_options)
    mocker.patch('udocker.container.structure.HostInfo.gid', return_value='1000')
    mocker.patch('subprocess.call', return_value=(0 if cmd_success else 1))
    mock_apply_whiteouts = mocker.patch.object(container_struct, '_apply_whiteouts')

    # Test
    result = container_struct._untar_layers(tarfiles, '/dest/dir')

    # Assert
    assert result == expected_status
    if tarfiles:
        assert mock_apply_whiteouts.call_count == len(tarfiles)
    else:
        mock_apply_whiteouts.assert_not_called()


#         tarfiles = ["a.tar", "b.tar", ]
#         mock_hinfo.gid = "1000"
#         mock_hinfo.return_value.cmd_has_option.return_value = False
#         mock_appwhite.side_effect = [None, None]
#         mock_call.side_effect = [1, 1, 1, 1]
#         prex = ContainerStructure(self.local)
#         status = prex._untar_layers(tarfiles, "/tmp")
#         self.assertFalse(status)
#         self.assertTrue(mock_call.call_count, 2)
#         self.assertTrue(mock_appwhite.call_count, 2)
#
#         tarfiles = ["a.tar", "b.tar", ]
#         mock_hinfo.gid = "1000"
#         mock_hinfo.return_value.cmd_has_option.return_value = False
#         mock_appwhite.side_effect = [None, None]
#         mock_call.side_effect = [0, 0, 0, 0]
#         prex = ContainerStructure(self.local)
#         status = prex._untar_layers(tarfiles, "/tmp")
#         self.assertTrue(status)
#         self.assertTrue(mock_call.call_count, 2)
#         self.assertTrue(mock_appwhite.call_count, 2)
#
#     @patch('udocker.container.structure.FileUtil.tar')


@pytest.mark.parametrize("container_exists, tar_status, log_error, expected", [
    (True, True, False, '123456'),
    (True, False, "export container as clone: %s", "123456"),
    (False, True, "container not found: %s", False),
    (False, False, "container not found: %s", False),
])
def test_12_export_tofile(mocker, container_struct, container_exists, tar_status, log_error, expected):
    """Test12 ContainerStructure().export_tofile()."""
    mocker.patch.object(container_struct, 'container_id', '123456')
    mocker.patch.object(container_struct.localrepo, 'cd_container',
                        return_value=(None if not container_exists else '/ROOT'))

    mocker.patch.object(FileUtil, 'tar', return_value=tar_status)
    result = container_struct.export_tofile('/path/to/clone_file.tar')

    assert result == expected


#         # Empty container dir
#         self.local.cd_container.return_value = ""
#         mock_futar.return_value = False
#         prex = ContainerStructure(self.local)
#         status = prex.export_tofile("clone_file")
#         self.assertFalse(status)
#
#         # Non-empty container dir
#         self.local.cd_container.return_value = "/ROOT"
#         mock_futar.return_value = True
#         prex = ContainerStructure(self.local, "123456")
#         status = prex.export_tofile("clone_file")
#         self.assertEqual(status, "123456")
#
#     @patch('udocker.container.structure.FileUtil.tar')

@pytest.mark.parametrize("container_exists, tar_status, log_error, expected", [
    (True, True, False, '123456'),
    (True, False, "export container as clone: %s", "123456"),
    (False, True, "container not found: %s", False),
    (False, False, "container not found: %s", False),
])
def test_13_clone_tofile(mocker, container_struct, logger, container_exists, tar_status, log_error, expected):
    """Test13 ContainerStructure().clone_tofile()."""

    mocker.patch.object(container_struct, 'container_id', '123456')
    mocker.patch.object(container_struct.localrepo, 'cd_container',
                        return_value=(None if not container_exists else '/ROOT'))
    mocker.patch.object(FileUtil, 'tar', return_value=tar_status)

    result = container_struct.clone_tofile('/path/to/clone_file.tar')

    assert result == expected
    if log_error:
        logger.error.called_once_with(log_error, mocker.ANY)


#         # Empty container dir
#         self.local.cd_container.return_value = ""
#         mock_futar.return_value = False
#         prex = ContainerStructure(self.local)
#         status = prex.clone_tofile("clone_file")
#         self.assertFalse(status)
#
#         # Non-empty container dir
#         self.local.cd_container.return_value = "/ROOT"
#         mock_futar.return_value = True
#         prex = ContainerStructure(self.local, "123456")
#         status = prex.clone_tofile("clone_file")
#         self.assertEqual(status, "123456")
#
#     @patch.object(ContainerStructure, '_chk_container_root')
#     @patch('udocker.container.structure.FileUtil.copydir')
#     @patch('udocker.container.structure.Unique.uuid')

@pytest.mark.parametrize("source_exists,dest_setup,copydir,log_warning,log_error,root_check,expected", [
    (True, True, True, True, False, False, '123456'),
    (True, True, True, False, False, "check container content: %s", '123456'),
    (True, True, False, False, "creating container: %s", True, False),
    (True, False, True, False, "create destination container: setting up", True, False),
    (False, True, True, False, "source container not found: %s", True, False),
])
def test_14_clone(mocker, container_struct, logger, source_exists, dest_setup, copydir, log_warning, log_error,
                  root_check, expected):
    """Test14 ContainerStructure().clone()."""
    mocker.patch.object(container_struct, 'container_id', 'source_container_id')
    mocker.patch.object(container_struct, 'imagerepo', 'imagerepo')
    mocker.patch.object(container_struct.localrepo, 'cd_container', return_value='/ROOT/src' if source_exists else None)
    mocker.patch.object(container_struct.localrepo, 'setup_container', return_value='/ROOT/dst' if dest_setup else None)

    mocker.patch.object(Unique, 'uuid', return_value='123456')
    mocker.patch.object(FileUtil, 'copydir', return_value=copydir)
    mocker.patch.object(container_struct, '_chk_container_root', return_value=root_check)

    result = container_struct.clone()
    assert result == expected

    if log_warning:
        logger.warning.called_once_with(log_warning, mocker.ANY)

    if log_error:
        logger.error.called_once_with(log_error, mocker.ANY)

#         # Empty source container_dir
#         self.local.cd_container.return_value = ""
#         mock_uuid.return_value = "123456"
#         prex = ContainerStructure(self.local)
#         status = prex.clone()
#         self.assertFalse(status)
#
#         # Non-empty source container_dir
#         self.local.cd_container.return_value = "/ROOT/src"
#         self.local.setup_container.return_value = "/ROOT/dst"
#         mock_uuid.return_value = "123456"
#         mock_chkcont.return_value = 3
#         mock_fucpd.return_value = False
#         prex = ContainerStructure(self.local)
#         status = prex.clone()
#         self.assertFalse(status)
#
#         self.local.cd_container.return_value = "/ROOT/src"
#         self.local.setup_container.return_value = "/ROOT/dst"
#         mock_uuid.return_value = "123456"
#         mock_chkcont.return_value = False
#         mock_fucpd.return_value = True
#         prex = ContainerStructure(self.local)
#         status = prex.clone()
#         self.assertEqual(status, "123456")
#
#
# if __name__ == '__main__':
#     main()
