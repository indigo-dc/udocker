#!/usr/bin/env python
"""
udocker unit tests: LocalRepository
"""
import json
import os
import random

import pytest

from udocker.config import Config
from udocker.container.localrepo import LocalRepository
from udocker.helper.osinfo import OSInfo
from udocker.utils.chksum import ChkSUM
from udocker.utils.fileutil import FileUtil
from udocker.utils.uprocess import Uprocess

UDOCKER_TOPDIR = ["/home/u1/.udocker", ]
BUILTIN = "builtins"
BOPEN = BUILTIN + '.open'
CHARACTERS_64 = "a" * 64


@pytest.fixture
def container_id():
    return str(random.randint(1, 1000))


@pytest.fixture
def localrepo(mocker, topdir):
    mocker.patch.object(Config, 'conf', {
        'topdir': None,
        'bindir': "",
        'libdir': "",
        'reposdir': "",
        'layersdir': "",
        'containersdir': "",
        'homedir': "/home/u1",
        'installdir': "",
        'tmpdir': ""
    })
    localrepo = LocalRepository(topdir)
    return localrepo


@pytest.fixture
def logger(mocker):
    mock_log = mocker.patch('udocker.container.localrepo.LOG')
    return mock_log


@pytest.fixture
def mock_fileutil(mocker):
    return mocker.patch('udocker.container.localrepo.FileUtil', autospec=True)


#
@pytest.mark.parametrize("topdir,conf,expected", [
    (UDOCKER_TOPDIR[0],
     {'topdir': None, 'bindir': "", 'libdir': "", 'reposdir': "", 'layersdir': "", 'containersdir': "",
      'homedir': "/home/u1", 'installdir': "", 'tmpdir': ""}, UDOCKER_TOPDIR[0]),
    ("", {'topdir': "", 'bindir': "", 'libdir': "", 'reposdir': "", 'layersdir': "", 'containersdir': "",
          'homedir': "/home/u1", 'installdir': "", 'tmpdir': ""}, ""),
])
def test_01_init(mocker, topdir, mock_fileutil, conf, expected):
    """Test01 LocalRepository() constructor."""
    mocker.patch.object(Config, 'conf', conf)
    localrepo = LocalRepository(topdir)
    assert localrepo.topdir == expected
    assert localrepo.installdir == ""
    assert localrepo.bindir == "" + "/bin"
    assert localrepo.libdir == "" + "/lib"
    assert localrepo.docdir == "" + "/doc"
    assert localrepo.tardir == "" + "/tar"
    assert localrepo.reposdir == topdir + "/repos"
    assert localrepo.layersdir == topdir + "/layers"
    assert localrepo.containersdir == topdir + "/containers"
    assert localrepo.homedir == "/home/u1"
    assert localrepo.cur_repodir == ""
    assert localrepo.cur_tagdir == ""
    assert localrepo.cur_containerdir == ""
    assert mock_fileutil.return_value.register_prefix.call_count == 3


@pytest.mark.parametrize("topdir,expected", [
    ("/home/u2/.udocker", "/home/u2/.udocker"),
])
def test_02_setup(mocker, localrepo, topdir, mock_fileutil, expected):
    """Test02 LocalRepository().setup()."""
    mocker.patch.object(Config, 'conf', {'topdir': None,
                                         'bindir': "",
                                         'libdir': "",
                                         'reposdir': "",
                                         'layersdir': "",
                                         'containersdir': "",
                                         'homedir': "/home/u1",
                                         'installdir': "",
                                         'tmpdir': ""})

    localrepo.setup(topdir)
    assert localrepo.topdir == expected
    assert localrepo.reposdir == topdir + "/repos"
    assert localrepo.layersdir == topdir + "/layers"
    assert localrepo.containersdir == topdir + "/containers"
    mock_fileutil.return_value.register_prefix.call_count == 3


@pytest.mark.parametrize(",os_exists,keystore,call_count,expected", [
    ([False] * 10, False, 10, True),
    (OSError, False, 0, False),
    ([False] * 10, True, 9, True),
    ([True] * 10, True, 0, True),
])
@pytest.mark.parametrize("topdir", UDOCKER_TOPDIR)
def test_03_create_repo(mocker, localrepo, topdir, os_exists, keystore, call_count, expected):
    """Test03 LocalRepository().create_repo()."""
    mocker.patch.object(os.path, 'exists', side_effect=os_exists)
    mock_makedirs = mocker.patch.object(os, 'makedirs')
    mocker.patch.dict(Config.conf, {'keystore': "/" if keystore else "some_keystore"})

    result = localrepo.create_repo()
    assert result == expected
    assert mock_makedirs.call_count == call_count


@pytest.mark.parametrize("dirs_exists,expected", [
    ([True] * 5, True),
    ([False, True, True, True, True], False),
    ([True, False, True, True, True], False),
    ([True, True, False, True, True], False),
    ([True, True, True, False, True], False),
    ([True, True, True, True, False], False),
    ([False] * 5, False),
])
@pytest.mark.parametrize("topdir", UDOCKER_TOPDIR)
def test_04_is_repo(mocker, localrepo, topdir, dirs_exists, expected):
    """Test04 LocalRepository().is_repo()."""
    mocker.patch.object(os.path, 'exists', side_effect=dirs_exists)

    result = localrepo.is_repo()
    assert result == expected


@pytest.mark.parametrize("container_id, expected", [
    (12345, False),
    (["d2578feb-acfc-37e0-8561-47335f85e46a"], False),
    ("d2578feb-acfc-37e0-8561-47335f85e46a", True),
    ("d2578feb-acfc-37e0-8561", False),
    ("d2578feb-ACFC-37e0-8561-47335f85e46a", False),
], ids=[
    "cont_id is int",
    "cont_id is list",
    "cont_id is valid",
    "cont_id is too short",
    "cont_id has uppercase",
])
@pytest.mark.parametrize("topdir", UDOCKER_TOPDIR)
def test_05_is_container_id(localrepo, container_id, expected):
    """Test05 LocalRepository().is_container_id()."""
    result = localrepo.is_container_id(container_id)
    assert result == expected


@pytest.mark.parametrize("protected,expected", [
    (True, True),
    (False, False)
])
@pytest.mark.parametrize("container_id", ("d2578feb-acfc-37e0-8561-47335f85e46a",))
@pytest.mark.parametrize("topdir", UDOCKER_TOPDIR)
def test_06_protect_container(mocker, localrepo, container_id, protected, expected):
    """Test06 LocalRepository().protect_container()."""
    mocker.patch.object(localrepo, '_protect', return_value=protected)
    mock_cd_container = mocker.patch.object(localrepo, 'cd_container', return_value="/home/u1/.udocker/containerid")

    result = localrepo.protect_container(container_id)

    assert result == expected
    mock_cd_container.assert_called_once_with(container_id)


@pytest.mark.parametrize("unprotect,expected", [
    (True, True),
    (False, False)
])
@pytest.mark.parametrize("container_id", ("d2578feb-acfc-37e0-8561-47335f85e46a",))
@pytest.mark.parametrize("topdir", UDOCKER_TOPDIR)
def test_07_unprotect_container(mocker, localrepo, container_id, unprotect, expected):
    """Test07 LocalRepository().unprotect_container()."""
    mocker.patch.object(localrepo, '_unprotect', return_value=unprotect)
    mock_cd_container = mocker.patch.object(localrepo, 'cd_container', return_value="/home/u1/.udocker/containerid")

    result = localrepo.unprotect_container(container_id)

    assert result == expected
    mock_cd_container.assert_called_once_with(container_id)


@pytest.mark.parametrize("isprotected,expected", [
    (True, True),
    (False, False)
])
@pytest.mark.parametrize("container_id", ("d2578feb-acfc-37e0-8561-47335f85e46a",))
@pytest.mark.parametrize("topdir", UDOCKER_TOPDIR)
def test_08_isprotected_container(mocker, localrepo, container_id, isprotected, expected):
    """Test08 LocalRepository().isprotected_container()."""
    mocker.patch.object(localrepo, '_isprotected', return_value=isprotected)
    mock_cd_container = mocker.patch.object(localrepo, 'cd_container', return_value="/home/u1/.udocker/containerid")

    result = localrepo.isprotected_container(container_id)

    assert result == expected
    mock_cd_container.assert_called_once_with(container_id)


@pytest.mark.parametrize("file_created, expected", [
    (True, True),
    (False, False)
])
@pytest.mark.parametrize("topdir", UDOCKER_TOPDIR)
def test_09__protect(mocker, localrepo, file_created, expected):
    """Test09 LocalRepository()._protect()."""
    directory = 'home/u1/.udocker/contid'

    if file_created:
        mock_open = mocker.mock_open()
        mocker.patch('builtins.open', mock_open)
    else:
        mocker.patch('builtins.open', side_effect=OSError())

    result = localrepo._protect(directory)

    assert result == expected

    if file_created:
        mock_open.assert_called_once_with(directory + "/PROTECT", 'w', encoding='utf-8')


@pytest.mark.parametrize("file_removal_outcome, expected", [
    (True, True),
    (False, False),
])
@pytest.mark.parametrize("topdir", UDOCKER_TOPDIR)
def test_10__unprotect(localrepo, mock_fileutil, file_removal_outcome, expected):
    """Test10 LocalRepository()._unprotect()."""
    directory = 'home/u1/.udocker/contid'
    mock_fileutil.return_value.remove.return_value = file_removal_outcome

    result = localrepo._unprotect(directory)

    assert result == expected
    mock_fileutil.assert_called_once_with(directory + "/PROTECT")
    mock_fileutil.return_value.remove.assert_called_once_with()


@pytest.mark.parametrize("protect_exists, expected", [
    (True, True),
    (False, False),
])
@pytest.mark.parametrize("topdir", UDOCKER_TOPDIR)
def test_11__isprotected(mocker, localrepo, protect_exists, expected):
    """Test11 LocalRepository()._isprotected()."""
    directory = 'home/u1/.udocker/contid'
    mocker.patch.object(os.path, 'exists', return_value=protect_exists, autospec=True)

    result = localrepo._isprotected(directory)

    assert result == expected
    os.path.exists.assert_called_once_with(directory + "/PROTECT")


@pytest.mark.parametrize("path_exists, is_dir, is_writable, expected", [
    # (False, False, False, 2),
    (True, False, False, 3),
    (True, True, True, 1),
    (True, True, False, 0),
])
@pytest.mark.parametrize("container_id", ("d2578feb-acfc-37e0-8561-47335f85e46a",))
@pytest.mark.parametrize("topdir", UDOCKER_TOPDIR)
def test_12_iswriteable_container(mocker, container_id, localrepo, path_exists, is_dir, is_writable, expected):
    """Test12 LocalRepository().iswriteable_container()."""
    container = "/home/u1/.udocker/containerid"
    container_root = container + "/ROOT"

    mocker.patch.object(localrepo, 'cd_container', return_value=container)
    mocker_ospath_exists = mocker.patch.object(os.path, 'exists', return_value=path_exists)
    mocker_osaccess = mocker.patch.object(os, 'access', return_value=is_writable)
    mocker_ospath_isdir = mocker.patch.object(FileUtil, 'isdir', return_value=is_dir)

    result = localrepo.iswriteable_container(container_id)

    assert result == expected

    if expected == 2:
        mocker_ospath_exists.assert_called_once_with(container_root)
    elif expected == 3:
        mocker_ospath_isdir.assert_called_once_with()
    elif expected == 1:
        mocker_osaccess.assert_called_once_with(container_root, mocker.ANY)


@pytest.mark.parametrize("du_output, expected_size", [
    ("1234\tdd", 1234),
    ("invalid_output", -1),
    ("", -1),
])
@pytest.mark.parametrize("container_id", ("d2578feb-acfc-37e0-8561-47335f85e46a",))
@pytest.mark.parametrize("topdir", UDOCKER_TOPDIR)
def test_13_get_size(container_id, du_output, expected_size, localrepo, mocker):
    """Test13 LocalRepository().get_size()."""
    container = "/home/u1/.udocker/containerid"
    container_root = container + "/ROOT"
    mocker.patch.object(localrepo, 'cd_container', return_value=container)
    mock_uprocess = mocker.patch.object(Uprocess, 'get_output', return_value=du_output)

    result = localrepo.get_size(container_id)

    assert result == expected_size
    mock_uprocess.assert_called_once_with(["du", "-s", "-m", "-x", container_root])


@pytest.mark.parametrize("isdir,listdir, file_contents,dir_only, container_name, expected", [
    (False, [], None, True, "container_name", []),
    (True, [], None, True, "container_name", []),
    (True, ['container1'], "some_repo_name", True, "container_name", ['/home/u1/.udocker/containers/container1']),
    (True, ['container1'], None, True, "container_name", ['/home/u1/.udocker/containers/container1']),
    (True, ['container1'], "some_repo_name", False, "container_name",
     [('container1', 'some_repo_name', 'container_name')]),
    (True, ['container1'], "some_repo_name", False, "",
     [('container1', 'some_repo_name', '')]),
    (True, ['a'], None, True, "container_name", ['/home/u1/.udocker/containers/a']),
    (True, ['a'], None, False, "container_name", [('a', '', 'container_name')]),
])
@pytest.mark.parametrize("topdir", UDOCKER_TOPDIR)
def test_14_get_containers_list(mocker, localrepo, container_id, isdir, listdir, file_contents, dir_only,
                                container_name, expected):
    """Test14 LocalRepository().get_containers_list()."""
    mocker.patch.object(os.path, 'isdir', return_value=isdir)
    mocker.patch.object(os, 'listdir', return_value=listdir)
    mocker.patch.object(os.path, 'islink', return_value=False)

    if file_contents is not None:
        mocker.patch('builtins.open', mocker.mock_open(read_data=file_contents))
    else:
        mocker.patch('builtins.open', side_effect=OSError)

    mocker.patch.object(localrepo, 'get_container_name', return_value=container_name)
    mocker.patch.object(localrepo, 'containersdir', '/home/u1/.udocker/containers')

    result = localrepo.get_containers_list(dir_only)
    assert result == expected


@pytest.mark.parametrize("container_dir, in_list, container_name, remove, force, expected", [
    (None, False, [], False, False, False),
    ("/home/u1/.udocker/containers", False, [], False, False, False),
    ("/home/u1/.udocker/containers", True, ["mycont"], False, False, False),
    ("/home/u1/.udocker/containers", True, ["mycont"], True, False, True),
    ("/home/u1/.udocker/containers", True, ["mycont"], True, True, True),
])
@pytest.mark.parametrize("topdir", UDOCKER_TOPDIR)
def test_15_del_container(mocker, localrepo, mock_fileutil, container_dir, topdir, container_id, in_list,
                          container_name, remove, force, expected):
    """Test15 LocalRepository().del_container()."""
    mocker.patch.object(localrepo, 'cd_container', return_value=container_dir)
    mocker.patch.object(localrepo, 'get_containers_list', return_value=[container_dir] if in_list else [])
    mocker.patch.object(localrepo, 'get_container_name', return_value=container_name)
    mocker.patch.object(localrepo, 'del_container_name')

    mock_fileutil.return_value.remove.return_value = remove

    result = localrepo.del_container(container_id, force=force)
    assert result == expected


@pytest.mark.parametrize("os_exists,container_list,expected", [
    (False, [], ""),
    (True, [], ""),
    (True, ["/home/u1/.udocker/containers/d2578feb-acfc-37e0-8561-47335f85e46a"],
     "/home/u1/.udocker/containers/d2578feb-acfc-37e0-8561-47335f85e46a"),
    (True, ["/home/u1/.udocker/containers/random_id"], ""),
])
@pytest.mark.parametrize("container_id", ("d2578feb-acfc-37e0-8561-47335f85e46a",))
@pytest.mark.parametrize("topdir", UDOCKER_TOPDIR)
def test_16_cd_container(mocker, localrepo, topdir, container_id, os_exists, container_list, expected):
    """Test16 LocalRepository().cd_container()."""
    mocker.patch.object(os.path, 'exists', return_value=os_exists)
    mocker.patch.object(localrepo, 'get_containers_list', return_value=container_list)

    result = localrepo.cd_container(container_id)
    assert result == expected


@pytest.mark.parametrize("os_exists, symlink_success, log_debug, expected", [
    (True, False, [], False),
    (False, True, ['set name through link: %s', 'container name set OK'], True),
    (False, False, ['set name through link: %s'], False),
])
@pytest.mark.parametrize("container_id", ("d2578feb-acfc-37e0-8561-47335f85e46a",))
@pytest.mark.parametrize("topdir", UDOCKER_TOPDIR)
def test_17__symlink(mocker, localrepo, logger, container_id, os_exists, symlink_success, log_debug, expected):
    """Test17 LocalRepository()._symlink()."""
    mocker.patch.object(os.path, 'exists', return_value=os_exists)
    mock_os_symlink = mocker.patch.object(os, 'symlink')
    if not symlink_success:
        mock_os_symlink.side_effect = OSError

    result = localrepo._symlink("EXISTINGFILE", "LINKFILE")
    assert result == expected

    logged_messages = [call_args[0][0] for call_args in logger.debug.call_args_list]
    assert logged_messages == log_debug


@pytest.mark.parametrize("container_name, expected", [
    ("lzskjghdlak", True),
    ("lzskjghd/lak", False),
    (".lzsklak", False),
    ("lzs klak", False),
    ("lzsklak ", False),
    ("]lzsklak", False),
    ("lzs[klak", False),
    ("a" * 2049, False),
    ("a" * 2048, True)
])
@pytest.mark.parametrize("topdir", UDOCKER_TOPDIR)
def test_18__name_is_valid(localrepo, topdir, container_id, container_name, expected):
    """Test18 LocalRepository()._name_is_valid().
    Check name alias validity.
    """
    result = localrepo._name_is_valid(container_name)
    assert result == expected


@pytest.mark.parametrize("container_name, is_valid, exists, calls, log_info, expected", [
    ("WRONG[/", False, False, {'cd_container': 0, 'os_exists': 0, '_symlink': 0}, 0, False),
    ("RIGHT", True, False, {'cd_container': 1, 'os_exists': 1, '_symlink': 1}, 1, True),
    ("RIGHT", True, True, {'cd_container': 1, 'os_exists': 1, '_symlink': 0}, 0, False),
    ("RIGHT", True, False, {'cd_container': 1, 'os_exists': 1, '_symlink': 1}, 1, True),
])
@pytest.mark.parametrize("container_id", ("d2578feb-acfc-37e0-8561-47335f85e46a",))
@pytest.mark.parametrize("topdir", UDOCKER_TOPDIR)
def test_18_set_container_name(mocker, localrepo, logger, container_name, container_id, is_valid, calls, exists,
                               log_info, expected):
    """Test18 LocalRepository().set_container_name()."""
    mocker.patch.object(localrepo, '_name_is_valid', return_value=is_valid)
    mocker.patch.object(localrepo, 'cd_container',
                        return_value="/home/u1/.udocker/containers" if container_name == "RIGHT" else "")
    mocker_os_exists = mocker.patch.object(os.path, 'exists', return_value=exists)
    mocker.patch.object(localrepo, '_symlink', return_value=not exists)

    result = localrepo.set_container_name(container_id, container_name)

    assert result == expected
    assert localrepo.cd_container.call_count == calls['cd_container']
    assert mocker_os_exists.call_count == calls['os_exists']
    assert localrepo._symlink.call_count == calls['_symlink']
    assert logger.info.call_count == log_info
    logger.info.called_once_with('set name through link: %s', container_name)


@pytest.mark.parametrize("contname, is_valid, is_link, file_remove, expected", [
    ("invalid/name", False, False, False, False),
    ("validname", True, False, False, False),
    ("validname", True, True, False, False),
    ("validname", True, True, True, True),
])
@pytest.mark.parametrize("container_id", ("d2578feb-acfc-37e0-8561-47335f85e46a",))
@pytest.mark.parametrize("topdir", UDOCKER_TOPDIR)
def test_19_del_container_name(mocker, localrepo, container_id, mock_fileutil, contname, is_valid, is_link, file_remove,
                               expected):
    """Test19 LocalRepository().del_container_name()."""
    mocker.patch.object(localrepo, '_name_is_valid', return_value=is_valid)
    mocker.patch.object(os.path, 'islink', return_value=is_link)
    mock_fileutil.return_value.remove.return_value = file_remove

    result = localrepo.del_container_name(container_id)
    assert result == expected
    if is_link:
        assert mock_fileutil.return_value.remove.call_count == 1


@pytest.mark.parametrize("contname, is_link, is_dir, readlink, expected", [
    (None, False, False, [""], ""),
    ("", False, False, [""], ""),
    ("ALIASNAM", False, False, [""], ""),
    ("ALIASNAM", True, False, ["BASENAME"], "BASENAME"),
    ("ALIASNAM", False, True, [""], "ALIASNAM"),
    ("ALIASNAM", True, False, ["", ""], ""),
])
@pytest.mark.parametrize("topdir", UDOCKER_TOPDIR)
def test_20_get_container_id(mocker, localrepo, container_id, contname, is_link, is_dir, readlink, expected):
    """Test20 LocalRepository().get_container_id()."""
    mocker.patch.object(os.path, 'islink', return_value=is_link)
    mocker.patch.object(os.path, 'isdir', return_value=is_dir)
    mocker.patch.object(os, 'readlink', side_effect=readlink)

    result = localrepo.get_container_id(contname)
    assert result == expected
    assert os.readlink.call_count == 1 if is_link else os.readlink.call_count == 0


@pytest.mark.parametrize("dir_exists, list_dir, link_targets, expected", [
    (False, [], [], []),
    (True, [], [], []),
    (True, ["FILE1", "FILE2"], [], []),
    (True, ["LINK1", "LINK2"], ["other_id", "another_id"], []),
    (True, ["LINK1", "LINK2", "LINK3"], ["LINK1", "LINK2", "yet_another_id"], ["LINK1", "LINK2"]),
])
@pytest.mark.parametrize("container_id", ("d2578feb-acfc-37e0-8561-47335f85e46a",))
@pytest.mark.parametrize("topdir", UDOCKER_TOPDIR)
def test_21_get_container_name(mocker, localrepo, container_id, dir_exists, list_dir, link_targets, expected):
    """Test21 LocalRepository().get_container_name()."""
    mocker.patch.object(os.path, 'isdir', return_value=dir_exists)
    mocker.patch.object(os, 'listdir', return_value=list_dir)
    mocker.patch.object(os.path, 'islink', side_effect=[item in link_targets for item in list_dir])
    full_link_targets = [f"/home/u1/.udocker/{container_id}" if item in link_targets else None for item in list_dir]
    mocker.patch.object(os, 'readlink', side_effect=full_link_targets)
    result = localrepo.get_container_name(container_id)
    assert result == expected


@pytest.mark.parametrize("os_path_exists, os_makedirs_success, expected", [
    (True, True, ""),
    (False, False, None),
    (False, True, "/home/u1/.udocker/d2578feb-acfc-37e0-8561-47335f85e46a"),  # Scenario 3
])
@pytest.mark.parametrize("container_id", ("d2578feb-acfc-37e0-8561-47335f85e46a",))
@pytest.mark.parametrize("topdir", UDOCKER_TOPDIR)
def test_22_setup_container(mocker, localrepo, container_id, os_path_exists, os_makedirs_success, expected):
    """Test22 LocalRepository().setup_container()."""
    container_dir = "/home/u1/.udocker/" + container_id
    mocker.patch.object(localrepo, 'containersdir', '/home/u1/.udocker')

    mocker.patch.object(os.path, 'exists', return_value=os_path_exists)
    mocker.patch.object(os, 'makedirs') if os_makedirs_success else mocker.patch('os.makedirs', side_effect=OSError)
    mock_open = mocker.patch('builtins.open', mocker.mock_open())

    result = localrepo.setup_container("imagerepo", "tag", container_id)
    assert result == expected

    if os_makedirs_success and not os_path_exists:
        mock_open.assert_called_once_with(container_dir + "/imagerepo.name", 'w', encoding='utf-8')


@pytest.mark.parametrize("tag_file_exists, expected", [
    ([True], True),
    ([False], False),
    ([OSError], False),
])
@pytest.mark.parametrize("container_id", ("d2578feb-acfc-37e0-8561-47335f85e46a",))
@pytest.mark.parametrize("topdir", UDOCKER_TOPDIR)
def test_23__is_tag(mocker, localrepo, container_id, tag_file_exists, expected):
    """Test23 LocalRepository()._is_tag()."""
    tag_dir = "/home/u1/.udocker/" + container_id
    mocker.patch.object(os.path, 'isfile', side_effect=tag_file_exists)
    result = localrepo._is_tag(tag_dir)
    assert result == expected


@pytest.mark.parametrize("protect, expected", [
    (True, True),
    (False, False),
])
@pytest.mark.parametrize("topdir", UDOCKER_TOPDIR)
def test_24_protect_imagerepo(mocker, localrepo, protect, expected):
    """Test24 LocalRepository().protect_imagerepo()."""
    mocker.patch.object(localrepo, '_protect', return_value=protect)
    imagerepo = "IMAGE/TAG/PROTECT"
    tag = "latest"
    result = localrepo.protect_imagerepo(imagerepo, tag)
    assert result == expected


@pytest.mark.parametrize("unprotect, expected", [
    (True, True),
    (False, False),
])
@pytest.mark.parametrize("topdir", UDOCKER_TOPDIR)
def test_25_unprotect_imagerepo(mocker, localrepo, unprotect, expected):
    """Test25 LocalRepository().unprotected_imagerepo()."""
    mocker.patch.object(localrepo, '_unprotect', return_value=unprotect)
    imagerepo = "IMAGE/TAG/SOMEDIR"
    tag = "latest"
    result = localrepo.unprotect_imagerepo(imagerepo, tag)
    assert result == expected


@pytest.mark.parametrize("tag_protection, expected", [
    (True, True),
    (False, False),
])
@pytest.mark.parametrize("topdir", UDOCKER_TOPDIR)
def test_26_isprotected_imagerepo(mocker, localrepo, tag_protection, expected):
    """Test26 LocalRepository().isprotected_imagerepo()."""
    mocker.patch.object(localrepo, '_isprotected', return_value=tag_protection)
    imagerepo = "/IMAGE/TAG/PROTECT"
    tag = "latest"
    result = localrepo.isprotected_imagerepo(imagerepo, tag)
    assert result == expected


@pytest.mark.parametrize("imagerepo, tag, path_exists, is_tag, expected", [
    ("sample_repo", "latest", True, True, "/home/u2/.udocker/repos/sample_repo/latest"),
    ("sample_repo", "latest", False, True, ""),
    ("sample_repo", "latest", True, False, ""),
    (None, "latest", True, True, ""),
    ("sample_repo", None, True, True, ""),
])
@pytest.mark.parametrize("topdir", UDOCKER_TOPDIR)
def test_27_cd_imagerepo(mocker, localrepo, imagerepo, tag, path_exists, is_tag, expected):
    """Test27 LocalRepository().cd_imagerepo()."""
    mocker.patch.object(localrepo, 'reposdir', '/home/u2/.udocker/repos')
    mocker.patch.object(os.path, 'exists', return_value=path_exists)
    mocker.patch.object(localrepo, '_is_tag', return_value=is_tag)
    result = localrepo.cd_imagerepo(imagerepo, tag)
    assert result == expected


@pytest.mark.parametrize("cd_imagerepo, new_exists, setup_new_repo, setup_new_tag, file_structure, copyto, expected", [
    ([None, None], False, True, True, {}, False, None),
    ([None, "XXXX"], False, False, True, {}, False, None),
    (["XXX", ""], False, True, False, {}, False, False),
    (["XXX", None, "XXX"], False, True, True, {}, False, True),
    (["XXX", "XXXX"], True, True, True, {}, False, None),
    (["XXX", None, None], False, True, True, {}, True, False),
    (["XXX", None, "XXX"], False, True, True, {"file1": "file", "file2": "symlink", "TAG": "special"}, True, True),
    (["XXX", None, "XXX"], False, True, True, {"file1": "file", "file2": "file", "TAG": "special"}, False, False),
    (["XXX", None, "XXX"], False, True, True, {"file1": "symlink", "file2": "symlink", "TAG": "special"}, True, False),
    (["XXX", None, "XXX"], False, True, True, {"file1": "file", "TAG": "special"}, True, True),
], ids=[
    "Source tag directory missing",
    "New repo exists with correct source structure",
    "Setup of new repo/tag fails",
    "New tag creation in existing repo succeeds",
    "New repo/tag already exist",
    "New tag definition fails, setup ambiguous",
    "Successful copy/link of files and symlinks",
    "Failure when copying files",
    "Fail to add image layer for symlinks",
    "TAG file in source ignored",
])
@pytest.mark.parametrize("topdir", UDOCKER_TOPDIR)
def test_28_tag(mocker, localrepo, cd_imagerepo, new_exists, setup_new_repo,
                setup_new_tag, file_structure, copyto, expected):
    """Test LocalRepository.tag() method."""
    mocker.patch.object(localrepo, 'setup_imagerepo', return_value=setup_new_repo)
    mocker.patch.object(localrepo, 'setup_tag', return_value=setup_new_tag)
    mocker.patch.object(localrepo, 'cd_imagerepo', side_effect=cd_imagerepo)
    mocker.patch.object(os.path, 'isdir', return_value=new_exists)
    mocker.patch.object(os, 'listdir', return_value=list(file_structure.keys()))
    mocker.patch.object(os.path, 'islink', side_effect=lambda x: file_structure.get(os.path.basename(x)) == 'symlink')
    mocker.patch.object(os.path, 'isfile', side_effect=lambda x: file_structure.get(os.path.basename(x)) == 'file')
    mocker.patch.object(os.path, 'realpath',
                        side_effect=lambda x: f"/real/path/{os.path.basename(x)}" if file_structure.get(
                            os.path.basename(x)) == 'symlink' else x)
    mocker.patch.object(FileUtil, 'copyto', return_value=copyto)
    mocker.patch.object(localrepo, 'add_image_layer', side_effect=lambda filename: not filename.endswith('file1'))

    result = localrepo.tag("src_repo", "src_tag", "new_repo", "new_tag")
    assert result == expected


@pytest.mark.parametrize("listdir_map, isdir, islink, filename, expected", [
    ({'/dir': []}, [False, False], [False], 'test.layer', []),
    ({'/dir': []}, [True, False], [False], 'test.layer', []),
    ({'/dir': ['file1.txt', 'file2.txt']}, [True, False, False], [False, False, False], 'test.layer', []),
    ({'/dir': ['other.link', 'random.link']}, [True, False, False], [True, True, True], 'test.layer', []),
    ({'/dir': ['test.layer']}, [True, False], [True, True], 'test.layer', ['/dir/test.layer']),
    ({'/dir': ['subdir', 'test.layer'], '/dir/subdir': []}, [True, True, False], [True, True, True], 'test.layer',
     ['/dir/test.layer']),
    ({'/dir': ['subdir1', 'subdir2'], '/dir/subdir1': ['test.layer'], '/dir/subdir2': ['other.layer', 'test.layer']},
     [True, True, True, False, False], [True, True, True], 'test.layer', []),
])
@pytest.mark.parametrize("topdir", UDOCKER_TOPDIR)
def test_29__find(mocker, localrepo, listdir_map, isdir, islink, filename, expected):
    """Test29 LocalRepository()._find()."""
    # FIXME: miss the recursive call to _find
    mocker.patch.object(os, 'listdir', side_effect=lambda x: listdir_map.get(x, []))
    mocker.patch.object(os.path, 'isdir', side_effect=isdir)
    mocker.patch.object(os.path, 'islink', side_effect=islink)

    result = sorted(localrepo._find(filename, '/dir'))
    expected_sorted = sorted(expected)
    assert result == expected_sorted


@pytest.mark.parametrize("filename,expected", [
    ('existing_file.layer', True),
    ('nonexistent_file.layer', False)
])
@pytest.mark.parametrize("topdir", UDOCKER_TOPDIR)
def test_30__inrepository(mocker, localrepo, filename, expected):
    """Test30 LocalRepository()._inrepository()."""
    find_result = [filename] if expected else []
    mocker.patch.object(localrepo, '_find', return_value=find_result)
    result = (localrepo._inrepository(filename) != [])
    assert result == expected


@pytest.mark.parametrize("links_in_dir, remove_link, remove_layer, force, calls, expected", [
    (['FILE1', 'FILE2'], True, True, False, {'_inrepository': 2}, True),
    (['FILE1', 'FILE2'], False, True, False, {'_inrepository': 0}, False),
    (['FILE1', 'FILE2'], True, False, False, {'_inrepository': 1}, False),
    (['FILE1', 'FILE2'], False, False, True, {'_inrepository': 2}, True)
])
@pytest.mark.parametrize("topdir", UDOCKER_TOPDIR)
def test_31__remove_layers(mocker, localrepo, links_in_dir, remove_link, remove_layer, force, calls, expected):
    """Test31 LocalRepository()._remove_layers()."""
    tag_dir = 'TAG_DIR'
    mocker.patch.object(os, 'listdir', return_value=links_in_dir)
    mocker.patch.object(os.path, 'islink', return_value=True)
    mocker.patch.object(os, 'readlink', side_effect=lambda x: x + '_link')
    mocker.patch.object(FileUtil, 'remove', side_effect=[remove_link, remove_layer] * len(links_in_dir))
    mocker.patch.object(localrepo, '_inrepository', return_value=False)

    result = localrepo._remove_layers(tag_dir, force)
    assert result == expected
    assert localrepo._inrepository.call_count == calls['_inrepository']


@pytest.mark.parametrize("exist_repo, remove_layers, remove_tag_dir, expected", [
    (True, True, True, True),
    (False, True, True, False),
    (True, False, True, False),
    (True, True, False, False),
])
@pytest.mark.parametrize("topdir", UDOCKER_TOPDIR)
def test_32_del_imagerepo(mocker, localrepo, exist_repo, remove_layers, remove_tag_dir, expected):
    """Test32 LocalRepository()._del_imagerepo()."""
    mocker.patch.object(localrepo, 'cd_imagerepo', return_value='reposdir/imagerepo/tag' if exist_repo else "")
    mocker.patch.object(localrepo, '_remove_layers', return_value=remove_layers)
    mocker.patch.object(FileUtil, 'remove', return_value=remove_tag_dir)
    mocker.patch.object(FileUtil, 'rmdir')
    result = localrepo.del_imagerepo("IMAGE", "TAG")
    assert result == expected


@pytest.mark.parametrize("directories, is_tag, is_dir, call_count, expected", [
    (['/repo/tag1', '/repo/tag2'], [True, True], [False, False], 1,
     [('CONTAINERS_DIR', 'tag1'), ('CONTAINERS_DIR', 'tag2')]),
    (['/repo/dir1/tag1', '/repo/dir2/tag2'], [True, True, True, True], [True, False, True, False], 1,
     [('CONTAINERS_DIR', 'tag1'), ('CONTAINERS_DIR', 'tag2')]),
    (['/repo/tag1', '/repo/dir1/tag2'], [True, False, True], [False, True, False], 1, [('CONTAINERS_DIR', 'tag1')]),
    (['/repo/dir'], [False], [True], 2, []),
    (['/repo/dir1', '/repo/dir2'], [False, False], [True, True], 3, [])
])
@pytest.mark.parametrize("topdir", UDOCKER_TOPDIR)
def test_32__get_tags(mocker, localrepo, mock_fileutil, directories, is_tag, is_dir, call_count, expected):
    """Test32 LocalRepository()._get_tags()."""
    tag_dir = 'CONTAINERS_DIR'
    mocker.patch.object(os, 'listdir', return_value=[d.split('/')[-1] for d in directories])
    mocker.patch.object(os.path, 'isdir', side_effect=is_dir)
    mocker.patch.object(mock_fileutil, 'isdir', side_effect=lambda x: x in directories)
    mocker.patch.object(localrepo, '_is_tag', side_effect=is_tag)
    original_get_tags = localrepo._get_tags
    recursive_mock = mocker.patch.object(localrepo, '_get_tags',
                                         side_effect=lambda path: original_get_tags(path) if path == tag_dir else [])
    result = localrepo._get_tags(tag_dir)
    assert result == expected
    assert recursive_mock.call_count == call_count


@pytest.mark.parametrize("get_tags", [
    ([]),
    ([('repo1', 'tag1'), ('repo1', 'tag2')]),
    ([('repo1', 'tag1'), ('repo2', 'tag1'), ('repo2', 'tag2')]),
])
@pytest.mark.parametrize("topdir", UDOCKER_TOPDIR)
def test_34_get_imagerepos(mocker, localrepo, get_tags):
    """Test34 LocalRepository().get_imagerepos()."""
    expected = get_tags
    mocker.patch.object(localrepo, '_get_tags', return_value=expected)
    result = localrepo.get_imagerepos()
    assert result == expected


@pytest.mark.parametrize("tag_dir, listdir_output, islink_output, size_output, expected_output", [
    (None, [], [], [], []),
    ("IMAGE/TAG/tag1", [], [], [], []),
    ("IMAGE/TAG/tag2", ["file1", "file2"], [True, False], ["123", None], [("IMAGE/TAG/tag2/file1", "123")]),
])
@pytest.mark.parametrize("topdir", UDOCKER_TOPDIR)
def test_35_get_layers(mocker, localrepo, mock_fileutil, tag_dir, listdir_output, islink_output, size_output,
                       expected_output):
    """Test35 LocalRepository().get_layers()."""
    mocker.patch.object(os, 'listdir', return_value=listdir_output)
    mocker.patch.object(os.path, 'islink', side_effect=islink_output)
    mocker.patch.object(localrepo, 'cd_imagerepo', return_value=tag_dir)
    mock_fileutil.return_value.size.side_effect = size_output

    result = localrepo.get_layers("IMAGE", "TAG")
    assert result == expected_output


@pytest.mark.parametrize("cur_tagdir, filename, linkname, file_exists, tagdir_exists, link_exists, expected", [
    (None, "FILE", None, [False], True, False, False),
    ("TAG", "FILE", None, [False], True, False, False),
    ("TAG", "FILE", None, [True, True], True, False, True),
    ("TAG", "FILE", "linkname", [True, True], True, False, True),
    ("TAG", "FILE", "linkname", [True, True], True, True, True),
])
@pytest.mark.parametrize("topdir", UDOCKER_TOPDIR)
def test_36_add_image_layer(mocker, mock_fileutil, localrepo, cur_tagdir, filename, linkname, file_exists,
                            tagdir_exists, link_exists, expected):
    """Test36 LocalRepository().add_image_layer()."""
    localrepo.cur_tagdir = cur_tagdir
    mocker.patch.object(os.path, 'exists', side_effect=file_exists)
    mocker.patch.object(os.path, 'islink', return_value=link_exists)
    mock_fileutil.return_value.remove.return_value = True
    mocker.patch.object(localrepo, '_symlink', return_value=None)
    result = localrepo.add_image_layer(filename, linkname)
    assert result == expected


@pytest.mark.parametrize("imagerepo, exists, raises_oserror, expected, expected_cur_repodir", [
    ("repo1", False, False, True, "/tmp/repo1"),
    ("repo2", True, False, False, "/tmp/repo2"),
    ("repo3", False, True, None, ''),
    (None, False, False, None, ''),
    ("", True, False, None, ''),
])
@pytest.mark.parametrize("topdir", UDOCKER_TOPDIR)
def test_37_setup_imagerepo(mocker, localrepo, imagerepo, exists, raises_oserror, expected,
                            expected_cur_repodir):
    """Test37 LocalRepository().setup_imagerepo()."""
    mocker.patch.object(localrepo, 'reposdir', '/tmp')
    mocker.patch.object(os.path, 'exists', return_value=exists)
    makedirs_mock = mocker.patch.object(os, 'makedirs', side_effect=OSError if raises_oserror else mocker.Mock())
    result = localrepo.setup_imagerepo(imagerepo)
    assert result == expected
    assert localrepo.cur_repodir == expected_cur_repodir

    if (imagerepo and not exists) or raises_oserror:
        makedirs_mock.assert_called_once_with("/tmp/" + imagerepo)
    else:
        makedirs_mock.assert_not_called()


@pytest.mark.parametrize("tag, exists, makedirs_error, open_error, expected_tag, expected", [
    ("NEWTAG1", False, None, None, "/tmp/IMAGE/NEWTAG1", True),
    ("NEWTAG2", True, None, None, "/tmp/IMAGE/NEWTAG2", True),
    ("NEWTAG3", True, None, OSError, "/tmp/IMAGE/NEWTAG3", False),
    ("NEWTAG4", False, OSError, None, "", False),
])
@pytest.mark.parametrize("topdir", UDOCKER_TOPDIR)
def test_38_setup_tag(mocker, localrepo, tag, exists, makedirs_error, open_error, expected_tag, expected):
    """Test38 LocalRepository().setup_tag()."""
    mocker.patch.object(localrepo, 'cur_repodir', "/tmp/IMAGE")
    mocker.patch.object(os.path, 'exists', return_value=exists)
    mocker.patch.object(os, 'makedirs', side_effect=makedirs_error)
    open_mock = mocker.mock_open()
    if open_error:
        open_mock.side_effect = open_error

    mocker.patch("builtins.open", open_mock)

    result = localrepo.setup_tag(tag)
    assert result == expected
    assert localrepo.cur_tagdir == expected_tag


@pytest.mark.parametrize(
    "cur_repodir, cur_tagdir, exists_side_effect, version, dir_contents, open_successful, error_remove, expected", [
        ("", "", [False, False, False, False], "v1", [], False, False, False),
        ("/tmp/repodir/IMAGE", "/tmp/repodir/IMAGE/TAG", [False, True, True, False, False], "v1", [], True, False,
         False),
        ("/tmp/repodir/IMAGE", "/tmp/repodir/IMAGE/TAG", [True, False, True, False, False], "v1", [], True, False,
         False),
        ("/tmp/repodir/IMAGE", "/tmp/repodir/IMAGE/TAG", [True, True, True, False, False], "v1", ["v1"], True, False,
         True),
        ("/tmp/repodir/IMAGE", "/tmp/repodir/IMAGE/TAG", [True, True, True, False, False], "v3", ["v3"], False, False,
         False),
        ("/tmp/repodir/IMAGE", "/tmp/repodir/IMAGE/TAG", [True, True, True, False, False], "v3", ["v3"], False, True,
         False),
        ("/tmp/repodir/IMAGE", "/tmp/repodir/IMAGE/TAG", [True, True, False, True, False], "v2", ["v2"], True, False,
         True),
        ("/tmp/repodir/IMAGE", "/tmp/repodir/IMAGE/TAG", [True, True, True, False, False], "v1", ["v1"], False, False,
         False),
    ])
@pytest.mark.parametrize("topdir", UDOCKER_TOPDIR)
def test_39_set_version(mocker, localrepo, cur_repodir, cur_tagdir, exists_side_effect, version, dir_contents,
                        open_successful, error_remove, expected):
    """Test39 LocalRepository().set_version()."""
    localrepo.cur_repodir = cur_repodir
    localrepo.cur_tagdir = cur_tagdir

    paths_to_check = [cur_repodir, cur_tagdir, os.path.join(cur_tagdir, "v1"), os.path.join(cur_tagdir, "v2")]
    mocker.patch.object(os.path, 'exists', side_effect=lambda x: exists_side_effect[
        paths_to_check.index(x)] if x in paths_to_check else False)
    mocker.patch.object(os, 'listdir', return_value=dir_contents)
    mocker.patch.object(FileUtil, "remove", side_effect=OSError if error_remove else [True, True])
    open_mock = mocker.mock_open()
    if not open_successful:
        open_mock.side_effect = OSError()
    mocker.patch("builtins.open", open_mock)

    result = localrepo.set_version(version)
    assert result == expected

    if expected and version in ["v1", "v2"]:
        open_mock.assert_called_with(os.path.join(cur_tagdir, version), 'a', encoding='utf-8')


@pytest.mark.parametrize("ancestry_exists,layer_exists,json_exists,expected", [
    (None, False, False, (None, None)),
    ([['layer1', 'layer2']], False, False, (None, None)),
    ([['layer1', 'layer2']], True, False, (None, None)),
    ([['layer1', 'layer2'], ['layer1', 'layer2']], True, True,
     (['layer1', 'layer2'], ['/udocker/test/directory/layer1.layer', '/udocker/test/directory/layer2.layer'])),
])
@pytest.mark.parametrize("topdir", UDOCKER_TOPDIR)
def test_40__get_image_attr_v1(mocker, localrepo, ancestry_exists, layer_exists, json_exists, expected):
    """Test40 LocalRepository()._get_image_attributes_v1()."""
    directory = '/udocker/test/directory'

    mocker.patch.object(localrepo, 'load_json', side_effect=ancestry_exists)
    mocker.patch.object(os.path, 'exists',
                        side_effect=lambda x: (layer_exists if x.endswith('.layer') else json_exists))
    mock_open = mocker.mock_open(read_data=json.dumps({"data": "json"}))
    mocker.patch('builtins.open', mock_open)

    container_json, files = localrepo._get_image_attributes_v1(directory)

    if expected != (None, None):
        assert (container_json, sorted(files)) == (expected[0], sorted(expected[1]))
    else:
        assert (container_json, files) == expected


@pytest.mark.parametrize("manifest_data, layer_file_exists, expected", [
    ({"fsLayers": [{"blobSum": "foolayername"}, {"blobSum": "foolayername2"}],
      "history": [{"v1Compatibility": '{"data":"json"}'}]},
     False, (None, None)),
    ({"fsLayers": [{"blobSum": "foolayername"}, {"blobSum": "foolayername2"}],
      "history": [{"v1Compatibility": '{"data":"json"}'}]},
     True, ({"data": "json"}, ['/udocker/test/directory/foolayername', '/udocker/test/directory/foolayername2'])),
    ({"fsLayers": [{"blobSum": "foolayername"}, {"blobSum": "foolayername2"}], "history": []}, True,
     (None, ['/udocker/test/directory/foolayername', '/udocker/test/directory/foolayername2'])),
])
@pytest.mark.parametrize("topdir", UDOCKER_TOPDIR)
def test_41__get_image_attr_v2_s1(mocker, localrepo, manifest_data, layer_file_exists, expected):
    """Test41 LocalRepository()._get_image_attributes_v2_s1()."""

    directory = '/udocker/test/directory'
    mocker.patch.object(os.path, 'exists', return_value=layer_file_exists)

    attributes = localrepo._get_image_attributes_v2_s1(directory, manifest_data)

    if attributes != (None, None):
        assert (attributes[0], sorted(attributes[1])) == (expected[0], sorted(expected[1]))
    else:
        assert attributes == expected


@pytest.mark.parametrize("manifest_data,layer_files_exist,config_file_data,raise_exception,expected", [
    ({"layers": [{"digest": "layer1"}, {"digest": "layer2"}], "config": {"digest": "config"}},
     True, ['{"data":"json"}'], None,
     ({"data": "json"}, ['/udocker/test/directory/layer1', '/udocker/test/directory/layer2'])),
    ({"layers": ({"digest": "foolayername"},), "config": ({"digest": '["foojsonstring"]'})},
     True, ['{"data":"json"}'], None, ({'data': 'json'}, ['/udocker/test/directory/foolayername'])),
    ({"layers": ({"digest": "foolayername"},), "config": ({"digest": '["foojsonstring"]'})},
     False, ['{"data":"json"}'], None, (None, None)),
    ({"layers": [{"digest": "layer1"}, {"digest": "layer2"}], "config": {"digest": "config"}},
     True, [None], OSError, (None, ['/udocker/test/directory/layer1', '/udocker/test/directory/layer2'])),
])
@pytest.mark.parametrize("topdir", UDOCKER_TOPDIR)
def test_42__get_image_attr_v2_s2(mocker, localrepo, manifest_data, layer_files_exist, config_file_data, expected,
                                  raise_exception):
    """Test42 LocalRepository()._get_image_attributes_v2_s2()."""
    directory = '/udocker/test/directory'
    mocker.patch.object(os.path, 'exists', return_value=layer_files_exist)
    mocker.patch.object(FileUtil, 'getdata', side_effect=config_file_data if not raise_exception else raise_exception)

    result = localrepo._get_image_attributes_v2_s2(directory, manifest_data)
    assert result == expected


@pytest.mark.parametrize("os_exists, directory_content, manifest_content, expected", [
    ([True, True], ["v1"], None, ("v1_result", ["layer1", "layer2"])),
    ([False, True], ["v2"], {"fsLayers": [...]}, ("v2_s1_result", ["layer1", "layer2"])),
    ([False, True], ["v2"], {"layers": [...]}, ("v2_s2_result", ["layer1", "layer2"])),
    ([False, False], [], None, (None, None)),
])
@pytest.mark.parametrize("topdir", UDOCKER_TOPDIR)
def test_43_get_image_attributes(mocker, localrepo, os_exists, directory_content, manifest_content, expected):
    """Test43 LocalRepository().get_image_attributes()."""
    mocker.patch.object(os.path, 'exists', side_effect=os_exists)
    mocker.patch.object(localrepo, 'load_json', side_effect=[manifest_content])
    mocker.patch.object(localrepo, '_get_image_attributes_v1', return_value=("v1_result", ["layer1", "layer2"]))
    mocker.patch.object(localrepo, '_get_image_attributes_v2_s1', return_value=("v2_s1_result", ["layer1", "layer2"]))
    mocker.patch.object(localrepo, '_get_image_attributes_v2_s2', return_value=("v2_s2_result", ["layer1", "layer2"]))

    result = localrepo.get_image_attributes()
    assert result == expected

@pytest.mark.parametrize("manifest_json, expected_output", [
    ({"architecture": "x86_64", "os": "linux", "variant": "v8"}, "linux/x86_64/v8"),
    ({"architecture": "x86_64", "os": "linux"}, "linux/x86_64"),
    ({"architecture": "x86_64"}, "unknown/x86_64"),
    ({"os": "linux"}, "linux/unknown"),
    ({}, "unknown/unknown"),
    (None, "unknown/unknown"),
])
@pytest.mark.parametrize("topdir", UDOCKER_TOPDIR)
def test_44_get_image_platform_fmt(mocker, localrepo, manifest_json, expected_output):
    """Test44 LocalRepository().get_image_platform_fmt()."""
    mocker.patch.object(localrepo, 'get_image_attributes', return_value=(manifest_json, None))
    result = localrepo.get_image_platform_fmt()
    assert result == expected_output


@pytest.mark.parametrize("filename, starts_with_slash, repodir, tagdir, os_exists, raise_error, expected", [
    ("/absolute/path.json", True, False, False, [True], None, True),
    ("relative/path.json", False, True, True, [True, True], None, True),
    ("relative/no_repodir.json", False, False, True, [False, True], None, False),
    ("relative/no_tagdir.json", False, True, False, [True, False], None, False),
    ("relative/no_tagdir_no_repodir.json", False, False, False, [False, False], None, False),
    ("relative/repodir.json", False, True, True, [True, False], None, False),
    ("relative/tagdir.json", False, True, True, [False, True], None, False),
    ("/absolute/exception.json", True, False, False, [True], {'open': OSError, 'load': None}, False),
    ("/absolute/exception.json", True, False, False, [True], {'open': None, 'dump': OSError}, False),
    ("relative/exception.json", False, True, True, [True, True], {'open': OSError, 'dump': None}, False),
], ids=[
    "absolute path",
    "relative path with valid directories",
    "missing cur_repodir",
    "missing cur_tagdir",
    "miss both directories",
    "only cur_repodir exists",
    "only cur_tagdir exists",
    "exception with absolute path open file",
    "exception with absolute path dump file",
    "exception with relative path"
])
@pytest.mark.parametrize("topdir", UDOCKER_TOPDIR)
def test_45_save_json(mocker, localrepo, filename, starts_with_slash, repodir, tagdir, os_exists, raise_error,
                      expected):
    """Test45 LocalRepository().save_json()."""
    mocker.patch.object(localrepo, 'cur_repodir', '/tmp/repodir' if repodir else None)
    mocker.patch.object(localrepo, 'cur_tagdir', '/tmp/repodir' if tagdir else None)
    mocker.patch.object(os.path, 'exists', side_effect=os_exists)

    if raise_error and raise_error.get('open'):
        mocker.patch("builtins.open", side_effect=OSError)
    else:
        mock_file = mocker.mock_open()
        mocker.patch("builtins.open", mock_file)

    if raise_error and raise_error.get('dump'):
        mocker.patch("json.dump", side_effect=OSError)

    result = localrepo.save_json(filename, {"data": "test"})
    assert result == expected


@pytest.mark.parametrize("filename, st_with_slash, repodir, tagdir, os_exists, file_exists, raise_error, expected", [
    ("/absolute/path.json", True, False, False, [True, None], True, None, {"test": "data"}),
    ("relative/path.json", False, True, True, [True, True], True, None, {"test": "data"}),
    ("relative/no_repodir.json", False, False, True, [False, True], True, False, False),
    ("relative/no_tagdir.json", False, True, False, [True, False], True, False, False),
    ("relative/no_tagdir_no_repodir.json", False, False, False, [False, False], None, True, False),
    ("relative/repodir.json", False, True, True, [True, False], None, True, False),
    ("relative/tagdir.json", False, True, True, [False, True], None, True, False),
    ("/absolute/no_file.json", True, False, False, [True], False, False, None),
    ("relative/exception.json", False, True, True, [True, True], True, True, None),
], ids=[
    "absolute path",
    "relative path with valid directories",
    "missing cur_repodir",
    "missing cur_tagdir",
    "miss both directories",
    "only cur_repodir exists",
    "only cur_tagdir exists",
    "exception with absolute path",
    "exception with relative path"
])
@pytest.mark.parametrize("topdir", UDOCKER_TOPDIR)
def test_46_load_json(mocker, localrepo, filename, st_with_slash, repodir, tagdir, os_exists, file_exists, raise_error,
                      expected):
    """Test46 LocalRepository().load_json()."""
    mocker.patch.object(localrepo, 'cur_repodir', '/tmp/repodir' if repodir else None)
    mocker.patch.object(localrepo, 'cur_tagdir', '/tmp/repodir' if tagdir else None)
    mocker.patch.object(os.path, 'exists', side_effect=os_exists)

    mock_file = mocker.mock_open(read_data='{"test": "data"}' if file_exists else "")
    mocker.patch("builtins.open", side_effect=OSError if raise_error else mock_file)

    if file_exists:
        mocker.patch("json.load", return_value={"test": "data"})

    result = localrepo.load_json(filename)
    assert result == expected


@pytest.mark.parametrize(
    "imagetagdir_exists, file_list, load_json_returns, expected_structure, expected_calls, expected_warnings", [
        (False, [], {}, {'repolayers': {}}, 0, 0),
        (True, [], {}, {'repolayers': {}}, 0, 0),
        (True, ["ancestry", "manifest", "randomfile.txt"], {"ancestry": {}, "manifest": {}},
         {'ancestry': {}, 'manifest': {}, 'repolayers': {}}, 2, 1),
        (True, [CHARACTERS_64 + "64chars.json"], {CHARACTERS_64 + "64chars.json": {}},
         {'has_json_f': True,
          'repolayers': {CHARACTERS_64 + "64chars": {'json': {}, 'json_f': '/test/' + CHARACTERS_64 + '64chars.json'}}},
         1, 0),
        (True, [CHARACTERS_64 + "64chars.layer"], {},
         {"repolayers": {CHARACTERS_64 + "64chars": {"layer_f": "/test/" + CHARACTERS_64 + "64chars.layer"}}}, 0, 0),
        (True, [CHARACTERS_64 + "file:with:colon"], {},
         {"repolayers": {CHARACTERS_64 + "file:with:colon": {"layer_f": "/test/" + CHARACTERS_64 + "file:with:colon"}}},
         0, 0),
        (True, [CHARACTERS_64], {}, {'repolayers': {CHARACTERS_64: {}}}, 0, 1),
        (True, ["TAG", "v1", "v2", "PROTECT", "container.json"], {}, {'repolayers': {}}, 0, 0),
    ]
)
@pytest.mark.parametrize("topdir", UDOCKER_TOPDIR)
def test_47__load_structure(mocker, localrepo, logger, imagetagdir_exists, file_list, load_json_returns,
                            expected_structure, expected_calls, expected_warnings):
    """Test47 LocalRepository()._load_structure().
    Scan the repository structure of a given image tag.
    """
    mocker.patch.object(os.path, 'isdir', return_value=imagetagdir_exists)
    mocker.patch.object(os, 'listdir', return_value=file_list)
    mocker.patch.object(localrepo, 'load_json', side_effect=lambda x: load_json_returns.get(x, {}))

    result = localrepo._load_structure("/test")
    assert localrepo.load_json.call_count == expected_calls
    assert result == expected_structure
    assert logger.warning.call_count == expected_warnings


@pytest.mark.parametrize("structure, my_layer_id, expected_top_layer_id", [
    ({}, "", ""),
    ({"repolayers": {"layer1": {"json": {}}}, "ancestry": {"layers": "foolayername"}}, "", "layer1"),
    ({"repolayers": {"layer1": {}}, "ancestry": {"layers": "foolayername"}}, "", "layer1"),
    ({"repolayers": {"layer1": {"json": {"parent": "layer2"}}, "layer2": {"json": {}}},
      "ancestry": {"layers": "foolayername"}}, "layer1", "layer1"),
    ({"repolayers": {"layer1": {"json": {"parent": "nonexistent"}}}, "ancestry": {"layers": "foolayername"}}, "layer1",
     "layer1"),
    ({"repolayers": {"layer1": {"json": {"parent": "layer2"}}, "layer2": {"json": {"parent": "layer3"}},
                     "layer3": {"json": {}}}}, "layer1", "layer1"),
    ({"repolayers": {"layer1": {"json": {"parent": "layer2"}},
                     "layer2": {"json": {}}}, "repoconfigs": {}}, "layer2", "layer1"),

])
@pytest.mark.parametrize("topdir", UDOCKER_TOPDIR)
def test_48__find_top_layer_id(localrepo, structure, my_layer_id, expected_top_layer_id):
    """Test48 LocalRepository()._find_top_layer_id"""
    result = localrepo._find_top_layer_id(structure, my_layer_id)
    assert result == expected_top_layer_id


@pytest.mark.parametrize("structure, top_layer_id, expected", [
    ({"repolayers": {"layer1": {"json": {}}}}, "layer1", ["layer1"]),
    ({"repolayers": {"layer1": {"json": {"parent": "layer2"}}, "layer2": {"json": {"parent": "layer3"}},
                     "layer3": {"json": {}}}}, "layer1", ["layer1", "layer2", "layer3"]),
    ({"repolayers": {"layer1": {"json": {"parent": {}}}, "layer2": {"json": {}}}}, "layer1", ["layer1"]),
])
@pytest.mark.parametrize("topdir", UDOCKER_TOPDIR)
def test_49__sorted_layers(localrepo, structure, top_layer_id, expected):
    """Test49 LocalRepository()._sorted_layers"""
    result = localrepo._sorted_layers(structure, top_layer_id)
    assert result == expected


@pytest.mark.parametrize("layer_id, expected", [
    ("", ("", "")),
    (":", ["", ""]),
    ("sha256:abcdef1234567890", ["sha256", "abcdef1234567890"]),
    ("md5:12345abcdef", ["md5", "12345abcdef"]),
    (":abcdef1234567890", ["", "abcdef1234567890"]),
    ("sha256:abcdef:1234567890", ["sha256", "abcdef:1234567890"]),
])
@pytest.mark.parametrize("topdir", UDOCKER_TOPDIR)
def test_50__split_layer_id(localrepo, layer_id, expected):
    """Test50 LocalRepository()._split_layer_id"""
    result = localrepo._split_layer_id(layer_id)
    assert result == expected


@pytest.mark.parametrize(
    "layer_id, layer_f, cur_tagdir, layer_f_exists, islink, layer_target_exists, filetype, tar, checksum, expected", [
        ("sha256:abc123", "/path/to/layer", "/path/to/tagdir", False, False, False, "", True, True, False),
        ("sha256:abc123", "/path/to/layer", "/path/to/tagdir", True, True, False, "", True, True, False),
        ("sha256:abc123", "/path/to/layer", "/path/to/tagdir", True, True, True, "text", True, True, True),
        ("sha256:abc123", "/path/to/layer", "/path/to/tagdir", True, True, True, "gzip", False, True, False),
        ("sha256:abc123", "/path/to/layer", "/path/to/tagdir", True, True, True, "gzip", True, True, True),
        ("sha256:abc123", "/path/to/layer", "/path/to/tagdir", True, True, True, "gzip", True, False, False),
    ], ids=[
        "Layer file does not exist or is not a symlink",
        "The target of the symlink does not exist",
        "Layer file exists, is a symlink, target exists, but not gzip",
        "Gzip file, tar verification fails",
        "Gzip file, tar verification succeeds, checksum matches",
        "Gzip file, tar verification succeeds, checksum does not match",
    ])
@pytest.mark.parametrize("topdir", UDOCKER_TOPDIR)
def test_51_verify_layer_file(mocker, localrepo, layer_id, layer_f, cur_tagdir, layer_f_exists, islink,
                           layer_target_exists, filetype, tar, checksum, expected):
    """Test51 LocalRepository()._verify_layer_file"""
    mocker.patch.object(localrepo, 'cur_tagdir', cur_tagdir)
    structure = {"repolayers": {layer_id: {"layer_f": layer_f}}}
    mocker.patch.object(os.path, 'exists', side_effect=lambda x: {
        layer_f: layer_f_exists,
        cur_tagdir + '/' + os.readlink(layer_f): layer_target_exists
    }.get(x, False))
    mocker.patch.object(os.path, 'islink', return_value=islink)
    mocker.patch.object(os, 'readlink', return_value="/path/to/actual/layer")
    mocker.patch.object(OSInfo, 'get_filetype', return_value=(None, filetype))
    mocker.patch.object(FileUtil, 'verify_tar', return_value=tar)
    mocker.patch.object(ChkSUM, 'hash', return_value=layer_id.split(":")[1] if checksum else "differenthash")

    result = localrepo._verify_layer_file(structure, "sha256:abc123")
    assert result == expected


@pytest.mark.parametrize("structure, log_info, log_errors, expected_result", [
    ({'top_layer_id': 'top_layer', 'sorted_layers': ['layer1', 'layer2', 'top_layer'],
      'ancestry': ['layer1', 'layer2', 'top_layer']}, ["finding top layer id"], [], True),
    ({'top_layer_id': 'top_layer', 'sorted_layers': ['layer1', 'layer2', 'top_layer'],
      'ancestry': ['layer1', 'wrong_layer', 'top_layer']}, ["finding top layer id"],
     ["ancestry: %s and layers not match: %s"], False),
    ({'top_layer_id': None, 'ancestry': ['layer1', 'layer2', 'top_layer']}, ["finding top layer id"],
     ["finding top layer id"], False),
], ids=[
    "Correct ancestry matching layers",
    "Ancestry layers do not match sorted layers",
    "Top layer ID cannot be found",
])
@pytest.mark.parametrize("topdir", UDOCKER_TOPDIR)
def test_52__verify_image_v1(mocker, localrepo, logger, structure, log_info, log_errors, expected_result):
    """Test52 LocalRepository()._verify_image_v1"""
    mocker.patch.object(localrepo, '_find_top_layer_id', return_value=structure.get('top_layer_id'))
    mocker.patch.object(localrepo, '_sorted_layers', return_value=structure.get('sorted_layers', []))

    result = localrepo._verify_image_v1(structure)
    assert result == expected_result

    for info_message in log_info:
        basic_info_call = mocker.call(info_message)
        info_call_with_arg = mocker.call(info_message, mocker.ANY)
        assert any(
            basic_info_call == call or info_call_with_arg == call
            for call in logger.info.call_args_list
        )

    for error_message in log_errors:
        basic_error_call = mocker.call(error_message)
        error_call_with_arg = mocker.call(error_message, mocker.ANY, mocker.ANY)
        assert any(
            basic_error_call == call or error_call_with_arg == call
            for call in logger.error.call_args_list
        )

    if not log_errors:
        logger.error.assert_not_called()


@pytest.mark.parametrize("structure, log_error, expected", [
    ({"manifest": {"fsLayers": [{"blobSum": "layer1"}, {"blobSum": "layer2"}]},
      "repolayers": {"layer1": {}, "layer2": {}}}, False, True),
    ({"manifest": {"fsLayers": [{"blobSum": "layer1"}, {"blobSum": "layer3"}]},
      "repolayers": {"layer1": {}, "layer2": {}}}, True, False),
    ({"manifest": {"fsLayers": []}, "repolayers": {"layer1": {}, "layer2": {}}}, False, True),
], ids=[
    "All manifest layers exist in repolayers",
    "A layer in the manifest does not exist in repolayers",
    "No layers in manifest, but repolayers exist"
])
@pytest.mark.parametrize("topdir", UDOCKER_TOPDIR)
def test_53__verify_image_v2_s1(mocker, localrepo, logger, structure, log_error, expected):
    """Test53 LocalRepository()._verify_image_v2_s1"""
    result = localrepo._verify_image_v2_s1(structure)

    assert result == expected
    logger.error.assert_called_with("layer in manifest not exist in repo: %s", mocker.ANY) if log_error else \
        logger.error.assert_not_called


@pytest.mark.parametrize("structure, log_error, expected", [
    ({"blobSum": "layer1", "manifest": {
        "layers": [{"digest": "layer1", "blobSum": "foolayername"}, {"digest": "layer2", "blobSum": "foolayername"}]},
      "repolayers": {"layer1": {}, "layer2": {}}}, False, True),
    ({"manifest": {"layers": [{"digest": "non_existent_layer", "blobSum": "foolayername"},
                              {"digest": "layer3", "blobSum": "foolayername"}]},
      "repolayers": {"layer1": {}, "layer2": {}}}, True, False),
    ({"blobSum": "layer1", "manifest": {"layers": []}, "repolayers": {"layer1": {}, "layer2": {}}}, False, True),
], ids=[
    "All manifest layers exist in repolayers",
    "A layer in the manifest does not exist in repolayers",
    "No layers in manifest, but repolayers exist"
])
@pytest.mark.parametrize("topdir", UDOCKER_TOPDIR)
def test_54__verify_image_v2_s2(mocker, localrepo, logger, structure, log_error, expected):
    """Test54 LocalRepository()._verify_image_v2_s2"""
    result = localrepo._verify_image_v2_s2(structure)
    assert result == expected
    logger.error.assert_called_with("layer in manifest not exist in repo: %s", mocker.ANY) if log_error else \
        logger.error.assert_not_called


@pytest.mark.parametrize("structure, ver_v1, ver_v2_s1, ver_v2_s2, layer, log_info, log_errors, expected", [
    (None, None, None, None, [], ["loading structure"], ["load of image tag structure failed"], False),

    ({"ancestry": ["layer1", "layer2"], "has_json_f": True,
      "repolayers": {"layer1": {"layer_f": True}, "layer2": {"layer_f": True}}}, True, None, None, [True, True],
     ["loading structure", "verifying layers", "layer ok: %s"], [], True),

    ({"manifest": {"fsLayers": [{"blobSum": "layer1"}, {"blobSum": "layer2"}]},
      "repolayers": {"layer1": {"layer_f": True}, "layer2": {"layer_f": True}}}, None, True, None, [True, True],
     ["loading structure", "verifying layers", "layer ok: %s"], [], True),

    ({"manifest": None, "repolayers": {}, "layer2": {}}, None, True, None, [],
     ["loading structure", "verifying layers", ], ["manifest is empty"], False),

    ({"manifest": {"layers": [{"digest": "layer1"}, {"digest": "layer2"}]},
      "repolayers": {"layer1": {"layer_f": True}, "layer2": {"layer_f": True}}}, None, None, True, [True, True],
     ["loading structure", "verifying layers", "layer ok: %s"], [], True),

    ({"manifest": {"layers": [{"digest": "layer1"}, {"digest": "layer2"}]},
      "repolayers": {"layer1": {"layer_f": {}}, "layer2": {}}}, None, None, True, [False, False],
     ["loading structure", "verifying layers"], ["layer file not found in structure: %s"], False),

    ({"manifest": {"layers": [{"digest": "layer1"}, {"digest": "layer2"}]},
      "repolayers": {"layer1": {}, "layer2": {}}}, None, None, True, [False, False],
     ["loading structure", "verifying layers"], ["layer file not found in structure: %s"], False),
], ids=[
    "No structure",
    "Valid v1 image structure",
    "Valid v2 schema 1 image structure",
    "Missing v2 schema 1 image structure",
    "Valid v2 schema 2 image structure",
    "Missing v2 schema 2 image structure",
    "Incomplete or incorrect structure"
])
@pytest.mark.parametrize("topdir", UDOCKER_TOPDIR)
def test_55_verify_image(mocker, localrepo, logger, structure, ver_v1, ver_v2_s1, ver_v2_s2, layer, log_info,
                         log_errors, expected):
    """Test55 LocalRepository().verify_image"""
    mocker.patch.object(localrepo, '_load_structure', return_value=structure)

    if ver_v1 is not None:
        mocker.patch.object(localrepo, '_verify_image_v1', return_value=ver_v1)
    if ver_v2_s1 is not None:
        mocker.patch.object(localrepo, '_verify_image_v2_s1', return_value=ver_v2_s1)
    if ver_v2_s2 is not None:
        mocker.patch.object(localrepo, '_verify_image_v2_s2', return_value=ver_v2_s2)

    mocker.patch.object(localrepo, '_verify_layer_file', side_effect=layer)

    result = localrepo.verify_image()

    assert result == expected
    for info_message in log_info:
        basic_info_call = mocker.call(info_message)
        info_call_with_arg = mocker.call(info_message, mocker.ANY)
        assert any(
            basic_info_call == call or info_call_with_arg == call
            for call in logger.info.call_args_list
        )

    for error_message in log_errors:
        basic_error_call = mocker.call(error_message)
        error_call_with_arg = mocker.call(error_message, mocker.ANY)
        assert any(
            basic_error_call == call or error_call_with_arg == call
            for call in logger.error.call_args_list
        )

    if not log_errors:
        logger.error.assert_not_called()
